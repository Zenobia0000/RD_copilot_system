"""Action Suggestions: post-decision action items with assignees.

SOW Module: 行動建議 (actions)
"""

from fastapi import APIRouter

from app.models.schemas import ActionSuggestRequest, ActionSuggestResponse
from app.agents.knowledge import suggest_actions

router = APIRouter()


@router.post("/actions/suggest", response_model=ActionSuggestResponse)
def actions_suggest(req: ActionSuggestRequest):
    """Knowledge Agent suggests action items based on decision outcome."""
    return suggest_actions(req)
