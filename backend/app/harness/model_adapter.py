"""Model Adapter — bridges Pydantic AI Model protocol to existing _call_provider.

Wraps app.agents.base._call_provider without replacing it:
- Preserves multi-provider dispatch (Anthropic/OpenAI/Azure/Gemini/Qwen)
- Preserves retry_on_transient exponential backoff
- Adds per-call token usage emission
- Separates static_system (cacheable) from dynamic_context (non-cacheable)

Usage:
    from app.harness.model_adapter import HarnessModel

    agent = PydanticAgent(
        model=HarnessModel(),
        system_prompt="...",
        output_type=MyResponse,
    )
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelResponseStreamEvent,
    TextPart,
)
from pydantic_ai.models import Model, ModelRequestParameters, ModelSettings
from pydantic_ai.usage import RequestUsage

from app.core.config import settings
from app.observability import emit_counter, phase_timer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token usage tracking
# ---------------------------------------------------------------------------


def emit_token_usage(
    agent_name: str,
    usage: RequestUsage,
    latency_ms: float = 0.0,
) -> None:
    """Emit per-agent token usage metrics to the observability layer.

    This is the central instrumentation point for token monitoring.
    Phase 5 will extend this to write to Supabase / structured log.
    """
    if not usage.has_values:
        return

    logger.info(
        "Token usage [%s]: input=%d, output=%d, cache_read=%d, cache_write=%d, total=%d, latency=%.0fms",
        agent_name,
        usage.input_tokens,
        usage.output_tokens,
        usage.cache_read_tokens,
        usage.cache_write_tokens,
        usage.total_tokens,
        latency_ms,
    )
    emit_counter("harness.tokens.input", usage.input_tokens)
    emit_counter("harness.tokens.output", usage.output_tokens)
    if usage.cache_read_tokens:
        emit_counter("harness.tokens.cache_read", usage.cache_read_tokens)


# ---------------------------------------------------------------------------
# Message extraction helpers
# ---------------------------------------------------------------------------


def _extract_system_prompt(messages: list[ModelMessage]) -> str:
    """Extract system prompt from Pydantic AI message list.

    Pydantic AI puts system prompts as SystemPromptPart in the first ModelRequest.
    """
    parts = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if hasattr(part, "part_kind") and part.part_kind == "system-prompt":
                    parts.append(part.content)
    return "\n\n".join(parts)


def _extract_user_message(messages: list[ModelMessage]) -> str:
    """Extract user message from Pydantic AI message list.

    Combines all UserPromptPart content from all messages.
    """
    parts = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if hasattr(part, "part_kind") and part.part_kind == "user-prompt":
                    content = part.content
                    if isinstance(content, str):
                        parts.append(content)
                    elif isinstance(content, list):
                        # Multi-part content (text + images)
                        for item in content:
                            if isinstance(item, str):
                                parts.append(item)
                            elif hasattr(item, "text"):
                                parts.append(item.text)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# HarnessModel — the adapter
# ---------------------------------------------------------------------------


class HarnessModel(Model):
    """Pydantic AI Model adapter that delegates to existing _call_provider.

    This wraps the battle-tested multi-provider dispatch without replacing it.
    All retry logic, provider routing, and streaming are preserved.
    """

    def __init__(
        self,
        *,
        agent_name: str = "unknown",
        model_override: str | None = None,
        temperature: float = 0.3,
    ):
        self._agent_name = agent_name
        self._model_override = model_override
        self._temperature = temperature

    @property
    def model_name(self) -> str:
        return self._model_override or settings.default_model or "default"

    @property
    def system(self) -> str:
        return "harness"

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Send a request via _call_provider and wrap the result.

        Extracts system + user from Pydantic AI messages, calls the
        existing provider dispatch, and wraps the text response.
        """
        from app.agents.base import _call_provider

        system = _extract_system_prompt(messages)
        user_message = _extract_user_message(messages)

        # Resolve settings
        temperature = self._temperature
        max_tokens: int | None = None
        if model_settings:
            if hasattr(model_settings, "temperature") and model_settings.temperature is not None:
                temperature = model_settings.temperature
            if hasattr(model_settings, "max_tokens") and model_settings.max_tokens is not None:
                max_tokens = model_settings.max_tokens

        # Call the existing provider dispatch
        start = time.monotonic()
        try:
            text = _call_provider(
                system,
                user_message,
                model=self._model_override,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception:
            emit_counter("harness.request.error")
            raise

        latency_ms = (time.monotonic() - start) * 1000

        # Estimate token usage (actual counts come from provider response
        # but _call_provider doesn't expose them — use estimation for now)
        est_input = len(system + user_message) // 4
        est_output = len(text) // 4
        usage = RequestUsage(
            input_tokens=est_input,
            output_tokens=est_output,
        )

        emit_token_usage(self._agent_name, usage, latency_ms)
        emit_counter("harness.request.success")

        return ModelResponse(
            parts=[TextPart(content=text)],
            usage=usage,
            model_name=self.model_name,
        )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> AsyncIterator[ModelResponseStreamEvent]:
        """Streaming is not supported — fall back to non-streaming request."""
        # For now, we don't support streaming through the adapter.
        # The existing _call_provider already uses streaming internally
        # for Anthropic (to avoid 10-min timeout) but returns full text.
        raise NotImplementedError(
            "HarnessModel does not support streaming. "
            "Use request() instead."
        )
        yield  # type: ignore[misc]  # unreachable, satisfies async generator type
