"""Step 6 — MUST Evaluation: AI-assisted Go/No-Go screening."""

from fastapi import APIRouter

from app.models.schemas import MustEvaluationRequest, MustEvaluationResponse
from app.agents.evaluator import evaluate_must

router = APIRouter()


@router.post("/must/evaluate", response_model=MustEvaluationResponse)
def must_evaluate(req: MustEvaluationRequest):
    """Evaluator Agent pre-judges MUST pass/fail with confidence + reasoning.

    RD engineer reviews AI results and confirms or overrides on frontend.
    """
    return evaluate_must(req)
