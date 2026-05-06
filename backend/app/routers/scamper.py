"""SCAMPER: 7-action module transformation per subsystem.

SOW Module: SCAMPER (scamper)
SOW Endpoints:
  - POST /scamper/perform                                ← 7-action transform (implemented)
  - POST /scamper/subsystem-suggestions                  ← AI suggest subsystems (implemented)
  - POST /scamper/engineering-spec-drafts                ← concept pack → eng spec drafts (wrapper, implemented)
  - POST /scamper/engineering-spec-drafts/step1-expand   ← split step 1 (implemented)
  - POST /scamper/engineering-spec-drafts/step2-generate ← split step 2 (implemented)
  - POST /scamper/engineering-spec-drafts/step3-strengthen ← split step 3 (implemented)
  - POST /scamper/feedback-contradictions                ← Feed new contradictions back (stub)
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ScamperRequest,
    ScamperResponse,
    SubsystemSuggestRequest,
    SubsystemSuggestResponse,
    EngineeringSpecDraftResponse,
    EngSpecStep1Response,
    EngSpecStep2Request,
    EngSpecStep2Response,
    EngSpecStep3Request,
    EngSpecStep3Response,
    ScamperFeedbackRequest,
    ScamperFeedbackResponse,
    SpatialOverlayRequest,
    SpatialOverlayResponse,
)
from app.agents.triz_solver import (
    scamper_transform,
    suggest_subsystems,
    generate_engineering_spec_drafts,
    eng_spec_step1_expand,
    eng_spec_step2_generate,
    eng_spec_step3_strengthen,
    IncompleteLLMResponseError,
)
from app.agents.scamper_feedback import process_scamper_feedback
from app.services.spatial_validator import discover_package, apply_overlay

router = APIRouter()


@router.post("/scamper/perform", response_model=ScamperResponse)
def scamper_perform(req: ScamperRequest):
    """TRIZ Solver Agent applies SCAMPER 7-action transformation."""
    return scamper_transform(req)


@router.post("/scamper/subsystem-suggestions", response_model=SubsystemSuggestResponse)
def scamper_subsystem_suggestions(req: SubsystemSuggestRequest):
    """AI suggests subsystems suitable for SCAMPER analysis.

    Raises HTTP 502 with a structured body when the LLM cannot produce a
    complete 6-dim interface contract even after one targeted retry. The FE
    should surface this to RD as "LLM output incomplete, please retry" and
    log the violations for prompt tuning. This is intentionally fail-loud —
    silent fallback to partial data was the root cause of the
    "interface contracts disappearing" class of bugs.
    """
    try:
        return suggest_subsystems(req)
    except IncompleteLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=exc.to_dict()) from exc


@router.post("/scamper/engineering-spec-drafts", response_model=EngineeringSpecDraftResponse)
def scamper_engineering_spec_drafts(req: SubsystemSuggestRequest):
    """3-step pipeline: Concept Architecture Pack → detailed Engineering Spec Drafts.

    Requires ``req.concept_pack`` to be populated (i.e. the user must have
    generated a Concept Architecture Pack first). Returns per-subsystem spec
    drafts with full provenance (DraftValue) and a verification checklist.

    Raises HTTP 422 when concept_pack is missing.
    Raises HTTP 502 when the LLM cannot produce complete 6-dim contracts.
    """
    if req.concept_pack is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "missing_concept_pack",
                "message": (
                    "engineering-spec-drafts requires concept_pack to be set. "
                    "Generate a Concept Architecture Pack first."
                ),
            },
        )
    try:
        return generate_engineering_spec_drafts(req)
    except IncompleteLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=exc.to_dict()) from exc


# ── Split Engineering-Spec Pipeline Endpoints ────────────────────────────


@router.post(
    "/scamper/engineering-spec-drafts/step1-expand",
    response_model=EngSpecStep1Response,
)
def scamper_eng_spec_step1(req: SubsystemSuggestRequest):
    """Step 1: Expand concept architecture into 3-level subsystem hierarchy.

    Requires ``req.concept_pack`` to be populated.
    Raises HTTP 422 when concept_pack is missing.
    Raises HTTP 502 when the LLM cannot produce complete 6-dim contracts.
    """
    if req.concept_pack is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "missing_concept_pack",
                "message": (
                    "step1-expand requires concept_pack to be set. "
                    "Generate a Concept Architecture Pack first."
                ),
            },
        )
    try:
        return eng_spec_step1_expand(req)
    except IncompleteLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=exc.to_dict()) from exc


@router.post(
    "/scamper/engineering-spec-drafts/step2-generate",
    response_model=EngSpecStep2Response,
)
def scamper_eng_spec_step2(req: EngSpecStep2Request):
    """Step 2: Generate engineering spec drafts for each subsystem."""
    return eng_spec_step2_generate(req)


@router.post(
    "/scamper/engineering-spec-drafts/step3-strengthen",
    response_model=EngSpecStep3Response,
)
def scamper_eng_spec_step3(req: EngSpecStep3Request):
    """Step 3: Strengthen sources and upgrade confidence levels."""
    return eng_spec_step3_strengthen(req)


@router.post("/scamper/spatial-overlay", response_model=SpatialOverlayResponse)
def scamper_spatial_overlay(req: SpatialOverlayRequest):
    """Apply an OPTIONAL what-if overlay to a previously generated subsystem
    tree. Stateless: caller passes the subsystems back together with the
    hypothetical frame envelope; this endpoint re-runs discovery and reports
    overlay violations. Discovery never requires this — it exists so RD can
    explore trade-offs against multiple imaginary frames after the design has
    been freely proposed.
    """
    pkg = discover_package(req.subsystems)
    overlaid = apply_overlay(pkg, req.overlay or {})
    return SpatialOverlayResponse(package_map=overlaid)


@router.post("/scamper/feedback-contradictions", response_model=ScamperFeedbackResponse)
async def scamper_feedback_contradictions(req: ScamperFeedbackRequest):
    """Feed SCAMPER-generated contradictions back to contradiction management."""
    return await process_scamper_feedback(
        project_id=req.project_id,
        new_contradictions=[c for c in req.new_contradictions],
    )
