"""Tests for Auto-TRIZ v2 extensions — SIM Matrix, CCI, solve_layered FA/OZ-OT.

WBS 8.3 — all LLM calls are mocked.
"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from app.models.schemas import (
    SIMMatrixRequest,
    SIMMatrixResponse,
    SolutionInteraction,
    ComplexityCheckRequest,
    ComplexityCheckResponse,
    SolveTrizLayeredRequest,
)


# ---------------------------------------------------------------------------
# Mock LLM responses
# ---------------------------------------------------------------------------

_SIM_MATRIX_LLM_RESPONSE = json.dumps({
    "interactions": [
        {
            "solution_a": "Add heat sink to motor",
            "contradiction_a": "C-001",
            "solution_b": "Use lightweight alloy frame",
            "contradiction_b": "C-002",
            "score": 0,
            "reasoning": "兩者互不影響，各自獨立",
        },
        {
            "solution_a": "Add heat sink to motor",
            "contradiction_a": "C-001",
            "solution_b": "Shared cooling loop",
            "contradiction_b": "C-003",
            "score": 1,
            "reasoning": "散熱片可與冷卻迴路整合，協同降溫",
        },
        {
            "solution_a": "Use lightweight alloy frame",
            "contradiction_a": "C-002",
            "solution_b": "Shared cooling loop",
            "contradiction_b": "C-003",
            "score": -1,
            "reasoning": "輕量合金導熱差，與液冷迴路需求衝突",
        },
    ],
    "optimal_combination": [
        "Add heat sink to motor",
        "Shared cooling loop",
    ],
    "conflicts": [
        {
            "solution_a": "Use lightweight alloy frame",
            "solution_b": "Shared cooling loop",
            "reasoning": "輕量合金導熱差",
        },
    ],
    "synergies": [
        {
            "solution_a": "Add heat sink to motor",
            "solution_b": "Shared cooling loop",
            "reasoning": "協同降溫",
        },
    ],
})

_CCI_LLM_RESPONSE = json.dumps({
    "cci_level": "weak_evolution",
    "score": 65,
    "reasoning": "方案淨增 Ideality，但需新增感測器增加控制複雜度",
    "four_questions": {
        "is_new_function_needed": {"answer": True, "reasoning": "冷卻功能為使用者需求"},
        "introduces_new_contradiction": {"answer": False, "reasoning": "無新矛盾"},
        "increases_control_complexity": {"answer": True, "reasoning": "需新增溫度感測器"},
        "reduces_resource_efficiency": {"answer": False, "reasoning": "能耗持平"},
    },
})

_TC_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "TC",
            "principle_number": 35,
            "principle_name": "Parameter changes",
            "suggestion": "Change the cooling medium temperature dynamically based on load",
            "affected_modules": ["cooling_system"],
            "secondary_contradictions": [],
        },
    ]
})

_PC_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "PC",
            "principle_number": None,
            "principle_name": "Separation in time",
            "suggestion": "Use phase-change material that absorbs heat during peak",
            "affected_modules": ["thermal_management"],
            "secondary_contradictions": [],
        },
    ]
})

_L1_CRITIC_RESPONSE = json.dumps({
    "trigger_l2": False,
    "reason": "L1 已有根因突破",
    "confidence": 0.3,
})

_DEEPEN_LINK_RESPONSE = json.dumps({
    "derived_physical_parameter": "瞬時功率 P(t)",
    "contradiction_statement": "P(t) 必須高且必須低",
    "separation_type_candidates": [
        {"type": "time", "confidence": 0.85, "rationale": "時間分離"},
    ],
})

_SUFIELD_LLM_RESPONSE = json.dumps({
    "su_field": {"S1": "Motor", "S2": "Cooling plate", "F": "Thermal"},
    "system_state": "insufficient",
    "matched_solutions": [],
})

_DIFF_ANALYSIS_RESPONSE = json.dumps({
    "l1_vs_l2": {"on_solving_degree": "L1 優化", "on_effort": "低", "on_risk": "低"},
    "l1_vs_l3": {"orthogonality": "互補"},
    "l2_vs_l3": {"synergy": "協同"},
    "recommended_route": {
        "primary": "L1 + L3",
        "fallback": "L1 單獨",
        "adopted_layers": ["L1", "L3"],
        "rationale": "severity=minor",
    },
    "l3_bridge": {
        "supports_l1": "supports",
        "supports_l2": "supports",
        "standalone_value": "independent value",
    },
})


# ---------------------------------------------------------------------------
# 8.3.1 — sim_matrix tests
# ---------------------------------------------------------------------------


class TestSimMatrix:
    """SIM Matrix (WBS 8.3.1)."""

    @patch("app.agents.triz_solver._persist_sim_matrix")
    @patch("app.agents.triz_solver.call_llm_json", return_value=_SIM_MATRIX_LLM_RESPONSE)
    def test_sim_matrix_basic(self, mock_llm, mock_persist):
        from app.agents.triz_solver import sim_matrix

        req = SIMMatrixRequest(
            project_id="proj-1",
            contradiction_ids=["C-001", "C-002", "C-003"],
            solutions_per_contradiction={
                "C-001": ["Add heat sink to motor"],
                "C-002": ["Use lightweight alloy frame"],
                "C-003": ["Shared cooling loop"],
            },
        )
        resp = sim_matrix(req)

        assert isinstance(resp, SIMMatrixResponse)
        assert resp.project_id == "proj-1"
        assert len(resp.matrix) == 3
        assert len(resp.conflicts) == 1
        assert len(resp.synergies) == 1
        assert len(resp.optimal_combination) == 2
        mock_persist.assert_called_once()

    @patch("app.agents.triz_solver._persist_sim_matrix")
    @patch("app.agents.triz_solver.call_llm_json", return_value="{}")
    def test_sim_matrix_empty_llm_response(self, mock_llm, mock_persist):
        from app.agents.triz_solver import sim_matrix

        req = SIMMatrixRequest(
            project_id="proj-2",
            contradiction_ids=["C-A", "C-B"],
            solutions_per_contradiction={
                "C-A": ["sol A"],
                "C-B": ["sol B"],
            },
        )
        resp = sim_matrix(req)

        assert resp.matrix == []
        assert resp.optimal_combination == []
        assert resp.conflicts == []
        assert resp.synergies == []

    def test_sim_matrix_request_min_contradictions(self):
        """Requires at least 2 contradiction_ids."""
        with pytest.raises(Exception):
            SIMMatrixRequest(
                project_id="proj",
                contradiction_ids=["C-001"],  # only 1 — should fail
                solutions_per_contradiction={"C-001": ["sol"]},
            )


# ---------------------------------------------------------------------------
# 8.3.2 — complexity_check (CCI) tests
# ---------------------------------------------------------------------------


class TestComplexityCheck:
    """Complexity Check / CCI (WBS 8.3.2)."""

    @patch("app.agents.triz_solver.call_llm_json", return_value=_CCI_LLM_RESPONSE)
    def test_cci_basic(self, mock_llm):
        from app.agents.triz_solver import complexity_check

        req = ComplexityCheckRequest(
            project_id="proj-1",
            solution_description="Add active cooling with temperature sensor feedback",
            original_contradiction="Motor overheats under peak load",
            affected_subsystems=["motor", "cooling_system"],
        )
        resp = complexity_check(req)

        assert isinstance(resp, ComplexityCheckResponse)
        assert resp.cci_level == "weak_evolution"
        assert resp.score == 65
        assert "感測器" in resp.reasoning
        assert "is_new_function_needed" in resp.four_questions

    @patch("app.agents.triz_solver.call_llm_json", return_value="{}")
    def test_cci_empty_llm_response(self, mock_llm):
        from app.agents.triz_solver import complexity_check

        req = ComplexityCheckRequest(
            project_id="proj-2",
            solution_description="Some solution",
            original_contradiction="Some contradiction",
        )
        resp = complexity_check(req)

        assert resp.cci_level == "patch"
        assert resp.score == 0
        assert resp.reasoning == ""

    @patch("app.agents.triz_solver.call_llm_json", return_value=json.dumps({
        "cci_level": "invalid_level",
        "score": 200,
    }))
    def test_cci_invalid_values_clamped(self, mock_llm):
        from app.agents.triz_solver import complexity_check

        req = ComplexityCheckRequest(
            project_id="proj-3",
            solution_description="x",
            original_contradiction="y",
        )
        resp = complexity_check(req)

        assert resp.cci_level == "patch"  # invalid → fallback
        assert resp.score == 100  # clamped to max


# ---------------------------------------------------------------------------
# 8.3.3 — solve_layered with FA + OZ-OT context
# ---------------------------------------------------------------------------


class TestSolveLayeredV2:
    """solve_triz_layered with fa_context and oz_ot_context (WBS 8.3.3)."""

    def _mock_llm_side_effect(self, system, prompt, **kwargs):
        """Route mock responses based on prompt content."""
        if "L1 Critic" in system or "Critically evaluate" in prompt:
            return _L1_CRITIC_RESPONSE
        if "ARIZ-style deepening" in prompt or "derived_physical_parameter" in prompt:
            return _DEEPEN_LINK_RESPONSE
        if "Separation" in prompt or "Physical Contradiction" in prompt:
            return _PC_LLM_RESPONSE
        if "Su-Field" in prompt or "Su-Field" in system:
            return _SUFIELD_LLM_RESPONSE
        if "differential" in prompt.lower() or "cross-layer" in prompt.lower():
            return _DIFF_ANALYSIS_RESPONSE
        # Default: TC response
        return _TC_LLM_RESPONSE

    @patch("app.agents.triz_solver._persist_layered_solution")
    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[1, 35])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="tc_context")
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="pc_context")
    @patch("app.agents.triz_solver.build_sufield_context", return_value="sf_context")
    def test_layered_with_fa_context(
        self, mock_sf_ctx, mock_pc_ctx, mock_tc_ctx, mock_matrix,
        mock_llm, mock_persist,
    ):
        from app.agents.triz_solver import solve_triz_layered

        mock_llm.side_effect = self._mock_llm_side_effect

        req = SolveTrizLayeredRequest(
            project_id="proj-fa",
            contradiction_id="C-FA-001",
            natural_description="Motor overheats under peak load",
            severity="minor",
            improving_param=21,
            worsening_param=17,
            fa_context={
                "system_function": "Convert electrical energy to mechanical torque",
                "substance_1": "Stator winding",
                "substance_2": "Rotor magnet",
                "field_type": "electromagnetic",
                "interaction_type": "useful",
            },
        )
        resp = solve_triz_layered(req)

        assert resp.layered_solution is not None
        assert resp.layered_solution.l1_surface.status == "ran"

        # Verify the LLM was called with FA context in the description
        tc_call_found = False
        for call_args in mock_llm.call_args_list:
            prompt = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("user_message", "")
            if "function_analysis_context" in str(prompt):
                tc_call_found = True
                break
        assert tc_call_found, "FA context should appear in LLM prompt"

    @patch("app.agents.triz_solver._persist_layered_solution")
    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[1, 35])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="tc_context")
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="pc_context")
    @patch("app.agents.triz_solver.build_sufield_context", return_value="sf_context")
    def test_layered_with_oz_ot_context(
        self, mock_sf_ctx, mock_pc_ctx, mock_tc_ctx, mock_matrix,
        mock_llm, mock_persist,
    ):
        from app.agents.triz_solver import solve_triz_layered

        mock_llm.side_effect = self._mock_llm_side_effect

        req = SolveTrizLayeredRequest(
            project_id="proj-oz",
            contradiction_id="C-OZ-001",
            natural_description="Motor overheats under peak load",
            severity="fatal",
            improving_param=21,
            worsening_param=17,
            force_l2=True,
            oz_ot_context={
                "oz_zone": "Motor winding area (50mm radius)",
                "ot_time": "Peak load phase (0-10s)",
                "px_variable": "Temperature T_winding",
            },
        )
        resp = solve_triz_layered(req)

        assert resp.layered_solution is not None
        # L2 should have run (force_l2=True)
        assert resp.layered_solution.l2_root_cause is not None

    @patch("app.agents.triz_solver._persist_layered_solution")
    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[1, 35])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="tc_context")
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="pc_context")
    @patch("app.agents.triz_solver.build_sufield_context", return_value="sf_context")
    def test_layered_backward_compat_no_fa_oz(
        self, mock_sf_ctx, mock_pc_ctx, mock_tc_ctx, mock_matrix,
        mock_llm, mock_persist,
    ):
        """Existing callers without fa_context/oz_ot_context still work."""
        from app.agents.triz_solver import solve_triz_layered

        mock_llm.side_effect = self._mock_llm_side_effect

        req = SolveTrizLayeredRequest(
            project_id="proj-compat",
            contradiction_id="C-COMPAT-001",
            natural_description="Motor overheats under peak load",
            severity="minor",
            improving_param=21,
            worsening_param=17,
        )
        resp = solve_triz_layered(req)

        assert resp.layered_solution is not None
        assert resp.layered_solution.l1_surface.status == "ran"


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Validate new Pydantic schemas."""

    def test_sim_matrix_request_valid(self):
        req = SIMMatrixRequest(
            project_id="p",
            contradiction_ids=["C-1", "C-2"],
            solutions_per_contradiction={"C-1": ["s1"], "C-2": ["s2"]},
        )
        assert len(req.contradiction_ids) == 2

    def test_complexity_check_request_valid(self):
        req = ComplexityCheckRequest(
            project_id="p",
            solution_description="desc",
            original_contradiction="contradiction",
            affected_subsystems=["sub1"],
        )
        assert req.affected_subsystems == ["sub1"]

    def test_solve_layered_request_with_fa_oz(self):
        req = SolveTrizLayeredRequest(
            project_id="p",
            contradiction_id="C-1",
            natural_description="test",
            fa_context={"system_function": "test"},
            oz_ot_context={"oz_zone": "zone1"},
        )
        assert req.fa_context is not None
        assert req.oz_ot_context is not None

    def test_solve_layered_request_without_fa_oz(self):
        req = SolveTrizLayeredRequest(
            project_id="p",
            contradiction_id="C-1",
            natural_description="test",
        )
        assert req.fa_context is None
        assert req.oz_ot_context is None
