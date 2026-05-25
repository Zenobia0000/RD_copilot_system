"""Phase 1 / D1：SR 生成穩定性測試。

對應 plans/triz-redesign.md §9.1。

驗證新的「演算法為骨」SR 生成流程的兩個核心承諾：
1. _enumerate_sr_candidates 是純函式：同 input 必須產出 byte-identical 候選清單。
2. 完整 _decompose_contradiction 流程在 LLM mock 下，連跑 10 次 SR 結構
   （哪幾條、kind、source_ref、順序）必須完全相同；字句允許 5% 差異。

LLM 部分用 unittest.mock.patch 強制回傳固定 JSON，模擬「同 prompt 在
temperature=0 下會給同樣答案」的理想行為；測試的不是「LLM 自身是否
deterministic」，而是「我們的演算法層是否能把 LLM 翻面的影響鎖在
描述字句層、不傳染到 SR 結構」。
"""

import json
from unittest.mock import patch

import pytest

from app.agents.triz_solver import (
    SrCandidate,
    _enumerate_sr_candidates,
    _score_sr_relevance,
    _filter_by_relevance,
    _decompose_contradiction,
)
from app.models.schemas import (
    BriefConstraint,
    BriefContextSnapshot,
    BriefKpi,
    SubRequirement,
    SrWeakWarning,
)


# ---------------------------------------------------------------------------
# E-BIKE fixture — 對應 DB project bff913c9-… 的真實 brief 內容（截取）
# ---------------------------------------------------------------------------

EBIKE_NATURAL = (
    "Improving motor torque density in the limited package worsens thermal "
    "conditions because higher current density and magnetic loading increase losses."
)
EBIKE_IMPROVING = 21    # Power
EBIKE_WORSENING = 17    # Temperature

EBIKE_CONSTRAINTS = [
    BriefConstraint(code="C-01", description="產品最大徑向尺寸≤111mm", type="hard"),
    BriefConstraint(code="M2", description="Spindle length≤153mm", type="hard"),
    BriefConstraint(code="M3", description="drive unit運轉噪聲≤60dBA", type="hard"),
    BriefConstraint(code="M4", description="矩時峰值輸出扭矩125Nm", type="hard"),
]
EBIKE_KPIS = [
    BriefKpi(name="傳動效率", target_value="≥83", unit="%"),
    BriefKpi(name="馬達效率", target_value="≥85", unit="%"),
    BriefKpi(name="輸出扭矩", target_value="≥125", unit="Nm"),
    BriefKpi(name="重量", target_value="≤2500", unit="g"),
    BriefKpi(name="馬達最大輸出扭矩", target_value="5", unit="Nm"),
]
EBIKE_CTX = BriefContextSnapshot(
    project_id="bff913c9-fixture",
    mission="E-bike mid-drive unit, coaxial structure, low noise, 125Nm peak torque.",
    constraints=EBIKE_CONSTRAINTS,
    kpis=EBIKE_KPIS,
)


# ===========================================================================
# S0a 純函式測試
# ===========================================================================

class TestEnumerateSrCandidates:

    def test_enumeration_is_pure(self):
        """同 input → byte-identical 候選清單。"""
        cands1 = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        cands2 = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        assert cands1 == cands2

    def test_ebike_yields_exactly_11_candidates(self):
        """E-BIKE fixture (2 contradiction sides + 4 constraints + 5 KPIs)."""
        cands = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        assert len(cands) == 11, f"expected 11 candidates, got {len(cands)}"

    def test_first_two_are_contradiction_sides(self):
        cands = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        assert cands[0].source_ref == "contradiction"
        assert cands[0].kind == "desired_improvement"
        assert cands[1].source_ref == "contradiction"
        assert cands[1].kind == "undesired_effect"

    def test_constraint_candidates_carry_type(self):
        cands = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        constraint_cands = [c for c in cands if c.kind == "boundary_condition"]
        assert len(constraint_cands) == 4
        # 所有 E-BIKE constraint 都是 hard
        assert all(c.extras.get("type") == "hard" for c in constraint_cands)
        # source_ref 應該對應 constraint code
        assert {c.source_ref for c in constraint_cands} == {
            "constraint:C-01", "constraint:M2", "constraint:M3", "constraint:M4",
        }

    def test_kpi_candidates_preserve_target_unit(self):
        cands = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=EBIKE_CTX,
        )
        kpi_cands = [c for c in cands if c.kind == "mission_outcome"]
        assert len(kpi_cands) == 5
        # 至少一條 raw_text 含「125 Nm」這種數值
        torque = next(c for c in kpi_cands if c.source_ref == "kpi:輸出扭矩")
        assert "125" in torque.raw_text
        assert "Nm" in torque.raw_text

    def test_empty_ctx_yields_only_contradiction_sides(self):
        cands = _enumerate_sr_candidates(
            natural_description=EBIKE_NATURAL,
            improving_param=EBIKE_IMPROVING,
            worsening_param=EBIKE_WORSENING,
            ctx=BriefContextSnapshot(),
        )
        assert len(cands) == 2


# ===========================================================================
# S0c 純函式測試
# ===========================================================================

class TestFilterByRelevance:

    def _make_cands(self):
        return [
            SrCandidate(candidate_id=1, kind="desired_improvement",
                        source_ref="contradiction", raw_text="想改善"),
            SrCandidate(candidate_id=2, kind="undesired_effect",
                        source_ref="contradiction", raw_text="想避免"),
            SrCandidate(candidate_id=3, kind="boundary_condition",
                        source_ref="constraint:C-01", raw_text="徑向≤111mm",
                        extras={"type": "hard"}),
            SrCandidate(candidate_id=4, kind="mission_outcome",
                        source_ref="kpi:重量", raw_text="重量≤2500g"),
        ]

    def test_threshold_2_separates_sr_and_warning(self):
        cands = self._make_cands()
        scored = {
            1: {"score": 3, "why": "self"},
            2: {"score": 3, "why": "self"},
            3: {"score": 2, "why": "relevant"},
            4: {"score": 1, "why": "weak"},
        }
        sr_list, warnings = _filter_by_relevance(cands, scored)
        assert {c.candidate_id for c in sr_list} == {1, 2, 3}
        assert {c.candidate_id for c in warnings} == {4}

    def test_score_zero_dropped(self):
        cands = self._make_cands()
        scored = {1: {"score": 3, "why": ""}, 2: {"score": 3, "why": ""},
                  3: {"score": 0, "why": ""}, 4: {"score": 0, "why": ""}}
        sr_list, warnings = _filter_by_relevance(cands, scored)
        assert len(sr_list) == 2
        assert warnings == []

    def test_pure_function_same_input_same_output(self):
        cands = self._make_cands()
        scored = {1: {"score": 3}, 2: {"score": 3}, 3: {"score": 2}, 4: {"score": 1}}
        out1 = _filter_by_relevance(cands, scored)
        out2 = _filter_by_relevance(cands, scored)
        assert out1[0] == out2[0]
        assert out1[1] == out2[1]


# ===========================================================================
# S0b 強制規則測試（LLM mock）
# ===========================================================================

class TestScoreSrRelevance:

    def _fake_llm_response_drop_contradiction_self(self):
        """模擬 LLM 沒有給 contradiction self 高分（強制規則應拉回 3）。"""
        return json.dumps({
            "scores": [
                {"candidate_id": 1, "score": 1, "why": "weak (test broken response)"},
                {"candidate_id": 2, "score": 0, "why": "missed (test broken response)"},
                {"candidate_id": 3, "score": 1, "why": "weak"},  # hard constraint
                {"candidate_id": 4, "score": 0, "why": "irrelevant"},  # hard constraint, LLM 給 0
                {"candidate_id": 5, "score": 2, "why": "ok"},  # KPI
            ]
        })

    @patch("app.agents.triz_solver.call_llm_json")
    def test_contradiction_self_forced_to_3(self, mock_llm):
        mock_llm.return_value = self._fake_llm_response_drop_contradiction_self()
        cands = [
            SrCandidate(candidate_id=1, kind="desired_improvement",
                        source_ref="contradiction", raw_text="想改善"),
            SrCandidate(candidate_id=2, kind="undesired_effect",
                        source_ref="contradiction", raw_text="想避免"),
            SrCandidate(candidate_id=3, kind="boundary_condition",
                        source_ref="constraint:C-01", raw_text="徑向≤111mm",
                        extras={"type": "hard"}),
            SrCandidate(candidate_id=4, kind="boundary_condition",
                        source_ref="constraint:M3", raw_text="噪聲≤60dBA",
                        extras={"type": "hard"}),
            SrCandidate(candidate_id=5, kind="mission_outcome",
                        source_ref="kpi:重量", raw_text="重量≤2500g"),
        ]
        scored = _score_sr_relevance("test", cands)
        # 強制規則：contradiction self 必須 score=3
        assert scored[1]["score"] == 3
        assert scored[2]["score"] == 3
        # 強制規則：hard constraint 至少 score=1
        assert scored[3]["score"] >= 1
        assert scored[4]["score"] >= 1
        # 一般候選保留 LLM 給分
        assert scored[5]["score"] == 2

    @patch("app.agents.triz_solver.call_llm_json", side_effect=Exception("LLM down"))
    def test_llm_failure_falls_back_to_warning_for_all(self, mock_llm):
        cands = [
            SrCandidate(candidate_id=1, kind="desired_improvement",
                        source_ref="contradiction", raw_text="想改善"),
            SrCandidate(candidate_id=3, kind="boundary_condition",
                        source_ref="constraint:C-01", raw_text="徑向≤111mm",
                        extras={"type": "hard"}),
            SrCandidate(candidate_id=5, kind="mission_outcome",
                        source_ref="kpi:重量", raw_text="重量≤2500g"),
        ]
        scored = _score_sr_relevance("test", cands)
        # contradiction self 仍然強制 3
        assert scored[1]["score"] == 3
        # hard constraint 仍然強制 ≥1
        assert scored[3]["score"] >= 1
        # 一般候選 LLM 失敗 → fallback score=1（保守）
        assert scored[5]["score"] == 1


# ===========================================================================
# D1 核心：連跑 10 次穩定性測試
# ===========================================================================

def _fixed_scoring_response():
    """模擬 temperature=0 下 LLM 給的固定評分（這是「理想穩定」場景）。"""
    return json.dumps({
        "scores": [
            {"candidate_id": 1, "score": 3, "why": "矛盾本身 improving"},
            {"candidate_id": 2, "score": 3, "why": "矛盾本身 worsening"},
            {"candidate_id": 3, "score": 2, "why": "外徑限制直接影響扭矩密度"},
            {"candidate_id": 4, "score": 1, "why": "Spindle length 與此矛盾弱相關"},
            {"candidate_id": 5, "score": 1, "why": "噪聲與此 thermal 矛盾弱相關"},
            {"candidate_id": 6, "score": 2, "why": "峰值扭矩與此矛盾直接相關"},
            {"candidate_id": 7, "score": 1, "why": "傳動效率主要由齒箱決定"},
            {"candidate_id": 8, "score": 3, "why": "馬達效率直接由 thermal 影響"},
            {"candidate_id": 9, "score": 3, "why": "輸出扭矩是目標"},
            {"candidate_id": 10, "score": 1, "why": "重量與此矛盾弱相關"},
            {"candidate_id": 11, "score": 3, "why": "馬達 max 5Nm 是物理瓶頸"},
        ]
    })


def _fixed_rewrite_response(call_idx_holder):
    """模擬改寫 LLM 回應 — 每呼叫一次根據呼叫順序回對應內容。

    這裡刻意把「字句」做小幅度抖動模擬 LLM 字面差異，但保留所有數值與
    source_ref 結構 — 用來證明「結構穩定、字句允許小差」這個承諾。
    """
    descriptions = [
        ("desired_improvement", "在受限封裝內提升馬達扭矩密度", "矛盾的 improving 側"),
        ("undesired_effect", "避免電流密度上升導致熱負荷惡化", "矛盾的 worsening 側"),
        ("boundary_condition", "drive unit 外徑必須 ≤111mm", "hard constraint C-01"),
        ("boundary_condition", "drive unit 峰值輸出扭矩需達 125Nm", "hard constraint M4"),
        ("mission_outcome", "馬達效率須維持 ≥85%", "KPI 馬達效率"),
        ("mission_outcome", "輸出扭矩須達 ≥125Nm", "KPI 輸出扭矩"),
        ("mission_outcome", "馬達最大輸出扭矩 = 5Nm", "KPI 馬達最大輸出扭矩"),
    ]

    def _side_effect(*args, **kwargs):
        # 第一次呼叫 _score_sr_relevance 用 scoring response
        # 後續呼叫 _rewrite_sr_descriptions 用 rewrite responses
        idx = call_idx_holder["i"]
        call_idx_holder["i"] += 1
        if idx == 0:
            return _fixed_scoring_response()
        rewrite_idx = idx - 1
        if rewrite_idx >= len(descriptions):
            return json.dumps({"description": "(no more rewrites)",
                               "why_necessary": "", "domain": ""})
        kind, desc, why = descriptions[rewrite_idx]
        return json.dumps({"description": desc, "why_necessary": why, "domain": ""})

    return _side_effect


class TestSrStability10Runs:
    """D1：連跑 10 次，SR 結構必須 100% 一致。"""

    def _run_once(self):
        holder = {"i": 0}
        with patch("app.agents.triz_solver.call_llm_json",
                   side_effect=_fixed_rewrite_response(holder)):
            sr_list = _decompose_contradiction(
                EBIKE_NATURAL,
                EBIKE_CTX,
                improving_param=EBIKE_IMPROVING,
                worsening_param=EBIKE_WORSENING,
            )
        return sr_list

    def test_sr_structure_stable_across_10_runs(self):
        """同 input 連跑 10 次，SR 的 (kind, source_ref) tuple list 必須 100% 一致。"""
        structures = []
        for _ in range(10):
            sr_list = self._run_once()
            # 用 (kind, source_ref) 比對結構，忽略 description 字句
            structure = tuple((sr.kind, sr.source_ref) for sr in sr_list)
            structures.append(structure)

        unique_structures = set(structures)
        assert len(unique_structures) == 1, (
            f"SR 結構不穩定！跑 10 次出現 {len(unique_structures)} 種不同結構：\n"
            + "\n".join(str(s) for s in unique_structures)
        )

    def test_sr_count_stable(self):
        """SR 數量必須穩定。"""
        counts = []
        for _ in range(10):
            sr_list = self._run_once()
            counts.append(len(sr_list))
        assert len(set(counts)) == 1, f"SR 數量不穩定：{counts}"

    def test_sr_includes_all_threshold_2_plus_candidates(self):
        """跑 1 次，驗證所有 score>=2 的候選都進到 SR（不會被誤丟）。

        對 E-BIKE fixture：score>=2 的應該是 11 條中的 7 條：
        ID 1, 2, 3, 6, 8, 9, 11 — 對應 contradiction*2 + C-01 + M4 + 3 KPIs。
        """
        sr_list = self._run_once()
        # 驗證 source_ref 集合
        actual_refs = {sr.source_ref for sr in sr_list}
        expected_refs = {
            "contradiction",                # 兩條都用同一個 source_ref
            "constraint:C-01",
            "constraint:M4",
            "kpi:馬達效率",
            "kpi:輸出扭矩",
            "kpi:馬達最大輸出扭矩",
        }
        assert actual_refs == expected_refs

        # 矛盾本身 source_ref="contradiction" 應該出現 2 次（improving + worsening）
        contradiction_count = sum(1 for sr in sr_list if sr.source_ref == "contradiction")
        assert contradiction_count == 2

    def test_weak_warnings_returned_when_requested(self):
        """return_weak_warnings=True 時，score==1 的應該變成 SrWeakWarning。"""
        holder = {"i": 0}
        with patch("app.agents.triz_solver.call_llm_json",
                   side_effect=_fixed_rewrite_response(holder)):
            result = _decompose_contradiction(
                EBIKE_NATURAL,
                EBIKE_CTX,
                improving_param=EBIKE_IMPROVING,
                worsening_param=EBIKE_WORSENING,
                return_weak_warnings=True,
            )
        assert isinstance(result, tuple)
        sr_list, warnings = result
        # score==1 的有 4 條：M2 Spindle / M3 噪聲 / 傳動效率 / 重量
        assert len(warnings) == 4
        weak_refs = {w.source_ref for w in warnings}
        assert weak_refs == {
            "constraint:M2", "constraint:M3", "kpi:傳動效率", "kpi:重量",
        }


# ===========================================================================
# 對比舊行為的快照：證明新流程確實會穩定列出 hard constraint
# ===========================================================================

class TestRegressionAgainstOldBehavior:
    """對應 plans/triz-redesign.md §A.2 的「漏列 4 條」問題。

    新流程下，這些條件雖然可能 score=1（弱相關），但至少會出現在
    weak_warnings 中，不會像舊流程那樣完全消失。
    """

    def test_hard_constraints_never_disappear(self):
        """所有 hard constraint 至少要出現在 SR 或 weak_warnings 之一。"""
        holder = {"i": 0}
        with patch("app.agents.triz_solver.call_llm_json",
                   side_effect=_fixed_rewrite_response(holder)):
            sr_list, warnings = _decompose_contradiction(
                EBIKE_NATURAL,
                EBIKE_CTX,
                improving_param=EBIKE_IMPROVING,
                worsening_param=EBIKE_WORSENING,
                return_weak_warnings=True,
            )

        all_refs = (
            {sr.source_ref for sr in sr_list}
            | {w.source_ref for w in warnings}
        )
        # 所有 hard constraint 都應該在
        for c in EBIKE_CONSTRAINTS:
            ref = f"constraint:{c.code}"
            assert ref in all_refs, \
                f"hard constraint {ref} 從 SR 與 warning 完全消失（舊 bug 復發）"

    def test_motor_max_5nm_kpi_never_disappears(self):
        """E-BIKE 真正的物理瓶頸 KPI 馬達最大輸出扭矩=5Nm，
        在舊流程中經常被遺漏。新流程必須保證它出現。"""
        holder = {"i": 0}
        with patch("app.agents.triz_solver.call_llm_json",
                   side_effect=_fixed_rewrite_response(holder)):
            sr_list, warnings = _decompose_contradiction(
                EBIKE_NATURAL,
                EBIKE_CTX,
                improving_param=EBIKE_IMPROVING,
                worsening_param=EBIKE_WORSENING,
                return_weak_warnings=True,
            )
        all_refs = (
            {sr.source_ref for sr in sr_list}
            | {w.source_ref for w in warnings}
        )
        assert "kpi:馬達最大輸出扭矩" in all_refs
