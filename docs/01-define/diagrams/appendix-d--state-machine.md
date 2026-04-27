## Appendix D: State Machine

> 錨點：`#appendix-d-state-machine`

## RD Design Copilot 整合流程狀態機與 R&R (E2E)

本附錄以程式設計角度繪製 `RD Design Copilot 整合流程 (E2E)` 的狀態機圖，並說明每個階段的 Roles & Responsibilities (R&R)。
核心概念為 **雙層狀態機 (Dual-Layer State Machine)**，同時管理 **流程狀態 (Process State)** 與 **工件狀態 (Artifact State)**。

### Step 編號對照


| 編號 | 名稱 | Phase | 核心工件類型 |
|------|------|-------|-----------|
| Step 1 | 問題界定（白帽 + 5W1H + 素材上傳解讀） | I | Constraint |
| Step 2 | 理解全貌（蘇格拉底問答） | I | Contradiction, Assumption |
| **Step 2b** | **根因分析與功能建模**（5Why + KT + FA + SF） | **I** | 根因假設, Px 候選, FunctionModel |
| Step 3 | 系統建模（因果迴路+TRIZ矛盾+斷路點） | I | Contradiction, Breakpoint |
| Step 4 | 假設與驗證規劃（HDA+未知集合） | II | Assumption |
| **Step 5a** | **TRIZ 解矛盾**（含 OZ-OT 前置 + 矩陣查表 + 原理具體化 + Architecture Health Monitor + SIM；**Anti-Anchor Sprint 並行**） | **II** | Concept Route (部分), SimMatrix, OzOtResult |
| **Step 5b** | **子系統定義**（三層階層 System→Module→Component；含 optional Spatial Discovery） | **II** | Concept Route (部分), SpatialEstimate |
| **Step 5d** | **AI 方案生成 + Decision Hub**（整合 + CCI 複雜度指標） | **II** | Concept Route, Interface, ComplexityCheckResult |
| **Step P** | **Pre-CAD 資格審查**（MUST Go/No-Go 自動篩 + 人工 Pre-CAD Gate） | **II** | Concept Route, Pre-CAD Review Report |
| **Step 6** | **設計審查** (CAD Gate - MVP CAD Review) | **III** | Concept Route, Evidence Matrix, Risk |
| Step 6e | 證據補齊 (Evidence Closure) | III | Evidence |
| Step 7 | 決策與行動（KT Decision Analysis+最小實驗） | III | Concept Route, Decision Record, Evidence |
| Step 8 | 內化與傳達（費曼） | III | Asset |

> **v10 簡化**：原 Step 2c 併入 2b；原 Step 5-0 降為 5a 並行任務；原 Step 5a-0 併入 5a 子步驟；原 Step 5b.5 降為 5b optional；原 Step 5e 併入 Step P。~~Step 5c SCAMPER 已於 v9 移除~~。


### 核心流程狀態機 (Process State Machine)

```mermaid
%%{init: {'theme': 'neutral'}}%%
stateDiagram-v2
    state "Phase I: 定義問題空間" as PhaseI {
        state "Step 1: 問題界定" as S1
        state "Step 2: 理解全貌（蘇格拉底）" as S2
        state "Step 2b: 根因分析與功能建模" as S2b
        state "Step 3: 系統建模" as S3

        S1 --> S2 : Gate 1
        S2 --> S2b : 揭露假設後
        S2b --> S3 : Gate 2
    }

    state "Phase II: 假設與發散" as PhaseII {
        state "Step 4: 假設與驗證規劃" as S4
        state "Step 5: 創造與調整" as S5
        state "Step P: Pre-CAD 設計審查" as S_P
        S4 --> S5 : Gate 4
        S5 --> S_P : Gate P
    }

    state "Phase III: 收斂與驗證" as PhaseIII {
        state "Step 6: 設計審查" as S6
        state "Step 6e: 證據補齊" as S6e
        state "Step 7: 決策與行動" as S7
        state "Step 8: 內化與傳達" as S8

        S6 --> S6e : 證據缺口
        S6e --> S6 : 證據更新
        S6 --> S7 : Gate C (證據充足，北極星 ≥ E2)
        S7 --> S8 : Gate 7
    }

    [*] --> S1 : DRAFT to PHASE_I
    S3 --> S4 : Gate 3 (PHASE_I to PHASE_II)
    S_P --> S6 : Pre-CAD 通過 (PHASE_II to PHASE_III)
    S8 --> [*] : Gate 8 (COMPLETED)
```



> **Note**: Step 5a 採雙軌架構：反向創意（Anti-Anchor，並行任務）直入候選池，正向演繹（OZ-OT → TRIZ → 子系統）生成候選。所有路徑匯流至 5d 決策中心 (Decision Hub)，由 RD 做 adopt/skip + CCI 標籤 + 橫向比較。最終通過 Gate P（含 MUST 自動篩 + 人工 Pre-CAD 審查）進入 Phase III。（~~Phase B 已於 v9 退役~~，由 SIM + CCI 前置覆蓋。~~SCAMPER 已於 v9 移除~~。）

##### Step 5 內部子流程

```mermaid
%%{init: {'theme': 'neutral'}}%%
stateDiagram-v2
    state "Step 5a: TRIZ 解矛盾 (含並行)" as Step5a {
        state "Anti-Anchor Sprint (並行任務)" as S5_AA
        state "OZ-OT 分析 (Px 鎖定)" as S5a_OZ
        state "TRIZ 三路徑候選生成" as S5a_TRIZ
        state "Architecture Health Monitor" as S5a_health
        note right of S5_AA : 直入候選池\n附 Validation Passport\n≥1 非對標路線
        note right of S5a_OZ : OZ + OT → Px 物理變數\nL2 PC 深挖前置條件
        note right of S5a_TRIZ : TC/PC/SF 三路徑\n全部 pending 生成
        note right of S5a_health : nodes > 5 → halt\n循環矛盾 → halt

        S5a_OZ --> S5a_TRIZ : Px locked → TRIZ 求解
        S5a_TRIZ --> S5a_health : 三路徑產出
        S5a_health --> S5a_TRIZ : warning/critical → 繼續求解
        S5a_health --> S2b : 🛑 結構性/框架性循環 → 回根因分析
    }

    state "5b: 子系統定義 (3-level)" as S5b
    state "5d: Decision Hub (決策中心)" as S5d
    note right of S5b : System → Module → Component\n+ 6-dim interface contracts\n+ optional Spatial Discovery
    note right of S5d : 候選池匯流\nRD adopt/skip\nCCI 標籤 + 橫向比較

    [*] --> S5_AA
    [*] --> S5a_OZ
    S5_AA --> S5d : Anti-Anchor 候選 (附 VP)
    S5a_health --> S5b : healthy/minor → 進入子系統
    S5a_health --> S5d : TRIZ 候選 (healthy)
    S5b --> S5d : 子系統定義完成
    S5d --> [*] : Gate P (MUST 自動篩 + 人工 Pre-CAD)
```



> **矛盾收斂圖 + 架構健康度監控**：
>
> - **Architecture Health Monitor（phase-agnostic）**：nodes > 5 → critical → halt。L1 critic badge 取代舊版全域收斂掃描。`is_confirmatory` 語意去重仍存在於 schema。
> - **~~Phase B~~（v9 退役）**：原方案交叉檢查已退役。其 5 項檢查全部由 SIM 矩陣（ADR-008 D5，TC 層跨矛盾衝突前置）和 CCI（ADR-008 D4，解法品質判定）覆蓋。PC 衝突 ⊂ TC 衝突（ADR-007），SIM -1 即捕捉。
>
> 新矛盾分級為 Fatal/Major/Minor：
>
> - **Fatal + Major**：必須回到 5a 繼續求解，直到完全收斂。**不設硬性次數上限**。
> - **Minor**：記入 Risk Register，不阻擋流程。
> - **架構健康度監控**（非告警，是強制停止；v1.3 改為漸進回退）：
>   - 節點 > 5（扣除 SIM 已收斂 TC 對）→ 🛑 **漸進回退**：① 回 Step 2b 重建功能模型/根因分析 → ② 仍無法收斂則回 Step 1 重新問題界定。「矛盾級聯超過 5 個節點。這不是 TRIZ 問題，是架構問題。」
>   - 循環矛盾 → 🛑 **依循環類型回退**：結構性循環（組件 A↔B 互為因果）→ 回 Step 2b 重建功能模型；框架性循環（問題定義自相矛盾）→ 回 Step 2b 或 Step 1。「架構內在矛盾，無法透過 TRIZ 解決。必須根本重構。」
> - **Pre-CAD Confidence Score**：`已收斂 (Fatal+Major) / 總 (Fatal+Major) × 100%`，Gate P 門檻 = 100%。
>
> **核心洞察**：矛盾數量是架構健康度的診斷信號。健康架構有 1-3 個矛盾；>5 個矛盾意味著在給錯誤架構打補丁。最好的設計流程不是「解矛盾最厲害」，而是「選到矛盾最少的架構」。

### Gate 與 Phase 轉換對照

> **權威定義見** [E3--ai-agent-detailed-design.md §2.2a](../E3--ai-agent-detailed-design.md#22a-gate-自動化判定)（含自動化等級與 Fallback）。
> 以下僅保留狀態機視覺化。

### 雙層狀態機概念圖 (Process State + Artifact State)

```mermaid
%%{init: {'theme': 'neutral'}}%%
stateDiagram-v2
    state "Step 6: 設計審查" as Process6 {
        state "EM: Draft" as EM_Draft
        state "EM: Reviewed" as EM_Reviewed
        state "EM: Verified" as EM_Verified
        state "CR: Reviewed" as CR_Reviewed
        state "CR: Verified" as CR_Verified
        state "Risk: Draft" as Risk_Draft
        state "Risk: Reviewed" as Risk_Reviewed
        state "CAD: Draft" as MVP_CAD_Draft
        state "CAD: Reviewed" as MVP_CAD_Reviewed

        EM_Draft --> EM_Reviewed : 填寫 EM
        EM_Reviewed --> EM_Verified : 證據補齊 (S6e)
        EM_Verified --> EM_Reviewed : 發現新缺口
        CR_Reviewed --> CR_Verified : 證據充足
        Risk_Draft --> Risk_Reviewed : 風險登錄
        MVP_CAD_Draft --> MVP_CAD_Reviewed : 繪製 MVP CAD
    }

    state "Step 6e: 證據補齊" as Process6e {
        state "Evidence: Draft" as Evid_Draft
        state "Evidence: Verified" as Evid_Verified
        Evid_Draft --> Evid_Verified : 執行最小實驗
    }

    state "Step 7: 決策與行動" as Process7 {
        state "DR: Draft" as DR_Draft
        state "DR: Reviewed" as DR_Reviewed
        DR_Draft --> DR_Reviewed : 完成 KT Decision
    }

    Process6 --> Process6e : 發現證據缺口
    Process6e --> Process6 : 證據更新
    Process6 --> Process7 : Gate C (證據充足，北極星 ≥ E2)
```



> **權威定義見** [E3--ai-agent-detailed-design.md §11.4.2](../E3--ai-agent-detailed-design.md#1142-並行處理規則)。

### 階段與狀態說明 (R&R)

> **Steps 1-8 的完整 R&R 定義已移至** [E3--ai-agent-detailed-design.md §11.2](../E3--ai-agent-detailed-design.md#112-逐步自動化分級)（自動化等級 + Agent 分配）及 [DK-01](../_domain-knowledge/DK-01--design-philosophy-and-process.md)（流程層 Gate 條件）。
>
> 本附錄僅保留上方的狀態機視覺化圖。

### ADR-008 新增 Artifact 生命週期（2026-04-27）

以下 5 個 artifact 由 ADR-008 Auto-TRIZ v2 引入。

> **編號對照**：「TRIZ Step」為 Auto-TRIZ Skill 內部步驟（`/triz-model` = Step 1、`/triz-solve` = Step 2+3、`/triz-verify` = Step 4）；「E2E Step」為本文件 Appendix D 定義的整合流程步驟。兩套編號互不相同，請依上下文區分。

| Artifact | TRIZ Skill Step | E2E Step | 建立者 | 生命週期 | 持久化 |
|----------|----------------|----------|--------|---------|--------|
| **FunctionModel** | TRIZ Step 1 (FA) | E2E Step 2b 根因分析與功能建模 | Analyst Agent `function_analysis()` | Draft → Reviewed（Gate 2 出口） | `function_models` 表 |
| **OzOtResult** | TRIZ Step 2 (OZ-OT) | E2E Step 5a OZ-OT 子步驟 | Analyst Agent `oz_ot_analysis()` | Draft → Reviewed（L2 入口前鎖定） | `contradictions` 表 `oz_zone/ot_time/px_variable` 欄 |
| **SimMatrixResult** | TRIZ Step 2+3 (SIM) | E2E Step 5a TRIZ 解矛盾 | TRIZ Solver `sim_matrix()`，≥2 TC 觸發 | Draft → Final（≤2 輪收斂後凍結） | `sim_matrices` 表 |
| **ComplexityCheckResult** | TRIZ Step 4 (CCI) | E2E Step 5d Decision Hub | TRIZ Solver `complexity_check()` | — （一次性計算，不可變） | 方案 `complexity_check_result` 欄 |
| **EvidenceClaim** | — （跨步驟） | — （跨步驟） | 所有 Agent LLM 輸出時自動註冊 | Registered → VERIFIED / APPROXIMATE / UNVERIFIED | `evidence_claims` 表 |

**EvidenceClaim 驗證流程**：
```
Agent LLM 輸出含數值聲明
  → EvidenceRegistryService.register_claim()
  → Tavily WebSearch 交叉驗證
  → 標記 VERIFIED / APPROXIMATE / UNVERIFIED
  → Gate P 退出: Evidence Coverage ≥ 40%
```

---
