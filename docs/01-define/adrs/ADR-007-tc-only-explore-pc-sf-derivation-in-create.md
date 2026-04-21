# ADR-007: Explore 階段矛盾識別限縮為 TC-only；PC/SF 自 TC 派生為子項

- **Status:** Accepted → **Amended (Plan B)**
- **Date:** 2026-04-15 (初版) · 2026-04-21 (Plan B 修訂)
- **Deciders:** Sunny (PO) · Backend AI Agents Team
- **Supersedes:** 部分 ADR-002（TC/PC/SF 三型並列識別）
- **Amended by:** Plan B — 階層式 TC 樹狀結構 (`plans/plan-b-hierarchical-tc-tree.md`)

## Context

分層 Drill-Down 診斷（L1 現象 / L2 根因 / L3 結構）現狀：Explore 階段矛盾識別可輸出 `type ∈ {TC, PC, SF}`，Create 階段依 `type` 互斥選擇傳參給 `solve_triz_layered`。結果任何單一 type 都無法跑出完整三層：

| Explore 選擇 | L1 | L2 | L3 |
|---|---|---|---|
| TC | ✅ | ⚠️ 需再分解 | ❌ |
| PC | ❌ | ✅ | ❌ |
| SF | ❌ | ❌ | ✅ |

**根因**：TRIZ 方法論中 TC 是母體（兩個具名參數、資訊最豐富的表層描述），PC/SF 是 TC 的**變換衍生**（PC = Separation Principle 分解、SF = 結構再表述）。Explore 若直接輸出 PC/SF，就失去母體錨點，L1 無矩陣可查、跨層回溯連結（`parent_contradiction_id`）斷裂。

## Decision

### 原始 Decision (v1)

> PC/SF 派生產物不回寫 `contradictions` 表，僅在 Create 階段 solve response 帶回。

### Plan B 修訂 (v2, 2026-04-21)

使用者反饋扁平三區塊不符需求，要求改為**階層式 TC 樹狀結構**：

1. **Explore 階段**：`formalize_contradiction` 強制輸出 `type="TC"`。若 LLM 無法映射到兩個 `improving/worsening_param`，拒絕並要求重述（不再 downgrade 至 PC/SF）。
2. **Explore 階段自動派生子項**：TC 識別成功後，**立即並行派生** PC 和 SF 子項：
   - PC ← `POST /contradictions/{cid}/decompose`（多個 child PC rows，帶 `parent_contradiction_id`）
   - SF ← `POST /contradictions/{cid}/derive-sf`（單個 child SF row，帶 `parent_contradiction_id`）
3. **派生產物回寫** `contradictions` 表，以 `parent_contradiction_id` 連結至父 TC，形成樹狀結構。
4. **前端 UI**：TC 為唯一頂層根節點，手動新增只能加 TC。PC/SF 以巢狀子卡片形式顯示在父 TC 下方，孤兒 PC/SF 忽略不顯示。
5. **Create 階段**：`solve_triz_layered` 入口仍可就地派生缺失的 PC/SF。

## Consequences

### Positive
- L1/L2/L3 三層在任一矛盾上皆可完整跑通
- Explore UX 呈現清晰的 TC → PCs + SF 樹狀結構，符合 TRIZ 方法論層次
- 使用者可在 Explore 階段直接看到完整矛盾分解，不必等到 Create 階段
- Fix 根因而非症狀，與 E3 Appendix B（Forward TRIZ Solver）語意一致

### Negative / Trade-off
- LLM 無法映射到 39 參數時，Explore 需回退到 Socratic 追問，延長 Diverge 時間
- 每個 TC 識別後觸發兩次額外 LLM 呼叫（decompose + derive-sf），約增加 4-8 秒/矛盾
- 派生產物回寫 DB，需管理父子一致性（父 TC 參數變更時子項標記為 stale）

### Neutral
- 舊資料（DB 中無 `parent_contradiction_id` 的孤兒 PC/SF row）前端忽略不顯示，不強制 migration
- Schema `sf_substance_1/2/field`、`physical_contradiction` 欄位保留，用於 SF 子項

## Implementation Plan

| # | 模組 | 變更 | 狀態 |
|---|---|---|---|
| 1 | `backend/app/prompts/analyst.py` | 還原 TC-only prompt | ✅ Done |
| 2 | `backend/app/agents/analyst.py` | 強制 `type="TC"` coercion；新增 `derive_su_field_from_tc()` | ✅ Done |
| 3 | `backend/app/models/schemas.py` | 新增 `ContradictionDeriveSFRequest/Response` | ✅ Done |
| 4 | `backend/app/routers/contradictions.py` | 新增 `POST /contradictions/{cid}/derive-sf` 端點 | ✅ Done |
| 5 | `src/lib/api.ts` | 新增 `contradictionDeriveSF` API 函式 | ✅ Done |
| 6 | `src/components/explore/ContradictionTab.tsx` | TC-only 頂層：移除扁平 PC/SF 區塊，新增 `maybeAutoDeriveChildSF`，`handleAiReidentify` 並行派生 PC+SF | ✅ Done |
| 7 | `src/components/explore/DecomposedSFCard.tsx` | 新建 SF 子卡片元件（顯示 S1/S2/F/interaction/completeness） | ✅ Done |
| 8 | `src/components/explore/DecomposedChildrenList.tsx` | 擴充支援 PC + SF 雙區塊顯示 | ✅ Done |
| 9 | `src/pages/Create.tsx` | 移除 `cType` 互斥閘門，無條件傳 `improvingParam/worseningParam` | ✅ Done (prior) |
| 10 | Tests | 更新相關測試情境 | Pending |

## Rollout

- **Phase 1（已完成）**：前端 Fix 移除閘門 + 後端 formalize enforce TC-only
- **Phase 2（已完成）**：`derive_su_field_from_tc` + `/derive-sf` 端點 + `decompose` 端點
- **Phase 3（已完成）**：Plan B 前端重構 — 階層式 TC 樹狀結構 UI
- **Phase 4（待辦）**：整合測試 + E3/E5 docs 更新
