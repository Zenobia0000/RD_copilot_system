"""Assumption Management: AI extraction from Socratic Q&A answers.

SOW Module: 假設台帳 (assumptions)
SOW Endpoints:
  - POST /assumptions/extract             ← AI extract (implemented)
  - POST/GET/PUT /assumptions             ← CRUD (handled by Supabase frontend)
  - POST /assumptions/{aid}/disprove      ← TODO v1.1
"""

from fastapi import APIRouter

from app.models.schemas import AssumptionExtractRequest, AssumptionExtractResponse
from app.agents.analyst import extract_assumptions

router = APIRouter()


@router.post("/assumptions/extract", response_model=AssumptionExtractResponse)
def assumptions_extract(req: AssumptionExtractRequest):
    """Analyst Agent extracts assumptions from Socratic question answers."""
    return extract_assumptions(req)
