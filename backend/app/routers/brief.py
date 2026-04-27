"""Task Definition: extraction, mission rewrite, constraint/KPI suggestions, 5W1H.

SOW Module: 任務定義 (definitions)
"""

from fastapi import APIRouter

from app.models.schemas import (
    BriefExtractionRequest,
    BriefExtractionResponse,
    BriefRewriteRequest,
    BriefRewriteResponse,
    ConstraintSuggestRequest,
    ConstraintSuggestResponse,
    ConstraintFeasibilityRequest,
    ConstraintFeasibilityResponse,
    KpiSuggestRequest,
    KpiSuggestResponse,
    TaskDef5W1HRequest,
    TaskDef5W1HResponse,
)
from app.agents.analyst import (
    extract_brief,
    rewrite_mission,
    suggest_constraints,
    check_constraint_feasibility,
    suggest_kpis,
    generate_5w1h,
)

router = APIRouter()


@router.post("/definitions/extract", response_model=BriefExtractionResponse)
def definitions_extract(req: BriefExtractionRequest):
    """Analyst Agent extracts structured brief from raw text."""
    return extract_brief(req)


@router.post("/definitions/rewrite", response_model=BriefRewriteResponse)
async def definitions_rewrite(req: BriefRewriteRequest):
    """AI rewrites mission statement with precise engineering language."""
    return await rewrite_mission(req)


@router.post("/definitions/check-feasibility", response_model=ConstraintFeasibilityResponse)
def definitions_check_feasibility(req: ConstraintFeasibilityRequest):
    """AI checks pairwise feasibility of constraints — identifies conflicts and trade-offs."""
    return check_constraint_feasibility(req)


@router.post("/definitions/suggest-constraints", response_model=ConstraintSuggestResponse)
async def definitions_suggest_constraints(req: ConstraintSuggestRequest):
    """AI suggests missing hard constraints based on mission context."""
    return await suggest_constraints(req)


@router.post("/definitions/suggest-kpis", response_model=KpiSuggestResponse)
async def definitions_suggest_kpis(req: KpiSuggestRequest):
    """AI suggests KPIs based on mission and constraints."""
    return await suggest_kpis(req)


@router.post("/definitions/generate-5w1h", response_model=TaskDef5W1HResponse)
async def definitions_generate_5w1h(req: TaskDef5W1HRequest):
    """AI generates 5W1H task definition from mission context."""
    return await generate_5w1h(req)
