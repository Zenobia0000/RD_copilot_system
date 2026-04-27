"""Evaluator Agent — risk analysis, convergence scan, MUST evaluation.

Ref: AI_Agent_Architecture.md §1.1 Evaluator Agent + §6.2 evaluator_agent tools
"""

import json

from app.agents.base import call_llm_json
from app.core.config import settings
from app.prompts.evaluator import (
    EVALUATOR_SYSTEM,
    RISK_ANALYSIS,
    CONVERGENCE_SCAN,
    MUST_EVALUATION,
    PRE_CAD_ANALYSIS,
    WANT_CRITERIA_SEED,
    BRIEF_QUALITY_REVIEW,
    DEPTH_QUALITY_REVIEW,
    EXPERIMENT_COVERAGE_REVIEW,
    SOLUTION_VALIDATION_PASSPORT,
)
from app.models.schemas import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    ConvergenceScanRequest,
    ConvergenceScanResponse,
    MustEvaluationRequest,
    MustEvaluationResponse,
    PreCadAnalyzeRequest,
    PreCadAnalyzeResponse,
    SpatialTrace,
    WantSeedRequest,
    WantSeedResponse,
    ValidationPassportRequest,
    ValidationPassportResponse,
)


def analyze_risk(req: RiskAnalysisRequest) -> RiskAnalysisResponse:
    prompt = RISK_ANALYSIS.format(
        alternative_name=req.alternative_name,
        mechanism=req.mechanism,
        assumptions="\n".join(f"- {a}" for a in req.assumptions),
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        return harness_call("evaluator_risk", EVALUATOR_SYSTEM, prompt, RiskAnalysisResponse)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    data = json.loads(raw)
    return RiskAnalysisResponse(**data)


def evaluate_must(req: MustEvaluationRequest) -> MustEvaluationResponse:
    criteria_text = "\n".join(
        f"- {c.id}: {c.label} (來源: {c.source}, 閾值: {c.threshold or '見描述'})"
        for c in req.must_criteria
    )
    prompt = MUST_EVALUATION.format(
        alternative_name=req.alternative_name,
        mechanism=req.mechanism,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（無）",
        must_criteria=criteria_text,
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        return harness_call("evaluator_must", EVALUATOR_SYSTEM, prompt, MustEvaluationResponse)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    data = json.loads(raw)
    return MustEvaluationResponse(**data)


def _spatial_score_from_validator(package) -> int:
    """Deterministic 1–5 score derived from PackageMap arithmetic.

    Rules (cumulative penalties from a perfect 5):
      - −1 per clashing module pair (capped)
      - −1 if total mass exceeds a soft commuter-class threshold of 12 kg
      - −1 if any single module is heavier than 5 kg
      - −1 if required envelope x exceeds 700 mm (rough downtube cap)
    Floor at 1.
    """
    if package is None or not package.nodes:
        return 0  # signal "no evidence"
    score = 5
    distinct_clashes = sum(1 for n in package.nodes if n.clashes)
    score -= min(2, distinct_clashes)
    if package.required.total_mass_g > 12_000:
        score -= 1
    if any((n.spatial.mass_g or 0) > 5_000 for n in package.nodes):
        score -= 1
    if package.required.total_bbox_mm[0] > 700:
        score -= 1
    return max(1, score)


def _format_spatial_evidence(package) -> str:
    """Render the validator output as a compact text block for the prompt."""
    if package is None or not package.nodes:
        return "(empty — no spatial estimates available; use qualitative judgement)"
    lines = [
        f"required_envelope_mm: {package.required.total_bbox_mm[0]:.0f} x "
        f"{package.required.total_bbox_mm[1]:.0f} x {package.required.total_bbox_mm[2]:.0f}",
        f"total_mass_g: {package.required.total_mass_g:.0f}",
        f"module_count: {len(package.nodes)}",
    ]
    clash_pairs = [
        f"{n.name} <-> {', '.join(n.clashes)}" for n in package.nodes if n.clashes
    ]
    lines.append(f"clashes: {clash_pairs if clash_pairs else 'none'}")
    if package.notes:
        lines.append("notes:")
        for note in package.notes:
            lines.append(f"  - {note}")
    lines.append(f"validator_spatial_score: {_spatial_score_from_validator(package)}")
    return "\n".join(lines)


def _build_spatial_trace(package, source: str) -> SpatialTrace:
    """Flatten a PackageMap into the compact SpatialTrace the FE renders.

    Clash pairs are collapsed into undirected unique tuples — PackageMap lists
    each clash once per endpoint, so we deduplicate here (A↔B appears once).
    """
    if package is None or not package.nodes:
        return SpatialTrace(source=source)  # type: ignore[arg-type]

    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str]] = []
    for node in package.nodes:
        for other in node.clashes:
            key = tuple(sorted((node.name, other)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((key[0], key[1]))

    return SpatialTrace(
        total_mass_g=package.required.total_mass_g,
        total_bbox_mm=tuple(package.required.total_bbox_mm),  # type: ignore[arg-type]
        clash_pairs=pairs,
        module_count=len(package.nodes),
        notes=list(package.notes),
        source=source,  # type: ignore[arg-type]
    )


def analyze_pre_cad(req: PreCadAnalyzeRequest) -> PreCadAnalyzeResponse:
    # Compute the deterministic spatial validator output up front, if the
    # caller supplied subsystems. The result feeds the prompt as evidence and
    # also overrides the LLM's spatial_score on the way back.
    from app.services.spatial_validator import discover_package

    package = None
    validator_errored = False
    if req.subsystems:
        try:
            package = discover_package(req.subsystems)
        except Exception:  # pragma: no cover - defensive
            # Validator crashed (unexpected). Record the fact so the trace can
            # surface 'llm_fallback' to the UI instead of silently trusting
            # the LLM's guess.
            validator_errored = True
            package = None

    spatial_evidence = _format_spatial_evidence(package)
    deterministic_spatial = _spatial_score_from_validator(package)

    prompt = PRE_CAD_ANALYSIS.format(
        alternative_name=req.alternative_name,
        mechanism=req.mechanism,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（無）",
        spatial_evidence=spatial_evidence,
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        response = harness_call("evaluator_pre_cad", EVALUATOR_SYSTEM, prompt, PreCadAnalyzeResponse)
    else:
        raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
        data = json.loads(raw)
        response = PreCadAnalyzeResponse(**data)

    # Deterministic override: whenever the caller supplied subsystems, the
    # validator — not the LLM — owns `spatial_score`. Three sub-cases:
    #   1. validator produced a scored PackageMap  → use that score
    #   2. validator returned empty (no spatial)   → neutral fallback of 3
    #      (middle of 1–5) so the LLM's guess cannot sneak through; notes
    #      make clear why.
    #   3. validator raised                        → neutral 3 + source=llm_fallback
    #      so the FE can warn "trace unavailable, score is a neutral fallback".
    if req.subsystems:
        if deterministic_spatial > 0:
            response.spatial_score = deterministic_spatial
            response.package_map = package
            response.spatial_trace = _build_spatial_trace(package, source="validator")
        elif validator_errored:
            response.spatial_score = 3  # neutral; see note above
            response.spatial_trace = _build_spatial_trace(None, source="llm_fallback")
        else:
            # Subsystems present but no spatial data in them → empty PackageMap
            response.spatial_score = 3  # neutral; see note above
            response.spatial_trace = _build_spatial_trace(None, source="empty")
    else:
        # No subsystems at all → legacy LLM-only scoring path. Still attach
        # an empty trace so downstream code can detect the absence uniformly.
        response.spatial_trace = _build_spatial_trace(None, source="empty")

    return response


PhaseBDecision = tuple[str, str]  # (decision, reason) where decision ∈ {"SKIP", "CHECK", "WARN"}


def check_phase_b_conflict(
    *,
    lts_id_a: str | None,
    contradiction_id_a: str,
    layer_a: str | None,
    lts_id_b: str | None,
    contradiction_id_b: str,
    layer_b: str | None,
    directive_same_contradiction_intra_layer: str = "skip",
    directive_cross_contradiction: str = "check",
) -> PhaseBDecision:
    """Structured Phase B conflict checker (v7 §8.3).

    Replaces the legacy "same-contradiction multi-path warning" with the
    three-state intra-LTS vs cross-contradiction logic:

      1. Same contradiction AND same LTS  → drill-down combination → SKIP
      2. Same contradiction, different LTS → WARN (redundant work)
      3. Different contradictions         → CHECK (normal cross-scan)

    The directive values come from `LayeredTrizSolution.phase_b_directive` and
    normally default to `skip` / `check`. Callers may override per-project.

    Ref:
      - docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §8.3 Phase B 偽代碼
      - docs/e2e/module/TRIZ_Layered_Drilldown_Development_WBS.md §6.3
    """
    if contradiction_id_a == contradiction_id_b:
        if lts_id_a and lts_id_b and lts_id_a == lts_id_b:
            return (
                "SKIP" if directive_same_contradiction_intra_layer == "skip" else "CHECK",
                f"intra-LTS cross-layer (L{layer_a} + L{layer_b}) — "
                f"drill-down combination, directive={directive_same_contradiction_intra_layer}",
            )
        return (
            "WARN",
            "same contradiction, different LTS ids — possibly redundant work",
        )
    return (
        "SKIP" if directive_cross_contradiction == "skip" else "CHECK",
        f"cross-contradiction pair ({contradiction_id_a} vs {contradiction_id_b}), "
        f"directive={directive_cross_contradiction}",
    )


def seed_want_criteria(req: WantSeedRequest) -> WantSeedResponse:
    prompt = WANT_CRITERIA_SEED.format(
        mission=req.mission,
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（無）",
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        return harness_call("evaluator_want_seed", EVALUATOR_SYSTEM, prompt, WantSeedResponse)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    data = json.loads(raw)
    return WantSeedResponse(**data)


def _apply_layered_directives(req: ConvergenceScanRequest) -> tuple[list, list[str]]:
    """v7 WP 10.6: Pre-filter alternatives using layered_directives.

    Returns:
      - `alternatives_for_prompt`: the list of alternatives to feed to the LLM
        prompt. For a drill-down group (same lts_id), we keep ONE representative
        whose `name` lists all adopted layers, so the LLM doesn't
        double-count the same LTS across layers when cross-checking.
      - `notes`: human-readable log lines describing what the directive did.

    TODO(L3-WBS §7): When Phase B conflict checking is fully implemented,
    grouping must also respect `parent_contradiction_id` — child PCs
    decomposed from a parent TC share the same causal chain and should NOT
    be treated as competing/conflicting alternatives.
    Ref: TRIZ_Multi_Solution_Adoption_Strategy.md §2.1
         same_contradiction_intra_layer_conflict: skip
    """
    notes: list[str] = []
    if not req.layered_directives:
        return list(req.alternatives), notes

    directive_by_id = {d.alternative_id: d for d in req.layered_directives}
    # Group alternatives by lts_id.
    groups: dict[str, list] = {}
    loose: list = []
    for alt in req.alternatives:
        d = directive_by_id.get(alt.id)
        if d is None:
            loose.append(alt)
            continue
        groups.setdefault(d.lts_id, []).append(alt)

    representatives: list = []
    for lts_id, alts in groups.items():
        if len(alts) == 1:
            representatives.append(alts[0])
            continue
        # Same LTS with multiple alternatives = drill-down combination.
        # Honor the directive: if intra-layer SKIP, collapse into one rep.
        first_directive = directive_by_id[alts[0].id]
        if first_directive.same_contradiction_intra_layer_conflict == "skip":
            rep = alts[0].model_copy(deep=True)
            rep.name = (
                f"{rep.name} [drill-down {lts_id}: "
                f"{len(alts)} layers merged]"
            )
            representatives.append(rep)
            notes.append(
                f"intra-LTS {lts_id}: merged {len(alts)} alternatives into 1 representative (SKIP)"
            )
        else:
            representatives.extend(alts)
            notes.append(f"intra-LTS {lts_id}: directive=check, kept all {len(alts)}")

    combined = representatives + loose
    return combined, notes


def scan_convergence(req: ConvergenceScanRequest) -> ConvergenceScanResponse:
    contradiction_json = json.dumps(
        [c.model_dump() for c in req.contradictions],
        ensure_ascii=False, indent=2,
    )
    mission = req.mission or "（未提供）"
    constraints = "\n".join(f"- {c}" for c in req.constraints) or "（尚無）"
    kpis = "\n".join(f"- {k}" for k in req.kpis) or "（尚無）"

    alternatives_for_prompt, skip_notes = _apply_layered_directives(req)
    if skip_notes:
        import logging
        logging.getLogger(__name__).info(
            "Phase B: applied %d layered directives: %s",
            len(req.layered_directives), "; ".join(skip_notes),
        )
    prompt = CONVERGENCE_SCAN.format(
        alternatives=json.dumps(
            [a.model_dump() for a in alternatives_for_prompt],
            ensure_ascii=False, indent=2,
        ),
        contradictions=contradiction_json,
        mission=mission, constraints=constraints, kpis=kpis,
    )

    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        result = harness_call("evaluator_convergence", EVALUATOR_SYSTEM, prompt, ConvergenceScanResponse)
        result.phase = req.phase
        return result
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    data = json.loads(raw)
    # Defensive defaults — LLM may omit optional fields
    data.setdefault("new_contradictions", [])
    data.setdefault("force_pause", False)
    data.setdefault("pause_reason", "")
    data["phase"] = req.phase  # echo phase back
    # model_validator handles key normalisation + score scaling
    return ConvergenceScanResponse(**data)


def generate_validation_passport(req: ValidationPassportRequest) -> ValidationPassportResponse:
    """Generate a self-declared validation passport for a solution hypothesis."""
    prompt = SOLUTION_VALIDATION_PASSPORT.format(
        solution_name=req.solution_name,
        mechanism=req.mechanism,
        source=req.source or "（未指定）",
        constraints="\n".join(f"- {c}" for c in req.constraints) or "（無）",
        kpis="\n".join(f"- {k}" for k in req.kpis) or "（無）",
    )
    if settings.use_harness_agents:
        from app.harness.agent_base import harness_call
        return harness_call("evaluator_passport", EVALUATOR_SYSTEM, prompt, ValidationPassportResponse)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    data = json.loads(raw)
    return ValidationPassportResponse(**data)


# ---------------------------------------------------------------------------
# Gate quality evaluators (called from evaluator_registry.py)
# ---------------------------------------------------------------------------

def _harness_call_dict(name: str, system_prompt: str, prompt: str) -> dict:
    """Harness path for functions that return raw dict (no Pydantic model)."""
    from app.harness.agent_base import HarnessAgent
    from pydantic import BaseModel as _BM

    class _DictWrapper(_BM):
        class Config:
            extra = "allow"

    agent = HarnessAgent(name=name, system_prompt=system_prompt, output_type=_DictWrapper)
    result = agent.run_sync(prompt)
    return result.model_dump()


def review_brief_quality(
    mission: str, constraints: list[str], kpis: list[str],
) -> dict:
    prompt = BRIEF_QUALITY_REVIEW.format(
        mission=mission,
        constraints="\n".join(f"- {c}" for c in constraints) or "（尚無）",
        kpis="\n".join(f"- {k}" for k in kpis) or "（尚無）",
    )
    if settings.use_harness_agents:
        return _harness_call_dict("evaluator_brief_quality", EVALUATOR_SYSTEM, prompt)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    return json.loads(raw)


def review_depth_quality(
    mission: str,
    assumptions: list[dict],
    contradictions: list[dict],
) -> dict:
    prompt = DEPTH_QUALITY_REVIEW.format(
        mission=mission,
        assumptions="\n".join(
            f"- [{a.get('severity', '?')}] {a.get('content', '')}"
            for a in assumptions
        ) or "（尚無）",
        contradictions="\n".join(
            f"- [{c.get('severity', '?')}] {c.get('description', '')}"
            for c in contradictions
        ) or "（尚無）",
    )
    if settings.use_harness_agents:
        return _harness_call_dict("evaluator_depth_quality", EVALUATOR_SYSTEM, prompt)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    return json.loads(raw)


def review_experiment_coverage(
    high_risk_assumptions: list[dict],
    experiments: list[dict],
) -> dict:
    prompt = EXPERIMENT_COVERAGE_REVIEW.format(
        high_risk_assumptions="\n".join(
            f"- {a.get('code', '?')}: {a.get('content', '')} [{a.get('severity', '')}]"
            for a in high_risk_assumptions
        ),
        experiments="\n".join(
            f"- [{e.get('assumption_code', '?')}] {e.get('description', '')} (方法: {e.get('method', '未指定')})"
            for e in experiments
        ) or "（尚無實驗）",
    )
    if settings.use_harness_agents:
        return _harness_call_dict("evaluator_experiment_coverage", EVALUATOR_SYSTEM, prompt)
    raw = call_llm_json(EVALUATOR_SYSTEM, prompt)
    return json.loads(raw)
