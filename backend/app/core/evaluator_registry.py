"""Extensible AI evaluator registry for gate checks.

Each evaluator is a function: (sb, project_id) -> AiReviewResult.
Register with @register_evaluator("name") decorator.
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from app.models.schemas import AiReviewResult

logger = logging.getLogger(__name__)

EvaluatorFn = Callable[..., AiReviewResult]

AI_EVALUATOR_REGISTRY: dict[str, EvaluatorFn] = {}


def register_evaluator(name: str):
    """Decorator to register an AI evaluator function."""
    def decorator(fn: EvaluatorFn) -> EvaluatorFn:
        AI_EVALUATOR_REGISTRY[name] = fn
        return fn
    return decorator


def run_ai_review(evaluator: str, sb, project_id: str) -> AiReviewResult:
    """Dispatch to the registered evaluator. Raises ValueError if unknown."""
    fn = AI_EVALUATOR_REGISTRY.get(evaluator)
    if fn is None:
        raise ValueError(
            f"Unknown evaluator: {evaluator}. "
            f"Registered: {set(AI_EVALUATOR_REGISTRY.keys())}"
        )
    return fn(sb, project_id)


# ---------------------------------------------------------------------------
# Built-in evaluators (migrated from gates.py)
# ---------------------------------------------------------------------------

@register_evaluator("must")
def _ai_must_review(sb, project_id: str) -> AiReviewResult:
    from app.agents.evaluator import evaluate_must
    from app.models.schemas import MustEvaluationRequest, MustCriterion

    brief = sb.table("briefs").select("mission").eq("project_id", project_id).maybe_single().execute()
    constraints_rows = sb.table("constraints").select("description").eq("project_id", project_id).execute()
    kpis_rows = sb.table("kpis").select("name, target_value, unit").eq("project_id", project_id).execute()
    alts = sb.table("alternatives").select("id, name, mechanism").eq("project_id", project_id).execute()
    project = sb.table("projects").select("must_criteria_config").eq("id", project_id).maybe_single().execute()

    constraints = [r["description"] for r in (constraints_rows.data or [])]
    kpis = [f"{r['name']}: {r.get('target_value', '')} {r.get('unit', '')}" for r in (kpis_rows.data or [])]

    must_config = (project.data or {}).get("must_criteria_config") or []
    if isinstance(must_config, str):
        try:
            must_config = json.loads(must_config)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Malformed must_criteria_config for project %s", project_id)
            must_config = []
    must_criteria = [MustCriterion(**c) for c in must_config] if must_config else []

    if not alts.data or not must_criteria:
        return AiReviewResult(
            evaluator="must",
            summary="資料不足：缺少方案或 MUST 準則，無法進行 AI 評估",
            confidence=0.0,
        )

    alt = alts.data[0]
    req = MustEvaluationRequest(
        project_id=project_id,
        alternative_name=alt.get("name", ""),
        mechanism=alt.get("mechanism", ""),
        constraints=constraints,
        kpis=kpis,
        must_criteria=must_criteria,
    )
    result = evaluate_must(req)

    return AiReviewResult(
        evaluator="must",
        summary=result.summary,
        confidence=min((cr.confidence for cr in result.criteria_results), default=0.0),
        details={
            "overall_pass": result.overall_pass,
            "criteria_count": len(result.criteria_results),
            "evaluated_alternative": alt.get("name", ""),
        },
    )


@register_evaluator("pre_cad")
def _ai_pre_cad_review(sb, project_id: str) -> AiReviewResult:
    from app.agents.evaluator import analyze_pre_cad
    from app.models.schemas import PreCadAnalyzeRequest

    alts = sb.table("alternatives").select("id, name, mechanism").eq("project_id", project_id).execute()
    constraints_rows = sb.table("constraints").select("description").eq("project_id", project_id).execute()
    constraints = [r["description"] for r in (constraints_rows.data or [])]

    if not alts.data:
        return AiReviewResult(
            evaluator="pre_cad",
            summary="資料不足：缺少方案，無法進行 Pre-CAD AI 評估",
            confidence=0.0,
        )

    alt = alts.data[0]
    req = PreCadAnalyzeRequest(
        project_id=project_id,
        alternative_name=alt.get("name", ""),
        mechanism=alt.get("mechanism", ""),
        constraints=constraints,
    )
    result = analyze_pre_cad(req)

    scores = {
        "spatial": result.spatial_score,
        "cost": result.cost_score,
        "safety": result.safety_score,
        "decoupling": result.decoupling_score,
        "supply": result.supply_score,
    }
    avg_score = sum(scores.values()) / len(scores) if scores else 0

    return AiReviewResult(
        evaluator="pre_cad",
        summary=result.analysis,
        confidence=avg_score / 5.0,
        details={
            "overall_pass": result.overall_pass,
            "scores": scores,
            "evaluated_alternative": alt.get("name", ""),
        },
    )


@register_evaluator("convergence")
def _ai_convergence_review(sb, project_id: str) -> AiReviewResult:
    from app.agents.evaluator import scan_convergence
    from app.models.schemas import ConvergenceScanRequest

    alts = sb.table("alternatives").select("name, mechanism").eq("project_id", project_id).execute()
    contras = sb.table("contradictions").select("description, severity").eq("project_id", project_id).execute()

    alternatives = [{"name": a.get("name", ""), "mechanism": a.get("mechanism", "")} for a in (alts.data or [])]
    contradictions = [{"description": c.get("description", ""), "severity": c.get("severity", "")} for c in (contras.data or [])]

    if not alternatives and not contradictions:
        return AiReviewResult(
            evaluator="convergence",
            summary="資料不足：缺少方案和矛盾資料，無法進行收斂掃描",
            confidence=0.0,
        )

    req = ConvergenceScanRequest(
        project_id=project_id,
        alternatives=alternatives,
        contradictions=contradictions,
    )
    result = scan_convergence(req)

    return AiReviewResult(
        evaluator="convergence",
        summary=result.summary,
        confidence=result.convergence_score,
        details={
            "convergence_score": result.convergence_score,
            "architecture_health": result.architecture_health,
            "force_pause": result.force_pause,
            "secondary_contradictions_count": len(result.secondary_contradictions),
        },
    )


# ---------------------------------------------------------------------------
# New evaluators — quality-layer for gates 1.1, 1.2, 2.1
# ---------------------------------------------------------------------------

@register_evaluator("brief_quality")
def _ai_brief_quality_review(sb, project_id: str) -> AiReviewResult:
    """Gate D1 — assess mission clarity and KPI measurability."""
    from app.agents.evaluator import review_brief_quality

    brief = sb.table("briefs").select("mission").eq("project_id", project_id).maybe_single().execute()
    mission = (brief.data or {}).get("mission", "")
    constraints_rows = sb.table("constraints").select("description, type").eq("project_id", project_id).execute()
    kpis_rows = sb.table("kpis").select("name, target_value, unit, measurement_method").eq("project_id", project_id).execute()

    constraints = [r["description"] for r in (constraints_rows.data or [])]
    kpis = [
        f"{r['name']}: {r.get('target_value', '')} {r.get('unit', '')} ({r.get('measurement_method', '')})"
        for r in (kpis_rows.data or [])
    ]

    if not mission:
        return AiReviewResult(
            evaluator="brief_quality",
            summary="Mission 尚未定義，無法進行品質評估",
            confidence=0.0,
        )

    result = review_brief_quality(mission, constraints, kpis)
    return AiReviewResult(
        evaluator="brief_quality",
        summary=result["summary"],
        confidence=result["overall_score"] / 5.0,
        details={
            "overall_score": result["overall_score"],
            "mission_score": result["mission_score"],
            "kpi_score": result["kpi_score"],
            "constraint_score": result["constraint_score"],
            "suggestions": result.get("suggestions", []),
        },
    )


@register_evaluator("depth_quality")
def _ai_depth_quality_review(sb, project_id: str) -> AiReviewResult:
    """Gate D2 — assess assumption/contradiction depth and coverage."""
    from app.agents.evaluator import review_depth_quality

    brief = sb.table("briefs").select("mission").eq("project_id", project_id).maybe_single().execute()
    mission = (brief.data or {}).get("mission", "")
    assumptions_rows = sb.table("assumptions").select("content, worst_severity").eq("project_id", project_id).execute()
    contradictions_rows = sb.table("contradictions").select("description, severity").eq("project_id", project_id).execute()

    assumptions = [
        {"content": r.get("content", ""), "severity": r.get("worst_severity", "")}
        for r in (assumptions_rows.data or [])
    ]
    contradictions = [
        {"description": r.get("description", ""), "severity": r.get("severity", "")}
        for r in (contradictions_rows.data or [])
    ]

    if not assumptions and not contradictions:
        return AiReviewResult(
            evaluator="depth_quality",
            summary="假設與矛盾資料不足，無法評估深度",
            confidence=0.0,
        )

    result = review_depth_quality(mission, assumptions, contradictions)
    return AiReviewResult(
        evaluator="depth_quality",
        summary=result["summary"],
        confidence=result["overall_score"] / 5.0,
        details={
            "overall_score": result["overall_score"],
            "assumption_depth_score": result["assumption_depth_score"],
            "contradiction_depth_score": result["contradiction_depth_score"],
            "blind_spots": result.get("blind_spots", []),
        },
    )


@register_evaluator("experiment_coverage")
def _ai_experiment_coverage_review(sb, project_id: str) -> AiReviewResult:
    """Gate X1 — assess whether experiments actually address high-risk assumptions."""
    from app.agents.evaluator import review_experiment_coverage

    assumptions_rows = (
        sb.table("assumptions")
        .select("code, content, worst_severity")
        .eq("project_id", project_id)
        .execute()
    )
    experiments_rows = (
        sb.table("experiments")
        .select("assumption_code, description, method")
        .eq("project_id", project_id)
        .execute()
    )

    high_risk = [
        {"code": r.get("code", ""), "content": r.get("content", ""), "severity": r.get("worst_severity", "")}
        for r in (assumptions_rows.data or [])
        if r.get("worst_severity") in ("critical", "high")
    ]
    experiments = [
        {"assumption_code": r.get("assumption_code", ""), "description": r.get("description", ""), "method": r.get("method", "")}
        for r in (experiments_rows.data or [])
    ]

    if not high_risk:
        return AiReviewResult(
            evaluator="experiment_coverage",
            summary="尚無高風險假設，無需實驗覆蓋評估",
            confidence=1.0,
        )

    result = review_experiment_coverage(high_risk, experiments)
    return AiReviewResult(
        evaluator="experiment_coverage",
        summary=result["summary"],
        confidence=result["coverage_score"] / 5.0,
        details={
            "coverage_score": result["coverage_score"],
            "uncovered_assumptions": result.get("uncovered_assumptions", []),
            "weak_experiments": result.get("weak_experiments", []),
        },
    )
