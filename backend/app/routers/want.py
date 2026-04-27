"""WANT Criteria: AI-seeded desirable criteria for KT decision.

SOW Module: WANT 評分 (want)
SOW Endpoints:
  - POST /want/criteria/seed       ← AI seed (implemented)
  - POST/GET /want/criteria        ← CRUD (handled by Supabase frontend)
"""

from fastapi import APIRouter

from app.models.schemas import WantSeedRequest, WantSeedResponse
from app.agents.evaluator import seed_want_criteria

router = APIRouter()


@router.post("/want/criteria/seed", response_model=WantSeedResponse)
def want_criteria_seed(req: WantSeedRequest):
    """Evaluator Agent generates W1-W6 WANT criteria from mission context."""
    return seed_want_criteria(req)
