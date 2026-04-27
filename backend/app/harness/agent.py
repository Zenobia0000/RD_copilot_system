"""AgentLoop — Anthropic Messages API + tool-use loop.

The minimal viable agent: send messages → if the model wants tools, run them
and feed results back → loop until end_turn or max_iterations. No streaming,
no prompt caching, no thinking — those layer on later.

Design contract:
- Append the FULL response.content on each iteration (preserves tool_use blocks
  the model needs to see in its own history).
- Each tool_result must reference the matching tool_use.id.
- Tool failures are surfaced as is_error=True tool_results, never as Python
  exceptions — the loop must keep the model informed and let it adapt.
- Unknown stop_reason raises immediately; silent retries hide bugs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterator

from anthropic import Anthropic

from app.harness.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentResult:
    """End state of one AgentLoop.run() call."""

    final_text: str
    """Concatenation of all text blocks in the final assistant message."""

    stop_reason: str
    """The Anthropic stop_reason from the final API response."""

    iterations: int
    """How many model calls were made (1 = no tool use)."""

    tool_calls: int
    """Total number of tool invocations across the run."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    """Full conversation transcript for debugging."""


# ────────────────────────────────────────────────────────────────────────────
# Stream events — yielded by AgentLoop.stream()
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TextDeltaEvent:
    """A piece of text streamed from the model. Concatenate to get the
    running response."""

    text: str
    type: str = "text_delta"


@dataclass(frozen=True)
class ToolUseEvent:
    """The model decided to call a tool. Fires before dispatch."""

    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"


@dataclass(frozen=True)
class ToolResultEvent:
    """A tool finished. is_error=True surfaces handler failures."""

    tool_use_id: str
    content: str
    is_error: bool
    type: str = "tool_result"


@dataclass(frozen=True)
class IterationEndEvent:
    """One model call (one stream) just finished. Emitted before any
    follow-up tool dispatch or the next iteration."""

    iteration: int
    stop_reason: str
    type: str = "iteration_end"


@dataclass(frozen=True)
class DoneEvent:
    """Terminal event. Either end_turn or max_tokens."""

    final_text: str
    iterations: int
    tool_calls: int
    stop_reason: str
    type: str = "done"


@dataclass(frozen=True)
class ErrorEvent:
    """Terminal event for unrecoverable loop errors. The stream() generator
    yields this then stops; callers should treat it like done."""

    message: str
    type: str = "error"


HarnessEvent = (
    TextDeltaEvent
    | ToolUseEvent
    | ToolResultEvent
    | IterationEndEvent
    | DoneEvent
    | ErrorEvent
)


class AgentLoopError(RuntimeError):
    """Raised on unexpected stop reasons or iteration cap."""


class AgentLoop:
    """One-shot agent runner. Reusable across calls (no per-call state)."""

    def __init__(
        self,
        *,
        client: Anthropic,
        model: str,
        system_prompt: str,
        tool_registry: ToolRegistry,
        allowed_tools: list[str] | tuple[str, ...] | None = None,
        max_iterations: int = 20,
        max_tokens: int = 16000,
    ) -> None:
        self._client = client
        self._model = model
        self._system_prompt = system_prompt
        self._registry = tool_registry
        self._allowed = list(allowed_tools) if allowed_tools is not None else None
        self._max_iterations = max_iterations
        self._max_tokens = max_tokens

    def run(self, user_message: str) -> AgentResult:
        """Run the loop until end_turn or stop reason that ends generation."""
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]
        tool_schemas = self._registry.to_anthropic_schemas(only=self._allowed)
        tool_calls = 0

        for iteration in range(1, self._max_iterations + 1):
            logger.debug("agent iter %d (model=%s)", iteration, self._model)
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=self._system_prompt,
                tools=tool_schemas,
                messages=messages,
            )

            # Preserve full content (tool_use blocks must round-trip back).
            messages.append(
                {"role": "assistant", "content": _content_to_dicts(response.content)}
            )

            stop = response.stop_reason

            if stop == "end_turn":
                return AgentResult(
                    final_text=_extract_text(response.content),
                    stop_reason=stop,
                    iterations=iteration,
                    tool_calls=tool_calls,
                    messages=messages,
                )

            if stop == "max_tokens":
                # Truncated mid-thought. Don't loop — surface to caller.
                return AgentResult(
                    final_text=_extract_text(response.content),
                    stop_reason=stop,
                    iterations=iteration,
                    tool_calls=tool_calls,
                    messages=messages,
                )

            if stop == "tool_use":
                tool_results = []
                for block in response.content:
                    if getattr(block, "type", None) != "tool_use":
                        continue
                    tool_calls += 1
                    result = self._registry.dispatch(
                        block.name, dict(block.input or {})
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content,
                            "is_error": result.is_error,
                        }
                    )
                if not tool_results:
                    raise AgentLoopError(
                        "stop_reason=tool_use but no tool_use blocks in response"
                    )
                messages.append({"role": "user", "content": tool_results})
                continue

            # refusal, pause_turn, stop_sequence, or anything new — fail loud.
            raise AgentLoopError(
                f"unexpected stop_reason {stop!r} on iteration {iteration}"
            )

        raise AgentLoopError(
            f"agent did not finish within {self._max_iterations} iterations"
        )

    def stream(self, user_message: str) -> Iterator[HarnessEvent]:
        """Streaming variant of run(). Yields HarnessEvents as they happen:
        text deltas as the model generates, tool_use/tool_result around each
        dispatch, iteration_end after each model call, and a terminal done
        or error.

        Same control flow as run() — the only difference is we use
        messages.stream() and emit events instead of returning AgentResult
        at the end. AgentLoopError becomes a final ErrorEvent.
        """
        try:
            yield from self._stream_impl(user_message)
        except AgentLoopError as exc:
            yield ErrorEvent(message=str(exc))

    def _stream_impl(self, user_message: str) -> Iterator[HarnessEvent]:
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]
        tool_schemas = self._registry.to_anthropic_schemas(only=self._allowed)
        tool_calls = 0

        for iteration in range(1, self._max_iterations + 1):
            logger.debug("agent stream iter %d (model=%s)", iteration, self._model)

            with self._client.messages.stream(
                model=self._model,
                max_tokens=self._max_tokens,
                system=self._system_prompt,
                tools=tool_schemas,
                messages=messages,
            ) as stream:
                # Emit text deltas as they arrive. Tool-use blocks aren't
                # surfaced here — they're processed from the final message
                # below, where the input is fully assembled.
                for event in stream:
                    delta = _text_delta(event)
                    if delta is not None:
                        yield TextDeltaEvent(text=delta)
                final = stream.get_final_message()

            messages.append(
                {"role": "assistant", "content": _content_to_dicts(final.content)}
            )
            stop = final.stop_reason
            yield IterationEndEvent(iteration=iteration, stop_reason=stop or "unknown")

            if stop == "end_turn" or stop == "max_tokens":
                yield DoneEvent(
                    final_text=_extract_text(final.content),
                    iterations=iteration,
                    tool_calls=tool_calls,
                    stop_reason=stop,
                )
                return

            if stop == "tool_use":
                tool_results = []
                tool_use_blocks = [
                    b for b in final.content if getattr(b, "type", None) == "tool_use"
                ]
                if not tool_use_blocks:
                    raise AgentLoopError(
                        "stop_reason=tool_use but no tool_use blocks in response"
                    )
                for block in tool_use_blocks:
                    tool_calls += 1
                    args = dict(block.input or {})
                    yield ToolUseEvent(id=block.id, name=block.name, input=args)
                    result = self._registry.dispatch(block.name, args)
                    yield ToolResultEvent(
                        tool_use_id=block.id,
                        content=result.content,
                        is_error=result.is_error,
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content,
                            "is_error": result.is_error,
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
                continue

            raise AgentLoopError(
                f"unexpected stop_reason {stop!r} on iteration {iteration}"
            )

        raise AgentLoopError(
            f"agent did not finish within {self._max_iterations} iterations"
        )


def _text_delta(event: Any) -> str | None:
    """Extract a text delta from a stream event, or None.

    The SDK emits BOTH raw `content_block_delta` events AND high-level `text`
    convenience events for the same chunk while iterating MessageStream — so
    handling both would duplicate every delta. We pick the high-level form
    (simpler and provider-stable) and ignore raw content_block_deltas here.
    """
    if getattr(event, "type", None) == "text":
        return getattr(event, "text", None)
    return None


def _extract_text(content: list[Any]) -> str:
    """Concatenate all top-level text blocks. Skips tool_use, thinking, etc."""
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


def _content_to_dicts(content: list[Any]) -> list[dict[str, Any]]:
    """Convert SDK content blocks to plain dicts so they can be re-sent.

    The Anthropic SDK accepts dict shapes for assistant messages on subsequent
    requests; converting up-front avoids leaking SDK internal types into the
    transcript and keeps it JSON-serializable for logging.
    """
    out: list[dict[str, Any]] = []
    for block in content:
        btype = getattr(block, "type", None)
        if btype == "text":
            out.append({"type": "text", "text": block.text})
        elif btype == "tool_use":
            out.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": dict(block.input or {}),
                }
            )
        elif btype == "thinking":
            # Thinking blocks have a `signature` field that must round-trip
            # if extended thinking is enabled. Preserve everything we can.
            out.append(
                {
                    "type": "thinking",
                    "thinking": getattr(block, "thinking", ""),
                    "signature": getattr(block, "signature", ""),
                }
            )
        else:
            # Unknown block type — preserve raw if it has model_dump
            if hasattr(block, "model_dump"):
                out.append(block.model_dump())
            else:
                logger.warning("dropping unknown content block type: %r", btype)
    return out
