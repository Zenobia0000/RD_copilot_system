"""Subsystem discovery and spatial overlay endpoints.

Migrated from the former SCAMPER router — subsystem discovery and spatial
overlay are methodology-independent and no longer belong under /scamper/.

Routes:
  - POST /subsystems/suggest          — AI-powered subsystem tree discovery
  - POST /subsystems/spatial-overlay   — What-if spatial overlay on subsystem tree
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SubsystemSuggestRequest,
    SubsystemSuggestResponse,
    SpatialOverlayRequest,
    SpatialOverlayResponse,
)
from app.agents.triz_solver import (
    suggest_subsystems,
    IncompleteLLMResponseError,
)
from app.services.spatial_validator import discover_package, apply_overlay

router = APIRouter()


@router.post("/subsystems/suggest", response_model=SubsystemSuggestResponse)
def subsystem_suggestions(req: SubsystemSuggestRequest):
    """AI suggests subsystems suitable for analysis.

    Raises HTTP 502 with a structured body when the LLM cannot produce a
    complete 6-dim interface contract even after one targeted retry. The FE
    should surface this to RD as "LLM output incomplete, please retry" and
    log the violations for prompt tuning.
    """
    try:
        return suggest_subsystems(req)
    except IncompleteLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=exc.to_dict()) from exc


@router.post("/subsystems/spatial-overlay", response_model=SpatialOverlayResponse)
def spatial_overlay(req: SpatialOverlayRequest):
    """Apply an OPTIONAL what-if overlay to a previously generated subsystem
    tree. Stateless: caller passes the subsystems back together with the
    hypothetical frame envelope; this endpoint re-runs discovery and reports
    overlay violations.
    """
    pkg = discover_package(req.subsystems)
    overlaid = apply_overlay(pkg, req.overlay or {})
    return SpatialOverlayResponse(package_map=overlaid)
