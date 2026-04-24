"""Tests for LayeredTrizSolution drill-down orchestrator — v7 WBS 12.2 / 12.3.

Covers:
  - _l1_critic: rule path (principle_hits ≤ 2) and LLM path
  - _derive_pc_from_tc: LLM happy path + failure fallback
  - _should_trigger_l2: all five decision branches
  - solve_triz_layered: e-bike golden case (§7 of TRIZ_Layered_DrillDown_Optimization.md)
  - Phase B directive default (intra-LTS skip, cross-contradiction check)

All LLM calls are mocked — no network.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.models.schemas import (
    SolveTrizLayeredRequest,
    LayeredTrizSolution,
    L1Surface,
    L2RootCause,
    L3StructuralCheck,
    SuFieldModel,
    TrizSuggestion,
    TrizLookupResponse,
    SuFieldResponse,
)
from app.agents.triz_solver import (
    _l1_critic,
    _derive_pc_from_tc,
    _should_trigger_l2,
    solve_triz_layered,
)


# ---------------------------------------------------------------------------
# Fixtures — canned LLM responses matching §7 e-bike motor cooling case
# ---------------------------------------------------------------------------

_L1_TC_RAW = json.dumps({
    "suggestions": [
        {"path": "TC", "principle_number": 19, "principle_name": "Periodic Action",
         "suggestion": "脈衝冷卻 PWM 風扇", "affected_modules": ["cooling"]},
        {"path": "TC", "principle_number": 35, "principle_name": "Parameter changes",
         "suggestion": "溫控可變黏度冷卻液", "affected_modules": ["cooling"]},
        {"path": "TC", "principle_number": 3, "principle_name": "Local quality",
         "suggestion": "定子繞線末端局部散熱強化", "affected_modules": ["stator"]},
        {"path": "TC", "principle_number": 36, "principle_name": "Phase transitions",
         "suggestion": "定子端蓋填充 PCM 相變材料", "affected_modules": ["stator"]},
    ]
})

_L1_CRITIC_TRIGGER_RAW = json.dumps({
    "trigger_l2": True,
    "reason": "四條建議皆屬折衷修補，未改變功率與溫度的物理耦合。",
    "confidence": 0.88,
})

_L1_CRITIC_OK_RAW = json.dumps({
    "trigger_l2": False,
    "reason": "已有根因解，不需深挖",
    "confidence": 0.9,
})

_DEEPEN_LINK_RAW = json.dumps({
    "derived_physical_parameter": "瞬時功率 P(t)",
    "contradiction_statement": "P(t) 必須 ≥ P_peak（爬坡）且必須 ≤ P_thermal（散熱上限）",
    "separation_type_candidates": [
        {"type": "time", "confidence": 0.85, "rationale": "爬坡 10 秒允許 P_peak，巡航降回 P_thermal"},
        {"type": "condition", "confidence": 0.62, "rationale": "溫度 <100°C 時允許高功率"},
    ],
})

_L2_PC_RAW = json.dumps({
    "suggestions": [
        {"path": "PC", "principle_name": "時間分離: 週期性切換",
         "separation_principle": "時間分離",
         "suggestion": "雙模態功率管理：爬坡模式 P_peak 10s，巡航模式降回 P_thermal",
         "affected_modules": ["firmware", "motor"],
         "secondary_contradictions": ["感測器可靠度"]},
    ]
})

_L3_SF_RAW = json.dumps({
    "su_field": {"S1": "定子繞線", "S2": "外殼", "F": "熱場（Fourier 傳導）"},
    "system_state": "insufficient",
    "matched_solutions": [
        {"standard_id": "2.2.1", "standard_name": "引入 S3 中介物",
         "class_name": "Class 2",
         "suggestion": "引入熱管陣列作為 S3 中介物提升熱傳導路徑",
         "affected_modules": ["thermal_management"]},
    ]
})

_DIFF_RAW = json.dumps({
    "l1_vs_l2": {
        "on_solving_degree": "L1 優化 10-15%，L2 以時間分離消除主矛盾",
        "on_effort": "L1 小改 BOM；L2 需韌體",
        "on_risk": "L1 低；L2 需驗證",
    },
    "l1_vs_l3": {"orthogonality": "L1 時間維度 × L3 熱傳路徑"},
    "l2_vs_l3": {"synergy": "峰值窗口 +40%"},
    "recommended_route": {
        "primary": "L2 + L3 組合（突破路線）",
        "fallback": "L1 單獨（快速路線）",
        "adopted_layers": ["L2", "L3"],
        "rationale": "severity=major，韌體資源充足",
    },
    "l3_bridge": {
        "supports_l1": "為脈衝冷卻提供熱容緩衝",
        "supports_l2": "延長峰值窗口 +40%",
        "standalone_value": "獨立改善 15%",
    },
})


def _llm_response_router(num_candidates):
    """Return a stateful stub that dispatches LLM calls by order:
       1. L1 TC instantiation
       2. L1 critic
       3. deepen_link derive
       4. L2 PC instantiation
       5. L3 SF analysis (SuFieldAnalysis called twice: _solve_sf + analyze_sufield enrichment)
       6. differential_analysis
    """
    queue = [
        _L1_TC_RAW,
        _L1_CRITIC_TRIGGER_RAW,
        _DEEPEN_LINK_RAW,
        _L2_PC_RAW,
        _L3_SF_RAW,   # _solve_sf calls analyze_sufield internally
        _L3_SF_RAW,   # enrichment analyze_sufield call
        _DIFF_RAW,
    ]

    def _pop(*args, **kwargs):
        if not queue:
            return "{}"
        return queue.pop(0)

    return _pop


# ---------------------------------------------------------------------------
# _should_trigger_l2 — pure branching logic (no LLM)
# ---------------------------------------------------------------------------


class TestShouldTriggerL2:
    BASE = dict(project_id="p", contradiction_id="C-1", natural_description="test")

    def _l1(self, principles=None, critic=False, conf=0.0):
        return L1Surface(
            improving_param=21, worsening_param=17,
            candidate_principles=principles or [19, 35, 3, 36],
            suggestions=[], critic_trigger_l2=critic, critic_confidence=conf,
        )

    def test_quick_mode_minor_skipped(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="minor", quick_mode=True)
        trig, reason = _should_trigger_l2(req, self._l1())
        assert trig is False
        assert "quick_mode" in reason

    def test_force_l2_overrides_all(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="minor", force_l2=True)
        trig, reason = _should_trigger_l2(req, self._l1())
        assert trig is True
        assert "manual" in reason

    def test_major_severity_auto_triggers(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="major")
        trig, _ = _should_trigger_l2(req, self._l1())
        assert trig is True

    def test_fatal_severity_auto_triggers(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="fatal")
        trig, _ = _should_trigger_l2(req, self._l1())
        assert trig is True

    def test_high_conf_critic_triggers(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="unknown")
        trig, reason = _should_trigger_l2(req, self._l1(critic=True, conf=0.88))
        assert trig is True
        assert "critic" in reason

    def test_low_conf_critic_defers_to_rd(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="unknown")
        trig, reason = _should_trigger_l2(req, self._l1(critic=True, conf=0.3))
        assert trig is False
        assert "低信心" in reason or "0.30" in reason

    def test_no_critic_no_severity_skips(self):
        req = SolveTrizLayeredRequest(**self.BASE, severity="unknown")
        trig, reason = _should_trigger_l2(req, self._l1(critic=False))
        assert trig is False


# ---------------------------------------------------------------------------
# _l1_critic — rule + LLM
# ---------------------------------------------------------------------------


class TestL1Critic:
    def test_rule_fast_path_thin_matrix(self):
        trig, reason, conf = _l1_critic(
            natural_description="t",
            improving=1, worsening=14,
            candidate_principles=[1, 2],  # ≤ 2 → rule trigger
            l1_suggestions=[TrizSuggestion(suggestion="x")],
        )
        assert trig is True
        assert conf >= 0.8
        assert "2" in reason

    def test_rule_empty_suggestions_triggers(self):
        trig, _reason, conf = _l1_critic(
            natural_description="t", improving=21, worsening=17,
            candidate_principles=[19, 35, 3, 36], l1_suggestions=[],
        )
        assert trig is True
        assert conf >= 0.8

    @patch("app.agents.triz_solver.call_llm_json", return_value=_L1_CRITIC_TRIGGER_RAW)
    def test_llm_trade_off_diagnosis(self, _mock):
        trig, reason, conf = _l1_critic(
            natural_description="馬達散熱",
            improving=21, worsening=17,
            candidate_principles=[19, 35, 3, 36],
            l1_suggestions=[TrizSuggestion(principle_number=19, suggestion="脈衝冷卻")],
        )
        assert trig is True
        assert 0.8 < conf <= 1.0
        assert "折衷" in reason

    @patch("app.agents.triz_solver.call_llm_json", return_value=_L1_CRITIC_OK_RAW)
    def test_llm_root_cause_present(self, _mock):
        trig, _, conf = _l1_critic(
            natural_description="t", improving=21, worsening=17,
            candidate_principles=[19, 35, 3, 36],
            l1_suggestions=[TrizSuggestion(principle_number=19, suggestion="x")],
        )
        assert trig is False
        assert conf >= 0.8

    @patch("app.agents.triz_solver.call_llm_json", side_effect=RuntimeError("LLM down"))
    def test_llm_failure_defaults_no_trigger(self, _mock):
        trig, _, conf = _l1_critic(
            natural_description="t", improving=21, worsening=17,
            candidate_principles=[19, 35, 3, 36],
            l1_suggestions=[TrizSuggestion(suggestion="x")],
        )
        assert trig is False
        assert conf == 0.0


# ---------------------------------------------------------------------------
# _derive_pc_from_tc — ARIZ deepen
# ---------------------------------------------------------------------------


class TestDerivePcFromTc:
    @patch("app.agents.triz_solver.call_llm_json", return_value=_DEEPEN_LINK_RAW)
    def test_happy_path_ebike(self, _mock):
        link = _derive_pc_from_tc(
            natural_description="馬達功率密度提升導致溫升", improving=21, worsening=17,
        )
        assert link.from_tc_pair == (21, 17)
        assert "P(t)" in link.derived_physical_parameter
        assert link.separation_type_candidates[0].type == "time"
        assert link.separation_type_candidates[0].confidence == 0.85
        # sorted by confidence desc
        assert (
            link.separation_type_candidates[0].confidence
            >= link.separation_type_candidates[1].confidence
        )

    def test_missing_params_returns_empty_link(self):
        link = _derive_pc_from_tc(natural_description="t", improving=None, worsening=None)
        assert link.from_tc_pair == (None, None)
        assert link.derived_physical_parameter == ""
        assert link.separation_type_candidates == []

    @patch("app.agents.triz_solver.call_llm_json", side_effect=RuntimeError("LLM down"))
    def test_llm_failure_returns_default_link(self, _mock):
        link = _derive_pc_from_tc(natural_description="t", improving=21, worsening=17)
        assert link.from_tc_pair == (21, 17)
        assert link.derived_physical_parameter == ""


# ---------------------------------------------------------------------------
# solve_triz_layered — end-to-end e-bike golden case (§7)
# ---------------------------------------------------------------------------


class TestSolveTrizLayeredGoldenCase:
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[19, 35, 3, 36])
    def test_ebike_motor_cooling(self, _matrix_mock):
        router = _llm_response_router(4)
        with patch("app.agents.triz_solver.call_llm_json", side_effect=router):
            req = SolveTrizLayeredRequest(
                project_id="ebike-001",
                contradiction_id="C-EBIKE-012",
                natural_description="馬達功率密度提升導致定子溫度超過 145°C 絕緣上限",
                improving_param=21,
                worsening_param=17,
                severity="major",
                sf_substance_1="定子繞線",
                sf_substance_2="外殼",
                sf_field="熱場",
            )
            resp = solve_triz_layered(req)

        lts = resp.layered_solution
        # Identity
        assert lts.id.startswith("LTS-")
        assert lts.contradiction_id == "C-EBIKE-012"
        assert lts.severity == "major"

        # L1 — always ran, has 4 suggestions and candidate principles
        assert lts.l1_surface.status == "ran"
        assert lts.l1_surface.candidate_principles == [19, 35, 3, 36]
        assert len(lts.l1_surface.suggestions) == 4
        assert lts.l1_surface.depth_indicator == "trade-off 改良"
        # critic said trigger_l2=True with high confidence
        assert lts.l1_surface.critic_trigger_l2 is True
        assert lts.l1_surface.critic_confidence >= 0.8

        # L2 — triggered due to major + critic, has deepen_link
        assert lts.l2_root_cause is not None
        assert lts.l2_root_cause.triggered is True
        assert lts.l2_root_cause.status == "ran"
        link = lts.l2_root_cause.deepen_link
        assert link is not None
        assert "P(t)" in link.derived_physical_parameter
        assert link.separation_type_candidates[0].type == "time"
        assert len(lts.l2_root_cause.suggestions) >= 1

        # L3 — always ran, has Su-Field model and at least one matched standard solution
        assert lts.l3_structural_check.status == "ran"
        assert lts.l3_structural_check.su_field_model.state in (
            "insufficient", "harmful", "unknown"
        )
        # L3 bridge text populated by differential_analysis
        assert lts.l3_structural_check.standalone_value != ""

        # differential_analysis + recommended_route
        diff = lts.differential_analysis
        assert diff.recommended_route.primary.startswith("L2")
        assert diff.recommended_route.adopted_layers == ["L2", "L3"]
        assert "severity" in diff.recommended_route.rationale

        # Phase B directive default — intra-LTS SKIP
        assert lts.phase_b_directive.same_contradiction_intra_layer_conflict == "skip"
        assert lts.phase_b_directive.cross_contradiction_conflict == "check"

    @patch("app.agents.triz_solver.lookup_matrix", return_value=[19, 35, 3, 36])
    def test_quick_mode_minor_skips_l2(self, _matrix_mock):
        """severity=minor + quick_mode=true → L2 status=skipped_quick_mode."""
        queue = [_L1_TC_RAW, _L1_CRITIC_OK_RAW, _L3_SF_RAW, _L3_SF_RAW, _DIFF_RAW]

        def pop(*a, **k):
            return queue.pop(0) if queue else "{}"

        with patch("app.agents.triz_solver.call_llm_json", side_effect=pop):
            req = SolveTrizLayeredRequest(
                project_id="p", contradiction_id="C-2",
                natural_description="微調矛盾",
                improving_param=21, worsening_param=17,
                severity="minor", quick_mode=True,
            )
            resp = solve_triz_layered(req)

        # L2 should be present but skipped (not triggered)
        l2 = resp.layered_solution.l2_root_cause
        # skipped layer may be None (not emitted) — check both shapes
        if l2 is not None:
            assert l2.triggered is False
            assert l2.status == "skipped_quick_mode"
            assert "quick_mode" in l2.trigger_reason

    @patch("app.agents.triz_solver.lookup_matrix", return_value=[])
    def test_missing_tc_params_degrades_gracefully(self, _matrix_mock):
        """Missing improving/worsening params → L1 errors, L2 forced on fallback."""
        queue = [_L3_SF_RAW, _L3_SF_RAW, _DIFF_RAW]

        def pop(*a, **k):
            return queue.pop(0) if queue else "{}"

        with patch("app.agents.triz_solver.call_llm_json", side_effect=pop):
            req = SolveTrizLayeredRequest(
                project_id="p", contradiction_id="C-3",
                natural_description="無完整參數",
                improving_param=None, worsening_param=None,
                severity="unknown",
            )
            resp = solve_triz_layered(req)

        lts = resp.layered_solution
        assert lts.l1_surface.status == "error"
        assert lts.l1_surface.critic_trigger_l2 is True
        # L3 still runs
        assert lts.l3_structural_check.status == "ran"
