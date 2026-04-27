"""Unit + integration tests for the Agent tool (subagent dispatcher).

Covers:
- P1.2: Agent tool unit — load agent def, build sub-loop, return summary,
        error paths (missing agent, malformed def, sub-loop failure,
        nested-spawn rejection).
- P1.3: Fan-out integration — main loop dispatches multiple Agent tool calls
        in one tool_use turn; each sub-loop runs with isolated context,
        respects per-agent tool whitelist, returns its own summary; main
        receives N independent ToolResults.

We don't hit the real API. FakeAnthropicClient mocks responses; the
SAME fake client is shared by main and sub-loops (responses queue is
consumed in dispatch order — main response first, then per-subagent
responses).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness.agent import AgentLoop
from app.harness.tools.agent import AgentTool, AgentToolConfig
from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.registry import ToolRegistry, default_registry

# Reuse the fakes from test_agent.py rather than duplicate them.
from tests.harness.test_agent import (
    FakeAnthropicClient,
    FakeResponse,
    FakeTextBlock,
    FakeToolUseBlock,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _write_agent(agents_dir: Path, name: str, *, body: str = "Worker prompt body.\n# Role\nYou are a worker.",
                 model: str | None = None, tools: list[str] | None = None) -> None:
    """Write a minimal valid .claude/agents/<name>.md file."""
    lines = ["---", f"name: {name}", "description: A test worker agent."]
    if model is not None:
        lines.append(f"model: {model}")
    if tools is not None:
        if not tools:
            lines.append("tools: []")
        else:
            lines.append("tools: [" + ", ".join(tools) + "]")
    lines.append("---")
    lines.append("")
    lines.append(body)
    (agents_dir / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")


def _make_agent_tool(
    *,
    client: FakeAnthropicClient,
    agents_root: Path,
    sub_registry_factory=default_registry,
) -> AgentTool:
    return AgentTool(
        AgentToolConfig(
            client=client,  # type: ignore[arg-type]
            default_model="model-default",
            agents_root=agents_root,
            sub_registry_factory=sub_registry_factory,
        )
    )


# ────────────────────────────────────────────────────────────────────────────
# P1.2 — Agent tool unit tests
# ────────────────────────────────────────────────────────────────────────────

class TestAgentToolUnit:
    def test_runs_subagent_and_returns_summary(self, tmp_path):
        _write_agent(tmp_path, "worker")
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="subagent summary")],
                stop_reason="end_turn",
            )
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        result = tool.run(agent="worker", prompt="do thing X")

        assert result.is_error is False
        assert result.content == "subagent summary"
        # Sub-loop made exactly one API call
        assert len(client.messages.calls) == 1

    def test_uses_agent_model_override(self, tmp_path):
        _write_agent(tmp_path, "worker", model="model-special")
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        assert client.messages.calls[0]["model"] == "model-special"

    def test_falls_back_to_default_model_when_agent_omits(self, tmp_path):
        _write_agent(tmp_path, "worker", model=None)
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        assert client.messages.calls[0]["model"] == "model-default"

    def test_passes_agent_body_as_system_prompt(self, tmp_path):
        body = "# Worker role\nYou must obey instructions."
        _write_agent(tmp_path, "worker", body=body)
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        assert client.messages.calls[0]["system"] == body

    def test_passes_prompt_as_user_message(self, tmp_path):
        _write_agent(tmp_path, "worker")
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="solve TC1")

        msgs = client.messages.calls[0]["messages"]
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "solve TC1"

    def test_applies_tool_whitelist(self, tmp_path):
        """tools: [Read] in agent def → sub-loop's API call sends only Read."""
        _write_agent(tmp_path, "worker", tools=["Read"])
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        sub_tools = {t["name"] for t in client.messages.calls[0]["tools"]}
        assert sub_tools == {"Read"}

    def test_empty_tools_whitelist_gives_no_tools(self, tmp_path):
        """tools: [] → sub-loop sees empty tool list (pure chat)."""
        _write_agent(tmp_path, "worker", tools=[])
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        assert client.messages.calls[0]["tools"] == []

    def test_omitted_tools_inherits_full_subregistry(self, tmp_path):
        """No `tools` in agent def → sub-loop uses every tool the
        sub_registry_factory provides (default_registry → fs + web)."""
        _write_agent(tmp_path, "worker")  # no tools field
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        tool.run(agent="worker", prompt="x")

        sub_tools = {t["name"] for t in client.messages.calls[0]["tools"]}
        assert sub_tools == {
            "Read", "Write", "Glob", "Grep", "WebFetch", "WebSearch",
        }

    def test_missing_agent_returns_is_error(self, tmp_path):
        client = FakeAnthropicClient.with_responses()
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        result = tool.run(agent="nonexistent", prompt="x")

        assert result.is_error is True
        assert "nonexistent" in result.content
        # No API call should have been made
        assert client.messages.calls == []

    def test_malformed_agent_def_returns_is_error(self, tmp_path):
        # Missing description → AgentParseError
        (tmp_path / "broken.md").write_text(
            "---\nname: broken\n---\nbody\n", encoding="utf-8"
        )
        client = FakeAnthropicClient.with_responses()
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        result = tool.run(agent="broken", prompt="x")

        assert result.is_error is True
        assert "broken" in result.content

    def test_subloop_error_returns_is_error(self, tmp_path):
        _write_agent(tmp_path, "worker")
        # stop_reason "refusal" is unexpected → AgentLoopError → is_error
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="")], stop_reason="refusal")
        )
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        result = tool.run(agent="worker", prompt="x")

        assert result.is_error is True
        assert "worker" in result.content

    def test_rejects_sub_registry_with_agent_tool(self, tmp_path):
        """If sub_registry_factory accidentally produces a registry with the
        Agent tool registered, dispatch must refuse — nested spawn would
        let subagents recurse indefinitely."""
        _write_agent(tmp_path, "worker")
        client = FakeAnthropicClient.with_responses()  # no responses needed

        def bad_factory() -> ToolRegistry:
            reg = default_registry()
            reg.register(
                AgentTool(
                    AgentToolConfig(
                        client=client,  # type: ignore[arg-type]
                        default_model="m",
                        agents_root=tmp_path,
                        sub_registry_factory=default_registry,
                    )
                )
            )
            return reg

        tool = _make_agent_tool(
            client=client,
            agents_root=tmp_path,
            sub_registry_factory=bad_factory,
        )

        result = tool.run(agent="worker", prompt="x")

        assert result.is_error is True
        assert "nested" in result.content.lower()


# ────────────────────────────────────────────────────────────────────────────
# P1.2 — Tool schema sanity (Anthropic API shape)
# ────────────────────────────────────────────────────────────────────────────

class TestAgentToolSchema:
    def test_tool_metadata(self, tmp_path):
        client = FakeAnthropicClient.with_responses()
        tool = _make_agent_tool(client=client, agents_root=tmp_path)

        assert tool.name == "Agent"
        assert tool.description  # non-empty
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert set(schema["required"]) == {"agent", "prompt"}
        assert "agent" in schema["properties"]
        assert "prompt" in schema["properties"]


# ────────────────────────────────────────────────────────────────────────────
# P1.3 — Fan-out integration: main dispatches N Agent calls in one turn
# ────────────────────────────────────────────────────────────────────────────

class TestFanOutIntegration:
    """Main agent decides to spawn 3 subagents in one tool_use turn. Each
    sub-loop runs in isolation; main receives 3 independent summaries."""

    def test_three_parallel_subagent_calls_in_one_turn(self, tmp_path):
        # Three independent agent definitions (e.g. one per TC).
        for n in (1, 2, 3):
            _write_agent(tmp_path, f"tc-worker-{n}", body=f"# TC{n} worker\nSolve TC{n}.")

        # Response queue: main makes 1 call (3 tool_use), then 1 final call.
        # In between, each sub-loop makes 1 call.
        # SDK is synchronous — fakes consume responses in dispatch order:
        # main(1) → sub-tc1(2) → sub-tc2(3) → sub-tc3(4) → main-final(5)
        client = FakeAnthropicClient.with_responses(
            # 1. Main asks for 3 subagents
            FakeResponse(
                content=[
                    FakeToolUseBlock(id="t1", name="Agent",
                                     input={"agent": "tc-worker-1", "prompt": "solve TC1"}),
                    FakeToolUseBlock(id="t2", name="Agent",
                                     input={"agent": "tc-worker-2", "prompt": "solve TC2"}),
                    FakeToolUseBlock(id="t3", name="Agent",
                                     input={"agent": "tc-worker-3", "prompt": "solve TC3"}),
                ],
                stop_reason="tool_use",
            ),
            # 2. Sub-tc1 responds
            FakeResponse(
                content=[FakeTextBlock(text="TC1 solved with strategy A")],
                stop_reason="end_turn",
            ),
            # 3. Sub-tc2 responds
            FakeResponse(
                content=[FakeTextBlock(text="TC2 solved with strategy B")],
                stop_reason="end_turn",
            ),
            # 4. Sub-tc3 responds
            FakeResponse(
                content=[FakeTextBlock(text="TC3 solved with strategy C")],
                stop_reason="end_turn",
            ),
            # 5. Main aggregates and ends
            FakeResponse(
                content=[FakeTextBlock(text="Aggregated: A, B, C")],
                stop_reason="end_turn",
            ),
        )

        # Build main registry with Agent tool wired up
        agent_tool = _make_agent_tool(client=client, agents_root=tmp_path)
        main_registry = default_registry()
        main_registry.register(agent_tool)

        main_loop = AgentLoop(
            client=client,  # type: ignore[arg-type]
            model="model-main",
            system_prompt="You are the main agent. Spawn workers for parallel TCs.",
            tool_registry=main_registry,
        )

        result = main_loop.run("Solve TC1, TC2, TC3 in parallel.")

        # 5 API calls total: 1 main + 3 subagents + 1 main final
        assert len(client.messages.calls) == 5

        # Main loop made 2 iterations (1 tool_use, 1 end_turn)
        assert result.iterations == 2
        assert result.tool_calls == 3
        assert result.final_text == "Aggregated: A, B, C"

        # Each sub-loop got the right system prompt (isolated context)
        sub_calls = client.messages.calls[1:4]  # calls 2, 3, 4 are subagents
        assert "TC1 worker" in sub_calls[0]["system"]
        assert "TC2 worker" in sub_calls[1]["system"]
        assert "TC3 worker" in sub_calls[2]["system"]

        # Each sub-loop got its own user prompt (no cross-contamination)
        assert sub_calls[0]["messages"][0]["content"] == "solve TC1"
        assert sub_calls[1]["messages"][0]["content"] == "solve TC2"
        assert sub_calls[2]["messages"][0]["content"] == "solve TC3"

    def test_subagent_tool_results_round_trip_to_main(self, tmp_path):
        """The 3 subagent summaries must appear as 3 tool_result blocks in
        the main loop's follow-up user message — that's how main 'sees' the
        results."""
        _write_agent(tmp_path, "w1")
        _write_agent(tmp_path, "w2")

        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeToolUseBlock(id="t1", name="Agent",
                                     input={"agent": "w1", "prompt": "p1"}),
                    FakeToolUseBlock(id="t2", name="Agent",
                                     input={"agent": "w2", "prompt": "p2"}),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(content=[FakeTextBlock(text="summary 1")], stop_reason="end_turn"),
            FakeResponse(content=[FakeTextBlock(text="summary 2")], stop_reason="end_turn"),
            FakeResponse(content=[FakeTextBlock(text="done")], stop_reason="end_turn"),
        )

        agent_tool = _make_agent_tool(client=client, agents_root=tmp_path)
        main_registry = default_registry()
        main_registry.register(agent_tool)

        main_loop = AgentLoop(
            client=client,  # type: ignore[arg-type]
            model="m", system_prompt="s", tool_registry=main_registry,
        )

        main_loop.run("go")

        # The main's 2nd API call (calls[4] — index 4 since 1 main + 2 sub + 1 final
        # but final is index 4 because list is [main(0), sub1(1), sub2(2), main-final(3)])
        # Actually: 1 main + 2 sub + 1 main-final = 4 total, indices 0-3.
        assert len(client.messages.calls) == 4

        # The main-final call's messages should include tool_result blocks.
        final_main_call = client.messages.calls[3]
        last_user_msg = final_main_call["messages"][-1]
        assert last_user_msg["role"] == "user"

        tool_results = last_user_msg["content"]
        assert len(tool_results) == 2
        result_contents = {r["tool_use_id"]: r["content"] for r in tool_results}
        assert result_contents["t1"] == "summary 1"
        assert result_contents["t2"] == "summary 2"
        # No is_error on either
        assert all(not r["is_error"] for r in tool_results)

    def test_real_triz_analyst_dispatches_without_keyerror(self):
        """End-to-end check that triz-analyst.md (real agent) can be
        dispatched against the default sub-registry.

        Motivating bug: triz-analyst declares
            tools: [Read, Grep, Glob, WebSearch, WebFetch]
        but earlier default_registry only had Read/Write/Glob, so the
        sub-loop's `to_anthropic_schemas(only=...)` raised KeyError on
        WebSearch / WebFetch. Adding the web tools to default_registry (P3)
        fixes this. Also asserts: Grep is the one declared tool that
        STILL doesn't exist — the sub-loop should error gracefully on it
        rather than crashing the agent loop.
        """
        # Resolve the real .claude/agents/ root
        project_root = Path(__file__).resolve().parents[3]
        agents_root = project_root / ".claude" / "agents"
        assert (agents_root / "triz-analyst.md").is_file(), (
            f"triz-analyst.md missing — test depends on it being checked in"
        )

        # FakeAnthropicClient with a single end_turn response for the sub-loop.
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="TC analysis summary")],
                stop_reason="end_turn",
            )
        )
        tool = _make_agent_tool(client=client, agents_root=agents_root)

        result = tool.run(agent="triz-analyst", prompt="solve TC1")

        # The motivating bug would surface as is_error with a KeyError
        # message about Grep (the only declared tool we still don't have).
        # Gracefully surfacing that vs crashing IS the contract.
        if result.is_error:
            # Acceptable failure: missing tools surfaced in the message.
            assert "Grep" in result.content or "not registered" in result.content
        else:
            # Or: agent dispatched cleanly, returning the sub-loop's text.
            assert "TC analysis summary" in result.content

        # Either way: no Python exception escaped to the caller.

    def test_one_subagent_failing_does_not_block_others(self, tmp_path):
        """If one subagent fails (e.g. unknown agent name), main still gets
        results from the other two (with is_error=True for the failed one)."""
        _write_agent(tmp_path, "good1")
        _write_agent(tmp_path, "good2")
        # 'broken' agent intentionally not written

        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeToolUseBlock(id="t1", name="Agent",
                                     input={"agent": "good1", "prompt": "p1"}),
                    FakeToolUseBlock(id="t2", name="Agent",
                                     input={"agent": "broken", "prompt": "p2"}),
                    FakeToolUseBlock(id="t3", name="Agent",
                                     input={"agent": "good2", "prompt": "p3"}),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(content=[FakeTextBlock(text="ok1")], stop_reason="end_turn"),
            # 'broken' makes NO API call (fails before sub-loop starts)
            FakeResponse(content=[FakeTextBlock(text="ok3")], stop_reason="end_turn"),
            FakeResponse(content=[FakeTextBlock(text="done")], stop_reason="end_turn"),
        )

        agent_tool = _make_agent_tool(client=client, agents_root=tmp_path)
        main_registry = default_registry()
        main_registry.register(agent_tool)

        main_loop = AgentLoop(
            client=client,  # type: ignore[arg-type]
            model="m", system_prompt="s", tool_registry=main_registry,
        )

        result = main_loop.run("go")

        assert result.iterations == 2
        assert result.tool_calls == 3

        # 4 API calls total (1 main, 2 sub-good, 1 main-final). The 'broken'
        # agent failed before any API call.
        assert len(client.messages.calls) == 4

        # main-final saw 3 tool_result blocks — one with is_error=True
        final_user_msg = client.messages.calls[3]["messages"][-1]
        tool_results = final_user_msg["content"]
        assert len(tool_results) == 3
        errors = {r["tool_use_id"]: r["is_error"] for r in tool_results}
        assert errors == {"t1": False, "t2": True, "t3": False}
