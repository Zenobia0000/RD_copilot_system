"""Tests for Gate checking logic — WP-6.1.

Covers gates 1.1, 1.2, 2.2 and invalid gate_id handling.
All Supabase queries are mocked to return controlled data.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import AiReviewResult


# ---------------------------------------------------------------------------
# Helpers — mock Supabase query builder chain
# ---------------------------------------------------------------------------


def _sb_response(data=None, count=None):
    """Build an object that mimics a Supabase query result."""
    return SimpleNamespace(data=data, count=count)


def _make_chain(final_response):
    """Return a mock that supports chained Supabase query calls like:
    sb.table("x").select("y").eq("k","v").maybe_single().execute()
    """
    m = MagicMock()
    m.execute.return_value = final_response
    m.maybe_single.return_value = m
    m.eq.return_value = m
    m.select.return_value = m
    return m


def _build_sb_mock(table_map: dict[str, MagicMock]) -> MagicMock:
    """Build a get_supabase() mock where .table(name) dispatches to table_map."""
    sb = MagicMock()
    sb.table.side_effect = lambda name: table_map[name]
    return sb


# ---------------------------------------------------------------------------
# Gate D1 — Mission + KPIs
# ---------------------------------------------------------------------------


class TestGate11:
    @patch("app.routers.gates.get_supabase")
    def test_gate_11_pass_mission_and_3_kpis(self, mock_sb, client):
        """Mission exists + >=3 KPIs with measurement_method => pass."""
        briefs_chain = _make_chain(_sb_response(data={"mission": "Design an e-bike motor"}))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "k1", "measurement_method": "dynamometer"},
            {"id": "k2", "measurement_method": "thermal sensor"},
            {"id": "k3", "measurement_method": "efficiency meter"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is True
        assert body["gate_id"] == "D1"
        assert len(body["failed_reasons"]) == 0
        assert len(body["checklist_items"]) == 3

    @patch("app.routers.gates.get_supabase")
    def test_gate_11_fail_no_mission(self, mock_sb, client):
        """No mission => fail with reason."""
        briefs_chain = _make_chain(_sb_response(data=None))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "k1", "measurement_method": "m1"},
            {"id": "k2", "measurement_method": "m2"},
            {"id": "k3", "measurement_method": "m3"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is False
        assert any("Mission" in r for r in body["failed_reasons"])

    @patch("app.routers.gates.get_supabase")
    def test_gate_11_fail_too_few_kpis(self, mock_sb, client):
        """Only 2 KPIs => fail."""
        briefs_chain = _make_chain(_sb_response(data={"mission": "OK"}))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "k1", "measurement_method": "m1"},
            {"id": "k2", "measurement_method": "m2"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is False
        assert any("KPI" in r for r in body["failed_reasons"])

    @patch("app.routers.gates.get_supabase")
    def test_gate_11_fail_kpis_missing_measurement(self, mock_sb, client):
        """3 KPIs but one missing measurement_method => checklist item not met."""
        briefs_chain = _make_chain(_sb_response(data={"mission": "OK"}))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "k1", "measurement_method": "m1"},
            {"id": "k2", "measurement_method": ""},
            {"id": "k3", "measurement_method": "m3"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": "p1"})
        body = resp.json()
        # The third checklist item checks that all KPIs have measurement methods
        measurement_item = body["checklist_items"][2]
        assert measurement_item["met"] is False


# ---------------------------------------------------------------------------
# Gate D2 — Assumptions + High-risk + Contradictions
# ---------------------------------------------------------------------------


class TestGate12:
    @patch("app.routers.gates.get_supabase")
    def test_gate_12_pass(self, mock_sb, client):
        """>=10 assumptions, >=3 high-risk, >=3 contradictions => pass."""
        assumptions_data = [
            {"id": f"a{i}", "worst_severity": "critical" if i < 3 else "medium"}
            for i in range(12)
        ]
        assumptions_chain = _make_chain(_sb_response(data=assumptions_data))
        contradictions_chain = _make_chain(_sb_response(data=[], count=5))
        sb = _build_sb_mock({
            "assumptions": assumptions_chain,
            "contradictions": contradictions_chain,
        })
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D2/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is True
        assert len(body["checklist_items"]) == 3

    @patch("app.routers.gates.get_supabase")
    def test_gate_12_fail_insufficient_assumptions(self, mock_sb, client):
        """Only 5 assumptions => fail."""
        assumptions_data = [
            {"id": f"a{i}", "worst_severity": "high"} for i in range(5)
        ]
        assumptions_chain = _make_chain(_sb_response(data=assumptions_data))
        contradictions_chain = _make_chain(_sb_response(data=[], count=3))
        sb = _build_sb_mock({
            "assumptions": assumptions_chain,
            "contradictions": contradictions_chain,
        })
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D2/check", params={"project_id": "p1"})
        body = resp.json()
        assert body["passed"] is False
        assert any("假設不足" in r for r in body["failed_reasons"])

    @patch("app.routers.gates.get_supabase")
    def test_gate_12_fail_insufficient_contradictions(self, mock_sb, client):
        """>=10 assumptions, >=3 high-risk but only 1 contradiction => fail."""
        assumptions_data = [
            {"id": f"a{i}", "worst_severity": "critical" if i < 4 else "low"}
            for i in range(11)
        ]
        assumptions_chain = _make_chain(_sb_response(data=assumptions_data))
        contradictions_chain = _make_chain(_sb_response(data=[], count=1))
        sb = _build_sb_mock({
            "assumptions": assumptions_chain,
            "contradictions": contradictions_chain,
        })
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D2/check", params={"project_id": "p1"})
        body = resp.json()
        assert body["passed"] is False
        assert any("矛盾不足" in r for r in body["failed_reasons"])


# ---------------------------------------------------------------------------
# Gate X2 — Alternatives with MUST pass
# ---------------------------------------------------------------------------


class TestGate22:
    @patch("app.routers.gates.get_supabase")
    def test_gate_22_pass(self, mock_sb, client):
        """>=3 alternatives => pass."""
        alts = [
            {"id": f"alt{i}", "must_scores": {}, "overall_pass": True}
            for i in range(3)
        ]
        alt_chain = _make_chain(_sb_response(data=alts))
        sb = _build_sb_mock({"alternatives": alt_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/X2/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is True

    @patch("app.routers.gates.get_supabase")
    def test_gate_22_fail_too_few_alternatives(self, mock_sb, client):
        """Only 2 alternatives => fail."""
        alts = [
            {"id": f"alt{i}", "must_scores": {}, "overall_pass": True}
            for i in range(2)
        ]
        alt_chain = _make_chain(_sb_response(data=alts))
        sb = _build_sb_mock({"alternatives": alt_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/X2/check", params={"project_id": "p1"})
        body = resp.json()
        assert body["passed"] is False
        assert any("方案不足" in r for r in body["failed_reasons"])


# ---------------------------------------------------------------------------
# Invalid gate_id
# ---------------------------------------------------------------------------


class TestGateInvalid:
    def test_invalid_gate_id_returns_400(self, client):
        resp = client.get("/api/v1/gates/INVALID/check", params={"project_id": "p1"})
        assert resp.status_code == 400

    def test_missing_project_id_returns_422(self, client):
        resp = client.get("/api/v1/gates/D1/check")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Gate PG-V — always requires manual confirmation
# ---------------------------------------------------------------------------


class TestGatePG3:
    @patch("app.routers.gates.get_supabase")
    def test_pg3_always_fails(self, mock_sb, client):
        """PG3 always returns passed=False (requires manual confirmation)."""
        sb = MagicMock()
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/PG-V/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is False
        assert len(body["failed_reasons"]) > 0


# ---------------------------------------------------------------------------
# AI Review — backward compatibility + integration
# ---------------------------------------------------------------------------


class TestAiReviewBackwardCompat:
    @patch("app.routers.gates.get_supabase")
    def test_ai_review_null_by_default(self, mock_sb, client):
        """Without include_ai_review, ai_review should be null."""
        briefs_chain = _make_chain(_sb_response(data={"mission": "OK"}))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "k1", "measurement_method": "m1"},
            {"id": "k2", "measurement_method": "m2"},
            {"id": "k3", "measurement_method": "m3"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": "p1"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ai_review"] is None

    @patch("app.routers.gates.get_supabase")
    def test_ai_review_null_for_gate_without_evaluator(self, mock_sb, client):
        """Gate V2 has no AI evaluator — ai_review stays null even when requested."""
        decisions_chain = _make_chain(_sb_response(data=[
            {"id": "d1", "status": "confirmed"},
        ]))
        sb = _build_sb_mock({"decisions": decisions_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/V2/check", params={
            "project_id": "p1",
            "include_ai_review": "true",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ai_review"] is None


class TestAiReviewIntegration:
    @patch("app.routers.gates.run_ai_review")
    @patch("app.routers.gates.get_supabase")
    def test_ai_review_called_for_gate_22(self, mock_sb, mock_ai, client):
        """Gate X2 has ai_evaluator='must' — should call _run_ai_review when requested."""
        alts = [{"id": f"alt{i}", "must_scores": {}, "overall_pass": True} for i in range(3)]
        alt_chain = _make_chain(_sb_response(data=alts))
        sb = _build_sb_mock({"alternatives": alt_chain})
        mock_sb.return_value = sb

        mock_ai.return_value = AiReviewResult(
            evaluator="must",
            summary="All MUST criteria passed",
            confidence=0.9,
            details={"overall_pass": True},
        )

        resp = client.get("/api/v1/gates/X2/check", params={
            "project_id": "p1",
            "include_ai_review": "true",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ai_review"] is not None
        assert body["ai_review"]["evaluator"] == "must"
        mock_ai.assert_called_once_with("must", sb, "p1")

    @patch("app.routers.gates.run_ai_review", side_effect=Exception("LLM failed"))
    @patch("app.routers.gates.get_supabase")
    def test_ai_review_failure_returns_error_result(self, mock_sb, mock_ai, client):
        """AI review failure should not crash — returns error AiReviewResult."""
        alts = [{"id": f"alt{i}", "must_scores": {}, "overall_pass": True} for i in range(3)]
        alt_chain = _make_chain(_sb_response(data=alts))
        sb = _build_sb_mock({"alternatives": alt_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/X2/check", params={
            "project_id": "p1",
            "include_ai_review": "true",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ai_review"]["evaluator"] == "must"
        assert "失敗" in body["ai_review"]["summary"]
