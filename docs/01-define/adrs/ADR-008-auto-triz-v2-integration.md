# ADR-008: Auto-TRIZ v2 閉環流程整合 — FA / OZ-OT / SIM / CCI / Evidence Registry

- **Status:** Proposed
- **Date:** 2026-04-23
- **Deciders:** Sunny (PO) · Backend AI Agents Team · Frontend Lead
- **Extends:** ADR-007（TC-only Explore + PC/SF Create 派生）
- **Upstream:** `docs_harness/auto_triz_strategy.md` (Auto-TRIZ v2 框架)

## Context

TR0 階段比較分析（`docs_harness` vs `docs/02-design`）揭露舊架構在 TRIZ 方法論上有 10 個結構性缺口。其中 5 個為 P0（方法論根基），直接影響 RD 收到的解法品質：

| # | 缺口 | 影響 |
|---|------|------|
| G1 | **Function Analysis (FA)** 完全缺失 | 系統邊界未驗證，矛盾可能定義在錯誤粒度 |
| G2 | **OZ-OT 分析**缺失 | TC→PC 轉換缺少核心橋樑（Px 鎖定），LLM 直接猜 PC |
| G3 | **問題定向**用 Socratic 替代 5 Why/KT | Socratic 是認知工具非 TRIZ 工具，無法直接產出 TC 假設 |
| G5 | **多 TC 交互 (SIM 矩陣)** 缺失 | 多矛盾間交互效應未評估，組合方案可能自相矛盾 |
| G6 | **Evidence Registry** 缺失 | LLM 數值聲明無外部驗證，hallucination 風險高 |
| G8 | **Evolution vs Patch (CCI)** 缺失 | RD 無法判斷方案是真正突破還是複雜度堆疊 |

**根因**：舊架構在自動化（LLM 驅動一鍵操作）上成熟，但跳過了 TRIZ 方法論的多個基礎步驟。Auto-TRIZ v2 框架（`docs_harness/auto_triz_strategy.md`）提供了方法論完整的 5-Step 閉環流程，需注入至現有自動化架構。

## Decision

### D1: 採用 Auto-TRIZ v2 的 5-Step 閉環作為 TRIZ 流程骨幹

將 Auto-TRIZ v2 的步驟映射至現有架構：

| Auto-TRIZ v2 Step | 映射至現有架構 | 實作方式 |
|---|---|---|
| §1.1 入口判定 (Level A/B/C) | Explore 頁入口 Modal | `analyst.entry_grading()` — 首次進入觸發，結果存入 `projects.entry_level`，驅動 Conditional Stepper 路由（Level A → 5-step stepper / Level B → 原 3-tab / Level C → SF-only 提示） |
| Step 0: 5 Why + KT | Explore 頁 **Level A stepper** Step 1 | `analyst.five_why()` + `analyst.kt_is_is_not()` — 與 Socratic **並存**互補；Level B 使用者可選跳過（原 3-tab 不受影響） |
| Step 1: FA + SF 診斷 | Explore 頁 **Level A stepper** Step 2 | `analyst.function_analysis()` — 產出組件交互圖 + SF 狀態；Level B 使用者以可選側面板呈現 |
| Step 2: TC + 矩陣查表 | `analyst.formalize_contradiction()` (已有) | 增強 KB 操作協議（結構化 5 KB 查詢） |
| Step 2b: OZ/OT 預篩 | Create 頁 TRIZ step 前置 | `analyst.oz_ot_analysis()` — 鎖定 Px |
| Step 3b: SIM 精篩 | Create 頁多 TC 場景 | `triz_solver.sim_matrix()` — +1/0/-1 交互矩陣 |
| Step 4: 複雜度檢查 | Create 頁決策中心 | `triz_solver.complexity_check()` — CCI 0-1 連續指標 |
| Evidence Registry | 全流程 cross-cutting | `EvidenceRegistryService` — claim 註冊 + WebSearch 驗證 |

### D2: Socratic Q&A 與 Anti-Anchor 保留不變

- **Socratic Q&A** 作為認知層面的發散工具保留，與 5 Why/KT 互補（而非替代）
- **Anti-Anchor** 作為反向思維工具保留，Auto-TRIZ v2 無對應機制
- **CLD (因果圖)** 保留，與 FA 互補（CLD 看因果關係，FA 看功能交互）

### D3: Evidence Registry 作為 cross-cutting service

- 所有 LLM agent 產出的數值聲明（材料性質、物理參數、成本估算等）須經 Evidence Registry 註冊
- 透過 Tavily WebSearch 自動驗證，標記為 `VERIFIED` / `APPROXIMATE` / `UNVERIFIED`
- 每個 claim 有唯一 `claim_id`，可追溯至產生該 claim 的 agent + step
- Gate 退出條件：Evidence Coverage（VERIFIED + APPROXIMATE 佔比）≥ 40%（可配置）

### D4: CCI (Continuous Complexity Index) 取代 binary 判定

- CCI ∈ [0, 1]：0 = 純進化（理想），1 = 純補丁（最差）
- 四維計算：組件數變化 / 能耗變化 / 認知負荷 / 演化趨勢對齊
- 判定閾值：CCI ≤ 0.3 → Evolution；0.3 < CCI ≤ 0.6 → Weak Evolution；CCI > 0.6 → Patch
- Patch 不阻擋出貨，但必須記錄技術債（`technical_debt_registry`）

### D5: 多 TC 場景以 SIM 矩陣處理

- 當 project 有 ≥2 個 formalized TC 時，自動觸發 SIM 評估
- SIM 矩陣：每對 TC 的候選解法間做 +1 (互相強化) / 0 (無關) / -1 (衝突) 評分
- -1 交互項視為新 TC，回流至 Step 3 處理
- 收斂規則：≤2 輪 SIM 迭代

### D6: Explore 頁採用 Conditional Stepper（取代平行 Tab 方案）

原始方案為 Explore 新增 2 個 Tab（`#problem-scoping` / `#function-analysis`），使 Explore 成為 5-tab 頁面。經 UX 分析後改採 **Conditional Stepper**，理由如下：

1. **方法論序列性**：5Why/KT → FA → Socratic → 矛盾有明確前後依賴。Tab 的 flat-access 心智模型假設平行操作，無法強制使用者先完成 FA 再定義矛盾，將導致 G1 缺口（矛盾定義在錯誤粒度）重現
2. **Entry Grading 是路由決策**：Level A/B/C 判定決定使用者需要哪些步驟，屬 gateway 而非內容 Tab
3. **認知負荷管理**：5 個含序列依賴的 Tab 違反 progressive disclosure 原則。Level B（已知 TC）的資深 RD 不需要走 5Why/FA，強制暴露這些 Tab 增加無效認知負擔
4. **繁瑣風險緩解**：ADR-008 風險表識別「流程步驟增加 → RD 覺得繁瑣」為高機率風險。Conditional Stepper 讓 Level B 使用者看到與 v1.0 完全一致的 3-tab UI，繁瑣風險降至最低

**Conditional Stepper 設計**：
- **Level A**（問題症狀，需引導）→ Explore 渲染為 5-step stepper：Problem Scoping → FA → Socratic → Contradictions → CLD
- **Level B**（已知 TC，快速通道）→ Explore 維持原 3-tab 佈局，FA 作為可選側面板
- **Level C**（功能缺失，無副作用）→ 提示導向 Create SF-only 通道

## Consequences

### Positive

- RD 收到的解法從「表面 TC 映射」升級為「現象→根因→結構」三層遞進
- FA 確保矛盾定義在正確系統粒度，避免「子系統問題當系統問題解」
- OZ-OT 讓 TC→PC 轉換有物理基礎，而非 LLM 直接猜測
- Evidence Registry 大幅降低 hallucination 風險，增加 RD 信任度
- CCI 讓 RD 能分辨「真突破」vs「複雜度堆疊」，避免無意識採用 Patch 方案

### Negative / Trade-off

- 流程步驟增加（Explore Level A 模式新增 5-step stepper + Create Step 1 內嵌 OZ-OT 前置面板）；Level B 使用者維持原 3-tab 無額外負擔
- LLM 呼叫次數增加（FA: +1, OZ-OT: +1, SIM: +N×N/2, CCI: +1, Evidence verify: +M per session）
- 預估每個矛盾增加 10-20 秒處理時間（FA + OZ-OT + Evidence verify）
- 需要 3 個新 DB 表（`function_models`, `evidence_claims`, `sim_matrices`）

### Neutral

- 現有 `formalize_contradiction()` 不變（TC-only per ADR-007），FA/OZ-OT 作為前置步驟
- 現有 `solve_triz_layered()` L1/L2/L3 架構不變，增加接收 FA + OZ-OT 結果作為 context
- Socratic / Anti-Anchor / CLD / SCAMPER / Subsystem 等現有流程不受影響

## Implementation Plan

| # | 模組 | 變更 | 新增/修改 |
|---|---|---|---|
| 1 | `backend/app/agents/analyst.py` | 新增 `five_why()`, `kt_is_is_not()`, `function_analysis()`, `oz_ot_analysis()`, `entry_grading()` | 新增 5 個 method |
| 2 | `backend/app/agents/triz_solver.py` | 新增 `sim_matrix()`, `complexity_check()`；`solve_layered()` 擴充接收 FA + OZ-OT context | 新增 2 method + 修改 1 |
| 3 | `backend/app/services/evidence_registry.py` | 新增 `register_claim()`, `verify_claim()`, `get_coverage()` | 新增 service |
| 4 | `backend/app/prompts/analyst.py` | 新增 5 Why / KT / FA / OZ-OT / Entry Grading prompt templates | 新增 5 templates |
| 5 | `backend/app/models/schemas.py` | 新增 `FunctionModel`, `OzOtResult`, `SimMatrixResult`, `ComplexityCheckResult`, `EvidenceClaim` Pydantic models | 新增 5 schemas |
| 6 | `supabase/migrations/` | 新增 `function_models`, `evidence_claims`, `sim_matrices` 表；`contradictions` 新增 `oz_zone`, `ot_time`, `px_variable` 欄位 | 新增 migration |
| 7 | `backend/app/routers/` | 新增 analyst 5 端點 + triz 2 端點 + evidence 3 端點 | 新增 10 endpoints |
| 8 | `src/pages/Explore.tsx` | Conditional Stepper：Entry Grading Modal + Level A 5-step stepper（Problem Scoping / FA / Socratic / Contradictions / CLD）/ Level B 原 3-tab + FA 可選側面板 | 修改 |
| 9 | `src/pages/Create.tsx` | Step 1 TRIZ 內部新增 OZ-OT accordion section + SIM Matrix conditional view（≥2 TC）；Step 4 Decision Hub 新增 CCI Badge + Evidence Coverage Gauge | 修改 |
| 10 | `src/hooks/api/` | 新增 `useEntryGrading`, `useFiveWhy`, `useKtAnalysis`, `useFunctionAnalysis`, `useOzOtAnalysis`, `useSimMatrix`, `useComplexityCheck`, `useEvidenceRegistry` hooks | 新增 8 hooks |
| 11 | Docs | 本 ADR 觸發 20 份文件更新（見架構融合計畫） | 修改 |

## Rollout

- **Phase 1**：ADR + Agent specs + API spec + Evidence Registry spec（文件層）
- **Phase 2**：DB migration + Backend agents + Backend tests（後端實作）
- **Phase 3**：Frontend hooks + components + E2E tests（前端實作）
- **Phase 4**：BDD 驗收 + 文件校驗

## References

- `docs_harness/auto_triz_strategy.md` — Auto-TRIZ v2 完整方法論
- `docs_harness/engineering/tr_gate_framework.md` — TR0-TR10 Gate 定義
- `docs/02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md` — 現有 L1/L2/L3 架構
- ADR-007 — TC-only Explore（本 ADR extends）
