"""TRIZ Solver Agent — matrix lookup + principle instantiation + SCAMPER.

Ref: AI_Agent_Architecture.md §1.1 TRIZ Solver Agent + §6.2 triz_solver_agent tools
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

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
    # Engineering Spec Pipeline
    ENGINEERING_SPEC_SYSTEM,
    ENGINEERING_SPEC_EXPANSION,
    ENGINEERING_SPEC_GENERATION,
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
)
from app.services import reference_library  # legacy direct access (kept for back-compat)
from app.services.spatial_lookup import LookupQuery, default_resolver
from app.services.spatial_validator import discover_package
from app.observability import emit_counter, phase_timer


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

def generate_engineering_spec_drafts(
    req: SubsystemSuggestRequest,
) -> EngineeringSpecDraftResponse:
    """3-step pipeline: concept architecture pack → detailed engineering spec drafts.

    Step 1 — Structure Expansion:
        Expand concept-level subsystems into a full 3-level hierarchy
        (System → Module → Component) with spatial estimates and interface contracts.

    Step 2 — AI Spec Generation:
        For each subsystem, generate 5-15 DraftValue specs with full provenance
        (source, confidence, needs_verification).

    Step 3 — Source Strengthening:
        Attempt to upgrade confidence levels by finding better references,
        and produce a verification checklist for all remaining unverified items.

    Requires ``req.concept_pack`` to be non-None.

    Returns:
        EngineeringSpecDraftResponse with drafts, subsystem_tree, and package_map.
    """
    if req.concept_pack is None:
        raise ValueError(
            "generate_engineering_spec_drafts requires req.concept_pack to be set. "
            "Use suggest_subsystems() for the legacy (non-concept-pack) path."
        )

    pack = req.concept_pack

    # -- Resolver & library summary (same pattern as suggest_subsystems) -----
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

    # ── Step 1: Structure Expansion ─────────────────────────────────────────
    expansion_prompt = ENGINEERING_SPEC_EXPANSION.format(
        mission=req.mission,
        concept_subsystems=concept_subsystems_json,
        concept_interfaces=concept_interfaces_json,
        reference_library=library_summary,
    )
    with phase_timer("eng_spec.step1_expansion", project_id=req.project_id):
        raw_expansion = call_llm_json(ENGINEERING_SPEC_SYSTEM, expansion_prompt)
    emit_counter("eng_spec.step1_done", value=1, project_id=req.project_id)

    expansion_data = json.loads(raw_expansion)

    # ── Defensive coercion: LLM may emit "spatial": "<string>" instead of an
    #    object or null.  Walk the tree and normalise before model_validate.
    def _coerce_spatial(node: dict) -> None:
        contracts = node.get("interface_contracts")
        if isinstance(contracts, dict):
            for _neighbour, contract in contracts.items():
                if isinstance(contract, dict):
                    sp = contract.get("spatial")
                    if sp is not None and not isinstance(sp, dict):
                        contract["spatial"] = None
        for child in node.get("children") or []:
            if isinstance(child, dict):
                _coerce_spatial(child)

    for _sub in expansion_data.get("subsystems") or []:
        if isinstance(_sub, dict):
            _coerce_spatial(_sub)

    tree_response = SubsystemSuggestResponse.model_validate(expansion_data)

    # Validate 6-dim contracts — retry once if violations found (same as suggest_subsystems)
    violations = _find_empty_contracts(tree_response.subsystems)
    if violations:
        emit_counter("eng_spec.step1_violations", value=len(violations), attempt=1)
        logger.warning(
            "eng_spec step1: %d interface contracts had empty 6-dim fields; retrying",
            len(violations),
        )
        retry_prompt = (
            expansion_prompt + "\n\n" + _format_violations_for_retry(violations)
        )
        with phase_timer("eng_spec.step1_expansion", attempt=2, project_id=req.project_id):
            raw_expansion = call_llm_json(ENGINEERING_SPEC_SYSTEM, retry_prompt)
        expansion_data = json.loads(raw_expansion)
        tree_response = SubsystemSuggestResponse.model_validate(expansion_data)

        violations = _find_empty_contracts(tree_response.subsystems)
        if violations:
            emit_counter("eng_spec.step1_incomplete", value=1, project_id=req.project_id)
            raise IncompleteLLMResponseError(
                "Engineering spec expansion left required 6-dim interface contract "
                f"fields blank after retry ({len(violations)} violations remaining)",
                violations=violations,
            )

    # Resolve spatial estimates through layered chain (web enabled)
    full_resolver = default_resolver(include_web=True)
    with phase_timer("eng_spec.resolve_spatial", project_id=req.project_id):
        _resolve_spatial_via_layers(tree_response.subsystems, req.project_id, full_resolver)

    # Serialise the expanded tree for downstream prompts
    subsystem_tree_json = json.dumps(
        [s.model_dump(mode="json") for s in tree_response.subsystems],
        ensure_ascii=False,
        indent=2,
    )

    # ── Step 2: AI Spec Generation ──────────────────────────────────────────
    generation_prompt = ENGINEERING_SPEC_GENERATION.format(
        mission=req.mission,
        subsystem_tree=subsystem_tree_json,
        reference_library=library_summary,
    )
    with phase_timer("eng_spec.step2_generation", project_id=req.project_id):
        raw_generation = call_llm_json(ENGINEERING_SPEC_SYSTEM, generation_prompt)
    emit_counter("eng_spec.step2_done", value=1, project_id=req.project_id)

    generation_data = json.loads(raw_generation)
    raw_drafts: list[dict] = generation_data.get("drafts", [])

    # Parse and validate each draft
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

    if not drafts:
        emit_counter("eng_spec.step2_empty", value=1, project_id=req.project_id)
        logger.error("eng_spec step2: LLM returned zero valid drafts")

    # ── Step 3: Source Strengthening + Verification Checklist ───────────────
    current_drafts_json = json.dumps(
        [d.model_dump(mode="json") for d in drafts],
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
    for draft in drafts:
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

    # Compute package map
    package_map = None
    with phase_timer("eng_spec.discover_package", project_id=req.project_id) as _phase:
        try:
            package_map = discover_package(tree_response.subsystems)
        except Exception as exc:
            emit_counter(
                "eng_spec.validator_fallback",
                value=1,
                error_type=type(exc).__name__,
            )
            logger.warning("eng_spec: spatial validator failed: %s", exc)
            _phase["status"] = "fallback"

    emit_counter(
        "eng_spec.pipeline_complete",
        value=1,
        project_id=req.project_id,
        draft_count=len(final_drafts),
        tree_count=len(tree_response.subsystems),
    )

    return EngineeringSpecDraftResponse(
        drafts=final_drafts,
        subsystem_tree=tree_response.subsystems,
        package_map=package_map,
    )


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
    SubRequirement,
    CoverageEntry,
    DirectionCoverageAudit,
    CombinedDirection,
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
# Step H / Step I: Resolution Coverage helpers
# ---------------------------------------------------------------------------


def _decompose_contradiction(natural_description: str) -> list[SubRequirement]:
    """Step H-1: Decompose contradiction into physical sub-requirements."""
    prompt = CONTRADICTION_DECOMPOSE_PROMPT.format(
        natural_description=natural_description,
    )
    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_decompose_contradiction LLM failed: %s", exc)
        return []

    subs: list[SubRequirement] = []
    for item in data.get("sub_requirements", []):
        try:
            subs.append(SubRequirement(
                id=item.get("id", f"SR-{len(subs)+1}"),
                domain=item.get("domain", ""),
                description=item.get("description", ""),
                why_necessary=item.get("why_necessary", ""),
            ))
        except Exception as exc:
            logger.debug("Dropping malformed sub_requirement: %s (%s)", item, exc)

    if not subs:
        logger.warning("_decompose_contradiction returned 0 sub-requirements")
    return subs


def _audit_coverage(
    natural_description: str,
    sub_requirements: list[SubRequirement],
    top_directions: list[DirectionGroup],
) -> list[DirectionCoverageAudit]:
    """Step H-2: Audit how well each direction covers the sub-requirements."""
    if not sub_requirements or not top_directions:
        return []

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
            }
            for d in top_directions
        ],
        ensure_ascii=False,
    )

    prompt = RESOLUTION_COVERAGE_AUDIT_PROMPT.format(
        natural_description=natural_description,
        sub_requirements_json=sr_json,
        top_directions_json=dirs_json,
    )

    try:
        raw = call_llm_json(TRIZ_SOLVER_SYSTEM, prompt, model=settings.fast_model)
        data = json.loads(raw) if raw and raw.strip() else {}
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("_audit_coverage LLM failed: %s", exc)
        return []

    audits: list[DirectionCoverageAudit] = []
    for item in data.get("audits", []):
        try:
            matrix = [
                CoverageEntry(
                    sub_requirement_id=e.get("sub_requirement_id", ""),
                    score=int(e.get("score", 0)),
                    rationale=str(e.get("rationale", "")),
                )
                for e in item.get("coverage_matrix", [])
            ]
            audits.append(DirectionCoverageAudit(
                direction_id=item.get("direction_id", ""),
                coverage_matrix=matrix,
                coverage_score=float(item.get("coverage_score", 0.0)),
                unresolved_gaps=item.get("unresolved_gaps", []),
            ))
        except Exception as exc:
            logger.debug("Dropping malformed coverage audit: %s (%s)", item, exc)

    return audits


def _apply_coverage_to_scores(
    scores: list[DirectionScore],
    audits: list[DirectionCoverageAudit],
    directions: list[DirectionGroup],
) -> list[DirectionScore]:
    """Re-compute weighted_total incorporating coverage_score from audits."""
    audit_map = {a.direction_id: a for a in audits}
    dir_map = {d.direction_id: d for d in directions}

    new_scores: list[DirectionScore] = []
    for s in scores:
        audit = audit_map.get(s.direction_id)
        cov = audit.coverage_score if audit else 0.0

        # Recalculate penalty from direction counts
        d = dir_map.get(s.direction_id)
        raw_count = (d.tc_count + d.pc_count + d.sf_count) if d else 0
        over_cluster = max(0, raw_count - OVER_CLUSTER_THRESHOLD)
        penalty = over_cluster * OVER_CLUSTER_PENALTY

        weighted = (
            s.tool_support * WEIGHT_CONSENSUS
            + s.feasibility * WEIGHT_FEASIBILITY
            + s.cost_difficulty * WEIGHT_COST
            + cov * WEIGHT_COVERAGE
            - penalty
        )
        new_scores.append(DirectionScore(
            direction_id=s.direction_id,
            tool_support=s.tool_support,
            feasibility=s.feasibility,
            cost_difficulty=s.cost_difficulty,
            coverage_score=round(cov, 2),
            weighted_total=round(weighted, 2),
            score_rationale=s.score_rationale,
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
        sub_requirements = _decompose_contradiction(req.natural_description)
        coverage_audits: list[DirectionCoverageAudit] = []
        combined_direction: CombinedDirection | None = None

        if sub_requirements:
            coverage_audits = _audit_coverage(
                req.natural_description, sub_requirements, all_directions,
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
            coverage_audits=coverage_audits,
            combined_direction=combined_direction,
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
        }
        sb.table("directed_triz_solutions").upsert(payload, on_conflict="id").execute()
    except Exception as exc:
        logger.warning("persist directed_triz_solution failed for %s: %s", result.contradiction_id, exc)


def _persist_consolidation_result(project_id: str, result: ConsolidationResult) -> None:
    """Upsert consolidation result into triz_consolidation_results (migration 012)."""
    from app.core.supabase import get_supabase
    try:
        sb = get_supabase()
        tcr_id = f"TCR-{project_id[:8]}"
        payload = {
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
        sb.table("triz_consolidation_results").upsert(payload, on_conflict="id").execute()
        logger.info("persisted consolidation result for project %s (status=%s)", project_id, result.status)
    except Exception as exc:
        logger.warning("persist consolidation_result failed for project %s: %s", project_id, exc)


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
) -> tuple[dict[str, DirectionGroup], list[CompatibilityResult]]:
    """Try swapping conflicting Top1 → Top2 and re-check.

    Returns (adopted_map, remaining_conflicts).
    """
    adopted: dict[str, DirectionGroup] = {}
    for r in results:
        if r.top1:
            adopted[r.contradiction_id] = r.top1

    # Find contradiction IDs involved in conflicts
    conflict_cids: set[str] = set()
    for c in conflicts:
        if not c.compatible:
            conflict_cids.add(c.contradiction_b_id)  # swap the "B" side first

    # Swap Top1 → Top2 for conflicted contradictions
    result_map = {r.contradiction_id: r for r in results}
    for cid in conflict_cids:
        r = result_map.get(cid)
        if r and r.top2:
            adopted[cid] = r.top2
            logger.info("consolidate: swapped %s Top1→Top2 (%s → %s)",
                        cid, r.top1.direction_name if r.top1 else "?", r.top2.direction_name)

    # Re-check compatibility with swapped directions
    # Build a mini top1_block with swapped values
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


def consolidate_solutions(req: ConsolidateRequest) -> ConsolidateResponse:
    """Cross-contradiction consolidation (§三).

    1. Collect Top1 from each contradiction.
    2. Check pairwise compatibility.
    3. If all compatible → output plan.
    4. If conflict → swap Top1→Top2 for conflicting side, re-check.
    5. If still conflict → output conflict report.
    """
    results = req.results

    # Step 1: Check compatibility
    compatibility = _check_compatibility(results)
    incompatible = [c for c in compatibility if not c.compatible]

    if not incompatible:
        # All compatible — build adopted map + integration advice
        adopted = {r.contradiction_id: r.top1 for r in results if r.top1}
        _, integration_advice = _generate_conflict_report([], results, status="compatible")
        consolidation = ConsolidationResult(
            status="compatible",
            adopted_directions=adopted,
            conflict_report=None,
            integration_advice=integration_advice,
        )
        _persist_consolidation_result(req.project_id, consolidation)
        return ConsolidateResponse(consolidation=consolidation)

    # Step 2: Try swap
    adopted, remaining = _try_swap_top2(results, incompatible)

    if not remaining:
        # Swap resolved the conflict
        _, integration_advice = _generate_conflict_report([], results, status="resolved_with_swap")
        consolidation = ConsolidationResult(
            status="resolved_with_swap",
            adopted_directions=adopted,
            conflict_report=None,
            integration_advice=integration_advice,
        )
        _persist_consolidation_result(req.project_id, consolidation)
        return ConsolidateResponse(consolidation=consolidation)

    # Step 3: Still conflicting — generate report
    report, integration_advice = _generate_conflict_report(remaining, results, status="conflict")
    consolidation = ConsolidationResult(
        status="conflict",
        adopted_directions=adopted,
        conflict_report=report,
        integration_advice=integration_advice,
    )
    _persist_consolidation_result(req.project_id, consolidation)
    return ConsolidateResponse(consolidation=consolidation)


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
