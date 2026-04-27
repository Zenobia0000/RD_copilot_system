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
from typing import Any

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
