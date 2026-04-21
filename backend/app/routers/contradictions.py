"""Contradiction Management: formalization + TC→multi-PC decomposition + SF derivation.

SOW Module: 矛盾管理 (contradictions)
SOW Endpoints:
  - POST /contradictions/{cid}/formalize   ← AI formalize (TC-only, ADR-007)
  - POST /contradictions/{cid}/decompose   ← TC → multi-PC (L2 WBS task 3.4)
  - POST /contradictions/{cid}/derive-sf   ← TC → child SF (Plan B hierarchical tree)
  - POST/GET/PUT /contradictions            ← CRUD (handled by Supabase frontend)
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ContradictionFormalizeRequest,
    ContradictionFormalizeResponse,
    ContradictionDecomposeRequest,
    ContradictionDecomposeResponse,
    ContradictionDeriveSFRequest,
    ContradictionDeriveSFResponse,
)
from app.agents.analyst import formalize_contradiction, decompose_tc_to_pcs, derive_su_field_from_tc

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/contradictions/{cid}/formalize", response_model=ContradictionFormalizeResponse)
def contradictions_formalize(cid: str, req: ContradictionFormalizeRequest):
    """Analyst Agent formalizes natural-language contradiction into TRIZ sentence."""
    return formalize_contradiction(req)


@router.post("/contradictions/{cid}/decompose", response_model=ContradictionDecomposeResponse)
def contradictions_decompose(cid: str, req: ContradictionDecomposeRequest):
    """TC → multi-PC decomposition. Triggered automatically after AI TC
    identification, per docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §3.4.
    """
    try:
        return decompose_tc_to_pcs(req)
    except Exception:
        logger.exception(
            "PC decomposition failed for project %s contradiction %s",
            req.project_id, cid,
        )
        raise HTTPException(status_code=502, detail="PC 分解失敗，請稍後重試")


@router.post("/contradictions/{cid}/derive-sf", response_model=ContradictionDeriveSFResponse)
def contradictions_derive_sf(cid: str, req: ContradictionDeriveSFRequest):
    """Derive a child Su-Field model from a parent TC (Plan B hierarchical tree).

    Wraps the existing derive_su_field_from_tc agent function into a REST
    endpoint so the frontend can call it alongside /decompose in parallel.
    """
    try:
        result = derive_su_field_from_tc(
            improving_param=req.improving_param,
            worsening_param=req.worsening_param,
            engineering_statement=req.engineering_statement,
            natural_description=req.natural_description or None,
        )
        if result is None:
            return ContradictionDeriveSFResponse(derived=False)
        return ContradictionDeriveSFResponse(
            derived=True,
            sf_substance_1=result.S1 or None,
            sf_substance_2=result.S2 or None,
            sf_field=result.F or None,
            sf_interaction=result.state if result.state != "unknown" else None,
            sf_completeness=None,  # derive_su_field_from_tc doesn't return completeness
        )
    except Exception:
        logger.exception(
            "SF derivation failed for project %s contradiction %s",
            req.project_id, cid,
        )
        raise HTTPException(status_code=502, detail="SF 推導失敗，請稍後重試")
