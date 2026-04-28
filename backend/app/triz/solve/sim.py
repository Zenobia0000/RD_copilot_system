"""SIM (Solution Interaction Matrix) — convergence computation.

Deterministic module: given pairwise scores, compute stats and convergence.
The actual scoring of each pair (+1/0/-1) requires LLM reasoning —
this module only handles the math and decision logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..state import SIMResult


@dataclass
class SIMStats:
    """Summary statistics for a SIM iteration."""
    plus_one: int = 0   # synergy pairs
    zero: int = 0       # neutral pairs
    minus_one: int = 0  # conflict pairs
    total_pairs: int = 0


def compute_sim_stats(matrix: dict[str, int]) -> SIMStats:
    """Compute summary statistics from SIM matrix entries.

    Args:
        matrix: Dict of "SOL-TCx × SOL-TCy" → score (-1, 0, +1).
    """
    stats = SIMStats(total_pairs=len(matrix))
    for score in matrix.values():
        if score > 0:
            stats.plus_one += 1
        elif score < 0:
            stats.minus_one += 1
        else:
            stats.zero += 1
    return stats


def check_convergence(
    stats: SIMStats,
    iteration: int,
    max_iterations: int = 2,
    minus1_history: list[int] | None = None,
) -> str:
    """Determine SIM convergence status.

    Decision tree (from triz-contradict SKILL.md):
    - No -1 → "converged"
    - Has -1 AND iteration < max → "iterate" (refine conflicting solutions)
    - Has -1 AND iteration >= max → check minus1_history
      - If -1 count decreasing → "iterate" (one more round)
      - If -1 count NOT decreasing → "stop" (escalate to user)

    Returns:
        "converged" | "iterate" | "stop"
    """
    if stats.minus_one == 0:
        return "converged"

    if iteration < max_iterations:
        return "iterate"

    # At max iterations — check if -1 count is improving
    if minus1_history and len(minus1_history) >= 2:
        if minus1_history[-1] < minus1_history[-2]:
            return "iterate"  # improving, allow one more
    return "stop"


def build_sim_result(
    matrix: dict[str, int],
    synergy_reasons: list[str] | None = None,
    conflict_reasons: list[str] | None = None,
    iteration: int = 1,
) -> SIMResult:
    """Build a SIMResult from raw matrix data."""
    stats = compute_sim_stats(matrix)

    verdict_status = check_convergence(stats, iteration)

    return SIMResult(
        iteration=iteration,
        matrix=matrix,
        summary={"+1": stats.plus_one, "0": stats.zero, "-1": stats.minus_one},
        verdict=verdict_status,
        synergies=synergy_reasons or [],
        conflicts=conflict_reasons or [],
    )
