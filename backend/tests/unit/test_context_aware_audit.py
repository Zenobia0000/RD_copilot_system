"""Tests for the context-aware coverage audit refactor (方案 A).

Covers:
  (a) :class:`SubRequirement` parses with/without the new `kind` field
      and clamps invalid values to the safe default.
  (b) :class:`DirectionCoverageAudit` parses both new and legacy shapes
      and auto-promotes ``directly_resolves`` with key_assumptions →
      ``conditionally_resolves``.
  (c) :func:`_apply_coverage_to_scores` actually demotes
      ``does_not_resolve`` / ``unclear`` below ``directly_resolves``
      even when the does_not_resolve direction has a higher raw
      coverage_score.
  (d) :func:`_decompose_contradiction` and :func:`_audit_coverage`
      remain tolerant when the LLM returns no `resolution_status` /
      `kind` (legacy LLM behaviour during rollout).

No live LLM is touched — ``call_llm_json`` is monkey-patched.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.agents import triz_solver
from app.agents.triz_solver import (
    RESOLUTION_STATUS_MULTIPLIER,
    _apply_coverage_to_scores,
    _audit_coverage,
    _decompose_contradiction,
    _derive_verdict,
    _format_cld_block,
    _format_constraints_block,
    _format_kpis_block,
    _format_mission_block,
    _format_socratic_block,
    _parse_coverage_matrix,
    _VERDICT_ZH_DEFAULT,
)
from app.models.schemas import (
    BriefConstraint,
    BriefContextSnapshot,
    BriefKpi,
    CldEdgeSummary,
    CldNodeSummary,
    CldSummary,
    DirectionCoverageAudit,
    DirectionGroup,
    DirectionScore,
    SocraticInsight,
    SubRequirement,
)


# ---------------------------------------------------------------------------
# (a) SubRequirement schema
# ---------------------------------------------------------------------------

def test_sub_requirement_accepts_legacy_payload_without_kind():
    """Legacy persisted rows have no `kind` — default keeps them parseable."""
    sr = SubRequirement(
        id="SR-1",
        description="legacy domain SR",
        why_necessary="needed",
    )
    # Default kind is desired_improvement so the FE still renders a badge.
    assert sr.kind == "desired_improvement"
    assert sr.source_ref == ""


def test_sub_requirement_accepts_new_payload_with_kind_and_source_ref():
    sr = SubRequirement(
        id="SR-3",
        kind="boundary_condition",
        source_ref="constraint:C2",
        description="mass cap",
        why_necessary="hard limit",
    )
    assert sr.kind == "boundary_condition"
    assert sr.source_ref == "constraint:C2"


def test_sub_requirement_rejects_invalid_kind():
    """Pydantic Literal enforcement prevents off-vocabulary kinds."""
    with pytest.raises(ValidationError):
        SubRequirement(id="SR-X", kind="totally_made_up", description="x")


# ---------------------------------------------------------------------------
# (b) DirectionCoverageAudit schema
# ---------------------------------------------------------------------------

def test_audit_defaults_to_unclear_when_legacy_payload():
    """Legacy rows without resolution_status default to 'unclear' so the
    FE can still render a deterministic badge."""
    a = DirectionCoverageAudit(direction_id="DIR-1", coverage_score=4.2)
    assert a.resolution_status == "unclear"
    assert a.addresses_layer == "unclear"
    assert a.key_assumptions == []
    assert a.mission_violations == []


def test_audit_auto_promotes_directly_with_assumptions_to_conditional():
    """If the LLM tags directly_resolves but also enumerates
    key_assumptions, those are prerequisites — the model_validator
    downgrades to conditionally_resolves so the verdict matches reality."""
    a = DirectionCoverageAudit(
        direction_id="DIR-1",
        coverage_score=8.5,
        resolution_status="directly_resolves",
        key_assumptions=["supplier honours pricing at ≥1k/yr"],
    )
    assert a.resolution_status == "conditionally_resolves"


def test_audit_keeps_directly_when_no_assumptions():
    a = DirectionCoverageAudit(
        direction_id="DIR-2",
        coverage_score=9.5,
        resolution_status="directly_resolves",
        key_assumptions=[],
    )
    assert a.resolution_status == "directly_resolves"


def test_audit_rejects_invalid_resolution_status():
    with pytest.raises(ValidationError):
        DirectionCoverageAudit(direction_id="DIR-X", resolution_status="maybe")


# ---------------------------------------------------------------------------
# (c) _apply_coverage_to_scores demotion
# ---------------------------------------------------------------------------

def _make_score(direction_id: str, **kw) -> DirectionScore:
    return DirectionScore(
        direction_id=direction_id,
        tool_support=kw.get("tool_support", 2),
        feasibility=kw.get("feasibility", 7.0),
        cost_difficulty=kw.get("cost_difficulty", 6.0),
        weighted_total=kw.get("weighted_total", 0.0),
        score_rationale=kw.get("score_rationale", ""),
    )


def _make_group(direction_id: str) -> DirectionGroup:
    return DirectionGroup(
        direction_id=direction_id,
        direction_name=direction_id,
        direction_summary="",
        solutions=[],
        tc_count=1,
        pc_count=1,
        sf_count=1,
    )


def test_does_not_resolve_demoted_below_directly_resolves_even_with_higher_coverage():
    """The core architect-plan requirement: does_not_resolve with
    coverage=8.5 must rank below directly_resolves with coverage=5.0.
    """
    scores = [_make_score("DIR-HIGH"), _make_score("DIR-LOW")]
    audits = [
        DirectionCoverageAudit(
            direction_id="DIR-HIGH",
            coverage_score=8.5,
            resolution_status="does_not_resolve",
        ),
        DirectionCoverageAudit(
            direction_id="DIR-LOW",
            coverage_score=5.0,
            resolution_status="directly_resolves",
        ),
    ]
    dirs = [_make_group("DIR-HIGH"), _make_group("DIR-LOW")]

    new = _apply_coverage_to_scores(scores, audits, dirs)
    high = next(s for s in new if s.direction_id == "DIR-HIGH")
    low = next(s for s in new if s.direction_id == "DIR-LOW")

    assert (
        high.weighted_total < low.weighted_total
    ), f"does_not_resolve should rank below directly_resolves; got HIGH={high.weighted_total} LOW={low.weighted_total}"
    # The rationale must explain WHY the demotion happened so RD can
    # trace it back in the UI.
    assert "does_not_resolve" in high.score_rationale
    assert "directly_resolves" in low.score_rationale


def test_unclear_demotion_factor_is_strong_but_not_zero():
    """unclear keeps the direction visible but pushes it down."""
    assert RESOLUTION_STATUS_MULTIPLIER["unclear"] == 0.50
    assert RESOLUTION_STATUS_MULTIPLIER["does_not_resolve"] == 0.40
    assert RESOLUTION_STATUS_MULTIPLIER["directly_resolves"] == 1.0


def test_conditionally_resolves_mild_demotion():
    """conditional should be near-1.0 because key_assumptions are
    listed for RD review — not a reason to bury the direction."""
    scores = [_make_score("DIR-COND"), _make_score("DIR-DIRECT")]
    audits = [
        DirectionCoverageAudit(
            direction_id="DIR-COND",
            coverage_score=9.0,
            resolution_status="conditionally_resolves",
            key_assumptions=["needs FEA validation"],
        ),
        DirectionCoverageAudit(
            direction_id="DIR-DIRECT",
            coverage_score=9.0,
            resolution_status="directly_resolves",
        ),
    ]
    dirs = [_make_group("DIR-COND"), _make_group("DIR-DIRECT")]
    new = _apply_coverage_to_scores(scores, audits, dirs)
    cond = next(s for s in new if s.direction_id == "DIR-COND")
    direct = next(s for s in new if s.direction_id == "DIR-DIRECT")
    # Both should be high, with a small gap — conditional is < direct
    # but the gap is small (≤ 5% of direct's score).
    assert cond.weighted_total < direct.weighted_total
    assert cond.weighted_total / direct.weighted_total >= 0.90


def test_missing_audit_treated_as_unclear():
    """A direction with no matching audit row is treated as unclear so
    its weighted_total is demoted, not silently passed through."""
    scores = [_make_score("DIR-A", weighted_total=0)]
    dirs = [_make_group("DIR-A")]
    new = _apply_coverage_to_scores(scores, [], dirs)
    # weighted_total recomputed from components × unclear multiplier
    expected_raw = (
        2 * triz_solver.WEIGHT_CONSENSUS
        + 7.0 * triz_solver.WEIGHT_FEASIBILITY
        + 6.0 * triz_solver.WEIGHT_COST
    )
    expected_demoted = expected_raw * RESOLUTION_STATUS_MULTIPLIER["unclear"]
    assert new[0].weighted_total == pytest.approx(round(expected_demoted, 2))


# ---------------------------------------------------------------------------
# (d) LLM-touching helpers — call_llm_json monkey-patched
# ---------------------------------------------------------------------------

# Phase 1 (S0) — 演算法為骨重構：以下兩個測試針對舊「LLM 自由產 SR」流程，
# 在新流程下 contradiction 兩面永遠由程式列舉（不是 LLM 從 sub_requirements
# 欄位產出），所以這兩個 fallback / clamping 行為不再相關。
#
# 新的穩定性測試見 backend/tests/integration/test_sr_stability.py
# - TestEnumerateSrCandidates / TestFilterByRelevance / TestScoreSrRelevance
# - TestSrStability10Runs：連跑 10 次 SR 結構穩定性

import pytest


@pytest.mark.skip(reason="Phase 1 S0 deprecated this fallback path; "
                         "see test_sr_stability.py for new behaviour")
def test_decompose_contradiction_tolerant_when_kind_missing(monkeypatch):
    """[DEPRECATED] 舊 LLM 自由產 SR 流程的容錯行為。

    在 Phase 1 S0 重構後，SR 由程式列舉候選 + LLM 評分 + 改寫產生，
    舊的「LLM 給空 kind」場景不存在了。
    """
    pass


@pytest.mark.skip(reason="Phase 1 S0 deprecated this fallback path; "
                         "see test_sr_stability.py for new behaviour")
def test_decompose_contradiction_clamps_invalid_kind(monkeypatch):
    """[DEPRECATED] 舊 LLM 自由產 SR 流程的 invalid kind clamping。

    新流程的 kind 由 _enumerate_sr_candidates 程式決定，LLM 無法產出
    invalid kind，所以這個 clamping 路徑不再需要。
    """
    pass


def test_audit_coverage_parses_full_v2_payload(monkeypatch):
    """Round-trip: rich v2 LLM output → fully-populated DirectionCoverageAudit."""

    def fake_llm(_system, _prompt, **_kw):
        return json.dumps({
            "audits": [
                {
                    "direction_id": "DIR-1",
                    "coverage_matrix": [
                        {"sub_requirement_id": "SR-1", "score": 2, "rationale": "good"},
                    ],
                    "coverage_score": 7.5,
                    "resolution_status": "conditionally_resolves",
                    "key_assumptions": ["needs supplier quote"],
                    "mission_violations": [],
                    "cld_side_effects": [],
                    "addresses_layer": "root_cause",
                    "unresolved_gaps": [],
                    "gap_summary": "solid root-cause fix if quote holds",
                }
            ]
        })

    monkeypatch.setattr(triz_solver, "call_llm_json", fake_llm)
    subs = [SubRequirement(id="SR-1", description="x", kind="desired_improvement")]
    dirs = [_make_group("DIR-1")]
    audits = _audit_coverage("c", subs, dirs, BriefContextSnapshot())
    assert len(audits) == 1
    a = audits[0]
    assert a.resolution_status == "conditionally_resolves"
    assert a.key_assumptions == ["needs supplier quote"]
    assert a.addresses_layer == "root_cause"
    assert a.gap_summary.startswith("solid root-cause")


def test_audit_coverage_clamps_invalid_status(monkeypatch):
    """Off-vocab resolution_status → 'unclear', no crash."""

    def fake_llm(_system, _prompt, **_kw):
        return json.dumps({
            "audits": [
                {
                    "direction_id": "DIR-1",
                    "coverage_matrix": [],
                    "coverage_score": 0.0,
                    "resolution_status": "nope",
                    "addresses_layer": "mystery",
                }
            ]
        })

    monkeypatch.setattr(triz_solver, "call_llm_json", fake_llm)
    subs = [SubRequirement(id="SR-1", description="x")]
    dirs = [_make_group("DIR-1")]
    audits = _audit_coverage("c", subs, dirs, BriefContextSnapshot())
    assert audits[0].resolution_status == "unclear"
    assert audits[0].addresses_layer == "unclear"


# ---------------------------------------------------------------------------
# Context block formatters — verify "(未提供)" fallback and basic rendering
# ---------------------------------------------------------------------------

def test_context_formatters_emit_not_provided_for_empty_snapshot():
    snap = BriefContextSnapshot()
    assert _format_mission_block(snap) == "(未提供)"
    assert _format_constraints_block(snap) == "(未提供)"
    assert _format_kpis_block(snap) == "(未提供)"
    assert _format_socratic_block(snap) == "(未提供)"
    assert _format_cld_block(snap) == "(未提供)"


def test_context_formatters_render_populated_snapshot():
    snap = BriefContextSnapshot(
        mission="Mission text",
        constraints=[
            BriefConstraint(code="C1", description="mass <= 5kg", type="hard", feasibility="likely"),
        ],
        kpis=[
            BriefKpi(name="K1", target_value="100", unit="Nm", current_value="80", current_status="at_risk"),
        ],
        socratic_summary=[
            SocraticInsight(category="clarification", question="duty?", answer="continuous", is_assumption=True),
        ],
        cld_summary=CldSummary(
            nodes=[CldNodeSummary(label="heat", is_leverage=True)],
            edges=[CldEdgeSummary(from_label="heat", to_label="loss", polarity="+")],
            leverage_points=["heat"],
        ),
    )
    assert "Mission text" in _format_mission_block(snap)
    assert "C1" in _format_constraints_block(snap)
    assert "feasibility=likely" in _format_constraints_block(snap)
    assert "K1" in _format_kpis_block(snap)
    assert "100 Nm" in _format_kpis_block(snap)
    assert "ASSUMPTION" in _format_socratic_block(snap)
    cld = _format_cld_block(snap)
    assert "LEVERAGE" in cld
    assert "heat --[+]--> loss" in cld


# ---------------------------------------------------------------------------
# Per-SR verdict derivation (v3 SR-grouped UI fallback)
# ---------------------------------------------------------------------------

class TestDeriveVerdict:
    """When the LLM omits verdict / verdict_zh, the rule-based deriver
    must turn (score, mission_violations, unresolved_gaps) into the
    correct 6-state verdict so the SR-grouped UI always has data."""

    def test_violates_when_mission_violations_mentions_sr(self):
        v = _derive_verdict(
            "SR-3",
            score=2,                  # high score does NOT save it
            mission_violations=["violates constraint C2 — SR-3 mass cap exceeded"],
            unresolved_gaps=[],
        )
        assert v == "violates"

    def test_directly_solves_when_score_2_and_no_gap(self):
        assert _derive_verdict("SR-1", 2, [], []) == "directly_solves"

    def test_needs_verify_when_score_2_but_gap_mentions_sr(self):
        v = _derive_verdict(
            "SR-3",
            score=2,
            mission_violations=[],
            unresolved_gaps=["SR-3 mass cap not yet verified by FEA"],
        )
        assert v == "needs_verify"

    def test_partially_solves_when_score_1(self):
        assert _derive_verdict("SR-2", 1, [], []) == "partially_solves"

    def test_not_addressed_when_score_0(self):
        assert _derive_verdict("SR-5", 0, [], []) == "not_addressed"

    def test_unclear_when_score_0_and_no_sr_id(self):
        """Anonymous entries (no SR id) fall back to unclear rather
        than mis-labelling as 'not_addressed' (we don't know what
        was supposed to be addressed)."""
        assert _derive_verdict("", 0, [], []) == "unclear"

    def test_sr_id_match_is_case_insensitive(self):
        """LLM may write 'sr-3 mass cap' while we look up 'SR-3'."""
        assert _derive_verdict(
            "SR-3", 2, ["violates sr-3 mass cap"], [],
        ) == "violates"


class TestParseCoverageMatrix:
    """End-to-end parsing of one audit's coverage_matrix list, with the
    v3 verdict/verdict_zh fields and fallback for legacy payloads."""

    _VERDICTS = {
        "directly_solves", "partially_solves", "needs_verify",
        "violates", "not_addressed", "unclear",
    }

    def test_passes_through_llm_supplied_verdict(self):
        raw = [
            {
                "sub_requirement_id": "SR-1",
                "score": 2,
                "verdict": "directly_solves",
                "verdict_zh": "直接抽熱，正面解決",
                "rationale": "drops temp 25°C",
            }
        ]
        out = _parse_coverage_matrix(
            raw_entries=raw,
            mission_violations=[],
            unresolved_gaps=[],
            valid_verdict=self._VERDICTS,
        )
        assert len(out) == 1
        assert out[0].verdict == "directly_solves"
        assert out[0].verdict_zh == "直接抽熱，正面解決"

    def test_clamps_invalid_verdict_and_uses_default_zh(self):
        raw = [
            {"sub_requirement_id": "SR-1", "score": 2, "verdict": "made_up"},
        ]
        out = _parse_coverage_matrix(
            raw_entries=raw,
            mission_violations=[],
            unresolved_gaps=[],
            valid_verdict=self._VERDICTS,
        )
        # Invalid verdict was clamped via derivation (score=2 + no gap → directly_solves)
        assert out[0].verdict == "directly_solves"
        # verdict_zh fell back to the canonical default
        assert out[0].verdict_zh == _VERDICT_ZH_DEFAULT["directly_solves"]

    def test_legacy_payload_without_verdict_derived_from_score_and_lists(self):
        """No verdict / verdict_zh in raw payload — pure fallback path."""
        raw = [
            {"sub_requirement_id": "SR-1", "score": 2, "rationale": "good"},
            {"sub_requirement_id": "SR-3", "score": 1, "rationale": "partial"},
            {"sub_requirement_id": "SR-5", "score": 0, "rationale": "miss"},
        ]
        out = _parse_coverage_matrix(
            raw_entries=raw,
            mission_violations=["fails KPI for SR-5 cost ceiling"],
            unresolved_gaps=["SR-1 mass envelope still unverified"],
            valid_verdict=self._VERDICTS,
        )
        by_sr = {e.sub_requirement_id: e for e in out}
        # SR-1 score=2 but gap mentions it → needs_verify
        assert by_sr["SR-1"].verdict == "needs_verify"
        # SR-3 score=1 → partially_solves
        assert by_sr["SR-3"].verdict == "partially_solves"
        # SR-5 mission_violation mentions it → violates (overrides score=0)
        assert by_sr["SR-5"].verdict == "violates"
        # All verdict_zh strings filled
        for e in out:
            assert e.verdict_zh, f"{e.sub_requirement_id} missing verdict_zh"

    def test_skips_malformed_entries_silently(self):
        raw = [
            "not_a_dict",       # dropped
            {"sub_requirement_id": "SR-1", "score": 2},  # kept
            123,                # dropped
        ]
        out = _parse_coverage_matrix(
            raw_entries=raw,
            mission_violations=[],
            unresolved_gaps=[],
            valid_verdict=self._VERDICTS,
        )
        assert len(out) == 1
        assert out[0].sub_requirement_id == "SR-1"

    def test_audit_coverage_e2e_with_v3_fields(self, monkeypatch):
        """Round-trip: rich v3 LLM output → DirectionCoverageAudit with
        verdict + verdict_zh preserved on every entry."""

        def fake_llm(_system, _prompt, **_kw):
            return json.dumps({
                "audits": [
                    {
                        "direction_id": "DIR-1",
                        "coverage_matrix": [
                            {
                                "sub_requirement_id": "SR-1", "score": 2,
                                "verdict": "directly_solves",
                                "verdict_zh": "直接解",
                                "rationale": "x",
                            },
                            {
                                "sub_requirement_id": "SR-2", "score": 0,
                                "verdict": "not_addressed",
                                "verdict_zh": "未觸及",
                                "rationale": "y",
                            },
                        ],
                        "coverage_score": 5.0,
                        "resolution_status": "partially_resolves",
                        "addresses_layer": "mechanism",
                    }
                ]
            })

        monkeypatch.setattr(triz_solver, "call_llm_json", fake_llm)
        subs = [SubRequirement(id=f"SR-{i}", description=f"x{i}") for i in (1, 2)]
        dirs = [_make_group("DIR-1")]
        audits = _audit_coverage("c", subs, dirs, BriefContextSnapshot())
        assert len(audits) == 1
        cm = {e.sub_requirement_id: e for e in audits[0].coverage_matrix}
        assert cm["SR-1"].verdict == "directly_solves"
        assert cm["SR-1"].verdict_zh == "直接解"
        assert cm["SR-2"].verdict == "not_addressed"
        assert cm["SR-2"].verdict_zh == "未觸及"
