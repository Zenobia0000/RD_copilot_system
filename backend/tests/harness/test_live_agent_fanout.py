"""Live API smoke test — Agent tool fan-out end-to-end.

Verifies the post-P1+P2+P3 stack actually runs against the real Anthropic
API (via `config.build_client`):

- Custom agent loaded from a tmp `.claude/agents/<name>.md` file
- AgentLoop with `default_registry_with_agent` exposes the Agent tool
- Main loop dispatches one (or more) Agent tool calls
- Sub-loop runs in isolated context, returns its summary as tool_result
- WorkerStatus lifecycle (SPAWNING → RUNNING → FINISHED) emits on the main stream
- Final text reflects the subagent's output

Marked @pytest.mark.live, skipped by default. Run explicitly:
    pytest -m live tests/harness/test_live_agent_fanout.py

Cost: tiny prompt, max_tokens=500, max_iterations=3. Estimated ~$0.02 per run
on Anthropic Sonnet 4.6 (Azure or direct).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from app.harness.agent import (
    AgentLoop,
    DoneEvent,
    ErrorEvent,
    HarnessEvent,
    ToolResultEvent,
    ToolUseEvent,
    WorkerStatus,
    WorkerStatusEvent,
)
from app.harness.config import build_client, load_env
from app.harness.tools.registry import default_registry_with_agent

pytestmark = pytest.mark.live


# Path to project root: backend/tests/harness/test_live_agent_fanout.py
# parents[3] climbs harness → tests → backend → <project root>
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def harness_client():
    """Build a real Anthropic client from .env. Skip module if config missing."""
    load_env(_PROJECT_ROOT / ".env")
    try:
        return build_client()
    except Exception as exc:
        pytest.skip(f"harness config unavailable for live test: {exc}")


@pytest.fixture
def counter_agent_dir(tmp_path: Path) -> Path:
    """Write a minimal `counter` agent definition with no tool surface
    (pure-chat). Caller's prompt asks it to count and stop."""
    agent_md = (
        "---\n"
        "name: counter\n"
        "description: A trivial worker that outputs a counted sequence.\n"
        "tools: []\n"
        "---\n"
        "\n"
        "# Counter worker\n"
        "\n"
        "You count numbers in the requested range, separated by commas, on one\n"
        "line, then stop. Output exactly: `<n1>, <n2>, ..., <nk>`. No extra\n"
        "text, no explanation, no headings.\n"
    )
    (tmp_path / "counter.md").write_text(agent_md, encoding="utf-8")
    return tmp_path


# ────────────────────────────────────────────────────────────────────────────
# The test
# ────────────────────────────────────────────────────────────────────────────

class TestLiveAgentFanOut:
    """End-to-end: real API, real agent dispatch, deterministic prompt."""

    def test_main_dispatches_two_counter_workers(self, harness_client, counter_agent_dir):
        """Main loop should call the Agent tool at least twice (one per
        counter range), receive both summaries, and reflect both ranges in
        its final_text."""

        system_prompt = (
            "You orchestrate counter workers via the Agent tool.\n"
            "\n"
            "Your job: produce a single line listing numbers 1 through 10,\n"
            "comma-separated, by spawning TWO counter workers in parallel:\n"
            "  - Worker A: agent='counter', prompt='count 1 to 5'\n"
            "  - Worker B: agent='counter', prompt='count 6 to 10'\n"
            "\n"
            "Issue both Agent tool calls in a SINGLE response (parallel\n"
            "fan-out). When both workers return, concatenate their outputs\n"
            "with a comma and reply with just that line. Nothing else.\n"
        )

        registry = default_registry_with_agent(
            client=harness_client.client,
            default_model=harness_client.default_model,
            agents_root=counter_agent_dir,
        )

        loop = AgentLoop(
            client=harness_client.client,
            model=harness_client.default_model,
            system_prompt=system_prompt,
            tool_registry=registry,
            allowed_tools=["Agent"],  # main only has Agent — forces dispatch
            max_iterations=3,
            max_tokens=500,
        )

        # Use stream() to observe WorkerStatus lifecycle.
        events: list[HarnessEvent] = list(loop.stream(
            "Produce the line."
        ))

        # ───────────── Assertions ─────────────

        # 1. No ErrorEvent — loop completed successfully.
        errors = [e for e in events if isinstance(e, ErrorEvent)]
        assert not errors, (
            f"agent loop errored: {errors[0].message if errors else ''}\n"
            f"event types: {[type(e).__name__ for e in events]}"
        )

        # 2. WorkerStatus sequence: SPAWNING → RUNNING → FINISHED
        statuses = [
            e.status for e in events if isinstance(e, WorkerStatusEvent)
        ]
        assert statuses == [
            WorkerStatus.SPAWNING.value,
            WorkerStatus.RUNNING.value,
            WorkerStatus.FINISHED.value,
        ], f"unexpected status sequence: {statuses}"

        # 3. Exactly the Agent tool was called (no fs / web tools).
        tool_uses = [e for e in events if isinstance(e, ToolUseEvent)]
        agent_calls = [e for e in tool_uses if e.name == "Agent"]
        assert agent_calls, (
            f"main never invoked the Agent tool. "
            f"tools called: {[e.name for e in tool_uses]}"
        )

        # 4. At least 2 Agent tool calls (one per counter range).
        # Sonnet may parallelize in one turn (fan-out) or sequentially across
        # turns; both demonstrate dispatch works. We assert ≥ 2 either way.
        assert len(agent_calls) >= 2, (
            f"expected ≥ 2 Agent tool calls (one per counter), got "
            f"{len(agent_calls)}: {[(e.id, e.input) for e in agent_calls]}"
        )

        # 5. All Agent dispatches reference the 'counter' agent.
        for e in agent_calls:
            assert e.input.get("agent") == "counter", (
                f"Agent tool dispatched to unexpected agent: {e.input!r}"
            )

        # 6. Each Agent tool call produced a non-error tool_result.
        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        agent_results = [
            e for e in tool_results
            if e.tool_use_id in {a.id for a in agent_calls}
        ]
        assert len(agent_results) == len(agent_calls)
        for r in agent_results:
            assert r.is_error is False, (
                f"Agent dispatch returned is_error: {r.content[:300]}"
            )
            # Each subagent's output must be the comma-separated sequence
            # in its requested range — verify at least one number leaks
            # through (defensive against minor formatting variations).
            assert any(d in r.content for d in "0123456789"), (
                f"counter result lacks digits: {r.content[:300]}"
            )

        # 7. final_text covers the full 1..10 range.
        done = [e for e in events if isinstance(e, DoneEvent)]
        assert len(done) == 1
        final_text = done[0].final_text
        # All ten numbers should appear (counter A: 1-5, counter B: 6-10).
        for n in range(1, 11):
            assert str(n) in final_text, (
                f"final_text missing {n}. Got first 500 chars:\n"
                f"{final_text[:500]}"
            )

        # 8. iterations and tool_calls accounting.
        assert done[0].tool_calls == len(agent_calls)
        assert done[0].iterations >= 2  # at least: dispatch + final summary
        assert done[0].iterations <= 3  # bounded by max_iterations
