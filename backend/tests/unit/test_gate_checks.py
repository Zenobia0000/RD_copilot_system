"""Unit tests for gate checker factory functions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.core.gate_checks import (
    check_field_exists,
    check_table_count,
    check_all_have_field,
    check_severity_count,
    check_cross_table,
    check_any_status,
    check_manual,
)


def _sb_response(data=None, count=None):
    return SimpleNamespace(data=data, count=count)


def _make_chain(final_response):
    m = MagicMock()
    m.execute.return_value = final_response
    m.maybe_single.return_value = m
    m.eq.return_value = m
    m.select.return_value = m
    return m


def _sb_mock(table_map: dict[str, MagicMock]) -> MagicMock:
    sb = MagicMock()
    sb.table.side_effect = lambda name: table_map[name]
    return sb


# ---------------------------------------------------------------------------
# check_field_exists
# ---------------------------------------------------------------------------

class TestCheckFieldExists:
    def test_field_present_passes(self):
        fn = check_field_exists("briefs", "mission", "Mission 已定義", "Mission 尚未定義")
        chain = _make_chain(_sb_response(data={"mission": "Design a motor"}))
        sb = _sb_mock({"briefs": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True
        assert reason is None

    def test_field_missing_fails(self):
        fn = check_field_exists("briefs", "mission", "Mission 已定義", "Mission 尚未定義")
        chain = _make_chain(_sb_response(data=None))
        sb = _sb_mock({"briefs": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False
        assert reason == "Mission 尚未定義"

    def test_field_empty_string_fails(self):
        fn = check_field_exists("briefs", "mission", "Mission 已定義", "Mission 尚未定義")
        chain = _make_chain(_sb_response(data={"mission": ""}))
        sb = _sb_mock({"briefs": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False


# ---------------------------------------------------------------------------
# check_table_count
# ---------------------------------------------------------------------------

class TestCheckTableCount:
    def test_count_met(self):
        fn = check_table_count("kpis", min_count=3)
        chain = _make_chain(_sb_response(data=[{"id": "k1"}, {"id": "k2"}, {"id": "k3"}]))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True
        assert reason is None

    def test_count_not_met(self):
        fn = check_table_count("kpis", min_count=3)
        chain = _make_chain(_sb_response(data=[{"id": "k1"}]))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False
        assert reason is not None

    def test_count_exact_mode(self):
        fn = check_table_count("contradictions", min_count=3, use_count_exact=True)
        chain = _make_chain(_sb_response(data=[], count=5))
        sb = _sb_mock({"contradictions": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True

    def test_empty_data_none(self):
        fn = check_table_count("kpis", min_count=1)
        chain = _make_chain(_sb_response(data=None))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False


# ---------------------------------------------------------------------------
# check_all_have_field
# ---------------------------------------------------------------------------

class TestCheckAllHaveField:
    def test_all_have_field_passes(self):
        fn = check_all_have_field("kpis", "measurement_method", min_total=3)
        data = [{"id": f"k{i}", "measurement_method": f"m{i}"} for i in range(3)]
        chain = _make_chain(_sb_response(data=data))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True

    def test_one_missing_fails(self):
        fn = check_all_have_field("kpis", "measurement_method", min_total=3)
        data = [
            {"id": "k1", "measurement_method": "m1"},
            {"id": "k2", "measurement_method": ""},
            {"id": "k3", "measurement_method": "m3"},
        ]
        chain = _make_chain(_sb_response(data=data))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False

    def test_below_min_total_fails(self):
        fn = check_all_have_field("kpis", "measurement_method", min_total=3)
        data = [{"id": "k1", "measurement_method": "m1"}, {"id": "k2", "measurement_method": "m2"}]
        chain = _make_chain(_sb_response(data=data))
        sb = _sb_mock({"kpis": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False


# ---------------------------------------------------------------------------
# check_severity_count
# ---------------------------------------------------------------------------

class TestCheckSeverityCount:
    def test_severity_met(self):
        fn = check_severity_count(
            "assumptions", "worst_severity", ["critical", "high"], min_count=3,
        )
        data = [
            {"id": "a1", "worst_severity": "critical"},
            {"id": "a2", "worst_severity": "high"},
            {"id": "a3", "worst_severity": "critical"},
            {"id": "a4", "worst_severity": "low"},
        ]
        chain = _make_chain(_sb_response(data=data))
        sb = _sb_mock({"assumptions": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True

    def test_severity_not_met(self):
        fn = check_severity_count(
            "assumptions", "worst_severity", ["critical", "high"], min_count=3,
        )
        data = [{"id": "a1", "worst_severity": "low"}, {"id": "a2", "worst_severity": "medium"}]
        chain = _make_chain(_sb_response(data=data))
        sb = _sb_mock({"assumptions": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False


# ---------------------------------------------------------------------------
# check_cross_table
# ---------------------------------------------------------------------------

class TestCheckCrossTable:
    def test_cross_table_met(self):
        fn = check_cross_table(
            "assumptions", "code",
            "experiments", "assumption_code",
            primary_severity_field="worst_severity",
            primary_severity_values=["critical", "high"],
            min_count=2,
        )
        assumptions_chain = _make_chain(_sb_response(data=[
            {"code": "A-01", "worst_severity": "critical"},
            {"code": "A-02", "worst_severity": "high"},
            {"code": "A-03", "worst_severity": "low"},
        ]))
        experiments_chain = _make_chain(_sb_response(data=[
            {"assumption_code": "A-01"},
            {"assumption_code": "A-02"},
        ]))
        sb = _sb_mock({"assumptions": assumptions_chain, "experiments": experiments_chain})
        item, reason = fn(sb, "p1")
        assert item.met is True

    def test_cross_table_not_met(self):
        fn = check_cross_table(
            "assumptions", "code",
            "experiments", "assumption_code",
            primary_severity_field="worst_severity",
            primary_severity_values=["critical", "high"],
            min_count=3,
        )
        assumptions_chain = _make_chain(_sb_response(data=[
            {"code": "A-01", "worst_severity": "critical"},
            {"code": "A-02", "worst_severity": "low"},
        ]))
        experiments_chain = _make_chain(_sb_response(data=[
            {"assumption_code": "A-01"},
        ]))
        sb = _sb_mock({"assumptions": assumptions_chain, "experiments": experiments_chain})
        item, reason = fn(sb, "p1")
        assert item.met is False


# ---------------------------------------------------------------------------
# check_any_status
# ---------------------------------------------------------------------------

class TestCheckAnyStatus:
    def test_status_matched(self):
        fn = check_any_status(
            "decisions", "status", ["confirmed", "signed"],
            label="決策已簽核", fail_reason="決策未簽核",
        )
        chain = _make_chain(_sb_response(data=[
            {"status": "draft"}, {"status": "confirmed"},
        ]))
        sb = _sb_mock({"decisions": chain})
        item, reason = fn(sb, "p1")
        assert item.met is True

    def test_no_status_matched(self):
        fn = check_any_status(
            "decisions", "status", ["confirmed", "signed"],
            label="決策已簽核", fail_reason="決策未簽核",
        )
        chain = _make_chain(_sb_response(data=[{"status": "draft"}]))
        sb = _sb_mock({"decisions": chain})
        item, reason = fn(sb, "p1")
        assert item.met is False
        assert reason == "決策未簽核"


# ---------------------------------------------------------------------------
# check_manual
# ---------------------------------------------------------------------------

class TestCheckManual:
    def test_always_fails(self):
        fn = check_manual("人工確認", "需人工", "需人工確認")
        sb = MagicMock()
        item, reason = fn(sb, "p1")
        assert item.met is False
        assert reason == "需人工確認"
