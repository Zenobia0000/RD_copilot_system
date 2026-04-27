"""Tests for TRIZ Solver agent and router — WP-6.1.

Covers TC path, PC path, invalid input handling.
All LLM calls are mocked.
"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from app.models.schemas import TrizLookupRequest, TrizLookupResponse, SuFieldRequest, SuFieldResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TC_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "TC",
            "principle_number": 1,
            "principle_name": "Segmentation",
            "suggestion": "Divide the motor into modular segments",
            "affected_modules": ["motor_core"],
            "secondary_contradictions": [],
        },
        {
            "path": "TC",
            "principle_number": 35,
            "principle_name": "Parameter changes",
            "suggestion": "Change the cooling medium temperature",
            "affected_modules": ["cooling_system"],
            "secondary_contradictions": ["May increase weight"],
        },
    ]
})

_SUFIELD_LLM_RESPONSE = json.dumps({
    "su_field": {"S1": "Battery cell", "S2": "Cooling plate", "F": "Thermal (conduction)"},
    "system_state": "insufficient",
    "matched_solutions": [
        {
            "standard_id": "1.1.2",
            "standard_name": "Add Internal Additive",
            "class_name": "Class 1",
            "suggestion": "Add thermally conductive filler between battery cell and cooling plate to improve heat transfer efficiency. "
                          "This addresses the insufficient thermal coupling by introducing an internal additive that bridges "
                          "micro-gaps between the contact surfaces, increasing effective thermal conductivity by 2-3x.",
            "affected_modules": ["battery_pack", "thermal_management"],
            "secondary_contradictions": ["Added filler may increase assembly complexity"],
        },
        {
            "standard_id": "2.2.1",
            "standard_name": "Replace Mechanical Field with Thermal Field",
            "class_name": "Class 2",
            "suggestion": "Replace passive conduction with active liquid cooling loop that circulates coolant directly against cell surfaces.",
            "affected_modules": ["thermal_management", "power_electronics"],
            "secondary_contradictions": ["Liquid cooling adds weight and leak risk"],
        },
    ]
})

_PC_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "PC",
            "principle_number": None,
            "principle_name": "Separation in time",
            "suggestion": "Use phase-change material that absorbs heat during peak, releases at idle",
            "affected_modules": ["thermal_management"],
            "secondary_contradictions": [],
        },
    ]
})


# ---------------------------------------------------------------------------
# Unit tests — solve_triz function directly
# ---------------------------------------------------------------------------


class TestSolveTrizTC:
    """TC (Technical Contradiction) path."""

    @patch("app.agents.triz_solver.call_llm_json", return_value=_TC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[1, 35, 28])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<context>")
    def test_tc_returns_structured_result(self, mock_ctx, mock_matrix, mock_llm):
        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c1",
            natural_description="Motor efficiency vs weight",
            improving_param=9,
            worsening_param=1,
            type="TC",
        )
        result = solve_triz(req)

        assert isinstance(result, TrizLookupResponse)
        assert result.mapped_improving == 9
        assert result.mapped_worsening == 1
        assert result.candidate_principles == [1, 35, 28]
        assert len(result.suggestions) == 2
        assert result.suggestions[0].path == "TC"
        assert result.suggestions[0].principle_number == 1
        mock_llm.assert_called_once()

    @patch("app.agents.triz_solver.call_llm_json", return_value=_TC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<context>")
    def test_tc_empty_matrix_still_returns_suggestions(self, mock_ctx, mock_matrix, mock_llm):
        """Even when matrix returns no candidates, LLM can still suggest."""
        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c1",
            natural_description="Speed vs safety",
            improving_param=9,
            worsening_param=30,
            type="TC",
        )
        result = solve_triz(req)
        assert result.candidate_principles == []
        assert len(result.suggestions) >= 1


class TestSolveTrizPC:
    """PC (Physical Contradiction) path."""

    @patch("app.agents.triz_solver.call_llm_json", return_value=_PC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<pc_context>")
    def test_pc_returns_separation_strategies(self, mock_ctx, mock_llm):
        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c2",
            natural_description="Must be both rigid and flexible",
            physical_contradiction="Shaft must be rigid for torque but flexible for vibration",
            type="PC",
        )
        result = solve_triz(req)

        assert isinstance(result, TrizLookupResponse)
        # PC path does not populate matrix fields
        assert result.mapped_improving is None
        assert result.mapped_worsening is None
        assert result.candidate_principles == []
        assert len(result.suggestions) == 1
        assert result.suggestions[0].path == "PC"
        assert "Separation" in result.suggestions[0].principle_name

    @patch("app.agents.triz_solver.call_llm_json", return_value=_PC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<pc_context>")
    def test_pc_fallback_when_no_improving_param(self, mock_ctx, mock_llm):
        """When type=TC but no improving_param, falls back to PC path."""
        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c3",
            natural_description="Unknown contradiction",
            type="TC",
            improving_param=None,
            worsening_param=None,
        )
        result = solve_triz(req)
        # Should fall back to PC since improving_param is None
        assert len(result.suggestions) >= 1
        mock_ctx.assert_called_once()


class TestSolveTrizInvalidInput:
    """Edge cases and invalid inputs."""

    @patch("app.agents.triz_solver.call_llm_json", return_value='{"suggestions": []}')
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<ctx>")
    def test_empty_suggestions_returns_empty_list(self, mock_ctx, mock_llm):
        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c4",
            natural_description="No real contradiction",
            type="PC",
        )
        result = solve_triz(req)
        assert result.suggestions == []

    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<ctx>")
    def test_malformed_llm_json_raises(self, mock_ctx, mock_llm):
        """If LLM returns invalid JSON, json.loads should raise."""
        mock_llm.return_value = "not valid json {"

        from app.agents.triz_solver import solve_triz

        req = TrizLookupRequest(
            project_id="p1",
            contradiction_id="c5",
            natural_description="Test",
            type="PC",
        )
        with pytest.raises(Exception):
            solve_triz(req)


# ---------------------------------------------------------------------------
# Su-Field Analysis tests
# ---------------------------------------------------------------------------


class TestAnalyzeSuField:
    """Su-Field model analysis + 76 standard solutions matching."""

    @patch("app.agents.triz_solver.call_llm_json", return_value=_SUFIELD_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_sufield_context", return_value="<sufield_kb>")
    def test_sufield_returns_structured_result(self, mock_ctx, mock_llm):
        from app.agents.triz_solver import analyze_sufield

        req = SuFieldRequest(
            project_id="p1",
            system_description="Battery cell cooled by aluminium plate via conduction",
            current_issues=["Heat transfer insufficient at high discharge rate"],
        )
        result = analyze_sufield(req)

        assert isinstance(result, SuFieldResponse)
        assert result.system_state == "insufficient"
        assert result.su_field["S1"] == "Battery cell"
        assert result.su_field["F"] == "Thermal (conduction)"
        assert len(result.matched_solutions) == 2
        assert result.matched_solutions[0].standard_id == "1.1.2"
        mock_llm.assert_called_once()

    @patch("app.agents.triz_solver.call_llm_json", return_value=_SUFIELD_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_sufield_context", return_value="<sufield_kb>")
    def test_sufield_no_issues_still_works(self, mock_ctx, mock_llm):
        from app.agents.triz_solver import analyze_sufield

        req = SuFieldRequest(
            project_id="p1",
            system_description="Generic system description",
            current_issues=[],
        )
        result = analyze_sufield(req)
        assert isinstance(result, SuFieldResponse)
        mock_llm.assert_called_once()


# ---------------------------------------------------------------------------
# Router endpoint tests via TestClient
# ---------------------------------------------------------------------------


class TestTrizSolveEndpoint:
    @patch("app.agents.triz_solver.call_llm_json", return_value=_TC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[1, 35])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<ctx>")
    def test_post_triz_solve_tc(self, mock_ctx, mock_matrix, mock_llm, client):
        resp = client.post("/api/v1/triz/solve", json={
            "project_id": "p1",
            "contradiction_id": "c1",
            "natural_description": "Efficiency vs weight",
            "improving_param": 9,
            "worsening_param": 1,
            "type": "TC",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "suggestions" in body
        assert body["mapped_improving"] == 9
        assert body["candidate_principles"] == [1, 35]

    @patch("app.agents.triz_solver.call_llm_json", return_value=_PC_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<ctx>")
    def test_post_triz_solve_pc(self, mock_ctx, mock_llm, client):
        resp = client.post("/api/v1/triz/solve", json={
            "project_id": "p1",
            "contradiction_id": "c2",
            "natural_description": "Rigid vs flexible",
            "physical_contradiction": "Must be rigid and flexible",
            "type": "PC",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["suggestions"]) == 1

    def test_post_triz_solve_missing_fields_422(self, client):
        """Missing required fields => 422."""
        resp = client.post("/api/v1/triz/solve", json={})
        assert resp.status_code == 422


class TestSuFieldEndpoint:
    @patch("app.agents.triz_solver.call_llm_json", return_value=_SUFIELD_LLM_RESPONSE)
    @patch("app.agents.triz_solver.build_sufield_context", return_value="<kb>")
    def test_post_triz_sufield(self, mock_ctx, mock_llm, client):
        resp = client.post("/api/v1/triz/sufield", json={
            "project_id": "p1",
            "system_description": "Battery cooled by plate",
            "current_issues": ["Insufficient heat transfer"],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["system_state"] == "insufficient"
        assert len(body["matched_solutions"]) == 2
        assert body["su_field"]["S1"] == "Battery cell"

    def test_post_triz_sufield_missing_fields_422(self, client):
        resp = client.post("/api/v1/triz/sufield", json={})
        assert resp.status_code == 422
