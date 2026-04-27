# Explore 階段 TC→多PC 分解 WBS（Explore · Tab 矛盾識別）

> **版本**：1.0 | **日期**：2026-04-09 | **狀態**：Draft · 待啟動 | **Owner**：Explore FE + Backend Agents
>
> **⚠️ Phase B 退役通知 (2026-04-27)**：本 WBS §9.6（Phase B adoption 相容性）和 §7.0（Phase B 採納 UX）中的 Phase B 相關任務不再需要。**Phase B 已於 v9 退役**，由 SIM 矩陣（ADR-008 D5）和 CCI（ADR-008 D4）前置覆蓋。相關工作項標記為 N/A。
> **範圍**：Explore 頁矛盾識別階段，當 AI 識別出 TC 後由 **L1 critic** 判斷是否觸發 **TC→多 PC 深挖**，每個 PC 自動附掛 **分離原則 (16 類)**，結果以 `parent_contradiction_id` FK 方式寫入 `contradictions` 表並以巢狀卡片呈現。
> **對齊文件**：
> - `docs/e2e/module/Forward_TRIZ_Solver_Architecture.md` v1.1（§6.2 L2 觸發條件、§6.7 `deepen_link` 契約、§7.0 `solve_triz_layered` 時序）
> - `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md`（L1/L2/L3 drill-down 方法論）
> - `docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md`（§1.1 多分離原則同時適用）
>
> **TRIZ 知識庫來源**（`rd_assistant_design_system/triz_knowledge_base/`）：
> - **`04_separation_principles.md`（8 KB，4 大類 × 4 策略 = 16 項，含物理本質 + 跨域範例）— 本 WBS §1.1 的權威來源** ★
> - `01_39_parameters.md`（3 KB，39 工程參數）— 本 WBS §3.1 TC_TO_MULTI_PC_DECOMPOSITION prompt 注入；對應既有 `load_39_parameters()`
> - `03_40_principles.md`（17 KB，40 發明原理）— 本 WBS §3.1 注入（給 LLM 理解 separation 與 40 原理對應）+ 9.1.2 hint prompt；對應既有 `load_40_principles()`
> - `06_tc_pc_sf_flows.md`（10 KB）— 既有 TC/PC/SF 流程架構；本 WBS §3.1 / §9.1 prompt 設計必須對齊
> - `07_tc_pc_sf_differences.md`（5 KB）— **§1.1 PC 判定三要點 + §3 TC/PC 共用 `TRIZ_SOLVER_SYSTEM`**；本 WBS §2 critic 第五條規則 + §3.1 prompt 防退化都源自此
> - `README.md`（KB token 估算 + 注入策略：全量 / RAG / 混合）
>
> **既有可重用資產**（勿重造）：
> - **`backend/app/tools/triz_kb.py`** — 已有 `load_39_parameters()` / `load_40_principles()` / `load_separation_principles()` / `load_76_standard_solutions()` / `lookup_matrix()` / `build_triz_tc_context()` / `build_triz_pc_context()` / `build_sufield_context()` / `get_param_name()`；全部 `@lru_cache`；**但都只回傳 raw markdown，未結構化**
> - **`backend/app/prompts/triz_solver.py:7` `TRIZ_SOLVER_SYSTEM`** — TC / PC 共用 system prompt；本 WBS 9.1.2 `TRIZ_PC_INSTANTIATION_WITH_HINT` 必須繼承此 system 不自造

---

## 知識庫稽核發現（2026-04-09 更新）

**重大發現**：既有 `backend/app/tools/triz_kb.py` 與 TRIZ 知識庫基礎設施比預期完整。本 WBS §1.1 / §3.1 / §9.1 的實作方式因此精修：

1. **`rd_assistant_design_system/triz_knowledge_base/` 內 7 個 .md 檔皆存在**：01 參數 / 02 矩陣 / 03 原理 / 04 分離原則 / 05 標準解 / 06 三徑流程 / 07 差異對照
2. **`triz_kb.py` 既有 loader 全齊**：`load_39_parameters()` / `load_40_principles()` / `load_separation_principles()` / `load_76_standard_solutions()` / `lookup_matrix()` / `build_triz_tc_context()` / `build_triz_pc_context()` / `build_sufield_context()` / `get_param_name()` — **但都只回傳 raw markdown，未結構化**
3. **07 §3 確認**：TC 與 PC **共用** `TRIZ_SOLVER_SYSTEM` system prompt — 本 WBS 9.1.2 `TRIZ_PC_INSTANTIATION_WITH_HINT` 繼承不自造
4. **07 §1.1 PC 三要點**隱含「**同屬性互斥語言偵測**」可作為 L1 critic 第五條規則（新增 2.1.5）
5. **07 §1.1 典型誤判警告**：LLM 可能把 TC 當 PC 或反之 — 3.1 prompt 必須加**防退化硬約束**與正反例
6. **06 §4.2 / §5.1 既有 prompt 注入策略**：TC 解題注入 01 + 02(單行) + 03；PC 解題注入 04（+03 選用）— 本 WBS 3.1 的 `TC_TO_MULTI_PC_DECOMPOSITION` prompt 應**同時注入 01 + 03 + 04** 給 LLM 完整推導上下文

### 精修影響

- §1.1 從「抽出常數」→「**在既有 loader 之上新增結構化 parser**」（避免重造）
- §2.1 critic 新增第五條規則 + 2.1.5 helper `contains_same_property_exclusion`
- §3.1 prompt 加入防退化硬約束 + 三 KB 注入 + 正反例
- §9.1.2 hint prompt 明確繼承 `TRIZ_SOLVER_SYSTEM`

---

## 使用者決策（已凍結）

| # | 項目 | 決策 | 備註 |
|---|------|------|------|
| 1 | 觸發方式 | **自動觸發 (critic-based)** | 無手動按鈕；AI 識別完成後立即跑 critic |
| 2 | 儲存策略 | **`contradictions` 新增欄位 + `parent_contradiction_id`** | 子 PC = 子列，FK ON DELETE CASCADE |
| 3 | 分離原理分類法 | **沿用 triz_solver 現有 16 分類** | 抽共用常數；backend/frontend 各一份 |

---

## 邏輯流程（摘要）

```
AI 識別矛盾 → formalize_contradiction 回傳 TC
    → L1 critic (規則 + LLM) 判斷是否深挖
        ├─ 不觸發 → 維持單一 TC，結束
        └─ 觸發 → TC_TO_MULTI_PC_DECOMPOSITION prompt
            → LLM 推導 2–5 個 derived_parameter
            → 每個 PC 挑 1 項 16 分離原則 + rationale + confidence
            → 驗證 (去重 / ID 合法性 / ≥2)
            → 批次 INSERT 子列 (parent_contradiction_id = 父 TC)
            → invalidate query → 巢狀卡片渲染
            → toast「已自動深挖出 N 個物理矛盾」
```

---

## MVP 切分與建議順序

| 優先 | 標籤 | 說明 |
|------|------|------|
| P0 | 1.x 基線 + 分離原則共用常數 + LayeredTrizSolution schema | 下游所有任務包都依賴此 |
| P0 | 2.x 後端 L1 critic + 深挖 prompt + agent | 無此則無法產出多 PC |
| P0 | 3.x DB migration + Supabase types | 無此則無法持久化子 PC |
| P1 | 4.x 前端自動觸發 + 批次 insert | 與後端串接的關鍵閘 |
| P1 | 5.x 前端巢狀卡片 + 分離原則 badge | UX 主要交付 |
| P1 | 9.x 下游銜接（`_solve_pc` hint + Create 樹狀 solve + F2 adapter + CLD scope） | 防止 Explore 成果在下游被忽略 |
| P2 | 6.x 父 TC 更新時 children stale 提示 | 防髒資料，可後補 |
| P2 | 7.x 單測 + E2E | 回歸保護；e-Bike 驗證腳本 |

---

## WBS 總覽

| ID | 工作包 | 主要交付物 |
|----|--------|------------|
| 1 | 基線與共用常數 | 16 分離原則雙端常數、型別表、文件對照、`LayeredTrizSolution` Pydantic + TS |
| 2 | 後端：L1 critic | `should_trigger_pc_decomposition` + LLM critic prompt |
| 3 | 後端：TC→多 PC 深挖 agent | `decompose_tc_to_pcs` + prompt + schema + router |
| 4 | 資料庫：migration 與型別 | `006_pc_decomposition.sql` + supabase types |
| 5 | 前端：自動觸發與持久化 | AI 識別 hook → 批次 insert → query invalidate |
| 6 | 前端：巢狀卡片與分離原則 UI | `<DecomposedChildrenList>`、色條 badge、可折疊 rationale |
| 7 | 前端：父更新防護 | stale 標記 + 手動重新深挖按鈕（僅此例外） |
| 8 | 測試、可觀測性、文件 | 單測/整合測/E2E；e-Bike 驗證腳本；runbook |
| **9** | **下游銜接** | **`_solve_pc` hint / Create 樹狀 solve / F2 adapter / CLD scope / Phase B 相容性** |

---

## 1.0 基線與共用常數

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 1.1 | 結構化 parser `backend/app/tools/separation_principles.py`，從 `04_separation_principles.md` 切出 16 項常數 | `SEPARATION_PRINCIPLES: list[dict]` 16 項 + `get_separation_principle` + `get_separation_principles_by_category` + `build_separation_principle_id_context()`；8 pytest 全綠；既有 `build_triz_pc_context()` 未動 | — | ✅ Wave1 (backend/app/tools/separation_principles.py, 8 tests passed) |
| 1.2 | 前端對應常數 `src/lib/triz/separationPrinciples.ts` | `SEPARATION_PRINCIPLES` 16 項（與 1.1 完全對應）+ `getSeparationPrinciple` + `CATEGORY_COLOR` + `CATEGORY_LABEL_ZH` + `getSeparationPrinciplesByCategory`；10 vitest 全綠 | 1.1 | ✅ Wave1 (src/lib/triz/separationPrinciples.ts, 10 tests passed) |
| 1.3 | backend↔frontend id parity 測試 | `backend/tests/test_separation_principles_parity.py`（4 tests）+ `src/lib/triz/__tests__/separationPrinciplesParity.test.ts`（4 tests）；兩端 extract ids 並互相驗證集合與順序 | 1.1, 1.2 | ✅ Wave2 (4+4 tests passed) |
| 1.4 | 型別對齊文件 `docs/e2e/module/Explore_TC_to_MultiPC_Type_Alignment.md` | 12 個型別對照表 + 一致性檢查清單 + 相關檔案索引；點出 backend/frontend 差異（反映發現 10） | 1.1 | ✅ Wave2 (documents 12 type classes, flagged canonical mismatch) |
| **1.5** | ~~新增 `LayeredTrizSolution` 到 `schemas.py`~~ | **🔄 Reverted — canonical types 已存在**：`schemas.py` 既有 lines 515-650 有完整 `L1Surface` / `L2RootCause` / `L3StructuralCheck` / `DeepenLink` / `SeparationCandidate` / `DifferentialPairAnalysis` / `RecommendedRoute` / `DifferentialAnalysis` / `PhaseBDirective` / `LayeredTrizSolution` / `SuFieldModel`（對齊 `TRIZ_Layered_DrillDown_Optimization.md §5`，比本 WBS skeleton 更豐富）。Wave1 Agent 未發現而加重名 scaffold，已被 Wave2 task 3.2 Agent 移除 | 1.4 | ❌ No-op (canonical existed pre-Wave1, scaffold removed by Wave2-G) |
| **1.6** | ~~前端 `src/types/trizLayered.ts`~~ | **🔄 Reverted — canonical `src/types/layeredTriz.ts` 已存在**（注意大小寫不同）：既有檔已 1:1 鏡像 canonical backend（snake_case 零轉換），且被 `Create.tsx` / `api.ts` / `LayeredSolutionCard.tsx` / `DifferentialAnalysisPanel.tsx` 消費中。Wave1 Agent 未發現而加 camelCase 重複檔，零外部消費者，已刪除 | 1.5 | ❌ Deleted (zero consumers, canonical layeredTriz.ts used everywhere) |
| **1.7** | ~~前端 helper `src/lib/triz/assembleLayeredSolution.ts`~~ | **🔄 Reverted**：基於 1.6 錯誤 scaffold 建構，所有欄位名稱錯誤。零外部消費者，連同測試一併刪除。未來若需要前端 stub assembler，應基於 canonical `layeredTriz.ts`（snake_case） | 1.6 | ❌ Deleted (built on wrong types) |

---

## 2.0 後端：L1 critic

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 2.1 | `should_trigger_pc_decomposition(tc_response, severity, natural_description, candidate_principles, rd_manual, enable_llm_critic)` | 5 條規則（severity / hits≤2 / rd_manual / contains_same_property_exclusion / LLM critic fallback）；對應 `Forward_TRIZ_Solver_Architecture.md:645-660` | 1.4, 2.1.5, 2.2 | ✅ Wave2 (triz_critic.py +95 lines, 11 tests) |
| **2.1.5** | helper `contains_same_property_exclusion(text: str) -> bool` | 18 中文 + 5 英文 regex 模式 | — | ✅ Wave1 (20 tests passed) |
| 2.2 | `L1_TRADE_OFF_CRITIC` prompt in `analyst.py` | LLM 判斷 trade-off 折衷；輸出 `{"all_trade_off": bool, "reason": str}`；規則層未觸發時才呼叫 | — | ✅ Wave2 (appended to analyst.py) |
| 2.3 | 單測 `backend/tests/test_triz_critic.py` | 5 條規則各自一個 case + LLM fallback 2 case + exception path | 2.1, 2.1.5, 2.2 | ✅ Wave2 (11 tests passed, 31 total with helper tests) |

---

## 3.0 後端：TC→多 PC 深挖 agent

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 3.1 | `TC_TO_MULTI_PC_DECOMPOSITION` prompt in `analyst.py`；三 KB 並注（39/40/分離原則）；防退化硬約束；正反例 | prompt 含完整指令、2 正例（e-Bike 齒輪模數/殼體密度）+ 2 反例（兩參數取捨），fixed JSON schema | 1.1, 1.4 | ✅ Wave2 (appended to analyst.py) |
| 3.2 | `DecomposedPC` / `ContradictionDecomposeRequest` / `ContradictionDecomposeResponse` in `schemas.py` | Pydantic v2 model；`DecomposedPC` 9 欄位 + `field_validator` 檢查 `separation_principle_id` 必在 16 項 canonical；Request/Response 完整 | 1.4 | ✅ Wave2 (schemas.py +64 lines, validator rejects fake ids) |
| 3.3 | `decompose_tc_to_pcs(req)` in `analyst.py` (+133 lines) | Critic → `_extract_socratic_insights` 重用 → 三 KB 注入 → `call_llm_json` → 去重 + 逐項 `ValidationError` skip → 兩層 try/except 錯誤隔離；`enable_llm_critic=False`（Explore 階段避免 LLM 雙重呼叫） | 2.1, 3.1, 3.2 | ✅ Wave3 |
| 3.4 | `POST /contradictions/{cid}/decompose` in `contradictions.py` (+24 lines) | 鏡像 `cld.py` error handling；`HTTPException(502)` on agent exception | 3.3 | ✅ Wave3 |
| 3.5 | `backend/tests/test_decompose_tc.py` 8 agent unit tests | critic 未觸發 / happy 3 PCs / 重複去重 / 無效 id 拒絕 / 空列 / LLM exception / malformed JSON / socratic insights injection | 3.3 | ✅ Wave3 (8 tests passed) |
| 3.6 | 2 router integration tests（同檔案） | happy path 200 + 502 on agent exception（發現 `error_handler` middleware shape，用 `body["error"]["message"]`） | 3.4 | ✅ Wave3 (2 tests passed) |

---

## 4.0 資料庫：migration 與 Supabase 型別

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 4.1 | 新檔 `supabase/migrations/009_pc_decomposition.sql`（006 已被占用，改為 009） | 8 個 nullable 欄位 + FK cascade + index + DO $$ ... $$ 防重入 CHECK constraint + rollback 註解；`pc_attribute_a/not_a` 併入本 migration（pre-investigation 確認未存在） | — | ✅ Wave1 (009_pc_decomposition.sql, idempotent DDL) |
| 4.2 | `supabase db reset` 本地驗證 | `information_schema.columns` 可見新欄位；`EXPLAIN` 子查詢使用 index | 4.1 | ⏳ Wave3 (需 supabase 本地 runtime) |
| 4.3 | `src/integrations/supabase/types.ts` `contradictions.Row/Insert/Update` 含 8 個 migration 009 欄位 | 手動 patch 完成並有 `// Added by migration 009` 註解 | 4.1 | ✅ Pre-existing (already present before Wave 2 reconciliation) |
| 4.4 | `src/types/explore.ts` `ExploreContradiction` 擴充 8 個 camelCase 欄位 | `pcAttributeA` / `pcAttributeNotA` 本來就有；Wave 階段補上 `parentContradictionId`, `derivedParameter`, `subsystemHint`, `separationPrincipleId`, `separationCategory`, `separationRationale` | 4.3 | ✅ Pre-existing (all 8 fields present in explore.ts lines 37-57) |

---

## 5.0 前端：自動觸發與持久化

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 5.1 | API client `contradictionDecompose` in `src/lib/api.ts` | 3 interfaces + 1 async function；使用既有 `request<T>()` helper | 3.4, 4.4 | ✅ Wave4-L |
| 5.2 | `maybeAutoDecomposeTC` in ContradictionTab — AI re-identify 成功且 `type === 'TC'` 時自動呼叫 | 兩個 call-site（formalize loop + new draft branch） | 5.1 | ✅ Wave4-L |
| 5.3 | 批次 Supabase INSERT 子 PC | `supabase.from('contradictions').insert(childRows)` + `invalidate()` | 4.3, 5.2 | ✅ Wave4-L |
| 5.4 | Toast `sonner` — 成功顯示「已自動深挖出 N 個物理矛盾」；失敗安靜處理 | — | 5.2 | ✅ Wave4-L |
| 5.5 | 防重入 `force` 參數 + `parentContradictionId` dedup guard | — | 5.3 | ✅ Wave4-L |

---

## 6.0 前端：巢狀卡片與分離原則 UI

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 6.1 | ContradictionTab `childrenMap` useMemo + `topLevelContradictions` 過濾 + `<DecomposedChildrenList>` JSX wiring | 頂層只渲染無父的矛盾；子 PC 巢狀於父 TC 下方 | 4.4 | ✅ Wave5-Q |
| 6.2 | `<DecomposedPCCard>` 新組件（195 行）| 色條 + badge + 折疊 rationale + confidence prop | 1.2 | ✅ Wave4-M (13 tests) |
| 6.3 | `confidence < 0.5` 灰階 + `AlertTriangle` 警示 | `opacity-70` + tooltip "低信心，建議驗證" | 6.2 | ✅ Wave4-M |
| 6.4 | 子 PC 編輯/刪除 handler 重用既有 `handleStartEdit` / `setDeleteConfirmId` | 與父矛盾用同一套確認對話框 | 6.1, 4.1 | ✅ Wave5-Q |

---

## 7.0 前端：父更新時 children stale 提示

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 7.1 | `staleParentIds` Set state + edit save handler 參數比對 | volatile client-side；重整頁面消失 | 6.1 | ✅ Wave6-U |
| 7.2 | `DecomposedChildrenList` stale banner + `handleReDecompose`（刪舊 children → force re-decompose → clear stale） | 黃色 `AlertTriangle` 提示 + 「重新深挖」按鈕 | 7.1, 5.1 | ✅ Wave6-U |

---

## 8.0 測試、可觀測性、文件

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 8.1 | CI 整合 | `.github/workflows/` 不存在，需獨立 initiative 建立 | 2–3.x | ⏸ Deferred — 無 CI 基礎設施 |
| 8.2 | E2E 手測腳本 + 9.7 延伸（11 步驟涵蓋 Explore → Create → CLD → F2 → Stale → Cascade） | 6 步 base + 5 步 downstream 延伸 | 5, 6 | ✅ Wave4-P + Wave6 延伸 |
| 8.3 | 可觀測性：5 個結構化 log + `time.monotonic()` 計時 | entry / critic / LLM elapsed / result / error | 3.3 | ✅ Wave6-V |
| 8.4 | `TRIZ_Layered_DrillDown_Optimization.md` Changelog v1.2 | 涵蓋 L1 critic + 多 PC + hint + CLD/AntiAnchor + L3 deferred | 3.3 | ✅ Wave4-P |
| 8.5 | Runbook `docs/e2e/operations/runbook_pc_decomposition.md` | 5 層 rollback：FE stop → BE stop → data cleanup → migration rollback → restore | 4.1 | ✅ Wave4-P |

---

## 9.0 下游銜接（Explore → TRIZ Solve → F2 / CLD / Phase B）

> **目的**：確保 Explore 階段產出的 `parent_contradiction_id` 樹 + `separation_principle_id` hint + `subsystem_hint` 能被 Create 階段 TRIZ Solve、F2 Subsystem Discovery、CLD 生成、Phase B adoption 正確消費，避免深挖成果在下游被忽略或誤用。
> **設計前提**：L3 (SF) 完全延後到獨立 WBS (`Explore_L3_SF_Parallel_Check_WBS.md`)；本版產出的 `LayeredTrizSolution.l3` 永遠為 `None`，並以 `l3_status="deferred"` 明確告知下游。

### 9.1 `_solve_pc` 接受 separation hint（反向相容）

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.1.1 | `TrizLookupRequest` +4 optional hint fields | Pydantic v2；反向相容 | 1.4 | ✅ Wave4-N |
| 9.1.2 | `TRIZ_PC_INSTANTIATION_WITH_HINT` prompt (+56 lines) | 繼承 `TRIZ_SOLVER_SYSTEM`；跳過 separation KB 注入 | 1.1, 1.5 | ✅ Wave4-N |
| 9.1.3 | `_solve_pc` dispatcher → `_solve_pc_base` + `_solve_pc_with_hint` | 未知 id fallback 到 base path；6 tests | 9.1.1, 9.1.2 | ✅ Wave4-N (6 tests) |
| 9.1.4 | `_log_hint_override_delta` observability | `logger.info("separation hint override: ...")` | 9.1.3 | ✅ Wave4-N |

### 9.2 Create 頁 TRIZ Solve 改為 parent-aware 樹狀流程

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.2.1 | Create.tsx `childrenMap` + `topLevelContradictions` useMemo | 與 Explore 同模式 | 5.3, 6.1 | ✅ Wave5-R |
| 9.2.2 | 分層 Solve 按鈕（layered + legacy 雙模式）帶 hint fields | `solvingIds` Set 提供 per-card loading | 9.1.3, 9.2.1 | ✅ Wave5-R |
| 9.2.3 | Client-side 使用 canonical `layeredTriz.ts` | `Contradiction` type 擴充 8 欄位 + `mapRow` adapter | 1.7 | ✅ Wave5-R |
| 9.2.4 | 子 PC 結果色條（`border-l-4` by `separationCategory`）| blue/green/orange/purple | 9.2.1, 6.2 | ✅ Wave5-R |

---

## 9.0 下游銜接（Explore → TRIZ Solve → F2 / CLD / Phase B）

> **目的**：確保 Explore 階段產出的 `parent_contradiction_id` 樹 + `separation_principle_id` hint + `subsystem_hint` 能被 Create 階段 TRIZ Solve、F2 Subsystem Discovery、CLD 生成、Phase B adoption 正確消費，避免深挖成果在下游被忽略或誤用。
> **設計前提**：L3 (SF) 完全延後到獨立 WBS (`Explore_L3_SF_Parallel_Check_WBS.md`)；本版產出的 `LayeredTrizSolution.l3` 永遠為 `None`，並以 `l3_status="deferred"` 明確告知下游。

### 9.1 `_solve_pc` 接受 separation hint（反向相容）

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 |
|---------|--------|-------------------|------|
| 9.1.1 | `TrizLookupRequest` (`schemas.py:415`) 新增 optional 欄位 `separation_principle_id`, `separation_category`, `separation_rationale`, `derived_parameter` | Pydantic v2 model；預設 None；現有呼叫端無需改動即可反向相容 | 1.4 |
| 9.1.2 | 新 prompt `TRIZ_PC_INSTANTIATION_WITH_HINT` 於 `backend/app/prompts/triz_solver.py`；**必須使用既有 `TRIZ_SOLVER_SYSTEM`**（發現 2 / 07 §3：TC / PC 共用 system，勿另造） | 指令：「Explore 階段已挑選 `{separation_principle_id}` (`{separation_category}`)，理由：`{separation_rationale}`。請**直接用此分離原則**生成 3-5 條具象化 implementation ideas，不再重新判斷分類」；輸出 schema 對齊現有 `TrizSuggestion`；注入 `load_40_principles()` 但跳過 `load_separation_principles()`（已有 hint） | 1.1, 1.5 |
| 9.1.3 | `_solve_pc` (`triz_solver.py:124`) 加分支：`req.separation_principle_id` 非空 → 用 `_WITH_HINT` prompt + 輕量 KB 注入；空 → 維持既有 `build_triz_pc_context()` 路徑 | 單測：兩條路徑各一；驗證 hint 路徑的 prompt 長度 < 原路徑 60%（省 tokens）；反向相容舊呼叫 | 9.1.1, 9.1.2 |
| 9.1.4 | 記 delta log：當 hint 路徑的 LLM 產出之 `separation_principle` 與 Explore 傳入的 id 不同時 | `logger.warning("separation hint override: explore=%s solver=%s reason=%s", ...)` — 不失敗，僅觀測 | 9.1.3 |

### 9.2 Create 頁 TRIZ Solve 改為 parent-aware 樹狀流程

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 |
|---------|--------|-------------------|------|
| 9.2.1 | `Create.tsx` 取得 contradictions 後以 `parent_contradiction_id` 分群，建 `Map<parentId, {parent: TC, children: PC[]}>` | 頂層只顯示 `parent_contradiction_id == null` 的矛盾；子 PC 縮排掛在父下方（與 Explore `<DecomposedChildrenList>` 視覺一致） | 5.3, 6.1 |
| 9.2.2 | Solve 按鈕行為分層：父卡片的按鈕跑 `_solve_tc`；子 PC 卡片的按鈕跑 `_solve_pc` **並帶 separation hint**；「一鍵全跑」按鈕 loop 父 + 所有子 | 每張卡片獨立 loading state；suggestion 結果掛回對應卡片；失敗不影響其他 | 9.1.3, 9.2.1 |
| 9.2.3 | 用 `assembleLayeredSolution` (1.7) 將單一父 TC + 其 children 的 solve 結果組成 `LayeredTrizSolution` 暫存於 client-side 狀態 | 物件形狀符合 `Forward_Subsystem_Discovery_Architecture.md §3.1` 契約；`l3` 固定 `null`；為 9.5 F2 adapter 鋪路 | 1.7, 9.2.2 |
| 9.2.4 | 父 TC 和子 PC 的 suggestions 在 UI 上視覺分群：父用灰底、子用依 `separation_category` 色條 | 使用 1.2 的 `CATEGORY_COLOR`；複用 6.2 `<DecomposedChildrenList>` 樣式 | 9.2.1, 6.2 |

### 9.3 CLD 生成 scope 控制

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.3.1 | `contradiction_tree.py` 新檔（67 行）：`get_contradiction_leaves` / `get_root_tcs` / `get_children_of` | 純 dict 操作 + 8 tests | 4.1 | ✅ Wave4-O |
| 9.3.2 | CLD prompt +1 instruction 指引 LLM 用 `derived_parameter` 作 CLD 變數名 | 輕量 prompt 注入；filtering 在 caller 層（非 generate_cld 內部） | 9.3.1 | ✅ Wave4-O |
| 9.3.3 | (合併入 9.3.2) | — | — | ✅ |

### 9.4 Anti-Anchor leaves-only 濾鏡

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.4.1 | `generate_anti_anchor` 加 4 行 comment 指引 caller 用 leaves-only；anti_anchor prompt 不直接吃 contradictions | comment-only guidance | 9.3.1 | ✅ Wave4-O |

### 9.5 F2 Subsystem Discovery input adapter

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.5.1 | `_enrich_contradiction_lines()` helper + prompt 注入 `[子系統提示:] [物理變數:]` 標記 | +31 lines in triz_solver.py；6 tests | 4.1 | ✅ Wave5-S |
| 9.5.2 | 混合父子 contradictions 不 crash 測試 | 含在 9.5.1 的 6 tests 中 | 9.5.1 | ✅ Wave5-S |
| 9.5.3 | `suggest_subsystems` 頂部 TODO(L3 WBS §6.1) 註解 | 指向 `Explore_L3_SF_Parallel_Check_WBS.md §6` | 9.5.1 | ✅ Wave5-S |

### 9.6 Phase B adoption 相容性

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.6.1 | Phase B code scan：發現 `check_phase_b_conflict` (evaluator.py:204) + `_apply_layered_directives` (evaluator.py:260) + `PhaseBDirective` schema + 既有 227 行測試 | 完整 grep 報告；現有 SKIP/WARN/CHECK 三態邏輯不衝突但有潛在缺口（`contradiction_id` vs `parent_contradiction_id` grouping） | — | ✅ Wave5-T |
| 9.6.2 | 無需改 code（Phase B + decomposition 尚未整合）；在 `_apply_layered_directives` docstring 加 TODO | TODO 指向 L3 WBS §7 | 9.6.1 | ✅ Wave5-T (TODO only) |
| 9.6.3 | `TRIZ_Multi_Solution_Adoption_Strategy.md` Changelog v1.1 | `parent_contradiction_id` 跨層不互斥備註 | 9.6.1 | ✅ Wave5-T |

### 9.7 下游銜接 E2E 驗證

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.7.1 | 延伸 8.2 腳本 Step 7-11：Create 頁分層 solve + hint 驗證 + CLD 節點 + F2 subsystem_hint + stale 防護 | 5 個延伸步驟 + 驗證清單 | 8.2, 9.2 | ✅ Wave6 (docs) |
| 9.7.2 | (合併入 9.7.1 Step 9) F2 module 節點語意對齊 | — | 9.5.1 | ✅ |
| 9.7.3 | (合併入 9.7.1 Step 8) CLD `derived_parameter` 節點標籤 | — | 9.3.2 | ✅ |

---

## 依賴圖（關鍵路徑）

```
1.1 (backend 16 分類) ──┬─► 1.2 (frontend 16 分類) ──┐
                       │                            │
                       ├─► 1.5 LayeredTrizSolution Pydantic ──► 1.6 TS types ──► 1.7 assembleLTS helper
                       │                                                              │
                       ├─► 2.1 critic ──► 2.2 LLM critic prompt ──► 2.3 test            │
                       │                                            │                   │
                       ├─► 3.1 decomp prompt ──► 3.2 schemas ──► 3.3 agent ──► 3.4 router ──► 3.5/3.6 test
                       │                                                                      │
4.1 migration ──► 4.2 verify ──► 4.3 types ──► 4.4 explore types                               │
                                                                                               │
                5.1 api client ◄──────────────────────────────────────────────────────────────┤
                5.2 auto trigger ──► 5.3 batch insert ──► 5.4 toast ──► 5.5 dedup              │
                                                                        │                      │
6.1 grouping ──► 6.2 card ──► 6.3 confidence ──► 6.4 edit/delete ──────┴─► 7.1 stale ──► 7.2 re-decompose
                                                                                               │
               ┌─────────────── Phase 9 下游銜接 ───────────────────────────────────────────────┤
               │                                                                               │
9.1.1 req 欄位 ──► 9.1.2 hint prompt ──► 9.1.3 _solve_pc 分支 ──► 9.1.4 delta log                │
                                              │                                                │
9.3.1 tree helper ──► 9.3.2 generate_cld leaves ──► 9.3.3 CLD prompt                            │
      │                                                                                        │
      └─► 9.4.1 anti_anchor leaves                                                              │
                                                                                                │
9.5.1 F2 adapter ──► 9.5.2 F2 test ──► 9.5.3 F2 TODO                                            │
                                                                                                │
9.2.1 Create tree grouping ──► 9.2.2 分層 Solve ──► 9.2.3 assembleLTS client ──► 9.2.4 色條      │
                                     ▲                                                         │
                                     └── depends on 9.1.3 + 1.7                                │
                                                                                                │
9.6.1 Phase B scan ──► 9.6.2 intra-layer skip ──► 9.6.3 docs                                    │
                                                                                                │
9.7 e2e 延伸驗證 ──► 8.2 e-Bike 主腳本                                                            │
                                                                                                │
8.1 ci ──► 8.2 e2e ──► 8.3 logs ──► 8.4 docs ──► 8.5 runbook ◄──────────────────────────────────┘
```

關鍵路徑：**1.1 → 1.5 → 3.1 → 3.2 → 3.3 → 3.4 → 4.1 → 4.3 → 5.1 → 5.2 → 5.3 → 6.1 → 6.2 → 9.1.3 → 9.2.2 → 9.3.2 → 9.5.1 → 9.7.1 → 8.2**

---

## 本版涵蓋 / 不涵蓋

| 涵蓋 | 不涵蓋（另開 WBS 或文件） |
|------|---------------------------|
| Explore 階段 L1 critic + TC→多 PC 自動深挖 | **L3 (SF) 平行旁路整條路徑** → `Explore_L3_SF_Parallel_Check_WBS.md`（獨立 WBS，L3-γ 路線） |
| 16 分離原則 backend / frontend 共用常數與 drift 防護 | `differential_analysis` 跨層推薦路線（`Forward_TRIZ_Solver_Architecture.md §7.5`） → L3 WBS 一併處理 |
| **`LayeredTrizSolution` Pydantic 完整 schema + 前端 TS helper (1.5–1.7)** | `solve_triz_layered` orchestrator backend 實作（§7.0）→ L3 WBS |
| `contradictions` 表 `parent_contradiction_id` FK 與巢狀卡片 UI | 76 standard solutions 知識庫重建 → L3 WBS |
| 父 TC stale 提示與唯一手動重新深挖入口（7.2） | MUST 評估納入「PC 分解完整度」維度（`memory/project_must_evaluation_design.md`） |
| e-Bike 驗證腳本與 cascade 刪除行為 | 手動深挖按鈕（除 7.2 stale 情境外；使用者決策為全自動觸發） |
| **9.x 下游銜接（`_solve_pc` hint / Create 樹狀 solve / CLD leaves / anti-anchor / F2 subsystem_hint / Phase B intra-layer skip）** | F2 完整切換為吃 `LayeredTrizSolution[]` 輸入 → L3 WBS；本版只做 input adapter 預留 |

---

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| LLM 產出重複 `derived_parameter`（同義換字） | 子 PC 資訊冗餘 | 3.3 驗證層做去重；prompt 明確要求「不同物理變數 / 子系統 / 尺度」 |
| LLM 回 `separation_principle_id` 不在 16 清單 | 資料汙染 | 3.3 驗證層拒絕；記 log；回空 list 並在 reasoning 註記 |
| 兩次 LLM 呼叫（critic + decompose）latency 增加 | 使用者等待 | critic 規則層先跑；LLM critic 只在規則未觸發時；decompose 可 stream 或 toast 先顯示「深挖中…」 |
| 父 TC 被多人同時識別導致重複深挖 | 子 PC 重複 | 5.5 前端前置查詢；後端可加 advisory lock（後續迭代） |
| Migration 在 production 有歷史資料時衝突 | 部署失敗 | 新欄位皆 nullable；index 用 `CREATE INDEX IF NOT EXISTS` |
| **`_solve_pc` 帶 hint 後 LLM 仍自行變更 separation_principle** | 下游解題與 Explore 預分類不一致 | 9.1.4 delta log 觀測；不阻斷，累積樣本後決定是否強制 |
| **Create 頁多 PC 同時 solve → LLM 請求併發風暴** | 使用者等待、token 爆衝 | 9.2.2 每張卡獨立 loading 而非一次性 Promise.all；可加 concurrency limit (例 3) |
| **F2 同時收到父 TC id 與子 PC id 造成 related_contradictions 重複** | subsystem 樹節點錯誤歸類 | 9.5.2 單測覆蓋；F2 內部去重邏輯若不存在需補 |
| **`LayeredTrizSolution.l3=None` 被下游誤判為資料損壞** | F2 / 決策中心顯示錯誤 *(v9: 原 SCAMPER)* | 1.5 明確 `l3_status="deferred"` 欄位；下游讀取前檢查 status 而非 null |
| **3.1 prompt LLM 退化：產出 N 個小 TC 偽裝為 PC** | 多 PC 分解品質失效；下游 `_solve_pc` hint 路徑得到錯誤輸入；無法真正觸發分離原則解 | (a) 3.1 prompt 加防退化硬約束 + 2 正例 + 2 反例（e-Bike 齒輪模數 ✓ / 兩參數取捨 ✗）；(b) 3.3 驗證層加規則檢查「`derived_parameter` 必須是單一物理屬性 P 的 A / ¬A 互斥陳述」，偵測到「改善 X 惡化 Y」句式即拒絕該條 PC；(c) 測試 3.5 加反例案例 mock，確認驗證層會 reject；(d) 8.2 e-Bike E2E 人工檢核每個 derived_parameter 語意 |
| **1.1 markdown parser 脆弱性：`04_separation_principles.md` 結構變動導致 parser 壞** | 16 項常數產出錯誤；下游 separation_principle_id 驗證全部失效；部署失敗 | (a) `parse_separation_principles()` 用明確錨點（`### N. 時間分離` 等 4 大類標題 + `| 策略 |` 表格行）而非位置依賴；(b) 鎖定 parity test：4 類 × 4 策略 = **恰好** 16 項，少於或多於即 fail；(c) 每項必須成功抽出 `id` / `category` / `name_zh` / `physical_principle`，任一欄為空即 fail；(d) parser 單測含 golden fixture（當前 .md 快照）；(e) .md 如有修改 PR 必須同步更新 fixture 與跑 parity test |

---

## 完成判準（Definition of Done）

- [ ] 所有 P0 / P1 任務包單測 + 整合測全綠
- [ ] e-Bike 驗證腳本 8.2 + 9.7 能在本地端到端走通：Explore 識別 → 深挖 ≥3 子 PC → Create 頁分層 solve → F2 subsystem 樹含對應 subsystem_hint → CLD 節點含 `derived_parameter`
- [ ] 每個子 PC 的 `separation_principle_id` 在 16 清單內且 `separation_category` 至少涵蓋 2 種
- [ ] 父 TC 刪除後子 PC 由 DB FK CASCADE 正確消失（無孤兒列）
- [ ] **`LayeredTrizSolution` Pydantic schema 通過 mypy / pytest，`l3_status="deferred"` 於 `docs/e2e/module/Explore_L3_SF_Parallel_Check_WBS.md` 有明確承接**
- [ ] **`_solve_pc` 新增 hint 路徑單測覆蓋兩條分支 (有/無 hint)，反向相容舊呼叫**
- [ ] **Create 頁對同一父 TC 的多 PC solve 後，UI 以分層卡片呈現且各卡片獨立 loading state**
- [ ] **CLD 與 Anti-Anchor 切換到 `get_contradiction_leaves` 後，現有無子 PC 情境行為不變 (回歸測試)**
- [ ] `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md` Changelog 已更新
- [ ] `docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md` 已註記「同 parent 跨層不互斥」(9.6.3)
- [ ] PR #9 review 提出的「_extract_socratic_insights 錯誤隔離」建議已一併修復（analyst.py 整段包 try/except）

---

## 文件對照（快速索引）

| WBS 區段 | Forward_TRIZ_Solver_Architecture.md v1.1 | TRIZ_Layered_DrillDown_Optimization.md | TRIZ_Multi_Solution_Adoption_Strategy.md v1.1 |
|----------|-------------------------------------------|-----------------------------------------|----------------------------------------------|
| 1.x 共用常數 + LTS schema | §6.7 DeepenLink / §10 LayeredTrizSolution | §5 LayeredTrizSolution schema | §1.1 多分離原則同時適用 |
| 2.x L1 critic | §6.2 L2 觸發條件（645-660） | §4.2 觸發表 | — |
| 3.x 深挖 agent | §6.7 `deepen_link` 契約 | §4.3 deepen_link 契約、§7.3 e-bike 案例 | — |
| 4.x Migration | — | §5 schema FK 語意 | §4.2 Concept Route layered 欄位 |
| 5.x 前端自動觸發 | §7.0 `solve_triz_layered` 時序 | — | — |
| 6.x 巢狀卡片 UI | — | §5 視覺化規範 | — |
| 7.x Stale 重深挖 | — | §4.2 RD 手動觸發 | — |
| 8.x 測試 / 文件 | §10 Anti-Pattern | §6 文件修改指引、§11 驗證 | §6 Anti-Pattern |
| **9.1 `_solve_pc` hint** | §6.7 separation_type_candidates | §4.3 deepen_link 產出 | — |
| **9.2 Create 樹狀 solve** | §7.0 solve_triz_layered 時序（UI 層簡化版） | §8.1 F1 輸出形狀 | §2.1 同 LTS 跨層非互斥 |
| **9.3 CLD leaves** | — | — | §M4 衝突檢查（父子去重語意） |
| **9.4 Anti-Anchor leaves** | — | — | 同上 |
| **9.5 F2 adapter** | — | — | §4.2 Concept Route |
| **9.6 Phase B 相容** | — | — | §2.1 `same_contradiction_intra_layer_conflict: skip` |
| **9.7 下游 e2e** | §11 驗證 | §11 驗證 | — |
| **L3 (整段)** | §7.0 L3 平行旁路 / §6.3 SF | §4.4 L3 角色 | §6 L3 adoption |

### 關聯 WBS 文件

- `docs/e2e/module/Subsystem_Interface_Development_WBS.md` v1.0 — F2 子系統定義；本 WBS 9.5.1 的 `suggest_subsystems` input adapter 改動需同步該 WBS 的 2.x
- `docs/e2e/module/Explore_L3_SF_Parallel_Check_WBS.md` — **L3-γ 獨立 WBS 待建立**（見下一段）

---

## 關聯 L3 WBS stub（待建立）

**檔案**：`docs/e2e/module/Explore_L3_SF_Parallel_Check_WBS.md`

**建議範圍**（由本 WBS 交棒，切勿在本版實作）：
1. **backend `_solve_sf` 重寫** 符合 `Forward_TRIZ_Solver_Architecture.md §7.0` 「L3 平行旁路、無條件跑」語意；目前的 delegate-to-`analyze_sufield` 路徑標為 legacy
2. **`solve_triz_layered` orchestrator** 真正實作：L1 + L3 並行、L2 條件觸發、`differential_analyzer`、`LayeredTrizSolution` 完整聚合
3. **76 standard solutions 知識庫** 評估完整性並補齊
4. **前端 `<DecomposedChildrenList>` SF children 區塊** 啟用：色條、S1/S2/F 三元組顯示、interaction/completeness badge
5. **F2 輸入完整切換** 為吃 `LayeredTrizSolution[]`（現本 WBS 9.5 只做 input adapter 預留）
6. **Phase B `differential_analysis.recommended_route`** 採納 UX：RD 在決策中心看到 L1 / L2 / L3 三路線比較並選擇 `adopted_route`
7. **UX 決策**：Explore 頁的「SF」類型按鈕是否從三選一 UI 移除（改由 solver 自動產出）— 需 RD 使用者研究
8. **Migration**：`contradictions` 表的 `sf_*` 欄位在新路徑下的寫入責任重分配（Explore 不再寫，solver 回寫）

**觸發條件**：本 WBS 的 P0 + P1 全部上線穩定後啟動 L3 WBS。
