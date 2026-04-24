"""API contract tests for POST /triz/solve-layered — WBS 12.4.

Verifies the wire format between FE and backend:
  - required request fields (422 on missing project_id / contradiction_id)
  - optional control flags (quick_mode / force_l2 / severity)
  - response shape mirrors LayeredTrizSolution Pydantic model
  - Phase B directive defaults emitted on the wire
  - back-compat: legacy POST /triz/solve still returns the flat payload

All LLM calls are mocked. No network.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

# Reuse the canned LLM responses from the orchestrator test module so this
# stays the single source of truth for the e-bike golden case.
from tests.test_triz_layered import (
    _L1_TC_RAW,
    _L1_CRITIC_TRIGGER_RAW,
    _DEEPEN_LINK_RAW,
    _L2_PC_RAW,
    _L3_SF_RAW,
    _DIFF_RAW,
)


def _router(queue):
    def _pop(*args, **kwargs):
        return queue.pop(0) if queue else "{}"

    return _pop


class TestSolveLayeredEndpoint:
    """HTTP contract for POST /triz/solve-layered."""

    @patch("app.agents.triz_solver.lookup_matrix", return_value=[19, 35, 3, 36])
    def test_post_solve_layered_happy_path(self, _matrix_mock, client):
        queue = [
            _L1_TC_RAW,
            _L1_CRITIC_TRIGGER_RAW,
            _DEEPEN_LINK_RAW,
            _L2_PC_RAW,
            _L3_SF_RAW,   # _solve_sf
            _L3_SF_RAW,   # analyze_sufield enrichment
            _DIFF_RAW,
        ]
        with patch("app.agents.triz_solver.call_llm_json", side_effect=_router(queue)):
            resp = client.post(
                "/api/v1/triz/solve-layered",
                json={
                    "project_id": "ebike-001",
                    "contradiction_id": "C-EBIKE-012",
                    "natural_description": "馬達功率密度提升導致定子溫度",
                    "improving_param": 21,
                    "worsening_param": 17,
                    "severity": "major",
                    "sf_substance_1": "定子繞線",
                    "sf_substance_2": "外殼",
                    "sf_field": "熱場",
                },
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()

        # Top-level envelope
        assert "layered_solution" in body
        lts = body["layered_solution"]

        # Identity
        assert lts["id"].startswith("LTS-")
        assert lts["contradiction_id"] == "C-EBIKE-012"
        assert lts["severity"] == "major"

        # L1
        assert lts["l1_surface"]["status"] == "ran"
        assert lts["l1_surface"]["candidate_principles"] == [19, 35, 3, 36]
        assert lts["l1_surface"]["critic_trigger_l2"] is True

        # L2 triggered + deepen_link materialised
        assert lts["l2_root_cause"] is not None
        assert lts["l2_root_cause"]["triggered"] is True
        dl = lts["l2_root_cause"]["deepen_link"]
        assert "P(t)" in dl["derived_physical_parameter"]
        # tuple is serialised as a 2-element JSON array
        assert dl["from_tc_pair"] == [21, 17]
        sep = dl["separation_type_candidates"]
        assert sep[0]["type"] == "time"
        assert sep[0]["confidence"] == pytest.approx(0.85)

        # L3
        assert lts["l3_structural_check"]["status"] == "ran"
        assert lts["l3_structural_check"]["su_field_model"]["state"] in (
            "insufficient", "harmful", "unknown"
        )
        # L3 bridge text hydrated from differential_analysis.l3_bridge
        assert lts["l3_structural_check"]["standalone_value"] != ""

        # differential_analysis: recommended_route points at L2+L3
        route = lts["differential_analysis"]["recommended_route"]
        assert route["primary"].startswith("L2")
        assert route["adopted_layers"] == ["L2", "L3"]

        # Phase B directive defaults — the intra-LTS SKIP rule
        pbd = lts["phase_b_directive"]
        assert pbd["same_contradiction_intra_layer_conflict"] == "skip"
        assert pbd["cross_contradiction_conflict"] == "check"

    @patch("app.agents.triz_solver.lookup_matrix", return_value=[19, 35, 3, 36])
    def test_post_solve_layered_quick_mode_minor(self, _matrix_mock, client):
        """severity=minor + quick_mode=true → L2 status=skipped_quick_mode."""
        queue = [_L1_TC_RAW, '{"trigger_l2": false, "reason": "ok", "confidence": 0.9}',
                 _L3_SF_RAW, _L3_SF_RAW, _DIFF_RAW]
        with patch("app.agents.triz_solver.call_llm_json", side_effect=_router(queue)):
            resp = client.post(
                "/api/v1/triz/solve-layered",
                json={
                    "project_id": "ebike-001",
                    "contradiction_id": "C-EBIKE-014",
                    "natural_description": "minor 微調",
                    "improving_param": 21,
                    "worsening_param": 17,
                    "severity": "minor",
                    "quick_mode": True,
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            lts = body["layered_solution"]
            if lts["l2_root_cause"] is not None:
                assert lts["l2_root_cause"]["status"] == "skipped_quick_mode"
                assert "quick_mode" in lts["l2_root_cause"]["trigger_reason"]

    def test_post_solve_layered_missing_fields_422(self, client):
        """Missing required fields → FastAPI validation 422."""
        resp = client.post("/api/v1/triz/solve-layered", json={})
        assert resp.status_code == 422

    def test_post_solve_layered_unknown_severity_rejected(self, client):
        """Unknown severity literal → 422."""
        resp = client.post(
            "/api/v1/triz/solve-layered",
            json={
                "project_id": "p",
                "contradiction_id": "c",
                "natural_description": "x",
                "severity": "catastrophic",  # not in Literal
            },
        )
        assert resp.status_code == 422

    def test_legacy_triz_solve_still_works(self, client):
        """WBS 12.6 back-compat: /triz/solve endpoint must still return flat format."""
        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=json.dumps({"suggestions": []}),
        ), patch("app.agents.triz_solver.lookup_matrix", return_value=[1]), patch(
            "app.agents.triz_solver.build_triz_tc_context", return_value="<ctx>"
        ):
            resp = client.post(
                "/api/v1/triz/solve",
                json={
                    "project_id": "p1",
                    "contradiction_id": "c1",
                    "natural_description": "t",
                    "improving_param": 9,
                    "worsening_param": 1,
                    "type": "TC",
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            # Legacy shape — flat `suggestions` array, not layered envelope
            assert "suggestions" in body
            assert "layered_solution" not in body


class TestLayeredTrizSolutionSchemaSnapshot:
    """Schema snapshot guard — alerts when the wire format drifts."""

    def test_top_level_fields_are_frozen(self):
        from app.models.schemas import LayeredTrizSolution
        expected_top_level = {
            "id", "project_id", "contradiction_id",
            "contradiction_natural_description", "severity",
            "l1_surface", "l2_root_cause", "l3_structural_check",
            "differential_analysis", "phase_b_directive",
        }
        actual = set(LayeredTrizSolution.model_fields.keys())
        assert actual == expected_top_level, (
            f"LayeredTrizSolution top-level schema drifted.\n"
            f"added: {actual - expected_top_level}\n"
            f"removed: {expected_top_level - actual}"
        )

    def test_phase_b_directive_defaults_frozen(self):
        from app.models.schemas import PhaseBDirective
        d = PhaseBDirective()
        assert d.same_contradiction_intra_layer_conflict == "skip"
        assert d.cross_contradiction_conflict == "check"

    def test_separation_type_enum_frozen(self):
        """Regression guard for WBS 1.2 frozen enums."""
        from app.models.schemas import SeparationCandidate
        valid = ["time", "space", "condition", "whole_part"]
        for t in valid:
            SeparationCandidate(type=t, rationale="", confidence=0.5)
        with pytest.raises(Exception):
            SeparationCandidate(type="temporal", rationale="", confidence=0.5)
