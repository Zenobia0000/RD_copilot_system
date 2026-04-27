# Explore L3 (SF) 平行旁路 WBS（Create · TRIZ Solve 分層完整化）

> **版本**：0.1 Skeleton | **日期**：2026-04-09 | **狀態**：Draft · 待啟動（等 L2 WBS P0/P1 上線後）
>
> **⚠️ Phase B 退役通知 (2026-04-27)**：本 WBS 中 WP 7（Phase B 採納 UX）相關任務不再需要。**Phase B 已於 v9 退役**，由 SIM 矩陣（ADR-008 D5）和 CCI（ADR-008 D4）前置覆蓋。
> **前置 WBS**：`Explore_TC_to_MultiPC_Decomposition_WBS.md`（L1→L2 分解；已規劃）
> **範圍**：把 TRIZ 分層解題的 **L3 (SF) 平行旁路** 完整落地，包含 `solve_triz_layered` orchestrator、`differential_analyzer`、F2 完整切換到 `LayeredTrizSolution[]` 輸入，並完成 Explore 頁的「SF 三選一」UX 退場決策。
> **對齊文件**：
>
> - `docs/e2e/module/Forward_TRIZ_Solver_Architecture.md` v1.1（§6.2 L3 平行旁路、§6.3 SF solver、§7.0 `solve_triz_layered` 時序、§7.5 differential_analysis）
> - `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md`（§4.4 L3 角色、§4.3 Phase B 跨層不互斥）
> - `docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md`（§6 L3 adoption、M6 跨層 drill-down）
> - `docs/e2e/module/Forward_Subsystem_Discovery_Architecture.md` v2.1（§3.1 F1→F2 `LayeredTrizSolution[]` 契約）
>
> **TRIZ 知識庫來源**（`rd_assistant_design_system/triz_knowledge_base/`）：
>
> - `**05_76_standard_solutions.md`（30 KB，5 大類 76 條）— 本 WBS §1.0 的主要輸入** ★ 知識庫已存在，§1.0 從「盤點補齊」改為「驗證整合」
> - `06_tc_pc_sf_flows.md`（10 KB）— **§6 SF 流程既有設計（確定性狀態分類 → RAG 注入 05 → LLM 匹配）**；本 WBS §2.x / §3.x orchestrator 設計必須對齊
> - `07_tc_pc_sf_differences.md`（5 KB）— §4 顯示 SF 槽位 `sf_substance_1/2/field` 「與模型一致時必填」—意味著既有 `analyze_sufield` 假設 Step 3 Function Model 已產出 S1/S2/F；**本 WBS §2.1「LLM 自行推導 S1/S2/F」是新增路徑，與既有併存**
> - `04_separation_principles.md`（8 KB）— L2 WBS §1.1 的權威來源
> - `README.md` — 整個 KB 的 token 估算與注入策略（全量 / RAG / 混合）
>
> **既有可重用資產**（勿重造）：
>
> - `**backend/app/tools/triz_kb.py`**：
>   - `load_76_standard_solutions()` — 已有 loader，raw markdown 注入
>   - `**build_sufield_context(system_state: str | None)`（triz_kb.py:194）— 已支援 state-based filtering（incomplete / effective / harmful / insufficient），本 WBS §2.1 可**直接重用**作為二階段設計的第二階段 RAG
> - `**backend/app/agents/triz_solver.py:_solve_sf`（line 128~）** — 既有實作 delegate 到 `analyze_sufield`；本 WBS §2 為**新增並行路徑**（不取代）
> - `**backend/app/prompts/triz_solver.py:7` `TRIZ_SOLVER_SYSTEM`** — 07 §3 顯示 SF 使用 **不同** task 模板鏈，但 system prompt 仍可共用

---

## 知識庫稽核發現（2026-04-09 更新）

**重大發現**：整個 TRIZ 知識庫與既有 `triz_kb.py` 基礎設施比預期完整。本 WBS §1.0 範圍因此**大幅降級**：

1. `**rd_assistant_design_system/triz_knowledge_base/05_76_standard_solutions.md` 已存在且結構完整**（30 KB，5 大類 76 條，含物理本質 + 跨域範例）
2. `**triz_kb.py:load_76_standard_solutions()` loader 已實作**（`@lru_cache`，raw markdown 注入）
3. `**triz_kb.py:build_sufield_context(system_state)` 已支援 state-based RAG filtering**（triz_kb.py:194）— 本 WBS §2.1 兩段式設計可直接重用
4. **既有 `analyze_sufield` / `_solve_sf` (triz_solver.py:128) 是「Function Model 已產出 S1/S2/F」路徑** — 本 WBS §2.1 的「LLM 自行推導」路徑為**新增並行**，併存不取代
5. **07 §3 確認**：SF 與 TC/PC **共用** `TRIZ_SOLVER_SYSTEM` system prompt，但 task 模板鏈獨立
6. **06 §6 既有 SF 流程**採「確定性狀態分類 → RAG 注入 05 → LLM 匹配」兩段式，本 WBS §2.1 採同樣兩段式設計

### 降級影響

- §1.0「稽核補齊」→ 「**驗證 + 結構化 parser**」（工作量 -60%）
- §2.0 `_solve_sf` 重寫 → 「**新增 `_solve_sf_structural_check` 並存**」（範圍更明確，無 migration 風險）
- 原計畫 §2.2 `analyze_sufield` deprecation → **取消**，兩條路徑並存

---

## 為什麼分開這個 WBS

在 `Explore_TC_to_MultiPC_Decomposition_WBS.md` 中因為以下理由把 L3 延後：

1. **e-Bike 使用者範例核心痛點是「多 PC + 分離原則」** — SF 不是本次痛點
2. **L3 實作代價不小**：需要 76 standard solutions 知識庫完整性驗證、`_solve_sf` 當前是 delegate-to-legacy 路徑、需要 `differential_analyzer` 全新組件
3. **範圍控制**：L2 WBS 已含 9 個 Phase，加入 L3 會讓範圍翻倍，影響 L2 上線
4. **使用者決策**：明確選擇 L3-γ 路線（獨立 WBS）

L2 WBS 已經把**相容性預留做完**：

- `LayeredTrizSolution` Pydantic schema 已建（L2 WBS 1.5），`l3` 欄位存在但本版永遠為 `None` + `l3_status="deferred"`
- 前端 `<DecomposedChildrenList>` 組件預留 SF children 區塊（L2 WBS 6.x）
- `parent_contradiction_id` FK 不限 type='PC'，可直接掛 type='SF' children
- `contradictions` 表已有 `sf_substance_1/2`, `sf_field`, `sf_interaction`, `sf_completeness` 欄位
- F2 `suggest_subsystems` 已留 TODO 註記等待切換完整 LTS 輸入（L2 WBS 9.5.3）

本 WBS 只需補完 L3 本體與 orchestrator，不需回頭改 schema。

---

## 啟動前置條件（DoD 入場券）

以下條件**全部達成**才能啟動本 WBS：

- `Explore_TC_to_MultiPC_Decomposition_WBS.md` 的 P0 + P1 全部完成並 merge 到 main
- e-Bike e2e 驗證腳本 8.2 + 9.7 可重現產出 ≥3 互異子 PC + 分層 solve + CLD leaves + F2 subsystem_hint 注入
- `LayeredTrizSolution` Pydantic schema (L2 WBS 1.5) 已合併並被 Create 頁 assembleLayeredSolution helper 使用
- `_solve_pc` hint 路徑 (L2 WBS 9.1) 穩定運作 ≥ 2 週，delta log 無持續異常
- 團隊確認 L2 上線後的使用者反饋，確認 L3 仍是優先項（避免此 WBS 被其他需求插隊）

---

## 8 條範圍項目（使用者決策時凍結）


| #   | 範圍項目                                                                                              | 對應 docs                                        | 備註                             |
| --- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------ |
| 1   | `_solve_sf` 重寫符合「平行旁路、無條件跑」語意；legacy `analyze_sufield` 路徑保留 fallback                              | §6.3, §7.0                                     | TBD: 決定是否移除 legacy             |
| 2   | `solve_triz_layered` orchestrator 真正實作（backend 端點 `POST /triz/solve-layered`）                     | §7.0 sequence, §10 output schema               | TBD: 是否併入現有 `POST /triz/solve` |
| 3   | `differential_analyzer` 組件：比較 L1 / L2 / L3 並產出 `recommended_route` + `fallback_route`             | §7.5, TRIZ_Multi_Solution_Adoption_Strategy §4 | TBD: LLM-only 或 rule + LLM     |
| 4   | 76 standard solutions 知識庫**驗證與整合**（知識庫已存在於 `05_76_standard_solutions.md`）                         | §6.3                                           | **降級**：從「稽核補齊」改為「驗證 + 結構化解析」   |
| 5   | 前端 `<DecomposedChildrenList>` SF children 區塊啟用（色條 / S1/S2/F 三元組 / interaction/completeness badge） | L2 WBS 6.2 預留                                  | TBD: 視覺規格細節                    |
| 6   | F2 `suggest_subsystems` 完整切換為吃 `LayeredTrizSolution[]`（取代 L2 WBS 9.5 的 input adapter 預留）          | Forward_Subsystem_Discovery_Architecture §3.1  | TBD: 與 F2 WBS 協調               |
| 7   | Phase B adoption UX：RD 在決策中心看到 L1/L2/L3 三路線比較並選 `adopted_route`                                   | TRIZ_Multi_Solution_Adoption_Strategy §6       | TBD: 決策中心 UI 位置                |
| 8   | UX 決策：Explore 頁「SF」類型按鈕退場（改由 solver 自動產出） + `contradictions.sf_*` 欄位寫入責任重分配（Explore 不寫、solver 回寫） | —                                              | TBD: 使用者研究 + 資料 migration 計畫   |


---

## MVP 切分與建議順序

> **待填**：啟動時依使用者痛點排序。初步傾向 1 → 4 → 2 → 3 → 6 → 5 → 7 → 8


| 優先  | 標籤   | 說明                                        |
| --- | ---- | ----------------------------------------- |
| P0  | 1, 4 | 無 `_solve_sf` 重寫 + 知識庫盤點，其他都是空中樓閣         |
| P0  | 2    | `solve_triz_layered` orchestrator 為下游契約基石 |
| P1  | 3, 6 | differential_analyzer 與 F2 完整切換可解鎖下游價值    |
| P2  | 5    | SF children UI，使用者可見成果                    |
| P2  | 7    | Phase B 採納 UX                             |
| P3  | 8    | Explore SF 按鈕退場，UX 改動需使用者研究               |


---

## WBS 總覽（待填）


| ID  | 工作包                                        | 主要交付物                                                  |
| --- | ------------------------------------------ | ------------------------------------------------------ |
| 1   | 基線：76 std solutions 知識庫**驗證與整合**           | 覆蓋率報告 + `standard_solutions_kb.py` 結構化常數 + parity test |
| 2   | 後端：`_solve_sf` 重寫                          | 符合 §6.3 語意的新 `_solve_sf` + legacy 保留策略                 |
| 3   | 後端：`solve_triz_layered` orchestrator       | `POST /triz/solve-layered` + L1/L3 並行 + L2 條件          |
| 4   | 後端：`differential_analyzer`                 | LLM + rule 混合，產出 recommended/fallback route            |
| 5   | 前端：SF children UI 啟用                       | `<DecomposedChildrenList>` SF 區塊實作                     |
| 6   | 後端 + 前端：F2 完整切換 `LayeredTrizSolution[]` 輸入 | 取代 L2 WBS 9.5 的 adapter 預留                             |
| 7   | 前端：Phase B 採納 UX                           | 決策中心三路線比較卡片 + `adopted_route` 選擇                       |
| 8   | UX + migration：Explore SF 按鈕退場             | 使用者研究報告 + schema 遷移計畫                                  |
| 9   | 測試、可觀測性、文件                                 | e2e 腳本、LTS golden、runbook                              |


---

## 1.0 基線：76 std solutions 知識庫驗證與整合

> **知識庫已存在**：`rd_assistant_design_system/triz_knowledge_base/05_76_standard_solutions.md`（30 KB，5 大類，含物理本質 + 跨域範例）。本 WBS §1.0 從原先的「盤點補齊」降級為「驗證整合」—大幅減少工作量。


| 任務 ID | 工作項                                                                                                                                                                             | 交付物 / 完成準則                                                                                                                                                                                                                                                                                       | 依賴  |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --- |
| 1.1   | **驗證 `05_76_standard_solutions.md` 的 5 大類 76 條完整性**：逐類逐條核對數量（Class 1–5 分布待核對，總計 76 條）                                                                                           | 覆蓋率報告；若有缺漏則在本任務補齊（以第一性原理風格），但不另開 WBS                                                                                                                                                                                                                                                             | —   |
| 1.2   | **在既有 `triz_kb.py:load_76_standard_solutions()` loader 之上新增結構化 parser**（勿重造 loader）：新函數 `parse_76_standard_solutions() -> list[StandardSolution]`，從既有 loader 拿 raw markdown 後切片 | 欄位：`std_id`, `class_number`, `class_name`, `name_zh`, `applicable_interaction` (useful/harmful/insufficient/missing), `applicable_completeness` (complete/incomplete/harmful_complete), `physical_principle`, `cross_domain_examples`；Python 常數 + parity test（與 .md 對照）；保留 .md 為 source of truth | 1.1 |
| 1.3   | **確認既有 `analyze_sufield` / `_solve_sf` (triz_solver.py:128)** 的消費路徑與 `build_sufield_context(system_state)` (triz_kb.py:194) 的 RAG filtering 實作現況                                | 既有行為對照表；釐清 `build_sufield_context` 目前對 `system_state` 參數如何切片 05；若切片邏輯薄弱，需在本任務補強並加單測                                                                                                                                                                                                              | 1.2 |
| 1.4   | **讀 `06_tc_pc_sf_flows.md` + `07_tc_pc_sf_differences.md` 並對照本 WBS §2.x / §3.x 設計**：確認 `_solve_sf` 重寫後的行為與 .md 描述一致（尤其 TC / PC / SF 互斥判定、共用 prompt 段落）                          | 對照筆記；若發現本 WBS 設計與 .md 衝突需先解決                                                                                                                                                                                                                                                                     | —   |
| 1.5   | **Token 預算驗證**：依 `README.md` 的估算（76 標準解 ≈ 5000 tokens），評估全量注入 vs RAG 檢索策略對 `solve_triz_layered` 的 L3 路徑是否可行                                                                     | token budget 決策文件                                                                                                                                                                                                                                                                                | 1.2 |


---

## 2.0 後端：`_solve_sf` 重寫


| 任務 ID     | 工作項                                                                                                                                                                                                                                                                                                                                | 交付物 / 完成準則                                                                                                                                                                                                                                                      | 依賴            |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 2.1       | **新 `_solve_sf_structural_check` 函數**符合「平行旁路、無條件跑」語意：直接接 `(natural_description, mission, constraints)` 輸入，不要求 S1/S2/F；**兩階段設計**：(a) 第一階段 LLM 推導 S1/S2/F 並分類 `system_state` (incomplete/effective/harmful/insufficient) (b) 第二階段**重用既有 `build_sufield_context(system_state)`** 做 state-based RAG 切片 + 二次 LLM 匹配 2–3 條 std solutions | 兩段式實作；輸出符合 `L3StructuralCheck` Pydantic schema；引用的 std_id 必須在 1.2 結構化常數內                                                                                                                                                                                        | 1.2, 1.3, 1.4 |
| **2.1.5** | **並存策略（勿取代）**：既有 `analyze_sufield` 與 `_solve_sf` (triz_solver.py:128) 保留作為「使用者已提供 Function Model S1/S2/F」的路徑；新 `_solve_sf_structural_check` 為「無 Function Model 的平行旁路」路徑；`solve_triz_layered` orchestrator 依輸入是否含 S1/S2/F 決定走哪條                                                                                                     | 兩條路徑並存，無 deprecation；文件明確區分使用情境；對齊 07 §4 SF 槽位「與模型一致時必填」語意                                                                                                                                                                                                      | 2.1           |
| 2.2       | ~~legacy `analyze_sufield` 路徑處理~~ **取消**：既有路徑保留並存（見 2.1.5），不 deprecate；僅需在 docstring 註明「供 Function Model 已產出情境」                                                                                                                                                                                                                    | docstring 更新 PR                                                                                                                                                                                                                                                 | 2.1.5         |
| 2.3       | **新 prompt `SF_STRUCTURAL_CHECK_DERIVE` + `SF_STRUCTURAL_CHECK_MATCH`（兩段式）於 `backend/app/prompts/triz_solver.py`**；共用既有 `TRIZ_SOLVER_SYSTEM`（發現 2）                                                                                                                                                                                 | DERIVE prompt：輸入 natural_description + mission，輸出 `{s1, s2, f, system_state, confidence}`；MATCH prompt：輸入 DERIVE 結果 + `build_sufield_context(system_state)` 切片 + 1.2 結構化 std_id 清單，輸出 `{matched_solutions: [{std_id, rationale, confidence}]}`；兩段各自 golden test | 2.1           |
| 2.4       | 單測 `backend/tests/test_solve_sf_structural_check.py`                                                                                                                                                                                                                                                                               | 至少 4 個 SF 典型案例：incomplete (缺 S3) / harmful (振動耦合) / insufficient (場強不足) / effective (作為負控測試，確認不過度觸發)；使用 `05_76_standard_solutions.md` 內的跨域範例反查測資料                                                                                                               | 2.1, 2.3      |


---

## 3.0 後端：`solve_triz_layered` orchestrator

> **待填**


| 任務 ID | 工作項                                                                                                              | 交付物 / 完成準則                      | 依賴           |
| ----- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------ |
| 3.1   | 新端點 `POST /triz/solve-layered` + `SolveLayeredRequest` schema（可接 parent contradiction id，自動查 children）           | FastAPI router + Pydantic model | 2.x          |
| 3.2   | Orchestrator 實作 §7.0 時序：`par L1 / L3` 並行 → critic → alt L2 → `differential_analyzer` → 回 `LayeredTrizSolution`   | asyncio.gather 或同等；錯誤隔離每層       | 2.1, 4.1     |
| 3.3   | 與 L2 WBS 9.1 的 `_solve_pc` hint 路徑整合：orchestrator 從 DB 查 children PC 時將 `separation_principle_id` 傳入 `_solve_pc` | 整合測試                            | L2 WBS 9.1.3 |
| 3.4   | 舊 `POST /triz/solve` dispatcher 的退場策略：保留為 primitive，UI 改呼叫 `/triz/solve-layered`                                 | 遷移計畫                            | 3.1          |


---

## 4.0 後端：`differential_analyzer`

> **待填**


| 任務 ID | 工作項                                                                                         | 交付物 / 完成準則           | 依賴               |
| ----- | ------------------------------------------------------------------------------------------- | -------------------- | ---------------- |
| 4.1   | 規則層：比較 L1 / L2 / L3 的 `candidate_principles` 數量、`secondary_contradictions` 嚴重度、`confidence` | 規則函數 + 單測            | 1.5 (LTS schema) |
| 4.2   | LLM 層：產出人類可讀的 `recommended_route` 理由文字與 `fallback_route`                                    | prompt + 單測          | 4.1              |
| 4.3   | 輸出 `DifferentialAnalysis` 嵌入 `LayeredTrizSolution`                                          | schema 對齊 L2 WBS 1.5 | 4.2              |


---

## 5.0 前端：SF children UI 啟用

> **待填**


| 任務 ID | 工作項                                                    | 交付物 / 完成準則                                                               | 依賴         |
| ----- | ------------------------------------------------------ | ------------------------------------------------------------------------ | ---------- |
| 5.1   | 啟用 `<DecomposedChildrenList>` 的 SF 區塊（L2 WBS 6.2 已留骨架） | SF 卡片：色條 = `sf_completeness`、顯示 S1/S2/F + interaction/completeness badge | L2 WBS 6.2 |
| 5.2   | 視覺規格確認（色票 / icon / 文案）                                 | 設計稿 + code review                                                        | 5.1        |


---

## 6.0 F2 完整切換 `LayeredTrizSolution[]` 輸入

> **待填**；需與 `Subsystem_Interface_Development_WBS.md` 協調


| 任務 ID | 工作項                                                                                               | 交付物 / 完成準則     | 依賴  |
| ----- | ------------------------------------------------------------------------------------------------- | -------------- | --- |
| 6.1   | `suggest_subsystems` 輸入 schema 改為 `LayeredTrizSolution[]`（取代 L2 WBS 9.5 的 flat contradictions 適配） | OpenAPI 契約更新   | 3.3 |
| 6.2   | F2 prompt 組裝改為消費 `differential_analysis.recommended_route` 的 L1/L2/L3 內容                          | prompt 範例 + 單測 | 6.1 |
| 6.3   | `Subsystem_Interface_Development_WBS.md` 2.1 / 2.2 / 2.3 同步更新                                     | 交叉 PR          | 6.2 |


---

## 7.0 前端：Phase B 採納 UX

> **待填**


| 任務 ID | 工作項                                                                           | 交付物 / 完成準則     | 依賴  |
| ----- | ----------------------------------------------------------------------------- | -------------- | --- |
| 7.1   | 決策中心新增「三路線比較卡片」：並列 L1 / L2 / L3 的 key metrics + `recommended_route` highlight | 設計稿 + 實作       | 4.3 |
| 7.2   | RD 選擇 `adopted_route` 後持久化到 DB（`contradictions.adopted_route` 欄位，待 migration） | UI + migration | 7.1 |


---

## 8.0 UX 決策 + migration：Explore SF 按鈕退場

> **待填**；需使用者研究後才能決定


| 任務 ID | 工作項                                                              | 交付物 / 完成準則       | 依賴              |
| ----- | ---------------------------------------------------------------- | ---------------- | --------------- |
| 8.1   | 使用者研究：RD 是否仍希望手動標記 SF 類型                                         | 訪談報告             | 本 WBS P0–P2 上線後 |
| 8.2   | 若退場：Explore 頁 `ContradictionTab.tsx` 的 SF 按鈕移除；現有 SF 類型矛盾顯示但不可新建 | UI 改動 + 回歸測試     | 8.1             |
| 8.3   | `contradictions.sf_`* 欄位寫入責任重分配：Explore 不寫、`_solve_sf` 回寫        | 文件 + code review | 3.2, 8.2        |


---

## 9.0 測試、可觀測性、文件

> **待填**


| 任務 ID | 工作項                                                          | 交付物 / 完成準則       | 依賴       |
| ----- | ------------------------------------------------------------ | ---------------- | -------- |
| 9.1   | e2e 腳本延伸：e-Bike 案例完整走通 L1 + L2 + L3 + differential_analysis  | 腳本 + 截圖          | 3.3, 5.1 |
| 9.2   | LTS golden 測試：同一輸入應產出穩定結構（principal_number 可變，但層次結構穩定）       | snapshot test    | 3.3      |
| 9.3   | 觀測：`solve_triz_layered` 各層耗時 metric                          | log / Prometheus | 3.2      |
| 9.4   | 更新 `Forward_TRIZ_Solver_Architecture.md` Changelog 與 §11 驗證節 | 文件 PR            | 全部上線後    |


---

## Out of Scope（即使本 WBS 也不處理）

- TRIZ Trends of Evolution / Function Analysis / Trimming 等進階 TRIZ 工具 → 再開 WBS
- ARIZ 完整 9 步驟流程自動化 → 再開 WBS
- 多語言 separation principle 名稱（目前只有中文）→ i18n WBS

---

## 風險與緩解（待填）


| 風險                                          | 影響       | 緩解                                |
| ------------------------------------------- | -------- | --------------------------------- |
| 76 std solutions 知識庫實際覆蓋率不足                 | L3 結果品質低 | 1.1 盤點階段先發現，必要時延後本 WBS            |
| `solve_triz_layered` 同時三層 LLM 呼叫 latency 過高 | 使用者等待    | 3.2 用 asyncio.gather 並行；stream 顯示 |
| Explore SF 按鈕退場遭 RD 反對                      | 範圍 8 卡關  | 8.1 先做使用者研究；若反對則保留按鈕並改讀 solver 回寫 |


---

## 完成判準（待填）

- L1 + L2 + L3 三層在 e-Bike 案例下都產出有效 suggestions
- `differential_analysis.recommended_route` 可被 RD 在決策中心採納
- F2 `suggest_subsystems` 完整切換為吃 `LayeredTrizSolution[]`，L2 WBS 9.5 的 adapter 可下架
- `Subsystem_Interface_Development_WBS.md` 已同步更新（6.3）
- Explore SF 按鈕退場決策完成（保留 / 退場 / 改自動回寫，任一結果皆可）

---

## 文件對照（待填）


| WBS 區段                    | Forward_TRIZ_Solver_Architecture.md v1.1 | TRIZ_Layered_DrillDown_Optimization.md | TRIZ_Multi_Solution_Adoption_Strategy.md v1.1 | Forward_Subsystem_Discovery_Architecture.md v2.1 |
| ------------------------- | ---------------------------------------- | -------------------------------------- | --------------------------------------------- | ------------------------------------------------ |
| 1.x 知識庫                   | §6.3 SF solver                           | —                                      | —                                             | —                                                |
| 2.x `_solve_sf`           | §6.3, §7.0                               | §4.4 L3 角色                             | —                                             | —                                                |
| 3.x orchestrator          | §7.0 sequence                            | §4.2 觸發表                               | §2.1 跨層不互斥                                    | §3.1 F1→F2 契約                                    |
| 4.x differential_analyzer | §7.5                                     | §4.3                                   | §4 Concept Route                              | —                                                |
| 5.x SF UI                 | —                                        | §5 視覺化規範                               | —                                             | —                                                |
| 6.x F2 切換                 | —                                        | —                                      | §4.2 Concept Route                            | §3.1 正式輸入 `LayeredTrizSolution[]`                |
| 7.x Phase B UX            | —                                        | §4.3                                   | §6 L3 adoption                                | —                                                |
| 8.x SF 退場                 | —                                        | —                                      | —                                             | —                                                |


---

**狀態**：此文件為 L3 WBS 空殼 skeleton，真正內容待 `Explore_TC_to_MultiPC_Decomposition_WBS.md` P0/P1 上線後填寫。所有 TBD 與「待填」區塊請在啟動時補齊。