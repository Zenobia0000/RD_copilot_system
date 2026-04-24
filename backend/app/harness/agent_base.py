"""HarnessAgent[DepsT, OutputT] — typed agent base class.

Wraps Pydantic AI Agent with:
- Typed dependency injection (DepsT)
- Typed structured output (OutputT extends BaseModel)
- Token usage emission per invocation
- Context isolation (each agent has independent system prompt + tool scope)

Usage:
    from app.harness.agent_base import HarnessAgent
    from app.models.schemas import TrizLookupResponse

    triz_tc_agent = HarnessAgent(
        name="triz_tc",
        system_prompt=TRIZ_SOLVER_SYSTEM,
        output_type=TrizLookupResponse,
    )

    result = triz_tc_agent.run_sync("Solve this TC...", deps=None)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.harness.model_adapter import HarnessModel, emit_token_usage

logger = logging.getLogger(__name__)

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT", bound=BaseModel)


class HarnessAgent(Generic[DepsT, OutputT]):
    """Typed agent that wraps Pydantic AI for structured LLM calls.

    Each instance has:
    - An independent system prompt (context isolation)
    - A typed output model (Pydantic validation)
    - Per-call token usage tracking
    - Optional max_context_tokens budget
    """

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        output_type: type[OutputT],
        model_override: str | None = None,
        temperature: float = 0.2,
        max_context_tokens: int | None = None,
    ):
        self._name = name
        self._system_prompt = system_prompt
        self._output_type = output_type
        self._model = HarnessModel(
            agent_name=name,
            model_override=model_override,
            temperature=temperature,
        )
        self._max_context_tokens = max_context_tokens

    @property
    def name(self) -> str:
        return self._name

    def run_sync(
        self,
        user_message: str,
        *,
        deps: DepsT | None = None,
    ) -> OutputT:
        """Run the agent synchronously and return typed output.

        This bypasses Pydantic AI's Agent.run_sync to avoid async complexity.
        Instead, it directly calls the model adapter and parses the response.

        The approach matches the existing call_llm_json pattern:
        1. Send system_prompt + user_message to LLM
        2. Parse JSON response
        3. Validate with Pydantic output_type
        """
        from app.agents.base import call_llm_json
        from app.core.config import settings

        model_name = self._model._model_override or settings.fast_model

        raw = call_llm_json(
            self._system_prompt,
            user_message,
            model=model_name,
            temperature=self._model._temperature,
        )

        try:
            data = json.loads(raw) if raw and raw.strip() else {}
        except json.JSONDecodeError:
            logger.warning(
                "Agent '%s' returned unparseable JSON, using empty dict",
                self._name,
            )
            data = {}

        try:
            result = self._output_type.model_validate(data)
        except Exception as exc:
            logger.error(
                "Agent '%s' output validation failed: %s",
                self._name,
                exc,
            )
            raise

        return result

    def __repr__(self) -> str:
        return (
            f"HarnessAgent(name={self._name!r}, "
            f"output_type={self._output_type.__name__})"
        )


def harness_call(
    name: str,
    system_prompt: str,
    user_message: str,
    output_type: type[OutputT],
    *,
    model_override: str | None = None,
    temperature: float = 0.2,
) -> OutputT:
    """One-shot convenience: create a HarnessAgent and run it.

    Use this for the common pattern where a function just needs to call
    an LLM with a system prompt + user message and get typed output back.
    Provides token monitoring + context isolation for free.
    """
    agent = HarnessAgent(
        name=name,
        system_prompt=system_prompt,
        output_type=output_type,
        model_override=model_override,
        temperature=temperature,
    )
    return agent.run_sync(user_message)
