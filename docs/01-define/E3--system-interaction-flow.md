# E3 — 系統互動流程 (System Interaction Flow)

> **版本**: v2.0 | **日期**: 2026-04-27
> **定位**: 本文檔是 [E3 架構](E3--architecture-and-design.md) 的 **user-facing 視角**，對照 [00-discover/E1x--user-journey-map](../00-discover/E1x--user-journey-map.md)（現狀痛點）描繪 **設計後的目標體驗流**。
> **範疇**: 從使用者動作 → 跨子系統互動 → State Machine 狀態轉換的 end-to-end 任務流程。
> **來源**: 從 `../00-discover/E1--project-brief-and-prd.md` §2.4 Day-in-the-Life 與 `E3--architecture-and-design.md` Appendix A–E 推導，不引入新流程設計。
>
> **v2.0 變更 (2026-04-27)**：
> - 採用 D/X/V 三段式步驟編號（D = Define、X = eXplore、V = Verify），取代舊 Step 1–8 編號
> - 對齊 `E3--ai-agent-detailed-design.md` v2.2/v10 簡化：2c 併入 D3、OZ-OT 併入 X2、MUST 併入 X5
>
> **v3.0 變更 (2026-04-27)**：
> - Anti-Anchor 獨立子系統退役 — 合併為 TRIZ L1 內建「跨域去錨定」UX 步驟
> - Scenario 2 改寫：從「AA-seeded TRIZ」改為「TRIZ 跨域去錨定具體化」
> - 移除所有 `seed_source=anti_anchor` 追溯標記（統一為 TRIZ 路徑）
> - Appendix C 退役至 `_superseded/`

---

## §0 為什麼需要這份文件

| 現有文件 | 視角 | 回答的問題 |
|---------|------|-----------|
| `00-discover/E1x--user-journey-map` | **現狀痛點** | 使用者今天怎麼痛苦？ |
| `01-define/E3--architecture-and-design` Appendix A-E | **SA 架構** | 系統內部如何運作？（子系統、Container、Component） |
| `01-define/E3--architecture-and-design` Appendix D State Machine | **流程狀態機** | Artifact 如何流轉？ |
| `02-design/specs/ux/E5x--create-ux-spec` | **UI 規格** | 單一頁面長什麼樣？ |
| **本文件 (E3)** | **目標使用者流** | 使用者在設計後系統上**怎麼走完一個任務**？跨了哪些子系統？觸發哪些狀態？ |

**缺口補齊**：E3 附錄描述「系統本身怎麼設計」，本文件描述「使用者如何使用設計後的系統」，連接 WHY（痛點）與 HOW（架構）。

---

## §0.1 步驟編號對照表

> 對齊 `E3--ai-agent-detailed-design.md` v2.2 §11.2 步驟表。

| 新編號 | 名稱 | 舊編號 | 階段 |
|--------|------|--------|------|
| **D1** | 問題界定 | Step 1 | Define |
| **D2** | 理解全貌 | Step 2 | Define |
| **D3** | 根因分析與功能建模 | Step 2b *(含舊 2c FA)* | Define |
| **D4** | 系統建模 | Step 3 | Define |
| **X1** | 假設與驗證規劃 | Step 4 | eXplore |
| **X2** | TRIZ 解矛盾 (含跨域去錨定 + OZ-OT) | Step 5a *(含舊 5-0, 5a-0)* | eXplore |
| **X3** | 子系統定義 | Step 5b | eXplore |
| **X4** | Decision Hub | Step 5d | eXplore |
| **X5** | Pre-CAD 資格審查 | Step P *(含舊 5e MUST)* | eXplore |
| **V1** | 設計審查 | Step 6 | Verify |
| **V2** | 證據補齊（條件觸發） | Step 6e | Verify |
| **V3** | 決策與行動 | Step 7 | Verify |
| **V4** | 內化與傳達 | Step 8 | Verify |

---

## §1 目標狀態旅程總覽

對照 00-discover 痛點旅程的情緒低谷（發想 → 審查區間），以下是設計後的目標體驗。

```mermaid
graph TD
    %% ── Define 階段 ──
    S0["🏁 Entry — 入口分級 Level A/B/C"]
    D1["D1 — 問題界定 Constraint"]
    D2["D2 — 理解全貌 Socratic + 5Why/KT"]
    D3["D3 — 根因分析與功能建模 5Why/KT + FA"]
    D4["D4 — 系統建模 Contradiction"]

    S0 --> D1 --> D2 --> D3 --> D4

    %% ── eXplore 階段 ──
    X1["X1 — 假設驗證規劃 Assumption"]
    X2["X2 — TRIZ 解矛盾 (含跨域去錨定 + OZ-OT)"]
    X3["X3 — 子系統定義 (含 optional Spatial)"]
    X4["X4 — Decision Hub 候選池匯流"]
    X5["X5 — Pre-CAD 資格審查 (P1 MUST + P2 審查)"]

    D4 --> X1 --> X2
    X2 --> X3 --> X4
    X2 --> X4
    X4 --> X5

    %% ── Verify 階段 ──
    V1["V1 — 設計審查 Evidence Matrix"]
    V2["V2 — 證據補齊 (條件觸發)"]
    V3["V3 — KT 決策 Decision Record"]
    V4["V4 — 費曼內化 Asset"]

    X5 --> V1
    V1 --> V2 --> V3
    V1 -.->|"證據充分則跳過 V2"| V3
    V3 --> V4

    %% ── 樣式：深色填充 + 白字，暗色背景友好 ──
    style S0 fill:#6B21A8,color:#fff,stroke:#A855F7,stroke-width:2px
    style D1 fill:#1E40AF,color:#fff,stroke:#3B82F6,stroke-width:2px
    style D2 fill:#1E40AF,color:#fff,stroke:#3B82F6,stroke-width:2px
    style D3 fill:#1E40AF,color:#fff,stroke:#3B82F6,stroke-width:2px
    style D4 fill:#1E40AF,color:#fff,stroke:#3B82F6,stroke-width:2px
    style X1 fill:#92400E,color:#fff,stroke:#F59E0B,stroke-width:2px
    style X2 fill:#92400E,color:#fff,stroke:#F59E0B,stroke-width:2px
    style X3 fill:#92400E,color:#fff,stroke:#F59E0B,stroke-width:2px
    style X4 fill:#92400E,color:#fff,stroke:#F59E0B,stroke-width:2px
    style X5 fill:#065F46,color:#fff,stroke:#10B981,stroke-width:2px
    style V1 fill:#065F46,color:#fff,stroke:#10B981,stroke-width:2px
    style V2 fill:#065F46,color:#fff,stroke:#10B981,stroke-width:2px
    style V3 fill:#6B21A8,color:#fff,stroke:#A855F7,stroke-width:2px
    style V4 fill:#6B21A8,color:#fff,stroke:#A855F7,stroke-width:2px
```

> **v2.0 變更**：
> - 舊 Step 2c (FA) 併入 D3；舊 Step 5-0 (AA) 與 Step 5a-0 (OZ-OT) 併入 X2；舊 Step 5e (MUST) 併入 X5
> - X3（子系統定義）加入主流程圖（舊版遺漏）
> - V2（證據補齊）為條件觸發（V1→V3 直通 或 V1→V2→V3）

**設計後情緒曲線對比現狀**：發想階段（X2）情緒由焦躁 → 有工具支撐；審查階段（V1-V3）由緊張 → 有證據鏈可溯。

---

## §2 Scenario 1 — RD 用 Forward TRIZ 解矛盾

> **角色**: Persona 1 資深 RD 張三
> **觸發**: 收到 Brief，識別出「功率密度 vs. 散熱面積」矛盾
> **對齊痛點**: PP-1 經驗鎖定、PP-2 假設隱藏
> **對應 PRD**: §2.4 Day-in-the-Life 場景 + E3 Appendix B (Forward TRIZ Solver)
> **合約更新**: 依 [ADR-007](adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)（2026-04-15），Explore 階段矛盾識別改為 **TC-only**；PC/SF 於 Create 階段 `solve_triz_layered` 入口自 TC 派生，使用者不再需要「選擇 TC/PC/SF」。
> **ADR-008 補充 (2026-04-27)**：所有 Agent LLM 輸出中的數值聲明會透過 `EvidenceRegistryService.register_claim()` 自動註冊並交叉驗證（Tavily WebSearch），標記 VERIFIED / APPROXIMATE / UNVERIFIED。此為跨步驟 cross-cutting 行為，不逐一標示於下方序列圖中。
> **ADR-006 補充 (2026-04-27)**：TRIZ Layered 解題管線（L1→Critic→L2→L3）已由 `harness/orchestrator.py` 後端編排（非 client-driven），前端仍驅動產品級 Step 流轉。

### 2.1 Sequence Diagram

```mermaid
sequenceDiagram
    actor RD as RD 張三
    participant UI as Create 頁面
    participant AA as Analyst Agent
    participant TS as TRIZ Solver
    participant EV as Evaluator
    participant KB as Knowledge Agent

    RD->>UI: 上傳 Brief + 測試報告 (D1)
    UI->>AA: 解讀素材
    AA->>KB: 企業 RAG 檢索類似專案
    KB-->>AA: 歷史 citations
    AA-->>RD: 12 條 Constraint 草稿 + 缺口問卷

    RD->>UI: 確認約束（Gate D1）
    Note over UI: Constraint: Draft → Reviewed

    UI->>AA: 啟動蘇格拉底七類提問 (D2)
    AA-->>RD: 揭露 10 條隱含假設 + 3 條矛盾

    Note over UI: D3 — 根因分析與功能建模
    UI->>AA: five_why(symptom)
    AA-->>RD: 5 Why chain → 根因假設 + TC 候選
    opt 有對照組
        UI->>AA: kt_is_is_not(is_desc, is_not_desc)
        AA-->>RD: 4 維差異矩陣 → Px 候選 + OZ/OT hint
    end
    UI->>AA: function_analysis(brief_context)
    AA-->>RD: 組件交互圖 + SF 診斷 + 子系統邊界

    RD->>UI: 校準矛盾句 (D4, Gate D4)
    UI->>AA: formalize_contradiction (TC-only, ADR-007)
    AA-->>UI: type="TC" + improving/worsening_param + rationale
    Note over UI: Contradiction: Reviewed → Verified (僅 TC)

    Note over UI: X2 — TRIZ 解矛盾 (含 OZ-OT + 跨域去錨定)
    UI->>AA: oz_ot_analysis(contradiction_id, fa_result)
    AA-->>UI: OZ + OT + Px + PC 造句

    RD->>UI: 點擊「正向分析」卡片 (X2)
    UI->>TS: solve_triz_layered(C-001, TC + OZ-OT context)
    TS->>AA: derive PC (decompose_tc_to_pcs) + SF (derive_su_field_from_tc)
    AA-->>TS: PC[] + SuFieldModel (ADR-007 入口派生, 以 OZ-OT Px 輔助)
    TS->>TS: L1 TC 查矛盾矩陣
    TS->>TS: L2 PC 深挖物理根因 (ARIZ, 以 Px 為錨)
    TS->>TS: L3 SF 結構旁路
    TS-->>UI: LayeredTrizSolution (L1/L2/L3)
    UI-->>RD: 分層 drill-down 卡片 + critic badge

    RD->>UI: 採納 L2 推薦路線
    UI->>EV: 生成 Validation Passport
    EV-->>UI: assumptions[] + weak_points[] + required_verifications[]

    UI->>UI: 候選進入 Decision Hub (X4)
    Note over UI: 後續 MUST + Gate X5 見 Scenario 3 (§4)
```

### 2.2 跨子系統互動對照

> **頁面軌跡**：P01 Auth → P03 ProjectList → P04 Dashboard → P08 Create (Step 0–4)

| 使用者動作 | 觸發子系統 (Appendix) | 觸發狀態轉換 (State Machine) |
|-----------|---------------------|----------------------------|
| 上傳 Brief (D1) | Knowledge Agent (E3--architecture-and-design.md §11.5.2) | DRAFT → PHASE_I |
| 確認約束 (D1) | Analyst Agent | Constraint: Draft → Reviewed (Gate D1) |
| 執行 5 Why / KT (D3) | Analyst Agent | — (中間產物，不觸發狀態轉換) |
| 執行 FA 功能建模 (D3) | Analyst Agent | FunctionModel: — → Generated |
| 校準矛盾 (D4) | Analyst + TRIZ Solver | Contradiction: Reviewed → Verified (Gate D4) |
| 執行 OZ-OT 分析 (X2) | Analyst Agent | OzOtResult: — → Px Locked / Px Not Found |
| TRIZ L1 跨域去錨定具體化 (X2) | TRIZ Solver (L1 內建) | 跨域類比注入 L1 具體化步驟 |
| 啟動 TRIZ (X2) | Forward TRIZ Solver (Appendix B) | TrizSuggestion: pending → generated |
| 採納 L2 路線 | Evaluator (VP 生成) | Concept Route: — → Draft |
| CCI 複雜度檢查 | TRIZ Solver | ComplexityCheck: — → Evolution / Weak Evolution / Patch |
| 候選進入 Decision Hub (X4) | Decision Hub | SolutionCandidate: — → adopted（後續 X5 見 §4） |

---

## §3 Scenario 2 — RD 透過 TRIZ 跨域去錨定突破經驗鎖定

> **角色**: Persona 1 資深 RD 張三（或新人）
> **觸發**: 想避免「太快收斂到安全牌」
> **對齊痛點**: PP-1 經驗鎖定（最高優先級）
> **對應**: E3 Appendix B (Forward TRIZ Solver) — L1 具體化步驟內建跨域去錨定
> **v3.0 說明**: Anti-Anchor 獨立子系統退役。去錨定（打破路徑依賴）作為 UX 步驟內建於 TRIZ L1 具體化階段，不再是獨立流程。

### 3.1 Sequence Diagram

```mermaid
sequenceDiagram
    actor RD as RD 張三
    participant UI as Create 頁面
    participant AA as Analyst Agent
    participant KB as Knowledge Agent
    participant EV as Evaluator
    participant TS as TRIZ Solver

    Note over UI: X2 — TRIZ 解矛盾（L1 內建跨域去錨定）

    RD->>UI: 點擊「TRIZ 求解」卡片 (X2)
    UI->>AA: oz_ot_analysis(contradiction_id, fa_result)
    AA-->>UI: OZ + OT + Px + PC 造句

    UI->>TS: solve_triz_layered(C-001, TC + OZ-OT context)
    Note over TS: L1 具體化：查矛盾矩陣 → 40 原理
    TS->>KB: 跨域類比搜尋 (醫療/航太/消費電子)
    KB-->>TS: ≥2 條跨域解法 + citations
    Note over TS: 強制去錨定 UX：<br/>系統提示「以下為跨域實例，<br/>請確認是否與現有方案同源」
    TS->>TS: L1 具體化（含跨域去錨定 prompt）
    TS->>TS: L2 PC 深挖物理根因 (ARIZ, 以 Px 為錨)
    TS->>TS: L3 SF 結構旁路

    TS-->>UI: LayeredTrizSolution (L1/L2/L3)
    UI-->>RD: 分層 drill-down 卡片 + critic badge
    Note over UI: L1 卡片標記「跨域去錨定」來源

    RD->>UI: 採納 L2 推薦路線
    UI->>EV: 生成 Validation Passport
    EV-->>UI: assumptions[] + weak_points[] + required_verifications[]

    RD->>UI: 採納方案進 Decision Hub (X4)
    Note over UI: SolutionCandidate (source=triz)
```

### 3.2 跨子系統互動對照

> **頁面軌跡**：P04 Dashboard → P08 Create (X2 TRIZ 含去錨定) → P07 Track

| 使用者動作 | 觸發子系統 | 觸發狀態轉換 |
|-----------|-----------|-------------|
| 啟動 TRIZ 求解 | Forward TRIZ Solver (Appendix B) | LayeredTrizSolution: — → pending |
| L1 跨域去錨定具體化 | TRIZ Solver + Knowledge Agent | 跨域類比注入 L1；系統 prompt 強制去錨定確認 |
| L2/L3 深挖 | TRIZ Solver | LayeredTrizSolution: pending → generated |
| VP 生成 | Evaluator | VP 附加至路線 |
| 進入 Decision Hub | Decision Hub | SolutionCandidate (source=triz) |

**去錨定品質守衛**：L1 具體化時，系統檢查跨域類比結果是否與現有方案同源（物理機制相同）；若全部同源，提示 RD「可能存在錨定效應，建議檢視更遠領域」。品質檢查由 TRIZ 流程的 Critic + CCI 負責。

### 3.3 設計決策：為什麼去錨定是 TRIZ UX 步驟而非獨立子系統

> **v3.0 決策** (2026-04-27)：Anti-Anchor 從獨立子系統退役，去錨定功能內建於 TRIZ L1 具體化。

**蘇格拉底批判（AA 獨立價值分析）**：

| AA 宣稱價值 | TRIZ 已有覆蓋 | 判定 |
|:-----------|:-------------|:-----|
| 物理原理啟發 | PC + SF 路徑本質就是物理原理推導 | 重複 |
| 跨域類比 | 40 原理 + AutoTRIZ LLM 語義搜尋天然跨域 | 重複 |
| 矛盾消除 | IFR（理想最終結果）為 TRIZ 核心方法 | 重複 |
| **心理去錨定** | TRIZ 方法論不含此 UX 關注 | **唯一獨立價值** |

**結論**：AA 的唯一不可替代價值是「強制打破 PP-1 經驗鎖定」的心理效果，屬於 UX 層面而非方法論層面。將其作為 TRIZ L1 的內建 UX 步驟（跨域類比提示 + 同源檢查 prompt）即可實現，無需獨立子系統、獨立 API、獨立資料表。

**簡化收益**：
- 移除 1 個 API endpoint（`POST /api/v1/alternatives/anti-anchor`）
- 移除 1 張資料表（`anti_anchor_routes`）
- 移除 Appendix C 整份文件（~950 行）
- 使用者旅程少一個步驟（無需先跑 AA Sprint 再轉 TRIZ，直接在 TRIZ 中完成去錨定）

---

## §4 Scenario 3 — Decision Hub 品質評估 + Pre-CAD Gate 審查

> **v1.3 變更**：Phase B 收斂掃描已退役（v9）。其 5 項檢查全部由 SIM 矩陣（ADR-008 D5）和 CCI（ADR-008 D4）前置覆蓋。Decision Hub 流程簡化為：RD 採納 → CCI 標籤 → 橫向比較（≥2 路線時） → MUST 快篩 → 探索完整度 → Evidence Coverage → Gate X5。
> **v2.0 變更**：MUST 快篩從獨立步驟（舊 Step 5e）併入 X5 作為 P1 自動篩階段。
> **v2.1 變更**：Architecture Health Monitor 回歸 X2（對齊 Appendix D state machine `SX2_health`）；X4 移除循環矛盾分支（SIM §5.3 + Section 7 已前置攔截）；X5 RouteCheck 從「≥3 路線」改為「探索完整度」（衡量 process 而非 output count）+ 移除矛盾數分流（Pre-CAD Confidence = 100% 使「矛盾≥2」不可達）。
> 跨域去錨定作為 TRIZ L1 內建步驟，不再需要獨立追溯標記。

### 4.1 Decision Hub 品質評估（RD 張三 主導）

> **角色**: Persona 1 RD 張三
> **觸發**: Decision Hub 已匯流候選路線（TRIZ 三路徑產出，含跨域去錨定具體化）
> **對齊痛點**: PP-3 風險後置
> **對應**: E3 Appendix D State Machine + Appendix E Decision Hub

```mermaid
flowchart TD
    Start(["X4 候選池匯流"]) --> Hub["Decision Hub<br/>TRIZ 三路徑產出（含跨域去錨定）"]
    Hub --> Adopt["RD 採納方案<br/>+ CCI 標籤 (Evolution/Weak/Patch)<br/>+ 橫向比較 (≥2 路線時)"]

    Adopt --> X5["X5 Pre-CAD 資格審查"]

    subgraph X5sub ["X5 Pre-CAD 資格審查"]
        MUST["P1: MUST 快篩 (Go/No-Go)"] --> ExploreCheck{"探索完整度?<br/>TRIZ 三路徑（含跨域去錨定具體化）<br/>+ ≥1 存活路線"}
    ExploreCheck -->|不通過| Back["回 X2 補足未執行路徑"]
    ExploreCheck -->|通過| EvCheck{"Evidence Coverage<br/>≥ 40%?"}
    EvCheck -->|不通過| BackEv["提示補充證據"]
    EvCheck -->|通過| GateP["P2: 主管 Pre-CAD 審查<br/>(含探索完整度報告)"]
    end

    GateP --> Notify["系統推送審查請求<br/>至主管 Dashboard"]

    style Notify fill:#DBEAFE
    style X5sub fill:#F0FFF0,stroke:#4CAF50
```

**Decision Hub 品質評估互動對照**

> **頁面軌跡**：P08 Create (Step 4 Decision Hub → Step 5 MUST) → P09 PreCadReview → P12 DecisionRecord

| 使用者動作 | 角色 | 觸發子系統 | 觸發狀態轉換 |
|-----------|------|-----------|-------------|
| 採納方案 + 檢視 CCI 標籤 | RD 張三 | Decision Hub (CCI overlay) | SolutionCandidate: — → adopted；CCI 標籤為資訊性（Evolution / Weak Evolution / Patch） |
| P1: MUST 快篩 | 系統自動 | Evaluator | Concept Route 逐條 Go/No-Go |
| 探索完整度檢查 | 系統自動 | Evaluator | TRIZ 三路徑（含跨域去錨定具體化）皆執行 + ≥1 存活路線；不通過 → 回 X2 補足未執行路徑 |
| Evidence Coverage 檢查 | 系統自動 | EvidenceRegistryService | **Evidence Coverage ≥ 40%**（VERIFIED + APPROXIMATE 佔比，ADR-008 D3）；未達標則提示補充證據 |
| 檢視 CCI 標籤 | RD 張三 | Decision Hub (CCI overlay) | — （資訊性，不觸發狀態轉換；顯示 Evolution / Weak Evolution / Patch 分類） |
| 推送審查請求 | 系統自動 | Notification Service | Gate X5: — → Pending Review（探索完整度 + Evidence Coverage 均通過後觸發） |

### 4.2 Gate X5 審查（RD 主管 李四 主導）

> **角色**: Persona 2 RD 主管 李四
> **觸發**: 系統在探索完整度 + Evidence Coverage 通過後，自動推送 Gate X5 審查請求至主管 Dashboard
> **使用介面**: Review 頁面（非 Create 頁面）
> **對齊痛點**: PP-4 決策不可追溯、PP-6 證據缺口不可見
> **對應**: E3 Appendix D State Machine (Gate X5) + `Pre_CAD_Review_Template`

```mermaid
flowchart TD
    Notify(["系統推送 Gate X5 審查請求"]) --> Open["主管開啟 Review 頁面"]
    Open --> Review["逐條審查路線:<br/>1. Interface Contract 完整度<br/>2. 最小 CAD 範圍<br/>3. Evidence Coverage ≥ 40%<br/>4. TRIZ 路徑追溯鏈"]

    Review --> TL{"每條路線<br/>滿足退出條件?"}
    TL -->|通過| Sign["主管簽核"]
    TL -->|不通過| Fix["退回 RD 補強<br/>（明確指出缺失項目）"]

    Sign --> PhaseIII["Phase II → Phase III<br/>Concept Route: Reviewed → Verified"]
    Fix --> BackX["RD 回 X2 / X3 補強"]

    style PhaseIII fill:#DCFCE7
    style Fix fill:#FEF3C7
```

**Gate X5 審查互動對照**

| 使用者動作 | 角色 | 觸發子系統 | 觸發狀態轉換 |
|-----------|------|-----------|-------------|
| 收到審查通知 | 系統 → 主管 | Notification Service | — |
| 開啟 Review 頁面 | RD 主管 李四 | UI (Review 頁面) | — |
| 逐條審查 Interface Contract + CAD 範圍 | RD 主管 李四 | Human-in-the-Loop | — |
| 簽核 Pre-CAD | RD 主管 李四 | Human-in-the-Loop | Concept Route: Reviewed → Verified; Pre-CAD Report: Draft → Reviewed; **PHASE_II → PHASE_III** |
| 退回補強 | RD 主管 李四 | Human-in-the-Loop | Gate X5: Pending Review → Returned（附退回理由） |

---

## §5 跨子系統互動總表

彙整本文件三個 scenario 中使用者動作與子系統/State Machine 的完整對應。

| Step | 使用者動作 | 頁面 | Primary Subsystem | 觸發 Agent | Artifact 狀態轉換 | 參照 (`E3--architecture-and-design.md`) |
|------|-----------|-------------------|-----------|------------------|---------------------------------------|
| D1 | 上傳 Brief 與素材 | P05 | — | Knowledge + Analyst | Constraint: — → Draft → Reviewed | §11.5.2 Agent-Tool 綁定 |
| D2 | 參與蘇格拉底問答 | P06 | — | Analyst | Contradiction: Draft → Reviewed | §11.4.1 主流程序列圖 |
| D3 | 根因分析 (5Why/KT) + 功能建模 (FA) | P06 | — | Analyst | FunctionModel: — → Generated | §11.2 逐步自動化分級 |
| D4 | 校準 TRIZ 矛盾句 | P06 | Forward TRIZ Solver | TRIZ Solver + Analyst | Contradiction: Reviewed → Verified | Appendix B |
| X1 | 填寫假設台帳 | P07 | — | Analyst + Knowledge | Assumption: Reviewed → Verified | §11.2 逐步自動化分級 |
| X2 | 啟動 TRIZ 三路徑（含跨域去錨定） | P08 | Forward TRIZ Solver | TRIZ Solver + Knowledge | LayeredTrizSolution: — → generated（L1 含跨域去錨定具體化） | Appendix B |
| X3 | 定義子系統 | P08 | Forward Subsystem Discovery | Analyst | Subsystem: — → Draft (3-level) | Appendix A |
| ~~5c~~ | ~~SCAMPER 變形~~ | — | — | — | *(v9 移除)* | — |
| X4 | Decision Hub 採納 | P08 | 決策中心 | Evaluator | SolutionCandidate: — → adopted | Appendix E |
| X5 | P1 MUST 快篩 + P2 Pre-CAD 審查 | P09 | — | Evaluator + Human | Concept Route: Draft → Reviewed → Verified；**Phase II → III** | §11.2 + Appendix D |
| V1 | CAD 審查 + DR EM | P11 | — | Evaluator + Knowledge | Evidence Matrix: Draft → Verified | Appendix D |
| V2 | 證據補齊迴圈 | P11 | — | Knowledge | Evidence: Draft → Verified | Appendix D |
| V3 | KT 決策簽核 | P12 | — | Evaluator + Human | Decision Record: Draft → Reviewed；Concept Route: Verified → Baselined | Appendix D |
| V4 | 費曼內化 | P13 | — | Knowledge | Asset: — → Released；**Phase III → COMPLETED** | Appendix D |

---

## §6 對照 00-discover 痛點 → 設計後體驗

| 現狀痛點 (PP) | 現狀表現 | 目標體驗流對應點 | 緩解機制 |
|--------------|---------|-----------------|---------|
| PP-1 經驗鎖定 | 直覺搜尋過去方案 | Scenario 2 TRIZ L1 跨域去錨定具體化 | TRIZ L1 內建跨域類比 + 同源檢查 prompt，強制打破路徑依賴 |
| PP-2 假設隱藏 | 預設答案未明說 | Scenario 1 蘇格拉底七類提問 | Assumption Challenge (E3--architecture-and-design.md §11.3.2 機制 1) |
| PP-3 風險後置 | Proto 才爆問題 | Scenario 3 Decision Hub 品質評估 (X4) + X5 (P1 MUST + P2 Gate P) | SIM 矩陣前置跨矛盾衝突檢查 + CCI 複雜度判定 + 架構健康度（X2 SIM 出口，淨節點 >5 → 漸進回退 D3→D2→D1） |
| PP-4 決策不可追溯 | 半年後無法回溯 | Scenario 3 Validation Passport + KT Decision Record | 自動留痕（Artifact 狀態流轉） |
| PP-5 溝通斷層 | PM/RD/主管語言不同 | D1 約束改寫 + V4 費曼摘要 | 統一 Artifact schema |
| PP-6 證據缺口不可見 | 不知哪些需補數據 | Scenario 3 DR Evidence Matrix + Gate C | Evidence Level E0-E4 自動標記 |

---

## §7 連結與下一步

### 相關文件

| 文件 | 路徑 | 用途 |
|------|------|------|
| E3 架構主文件 | `E3--architecture-and-design.md` | §11.4.1 主流程序列圖、Appendix A–E |
| E1x 現狀使用者旅程 | `../00-discover/E1x--user-journey-map.md` | 痛點對照基準 |
| Create UX Spec | `../02-design/specs/ux/E5x--create-ux-spec.md` | UI 規格細節 |

### 下一步

- [ ] 訪談驗證後，更新 §6 痛點緩解對照表的實際效益量測
- [ ] Scenario 新增：PM 王五（跨部門對齊）與 RD 主管（多專案儀表板）
- [ ] 與 02-design 其他頁面規格對齊（review / dashboard / gate pages）
