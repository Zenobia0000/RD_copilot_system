"""End-to-end API integration tests — WP-6.2.

Tests full router -> agent -> response chains with mocked external services.

Phase 1 flow: extract brief -> generate socratic questions -> extract assumptions
Phase 2 flow: solve TRIZ -> SCAMPER transform -> MUST evaluate
"""

from __future__ import annotations

import json
from unittest.mock import patch, AsyncMock

import pytest

from app.services.evidence_retrieval import EvidenceContext, EvidenceReference as SvcEvidenceRef


# ---------------------------------------------------------------------------
# Shared LLM response fixtures
# ---------------------------------------------------------------------------

_BRIEF_EXTRACT_RESPONSE = json.dumps({
    "constraints": [
        {
            "code": "C1",
            "description": "Rated power >= 250W",
            "source": "EU regulation",
            "type": "hard",
            "feasibility": "feasible",
        },
        {
            "code": "C2",
            "description": "Weight <= 4kg",
            "source": "customer_spec",
            "type": "hard",
            "feasibility": "challenging",
        },
    ],
    "kpis": [
        {
            "name": "Efficiency",
            "target_value": "92",
            "unit": "%",
            "measurement_method": "dynamometer",
        },
        {
            "name": "Noise",
            "target_value": "55",
            "unit": "dB(A)",
            "measurement_method": "anechoic chamber",
        },
    ],
    "assumptions": [
        "Ambient temperature is 25-40C",
        "Battery voltage is 48V nominal",
    ],
    "feasibility_warnings": [
        "4kg weight target is aggressive for 250W rated power",
    ],
})

_SOCRATIC_RESPONSE = json.dumps({
    "questions": [
        {
            "category": "assumption",
            "text": "What if ambient temperature exceeds 40C during summer use?",
            "suggested_tag": "assumption",
        },
        {
            "category": "contradiction",
            "text": "How can we achieve 250W in under 4kg without sacrificing efficiency?",
            "suggested_tag": "contradiction",
        },
        {
            "category": "clarification",
            "text": "Is the 92% efficiency target at rated power or peak power?",
            "suggested_tag": None,
        },
    ],
})

_ASSUMPTION_EXTRACT_RESPONSE = json.dumps({
    "assumptions": [
        {
            "content": "Motor will not operate above 45C ambient",
            "source": "Q&A session",
            "worst_consequence": "Insulation breakdown leading to motor failure",
            "worst_severity": "critical",
        },
        {
            "content": "48V battery maintains voltage above 42V under load",
            "source": "Q&A session",
            "worst_consequence": "Reduced torque at low battery",
            "worst_severity": "high",
        },
    ],
})

_TRIZ_TC_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "TC",
            "principle_number": 35,
            "principle_name": "Parameter changes",
            "suggestion": "Use high-density winding to reduce motor size/weight",
            "affected_modules": ["stator", "winding"],
            "secondary_contradictions": ["May increase thermal resistance"],
        },
    ],
})

_SCAMPER_RESPONSE = json.dumps({
    "variants": [
        {
            "action": "Substitute",
            "description": "Replace copper winding with aluminium to reduce weight",
            "potential_benefits": "30% weight reduction in winding",
            "new_contradictions": ["Lower conductivity increases I2R losses"],
        },
        {
            "action": "Combine",
            "description": "Integrate controller into motor housing",
            "potential_benefits": "Eliminate separate controller housing weight",
            "new_contradictions": ["Thermal coupling between motor and controller"],
        },
    ],
})
# NOTE: _SCAMPER_RESPONSE kept for backward-compat test of scamper_transform()
# internal function. The /scamper/perform endpoint has been removed.

_MUST_EVAL_RESPONSE = json.dumps({
    "criteria_results": [
        {
            "id": "M1",
            "label": "Rated power >= 250W",
            "passed": True,
            "confidence": 0.9,
            "reasoning": "High-density winding design supports 250W output",
            "evidence_sources": ["motor_design_calc"],
        },
        {
            "id": "M2",
            "label": "Weight <= 4kg",
            "passed": True,
            "confidence": 0.7,
            "reasoning": "Estimated 3.8kg with aluminium winding substitution",
            "evidence_sources": ["weight_estimate"],
        },
    ],
    "overall_pass": True,
    "summary": "Alternative passes all MUST criteria with moderate-to-high confidence",
})


# ---------------------------------------------------------------------------
# Phase 1 Integration: Brief -> Socratic -> Assumptions
# ---------------------------------------------------------------------------


class TestPhase1Flow:
    """End-to-end Phase 1: extract brief, generate socratic questions, extract assumptions."""

    @patch("app.agents.analyst.call_llm_json")
    def test_full_phase1_flow(self, mock_llm, client):
        """Chain: extract brief -> socratic questions -> assumption extraction."""

        # D1: Extract brief
        mock_llm.return_value = _BRIEF_EXTRACT_RESPONSE
        resp1 = client.post("/api/v1/definitions/extract", json={
            "project_id": "proj-integration-1",
            "raw_text": "Design a 250W e-bike hub motor, max 4kg, 92% efficiency, 55dB noise limit.",
        })
        assert resp1.status_code == 200
        brief = resp1.json()
        assert len(brief["constraints"]) == 2
        assert len(brief["kpis"]) == 2
        assert len(brief["assumptions"]) == 2

        # D2: Generate Socratic questions using extracted brief data
        mock_llm.return_value = _SOCRATIC_RESPONSE
        resp2 = client.post("/api/v1/questions/generate", json={
            "project_id": "proj-integration-1",
            "mission": "Design a 250W e-bike hub motor under 4kg",
            "constraints": [c["description"] for c in brief["constraints"]],
            "existing_questions": [],
        })
        assert resp2.status_code == 200
        socratic = resp2.json()
        assert len(socratic["questions"]) == 3
        # Verify question categories are present
        categories = {q["category"] for q in socratic["questions"]}
        assert "assumption" in categories
        assert "contradiction" in categories

        # D3: Extract assumptions from Q&A answers
        mock_llm.return_value = _ASSUMPTION_EXTRACT_RESPONSE
        resp3 = client.post("/api/v1/assumptions/extract", json={
            "project_id": "proj-integration-1",
            "mission": "Design a 250W e-bike hub motor under 4kg",
            "questions_and_answers": [
                {
                    "question": socratic["questions"][0]["text"],
                    "answer": "We assume ambient never exceeds 45C based on target market climate data.",
                },
                {
                    "question": socratic["questions"][1]["text"],
                    "answer": "We rely on 48V battery maintaining at least 42V under full load.",
                },
            ],
        })
        assert resp3.status_code == 200
        assumptions = resp3.json()
        assert len(assumptions["assumptions"]) == 2
        assert assumptions["assumptions"][0]["worst_severity"] == "critical"
        assert assumptions["assumptions"][1]["worst_severity"] == "high"

    @patch("app.agents.analyst.call_llm_json")
    def test_phase1_extract_then_socratic_consistency(self, mock_llm, client):
        """Verify data from extract step can feed into socratic step."""
        mock_llm.return_value = _BRIEF_EXTRACT_RESPONSE
        resp1 = client.post("/api/v1/definitions/extract", json={
            "project_id": "p2",
            "raw_text": "Some motor spec",
        })
        brief = resp1.json()

        mock_llm.return_value = _SOCRATIC_RESPONSE
        resp2 = client.post("/api/v1/questions/generate", json={
            "project_id": "p2",
            "mission": "Design motor",
            "constraints": [c["description"] for c in brief["constraints"]],
        })
        assert resp2.status_code == 200
        # LLM was called with constraint text from brief
        call_args = mock_llm.call_args[0][1]
        assert "Rated power" in call_args or "Weight" in call_args


# ---------------------------------------------------------------------------
# Phase 2 Integration: TRIZ -> SCAMPER -> MUST
# ---------------------------------------------------------------------------


class TestPhase2Flow:
    """End-to-end Phase 2: solve TRIZ, MUST evaluate.

    SCAMPER step removed — TRIZ 40 principles now cover all SCAMPER actions.
    """

    @patch("app.agents.evaluator.call_llm_json")
    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[35, 1, 28])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<tc_context>")
    def test_full_phase2_flow(self, mock_tc_ctx, mock_matrix, mock_triz_llm, mock_eval_llm, client):
        """Chain: TRIZ solve -> MUST evaluate."""

        # X2: Solve TRIZ contradiction
        mock_triz_llm.return_value = _TRIZ_TC_RESPONSE
        resp1 = client.post("/api/v1/triz/solve", json={
            "project_id": "proj-integration-2",
            "contradiction_id": "c1",
            "natural_description": "Motor weight vs output power",
            "improving_param": 9,
            "worsening_param": 1,
            "type": "TC",
        })
        assert resp1.status_code == 200
        triz_result = resp1.json()
        assert len(triz_result["suggestions"]) >= 1
        assert triz_result["candidate_principles"] == [35, 1, 28]

        # X4: MUST evaluation on proposed alternative
        mock_eval_llm.return_value = _MUST_EVAL_RESPONSE
        resp2 = client.post("/api/v1/must/evaluate", json={
            "project_id": "proj-integration-2",
            "alternative_name": "High-density aluminium winding motor",
            "mechanism": "Replace copper with aluminium, integrate controller",
            "must_criteria": [
                {
                    "id": "M1",
                    "label": "Rated power >= 250W",
                    "source": "C1",
                    "threshold": "250W",
                },
                {
                    "id": "M2",
                    "label": "Weight <= 4kg",
                    "source": "C2",
                    "threshold": "4kg",
                },
            ],
            "constraints": ["Rated power >= 250W", "Weight <= 4kg"],
            "kpis": ["Efficiency >= 92%"],
        })
        assert resp2.status_code == 200
        must_result = resp2.json()
        assert must_result["overall_pass"] is True
        assert len(must_result["criteria_results"]) == 2
        assert all(cr["passed"] for cr in must_result["criteria_results"])


# ---------------------------------------------------------------------------
# Cross-phase edge cases
# ---------------------------------------------------------------------------


class TestCrossPhaseEdgeCases:
    @patch("app.agents.analyst.call_llm_json")
    def test_extract_with_empty_text_then_socratic(self, mock_llm, client):
        """Even with minimal extraction, socratic generation should work."""
        mock_llm.return_value = json.dumps({
            "constraints": [],
            "kpis": [],
            "assumptions": [],
            "feasibility_warnings": [],
        })
        resp1 = client.post("/api/v1/definitions/extract", json={
            "project_id": "p4",
            "raw_text": "",
        })
        assert resp1.status_code == 200

        mock_llm.return_value = _SOCRATIC_RESPONSE
        resp2 = client.post("/api/v1/questions/generate", json={
            "project_id": "p4",
            "mission": "Vague mission",
            "constraints": [],
        })
        assert resp2.status_code == 200

    @patch("app.agents.evaluator.call_llm_json")
    def test_must_evaluate_with_no_criteria(self, mock_llm, client):
        """MUST evaluation with empty criteria list should still return valid response."""
        mock_llm.return_value = json.dumps({
            "criteria_results": [],
            "overall_pass": True,
            "summary": "No criteria to evaluate",
        })
        resp = client.post("/api/v1/must/evaluate", json={
            "project_id": "p5",
            "alternative_name": "Test alt",
            "mechanism": "Test mechanism",
            "must_criteria": [],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["criteria_results"] == []

    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.build_triz_pc_context", return_value="<ctx>")
    def test_triz_pc_solve(self, mock_ctx, mock_llm, client):
        """PC path TRIZ solve returns suggestions with affected modules."""
        mock_llm.return_value = json.dumps({
            "suggestions": [
                {
                    "path": "PC",
                    "principle_number": None,
                    "principle_name": "Separation in space",
                    "suggestion": "Separate heat generation zone from electronics",
                    "affected_modules": ["housing"],
                    "secondary_contradictions": [],
                },
            ],
        })
        resp1 = client.post("/api/v1/triz/solve", json={
            "project_id": "p6",
            "contradiction_id": "c10",
            "natural_description": "Hot and cold at the same time",
            "physical_contradiction": "Housing must be thermally conductive and insulating",
            "type": "PC",
        })
        assert resp1.status_code == 200
        triz = resp1.json()
        assert len(triz["suggestions"]) >= 1
        assert triz["suggestions"][0]["affected_modules"] == ["housing"]
