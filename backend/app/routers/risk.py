"""Risk Analysis: FMEA-style risk identification and scoring.

SOW Module: 風險登錄 (risks)
"""

from fastapi import APIRouter

from app.models.schemas import RiskAnalysisRequest, RiskAnalysisResponse
from app.agents.evaluator import analyze_risk

router = APIRouter()


@router.post("/risks/analyze", response_model=RiskAnalysisResponse)
def risks_analyze(req: RiskAnalysisRequest):
    """Evaluator Agent identifies risks with probability × severity scoring."""
    return analyze_risk(req)
