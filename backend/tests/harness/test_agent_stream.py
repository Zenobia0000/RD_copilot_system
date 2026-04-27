"""Unit tests for AgentLoop.stream() — the streaming variant of run().

Uses FakeAnthropicClient (extended in test_agent.py) which now supports
.messages.stream() out of the same response queue. Each FakeResponse can
carry stream_events; the stream context manager replays them in order then
returns the FakeResponse itself as the final message.
"""

from __future__ import annotations

import pytest

from app.harness.agent import (
    AgentLoop,
    DoneEvent,
    ErrorEvent,
    IterationEndEvent,
    TextDeltaEvent,
    ToolResultEvent,
    ToolUseEvent,
)
from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.registry import ToolRegistry
from tests.harness.test_agent import (
    FakeAnthropicClient,
    FakeResponse,
    FakeTextBlock,
    FakeTextEvent,
    FakeToolUseBlock,
)


class _EchoTool(Tool):
    name = "Echo"
    description = "echoes its input back"
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


def _make_loop(client: FakeAnthropicClient, **kwargs) -> AgentLoop:
    defaults = dict(
        client=client, model="m", system_prompt="s",
        tool_registry=_registry_with_echo(),
    )
    defaults.update(kwargs)
    return AgentLoop(**defaults)


# ────────────────────────────────────────────────────────────────────────────
# Single-shot end_turn
# ────────────────────────────────────────────────────────────────────────────

class TestStreamSingleShot:
    def test_text_deltas_then_iteration_end_then_done(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="hello world")],
                stop_reason="end_turn",
                stream_events=[
                    FakeTextEvent(text="hello "),
                    FakeTextEvent(text="world"),
                ],
            )
        )
        loop = _make_loop(client)

        events = list(loop.stream("hi"))

        # Order: 2× TextDelta → IterationEnd → Done
        assert [type(e) for e in events] == [
            TextDeltaEvent,
            TextDeltaEvent,
            IterationEndEvent,
            DoneEvent,
        ]
        assert events[0].text == "hello "
        assert events[1].text == "world"
        assert events[2].iteration == 1
        assert events[2].stop_reason == "end_turn"
        done: DoneEvent = events[3]
        assert done.final_text == "hello world"
        assert done.iterations == 1
        assert done.tool_calls == 0
        assert done.stop_reason == "end_turn"

    def test_no_text_deltas_still_emits_done(self):
        """Some responses (pure tool_use, immediately) might have no text
        deltas. Loop should still emit IterationEnd + Done correctly."""
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="silent")],
                stop_reason="end_turn",
                stream_events=[],
            )
        )
        events = list(_make_loop(client).stream("hi"))

        assert [type(e) for e in events] == [IterationEndEvent, DoneEvent]


# ────────────────────────────────────────────────────────────────────────────
# Tool-use round-trip
# ────────────────────────────────────────────────────────────────────────────

class TestStreamToolUse:
    def test_emits_tool_use_then_tool_result_then_continues(self):
        client = FakeAnthropicClient.with_responses(
            # Iteration 1: text "let me check" + tool_use Echo(msg=hi)
            FakeResponse(
                content=[
                    FakeTextBlock(text="let me check"),
                    FakeToolUseBlock(id="tu_1", name="Echo", input={"msg": "hi"}),
                ],
                stop_reason="tool_use",
                stream_events=[FakeTextEvent(text="let me check")],
            ),
            # Iteration 2: result text + end_turn
            FakeResponse(
                content=[FakeTextBlock(text="result was: echo:hi")],
                stop_reason="end_turn",
                stream_events=[FakeTextEvent(text="result was: echo:hi")],
            ),
        )
        events = list(_make_loop(client).stream("call echo"))

        types = [type(e) for e in events]
        # iter1: text → iter_end(tool_use) → tool_use → tool_result
        # iter2: text → iter_end(end_turn) → done
        assert types == [
            TextDeltaEvent,
            IterationEndEvent,
            ToolUseEvent,
            ToolResultEvent,
            TextDeltaEvent,
            IterationEndEvent,
            DoneEvent,
        ]
        tu: ToolUseEvent = events[2]
        assert tu.id == "tu_1" and tu.name == "Echo" and tu.input == {"msg": "hi"}
        tr: ToolResultEvent = events[3]
        assert tr.tool_use_id == "tu_1"
        assert tr.content == "echo:hi"
        assert tr.is_error is False
        done: DoneEvent = events[6]
        assert done.iterations == 2
        assert done.tool_calls == 1

    def test_multiple_tool_calls_in_one_turn_yield_all(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[
                    FakeToolUseBlock(id="a", name="Echo", input={"msg": "1"}),
                    FakeToolUseBlock(id="b", name="Echo", input={"msg": "2"}),
                ],
                stop_reason="tool_use",
                stream_events=[],
            ),
            FakeResponse(
                content=[FakeTextBlock(text="ok")],
                stop_reason="end_turn",
                stream_events=[FakeTextEvent(text="ok")],
            ),
        )
        events = list(_make_loop(client).stream("call twice"))

        tool_uses = [e for e in events if isinstance(e, ToolUseEvent)]
        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert {e.id for e in tool_uses} == {"a", "b"}
        assert {e.tool_use_id for e in tool_results} == {"a", "b"}
        # Order: each tool_use immediately followed by its tool_result
        for i, e in enumerate(events):
            if isinstance(e, ToolUseEvent):
                assert isinstance(events[i + 1], ToolResultEvent)
                assert events[i + 1].tool_use_id == e.id

    def test_tool_failure_emitted_as_is_error_not_raised(self):
        # Echo will TypeError on missing 'msg'
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeToolUseBlock(id="t1", name="Echo", input={"wrong": "x"})],
                stop_reason="tool_use",
                stream_events=[],
            ),
            FakeResponse(
                content=[FakeTextBlock(text="recovered")],
                stop_reason="end_turn",
                stream_events=[FakeTextEvent(text="recovered")],
            ),
        )
        events = list(_make_loop(client).stream("go"))

        tr = next(e for e in events if isinstance(e, ToolResultEvent))
        assert tr.is_error is True
        assert "bad arguments" in tr.content
        # Loop still completed
        done = next(e for e in events if isinstance(e, DoneEvent))
        assert done.stop_reason == "end_turn"


# ────────────────────────────────────────────────────────────────────────────
# Stop-reason edge cases
# ────────────────────────────────────────────────────────────────────────────

class TestStreamStopReasons:
    def test_max_tokens_emits_done_with_truncated_text(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="cut off mid-")],
                stop_reason="max_tokens",
                stream_events=[FakeTextEvent(text="cut off mid-")],
            )
        )
        events = list(_make_loop(client).stream("essay"))

        done = events[-1]
        assert isinstance(done, DoneEvent)
        assert done.stop_reason == "max_tokens"
        assert done.final_text == "cut off mid-"

    def test_unknown_stop_reason_emits_error_not_raises(self):
        client = FakeAnthropicClient.with_responses(
            FakeResponse(
                content=[FakeTextBlock(text="x")],
                stop_reason="refusal",
                stream_events=[FakeTextEvent(text="x")],
            )
        )
        events = list(_make_loop(client).stream("hi"))

        # Sequence: text → iter_end(refusal) → error
        assert isinstance(events[-1], ErrorEvent)
        assert "refusal" in events[-1].message

    def test_max_iterations_cap_emits_error(self):
        infinite = [
            FakeResponse(
                content=[FakeToolUseBlock(id=f"t{i}", name="Echo", input={"msg": "x"})],
                stop_reason="tool_use",
                stream_events=[],
            )
            for i in range(10)
        ]
        client = FakeAnthropicClient.with_responses(*infinite)
        loop = _make_loop(client, max_iterations=2)

        events = list(loop.stream("go"))
        assert isinstance(events[-1], ErrorEvent)
        assert "2 iterations" in events[-1].message


# ────────────────────────────────────────────────────────────────────────────
# Cross-check: stream() returns same final_text/iterations as run()
# ────────────────────────────────────────────────────────────────────────────

class TestStreamMatchesRun:
    @pytest.mark.parametrize("with_tools", [False, True])
    def test_done_event_matches_run_result(self, with_tools):
        if with_tools:
            run_responses = [
                FakeResponse(
                    content=[FakeToolUseBlock(id="t1", name="Echo", input={"msg": "x"})],
                    stop_reason="tool_use",
                ),
                FakeResponse(
                    content=[FakeTextBlock(text="done")],
                    stop_reason="end_turn",
                ),
            ]
            stream_responses = [
                FakeResponse(
                    content=[FakeToolUseBlock(id="t1", name="Echo", input={"msg": "x"})],
                    stop_reason="tool_use",
                    stream_events=[],
                ),
                FakeResponse(
                    content=[FakeTextBlock(text="done")],
                    stop_reason="end_turn",
                    stream_events=[FakeTextEvent(text="done")],
                ),
            ]
        else:
            run_responses = [
                FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
            ]
            stream_responses = [
                FakeResponse(
                    content=[FakeTextBlock(text="ok")],
                    stop_reason="end_turn",
                    stream_events=[FakeTextEvent(text="ok")],
                )
            ]

        # Run via run()
        client_run = FakeAnthropicClient.with_responses(*run_responses)
        result = _make_loop(client_run).run("hi")

        # Run via stream()
        client_stream = FakeAnthropicClient.with_responses(*stream_responses)
        events = list(_make_loop(client_stream).stream("hi"))
        done: DoneEvent = events[-1]

        assert done.final_text == result.final_text
        assert done.iterations == result.iterations
        assert done.tool_calls == result.tool_calls
        assert done.stop_reason == result.stop_reason
