"""CCI (Composite Complexity Index) calculator — pure deterministic.

Implements the 4-question scoring + weighted formula from triz-verify SKILL.md.
No LLM calls — Q1-Q3 are rule-based, Q4 requires trend count as input.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..state import CCIScores, CCIVerdict, EvidenceRegistry


# ── Weights ──────────────────────────────────────────────────────────

W_Q1 = 0.30  # structural
W_Q2 = 0.25  # energy
W_Q3 = 0.20  # cognitive
W_Q4 = 0.25  # evolution alignment


# ── CCI Verdicts ─────────────────────────────────────────────────────

VERDICT_THRESHOLDS: list[tuple[float, CCIVerdict]] = [
    (0.30, CCIVerdict.strong_evolution),
    (0.55, CCIVerdict.weak_evolution),
    (0.75, CCIVerdict.conscious_patch),
    (1.00, CCIVerdict.hard_patch),
]


# ── Q1 Structural Scoring ───────────────────────────────────────────

class StructuralChange(str, Enum):
    """Q1: Net component count change."""
    reduced = "reduced"           # 0.00 — net component count decreased
    unchanged = "unchanged"       # 0.25 — same count, new function
    added_no_interface = "added_no_interface"   # 0.50 — +1-2 parts, no new cross-subsystem interface
    added_with_interface = "added_with_interface"  # 0.75 — +1-2 parts with new interface
    new_subsystem = "new_subsystem"  # 1.00 — +3 parts or new subsystem


Q1_SCORES: dict[StructuralChange, float] = {
    StructuralChange.reduced: 0.00,
    StructuralChange.unchanged: 0.25,
    StructuralChange.added_no_interface: 0.50,
    StructuralChange.added_with_interface: 0.75,
    StructuralChange.new_subsystem: 1.00,
}


# ── Q2 Energy Scoring ───────────────────────────────────────────────

class EnergyChange(str, Enum):
    """Q2: Energy consumption change."""
    reduced = "reduced"           # 0.00
    unchanged = "unchanged"       # 0.25
    slight_increase = "slight_increase"  # 0.50 — <10%
    moderate_increase = "moderate_increase"  # 0.75 — 10-50%
    new_source = "new_source"     # 1.00 — needs new energy source


Q2_SCORES: dict[EnergyChange, float] = {
    EnergyChange.reduced: 0.00,
    EnergyChange.unchanged: 0.25,
    EnergyChange.slight_increase: 0.50,
    EnergyChange.moderate_increase: 0.75,
    EnergyChange.new_source: 1.00,
}


# ── Q3 Cognitive Scoring ─────────────────────────────────────────────

class CognitiveChange(str, Enum):
    """Q3: Cognitive complexity change."""
    simplified = "simplified"     # 0.00 — dependency chain shortened
    unchanged = "unchanged"       # 0.25
    one_branch = "one_branch"     # 0.50 — +1 condition or calibration step
    specialist = "specialist"     # 0.75 — +2-3 branches, needs specialist
    new_model = "new_model"       # 1.00 — needs entirely new mental model


Q3_SCORES: dict[CognitiveChange, float] = {
    CognitiveChange.simplified: 0.00,
    CognitiveChange.unchanged: 0.25,
    CognitiveChange.one_branch: 0.50,
    CognitiveChange.specialist: 0.75,
    CognitiveChange.new_model: 1.00,
}


# ── Q4 Evolution Alignment ──────────────────────────────────────────

def score_evolution_alignment(trends_satisfied: int, total_trends: int = 3) -> float:
    """Score Q4 based on how many evolution trends the solution satisfies.

    Default 3 trends:
    1. Increasing ideality (more function, less cost/harm)
    2. Transition to micro-level (material-level solutions)
    3. Increasing dynamism (sensor-driven state switching)
    """
    if total_trends <= 0:
        return 0.00
    if trends_satisfied >= total_trends:
        return 0.00
    if trends_satisfied == total_trends - 1:
        return 0.33
    if trends_satisfied == 1:
        return 0.67
    return 1.00  # 0 trends satisfied


# ── Main CCI Computation ────────────────────────────────────────────

@dataclass
class CCIInput:
    """Inputs for CCI computation."""
    q1: StructuralChange
    q2: EnergyChange
    q3: CognitiveChange
    trends_satisfied: int
    total_trends: int = 3


def compute_cci(inp: CCIInput) -> CCIScores:
    """Compute CCI scores and weighted index."""
    q1 = Q1_SCORES[inp.q1]
    q2 = Q2_SCORES[inp.q2]
    q3 = Q3_SCORES[inp.q3]
    q4 = score_evolution_alignment(inp.trends_satisfied, inp.total_trends)
    cci = W_Q1 * q1 + W_Q2 * q2 + W_Q3 * q3 + W_Q4 * q4
    return CCIScores(
        structural=q1,
        energy=q2,
        cognitive=q3,
        evolution_aligned=q4,
        cci=round(cci, 4),
    )


def classify_verdict(cci: float) -> CCIVerdict:
    """Classify CCI score into verdict tier."""
    for threshold, verdict in VERDICT_THRESHOLDS:
        if cci <= threshold:
            return verdict
    return CCIVerdict.hard_patch


def check_evidence_downgrade(
    verdict: CCIVerdict,
    registry: EvidenceRegistry,
) -> CCIVerdict:
    """Downgrade Evolution verdicts if evidence confidence is too low.

    Rule: If LOW confidence claims > 50% of total, downgrade
    Strong Evolution → Weak Evolution.
    """
    if verdict not in (CCIVerdict.strong_evolution, CCIVerdict.weak_evolution):
        return verdict

    if registry.total_claims == 0:
        return verdict

    low_pct = registry.low_confidence / registry.total_claims
    if low_pct > 0.50:
        return CCIVerdict.weak_evolution

    return verdict


def cci_to_step4_verdict(verdict: CCIVerdict) -> str:
    """Map CCI verdict to step4.verdict enum value."""
    mapping = {
        CCIVerdict.strong_evolution: "evolution",
        CCIVerdict.weak_evolution: "weak-evolution",
        CCIVerdict.conscious_patch: "patch",
        CCIVerdict.hard_patch: "strong-patch",
    }
    return mapping[verdict]
