"""Registry integrity tests — validate all 8 gates are registered correctly."""

from __future__ import annotations

from app.core.gate_registry import GATE_REGISTRY, GateDefinition


EXPECTED_GATES = {"D1", "D2", "PG-D", "X1", "X2", "PG-X", "V2", "PG-V"}
VALID_EVALUATORS = {None, "brief_quality", "depth_quality", "experiment_coverage", "must", "pre_cad", "convergence"}


class TestGateRegistry:
    def test_all_8_gates_registered(self):
        assert set(GATE_REGISTRY.keys()) == EXPECTED_GATES

    def test_no_duplicate_ids(self):
        assert len(GATE_REGISTRY) == len(EXPECTED_GATES)

    def test_all_definitions_are_gate_definition(self):
        for defn in GATE_REGISTRY.values():
            assert isinstance(defn, GateDefinition)

    def test_all_gates_have_checks(self):
        """Every gate must have at least one check function."""
        for gate_id, defn in GATE_REGISTRY.items():
            assert len(defn.checks) >= 1, f"Gate {gate_id} has no checks"

    def test_checks_are_callable(self):
        for gate_id, defn in GATE_REGISTRY.items():
            for i, fn in enumerate(defn.checks):
                assert callable(fn), f"Gate {gate_id} check[{i}] is not callable"

    def test_ai_evaluator_values_valid(self):
        for gate_id, defn in GATE_REGISTRY.items():
            assert defn.ai_evaluator in VALID_EVALUATORS, (
                f"Gate {gate_id} has invalid ai_evaluator: {defn.ai_evaluator}"
            )

    def test_manual_gate_only_pg3(self):
        manual_gates = [gid for gid, d in GATE_REGISTRY.items() if d.manual]
        assert manual_gates == ["PG-V"]

    def test_ai_gates_are_pg1_22_pg2(self):
        ai_gates = {gid for gid, d in GATE_REGISTRY.items() if d.ai_evaluator}
        assert ai_gates == {"D1", "D2", "PG-D", "X1", "X2", "PG-X"}
