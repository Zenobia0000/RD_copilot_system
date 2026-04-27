# ==========================================================================
# v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1
# instantiation as a built-in "cross-domain de-anchoring" UX step.
# This file is kept for git history and import safety. Do not add new code.
# ==========================================================================
"""Anti-Anchor Sprint: forced divergence to break path dependency.

SOW Module: 方案管理 (alternatives) — anti-anchor sub-route

DEPRECATED (v3.0): Anti-Anchor is retired. Its functionality has been merged
into the TRIZ solver as a built-in cross-domain de-anchoring step within
TRIZ L1 instantiation. See TRIZ solver for the replacement implementation.
"""

from fastapi import APIRouter

from app.models.schemas import AntiAnchorRequest, AntiAnchorResponse
from app.agents.analyst import generate_anti_anchor

router = APIRouter()


# v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1
# @router.post("/alternatives/anti-anchor", response_model=AntiAnchorResponse)
# def alternatives_anti_anchor(req: AntiAnchorRequest):
#     """Analyst Agent generates 3+ non-typical architecture concepts."""
#     return generate_anti_anchor(req)
