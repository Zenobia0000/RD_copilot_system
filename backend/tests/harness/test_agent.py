"""Unit tests for AgentLoop using a FakeAnthropicClient.

We don't hit the real API here — that comes in M4 when the CLI ties it all
together. These tests pin loop semantics: stop reasons, tool round-trips,
content preservation, error paths.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.harness.agent import AgentLoop, AgentLoopError
from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.registry import ToolRegistry


# ────────────────────────────────────────────────────────────────────────────
# Fakes — mimic Anthropic SDK response shape
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"


@dataclass
class FakeTextEvent:
    """Minimal stand-in for Anthropic's high-level `text` stream event."""

    text: str
    type: str = "text"


@dataclass
class FakeResponse:
    content: list[Any]
    stop_reason: str
    stream_events: list[Any] = field(default_factory=list)
    """Events yielded during messages.stream(). Empty = no streaming use."""


class FakeStream:
    """Context manager mimicking the SDK's MessageStream return type."""

    def __init__(self, *, events: list[Any], final: FakeResponse) -> None:
        self._events = events
        self._final = final

    def __enter__(self) -> "FakeStream":
        return self

    def __exit__(self, *_: Any) -> bool:
        return False

    def __iter__(self):
        return iter(self._events)

    def get_final_message(self) -> FakeResponse:
        return self._final


@dataclass
class FakeMessages:
    """The .messages namespace on the Anthropic client. Both .create() and
    .stream() pull from the same `responses` queue, so a test that drives the
    streaming loop just sets stream_events on its FakeResponses."""

    responses: list[FakeResponse]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def create(self, **kwargs: Any) -> FakeResponse:
        # Deep-copy so the snapshot doesn't mutate when the caller appends
        # to the messages list after this call returns.
        self.calls.append(copy.deepcopy(kwargs))
        if not self.responses:
            raise AssertionError(
                f"FakeAnthropicClient ran out of mocked responses "
                f"after {len(self.calls)} call(s)"
            )
        return self.responses.pop(0)

    def stream(self, **kwargs: Any) -> FakeStream:
        self.calls.append(copy.deepcopy(kwargs))
        if not self.responses:
            raise AssertionError(
                f"FakeAnthropicClient ran out of mocked stream responses "
                f"after {len(self.calls)} call(s)"
            )
        response = self.responses.pop(0)
        return FakeStream(events=list(response.stream_events), final=response)


@dataclass
class FakeAnthropicClient:
    """Just enough Anthropic shape for AgentLoop."""
    messages: FakeMessages

    @classmethod
    def with_responses(cls, *responses: FakeResponse) -> "FakeAnthropicClient":
        return cls(messages=FakeMessages(responses=list(responses)))


class _EchoTool(Tool):
    name = "Echo"
    description = "Echoes its input back"
    input_schema = {
        "type": "object",
        "properties": {"msg": {"type": "string"}},
        "required": ["msg"],
    }

    def run(self, *, msg: str) -> ToolResult:
        return ToolResult(content=f"echo:{msg}")


def _registry_with_echo() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(_EchoTool())
    return reg


# ────────────────────────────────────────────────────────────────────────────
# Single-shot end_turn (no tools)
# ────────────────────────────────────────────────────────────────────────────

class TestSingleShot:
    def test_end_turn_returns_text(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="hello world")],
                stop_reason="end_turn",
            )
        )
        loop = AgentLoop(
            client=client,
            model="claude-sonnet-4-6",
            system_prompt="be helpful",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("hi")

        assert result.final_text == "hello world"
        assert result.stop_reason == "end_turn"
        assert result.iterations == 1
        assert result.tool_calls == 0

    def test_concatenates_multiple_text_blocks(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeTextBlock(text="part one. "),
                    FakeTextBlock(text="part two."),
                ],
                stop_reason="end_turn",
            )
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("hi")
        assert result.final_text == "part one. part two."

    def test_passes_system_and_tools_to_api(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        loop = AgentLoop(
            client=client, model="claude-sonnet-4-6",
            system_prompt="YOU ARE A HELPER",
            tool_registry=_registry_with_echo(),
            max_tokens=4096,
        )

        loop.run("question")

        call = client.messages.calls[0]
        assert call["model"] == "claude-sonnet-4-6"
        assert call["system"] == "YOU ARE A HELPER"
        assert call["max_tokens"] == 4096
        assert call["messages"] == [{"role": "user", "content": "question"}]
        # tools schema present, only Echo registered
        assert len(call["tools"]) == 1
        assert call["tools"][0]["name"] == "Echo"


# ────────────────────────────────────────────────────────────────────────────
# Tool-use round-trip
# ────────────────────────────────────────────────────────────────────────────

class TestToolUseLoop:
    def test_single_tool_then_end_turn(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeTextBlock(text="let me check"),
                    FakeToolUseBlock(id="tu_1", name="Echo", input={"msg": "hi"}),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(
                content=[FakeTextBlock(text="result was: echo:hi")],
                stop_reason="end_turn",
            ),
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("call echo with hi")

        assert result.final_text == "result was: echo:hi"
        assert result.iterations == 2
        assert result.tool_calls == 1

    def test_second_call_includes_tool_result_in_messages(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeToolUseBlock(id="tu_42", name="Echo", input={"msg": "x"})],
                stop_reason="tool_use",
            ),
            FakeResponse(content=[FakeTextBlock(text="done")], stop_reason="end_turn"),
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        loop.run("go")

        # The 2nd API call must carry the assistant's tool_use AND the user's tool_result.
        second_call_msgs = client.messages.calls[1]["messages"]
        # [user(initial), assistant(tool_use), user(tool_result)]
        assert len(second_call_msgs) == 3
        assert second_call_msgs[0] == {"role": "user", "content": "go"}

        assistant_msg = second_call_msgs[1]
        assert assistant_msg["role"] == "assistant"
        # Content was preserved as dict including the tool_use block
        tool_use_block = assistant_msg["content"][0]
        assert tool_use_block["type"] == "tool_use"
        assert tool_use_block["id"] == "tu_42"
        assert tool_use_block["name"] == "Echo"
        assert tool_use_block["input"] == {"msg": "x"}

        user_msg = second_call_msgs[2]
        assert user_msg["role"] == "user"
        tool_result = user_msg["content"][0]
        assert tool_result["type"] == "tool_result"
        assert tool_result["tool_use_id"] == "tu_42"
        assert tool_result["content"] == "echo:x"
        assert tool_result["is_error"] is False

    def test_multiple_tool_calls_in_one_turn(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeToolUseBlock(id="a", name="Echo", input={"msg": "1"}),
                    FakeToolUseBlock(id="b", name="Echo", input={"msg": "2"}),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn"),
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("call twice")

        assert result.tool_calls == 2
        # All tool_results must be in a single user message
        results_msg = client.messages.calls[1]["messages"][-1]
        assert results_msg["role"] == "user"
        assert len(results_msg["content"]) == 2
        assert {b["tool_use_id"] for b in results_msg["content"]} == {"a", "b"}

    def test_tool_failure_surfaces_as_is_error_not_exception(self):
        # Echo will raise TypeError because we call with wrong arg name
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeToolUseBlock(id="t1", name="Echo", input={"wrong": "x"})],
                stop_reason="tool_use",
            ),
            FakeResponse(content=[FakeTextBlock(text="fixed")], stop_reason="end_turn"),
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("go")

        # No exception raised — tool error went into the conversation
        result_block = client.messages.calls[1]["messages"][-1]["content"][0]
        assert result_block["is_error"] is True
        assert "bad arguments" in result_block["content"]
        assert result.final_text == "fixed"


# ────────────────────────────────────────────────────────────────────────────
# Stop reason edge cases
# ────────────────────────────────────────────────────────────────────────────

class TestStopReasons:
    def test_max_tokens_returns_truncated_text(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="this got cut off mid-")],
                stop_reason="max_tokens",
            )
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        result = loop.run("write a long essay")

        assert result.stop_reason == "max_tokens"
        assert result.final_text == "this got cut off mid-"
        assert result.iterations == 1

    def test_unknown_stop_reason_raises(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="x")], stop_reason="refusal")
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        with pytest.raises(AgentLoopError, match="unexpected stop_reason 'refusal'"):
            loop.run("hi")

    def test_tool_use_with_no_tool_blocks_raises(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="thinking but no tools...")],
                stop_reason="tool_use",
            )
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
        )

        with pytest.raises(AgentLoopError, match="no tool_use blocks"):
            loop.run("go")

    def test_max_iterations_cap_enforced(self):
        # Infinite tool-use loop: every response says "use tool again"
        responses = [
            FakeResponse(
                content=[FakeToolUseBlock(id=f"t{i}", name="Echo", input={"msg": "x"})],
                stop_reason="tool_use",
            )
            for i in range(10)
        ]
        client = FakeAnthropicClient.with_responses(*responses)
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
            max_iterations=3,
        )

        with pytest.raises(AgentLoopError, match="3 iterations"):
            loop.run("go")
        assert len(client.messages.calls) == 3


# ────────────────────────────────────────────────────────────────────────────
# Allowed-tools whitelist
# ────────────────────────────────────────────────────────────────────────────

class TestAllowedToolsWhitelist:
    def test_only_whitelisted_tool_schemas_passed_to_api(self):
        from app.harness.tools.fs import GlobTool, ReadTool, WriteTool
        reg = ToolRegistry()
        reg.register(ReadTool())
        reg.register(WriteTool())
        reg.register(GlobTool())

        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=reg,
            allowed_tools=["Read", "Write"],
        )

        loop.run("hi")

        call_tools = {t["name"] for t in client.messages.calls[0]["tools"]}
        assert call_tools == {"Read", "Write"}

    def test_empty_whitelist_passes_empty_tools(self):
        """A skill could declare `allowed-tools: []` to run pure-chat with
        no tool surface. Loop should still complete; API receives tools=[]."""
        client = FakeAnthropicClient.with_responses(
            FakeResponse(content=[FakeTextBlock(text="just chat")], stop_reason="end_turn")
        )
        loop = AgentLoop(
            client=client, model="m", system_prompt="s",
            tool_registry=_registry_with_echo(),
            allowed_tools=[],
        )

        result = loop.run("hello")

        assert result.final_text == "just chat"
        assert client.messages.calls[0]["tools"] == []
