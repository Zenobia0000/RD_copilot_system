"""Tests for deterministic modules: CCI, SIM, parameter mapper."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.triz.verify.cci import (
    CCIInput,
    CCIVerdict,
    CognitiveChange,
    EnergyChange,
    StructuralChange,
    check_evidence_downgrade,
    classify_verdict,
    compute_cci,
    score_evolution_alignment,
)
from app.triz.solve.sim import (
    SIMStats,
    build_sim_result,
    check_convergence,
    compute_sim_stats,
)
from app.triz.state import EvidenceRegistry

KB_ROOT = Path(
    "/home/os-sunnie.gd.weng/python_workstation/sunny_01/"
    "RD_copilot_system/rd_assistant_design_system/triz_knowledge_base"
)


# ── CCI Tests ────────────────────────────────────────────────────────

class TestCCI:
    def test_strong_evolution(self):
        """All dimensions minimal → Strong Evolution."""
        inp = CCIInput(
            q1=StructuralChange.reduced,
            q2=EnergyChange.reduced,
            q3=CognitiveChange.simplified,
            trends_satisfied=3,
        )
        scores = compute_cci(inp)
        assert scores.cci == 0.0
        assert classify_verdict(scores.cci) == CCIVerdict.strong_evolution

    def test_hard_patch(self):
        """All dimensions maximal → Hard Patch."""
        inp = CCIInput(
            q1=StructuralChange.new_subsystem,
            q2=EnergyChange.new_source,
            q3=CognitiveChange.new_model,
            trends_satisfied=0,
        )
        scores = compute_cci(inp)
        assert scores.cci == 1.0
        assert classify_verdict(scores.cci) == CCIVerdict.hard_patch

    def test_ebike_scenario(self):
        """Approximate ebike drive unit CCI scoring."""
        inp = CCIInput(
            q1=StructuralChange.added_no_interface,  # 0.50
            q2=EnergyChange.reduced,                   # 0.00
            q3=CognitiveChange.one_branch,             # 0.50
            trends_satisfied=2,                         # 0.33
        )
        scores = compute_cci(inp)
        # CCI = 0.30*0.50 + 0.25*0.00 + 0.20*0.50 + 0.25*0.33
        expected = 0.30 * 0.50 + 0.25 * 0.00 + 0.20 * 0.50 + 0.25 * 0.33
        assert abs(scores.cci - expected) < 0.001
        verdict = classify_verdict(scores.cci)
        assert verdict in (CCIVerdict.weak_evolution, CCIVerdict.strong_evolution)

    def test_evolution_alignment_scoring(self):
        assert score_evolution_alignment(3, 3) == 0.00
        assert score_evolution_alignment(2, 3) == 0.33
        assert score_evolution_alignment(1, 3) == 0.67
        assert score_evolution_alignment(0, 3) == 1.00

    def test_evidence_downgrade(self):
        # 60% LOW → should downgrade
        registry = EvidenceRegistry(
            total_claims=10, high_confidence=2,
            medium_confidence=2, low_confidence=6,
        )
        result = check_evidence_downgrade(CCIVerdict.strong_evolution, registry)
        assert result == CCIVerdict.weak_evolution

    def test_no_downgrade_when_confidence_ok(self):
        registry = EvidenceRegistry(
            total_claims=10, high_confidence=6,
            medium_confidence=3, low_confidence=1,
        )
        result = check_evidence_downgrade(CCIVerdict.strong_evolution, registry)
        assert result == CCIVerdict.strong_evolution

    def test_no_downgrade_for_patch(self):
        """Patches don't get downgraded."""
        registry = EvidenceRegistry(
            total_claims=10, low_confidence=10,
        )
        result = check_evidence_downgrade(CCIVerdict.conscious_patch, registry)
        assert result == CCIVerdict.conscious_patch


# ── SIM Tests ────────────────────────────────────────────────────────

class TestSIM:
    def test_compute_stats(self):
        matrix = {
            "A × B": 1,
            "A × C": 0,
            "A × D": -1,
            "B × C": 0,
            "B × D": 1,
            "C × D": 0,
        }
        stats = compute_sim_stats(matrix)
        assert stats.plus_one == 2
        assert stats.zero == 3
        assert stats.minus_one == 1
        assert stats.total_pairs == 6

    def test_convergence_no_conflicts(self):
        stats = SIMStats(plus_one=2, zero=4, minus_one=0, total_pairs=6)
        assert check_convergence(stats, iteration=1) == "converged"

    def test_convergence_iterate(self):
        stats = SIMStats(plus_one=1, zero=3, minus_one=2, total_pairs=6)
        assert check_convergence(stats, iteration=1) == "iterate"

    def test_convergence_stop_at_max(self):
        stats = SIMStats(plus_one=1, zero=3, minus_one=2, total_pairs=6)
        result = check_convergence(
            stats, iteration=2, minus1_history=[3, 3]  # not improving
        )
        assert result == "stop"

    def test_convergence_improving_at_max(self):
        stats = SIMStats(plus_one=1, zero=4, minus_one=1, total_pairs=6)
        result = check_convergence(
            stats, iteration=2, minus1_history=[3, 1]  # improving
        )
        assert result == "iterate"

    def test_build_sim_result(self):
        matrix = {"SOL-TC1 × SOL-TC3": 0, "SOL-TC1 × SOL-TC4": 1, "SOL-TC3 × SOL-TC4": 0}
        result = build_sim_result(
            matrix,
            synergy_reasons=["TC1↔TC4: efficiency helps thermal"],
        )
        assert result.verdict == "converged"
        assert result.summary["+1"] == 1
        assert len(result.synergies) == 1

    def test_ebike_sim(self):
        """Replicate the ebike session SIM result."""
        matrix = {
            "SOL-TC1 × SOL-TC3": 0,
            "SOL-TC1 × SOL-TC5": 0,
            "SOL-TC1 × SOL-TC4": 1,
            "SOL-TC3 × SOL-TC5": 1,
            "SOL-TC3 × SOL-TC4": 0,
            "SOL-TC5 × SOL-TC4": 0,
        }
        result = build_sim_result(matrix)
        assert result.summary["+1"] == 2
        assert result.summary["0"] == 4
        assert result.summary["-1"] == 0
        assert result.verdict == "converged"


# ── Parameter Mapper Tests ───────────────────────────────────────────

class TestParamMapper:
    @pytest.fixture
    def kb(self):
        if not KB_ROOT.exists():
            pytest.skip("KB root not found")
        from app.triz.kb.loader import KBLoader
        return KBLoader(KB_ROOT)

    def test_torque_maps_to_force(self, kb):
        from app.triz.solve.param_mapper import rank_candidates
        candidates = rank_candidates("馬達扭力密度", kb, top_n=5)
        top_ids = [c.param.id for c in candidates]
        assert 10 in top_ids[:3]  # Force should be in top 3

    def test_noise_maps_to_harmful(self, kb):
        from app.triz.solve.param_mapper import rank_candidates
        candidates = rank_candidates("齒輪噪聲", kb, top_n=5)
        top_ids = [c.param.id for c in candidates]
        assert 31 in top_ids[:3]  # Harmful side effects

    def test_weight_maps_correctly(self, kb):
        from app.triz.solve.param_mapper import rank_candidates
        candidates = rank_candidates("系統重量", kb, top_n=5)
        top_ids = [c.param.id for c in candidates]
        assert 1 in top_ids[:3] or 2 in top_ids[:3]  # Weight (moving or stationary)

    def test_temperature_maps(self, kb):
        from app.triz.solve.param_mapper import rank_candidates
        candidates = rank_candidates("散熱溫升", kb, top_n=5)
        top_ids = [c.param.id for c in candidates]
        assert 17 in top_ids[:3]  # Temperature

    def test_needs_disambiguation(self, kb):
        from app.triz.solve.param_mapper import needs_llm_disambiguation, rank_candidates
        candidates = rank_candidates("something very generic", kb, top_n=5)
        # Generic input should need disambiguation
        assert needs_llm_disambiguation(candidates) is True
