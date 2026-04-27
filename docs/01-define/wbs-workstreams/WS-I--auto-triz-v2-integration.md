# WS-I — Auto-TRIZ v2 Integration

---

**版本:** v1.0 | **日期:** 2026-04-23  
**狀態:** Draft · Ready-to-start  
**Owner:** Backend AI Agents Team + Frontend Lead  
**觸發 ADR:** [ADR-008](../adrs/ADR-008-auto-triz-v2-integration.md)  
**上游:** `docs_harness/auto_triz_strategy.md` (Auto-TRIZ v2 框架)

---

## 1. 範圍

將 Auto-TRIZ v2 方法論（FA / OZ-OT / SIM / CCI / Evidence Registry / 入口分級 / 5 Why / KT）注入現有自動化架構，同時保留 Socratic + CLD 等現有工具。（~~Anti-Anchor~~ 已退役，其跨域去錨定功能併入 TRIZ L1 instantiation 內建步驟。）

## 2. 前置依賴


| 依賴                     | 狀態         | 說明                                                         |
| ---------------------- | ---------- | ---------------------------------------------------------- |
| ADR-008                | ✅ Created  | 決策記錄已建立                                                    |
| WS-D (TRIZ Layered)    | 88.6%      | L1/L2/L3 基礎架構已就緒                                           |
| WS-F (TC→Multi-PC)     | Draft      | `decompose_tc_to_pcs` 已有，OZ-OT 可獨立開發                       |
| Tavily API integration | ✅ Existing | `evidence_retrieval.py` 已有 WebSearch，Evidence Registry 可複用 |


## 3. 工作分解

### WP-I.1: 資料庫遷移 (DB Migration)


| #     | 任務                                                                                                                          | 預估  | 優先級 | 依賴  |
| ----- | --------------------------------------------------------------------------------------------------------------------------- | --- | --- | --- |
| I.1.1 | 新增 `function_models` 表 (project_id, component_interactions JSONB, sf_diagnosis JSONB, subsystem_boundary JSONB, created_at) | 2h  | P0  | —   |
| I.1.2 | 新增 `evidence_claims` 表 (id, project_id, claim_id, claim_text, status, verification_sources JSONB, ...) + RLS                | 3h  | P0  | —   |
| I.1.3 | 新增 `sim_matrices` 表 (project_id, contradiction_ids JSONB, matrix JSONB, optimal_combination JSONB, rounds_used INT)         | 2h  | P1  | —   |
| I.1.4 | `contradictions` 表新增欄位: `oz_zone TEXT`, `ot_time TEXT`, `px_variable TEXT` (nullable)                                       | 1h  | P0  | —   |


**小計: 8h**

### WP-I.2: 後端 — AnalystAgent 擴充


| #     | 任務                                                  | 預估  | 優先級 | 依賴          |
| ----- | --------------------------------------------------- | --- | --- | ----------- |
| I.2.1 | `five_why()` 實作 + prompt template + Pydantic schema | 6h  | P1  | —           |
| I.2.2 | `kt_is_is_not()` 實作 + prompt template + schema      | 6h  | P1  | —           |
| I.2.3 | `function_analysis()` 實作 + prompt template + schema | 8h  | P0  | —           |
| I.2.4 | `oz_ot_analysis()` 實作 + prompt template + schema    | 8h  | P0  | —           |
| I.2.5 | `entry_grading()` 實作 + prompt template + schema     | 4h  | P2  | —           |
| I.2.6 | Router endpoints (5 個 POST) + integration tests     | 6h  | P0  | I.2.1-I.2.5 |
| I.2.7 | Pilot tests (TC-Analyst-008 ~ TC-Analyst-011)       | 4h  | P0  | I.2.6       |


**小計: 42h**

### WP-I.3: 後端 — TrizSolverAgent 擴充


| #     | 任務                                                | 預估  | 優先級 | 依賴           |
| ----- | ------------------------------------------------- | --- | --- | ------------ |
| I.3.1 | `sim_matrix()` 實作 + prompt + schema               | 10h | P1  | —            |
| I.3.2 | `complexity_check()` (CCI) 實作 + prompt + schema   | 8h  | P1  | —            |
| I.3.3 | `solve_layered()` 擴充 — 接收 FA + OZ-OT context      | 4h  | P0  | I.2.3, I.2.4 |
| I.3.4 | Router endpoints (2 個 POST) + integration tests   | 4h  | P1  | I.3.1, I.3.2 |
| I.3.5 | Pilot tests (TC-TrizSolve-008 ~ TC-TrizSolve-011) | 4h  | P1  | I.3.4        |


**小計: 30h**

### WP-I.4: 後端 — Evidence Registry Service


| #     | 任務                                                               | 預估  | 優先級 | 依賴    |
| ----- | ---------------------------------------------------------------- | --- | --- | ----- |
| I.4.1 | `evidence_registry.py` service 實作 (register + verify + coverage) | 10h | P0  | I.1.2 |
| I.4.2 | Router endpoints (2 POST + 1 GET)                                | 3h  | P0  | I.4.1 |
| I.4.3 | Integration with existing agents — inject `register_claim` 呼叫    | 6h  | P1  | I.4.1 |
| I.4.4 | Gate check 擴充 — coverage threshold                               | 3h  | P1  | I.4.1 |
| I.4.5 | Pilot tests (TC-Evidence-001 ~ TC-Evidence-005)                  | 3h  | P0  | I.4.2 |


**小計: 25h**

### WP-I.5: 前端 — Explore 頁擴充


| #     | 任務                                                 | 預估  | 優先級 | 依賴    |
| ----- | -------------------------------------------------- | --- | --- | ----- |
| I.5.1 | `useFiveWhy` + `useKtAnalysis` hooks               | 4h  | P2  | I.2.6 |
| I.5.2 | `useFunctionAnalysis` hook                         | 3h  | P2  | I.2.6 |
| I.5.3 | Explore 頁 Conditional Stepper — Problem Scoping 步驟 (5 Why + KT UI)（ADR-008 D6） | 8h  | P2  | I.5.1 |
| I.5.4 | Explore 頁 Conditional Stepper — Function Analysis 步驟 (FA 組件交互視覺化)（ADR-008 D6） | 10h | P2  | I.5.2 |
| I.5.5 | Entry Grading UI (入口分級)                            | 4h  | P2  | I.2.5 |


**小計: 29h**

### WP-I.6: 前端 — Create 頁擴充


| #     | 任務                                                           | 預估  | 優先級 | 依賴    |
| ----- | ------------------------------------------------------------ | --- | --- | ----- |
| I.6.1 | `useOzOtAnalysis` hook                                       | 3h  | P2  | I.2.6 |
| I.6.2 | OZ-OT 分析面板 (TRIZ step 前置)                                    | 6h  | P2  | I.6.1 |
| I.6.3 | `useSimMatrix` hook + SimMatrixView component                | 8h  | P2  | I.3.4 |
| I.6.4 | CCI badge 元件 (Evolution/Weak Evolution/Patch)                | 4h  | P2  | I.3.4 |
| I.6.5 | `useEvidenceRegistry` hook + EvidenceCoverageGauge component | 6h  | P2  | I.4.2 |


**小計: 27h**

### WP-I.7: 文件 Phase 2 + 驗收


| #     | 任務                                     | 預估  | 優先級 | 依賴         |
| ----- | -------------------------------------- | --- | --- | ---------- |
| I.7.1 | Phase 2 文件更新 (11 份，見融合計畫)              | 16h | P1  | WP-I.1~I.4 |
| I.7.2 | Phase 3 文件更新 (5 份，見融合計畫)               | 8h  | P2  | WP-I.5~I.6 |
| I.7.3 | BDD 新增 Feature 4-8 場景                  | 4h  | P1  | WP-I.2~I.4 |
| I.7.4 | E2E 手測腳本 (FA → OZ-OT → SIM → CCI 完整路徑) | 4h  | P1  | WP-I.5~I.6 |


**小計: 32h**

---

## 4. 總工時估算


| 工作包                      | 工時       | 優先級   |
| ------------------------ | -------- | ----- |
| WP-I.1 DB Migration      | 8h       | P0    |
| WP-I.2 AnalystAgent      | 42h      | P0-P2 |
| WP-I.3 TrizSolverAgent   | 30h      | P0-P1 |
| WP-I.4 Evidence Registry | 25h      | P0-P1 |
| WP-I.5 FE Explore        | 29h      | P2    |
| WP-I.6 FE Create         | 27h      | P2    |
| WP-I.7 Docs + 驗收         | 32h      | P1-P2 |
| **合計**                   | **193h** | —     |


**P0 關鍵路徑**: I.1 → I.2.3+I.2.4 (FA+OZ-OT) → I.3.3 (solve_layered 擴充) → I.4 (Evidence Registry) ≈ **75h**

---

## 5. 風險


| #     | 風險                               | 概率  | 影響  | 緩解                                                 |
| ----- | -------------------------------- | --- | --- | -------------------------------------------------- |
| R-I-1 | FA prompt 品質不足 → 組件交互圖粒度錯誤       | 中   | 高   | 先用 e-bike 案例驗證 prompt，逐步調教                         |
| R-I-2 | OZ-OT Px 鎖定失敗率高 → L2 深挖降級        | 中   | 中   | 提供 3 種 fallback 策略 (broaden_oz, split_tc, reframe) |
| R-I-3 | SIM 矩陣 LLM 評分不穩定                 | 低   | 中   | 設定 temperature=0.2 + 固定 prompt 結構                  |
| R-I-4 | Evidence Registry 增加 API latency | 低   | 低   | register_claim 為非同步，不阻塞主流程                         |
| R-I-5 | 流程步驟增加 → RD 覺得繁瑣                 | 中   | 高   | 入口分級自動跳步 + progressive disclosure                  |


