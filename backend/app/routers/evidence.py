"""Evidence Registry: claim registration, verification, and coverage metrics.

WBS 8.4.2: REST endpoints for the Evidence Registry service.
Endpoints:
  - POST /evidence/claims           — register a new claim
  - POST /evidence/claims/{id}/verify — verify / update a claim
  - GET  /evidence/coverage/{project_id} — project coverage stats
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    RegisterClaimRequest,
    RegisterClaimResponse,
    VerifyClaimRequest,
    VerifyClaimResponse,
    CoverageResponse,
)
from app.services.evidence_registry import register_claim, verify_claim, get_coverage

router = APIRouter()


@router.post("/evidence/claims", response_model=RegisterClaimResponse)
async def evidence_register(req: RegisterClaimRequest):
    """Register a new evidence claim for tracking."""
    result = await register_claim(
        project_id=req.project_id,
        claim_text=req.claim_text,
        claim_type=req.claim_type,
        linked_artifact_id=req.linked_artifact_id,
        linked_artifact_type=req.linked_artifact_type,
    )
    return result


@router.post("/evidence/claims/{claim_id}/verify", response_model=VerifyClaimResponse)
async def evidence_verify(claim_id: str, req: VerifyClaimRequest):
    """Verify or update the status of an existing claim."""
    try:
        result = await verify_claim(
            claim_id=claim_id,
            verification_source=req.verification_source,
            new_status=req.new_status,
            confidence_score=req.confidence_score,
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}") from exc
    return result


@router.get("/evidence/coverage/{project_id}", response_model=CoverageResponse)
async def evidence_coverage(project_id: str):
    """Get evidence coverage statistics for a project."""
    return await get_coverage(project_id)
