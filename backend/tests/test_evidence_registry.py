"""Tests for Evidence Registry service + router endpoints (WBS 8.4.5)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from app.core.gate_checks import check_evidence_coverage


# ---------------------------------------------------------------------------
# Supabase mock helpers (aligned with test_gate_checks.py pattern)
# ---------------------------------------------------------------------------

def _sb_response(data=None, count=None):
    return SimpleNamespace(data=data, count=count)


def _make_chain(final_response):
    """Create a fluent Supabase query chain mock."""
    m = MagicMock()
    m.execute.return_value = final_response
    m.maybe_single.return_value = m
    m.single.return_value = m
    m.eq.return_value = m
    m.select.return_value = m
    m.insert.return_value = m
    m.update.return_value = m
    return m


def _sb_mock(table_map: dict[str, MagicMock]) -> MagicMock:
    sb = MagicMock()
    sb.table.side_effect = lambda name: table_map[name]
    return sb


# ---------------------------------------------------------------------------
# Service: register_claim
# ---------------------------------------------------------------------------

class TestRegisterClaim:
    @pytest.mark.asyncio
    async def test_register_claim_basic(self):
        from app.services.evidence_registry import register_claim

        fake_row = {
            "id": "test-uuid",
            "project_id": "proj-1",
            "claim_text": "Motor efficiency > 95%",
            "claim_type": "hypothesis",
            "status": "unverified",
            "verification_sources": [],
            "confidence_score": 0.0,
        }
        chain = _make_chain(_sb_response(data=[fake_row]))
        sb = _sb_mock({"evidence_claims": chain})

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await register_claim(
                project_id="proj-1",
                claim_text="Motor efficiency > 95%",
                claim_type="hypothesis",
            )

        assert result["claim_type"] == "hypothesis"
        assert result["status"] == "unverified"
        chain.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_claim_with_artifact_link(self):
        from app.services.evidence_registry import register_claim

        fake_row = {
            "id": "test-uuid",
            "project_id": "proj-1",
            "claim_text": "Heat dissipation meets spec",
            "claim_type": "assumption",
            "status": "unverified",
            "verification_sources": [],
            "confidence_score": 0.0,
            "linked_artifact_id": "alt-001",
            "linked_artifact_type": "alternative",
        }
        chain = _make_chain(_sb_response(data=[fake_row]))
        sb = _sb_mock({"evidence_claims": chain})

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await register_claim(
                project_id="proj-1",
                claim_text="Heat dissipation meets spec",
                claim_type="assumption",
                linked_artifact_id="alt-001",
                linked_artifact_type="alternative",
            )

        assert result["linked_artifact_id"] == "alt-001"
        assert result["linked_artifact_type"] == "alternative"


# ---------------------------------------------------------------------------
# Service: verify_claim
# ---------------------------------------------------------------------------

class TestVerifyClaim:
    @pytest.mark.asyncio
    async def test_verify_claim_appends_source(self):
        from app.services.evidence_registry import verify_claim

        # Two chains: one for the SELECT (fetch existing), one for the UPDATE
        select_chain = _make_chain(_sb_response(data={"verification_sources": [{"type": "old"}]}))
        update_chain = _make_chain(_sb_response(data=[{
            "id": "claim-1",
            "status": "verified",
            "verification_sources": [{"type": "old"}, {"type": "test_report", "ref": "TR-001"}],
            "confidence_score": 0.85,
        }]))

        # Build a mock that returns different chains for select vs update
        table_mock = MagicMock()
        call_count = {"n": 0}
        original_select = table_mock.select

        def route_select(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return select_chain
            return update_chain

        table_mock.select.side_effect = route_select
        table_mock.update.return_value = update_chain

        sb = MagicMock()
        sb.table.return_value = table_mock

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await verify_claim(
                claim_id="claim-1",
                verification_source={"type": "test_report", "ref": "TR-001"},
                new_status="verified",
                confidence_score=0.85,
            )

        assert result["status"] == "verified"
        assert len(result["verification_sources"]) == 2

    @pytest.mark.asyncio
    async def test_verify_claim_without_confidence(self):
        from app.services.evidence_registry import verify_claim

        select_chain = _make_chain(_sb_response(data={"verification_sources": []}))
        update_chain = _make_chain(_sb_response(data=[{
            "id": "claim-2",
            "status": "refuted",
            "verification_sources": [{"type": "analysis", "note": "contradicted"}],
        }]))

        table_mock = MagicMock()
        call_count = {"n": 0}

        def route_select(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return select_chain
            return update_chain

        table_mock.select.side_effect = route_select
        table_mock.update.return_value = update_chain

        sb = MagicMock()
        sb.table.return_value = table_mock

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await verify_claim(
                claim_id="claim-2",
                verification_source={"type": "analysis", "note": "contradicted"},
                new_status="refuted",
            )

        assert result["status"] == "refuted"


# ---------------------------------------------------------------------------
# Service: get_coverage
# ---------------------------------------------------------------------------

class TestGetCoverage:
    @pytest.mark.asyncio
    async def test_coverage_with_mixed_statuses(self):
        from app.services.evidence_registry import get_coverage

        rows = [
            {"claim_type": "assumption", "status": "verified"},
            {"claim_type": "assumption", "status": "unverified"},
            {"claim_type": "hypothesis", "status": "verified"},
            {"claim_type": "hypothesis", "status": "refuted"},
            {"claim_type": "result", "status": "partial"},
        ]
        chain = _make_chain(_sb_response(data=rows))
        sb = _sb_mock({"evidence_claims": chain})

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await get_coverage("proj-1")

        assert result["total_claims"] == 5
        assert result["verified_count"] == 2
        assert result["refuted_count"] == 1
        assert result["partial_count"] == 1
        assert result["unverified_count"] == 1
        assert result["coverage_ratio"] == pytest.approx(0.4)
        assert result["by_type"]["assumption"]["total"] == 2
        assert result["by_type"]["assumption"]["verified"] == 1
        assert result["by_type"]["hypothesis"]["refuted"] == 1

    @pytest.mark.asyncio
    async def test_coverage_empty_project(self):
        from app.services.evidence_registry import get_coverage

        chain = _make_chain(_sb_response(data=[]))
        sb = _sb_mock({"evidence_claims": chain})

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await get_coverage("proj-empty")

        assert result["total_claims"] == 0
        assert result["coverage_ratio"] == 0.0
        assert result["by_type"] == {}

    @pytest.mark.asyncio
    async def test_coverage_all_verified(self):
        from app.services.evidence_registry import get_coverage

        rows = [
            {"claim_type": "constraint", "status": "verified"},
            {"claim_type": "constraint", "status": "verified"},
        ]
        chain = _make_chain(_sb_response(data=rows))
        sb = _sb_mock({"evidence_claims": chain})

        with patch("app.services.evidence_registry.get_supabase", return_value=sb):
            result = await get_coverage("proj-full")

        assert result["coverage_ratio"] == 1.0


# ---------------------------------------------------------------------------
# Gate check: check_evidence_coverage (WBS 8.4.4)
# ---------------------------------------------------------------------------

class TestCheckEvidenceCoverage:
    def test_above_threshold_passes(self):
        fn = check_evidence_coverage(min_ratio=0.4)
        rows = [
            {"status": "verified"},
            {"status": "verified"},
            {"status": "verified"},
            {"status": "unverified"},
            {"status": "unverified"},
        ]
        chain = _make_chain(_sb_response(data=rows))
        sb = _sb_mock({"evidence_claims": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True
        assert reason is None

    def test_below_threshold_fails(self):
        fn = check_evidence_coverage(min_ratio=0.4)
        rows = [
            {"status": "verified"},
            {"status": "unverified"},
            {"status": "unverified"},
            {"status": "unverified"},
            {"status": "unverified"},
        ]
        chain = _make_chain(_sb_response(data=rows))
        sb = _sb_mock({"evidence_claims": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False
        assert reason is not None
        assert "20" in str(reason)  # 20% actual

    def test_no_claims_fails(self):
        fn = check_evidence_coverage(min_ratio=0.4)
        chain = _make_chain(_sb_response(data=[]))
        sb = _sb_mock({"evidence_claims": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False

    def test_exactly_at_threshold_passes(self):
        fn = check_evidence_coverage(min_ratio=0.4)
        rows = [
            {"status": "verified"},
            {"status": "verified"},
            {"status": "unverified"},
            {"status": "unverified"},
            {"status": "unverified"},
        ]
        chain = _make_chain(_sb_response(data=rows))
        sb = _sb_mock({"evidence_claims": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True


# ---------------------------------------------------------------------------
# Router endpoints (integration via TestClient)
# ---------------------------------------------------------------------------

class TestEvidenceRouter:
    def test_register_claim_endpoint(self, client):
        with patch("app.services.evidence_registry.get_supabase") as mock_sb:
            fake_row = {
                "id": "new-uuid",
                "project_id": "proj-1",
                "claim_text": "Gear ratio is optimal",
                "claim_type": "hypothesis",
                "status": "unverified",
                "verification_sources": [],
                "confidence_score": 0.0,
            }
            chain = _make_chain(_sb_response(data=[fake_row]))
            mock_sb.return_value = _sb_mock({"evidence_claims": chain})

            resp = client.post("/api/v1/evidence/claims", json={
                "project_id": "proj-1",
                "claim_text": "Gear ratio is optimal",
                "claim_type": "hypothesis",
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body["claim_type"] == "hypothesis"
        assert body["status"] == "unverified"

    def test_coverage_endpoint(self, client):
        with patch("app.services.evidence_registry.get_supabase") as mock_sb:
            rows = [
                {"claim_type": "assumption", "status": "verified"},
                {"claim_type": "assumption", "status": "unverified"},
            ]
            chain = _make_chain(_sb_response(data=rows))
            mock_sb.return_value = _sb_mock({"evidence_claims": chain})

            resp = client.get("/api/v1/evidence/coverage/proj-1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_claims"] == 2
        assert body["verified_count"] == 1
        assert body["coverage_ratio"] == 0.5

    def test_verify_claim_endpoint(self, client):
        with patch("app.services.evidence_registry.get_supabase") as mock_sb:
            select_chain = _make_chain(_sb_response(data={"verification_sources": []}))
            update_chain = _make_chain(_sb_response(data=[{
                "id": "c-1",
                "status": "verified",
                "verification_sources": [{"type": "test"}],
                "confidence_score": 0.9,
                "updated_at": "2026-04-24T00:00:00Z",
            }]))

            table_mock = MagicMock()
            call_count = {"n": 0}

            def route_select(*args, **kwargs):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return select_chain
                return update_chain

            table_mock.select.side_effect = route_select
            table_mock.update.return_value = update_chain

            sb = MagicMock()
            sb.table.return_value = table_mock
            mock_sb.return_value = sb

            resp = client.post("/api/v1/evidence/claims/c-1/verify", json={
                "verification_source": {"type": "test"},
                "new_status": "verified",
                "confidence_score": 0.9,
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "verified"
