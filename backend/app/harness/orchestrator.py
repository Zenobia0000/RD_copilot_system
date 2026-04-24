"""Orchestrator — linear pipeline coordinator for TRIZ layered drill-down.

Extracts the L1 → Critic → L2 → L3 → Differential pipeline from
triz_solver.py into a standalone orchestrator that:
- Sequences agent calls with context isolation
- Passes only structured Pydantic model output between layers
- Manages per-layer persistence (upsert to Supabase)
- Accumulates pipeline-level token usage metrics

The orchestrator delegates to the same layer runners (_run_l1, _run_l2,
_run_l3, etc.) — it owns the *flow*, not the *computation*.

Registered as "triz_layered" solver via solver_registry.
"""

from __future__ import annotations

import logging

from app.harness.solver_registry import register_solver
from app.observability import emit_counter, phase_timer

logger = logging.getLogger(__name__)


@register_solver(
    "triz_layered",
    description="Three-layer TRIZ drill-down: L1(TC) → critic → L2(PC) → L3(SF) → differential",
    tags=["triz", "layered"],
)
def solve_triz_layered_orchestrated(req):
    """Orchestrate the three-layer drill-down TRIZ solution for ONE contradiction.

    Pipeline (§4):
        L1 (TC, always)  →  critic  →  maybe L2 (PC, deepen_link)
                            │
                            └─→  L3 (always, structural_lens, in parallel)
                                      │
                                      └─→  differential_analysis (LLM)

    This is the harness-managed version of solve_triz_layered.
    It delegates to the same layer runners but adds:
    - Structured logging per layer
    - Token usage accumulation (when harness agents are enabled)
    - Context isolation between layers (Pydantic models only)
    """
    from app.agents.triz_solver import (
        _run_l1,
        _l1_critic,
        _should_trigger_l2,
        _run_l2,
        _run_l3,
        _run_differential_analysis,
        _build_lts_id,
    )
    from app.models.schemas import (
        SolveTrizLayeredResponse,
        LayeredTrizSolution,
        L2RootCause,
        PhaseBDirective,
    )

    with phase_timer("orchestrator.triz_layered"):
        # ADR-007: Derive Su-Field from TC if not provided
        req = _derive_sf_if_needed(req)

        # L1 — always
        logger.info("orchestrator: starting L1 for %s", req.contradiction_id)
        l1 = _run_l1(req)

        # L1 critic
        if l1.status == "ran":
            from app.tools.triz_kb import get_param_name
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
            logger.info("orchestrator: L2 triggered (%s)", l2_reason)
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

        # L3 — always
        logger.info("orchestrator: starting L3 for %s", req.contradiction_id)
        l3 = _run_l3(req)

        # Differential analysis
        diff = _run_differential_analysis(
            req, l1, l2 if l2.status == "ran" else None, l3,
        )

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
            phase_b_directive=PhaseBDirective(),
        )

        _persist_layered_solution(lts)

        emit_counter(
            "triz_layered_solved",
            severity=req.severity,
            l2_ran=str(l2.status == "ran").lower(),
            quick_mode=str(req.quick_mode).lower(),
        )
        return SolveTrizLayeredResponse(layered_solution=lts)


def _derive_sf_if_needed(req):
    """ADR-007: Derive Su-Field from TC if caller didn't supply SF fields."""
    if (
        not (req.sf_substance_1 or req.sf_substance_2 or req.sf_field)
        and isinstance(req.improving_param, int)
        and isinstance(req.worsening_param, int)
    ):
        try:
            from app.agents.analyst import derive_su_field_from_tc
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
                    "orchestrator: derived SF from TC (S1=%r S2=%r F=%r)",
                    derived_sf.S1, derived_sf.S2, derived_sf.F,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("orchestrator: SF derivation failed: %s", exc)
    return req


def _persist_layered_solution(lts) -> None:
    """Upsert LTS into layered_triz_solutions for UI rehydration.

    Non-fatal: persistence failures are logged but do NOT abort the response.
    """
    from app.core.supabase import get_supabase
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
