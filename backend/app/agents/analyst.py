"""Analyst Agent — brief extraction, Socratic Q&A, CLD, anti-anchor.

Ref: AI_Agent_Architecture.md §1.1 Analyst Agent
"""

import json
import logging
import time

logger = logging.getLogger(__name__)

from app.agents.base import call_llm_json, web_search_with_llm
from pydantic import ValidationError

from app.prompts.analyst import (
    ANALYST_SYSTEM,
    BRIEF_EXTRACTION,
    MISSION_REWRITE,
    CONSTRAINT_SUGGESTION,
    CONSTRAINT_FEASIBILITY,
    KPI_SUGGESTION,
    TASK_DEF_5W1H,
    SOCRATIC_QUESTIONS,
    SOCRATIC_FOLLOW_UP,
    SOCRATIC_BRIEF_IMPACT,
    SOCRATIC_AUTO_TAG,
    CLD_GENERATION,
    ANTI_ANCHOR_GENERATION,
    SOCRATIC_INSIGHT_EXTRACTION,
    CONTRADICTION_FORMALIZATION,
    SU_FIELD_DERIVATION_FROM_TC,
    ASSUMPTION_EXTRACTION,
    UNKNOWN_FACTOR_DISCOVERY,
    TC_TO_MULTI_PC_DECOMPOSITION,
    PURPOSE_CONTRADICTION,
    PURPOSE_CLD,
    PURPOSE_ANTI_ANCHOR,
    PURPOSE_DECOMPOSITION,
    FIVE_WHY_ANALYSIS,
    KT_IS_IS_NOT,
    FUNCTION_ANALYSIS,
    OZ_OT_ANALYSIS,
    ENTRY_GRADING,
)
from app.agents.triz_critic import should_trigger_pc_decomposition
from app.tools.triz_kb import (
    load_39_parameters,
    load_40_principles,
    load_separation_principles,
    get_param_name,
)
from app.tools.separation_principles import build_separation_principle_id_context
from app.models.schemas import (
    BriefExtractionRequest,
    BriefExtractionResponse,
    BriefRewriteRequest,
    BriefRewriteResponse,
    ConstraintSuggestRequest,
    ConstraintSuggestResponse,
    ConstraintFeasibilityRequest,
    ConstraintFeasibilityResponse,
    KpiSuggestRequest,
    KpiSuggestResponse,
    TaskDef5W1HRequest,
    TaskDef5W1HResponse,
    EvidenceReference,
    SocraticRequest,
    SocraticResponse,
    SocraticFollowUpRequest,
    SocraticFollowUpResponse,
    SocraticBriefImpactRequest,
    SocraticBriefImpactResponse,
    SocraticAutoTagRequest,
    SocraticAutoTagResponse,
    CldGenerationRequest,
    CldGenerationResponse,
    AntiAnchorRequest,
    AntiAnchorResponse,
    ContradictionFormalizeRequest,
    ContradictionFormalizeResponse,
    SuFieldModel,
    ContradictionDecomposeRequest,
    ContradictionDecomposeResponse,
    DecomposedPC,
    AssumptionExtractRequest,
    AssumptionExtractResponse,
    UnknownFactorDiscoverRequest,
    UnknownFactorDiscoverResponse,
    FiveWhyRequest,
    FiveWhyResponse,
    KtIsIsNotRequest,
    KtIsIsNotResponse,
    FunctionAnalysisRequest,
    FunctionAnalysisResponse,
    OzOtAnalysisRequest,
    OzOtAnalysisResponse,
    EntryGradingRequest,
    EntryGradingResponse,
)
from app.services.evidence_retrieval import (
    retrieve_constraint_evidence,
    retrieve_kpi_evidence,
    retrieve_5w1h_evidence,
    retrieve_mission_rewrite_evidence,
    EvidenceReference as ServiceEvidenceRef,
)


def _convert_refs(service_refs: list[ServiceEvidenceRef]) -> list[EvidenceReference]:
    """Convert service-layer evidence refs to Pydantic schema refs."""
    return [
        EvidenceReference(
            ref_id=r.ref_id,
            ref_type=r.ref_type,
            title=r.title,
            source=r.source,
            url=r.url,
            snippet=r.snippet,
        )
        for r in service_refs
    ]


def extract_brief(req: BriefExtractionRequest) -> BriefExtractionResponse:
    prompt = BRIEF_EXTRACTION.format(raw_text=req.raw_text or "(無文字，請根據 file_urls 推斷)")
    raw = call_llm_json(ANALYST_SYSTEM, prompt, max_tokens=2048)
    data = json.loads(raw)
    # Only keep the 4 expected keys to avoid Pydantic validation errors
    filtered = {
        "constraints": data.get("constraints", []),
        "kpis": data.get("kpis", []),
        "assumptions": data.get("assumptions", []),
        "feasibility_warnings": data.get("feasibility_warnings", []),
    }
    return BriefExtractionResponse(**filtered)


def check_constraint_feasibility(req: ConstraintFeasibilityRequest) -> ConstraintFeasibilityResponse:
    if len(req.constraints) < 2:
        return ConstraintFeasibilityResponse(status="pass", conflicts=[])
    prompt = CONSTRAINT_FEASIBILITY.format(
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints),
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return ConstraintFeasibilityResponse(**data)


async def rewrite_mission(req: BriefRewriteRequest) -> BriefRewriteResponse:
    # Retrieve evidence for grounding
    evidence = await retrieve_mission_rewrite_evidence(req.mission)

    prompt = MISSION_REWRITE.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        evidence_context=evidence.prompt_context,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return BriefRewriteResponse(
        **data,
        evidence_references=_convert_refs(evidence.references),
    )


async def suggest_constraints(req: ConstraintSuggestRequest) -> ConstraintSuggestResponse:
    # Retrieve evidence — safety standards, regulations, physical limits
    evidence = await retrieve_constraint_evidence(
        req.mission,
        req.existing_constraints,
    )

    prompt = CONSTRAINT_SUGGESTION.format(
        mission=req.mission,
        existing_constraints="\n".join(f"- {c}" for c in req.existing_constraints) or "（尚無）",
        evidence_context=evidence.prompt_context,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return ConstraintSuggestResponse(
        **data,
        evidence_references=_convert_refs(evidence.references),
    )


async def suggest_kpis(req: KpiSuggestRequest) -> KpiSuggestResponse:
    # Retrieve evidence — benchmarks, test standards
    evidence = await retrieve_kpi_evidence(
        req.mission,
        req.constraints,
    )

    prompt = KPI_SUGGESTION.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        existing_kpis="\n".join(f"- {k}" for k in req.existing_kpis) or "（尚無）",
        evidence_context=evidence.prompt_context,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return KpiSuggestResponse(
        **data,
        evidence_references=_convert_refs(evidence.references),
    )


async def generate_5w1h(req: TaskDef5W1HRequest) -> TaskDef5W1HResponse:
    evidence = await retrieve_5w1h_evidence(req.mission)

    prompt = TASK_DEF_5W1H.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        evidence_context=evidence.prompt_context,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return TaskDef5W1HResponse(
        **data,
        evidence_references=_convert_refs(evidence.references),
    )


_VALID_CATEGORIES = {
    "clarification", "assumption", "consequence",
    "counter", "origin", "action", "reframing",
}


def generate_socratic_questions(req: SocraticRequest) -> SocraticResponse:
    prompt = SOCRATIC_QUESTIONS.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints),
        existing_questions="\n".join(f"- {q}" for q in req.existing_questions),
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    # Prompt uses dict keyed by category → convert to list
    q_raw = data.get("questions", {})
    if isinstance(q_raw, dict):
        questions_list = [
            {"type_class": cat, **v}
            for cat, v in q_raw.items()
            if cat in _VALID_CATEGORIES and isinstance(v, dict)
        ]
        data["questions"] = questions_list
    return SocraticResponse(**data)


def analyze_socratic_depth(req: SocraticFollowUpRequest) -> SocraticFollowUpResponse:
    """Analyze answer depth and generate targeted follow-up questions."""
    qa_text = "\n".join(
        f"[{q.category}] Q: {q.question}\nA: {q.answer}" for q in req.answered_questions
    )
    prompt = SOCRATIC_FOLLOW_UP.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints),
        answered_questions=qa_text,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    data.setdefault("follow_ups", [])
    data.setdefault("depth_sufficient", len(data["follow_ups"]) == 0)
    return SocraticFollowUpResponse(**data)


def evaluate_brief_impact(req: SocraticBriefImpactRequest) -> SocraticBriefImpactResponse:
    """Evaluate which Socratic questions are affected by a Brief change."""
    q_text = "\n".join(
        f"- id={q.id} [{q.category}] Q: {q.text}" + (f" A: {q.answer}" if q.answer else "")
        for q in req.existing_questions
    )
    prompt = SOCRATIC_BRIEF_IMPACT.format(
        new_mission=req.new_mission,
        new_constraints="\n".join(f"- {c}" for c in req.new_constraints),
        existing_questions=q_text,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    data.setdefault("affected", [])
    data.setdefault("unaffected_ids", [])
    return SocraticBriefImpactResponse(**data)


def auto_tag_socratic(req: SocraticAutoTagRequest) -> SocraticAutoTagResponse:
    """Analyse untagged Socratic Q&A for hidden assumptions/contradictions."""
    untagged_text = "\n".join(
        f"[{q.id}] Q ({q.category}): {q.text}\nA: {q.answer}"
        for q in req.untagged_questions
        if q.answer
    ) or "（無未標記的已回答問題）"
    prompt = SOCRATIC_AUTO_TAG.format(
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        existing_assumptions="\n".join(f"- {a}" for a in req.existing_assumptions) or "（尚無）",
        existing_contradictions="\n".join(f"- {c}" for c in req.existing_contradictions) or "（尚無）",
        untagged_questions=untagged_text,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return SocraticAutoTagResponse(**data)


def _extract_socratic_insights(socraticAnswers: list[str], purpose: str) -> str:
    """Extract Socratic Q&A filtered by a caller-defined purpose string."""
    if not socraticAnswers:
        return "No additional insights available."

    prompt = SOCRATIC_INSIGHT_EXTRACTION.format(
        socraticAnswers="\n".join(f"- {a}" for a in socraticAnswers),
        purpose=purpose,
    )

    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    insights = data.get("insights", [])

    if not insights:
        return "No additional insights available."

    return "\n".join(f"- {ins}" for ins in insights)


def generate_cld(req: CldGenerationRequest) -> CldGenerationResponse:
    # Step 1: Refine Socratic Insights
    socratic_insights = _extract_socratic_insights(
        getattr(req, "socraticAnswers", None) or [],
        purpose=PURPOSE_CLD,
    )

    # Step 2: Assemble prompt
    prompt = CLD_GENERATION.format(
        contradictions="\n".join(f"- {c}" for c in req.contradictions),
        assumptions="\n".join(f"- {a}" for a in req.assumptions),
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        socratic_insights=socratic_insights,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return CldGenerationResponse.model_validate(data)


def formalize_contradiction(req: ContradictionFormalizeRequest) -> ContradictionFormalizeResponse:
    # Step 1: Refine Socratic Insights
    socratic_insights = _extract_socratic_insights(
        getattr(req, "socraticAnswers", None) or [],
        purpose=PURPOSE_CONTRADICTION,
    )

    # Step 2: Assemble prompt
    prompt = CONTRADICTION_FORMALIZATION.format(
        natural_description=req.natural_description,
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        socratic_insights=socratic_insights,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)

    # ADR-007: Explore stage always emits TC. Coerce any non-TC to null.
    raw_type = data.get("type")
    ip = data.get("improving_param")
    wp = data.get("worsening_param")

    if raw_type != "TC" and raw_type is not None:
        logger.info(
            "Formalize: LLM returned type=%r — ADR-007 coerces to TC-only; setting type=null",
            raw_type,
        )
        data["type"] = None
        data["improving_param"] = None
        data["worsening_param"] = None
        if not data.get("rationale"):
            data["rationale"] = (
                f"LLM classified as '{raw_type}' but Explore stage requires TC "
                "(ADR-007). PC/SF are derived automatically from TC. "
                "Please refine the description to surface a measurable trade-off."
            )
    elif raw_type == "TC":
        tc_params_valid = (
            isinstance(ip, int) and isinstance(wp, int) and 1 <= ip <= 39 and 1 <= wp <= 39
        )
        if not tc_params_valid:
            logger.warning(
                "Formalize: type=TC but params invalid (ip=%s, wp=%s) — coercing to type=null",
                ip, wp,
            )
            data["type"] = None
            data["improving_param"] = None
            data["worsening_param"] = None
            if not data.get("rationale"):
                data["rationale"] = (
                    "LLM returned type=TC but could not supply two valid TRIZ 39 "
                    "parameters (1–39). Please refine the contradiction description "
                    "or answer Socratic follow-ups to surface a measurable trade-off."
                )

    return ContradictionFormalizeResponse(**data)


def derive_su_field_from_tc(
    improving_param: int,
    worsening_param: int,
    engineering_statement: str,
    natural_description: str | None = None,
) -> SuFieldModel | None:
    """Derive a Su-Field model from an already-identified TC (ADR-007).

    Called at the Create stage (inside solve_triz_layered) when the
    request arrives without SF fields. Returns None on LLM/parse failure
    or when the TC is too abstract to yield a meaningful S1/S2/F triple —
    L3 then degrades gracefully (see ADR-007 §Consequences).
    """
    try:
        prompt = SU_FIELD_DERIVATION_FROM_TC.format(
            engineering_statement=engineering_statement or "",
            improving_param=improving_param,
            improving_name=get_param_name(improving_param) or "",
            worsening_param=worsening_param,
            worsening_name=get_param_name(worsening_param) or "",
            natural_description=natural_description or engineering_statement or "",
        )
        raw = call_llm_json(ANALYST_SYSTEM, prompt, max_tokens=512)
        data = json.loads(raw)
        model = SuFieldModel(
            S1=str(data.get("S1") or "").strip(),
            S2=str(data.get("S2") or "").strip(),
            F=str(data.get("F") or "").strip(),
            state=data.get("state") or "unknown",
        )
        # If everything is empty, treat as "no meaningful derivation"
        if not (model.S1 or model.S2 or model.F):
            logger.info(
                "derive_su_field_from_tc: empty Su-Field (ip=%s, wp=%s) — L3 will degrade",
                improving_param, worsening_param,
            )
            return None
        return model
    except Exception as exc:  # noqa: BLE001 — failure must not break L1/L2
        logger.warning(
            "derive_su_field_from_tc failed (ip=%s, wp=%s): %s",
            improving_param, worsening_param, exc,
        )
        return None


def extract_assumptions(req: AssumptionExtractRequest) -> AssumptionExtractResponse:
    qa_text = "\n".join(
        f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}"
        for qa in req.questions_and_answers
    ) or "（無問答紀錄）"
    prompt = ASSUMPTION_EXTRACTION.format(
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        existing_assumptions="\n".join(f"- {a}" for a in req.existing_assumptions) or "（尚無）",
        questions_and_answers=qa_text,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return AssumptionExtractResponse(**data)


def _flatten_to_str(value) -> str:
    """When LLM returns a dict, it merges them into a string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " | ".join(f"{k.replace('_', ' ').capitalize()}: {v}" 
                          for k, v in value.items())
    return str(value)


def generate_anti_anchor(req: AntiAnchorRequest) -> AntiAnchorResponse:
    # NOTE (§9.4): callers should pre-filter contradictions to leaf nodes
    # using get_contradiction_leaves() before building `current_constraints`
    # / `existing_alternatives`.  This avoids duplicate parent+child entries
    # when a TC has been decomposed into child PCs.
    socratic_insights = _extract_socratic_insights(
        getattr(req, "socraticAnswers", None) or [],
        purpose=PURPOSE_ANTI_ANCHOR,
    )
    prompt = ANTI_ANCHOR_GENERATION.format(
        mission=req.mission,
        current_constraints="\n".join(f"- {c}" for c in req.current_constraints),
        existing_alternatives="\n".join(f"- {a}" for a in req.existing_alternatives),
        socratic_insights=socratic_insights,
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    # Even if the prompt requires a string, the LLM may still return a dict.
    for alt in data.get("alternatives", []):
        for key in ("mechanism", "why_unconventional", 
                     "potential_advantage", "cross_domain_source"):
            if key in alt and not isinstance(alt[key], str):
                alt[key] = _flatten_to_str(alt[key])
    
    return AntiAnchorResponse(**data)


def decompose_tc_to_pcs(req: ContradictionDecomposeRequest) -> ContradictionDecomposeResponse:
    """TC → multi-PC decomposition at the Explore stage.

    Flow (per docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §3.3):
      1. Run L1 critic (should_trigger_pc_decomposition). If it says "no",
         return immediately with triggered=False and empty decomposed_pcs.
      2. Extract Socratic insights via the existing _extract_socratic_insights helper.
      3. Load KB context (39 params + 40 principles + separation principle ids).
      4. Format TC_TO_MULTI_PC_DECOMPOSITION prompt.
      5. call_llm_json → parse JSON.
      6. Validate (dedupe on derived_parameter, each separation_principle_id
         in canonical 16-item set via DecomposedPC validator — Pydantic auto-rejects).
      7. Return ContradictionDecomposeResponse. Wrap EVERYTHING in try/except —
         on any failure return triggered=True, decomposed_pcs=[], reasoning=error.
    """
    logger.info(
        "decompose_tc_to_pcs: project=%s parent=%s severity=%s",
        req.project_id, req.parent_contradiction_id, req.severity,
    )

    # Step 1: L1 critic decides whether drill-down is warranted.
    # Build a minimal ContradictionFormalizeResponse stub from the request —
    # the critic only reads engineering_statement / improving_param / worsening_param.
    # Use model_construct() to bypass unrelated required-field validation.
    tc_stub = ContradictionFormalizeResponse.model_construct(
        engineering_statement=req.engineering_statement,
        improving_param=req.improving_param,
        worsening_param=req.worsening_param,
        type="TC",
    )

    try:
        triggered, reason = should_trigger_pc_decomposition(
            tc_response=tc_stub,
            severity=req.severity,
            natural_description=req.engineering_statement,
            candidate_principles=req.candidate_principles,
            rd_manual=req.rd_manual,
            enable_llm_critic=False,  # cheaper: rule layer only inside decomposition
        )
    except Exception as exc:  # noqa: BLE001 — error isolation per WBS §3.3
        logger.exception("decompose_tc_to_pcs: L1 critic failed project=%s parent=%s", req.project_id, req.parent_contradiction_id)
        return ContradictionDecomposeResponse(
            triggered=True,
            trigger_reason=f"critic failed: {exc}",
            decomposed_pcs=[],
            reasoning=f"Decomposition failed: critic error {exc}",
        )

    logger.info("decompose_tc_to_pcs: critic triggered=%s reason=%s", triggered, reason)

    if not triggered:
        return ContradictionDecomposeResponse(
            triggered=False,
            trigger_reason=reason,
            decomposed_pcs=[],
            reasoning="L1 critic judged drill-down unnecessary.",
        )

    # Step 2-6: run decomposition with error isolation
    try:
        socratic_insights = _extract_socratic_insights(
            getattr(req, "socraticAnswers", None) or [],
            purpose=PURPOSE_DECOMPOSITION,
        )

        prompt = TC_TO_MULTI_PC_DECOMPOSITION.format(
            engineering_statement=req.engineering_statement,
            improving_param=req.improving_param or 0,
            improving_name=get_param_name(req.improving_param) if req.improving_param else "",
            worsening_param=req.worsening_param or 0,
            worsening_name=get_param_name(req.worsening_param) if req.worsening_param else "",
            mission=req.mission or "（未提供）",
            constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
            kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
            clarified_insights=socratic_insights,
            params_context=load_39_parameters(),
            principles_context=load_40_principles(),
            separation_principles_context=build_separation_principle_id_context(),
        )

        t0 = time.monotonic()
        raw = call_llm_json(ANALYST_SYSTEM, prompt)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info("decompose_tc_to_pcs: LLM call elapsed=%dms", elapsed_ms)
        data = json.loads(raw)

        raw_pcs = data.get("decomposed_pcs", []) or []
        llm_reasoning = str(data.get("reasoning", "") or "")

        # Validate + dedupe
        seen_params: set[str] = set()
        validated_pcs: list[DecomposedPC] = []
        for idx, item in enumerate(raw_pcs):
            if not isinstance(item, dict):
                logger.warning("Skipping non-dict PC at index %d: %r", idx, item)
                continue
            derived = str(item.get("derived_parameter", "")).strip()
            if derived and derived in seen_params:
                logger.warning(
                    "Duplicate derived_parameter '%s' at index %d — dropping", derived, idx
                )
                continue
            try:
                pc = DecomposedPC(**item)
            except ValidationError as ve:
                logger.warning(
                    "Rejecting invalid PC at index %d (derived=%r): %s",
                    idx, derived, ve.errors(),
                )
                continue
            seen_params.add(pc.derived_parameter)
            validated_pcs.append(pc)

        response = ContradictionDecomposeResponse(
            triggered=True,
            trigger_reason=reason,
            decomposed_pcs=validated_pcs,
            reasoning=llm_reasoning,
        )
        logger.info(
            "decompose_tc_to_pcs: result triggered=%s pcs=%d reasoning=%.100s",
            response.triggered, len(response.decomposed_pcs), response.reasoning,
        )
        return response
    except Exception as exc:  # noqa: BLE001 — error isolation per WBS §3.3
        logger.exception("decompose_tc_to_pcs: failed project=%s parent=%s", req.project_id, req.parent_contradiction_id)
        return ContradictionDecomposeResponse(
            triggered=True,
            trigger_reason=reason,
            decomposed_pcs=[],
            reasoning=f"Decomposition failed: {exc}",
        )


def analyze_five_why(req: FiveWhyRequest) -> FiveWhyResponse:
    """Perform 5-Why root-cause analysis on a problem statement."""
    logger.info("analyze_five_why: project=%s", req.project_id)
    prompt = FIVE_WHY_ANALYSIS.format(
        problem_statement=req.problem_statement,
        context=req.context or "（未提供）",
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return FiveWhyResponse(**data)


def analyze_kt_is_is_not(req: KtIsIsNotRequest) -> KtIsIsNotResponse:
    """Perform KT Problem Analysis Is/Is-Not matrix."""
    logger.info("analyze_kt_is_is_not: project=%s", req.project_id)
    prompt = KT_IS_IS_NOT.format(
        problem_statement=req.problem_statement,
        known_facts="\n".join(f"- {f}" for f in req.known_facts) or "（尚無）",
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return KtIsIsNotResponse(**data)


def analyze_function(req: FunctionAnalysisRequest) -> FunctionAnalysisResponse:
    """Perform TRIZ Function Analysis (FA) with component interactions and SF diagnosis."""
    logger.info("analyze_function: project=%s components=%d", req.project_id, len(req.components))
    prompt = FUNCTION_ANALYSIS.format(
        system_description=req.system_description,
        components="\n".join(f"- {c}" for c in req.components),
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return FunctionAnalysisResponse(**data)


def analyze_oz_ot(req: OzOtAnalysisRequest) -> OzOtAnalysisResponse:
    """Perform TRIZ OZ-OT-Px analysis on a Technical Contradiction."""
    logger.info(
        "analyze_oz_ot: project=%s contradiction=%s",
        req.project_id, req.contradiction_id,
    )
    prompt = OZ_OT_ANALYSIS.format(
        tc_description=req.tc_description,
        improving_param=req.improving_param or "（未提供）",
        worsening_param=req.worsening_param or "（未提供）",
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return OzOtAnalysisResponse(**data)


def grade_entry(req: EntryGradingRequest) -> EntryGradingResponse:
    """Grade problem entry level (A/B/C) based on complexity and data quality."""
    logger.info("grade_entry: project=%s", req.project_id)
    prompt = ENTRY_GRADING.format(
        problem_description=req.problem_description,
        available_data=json.dumps(req.available_data, ensure_ascii=False, default=str)
        if req.available_data else "（無可用資料）",
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return EntryGradingResponse(**data)


def discover_unknown_factors(req: UnknownFactorDiscoverRequest) -> UnknownFactorDiscoverResponse:
    """Discover unknown factors from project context gaps."""
    prompt = UNKNOWN_FACTOR_DISCOVERY.format(
        mission=req.mission or "（未提供）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（尚無）",
        contradictions="\n".join(f"- {c}" for c in req.contradictions) or "（尚無）",
        existing_assumptions="\n".join(f"- {a}" for a in req.existing_assumptions) or "（尚無）",
        existing_unknowns="\n".join(f"- {u}" for u in req.existing_unknowns) or "（尚無）",
    )
    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw)
    return UnknownFactorDiscoverResponse(**data)
