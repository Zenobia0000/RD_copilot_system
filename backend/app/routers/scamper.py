"""SCAMPER: 7-action module transformation per subsystem.

SOW Module: SCAMPER (scamper)
SOW Endpoints:
  - POST /scamper/perform                                 ← 7-action transform (implemented)
  - POST /scamper/subsystem-suggestions                   ← AI suggest subsystems (implemented)
  - POST /scamper/engineering-spec-drafts                 ← concept pack → eng spec drafts (wrapper, implemented)
  - POST /scamper/engineering-spec-drafts/step1-expand    ← split step 1 — backward-compat wrapper (implemented)
  - POST /scamper/engineering-spec-drafts/step1a-expand   ← step 1a: LLM expansion only (implemented)
  - POST /scamper/engineering-spec-drafts/step1b-enrich   ← step 1b: spatial + package map (implemented)
  - POST /scamper/engineering-spec-drafts/step2-generate  ← split step 2 (implemented)
  - POST /scamper/engineering-spec-drafts/step3-strengthen ← split step 3 (implemented)
  - POST /scamper/feedback-contradictions                 ← Feed new contradictions back (stub)
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ScamperRequest,
    ScamperResponse,
    SubsystemSuggestRequest,
    SubsystemSuggestResponse,
    EngineeringSpecDraftResponse,
    EngSpecStep1Response,
    EngSpecStep1aResponse,
    EngSpecStep1bRequest,
    EngSpecStep1bResponse,
    EngSpecStep2Request,
    EngSpecStep2Response,
    EngSpecStep2ModuleRequest,
    EngSpecStep2ModuleResponse,
    EngSpecStep2SystemRequest,
    EngSpecStep2SystemResponse,
    EngSpecStep3Request,
    EngSpecStep3Response,
    EngSpecPersistRequest,
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
    eng_spec_step1a_expand,
    eng_spec_step1b_enrich,
    eng_spec_step2_generate,
    eng_spec_step2_generate_module,
    eng_spec_step2_generate_system,
    eng_spec_step3_strengthen,
    _persist_engineering_spec_draft_pack,
    fetch_latest_engineering_spec_draft_pack,
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
        result = generate_engineering_spec_drafts(req)
        _persist_engineering_spec_draft_pack(req.project_id, result)
        return result
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
    "/scamper/engineering-spec-drafts/step1a-expand",
    response_model=EngSpecStep1aResponse,
)
def scamper_eng_spec_step1a(req: SubsystemSuggestRequest):
    """Step 1a: LLM Structure Expansion only (≤150 s typical).

    Expands concept architecture into 3-level subsystem hierarchy with
    interface contracts but *without* resolved spatial estimates or
    package map.  This is the first half of the old step1-expand.

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
                    "step1a-expand requires concept_pack to be set. "
                    "Generate a Concept Architecture Pack first."
                ),
            },
        )
    try:
        return eng_spec_step1a_expand(req)
    except IncompleteLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=exc.to_dict()) from exc


@router.post(
    "/scamper/engineering-spec-drafts/step1b-enrich",
    response_model=EngSpecStep1bResponse,
)
def scamper_eng_spec_step1b(req: EngSpecStep1bRequest):
    """Step 1b: Spatial Enrichment + Package Map (≤80 s typical).

    Takes the subsystem tree from step1a (pre-spatial) and resolves
    real-world spatial estimates via web lookup, then discovers the
    package map.  This is the second half of the old step1-expand.
    """
    return eng_spec_step1b_enrich(req)


@router.post(
    "/scamper/engineering-spec-drafts/step2-generate",
    response_model=EngSpecStep2Response,
)
def scamper_eng_spec_step2(req: EngSpecStep2Request):
    """Step 2: Generate engineering spec drafts for each subsystem."""
    _logger = logging.getLogger(__name__)
    try:
        return eng_spec_step2_generate(req)
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Step 2 (spec generation) failed")
        raise HTTPException(
            status_code=502,
            detail=f"Step 2 spec generation failed: {exc}",
        ) from exc


@router.post(
    "/scamper/engineering-spec-drafts/step2-generate-module",
    response_model=EngSpecStep2ModuleResponse,
)
def scamper_eng_spec_step2_module(req: EngSpecStep2ModuleRequest):
    """Step 2 (incremental): Generate specs for ONE module."""
    _logger = logging.getLogger(__name__)
    try:
        return eng_spec_step2_generate_module(req)
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Step 2 module (%s) failed", req.module_name)
        raise HTTPException(
            status_code=502,
            detail=f"Step 2 module spec generation failed ({req.module_name}): {exc}",
        ) from exc


@router.post(
    "/scamper/engineering-spec-drafts/step2-generate-system",
    response_model=EngSpecStep2SystemResponse,
)
def scamper_eng_spec_step2_system(req: EngSpecStep2SystemRequest):
    """Step 2 (incremental): Generate specs for system-level nodes."""
    _logger = logging.getLogger(__name__)
    try:
        return eng_spec_step2_generate_system(req)
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Step 2 system-level spec generation failed")
        raise HTTPException(
            status_code=502,
            detail=f"Step 2 system-level spec generation failed: {exc}",
        ) from exc


@router.post(
    "/scamper/engineering-spec-drafts/step3-strengthen",
    response_model=EngSpecStep3Response,
)
def scamper_eng_spec_step3(req: EngSpecStep3Request):
    """Step 3: Strengthen sources and upgrade confidence levels."""
    _logger = logging.getLogger(__name__)
    try:
        result = eng_spec_step3_strengthen(req)
        # Persist the complete response (subsystem_tree from req, package_map unavailable here)
        full_response = EngineeringSpecDraftResponse(
            drafts=result.drafts,
            subsystem_tree=req.subsystems,
            package_map=None,
        )
        _persist_engineering_spec_draft_pack(req.project_id, full_response)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Step 3 (source strengthening) failed")
        raise HTTPException(
            status_code=502,
            detail=f"Step 3 source strengthening failed: {exc}",
        ) from exc


@router.post(
    "/scamper/engineering-spec-drafts/persist",
    response_model=EngineeringSpecDraftResponse,
)
def scamper_persist_engineering_spec_drafts(req: EngSpecPersistRequest):
    """Persist an engineering-spec draft pack (no LLM call).

    Called by the frontend pipeline after Step 2 when Step 3 is skipped,
    so that the drafts are saved to the DB for later retrieval.
    """
    _logger = logging.getLogger(__name__)
    try:
        full_response = EngineeringSpecDraftResponse(
            drafts=req.drafts,
            subsystem_tree=req.subsystem_tree,
            package_map=req.package_map,
        )
        _persist_engineering_spec_draft_pack(req.project_id, full_response)
        return full_response
    except Exception as exc:
        _logger.exception("Persist engineering spec drafts failed")
        raise HTTPException(
            status_code=502,
            detail=f"Persist engineering spec drafts failed: {exc}",
        ) from exc


@router.get(
    "/scamper/engineering-spec-drafts/{project_id}",
    response_model=EngineeringSpecDraftResponse,
)
def scamper_get_engineering_spec_drafts(project_id: str):
    """Fetch the latest persisted engineering spec draft pack for a project."""
    result = fetch_latest_engineering_spec_draft_pack(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No engineering spec draft pack found")
    return result


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
