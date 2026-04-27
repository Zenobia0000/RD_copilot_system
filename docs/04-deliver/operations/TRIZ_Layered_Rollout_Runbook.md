# TRIZ Layered Drill-Down Rollout Runbook

> **版本**：1.0 | **日期**：2026-04-09
> **範圍**：`triz_layered_mode` 灰度切換的四階段 runbook，對應 `TRIZ_Layered_DrillDown_Optimization.md` §9.3 遷移路徑與 `TRIZ_Layered_Drilldown_Development_WBS.md` WP 12.1。
> **Owner**：TRIZ Solver Backend + Create FE + Release Eng.

---

## 0. TL;DR

| 階段 | Flag 值 | 流量 | Exit Criteria | Rollback |
|----|---|---|---|---|
| **S1 Pre-launch** | `off` (預設) | 0 % | 新 endpoint 就緒、schema 凍結、黃金案例綠燈 | 無 — flag 本來就 off |
| **S2 Internal grey** | `on` for test projects | ≤ 5 專案 | 10 次完整 drill-down 採納無 regression | FE env 切回 `VITE_TRIZ_LAYERED_MODE=false` |
| **S3 Docs + prompts aligned** | `on` for test projects | ≤ 5 專案 | §6 三份文件章節級更新合併 | 同 S2 |
| **S4 Full switch** | `on` 預設 | 100 % | 全部 RD 專案使用新卡；`/triz/solve` 降為 primitive | 同 S2 + 若資料表已寫入 `layered_solution` JSONB，rollback 後 decision hub 只渲染 single/composite |

---

## 1. 前置檢查清單（進入 S1 的必要條件）

Backend：
- [ ] `backend/app/agents/triz_solver.py::solve_triz_layered` 已合併
- [ ] `backend/app/models/schemas.py` 含 `LayeredTrizSolution` / `L1Surface` / `L2RootCause` / `L3StructuralCheck` / `DeepenLink` / `DifferentialAnalysis` / `PhaseBDirective`
- [ ] `POST /triz/solve-layered` endpoint 註冊（`routers/triz.py`）
- [ ] `backend/app/agents/evaluator.py::check_phase_b_conflict` 結構化 helper 存在
- [ ] `tests/test_triz_layered.py` 18/18 + `tests/test_triz_layered_api.py` 8/8 + `tests/test_phase_b_layered_conflict.py` 6/6 全綠
- [ ] 既有 `/triz/solve` 回歸測試綠燈（`tests/test_triz_solver.py`，2 pre-existing 失敗無關）
- [ ] `supabase/migrations/010_triz_layered_drilldown.sql` apply 到 staging DB，`concept_routes.layered_solution` JSONB 欄位存在、`layered_triz_solutions` 表建立

Frontend：
- [ ] `src/types/layeredTriz.ts` TS mirror 與 backend Pydantic schema 一對一
- [ ] `src/lib/api.ts::trizSolveLayered` 已導出
- [ ] `src/components/create/LayeredSolutionCard.tsx` + `DifferentialAnalysisPanel.tsx` + `ConceptRouteCard` layered type 合併
- [ ] `src/config/featureFlags.ts::trizLayeredMode` 存在；`VITE_TRIZ_LAYERED_MODE` 環境變數預設缺省 → `false`
- [ ] `src/components/create/__tests__/LayeredSolutionCard.test.tsx` 9/9 全綠；全體 `vitest run` 無退化

Observability：
- [ ] `phase_timer("solve_triz_layered")` 可見於 Grafana（backend logs）
- [ ] `emit_counter("triz_layered_solved", severity, l2_ran, quick_mode)` metric 註冊

---

## 2. S1 Pre-launch（flag off，程式碼合入）

**目的**：所有新程式碼進 main branch，不影響既有流量。

**操作**：
1. 合併 PR，不需更動任何 env variable。
2. 部署至 staging，驗證 `GET /api/v1/triz/solve-layered` OpenAPI schema 可見。
3. 手動發 `POST /triz/solve-layered` curl，確認回傳 `LayeredTrizSolution`。

**Exit Criteria**：
- 前置檢查清單全綠
- staging deploy 成功、健康檢查通過
- 舊 `/triz/solve` 延遲、錯誤率與合併前持平（±5 %）

**Rollback**：不需要 — flag 本來就 off。

---

## 3. S2 Internal grey（少數測試專案 on）

**目的**：在受控範圍驗證端到端流程，收集 RD 回饋。

**操作**：
1. 在 staging 環境設定 `VITE_TRIZ_LAYERED_MODE=true` 重建前端 bundle。
2. 挑 3–5 個內部測試專案，請 RD 用新流程跑 TRIZ。
3. 於每次 drill-down 採納後記錄：
   - LTS id、adoption mode（recommended/custom/fallback）
   - critic trigger rate（`trigger_l2=true` / 總呼叫數）
   - L2 實際觸發率（應 ≈ major severity 比例 + quick_mode off 比例）
   - deepen_link derived parameter 正確率（RD 主觀評分）
   - Phase B 是否出現誤判（intra-LTS 應 SKIP）

**Exit Criteria**：
- 完成 ≥ 10 次完整 drill-down 採納流程
- 零 regression：舊 flow 仍可用（flag off 的 production traffic 不受影響）
- RD 對分層診斷卡的可讀性 ≥ 7/10 平均分
- Phase B 誤判率 = 0
- `phase_timer("solve_triz_layered")` P95 < 既有 `/triz/solve` P95 × 2（三層解的合理上限）

**Rollback**：
1. `VITE_TRIZ_LAYERED_MODE=false` → 重建 FE bundle → staging 重新部署
2. 通知 RD 回到既有 `/triz/solve` 流程
3. 已採納的 `layered` Concept Route 保留在 DB，不刪除（下次啟用時可重用）

---

## 4. S3 Docs + prompts aligned

**目的**：將 §6 三份文件的章節級更新合併，避免語意漂移。

**操作**：
1. `docs/e2e/module/Forward_TRIZ_Solver_Architecture.md` §6.2 / §6.6 / §7.1 章節重寫（參考 `TRIZ_Layered_DrillDown_Optimization.md` §6.1）。
2. `docs/diagrams/triz-to-scamper-flow.md` §0 / §1 主流程圖 / §7 狀態轉換表更新（參考 §6.2）。*(v9: SCAMPER 已移除，F3 節點刪除)*
3. `docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md` 已於 v1.1 同步，僅需 smoke review。
4. grep 全 repo，確認無殘留的「TC/PC/SF 三選一」、「同矛盾多路徑警告」等舊語句：
   ```sh
   rg "TC/PC/SF 互斥|三選一|同矛盾多路徑警告|same-contradiction multi-path" docs/
   ```

**Exit Criteria**：
- grep 回傳空
- 新進 RD 閱讀文件後能在 15 分鐘內正確解釋 L1/L2/L3 drill-down 與 M6 採納策略
- Docs PR 合併

**Rollback**：docs 回退不影響 runtime，無需 runbook。

---

## 5. S4 Full switch（100 % 流量切過）

**目的**：將 `triz_layered_mode` 預設改為 on，舊 `/triz/solve` 保留為 primitive 供 SDK 呼叫。

**操作**：
1. 修改 `src/config/featureFlags.ts`：
   ```ts
   trizLayeredMode: readBool("VITE_TRIZ_LAYERED_MODE", true),  // default flip
   ```
2. 在 production 環境設置 `VITE_TRIZ_LAYERED_MODE=true`（與程式碼預設一致，也可省略）。
3. 發佈 FE bundle。
4. 更新 `pages/Create.tsx` 呼叫 `trizSolveLayered`；移除條件分支（Phase A 已於 v8 退役，按鈕已移除）。
5. 保留 `POST /triz/solve` endpoint 作為底層 primitive，內部用於 `solve_triz_layered` orchestrator 的三個 sub-call。
6. 通知下游（F2 subsystem discovery）可使用 `SubsystemSuggestRequest.layered_triz_solutions` 欄位。

**Exit Criteria**：
- 所有新專案看到 layered 卡片
- 舊專案既有資料（single/composite Concept Route）正常渲染
- Phase B converge rate 不下降
- `phase_timer` P95 持平
- RD 支援請求歸零

**Rollback**：
1. `VITE_TRIZ_LAYERED_MODE=false` → 重建 FE bundle → 回滾 deploy
2. 如 `pages/Create.tsx` 已移除舊分支，需改為 hotfix PR 回補舊流程
3. 已寫入 DB 的 `layered` Concept Route 仍保留；舊 UI 會在決策中心以「Layered (unsupported)」降級呈現（ConceptRouteCard fallback 分支預留）

---

## 6. Metrics & SLO

| Metric | Source | SLO |
|---|---|---|
| `solve_triz_layered` 延遲 P95 | `phase_timer` | < 90s（含 3 × LLM call） |
| L1 critic trigger rate | `emit_counter(triz_layered_solved, ..., l2_ran=true/false)` | 基準 40 – 60 %（實務值） |
| L2 deepen_link 成功率 | LLM 回傳非空的 `derived_physical_parameter` | > 85 % |
| Phase B 誤判 | `check_phase_b_conflict` WARN 率 | < 5 %（正常值；>10 % 需調查 LTS 去重邏輯） |
| decision hub `layered` 卡片 render 錯誤 | FE Sentry | 0 |
| 舊 `/triz/solve` 回歸失敗 | CI | 0（2 pre-existing 失敗不計） |

---

## 7. 常見問題排查

| 症狀 | 可能原因 | 解法 |
|---|---|---|
| FE 呼叫 `/triz/solve-layered` 401 | flag on 但 backend 未部署新版本 | 檢查 backend version tag，重部署 |
| L2 永遠 `skipped_condition` | critic LLM 回傳 `trigger_l2=false`；severity 非 major | 檢查 `_l1_critic` prompt 輸出；手動試 `force_l2=true` |
| deepen_link `derived_physical_parameter` 是空字串 | LLM 回傳格式漂移 | 檢查 `_derive_pc_from_tc` 錯誤 log；fallback 走規則路徑 |
| Phase B 把同 LTS 內的 L2/L3 也 WARN | scanner 未帶 `lts_id` 欄位 | 檢查 FE 採納時是否把 `LayeredConceptRouteMeta.ltsId` 塞入 alternative payload |
| 決策中心看到空的 `layered` 卡片 | `ConceptRouteCard.layered` 欄位未正確填 | 檢查 `src/types/conceptRoute.ts::LayeredConceptRouteMeta` 是否齊全 |
| Supabase RLS 拒絕寫入 `layered_triz_solutions` | migration 010 未 apply 或 policy 未建立 | 重跑 migration；`SELECT polname FROM pg_policy WHERE polrelid='layered_triz_solutions'::regclass` |

---

## 8. 參考文件

- `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md` §9.3 遷移路徑
- `docs/e2e/module/TRIZ_Layered_Drilldown_Development_WBS.md` WP 1.4 / 12.1
- `supabase/migrations/010_triz_layered_drilldown.sql`
- `src/config/featureFlags.ts`
- `backend/app/routers/triz.py`
- `backend/app/agents/evaluator.py::check_phase_b_conflict`
