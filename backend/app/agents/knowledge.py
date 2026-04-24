"""Knowledge Agent — action suggestions, knowledge write-back.

Ref: AI_Agent_Architecture.md §1.1 Knowledge Agent + §6.2 knowledge_agent tools
"""

import json

from app.agents.base import call_llm_json
from app.prompts.knowledge import KNOWLEDGE_SYSTEM, ACTION_SUGGESTION
from app.core.config import settings
from app.models.schemas import (
    ActionSuggestRequest,
    ActionSuggestResponse,
)


def suggest_actions(req: ActionSuggestRequest) -> ActionSuggestResponse:
    prompt = ACTION_SUGGESTION.format(
        selected_alternative=req.selected_alternative,
        rationale=req.rationale,
        risks="\n".join(f"- {r}" for r in req.risks),
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        return harness_call(
            "knowledge_actions", KNOWLEDGE_SYSTEM, prompt,
            ActionSuggestResponse, model_override=settings.fast_model,
        )
    raw = call_llm_json(
        KNOWLEDGE_SYSTEM,
        prompt,
        model=settings.fast_model,
    )
    data = json.loads(raw)
    return ActionSuggestResponse(**data)
