"""Auto-TRIZ v2 Analyst endpoints (WBS 8.2.1-8.2.5).

Five new analysis methods:
  - POST /analyst/five-why          (8.2.1)
  - POST /analyst/kt-analysis       (8.2.2)
  - POST /analyst/function-analysis  (8.2.3) — writes to function_models table
  - POST /analyst/oz-ot-analysis     (8.2.4) — updates contradictions table
  - POST /analyst/entry-grading      (8.2.5)
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    FiveWhyRequest,
    FiveWhyResponse,
    KtIsIsNotRequest,
    KtIsIsNotResponse,
    FunctionAnalysisRequest,
    FunctionAnalysisResponse,
    OzOtAnalysisRequest,
    OzOtAnalysisResponse,
    EntryGradingRequest,
    EntryGradingResponse,
)
from app.agents.analyst import (
    analyze_five_why,
    analyze_kt_is_is_not,
    analyze_function,
    analyze_oz_ot,
    grade_entry,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyst/five-why", response_model=FiveWhyResponse)
def analyst_five_why(req: FiveWhyRequest):
    """5-Why root-cause analysis (WBS 8.2.1)."""
    try:
        return analyze_five_why(req)
    except Exception:
        logger.exception("five_why failed for project %s", req.project_id)
        raise HTTPException(status_code=502, detail="5-Why 分析失敗，請稍後重試")


@router.post("/analyst/kt-analysis", response_model=KtIsIsNotResponse)
def analyst_kt_analysis(req: KtIsIsNotRequest):
    """KT Is/Is-Not problem analysis (WBS 8.2.2)."""
    try:
        return analyze_kt_is_is_not(req)
    except Exception:
        logger.exception("kt_analysis failed for project %s", req.project_id)
        raise HTTPException(status_code=502, detail="KT 分析失敗，請稍後重試")


@router.post("/analyst/function-analysis", response_model=FunctionAnalysisResponse)
def analyst_function_analysis(req: FunctionAnalysisRequest):
    """TRIZ Function Analysis with DB persistence (WBS 8.2.3)."""
    try:
        result = analyze_function(req)

        # Persist to function_models table
        try:
            from app.core.supabase import get_supabase
            sb = get_supabase()
            payload = {
                "project_id": req.project_id,
                "component_interactions": [
                    ci.model_dump(by_alias=True) for ci in result.component_interactions
                ],
                "sf_diagnosis": result.sf_diagnosis.model_dump(),
                "subsystem_boundary": result.subsystem_boundary,
            }
            sb.table("function_models").upsert(
                payload, on_conflict="project_id"
            ).execute()
            logger.info("function_analysis: persisted to DB for project %s", req.project_id)
        except Exception:
            logger.warning(
                "function_analysis: DB write failed for project %s — returning result without persistence",
                req.project_id,
                exc_info=True,
            )

        return result
    except Exception:
        logger.exception("function_analysis failed for project %s", req.project_id)
        raise HTTPException(status_code=502, detail="功能分析失敗，請稍後重試")


@router.post("/analyst/oz-ot-analysis", response_model=OzOtAnalysisResponse)
def analyst_oz_ot_analysis(req: OzOtAnalysisRequest):
    """TRIZ OZ-OT-Px analysis with DB update (WBS 8.2.4)."""
    try:
        result = analyze_oz_ot(req)

        # Update contradictions table with OZ/OT/Px fields
        try:
            from app.core.supabase import get_supabase
            sb = get_supabase()
            sb.table("contradictions").update({
                "oz_zone": result.oz_zone,
                "ot_time": result.ot_time,
                "px_variable": result.px_variable,
            }).eq("id", req.contradiction_id).execute()
            logger.info(
                "oz_ot_analysis: updated contradiction %s for project %s",
                req.contradiction_id, req.project_id,
            )
        except Exception:
            logger.warning(
                "oz_ot_analysis: DB update failed for contradiction %s — returning result without persistence",
                req.contradiction_id,
                exc_info=True,
            )

        return result
    except Exception:
        logger.exception(
            "oz_ot_analysis failed for project %s contradiction %s",
            req.project_id, req.contradiction_id,
        )
        raise HTTPException(status_code=502, detail="OZ-OT 分析失敗，請稍後重試")


@router.post("/analyst/entry-grading", response_model=EntryGradingResponse)
def analyst_entry_grading(req: EntryGradingRequest):
    """Problem entry-level grading (WBS 8.2.5)."""
    try:
        return grade_entry(req)
    except Exception:
        logger.exception("entry_grading failed for project %s", req.project_id)
        raise HTTPException(status_code=502, detail="入口分級失敗，請稍後重試")
