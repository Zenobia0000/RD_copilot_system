"""Tests for Auto-TRIZ v2 Analyst endpoints (WBS 8.2.1-8.2.5).

All LLM calls are mocked. DB writes are mocked to avoid Supabase dependency.
"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Mock LLM responses
# ---------------------------------------------------------------------------

_FIVE_WHY_LLM_RESPONSE = json.dumps({
    "why_chain": [
        {"why": "Why does the motor overheat?", "because": "Because copper losses exceed thermal dissipation capacity"},
        {"why": "Why do copper losses exceed capacity?", "because": "Because current density is too high at peak torque"},
        {"why": "Why is current density too high?", "because": "Because slot area is constrained by motor OD limit"},
        {"why": "Why is slot area constrained?", "because": "Because frame envelope was fixed before motor sizing"},
        {"why": "Why was frame envelope fixed first?", "because": "Because industrial design was finalized without thermal analysis input"},
    ],
    "root_causes": [
        "Frame envelope was locked without thermal co-design",
        "Slot area insufficient for required current at peak torque",
    ],
    "recommended_next_step": "Build function model to map thermal-structural interactions",
})

_KT_IS_IS_NOT_LLM_RESPONSE = json.dumps({
    "is_matrix": [
        {"dimension": "what", "is_value": "Motor overheating at peak torque", "is_not_value": "Motor overheating at steady state"},
        {"dimension": "where", "is_value": "Stator winding slot bottom", "is_not_value": "Rotor magnets or end-caps"},
        {"dimension": "when", "is_value": "During hill-climb above 15% grade", "is_not_value": "During flat-road cruising"},
        {"dimension": "extent", "is_value": "Temperature rise >80K in 5 min", "is_not_value": "Gradual rise over 30 min"},
    ],
    "distinctions": [
        "Peak torque requires 3x steady-state current",
        "Slot bottom has poorest thermal path to housing",
    ],
    "hypotheses": [
        "Insufficient thermal conductivity between slot liner and housing",
        "Slot fill factor too low, creating air gaps that act as insulators",
    ],
})

_FUNCTION_ANALYSIS_LLM_RESPONSE = json.dumps({
    "component_interactions": [
        {"from": "Stator", "to": "Rotor", "action": "generates electromagnetic torque", "type": "useful"},
        {"from": "Stator", "to": "Housing", "action": "conducts waste heat", "type": "insufficient"},
        {"from": "Rotor", "to": "Bearings", "action": "transmits radial load", "type": "useful"},
    ],
    "sf_diagnosis": {
        "S1": "Stator winding",
        "S2": "Housing",
        "F": "thermal",
        "state": "insufficient",
        "problem_summary": "Heat transfer from stator winding to housing is insufficient at peak load",
    },
    "subsystem_boundary": {
        "electromagnetic": ["Stator", "Rotor"],
        "thermal": ["Stator", "Housing"],
        "mechanical": ["Rotor", "Bearings"],
    },
})

_OZ_OT_LLM_RESPONSE = json.dumps({
    "oz_zone": "Stator slot bottom to housing inner surface (radial gap 0.5-1.0mm)",
    "ot_time": "During peak torque bursts lasting 10-30 seconds on hill climbs",
    "px_variable": "Slot liner thermal conductivity (must be high for cooling, but electrically insulating materials have low k)",
    "separation_hints": [
        "Condition separation: use thermally conductive but electrically insulating composite (e.g., BN-filled epoxy)",
        "Space separation: add dedicated thermal bridge at slot bottom, separate from electrical insulation at slot sides",
    ],
})

_ENTRY_GRADING_LLM_RESPONSE = json.dumps({
    "level": "B",
    "reasoning": "The problem involves coupled thermal-electromagnetic subsystems with partial test data. The contradiction is implicit but not yet formalized.",
    "recommended_steps": [
        "Run 5-Why to trace thermal failure root cause",
        "Build function model of stator-housing thermal path",
        "Formalize as TC: thermal conductivity vs electrical insulation",
    ],
})


# ---------------------------------------------------------------------------
# 8.2.1: POST /analyst/five-why
# ---------------------------------------------------------------------------

class TestFiveWhy:
    @patch("app.agents.analyst.call_llm_json", return_value=_FIVE_WHY_LLM_RESPONSE)
    def test_five_why_returns_chain(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/five-why", json={
            "project_id": "p1",
            "problem_statement": "Motor overheats during hill climbing",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["why_chain"]) == 5
        assert "root_causes" in body
        assert len(body["root_causes"]) >= 1
        assert "recommended_next_step" in body

    @patch("app.agents.analyst.call_llm_json", return_value=_FIVE_WHY_LLM_RESPONSE)
    def test_five_why_with_context(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/five-why", json={
            "project_id": "p1",
            "problem_statement": "Motor overheats",
            "context": "Mid-drive e-bike motor, 250W rated",
        })
        assert resp.status_code == 200
        mock_llm.assert_called_once()
        # Context should appear in the prompt
        call_args = mock_llm.call_args
        assert "Mid-drive e-bike motor" in call_args[0][1]

    def test_five_why_missing_problem_422(self, client):
        resp = client.post("/api/v1/analyst/five-why", json={
            "project_id": "p1",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 8.2.2: POST /analyst/kt-analysis
# ---------------------------------------------------------------------------

class TestKtAnalysis:
    @patch("app.agents.analyst.call_llm_json", return_value=_KT_IS_IS_NOT_LLM_RESPONSE)
    def test_kt_returns_matrix(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/kt-analysis", json={
            "project_id": "p1",
            "problem_statement": "Motor overheats only during hill climbing",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["is_matrix"]) == 4
        dimensions = {item["dimension"] for item in body["is_matrix"]}
        assert dimensions == {"what", "where", "when", "extent"}
        assert "distinctions" in body
        assert "hypotheses" in body

    @patch("app.agents.analyst.call_llm_json", return_value=_KT_IS_IS_NOT_LLM_RESPONSE)
    def test_kt_with_known_facts(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/kt-analysis", json={
            "project_id": "p1",
            "problem_statement": "Motor overheats",
            "known_facts": ["Peak torque is 80Nm", "Housing is aluminum"],
        })
        assert resp.status_code == 200
        call_args = mock_llm.call_args
        assert "Peak torque is 80Nm" in call_args[0][1]

    def test_kt_missing_problem_422(self, client):
        resp = client.post("/api/v1/analyst/kt-analysis", json={
            "project_id": "p1",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 8.2.3: POST /analyst/function-analysis
# ---------------------------------------------------------------------------

class TestFunctionAnalysis:
    @patch("app.agents.analyst.call_llm_json", return_value=_FUNCTION_ANALYSIS_LLM_RESPONSE)
    def test_function_analysis_returns_interactions(self, mock_llm, client):
        with patch("app.routers.analyst_v2.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_sb.return_value.table.return_value = mock_table
            mock_table.upsert.return_value.execute.return_value = None

            resp = client.post("/api/v1/analyst/function-analysis", json={
                "project_id": "p1",
                "system_description": "E-bike mid-drive motor assembly",
                "components": ["Stator", "Rotor", "Housing", "Bearings"],
            })
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["component_interactions"]) == 3
            assert body["sf_diagnosis"]["state"] == "insufficient"
            assert "subsystem_boundary" in body

    @patch("app.agents.analyst.call_llm_json", return_value=_FUNCTION_ANALYSIS_LLM_RESPONSE)
    def test_function_analysis_persists_to_db(self, mock_llm, client):
        with patch("app.routers.analyst_v2.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_sb.return_value.table.return_value = mock_table
            mock_table.upsert.return_value.execute.return_value = None

            client.post("/api/v1/analyst/function-analysis", json={
                "project_id": "p1",
                "system_description": "Motor assembly",
                "components": ["Stator", "Rotor"],
            })

            mock_sb.return_value.table.assert_called_with("function_models")
            mock_table.upsert.assert_called_once()
            payload = mock_table.upsert.call_args[0][0]
            assert payload["project_id"] == "p1"
            assert "component_interactions" in payload
            assert "sf_diagnosis" in payload

    @patch("app.agents.analyst.call_llm_json", return_value=_FUNCTION_ANALYSIS_LLM_RESPONSE)
    def test_function_analysis_survives_db_failure(self, mock_llm, client):
        """Result should still be returned even if DB write fails."""
        with patch("app.routers.analyst_v2.get_supabase", side_effect=Exception("DB down")):
            resp = client.post("/api/v1/analyst/function-analysis", json={
                "project_id": "p1",
                "system_description": "Motor assembly",
                "components": ["Stator", "Rotor"],
            })
            assert resp.status_code == 200
            assert len(resp.json()["component_interactions"]) == 3

    def test_function_analysis_missing_components_422(self, client):
        resp = client.post("/api/v1/analyst/function-analysis", json={
            "project_id": "p1",
            "system_description": "Motor assembly",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 8.2.4: POST /analyst/oz-ot-analysis
# ---------------------------------------------------------------------------

class TestOzOtAnalysis:
    @patch("app.agents.analyst.call_llm_json", return_value=_OZ_OT_LLM_RESPONSE)
    def test_oz_ot_returns_analysis(self, mock_llm, client):
        with patch("app.routers.analyst_v2.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_sb.return_value.table.return_value = mock_table
            mock_table.update.return_value.eq.return_value.execute.return_value = None

            resp = client.post("/api/v1/analyst/oz-ot-analysis", json={
                "project_id": "p1",
                "contradiction_id": "c1",
                "tc_description": "Improving thermal conductivity worsens electrical insulation",
                "improving_param": 17,
                "worsening_param": 33,
            })
            assert resp.status_code == 200
            body = resp.json()
            assert "oz_zone" in body
            assert "ot_time" in body
            assert "px_variable" in body
            assert "separation_hints" in body
            assert len(body["separation_hints"]) >= 1

    @patch("app.agents.analyst.call_llm_json", return_value=_OZ_OT_LLM_RESPONSE)
    def test_oz_ot_updates_contradiction_db(self, mock_llm, client):
        with patch("app.routers.analyst_v2.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_sb.return_value.table.return_value = mock_table
            mock_table.update.return_value.eq.return_value.execute.return_value = None

            client.post("/api/v1/analyst/oz-ot-analysis", json={
                "project_id": "p1",
                "contradiction_id": "c1",
                "tc_description": "TC description",
            })

            mock_sb.return_value.table.assert_called_with("contradictions")
            mock_table.update.assert_called_once()
            update_payload = mock_table.update.call_args[0][0]
            assert "oz_zone" in update_payload
            assert "ot_time" in update_payload
            assert "px_variable" in update_payload

    @patch("app.agents.analyst.call_llm_json", return_value=_OZ_OT_LLM_RESPONSE)
    def test_oz_ot_survives_db_failure(self, mock_llm, client):
        with patch("app.routers.analyst_v2.get_supabase", side_effect=Exception("DB down")):
            resp = client.post("/api/v1/analyst/oz-ot-analysis", json={
                "project_id": "p1",
                "contradiction_id": "c1",
                "tc_description": "TC description",
            })
            assert resp.status_code == 200
            assert "oz_zone" in resp.json()


# ---------------------------------------------------------------------------
# 8.2.5: POST /analyst/entry-grading
# ---------------------------------------------------------------------------

class TestEntryGrading:
    @patch("app.agents.analyst.call_llm_json", return_value=_ENTRY_GRADING_LLM_RESPONSE)
    def test_entry_grading_returns_level(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/entry-grading", json={
            "project_id": "p1",
            "problem_description": "Motor overheats during hill climbing",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] in ("A", "B", "C")
        assert "reasoning" in body
        assert "recommended_steps" in body
        assert len(body["recommended_steps"]) >= 1

    @patch("app.agents.analyst.call_llm_json", return_value=_ENTRY_GRADING_LLM_RESPONSE)
    def test_entry_grading_with_data(self, mock_llm, client):
        resp = client.post("/api/v1/analyst/entry-grading", json={
            "project_id": "p1",
            "problem_description": "Motor overheats",
            "available_data": {
                "thermal_test": True,
                "failure_modes": ["winding burnout"],
                "measurements": 12,
            },
        })
        assert resp.status_code == 200
        call_args = mock_llm.call_args
        assert "thermal_test" in call_args[0][1]

    def test_entry_grading_missing_description_422(self, client):
        resp = client.post("/api/v1/analyst/entry-grading", json={
            "project_id": "p1",
        })
        assert resp.status_code == 422
