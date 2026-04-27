"""CLD Generation: causal loop diagrams from contradictions + assumptions.

SOW Module: 因果迴路 (causal-loops)
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import CldGenerationRequest, CldGenerationResponse
from app.agents.analyst import generate_cld

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/causal-loops/generate", response_model=CldGenerationResponse)
def causal_loops_generate(req: CldGenerationRequest):
    """Analyst Agent generates causal loop diagram with breakpoints."""
    try:
        return generate_cld(req)
    except Exception:
        logger.exception("CLD generation failed for project %s", req.project_id)
        raise HTTPException(status_code=502, detail="CLD 生成失敗，請稍後重試")
