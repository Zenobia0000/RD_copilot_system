# E3 — 系統互動流程 (System Interaction Flow)

> **版本**: v1.2 | **日期**: 2026-04-27
> **定位**: 本文檔是 [E3 架構](E3--architecture-and-design.md) 的 **user-facing 視角**，對照 [00-discover/E1x--user-journey-map](../00-discover/E1x--user-journey-map.md)（現狀痛點）描繪 **設計後的目標體驗流**。
> **範疇**: 從使用者動作 → 跨子系統互動 → State Machine 狀態轉換的 end-to-end 任務流程。
> **來源**: 從 `../00-discover/E1--project-brief-and-prd.md` §2.4 Day-in-the-Life 與 `E3--architecture-and-design.md` Appendix A–E 推導，不引入新流程設計。

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

## §1 目標狀態旅程總覽

對照 00-discover 痛點旅程的情緒低谷（發想 → 審查區間），以下是設計後的目標體驗。

```mermaid
graph LR
    S0["Entry<br/>入口分級<br/>Level A/B/C"] --> S1["Step 1<br/>問題界定<br/>Constraint"]
    S1 --> S2["Step 2<br/>理解全貌<br/>Socratic + 5Why/KT"]
    S2 --> S2c["Step 2c<br/>功能建模 FA<br/>FunctionModel"]
    S2c --> S3["Step 3<br/>系統建模<br/>Contradiction"]
    S3 --> S4["Step 4<br/>假設驗證規劃<br/>Assumption"]

    S4 --> S5aa["Step 5-0<br/>Anti-Anchor<br/>啟發探索"]
    S5aa -.->|"concept seed"| S5a0

    S4 --> S5a0["Step 5a-0<br/>OZ-OT 分析<br/>Px 鎖定"]
    S5a0 --> S5a["Step 5a<br/>TRIZ 求解<br/>(含 AA seed)"]
    S5a --> S5d["Step 5d<br/>Decision Hub<br/>候選池匯流"]
    S5d --> S5e["Step 5e<br/>MUST 快篩<br/>Go/No-Go"]
    S5e --> SP["Step P<br/>Pre-CAD 審查<br/>Concept Route"]
    SP --> S6["Step 6<br/>CAD 審查<br/>Evidence Matrix"]
    S6 --> S7["Step 7<br/>KT 決策<br/>Decision Record"]
    S7 --> S8["Step 8<br/>費曼內化<br/>Asset"]

    style S0 fill:#F3E8FF
    style S1 fill:#E0F2FE
    style S2c fill:#E0F2FE
    style S5aa fill:#FFE4E1
    style S5a0 fill:#FEF3C7
    style S5a fill:#FEF3C7
    style S5d fill:#FEF3C7
    style S5e fill:#FEF3C7
    style SP fill:#DCFCE7
    style S6 fill:#DCFCE7
    style S7 fill:#E9D5FF
```

> **v1.2 變更**：Anti-Anchor 從「與 TRIZ 平行的方案產生器」重新定位為「TRIZ 的啟發 seed 來源」（虛線箭頭）；Decision Hub 與 Pre-CAD 之間插入 Step 5e MUST 快篩節點。

**設計後情緒曲線對比現狀**：發想階段（Step 5）情緒由焦躁 → 有工具支撐；審查階段（Step 6-7）由緊張 → 有證據鏈可溯。

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

    RD->>UI: 上傳 Brief + 測試報告 (Step 1)
    UI->>AA: 解讀素材
    AA->>KB: 企業 RAG 檢索類似專案
    KB-->>AA: 歷史 citations
    AA-->>RD: 12 條 Constraint 草稿 + 缺口問卷

    RD->>UI: 確認約束（Gate 1）
    Note over UI: Constraint: Draft → Reviewed

    UI->>AA: 啟動蘇格拉底七類提問 (Step 2)
    AA-->>RD: 揭露 10 條隱含假設 + 3 條矛盾

    Note over UI: (v1.1) Step 2b — 問題定向
    UI->>AA: five_why(symptom)
    AA-->>RD: 5 Why chain → 根因假設 + TC 候選
    opt 有對照組
        UI->>AA: kt_is_is_not(is_desc, is_not_desc)
        AA-->>RD: 4 維差異矩陣 → Px 候選 + OZ/OT hint
    end

    Note over UI: (v1.1) Step 2c — 功能建模
    UI->>AA: function_analysis(brief_context)
    AA-->>RD: 組件交互圖 + SF 診斷 + 子系統邊界

    RD->>UI: 校準矛盾句 (Gate 3)
    UI->>AA: formalize_contradiction (TC-only, ADR-007)
    AA-->>UI: type="TC" + improving/worsening_param + rationale
    Note over UI: Contradiction: Reviewed → Verified (僅 TC)

    Note over UI: (v1.1) Step 5a-0 — OZ-OT 分析
    UI->>AA: oz_ot_analysis(contradiction_id, fa_result)
    AA-->>UI: OZ + OT + Px + PC 造句

    RD->>UI: 點擊「正向分析」卡片 (Step 5a)
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

    UI->>UI: 候選進入 Decision Hub (5d)
    Note over UI: 後續 MUST + Gate P 見 Scenario 3 (§4)
```

### 2.2 跨子系統互動對照

| 使用者動作 | 觸發子系統 (Appendix) | 觸發狀態轉換 (State Machine) |
|-----------|---------------------|----------------------------|
| 上傳 Brief | Knowledge Agent (E3--architecture-and-design.md §11.5.2) | DRAFT → PHASE_I |
| 確認約束 | Analyst Agent | Constraint: Draft → Reviewed (Gate 1) |
| **(v1.1) 執行 5 Why / KT** | Analyst Agent | — (中間產物，不觸發狀態轉換) |
| **(v1.1) 執行 FA 功能建模** | Analyst Agent | FunctionModel: — → Generated |
| 校準矛盾 | Analyst + TRIZ Solver | Contradiction: Reviewed → Verified (Gate 3) |
| **(v1.1) 執行 OZ-OT 分析** | Analyst Agent | OzOtResult: — → Px Locked / Px Not Found |
| 啟動 TRIZ | Forward TRIZ Solver (Appendix B) | TrizSuggestion: pending → generated |
| 採納 L2 路線 | Evaluator (VP 生成) | Concept Route: — → Draft |
| **(v1.1) CCI 複雜度檢查** | TRIZ Solver | ComplexityCheck: — → Evolution / Weak Evolution / Patch |
| 候選進入 Decision Hub | Decision Hub | SolutionCandidate: — → adopted（後續 MUST + Gate P 見 §4） |

---

## §3 Scenario 2 — RD 用 Anti-Anchor 啟發非典型概念，經 TRIZ 轉化為工程方案

> **角色**: Persona 1 資深 RD 張三（或新人）
> **觸發**: 想避免「太快收斂到安全牌」
> **對齊痛點**: PP-1 經驗鎖定（最高優先級）
> **對應**: E3 Appendix C (Reverse Anti-Anchor) → Appendix B (Forward TRIZ Solver)
> **v1.2 變更**: Anti-Anchor 從「直入 Decision Hub 的方案產生器」重新定位為「TRIZ 的啟發 seed 來源」。產出經 TRIZ 流程工程化後再進 Decision Hub。

### 3.1 Sequence Diagram

```mermaid
sequenceDiagram
    actor RD as RD 張三
    participant UI as Create 頁面
    participant AA as Analyst Agent
    participant KB as Knowledge Agent
    participant EV as Evaluator
    participant TS as TRIZ Solver

    Note over UI: === Phase I: Anti-Anchor 啟發 ===
    RD->>UI: 點擊「反向探索」卡片 (Step 5-0)
    UI->>AA: 啟動 Anti-Anchor Sprint
    Note over AA: 第一性原理 prompt:<br/>物理原則 + 因果鏈量化<br/>+ 邊界條件 + 邏輯謬誤守衛

    AA->>KB: 跨域類比搜尋 (醫療/航太/消費電子)
    KB-->>AA: ≥2 條跨域解法 + citations
    AA->>AA: 產出 3 條非典型 Route
    AA->>EV: 每條附 Validation Passport (VP)
    EV-->>AA: VP (assumptions, weak_points, confidence_level)

    AA-->>UI: 3 條 Route (mechanism + cross_domain_source + VP)
    UI-->>RD: 呈現非典型架構 + 最小驗證實驗
    Note over UI: Route: — → generated (Inspiration 標籤)

    Note over UI: === Phase II: 概念篩選 + TRIZ 轉化 ===
    RD->>UI: 展開 VP，選擇有潛力的概念
    RD->>UI: 點擊「以此為 seed 啟動 TRIZ」
    Note over UI: Route: generated → seeded_to_triz

    UI->>AA: formalize_contradiction(seed=anti_anchor_route)
    AA-->>UI: TC 矛盾句 (improving/worsening_param) + seed_source 標記

    UI->>AA: oz_ot_analysis(contradiction_id, fa_result)
    AA-->>UI: OZ + OT + Px + PC 造句

    UI->>TS: solve_triz_layered(TC + OZ-OT context, seed_source=anti_anchor)
    TS-->>UI: LayeredTrizSolution (L1/L2/L3) + anti_anchor_lineage
    UI-->>RD: 分層 drill-down 卡片 + 「源自 Anti-Anchor」標記

    RD->>UI: 採納方案進 Decision Hub (5d)
    Note over UI: SolutionCandidate (source=triz, seed_source=anti_anchor)
```

### 3.2 跨子系統互動對照

| 使用者動作 | 觸發子系統 | 觸發狀態轉換 |
|-----------|-----------|-------------|
| 點擊反向探索 | Reverse Anti-Anchor (Appendix C) | Route: — → pending |
| AI 產出 Route | Analyst + Knowledge | Route: pending → generated (Inspiration) |
| VP 生成 | Evaluator | VP 附加至 Route |
| 展開 VP 篩選概念 | UI (Create 頁面) | 檢視 assumptions/confidence |
| **以概念為 seed 啟動 TRIZ** | **Analyst (formalize_contradiction)** | **Route: generated → seeded_to_triz; Contradiction: — → Verified** |
| **OZ-OT 分析** | **Analyst Agent** | **OzOtResult: — → Px Locked** |
| **TRIZ 三層求解** | **Forward TRIZ Solver (Appendix B)** | **LayeredTrizSolution: — → generated** |
| 進入 Decision Hub | Decision Hub | SolutionCandidate (source=triz, seed_source=anti_anchor) |

**Anti-Anchor 啟發閾值**：三條概念路線中至少一條「非對標」（物理機制與現有方案不同源）；若全部為同源變形，回退重新發散。篩選後的 seed 進入 TRIZ 流程，不再需要獨立通過 M1/M4 — 品質檢查由 TRIZ 流程的 Critic + CCI 負責。

### 3.3 設計決策：為什麼 Anti-Anchor 不直接進 Decision Hub

> **v1.2 變更** (2026-04-27)：Anti-Anchor 路線從「直入 Decision Hub」改為「seed → TRIZ 轉化 → Decision Hub」。

**根因分析（第一性原理）**：

Anti-Anchor 的定位是啟發工具（打破路徑依賴），但 v1.0/v1.1 的流程將其產出直接放入 Decision Hub 與 TRIZ 方案並列比較。Decision Hub 下游的 Gate P 要求 Interface Contract + 最小 CAD 範圍 + Evidence Coverage ≥ 40%，Anti-Anchor 路線天生缺乏這些交付物（因為它跳過了 OZ-OT、子系統分解、Evidence Registry 等步驟），導致下游審查迴圈浪費預估 10-18 天，且 PP-3（風險後置）、PP-4（決策不可追溯）迴歸。

**修正原則**：讓啟發歸啟發、工程歸工程。Anti-Anchor 負責「看到不一樣的」，TRIZ 負責「做得出來的」。

**保留的 Anti-Anchor 價值**：
- `seed_source` 標記全程可追溯（`SolutionCandidate.seed_source = "anti_anchor"`）
- VP 的 `cross_domain_source` 欄位保留，在 TRIZ L1 查矩陣時作為額外 context
- `seed_source=anti_anchor` 的 TRIZ 方案在候選池中可追溯，確保不全部收斂為同源方案

---

## §4 Scenario 3 — Decision Hub 品質評估 + Pre-CAD Gate 審查

> **v1.2 變更**：將原 Scenario 3 拆分為兩段，明確 RD（Decision Hub 品質評估）與主管（Gate P 審查）的職責邊界。
> **v1.3 變更**：Phase B 收斂掃描已退役（v9）。其 5 項檢查全部由 SIM 矩陣（ADR-008 D5）和 CCI（ADR-008 D4）前置覆蓋。Decision Hub 流程簡化為：RD 採納 → CCI 標籤 → 橫向比較 → MUST 快篩 → Evidence Coverage → Gate P。
> `seed_source=anti_anchor` 的 TRIZ 方案在候選池中保留追溯標記。

### 4.1 Decision Hub 品質評估（RD 張三 主導）

> **角色**: Persona 1 RD 張三
> **觸發**: Decision Hub 已匯流 3+ 條路線（含 TRIZ-only + AA-seeded TRIZ）
> **對齊痛點**: PP-3 風險後置
> **對應**: E3 Appendix D State Machine + Appendix E Decision Hub

```mermaid
flowchart TD
    Start(["Step 5d 候選池匯流"]) --> Hub["Decision Hub<br/>TRIZ ∥ AA-seeded TRIZ"]
    Hub --> Adopt["RD 採納方案<br/>+ CCI 標籤 (Evolution/Weak/Patch)<br/>+ 橫向比較"]

    Adopt --> SimDedup["SIM 去重:<br/>扣除 SIM 已收斂 TC 對"]
    SimDedup --> Heat{"架構健康度<br/>(淨節點數)"}
    Heat -->|節點 > 5| Halt1["漸進回退:<br/>① 回 Step 2c 重建功能模型<br/>② 仍 >5 → 回 Step 2b<br/>③ 仍無法收斂 → 回 Step 1"]
    Heat -->|循環矛盾| Halt2["依循環類型回退:<br/>結構性 → 回 Step 2c<br/>框架性 → 回 Step 2b/1"]
    Heat -->|healthy| MUST["5e MUST 快篩 (Go/No-Go)"]

    MUST --> RouteCheck{"≥3 條路線<br/>(含 ≥1 seed_source=anti_anchor)?"}
    RouteCheck -->|不通過,矛盾≥2| Back["回 Step 5-0 / 5a 重新發散"]
    RouteCheck -->|不通過,矛盾<2| Back2["回 Step 2c 檢視功能模型粒度"]
    RouteCheck -->|通過| EvCheck{"Evidence Coverage<br/>≥ 40%?"}
    EvCheck -->|不通過| BackEv["提示補充證據"]
    EvCheck -->|通過| Notify["系統推送 Gate P<br/>審查請求至主管 Dashboard"]

    style Halt1 fill:#FEE2E2
    style Halt2 fill:#FEE2E2
    style Notify fill:#DBEAFE
```

**Decision Hub 品質評估互動對照**

| 使用者動作 | 角色 | 觸發子系統 | 觸發狀態轉換 |
|-----------|------|-----------|-------------|
| 採納方案 + 檢視 CCI 標籤 | RD 張三 | Decision Hub (CCI overlay) | SolutionCandidate: — → adopted；CCI 標籤為資訊性（Evolution / Weak Evolution / Patch） |
| 架構健康度監控 | 系統自動 | Analyst Agent | 節點>5（SIM 去重後）→ 漸進回退 2c→2b→1；循環矛盾 → 依類型回退（結構性→2c / 框架性→2b 或 1） |
| MUST 快篩 | 系統自動 | Evaluator | Concept Route 逐條 Go/No-Go |
| 路線多樣性檢查 | 系統自動 | Evaluator | ≥3 條路線 + ≥1 Anti-Anchor |
| Evidence Coverage 檢查 | 系統自動 | EvidenceRegistryService | **Evidence Coverage ≥ 40%**（VERIFIED + APPROXIMATE 佔比，ADR-008 D3）；未達標則提示補充證據 |
| 檢視 CCI 標籤 | RD 張三 | Decision Hub (CCI overlay) | — （資訊性，不觸發狀態轉換；顯示 Evolution / Weak Evolution / Patch 分類） |
| 推��審查請求 | 系統自動 | Notification Service | Gate P: — → Pending Review（路線多樣性 + Evidence Coverage 均通過後觸發） |

### 4.2 Gate P 審查（RD 主管 李四 主導）

> **角色**: Persona 2 RD 主管 李四
> **觸發**: 系統在路線多樣性 + Evidence Coverage 通過後，自動推送 Gate P 審查請求至主管 Dashboard
> **使用介面**: Review 頁面（非 Create 頁面）
> **對齊痛點**: PP-4 決策不可追溯、PP-6 證據缺口不可見
> **對應**: E3 Appendix D State Machine (Gate P) + `Pre_CAD_Review_Template`

```mermaid
flowchart TD
    Notify(["系統推送 Gate P 審查請求"]) --> Open["主管開啟 Review 頁面"]
    Open --> Review["逐條審查路線:<br/>1. Interface Contract 完整度<br/>2. 最小 CAD 範圍<br/>3. Evidence Coverage ≥ 40%<br/>4. seed_source 追溯鏈"]

    Review --> TL{"每條路線<br/>滿足退出條件?"}
    TL -->|通過| Sign["主管簽核"]
    TL -->|不通過| Fix["退回 RD 補強<br/>（明確指出缺失項目）"]

    Sign --> PhaseIII["Phase II → Phase III<br/>Concept Route: Reviewed → Verified"]
    Fix --> Back["RD 回 Step 5a / 5b 補強"]

    style PhaseIII fill:#DCFCE7
    style Fix fill:#FEF3C7
```

**Gate P 審查互動對照**

| 使用者動作 | 角色 | 觸發子系統 | 觸發狀態轉換 |
|-----------|------|-----------|-------------|
| 收到審查通知 | 系統 → 主管 | Notification Service | — |
| 開啟 Review 頁面 | RD 主管 李四 | UI (Review 頁面) | — |
| 逐條審查 Interface Contract + CAD 範圍 | RD 主管 李四 | Human-in-the-Loop | — |
| 簽核 Pre-CAD | RD 主管 李四 | Human-in-the-Loop | Concept Route: Reviewed → Verified; Pre-CAD Report: Draft → Reviewed; **PHASE_II → PHASE_III** |
| 退回補強 | RD 主管 李四 | Human-in-the-Loop | Gate P: Pending Review → Returned（附退回理由） |

---

## §5 跨子系統互動總表

彙整本文件三個 scenario 中使用者動作與子系統/State Machine 的完整對應。

| Step | 使用者動作 | Primary Subsystem | 觸發 Agent | Artifact 狀態轉換 | 參照 (`E3--architecture-and-design.md`) |
|------|-----------|-------------------|-----------|------------------|---------------------------------------|
| 1 | 上傳 Brief 與素材 | — | Knowledge + Analyst | Constraint: — → Draft → Reviewed | §11.5.2 Agent-Tool 綁定 |
| 2 | 參與蘇格拉底問答 | — | Analyst | Contradiction: Draft → Reviewed | §11.4.1 主流程序列圖 |
| 3 | 校準 TRIZ 矛盾句 | Forward TRIZ Solver | TRIZ Solver + Analyst | Contradiction: Reviewed → Verified | Appendix B |
| 4 | 填寫假設台帳 | — | Analyst + Knowledge | Assumption: Reviewed → Verified | §11.2 逐步自動化分級 |
| 5-0 | 啟動 Anti-Anchor 啟發 | Reverse Anti-Anchor | Analyst + Knowledge | Route: — → generated (Inspiration) | Appendix C |
| 5-0→5a | 以 AA 概念為 seed 啟動 TRIZ | Forward TRIZ (seeded) | Analyst + TRIZ Solver | Route: generated → seeded_to_triz; LayeredTrizSolution: — → generated | Appendix B + C |
| 5a | 啟動 TRIZ 三路徑 | Forward TRIZ | TRIZ Solver | LayeredTrizSolution: — → generated | Appendix B |
| 5b | 定義子系統 | Forward Subsystem Discovery | Analyst | Subsystem: — → Draft (3-level) | Appendix A |
| ~~5c~~ | ~~SCAMPER 變形~~ | — | — | *(v9 移除)* | — |
| 5d | Decision Hub 採納 | 決策中心 | Evaluator | SolutionCandidate: — → adopted | Appendix E |
| 5e | MUST 快篩 | — | Evaluator | Concept Route: Draft → Reviewed | §11.2 逐步自動化分級 |
| P | Pre-CAD 審查 | — | Evaluator + Human | Concept Route: Reviewed → Verified；**Phase II → III** | Appendix D |
| 6 | CAD 審查 + DR EM | — | Evaluator + Knowledge | Evidence Matrix: Draft → Verified | Appendix D |
| 6e | 證據補齊迴圈 | — | Knowledge | Evidence: Draft → Verified | Appendix D |
| 7 | KT 決策簽核 | — | Evaluator + Human | Decision Record: Draft → Reviewed；Concept Route: Verified → Baselined | Appendix D |
| 8 | 費曼內化 | — | Knowledge | Asset: — → Released；**Phase III → COMPLETED** | Appendix D |

---

## §6 對照 00-discover 痛點 → 設計後體驗

| 現狀痛點 (PP) | 現狀表現 | 目標體驗流對應點 | 緩解機制 |
|--------------|---------|-----------------|---------|
| PP-1 經驗鎖定 | 直覺搜尋過去方案 | Scenario 2 Anti-Anchor 啟發 → TRIZ 轉化 | Forced Divergence（啟發）+ TRIZ 收斂（工程化） |
| PP-2 假設隱藏 | 預設答案未明說 | Scenario 1 蘇格拉底七類提問 | Assumption Challenge (E3--architecture-and-design.md §11.3.2 機制 1) |
| PP-3 風險後置 | Proto 才爆問題 | Scenario 3 Decision Hub 品質評估 (RD) + Gate P (主管) + 架構健康度監控 | SIM 矩陣前置跨矛盾衝突檢查 + CCI 複雜度判定 + 架構健康度（SIM 去重後淨節點）+ 漸進回退（2c→2b→1）；Anti-Anchor 經 TRIZ 工程化確保 OZ-OT + CCI 完備 |
| PP-4 決策不可追溯 | 半年後無法回溯 | Scenario 3 Validation Passport + KT Decision Record | 自動留痕（Artifact 狀態流轉） |
| PP-5 溝通斷層 | PM/RD/主管語言不同 | Step 1 約束改寫 + Step 8 費曼摘要 | 統一 Artifact schema |
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
