"""Tests for Brief extraction API (definitions router + analyst agent) — WP-6.1.

Covers /definitions/extract, /definitions/suggest-constraints, /definitions/suggest-kpis.
All LLM and evidence retrieval calls are mocked.
"""

from __future__ import annotations

import json
from unittest.mock import patch, AsyncMock

import pytest

from app.services.evidence_retrieval import EvidenceContext, EvidenceReference as SvcEvidenceRef


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

_EXTRACT_LLM_RESPONSE = json.dumps({
    "constraints": [
        {
            "code": "C1",
            "description": "Motor efficiency >= 95%",
            "source": "customer_spec",
            "type": "hard",
            "feasibility": "feasible",
        },
    ],
    "kpis": [
        {
            "name": "Efficiency",
            "target_value": "95",
            "unit": "%",
            "measurement_method": "dynamometer test",
        },
    ],
    "assumptions": ["Ambient temperature <= 40C"],
    "feasibility_warnings": ["Weight target may conflict with efficiency"],
})

_SUGGEST_CONSTRAINTS_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "description": "IP67 water resistance",
            "source": "IEC 60529",
            "rationale": "E-bike motors are exposed to rain",
            "ref_ids": ["WEB-SEARCH-001"],
        },
    ],
})

_SUGGEST_KPIS_LLM_RESPONSE = json.dumps({
    "suggestions": [
        {
            "kpi_name": "Thermal Rise",
            "target_value": "60",
            "unit": "K",
            "measurement_method": "thermocouple during rated load",
            "rationale": "Prevents insulation degradation",
            "ref_ids": ["WEB-SEARCH-002"],
        },
    ],
})


def _mock_evidence_context() -> EvidenceContext:
    return EvidenceContext(
        prompt_context="[Evidence: some web search results]",
        references=[
            SvcEvidenceRef(
                ref_id="WEB-SEARCH-001",
                ref_type="web_search",
                title="IP67 Standard",
                source="iec.ch",
                url="https://iec.ch/ip67",
                snippet="IP67 means dust-tight and waterproof...",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# /definitions/extract
# ---------------------------------------------------------------------------


class TestBriefExtract:
    @patch("app.agents.analyst.call_llm_json", return_value=_EXTRACT_LLM_RESPONSE)
    def test_extract_returns_brief_extraction_response(self, mock_llm, client):
        resp = client.post("/api/v1/definitions/extract", json={
            "project_id": "p1",
            "raw_text": "Design an e-bike motor with 95% efficiency under 5kg",
        })
        assert resp.status_code == 200
        body = resp.json()

        assert "constraints" in body
        assert "kpis" in body
        assert "assumptions" in body
        assert "feasibility_warnings" in body

        assert len(body["constraints"]) == 1
        assert body["constraints"][0]["code"] == "C1"
        assert len(body["kpis"]) == 1
        assert body["kpis"][0]["name"] == "Efficiency"
        assert len(body["assumptions"]) == 1

    @patch("app.agents.analyst.call_llm_json", return_value=_EXTRACT_LLM_RESPONSE)
    def test_extract_calls_llm_with_raw_text(self, mock_llm, client):
        client.post("/api/v1/definitions/extract", json={
            "project_id": "p1",
            "raw_text": "Motor spec document contents",
        })
        mock_llm.assert_called_once()
        # The user prompt should contain the raw_text
        call_args = mock_llm.call_args
        assert "Motor spec document contents" in call_args[0][1]

    def test_extract_missing_project_id_422(self, client):
        resp = client.post("/api/v1/definitions/extract", json={
            "raw_text": "something",
        })
        assert resp.status_code == 422

    @patch("app.agents.analyst.call_llm_json")
    def test_extract_empty_raw_text(self, mock_llm, client):
        """Empty raw_text is allowed (schema has default='')."""
        mock_llm.return_value = json.dumps({
            "constraints": [],
            "kpis": [],
            "assumptions": [],
            "feasibility_warnings": [],
        })
        resp = client.post("/api/v1/definitions/extract", json={
            "project_id": "p1",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["constraints"] == []


# ---------------------------------------------------------------------------
# /definitions/suggest-constraints
# ---------------------------------------------------------------------------


class TestSuggestConstraints:
    @patch(
        "app.agents.analyst.retrieve_constraint_evidence",
        new_callable=AsyncMock,
        return_value=_mock_evidence_context(),
    )
    @patch("app.agents.analyst.call_llm_json", return_value=_SUGGEST_CONSTRAINTS_LLM_RESPONSE)
    def test_suggest_constraints_returns_list(self, mock_llm, mock_evidence, client):
        resp = client.post("/api/v1/definitions/suggest-constraints", json={
            "project_id": "p1",
            "mission": "Design an e-bike motor",
            "existing_constraints": ["Weight < 5kg"],
        })
        assert resp.status_code == 200
        body = resp.json()

        assert "suggestions" in body
        assert len(body["suggestions"]) == 1
        assert body["suggestions"][0]["description"] == "IP67 water resistance"

        # Evidence references should be present
        assert "evidence_references" in body
        assert len(body["evidence_references"]) >= 1

    @patch(
        "app.agents.analyst.retrieve_constraint_evidence",
        new_callable=AsyncMock,
        return_value=_mock_evidence_context(),
    )
    @patch("app.agents.analyst.call_llm_json", return_value=_SUGGEST_CONSTRAINTS_LLM_RESPONSE)
    def test_suggest_constraints_empty_existing(self, mock_llm, mock_evidence, client):
        """Works fine with no existing constraints."""
        resp = client.post("/api/v1/definitions/suggest-constraints", json={
            "project_id": "p1",
            "mission": "Design an e-bike motor",
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /definitions/suggest-kpis
# ---------------------------------------------------------------------------


class TestSuggestKpis:
    @patch(
        "app.agents.analyst.retrieve_kpi_evidence",
        new_callable=AsyncMock,
        return_value=_mock_evidence_context(),
    )
    @patch("app.agents.analyst.call_llm_json", return_value=_SUGGEST_KPIS_LLM_RESPONSE)
    def test_suggest_kpis_returns_list(self, mock_llm, mock_evidence, client):
        resp = client.post("/api/v1/definitions/suggest-kpis", json={
            "project_id": "p1",
            "mission": "Design an e-bike motor",
            "constraints": ["Weight < 5kg", "Efficiency >= 95%"],
            "existing_kpis": [],
        })
        assert resp.status_code == 200
        body = resp.json()

        assert "suggestions" in body
        assert len(body["suggestions"]) == 1
        assert body["suggestions"][0]["kpi_name"] == "Thermal Rise"
        assert body["suggestions"][0]["measurement_method"] == "thermocouple during rated load"

        # Evidence references
        assert "evidence_references" in body

    @patch(
        "app.agents.analyst.retrieve_kpi_evidence",
        new_callable=AsyncMock,
        return_value=_mock_evidence_context(),
    )
    @patch("app.agents.analyst.call_llm_json", return_value=_SUGGEST_KPIS_LLM_RESPONSE)
    def test_suggest_kpis_includes_ref_ids(self, mock_llm, mock_evidence, client):
        """Suggested KPIs should include ref_ids linking to evidence."""
        resp = client.post("/api/v1/definitions/suggest-kpis", json={
            "project_id": "p1",
            "mission": "Design an e-bike motor",
            "constraints": [],
        })
        body = resp.json()
        assert body["suggestions"][0]["ref_ids"] == ["WEB-SEARCH-002"]

    def test_suggest_kpis_missing_mission_422(self, client):
        resp = client.post("/api/v1/definitions/suggest-kpis", json={
            "project_id": "p1",
        })
        assert resp.status_code == 422
