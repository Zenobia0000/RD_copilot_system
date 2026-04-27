"""Step 5a-6 — Convergence Scan: secondary contradiction detection + architecture health."""

from fastapi import APIRouter

from app.models.schemas import ConvergenceScanRequest, ConvergenceScanResponse
from app.agents.evaluator import scan_convergence

router = APIRouter()


@router.post("/convergence/scan", response_model=ConvergenceScanResponse)
def convergence_do_scan(req: ConvergenceScanRequest):
    """Evaluator Agent scans for secondary contradictions and architecture health."""
    return scan_convergence(req)
