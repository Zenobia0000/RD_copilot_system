# ADR-007: Explore 階段矛盾識別限縮為 TC-only；PC/SF 於 Create 階段自 TC 派生

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** Sunny (PO) · Backend AI Agents Team
- **Supersedes:** 部分 ADR-002（TC/PC/SF 三型並列識別）

## Context

分層 Drill-Down 診斷（L1 現象 / L2 根因 / L3 結構）現狀：Explore 階段矛盾識別可輸出 `type ∈ {TC, PC, SF}`，Create 階段依 `type` 互斥選擇傳參給 `solve_triz_layered`。結果任何單一 type 都無法跑出完整三層：

| Explore 選擇 | L1 | L2 | L3 |
|---|---|---|---|
| TC | ✅ | ⚠️ 需再分解 | ❌ |
| PC | ❌ | ✅ | ❌ |
| SF | ❌ | ❌ | ✅ |

**根因**：TRIZ 方法論中 TC 是母體（兩個具名參數、資訊最豐富的表層描述），PC/SF 是 TC 的**變換衍生**（PC = Separation Principle 分解、SF = 結構再表述）。Explore 若直接輸出 PC/SF，就失去母體錨點，L1 無矩陣可查、跨層回溯連結（`parent_contradiction_id`）斷裂。

## Decision

1. **Explore 階段**：`formalize_contradiction` 強制輸出 `type="TC"`。若 LLM 無法映射到兩個 `improving/worsening_param`，拒絕並要求重述（不再 downgrade 至 PC/SF）。
2. **Create 階段**：在 `solve_triz_layered` 入口，若 request 未帶 PC/SF 欄位，**就地派生**：
   - PC ← `analyst.decompose_tc_to_pcs(tc)` 
   - SF ← 新增 `analyst.derive_su_field_from_tc(tc)`（若 LLM 推不出有意義的 S1/S2/F 則 L3 以 warning 降級，不影響 L1/L2）
3. **派生產物不回寫** `contradictions` 表（避免污染 Explore 的 source of truth）；僅在本次 solve response 帶回，供 UI 顯示分層結果。
4. **前端 `Create.tsx`** 移除 `cType === 'TC' ? ... : undefined` 互斥閘門，`improving/worsening_param` 無條件傳出。

## Consequences

### Positive
- L1/L2/L3 三層在任一矛盾上皆可完整跑通
- Explore UX 簡化（只列 TC、可排序可比較），吻合 5D 的 Diverge 定位
- Fix 根因而非症狀，與 E3 Appendix B（Forward TRIZ Solver）語意一致

### Negative / Trade-off
- LLM 無法映射到 39 參數時，Explore 需回退到 Socratic 追問，延長 Diverge 時間
- 新增 `derive_su_field_from_tc` 一次 LLM 呼叫（加約 2-4 秒/矛盾）

### Neutral
- 舊資料（DB 中 `type ∈ {PC, SF}` 的舊 row）仍可讀取；前端顯示加相容層，不強制 migration
- Schema `sf_substance_1/2/field`、`physical_contradiction` 欄位保留（標 deprecated in Explore，仍用於 Create 派生結果快取於 memory）

## Implementation Plan

| # | 模組 | 變更 |
|---|---|---|
| 1 | `backend/app/prompts/analyst.py` | 移除 TC/PC/SF 三選一分類段落；改為 TC-only prompt，若無法映射就回傳 `type=null + rationale` |
| 2 | `backend/app/agents/analyst.py:formalize_contradiction` | 強制 `type="TC"` 或 reject；移除 PC downgrade 分支；新增 `derive_su_field_from_tc(TrizLookupRequest) -> SuFieldModel` |
| 3 | `backend/app/agents/triz_solver.py:solve_triz_layered` | 入口加派生步驟：若 SF 欄位缺，呼叫 `derive_su_field_from_tc` 補上；若 PC 缺，L2 內呼 `decompose_tc_to_pcs` |
| 4 | `backend/app/models/schemas.py` | `ContradictionFormalizeResponse.type: Literal["TC"]`；標註 `physical_contradiction/sf_*` 為 deprecated in Explore-output |
| 5 | `src/pages/Create.tsx:287-292` | 移除 `cType === 'TC'/'SF'` 閘門，改為無條件傳 `improvingParam/worseningParam` |
| 6 | Tests | 更新 `analyst` pilot + `triz-solver` pilot 測試情境；新增 TC→SF 派生 pilot |
| 7 | Docs | E3 Appendix B 新增 "TC-Only Contract" 段；E5 API spec 更新 request schema；E3x interaction flow 更新 scenario 1 |

## Rollout

- **Phase 1（即刻）**：前端 Fix 移除閘門 + 後端 formalize enforce TC-only
- **Phase 2（同 PR）**：`derive_su_field_from_tc` + `solve_triz_layered` 入口派生
- **Phase 3（次週）**：舊資料相容性驗證 + E3/E5 docs 更新
