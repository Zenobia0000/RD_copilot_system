# 子系統介面開發 WBS（Create · Tab ②）

> **版本**：1.0 | **日期**：2026-04-08 | **狀態**：Draft · 部分進行中 | **Owner**：Create FE + Subsystem Backend
> **範圍**：正向分析 E2E 內 **Tab ② 子系統定義**（F2 + F2.5）之 **介面契約、Spatial Discovery、Package Map、Overlay、RD override / learned** 的前後端開發與驗證。
> **對齊文件**：
> - `docs/diagrams/create-ux-spec.md` v6（區塊 A/B/C、API 觸發、視覺規範）
> - `docs/e2e/module/Forward_Subsystem_Discovery_Architecture.md` v2.1（容器、元件、資料模型、UC1–UC7、狀態機；§3.1 F1→F2 分層契約）
> - **`docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md`（L2 WBS）** — 新增 `parent_contradiction_id` 樹 + 子 PC 的 `subsystem_hint` / `derived_parameter` 會經由 L2 WBS **9.5 F2 input adapter** 注入本 WBS 2.1 的 `suggest_subsystems` prompt，**暫不切換**為完整 `LayeredTrizSolution[]` 輸入
> - **`docs/e2e/module/Explore_L3_SF_Parallel_Check_WBS.md`（L3 WBS, skeleton）** — 未來 L3 WBS 的 §6「F2 完整切換 `LayeredTrizSolution[]` 輸入」會取代 L2 WBS 9.5 的 adapter 預留，屆時本 WBS 的 2.1 / 2.2 / 2.3 需**同步更新**（見下方「L2/L3 跨 WBS 交叉影響」節）

---

## 使用者決策（已凍結）

| # | 項目 | 決策 | 備註 |
|---|------|------|------|
| 1 | 三層樹階層 | **System → Module → Component**，契約僅掛 **module** 節點 | 對齊架構 §6.4；與 F1 TRIZ 的 L1/L2/L3 命名完全隔離 |
| 2 | Spatial 真值來源 | **Layered Resolver L1–L4**（rd_override → learned → web → seed） | 引用 key 不存在 → confidence 降為 estimate |
| 3 | Discovery 失敗策略 | **non-blocking**：validator 掛了仍回樹，FE 友善退化 | 對齊架構 §4.1 |
| 4 | Package Map 渲染 | **後端輸出 SVG**（XY + XZ 正交視圖），FE 僅嵌入 | `render_package_map_svg` 為真值；inline SVG vs URL 於 2.2 定稿 |
| 5 | RD override 入口 | **UC3 `POST /spatial/component-overrides`** upsert 至 `project_component_overrides` | 下次 UC1 L1 命中；`reference_source=rd_override:<key>` |
| 6 | Discovery 與 Overlay 視覺分離 | 不共用同一 SVG 元件預設配色；Overlay 僅於對話框內呈現 | UX §Discovery vs Overlay |
| 7 | Tab ③ 解鎖閘 | **Tab ② RD 確認** 後方可進入 SCAMPER | 未確認時 Tab ③ disabled + 原因提示 |

---

## 邏輯流程（摘要）

```
Brief + 矛盾 → POST subsystem-suggestions → LLM 樹 + 契約
    → layered resolver 覆寫 spatial → validator 算 PackageMap + SVG
    → FE 呈現三層樹 + 6 維 + spatial badge + Package Map
    → RD 可 override / 推升 learned / 可選 overlay 試算
    → RD 確認 → 解鎖 Tab ③ SCAMPER；Pre-CAD 消費 deterministic spatial
```

---

## MVP 切分與建議順序

| 優先 | 標籤 | 說明 |
|------|------|------|
| P0 | 資料 + UC1 | 無此則 Tab ② 無法閉環 |
| P0 | 區塊 A 核心樹 + 契約顯示 | 與架構 §6.4 / §6.5 對齊 |
| P1 | 區塊 B Package Map | UX v6 與架構 §3.3 / validator 輸出 |
| P1 | UC3 override API + 最小 UI | L1 真值來源 |
| P2 | Confidence badge + reference_source hover | UX §Spatial Confidence |
| P2 | UC4 learned 推升 | Tab ② 與 Pre-CAD 批次推升可分期 |
| P3 | 區塊 C Overlay（UC5） | 可選、對話框隔離 |
| P3 | Pre-CAD spatial trace UI | create-ux-spec ④ 節 |

---

## WBS 總覽

| ID | 工作包 | 主要交付物 |
|----|--------|------------|
| 1 | 基線與契約凍結 | 介面型別、OpenAPI/契約快照、對照表 |
| 2 | 後端：UC1 建議管線 | `POST /scamper/subsystem-suggestions` 端到端 |
| 3 | 後端：Spatial 真值與驗證 | Resolver L1–L4 + `discover_package` + SVG |
| 4 | 後端：UC3 / UC4 | `POST /spatial/component-overrides`、`learned-components` |
| 5 | 後端：UC5 Overlay | `POST /scamper/spatial-overlay` |
| 6 | 前端：Tab ② 區塊 A | 三層樹、六維契約、spatial、確認閘 |
| 7 | 前端：Tab ② 區塊 B | Package Map 面板、clash、退化提示 |
| 8 | 前端：Tab ② 區塊 C | Overlay 對話框、與 discovery 視覺分離 |
| 9 | 整合、狀態與下游 | SCAMPER 解鎖、持久化、Pre-CAD 銜接 |
| 10 | 測試、可觀測性、文件 | 單測/契約測/E2E、錯誤碼、Runbook |

---

## 1.0 基線與契約凍結

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 1.1 | 從架構 §6 匯出 **TypeScript + Pydantic** 對齊的 `Subsystem` / `INTERFACE_CONTRACT` / `spatial` / `PackageMap` 欄位表 | 型別定義 PR；與 §6.1 JSON 範例雙向可追溯 | — | ✅ `schemas.py` + `src/types/generated/subsystem.ts` 鏡射 |
| 1.2 | **reference_source** 命名空間與 **confidence** 枚舉凍結（§6.2、UX §Spatial Confidence） | 常量表 + 禁止任意字串漂移的 lint/單測 | 1.1 | ✅ `test_reference_source_lint.py` (5 tests, 5 prefixes + 3 confidence values 鎖定) |
| 1.3 | **三層樹規則**（§6.4：system/module/component 數量、契約僅 module 層）寫入開發檢查清單 | Review checklist；prompt 與 FE 驗證一致 | 1.1 | ✅ `docs/e2e/module/Three_Tier_Tree_Review_Checklist.md` |
| 1.4 | **六維契約** 鍵名與「對鄰居」資料結構（§6.5.4 `Record<鄰居, SixDim>`）與 UI 折疊策略 | 資料結構文件截圖或範例 JSON | 1.1 | ✅ `InterfaceContract` + `InterfaceContractMap` + `INTERFACE_CONTRACT_DIMS` |

---

## 2.0 後端：UC1 子系統建議管線

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 2.1 | `suggest_subsystems` 編排：`summarize_for_prompt` → LLM → `_resolve_spatial_via_layers` → `discover_package`（§7.1） | 單元測試 + 整合測試；失敗時行為符合 §4.1（validator 掛了仍回樹） | 1.x | ✅ (triz_solver.py:337/390/397) |
| 2.1.L2 | **[L2 WBS 9.5.1 交叉影響]** `suggest_subsystems` prompt 組裝接收 contradictions 時若含子 PC，額外注入 `subsystem_hint` 與 `derived_parameter` 到 `<contradictions>` 區塊；prompt 加「以 subsystem_hint 作為 module 層級強提示」指令。**本任務由 L2 WBS 9.5.1 負責實作，本 WBS 僅同步接收改動** | L2 WBS 9.5.1 的 PR；本 WBS 2.1 單測需包含「混合父 TC + 子 PC 輸入」案例 | L2 WBS 9.5.1 | ⏳ 待 L2 WBS 啟動 |
| 2.2 | **POST `/scamper/subsystem-suggestions`** 請求/回應 schema 與 UX 表「區塊 A/B」欄位對齊 | OpenAPI 或同等契約；含 `package_map`、SVG 字串或 URL 策略 | 2.1 | ✅ `test_subsystem_contract.py` schema snapshot + round-trip |
| 2.3 | 矛盾與節點 **`related_contradictions`** 貫穿（§6.4.4） | 回傳 JSON 可驗證；供第三眼追溯使用；**需驗證父 TC id 與子 PC id 可共存於同一節點的 `related_contradictions` 陣列，不去重掉任一方** | 2.2, L2 WBS 9.5.2 | ✅ `test_tab1_to_tab2_e2e.py` (父 TC + 子 PC 共存待 L2 WBS 9.5.2 啟動時補) |
| 2.4 | 與 **Supabase `subsystems`** 寫入策略對齊（§7.1 FE 寫表—若實作改由後端寫入需一致） | 明確「誰寫庫」序時圖；無雙寫競態 | 2.2 | ✅ `docs/e2e/module/Subsystem_Persistence_Policy.md` (凍結 FE 寫 subsystems / BE 獨占寫 override+learned) |

---

## 3.0 後端：Layered Resolver 與 Spatial Validator

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 3.1 | **L1–L4** 查詢鏈（rd_override / learned / web / seed）與降級（§5、§9） | 各層獨立測試；超時 fail-fast 行為可配置 | 1.2 | ✅ (既有 test_spatial_validator.py) |
| 3.2 | 引用 key 不存在 → **confidence 降為 estimate**（§7.1） | 斷言測試 | 3.1 | ✅ gap-filled by test_subsystem_integration.py (rd_override/learned/seed) |
| 3.3 | **`discover_package`**：flatten、AABB clash、required envelope、notes（§5） | 與架構聲明之測試覆蓋一致；輸出含 UX 所需 `total_mass_g`、`total_bbox_mm` | 2.1 | ✅ `services/spatial_validator.py` + test_spatial_validator.py |
| 3.4 | **`render_package_map_svg`**：XY / XZ 正交視圖資料餵給 FE（UX 區塊 B） | 快照測試或 golden SVG | 3.3 | ✅ `services/package_svg.py` + FE `PackageMapPanel` inline SVG 測試 |
| 3.5 | **Discovery 不 blocking**：無 spatial 時友善退化（UX「失敗時」、架構 validator 失敗策略） | API 錯誤碼與 FE 提示文案一致 | 3.3 | ✅ `triz_solver.py` try/except 退化 + `uc1.validator_fallback` counter + FE 空狀態占位符 |

---

## 4.0 後端：UC3 RD inline override

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 4.1 | **POST `/spatial/component-overrides`** upsert `project_component_overrides`（§7.2） | DB migration（若需）；權限＝專案成員 | 1.1 | ✅ (既有) |
| 4.2 | 下次 UC1 **L1 命中** override（§8.2） | 整合測試：override 後 `reference_source` 為 `rd_override:<key>` | 4.1, 3.1 | ✅ end-to-end fake Supabase round-trip |

---

## 5.0 後端：UC4 推升 learned components

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 5.1 | **POST `/spatial/learned-components`** insert/update `confirmed_count`（§7.3） | 與 UX「推升至 learned」、④ Pre-CAD 批次推升共用同一實作或明確 wrapper | 4.1 | ✅ (既有) |
| 5.2 | 金鑰衝突、重複推升 idempotent 行為定義 | API 文件 + 測試 | 5.1 | ✅ duplicate key→bump confirmed_count, bbox first-seen canonical |

---

## 6.0 後端：UC5 What-if Overlay

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 6.1 | **POST `/scamper/spatial-overlay`**：`discover_package` → `apply_overlay`（§7.4） | 回傳 `overlay_violations`；**不修改**原始 discovery 狀態 | 3.3 | ✅ `routers/scamper.py` + test_subsystem_contract.py::TestSpatialOverlayContract (wrapped {package_map: ...} response 鎖定) |
| 6.2 | Overlay 輸入 schema（zones、per-module mass_budget）與 anchor 語意對齊 | 範例請求 + 驗證錯誤訊息 | 6.1 | ✅ `SpatialOverlayRequest` 巢狀 dict schema (`zones: {name: bbox}`, `mass_budget_g: {key: cap}`)；FE `handleOverlaySubmit` 轉換層已驗證 |

---

## 7.0 前端：區塊 A — 三層樹 + 介面契約

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 7.1 | **SubsystemHierarchyView**（或同等）：System→Module→Component 可摺疊；契約掛在 **module** 節點（§6.4） | 與 1.3 檢查清單一致 | 2.2 | ✅ (既有) |
| 7.2 | **六維欄位**展示與編輯策略（create-ux-spec：唯讀/可編輯與 `updateSubsystem()`） | 儲存後狀態符合 §8.1 `RDEdited` | 7.1 | ✅ (既有) |
| 7.3 | **spatial 區塊**：bbox、mass_g、mounting_pattern（唯讀為主；數字來源由 resolver 決定） | 與 API 欄位 1:1 | 7.1 | ⬜ (Wave 3: 整合進 Hierarchy) |
| 7.4 | **confidence badge** + **reference_source** hover（完整字串 + 更新時間，UX §Spatial Confidence） | 色票表與 spec 一致；無混用於 overlay 配色 | 1.2, 7.3 | ✅ `SpatialConfidenceBadge.tsx` (元件完成，Wave 3 整合) |
| 7.5 | **「我來給數字」** → 呼叫 UC3；成功後局部 refetch 或樂觀更新 | E2E：llm_estimate → override → badge 變深綠語意 | 4.1, 7.4 | ✅ `SpatialOverrideDialog.tsx` + Create.tsx 快取 invalidation |
| 7.6 | **「推升至 learned」**（Tab ② 入口，若與 ④ 批次分開則共用 service） | 成功/失敗 toast；權限錯誤處理 | 5.1, 7.4 | ✅ `PromoteToLearnedDialog.tsx` |
| 7.7 | **確認** 解鎖 Tab ③（create-ux-spec；§8.1 `RDConfirmed`） | 未確認時 SCAMPER tab disabled + 原因提示 | 7.2, 8.x 流程 | ✅ (Create.tsx `canProceedFromSubsystem` gate) |
| 7.8 | **手動新增**子系統表單（名稱、層級、理由、矛盾、鄰居）與 `createSubsystem()` | 表單驗證與 API 對齊 | 7.1 | ✅ (既有) |

---

## 8.0 前端：區塊 B — Package Map 面板

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 8.1 | **Package Map SVG** 嵌入（俯視 XY + 側視 XZ）；**clash** 紅色標示（UX 區塊 B） | 與 3.4 產出格式約定（inline SVG vs URL） | 3.4, 2.2 | ✅ `PackageMapPanel.tsx` |
| 8.2 | **總質量、最小封殼**（`required.total_mass_g`、`total_bbox_mm`）唯讀區 | 單元測試：空資料隱藏或占位符符合 UX | 8.1 | ✅ |
| 8.3 | **Notes** 清單（validator 提示） | 無資料時不報錯 | 8.1 | ✅ |
| 8.4 | **Discovery 與 Overlay 視覺分離**（UX §Discovery vs Overlay） | Code review 檢查：不得共用同一 SVG 元件預設配色 | 8.1, 9.2 | ✅ (slate palette) |

---

## 9.0 前端：區塊 C — What-if Overlay

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 9.1 | **二級按鈕**「試算車架包絡」預設摺疊；開啟對話框/抽屜（UX 區塊 C） | a11y：focus trap、ESC 關閉 | — | ✅ `SpatialOverlayDialog.tsx` (Radix Dialog) |
| 9.2 | Zone / mass budget 表單 → **POST spatial-overlay** → **紅/橘/綠** fits/tight/clash SVG | 關閉對話框後 discovery 主圖不變 | 6.1, 8.4 | ✅ (parent-injected onSubmit) |
| 9.3 | **overlay_violations** 清單與 **清除 Overlay**（僅本地 state 還原） | 與 spec 一致 | 9.2 | ✅ |

---

## 10.0 整合、狀態與下游銜接

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 10.1 | **F3 SCAMPER** 讀取已確認之結構化契約（UC6）；Frozen 後解鎖規則（§8.1） | 契約變更 invalidate 策略有 log 或版本號 | 7.7 | ✅ `ScamperRequest.interface_contracts` + `contracts_hash`；prompt 加入 6 維 + spatial 注入；FE `subsystemHash.ts` djb2 + `isContractDriftedSinceConfirm` predicate；renderScamper 漂移 banner + 重新確認按鈕；觀測計數 `scamper.contracts_provided` / `scamper.hash_missing` |
| 10.2 | **Pre-CAD** `spatial_score` deterministic 輸入來自 validator（架構 §5.2 / create-ux-spec ④） | 評分與 Tab ② 所見 package 一致；可追溯 | 3.3 | ✅ evaluator fix: 空 PackageMap/validator 崩潰時強制 neutral 3 + source 標記，不再信任 LLM |
| 10.3 | **Pre-CAD spatial trace** UI（hover 展開 bbox/clash/總質量） | 與 ④ 統一評估 wireframe 對齊 | 10.2 | ✅ `PreCadReview.tsx` useEffect 於開啟 review dialog 時呼叫 `preCadAnalyze`，按 solutionId 快取 `spatial_trace`/`spatial_score`；loading/idle/error/done 四態渲染。**DB 持久化**留作未來遷移（`pre_cad_reviews.ai_analysis` 欄位不存在；live fetch 可接受） |
| 10.4 | 與 **Tab ① TRIZ** 進入條件銜接（矛盾資料傳入 UC1） | 整合測試一條龍 | 2.2 | ✅ test_tab1_to_tab2_e2e.py (6 tests: id 保留 / 共矛盾耦合 / spatial 覆寫 / empty / package_map 篩選 / hermetic) |

---

## 11.0 測試、可觀測性、文件

| 任務 ID | 工作項 | 交付物 / 完成準則 | 依賴 | 狀態 |
|---------|--------|-------------------|------|------|
| 11.1 | 後端：**pure function** 單測（§5.1：resolver、validator、svg） | CI 綠燈 | 3.x, 6.x | ✅ (既有 test_spatial_validator.py 617 行) |
| 11.2 | API **契約測試**（Pact 或 schema snapshot）針對 2.2、4.1、5.1、6.1 | 破壞性更會失敗 | 2.2 | ✅ test_subsystem_contract.py (17 tests, 4 endpoints) |
| 11.3 | FE：**關鍵使用者流程** E2E（Suggest → Map → Override → Confirm → SCAMPER enabled） | 錄影或 trace 存 artifact | 7.x, 8.x | ⚠️ component tests via Vitest + Testing Library (32 tests)；Playwright E2E 延後，待辦已紀錄於 `docs/e2e/module/Playwright_E2E_Followup_WBS.md` |
| 11.4 | 可觀測性：UC1 各 phase 耗時、Tavily/LLM 失敗率 metric | Dashboard 或 log 欄位約定 | 2.1 | ✅ `app/observability/metrics.py` (phase_timer + emit_counter, JSON log lines); 6 phases + 9 counters |
| 11.5 | 本 WBS 與 **create-ux-spec / Forward_Subsystem** 對照表維護 | 版本升級時更新「對齊文件對應表」 | 全案 | ✅ 「文件對照」表於本 WBS §末段維持 |

---

## 依賴圖（關鍵路徑）

```
1.1 型別凍結 ──┬─► 2.1 suggest_subsystems (✅) ──► 2.2 API schema ──► 2.3 related_contradictions ──► 2.4 寫庫策略
               │
               ├─► 3.1 L1–L4 resolver ──► 3.2 estimate 降級 ──► 3.3 discover_package ──► 3.4 SVG 渲染 ──► 3.5 退化策略
               │                                                        │
               ├─► 4.1 override API ──► 4.2 L1 命中驗證                   │
               │          │                                               │
               │          └─► 5.1 learned API ──► 5.2 idempotent          │
               │                                                          │
               └─► 6.1 overlay API ──► 6.2 zone schema                    │
                                                                          │
7.1 tree (✅) ──► 7.2 六維 (✅) ──► 7.3 spatial (✅ inline) ──► 7.4 confidence badge (元件✅) ──► 7.5 override UI (✅) ──► 7.6 learned UI (✅) ──► 7.7 解鎖閘 (✅)
                                                                          │
8.1 Package Map (✅) ──► 8.2 總質量封殼 (✅) ──► 8.3 notes (✅) ──► 8.4 視覺分離 (✅)
                                                                          │
9.1 Overlay 對話框 (✅) ──► 9.2 fits/tight/clash (✅) ──► 9.3 violations (✅)
                                                                          │
10.1 F3 SCAMPER 讀契約 ──► 10.2 Pre-CAD spatial_score ──► 10.3 trace UI ──► 10.4 Tab ① 銜接
                                                                          │
11.1 單測 ──► 11.2 契約測 ──► 11.3 E2E ──► 11.4 可觀測性 ──► 11.5 對照表 ◄─┘
```

關鍵路徑：**1.1 → 2.2 → 3.3 → 3.4 → 7.3 → 7.5 → 7.7 → 10.1 → 11.3**（UC1 → Package Map → override → 解鎖 → SCAMPER enabled）

---

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| Validator (`discover_package`) 失敗造成 Tab ② 全頁卡住 | RD 無法確認、下游 SCAMPER 無法解鎖 | 3.5 non-blocking 降級；UX 顯示「Package Map 暫不可用」，樹與契約仍可編輯 |
| Resolver 降級到 seed 後 confidence 無法回復 | Pre-CAD `spatial_score` 失真 | 3.2 confidence 語意標示 `estimate`；7.4 badge 顯著提示 RD 覆寫 |
| Discovery 與 Overlay 視覺混淆 | RD 把假設值當真值 | 6.1 Overlay **不修改**原始 discovery；8.4 Code review 禁用相同配色；9.1 對話框隔離 |
| RD override 後 cache 未刷新，UC1 仍回舊值 | override 無效體感 | 4.2 整合測試斷言 `reference_source=rd_override:<key>`；7.5 成功後局部 refetch |
| 雙寫競態：FE 與後端都寫 `subsystems` | 資料不一致 | 2.4 明確「誰寫庫」序時圖；採單一寫入方 |
| Learned components idempotent 行為未定義導致 `confirmed_count` 爆衝 | 資料汙染 | 5.2 API 文件 + 測試鎖定金鑰衝突行為 |
| Pre-CAD 評分與 Tab ② 所見 Package 不一致 | RD 信任崩潰 | 10.2 deterministic 輸入來自 validator；10.3 trace UI 可追溯 |

---

## 完成判準（Definition of Done）

- [ ] 所有 P0 / P1 任務包單測 + 契約測 + E2E 全綠（11.1 / 11.2 / 11.3）
- [ ] e-Bike 案例：UC1 → Package Map → override → 推升 learned → 確認 → SCAMPER tab enabled 於本地可錄製完整 E2E
- [ ] Tab ② 每個 module 節點皆可展開 **六維契約**（對鄰居）與 **spatial 區塊**
- [ ] `confidence` badge 色票與 UX §Spatial Confidence 1:1；hover 顯示完整 `reference_source` + 更新時間
- [ ] Discovery 主圖與 Overlay SVG 在 code review 中確認不共用預設配色
- [ ] 未確認 Tab ② 時 SCAMPER tab 為 disabled 且顯示原因
- [ ] Pre-CAD `spatial_score` 與 Tab ② 所見 `total_mass_g` / `total_bbox_mm` 一致
- [ ] Validator 注入失敗時 Tab ② 仍可編輯樹與契約（non-blocking 降級驗證）

---

## 本版涵蓋 / 不涵蓋

| 涵蓋 | 不涵蓋（另開 WBS 或文件） |
|------|---------------------------|
| Tab ② 子系統介面之前後端與 F2.5 spatial | Tab ① TRIZ 分層 drill-down 細節（見 `Forward_TRIZ_Solver_Architecture.md`） |
| Package Map、Overlay、override、learned | Anti-Anchor 卡片與候選池全域 UX（create-ux-spec 其他區塊僅介面邊界） |
| Pre-CAD spatial 與 trace 的**介面層**需求 | CAD 工具鏈、實體 MLOps |

---

## 文件對照（快速索引）

| WBS 區段 | create-ux-spec.md | Forward_Subsystem_Discovery_Architecture.md |
|----------|-------------------|---------------------------------------------|
| 區塊 A | Tab ② 區塊 A 表格 | §6.4、§6.5、§6.1–§6.2、§7.1–§7.3 |
| 區塊 B | Tab ② 區塊 B | §3.3、§5、§7.1 |
| 區塊 C | Tab ② 區塊 C、Discovery vs Overlay | §7.4、§1.2 |
| Badge / trace | §Spatial Confidence、方案追溯 | §8.2、§6.2 |
| Pre-CAD | ④ 統一評估 | §5.2（架構內交叉引用） |

---

## L2 / L3 跨 WBS 交叉影響

本 WBS 的 `suggest_subsystems` 是 F2 的核心入口，會被上游兩個 WBS 依序改動。務必在啟動對應任務時同步 review：

### L2 WBS（`Explore_TC_to_MultiPC_Decomposition_WBS.md`）

| L2 WBS 任務 | 影響本 WBS | 同步動作 |
|-------------|-----------|---------|
| **9.5.1** `suggest_subsystems` prompt 加入 `subsystem_hint` / `derived_parameter` 注入 | 本 WBS 2.1 的 prompt 組裝會新增輸入欄位 | 確認本 WBS 2.1 單測覆蓋「含子 PC 的 contradictions 混合輸入」情境；prompt 變更記入本 WBS Changelog |
| **9.5.2** F2 `related_contradictions` 允許父 TC id 與子 PC id 共存 | 本 WBS 2.3 需驗證無去重錯誤 | 單測案例：節點 `related_contradictions = [parent_tc_id, child_pc_id]`，兩者都能追回 |
| **9.5.3** F2 docstring TODO 註記「等 L3 WBS 切換 LTS 輸入」 | 本 WBS 2.1 docstring 同步加註 | 在 2.1 任務狀態欄附註 L2 WBS 9.5 連結 |
| **9.7.2** F2 subsystem 樹的 module 節點命名與 `subsystem_hint` 語意對齊 | 本 WBS e2e 驗證（10.x 區段）需加案例 | e-Bike 腳本：子 PC 含「齒輪傳動」hint → F2 應產出「齒輪傳動模組」節點 |

### L3 WBS（`Explore_L3_SF_Parallel_Check_WBS.md`，skeleton）

| L3 WBS 任務（未啟動） | 影響本 WBS | 同步動作 |
|---------------------|-----------|---------|
| **L3 §6.1** `suggest_subsystems` 輸入 schema 改為 `LayeredTrizSolution[]`（取代 L2 9.5 的 flat adapter） | 本 WBS 2.1 / 2.2 schema **重大變更** | 啟動 L3 WBS 時本 WBS 2.x 必須同步 major version bump；OpenAPI 契約重簽 |
| **L3 §6.2** F2 prompt 改為消費 `differential_analysis.recommended_route` | 本 WBS 2.1 prompt 邏輯改寫 | prompt golden 測試需重寫 |
| **L3 §6.3** 交叉 PR 與本 WBS 同步 | 本 WBS 2.1 / 2.2 / 2.3 必須在 L3 WBS PR 中一併更新 | 設 L3 WBS §6 為 **blocker**，本 WBS 不得 refactor F2 入口直到 L3 §6 完成 |

### 相容性約束

- 在 L2 WBS 9.5 未上線前，本 WBS 2.1 / 2.2 維持現行 flat contradictions 輸入
- 在 L3 WBS §6 未上線前，本 WBS 2.1 / 2.2 **不可**自行切換到 `LayeredTrizSolution[]` 輸入（避免兩個 WBS 都在改同一檔）
- 本 WBS 若因其他原因需改動 2.1（例如 spatial / package_map 邏輯），必須在 PR description 明確標註「未觸及 L2 WBS 9.5 / L3 WBS §6 改動範圍」
