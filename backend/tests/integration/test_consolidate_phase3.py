"""Phase 3：整併三層改造的整合測試。

對應 plans/triz-redesign.md Phase 3，驗收四個核心承諾：

1. `_max_independent_subsets` 是純函式，能正確找出
   「4 個方向、其中 1 對衝突」的最大相容子集。
2. PickedSelection 的 N>6 在 Pydantic 層被擋下 (ValueError)。
3. `consolidate_solutions` 帶 picks 時，跨矛盾 swap 不會動到「已勾的方向」，
   並在仍衝突時把 status=conflict + integration_advice 加上 user_pinned 標註。
4. `_generate_engineering_verdict_card` 用 mock LLM 跑完後，八節都有實際內容
   （Q8 boundary_collapse ≥5；Q7 四工況全有 verdict）。
"""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.agents.triz_solver import (
    _max_independent_subsets,
    _check_intra_contradiction_compatibility,
    _generate_engineering_verdict_card,
    _build_candidate_pool,
    _score_loss_optimized_swap,
    consolidate_solutions,
)
from app.models.schemas import (
    BriefConstraint,
    BriefContextSnapshot,
    BriefKpi,
    CompatibilityResult,
    ConsolidateRequest,
    ConsolidationResult,
    ContradictionDirectionResult,
    DirectionGroup,
    DirectionScore,
    EngineeringVerdictCard,
    IntraContradictionCompatibility,
    PickedSelection,
)


# ===========================================================================
# Fixtures
# ===========================================================================


def _mk_dir(direction_id: str, name: str = "") -> DirectionGroup:
    return DirectionGroup(
        direction_id=direction_id,
        direction_name=name or direction_id,
        direction_summary=f"{direction_id} summary",
    )


def _mk_result(
    cid: str,
    direction_ids: list[str],
    top1: str | None = None,
    top2: str | None = None,
) -> ContradictionDirectionResult:
    dirs = [_mk_dir(d) for d in direction_ids]
    by_id = {d.direction_id: d for d in dirs}
    return ContradictionDirectionResult(
        contradiction_id=cid,
        natural_description=f"contradiction {cid}",
        all_directions=dirs,
        top1=by_id.get(top1) if top1 else (dirs[0] if dirs else None),
        top2=by_id.get(top2) if top2 else (dirs[1] if len(dirs) > 1 else None),
    )


EMPTY_CTX = BriefContextSnapshot(
    project_id="phase3-fixture",
    mission="Phase 3 unit-test mission.",
    constraints=[BriefConstraint(code="C-01", description="外徑≤111mm", type="hard")],
    kpis=[BriefKpi(name="效率", target_value=">=85", unit="%")],
)


# ===========================================================================
# A. _max_independent_subsets — 純函式
# ===========================================================================


class TestMaxIndependentSubsets:

    def test_no_conflict_returns_full_set(self):
        nodes = ["A", "B", "C"]
        out = _max_independent_subsets(nodes, [])
        assert out == [["A", "B", "C"]]

    def test_one_conflict_pair_drops_one(self):
        # A-B conflict; max independent = {A,C,D} or {B,C,D} (size 3)
        nodes = ["A", "B", "C", "D"]
        out = _max_independent_subsets(nodes, [("A", "B")])
        assert len(out) >= 1
        # All best subsets must have size 3
        assert all(len(s) == 3 for s in out)
        # Must include both {A,C,D} and {B,C,D}
        sets = {frozenset(s) for s in out}
        assert frozenset({"A", "C", "D"}) in sets
        assert frozenset({"B", "C", "D"}) in sets

    def test_chain_conflict(self):
        # A-B, B-C → max independent = {A, C} (drop B)
        nodes = ["A", "B", "C"]
        out = _max_independent_subsets(nodes, [("A", "B"), ("B", "C")])
        assert frozenset(out[0]) == frozenset({"A", "C"})

    def test_six_nodes_one_conflict(self):
        # N=6 (max allowed). One conflict A-B → best size 5.
        nodes = ["A", "B", "C", "D", "E", "F"]
        out = _max_independent_subsets(nodes, [("A", "B")])
        assert all(len(s) == 5 for s in out)


# ===========================================================================
# B. PickedSelection schema 守住 N ≤ 6
# ===========================================================================


class TestPickedSelectionLimit:

    def test_six_is_allowed(self):
        p = PickedSelection(
            contradiction_id="C-1",
            picked_direction_ids=[f"DIR-{i}" for i in range(1, 7)],
        )
        assert len(p.picked_direction_ids) == 6

    def test_seven_is_rejected_with_422_message(self):
        with pytest.raises(ValidationError) as exc_info:
            PickedSelection(
                contradiction_id="C-1",
                picked_direction_ids=[f"DIR-{i}" for i in range(1, 8)],
            )
        msg = str(exc_info.value)
        assert "6" in msg


# ===========================================================================
# C. _check_intra_contradiction_compatibility — 4 方向、1 對衝突
# ===========================================================================


class TestIntraContradictionCompatibility:

    def test_four_directions_one_conflict_finds_subset_of_three(self):
        result = _mk_result(
            cid="C-1",
            direction_ids=["DIR-1", "DIR-2", "DIR-3", "DIR-4"],
        )
        pick = PickedSelection(
            contradiction_id="C-1",
            picked_direction_ids=["DIR-1", "DIR-2", "DIR-3", "DIR-4"],
        )

        # Mock LLM to declare DIR-1 vs DIR-2 incompatible; rest compatible.
        mocked_pairs = {
            "pairs": [
                {
                    "direction_a": "DIR-1",
                    "direction_b": "DIR-2",
                    "compatible": False,
                    "conflict_type": "intervention_clash",
                    "reason": "shared PWM loop",
                },
                {
                    "direction_a": "DIR-1",
                    "direction_b": "DIR-3",
                    "compatible": True,
                    "conflict_type": "none",
                    "reason": "different layers",
                },
                {
                    "direction_a": "DIR-1",
                    "direction_b": "DIR-4",
                    "compatible": True,
                    "conflict_type": "none",
                    "reason": "different layers",
                },
                {
                    "direction_a": "DIR-2",
                    "direction_b": "DIR-3",
                    "compatible": True,
                    "conflict_type": "none",
                    "reason": "different layers",
                },
                {
                    "direction_a": "DIR-2",
                    "direction_b": "DIR-4",
                    "compatible": True,
                    "conflict_type": "none",
                    "reason": "different layers",
                },
                {
                    "direction_a": "DIR-3",
                    "direction_b": "DIR-4",
                    "compatible": True,
                    "conflict_type": "none",
                    "reason": "different layers",
                },
            ],
            "recommendation": "建議組合：DIR-1 + DIR-3 + DIR-4 或 DIR-2 + DIR-3 + DIR-4",
        }

        import json as _json
        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=_json.dumps(mocked_pairs),
        ):
            reports = _check_intra_contradiction_compatibility([pick], [result])

        assert len(reports) == 1
        report = reports[0]
        assert report.has_conflict is True
        assert len(report.pairwise_results) == 6
        # Best subsets: size 3, no pair {DIR-1, DIR-2}
        assert report.max_compatible_subsets, "should produce at least one subset"
        best = report.max_compatible_subsets[0]
        assert len(best) == 3
        # The conflicting pair must not co-occur in any subset
        for s in report.max_compatible_subsets:
            assert not ({"DIR-1", "DIR-2"} <= set(s))


# ===========================================================================
# D. consolidate_solutions with picks — swap 不動勾的方向
# ===========================================================================


class TestConsolidateSwapHonorsPicks:

    def test_swap_skips_pinned_contradiction(self):
        # Two contradictions; both with 2 directions (top1 / top2).
        # We will PIN C-1 to DIR-1 (which conflicts with C-2's top1 DIR-3).
        # → Swap must NOT touch C-1; must touch C-2 instead.

        result_1 = _mk_result(
            cid="C-1", direction_ids=["DIR-1", "DIR-2"], top1="DIR-1", top2="DIR-2"
        )
        result_2 = _mk_result(
            cid="C-2", direction_ids=["DIR-3", "DIR-4"], top1="DIR-3", top2="DIR-4"
        )

        picks = [
            PickedSelection(contradiction_id="C-1", picked_direction_ids=["DIR-1"]),
        ]
        req = ConsolidateRequest(
            project_id="proj-phase3-test",
            results=[result_1, result_2],
            picks=picks,
        )

        # Sequence of LLM responses:
        #   1. compat check — DIR-1 vs DIR-3 conflict.
        #   2. swap re-check (after C-2 swapped to DIR-4) — all compat.
        #   3. conflict_report (status=resolved_with_swap) — empty.
        #   4. verdict_card LLM — minimal valid card.
        import json as _json

        responses = iter(
            [
                # 1. initial compat
                _json.dumps(
                    {
                        "pairs": [
                            {
                                "direction_a": "DIR-1",
                                "direction_b": "DIR-3",
                                "contradiction_a_id": "C-1",
                                "contradiction_b_id": "C-2",
                                "compatible": False,
                                "conflict_type": "module_overlap",
                                "reason": "both touch same module X",
                            }
                        ]
                    }
                ),
                # 2. re-check after swap
                _json.dumps({"pairs": []}),
                # 3. conflict_report
                _json.dumps(
                    {"suggestions": [], "integration_advice": "swap resolved"}
                ),
                # 4. verdict_card
                _json.dumps(
                    {
                        "contradiction_face_per_picked": [],
                        "mechanism_trace": {
                            "technology_mix": ["control"],
                            "delta_chain": ["a", "b", "c"],
                            "assumptions": ["x", "y"],
                            "evidence_level": "E2",
                        },
                        "feasibility_matrix": {
                            "axes": [
                                {
                                    "axis": f"ax{i}",
                                    "source_ref": "",
                                    "verdict": "pass",
                                    "rationale": "...",
                                    "quantitative_estimate": "",
                                }
                                for i in range(5)
                            ],
                            "overall_verdict": "pass",
                            "bottleneck_axes": [],
                        },
                        "side_effects_via_cld": {
                            "paths": [],
                            "socratic_warnings": [],
                        },
                        "coverage_completeness": {
                            "resolves_fully": [],
                            "resolves_partial": [],
                            "resolves_conditional": [],
                            "does_not_address": [],
                            "open_questions": ["open?"],
                        },
                        "verification_plan": {
                            "steps": [
                                {
                                    "phase": "simulation",
                                    "test_description": "t1",
                                    "expected_outcome": "ok",
                                    "effort_hours": 4,
                                    "blocking": True,
                                }
                            ],
                            "socratic_action_links": [],
                        },
                        "duty_cycle_verdict": {
                            "peak": "addressed",
                            "continuous": "addressed",
                            "startup": "marginal",
                            "steady_state": "addressed",
                            "cycle_specific_notes": "ok",
                        },
                        "boundary_collapse": [
                            {
                                "condition": f"c{i}",
                                "failure_mode": "f",
                                "severity": "moderate",
                            }
                            for i in range(5)
                        ],
                        "final_verdict": "adopt_with_conditions",
                        "final_rationale": "ok",
                        "confidence": 0.7,
                    }
                ),
            ]
        )

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        # Avoid hitting Supabase / brief_context fetch — also avoid DB persistence.
        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result",
            return_value=None,
        ), patch(
            "app.services.brief_context.fetch_brief_context",
            return_value=EMPTY_CTX,
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        # C-1 must keep DIR-1 (pinned); C-2 swapped to DIR-4
        assert cons.adopted_directions["C-1"].direction_id == "DIR-1"
        assert cons.adopted_directions["C-2"].direction_id == "DIR-4"
        # Status must be resolved_with_swap (swap did succeed because C-2 was swappable)
        assert cons.status == "resolved_with_swap"
        # VerdictCard should be present
        assert resp.verdict_card is not None
        assert resp.verdict_card.final_verdict == "adopt_with_conditions"


# ===========================================================================
# D2. consolidate_solutions — single-contradiction fast path 也應產 verdict_card
# ===========================================================================
#
# 回歸測試：保護 src/pages/Create.tsx handleConsolidateOnly 的修復
# （移除 FE local fallback、單矛盾也呼叫 backend）。背景是使用者反映：
#   「正向分析只有 1 條矛盾、勾完方向按下跨矛盾方向整併，
#    只看到 toast『已為 1 條矛盾產出方向整併』，VerdictCard 沒出。」
# 根因：FE 走自己的 local fallback、跳過 backend。修復後 FE 一律打後端，
# 因此我們得在 backend 這頭確保：len(results)==1 一樣會回 verdict_card。
# 對應 backend 程式碼 triz_solver.consolidate_solutions line 4951 fast path。


class TestConsolidateSingleContradictionVerdictCard:
    """單矛盾 fast path：不跑跨矛盾 swap，但仍要產 verdict_card。"""

    def _verdict_payload(self) -> dict:
        """Minimal valid Q1–Q8 payload for _generate_engineering_verdict_card LLM."""
        return {
            "contradiction_face_per_picked": [],
            "mechanism_trace": {
                "technology_mix": ["structure"],
                "delta_chain": ["a", "b", "c"],
                "assumptions": ["x"],
                "evidence_level": "E2",
            },
            "feasibility_matrix": {
                "axes": [
                    {
                        "axis": f"ax{i}",
                        "source_ref": "",
                        "verdict": "pass",
                        "rationale": "...",
                        "quantitative_estimate": "",
                    }
                    for i in range(5)
                ],
                "overall_verdict": "pass",
                "bottleneck_axes": [],
            },
            "side_effects_via_cld": {"paths": [], "socratic_warnings": []},
            "coverage_completeness": {
                "resolves_fully": [],
                "resolves_partial": [],
                "resolves_conditional": [],
                "does_not_address": [],
                "open_questions": ["open?"],
            },
            "verification_plan": {
                "steps": [
                    {
                        "phase": "simulation",
                        "test_description": "t1",
                        "expected_outcome": "ok",
                        "effort_hours": 4,
                        "blocking": True,
                    }
                ],
                "socratic_action_links": [],
            },
            "duty_cycle_verdict": {
                "peak": "addressed",
                "continuous": "addressed",
                "startup": "marginal",
                "steady_state": "addressed",
                "cycle_specific_notes": "ok",
            },
            "boundary_collapse": [
                {
                    "condition": f"c{i}",
                    "failure_mode": "f",
                    "severity": "moderate",
                }
                for i in range(5)
            ],
            "final_verdict": "adopt",
            "final_rationale": "single contradiction adopted",
            "confidence": 0.8,
        }

    def test_single_contradiction_no_picks_returns_verdict_card(self):
        """沒 picks、僅 1 條矛盾 → backend 應走 fast path 並回傳 verdict_card。

        這對應 FE 修復後的「未勾選即按下整併」情境（單矛盾允許）。
        """
        import json as _json

        result = _mk_result(
            cid="C-only",
            direction_ids=["DIR-1", "DIR-2"],
            top1="DIR-1",
            top2="DIR-2",
        )
        req = ConsolidateRequest(
            project_id="proj-single-no-picks",
            results=[result],
            picks=[],
        )

        # 單矛盾 + 沒 picks → 只會呼叫 1 次 LLM (verdict_card)，不跑 intra_compat。
        responses = iter([_json.dumps(self._verdict_payload())])

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result",
            return_value=None,
        ), patch(
            "app.agents.triz_solver._gc_orphan_directed_solutions",
            return_value=None,
        ), patch(
            "app.services.brief_context.fetch_brief_context",
            return_value=EMPTY_CTX,
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        # Fast-path 採 pool[0] = top1
        assert "C-only" in cons.adopted_directions
        assert cons.adopted_directions["C-only"].direction_id == "DIR-1"
        # status 必為 compatible（沒跨矛盾衝突可比）
        assert cons.status == "compatible"
        # 沒勾任何方向 → was_user_picked 為空
        assert not cons.was_user_picked
        # 沒 swap → exhausted_contradictions 空、total_rounds=0
        assert cons.exhausted_contradictions == []
        assert cons.total_rounds == 0
        # 關鍵承諾：verdict_card 不可為 None
        assert resp.verdict_card is not None
        assert resp.verdict_card.final_verdict == "adopt"
        # 八節都應該有實際內容 — sanity check
        assert len(resp.verdict_card.feasibility_matrix.axes) == 5
        assert len(resp.verdict_card.boundary_collapse) == 5

    def test_single_contradiction_with_pick_honors_user_selection(self):
        """單矛盾 + 勾 DIR-2 (非 top1) → adopted 應為 DIR-2、was_user_picked 標註。

        這正是使用者抱怨「畫面看起來還是用其他的矛盾解法」的場景：
        FE 應該把 RD 勾的方向送進來，backend 應在 was_user_picked 標出，
        verdict_card 也必須產出。
        """
        import json as _json

        result = _mk_result(
            cid="C-only",
            direction_ids=["DIR-1", "DIR-2"],
            top1="DIR-1",
            top2="DIR-2",
        )
        picks = [
            PickedSelection(
                contradiction_id="C-only", picked_direction_ids=["DIR-2"]
            ),
        ]
        req = ConsolidateRequest(
            project_id="proj-single-with-pick",
            results=[result],
            picks=picks,
        )

        # 單矛盾 + 1 個 pick → intra_compat 跑「只勾 1 個 = 無需相容性檢查」(不打 LLM)，
        # 然後 fast path 走 verdict_card。總 LLM 呼叫 = 1。
        responses = iter([_json.dumps(self._verdict_payload())])

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result",
            return_value=None,
        ), patch(
            "app.agents.triz_solver._gc_orphan_directed_solutions",
            return_value=None,
        ), patch(
            "app.services.brief_context.fetch_brief_context",
            return_value=EMPTY_CTX,
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        # adopted 應為使用者勾的 DIR-2，非系統 Top1 DIR-1
        assert cons.adopted_directions["C-only"].direction_id == "DIR-2"
        # was_user_picked 標註 RD 勾選
        assert cons.was_user_picked == {"C-only": "DIR-2"}
        # status compatible（單矛盾無跨矛盾衝突）
        assert cons.status == "compatible"
        # verdict_card 必須有
        assert resp.verdict_card is not None
        assert resp.verdict_card.final_verdict == "adopt"


# ===========================================================================
# E. _generate_engineering_verdict_card — 八節都有內容
# ===========================================================================


class TestVerdictCardEightSections:

    def test_all_eight_sections_populated(self):
        import json as _json

        consolidation = ConsolidationResult(
            status="compatible",
            adopted_directions={
                "C-1": _mk_dir("DIR-1", "Direction One"),
            },
            integration_advice="ok",
        )
        results = [
            _mk_result(cid="C-1", direction_ids=["DIR-1", "DIR-2"], top1="DIR-1"),
        ]

        # LLM payload covering all 8 sections with realistic content.
        payload = {
            "contradiction_face_per_picked": [
                {
                    "contradiction_id": "C-1",
                    "picked_direction_id": "DIR-1",
                    "picked_direction_name": "Direction One",
                    "improving_side": "yes",
                    "worsening_side": "partial",
                    "introduces_new_side_effect": ["new noise"],
                }
            ],
            "mechanism_trace": {
                "technology_mix": ["control", "material"],
                "delta_chain": ["s1", "s2", "s3"],
                "assumptions": ["a1", "a2"],
                "evidence_level": "E3",
            },
            "feasibility_matrix": {
                "axes": [
                    {
                        "axis": f"axis-{i}",
                        "source_ref": "",
                        "verdict": "pass",
                        "rationale": "ok",
                        "quantitative_estimate": "no change",
                    }
                    for i in range(5)
                ],
                "overall_verdict": "pass",
                "bottleneck_axes": [],
            },
            "side_effects_via_cld": {
                "paths": [
                    {
                        "cld_path": ["A", "B", "C"],
                        "polarity_chain": ["positive", "negative"],
                        "direction_impact": "loop reinforces",
                        "risk_level": "medium",
                    }
                ],
                "socratic_warnings": ["⚠️ watch out"],
            },
            "coverage_completeness": {
                "resolves_fully": ["SR-1"],
                "resolves_partial": ["SR-2"],
                "resolves_conditional": [],
                "does_not_address": [],
                "open_questions": ["q1"],
            },
            "verification_plan": {
                "steps": [
                    {
                        "phase": "simulation",
                        "test_description": "FEA",
                        "expected_outcome": "stress < limit",
                        "effort_hours": 16,
                        "blocking": True,
                    },
                    {
                        "phase": "bench",
                        "test_description": "torque rig",
                        "expected_outcome": "125Nm ok",
                        "effort_hours": 40,
                        "blocking": False,
                    },
                ],
                "socratic_action_links": ["📋 bring up next review"],
            },
            "duty_cycle_verdict": {
                "peak": "addressed",
                "continuous": "marginal",
                "startup": "not_addressed",
                "steady_state": "addressed",
                "cycle_specific_notes": "peak ok, startup weak",
            },
            "boundary_collapse": [
                {"condition": f"cond-{i}", "failure_mode": "fail", "severity": "moderate"}
                for i in range(5)
            ],
            "final_verdict": "adopt_with_conditions",
            "final_rationale": "Most axes pass.",
            "confidence": 0.65,
        }

        with patch(
            "app.agents.triz_solver.call_llm_json", return_value=_json.dumps(payload)
        ):
            card = _generate_engineering_verdict_card(
                project_id="proj-x",
                consolidation=consolidation,
                results=results,
                brief_ctx=EMPTY_CTX,
                consolidation_id="TCR-x",
            )

        assert isinstance(card, EngineeringVerdictCard)
        # Q1
        assert len(card.contradiction_face_per_picked) == 1
        # Q2
        assert card.mechanism_trace.technology_mix
        assert card.mechanism_trace.evidence_level == "E3"
        # Q3
        assert len(card.feasibility_matrix.axes) >= 5
        assert card.feasibility_matrix.overall_verdict == "pass"
        # Q4
        assert card.side_effects_via_cld.paths
        # Q5
        assert "SR-1" in card.coverage_completeness.resolves_fully
        # Q6
        assert len(card.verification_plan.steps) >= 2
        # Q7 — all four cycle phases must be filled
        assert card.duty_cycle_verdict.peak in {"addressed", "marginal", "not_addressed"}
        assert card.duty_cycle_verdict.continuous in {"addressed", "marginal", "not_addressed"}
        assert card.duty_cycle_verdict.startup in {"addressed", "marginal", "not_addressed"}
        assert card.duty_cycle_verdict.steady_state in {"addressed", "marginal", "not_addressed"}
        # Q8 — at least 5 fail conditions
        assert len(card.boundary_collapse) >= 5
        # Final
        assert card.final_verdict in {
            "adopt", "adopt_with_conditions", "needs_revision", "reject"
        }

    def test_fallback_pads_q8_to_five(self):
        """LLM 給少於 5 條 boundary_collapse → 後端應補滿到 5。"""
        import json as _json

        partial = {
            "contradiction_face_per_picked": [],
            "mechanism_trace": {
                "technology_mix": [],
                "delta_chain": [],
                "assumptions": [],
                "evidence_level": "E0",
            },
            "feasibility_matrix": {
                "axes": [],
                "overall_verdict": "marginal",
                "bottleneck_axes": [],
            },
            "side_effects_via_cld": {"paths": [], "socratic_warnings": []},
            "coverage_completeness": {
                "resolves_fully": [],
                "resolves_partial": [],
                "resolves_conditional": [],
                "does_not_address": [],
                "open_questions": [],
            },
            "verification_plan": {"steps": [], "socratic_action_links": []},
            "duty_cycle_verdict": {
                "peak": "not_addressed",
                "continuous": "not_addressed",
                "startup": "not_addressed",
                "steady_state": "not_addressed",
                "cycle_specific_notes": "",
            },
            "boundary_collapse": [
                {"condition": "only one", "failure_mode": "...", "severity": "mild"}
            ],
            "final_verdict": "needs_revision",
            "final_rationale": "",
            "confidence": 0.3,
        }

        with patch(
            "app.agents.triz_solver.call_llm_json", return_value=_json.dumps(partial)
        ):
            card = _generate_engineering_verdict_card(
                project_id="proj-y",
                consolidation=ConsolidationResult(),
                results=[],
                brief_ctx=EMPTY_CTX,
                consolidation_id="TCR-y",
            )

        # Padding rule: at least 5 boundary conditions
        assert len(card.boundary_collapse) >= 5


# ===========================================================================
# F. Bug 2 — picks 指定的方向「剛好不是 Top1」不該被誤判為 resolved_with_swap
# ===========================================================================


# 最小 verdict_card JSON (符合 schema)，用於 mock LLM 回應。
def _minimal_verdict_card_json() -> str:
    import json as _json
    return _json.dumps(
        {
            "contradiction_face_per_picked": [],
            "mechanism_trace": {
                "technology_mix": ["control"],
                "delta_chain": ["a", "b", "c"],
                "assumptions": ["x", "y"],
                "evidence_level": "E2",
            },
            "feasibility_matrix": {
                "axes": [
                    {
                        "axis": f"ax{i}",
                        "source_ref": "",
                        "verdict": "pass",
                        "rationale": "...",
                        "quantitative_estimate": "",
                    }
                    for i in range(5)
                ],
                "overall_verdict": "pass",
                "bottleneck_axes": [],
            },
            "side_effects_via_cld": {"paths": [], "socratic_warnings": []},
            "coverage_completeness": {
                "resolves_fully": [],
                "resolves_partial": [],
                "resolves_conditional": [],
                "does_not_address": [],
                "open_questions": [],
            },
            "verification_plan": {"steps": [], "socratic_action_links": []},
            "duty_cycle_verdict": {
                "peak": "addressed",
                "continuous": "addressed",
                "startup": "addressed",
                "steady_state": "addressed",
                "cycle_specific_notes": "",
            },
            "boundary_collapse": [
                {"condition": f"c{i}", "failure_mode": "f", "severity": "moderate"}
                for i in range(5)
            ],
            "final_verdict": "adopt",
            "final_rationale": "ok",
            "confidence": 0.7,
        }
    )


class TestPickedDirectionNotMistakenAsSwap:
    """Bug 2: 使用者勾選非 Top1 的方向時，status 不應該是 resolved_with_swap。

    背景：consolidate_solutions 用 picks 構建 initial_adopted，並把 cid 加入 pinned。
    若 RD 勾的方向「剛好不是 Top1」，那 adopted_directions 確實會跟原本 Top1 不同，
    但這是 user_picked，**不是 system swap**。

    bugfix 後的判斷：只有「至少一條矛盾的 adopted ≠ initial_adopted」（即系統真的
    把 Top1 swap 成 Top2）才回 resolved_with_swap。
    """

    def test_single_pick_non_top1_returns_compatible_not_swap(self):
        """單條矛盾，RD 勾了 DIR-2（非 Top1=DIR-1）→ 應該回 compatible。"""
        import json as _json
        from unittest.mock import patch

        result = _mk_result(
            cid="C-1", direction_ids=["DIR-1", "DIR-2"], top1="DIR-1", top2="DIR-2"
        )
        picks = [PickedSelection(contradiction_id="C-1", picked_direction_ids=["DIR-2"])]
        req = ConsolidateRequest(
            project_id="proj-bug2-single",
            results=[result],
            picks=picks,
        )

        # 單條矛盾不會跑 cross-compat (len(adopted)==1) → _check_compatibility 直接回
        # 空 list；不會觸發 swap。但 verdict_card LLM 仍會跑一次。
        responses = iter(
            [
                # 1. initial compat (但 _check_compatibility 對單條只回空)
                _json.dumps({"pairs": []}),
                # 2. verdict_card
                _minimal_verdict_card_json(),
            ]
        )

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result", return_value=None
        ), patch(
            "app.agents.triz_solver._gc_orphan_directed_solutions", return_value=0
        ), patch(
            "app.services.brief_context.fetch_brief_context", return_value=EMPTY_CTX
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        # 採用了 DIR-2（RD 勾的）
        assert cons.adopted_directions["C-1"].direction_id == "DIR-2"
        # **核心驗收**：status 不是 resolved_with_swap (因為沒有 system swap)
        assert cons.status == "compatible", (
            f"當 RD 勾的方向剛好不是 Top1 時，status 應該是 compatible，"
            f"不應是 resolved_with_swap。實際: {cons.status}"
        )
        # was_user_picked 應該記錄這條矛盾的勾選方向
        assert cons.was_user_picked == {"C-1": "DIR-2"}

    def test_two_picks_non_top1_no_conflict_returns_compatible(self):
        """兩條矛盾都勾了非 Top1，但兩個勾選方向兩兩相容 → compatible，不是 swap。"""
        import json as _json
        from unittest.mock import patch

        result_1 = _mk_result(
            cid="C-1", direction_ids=["DIR-1", "DIR-2"], top1="DIR-1", top2="DIR-2"
        )
        result_2 = _mk_result(
            cid="C-2", direction_ids=["DIR-3", "DIR-4"], top1="DIR-3", top2="DIR-4"
        )
        # RD 勾的是兩條矛盾的 Top2
        picks = [
            PickedSelection(contradiction_id="C-1", picked_direction_ids=["DIR-2"]),
            PickedSelection(contradiction_id="C-2", picked_direction_ids=["DIR-4"]),
        ]
        req = ConsolidateRequest(
            project_id="proj-bug2-double",
            results=[result_1, result_2],
            picks=picks,
        )

        responses = iter(
            [
                # 1. compat check: DIR-2 vs DIR-4 → compatible (no pairs)
                _json.dumps({"pairs": []}),
                # 2. verdict_card
                _minimal_verdict_card_json(),
            ]
        )

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result", return_value=None
        ), patch(
            "app.agents.triz_solver._gc_orphan_directed_solutions", return_value=0
        ), patch(
            "app.services.brief_context.fetch_brief_context", return_value=EMPTY_CTX
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        assert cons.adopted_directions["C-1"].direction_id == "DIR-2"
        assert cons.adopted_directions["C-2"].direction_id == "DIR-4"
        # **核心驗收**：兩條都勾 Top2 但相容 → compatible，不是 resolved_with_swap
        assert cons.status == "compatible"
        assert cons.was_user_picked == {"C-1": "DIR-2", "C-2": "DIR-4"}

    def test_real_swap_still_returns_resolved_with_swap(self):
        """回歸測試：當「未 pinned 的矛盾」被系統 swap 時，status 必須仍是 resolved_with_swap。

        場景：C-1 被 RD pin 在 DIR-1；C-2 沒勾，系統因 conflict 把 C-2 從 DIR-3 swap 成 DIR-4。
        此情境下「真的有 swap」，status 應該保持 resolved_with_swap。
        """
        import json as _json
        from unittest.mock import patch

        result_1 = _mk_result(
            cid="C-1", direction_ids=["DIR-1", "DIR-2"], top1="DIR-1", top2="DIR-2"
        )
        result_2 = _mk_result(
            cid="C-2", direction_ids=["DIR-3", "DIR-4"], top1="DIR-3", top2="DIR-4"
        )
        picks = [
            PickedSelection(contradiction_id="C-1", picked_direction_ids=["DIR-1"]),
        ]
        req = ConsolidateRequest(
            project_id="proj-bug2-real-swap",
            results=[result_1, result_2],
            picks=picks,
        )

        responses = iter(
            [
                # 1. initial compat — DIR-1 vs DIR-3 conflict
                _json.dumps(
                    {
                        "pairs": [
                            {
                                "direction_a": "DIR-1",
                                "direction_b": "DIR-3",
                                "contradiction_a_id": "C-1",
                                "contradiction_b_id": "C-2",
                                "compatible": False,
                                "conflict_type": "module_overlap",
                                "reason": "...",
                            }
                        ]
                    }
                ),
                # 2. re-check after swap — clean
                _json.dumps({"pairs": []}),
                # 3. conflict report (status=resolved_with_swap path)
                _json.dumps(
                    {"suggestions": [], "integration_advice": "swap resolved"}
                ),
                # 4. verdict_card
                _minimal_verdict_card_json(),
            ]
        )

        def _llm_side_effect(*args, **kwargs):
            return next(responses)

        with patch(
            "app.agents.triz_solver.call_llm_json", side_effect=_llm_side_effect
        ), patch(
            "app.agents.triz_solver._persist_consolidation_result", return_value=None
        ), patch(
            "app.agents.triz_solver._gc_orphan_directed_solutions", return_value=0
        ), patch(
            "app.services.brief_context.fetch_brief_context", return_value=EMPTY_CTX
        ):
            resp = consolidate_solutions(req)

        cons = resp.consolidation
        assert cons.adopted_directions["C-1"].direction_id == "DIR-1"  # pinned
        assert cons.adopted_directions["C-2"].direction_id == "DIR-4"  # system swapped
        # 系統真的有 swap → status 必須仍是 resolved_with_swap
        assert cons.status == "resolved_with_swap"
        # C-1 是 user_picked（即使剛好等於 Top1），C-2 不是
        assert cons.was_user_picked == {"C-1": "DIR-1"}


# ===========================================================================
# PR2-Lite — 分數損失最小化候選池演算法
# ===========================================================================
#
# 對應 plans/triz-redesign.md PR2-Lite + docs/02-design/E5x--triz-consolidation-algorithm.md。
# 直接測試 _score_loss_optimized_swap 與整合測 consolidate_solutions，
# 覆蓋演算法的 4 個關鍵 case：
#   (a) 全相容          → status=compatible, rounds=1, 無 swap
#   (b) 一輪解決        → 換 loss 最小者
#   (c) 多輪解決        → 累計 swap 多次後 OK
#   (d) 池用盡          → status=conflict + exhausted_contradictions 列出全部


def _mk_scored_result(
    cid: str,
    dirs_with_scores: list[tuple[str, float]],
) -> ContradictionDirectionResult:
    """建立帶有 scored_directions 的測試 ContradictionDirectionResult。

    Args:
        cid: contradiction_id
        dirs_with_scores: list[(direction_id, weighted_total)]，依想要的池順序
    """
    dirs = [_mk_dir(did) for did, _ in dirs_with_scores]
    scored = [
        DirectionScore(direction_id=did, weighted_total=score)
        for did, score in dirs_with_scores
    ]
    return ContradictionDirectionResult(
        contradiction_id=cid,
        natural_description=f"contradiction {cid}",
        all_directions=dirs,
        scored_directions=scored,
        top1=dirs[0] if dirs else None,
        top2=dirs[1] if len(dirs) > 1 else None,
    )


class TestScoreLossOptimizedSwap:
    """直接測試 _score_loss_optimized_swap 純函式（mock LLM 相容性檢查）。"""

    def test_case_a_all_compatible_first_round(self):
        """(a) 各池首位天然相容 → 不需 swap，rounds=1。"""
        results = {
            "C-1": _mk_scored_result("C-1", [("D1.1", 95.0), ("D1.2", 80.0)]),
            "C-2": _mk_scored_result("C-2", [("D2.1", 90.0)]),
        }
        pools = {
            "C-1": results["C-1"].all_directions,
            "C-2": results["C-2"].all_directions,
        }
        # LLM 直接回相容
        with patch(
            "app.agents.triz_solver._check_compatibility",
            return_value=[],
        ):
            assignment, conflicts, exhausted, rounds = _score_loss_optimized_swap(
                pools, results
            )
        assert assignment["C-1"].direction_id == "D1.1"
        assert assignment["C-2"].direction_id == "D2.1"
        assert conflicts == []
        assert exhausted == set()
        assert rounds == 1

    def test_case_b_one_round_resolves_with_min_loss(self):
        """(b) 首位 C1↔C2 衝突；C1 池下一名損失 10、C2 損失 20 → 演算法應選 C1 換。"""
        # C1 池: D1.1(95) → D1.2(85), 損失 10
        # C2 池: D2.1(90) → D2.2(70), 損失 20
        results = {
            "C-1": _mk_scored_result("C-1", [("D1.1", 95.0), ("D1.2", 85.0)]),
            "C-2": _mk_scored_result("C-2", [("D2.1", 90.0), ("D2.2", 70.0)]),
        }
        pools = {
            "C-1": results["C-1"].all_directions,
            "C-2": results["C-2"].all_directions,
        }

        # Mock LLM: 第一輪 D1.1 ↔ D2.1 衝突，第二輪換成 D1.2 ↔ D2.1 → 相容
        call_count = {"n": 0}

        def _mock_compat(synthetic_results):
            call_count["n"] += 1
            # 取出當前 assignment 各代表方向
            current = {
                r.contradiction_id: (r.top1.direction_id if r.top1 else None)
                for r in synthetic_results
            }
            if current.get("C-1") == "D1.1" and current.get("C-2") == "D2.1":
                return [
                    CompatibilityResult(
                        direction_a="D1.1",
                        direction_b="D2.1",
                        contradiction_a_id="C-1",
                        contradiction_b_id="C-2",
                        compatible=False,
                        conflict_type="module_overlap",
                        reason="conflict",
                    )
                ]
            return []  # 換 C-1 後相容

        with patch(
            "app.agents.triz_solver._check_compatibility",
            side_effect=_mock_compat,
        ):
            assignment, conflicts, exhausted, rounds = _score_loss_optimized_swap(
                pools, results
            )
        assert conflicts == []
        # 演算法選了損失最小者：C-1 (10 < 20)
        assert assignment["C-1"].direction_id == "D1.2"
        assert assignment["C-2"].direction_id == "D2.1"
        assert exhausted == set()
        assert rounds == 2  # 第一輪偵測衝突、第二輪確認相容

    def test_case_c_multi_round_accumulated_swaps(self):
        """(c) 多輪 swap：先換損失最小者，新衝突再換次小者，最終相容。"""
        # C1: 95 → 85 (loss 10)
        # C2: 90 → 70 (loss 20)
        # C3: 88 (固定，只有 1 個方向)
        results = {
            "C-1": _mk_scored_result("C-1", [("D1.1", 95.0), ("D1.2", 85.0)]),
            "C-2": _mk_scored_result("C-2", [("D2.1", 90.0), ("D2.2", 70.0)]),
            "C-3": _mk_scored_result("C-3", [("D3.1", 88.0)]),
        }
        pools = {
            "C-1": results["C-1"].all_directions,
            "C-2": results["C-2"].all_directions,
            "C-3": results["C-3"].all_directions,
        }

        def _mock_compat(synthetic_results):
            current = {
                r.contradiction_id: (r.top1.direction_id if r.top1 else None)
                for r in synthetic_results
            }
            # Round 1: 全首位 → C1↔C2 衝突
            if (
                current.get("C-1") == "D1.1"
                and current.get("C-2") == "D2.1"
            ):
                return [
                    CompatibilityResult(
                        direction_a="D1.1",
                        direction_b="D2.1",
                        contradiction_a_id="C-1",
                        contradiction_b_id="C-2",
                        compatible=False,
                        conflict_type="module_overlap",
                        reason="r1",
                    )
                ]
            # Round 2: C1 換 D1.2 後 → C2↔C3 新衝突
            if current.get("C-1") == "D1.2" and current.get("C-2") == "D2.1":
                return [
                    CompatibilityResult(
                        direction_a="D2.1",
                        direction_b="D3.1",
                        contradiction_a_id="C-2",
                        contradiction_b_id="C-3",
                        compatible=False,
                        conflict_type="module_overlap",
                        reason="r2",
                    )
                ]
            # Round 3: C2 也換為 D2.2 後 → 全相容
            return []

        with patch(
            "app.agents.triz_solver._check_compatibility",
            side_effect=_mock_compat,
        ):
            assignment, conflicts, exhausted, rounds = _score_loss_optimized_swap(
                pools, results
            )
        assert conflicts == []
        assert assignment["C-1"].direction_id == "D1.2"
        # C3 只有 1 個方向，新衝突 collect 的 cids = {C-2, C-3}；
        # C-3 池只有 1 個方向 → exhausted；C-2 池還有 D2.2 可換 → 選 C-2
        assert assignment["C-2"].direction_id == "D2.2"
        assert assignment["C-3"].direction_id == "D3.1"
        # C-3 在第 2 輪被加入 exhausted（因為池只有 1 個方向）
        assert "C-3" in exhausted
        assert rounds == 3

    def test_case_d_all_exhausted_returns_conflict(self):
        """(d) 衝突方池都只有 1 個方向 → 演算法卡住，回 conflict + exhausted。"""
        results = {
            "C-1": _mk_scored_result("C-1", [("D1.1", 95.0)]),
            "C-2": _mk_scored_result("C-2", [("D2.1", 90.0)]),
        }
        pools = {
            "C-1": results["C-1"].all_directions,
            "C-2": results["C-2"].all_directions,
        }

        def _mock_compat(_synthetic_results):
            return [
                CompatibilityResult(
                    direction_a="D1.1",
                    direction_b="D2.1",
                    contradiction_a_id="C-1",
                    contradiction_b_id="C-2",
                    compatible=False,
                    conflict_type="module_overlap",
                    reason="stuck",
                )
            ]

        with patch(
            "app.agents.triz_solver._check_compatibility",
            side_effect=_mock_compat,
        ):
            assignment, conflicts, exhausted, rounds = _score_loss_optimized_swap(
                pools, results
            )
        # 池用盡 → conflict 仍存在，exhausted 含 C-1 + C-2
        assert len(conflicts) == 1
        assert conflicts[0].compatible is False
        assert "C-1" in exhausted
        assert "C-2" in exhausted
        # 演算法在 1 輪內就偵測到所有衝突方池用盡，立即終止
        assert rounds == 1
        # assignment 仍是初始首位（沒換）
        assert assignment["C-1"].direction_id == "D1.1"
        assert assignment["C-2"].direction_id == "D2.1"


class TestBuildCandidatePool:
    """測試 _build_candidate_pool 排序與 dedupe 邏輯。"""

    def test_picks_sorted_by_score_descending(self):
        """使用者勾的 2 個方向依分數降冪排序。"""
        result = _mk_scored_result(
            "C-1",
            [("D-A", 70.0), ("D-B", 95.0), ("D-C", 80.0)],
        )
        pick = PickedSelection(
            contradiction_id="C-1",
            picked_direction_ids=["D-A", "D-B", "D-C"],
        )
        pool = _build_candidate_pool(pick, result, None)
        ids = [d.direction_id for d in pool]
        assert ids == ["D-B", "D-C", "D-A"]  # 95 > 80 > 70

    def test_empty_picks_fallback_to_top1_top2(self):
        """無 picks → fallback 使用 top1 + top2（用於 single-contradiction / 測試路徑）。"""
        result = _mk_scored_result(
            "C-1",
            [("D-A", 95.0), ("D-B", 80.0), ("D-C", 70.0)],
        )
        pool = _build_candidate_pool(None, result, None)
        ids = [d.direction_id for d in pool]
        assert ids == ["D-A", "D-B"]

    def test_intra_conflict_subset_promoted_to_front(self):
        """同矛盾衝突報告中 max_compatible_subset 的方向應排前面（內部仍依分數）。"""
        result = _mk_scored_result(
            "C-1",
            [("D-A", 95.0), ("D-B", 85.0), ("D-C", 80.0)],
        )
        pick = PickedSelection(
            contradiction_id="C-1",
            picked_direction_ids=["D-A", "D-B", "D-C"],
        )
        # 假設 intra-conflict 找出 {D-B, D-C} 是 max compatible subset
        intra = IntraContradictionCompatibility(
            contradiction_id="C-1",
            picked_direction_ids=["D-A", "D-B", "D-C"],
            pairwise_results=[],
            max_compatible_subsets=[["D-B", "D-C"]],
            has_conflict=True,
            recommendation="D-A 與 D-B 衝突",
        )
        pool = _build_candidate_pool(pick, result, intra)
        ids = [d.direction_id for d in pool]
        # D-B 與 D-C 排前 (subset 內部依分數降冪：D-B=85 > D-C=80)，D-A 排後
        assert ids[0] == "D-B"
        assert ids[1] == "D-C"
        assert ids[2] == "D-A"
