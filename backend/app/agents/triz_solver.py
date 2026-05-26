"""TRIZ Solver Agent — matrix lookup + principle instantiation + SCAMPER.

Ref: AI_Agent_Architecture.md §1.1 TRIZ Solver Agent + §6.2 triz_solver_agent tools
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field as dc_field
from typing import Literal

logger = logging.getLogger(__name__)

from app.agents.base import call_llm_json
from app.core.config import settings
from app.prompts.triz_solver import (
    TRIZ_SOLVER_SYSTEM,
    TRIZ_TC_INSTANTIATION,
    TRIZ_PC_INSTANTIATION,
    TRIZ_PC_INSTANTIATION_WITH_HINT,
    SUFIELD_ANALYSIS,
    SCAMPER_TRANSFORM,
    SUBSYSTEM_SUGGESTION,
    L1_CRITIC_PROMPT,
    DEEPEN_LINK_DERIVE_PROMPT,
    DIFFERENTIAL_ANALYSIS_PROMPT,
    SIM_MATRIX_PROMPT,
    COMPLEXITY_CHECK_PROMPT,
    # Phase 1 (S0) 演算法為骨：SR 生成新流程 prompts
    RELEVANCE_SCORING_PROMPT,
    SR_REWRITE_PROMPT,
    # Phase 2: DecisionCard 產出
    DECISION_CARD_PROMPT,
    # Phase 3: 整併三層改造
    INTRA_COMPATIBILITY_CHECK_PROMPT,
    ENGINEERING_VERDICT_LITE_PROMPT,
    # Engineering Spec Pipeline
    ENGINEERING_SPEC_SYSTEM,
    ENGINEERING_SPEC_EXPANSION,
    ENGINEERING_SPEC_GENERATION,
    ENGINEERING_SPEC_FIELD_PLANNING,
    ENGINEERING_SPEC_VALUE_FILLING,
    ENGINEERING_SPEC_STRENGTHEN,
)
from app.tools.triz_kb import (
    build_triz_tc_context,
    build_triz_pc_context,
    build_sufield_context,
    get_param_name,
    lookup_matrix,
    load_40_principles,
)
from app.models.schemas import (
    TrizLookupRequest,
    TrizLookupResponse,
    SuFieldRequest,
    SuFieldResponse,
    ScamperRequest,
    ScamperResponse,
    SubsystemSuggestRequest,
    SubsystemSuggestResponse,
    SuggestedSubsystem,
    InterfaceContract,
    SpatialEstimate,
    BBox,
    # Layered drill-down (v7)
    LayeredTrizSolution,
    L1Surface,
    L2RootCause,
    L3StructuralCheck,
    DeepenLink,
    SeparationCandidate,
    SuFieldModel,
    DifferentialAnalysis,
    DifferentialPairAnalysis,
    RecommendedRoute,
    PhaseBDirective,
    SolveTrizLayeredRequest,
    SolveTrizLayeredResponse,
    TrizSuggestion,
    # Auto-TRIZ v2 (WBS 8.3)
    SIMMatrixRequest,
    SIMMatrixResponse,
    SolutionInteraction,
    ComplexityCheckRequest,
    ComplexityCheckResponse,
    # Engineering Spec Pipeline
    DraftValue,
    EngineeringSpecDraft,
    EngineeringSpecDraftResponse,
    ConceptArchitecturePack,
    PackageMap,
    # Split API: Engineering Spec Drafts Pipeline
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
)
from app.services import reference_library  # legacy direct access (kept for back-compat)
from app.services.spatial_lookup import LookupQuery, default_resolver
from app.services.spatial_validator import discover_package
from app.observability import emit_counter, phase_timer
from app.core.supabase import get_supabase


def solve_triz(req: TrizLookupRequest) -> TrizLookupResponse:
    """Resolve a TRIZ contradiction — route strictly by declared type.

    Step 3 classifies each contradiction/problem into a type; Step 5a
    dispatches to the corresponding solver path:
      TC → contradiction matrix → 40 principles (requires improving/worsening params)
      PC → separation principles (requires physical_contradiction)
      SF → Su-Field 76 standard solutions (requires sf_* fields)
    """
    if req.type == "SF":
        return _solve_sf(req)
    elif req.type == "TC":
        if not req.improving_param or not req.worsening_param:
            # Should not happen if formalize ran correctly — return empty with warning
            return TrizLookupResponse(
                mapped_improving=req.improving_param,
                mapped_worsening=req.worsening_param,
                suggestions=[],
            )
        return _solve_tc(req)
    elif req.type == "PC":
        return _solve_pc(req)
    else:
        raise ValueError(f"Unknown contradiction type '{req.type}'. Expected TC, PC, or SF.")


def _solve_tc(req: TrizLookupRequest) -> TrizLookupResponse:
    if settings.use_harness_agents:
        return _solve_tc_harness(req)
    return _solve_tc_legacy(req)


def _solve_tc_harness(req: TrizLookupRequest) -> TrizLookupResponse:
    """Harness path: route TC solving through HarnessAgent (Phase 2b)."""
    from app.harness.agent_base import HarnessAgent
    from app.harness.prompt_assembler import assemble_prompt
    from pydantic import BaseModel, Field as PydField

    class _TCSolverOutput(BaseModel):
        suggestions: list[TrizSuggestion] = PydField(default_factory=list)

    improving = req.improving_param
    worsening = req.worsening_param
    candidates = lookup_matrix(improving, worsening)
    triz_context = build_triz_tc_context(improving, worsening)

    system_prompt, user_message = assemble_prompt(
        TRIZ_SOLVER_SYSTEM,
        knowledge_blocks={"triz_tc_context": triz_context},
        dynamic_context={
            "user_input": TRIZ_TC_INSTANTIATION.format(
                natural_description=req.natural_description,
                triz_context=triz_context,
                improving=improving,
                worsening=worsening,
            ),
        },
    )

    agent = HarnessAgent(
        name="triz_tc",
        system_prompt=system_prompt,
        output_type=_TCSolverOutput,
        model_override=settings.fast_model,
    )

    result = agent.run_sync(user_message)

    # Ensure each suggestion carries path="TC"
    for s in result.suggestions:
        if not s.path:
            s.path = "TC"

    return TrizLookupResponse(
        mapped_improving=improving,
        mapped_worsening=worsening,
        candidate_principles=candidates,
        suggestions=[s.model_dump() for s in result.suggestions],
    )


def _solve_tc_legacy(req: TrizLookupRequest) -> TrizLookupResponse:
    """Legacy path: direct call_llm_json (pre-harness)."""
    improving = req.improving_param
    worsening = req.worsening_param
    candidates = lookup_matrix(improving, worsening)
    triz_context = build_triz_tc_context(improving, worsening)

    prompt = TRIZ_TC_INSTANTIATION.format(
        natural_description=req.natural_description,
        triz_context=triz_context,
        improving=improving,
        worsening=worsening,
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    # Ensure each suggestion carries path="TC"
    suggestions = data.get("suggestions", [])
    for s in suggestions:
        if not s.get("path"):
            s["path"] = "TC"

    return TrizLookupResponse(
        mapped_improving=improving,
        mapped_worsening=worsening,
        candidate_principles=candidates,
        suggestions=suggestions,
    )


def _solve_pc(req: TrizLookupRequest) -> TrizLookupResponse:
    if req.separation_principle_id:
        return _solve_pc_with_hint(req)
    return _solve_pc_base(req)


def _solve_pc_base(req: TrizLookupRequest) -> TrizLookupResponse:
    """Original PC solver path — selects separation principle from scratch."""
    triz_context = build_triz_pc_context()

    prompt = TRIZ_PC_INSTANTIATION.format(
        natural_description=req.natural_description,
        physical_contradiction=req.physical_contradiction or req.natural_description,
        triz_context=triz_context,
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    # Ensure each suggestion carries path="PC"
    suggestions = data.get("suggestions", [])
    for s in suggestions:
        if not s.get("path"):
            s["path"] = "PC"

    return TrizLookupResponse(
        suggestions=suggestions,
    )


def _solve_pc_with_hint(req: TrizLookupRequest) -> TrizLookupResponse:
    """Hint path — Explore already picked a separation principle.

    Uses the lighter TRIZ_PC_INSTANTIATION_WITH_HINT prompt which only
    injects 40 principles (skips the 16-item separation knowledge base
    because we already know the answer). Saves ~1000 tokens per call.
    """
    # Guard: if the hint id is not in canonical 16, fall back to base path
    from app.tools.separation_principles import get_separation_principle
    if get_separation_principle(req.separation_principle_id) is None:
        logger.warning(
            "Unknown separation_principle_id %r, falling back to base path",
            req.separation_principle_id,
        )
        return _solve_pc_base(req)

    principles_context = load_40_principles()
    prompt = TRIZ_PC_INSTANTIATION_WITH_HINT.format(
        natural_description=req.natural_description,
        physical_contradiction=req.physical_contradiction or req.natural_description,
        separation_principle_id=req.separation_principle_id,
        separation_category=req.separation_category or "",
        separation_rationale=req.separation_rationale or "",
        derived_parameter=req.derived_parameter or "",
        principles_context=principles_context,
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    suggestions = data.get("suggestions", [])
    for s in suggestions:
        if not s.get("path"):
            s["path"] = "PC"

    # 9.1.4 delta log — compare LLM output vs hint
    _log_hint_override_delta(
        expected_category=req.separation_category or "",
        suggestions=suggestions,
    )

    return TrizLookupResponse(suggestions=suggestions)


def _log_hint_override_delta(expected_category: str, suggestions: list[dict]) -> None:
    """Log when LLM output's separation_principle differs from the hint category.

    Does not fail or mutate — observability only (L2 WBS 9.1.4).
    """
    if not expected_category or not suggestions:
        return
    overrides = [
        s.get("separation_principle")
        for s in suggestions
        if s.get("separation_principle") and s.get("separation_principle") != expected_category
    ]
    if overrides:
        logger.info(
            "separation hint override: expected=%s llm=%s count=%d",
            expected_category, overrides, len(overrides),
        )


def _solve_sf(req: TrizLookupRequest) -> TrizLookupResponse:
    """Su-Field path: delegate to analyze_sufield and wrap result as TrizLookupResponse."""
    from app.models.schemas import SuFieldRequest as _SFReq

    sf_req = _SFReq(
        project_id=req.project_id,
        system_description=req.natural_description,
        current_issues=[req.natural_description],
        contradiction_id=req.contradiction_id,
        substance_1=req.sf_substance_1,
        substance_2=req.sf_substance_2,
        field_type=req.sf_field,
    )
    sf_resp = analyze_sufield(sf_req)

    # Convert matched 76-standard solutions into TrizSuggestion format
    suggestions = []
    for sol in sf_resp.matched_solutions:
        suggestions.append({
            "path": "SuField",
            "principle_number": None,
            "principle_name": f"{sol.standard_id} {sol.standard_name}",
            "suggestion": sol.suggestion,
            "separation_principle": "",
            "affected_modules": sol.affected_modules,
            "secondary_contradictions": sol.secondary_contradictions,
        })

    return TrizLookupResponse(suggestions=suggestions)


def _infer_sufield_state(req: SuFieldRequest) -> str | None:
    """Infer Su-Field system state from request metadata for KB filtering."""
    comp = (getattr(req, 'sf_completeness', None) or '').lower()
    inter = (getattr(req, 'sf_interaction', None) or '').lower()
    if 'incomplete' in comp or not (req.substance_1 and req.substance_2 and req.field_type):
        return 'incomplete'
    if 'harmful' in inter or 'harmful' in comp:
        return 'harmful'
    if 'insufficient' in inter:
        return 'insufficient'
    return None  # unknown → full inject


def analyze_sufield(req: SuFieldRequest) -> SuFieldResponse:
    """Analyse a technical system using Su-Field modelling + 76 standard solutions."""
    state_hint = _infer_sufield_state(req)
    triz_context = build_sufield_context(system_state=state_hint)

    # Enrich system_description with Su-Field context from Function Model if available
    desc = req.system_description
    if req.substance_1 or req.substance_2:
        desc += f"\nFunction Model: S1={req.substance_1 or '?'}, S2={req.substance_2 or '?'}, F={req.field_type or '?'}"

    prompt = SUFIELD_ANALYSIS.format(
        system_description=desc,
        current_issues="\n".join(f"- {i}" for i in req.current_issues) or "（未指定）",
        triz_context=triz_context,
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    empty_fallback = SuFieldResponse(
        su_field={"S1": req.substance_1 or "", "S2": req.substance_2 or "", "F": req.field_type or ""},
        system_state="unknown",
        matched_solutions=[],
    )
    if not raw or not raw.strip():
        logger.warning("Su-Field analysis: LLM returned empty response (raw=%r)", raw[:200] if raw else raw)
        return empty_fallback
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Su-Field analysis: LLM returned non-JSON (raw=%s)", raw[:500])
        return empty_fallback

    return SuFieldResponse(
        su_field=data.get("su_field", {}),
        system_state=data.get("system_state", "unknown"),
        matched_solutions=data.get("matched_solutions", []),
    )


# ---------------------------------------------------------------------------
# Auto-TRIZ v2 — SIM Matrix (WBS 8.3.1)
# ---------------------------------------------------------------------------


def sim_matrix(req: SIMMatrixRequest) -> SIMMatrixResponse:
    """Evaluate solution interactions across multiple contradictions.

    Builds a Solution Interaction Matrix (SIM) via LLM, then persists the
    result into the ``sim_matrices`` Supabase table (upsert on project_id +
    contradiction_ids combination).
    """
    # Build the solutions block for the prompt
    lines: list[str] = []
    for cid in req.contradiction_ids:
        solutions = req.solutions_per_contradiction.get(cid, [])
        lines.append(f"Contradiction {cid}:")
        for sol in solutions:
            lines.append(f"  - {sol}")
    solutions_block = "\n".join(lines)

    prompt = SIM_MATRIX_PROMPT.format(solutions_block=solutions_block)
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    # Parse interactions into SolutionInteraction models
    interactions: list[SolutionInteraction] = []
    for item in data.get("interactions", []):
        try:
            interactions.append(SolutionInteraction.model_validate(item))
        except Exception as exc:
            logger.debug("drop malformed SIM interaction: %s (%s)", item, exc)

    response = SIMMatrixResponse(
        project_id=req.project_id,
        contradiction_ids=req.contradiction_ids,
        matrix=interactions,
        optimal_combination=data.get("optimal_combination", []),
        conflicts=data.get("conflicts", []),
        synergies=data.get("synergies", []),
    )

    # Persist to Supabase (non-fatal)
    _persist_sim_matrix(response)

    return response


def _persist_sim_matrix(resp: SIMMatrixResponse) -> None:
    """Upsert SIM matrix into sim_matrices table. Non-fatal on failure."""
    from app.core.supabase import get_supabase
    try:
        sb = get_supabase()
        # Sort contradiction_ids for deterministic key
        sorted_ids = sorted(resp.contradiction_ids)
        payload = {
            "project_id": resp.project_id,
            "contradiction_ids": sorted_ids,
            "matrix": [i.model_dump(mode="json") for i in resp.matrix],
            "optimal_combination": resp.optimal_combination,
        }
        sb.table("sim_matrices").upsert(
            payload, on_conflict="project_id,contradiction_ids"
        ).execute()
    except Exception as exc:
        logger.warning("persist sim_matrix failed for project %s: %s", resp.project_id, exc)


# ---------------------------------------------------------------------------
# Auto-TRIZ v2 — Complexity Check / CCI (WBS 8.3.2)
# ---------------------------------------------------------------------------


def complexity_check(req: ComplexityCheckRequest) -> ComplexityCheckResponse:
    """Evaluate whether a solution is an evolution or a patch (CCI).

    Lightweight assessment — does NOT persist to DB.
    """
    prompt = COMPLEXITY_CHECK_PROMPT.format(
        solution_description=req.solution_description,
        original_contradiction=req.original_contradiction,
        affected_subsystems=", ".join(req.affected_subsystems) or "(none)",
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    # Validate cci_level
    cci_level = data.get("cci_level", "patch")
    if cci_level not in ("evolution", "weak_evolution", "patch"):
        cci_level = "patch"

    score = data.get("score", 0)
    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = 0

    return ComplexityCheckResponse(
        cci_level=cci_level,
        score=score,
        reasoning=str(data.get("reasoning") or ""),
        four_questions=data.get("four_questions", {}),
    )


# ---------------------------------------------------------------------------
# Layered Drill-Down (v7)
#
# Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §4–§8
#      docs/diagrams/create-ux-spec.md v7 Tab ① 區塊 B
#      docs/e2e/module/TRIZ_Layered_Drilldown_Development_WBS.md §3–§5
#
# Philosophy: TC/PC/SF are NOT mutually-exclusive routes. They are the three
# layers of one drill-down diagnosis. `solve_triz_layered` reuses the existing
# `_solve_tc` / `_solve_pc` / `_solve_sf` primitives unchanged, then wraps them
# in a LayeredTrizSolution with deepen_link (ARIZ L1→L2) and cross-layer
# differential analysis for RD decision-making.
# ---------------------------------------------------------------------------


def _tc_suggestions_to_models(data: dict) -> list[TrizSuggestion]:
    """Parse raw LLM output into validated TrizSuggestion list, tolerant to errors."""
    out: list[TrizSuggestion] = []
    for s in data.get("suggestions", []) or []:
        try:
            out.append(TrizSuggestion.model_validate(s))
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("drop malformed TC suggestion: %s (%s)", s, exc)
    return out


def _l1_critic(
    *,
    natural_description: str,
    improving: int | None,
    worsening: int | None,
    candidate_principles: list[int],
    l1_suggestions: list[TrizSuggestion],
) -> tuple[bool, str, float]:
    """Judge whether L1 suggestions are mere trade-offs (→ trigger L2 deepen)
    or contain at least one root-cause breakthrough.

    Uses a rule + LLM composite (§4.1):
      - Rule: if principles ≤ 2 → trigger_l2 with confidence 0.9.
      - Otherwise: ask LLM to classify each suggestion as trade-off vs breakthrough.

    Returns (trigger_l2, reason, confidence).
    """
    # Rule-based fast path: too few principles → matrix is thin, deepen immediately
    if len(candidate_principles) <= 2:
        return True, f"矩陣推薦原理僅 {len(candidate_principles)} 條，建議深挖為 PC", 0.9

    if not l1_suggestions:
        return True, "L1 未產出任何有效 suggestion，直接深挖", 0.9

    improving_name = get_param_name(improving)
    worsening_name = get_param_name(worsening)

    suggestions_block = "\n".join(
        f"- #{s.principle_number or '?'} {s.principle_name}: {s.suggestion}"
        for s in l1_suggestions
    )

    prompt = L1_CRITIC_PROMPT.format(
        natural_description=natural_description,
        improving=f"{improving} {improving_name}".strip(),
        worsening=f"{worsening} {worsening_name}".strip(),
        candidate_principles=candidate_principles,
        l1_suggestions=suggestions_block,
    )
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("L1 critic LLM call failed: %s — defaulting to trigger_l2=False", exc)
        return False, "critic LLM 無回應，預設不深挖", 0.0

    trigger = bool(data.get("trigger_l2", False))
    reason = str(data.get("reason") or "")
    try:
        confidence = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return trigger, reason, max(0.0, min(1.0, confidence))


def _derive_pc_from_tc(
    *,
    natural_description: str,
    improving: int | None,
    worsening: int | None,
) -> DeepenLink:
    """ARIZ-style deepen_link: TC (improving, worsening) → PC (derived_parameter, separation_candidates).

    Ref §4.3 contract. LLM-backed with a minimal rule fallback when LLM fails.
    """
    default_link = DeepenLink(from_tc_pair=(improving, worsening))

    if not improving or not worsening:
        return default_link

    improving_name = get_param_name(improving)
    worsening_name = get_param_name(worsening)
    prompt = DEEPEN_LINK_DERIVE_PROMPT.format(
        natural_description=natural_description,
        improving=improving,
        improving_name=improving_name,
        worsening=worsening,
        worsening_name=worsening_name,
    )
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("deepen_link LLM call failed: %s", exc)
        return default_link

    candidates: list[SeparationCandidate] = []
    for c in data.get("separation_type_candidates") or []:
        try:
            candidates.append(SeparationCandidate.model_validate(c))
        except Exception:
            continue
    # sort by confidence desc
    candidates.sort(key=lambda c: c.confidence, reverse=True)

    return DeepenLink(
        from_tc_pair=(improving, worsening),
        derived_physical_parameter=str(data.get("derived_physical_parameter") or ""),
        contradiction_statement=str(data.get("contradiction_statement") or ""),
        separation_type_candidates=candidates,
    )


# ---- L1 / L2 / L3 thin wrappers around existing primitives ----------------


def _run_l1(req: SolveTrizLayeredRequest) -> L1Surface:
    """Run the L1 (TC) layer — wraps existing _solve_tc primitive.

    WBS 8.3.3: If ``fa_context`` is provided on the request, the function
    analysis context is injected into the natural_description so the TC
    instantiation prompt can leverage functional model information.
    """
    if not (req.improving_param and req.worsening_param):
        return L1Surface(
            improving_param=req.improving_param,
            worsening_param=req.worsening_param,
            candidate_principles=[],
            suggestions=[],
            critic_trigger_l2=True,
            critic_reason="缺 improving/worsening 參數，L1 無法跑，直接建議深挖 PC",
            critic_confidence=0.9,
            status="error",
        )

    # WBS 8.3.3: Enrich description with FA context
    description = req.natural_description
    if req.fa_context:
        fa_lines = ["\n\n<function_analysis_context>"]
        for key in ("system_function", "substance_1", "substance_2", "field_type",
                     "interaction_type", "su_field_completeness", "problem_description"):
            val = req.fa_context.get(key)
            if val:
                fa_lines.append(f"  {key}: {val}")
        fa_lines.append("</function_analysis_context>")
        description += "\n".join(fa_lines)

    tc_req = TrizLookupRequest(
        project_id=req.project_id,
        contradiction_id=req.contradiction_id,
        natural_description=description,
        improving_param=req.improving_param,
        worsening_param=req.worsening_param,
        type="TC",
    )
    tc_resp = _solve_tc(tc_req)
    return L1Surface(
        improving_param=tc_resp.mapped_improving or req.improving_param,
        worsening_param=tc_resp.mapped_worsening or req.worsening_param,
        candidate_principles=list(tc_resp.candidate_principles),
        suggestions=list(tc_resp.suggestions),
        status="ran",
    )


def _run_l2(req: SolveTrizLayeredRequest, l1: L1Surface) -> L2RootCause:
    """Run the L2 (PC) layer with an ARIZ deepen_link from L1.

    WBS 8.3.3: If ``oz_ot_context`` is provided on the request, the
    OZ (operating zone) / OT (operating time) context is injected into the
    PC problem statement so the separation principle selection can leverage
    spatiotemporal operating window information.
    """
    deepen = _derive_pc_from_tc(
        natural_description=req.natural_description,
        improving=l1.improving_param,
        worsening=l1.worsening_param,
    )

    # Build a synthetic PC problem statement if RD did not provide one
    pc_statement = (
        req.physical_contradiction
        or deepen.contradiction_statement
        or req.natural_description
    )

    # WBS 8.3.3: Enrich PC statement with OZ-OT context
    description = req.natural_description
    if req.oz_ot_context:
        oz_ot_lines = ["\n\n<oz_ot_context>"]
        for key in ("oz_zone", "ot_time", "px_variable"):
            val = req.oz_ot_context.get(key)
            if val:
                oz_ot_lines.append(f"  {key}: {val}")
        oz_ot_lines.append("</oz_ot_context>")
        description += "\n".join(oz_ot_lines)

    pc_req = TrizLookupRequest(
        project_id=req.project_id,
        contradiction_id=req.contradiction_id,
        natural_description=description,
        physical_contradiction=pc_statement,
        type="PC",
    )
    try:
        pc_resp = _solve_pc(pc_req)
        suggestions = list(pc_resp.suggestions)
        status = "ran"
    except Exception as exc:
        logger.warning("L2 _solve_pc failed: %s", exc)
        suggestions = []
        status = "error"

    return L2RootCause(
        triggered=True,
        trigger_reason="",  # populated by orchestrator
        deepen_link=deepen,
        suggestions=suggestions,
        status=status,
    )


def _run_l3(req: SolveTrizLayeredRequest) -> L3StructuralCheck:
    """Run the L3 (SF) layer — always parallel, role=structural_lens."""
    sf_req = TrizLookupRequest(
        project_id=req.project_id,
        contradiction_id=req.contradiction_id,
        natural_description=req.natural_description,
        sf_substance_1=req.sf_substance_1,
        sf_substance_2=req.sf_substance_2,
        sf_field=req.sf_field,
        type="SF",
    )
    try:
        sf_resp = _solve_sf(sf_req)
    except Exception as exc:
        logger.warning("L3 _solve_sf failed: %s — L3 degrades to empty", exc)
        return L3StructuralCheck(status="error")

    # Extract standard_ids from suggestions (principle_name format: "<id> <name>")
    matched_ids: list[str] = []
    for s in sf_resp.suggestions:
        head = (s.principle_name or "").split(" ", 1)[0]
        if head and head[0].isdigit():
            matched_ids.append(head)

    # Try to fetch su-field model from SuFieldResponse via analyze_sufield for richness
    su_field_req = SuFieldRequest(
        project_id=req.project_id,
        system_description=req.natural_description,
        current_issues=[req.natural_description],
        contradiction_id=req.contradiction_id,
        substance_1=req.sf_substance_1,
        substance_2=req.sf_substance_2,
        field_type=req.sf_field,
    )
    try:
        sf_full = analyze_sufield(su_field_req)
        su_field_model = SuFieldModel(
            S1=str(sf_full.su_field.get("S1") or ""),
            S2=str(sf_full.su_field.get("S2") or ""),
            F=str(sf_full.su_field.get("F") or ""),
            state=sf_full.system_state if sf_full.system_state in
                {"incomplete", "effective", "harmful", "insufficient", "unknown"}
                else "unknown",
        )
    except Exception as exc:
        logger.debug("L3 su_field enrichment failed: %s", exc)
        su_field_model = SuFieldModel(state="unknown")

    return L3StructuralCheck(
        su_field_model=su_field_model,
        matched_standard_solutions=matched_ids,
        suggestions=list(sf_resp.suggestions),
        status="ran",
    )


def _run_differential_analysis(
    req: SolveTrizLayeredRequest,
    l1: L1Surface,
    l2: L2RootCause | None,
    l3: L3StructuralCheck,
) -> DifferentialAnalysis:
    """LLM-generated cross-layer differential + recommended_route (§5)."""

    def _layer_block(layer_name: str, suggestions: list, extra: str = "") -> str:
        bullets = "\n".join(f"  - {s.principle_name}: {s.suggestion}" for s in (suggestions or []))
        return f"{layer_name}: {extra}\n{bullets or '  (無)'}"

    l1_block = _layer_block(
        "L1 (TC)",
        l1.suggestions,
        f"depth={l1.depth_indicator}, principles={l1.candidate_principles}",
    )
    if l2 and l2.status == "ran":
        l2_block = _layer_block(
            "L2 (PC)",
            l2.suggestions,
            f"deepen_link.param={l2.deepen_link.derived_physical_parameter if l2.deepen_link else ''}",
        )
    else:
        l2_block = "L2: skipped or not triggered"
    l3_block = _layer_block(
        "L3 (SF)",
        l3.suggestions,
        f"state={l3.su_field_model.state}, matched={l3.matched_standard_solutions}",
    )

    prompt = DIFFERENTIAL_ANALYSIS_PROMPT.format(
        natural_description=req.natural_description,
        severity=req.severity,
        l1_block=l1_block,
        l2_block=l2_block,
        l3_block=l3_block,
    )
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("differential_analysis LLM failed: %s — using rule fallback", exc)
        data = {}

    def _pair(d):
        try:
            return DifferentialPairAnalysis.model_validate(d or {})
        except Exception:
            return DifferentialPairAnalysis()

    # Rule-based recommended_route fallback (§5.2)
    def _fallback_route() -> RecommendedRoute:
        has_l2 = bool(l2 and l2.status == "ran")
        has_l3 = bool(l3 and l3.status == "ran")
        if has_l2 and req.severity in {"fatal", "major"} and has_l3:
            return RecommendedRoute(
                primary="L2 + L3 組合（突破路線）",
                fallback="L1 單獨（快速路線）",
                adopted_layers=["L2", "L3"],
                rationale=f"severity={req.severity}，L2 深挖可行且 L3 可補結構旁路",
            )
        if has_l2 and req.severity == "minor":
            return RecommendedRoute(
                primary="L1 + L3",
                fallback="L2 單獨",
                adopted_layers=["L1", "L3"] if has_l3 else ["L1"],
                rationale="severity=minor，避免過度深挖",
            )
        return RecommendedRoute(
            primary="L1 + L3" if has_l3 else "L1 單獨",
            fallback="L1 單獨",
            adopted_layers=["L1", "L3"] if has_l3 else ["L1"],
            rationale="L2 未觸發，走 L1+L3 組合",
        )

    route_data = data.get("recommended_route")
    try:
        route = RecommendedRoute.model_validate(route_data) if route_data else _fallback_route()
    except Exception:
        route = _fallback_route()

    # Apply L3 bridge text back onto the L3 layer object
    bridge = data.get("l3_bridge") or {}
    if isinstance(bridge, dict):
        l3.supports_l1 = str(bridge.get("supports_l1") or l3.supports_l1)
        l3.supports_l2 = str(bridge.get("supports_l2") or l3.supports_l2)
        l3.standalone_value = str(bridge.get("standalone_value") or l3.standalone_value or "L3 結構旁路本身可獨立改善系統")

    return DifferentialAnalysis(
        l1_vs_l2=_pair(data.get("l1_vs_l2")),
        l1_vs_l3=_pair(data.get("l1_vs_l3")),
        l2_vs_l3=_pair(data.get("l2_vs_l3")),
        recommended_route=route,
    )


def _should_trigger_l2(
    req: SolveTrizLayeredRequest,
    l1: L1Surface,
) -> tuple[bool, str]:
    """L2 trigger decision (WBS 3.4 / 4.1 / 4.2).

    Order (first match wins):
      1. quick_mode + severity=minor → skip (quick_mode guard).
      2. force_l2 → trigger (RD manual override).
      3. severity ∈ {fatal, major} → trigger automatically.
      4. L1 critic_trigger_l2 with confidence ≥ 0.5 → trigger.
      5. otherwise → skip.

    Returns (should_trigger, reason_for_decision).
    """
    if req.quick_mode and req.severity == "minor":
        return False, "quick_mode skipped (severity=minor)"
    if req.force_l2:
        return True, "RD manual override (force_l2=true)"
    if req.severity in {"fatal", "major"}:
        return True, f"severity={req.severity} → 預設深挖"
    if l1.critic_trigger_l2 and l1.critic_confidence >= 0.5:
        return True, f"L1 critic: {l1.critic_reason}"
    if l1.critic_trigger_l2 and l1.critic_confidence < 0.5:
        return False, f"L1 critic 低信心 ({l1.critic_confidence:.2f})，改由 RD 手動決定"
    return False, "L1 已足夠深入，不需深挖"


def _build_lts_id(project_id: str, contradiction_id: str) -> str:
    cid = contradiction_id.replace("C-", "").strip() or "UNKNOWN"
    return f"LTS-{cid}"


def solve_triz_layered(req: SolveTrizLayeredRequest) -> SolveTrizLayeredResponse:
    """Orchestrate the three-layer drill-down TRIZ solution for ONE contradiction.

    Pipeline (§4):
        L1 (TC, always)  →  critic  →  maybe L2 (PC, deepen_link)
                            │
                            └─→  L3 (SF, always, structural_lens, in parallel)
                                      │
                                      └─→  differential_analysis (LLM)

    The three primitives `_solve_tc` / `_solve_pc` / `_solve_sf` are reused
    unchanged; this function is a thin orchestrator (§9.1).
    """
    with phase_timer("solve_triz_layered"):
        # ADR-007: Create-stage SF derivation.
        # Explore emits TC-only. If the caller did not supply Su-Field
        # fields but a valid TC is present, derive them here so L3 has
        # something structural to work with. Failure is non-fatal — L3
        # will degrade gracefully when S1/S2/F remain empty.
        if (
            not (req.sf_substance_1 or req.sf_substance_2 or req.sf_field)
            and isinstance(req.improving_param, int)
            and isinstance(req.worsening_param, int)
        ):
            try:
                from app.agents.analyst import derive_su_field_from_tc  # local import to avoid cycle
                derived_sf = derive_su_field_from_tc(
                    improving_param=req.improving_param,
                    worsening_param=req.worsening_param,
                    engineering_statement=req.natural_description,
                    natural_description=req.natural_description,
                )
                if derived_sf is not None:
                    req = req.model_copy(update={
                        "sf_substance_1": derived_sf.S1 or None,
                        "sf_substance_2": derived_sf.S2 or None,
                        "sf_field": derived_sf.F or None,
                    })
                    logger.info(
                        "solve_triz_layered: derived SF from TC (S1=%r S2=%r F=%r)",
                        derived_sf.S1, derived_sf.S2, derived_sf.F,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("solve_triz_layered: SF derivation failed: %s", exc)

        # L1 — always
        l1 = _run_l1(req)

        # L1 critic (skip if L1 errored on missing params)
        if l1.status == "ran":
            trig, reason, conf = _l1_critic(
                natural_description=req.natural_description,
                improving=l1.improving_param,
                worsening=l1.worsening_param,
                candidate_principles=l1.candidate_principles,
                l1_suggestions=l1.suggestions,
            )
            l1.critic_trigger_l2 = trig
            l1.critic_reason = reason
            l1.critic_confidence = conf

        # L2 — conditional
        should_l2, l2_reason = _should_trigger_l2(req, l1)
        if should_l2:
            l2 = _run_l2(req, l1)
            l2.trigger_reason = l2_reason
        else:
            l2 = L2RootCause(
                triggered=False,
                trigger_reason=l2_reason,
                deepen_link=None,
                suggestions=[],
                status="skipped_quick_mode"
                if (req.quick_mode and req.severity == "minor")
                else "skipped_condition",
            )

        # L3 — always (parallel-in-spirit; currently sequential to keep the
        # LLM client simple, but causally independent of L1/L2)
        l3 = _run_l3(req)

        # Differential analysis
        diff = _run_differential_analysis(req, l1, l2 if l2.status == "ran" else None, l3)

        lts = LayeredTrizSolution(
            id=_build_lts_id(req.project_id, req.contradiction_id),
            project_id=req.project_id,
            contradiction_id=req.contradiction_id,
            contradiction_natural_description=req.natural_description,
            severity=req.severity,
            l1_surface=l1,
            l2_root_cause=l2 if (l2.status == "ran" or l2.triggered) else None,
            l3_structural_check=l3,
            differential_analysis=diff,
            phase_b_directive=PhaseBDirective(),  # defaults: intra-LTS skip, cross-contradiction check
        )
        _persist_layered_solution(lts)
        emit_counter(
            "triz_layered_solved",
            severity=req.severity,
            l2_ran=str(l2.status == "ran").lower(),
            quick_mode=str(req.quick_mode).lower(),
        )
        return SolveTrizLayeredResponse(layered_solution=lts)


def _persist_layered_solution(lts: LayeredTrizSolution) -> None:
    """Upsert LTS into layered_triz_solutions so the UI can rehydrate on page
    reload and F2 subsystem discovery can read adopted LTS straight from DB.

    Non-fatal: persistence failures are logged but do NOT abort the response —
    the LLM work is expensive and we prefer to return it to the caller even if
    the DB write loses (caller keeps in-memory state as a fallback).
    """
    from app.core.supabase import get_supabase  # local import: keep module importable in tests without Supabase
    try:
        sb = get_supabase()
        payload = {
            "id": lts.id,
            "project_id": lts.project_id,
            "contradiction_id": lts.contradiction_id,
            "contradiction_natural_description": lts.contradiction_natural_description,
            "severity": lts.severity,
            "l1_surface": lts.l1_surface.model_dump(mode="json"),
            "l2_root_cause": lts.l2_root_cause.model_dump(mode="json") if lts.l2_root_cause else None,
            "l3_structural_check": lts.l3_structural_check.model_dump(mode="json"),
            "differential_analysis": lts.differential_analysis.model_dump(mode="json"),
            "phase_b_directive": lts.phase_b_directive.model_dump(mode="json"),
        }
        sb.table("layered_triz_solutions").upsert(payload, on_conflict="id").execute()
    except Exception as exc:
        logger.warning("persist layered_triz_solution failed for %s: %s", lts.id, exc)


def _resolve_spatial_via_layers(
    subsystems: list[SuggestedSubsystem],
    project_id: str,
    resolver=None,
) -> None:
    """Walk the subsystem tree and replace each LLM-supplied spatial estimate
    with the highest-priority lookup result from the layered resolver.

    The LLM may cite any of these source prefixes (or omit `reference_source`
    entirely):
        rd_override:<key>  | learned:<key>  | web:<...>  | seed:<key>  | llm_estimate

    For non-llm sources, the resolver is queried by `key`. If the resolver
    finds a match (in ANY layer — typically a project-level RD override or a
    learned component), the bbox/mass are overwritten with the authoritative
    values and `confidence` is set accordingly. The LLM number is always
    discarded when an authoritative source is available.

    For `llm_estimate` and entries with no reference_source set, the LLM
    number is left in place — that's the final fallback layer.
    """
    resolver = resolver or default_resolver(include_web=False)

    def visit(node: SuggestedSubsystem) -> None:
        for target_name, contract in (node.interface_contracts or {}).items():
            est = contract.spatial
            if est is None:
                continue
            src = est.reference_source or ""
            if not src or src == "llm_estimate":
                continue  # leave LLM numbers as the last-resort fallback
            # Strip any layer prefix to get the lookup key
            key = src.split(":", 1)[1] if ":" in src else src
            resolved = resolver.lookup(
                LookupQuery(key=key, category="", project_id=project_id)
            )
            if resolved is None or resolved.bbox is None:
                # The LLM cited a layer that didn't actually have this entry —
                # downgrade confidence so RD knows the number is not vendor-grade.
                est.confidence = "estimate"
                continue
            # Preserve any frame-relative origin/anchor the LLM proposed —
            # those describe placement, not the part itself.
            preserved_origin = est.bbox.origin_mm if est.bbox else (0.0, 0.0, 0.0)
            preserved_anchor = est.bbox.anchor if est.bbox else resolved.bbox.anchor
            est.bbox = BBox(
                x_mm=resolved.bbox.x_mm,
                y_mm=resolved.bbox.y_mm,
                z_mm=resolved.bbox.z_mm,
                origin_mm=preserved_origin,
                anchor=preserved_anchor,
            )
            est.mass_g = resolved.mass_g
            est.reference_source = resolved.reference_source
            est.confidence = resolved.confidence
            if not est.rationale and resolved.rationale:
                est.rationale = resolved.rationale
        for child in node.children or []:
            visit(child)

    for root in subsystems:
        visit(root)


# Legacy alias kept so older callers / tests still find this name. The new
# implementation routes through the layered resolver instead of the static
# JSON, but the behavioural contract is the same: vendor facts trump LLM.
def _override_with_reference_library(subsystems: list[SuggestedSubsystem]) -> None:
    _resolve_spatial_via_layers(subsystems, project_id="")


# ── Enum constant sets for defensive coercion ────────────────────────
_VALID_ARCHETYPES: set[str] = {
    "cube", "cylinder", "disc", "l_bracket", "sphere", "flat_plate", "custom",
}
_VALID_CONFIDENCES: set[str] = {"library", "estimate", "rd_confirmed"}
_VALID_LOD_HINTS: set[str] = {"concept", "envelope", "preliminary", "detailed"}


def _unwrap_value(v: object) -> object:
    """Extract bare value from an LLM provenance dict.

    LLM sometimes wraps numeric fields in::

        {"value": 28, "source": "llm_estimate", "confidence": "speculative"}

    This helper extracts the ``"value"`` key; if *v* is not a dict or has no
    ``"value"`` key, returns *v* unchanged.
    """
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def _coerce_bbox(bbox: dict) -> None:
    """In-place coercion for a raw BBox dict."""
    for dim in ("x_mm", "y_mm", "z_mm"):
        if dim in bbox:
            raw = _unwrap_value(bbox[dim])
            try:
                bbox[dim] = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                pass  # leave as-is; Pydantic will report
    origin = bbox.get("origin_mm")
    if isinstance(origin, (list, tuple)):
        bbox["origin_mm"] = [
            float(_unwrap_value(e)) if _unwrap_value(e) is not None else 0.0
            for e in origin
        ]
    archetype = _unwrap_value(bbox.get("geometry_archetype"))
    if archetype is not None and archetype not in _VALID_ARCHETYPES:
        archetype = None
    bbox["geometry_archetype"] = archetype


def _coerce_spatial_estimate(spatial: dict) -> None:
    """In-place coercion for a raw SpatialEstimate dict."""
    bbox = spatial.get("bbox")
    if isinstance(bbox, dict):
        _coerce_bbox(bbox)
    mass = spatial.get("mass_g")
    if mass is not None:
        raw = _unwrap_value(mass)
        try:
            spatial["mass_g"] = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pass
    conf = _unwrap_value(spatial.get("confidence"))
    if conf is not None and conf not in _VALID_CONFIDENCES:
        spatial["confidence"] = "estimate"
    elif conf is not None:
        spatial["confidence"] = conf
    lod = _unwrap_value(spatial.get("lod_hint"))
    if lod is not None and lod not in _VALID_LOD_HINTS:
        spatial["lod_hint"] = "concept"
    elif lod is not None:
        spatial["lod_hint"] = lod


def _coerce_ports(ports: list) -> None:  # type: ignore[type-arg]
    """In-place coercion for a raw ports list."""
    for port in ports:
        if not isinstance(port, dict):
            continue
        for field in ("position_mm", "normal"):
            vec = port.get(field)
            if isinstance(vec, (list, tuple)):
                port[field] = [
                    float(_unwrap_value(e)) if _unwrap_value(e) is not None else 0.0
                    for e in vec
                ]


def _coerce_contract(contract: dict) -> None:
    """In-place coercion for a raw InterfaceContract dict."""
    sp = contract.get("spatial")
    if sp is not None and isinstance(sp, dict):
        _coerce_spatial_estimate(sp)
    elif sp is not None and not isinstance(sp, dict):
        contract["spatial"] = None
    ports = contract.get("ports")
    if isinstance(ports, list):
        _coerce_ports(ports)


def _coerce_node(node: dict) -> None:
    """Recursively coerce a single subsystem node dict."""
    contracts = node.get("interface_contracts")
    if isinstance(contracts, dict):
        for _neighbour, contract in contracts.items():
            if isinstance(contract, dict):
                _coerce_contract(contract)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            _coerce_node(child)


def _coerce_subsystem_tree(data: dict) -> None:
    """Walk every subsystem in *data* and coerce LLM provenance dicts.

    Must be called **before** ``SubsystemSuggestResponse.model_validate(data)``
    so that wrapped numeric values and invalid enum strings are normalised to
    types that Pydantic can accept.
    """
    for sub in data.get("subsystems") or []:
        if isinstance(sub, dict):
            _coerce_node(sub)


_SIX_DIM_FIELDS = (
    "envelope", "loadPath", "thermalPath", "signalPath",
    "datumTolerance", "serviceability",
)


def _find_empty_contracts(
    subsystems: list[SuggestedSubsystem],
) -> list[tuple[str, str, list[str]]]:
    """Walk the tree and return a list of (owner_name, neighbour_name, empty_fields)
    tuples for every interface contract that has at least one blank 6-dim field.

    Returns an empty list when all contracts across all nodes are fully populated.
    Used by suggest_subsystems to gate the retry-once-then-raise validation loop.
    """
    violations: list[tuple[str, str, list[str]]] = []

    def visit(node: SuggestedSubsystem) -> None:
        for neighbour, contract in (node.interface_contracts or {}).items():
            missing = [
                field for field in _SIX_DIM_FIELDS
                if not (getattr(contract, field, "") or "").strip()
            ]
            if missing:
                violations.append((node.name, neighbour, missing))
        for child in node.children or []:
            visit(child)

    for root in subsystems:
        visit(root)
    return violations


def _format_violations_for_retry(
    violations: list[tuple[str, str, list[str]]],
) -> str:
    """Render violations as a concise instruction block for the retry prompt."""
    lines = ["## PREVIOUS RESPONSE HAD EMPTY REQUIRED FIELDS"]
    lines.append(
        "Your previous response left the following 6-dim fields blank. "
        "These fields are MANDATORY. Regenerate the full JSON response with "
        "all fields populated for these specific interfaces (keep everything "
        "else identical):"
    )
    for owner, neighbour, missing in violations[:20]:  # cap to keep prompt short
        lines.append(f"  - {owner} ↔ {neighbour}: missing {', '.join(missing)}")
    if len(violations) > 20:
        lines.append(f"  - ... and {len(violations) - 20} more")
    return "\n".join(lines)


def _enrich_contradiction_lines(
    contradictions: list,
) -> list[str]:
    """9.5.1 — Enrich contradiction context with child PC decomposition data.

    Each item in *contradictions* may be:
    - a plain ``str`` (legacy flat format) — passed through as-is
    - a ``dict`` with at least ``natural_description`` (or ``description``) and
      optionally ``subsystem_hint`` / ``derived_parameter`` — enriched with
      bracketed tags so the LLM can anchor subsystem naming.

    Returns a list of ``"- <line>"`` strings ready for prompt injection.
    """
    lines: list[str] = []
    for c in contradictions:
        if isinstance(c, dict):
            line = c.get("natural_description") or c.get("description", str(c))
            if c.get("subsystem_hint"):
                line += f" [子系統提示: {c['subsystem_hint']}]"
            if c.get("derived_parameter"):
                line += f" [物理變數: {c['derived_parameter']}]"
            lines.append(f"- {line}")
        else:
            lines.append(f"- {c}")
    return lines


def _serialize_layered_triz_for_f2_prompt(
    solutions: list[LayeredTrizSolution],
) -> list[str]:
    """v7 WP 11.2: Convert LayeredTrizSolution objects into prompt-ready lines
    for F2 subsystem discovery.

    Each LTS becomes a single bullet that tells the LLM:
      - the original contradiction description
      - which drill-down layers the RD adopted
      - the adopted mechanism(s) from those layers
      - the recommended_route label + rationale

    This lets F2 bind subsystems to the **adopted_route** (not just the flat
    contradiction description), which is the §8.1.1 primary-binding contract.
    """
    lines: list[str] = []
    for lts in solutions:
        # Honor the differential recommendation as the primary binding signal.
        recommended = lts.differential_analysis.recommended_route
        adopted = recommended.adopted_layers or ["L1"]
        mechanism_bits: list[str] = []
        if "L1" in adopted and lts.l1_surface.suggestions:
            top = lts.l1_surface.suggestions[0]
            mechanism_bits.append(f"L1: {top.principle_name} — {top.suggestion}")
        if (
            "L2" in adopted
            and lts.l2_root_cause is not None
            and lts.l2_root_cause.status == "ran"
            and lts.l2_root_cause.suggestions
        ):
            top = lts.l2_root_cause.suggestions[0]
            param = ""
            if lts.l2_root_cause.deepen_link:
                param = lts.l2_root_cause.deepen_link.derived_physical_parameter
            mechanism_bits.append(
                f"L2: {top.principle_name} (derived param: {param}) — {top.suggestion}"
            )
        if "L3" in adopted and lts.l3_structural_check.suggestions:
            top = lts.l3_structural_check.suggestions[0]
            state = lts.l3_structural_check.su_field_model.state
            mechanism_bits.append(
                f"L3: {top.principle_name} (Su-Field state={state}) — {top.suggestion}"
            )

        header = (
            f"[{lts.id} / {lts.contradiction_id}] "
            f"{lts.contradiction_natural_description or '(no description)'}"
        )
        route_label = f"adopted drill-down: {recommended.primary or '+'.join(adopted)}"
        if recommended.rationale:
            route_label += f" — {recommended.rationale}"
        lines.append(
            header
            + "\n    "
            + route_label
            + ("\n    " + "\n    ".join(mechanism_bits) if mechanism_bits else "")
        )
    return lines


# ---------------------------------------------------------------------------
# Engineering Spec Pipeline — Concept Architecture Pack → Engineering Drafts
# ---------------------------------------------------------------------------


def _inject_concept_origin_codes(
    subsystems: list[SuggestedSubsystem],
    concept_subsystems: list,
) -> None:
    """Defensive post-processing: ensure system-level nodes carry *concept_origin_code*.

    If the LLM didn't set ``concept_origin_code``, fuzzy-match by name against
    the original ``ConceptSubsystem`` list and inject ``code`` + ``mapped_kpis``.
    Only top-level (system) nodes are patched; children are left as-is.
    """
    if not concept_subsystems:
        return

    # Build lookup: normalised name → ConceptSubsystem
    cs_by_name: dict[str, object] = {}
    for cs in concept_subsystems:
        cs_by_name[cs.name.strip().lower()] = cs

    for sub in subsystems:
        if sub.concept_origin_code is not None:
            continue  # LLM already set it — trust the value

        key = sub.name.strip().lower()

        # 1. Exact match
        matched = cs_by_name.get(key)

        # 2. Substring / containment match (handles minor rephrasing)
        if matched is None:
            for cs_name, cs in cs_by_name.items():
                if cs_name in key or key in cs_name:
                    matched = cs
                    break

        if matched is not None:
            sub.concept_origin_code = matched.code  # type: ignore[union-attr]
            if not sub.mapped_kpis:
                sub.mapped_kpis = list(matched.mapped_kpis)  # type: ignore[union-attr]
            logger.debug(
                "Injected concept_origin_code=%s for subsystem '%s'",
                sub.concept_origin_code,
                sub.name,
            )


# ── Split API step functions ────────────────────────────────────────────────


def eng_spec_step1a_expand(
    req: SubsystemSuggestRequest,
) -> EngSpecStep1aResponse:
    """Step 1a — LLM Structure Expansion (≤150 s typical).

    Expand concept-level subsystems into a full 3-level hierarchy
    (System → Module → Component) with LLM-estimated spatial info and
    interface contracts.  Does NOT run web-based spatial resolution or
    package-map discovery (those are deferred to Step 1b).

    Requires ``req.concept_pack`` to be non-None.
    """
    if req.concept_pack is None:
        raise ValueError(
            "eng_spec_step1a_expand requires req.concept_pack to be set. "
            "Use suggest_subsystems() for the legacy (non-concept-pack) path."
        )

    pack = req.concept_pack

    # -- Resolver & library summary ------------------------------------------
    resolver = default_resolver(include_web=False)
    with phase_timer("eng_spec.summarize", project_id=req.project_id):
        library_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    # Serialise concept_pack fields for prompt injection
    concept_subsystems_json = json.dumps(
        [cs.model_dump(mode="json") for cs in pack.subsystems],
        ensure_ascii=False,
        indent=2,
    )
    concept_interfaces_json = json.dumps(
        [ci.model_dump(mode="json") for ci in pack.interfaces],
        ensure_ascii=False,
        indent=2,
    )

    # ── LLM expansion call ──────────────────────────────────────────────────
    expansion_prompt = ENGINEERING_SPEC_EXPANSION.format(
        mission=req.mission,
        concept_subsystems=concept_subsystems_json,
        concept_interfaces=concept_interfaces_json,
        reference_library=library_summary,
    )
    with phase_timer("eng_spec.step1a_expansion", project_id=req.project_id):
        raw_expansion = call_llm_json(ENGINEERING_SPEC_SYSTEM, expansion_prompt)
    emit_counter("eng_spec.step1a_done", value=1, project_id=req.project_id)

    expansion_data = json.loads(raw_expansion)

    # ── Defensive coercion: LLM may wrap values in provenance dicts,
    #    emit invalid enums, or return "spatial": "<string>".
    #    Normalise the entire tree before model_validate.
    _coerce_subsystem_tree(expansion_data)

    tree_response = SubsystemSuggestResponse.model_validate(expansion_data)

    # ── Defensive: inject concept_origin_code if the LLM missed it ──────
    _inject_concept_origin_codes(tree_response.subsystems, pack.subsystems)

    # Validate 6-dim contracts — retry once if violations found
    violations = _find_empty_contracts(tree_response.subsystems)
    if violations:
        emit_counter("eng_spec.step1a_violations", value=len(violations), attempt=1)
        logger.warning(
            "eng_spec step1a: %d interface contracts had empty 6-dim fields; retrying",
            len(violations),
        )
        retry_prompt = (
            expansion_prompt + "\n\n" + _format_violations_for_retry(violations)
        )
        with phase_timer("eng_spec.step1a_expansion", attempt=2, project_id=req.project_id):
            raw_expansion = call_llm_json(ENGINEERING_SPEC_SYSTEM, retry_prompt)
        expansion_data = json.loads(raw_expansion)
        _coerce_subsystem_tree(expansion_data)
        tree_response = SubsystemSuggestResponse.model_validate(expansion_data)
        _inject_concept_origin_codes(tree_response.subsystems, pack.subsystems)

        violations = _find_empty_contracts(tree_response.subsystems)
        if violations:
            emit_counter("eng_spec.step1a_incomplete", value=1, project_id=req.project_id)
            raise IncompleteLLMResponseError(
                "Engineering spec expansion left required 6-dim interface contract "
                f"fields blank after retry ({len(violations)} violations remaining)",
                violations=violations,
            )

    emit_counter(
        "eng_spec.step1a_complete",
        value=1,
        project_id=req.project_id,
        tree_count=len(tree_response.subsystems),
    )

    return EngSpecStep1aResponse(
        subsystems=tree_response.subsystems,
    )


def eng_spec_step1b_enrich(
    req: EngSpecStep1bRequest,
) -> EngSpecStep1bResponse:
    """Step 1b — Spatial Enrichment + Package Map (≤80 s typical).

    Takes the LLM-expanded subsystem tree from Step 1a, resolves spatial
    estimates via the layered chain (including web lookup), and discovers
    the package map.
    """
    # Resolve spatial estimates through layered chain (web enabled)
    full_resolver = default_resolver(include_web=True)
    with phase_timer("eng_spec.resolve_spatial", project_id=req.project_id):
        _resolve_spatial_via_layers(req.subsystems, req.project_id, full_resolver)

    # Compute package map
    package_map: PackageMap | None = None
    with phase_timer("eng_spec.discover_package", project_id=req.project_id) as _phase:
        try:
            package_map = discover_package(req.subsystems)
        except Exception as exc:
            emit_counter(
                "eng_spec.validator_fallback",
                value=1,
                error_type=type(exc).__name__,
            )
            logger.warning("eng_spec: spatial validator failed: %s", exc)
            _phase["status"] = "fallback"

    emit_counter(
        "eng_spec.step1b_complete",
        value=1,
        project_id=req.project_id,
        tree_count=len(req.subsystems),
    )

    return EngSpecStep1bResponse(
        subsystems=req.subsystems,
        package_map=package_map,
    )


def eng_spec_step1_expand(
    req: SubsystemSuggestRequest,
) -> EngSpecStep1Response:
    """Step 1 — Structure Expansion (backward-compatible wrapper).

    Calls Step 1a (LLM expansion) then Step 1b (spatial enrichment)
    sequentially.  Kept for the legacy ``step1-expand`` endpoint and the
    monolithic ``engineering-spec-drafts`` wrapper.
    """
    step1a = eng_spec_step1a_expand(req)
    step1b = eng_spec_step1b_enrich(
        EngSpecStep1bRequest(
            project_id=req.project_id,
            subsystems=step1a.subsystems,
        )
    )
    return EngSpecStep1Response(
        subsystems=step1b.subsystems,
        package_map=step1b.package_map,
    )


# ---------------------------------------------------------------------------
# Internal dataclasses for two-stage field planning (§3.1 of plan)
# ---------------------------------------------------------------------------

@dataclass
class PlannedField:
    """Stage 2a output: a single recommended spec field."""
    field_name: str
    category: str
    why: str
    expected_unit: str | None = None


@dataclass
class ComponentFieldPlan:
    """Stage 2a output: field plan for one component."""
    subsystem_code: str
    component_type_hint: str
    fields: list[PlannedField] = dc_field(default_factory=list)


@dataclass
class ModuleFieldPlan:
    """Stage 2a output: field plans for all components under one module."""
    module_name: str
    components: list[ComponentFieldPlan] = dc_field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper: extract module-level nodes from the subsystem tree
# ---------------------------------------------------------------------------

def _extract_modules(
    subsystems: list[SuggestedSubsystem],
) -> list[SuggestedSubsystem]:
    """Walk the subsystem tree and collect all ``level='module'`` nodes (with children)."""
    modules: list[SuggestedSubsystem] = []

    def visit(node: SuggestedSubsystem) -> None:
        if node.level == "module":
            modules.append(node)
        for child in node.children:
            visit(child)

    for s in subsystems:
        visit(s)
    return modules


# ---------------------------------------------------------------------------
# Helper: parse Stage 2a LLM JSON → ModuleFieldPlan
# ---------------------------------------------------------------------------

def _parse_field_plan(raw_json: str) -> ModuleFieldPlan:
    """Parse and validate the Stage 2a (field planning) LLM response."""
    data = json.loads(raw_json)
    components: list[ComponentFieldPlan] = []
    for comp in data.get("components", []):
        fields = [
            PlannedField(
                field_name=f.get("field_name", "unknown"),
                category=f.get("category", "spatial"),
                why=f.get("why", ""),
                expected_unit=f.get("expected_unit"),
            )
            for f in comp.get("fields", [])
        ]
        components.append(
            ComponentFieldPlan(
                subsystem_code=comp.get("subsystem_code", ""),
                component_type_hint=comp.get("component_type_hint", "generic"),
                fields=fields,
            )
        )
    return ModuleFieldPlan(
        module_name=data.get("module_name", "unknown"),
        components=components,
    )


def _field_plan_to_dict(plan: ModuleFieldPlan) -> dict:
    """Serialise a ModuleFieldPlan to a JSON-serialisable dict for prompt injection."""
    return {
        "module_name": plan.module_name,
        "components": [
            {
                "subsystem_code": c.subsystem_code,
                "component_type_hint": c.component_type_hint,
                "fields": [
                    {
                        "field_name": f.field_name,
                        "category": f.category,
                        "why": f.why,
                        "expected_unit": f.expected_unit,
                    }
                    for f in c.fields
                ],
            }
            for c in plan.components
        ],
    }


# ---------------------------------------------------------------------------
# Helper: parse and validate raw LLM drafts → list[EngineeringSpecDraft]
# ---------------------------------------------------------------------------

def _parse_and_validate_drafts(raw_json: str) -> list[EngineeringSpecDraft]:
    """Parse LLM JSON output into validated EngineeringSpecDraft objects."""
    data = json.loads(raw_json)
    raw_drafts: list[dict] = data.get("drafts", [])
    drafts: list[EngineeringSpecDraft] = []
    for rd in raw_drafts:
        try:
            draft = EngineeringSpecDraft.model_validate(rd)
            draft.recompute_stats()
            drafts.append(draft)
        except Exception as exc:
            logger.warning(
                "eng_spec step2: skipping malformed draft for %s: %s",
                rd.get("subsystem_code", "?"),
                exc,
            )
            emit_counter(
                "eng_spec.step2_draft_skip",
                value=1,
                subsystem_code=rd.get("subsystem_code", "unknown"),
            )
    return drafts


# ---------------------------------------------------------------------------
# Helper: two-stage spec generation for a single module
# ---------------------------------------------------------------------------

def _generate_module_specs(
    module: SuggestedSubsystem,
    mission: str,
    library_summary: str,
    project_id: str,
) -> list[EngineeringSpecDraft]:
    """Execute Stage 2a (field planning) + Stage 2b (value filling) for one module.

    If any stage fails, falls back to the legacy single-call approach using
    ENGINEERING_SPEC_GENERATION so the module still produces *some* output.
    """
    module_json = json.dumps(
        module.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )

    try:
        # ── Stage 2a: Field Planning ──────────────────────────────────────
        plan_prompt = ENGINEERING_SPEC_FIELD_PLANNING.format(
            mission=mission,
            module_tree=module_json,
        )
        with phase_timer(
            "eng_spec.step2a_field_plan",
            project_id=project_id,
            module=module.name,
        ):
            raw_plan = call_llm_json(ENGINEERING_SPEC_SYSTEM, plan_prompt)
        field_plan = _parse_field_plan(raw_plan)
        emit_counter(
            "eng_spec.step2a_done",
            value=1,
            project_id=project_id,
            module=module.name,
            planned_fields=sum(len(c.fields) for c in field_plan.components),
        )

        # ── Stage 2b: Value Filling ───────────────────────────────────────
        field_plan_json = json.dumps(
            _field_plan_to_dict(field_plan),
            ensure_ascii=False,
            indent=2,
        )
        fill_prompt = ENGINEERING_SPEC_VALUE_FILLING.format(
            mission=mission,
            module_name=module.name,
            field_plan=field_plan_json,
            reference_library=library_summary,
        )
        with phase_timer(
            "eng_spec.step2b_value_fill",
            project_id=project_id,
            module=module.name,
        ):
            raw_drafts = call_llm_json(ENGINEERING_SPEC_SYSTEM, fill_prompt)
        drafts = _parse_and_validate_drafts(raw_drafts)

        # ── Backfill component_type_hint from Stage 2a field plan ──
        hint_map: dict[str, str] = {
            c.subsystem_code: c.component_type_hint
            for c in field_plan.components
            if c.component_type_hint
        }
        for draft in drafts:
            if draft.component_type_hint is None and draft.subsystem_code in hint_map:
                draft.component_type_hint = hint_map[draft.subsystem_code]

        emit_counter(
            "eng_spec.step2b_done",
            value=1,
            project_id=project_id,
            module=module.name,
            draft_count=len(drafts),
        )
        return drafts

    except Exception as exc:
        # ── Fallback: legacy single-call for this module ──────────────────
        logger.warning(
            "eng_spec step2: two-stage failed for module '%s', "
            "falling back to single-call: %s",
            module.name,
            exc,
        )
        emit_counter(
            "eng_spec.step2_module_fallback",
            value=1,
            project_id=project_id,
            module=module.name,
        )
        fallback_tree = json.dumps(
            [module.model_dump(mode="json")],
            ensure_ascii=False,
            indent=2,
        )
        fallback_prompt = ENGINEERING_SPEC_GENERATION.format(
            mission=mission,
            subsystem_tree=fallback_tree,
            reference_library=library_summary,
        )
        with phase_timer(
            "eng_spec.step2_fallback",
            project_id=project_id,
            module=module.name,
        ):
            raw_fallback = call_llm_json(ENGINEERING_SPEC_SYSTEM, fallback_prompt)
        return _parse_and_validate_drafts(raw_fallback)


# ---------------------------------------------------------------------------
# Helper: generate specs for system-level nodes (simplified single call)
# ---------------------------------------------------------------------------

def _generate_system_level_specs(
    systems: list[SuggestedSubsystem],
    mission: str,
    library_summary: str,
    project_id: str,
) -> list[EngineeringSpecDraft]:
    """Generate specs for system-level nodes using the legacy single-call approach.

    System nodes are high-level (e.g. "風扇馬達系統") and don't have the deep
    component detail that benefits from two-stage planning, so a single
    ENGINEERING_SPEC_GENERATION call is sufficient.
    """
    if not systems:
        return []

    # Build a shallow tree containing only the system nodes (no children)
    shallow = []
    for s in systems:
        d = s.model_dump(mode="json")
        d["children"] = []  # strip module/component subtree
        shallow.append(d)

    tree_json = json.dumps(shallow, ensure_ascii=False, indent=2)
    prompt = ENGINEERING_SPEC_GENERATION.format(
        mission=mission,
        subsystem_tree=tree_json,
        reference_library=library_summary,
    )
    with phase_timer("eng_spec.step2_system_level", project_id=project_id):
        raw = call_llm_json(ENGINEERING_SPEC_SYSTEM, prompt)
    return _parse_and_validate_drafts(raw)


# ---------------------------------------------------------------------------
# Step 2 — Two-stage per-module AI Spec Generation
# ---------------------------------------------------------------------------

def eng_spec_step2_generate(req: EngSpecStep2Request) -> EngSpecStep2Response:
    """Step 2 — Two-stage per-module AI Spec Generation.

    Architecture (see plans/eng-spec-quality-gap.md §5):
      Stage 2a — Field Planning:  LLM reasons about *what* fields each component
                                  in a module needs (10-25 per component).
      Stage 2b — Value Filling:   LLM fills concrete values with full provenance
                                  for each planned field.

    Modules are processed in parallel (up to 4 workers). If a module's two-stage
    pipeline fails, it degrades to the legacy single-call approach so the overall
    response is never empty.
    """
    # Re-resolve library summary (< 1 s, avoids passing large string across API)
    resolver = default_resolver(include_web=False)
    with phase_timer("eng_spec.summarize", project_id=req.project_id):
        library_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    # 1. Extract module-level nodes from the tree
    modules = _extract_modules(req.subsystems)

    all_drafts: list[EngineeringSpecDraft] = []

    # 2. Per-module two-stage generation (parallel)
    if modules:
        with ThreadPoolExecutor(max_workers=min(len(modules), 4)) as pool:
            futures = {
                pool.submit(
                    _generate_module_specs,
                    module=mod,
                    mission=req.mission,
                    library_summary=library_summary,
                    project_id=req.project_id,
                ): mod.name
                for mod in modules
            }
            for future in as_completed(futures):
                mod_name = futures[future]
                try:
                    module_drafts = future.result()
                    all_drafts.extend(module_drafts)
                except Exception as exc:
                    logger.error(
                        "eng_spec step2: module '%s' failed entirely: %s",
                        mod_name,
                        exc,
                    )
                    emit_counter(
                        "eng_spec.step2_module_error",
                        value=1,
                        project_id=req.project_id,
                        module=mod_name,
                    )

    # 3. System-level nodes get a simplified single-call pass
    system_nodes = [s for s in req.subsystems if s.level == "system"]
    system_drafts = _generate_system_level_specs(
        systems=system_nodes,
        mission=req.mission,
        library_summary=library_summary,
        project_id=req.project_id,
    )
    all_drafts.extend(system_drafts)

    emit_counter(
        "eng_spec.step2_done",
        value=1,
        project_id=req.project_id,
        total_drafts=len(all_drafts),
    )

    if not all_drafts:
        emit_counter("eng_spec.step2_empty", value=1, project_id=req.project_id)
        logger.error("eng_spec step2: pipeline returned zero valid drafts")

    return EngSpecStep2Response(drafts=all_drafts)


# ── Incremental per-module endpoints ────────────────────────────────────────


def eng_spec_step2_generate_module(
    req: EngSpecStep2ModuleRequest,
) -> EngSpecStep2ModuleResponse:
    """Generate specs for ONE module (Stage 2a + 2b).

    Called once per module by the frontend to stay within Nginx 300 s.
    Typically finishes in 30-60 s per module.
    """
    # Re-resolve library summary (< 1 s)
    resolver = default_resolver(include_web=False)
    with phase_timer("eng_spec.summarize", project_id=req.project_id):
        lib_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    drafts = _generate_module_specs(
        module=req.module_node,
        mission=req.mission,
        library_summary=lib_summary,
        project_id=req.project_id,
    )

    emit_counter(
        "eng_spec.step2_module_done",
        value=1,
        project_id=req.project_id,
        module=req.module_name,
        draft_count=len(drafts),
    )

    return EngSpecStep2ModuleResponse(
        module_name=req.module_name,
        drafts=drafts,
    )


def eng_spec_step2_generate_system(
    req: EngSpecStep2SystemRequest,
) -> EngSpecStep2SystemResponse:
    """Generate specs for system-level (non-module) nodes only.

    Typically fast (< 30 s) because system nodes are few.
    """
    # Re-resolve library summary (< 1 s)
    resolver = default_resolver(include_web=False)
    with phase_timer("eng_spec.summarize", project_id=req.project_id):
        lib_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    drafts = _generate_system_level_specs(
        systems=req.subsystems,
        mission=req.mission,
        library_summary=lib_summary,
        project_id=req.project_id,
    )

    emit_counter(
        "eng_spec.step2_system_done",
        value=1,
        project_id=req.project_id,
        draft_count=len(drafts),
    )

    return EngSpecStep2SystemResponse(drafts=drafts)


def eng_spec_step3_strengthen(req: EngSpecStep3Request) -> EngSpecStep3Response:
    """Step 3 — Source Strengthening + Verification Checklist.

    Attempt to upgrade confidence levels by finding better references,
    and produce a verification checklist for all remaining unverified items.
    """
    # Re-resolve library summary (< 1 s)
    resolver = default_resolver(include_web=False)
    with phase_timer("eng_spec.summarize", project_id=req.project_id):
        library_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    current_drafts_json = json.dumps(
        [d.model_dump(mode="json") for d in req.drafts],
        ensure_ascii=False,
        indent=2,
    )
    strengthen_prompt = ENGINEERING_SPEC_STRENGTHEN.format(
        mission=req.mission,
        current_drafts=current_drafts_json,
        reference_library=library_summary,
    )
    with phase_timer("eng_spec.step3_strengthen", project_id=req.project_id):
        raw_strengthen = call_llm_json(ENGINEERING_SPEC_SYSTEM, strengthen_prompt)
    emit_counter("eng_spec.step3_done", value=1, project_id=req.project_id)

    strengthen_data = json.loads(raw_strengthen)
    strengthened_raw: list[dict] = strengthen_data.get("drafts", [])

    # Build a lookup from strengthened output keyed by subsystem_code
    strengthened_map: dict[str, dict] = {
        d["subsystem_code"]: d
        for d in strengthened_raw
        if "subsystem_code" in d
    }

    # Merge strengthened specs back into validated drafts
    final_drafts: list[EngineeringSpecDraft] = []
    for draft in req.drafts:
        if draft.subsystem_code in strengthened_map:
            try:
                upgraded = EngineeringSpecDraft.model_validate(
                    strengthened_map[draft.subsystem_code]
                )
                upgraded.recompute_stats()
                final_drafts.append(upgraded)
            except Exception as exc:
                logger.warning(
                    "eng_spec step3: strengthened draft for %s failed validation, "
                    "keeping original: %s",
                    draft.subsystem_code,
                    exc,
                )
                final_drafts.append(draft)
        else:
            # LLM didn't return a strengthened version — keep original
            final_drafts.append(draft)

    return EngSpecStep3Response(drafts=final_drafts)


def generate_engineering_spec_drafts(
    req: SubsystemSuggestRequest,
) -> EngineeringSpecDraftResponse:
    """Legacy wrapper — calls the 3 split pipeline steps sequentially.

    Kept for backward compatibility so the original
    ``/scamper/engineering-spec-drafts`` endpoint continues to work unchanged.

    Requires ``req.concept_pack`` to be non-None.
    """
    # Step 1 — Structure Expansion + discover_package
    step1 = eng_spec_step1_expand(req)

    # Step 2 — AI Spec Generation
    step2 = eng_spec_step2_generate(
        EngSpecStep2Request(
            project_id=req.project_id,
            mission=req.mission,
            subsystems=step1.subsystems,
        )
    )

    # Step 3 — Source Strengthening
    step3 = eng_spec_step3_strengthen(
        EngSpecStep3Request(
            project_id=req.project_id,
            mission=req.mission,
            drafts=step2.drafts,
            subsystems=step1.subsystems,
        )
    )

    emit_counter(
        "eng_spec.pipeline_complete",
        value=1,
        project_id=req.project_id,
        draft_count=len(step3.drafts),
        tree_count=len(step1.subsystems),
    )

    return EngineeringSpecDraftResponse(
        drafts=step3.drafts,
        subsystem_tree=step1.subsystems,
        package_map=step1.package_map,
    )


# ---------------------------------------------------------------------------
# Engineering Spec Draft Pack — persistence helpers
# ---------------------------------------------------------------------------

def _persist_engineering_spec_draft_pack(
    project_id: str,
    response: EngineeringSpecDraftResponse,
) -> None:
    """Upsert engineering spec draft pack into DB. Non-fatal on failure."""
    try:
        sb = get_supabase()
        sb.table("engineering_spec_draft_packs").upsert(
            {
                "project_id": project_id,
                "drafts_json": response.model_dump(mode="json"),
                "pipeline_version": "v2-4step",
                "step_count": len(response.drafts),
            },
            on_conflict="project_id",
        ).execute()
    except Exception:
        log.warning(
            "Failed to persist engineering spec draft pack for project %s",
            project_id,
            exc_info=True,
        )


def fetch_latest_engineering_spec_draft_pack(
    project_id: str,
) -> EngineeringSpecDraftResponse | None:
    """從資料庫讀取最新的工程規格草案包."""
    try:
        sb = get_supabase()
        result = (
            sb.table("engineering_spec_draft_packs")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        return EngineeringSpecDraftResponse.model_validate(row["drafts_json"])
    except Exception:
        log.warning(
            "fetch_latest_engineering_spec_draft_pack failed for project %s",
            project_id,
            exc_info=True,
        )
        return None


def suggest_subsystems(req: SubsystemSuggestRequest) -> SubsystemSuggestResponse:
    # TODO(L3 WBS §6.1): When L3 WBS ships, this function's input should
    # switch from flat contradictions to LayeredTrizSolution[]. The subsystem_hint
    # enrichment below is a lightweight adapter; the full L3 WBS will replace it
    # with direct LTS consumption.
    # See: docs/e2e/module/Explore_L3_SF_Parallel_Check_WBS.md §6

    # Build a project-scoped resolver so RD overrides for THIS project surface
    # in the prompt vocabulary alongside global learned components and the
    # seed JSON. Web lookup is excluded from the prompt summary because it is
    # an on-demand layer, not an enumerable one.
    resolver = default_resolver(include_web=False)
    with phase_timer("uc1.summarize", project_id=req.project_id):
        library_summary = resolver.summarize_for_prompt(project_id=req.project_id)

    # v7 WP 11.2: merge layered_triz_solutions into the contradiction prompt
    # block. Flat `contradictions` strings remain the back-compat fallback;
    # LTS-derived lines are prepended so the LLM sees the adopted drill-down
    # route first when it's available.
    contradiction_lines: list[str] = []
    if req.layered_triz_solutions:
        contradiction_lines.extend(_serialize_layered_triz_for_f2_prompt(req.layered_triz_solutions))
    contradiction_lines.extend(_enrich_contradiction_lines(req.contradictions))
    contradictions_block = "\n".join(contradiction_lines) or "（無）"

    # 9.5.1 — Prompt instruction: guide LLM to use subsystem hints when present
    subsystem_hint_instruction = (
        "\n如果矛盾文字包含 [子系統提示: ...] 標記，"
        "請將該提示作為 module 層級節點的強建議（優先使用該命名）。"
    )
    contradictions_block += subsystem_hint_instruction

    base_prompt = SUBSYSTEM_SUGGESTION.format(
        mission=req.mission,
        contradictions=contradictions_block,
        existing_subsystems="\n".join(f"- {s}" for s in req.existing_subsystems) or "（無）",
        reference_library=library_summary,
    )

    # First attempt
    with phase_timer("uc1.llm_suggest", attempt=1, project_id=req.project_id):
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, base_prompt)
    data = json.loads(raw)
    _coerce_subsystem_tree(data)
    response = SubsystemSuggestResponse.model_validate(data)

    # Fail-loud 6-dim validation — part of Stage 6 of
    # refactor/subsystem-interface-contracts. We retry ONCE with a targeted
    # instruction listing exactly which fields were empty, then raise if the
    # LLM still can't comply. Silent fallback is forbidden — dropped contracts
    # are exactly the "interface contracts disappearing" bug we're eliminating.
    violations = _find_empty_contracts(response.subsystems)
    if violations:
        emit_counter("uc1.llm_violations", value=len(violations), attempt=1)
        logger.warning(
            "suggest_subsystems: %d interface contracts had empty 6-dim fields "
            "on first attempt; retrying with targeted instruction",
            len(violations),
        )
        retry_prompt = (
            base_prompt
            + "\n\n"
            + _format_violations_for_retry(violations)
        )
        with phase_timer("uc1.llm_suggest", attempt=2, project_id=req.project_id):
            raw = call_llm_json(TRIZ_SOLVER_SYSTEM, retry_prompt)
        data = json.loads(raw)
        _coerce_subsystem_tree(data)
        response = SubsystemSuggestResponse.model_validate(data)

        violations = _find_empty_contracts(response.subsystems)
        if violations:
            emit_counter("uc1.llm_incomplete_final", value=1, project_id=req.project_id)
            # Bubble up a structured error; the FastAPI router will translate
            # this into an HTTP 502 with enough detail for the FE to show the
            # user a meaningful "LLM produced incomplete output, please retry"
            # toast. DO NOT fall back to partial data — that was the exact
            # pattern that caused the contracts-disappearing bug in the first
            # place.
            raise IncompleteLLMResponseError(
                "LLM left required 6-dim interface contract fields blank "
                f"after one retry ({len(violations)} violations remaining)",
                violations=violations,
            )

    # Resolve spatial estimates through the full layered chain (with web
    # lookup ENABLED — we're willing to spend a search call here when the
    # LLM cites web: or an unknown key, to keep the data grounded).
    full_resolver = default_resolver(include_web=True)
    with phase_timer("uc1.resolve_spatial", project_id=req.project_id):
        _resolve_spatial_via_layers(response.subsystems, req.project_id, full_resolver)

    # Discovery: compute the package map from whatever spatial estimates we
    # ended up with. This never blocks the response — if the validator finds
    # nothing useful (e.g., LLM omitted spatial entirely), it returns an empty
    # PackageMap and the caller can ignore it.
    with phase_timer("uc1.discover_package", project_id=req.project_id) as _phase:
        try:
            response.package_map = discover_package(response.subsystems)
        except Exception as exc:  # pragma: no cover - defensive, validator must not break the agent
            emit_counter("uc1.validator_fallback", value=1, error_type=type(exc).__name__)
            logger.warning("spatial validator failed: %s", exc)
            response.package_map = None
            _phase["status"] = "fallback"

    return response


class IncompleteLLMResponseError(Exception):
    """Raised when suggest_subsystems cannot coax a complete response from the
    LLM even after a targeted retry. The router layer translates this into
    HTTP 502 with a structured error body so the FE can surface it meaningfully.
    """

    def __init__(
        self,
        message: str,
        violations: list[tuple[str, str, list[str]]],
    ) -> None:
        super().__init__(message)
        self.violations = violations

    def to_dict(self) -> dict:
        return {
            "error": "incomplete_llm_response",
            "message": str(self),
            "violations": [
                {"owner": o, "neighbour": n, "missing_fields": m}
                for o, n, m in self.violations
            ],
        }


def _format_contracts_for_scamper_prompt(contracts: dict) -> str:
    """Render the RD-confirmed interface_contracts dict into a compact XML-ish
    block that the LLM can read alongside the related_contradictions.

    Falls back to a single line stating that no structured contracts were
    provided so the prompt stays grammatically consistent when the FE hasn't
    sent any (e.g. legacy callers, or a subsystem the LLM never produced
    contracts for). WBS 10.1 — F3 SCAMPER contract consumption.
    """
    if not contracts:
        return "<interface_contracts>（未提供結構化契約，僅依矛盾生成）</interface_contracts>"

    lines = ["<interface_contracts>"]
    for neighbour in sorted(contracts.keys()):
        c = contracts[neighbour]
        # c is an InterfaceContract pydantic model OR a plain dict (after
        # model_validate both shapes work identically via attribute access).
        get = (lambda k: getattr(c, k, "") or "") if hasattr(c, "envelope") else (lambda k: c.get(k, "") or "")
        parts = [
            f"envelope: {get('envelope')}",
            f"loadPath: {get('loadPath')}",
            f"thermalPath: {get('thermalPath')}",
            f"signalPath: {get('signalPath')}",
            f"datumTolerance: {get('datumTolerance')}",
            f"serviceability: {get('serviceability')}",
        ]
        spatial = getattr(c, "spatial", None) if hasattr(c, "envelope") else c.get("spatial")
        if spatial is not None:
            bbox = getattr(spatial, "bbox", None) if hasattr(spatial, "bbox") else spatial.get("bbox")
            mass_g = getattr(spatial, "mass_g", None) if hasattr(spatial, "mass_g") else spatial.get("mass_g")
            if bbox is not None:
                x = getattr(bbox, "x_mm", None) if hasattr(bbox, "x_mm") else bbox.get("x_mm")
                y = getattr(bbox, "y_mm", None) if hasattr(bbox, "y_mm") else bbox.get("y_mm")
                z = getattr(bbox, "z_mm", None) if hasattr(bbox, "z_mm") else bbox.get("z_mm")
                parts.append(f"spatial: {x}x{y}x{z} mm / {mass_g or 0} g")
            elif mass_g is not None:
                parts.append(f"spatial: - / {mass_g} g")
        lines.append(f"↔ {neighbour} ({' | '.join(parts)})")
    lines.append("</interface_contracts>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Directed TRIZ Solver — Direction-centric flow
#
# Replaces the layered drill-down (L1/L2/L3). For each contradiction:
#   Step A: _solve_tc → TC solutions
#   Step B: _derive_pc_from_tc + _solve_pc → PC solutions
#   Step C: derive_su_field_from_tc + _solve_sf → SF solutions
#   Step D: _merge_all_solutions → flat list tagged by path
#   Step E: _cluster_directions → group by implementation direction (LLM)
#   Step F: _score_directions → rate each direction (LLM + rules)
#   Step G: _pick_top_directions → select Top1 + Top2
#   Step H: _decompose_contradiction + _audit_coverage → coverage audit
#           + _apply_coverage_to_scores → re-rank with coverage weight
#   Step I: _compose_combined_direction → combined direction (if coverage < 7.0)
# ---------------------------------------------------------------------------

from app.prompts.triz_solver import (
    DIRECTION_CLUSTER_PROMPT,
    DIRECTION_SCORE_PROMPT,
    COMPATIBILITY_CHECK_PROMPT,
    CONFLICT_REPORT_PROMPT,
    CONTRADICTION_DECOMPOSE_PROMPT,
    RESOLUTION_COVERAGE_AUDIT_PROMPT,
    COMPOSE_COMBINED_DIRECTION_PROMPT,
)
from app.models.schemas import (
    DirectionSolution,
    DirectionGroup,
    DirectionScore,
    ContradictionDirectionResult,
    CompatibilityResult,
    ConflictReport,
    ConsolidationResult,
    SolveDirectedRequest,
    SolveDirectedResponse,
    ConsolidateRequest,
    ConsolidateResponse,
    PersistenceOutcome,
    SubRequirement,
    SrWeakWarning,
    CoverageEntry,
    DirectionCoverageAudit,
    CombinedDirection,
    BriefContextSnapshot,
    BriefConstraint,
    BriefKpi,
    # Phase 2 DecisionCard
    DecisionCard,
    DecisionCardQuickTags,
    DecisionCardCombinationHints,
    ContradictionFace,
    # Phase 3 整併三層 + VerdictLite (取代舊 Q1–Q8 工程審判卡)
    PickedSelection,
    IntraContradictionCompatibility,
    EngineeringVerdictLite,
    BriefItemCheck,
    NextAction,
    # v0.5 (v3) Explore 健檢徽章
    ExploreHealthSummary,
    CoverageStatus,
)


def _merge_all_solutions(
    tc_resp: TrizLookupResponse,
    pc_resp: TrizLookupResponse,
    sf_resp: TrizLookupResponse,
) -> list[DirectionSolution]:
    """Step D: Merge TC + PC + SF suggestions into a flat list of DirectionSolution."""
    merged: list[DirectionSolution] = []

    for s in tc_resp.suggestions:
        merged.append(DirectionSolution(
            path="TC",
            principle_number=s.principle_number,
            principle_name=s.principle_name,
            suggestion=s.suggestion,
            separation_principle=s.separation_principle,
            affected_modules=s.affected_modules,
            secondary_contradictions=s.secondary_contradictions,
        ))

    for s in pc_resp.suggestions:
        merged.append(DirectionSolution(
            path="PC",
            principle_number=s.principle_number,
            principle_name=s.principle_name,
            suggestion=s.suggestion,
            separation_principle=s.separation_principle,
            affected_modules=s.affected_modules,
            secondary_contradictions=s.secondary_contradictions,
        ))

    for s in sf_resp.suggestions:
        merged.append(DirectionSolution(
            path="SF",
            principle_number=s.principle_number,
            principle_name=s.principle_name,
            suggestion=s.suggestion,
            separation_principle=s.separation_principle,
            affected_modules=s.affected_modules,
            secondary_contradictions=s.secondary_contradictions,
        ))

    return merged


def _cluster_directions(
    natural_description: str,
    solutions: list[DirectionSolution],
) -> list[DirectionGroup]:
    """Step E: LLM clusters all solutions by implementation direction.

    Uses index-based clustering: the LLM only returns solution_indices per
    direction, and the code rebuilds full DirectionGroup objects from the
    original solutions list.  Includes orphan reconciliation so no solution
    is ever silently dropped.
    """
    if not solutions:
        return []

    # --- Build numbered solutions block for the prompt ---
    solutions_block = "\n".join(
        f"[{i}] [{s.path}] #{s.principle_number or '-'} {s.principle_name}: {s.suggestion}"
        for i, s in enumerate(solutions)
    )

    prompt = DIRECTION_CLUSTER_PROMPT.format(
        natural_description=natural_description,
        solutions_block=solutions_block,
        total_count=len(solutions),
        max_index=len(solutions) - 1,
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_cluster_directions LLM failed: %s", exc)
        return [_make_fallback_group(solutions, "所有解法歸為同一方向（LLM 分群失敗）")]

    # --- Parse index-based directions from LLM response ---
    directions: list[DirectionGroup] = []
    assigned_indices: set[int] = set()

    for d in data.get("directions", []):
        try:
            indices = [int(idx) for idx in d.get("solution_indices", [])]
            # Filter out-of-range indices
            valid_indices = [i for i in indices if 0 <= i < len(solutions)]
            if not valid_indices:
                logger.debug("Direction %s has no valid indices, skipping", d.get("direction_id"))
                continue

            group_solutions = [solutions[i] for i in valid_indices]
            assigned_indices.update(valid_indices)

            group = DirectionGroup(
                direction_id=d.get("direction_id", f"DIR-{len(directions)+1}"),
                direction_name=d.get("direction_name", "未命名方向"),
                direction_summary=d.get("direction_summary", ""),
                solutions=group_solutions,
                # Force-recompute counts from actual solutions — never trust LLM
                tc_count=sum(1 for s in group_solutions if s.path == "TC"),
                pc_count=sum(1 for s in group_solutions if s.path == "PC"),
                sf_count=sum(1 for s in group_solutions if s.path == "SF"),
            )
            directions.append(group)
        except Exception as exc:
            logger.debug("Dropping malformed direction: %s (%s)", d, exc)

    # --- Orphan reconciliation: catch any solutions the LLM forgot ---
    all_indices = set(range(len(solutions)))
    orphan_indices = all_indices - assigned_indices

    if orphan_indices:
        orphan_solutions = [solutions[i] for i in sorted(orphan_indices)]
        logger.warning(
            "_cluster_directions: %d orphan solution(s) not assigned by LLM "
            "(indices=%s). Creating fallback direction.",
            len(orphan_solutions),
            sorted(orphan_indices),
        )
        directions.append(DirectionGroup(
            direction_id=f"DIR-{len(directions)+1}",
            direction_name="Unclustered solutions",
            direction_summary="LLM 分群未涵蓋的解法，系統自動收容。",
            solutions=orphan_solutions,
            tc_count=sum(1 for s in orphan_solutions if s.path == "TC"),
            pc_count=sum(1 for s in orphan_solutions if s.path == "PC"),
            sf_count=sum(1 for s in orphan_solutions if s.path == "SF"),
        ))

    # If LLM returned empty, fallback
    if not directions:
        return [_make_fallback_group(solutions, "所有解法歸為同一方向")]

    return directions


def _make_fallback_group(solutions: list[DirectionSolution], summary: str) -> DirectionGroup:
    """Create a single fallback DirectionGroup containing all solutions."""
    return DirectionGroup(
        direction_id="DIR-1",
        direction_name="綜合方向",
        direction_summary=summary,
        solutions=solutions,
        tc_count=sum(1 for s in solutions if s.path == "TC"),
        pc_count=sum(1 for s in solutions if s.path == "PC"),
        sf_count=sum(1 for s in solutions if s.path == "SF"),
    )


# ---------------------------------------------------------------------------
# Scoring weight constants (module-level so _apply_coverage_to_scores can reuse)
# ---------------------------------------------------------------------------
WEIGHT_CONSENSUS = 3.0   # cross-tool agreement (0..3 → 0..9)
WEIGHT_FEASIBILITY = 2.0  # LLM feasibility (0..10 → 0..20)
WEIGHT_COST = 1.0         # LLM cost_difficulty (0..10 → 0..10)
WEIGHT_COVERAGE = 4.0     # resolution coverage (0..10 → 0..40) — highest weight
OVER_CLUSTER_THRESHOLD = 6
OVER_CLUSTER_PENALTY = 1.5
COVERAGE_THRESHOLD = 7.0  # below this → trigger combined direction composition


def _score_directions(
    natural_description: str,
    directions: list[DirectionGroup],
) -> list[DirectionScore]:
    """Step F: LLM + rules score each direction."""
    if not directions:
        return []

    directions_block = "\n".join(
        f"- {d.direction_id} 「{d.direction_name}」: {d.direction_summary} "
        f"(TC={d.tc_count}, PC={d.pc_count}, SF={d.sf_count})"
        for d in directions
    )

    prompt = DIRECTION_SCORE_PROMPT.format(
        natural_description=natural_description,
        directions_block=directions_block,
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_score_directions LLM failed: %s — using rule-only fallback", exc)
        data = {}

    llm_scores = {s.get("direction_id"): s for s in data.get("scores", [])}

    scores: list[DirectionScore] = []
    for d in directions:
        raw_count = d.tc_count + d.pc_count + d.sf_count
        # Cross-tool consensus: how many of TC/PC/SF actually contributed?
        # Caps at 3 so a direction with "5 TC + 0 PC + 0 SF" scores LOWER than
        # one with "1 TC + 1 PC + 1 SF" — true triangulation beats stacking.
        consensus = (
            (1 if d.tc_count > 0 else 0)
            + (1 if d.pc_count > 0 else 0)
            + (1 if d.sf_count > 0 else 0)
        )

        llm = llm_scores.get(d.direction_id, {})
        feasibility = float(llm.get("feasibility", 5.0))
        cost_difficulty = float(llm.get("cost_difficulty", 5.0))
        rationale = str(llm.get("score_rationale", ""))

        over_cluster = max(0, raw_count - OVER_CLUSTER_THRESHOLD)
        penalty = over_cluster * OVER_CLUSTER_PENALTY

        weighted = (
            consensus * WEIGHT_CONSENSUS
            + feasibility * WEIGHT_FEASIBILITY
            + cost_difficulty * WEIGHT_COST
            - penalty
        )

        # Keep `tool_support` field name for schema back-compat, but store
        # the consensus value (0-3) — that's the meaningful signal now.
        scores.append(DirectionScore(
            direction_id=d.direction_id,
            tool_support=consensus,
            feasibility=feasibility,
            cost_difficulty=cost_difficulty,
            weighted_total=round(weighted, 2),
            score_rationale=rationale,
        ))

    return scores


def _pick_top_directions(
    directions: list[DirectionGroup],
    scores: list[DirectionScore],
) -> tuple[DirectionGroup | None, DirectionGroup | None, DirectionScore | None, DirectionScore | None]:
    """Step G: Pick Top1 + Top2 by weighted_total descending."""
    if not scores or not directions:
        return None, None, None, None

    score_map = {s.direction_id: s for s in scores}
    sorted_dirs = sorted(
        directions,
        key=lambda d: score_map.get(d.direction_id, DirectionScore()).weighted_total,
        reverse=True,
    )

    top1 = sorted_dirs[0] if len(sorted_dirs) >= 1 else None
    top2 = sorted_dirs[1] if len(sorted_dirs) >= 2 else None
    top1_score = score_map.get(top1.direction_id) if top1 else None
    top2_score = score_map.get(top2.direction_id) if top2 else None

    return top1, top2, top1_score, top2_score


# ---------------------------------------------------------------------------
# Step H / Step I: Resolution Coverage helpers (context-aware)
# ---------------------------------------------------------------------------
#
# The "context-aware coverage audit" refactor (architect plan §三, 方案 A)
# enriches H-1/H-2 with the project's mission / constraints / KPIs /
# socratic insights / CLD summary so each direction is judged against
# the *original problem context*, not the contradiction sentence in
# isolation. Resolution status is then a 5-state semantic verdict that
# both the FE renders directly and the ranker uses to demote
# does_not_resolve / unclear directions.


# ---- Context block formatters -------------------------------------------
# Each returns a human-readable, deterministic block of text that gets
# inlined into the H-1 / H-2 prompts. Returning the literal string
# ``"(未提供)"`` (instead of "") is intentional — it tells the LLM
# *explicitly* that a context channel is missing, which is much safer
# than letting the LLM silently fabricate one.

_NOT_PROVIDED = "(未提供)"


def _format_mission_block(ctx: BriefContextSnapshot) -> str:
    """One-line mission statement or '(未提供)'."""
    return ctx.mission.strip() if ctx.mission and ctx.mission.strip() else _NOT_PROVIDED


def _format_constraints_block(ctx: BriefContextSnapshot) -> str:
    """Bulleted list of constraints with code/type/feasibility tags."""
    if not ctx.constraints:
        return _NOT_PROVIDED
    lines: list[str] = []
    for c in ctx.constraints:
        code = c.code or "C?"
        type_tag = c.type or "hard"
        feas = f", feasibility={c.feasibility}" if c.feasibility and c.feasibility != "unknown" else ""
        lines.append(f"- [{code}][{type_tag}{feas}] {c.description or '(no description)'}")
    return "\n".join(lines)


def _format_kpis_block(ctx: BriefContextSnapshot) -> str:
    """Bulleted list of KPIs with current/target and status."""
    if not ctx.kpis:
        return _NOT_PROVIDED
    lines: list[str] = []
    for k in ctx.kpis:
        name = k.name or "(no name)"
        target = f"{k.target_value} {k.unit}".strip() or "?"
        current = (
            f", current={k.current_value or '—'}/{k.current_status}"
            if k.current_status != "unknown" or k.current_value
            else ""
        )
        lines.append(f"- [{name}] target={target}{current}")
    return "\n".join(lines)


def _format_socratic_block(ctx: BriefContextSnapshot) -> str:
    """Bulleted Q&A pairs; tagged assumptions are marked [ASSUMPTION]."""
    if not ctx.socratic_summary:
        return _NOT_PROVIDED
    lines: list[str] = []
    for s in ctx.socratic_summary:
        tag = "[ASSUMPTION]" if s.is_assumption else f"[{s.category or 'Q'}]"
        q = (s.question or "").strip()
        a = (s.answer or "").strip()
        # One-line each so the LLM can scan quickly; truncate ultra-long
        # answers so a single chatty insight does not dominate the block.
        if len(a) > 240:
            a = a[:240] + "…"
        lines.append(f"- {tag} Q: {q} → A: {a}")
    return "\n".join(lines)


def _format_cld_block(ctx: BriefContextSnapshot) -> str:
    """Render CLD as 'nodes' + 'edges' + 'leverage_points' sections."""
    cld = ctx.cld_summary
    if not cld.nodes and not cld.edges:
        return _NOT_PROVIDED
    parts: list[str] = []
    if cld.leverage_points:
        parts.append("leverage_points: " + ", ".join(cld.leverage_points))
    if cld.nodes:
        node_lines = [
            f"- {n.label}" + (" [LEVERAGE]" if n.is_leverage else "")
            for n in cld.nodes
        ]
        parts.append("nodes:\n" + "\n".join(node_lines))
    if cld.edges:
        edge_lines = [
            f"- {e.from_label} --[{e.polarity}]--> {e.to_label}"
            for e in cld.edges
        ]
        parts.append("edges:\n" + "\n".join(edge_lines))
    return "\n".join(parts)


def _empty_context() -> BriefContextSnapshot:
    """Helper for callers that do not have a context — returns a snapshot
    where every field is empty so prompt formatters emit '(未提供)'."""
    return BriefContextSnapshot()


# ===========================================================================
# Step H-1 (Phase 1 / S0)：演算法為骨、LLM 為皮的 SR 生成流程
#
# 取代舊的 _decompose_contradiction 自由產 3-8 條 SR。新流程：
#   S0a — 純程式列舉候選：2 + |constraints| + |KPIs| 條
#   S0b — LLM 對每條打 0-3 相關性分（唯一可變決策點）
#   S0c — 純程式閥值篩選：score>=2 → SR；score==1 → weak warning；score==0 → 丟棄
#   S0d — LLM 對通過篩選的 SR 改寫單句描述（schema 強制保留 raw_text 數值）
#
# 穩定性保證：同 input → SR 結構（哪幾條、kind、source_ref、順序）100% 一致；
# 描述字句允許 5% 內小差異。詳細設計見 plans/triz-redesign.md §2。
# ===========================================================================

@dataclass
class SrCandidate:
    """純值物件：列舉出來的候選 SR。"""
    candidate_id: int                       # 從 1 開始的穩定編號
    kind: str                               # SubRequirementKind 之一
    source_ref: str                         # "contradiction" | "constraint:Cx" | "kpi:Kx"
    raw_text: str                           # 原始描述（不被 LLM 改寫）
    extras: dict = dc_field(default_factory=dict)


# ---- S0a: 純函式候選列舉 ---------------------------------------------------

def _enumerate_sr_candidates(
    natural_description: str,
    improving_param: int | None,
    worsening_param: int | None,
    ctx: BriefContextSnapshot | None,
) -> list[SrCandidate]:
    """純函式 — 列舉所有 SR 候選。

    同 input → 同 output，無 LLM 介入。對 N 條 constraints + M 條 KPIs 的
    project，永遠列出 ``2 + N + M`` 條候選，順序固定（contradiction 2 條
    在前、constraints 依輸入順序、KPIs 依輸入順序）。
    """
    ctx = ctx or _empty_context()
    cands: list[SrCandidate] = []
    cid = 1

    # === 1. 矛盾本身的兩面：固定 2 條 ===
    from app.tools.triz_kb import get_param_name
    improving_label = get_param_name(improving_param) or "improving side"
    worsening_label = get_param_name(worsening_param) or "worsening side"
    cands.append(SrCandidate(
        candidate_id=cid,
        kind="desired_improvement",
        source_ref="contradiction",
        raw_text=f"想改善：{improving_label}（{natural_description}）",
        extras={"param_id": improving_param, "param_label": improving_label},
    ))
    cid += 1
    cands.append(SrCandidate(
        candidate_id=cid,
        kind="undesired_effect",
        source_ref="contradiction",
        raw_text=f"想避免：{worsening_label}（{natural_description}）",
        extras={"param_id": worsening_param, "param_label": worsening_label},
    ))
    cid += 1

    # === 2. 每條 constraint = 1 條 boundary 候選 ===
    for c in ctx.constraints:
        if not c.code and not c.description:
            continue
        ref_key = c.code if c.code else f"constraint-{cid}"
        cands.append(SrCandidate(
            candidate_id=cid,
            kind="boundary_condition",
            source_ref=f"constraint:{ref_key}",
            raw_text=c.description,
            extras={"type": c.type or "hard", "feasibility": c.feasibility},
        ))
        cid += 1

    # === 3. 每條 KPI = 1 條 mission_outcome 候選 ===
    for k in ctx.kpis:
        if not k.name:
            continue
        # 用 KPI 名稱當 source_ref key — 與 brief 表對齊
        raw = f"{k.name}".strip()
        if k.target_value:
            raw += f" 目標 {k.target_value}"
        if k.unit:
            raw += f" {k.unit}".strip()
        cands.append(SrCandidate(
            candidate_id=cid,
            kind="mission_outcome",
            source_ref=f"kpi:{k.name}",
            raw_text=raw,
            extras={
                "target_value": k.target_value,
                "unit": k.unit,
                "current_value": k.current_value,
                "current_status": k.current_status,
            },
        ))
        cid += 1

    return cands


# ---- S0b: LLM 相關性評分（唯一可變決策點） ---------------------------------

def _score_sr_relevance(
    natural_description: str,
    candidates: list[SrCandidate],
) -> dict[int, dict]:
    """對每條 candidate 打 0-3 相關性分。

    Returns:
        dict: ``candidate_id`` → ``{"score": int, "why": str}``

    強制規則（程式層補強，避免 LLM 翻面）:
    - source_ref == "contradiction" → 永遠 score=3
    - kind == boundary_condition AND extras.type == "hard" → 至少 score=1
    - 缺漏 candidate → fallback score=1（保守當弱相關，不會丟掉資訊）
    """
    if not candidates:
        return {}

    cand_payload = [{
        "candidate_id": c.candidate_id,
        "kind": c.kind,
        "source_ref": c.source_ref,
        "raw_text": c.raw_text,
        "extras": c.extras,
    } for c in candidates]

    prompt = RELEVANCE_SCORING_PROMPT.format(
        natural_description=natural_description,
        candidates_json=json.dumps(cand_payload, ensure_ascii=False, indent=2),
    )

    scored: dict[int, dict] = {}
    try:
        raw = call_llm_json(
            TRIZ_SOLVER_SYSTEM,
            prompt,
            model=settings.fast_model,
            temperature=0,  # S1: 確定性
        )
        data = json.loads(raw) if raw and raw.strip() else {}
        for item in data.get("scores", []):
            try:
                cid = int(item.get("candidate_id"))
                sc = int(item.get("score", 0))
                sc = max(0, min(3, sc))  # clamp 0-3
                scored[cid] = {"score": sc, "why": str(item.get("why") or "").strip()}
            except (TypeError, ValueError):
                continue
    except Exception as exc:  # noqa: BLE001
        logger.warning("_score_sr_relevance LLM failed: %s — falling back to all score=1", exc)

    # === 程式層補強：強制規則 ===
    for c in candidates:
        existing = scored.get(c.candidate_id)
        # Rule 1: contradiction self → score=3
        if c.source_ref == "contradiction":
            scored[c.candidate_id] = {"score": 3,
                                      "why": (existing or {}).get("why") or "矛盾本身"}
            continue
        # Rule 2: hard constraint → score>=1
        if c.kind == "boundary_condition" and c.extras.get("type") == "hard":
            if not existing or existing["score"] < 1:
                scored[c.candidate_id] = {"score": 1,
                                          "why": (existing or {}).get("why") or "hard constraint 至少弱相關"}
                continue
        # Rule 3: 缺漏 fallback
        if not existing:
            scored[c.candidate_id] = {"score": 1, "why": "LLM 漏給分，fallback 弱相關"}

    return scored


# ---- S0c: 純函式閥值篩選 ---------------------------------------------------

def _filter_by_relevance(
    candidates: list[SrCandidate],
    scored: dict[int, dict],
    threshold_strong: int = 2,
    threshold_warning: int = 1,
) -> tuple[list[SrCandidate], list[SrCandidate]]:
    """純函式 — 用閥值切出正式 SR 與弱相關 warning。

    Returns:
        (sr_list, weak_warnings)
        sr_list: score >= threshold_strong 的候選 → 顯示為正式 SR
        weak_warnings: score == threshold_warning 的候選 → ⚠️ tooltip
    """
    sr_list = [c for c in candidates
               if scored.get(c.candidate_id, {}).get("score", 0) >= threshold_strong]
    weak_warnings = [c for c in candidates
                     if scored.get(c.candidate_id, {}).get("score", 0) == threshold_warning]
    return sr_list, weak_warnings


# ---- S0d: LLM 改寫單句描述 -------------------------------------------------

def _rewrite_sr_descriptions(
    natural_description: str,
    sr_candidates: list[SrCandidate],
    scored: dict[int, dict],
) -> list[SubRequirement]:
    """對通過篩選的候選逐條改寫為單句描述。

    Schema 強制保留 raw_text 中的數值與 source_ref（見 SR_REWRITE_PROMPT）。
    任何單條 LLM 改寫失敗 → fallback 用 raw_text 當 description，不影響整體 SR 集合。
    """
    out: list[SubRequirement] = []
    for idx, c in enumerate(sr_candidates, start=1):
        rel = scored.get(c.candidate_id, {})
        score = rel.get("score", 0)

        description = c.raw_text  # fallback
        why_necessary = rel.get("why") or ""
        domain = ""

        try:
            prompt = SR_REWRITE_PROMPT.format(
                kind=c.kind,
                source_ref=c.source_ref,
                raw_text=c.raw_text,
                contradiction_desc=natural_description,
            )
            raw = call_llm_json(
                TRIZ_SOLVER_SYSTEM,
                prompt,
                model=settings.fast_model,
                temperature=0,  # S1: 確定性
            )
            data = json.loads(raw) if raw and raw.strip() else {}
            description = str(data.get("description") or c.raw_text).strip()
            why_necessary = str(data.get("why_necessary") or why_necessary).strip()
            domain = str(data.get("domain") or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "_rewrite_sr_descriptions failed for candidate_id=%s, using raw_text: %s",
                c.candidate_id, exc,
            )

        out.append(SubRequirement(
            id=f"SR-{idx}",
            kind=c.kind,
            source_ref=c.source_ref,
            description=description,
            why_necessary=why_necessary,
            domain=domain,
            raw_text=c.raw_text,
            candidate_id=c.candidate_id,
            relevance_score=score,
        ))
    return out


# ---- S0 entrypoint: orchestrate four steps --------------------------------

def _decompose_contradiction(
    natural_description: str,
    ctx: BriefContextSnapshot | None = None,
    *,
    improving_param: int | None = None,
    worsening_param: int | None = None,
    return_weak_warnings: bool = False,
) -> list[SubRequirement] | tuple[list[SubRequirement], list[SrWeakWarning]]:
    """Step H-1 (Phase 1 / S0)：演算法為骨的 SR 生成。

    四步驟流程：
      1. _enumerate_sr_candidates — 純程式列舉
      2. _score_sr_relevance     — LLM 0-3 分（唯一決策點）
      3. _filter_by_relevance    — 純程式閥值篩選
      4. _rewrite_sr_descriptions— LLM 改寫單句

    Args:
        natural_description: 矛盾自然語言描述
        ctx: BriefContextSnapshot（mission / constraints / KPIs / socratic / cld）
        improving_param / worsening_param: TRIZ 39 參數 id（用於 contradiction 兩面標籤）
        return_weak_warnings: True → 回傳 (sr_list, weak_warnings) tuple

    Returns:
        list[SubRequirement] 或 (list[SubRequirement], list[SrWeakWarning])
    """
    ctx = ctx or _empty_context()

    # 1. 列舉候選
    candidates = _enumerate_sr_candidates(
        natural_description=natural_description,
        improving_param=improving_param,
        worsening_param=worsening_param,
        ctx=ctx,
    )
    if not candidates:
        logger.warning("_decompose_contradiction: no candidates enumerated")
        return ([], []) if return_weak_warnings else []

    # 2. 相關性評分
    scored = _score_sr_relevance(natural_description, candidates)

    # 3. 閥值篩選
    sr_cands, weak_cands = _filter_by_relevance(candidates, scored)

    # 4. 改寫描述
    sr_list = _rewrite_sr_descriptions(natural_description, sr_cands, scored)

    if not sr_list:
        logger.warning("_decompose_contradiction returned 0 sub-requirements after S0 pipeline")

    if return_weak_warnings:
        weak_warnings = [
            SrWeakWarning(
                candidate_id=c.candidate_id,
                kind=c.kind,
                source_ref=c.source_ref,
                raw_text=c.raw_text,
                relevance_score=scored.get(c.candidate_id, {}).get("score", 1),
                why_weak=scored.get(c.candidate_id, {}).get("why", ""),
            )
            for c in weak_cands
        ]
        return sr_list, weak_warnings

    return sr_list


# ---- Step H-2: Context-aware coverage audit -------------------------------

def _audit_coverage(
    natural_description: str,
    sub_requirements: list[SubRequirement],
    top_directions: list[DirectionGroup],
    ctx: BriefContextSnapshot | None = None,
) -> list[DirectionCoverageAudit]:
    """Step H-2: Audit each direction against the sub-requirements *and*
    the project context (mission / constraints / KPIs / socratic / CLD).

    Output carries both the numeric coverage_score (used by the
    re-ranker) and the 5-state resolution_status (used by the FE badge
    and by :func:`_apply_coverage_to_scores` for status-based demotion).
    """
    if not sub_requirements or not top_directions:
        return []

    ctx = ctx or _empty_context()

    sr_json = json.dumps(
        [sr.model_dump(mode="json") for sr in sub_requirements],
        ensure_ascii=False,
    )
    dirs_json = json.dumps(
        [
            {
                "direction_id": d.direction_id,
                "direction_name": d.direction_name,
                "direction_summary": d.direction_summary,
                # Affected modules help the LLM reason about constraint /
                # CLD touch-points concretely instead of by name only.
                "affected_modules": sorted({
                    m for s in d.solutions for m in (s.affected_modules or [])
                }),
            }
            for d in top_directions
        ],
        ensure_ascii=False,
    )

    prompt = RESOLUTION_COVERAGE_AUDIT_PROMPT.format(
        natural_description=natural_description,
        sub_requirements_json=sr_json,
        top_directions_json=dirs_json,
        mission_block=_format_mission_block(ctx),
        constraints_block=_format_constraints_block(ctx),
        kpis_block=_format_kpis_block(ctx),
        socratic_block=_format_socratic_block(ctx),
        cld_block=_format_cld_block(ctx),
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_audit_coverage LLM failed: %s", exc)
        return []

    valid_status = {
        "directly_resolves",
        "partially_resolves",
        "conditionally_resolves",
        "does_not_resolve",
        "unclear",
    }
    valid_layer = {"root_cause", "mechanism", "symptom", "unclear"}
    valid_verdict = {
        "directly_solves",
        "partially_solves",
        "needs_verify",
        "violates",
        "not_addressed",
        "unclear",
    }

    def _str_list(raw_val) -> list[str]:
        """Tolerant list-of-strings parser; drops non-string entries."""
        if not isinstance(raw_val, list):
            return []
        return [str(x).strip() for x in raw_val if isinstance(x, (str, int, float)) and str(x).strip()]

    audits: list[DirectionCoverageAudit] = []
    for item in data.get("audits", []):
        try:
            mission_violations = _str_list(item.get("mission_violations"))
            unresolved_gaps = _str_list(item.get("unresolved_gaps"))

            # Build coverage_matrix with verdict + verdict_zh, falling back
            # to a deterministic derivation if the LLM omitted them.
            matrix = _parse_coverage_matrix(
                raw_entries=item.get("coverage_matrix") or [],
                mission_violations=mission_violations,
                unresolved_gaps=unresolved_gaps,
                valid_verdict=valid_verdict,
            )

            status = str(item.get("resolution_status") or "unclear").strip()
            if status not in valid_status:
                logger.debug("audit: invalid resolution_status %r → unclear", status)
                status = "unclear"

            layer = str(item.get("addresses_layer") or "unclear").strip()
            if layer not in valid_layer:
                logger.debug("audit: invalid addresses_layer %r → unclear", layer)
                layer = "unclear"

            audits.append(DirectionCoverageAudit(
                direction_id=str(item.get("direction_id") or ""),
                coverage_matrix=matrix,
                coverage_score=float(item.get("coverage_score", 0.0)),
                unresolved_gaps=unresolved_gaps,
                resolution_status=status,
                key_assumptions=_str_list(item.get("key_assumptions")),
                mission_violations=mission_violations,
                cld_side_effects=_str_list(item.get("cld_side_effects")),
                addresses_layer=layer,
                gap_summary=str(item.get("gap_summary") or ""),
            ))
        except Exception as exc:
            logger.debug("Dropping malformed coverage audit: %s (%s)", item, exc)

    return audits


# ---- Per-SR verdict derivation --------------------------------------------
# When the LLM follows the v3 schema it directly emits `verdict` and
# `verdict_zh` per coverage entry. For legacy LLM output (or partial
# rollout) we deterministically derive a verdict from the score plus
# the audit-level mission_violations / unresolved_gaps lists so the
# SR-grouped UI never sees an "unclear" row when we can do better.
#
# Rule order (first match wins):
#   1. mission_violations mentions this SR  → "violates"
#   2. unresolved_gaps mentions this SR + score == 0
#                                            → "not_addressed"
#   3. score == 2                            → "directly_solves"
#      (downgrade to "needs_verify" if unresolved_gaps mentions this SR)
#   4. score == 1                            → "partially_solves"
#   5. score == 0                            → "not_addressed"
#   6. anything else                         → "unclear"

# Verdict colour / icon labels rendered as plain Chinese fallbacks
# when the LLM did not provide verdict_zh. Keeps the UI usable
# without ever showing an empty cell.
_VERDICT_ZH_DEFAULT: dict[str, str] = {
    "directly_solves": "直接解決這條子需求。",
    "partially_solves": "部分支撐這條，但不是直接解。",
    "needs_verify": "看起來能解，但有條件要先驗證。",
    "violates": "與這條子需求衝突或會違反它。",
    "not_addressed": "這個方向沒有觸及這條。",
    "unclear": "資訊不足，無法判斷。",
}


def _parse_coverage_matrix(
    raw_entries: list,
    *,
    mission_violations: list[str],
    unresolved_gaps: list[str],
    valid_verdict: set[str],
) -> list[CoverageEntry]:
    """Parse coverage_matrix entries with safe verdict fallback.

    Args:
      raw_entries: ``item["coverage_matrix"]`` straight from the LLM
        response (a list of dicts; may be partially malformed).
      mission_violations / unresolved_gaps: audit-level lists used to
        derive ``violates`` / ``not_addressed`` when the LLM did not
        emit a per-pair verdict.
      valid_verdict: the literal set, passed in so we don't import the
        Pydantic Literal here.
    """
    out: list[CoverageEntry] = []
    for e in raw_entries:
        if not isinstance(e, dict):
            continue
        sr_id = str(e.get("sub_requirement_id") or "").strip()
        try:
            score = int(e.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(2, score))   # clamp into [0, 2]
        rationale = str(e.get("rationale", "") or "")

        raw_verdict = str(e.get("verdict") or "").strip()
        verdict_zh = str(e.get("verdict_zh") or "").strip()

        if raw_verdict not in valid_verdict:
            raw_verdict = _derive_verdict(
                sr_id, score, mission_violations, unresolved_gaps,
            )

        if not verdict_zh:
            verdict_zh = _VERDICT_ZH_DEFAULT.get(raw_verdict, _VERDICT_ZH_DEFAULT["unclear"])

        out.append(CoverageEntry(
            sub_requirement_id=sr_id,
            score=score,
            rationale=rationale,
            verdict=raw_verdict,
            verdict_zh=verdict_zh,
        ))
    return out


def _derive_verdict(
    sr_id: str,
    score: int,
    mission_violations: list[str],
    unresolved_gaps: list[str],
) -> str:
    """Deterministic verdict derivation when the LLM omitted it.

    Looks for the sub_requirement_id substring inside the audit-level
    lists; if mission_violations names this SR the row is hard
    ``violates`` regardless of score. unresolved_gaps downgrades a
    score-2 row to ``needs_verify`` (we cannot fully trust it) and a
    score-0 row to ``not_addressed``.
    """
    sid_lower = sr_id.lower() if sr_id else ""

    if sid_lower and any(sid_lower in str(v).lower() for v in mission_violations):
        return "violates"

    has_gap = bool(sid_lower) and any(sid_lower in str(g).lower() for g in unresolved_gaps)

    if score == 2:
        return "needs_verify" if has_gap else "directly_solves"
    if score == 1:
        return "partially_solves"
    # score == 0 or anything weird → not_addressed (or unclear if no SR id)
    if not sr_id:
        return "unclear"
    return "not_addressed"


# ---- Status-based ranking penalty -----------------------------------------
# Multiplier applied to the numeric weighted_total when the 5-state
# resolution_status says a direction does not really resolve its
# contradiction. Even a high coverage_score should not push a
# "does_not_resolve" / "unclear" direction to Top1.
#
# Calibration:
#   directly_resolves     × 1.00 (no demotion)
#   conditionally_resolves× 0.95 (very mild — assumptions are listed
#                                 for RD; not a reason to bury the
#                                 direction)
#   partially_resolves    × 0.80 (visible drop; still surfaced for RD)
#   unclear               × 0.50 (push to the bottom but keep visible)
#   does_not_resolve      × 0.40 (strongest demotion short of removal)
# Numbers chosen so a strong does_not_resolve (weighted_total 60) sinks
# below a mediocre directly_resolves (weighted_total 30) — the design
# rule "5-state verdict overrides the number" from the prompt.
RESOLUTION_STATUS_MULTIPLIER: dict[str, float] = {
    "directly_resolves": 1.00,
    "conditionally_resolves": 0.95,
    "partially_resolves": 0.80,
    "unclear": 0.50,
    "does_not_resolve": 0.40,
}


def _apply_coverage_to_scores(
    scores: list[DirectionScore],
    audits: list[DirectionCoverageAudit],
    directions: list[DirectionGroup],
) -> list[DirectionScore]:
    """Re-compute weighted_total incorporating coverage_score AND the
    5-state resolution_status (context-aware demotion).
    """
    audit_map = {a.direction_id: a for a in audits}
    dir_map = {d.direction_id: d for d in directions}

    new_scores: list[DirectionScore] = []
    for s in scores:
        audit = audit_map.get(s.direction_id)
        cov = audit.coverage_score if audit else 0.0
        status = audit.resolution_status if audit else "unclear"
        # Default to 1.0 if status string somehow not in the map — should
        # not happen because _audit_coverage clamps to the Literal set.
        status_mult = RESOLUTION_STATUS_MULTIPLIER.get(status, 1.0)

        # Recalculate penalty from direction counts
        d = dir_map.get(s.direction_id)
        raw_count = (d.tc_count + d.pc_count + d.sf_count) if d else 0
        over_cluster = max(0, raw_count - OVER_CLUSTER_THRESHOLD)
        penalty = over_cluster * OVER_CLUSTER_PENALTY

        raw_weighted = (
            s.tool_support * WEIGHT_CONSENSUS
            + s.feasibility * WEIGHT_FEASIBILITY
            + s.cost_difficulty * WEIGHT_COST
            + cov * WEIGHT_COVERAGE
            - penalty
        )
        weighted = raw_weighted * status_mult

        if audit:
            # Preserve the audit linkage in the rationale so RD can see
            # WHY a high-coverage direction got demoted to Top3.
            extra = f" [resolution={status}×{status_mult:.2f}]"
            if extra not in s.score_rationale:
                rationale = (s.score_rationale or "") + extra
            else:
                rationale = s.score_rationale
        else:
            rationale = s.score_rationale

        new_scores.append(DirectionScore(
            direction_id=s.direction_id,
            tool_support=s.tool_support,
            feasibility=s.feasibility,
            cost_difficulty=s.cost_difficulty,
            coverage_score=round(cov, 2),
            weighted_total=round(weighted, 2),
            score_rationale=rationale,
        ))

    return new_scores


def _compose_combined_direction(
    natural_description: str,
    sub_requirements: list[SubRequirement],
    audits: list[DirectionCoverageAudit],
    all_directions: list[DirectionGroup],
) -> CombinedDirection | None:
    """Step I: Compose a combined direction from complementary candidates."""
    if not sub_requirements or not audits or not all_directions:
        return None

    sr_json = json.dumps(
        [sr.model_dump(mode="json") for sr in sub_requirements],
        ensure_ascii=False,
    )
    audits_json = json.dumps(
        [a.model_dump(mode="json") for a in audits],
        ensure_ascii=False,
    )
    dirs_json = json.dumps(
        [
            {
                "direction_id": d.direction_id,
                "direction_name": d.direction_name,
                "direction_summary": d.direction_summary,
            }
            for d in all_directions
        ],
        ensure_ascii=False,
    )

    prompt = COMPOSE_COMBINED_DIRECTION_PROMPT.format(
        natural_description=natural_description,
        sub_requirements_json=sr_json,
        coverage_audits_json=audits_json,
        all_directions_json=dirs_json,
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_compose_combined_direction LLM failed: %s", exc)
        return None

    cd = data.get("combined_direction", data)
    if not cd or not cd.get("selected_direction_ids"):
        return None

    try:
        return CombinedDirection(
            selected_direction_ids=cd.get("selected_direction_ids", []),
            total_coverage_score=float(cd.get("total_coverage_score", 0.0)),
            coverage_matrix=cd.get("coverage_matrix", []),
            unresolved_gaps=cd.get("unresolved_gaps", []),
            synergies=str(cd.get("synergies", "")),
            potential_conflicts=str(cd.get("potential_conflicts", "")),
            integration_strategy=str(cd.get("integration_strategy", "")),
        )
    except Exception as exc:
        logger.warning("_compose_combined_direction parse failed: %s", exc)
        return None


# ===========================================================================
# Phase 2: DecisionCard 產出（每條 direction 1 張，給 RD 選購用）
#
# 設計理念見 plans/triz-redesign.md §3。產出時機：在所有 directions /
# scored / SR / coverage_audits 都完成之後，對每條 direction 跑一輪輕量
# LLM call。並發跑減少總延遲；單條失敗 fallback 為「最低資訊」的 card
# 不會擋整體流程。
# ===========================================================================

_DEFAULT_FACE_BADGES = {
    "improving_side": "📈 推 improving",
    "worsening_side": "🛡️ 抑 worsening",
    "both": "⚖️ 兩面兼顧",
    "side_effect": "🌀 處理副作用",
}


def _generate_decision_card_for_direction(
    natural_description: str,
    direction: DirectionGroup,
    score: DirectionScore | None,
    sub_requirements: list[SubRequirement],
    coverage_audit: DirectionCoverageAudit | None,
    other_directions_brief: str,
) -> DecisionCard:
    """為單條 direction 產出 DecisionCard。

    用結構化方式控制 LLM 自由度：
    - resolution_status 從 coverage_audit 帶入（不讓 LLM 自由選）
    - effort 從 score.cost_difficulty 規則式映射（不讓 LLM 自由選）
    - 其餘欄位讓 LLM 填，但 schema 強制
    """
    # 1) 規則式預設值
    if score and score.cost_difficulty:
        cd = score.cost_difficulty
        effort: str = "low" if cd >= 8 else "medium" if cd >= 5 else "high"
    else:
        effort = "medium"

    resolution_status: str = "unclear"
    resolution_one_line = ""
    if coverage_audit:
        resolution_status = getattr(coverage_audit, "resolution_status", "unclear") or "unclear"
        resolution_one_line = (
            getattr(coverage_audit, "gap_summary", "")
            or getattr(coverage_audit, "rationale", "")
            or ""
        )[:60]

    # 2) 準備 prompt 變數
    sample_suggestions = [s.suggestion[:80] for s in direction.solutions[:3]]
    affected_modules = list({m for s in direction.solutions for m in s.affected_modules})[:6]
    sub_req_brief = "\n".join(
        f"- {sr.id} ({sr.kind}, {sr.source_ref}): {sr.description[:60]}"
        for sr in sub_requirements
    ) or "(無)"

    prompt = DECISION_CARD_PROMPT.format(
        natural_description=natural_description[:300],
        sub_requirements_brief=sub_req_brief,
        direction_id=direction.direction_id,
        direction_name=direction.direction_name,
        direction_summary=direction.direction_summary[:300],
        tc_count=direction.tc_count,
        pc_count=direction.pc_count,
        sf_count=direction.sf_count,
        affected_modules=json.dumps(affected_modules, ensure_ascii=False),
        sample_suggestions=json.dumps(sample_suggestions, ensure_ascii=False),
        other_directions_brief=other_directions_brief,
        resolution_status_hint=resolution_status,
    )

    # 3) LLM call（單條失敗 fallback）
    one_liner = direction.direction_summary[:40] or direction.direction_name
    face = "both"
    face_badge = _DEFAULT_FACE_BADGES[face]
    evidence_level = "E2"
    affects_modules_out = affected_modules[:4]
    synergy_with: list[str] = []
    conflict_with: list[str] = []
    best_paired_with: list[str] = []

    try:
        raw = call_llm_json(
            TRIZ_SOLVER_SYSTEM, prompt,
            model=settings.fast_model,
            temperature=0,
        )
        data = json.loads(raw) if raw and raw.strip() else {}

        one_liner = str(data.get("one_liner") or one_liner)[:80]
        cf_raw = str(data.get("contradiction_face") or "both").strip()
        if cf_raw in {"improving_side", "worsening_side", "both", "side_effect"}:
            face = cf_raw
        face_badge = str(data.get("face_badge") or "").strip() or _DEFAULT_FACE_BADGES[face]
        face_badge = face_badge[:20]

        rs_raw = str(data.get("resolution_status") or resolution_status).strip()
        if rs_raw in {
            "directly_resolves", "partially_resolves",
            "conditionally_resolves", "does_not_resolve", "unclear",
        }:
            resolution_status = rs_raw
        resolution_one_line = (
            str(data.get("resolution_one_line") or resolution_one_line)[:120]
        )

        qt = data.get("quick_tags") or {}
        effort_raw = str(qt.get("effort") or effort).strip()
        if effort_raw in {"low", "medium", "high"}:
            effort = effort_raw
        ev_raw = str(qt.get("evidence_level") or evidence_level).strip()
        if ev_raw in {"E0", "E1", "E2", "E3", "E4"}:
            evidence_level = ev_raw
        am = qt.get("affects_modules") or affects_modules_out
        if isinstance(am, list):
            affects_modules_out = [str(x).strip()[:30] for x in am if x][:4]

        ch = data.get("combination_hints") or {}
        for k_in, dst in (
            ("synergy_with", synergy_with),
            ("conflict_with", conflict_with),
            ("best_paired_with", best_paired_with),
        ):
            arr = ch.get(k_in) or []
            if isinstance(arr, list):
                for item in arr[:3]:
                    if item:
                        dst.append(str(item).strip()[:60])
    except Exception as exc:  # noqa: BLE001 — single card failure must not block batch
        logger.warning(
            "DecisionCard LLM failed for direction_id=%s: %s — using fallback",
            direction.direction_id, exc,
        )

    return DecisionCard(
        direction_id=direction.direction_id,
        direction_name=direction.direction_name,
        one_liner=one_liner,
        contradiction_face=face,  # type: ignore[arg-type]
        face_badge=face_badge,
        resolution_status=resolution_status,  # type: ignore[arg-type]
        resolution_one_line=resolution_one_line,
        quick_tags=DecisionCardQuickTags(
            effort=effort,  # type: ignore[arg-type]
            evidence_level=evidence_level,  # type: ignore[arg-type]
            affects_modules=affects_modules_out,
        ),
        combination_hints=DecisionCardCombinationHints(
            synergy_with=synergy_with,
            conflict_with=conflict_with,
            best_paired_with=best_paired_with,
        ),
        picked=False,
    )


def _generate_decision_cards(
    natural_description: str,
    all_directions: list[DirectionGroup],
    scored_directions: list[DirectionScore],
    sub_requirements: list[SubRequirement],
    coverage_audits: list[DirectionCoverageAudit],
) -> list[DecisionCard]:
    """並發為每條 direction 產出 DecisionCard。

    用 ThreadPoolExecutor 把單矛盾 N 個方向的 LLM call 並發化（典型 N ≤ 12）。
    順序由 input order 決定，與 all_directions 對齊。
    """
    if not all_directions:
        return []

    # 預先索引 score / audit
    score_by_dir = {s.direction_id: s for s in scored_directions}
    audit_by_dir = {a.direction_id: a for a in coverage_audits}

    # 對「每條 direction」準備一份 other_directions 簡介，方便 combination_hints 評估
    def _brief_for(skip_id: str) -> str:
        lines = []
        for d in all_directions:
            if d.direction_id == skip_id:
                continue
            lines.append(
                f"- {d.direction_id} {d.direction_name}: "
                f"{(d.direction_summary or '')[:80]}"
            )
        return "\n".join(lines) or "(無其他方向)"

    cards_by_dir: dict[str, DecisionCard] = {}
    with ThreadPoolExecutor(max_workers=min(6, len(all_directions))) as pool:
        future_to_dir = {
            pool.submit(
                _generate_decision_card_for_direction,
                natural_description,
                d,
                score_by_dir.get(d.direction_id),
                sub_requirements,
                audit_by_dir.get(d.direction_id),
                _brief_for(d.direction_id),
            ): d
            for d in all_directions
        }
        for fut in as_completed(future_to_dir):
            d = future_to_dir[fut]
            try:
                cards_by_dir[d.direction_id] = fut.result()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "DecisionCard generation failed for direction_id=%s: %s",
                    d.direction_id, exc,
                )
                cards_by_dir[d.direction_id] = DecisionCard(
                    direction_id=d.direction_id,
                    direction_name=d.direction_name,
                    one_liner=(d.direction_summary or d.direction_name)[:40],
                    contradiction_face="both",
                    face_badge=_DEFAULT_FACE_BADGES["both"],
                    resolution_status="unclear",
                    resolution_one_line="(DecisionCard 生成失敗)",
                )

    # 按 all_directions 順序輸出
    return [cards_by_dir[d.direction_id] for d in all_directions
            if d.direction_id in cards_by_dir]


def solve_triz_directed(req: SolveDirectedRequest) -> SolveDirectedResponse:
    """Main entry: Direction-centric TRIZ solver for ONE contradiction.

    Pipeline:
        Step A (TC) ─┐
        Step B (PC) ─┼─ parallel ─→ Step D (merge) → Step E (cluster)
        Step C (SF) ─┘                → Step F (score) → Step G (top)
                                       → Step H (decompose + coverage audit + re-rank)
                                       → Step I (combined direction if coverage < threshold)
    """
    with phase_timer("solve_triz_directed"):
        # --- Build the BriefContextSnapshot for context-aware H-1/H-2 ---
        # When the caller supplied an explicit snapshot (harness / tests),
        # honour it; otherwise lazy-load from Supabase. Any failure
        # silently degrades to an empty snapshot — the prompt formatters
        # render "(未提供)" so the LLM is told explicitly rather than
        # silently producing a context-blind audit.
        if req.brief_context is not None:
            brief_ctx = req.brief_context
            logger.info(
                "solve_triz_directed: using request-supplied brief_context "
                "(mission=%s constraints=%d kpis=%d socratic=%d cld_nodes=%d)",
                bool(brief_ctx.mission),
                len(brief_ctx.constraints),
                len(brief_ctx.kpis),
                len(brief_ctx.socratic_summary),
                len(brief_ctx.cld_summary.nodes),
            )
        else:
            try:
                from app.services.brief_context import fetch_brief_context
                brief_ctx = fetch_brief_context(req.project_id)
            except Exception as exc:  # noqa: BLE001 — context is optional
                logger.warning(
                    "fetch_brief_context failed for project %s: %s — falling back to empty snapshot",
                    req.project_id,
                    exc,
                )
                brief_ctx = _empty_context()

        # --- Steps A/B/C: TC, PC, SF in parallel via ThreadPoolExecutor ---
        def _do_tc() -> TrizLookupResponse:
            tc_req = TrizLookupRequest(
                project_id=req.project_id,
                contradiction_id=req.contradiction_id,
                natural_description=req.natural_description,
                improving_param=req.improving_param,
                worsening_param=req.worsening_param,
                type="TC",
            )
            try:
                return _solve_tc(tc_req) if (req.improving_param and req.worsening_param) else TrizLookupResponse(suggestions=[])
            except Exception as exc:
                logger.warning("solve_triz_directed: TC failed: %s", exc)
                return TrizLookupResponse(suggestions=[])

        def _do_pc() -> TrizLookupResponse:
            try:
                deepen = _derive_pc_from_tc(
                    natural_description=req.natural_description,
                    improving=req.improving_param,
                    worsening=req.worsening_param,
                )
                pc_statement = deepen.contradiction_statement or req.natural_description
                pc_req = TrizLookupRequest(
                    project_id=req.project_id,
                    contradiction_id=req.contradiction_id,
                    natural_description=req.natural_description,
                    physical_contradiction=pc_statement,
                    type="PC",
                )
                return _solve_pc(pc_req)
            except Exception as exc:
                logger.warning("solve_triz_directed: PC failed: %s", exc)
                return TrizLookupResponse(suggestions=[])

        def _do_sf() -> TrizLookupResponse:
            try:
                from app.agents.analyst import derive_su_field_from_tc
                derived_sf = None
                if isinstance(req.improving_param, int) and isinstance(req.worsening_param, int):
                    derived_sf = derive_su_field_from_tc(
                        improving_param=req.improving_param,
                        worsening_param=req.worsening_param,
                        engineering_statement=req.natural_description,
                        natural_description=req.natural_description,
                    )
                sf_req = TrizLookupRequest(
                    project_id=req.project_id,
                    contradiction_id=req.contradiction_id,
                    natural_description=req.natural_description,
                    sf_substance_1=derived_sf.S1 if derived_sf else None,
                    sf_substance_2=derived_sf.S2 if derived_sf else None,
                    sf_field=derived_sf.F if derived_sf else None,
                    type="SF",
                )
                return _solve_sf(sf_req)
            except Exception as exc:
                logger.warning("solve_triz_directed: SF failed: %s", exc)
                return TrizLookupResponse(suggestions=[])

        with ThreadPoolExecutor(max_workers=3) as pool:
            fut_tc = pool.submit(_do_tc)
            fut_pc = pool.submit(_do_pc)
            fut_sf = pool.submit(_do_sf)
            tc_resp = fut_tc.result()
            pc_resp = fut_pc.result()
            sf_resp = fut_sf.result()

        # --- Step D: Merge ---
        all_solutions = _merge_all_solutions(tc_resp, pc_resp, sf_resp)
        logger.info(
            "solve_triz_directed: merged %d solutions (TC=%d PC=%d SF=%d)",
            len(all_solutions),
            len(tc_resp.suggestions),
            len(pc_resp.suggestions),
            len(sf_resp.suggestions),
        )
        # --- Step E: Cluster ---
        all_directions = _cluster_directions(req.natural_description, all_solutions)

        # --- Step F: Score ---
        scored_directions = _score_directions(req.natural_description, all_directions)

        # --- Step G: Top1 + Top2 (preliminary) ---
        top1, top2, top1_score, top2_score = _pick_top_directions(all_directions, scored_directions)

        # --- Step H: Contradiction Decomposition + Coverage Audit ---
        # Phase 1 (S0): 演算法為骨流程；傳入 improving/worsening 讓 contradiction
        # 兩面候選帶上參數名稱標籤。同時取得 weak_warnings 帶給前端做 ⚠️ tooltip。
        sub_requirements, sr_weak_warnings = _decompose_contradiction(
            req.natural_description,
            brief_ctx,
            improving_param=req.improving_param,
            worsening_param=req.worsening_param,
            return_weak_warnings=True,
        )
        coverage_audits: list[DirectionCoverageAudit] = []
        combined_direction: CombinedDirection | None = None

        if sub_requirements:
            coverage_audits = _audit_coverage(
                req.natural_description, sub_requirements, all_directions, brief_ctx,
            )
            if coverage_audits:
                # Re-rank with coverage scores
                scored_directions = _apply_coverage_to_scores(
                    scored_directions, coverage_audits, all_directions,
                )
                # Re-pick top1/top2 after re-ranking
                top1, top2, top1_score, top2_score = _pick_top_directions(
                    all_directions, scored_directions,
                )

                # --- Step I: Combined Direction (if best coverage < threshold) ---
                best_coverage = max(
                    (a.coverage_score for a in coverage_audits), default=0.0,
                )
                if best_coverage < COVERAGE_THRESHOLD:
                    combined_direction = _compose_combined_direction(
                        req.natural_description,
                        sub_requirements,
                        coverage_audits,
                        all_directions,
                    )
                    logger.info(
                        "solve_triz_directed: best_coverage=%.1f < %.1f, composed combined direction: %s",
                        best_coverage,
                        COVERAGE_THRESHOLD,
                        combined_direction is not None,
                    )

        # --- Phase 2 (A2): DecisionCard per direction（並發跑減少總延遲）---
        decision_cards = _generate_decision_cards(
            natural_description=req.natural_description,
            all_directions=all_directions,
            scored_directions=scored_directions,
            sub_requirements=sub_requirements,
            coverage_audits=coverage_audits,
        )

        result = ContradictionDirectionResult(
            contradiction_id=req.contradiction_id,
            natural_description=req.natural_description,
            severity=req.severity,
            all_solutions=all_solutions,
            all_directions=all_directions,
            scored_directions=scored_directions,
            top1=top1,
            top2=top2,
            top1_score=top1_score,
            top2_score=top2_score,
            sub_requirements=sub_requirements,
            sr_weak_warnings=sr_weak_warnings,
            coverage_audits=coverage_audits,
            combined_direction=combined_direction,
            decision_cards=decision_cards,
        )

        # Persist to DB
        _persist_directed_solution(req.project_id, result)

        emit_counter("triz_directed_solved", severity=req.severity)
        return SolveDirectedResponse(result=result)


def _persist_directed_solution(project_id: str, result: ContradictionDirectionResult) -> None:
    """Upsert directed solution into DB."""
    from app.core.supabase import get_supabase
    try:
        sb = get_supabase()
        dts_id = f"DTS-{result.contradiction_id.replace('C-', '').strip() or 'UNKNOWN'}"
        payload = {
            "id": dts_id,
            "project_id": project_id,
            "contradiction_id": result.contradiction_id,
            "natural_description": result.natural_description,
            "severity": result.severity,
            "all_solutions": [s.model_dump(mode="json") for s in result.all_solutions],
            "all_directions": [d.model_dump(mode="json") for d in result.all_directions],
            "scored_directions": [s.model_dump(mode="json") for s in result.scored_directions],
            "top1": result.top1.model_dump(mode="json") if result.top1 else None,
            "top2": result.top2.model_dump(mode="json") if result.top2 else None,
            "top1_score": result.top1_score.model_dump(mode="json") if result.top1_score else None,
            "top2_score": result.top2_score.model_dump(mode="json") if result.top2_score else None,
            "sub_requirements": [sr.model_dump(mode="json") for sr in result.sub_requirements] if result.sub_requirements else [],
            "coverage_audits": [ca.model_dump(mode="json") for ca in result.coverage_audits] if result.coverage_audits else [],
            "combined_direction": result.combined_direction.model_dump(mode="json") if result.combined_direction else None,
            # Phase 2: DecisionCard + Phase 1 S0c SR weak warnings
            "decision_cards": [dc.model_dump(mode="json") for dc in result.decision_cards] if result.decision_cards else [],
            "sr_weak_warnings": [w.model_dump(mode="json") for w in result.sr_weak_warnings] if result.sr_weak_warnings else [],
        }
        sb.table("directed_triz_solutions").upsert(payload, on_conflict="id").execute()
    except Exception as exc:
        logger.warning("persist directed_triz_solution failed for %s: %s", result.contradiction_id, exc)


def _gc_orphan_directed_solutions(project_id: str) -> int:
    """Lazy GC: 刪除 `directed_triz_solutions` 中 contradiction_id 已不在
    `contradictions` 表的孤兒 row。

    為什麼需要：UI 流程允許 RD 在識別出 contradiction 後跑 /triz/solve-directed
    把 DTS 寫進 DB；之後若 RD 把這條 contradiction 刪了（或它被替換掉），
    contradictions 表的 row 沒了，但 DTS row 還在 → 變成孤兒，整併會把它撈進來
    跨矛盾比對，產出無意義結果。此函式在整併入口被呼叫做懶清理。

    回傳被刪掉的 row 數量；任何 Supabase 錯誤都 swallow（GC 不應該擋住整併）。
    """
    from app.core.supabase import get_supabase

    sb = get_supabase()
    # 先撈出 alive contradiction IDs，再從 DTS 中找出孤兒（避免 NOT IN 在 PostgREST
    # 上需要額外語法支援）。
    alive_resp = (
        sb.table("contradictions")
        .select("id")
        .eq("project_id", project_id)
        .execute()
    )
    alive_ids = {row["id"] for row in (alive_resp.data or [])}

    dts_resp = (
        sb.table("directed_triz_solutions")
        .select("id, contradiction_id")
        .eq("project_id", project_id)
        .execute()
    )
    orphan_pks: list[str] = [
        row["id"]
        for row in (dts_resp.data or [])
        if row.get("contradiction_id") not in alive_ids
    ]

    if not orphan_pks:
        return 0

    # Supabase python client 支援 .in_("id", [...]) 來批次刪
    sb.table("directed_triz_solutions").delete().in_("id", orphan_pks).execute()
    logger.info(
        "GC: removed %d orphan directed_triz_solutions for project %s",
        len(orphan_pks),
        project_id,
    )
    return len(orphan_pks)


# Phase 3 / PR2-Lite / VerdictLite 欄位名單 — 給 fallback / verify 使用
_PHASE3_COLUMNS = (
    "intra_compatibility",
    "verdict_lite",            # ← 取代舊 verdict_card (Q1–Q8)，migration 023
    "was_user_picked",
    "candidate_pools",
    "exhausted_contradictions",
    "total_rounds",
)

# PostgreSQL / PostgREST 「欄位不存在」錯誤的關鍵字（用於辨識 migration 未套用）。
# psycopg2 拋 UndefinedColumn (SQLSTATE 42703)；PostgREST 透過 supabase-py 通常
# 把這類錯誤序列化成 dict {"code": "42703", "message": "column ... does not exist", ...}。
_MISSING_COLUMN_SIGNATURES = (
    "42703",
    "does not exist",
    "column",  # 廣義匹配 PostgREST 訊息
    "PGRST204",  # PostgREST: column not in schema cache
    "schema cache",
)


def _looks_like_missing_column_error(exc: Exception) -> bool:
    """判斷 supabase upsert 拋的 exception 是否屬於『欄位不存在』。

    僅在 message 同時包含 "column" 或 "42703" / "PGRST204" / "schema cache"
    這類**明確**的 schema 錯誤訊號時才回 True，避免把 network / RLS / JSON
    encoding 等錯誤誤判為 schema 問題而 silent pop Phase 3 欄位（這正是
    2026-05 bug 的根因）。
    """
    msg = repr(exc).lower() + " " + str(exc).lower()
    has_column_word = "column" in msg
    has_signature = any(sig.lower() in msg for sig in ("42703", "pgrst204", "schema cache"))
    return has_column_word and has_signature


def _persist_consolidation_result(
    project_id: str,
    result: ConsolidationResult,
    intra_compatibility: list[IntraContradictionCompatibility] | None = None,
    verdict_lite: EngineeringVerdictLite | None = None,
) -> "PersistenceOutcome":
    """Upsert consolidation result into triz_consolidation_results (migration 012).

    Phase 3 (migration 020/021) 寫入 `intra_compatibility` + `was_user_picked`；
    PR2-Lite (migration 022) 寫 `candidate_pools` / `exhausted_contradictions` /
    `total_rounds`；VerdictLite (migration 023) 寫 `verdict_lite`（取代舊 Q1–Q8
    `verdict_card` 欄位）。

    Bug fix (2026-05) — *Fail loud, not silent*：
      - 舊版用 `except Exception as inner_exc: pop Phase 3 columns and retry`
        把**任何**錯誤都當成「migration 未套用」處理，結果一旦發生 network /
        RLS / JSON encoding 等錯誤，就會把 verdict_lite / was_user_picked
        等欄位 silent 清掉，DB 上只剩半殘的 row。重整後使用者就看到舊資料。
      - 新版只在錯誤明確帶有 column-missing signature (42703 / PGRST204) 時
        才退回 legacy schema，並回傳 status="partial"；其他錯誤直接回
        status="failed" 讓 FE 提示重試。
      - 不再使用最外層 broad except 吞錯。Persist 失敗會透過 PersistenceOutcome
        傳遞給 caller，而 caller (consolidate_solutions) 會把它塞進 response。
    """
    from app.core.supabase import get_supabase
    from app.models.schemas import PersistenceOutcome

    try:
        sb = get_supabase()
    except Exception as exc:
        logger.error(
            "_persist_consolidation_result: get_supabase() failed: %s",
            exc,
        )
        return PersistenceOutcome(
            status="failed",
            reason=f"supabase client init failed: {exc}",
            columns_written=[],
        )

    tcr_id = f"TCR-{project_id[:8]}"
    legacy_payload: dict = {
        "id": tcr_id,
        "project_id": project_id,
        "status": result.status,
        "adopted_directions": {
            cid: d.model_dump(mode="json")
            for cid, d in result.adopted_directions.items()
        },
        "conflict_report": result.conflict_report.model_dump(mode="json")
                           if result.conflict_report else None,
        "integration_advice": result.integration_advice or "",
    }
    phase3_payload: dict = {}
    if intra_compatibility is not None:
        phase3_payload["intra_compatibility"] = [
            ic.model_dump(mode="json") for ic in intra_compatibility
        ]
    if verdict_lite is not None:
        phase3_payload["verdict_lite"] = verdict_lite.model_dump(mode="json")
    if result.was_user_picked is not None:
        phase3_payload["was_user_picked"] = dict(result.was_user_picked)
    if result.candidate_pools is not None:
        phase3_payload["candidate_pools"] = {
            cid: [d.model_dump(mode="json") for d in pool]
            for cid, pool in result.candidate_pools.items()
        }
    if result.exhausted_contradictions is not None:
        phase3_payload["exhausted_contradictions"] = list(result.exhausted_contradictions)
    if result.total_rounds is not None:
        phase3_payload["total_rounds"] = result.total_rounds

    full_payload = {**legacy_payload, **phase3_payload}

    # ── 第一次嘗試：完整 payload ───────────────────────────────
    try:
        sb.table("triz_consolidation_results").upsert(full_payload, on_conflict="id").execute()
        logger.info(
            "persisted consolidation result for project %s (status=%s, columns=%d)",
            project_id, result.status, len(full_payload),
        )
        return PersistenceOutcome(
            status="ok",
            reason=None,
            columns_written=list(full_payload.keys()),
        )
    except Exception as inner_exc:
        if _looks_like_missing_column_error(inner_exc):
            # 真的是 migration 未套用 → fallback legacy
            logger.warning(
                "consolidation upsert: detected missing-column error (%s); "
                "falling back to legacy schema. Phase 3 fields WILL NOT persist — "
                "please run `node scripts/run-migration.mjs "
                "supabase/migrations/022_consolidation_candidate_pools.sql` (and 020/021).",
                inner_exc,
            )
            try:
                sb.table("triz_consolidation_results").upsert(
                    legacy_payload, on_conflict="id"
                ).execute()
                return PersistenceOutcome(
                    status="partial",
                    reason=(
                        "Phase 3 / PR2-Lite / VerdictLite columns missing in DB "
                        "(migration 020/021/022/023 not applied). "
                        "verdict_lite / was_user_picked / candidate_pools 等欄位將不會持久化，"
                        "重整後可能丟失審判資料。請執行對應 migration 後重試。"
                    ),
                    columns_written=list(legacy_payload.keys()),
                )
            except Exception as legacy_exc:
                logger.error(
                    "consolidation upsert legacy fallback also failed: %s",
                    legacy_exc,
                )
                return PersistenceOutcome(
                    status="failed",
                    reason=(
                        f"legacy fallback failed after missing-column error: {legacy_exc}"
                    ),
                    columns_written=[],
                )
        else:
            # 非 schema 錯誤 → 不要 silent pop Phase 3 欄位，直接回 failed
            logger.error(
                "consolidation upsert failed (non-schema error): %s",
                inner_exc,
            )
            return PersistenceOutcome(
                status="failed",
                reason=f"upsert failed: {inner_exc}",
                columns_written=[],
            )


# ---------------------------------------------------------------------------
# Cross-contradiction consolidation (§三)
# ---------------------------------------------------------------------------


def _check_compatibility(
    results: list[ContradictionDirectionResult],
) -> list[CompatibilityResult]:
    """LLM checks pairwise compatibility among Top1 directions.

    Feeds the LLM structured engineering facts (affected modules, secondary
    contradictions, solution count breakdown) so compatibility is judged on
    concrete overlap, not on direction-name similarity.
    """
    top1s = [(r.contradiction_id, r.top1) for r in results if r.top1]
    if len(top1s) <= 1:
        return []

    def _format_direction(cid: str, d: DirectionGroup) -> str:
        # Collect every affected module across the solutions inside this
        # direction — this is the key "where does it touch" signal the LLM
        # needs. Dedupe while preserving order.
        modules: list[str] = []
        for s in d.solutions:
            for m in (s.affected_modules or []):
                if m not in modules:
                    modules.append(m)
        secondary: list[str] = []
        for s in d.solutions:
            for c in (s.secondary_contradictions or []):
                if c and c not in secondary:
                    secondary.append(c)
        modules_line = ", ".join(modules) if modules else "(none stated)"
        secondary_line = "; ".join(secondary) if secondary else "(none stated)"
        return (
            f"- Contradiction {cid}\n"
            f"    direction: {d.direction_name}\n"
            f"    summary: {d.direction_summary}\n"
            f"    affected_modules: {modules_line}\n"
            f"    secondary_contradictions: {secondary_line}\n"
            f"    tool_breakdown: TC={d.tc_count} PC={d.pc_count} SF={d.sf_count}"
        )

    top1_block = "\n".join(_format_direction(cid, d) for cid, d in top1s)
    prompt = COMPATIBILITY_CHECK_PROMPT.format(top1_block=top1_block)

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_check_compatibility LLM failed: %s — assuming compatible", exc)
        return []

    pairs: list[CompatibilityResult] = []
    for p in data.get("pairs", []):
        try:
            pairs.append(CompatibilityResult.model_validate(p))
        except Exception:
            continue

    return pairs


def _try_swap_top2(
    results: list[ContradictionDirectionResult],
    conflicts: list[CompatibilityResult],
    initial_adopted: dict[str, DirectionGroup] | None = None,
    pinned_cids: set[str] | None = None,
) -> tuple[dict[str, DirectionGroup], list[CompatibilityResult]]:
    """Try swapping conflicting non-pinned directions → Top2 and re-check.

    Phase 3 changes
    ---------------
    - `initial_adopted` 可由 caller 傳入 (例如已套用 RD picks 的 map)；不傳則沿用
       「每條矛盾用 Top1」的舊行為。
    - `pinned_cids` 是「RD 已勾選、不允許被 swap」的矛盾 ID 集合。
       若所有衝突方都被 pin 住，這個函式不 swap、直接回傳原 adopted + 原 conflicts，
       讓 caller 把它落成 status="conflict" 並標註 user_pinned。

    Returns (adopted_map, remaining_conflicts).
    """
    pinned = pinned_cids or set()
    if initial_adopted is not None:
        adopted: dict[str, DirectionGroup] = dict(initial_adopted)
    else:
        adopted = {r.contradiction_id: r.top1 for r in results if r.top1}

    # Find contradiction IDs involved in conflicts — only consider non-pinned
    # contradictions for swap. If pair (A, B) is in conflict and both pinned,
    # neither is swappable → conflict stays.
    swappable_cids: set[str] = set()
    for c in conflicts:
        if c.compatible:
            continue
        b = c.contradiction_b_id
        a = c.contradiction_a_id
        if b and b not in pinned:
            swappable_cids.add(b)
        elif a and a not in pinned:
            swappable_cids.add(a)

    if not swappable_cids:
        # Nothing legal to swap → return as-is so caller can produce a user_pinned conflict
        return adopted, conflicts

    # Swap Top1 → Top2 for conflicted, non-pinned contradictions
    result_map = {r.contradiction_id: r for r in results}
    for cid in swappable_cids:
        r = result_map.get(cid)
        if r and r.top2:
            adopted[cid] = r.top2
            logger.info(
                "consolidate: swapped %s Top1→Top2 (%s → %s)",
                cid,
                r.top1.direction_name if r.top1 else "?",
                r.top2.direction_name,
            )

    # Re-check compatibility with swapped directions
    top1_block = "\n".join(
        f"- 矛盾 {cid}: 方向「{d.direction_name}」— {d.direction_summary}"
        for cid, d in adopted.items()
    )

    if len(adopted) <= 1:
        return adopted, []

    prompt = COMPATIBILITY_CHECK_PROMPT.format(top1_block=top1_block)
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_try_swap_top2 re-check failed: %s", exc)
        return adopted, conflicts  # assume still conflicting

    remaining: list[CompatibilityResult] = []
    for p in data.get("pairs", []):
        try:
            cr = CompatibilityResult.model_validate(p)
            if not cr.compatible:
                remaining.append(cr)
        except Exception:
            continue

    return adopted, remaining


# ---------------------------------------------------------------------------
# Phase 3 — Intra-contradiction compatibility (同一條矛盾多選)
# ---------------------------------------------------------------------------


def _max_independent_subsets(
    nodes: list[str],
    conflict_pairs: list[tuple[str, str]],
) -> list[list[str]]:
    """純函式：在「衝突圖」上找出所有 maximum independent sets，最大者排前。

    為避免 2^N 爆炸我們在 caller 處限制 N ≤ 6 (= 64 powersets 上限)。
    若 conflict_pairs 為空 → 全集本身就是唯一答案，直接 short-circuit。
    """
    if not conflict_pairs:
        return [list(nodes)] if nodes else []

    conflict_set: set[frozenset[str]] = {frozenset((a, b)) for a, b in conflict_pairs if a != b}
    node_list = list(nodes)
    n = len(node_list)
    best_size = 0
    independent_sets: list[list[str]] = []

    for mask in range(1, 1 << n):
        subset = [node_list[i] for i in range(n) if mask & (1 << i)]
        ok = True
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                if frozenset((subset[i], subset[j])) in conflict_set:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        if len(subset) > best_size:
            best_size = len(subset)
            independent_sets = [subset]
        elif len(subset) == best_size:
            independent_sets.append(subset)

    # 排序使可重現：先按 size 大優先，再按 lexicographic for determinism
    independent_sets.sort(key=lambda s: (-len(s), s))
    return independent_sets


def _check_intra_contradiction_compatibility(
    picks: list[PickedSelection],
    results: list[ContradictionDirectionResult],
) -> list[IntraContradictionCompatibility]:
    """對每條 PickedSelection 跑兩兩 LLM 相容性檢查，並用 max-independent-set 找出
    推薦組合。

    N 上限：6（由 PickedSelection.field_validator 在 schema 層守住，這裡再 defence-in-depth）。
    若同矛盾僅 1 個方向、或沒有 picks → 回空 list。
    """
    if not picks:
        return []

    result_by_cid = {r.contradiction_id: r for r in results}
    reports: list[IntraContradictionCompatibility] = []

    def _check_one(pick: PickedSelection) -> IntraContradictionCompatibility:
        cid = pick.contradiction_id
        ids = pick.picked_direction_ids
        # Defence in depth — schema 應該已守住
        if len(ids) > 6:
            raise ValueError(f"intra compatibility: {cid} 勾選 {len(ids)} > 6 (應由 schema 擋掉)")

        r = result_by_cid.get(cid)
        if not r:
            return IntraContradictionCompatibility(
                contradiction_id=cid,
                picked_direction_ids=ids,
                pairwise_results=[],
                max_compatible_subsets=[ids] if ids else [],
                has_conflict=False,
                recommendation="(找不到對應矛盾的方向清單，跳過相容性檢查)",
            )

        # Look up DirectionGroup objects from all_directions
        dir_by_id: dict[str, DirectionGroup] = {
            d.direction_id: d for d in (r.all_directions or [])
        }
        picked_dirs: list[DirectionGroup] = []
        for did in ids:
            d = dir_by_id.get(did)
            if d is not None:
                picked_dirs.append(d)
        if len(picked_dirs) <= 1:
            return IntraContradictionCompatibility(
                contradiction_id=cid,
                picked_direction_ids=ids,
                pairwise_results=[],
                max_compatible_subsets=[ids] if ids else [],
                has_conflict=False,
                recommendation="(僅勾選 1 個方向，無需相容性檢查)",
            )

        directions_block = "\n".join(
            f"- {d.direction_id}: {d.direction_name}\n    {d.direction_summary}"
            for d in picked_dirs
        )
        prompt = INTRA_COMPATIBILITY_CHECK_PROMPT.format(
            contradiction_desc=r.natural_description or "(矛盾描述未提供)",
            directions_block=directions_block,
        )
        pairwise: list[CompatibilityResult] = []
        recommendation = ""
        try:
            raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
            data = json.loads(raw) if raw and raw.strip() else {}
            for p in data.get("pairs", []):
                try:
                    p.setdefault("contradiction_a_id", cid)
                    p.setdefault("contradiction_b_id", cid)
                    pairwise.append(CompatibilityResult.model_validate(p))
                except Exception:
                    continue
            recommendation = str(data.get("recommendation", "")).strip()
        except Exception as exc:
            logger.warning(
                "_check_intra_contradiction_compatibility LLM failed for %s: %s — assuming compatible",
                cid,
                exc,
            )

        # Build conflict-pair list using direction_id (preferred), fallback to name
        id_lookup_by_name = {d.direction_name: d.direction_id for d in picked_dirs}
        conflict_pairs: list[tuple[str, str]] = []
        for pr in pairwise:
            if pr.compatible:
                continue
            # The LLM may have used direction_name in direction_a/_b; resolve back to ids.
            a_id = id_lookup_by_name.get(pr.direction_a, pr.direction_a)
            b_id = id_lookup_by_name.get(pr.direction_b, pr.direction_b)
            if a_id in ids and b_id in ids:
                conflict_pairs.append((a_id, b_id))

        has_conflict = len(conflict_pairs) > 0
        subsets = _max_independent_subsets(ids, conflict_pairs)
        if not recommendation:
            if not has_conflict:
                recommendation = f"勾選的 {len(ids)} 個方向兩兩相容，可一起整併。"
            elif subsets:
                recommendation = (
                    f"勾選的 {len(ids)} 個方向有衝突；建議組合：{', '.join(subsets[0])}"
                )
            else:
                recommendation = "勾選的方向彼此衝突，建議重新挑選。"

        return IntraContradictionCompatibility(
            contradiction_id=cid,
            picked_direction_ids=ids,
            pairwise_results=pairwise,
            max_compatible_subsets=subsets,
            has_conflict=has_conflict,
            recommendation=recommendation,
        )

    # 並發處理多條矛盾 (各自獨立 LLM call)
    if len(picks) == 1:
        reports.append(_check_one(picks[0]))
    else:
        with ThreadPoolExecutor(max_workers=min(4, len(picks))) as ex:
            futures = {ex.submit(_check_one, p): p for p in picks}
            for fut in as_completed(futures):
                try:
                    reports.append(fut.result())
                except Exception as exc:
                    p = futures[fut]
                    logger.warning(
                        "intra compat check failed for %s: %s", p.contradiction_id, exc
                    )
                    reports.append(
                        IntraContradictionCompatibility(
                            contradiction_id=p.contradiction_id,
                            picked_direction_ids=p.picked_direction_ids,
                            pairwise_results=[],
                            max_compatible_subsets=[p.picked_direction_ids]
                            if p.picked_direction_ids
                            else [],
                            has_conflict=False,
                            recommendation="(相容性檢查暫時失敗，預設視為相容)",
                        )
                    )

    # 保持與 picks 同順序，方便前端對應
    order = {p.contradiction_id: i for i, p in enumerate(picks)}
    reports.sort(key=lambda r: order.get(r.contradiction_id, 9999))
    return reports


def _generate_conflict_report(
    conflicts: list[CompatibilityResult],
    results: list[ContradictionDirectionResult],
    status: str = "conflict",
) -> tuple[ConflictReport, str]:
    """Generate a structured conflict report + integration advice via LLM.

    `status` is one of "compatible" | "resolved_with_swap" | "conflict" and
    controls whether the LLM writes suggestions (conflict path) or purely
    integrative text (compatible / swapped paths).
    """
    conflicts_block = "\n".join(
        f"- {c.direction_a} (contradiction {c.contradiction_a_id}) "
        f"vs {c.direction_b} (contradiction {c.contradiction_b_id}) "
        f"[{c.conflict_type or 'unspecified'}]: {c.reason}"
        for c in conflicts
    ) or "(none)"

    all_directions_block = "\n".join(
        f"- {r.contradiction_id}: "
        f"Top1={r.top1.direction_name if r.top1 else '?'}, "
        f"Top2={r.top2.direction_name if r.top2 else '?'}"
        for r in results
    )

    prompt = CONFLICT_REPORT_PROMPT.format(
        status=status,
        conflicts_block=conflicts_block,
        all_directions_block=all_directions_block,
    )
    
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_generate_conflict_report LLM failed: %s", exc)
        data = {}

    suggestions = data.get("suggestions", [])
    integration_advice = str(data.get("integration_advice", ""))

    report = ConflictReport(
        conflicting_pairs=conflicts,
        suggestions=suggestions,
    )
    return report, integration_advice


# ---------------------------------------------------------------------------
# EngineeringVerdictLite — 對照 Brief 任務的精簡審判 (取代舊 Q1–Q8)
# ---------------------------------------------------------------------------
# 設計理念見 plans/triz-verdict-card-simplification.md。
#
# 改名要點：
#   _generate_engineering_verdict_card → _generate_engineering_verdict_lite
#   ENGINEERING_VERDICT_CARD_PROMPT    → ENGINEERING_VERDICT_LITE_PROMPT
#   EngineeringVerdictCard (Q1–Q8)     → EngineeringVerdictLite (對照 brief)
#
# 為什麼可以放心改：下游 (pre-cad / concept architecture / engineering spec
# drafts) 全都沒讀過 verdict_card / Q1–Q8 任何子欄位，pipeline 是死端點。


def _format_brief_ctx_for_verdict(ctx: BriefContextSnapshot) -> dict[str, str]:
    """Format BriefContextSnapshot into prompt-ready text blocks for VerdictLite."""
    if not ctx:
        return {
            "mission_block": "(未提供)",
            "constraints_block": "(未提供)",
            "kpis_block": "(未提供)",
            "cld_block": "(未提供)",
            "socratic_block": "(未提供)",
        }
    mission_block = ctx.mission or "(未提供)"
    constraints_block = "\n".join(
        f"- [{c.code or '?'} / {c.type or 'soft'}] {c.description}"
        for c in (ctx.constraints or [])
    ) or "(未提供)"
    kpis_block = "\n".join(
        f"- {k.name} {getattr(k, 'operator', '') or '='} {k.target_value} {getattr(k, 'unit', '') or ''}"
        for k in (ctx.kpis or [])
    ) or "(未提供)"
    if ctx.cld_summary and (ctx.cld_summary.nodes or ctx.cld_summary.edges):
        nodes_line = ", ".join(n.label for n in ctx.cld_summary.nodes)
        edges_lines = "\n".join(
            f"- {e.from_label} --[{e.polarity}]--> {e.to_label}"
            for e in ctx.cld_summary.edges
        )
        leverage = ", ".join(ctx.cld_summary.leverage_points or [])
        cld_block = (
            f"nodes: {nodes_line}\n"
            f"edges:\n{edges_lines}\n"
            f"leverage_points: {leverage or '(none)'}"
        )
    else:
        cld_block = "(未提供)"
    if ctx.socratic_summary:
        socratic_block = "\n".join(
            f"- [{getattr(q, 'category', '?')}] Q: {getattr(q, 'question', '')} → A: {getattr(q, 'answer', '')}"
            for q in ctx.socratic_summary
        )
    else:
        socratic_block = "(未提供)"
    return {
        "mission_block": mission_block,
        "constraints_block": constraints_block,
        "kpis_block": kpis_block,
        "cld_block": cld_block,
        "socratic_block": socratic_block,
    }


def _compute_contradiction_coverage(
    consolidation: ConsolidationResult,
    results: list[ContradictionDirectionResult],
) -> tuple[Literal["green", "yellow", "red"], str]:
    """v0.5 (v3) defence-in-depth：程式級計算 Explore 矛盾覆蓋率。

    LLM 算除法常出錯（漏條目、誤把 not_relevant 當未對應），所以由程式
    覆寫 ``contradiction_coverage.level`` / ``label``；只保留 LLM 寫的
    ``details`` 當人話描述。

    規則：
      - 0 矛盾 → green / "（本專案無矛盾）"
      - 覆蓋率 = 1.0 → green
      - 0.5 <= 覆蓋率 < 1.0 → yellow
      - 覆蓋率 < 0.5 → red
    """
    adopted_map = consolidation.adopted_directions or {}
    total = len(results)
    if total == 0:
        return "green", "（本專案無矛盾）"

    adopted = sum(1 for r in results if r.contradiction_id in adopted_map)
    ratio = adopted / total
    if ratio >= 1.0:
        level: Literal["green", "yellow", "red"] = "green"
    elif ratio >= 0.5:
        level = "yellow"
    else:
        level = "red"
    label = f"{adopted} / {total} 條已對應方向"
    return level, label


def _generate_engineering_verdict_lite(
    project_id: str,
    consolidation: ConsolidationResult,
    results: list[ContradictionDirectionResult],
    brief_ctx: BriefContextSnapshot | None,
    consolidation_id: str = "",
) -> EngineeringVerdictLite:
    """對整併方案做「對照 brief 任務」的精簡審判（v0.5 / v3）。

    取代舊 `_generate_engineering_verdict_card` (Q1–Q8 工程審判卡)，因為
    使用者反映 Q1–Q8 結構太複雜、術語太多看不懂；且下游 pipeline (pre-cad /
    concept architecture / engineering spec drafts) 沒有任何 consumer。
    詳設計見 plans/triz-verdict-card-simplification.md。

    v0.5 (v3) 結構性精簡：
      - 拿掉 sr_block / socratic_block 輸入（sub_requirement 是 backend
        內部產物、socratic 是 brief 階段該收完的歷史紀錄）
      - 新增 contradictions_block 輸入，給 LLM 算「Explore 矛盾覆蓋率」
      - 輸出改成 mission_check / constraint_checks / kpi_checks +
        explore_health (contradiction_coverage + cld_warning) + next_actions
      - 結束前用 ``_compute_contradiction_coverage`` 做 defence-in-depth：
        程式級覆寫 ``card.explore_health.contradiction_coverage.level/label``，
        不信任 LLM 算的覆蓋率比例。

    1. 把 brief_ctx (mission/constraints/KPIs/cld) 塞進 prompt
    2. 把整併後 adopted_directions + 每條矛盾的對應方向塞進 prompt
    3. 一次 LLM call 產出 brief 對照版 verdict
    4. LLM 失敗 → 回傳保留結構的空殼 (overall_verdict=needs_revision)，
       避免阻斷主流程
    """
    blocks = _format_brief_ctx_for_verdict(brief_ctx or _empty_context())

    # 整併方案描述
    plan_lines: list[str] = []
    for cid, d in (consolidation.adopted_directions or {}).items():
        plan_lines.append(
            f"- 矛盾 {cid}: {d.direction_id} {d.direction_name}\n"
            f"    摘要: {d.direction_summary}"
        )
    plan_block = "\n".join(plan_lines) or "(整併方案為空)"

    # v0.5 (v3) 新增：contradictions_block —— 讓 LLM 知道有哪些 explore 階段
    # 挖出來的矛盾，以及每條矛盾是否有 adopted direction 對應，方便算覆蓋率。
    adopted_map = consolidation.adopted_directions or {}
    contradictions_lines: list[str] = []
    for r in results:
        cid = r.contradiction_id
        label = (r.natural_description or cid).strip().replace("\n", " ")
        if len(label) > 60:
            label = label[:60] + "…"
        adopted = adopted_map.get(cid)
        if adopted:
            contradictions_lines.append(
                f"- {cid}「{label}」 → adopted: {adopted.direction_id} "
                f"{adopted.direction_name}"
            )
        else:
            contradictions_lines.append(
                f"- {cid}「{label}」 → adopted: (未對應)"
            )
    contradictions_block = "\n".join(contradictions_lines) or "(本專案無矛盾)"

    prompt = ENGINEERING_VERDICT_LITE_PROMPT.format(
        mission_block=blocks["mission_block"],
        constraints_block=blocks["constraints_block"],
        kpis_block=blocks["kpis_block"],
        plan_block=plan_block,
        cld_block=blocks["cld_block"],
        contradictions_block=contradictions_block,
    )

    # default fallback used both on LLM failure & on validation failure
    # v0.5 (v3): fallback 補 explore_health 預設值（程式算的覆蓋率）。
    fb_level, fb_label = _compute_contradiction_coverage(consolidation, results)
    fallback = EngineeringVerdictLite(
        project_id=project_id,
        consolidation_id=consolidation_id,
        overall_verdict="needs_revision",
        overall_headline="自動審判失敗，請手動檢視整併方案是否覆蓋 brief 任務。",
        confidence=0.0,
        explore_health=ExploreHealthSummary(
            contradiction_coverage=CoverageStatus(
                level=fb_level,
                label=fb_label,
            ),
        ),
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except Exception as exc:
        logger.warning("_generate_engineering_verdict_lite LLM failed: %s", exc)
        return fallback

    try:
        # Inject project_id + consolidation_id (LLM is not asked to produce them)
        data.setdefault("project_id", project_id)
        data.setdefault("consolidation_id", consolidation_id)
        card = EngineeringVerdictLite.model_validate(data)
    except Exception as exc:
        logger.warning("EngineeringVerdictLite schema validation failed: %s", exc)
        return fallback

    # Defence in depth — 確保 next_actions 至少 1 條 blocking。
    # 若 LLM 偷懶完全沒給或全部 blocking=False，補一條 placeholder 給 RD 對焦。
    has_blocking = any(a.blocking for a in card.next_actions)
    if not has_blocking:
        logger.warning(
            "VerdictLite next_actions 缺 blocking 條目 (got %d total) — 補 placeholder",
            len(card.next_actions),
        )
        card.next_actions.append(
            NextAction(
                action="人工檢視審判結果，確認是否有未列出的 blocking 驗證項",
                why="LLM 未提供 blocking 行動，可能漏判",
                blocking=True,
                effort_hint="small",
                related_item_ids=[],
            )
        )

    # v0.5 (v3) defence-in-depth：程式級覆寫 contradiction_coverage.level / label。
    # LLM 算除法常出錯（漏條目、誤把 not_relevant 當未對應），所以由程式重算；
    # 只保留 LLM 寫的 details 當人話描述。若 LLM 完全沒給 explore_health，
    # 補一個只含 contradiction_coverage 的最小物件。
    correct_level, correct_label = _compute_contradiction_coverage(
        consolidation, results
    )
    if card.explore_health is None:
        card.explore_health = ExploreHealthSummary(
            contradiction_coverage=CoverageStatus(
                level=correct_level,
                label=correct_label,
            ),
        )
    else:
        card.explore_health.contradiction_coverage.level = correct_level
        card.explore_health.contradiction_coverage.label = correct_label
        # details 保留 LLM 寫的（人話描述），不動。

    return card


# ---------------------------------------------------------------------------
# Phase 3 — main consolidation entry point (picks-aware)
# ---------------------------------------------------------------------------


def _build_candidate_pool(
    pick: PickedSelection | None,
    result: ContradictionDirectionResult,
    intra_report: IntraContradictionCompatibility | None,
) -> list[DirectionGroup]:
    """PR2-Lite (語意 3)：將使用者勾的方向組成「候選池」，依分數降冪排序。

    池規則：
      - **空 picks** → 回 fallback 池 = [top1, top2] 中可用的部分（**僅**用於
        single-contradiction local 路徑或測試；正常多矛盾流程上層應拒絕空 picks）
      - **有 picks** → 池 = 使用者勾的方向，依 scored_directions.weighted_total
        降冪排序；同分時保持 picked_direction_ids 的原序
      - **intra_report 有衝突** → 池順序以 max_compatible_subsets[0] 為優先，
        其餘 picks 排在後面（仍依分數）。這樣演算法在跨矛盾衝突時優先嘗試
        「同矛盾內也相容」的方向組合
      - 找不到對應 DirectionGroup 的 id 直接略過

    Args:
        pick: 該矛盾的 PickedSelection（picked_direction_ids 可能為空）；
              傳 None 等同於 picked_direction_ids 為空
        result: 該矛盾的 ContradictionDirectionResult (含 all_directions / scored_directions)
        intra_report: 該矛盾的同矛盾相容性報告（可選）

    Returns:
        list[DirectionGroup]：依分數降冪 + 同矛盾相容性優先的候選池。
        若連 fallback 都拿不到（top1/top2 都 None），可能回空 list；caller 自行處理。
    """
    dir_by_id = {d.direction_id: d for d in (result.all_directions or [])}
    score_by_id = {s.direction_id: s.weighted_total for s in (result.scored_directions or [])}

    ids = pick.picked_direction_ids if pick else []
    if not ids:
        # Fallback 池（單矛盾 / 測試路徑用）
        pool: list[DirectionGroup] = []
        if result.top1 is not None:
            pool.append(result.top1)
        if result.top2 is not None and (
            result.top1 is None or result.top2.direction_id != result.top1.direction_id
        ):
            pool.append(result.top2)
        return pool

    # 把 picked ids 對應的 DirectionGroup 找出來
    picked_dirs: list[tuple[DirectionGroup, float, int]] = []  # (dir, score, orig_idx)
    for idx, did in enumerate(ids):
        d = dir_by_id.get(did)
        if d is None:
            continue
        picked_dirs.append((d, score_by_id.get(did, 0.0), idx))

    # 預設：分數降冪、同分用 orig_idx 升冪
    picked_dirs.sort(key=lambda x: (-x[1], x[2]))

    # Intra-conflict 優先排序：若 intra_report 有衝突且有 max_compatible_subset，
    # 把該 subset 的方向「整組」提到前面（內部仍依分數排）。
    if (
        intra_report
        and intra_report.has_conflict
        and intra_report.max_compatible_subsets
    ):
        preferred_ids = set(intra_report.max_compatible_subsets[0])
        preferred = [t for t in picked_dirs if t[0].direction_id in preferred_ids]
        rest = [t for t in picked_dirs if t[0].direction_id not in preferred_ids]
        picked_dirs = preferred + rest

    # 去重（保險，理論上 picked_direction_ids 已是 unique）
    seen: set[str] = set()
    pool_out: list[DirectionGroup] = []
    for d, _score, _idx in picked_dirs:
        if d.direction_id in seen:
            continue
        seen.add(d.direction_id)
        pool_out.append(d)
    return pool_out


def _score_for_direction(
    result: ContradictionDirectionResult,
    direction_id: str,
) -> float:
    """查找特定 direction 在 scored_directions 內的 weighted_total，找不到回 0.0。"""
    for s in result.scored_directions or []:
        if s.direction_id == direction_id:
            return float(s.weighted_total)
    return 0.0


def _score_loss_optimized_swap(
    candidate_pools: dict[str, list[DirectionGroup]],
    results_by_cid: dict[str, ContradictionDirectionResult],
    max_rounds: int | None = None,
) -> tuple[
    dict[str, DirectionGroup],
    list["CompatibilityResult"],
    set[str],
    int,
]:
    """PR2-Lite 核心：分數損失最小化候選池演算法。

    每輪策略：
      1. 用當前 assignment 跑 _check_compatibility(LLM)
      2. 若無衝突 → 返回 (assignment, [], exhausted=set(), rounds)
      3. 若有衝突 → collect 衝突涉及的 cids，對每個 cid 計算「換到池內下一名的
         score loss」，選最小者執行 swap
      4. 該 cid 池已用盡 → 加入 exhausted；若所有衝突方都 exhausted → 終止
      5. 偵測 cycle (visited assignment hash) 防死循環

    Args:
        candidate_pools: contradiction_id → 池（依分數降冪）
        results_by_cid: 給 _check_compatibility 用的完整 result（top1 在每輪會被
                        shallow-clone 為當前 assignment[cid]）
        max_rounds: 最大輪次，預設 N + 5

    Returns:
        (final_assignment, remaining_conflicts, exhausted_cids, rounds_executed)
        - rounds_executed: 至少 1（初始 check 也算）
    """
    n = len(candidate_pools)
    if max_rounds is None:
        max_rounds = n + 5

    # 初始 assignment = 每池首位
    pool_idx: dict[str, int] = {cid: 0 for cid in candidate_pools}
    assignment: dict[str, DirectionGroup] = {
        cid: pool[0] for cid, pool in candidate_pools.items() if pool
    }
    exhausted: set[str] = set()
    visited_signatures: set[frozenset] = set()
    rounds_executed = 0

    # 過濾 pools 為空的 cid（理論上不應發生，但 defence-in-depth）
    for cid, pool in candidate_pools.items():
        if not pool:
            exhausted.add(cid)

    for _round in range(max_rounds):
        rounds_executed = _round + 1

        # Step 1：用當前 assignment 跑 LLM 相容性檢查
        # 把 result.top1 替換為當前 assignment 的方向
        synthetic_results: list[ContradictionDirectionResult] = []
        for cid, current_dir in assignment.items():
            r = results_by_cid.get(cid)
            if r is None:
                continue
            synthetic_results.append(r.model_copy(update={"top1": current_dir}))

        compat = _check_compatibility(synthetic_results)
        conflicts = [c for c in compat if not c.compatible]

        if not conflicts:
            return assignment, [], exhausted, rounds_executed

        # Step 2：collect 衝突涉及的 cids
        conflict_cids: set[str] = set()
        for c in conflicts:
            if c.contradiction_a_id:
                conflict_cids.add(c.contradiction_a_id)
            if c.contradiction_b_id:
                conflict_cids.add(c.contradiction_b_id)

        # Step 3：對每個非 exhausted 的衝突 cid 計算 score loss（換池內下一名）
        swap_candidates: list[tuple[str, int, float]] = []  # (cid, new_idx, loss)
        for cid in conflict_cids:
            if cid in exhausted:
                continue
            pool = candidate_pools.get(cid, [])
            cur_idx = pool_idx.get(cid, 0)
            next_idx = cur_idx + 1
            if next_idx >= len(pool):
                # 此池用盡
                exhausted.add(cid)
                continue
            cur_score = _score_for_direction(results_by_cid[cid], pool[cur_idx].direction_id)
            next_score = _score_for_direction(results_by_cid[cid], pool[next_idx].direction_id)
            loss = cur_score - next_score
            swap_candidates.append((cid, next_idx, loss))

        if not swap_candidates:
            # 所有衝突方都用盡 → 卡住
            logger.info(
                "score_loss_optimized_swap: all conflict cids exhausted after round %d",
                rounds_executed,
            )
            return assignment, conflicts, exhausted, rounds_executed

        # Step 4：選 loss 最小者執行 swap（同 loss 取 cid 字母序最小，確保決定性）
        swap_candidates.sort(key=lambda t: (t[2], t[0]))
        chosen_cid, new_idx, chosen_loss = swap_candidates[0]
        old_dir = assignment[chosen_cid]
        new_dir = candidate_pools[chosen_cid][new_idx]
        assignment[chosen_cid] = new_dir
        pool_idx[chosen_cid] = new_idx
        logger.info(
            "score_loss_optimized_swap: round %d swapped %s (%s → %s, loss=%.2f)",
            rounds_executed,
            chosen_cid,
            old_dir.direction_name,
            new_dir.direction_name,
            chosen_loss,
        )

        # Step 5：cycle 偵測
        sig = frozenset((cid, pool_idx[cid]) for cid in candidate_pools)
        if sig in visited_signatures:
            logger.warning(
                "score_loss_optimized_swap: cycle detected at round %d, terminating",
                rounds_executed,
            )
            return assignment, conflicts, exhausted, rounds_executed
        visited_signatures.add(sig)

    # 超過 max_rounds — 回傳當下狀態與最後偵測到的衝突
    logger.warning(
        "score_loss_optimized_swap: exceeded max_rounds=%d, terminating", max_rounds
    )
    # 跑最後一次 check 確認 final conflicts
    synthetic_results = [
        results_by_cid[cid].model_copy(update={"top1": d})
        for cid, d in assignment.items()
        if cid in results_by_cid
    ]
    final_conflicts = [
        c for c in _check_compatibility(synthetic_results) if not c.compatible
    ]
    return assignment, final_conflicts, exhausted, rounds_executed


def consolidate_solutions(req: ConsolidateRequest) -> ConsolidateResponse:
    """Cross-contradiction consolidation (§三) — PR2-Lite 分數損失最小化候選池演算法.

    流程 (語意 3：勾選 = 候選池，演算法選代表)：
      A. GC 孤兒 DTS rows
      B. 若 req.picks 非空 → 跑 intra_compatibility（同矛盾內衝突檢查）
      C. 為每條矛盾用 _build_candidate_pool 建池（picks 為主，沒勾的 fallback top1+top2）
      D. 跑 _score_loss_optimized_swap：初始用各池首位，衝突時換池內下一名（loss 最小者優先）
      E. 整併後跑 _generate_engineering_verdict_lite 產出對照 brief 的精簡審判
      F. 寫入 candidate_pools / exhausted_contradictions / total_rounds 給前端

    Status 語意（PR2-Lite 重新詮釋）：
      - "compatible"          → 各池首位天然相容，演算法 1 輪通過
      - "resolved_with_swap"  → 至少一條非 pinned 矛盾被 swap 到池內非首位才相容
      - "conflict"            → 池用盡 / 超過 max_rounds 仍卡住
    """
    results = req.results
    picks = req.picks or []

    # Lazy GC: 啟動時清掉孤兒 DTS rows（contradiction_id 已不存在 contradictions 表中）。
    try:
        _gc_orphan_directed_solutions(req.project_id)
    except Exception as exc:
        logger.warning("consolidate: orphan DTS GC failed (non-fatal): %s", exc)

    # --- A. 同矛盾相容性檢查（picks 為主，沒勾就空）---
    intra_compat: list[IntraContradictionCompatibility] = []
    if picks:
        intra_compat = _check_intra_contradiction_compatibility(picks, results)
    intra_by_cid = {ic.contradiction_id: ic for ic in intra_compat}

    # --- B. 構建 candidate_pools + 追蹤 user_picked / pinned ---
    result_by_cid = {r.contradiction_id: r for r in results}
    pick_by_cid: dict[str, PickedSelection] = {p.contradiction_id: p for p in picks}
    candidate_pools: dict[str, list[DirectionGroup]] = {}
    pinned_cids: set[str] = set()
    was_user_picked: dict[str, str] = {}

    for r in results:
        cid = r.contradiction_id
        pick = pick_by_cid.get(cid)
        pool = _build_candidate_pool(pick, r, intra_by_cid.get(cid))
        if not pool:
            # 連 top1/top2 fallback 都拿不到 → 跳過此矛盾（已 log warning at solve-directed）
            logger.warning("consolidate: empty candidate pool for %s, skipping", cid)
            continue
        candidate_pools[cid] = pool
        # 追蹤這條矛盾的「初始代表方向」是否來自使用者勾選
        if pick and pick.picked_direction_ids:
            pinned_cids.add(cid)
            was_user_picked[cid] = pool[0].direction_id

    if not candidate_pools:
        # 沒有任何可用池 → 直接回空 conflict（保護性 fallback）
        consolidation = ConsolidationResult(
            status="conflict",
            adopted_directions={},
            conflict_report=None,
            integration_advice="沒有可用的候選方向，請先執行方向導向分析或重新勾選。",
            was_user_picked={},
            candidate_pools={},
            exhausted_contradictions=[],
            total_rounds=0,
        )
        persistence = _persist_consolidation_result(
            req.project_id, consolidation, intra_compat, None
        )
        return ConsolidateResponse(
            consolidation=consolidation,
            intra_compatibility=intra_compat,
            verdict_lite=None,
            # 防呆：unit tests 可能 mock _persist_consolidation_result 為 None，
            # 此時退回預設 PersistenceOutcome(status="ok")。Production 路徑永遠
            # 拿得到完整 PersistenceOutcome。
            persistence=persistence or PersistenceOutcome(),
        )

    # --- C. Build BriefContextSnapshot for VerdictCard (best-effort) ---
    brief_ctx: BriefContextSnapshot | None = None
    try:
        from app.services.brief_context import fetch_brief_context
        brief_ctx = fetch_brief_context(req.project_id)
    except Exception as exc:
        logger.warning(
            "consolidate: fetch_brief_context failed for project %s: %s — VerdictCard will run with empty ctx",
            req.project_id,
            exc,
        )

    consolidation_id = f"TCR-{req.project_id[:8]}"
    initial_assignment = {cid: pool[0] for cid, pool in candidate_pools.items()}

    # --- D. Single-contradiction fast path（不需要跨矛盾相容性比對）---
    if len(candidate_pools) <= 1:
        consolidation = ConsolidationResult(
            status="compatible",
            adopted_directions=dict(initial_assignment),
            conflict_report=None,
            integration_advice=(
                f"唯一矛盾的採納方向：{next(iter(initial_assignment.values())).direction_name}"
                if initial_assignment else ""
            ),
            was_user_picked=was_user_picked,
            candidate_pools=candidate_pools,
            exhausted_contradictions=[],
            total_rounds=0,
        )
        verdict = _generate_engineering_verdict_lite(
            req.project_id, consolidation, results, brief_ctx, consolidation_id
        )
        persistence = _persist_consolidation_result(
            req.project_id, consolidation, intra_compat, verdict
        )
        return ConsolidateResponse(
            consolidation=consolidation,
            intra_compatibility=intra_compat,
            verdict_lite=verdict,
            persistence=persistence or PersistenceOutcome(),
        )

    # --- E. 跑分數損失最小化演算法 ---
    final_assignment, remaining_conflicts, exhausted_cids, rounds_executed = (
        _score_loss_optimized_swap(candidate_pools, result_by_cid)
    )

    # 計算演算法是否「真的 swap 過」
    swapped_any = any(
        final_assignment.get(cid, None) is not None
        and final_assignment[cid].direction_id != initial_assignment[cid].direction_id
        for cid in final_assignment.keys()
    )

    # --- F. 判斷最終 status + 產 conflict_report / advice ---
    if not remaining_conflicts:
        final_status: Literal["compatible", "resolved_with_swap", "conflict"] = (
            "resolved_with_swap" if swapped_any else "compatible"
        )
        _, integration_advice = _generate_conflict_report(
            [], results, status=final_status
        )
        consolidation = ConsolidationResult(
            status=final_status,
            adopted_directions=final_assignment,
            conflict_report=None,
            integration_advice=integration_advice,
            was_user_picked=was_user_picked,
            candidate_pools=candidate_pools,
            exhausted_contradictions=sorted(exhausted_cids),
            total_rounds=rounds_executed,
        )
    else:
        # 卡住 — 標 exhausted；若衝突涉及 pinned cid 加 user_pinned advice
        user_pinned_blocked = any(
            (c.contradiction_a_id in pinned_cids or c.contradiction_b_id in pinned_cids)
            for c in remaining_conflicts
        )
        report, integration_advice = _generate_conflict_report(
            remaining_conflicts, results, status="conflict"
        )
        if user_pinned_blocked:
            integration_advice = (
                "⚠️ 衝突涉及您已勾選的方向，系統未對勾選方向 swap。"
                "請考慮加勾該矛盾的其他候選方向或取消部分勾選。\n"
                + (integration_advice or "")
            )
        consolidation = ConsolidationResult(
            status="conflict",
            adopted_directions=final_assignment,
            conflict_report=report,
            integration_advice=integration_advice,
            was_user_picked=was_user_picked,
            candidate_pools=candidate_pools,
            exhausted_contradictions=sorted(exhausted_cids),
            total_rounds=rounds_executed,
        )

    verdict = _generate_engineering_verdict_lite(
        req.project_id, consolidation, results, brief_ctx, consolidation_id
    )
    persistence = _persist_consolidation_result(
        req.project_id, consolidation, intra_compat, verdict
    )
    return ConsolidateResponse(
        consolidation=consolidation,
        intra_compatibility=intra_compat,
        verdict_lite=verdict,
        persistence=persistence or PersistenceOutcome(),
    )


def scamper_transform(req: ScamperRequest) -> ScamperResponse:
    # WBS 10.1 telemetry: track whether callers are passing structured
    # contracts and whether they send the companion hash. FE should always
    # send the hash once wave-6 ships; the counter lets us spot stragglers.
    emit_counter(
        "scamper.contracts_provided",
        value=1,
        has_contracts=bool(req.interface_contracts),
        project_id=req.project_id,
    )
    if req.interface_contracts and not req.contracts_hash:
        emit_counter(
            "scamper.hash_missing",
            value=1,
            project_id=req.project_id,
            subsystem_name=req.subsystem_name,
        )

    interface_contracts_block = _format_contracts_for_scamper_prompt(req.interface_contracts)
    prompt = SCAMPER_TRANSFORM.format(
        subsystem_name=req.subsystem_name,
        subsystem_description=req.subsystem_description,
        related_contradictions="\n".join(f"- {c}" for c in req.related_contradictions),
        interface_contracts_block=interface_contracts_block,
    )
    raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt)
    data = json.loads(raw)
    return ScamperResponse(**data)
