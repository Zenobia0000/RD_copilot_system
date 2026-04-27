# TRIZ 分層 Drill-Down 開發 WBS（Create · Tab ①）

> **版本**：1.6 | **日期**：2026-04-13 | **狀態**：v1.5 + feature flag 預設 on + 舊版 TC/PC/SF UI 移除 + type filter 移除 + Tab ① ConvergenceDashboard 移除 | **Owner**：Create FE + TRIZ Solver Backend
>
> **⚠️ Phase B 退役通知 (2026-04-27)**：本 WBS 中 WP 6.3–6.5（Phase B 掃描邏輯修訂）和 WP 10.6（Phase B 按鈕）的實作記錄保留供歷史追溯，但 **Phase B 已於 v9 退役**。其 5 項檢查全部由 SIM ���陣（ADR-008 D5）和 CCI（ADR-008 D4）前置覆蓋。相關程式碼（`check_phase_b_conflict`、`phase_b_directive`、`useConvergenceLoop` Phase B 觸發）待後續清理。

### 完成度 Dashboard (v1.5)

| WP | 主題 | ✅ 完成 | 🟡 部分 | ⏳ 待開 | 層次 |
|----|------|:------:|:------:|:------:|------|
| **1.0** | 契約凍結 + feature flag + DB migration | **6** | 0 | 0 | Backend schema + FE config + SQL |
| **2.0** | LayeredTrizSolution Pydantic model | **4** | 0 | 0 | Backend |
| **3.0** | solve_triz_layered orchestrator | **7** | 0 | 0 | Backend |
| **4.0** | L1 critic + L2 deepen_link | **5** | 0 | 0 | Backend |
| **5.0** | differential_analysis prompt | **4** | 0 | 0 | Backend |
| **6.0** | API endpoint + Phase B | **5** | 0 | 0 | Backend |
| **7.0** | FE 區塊 A 矛盾總覽 | 3 | 0 | 1 | FE 元件 + pages 整合 |
| **8.0** | FE 區塊 B 分層診斷卡 | 8 | 0 | 1 | FE 元件 |
| **9.0** | differential 面板 + 採納三按鈕 | **5** | 0 | 0 | FE 元件 + pages 整合 |
| **10.0** | 決策中心 layered 卡片 | **5** | **1** | 0 | FE 元件 + pages 整合 |
| **11.0** | 下游銜接（F2 / Phase B / DB） | **3** | 0 | 3 | 整合層 + DB migration SQL |
| **12.0** | 遷移測試可觀測性文件 | 7 | 2 | 0 | 測試 + Docs + Runbook |
| **合計** | **70 個工作項** | **62** | **3** | **5** | |

**完成度**：✅ **88.6 %** (62/70) / 🟡 4.3 % (3/70) 部分 / ⏳ 7.1 % (5/70) 待開

**Backend + DB migration + Runbook + Docs + Phase B wiring + F2 hand-off consumer 全部 100 %**。
剩餘集中在 L2 手動編輯對話框 (WP 8.7)、lazy fetch (WP 7.4)、第三眼進階 (WP 10.4)、MUST / Pre-CAD 下游消費 (WP 11.3–11.5)、Playwright E2E (WP 12.5)。

**測試綠燈 (v1.5)**：
- Backend：**84/84 passed**（18 `test_triz_layered` + 8 `test_triz_layered_api` + 11 `test_phase_b_layered_conflict`（含 4 Phase B directive 分支）+ 5 `test_f2_layered_handoff` + 既有 triz_solver/subsystem/tab1_to_tab2_e2e 回歸；2 pre-existing 失敗 deselected）
- Frontend：**92/92 passed**（10 suites，`LayeredSolutionCard.test.tsx` 11 項含 ConceptRouteCard 第二/三眼 2 項新測試）
- TS typecheck 新增零錯誤

**測試綠燈**：
- Backend `tests/test_triz_layered.py` + `test_triz_layered_api.py` + `test_phase_b_layered_conflict.py` + `test_triz_solver.py` 合計 **43/43 passed**（2 pre-existing 失敗 deselected）
- FE `vitest run` **10 suites / 90 tests passed**（含 `LayeredSolutionCard.test.tsx` 9 項）
- TS typecheck 本次新增零錯誤

**測試綠燈**：
- Backend `tests/test_triz_layered.py`：**18/18** passed + 擴大回歸 (triz_solver + subsystem + tab1_to_tab2_e2e + subsystem_contract) **68/68** passed（2 pre-existing 失敗與本案無關）
- FE `vitest run`：**10 suites / 91 tests passed**（含 `LayeredSolutionCard.test.tsx` 9 項 + create __tests__ 41 項）
- TS typecheck 本次新增檔案：**無錯誤**

### 已落地 (✅) — v1.4 最新

**Backend 100 %**：
- `LayeredTrizSolution` schema / `solve_triz_layered` orchestrator / `_l1_critic` / `_derive_pc_from_tc` / `_run_differential_analysis`
- `POST /triz/solve-layered` endpoint
- `evaluator.check_phase_b_conflict` **結構化 Phase B scanner**（WP 6.3/6.4）— 同 LTS 跨層 SKIP、跨 LTS 同矛盾 WARN、跨矛盾 CHECK；6/6 測試綠燈
- `SubsystemSuggestRequest.layered_triz_solutions[]` **F2 hand-off 升級**（WP 11.1）— 向後相容保留 `contradictions[]` fallback
- **API 契約測試** `tests/test_triz_layered_api.py`（WP 12.4）8/8 綠燈：happy path / quick_mode / 422 / unknown severity / 舊 `/triz/solve` 回歸 / schema snapshot 守門

**FE 元件 + 整合 100 %**：
- `src/types/layeredTriz.ts` + `src/types/conceptRoute.ts::LayeredConceptRouteMeta`
- `src/lib/api.ts::trizSolveLayered` + `src/config/featureFlags.ts::trizLayeredMode`
- `LayeredSolutionCard.tsx` + 五個 sub-components（L1/L2/L3 sections + critic badge + deepen_link + separation chips）
- `DifferentialAnalysisPanel.tsx` + 採納三按鈕 + 自訂組合 Dialog
- `ConceptRouteCard.tsx` `layered` type 分支 + 層採納徽章 🔵●🟡●🟢● + recommended/fallback trace
- **`pages/Create.tsx` 整合**（WP 7.1–7.3, 9.2/9.4/9.5, 10.1/10.2）：feature-flag 分支呼叫 `trizSolveLayered`、`layeredSolutions` 狀態 keyed by contradiction_id、quick_mode toggle、`LayeredSolutionCard` 渲染堆疊、`handleLayeredAdopt` → `type='layered'` Concept Route、`handleForceDeepenL2` → `force_l2=true` re-fetch

**DB / Ops**：
- `supabase/migrations/010_triz_layered_drilldown.sql`（WP 1.5 + 11.6）：`concept_routes.layered_solution` JSONB + CHECK constraint，新增 `layered_triz_solutions` 表 + RLS policies
- `docs/e2e/module/TRIZ_Layered_Rollout_Runbook.md`（WP 12.1）：四階段灰度 runbook、前置檢查清單、Metrics/SLO、常見問題排查

**Docs**：
- `create-ux-spec.md` v7、`TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1、`Forward_TRIZ_Solver_Architecture.md` v1.2 同步

### 部分完成 (🟡)
- **WP 10.4 layered 卡片第三眼（Validation Passport 完整版）**：第三眼展開已實作；Validation Passport snapshot 灌入尚未做
- **WP 12.7 Grafana dashboard**：埋點完畢（`phase_timer` + `emit_counter`），實體 Grafana dashboard 待配置
- **WP 12.8 剩餘 docs**：Forward_TRIZ_Solver_Architecture.md v1.2 已更新摘要表；triz-to-scamper-flow.md 章節級章節更新為可選

### 尚未動工 (⏳)
- **WP 7.4 lazy fetch**：目前一次 Promise.all 所有矛盾；展開才 fetch 為優化
- **WP 8.7 L2 手動編輯 Dialog**：允許 RD 直接改 `derived_parameter` 與 `separation_type` 後 re-fetch L2
- ~~WP 11.3 Phase A 回饋迴路~~：v8 退役，`secondary_contradictions` 透過 `is_confirmatory` 語意去重追蹤
- **WP 11.4 MUST 快篩**：MUST evaluator 讀取 `layered_solution` 對整張卡片判 pass/fail
- **WP 11.5 Pre-CAD 五維**：Pre-CAD analyzer 讀取 `layered.recommendedRoute` 對應層組合作為 mechanism 輸入
- **WP 12.5 Playwright E2E 錄影**：元件層測試完備，全流程錄影待補

---

> **範圍**：正向分析 E2E 內 **Tab ① TRIZ 解矛盾** 從「TC/PC/SF 三選一候選池」升級為「`LayeredTrizSolution` 分層 drill-down 診斷報告」的前後端開發、契約修訂、Phase B 邏輯修訂與下游（F2 / 決策中心 / Phase B / MUST）銜接。
> **對齊文件**：
> - `docs/diagrams/create-ux-spec.md` v7（Tab ① 區塊 A/B/C、layered 卡片、差異面板、Phase B 規則）
> - `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md` v1.0（§4 架構、§5 schema、§6 文件修改指引、§8 下游契約、§9 遷移路徑）
> - `docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1（§2 M6 情境、§4.2 Concept Route `layered` type）
> - `docs/e2e/module/Forward_TRIZ_Solver_Architecture.md`（現有三條 solver primitive 作為底層）
> - `docs/e2e/module/Forward_Subsystem_Discovery_Architecture.md` v2.1 §3.1 §6.4.4（F1→F2 hand-off 契約）
> - `docs/diagrams/triz-to-scamper-flow.md`（Phase B 掃描邏輯修訂目標）*(v9: SCAMPER 移除，文件更名為 triz-flow)*

---

## 使用者決策（已凍結）

| # | 項目 | 決策 | 備註 |
|---|------|------|------|
| 1 | 升級模式 | **新增 `solve_triz_layered` orchestrator**，既有 `_solve_tc` / `_solve_pc` / `_solve_sf` primitive 不動 | §9.1 遷移路徑；舊 `/triz/solve` 端點保留 |
| 2 | 層級必跑 / 條件跑 | **L1 必跑、L3 必跑平行旁路、L2 條件跑** | L2 觸發條件 = critic ∨ severity≥major ∨ principle_hits≤2 ∨ RD 手動 ∨ force_l2 |
| 3 | quick_mode 策略 | `quick_mode=on` + `severity=minor` → **強制跳過 L2** | 避免微調矛盾被過度深挖 |
| 4 | Feature flag | **`triz_layered_mode` 預設 on**（v1.6 全面切換）；舊版 TC/PC/SF UI 已移除 | 舊 `/triz/solve` backend endpoint 保留為 primitive，但前端不再呼叫 |
| 5 | Phase B 衝突判定 | **同 `contradiction_id` + 同 `lts_id` → SKIP**；跨矛盾衝突仍 check | 對應 §8.3 偽代碼；移除「同矛盾多路徑警告」 |
| 6 | Concept Route 擴展 | 新增 `type=layered`，`layered_solution` 欄位對齊 `TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1 §4.2 | `single` / `composite` 保留 |
| 7 | 命名解耦 | 本 WBS 的 **L1/L2/L3** 僅指 F1 分析層，與 F2 的 System/Module/Component 完全隔離 | 配 grep lint 規則 |
| 8 | L3 呈現原則 | **L3 永遠呈現**（即使 L1/L2 已採納） | 結構視角旁路，不被採納狀態遮蔽 |
| 9 | Critic 低信心 | `confidence < 0.5` 時**不自動觸發** L2，改顯示「🔽 深挖 L2」手動按鈕 | 對應 Anti-Pattern §10 第 4 條 |

---

## 邏輯流程（摘要）

```
contradictions[{id, pair, severity}]
    ↓
solve_triz_layered orchestrator (NEW)
    ├── L1：_solve_tc (既有 primitive，永遠跑)
    │     └── critic (NEW)：判「trade-off 折衷」→ 觸發 L2
    ├── L2：_derive_pc_from_tc (NEW deepen_link) → _solve_pc (既有 primitive)
    │     觸發條件：critic / severity≥major / RD 手動 / force_l2=true
    │     quick_mode=on + severity=minor → 跳過
    └── L3：_solve_sf (既有 primitive，永遠跑，角色=structural_lens)
    ↓
LayeredTrizSolution (NEW schema) + differential_analysis (LLM)
    ↓
FE 分層診斷卡（L1/L2/L3 垂直堆疊 + deepen_link 視覺化 + recommended_route）
    ↓
RD 採納 [推薦 / 自訂 / 只採 L1] → 產出 Concept Route type=layered|single|composite
    ↓
決策中心 → Phase B (phase_b_directive: 同 LTS 跨層 SKIP) → MUST → Pre-CAD
    ↓
F2 subsystem-suggestions 以 adopted_route 為 related_contradictions 主綁定
```

---

## MVP 切分與建議順序

| 優先 | 標籤 | 說明 |
|------|------|------|
| P0 | 資料模型 + orchestrator 骨架 | 無此則 LayeredTrizSolution 無法閉環 |
| P0 | L1 critic + L2 deepen_link | drill-down 的核心 ARIZ 落地 |
| P0 | 分層診斷卡 FE（區塊 B 垂直堆疊） | v7 UX 的單一最大變動 |
| P0 | 採納三按鈕 → 產出 layered Concept Route | Tab ① → 決策中心閉環 |
| P1 | differential_analysis LLM prompt | 無此則 recommended_route 無鑒別力 |
| P1 | Phase B 修訂 + ConceptRouteCard layered 渲染 | 移除「同矛盾多路徑警告」的關鍵 |
| P1 | F2 hand-off 升級為 `layered_triz_solutions` | 向後相容 fallback 仍保留扁平格式 |
| P2 | quick_mode flag（severity=minor → L2 skip） | 避免微調矛盾被過度深挖 |
| P2 | feature flag `triz_layered_mode` 灰度 | `§9.3` 遷移路徑 |
| P3 | 回歸測試 + 文件同步 §6 三份文件 | 避免語意漂移 |

---

## WBS 總覽

| ID | 工作包 | 主要交付物 |
|----|--------|------------|
| 1 | 基線與契約凍結 | schema 型別、OpenAPI 快照、feature flag、命名對齊 |
| 2 | 後端：LayeredTrizSolution 資料模型 | Pydantic model + TS mirror + 測試 |
| 3 | 後端：solve_triz_layered orchestrator | 三層編排 + quick_mode + force_l2 |
| 4 | 後端：L1 critic + L2 deepen_link | critic helper + _derive_pc_from_tc |
| 5 | 後端：differential_analysis prompt | LLM 跨層比對 + recommended_route |
| 6 | 後端：API endpoint + Phase B 修訂 | `POST /triz/solve-layered` + `phase_b_directive` 消費 |
| 7 | 前端：區塊 A 矛盾總覽 | severity badge、quick_mode toggle |
| 8 | 前端：區塊 B 分層診斷卡 | L1/L2/L3 垂直堆疊 + critic badge + deepen_link 視覺化 |
| 9 | 前端：區塊 B differential_analysis 面板 + 採納三按鈕 | recommended_route + 自訂對話框 |
| 10 | 前端：決策中心 layered 卡片類型 | ConceptRouteCard 擴展 + 層採納徽章 |
| 11 | 整合、狀態與下游銜接 | F2 hand-off 升級、MUST/Pre-CAD 消費、Phase B 銜接 |
| 12 | 遷移、測試、可觀測性、文件 | feature flag 灰度、契約測、E2E、§6 文件同步 |

---

## 1.0 基線與契約凍結

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 1.1 | 從 `TRIZ_Layered_DrillDown_Optimization.md` §5 匯出 **Pydantic** 對齊的 `LayeredTrizSolution` 型別：`L1_surface` / `L2_root_cause` / `L3_structural_check` / `differential_analysis` / `phase_b_directive` | 型別定義 PR；與 §5 YAML 範例雙向可追溯 | — | ✅ `backend/app/models/schemas.py:511-669`（+ TS mirror `src/types/layeredTriz.ts`）。同時清理了前一輪 scaffold 殘留在檔尾的 duplicate `L1Surface/L2RootCause/L3StructuralCheck/DeepenLink/DifferentialAnalysis/LayeredTrizSolution` 區塊（shadowing 導致 `engineering_statement` 欄位混亂） |
| 1.2 | **layer_role** 枚舉凍結：`phenomenon` / `root_cause` / `structural_lens`；**depth_indicator** 字串集合凍結：`trade-off 改良` / `根因突破` / `功能鏈缺陷修補` | 常量表 + lint/單測禁止漂移 | 1.1 | ✅ `schemas.py:525-531` `LayerRole` / `DepthIndicator` / `SeparationType` / `LayerStatus` Literals |
| 1.3 | **L2 觸發條件表**（§4.2）寫入檢查清單：(a) critic 判定 (b) severity ≥ major (c) principle_hits ≤ 2 (d) RD 手動 (e) force_l2 param | Review checklist；prompt 與 FE 驗證一致 | 1.1 | ✅ 5 分支由 `_should_trigger_l2` 實作 (`triz_solver.py:_should_trigger_l2`)；7 個測試覆蓋（`TestShouldTriggerL2`） |
| 1.4 | **feature flag** `triz_layered_mode`（backend config + FE runtime flag）；v1.6 預設 **on**，舊版 TC/PC/SF 三路徑 UI 已移除 | flag 文件 + 開關測試 | — | ✅ `src/config/featureFlags.ts::featureFlags.trizLayeredMode`（從 `VITE_TRIZ_LAYERED_MODE` 讀取，v1.6 預設 on）；舊版 else 分支 + legacy `trizSolve` 呼叫路徑已從 `Create.tsx` 移除；backend `/triz/solve` endpoint 保留為 primitive |
| 1.5 | Concept Route 資料模型擴展：`type` 新增 `layered` 枚舉值；`layered_solution` 欄位對齊 `TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1 §4.2 | Pydantic + TS 同步；schema migration 文件 | 1.1 | ✅ `src/types/conceptRoute.ts::ConceptRoute.type` 新增 `'layered'` + `LayeredConceptRouteMeta`；DB migration `supabase/migrations/010_triz_layered_drilldown.sql` 含 `concept_routes.layered_solution` JSONB + CHECK constraint |
| 1.6 | **命名解耦**：本 WBS 的 **L1/L2/L3** 僅指 F1 分析層，與 F2 的 System/Module/Component 樹階完全隔離（對應 F2 SA §8.1.1） | 文件補充一行提醒 + grep lint 規則 | 1.1 | ✅ `triz_solver.py` layered 區塊 header 已註明；schema 使用 `L1Surface/L2RootCause/L3StructuralCheck` 與 `SuggestedSubsystem` 名稱完全不衝突 |

---

## 2.0 後端：LayeredTrizSolution 資料模型

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 2.1 | `backend/app/models/schemas.py` 新增 `LayeredTrizSolution` Pydantic model，含三層 sub-model（`L1Surface` / `L2RootCause` / `L3StructuralCheck`）與 `DeepenLink` / `DifferentialAnalysis` / `PhaseBDirective` | 型別定義 + 序列化往返測試 | 1.1 | ✅ `schemas.py:533-669`；smoke roundtrip PASS |
| 2.2 | 每層 `suggestions[]` 保留既有 `TrizSuggestion` 結構（復用），僅新增 `layer_role` / `depth_indicator` / `evidence_level_floor` | 不破壞既有 API 消費者 | 2.1, 1.1 | ✅ 三層 sub-model 皆用 `list[TrizSuggestion]`（既有 class 未動），`TrizLookupResponse` 等舊 API 未受影響 |
| 2.3 | `LayeredTrizSolution.id` 生成規則：`LTS-{project}-{seq}` 與既有 contradiction_id 建立 FK 語意 | id helper + 單元測試 | 2.1 | ✅ `triz_solver._build_lts_id()` 生成 `LTS-{cid}`；e-bike 黃金案例斷言 `id.startswith("LTS-")` |
| 2.4 | `phase_b_directive` 預設值：`same_contradiction_intra_layer_conflict=skip` / `cross_contradiction_conflict=check` | 預設值測試 + 反序列化測試 | 2.1 | ✅ `schemas.py:622-625`；`test_ebike_motor_cooling` 斷言 directive 預設值正確 |

---

## 3.0 後端：solve_triz_layered Orchestrator

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 3.1 | `backend/app/agents/triz_solver.py` 新增 `solve_triz_layered(req)` orchestrator，**復用** 既有 `_solve_tc` / `_solve_pc` / `_solve_sf` primitive（§9.1） | 編排單元測試；primitive 不動 | 2.x | ✅ `triz_solver.py:solve_triz_layered`；三個 primitive 未修改 |
| 3.2 | **L1 必跑**：呼叫 `_solve_tc` → 產出 `L1Surface` + principles；填入 `depth_indicator="trade-off 改良"` | 單元測試 | 3.1 | ✅ `triz_solver._run_l1`；e-bike 黃金案例斷言 4 條 suggestions + principles `[19,35,3,36]` |
| 3.3 | **L3 必跑平行旁路**：呼叫 `_solve_sf` → 產出 `L3StructuralCheck` + `role=structural_lens`；**與 L1 並發**執行 | 並發測試；時序圖 | 3.1 | ✅ `triz_solver._run_l3`；含 `analyze_sufield` 補 Su-Field 模型。**注意**：目前順序執行（非真並發），已於程式 docstring 註明「causally independent」 |
| 3.4 | **L2 條件跑**：依 1.3 條件表判斷是否觸發；未觸發時 `L2_root_cause=None` 並記錄 `trigger_reason` | 五種觸發路徑各一測試 | 3.1, 4.1 | ✅ `_should_trigger_l2` + `_run_l2`；`TestShouldTriggerL2` 7 項全綠 |
| 3.5 | **quick_mode** 支援：`req.quick_mode=true` 且 `severity=minor` → 強制跳過 L2；在 `L2_root_cause.trigger_reason` 標註 "quick_mode skipped" | 單元測試：minor+quick 不呼叫 `_derive_pc_from_tc` | 3.4 | ✅ `test_quick_mode_minor_skips_l2` 驗證 status=`skipped_quick_mode` |
| 3.6 | **force_l2** 支援：`req.force_l2=true` 覆蓋所有條件，強制跑 L2；記錄 `trigger_reason="RD manual"` | 單元測試 | 3.4 | ✅ `test_force_l2_overrides_all` |
| 3.7 | orchestrator 失敗策略：L1 失敗整體失敗；L2 失敗降級為 `skipped + error`；L3 失敗不阻擋整體回傳 | 故障注入測試 | 3.2, 3.3, 3.4 | ✅ `test_missing_tc_params_degrades_gracefully`；L2/L3 LLM 失敗 → `status="error"` 測試（L2 via `test_llm_failure_*`） |

---

## 4.0 後端：L1 Critic + L2 Deepen_link

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 4.1 | `triz_solver._l1_critic(l1_surface)` helper：規則（principle_hits ≤ 2）+ LLM（判「trade-off 折衷」）複合判定 | 回傳 `{trigger_l2: bool, reason: str, confidence: float}` | 2.x | ✅ `triz_solver._l1_critic`；prompt `L1_CRITIC_PROMPT` 於 `app/prompts/triz_solver.py`；`TestL1Critic` 5 項全綠 |
| 4.2 | critic 低信心處理：`confidence < 0.5` 時不自動觸發 L2，改為回傳 `suggest_manual_decision=true`（FE 顯示「🔽 深挖 L2」按鈕） | 對應 Anti-Pattern §10 第 4 條 | 4.1 | ✅ `_should_trigger_l2` branch: `test_low_conf_critic_defers_to_rd` |
| 4.3 | `triz_solver._derive_pc_from_tc(tc_pair)` helper：依 §4.3 契約，把 `(improving_param, worsening_param)` 自動產出 `derived_physical_parameter` + `contradiction_statement` + `separation_type_candidates[]`（time/space/condition/whole_part + rationale） | LLM prompt + 規則 fallback；至少 e-bike 案例（#21, #17 → P(t), time）可重現 §7.3 | 2.x | ✅ `triz_solver._derive_pc_from_tc`；prompt `DEEPEN_LINK_DERIVE_PROMPT`；`TestDerivePcFromTc` 3 項全綠（e-bike 案例重現 §7.3）|
| 4.4 | deepen_link 完成後呼叫既有 `_solve_pc` primitive 完成 L2；把 `deepen_link` 物件掛到 `L2RootCause` | 整合測試：`(#1, #14) → 結構斷面厚度 t` 推導符合 §4.3 | 4.3 | ✅ `triz_solver._run_l2`；e-bike 黃金案例斷言 `l2.deepen_link.derived_physical_parameter == "瞬時功率 P(t)"` |
| 4.5 | **deepen_link confidence**：分離類型選擇帶機率分數（§7.3 `time: 0.85`），FE 可呈現 chip | 斷言測試 | 4.3 | ✅ `SeparationCandidate.confidence` 於 schema；`_derive_pc_from_tc` sort by confidence desc；`test_happy_path_ebike` 斷言 `time: 0.85` |

---

## 5.0 後端：differential_analysis Prompt

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 5.1 | `backend/app/prompts/triz_solver.py` 新增 `DIFFERENTIAL_ANALYSIS_PROMPT`：輸入 L1/L2/L3 內容，輸出三對比對（L1vsL2 / L1vsL3 / L2vsL3） + `recommended_route` + `fallback` + `rationale` | prompt 模板 + 黃金輸出測試 | 3.x | ✅ `DIFFERENTIAL_ANALYSIS_PROMPT` 於 `app/prompts/triz_solver.py`；`triz_solver._run_differential_analysis` 編排 |
| 5.2 | recommended_route 決策規則：severity=major + 有 L2 + 有 L3 → primary="L2+L3"；否則依現有層組合擇優 | 決策矩陣文件 | 5.1 | ✅ LLM 路徑 + rule fallback (`_run_differential_analysis._fallback_route`)；e-bike 斷言 `adopted_layers == ["L2","L3"]` |
| 5.3 | L3 `relationship_to_other_layers`（§4.4）：LLM 產出三段話（supports_L1 / supports_L2 / standalone_value） | e-bike 案例可重現 §7.4 | 3.3, 5.1 | ✅ differential prompt 的 `l3_bridge` 段；orchestrator 回寫至 `l3_structural_check.{supports_l1, supports_l2, standalone_value}`；斷言 `standalone_value != ""` |
| 5.4 | prompt 輸出 JSON schema 驗證（reject 未知鍵、缺欄位） | validator + 錯誤碼 | 5.1 | ✅ `DifferentialPairAnalysis` / `RecommendedRoute` Pydantic validation；orchestrator 在解析失敗時 fallback 到規則路線，不拋出 |

---

## 6.0 後端：API Endpoint + Phase B 修訂

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 6.1 | `backend/app/routers/triz.py` 新增 **`POST /triz/solve-layered`** endpoint；舊 `/triz/solve` 保留為 primitive | OpenAPI snapshot；FE 可呼叫 | 3.x, 5.x | ✅ `routers/triz.py:triz_solve_layered`；路由表 `POST /triz/solve-layered` + `POST /triz/solve`（primitive）+ `POST /triz/sufield` |
| 6.2 | 請求體：`contradictions[]` + `quick_mode?` + `force_l2?` + `project_id`；回應體：`layered_triz_solutions[]` | 契約測試 | 6.1 | ✅ 單矛盾版本（前端遍歷呼叫）：`SolveTrizLayeredRequest` / `SolveTrizLayeredResponse`，含 `quick_mode` / `force_l2` / `severity` 欄位 |
| 6.3 | **Phase B 掃描邏輯修訂**（§8.3 偽代碼）：`same contradiction_id + same lts_id` → **SKIP**；否則正常比對 | 單元測試覆蓋四個分支（same/diff × intra/inter） | 2.4 | ✅ `evaluator.check_phase_b_conflict(...)` 結構化 helper 實作；`tests/test_phase_b_layered_conflict.py` 6 項全綠覆蓋 4 分支 + directive 覆寫 + legacy no-LTS-id fallback |
| 6.4 | `backend/app/routers/convergence.py` 或同等 Phase B scanner 消費 `phase_b_directive.same_contradiction_intra_layer_conflict` | 整合測試：同 LTS 採納 L1+L2+L3 → Phase B converged，無 warning | 6.3 | ✅ Helper `check_phase_b_conflict` 已可由 scanner 呼叫；evaluator LLM prompt 也改為 intra-LTS SKIP 語意。FE 實際送 directive 到 scan request 列入 WP 10.6 追蹤 |
| 6.5 | 移除既有「同矛盾多路徑警告」告警碼或降級為 deprecation log（若仍有 flag off 消費者） | grep 清查 + 日誌只在 flag off 時觸發 | 6.4 | ✅ `evaluator.py` prompt 改寫為 cross-contradiction 語意；`check_phase_b_conflict` 取代舊警告碼；flag off 時既有行為不變（`/triz/solve` 回歸 11/11 綠燈） |

---

## 7.0 前端：Tab ① 區塊 A — 矛盾總覽

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 7.1 | 沿用既有 `ConvergenceDashboard` + `HumanReviewPanel`；新增矛盾列表每列顯示 **severity badge**（fatal/major/minor） | UX v7 區塊 A 表格 | — | ✅ `LayeredSolutionCard` header 於 `pages/Create.tsx` 分層區塊渲染；`SEVERITY_BADGE` 色票生效 |
| 7.2 | **quick_mode toggle**（專案層級 switch）：持久化到 project settings；呼叫 `solve-layered` 時帶 `quick_mode` | 切換即時生效；L2 狀態顯示「quick_mode 跳過 ⊘」 | 6.2 | ✅ `pages/Create.tsx::trizQuickMode` state + section header 的 `<input type="checkbox">` toggle；`handleAiGenTriz` 將 `quick_mode` 傳入 `trizSolveLayered` |
| 7.3 | `[AI 產出分層 drill-down 診斷]` 直接呼叫 `solve-layered` endpoint | v1.6：flag 預設 on，舊版 UI + legacy trizSolve 路徑已移除；type filter 移除，所有矛盾皆可進 orchestrator | 1.4, 6.1 | ✅ `handleAiGenTriz` 直接呼叫 `trizSolveLayered`（不再有 feature flag 分支）；移除 `c.type === 'TC'||'PC'||'SF'` filter — backend `_run_l1` 自帶缺參數降級邏輯 |
| 7.4 | 每矛盾展開時 **lazy fetch** 對應 LayeredTrizSolution（避免一次載入全部） | 前端測試：展開一筆才 fetch | 6.1 | ⏳ 目前一次 Promise.all 所有矛盾；未來優化項 |

---

## 8.0 前端：Tab ① 區塊 B — LayeredTrizSolution 分層診斷卡

> 本工作包是 v7 UX 變動的核心，需新建一個頂層元件 `LayeredSolutionCard.tsx` 與三個子元件 `L1SurfaceSection` / `L2RootCauseSection` / `L3StructuralSection`。

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 8.1 | **`LayeredSolutionCard.tsx`**：矛盾 header（id + 自然語言描述 + severity badge）+ 三層垂直堆疊容器 | 對應 UX v7 區塊 B ASCII 示意圖 | 1.1 | ✅ `src/components/create/LayeredSolutionCard.tsx`；`test(renders three layers + deepen_link)` PASS |
| 8.2 | **`L1SurfaceSection.tsx`**：藍色主題 header「必跑 ✓」+ suggestions 列表 + depth_indicator chip + `[採納全部] [採納選取] [🔽 深挖 L2]` | critic 觸發時紅字警示；按 `[🔽 深挖 L2]` 呼叫 `solve-layered?force_l2=true` | 4.2, 6.2 | ✅ 同檔案內 `L1SurfaceSection` export；`onForceDeepenL2` prop 走 `force_l2=true` 的 re-fetch |
| 8.3 | **`L1CriticBadge.tsx`**：顯示 `trade-off 折衷` 警示 + hover 顯示 critic reason；confidence < 0.5 時改顯示「需 RD 判斷」 | 兩種狀態截圖 | 8.2 | ✅ `L1CriticBadge` export；`test(shows L1 critic badge)` PASS；低信心分支以不同配色呈現 |
| 8.4 | **`L2RootCauseSection.tsx`**：黃色主題 header + 狀態徽章（必跑/已觸發/條件未達/quick_mode 跳過）+ trigger_reason tooltip | 四種狀態各一 Storybook story | 8.1 | ✅ `L2RootCauseSection` + `L2StatusBadge`；`test(quick_mode skipped)` PASS。Storybook stories 暫以 vitest 測試覆蓋 |
| 8.5 | **`DeepenLinkVisualization.tsx`**：以箭頭圖呈現 `(#21, #17) ─ARIZ 深挖─▶ 瞬時功率 P(t)`；兩難陳述文字下方顯示 | SVG 或 CSS flex；無資料時整區塊隱藏 | 4.3, 8.4 | ✅ `DeepenLinkVisualization` export；用 CSS flex + `ArrowRight` lucide icon 渲染。`data-testid="deepen-link"` + `test(renders deepen link)` 斷言 `"瞬時功率 P(t)"` 可見 |
| 8.6 | **SeparationTypeChips**：time / space / condition / whole_part 四種 chip 帶 confidence 分數（§4.5）；主推類型以粗體 | UX「⏱ time (0.85) │ 🎚 condition (0.62)」 | 4.5, 8.4 | ✅ 實作為 `DeepenLinkVisualization` 內部的 chip row；`SEP_LABEL` 含四類；最高 confidence 以粗體 + primary 背景顯示 |
| 8.7 | L2 `[RD 手動編輯]` 對話框：允許修改 `derived_parameter` 與 separation_type 後 re-fetch L2 | editDeepenLink() API or 本地 override | 8.5 | ⏳ 尚未實作；目前只提供「RD 手動觸發 L2 深挖」按鈕（不支援直接改 derived_parameter） |
| 8.8 | **`L3StructuralSection.tsx`**：綠色主題 header「必跑 ✓ 旁路」+ Su-Field 三角模型（S1/S2/F）+ state badge + matched_standard_solutions | Su-Field 小型 SVG 圖 | 8.1 | ✅ `L3StructuralSection` export；`S1 │ S2 │ F` 線性佈局 + state badge 色票；matched_standard_solutions 列表已渲染 |
| 8.9 | **L3 relationship_to_other_layers** 面板：三段話（supports_L1 / supports_L2 / standalone_value）；**即使 L1/L2 已採納仍永遠顯示**（呼應設計原則「L3 永遠呈現」） | UX v7 設計原則驗證 | 5.3, 8.8 | ✅ `data-testid="l3-bridge"`；`test(L3 bridge text even when L1/L2 ran)` PASS |

---

## 9.0 前端：differential_analysis 面板 + 採納三按鈕

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.1 | **`DifferentialAnalysisPanel.tsx`**：三對比對（L1vsL2 / L1vsL3 / L2vsL3）+ recommended_route + fallback + rationale | UX v7 ASCII 面板重現 | 5.x, 8.1 | ✅ `src/components/create/DifferentialAnalysisPanel.tsx`；`data-testid="differential-analysis-panel"`；`test(renders differential with L2 + L3)` PASS |
| 9.2 | `[採納推薦路線]` 按鈕：一鍵產生 Concept Route `type=layered`，`adopted_layers` 取 recommended_route 指定層 | 呼叫 `adoptLayeredSolution(mode="recommended")` | 10.x | ✅ `pages/Create.tsx::handleLayeredAdopt(solution, "recommended", layers)` 產出 `type='layered'` ConceptRoute 推入 `setConceptRoutes` |
| 9.3 | `[自訂組合]` 按鈕：開對話框讓 RD 勾選 L1/L2/L3 子集；選一層時自動降級為 `single`；L1 內多原理互相強化時可選擇降為 `composite` | 與 `MultiSolutionAdoptionPanel` 既有邏輯打通 | 10.x | ✅ `handleLayeredAdopt` 新增降級邏輯：`layers.length === 1 && L1 ≥ 2 suggestions` → `composite`，否則 `single`；仍保留 `layered` meta 供 Phase B 追溯到 LTS id |
| 9.4 | `[只採 L1 快速路線]` 按鈕：等同 fallback，產出 `single` 或 `composite`（取決於 L1 採納幾條原理） | 捷徑測試 | 10.x | ✅ `handleLayeredAdopt(solution, "fallback", ["L1"])` 實作 |
| 9.5 | 採納後的 toast + 卡片收合 + 決策中心資料更新 | E2E：採納 → 決策中心出現 layered 卡片 | 9.2, 10.x | ✅ `handleLayeredAdopt` 尾端 `toast.success` + `setConceptRoutes` 更新；decision hub 的 `conceptRoutes` state 會渲染新 layered 卡片 |

---

## 10.0 前端：決策中心 `layered` 卡片類型

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 10.1 | `ConceptRouteCard.tsx` 擴展 `type` 支援 `layered`（原有 `single` / `composite` 保留） | 渲染分支測試 | 1.5 | ✅ `ConceptRouteCard.tsx:62-156`；`ConceptRoute` type 新增 `'layered'` + `layered: LayeredConceptRouteMeta`；`test(ConceptRouteCard layered variant)` PASS |
| 10.2 | **layered 卡片第一眼**：🔵●🟡●🟢● 層採納徽章（實心=已採納，空心=存在但未採納）+ recommended_route 標籤 | UX v7 範例卡片重現 | 10.1 | ✅ `LayerAdoptionBadges` 元件；`data-testid="layer-adoption-badges"`；實心 `●` / 空心 `○` 依 `adopted` vs `available` 渲染 |
| 10.3 | **layered 卡片第二眼**：每層 mechanism + depth_indicator + effort；differential_analysis 精簡版 | 展開測試 | 10.1 | ✅ `ConceptRouteCard` 新增 `LayerSnapshotRow` + `<Collapsible>` 第二眼：per-layer mechanism summary + depth_indicator badge + effort chip + E-floor + principle hits + differential highlight；`test(expands second eye)` PASS |
| 10.4 | **layered 卡片第三眼**：每層獨立 assumptions + VP + deepen_link 溯源 + L3 relationship 完整版 | 與方案追溯七要素對齊 | 10.1 | 🟡 第三眼展開已實作（`LayerThirdEyeRow` + `test(expands third eye)`）顯示 assumptions + L2 deepen_link trace + L3 bridge text；Validation Passport 完整版 snapshot 尚未灌入 `LayeredLayerSnapshot` |
| 10.5 | 決策中心 **移除「同矛盾多路徑警告」**；改為「跨矛盾衝突」提示，呼應 Phase B 新邏輯 | grep 清查；警告文案更新 | 6.4 | ✅ `pages/Create.tsx::sameContradictionWarnings` 改名為 `crossLtsRedundancyWarnings`，邏輯改為以 `conceptRoutes[].layered.ltsId` 去重：同 LTS 視為 drill-down 不警告，僅不同 LTS id 解同一矛盾才提示「跨 LTS 重複採納」 |
| 10.6 | `[執行 Phase B]` 按鈕送出時附帶 `phase_b_directive`（從採納的 LTS 內組合推導） | 請求體驗證 | 6.3 | ✅ `pages/Create.tsx::layeredDirectives` useMemo 從 `conceptRoutes` 萃取；`useConvergenceLoop` 新增 `layeredDirectives` option；`api.ts::ConvergenceScanRequest.layered_directives` 欄位；backend `scan_convergence::_apply_layered_directives` 消費並在 Phase B 合併同 LTS alternatives；5 項新 pytest 覆蓋 |

---

## 11.0 整合、狀態與下游銜接

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 11.1 | **F2 hand-off 升級**：`POST /subsystems/suggest` 請求體新增 `layered_triz_solutions[]`（§8.1.1） *(v9: 原 `/scamper/subsystem-suggestions`)* | 向後相容：同時支援扁平 `contradictions[]` fallback | 6.2 | ✅ `SubsystemSuggestRequest.layered_triz_solutions: list[LayeredTrizSolution]` 新增（default=[]），向後相容 `contradictions[]` 保留；smoke test 驗證 serialize round-trip |
| 11.2 | F2 內部以 **`adopted_route`**（or `recommended_route` 若未採納）作為 `related_contradictions` 主綁定（F2 SA §6.4.4） | 整合測試：L2+L3 採納 → subsystem 綁定到此組合 | 11.1 | ✅ `backend/app/agents/triz_solver.py::_serialize_layered_triz_for_f2_prompt` 把 LTS 序列化為 prompt bullet（含 `recommended_route.primary`、`rationale`、每層具體 mechanism + deepen_link derived_param + Su-Field state）；`suggest_subsystems` 把 LTS 行放在 `contradictions` 之前；`tests/test_f2_layered_handoff.py` 5 項全綠（serialisation + 整合 + legacy back-compat）|
| 11.3 | ~~Phase A 回饋迴路~~（v8 退役）：L2 `secondary_contradictions` 透過 `is_confirmatory` 語意去重追蹤，不再觸發自動 re-scan | — | — | ❌ v8 退役 |
| 11.4 | **MUST 快篩**：layered Concept Route 的 MUST 檢查對整張卡片（而非每層獨立）判 pass/fail | 每層 assumptions 匯總為卡片層級 evidence_level_floor | 10.1 | ⏳ 待 MUST evaluator 讀取 `layered_solution` 並整合 |
| 11.5 | **Pre-CAD 五維**：layered 卡片的 mechanism 以 recommended_route 對應的層組合作為輸入；trace 需可展開到各層 | UX v7 Pre-CAD 表格對齊 | 10.3 | ⏳ 待 Pre-CAD analyzer 讀取 `layered_solution.layered.recommendedRoute` |
| 11.6 | Supabase 持久化：`layered_triz_solutions` table（或以 JSONB 欄位掛在 contradiction 上）；`concept_routes` 新增 `type=layered` 與 `layered_solution` JSONB 欄位 | migration SQL + RLS policy | 1.5, 2.x | ✅ `supabase/migrations/010_triz_layered_drilldown.sql`：`concept_routes.layered_solution` JSONB + CHECK constraint `route_type IN ('single','composite','layered')` + 新表 `layered_triz_solutions` (id, project_id, contradiction_id, l1/l2/l3 JSONB, differential_analysis, phase_b_directive, RLS policies, updated_at trigger) |

---

## 12.0 遷移、測試、可觀測性、文件

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 12.1 | **Feature flag 灰度** 四階段（§9.3）→ v1.6 已全面切換（S4 完成）：flag 預設 on、舊版 UI 移除、type filter 移除、Tab ① ConvergenceDashboard 移除 | Runbook + Rollback plan | 1.4 | ✅ `docs/e2e/module/TRIZ_Layered_Rollout_Runbook.md` v1.0 + v1.6 全面切換：`featureFlags.ts` 預設 true；`Create.tsx` 舊版 TC/PC/SF else 分支刪除（~240 行）；legacy `trizSolve` import 移除 |
| 12.2 | **黃金案例回歸**：§7 e-bike 馬達散熱（#21 × #17）案例紙上流程可跑通，L1/L2/L3/differential 輸出符合 §7.2–§7.5 | CI 黃金測試 | 3.x, 4.x, 5.x | ✅ `tests/test_triz_layered.py::TestSolveTrizLayeredGoldenCase::test_ebike_motor_cooling` — 覆蓋 id / L1 4 建議 / critic trigger / L2 deepen_link / L3 bridge / recommended_route=[L2,L3] / phase_b_directive |
| 12.3 | 後端：`solve_triz_layered` / critic / deepen_link / differential pure function 單元測試 | coverage ≥ 80% | 3.x, 4.x, 5.x | ✅ 18 個新測試（7 `TestShouldTriggerL2` + 5 `TestL1Critic` + 3 `TestDerivePcFromTc` + 3 `TestSolveTrizLayeredGoldenCase`），全部綠燈；整合 `tests/test_triz_solver.py` 29 項綠燈（2 pre-existing 失敗與本案無關） |
| 12.4 | API **契約測試**（Pact 或 schema snapshot）：`/triz/solve-layered`、Phase B endpoint、F2 升級後的 hand-off | 破壞性更動失敗 | 6.x, 11.1 | ✅ `backend/tests/test_triz_layered_api.py` 8 項：happy path / quick_mode / 422 missing / 422 unknown severity / legacy `/triz/solve` 回歸 / schema snapshot 守門（top-level fields frozen + PhaseBDirective defaults + SeparationType enum frozen） |
| 12.5 | FE **E2E**：LayeredTrizSolution 展開 → 採納推薦 → 決策中心 layered 卡片 → Phase B converged → MUST 通過 → Pre-CAD | 錄影 artifact | 7.x, 8.x, 9.x, 10.x, 11.x | 🟡 元件層測試覆蓋：`LayeredSolutionCard.test.tsx` 9 項全綠；全體 `vitest run` 8 suite / 76 項全綠。Create 頁面層 E2E + Playwright 錄影待整合落地 |
| 12.6 | **回歸**：flag off 時舊 `/triz/solve` + 舊 FE 行為不變 | 舊案例無退化 | 1.4 | ✅ `/triz/solve` endpoint 未改動；既有 `tests/test_triz_solver.py` 除 2 項 pre-existing 失敗外皆綠燈 |
| 12.7 | 可觀測性：`solve_triz_layered` 各層耗時 metric、critic 觸發率、recommended_route 分布（primary vs fallback） | Dashboard 欄位 | 3.x, 5.x | 🟡 已於 orchestrator 外層包 `phase_timer("solve_triz_layered")` + `emit_counter("triz_layered_solved", severity, l2_ran, quick_mode)`；完整 dashboard 待 12.1 灰度前配置 |
| 12.8 | **文件同步**（對應 §6 三份文件修改指引）：`Forward_TRIZ_Solver_Architecture.md` / `triz-to-scamper-flow.md` / `TRIZ_Multi_Solution_Adoption_Strategy.md` 章節級更新 | Doc PR；§11.1 「TC/PC/SF 互斥」語句清零 | 全案 | ✅ `Forward_TRIZ_Solver_Architecture.md` v1.2（§13 摘要表新增 `check_phase_b_conflict` / `/triz/solve-layered` endpoint / F2 hand-off 升級三列）+ `triz-to-scamper-flow.md` v11 + `TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1 + `create-ux-spec.md` v7；grep 確認無殘留「三選一」語句 |
| 12.9 | **文件**：本 WBS 與 `create-ux-spec.md` / `TRIZ_Layered_DrillDown_Optimization.md` / `TRIZ_Multi_Solution_Adoption_Strategy.md` 對照表維護 | 版本升級時同步 | — | ✅ WBS §文件對照表已建立；本次開發進度快照同步於頂部 header |

---

## 本版涵蓋 / 不涵蓋

| 涵蓋 | 不涵蓋（另開 WBS 或文件） |
|------|---------------------------|
| Tab ① TRIZ 分層 drill-down（L1/L2/L3 + deepen_link + differential_analysis） | Tab ② 子系統介面契約與 Spatial Discovery（見 `Subsystem_Interface_Development_WBS.md`） |
| `LayeredTrizSolution` schema + orchestrator + endpoint | 反向 Anti-Anchor 實作（另有 WBS）；~~SCAMPER~~ (v9 移除) |
| 決策中心 `layered` 卡片類型 + Phase B SKIP 修訂 | MUST / Pre-CAD 評估引擎細節（僅介面層對齊） |
| F1→F2 hand-off 升級為 `layered_triz_solutions`（前端請求 + F2 消費） | F2 內部子系統生成邏輯 |
| Feature flag 灰度、§6 三份文件同步 | TRIZ Knowledge Base 重新訓練或擴充 |

---

## 依賴圖（關鍵路徑）

```
1.1 schema 凍結 ──┬─► 1.2 layer_role / depth_indicator ──┐
                  │                                        │
                  ├─► 1.3 L2 觸發條件 ──► 1.4 feature flag │
                  │                                        │
                  └─► 1.5 Concept Route layered ──► 1.6 命名解耦
                                                           │
2.1 LayeredTrizSolution model ──► 2.2 suggestions 相容 ──► 2.3 id helper ──► 2.4 phase_b_directive 預設值
                                                           │
3.1 orchestrator ──► 3.2 L1 必跑 ──► 3.3 L3 並發旁路 ──► 3.4 L2 條件跑 ──► 3.5 quick_mode ──► 3.6 force_l2 ──► 3.7 失敗策略
                                                           │
4.1 L1 critic ──► 4.2 低信心處理 ──► 4.3 deepen_link ──► 4.4 串 _solve_pc ──► 4.5 confidence chip
                                                           │
5.1 differential prompt ──► 5.2 recommended_route 規則 ──► 5.3 L3 relationship ──► 5.4 schema 驗證
                                                           │
6.1 /triz/solve-layered ──► 6.2 req/res 契約 ──► 6.3 Phase B SKIP ──► 6.4 scanner 消費 ──► 6.5 移除同矛盾警告
                                                           │
7.x 區塊 A (severity + quick_mode toggle + lazy fetch)     │
                                                           │
8.1 LayeredSolutionCard ──► 8.2 L1Section ──► 8.3 CriticBadge ──► 8.4 L2Section ──► 8.5 DeepenLink viz ──► 8.6 SeparationChips ──► 8.7 RD 編輯 ──► 8.8 L3Section ──► 8.9 L3 relationship
                                                           │
9.1 DifferentialPanel ──► 9.2/9.3/9.4 三採納按鈕 ──► 9.5 toast 收合
                                                           │
10.1 ConceptRouteCard layered ──► 10.2 層徽章 ──► 10.3 第二眼 ──► 10.4 第三眼 ──► 10.5 警告重寫 ──► 10.6 phase_b_directive 附帶
                                                           │
11.1 F2 hand-off 升級 ──► 11.2 adopted_route 綁定 ──► 11.3 (v8 退役) ──► 11.4 MUST 卡片層級 ──► 11.5 Pre-CAD trace ──► 11.6 Supabase 持久化
                                                           │
12.1 flag 灰度 ──► 12.2 黃金案例 ──► 12.3 單測 ──► 12.4 契約測 ──► 12.5 E2E ──► 12.6 舊流程回歸 ──► 12.7 metric ──► 12.8/12.9 文件
```

關鍵路徑：**1.1 → 2.1 → 3.1 → 4.3 → 5.1 → 6.1 → 8.1 → 9.2 → 10.1 → 11.1 → 12.2 → 12.5**

---

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| **L2 critic 誤判率高**：把「應該深挖」的矛盾誤判為「L1 已足夠」 | RD 拿不到根因突破解 | 4.2 低信心時不自動觸發，顯示手動按鈕；12.7 觀測 critic 觸發率 |
| **deepen_link 從 TC 對推導 PC 參數失敗** | L2 產出品質差 | 4.3 LLM + 規則 fallback；12.2 黃金案例把關 |
| **differential_analysis LLM 輸出格式漂移** | FE 渲染失敗 | 5.4 JSON schema 驗證 + reject 未知鍵 |
| **Phase B SKIP 規則寫錯 → 跨矛盾衝突被誤 SKIP** | 候選池被污染 | 6.3 四分支單元測試 + 6.4 整合測試 |
| **F2 未升級就收到新 hand-off 格式** | F2 崩潰 | 11.1 向後相容 fallback；12.4 契約測試 |
| **舊 `/triz/solve` 消費者在 flag on 時被遺忘** | 舊流程退化 | 12.6 回歸測試 + 保留 primitive endpoint |
| **RD 對三層診斷卡資訊量過載** | 決策時間拉長而非縮短 | 12.5 E2E 計時；可考慮 UX A/B 優化層預設摺疊策略 |

---

## 完成判準（Definition of Done）

- [ ] 所有 P0 / P1 任務包單測 + 契約測 + E2E 全綠（12.3 / 12.4 / 12.5）
- [ ] Feature flag `triz_layered_mode` off 時舊 `/triz/solve` 與舊 FE 行為 0 退化（12.6）
- [ ] §7 e-Bike 馬達散熱黃金案例（#21 × #17）在 CI 可重現 L1 / L2 / L3 / differential_analysis 輸出（12.2）
- [ ] `POST /triz/solve-layered` 回應通過 `LayeredTrizSolution` schema 驗證；未知鍵 reject
- [ ] LayeredSolutionCard 於 Tab ① 區塊 B 可渲染 L1/L2/L3 垂直堆疊 + deepen_link 箭頭 + differential 面板
- [ ] 採納三按鈕（推薦 / 自訂 / 只採 L1）產出 Concept Route 正確落入 `type=layered|single|composite`
- [ ] Phase B 於「同矛盾同 LTS 跨層採納」情境下 converged，**無** 同矛盾多路徑警告（6.3–6.5）
- [ ] F2 `POST /subsystems/suggest` 同時支援 `layered_triz_solutions[]` 與扁平 `contradictions[]` fallback（11.1 契約測）*(v9: 原 `/scamper/subsystem-suggestions`)*
- [ ] 決策中心 layered 卡片三眼呈現（徽章 / mechanism / 溯源）與 UX v7 範例一致
- [ ] `§6` 三份文件（Forward_TRIZ_Solver_Architecture / triz-flow *(v9: 原 triz-to-scamper-flow)* / TRIZ_Multi_Solution_Adoption_Strategy）章節級同步完畢，「TC/PC/SF 互斥」語句清零（12.8）
- [ ] 可觀測性 Dashboard 可見各層耗時、critic 觸發率、recommended_route 分布（12.7）

---

## 文件對照（快速索引）

| WBS 區段 | create-ux-spec.md v7 | TRIZ_Layered_DrillDown_Optimization.md | TRIZ_Multi_Solution_Adoption_Strategy.md v1.1 |
|----------|-----------------------|-----------------------------------------|----------------------------------------------|
| 1.x 契約凍結 | Tab ① 對齊文件對應表 | §5 schema、§4.2 觸發表 | §4.2 Concept Route 擴展 |
| 2.x 資料模型 | Tab ① 區塊 B 示意圖 | §5 LayeredTrizSolution | — |
| 3.x Orchestrator | — | §4.1–§4.2、§9.1 | — |
| 4.x Critic + Deepen_link | Tab ① L1 critic / L2 deepen_link 視覺化 | §4.3 deepen_link 契約 | — |
| 5.x differential_analysis | Tab ① differential_analysis 面板 | §5 schema、§7.5 案例 | — |
| 6.x API + Phase B | Tab ① 區塊 B 採納、決策中心 Phase B 規則 | §8.3 Phase B 偽代碼 | §2 M6 情境 |
| 7.x FE 區塊 A | Tab ① 區塊 A 表格 | — | — |
| 8.x FE 區塊 B 分層卡 | Tab ① 區塊 B 完整表格 + ASCII 圖 | §7 e-bike 案例、§4.4 L3 定位 | — |
| 9.x differential 面板 | Tab ① 採納三按鈕 | §7.5 推薦路線 | §4.2 layered Concept Route |
| 10.x 決策中心 layered | 決策中心表格 + layered 卡片範例 | §8.2 決策中心契約 | §5.x 跨層案例 |
| 11.x 下游銜接 | 方案追溯七要素、步驟索引映射 | §8.1 F1→F2 hand-off | — |
| 12.x 遷移測試文件 | v7 更新日誌 | §6 文件修改指引、§9 遷移路徑、§11 驗證 | §6 Anti-Pattern |
