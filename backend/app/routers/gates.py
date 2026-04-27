"""Gate Checking: configurable rule engine + optional AI evaluation.

SOW Module: Gate 檢查 (gates)
SOW Endpoints:
  - GET /gates/{gate_id}/check  ← 8 gate variants (D1, D2, PG-D, X1, X2, PG-X, V2, PG-V)

Gate definitions are declarative — see app/core/gate_registry.py.
AI evaluators are registered in app/core/evaluator_registry.py (extensible).
AI evaluation is opt-in via include_ai_review query parameter.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import GateCheckResponse, GateCheckItem, AiReviewResult
from app.core.supabase import get_supabase
from app.core.gate_registry import GATE_REGISTRY
from app.core.evaluator_registry import run_ai_review

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/gates/{gate_id}/check", response_model=GateCheckResponse)
def gates_check(
    gate_id: str,
    project_id: str,
    include_ai_review: bool = False,
):
    """Check whether a project passes the specified quality gate.

    gate_id: D1 | D2 | PG-D | X1 | X2 | PG-X | V2 | PG-V
    include_ai_review: when True, gates with an AI evaluator run additional analysis.
    """
    defn = GATE_REGISTRY.get(gate_id)
    if defn is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid gate_id: {gate_id}. Valid: {set(GATE_REGISTRY.keys())}",
        )

    sb = get_supabase()
    checklist: list[GateCheckItem] = []
    failed_reasons: list[str] = []

    for check_fn in defn.checks:
        item, reason = check_fn(sb, project_id)
        checklist.append(item)
        if reason:
            failed_reasons.append(reason)

    # Optional AI review — dispatched via evaluator registry
    ai_review = None
    if include_ai_review and defn.ai_evaluator:
        try:
            ai_review = run_ai_review(defn.ai_evaluator, sb, project_id)
        except Exception:
            logger.exception("AI review failed for gate %s", gate_id)
            ai_review = AiReviewResult(
                evaluator=defn.ai_evaluator,
                summary="AI 評估失敗，請稍後重試",
                confidence=0.0,
            )

    return GateCheckResponse(
        gate_id=gate_id,
        passed=len(failed_reasons) == 0,
        failed_reasons=failed_reasons,
        checklist_items=checklist,
        ai_review=ai_review,
    )
