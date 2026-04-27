"""Pre-CAD Review: AI-assisted 5D scoring and analysis.

SOW Module: Pre-CAD 審查 (pre-cad-reviews)
SOW Endpoints:
  - POST /pre-cad-reviews/{rid}/ai-analyze  ← AI analyze (implemented)
  - POST/GET /pre-cad-reviews               ← CRUD (handled by Supabase frontend)
"""

from fastapi import APIRouter

from app.models.schemas import PreCadAnalyzeRequest, PreCadAnalyzeResponse
from app.agents.evaluator import analyze_pre_cad

router = APIRouter()


@router.post("/pre-cad-reviews/{rid}/ai-analyze", response_model=PreCadAnalyzeResponse)
def pre_cad_ai_analyze(rid: str, req: PreCadAnalyzeRequest):
    """Evaluator Agent performs 5D Pre-CAD analysis with scoring."""
    return analyze_pre_cad(req)
