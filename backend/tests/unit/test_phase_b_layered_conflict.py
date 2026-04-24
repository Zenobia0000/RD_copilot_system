"""Phase B intra-LTS SKIP logic tests — WBS 6.3 / 6.4.

Covers the four branches of `check_phase_b_conflict`:
  1. Same contradiction + same LTS  → SKIP (drill-down combination)
  2. Same contradiction + different LTS → WARN (redundant)
  3. Different contradictions         → CHECK
  4. Directive override (check instead of skip)

Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §8.3
"""

from __future__ import annotations

from app.agents.evaluator import check_phase_b_conflict, _apply_layered_directives
from app.models.schemas import (
    ConvergenceScanRequest,
    ConvergenceAlternativeInput,
    ConvergenceContradictionInput,
    LayeredAlternativeDirective,
)


class TestCheckPhaseBConflict:
    def test_intra_lts_cross_layer_skipped(self):
        decision, reason = check_phase_b_conflict(
            lts_id_a="LTS-EBIKE-012",
            contradiction_id_a="C-EBIKE-012",
            layer_a="1",
            lts_id_b="LTS-EBIKE-012",
            contradiction_id_b="C-EBIKE-012",
            layer_b="2",
        )
        assert decision == "SKIP"
        assert "intra-LTS" in reason
        assert "drill-down" in reason

    def test_same_contradiction_different_lts_warns(self):
        decision, reason = check_phase_b_conflict(
            lts_id_a="LTS-EBIKE-012",
            contradiction_id_a="C-EBIKE-012",
            layer_a="1",
            lts_id_b="LTS-EBIKE-012-v2",
            contradiction_id_b="C-EBIKE-012",
            layer_b="1",
        )
        assert decision == "WARN"
        assert "different LTS" in reason

    def test_cross_contradiction_checked(self):
        decision, reason = check_phase_b_conflict(
            lts_id_a="LTS-EBIKE-012",
            contradiction_id_a="C-EBIKE-012",
            layer_a="2",
            lts_id_b="LTS-EBIKE-013",
            contradiction_id_b="C-EBIKE-013",
            layer_b="1",
        )
        assert decision == "CHECK"
        assert "cross-contradiction" in reason

    def test_intra_lts_directive_override_check(self):
        """If someone overrides the directive to 'check', same-LTS pairs go CHECK."""
        decision, _ = check_phase_b_conflict(
            lts_id_a="LTS-A",
            contradiction_id_a="C-A",
            layer_a="1",
            lts_id_b="LTS-A",
            contradiction_id_b="C-A",
            layer_b="2",
            directive_same_contradiction_intra_layer="check",
        )
        assert decision == "CHECK"

    def test_cross_contradiction_directive_override_skip(self):
        """If someone overrides cross-contradiction directive to skip, skip."""
        decision, _ = check_phase_b_conflict(
            lts_id_a="LTS-A",
            contradiction_id_a="C-A",
            layer_a="1",
            lts_id_b="LTS-B",
            contradiction_id_b="C-B",
            layer_b="1",
            directive_cross_contradiction="skip",
        )
        assert decision == "SKIP"

    def test_no_lts_id_same_contradiction_still_warns(self):
        """Legacy per-path candidates without an LTS id fall through to WARN."""
        decision, _ = check_phase_b_conflict(
            lts_id_a=None,
            contradiction_id_a="C-A",
            layer_a=None,
            lts_id_b=None,
            contradiction_id_b="C-A",
            layer_b=None,
        )
        assert decision == "WARN"


# ---------------------------------------------------------------------------
# _apply_layered_directives — Phase B alternative pre-filter (WP 10.6)
# ---------------------------------------------------------------------------


def _mk_alt(alt_id: str, name: str) -> ConvergenceAlternativeInput:
    return ConvergenceAlternativeInput(
        id=alt_id, name=name, mechanism="", source="triz_tc",
        resolves_contradiction_ids=["C-EBIKE-012"],
    )


def _mk_contr() -> ConvergenceContradictionInput:
    return ConvergenceContradictionInput(
        id="C-EBIKE-012",
        natural_description="馬達功率密度 vs 散熱",
        severity="major",
    )


class TestApplyLayeredDirectives:
    def test_empty_directives_passthrough(self):
        req = ConvergenceScanRequest(
            project_id="p",
            alternatives=[_mk_alt("a1", "route1"), _mk_alt("a2", "route2")],
            contradictions=[_mk_contr()],
            phase="B",
        )
        combined, notes = _apply_layered_directives(req)
        assert len(combined) == 2
        assert notes == []

    def test_intra_lts_skip_collapses_into_one(self):
        """Three alts sharing the same LTS (one per layer) → 1 representative."""
        req = ConvergenceScanRequest(
            project_id="p",
            alternatives=[
                _mk_alt("a1", "L1 path"),
                _mk_alt("a2", "L2 path"),
                _mk_alt("a3", "L3 path"),
            ],
            contradictions=[_mk_contr()],
            phase="B",
            layered_directives=[
                LayeredAlternativeDirective(
                    alternative_id="a1", lts_id="LTS-1",
                    adopted_layers=["L1"], same_contradiction_intra_layer_conflict="skip",
                ),
                LayeredAlternativeDirective(
                    alternative_id="a2", lts_id="LTS-1",
                    adopted_layers=["L2"], same_contradiction_intra_layer_conflict="skip",
                ),
                LayeredAlternativeDirective(
                    alternative_id="a3", lts_id="LTS-1",
                    adopted_layers=["L3"], same_contradiction_intra_layer_conflict="skip",
                ),
            ],
        )
        combined, notes = _apply_layered_directives(req)
        assert len(combined) == 1
        assert "drill-down" in combined[0].name
        assert "3 layers merged" in combined[0].name
        assert any("3 alternatives into 1" in n for n in notes)

    def test_intra_lts_check_keeps_all(self):
        """When directive overrides to `check`, all intra-LTS alts kept."""
        req = ConvergenceScanRequest(
            project_id="p",
            alternatives=[_mk_alt("a1", "L1"), _mk_alt("a2", "L2")],
            contradictions=[_mk_contr()],
            phase="B",
            layered_directives=[
                LayeredAlternativeDirective(
                    alternative_id="a1", lts_id="LTS-1", adopted_layers=["L1"],
                    same_contradiction_intra_layer_conflict="check",
                ),
                LayeredAlternativeDirective(
                    alternative_id="a2", lts_id="LTS-1", adopted_layers=["L2"],
                    same_contradiction_intra_layer_conflict="check",
                ),
            ],
        )
        combined, notes = _apply_layered_directives(req)
        assert len(combined) == 2
        assert any("directive=check" in n for n in notes)

    def test_cross_lts_alternatives_untouched(self):
        """Alternatives from different LTS ids stay separate (no merging)."""
        req = ConvergenceScanRequest(
            project_id="p",
            alternatives=[
                _mk_alt("a1", "route1"),
                _mk_alt("a2", "route2"),
                _mk_alt("a3", "route3"),
            ],
            contradictions=[_mk_contr()],
            phase="B",
            layered_directives=[
                LayeredAlternativeDirective(
                    alternative_id="a1", lts_id="LTS-1", adopted_layers=["L1"],
                ),
                LayeredAlternativeDirective(
                    alternative_id="a2", lts_id="LTS-2", adopted_layers=["L2"],
                ),
                LayeredAlternativeDirective(
                    alternative_id="a3", lts_id="LTS-3", adopted_layers=["L3"],
                ),
            ],
        )
        combined, _ = _apply_layered_directives(req)
        assert len(combined) == 3

    def test_loose_alternatives_without_directive_passthrough(self):
        """Mixed: one layered + one legacy without directive → both kept."""
        req = ConvergenceScanRequest(
            project_id="p",
            alternatives=[_mk_alt("a1", "layered"), _mk_alt("a2", "legacy")],
            contradictions=[_mk_contr()],
            phase="B",
            layered_directives=[
                LayeredAlternativeDirective(
                    alternative_id="a1", lts_id="LTS-1", adopted_layers=["L1", "L2"],
                ),
            ],
        )
        combined, _ = _apply_layered_directives(req)
        assert len(combined) == 2
