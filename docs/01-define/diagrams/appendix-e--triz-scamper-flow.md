## Appendix E: TRIZ → SCAMPER Flow

> 錨點：`#appendix-e-triz-to-scamper-flow`
> **相關文件**：`../../02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md`

## 雙軌分析 → 候選方案決策中心：設計概念與流程圖

---

### 0. 第一性原理：TC/PC/SF 是分層 drill-down，不是互斥三路徑

#### TRIZ 三層的本質


| 層           | 角色          | 問題表述             | 解法方向              |
| ----------- | ----------- | ---------------- | ----------------- |
| **L1 — TC** | **現象層**     | 改善 A 會惡化 B       | 40 原理打破 trade-off |
| **L2 — PC** | **本質層**     | 同一物理參數同時要 X 和 ¬X | 時間/空間/條件/整體-局部分離  |
| **L3 — SF** | **結構層**（旁路） | 物場交互不完整或有害       | 修改物質-場模型          |


**這三者不是「三個獨立醫生對同一病人開不同處方」，而是「同一份分層診斷報告的三層 — 表象 / 根因 / 結構」。** TC 是現象層、PC 是本質層（對 TC 的深挖）、SF 是結構層（平行的功能鏈旁證）。完整論述見 `../../02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md`。

#### 當前設計：分層 drill-down orchestrator

```
矛盾 C1 → solve_triz_layered orchestrator
       → L1 必跑 + L3 必跑（平行）
       → L2 critic 觸發判斷 → 必要時 deepen_link 推導 PC
       → 聚合為 LayeredTrizSolution（含 differential_analysis）
→ 決策中心：RD 採納整個 drill-down 組合 或 單層
→ Phase B 收斂掃描：
       同 LTS 內的跨層 → SKIP（同矛盾的不同層本來就應該協同）
       跨矛盾 → 正常檢查衝突
```

**設計原則**：TC/PC/SF 是同一矛盾的分層診斷（表象/根因/結構），不是互斥候選。Phase B 只比對跨矛盾衝突，同 LTS 內跨層自動跳過互斥檢查。

---

### 1. 主流程總覽

**設計哲學**：Phase 2 是 **雙軌產出 → 人類選擇 → 交叉檢查 → 統一評估**。

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph Phase2["Phase 2: 雙軌分析 → 匯流決策"]
        direction TB

        subgraph REVERSE["反向路徑 — 打破框架（創意發散）"]
            direction TB
            R1["Anti-Anchor Sprint<br/>AI 非典型架構探索<br/>Output: AntiAnchorRoute[] ≥3<br/>每條自帶 Validation Passport<br/>(assumptions + weak_points +<br/>required_verifications + confidence)"]
            RP["反向候選池<br/>Anti-Anchor routes<br/>直接進入，不經 TRIZ 收斂"]
            R1 --> RP
        end

        subgraph FORWARD["正向路徑 — 系統化解矛盾"]
            direction TB
            F1["F1: TRIZ 解矛盾 (v11 分層化)<br/>solve_triz_layered orchestrator<br/>L1 (TC 必跑) + L2 (PC 條件觸發) + L3 (SF 必跑旁路)<br/>輸出: LayeredTrizSolution[] + differential_analysis<br/>Architecture Health Monitor"]
            F2["F2: 子系統定義<br/>System→Module→Component 3 層<br/>+ 6 維介面契約"]
            F2S["F2.5: Spatial Discovery Validator<br/>Reference library 覆寫 + 算術<br/>→ Package Map (SVG)<br/>(overlay 為 optional，不限制創意)"]
            F3["F3: SCAMPER 變形（創意工具）<br/>7 創意行動 × 子系統<br/>風險標註，不觸發 re-scan"]
            FP["正向路徑候選池<br/>LayeredTrizSolution[]<br/>+ SCAMPER 候選"]
            F1 --> F2 --> F2S --> F3 --> FP
        end

        subgraph HUB["候選方案決策中心"]
            direction TB
            SELECT["RD 採納：drill-down 組合或單層<br/>預設依 differential_analysis.recommended_route<br/>同 LTS 跨層為合法組合，不再警告"]
            PHASE_B["Phase B 收斂掃描 (v11)<br/>同 LTS 內跨層 → SKIP<br/>跨矛盾 → 正常衝突檢查"]
            COMPARE["橫向比較<br/>來源 / 機制 / 假設 / 驗證需求 / 信心<br/>+ 跨層 differential_analysis"]
            SELECT --> PHASE_B --> COMPARE
        end

        RP --> SELECT
        FP --> SELECT

        MUST["MUST 快篩 (M1-M6)<br/>pass | fail | marginal"]
        PRECAD["Pre-CAD 審查 (5維)<br/>must / decoupling / testability /<br/>failureMech / mvpCadEffort"]
        COMPARE --> MUST --> PRECAD
    end

    GATE["Phase Gate 2<br/>≥1 alternative overallPass"]
    PRECAD --> GATE

    style REVERSE fill:#FEF3C7,stroke:#F59E0B
    style FORWARD fill:#DBEAFE,stroke:#3B82F6
    style HUB fill:#F3E8FF,stroke:#8B5CF6
    style GATE fill:#F0FDF4,stroke:#22C55E
```



#### 設計決策說明


| 決策                        | 說明                                                                                |
| ------------------------- | --------------------------------------------------------------------------------- |
| **方法獨立**                  | 反向（創意）和正向（演繹）是兩種本質不同的方法，不應讓創意工具再跑演繹收斂                                             |
| **正向路徑分層** (v11)          | F1 內部 TC/PC/SF 是同一矛盾的三層 drill-down，不是互斥三選一。由 `solve_triz_layered` orchestrator 調度 |
| **反向路徑簡化**                | Anti-Anchor 自帶 Validation Passport，直接進候選池。不需要 R2-R4（TRIZ/子系統/SCAMPER）             |
| **產出與選擇分離**               | 正向路徑：TRIZ 步驟產出 `LayeredTrizSolution`（含 Architecture Health Monitor），採納在決策中心（Phase B） |
| Phase B = 方案交叉檢查          | 決策中心 RD 採納後手動觸發 `startPhaseB()`，只送 adopted 解法                                     |
| **同 LTS 跨層 = 合法組合** (v11) | Phase B 對同一 LayeredTrizSolution 內的多層解 SKIP 互斥檢查；只有跨矛盾才比對                          |
| ~~同矛盾多路徑警告~~ (v10 規則)     | **v11 已下線**。drill-down 是合法路徑而非缺陷                                                  |


---

### 2. TRIZ 狀態機（含轉換守衛）

**設計意圖**：每條 TRIZ 解法有獨立的生命週期。`edited` 狀態保留「人類修正 AI 建議」的追溯性，因此禁止從 `edited` 退回 `pending`。

```mermaid
%%{init: {'theme': 'neutral'}}%%
stateDiagram-v2
    [*] --> pending

    state "TrizActionStatus 狀態機" as FSM {
        pending --> adopted: 採用
        pending --> skipped: 跳過
        pending --> edited: RD 修改文字後確認

        adopted --> pending: 反悔
        adopted --> skipped: 改為跳過

        skipped --> pending: 重新考慮

        edited --> adopted: 確認修改版
        edited --> skipped: 放棄修改版
    }

    note right of FSM
        守衛規則:
        edited → pending 禁止
        (保留人類編輯追溯性)
    end note
```



#### 合法轉換矩陣


| from ＼ to   | pending | adopted | skipped | edited |
| ----------- | ------- | ------- | ------- | ------ |
| **pending** | -       | V       | V       | V      |
| **adopted** | V       | -       | V       | -      |
| **skipped** | V       | -       | -       | -      |
| **edited**  | **X**   | V       | V       | -      |


---

### 3. 收斂迴圈：Phase B

> **v8 變更**：Phase A 收斂掃描已退役。矛盾空間健康度改由 Architecture Health Monitor（phase-agnostic，nodes > 5 → critical → halt）監控。L1 critic badge 取代 Phase A 的全域收斂功能。`is_confirmatory` 語意去重仍存在於 schema 層級。

#### Phase B：方案交叉檢查（決策中心使用）

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph PHASE_B["Phase B — startPhaseB()"]
        direction TB
        B_START["決策中心：RD 按「執行收斂掃描」"]
        B_COLLECT["收集 adopted alternatives<br/>（RD 已挑選的解法）"]
        B_SCAN["POST /convergence/scan<br/>phase: B<br/>送 contradictions + adopted alternatives"]
        B_CHECK["檢查項 (v11)：<br/>1. 跨矛盾解法衝突<br/>2. 參數影響分析<br/>3. PC 狀態衝突<br/>4. 跨方案干涉<br/>5. (v11 移除) 同矛盾多路徑風險<br/>→ 同 LTS 跨層 SKIP 互斥檢查"]
        B_RESULT["converged → 進入 MUST<br/>halted → 人類審核調整方案"]
        B_START --> B_COLLECT --> B_SCAN --> B_CHECK --> B_RESULT
    end

    style PHASE_B fill:#F3E8FF,stroke:#8B5CF6
```



#### 收斂判定邏輯

```
converged = iteration > 0
    AND allResolved (fatal + major 全部 resolved)
    AND (confidence >= 80 OR noNewBlocking)

halted = forcePause
    OR health = critical / circular
    OR (noNewInfo AND hasUnresolvedBlocking)
    → 觸發人類審核
```

#### 人為介入點


| 動作          | 方法                                | 效果                                      |
| ----------- | --------------------------------- | --------------------------------------- |
| 強制停止        | `forceHalt()`                     | 立即取消 timer + abort flag，status → halted |
| 強制繼續        | `forceContinue()`                 | health 降級為 warning，排程下一輪 scan           |
| 重試分支        | `retryBranch(id)`                 | 該分支 status → exploring，排程下一輪            |
| 注入新矛盾       | `addContradiction()`              | 加入 graph，若 fatal/major 自動觸發 re-scan     |
| 覆寫 severity | `confirmSeverity()`               | 手動修正 AI 判定的 severity                    |
| 重新執行        | `startPhaseB()`                   | generation counter 防舊回呼污染               |


---

### 4. 資料流向

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph DUAL_TRACK["雙軌資料流"]
        direction TB

        subgraph REV_DATA["反向路徑資料（創意發散）"]
            AA["AntiAnchorRoute[]<br/>mechanism / cross_domain_source<br/>validation_passport<br/>(assumptions + weak_points +<br/>required_verifications + confidence)"]
            R_POOL["反向候選池<br/>直接進入，不經 TRIZ 收斂"]
            AA --> R_POOL
        end

        subgraph FWD_DATA["正向路徑資料"]
            F_EC["CLD Contradiction[]<br/>(from Phase 1 Explore)"]
            F_TS["正向 TrizSolution[]<br/>TC候選 + PC候選 + SF候選<br/>全部 pending"]
            F_SS["正向 Subsystem[]<br/>System→Module→Component"]
            F_SV["正向 ScamperVariant[]"]
            F_POOL["正向候選池"]
            F_EC -->|"1:N 求解"| F_TS
            F_TS -->|"矛盾親和性"| F_SS
            F_SS -->|"FK"| F_SV -->|"整合"| F_POOL
        end

        subgraph HUB_DATA["候選方案決策中心"]
            SELECT_DATA["RD 挑選<br/>每矛盾選一條路徑"]
            PHASE_B_DATA["Phase B 收斂掃描<br/>只送 adopted alternatives"]
            ADOPTED["被選方案集<br/>Alternative[]"]
            SELECT_DATA --> PHASE_B_DATA --> ADOPTED
        end
        R_POOL --> SELECT_DATA
        F_POOL --> SELECT_DATA

        EVAL["統一評估<br/>mustScores: Record M1-M6<br/>preCadScores: 5維<br/>overallPass: boolean"]
        ADOPTED --> EVAL
    end

    style REV_DATA fill:#FEF3C7,stroke:#F59E0B
    style FWD_DATA fill:#DBEAFE,stroke:#3B82F6
    style HUB_DATA fill:#F3E8FF,stroke:#8B5CF6
```



---

### 5. SCAMPER 定位：創意發散工具（不回饋收斂迴圈）

**設計意圖**：SCAMPER 與 Anti-Anchor 同屬**創意發散工具**。潛在風險以標註方式顯示，不自動觸發 re-scan。所有產出直接進入候選方案池，在決策中心由 RD 統一評估。

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    A["SCAMPER Variant 採用"] --> B{"AI 標註潛在風險?"}
    B -->|"否"| C["直接進入候選池"]
    B -->|"是"| D["風險標註<br/>（severity badge + 描述）<br/>供決策中心參考"]
    D --> C
    C --> E["候選方案決策中心<br/>統一做 Phase B 交叉檢查"]

    style A fill:#D1FAE5,stroke:#10B981
    style D fill:#FEF3C7,stroke:#F59E0B
    style E fill:#F3E8FF,stroke:#8B5CF6
```



**與 v7 的差異**：


|                   | v7（舊）                                               | v8（現在）                            |
| ----------------- | --------------------------------------------------- | --------------------------------- |
| newContradictions | fatal/major → 自動 addContradiction + re-scan         | 顯示為風險標註，不觸發 re-scan               |
| 確認流程              | 有未回饋矛盾 → 警告阻擋                                       | 無阻擋，所有風險在決策中心統一處理                 |
| 定位                | 分析工具（產出需要收斂驗證）                                      | **創意工具**（產出直接進池，與 Anti-Anchor 同級） |


---

### 6. 候選方案追溯六要素

每個進入決策中心的方案必須攜帶：


| #   | 要素    | 欄位                                                            | 說明                                                                           |
| --- | ----- | ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | 來源路徑  | `track: 'reverse' | 'forward'`                                | 從哪條分析鏈來                                                                      |
| 2   | 來源步驟  | `source: triz_tc | triz_pc | triz_sf | scamper | anti_anchor` | 具體產出步驟                                                                       |
| 3   | 解的矛盾  | `contradiction_ids: string[]`                                 | 追溯至原始矛盾                                                                      |
| 4   | 涉及子系統 | `subsystem_ids: string[]`                                     | 影響範圍                                                                         |
| 5   | 基於假設  | `validation_passport.assumptions[]`                           | 方案成立的前提。每項含 `evidence_level` (E0-E4)、`is_falsifiable`、`falsification_method` |
| 6   | 缺少驗證  | `validation_passport.required_verifications[]`                | 還需要什麼實驗                                                                      |


#### 假設可證偽性（P4）

每個 assumption 必須攜帶以下欄位，決策中心依此篩選低品質假設：


| 欄位                     | 型別                               | 說明                                        |
| ---------------------- | -------------------------------- | ----------------------------------------- |
| `evidence_level`       | `E0` | `E1` | `E2` | `E3` | `E4` | E0=純猜測, E1=類比, E2=文獻, E3=模擬, E4=實測        |
| `is_falsifiable`       | `boolean`                        | 此假設是否可被反證                                 |
| `falsification_method` | `string | null`                  | 具體的反證實驗或方法。`is_falsifiable=false` 時為 null |


**篩選規則**：`evidence_level ≤ E1` 且 `is_falsifiable = false` 的假設標記為 `low_quality`，決策中心顯示警告。

---

### 7. 完整狀態轉換表


| 階段                   | 輸入                          | 處理                                                                                      | 輸出                                                       | 連鎖效果                             |
| -------------------- | --------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------- |
| Anti-Anchor 生成       | mission + constraints       | AI 產出非典型架構（創意工具，自帶 Validation Passport）                                                 | `AntiAnchorRoute[].length ≥ 3`                           | **直接進反向候選池**，不經 TRIZ/子系統/SCAMPER |
| **TRIZ 分層求解** (v11)  | 矛盾集 + severity              | `solve_triz_layered`：L1 必跑 + L3 必跑 + L2 critic 觸發 + deepen_link + differential_analyzer | `LayeredTrizSolution[]`（含 L1/L2?/L3 + recommended_route） | 不做 Phase B                       |
| 子系統定義                | TRIZ 矛盾親和性                  | RD/AI 定義 System→Module→Component 3 層 + 6 維介面契約                                          | `Subsystem[confirmed]`                                   | 解鎖 SCAMPER                       |
| SCAMPER 展開           | 已確認子系統                      | 7 行動 × N 子系統（創意工具，不觸發 re-scan）                                                          | `ScamperVariant[adopted]` + 風險標註                         | 直接進候選池                           |
| **決策中心採納** (v11)     | 所有候選池                       | **RD 採納 LTS 推薦組合 / 自訂組合 / 單層**                                                          | adopted Alternative[]（標註層級）                              | —                                |
| **Phase B 掃描** (v11) | `startPhaseB()`             | **跨矛盾衝突檢查；同 LTS 跨層 SKIP 互斥**                                                            | converged / halted                                       | 人類審核                             |
| MUST 篩選              | adopted Alternative + M1-M6 | AI + RD 評分                                                                              | pass / fail / marginal                                   | 淘汰不可行方案                          |
| Pre-CAD 審查           | 通過 MUST 的方案                 | 五維評分                                                                                    | overallPass                                              | Phase Gate 2 判定                  |


---

### 8. Health 閾值定義


| 狀態         | 條件                     | UI 表現 | 流程影響              |
| ---------- | ---------------------- | ----- | ----------------- |
| `healthy`  | nodeCount < 4 且無循環     | 綠燈    | 正常通行              |
| `warning`  | 4 ≤ nodeCount ≤ 5 且無循環 | 黃燈    | 提示檢視，不阻斷          |
| `critical` | nodeCount > 5          | 紅燈    | 收斂迴圈 halted，建議回退  |
| `circular` | 偵測到循環矛盾依賴              | 紅燈    | 收斂迴圈 halted，需架構重構 |


---

### 9. Gate 條件

#### 路徑完成 Gate


| Gate           | 條件                                           |
| -------------- | -------------------------------------------- |
| **反向路徑**       | Anti-Anchor routes.length ≥ 3（完成即可，無後續步驟）    |
| 正向: F1 TRIZ    | health != critical/circular 且 trizSolutions.length > 0 |
| 正向: F2 子系統     | confirmed subsystems > 0                     |
| 正向: F3 SCAMPER | SCAMPER adopted > 0                          |


#### 決策中心 Gate


| Gate         | 條件                                   |
| ------------ | ------------------------------------ |
| 進入決策中心       | 任一路徑候選池 > 0                          |
| Phase B 可執行  | ≥1 alternative adopted               |
| MUST         | Phase B converged + 所有候選方案 M1-M6 已評分 |
| Pre-CAD      | 通過 MUST 者 5 維全評分                     |
| Phase Gate 2 | ≥1 alternative overallPass           |


---

### 10. 關鍵元件對照


| 元件                        | 職責                                                 | 性質        |
| ------------------------- | -------------------------------------------------- | --------- |
| `useConvergenceLoop`      | 收斂迴圈 driver。`startPhaseB()` 觸發                       | 狀態 hook   |
| `/convergence/scan` API   | Phase B: 方案交叉檢查（同 LTS 跨層 SKIP 互斥）                    | 後端 AI     |
| `ConvergenceDashboard`    | 顯示 confidence %、fatal/major/minor 計數               | 純展示       |
| `BranchExplorationPanel`  | 顯示各矛盾分支的探索輪次                                       | 純展示       |
| `HumanReviewPanel`        | converged / halted 時的人類審查介面                        | 純展示       |
| `ArchitectureHaltOverlay` | health critical/circular 時的 overlay                | 互動        |
| `HealthMonitor`           | 渲染 health 燈號                                       | 純展示       |
| `ConvergenceGraph`        | 渲染矛盾 DAG                                           | 純展示       |
| **Decision Hub**          | 攤平所有候選、RD 路徑選擇、Phase B 觸發、橫向比較                     | **核心互動區** |

### ADR-008 擴充：SIM 分支與 Evidence Registry 整合（2026-04-27）

ADR-008 在雙軌流程中新增兩個跨切面：

**1. SIM 矩陣分支（Forward 路徑 F1 後）**

當 Forward TRIZ (F1) ���出涵蓋 ≥2 條 TC 的解法候選時，觸發 SIM 矩陣評估：
- 位置：F1 → **SIM 評估** → F2（取代直接 F1→F2）
- SIM +1/0/-1 評分 → -1 衝突回流為��� TC → ≤2 輪收斂
- 結果影響 Decision Hub 橫向比較（最優組合排序）

**2. Evidence Registry 覆蓋檢查（Gate P 前）**

在推送 Gate P 審查前，新增 Evidence Coverage 門檻：
- 所有 Agent 產出的 LLM 數值聲明已透��� `register_claim()` 註冊
- VERIFIED + APPROXIMATE 佔比 ≥ 40% 方可進入 Gate P
- 未達標時 Decision Hub 顯示 Evidence 缺口報告，引導 RD 補充


