# Product Requirements Document (PRD)
# RD Design Copilot v3.0 — Discovery Phase

---

## 文件資訊

| 項目 | 內容 |
|------|------|
| **產品名稱** | RD Design Copilot |
| **版本** | v3.0 |
| **文件狀態** | Draft |
| **建立日期** | 2026-02-01 |
| **最後更新** | 2026-04-13 |
| **文件擁有者** | [PM 姓名] |
| **文件範圍** | Discovery Phase — WHY we build, WHO we serve, WHAT problem we solve |

---

## 1. 產品概述

### 1.1 一句話定義

> **RD Design Copilot 是一套 AI 輔助的早期概念設計系統，把「未知」變成「可追蹤的假設」，把「靈感」變成「可審查的方案」，把「試錯」變成「最小實驗」，並透過數位線索 (Digital Thread) 連結所有設計工件與證據，驅動 Evidence-based Gate 決策。**

### 1.2 Customer Promise

> **RD Design Copilot 讓 RD 工程師在概念設計階段，用結構化的 AI 輔助發散與收斂流程，在更短的時間內探索更多可能性、更早暴露風險，使每一個設計決策都有可追溯的證據鏈。**

### 1.3 產品願景

在產品開發早期階段（概念設計），協助 RD 團隊：
- **結構化發散**：用 TRIZ + Anti-Anchor Sprint 擴大可能性空間，打破路徑依賴
- **嚴格收斂**：用 KT Decision Analysis + Evidence Matrix 做可審查的決策
- **最小驗證**：用假設台帳 + 最小實驗 + 證據補齊迴圈降低後期返工
- **知識增強**：用企業知識庫 RAG + 網路文獻搜尋自動注入佐證

### 1.4 產品定位

```
┌─────────────────────────────────────────────────────────────────┐
│                        產品定位                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  通用 LLM (ChatGPT/Gemini)      RD Design Copilot               │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ 探索、學習、草稿     │      │ 正式設計、決策、審查 │        │
│  │ 自由對話             │      │ 結構化流程           │        │
│  │ AI 自由發揮          │      │ AI 受約束            │        │
│  │ 一次性輸出           │  →   │ 可追蹤記錄           │        │
│  │ 無法審查             │      │ 可進設計審查         │        │
│  │ 無證據鏈             │      │ Evidence-driven Gate │        │
│  └──────────────────────┘      └──────────────────────┘        │
│                                                                  │
│  核心差異：不是讓 AI 更聰明，而是讓 AI 輸出                      │
│           「可審查、可追蹤、可負責、有證據鏈」                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 目標用戶

### 2.1 主要用戶 (Primary Users)

| 用戶角色 | 描述 | 使用場景 | 痛點 |
|---------|------|---------|------|
| **RD 工程師** | 負責概念設計與方案生成 | 日常設計工作 | 經驗鎖定、跨域知識不足 |
| **RD 主管** | 負責設計審查與決策 | 設計審查會議 | 決策依據不足、風險不可見 |
| **專案經理 (PM)** | 負責需求對齊與進度追蹤 | 專案管理 | 溝通斷層、反覆對齊 |

### 2.2 次要用戶 (Secondary Users)

| 用戶角色 | 描述 | 使用場景 |
|---------|------|---------|
| **品質工程師** | 參與風險評估 | FMEA、風險審查 |
| **製造工程師** | 參與可製造性評估 | DFM/DFA 審查 |
| **高階主管** | 接收決策摘要 | 一頁式報告 |

### 2.3 用戶畫像

**典型用戶：資深 RD 工程師 張三**

- **背景**：10 年機構設計經驗，熟悉馬達、減速機整合
- **痛點**：
  - 習慣用熟悉的方案，擔心錯過更好的架構
  - 跨域知識（熱、振、控制）不足
  - 早期假設沒人追蹤，後期才發現問題
- **期望**：
  - 有工具幫忙擴大可能性，但不是「亂槍打鳥」
  - 決策有依據，可以跟老闆解釋
  - 經驗可以沉澱，不用每次從頭來

### 2.4 Day-in-the-Life 場景（主要 Persona）

> **週一早上 9:00 — 張三接到新專案 Brief**
>
> 張三打開 Brief，裡面寫著「整合式中置馬達，功率密度提升 20%，成本降 15%」。他心裡閃過三個熟悉的架構，但去年就是因為太快收斂到「安全牌」方案，後來被客戶退回重做。
>
> 這次他打開 RD Design Copilot，把 Brief 和上一代測試報告丟進去。系統幫他拆解出 12 條硬約束、識別出 3 對矛盾（功率密度 vs. 散熱面積、減重 vs. 結構剛性、成本 vs. 材料等級），並用蘇格拉底問答逼他把「以為是常識」的前提攤開來看。
>
> 下午他跑了 Anti-Anchor Sprint，發現一條自己從沒想過的非同軸佈局方案。雖然直覺告訴他「不太可能」，但系統標出這條路線的假設和需要驗證的最小實驗——只要一次 thermal simulation 就能判斷。
>
> 週五設計審查時，他帶著 Evidence Matrix 和 KT 決策記錄進會議室。主管第一次不用問「你為什麼選這個方案？」，因為答案已經在證據鏈裡。

---

## 3. 問題陳述

### 3.1 核心問題

> **早期概念設計階段面臨「三重困境」：未知最多、決策最重、時間最緊。傳統流程依賴「試了才知道」，導致高昂的返工成本。**

### 3.2 問題量化

| 指標 | 現狀 | 影響 |
|------|------|------|
| 早期決策影響比例 | 70% 最終成本 | 架構選錯，後期改不動 |
| 早期資訊確定度 | <10% | 決策依據不足 |
| 設計變更來源 | 60% 源自「早期沒想到」 | 後期大返工 |
| 架構級返工次數 | 3-5 次/專案 | 時間、成本、信任成本 |

### 3.3 具體痛點

| 痛點 | 現象 | 後果 |
|------|------|------|
| **經驗鎖定** | RD 傾向用熟悉的方案 | 錯過更好的架構 |
| **腦內庫存有限** | 創意依賴個人經驗 | TRIZ 問得出來，答不出來 |
| **假設隱藏** | 前提沒被翻出來 | 後期才發現假設是錯的 |
| **風險後置** | 問題拖到 prototype 才爆 | 返工成本最高 |
| **決策不可追溯** | 當初為什麼選這個方案？ | 經驗無法沉澱 |
| **溝通斷層** | RD、PM、老闆各說各話 | 反覆對齊、反覆開會 |
| **證據缺口不可見** | 不知道哪些決策有證據支撐 | Gate Review 流於形式 |

---

## 4. 產品目標與成功指標 (HEART/GSM Framework)

### 4.1 Goals → Signals → Metrics

| 目標 (Goal) | 對應痛點 | 訊號 (Signal) | 指標 (Metric) | 基線 | 目標值 |
|-------------|---------|---------------|---------------|------|--------|
| **G1: 擴大設計可能性空間** | 經驗鎖定、腦內庫存有限 | 方案探索路線數增加 | 方案探索數量（含 Anti-Anchor） | 1-2 條 | ≥3 條 |
| **G2: 使未知可見、可追蹤** | 假設隱藏 | 假設被識別並追蹤 | 假設驗證覆蓋率 | <30% | ≥80% |
| **G3: 前置風險驗證** | 風險後置、證據缺口不可見 | 架構級返工減少 | 架構級返工次數 | 3-5 次 | ≤2 次 |
| **G4: 決策可審查、可複用** | 決策不可追溯 | KT 記錄與 Evidence Matrix 完整 | 決策可追溯率 | 低 | 100% |
| **G5: 提升溝通效率** | 溝通斷層 | 概念評審時間縮短 | 概念評審效率 | 3-4 hr/次 | ≤2 hr/次 |
| **G6: 用戶願意使用** | — | 用戶主動使用系統 | 用戶採納率 | N/A | ≥70% |
| **G7: 證據缺口可見** | 證據缺口不可見 | Evidence Matrix 覆蓋 | 證據缺口識別率 | N/A | ≥90% |

### 4.2 非目標 (Non-Goals)

| 非目標 | 原因 |
|--------|------|
| 取代 RD 工程師 | AI 是副駕，不是駕駛 |
| 自動輸出「最優解」 | 早期沒有足夠資訊支撐最優解 |
| 取代詳細設計工具（CAD/CAE） | 專注於概念階段 |
| 自動生成可簽核的設計文件 | 責任在人，AI 只提供草稿 |

---

## 5. Product Principles（產品原則）

以下原則是所有後續 Define / Develop 階段的設計決策守欄：

| # | Always | Never |
|---|--------|-------|
| 1 | **AI 建議，人決策** — AI 提供結構化選項與證據，最終判斷權在 RD | AI 自行做出設計決策或跳過人工確認 |
| 2 | **證據先行** — 每一個 Gate 通過都必須有可追溯的證據支撐 | 允許無證據的決策通過 Gate |
| 3 | **結構化但不僵化** — 流程引導發散與收斂，但 RD 可跳過非關鍵步驟 | 強迫 RD 填完所有欄位才能往下走 |
| 4 | **打破錨定** — 每次發散至少包含一條非對標、非慣性路線 | 讓 AI 只產出「安全牌」方案 |
| 5 | **透明可解釋** — AI 的每一個建議都附帶推理依據與來源 | 用 AI confidence score 取代工程判斷 |
| 6 | **漸進式負擔** — 初次使用 2 小時內完成首個專案，複雜度隨需求遞增 | 要求用戶一開始就填滿 Evidence Matrix |
| 7 | **知識可沉澱** — 每個專案的決策記錄與被推翻假設都回寫知識庫 | 讓經驗停留在個人腦中 |

---

## 6. Scope Boundaries（範圍邊界）

### 6.1 This Product IS

- 概念設計階段的 AI 輔助工具（從 Brief 到決策記錄）
- 結構化發散與收斂的流程引擎
- 證據驅動的 Gate 決策支援系統
- 設計知識的沉澱與複用平台

### 6.2 This Product IS NOT

- 詳細設計工具（不取代 CAD/CAE/CAM）
- 自動設計系統（不生成最終設計圖面）
- 專案管理工具（不取代 Jira/MS Project）
- 通用 AI 聊天機器人（不做開放式問答）
- PLM / PDM 系統（不管理 BOM 或工程變更流程）

---

## 7. 產品假設

| 編號 | 假設 | 若假設錯誤的影響 | 驗證方式 |
|------|------|-----------------|---------|
| A1 | 用戶願意輸入結構化資料 | 採納率低 | Alpha 用戶訪談 |
| A2 | 用戶接受 AI 輔助但不取代決策 | 信任問題 | Beta 用戶回饋 |
| A3 | KT 決策框架適用於客戶產業 | 流程不合用 | 客戶訪談 |
| A4 | 客戶有足夠的過往案例可供 RAG 學習 | 知識庫品質差 | 資料盤點 |
| A5 | MUST Rulebook 的分層證據要求 (E0-E1 / E2+) 足以區分粗篩與精篩 | 篩選品質不一致 | Pilot 專案驗證 |
| A6 | Anti-Anchor Sprint 能有效打破路徑依賴 | 工程師抗拒或流於形式 | Alpha 用戶觀察 |

---

## 7A. 使用者故事與允收標準 (User Stories × UAT)

> **目的**：將第 2、3 節的 Persona / Day-in-the-Life / 痛點 refactor 成 Given/When/Then 風格的可驗證 User Story，供後續 BDD ([`../02-design/E5x--bdd-scenarios.md`](../02-design/E5x--bdd-scenarios.md)) 與 E2E 手測腳本 ([`../02-design/E7x--e2e-manual-scripts/`](../02-design/E7x--e2e-manual-scripts/)) 對應。
>
> **Story 格式**：`As [role], I want [capability], so that [benefit]`
> **UAT 格式**：Given/When/Then 三段；每條 3-5 項可驗證 checklist。

### 7A.1 使用者故事一覽

| Story ID | 角色 (As) | 能力 (I want) | 益處 (So that) | 對應痛點 | 對應 BDD Feature |
|----------|----------|---------------|----------------|---------|-----------------|
| **US-01** | RD 工程師 | 上傳 Brief 後自動拆解出硬約束 / 矛盾 / 假設 | 不靠記憶列清單、避免漏項 | 假設隱藏、腦內庫存有限 | Feature 1 (TRIZ) Background |
| **US-02** | RD 工程師 | 在 Create 頁以分層 drill-down 探索 TRIZ 解（L1→L2→L3） | 解耦「快速看答案」與「深入分析」，節省時間 | 經驗鎖定 | Feature 1 |
| **US-03** | RD 工程師 | 啟動 Anti-Anchor Sprint 產生 ≥3 條反向路線 | 打破自己習慣的「安全牌」慣性 | 經驗鎖定、腦內庫存有限 | Feature 2 (Anti-Anchor) |
| **US-04** | RD 工程師 | 為每條路線生成 Validation Passport 並追蹤假設狀態 | 在後期返工前先暴露風險 | 風險後置、假設隱藏 | Feature 2 |
| **US-05** | RD 主管 | 在 Pre-CAD Gate 以六維評分 + citations 審查方案 | 能據實質證據簽核，而非憑直覺 | 決策依據不足、證據缺口不可見 | Feature 3 (Pre-CAD) |
| **US-06** | RD 主管 | 看見 MUST 硬限制的 Pass/Conditional/Fail 分類 | 明確區分「淘汰」與「保留但補證據」 | 證據缺口不可見 | Feature 3 |
| **US-07** | RD 工程師 | 用 Evidence Matrix 為每個 KT 決策項關聯證據來源 | 日後回溯「當初為什麼這麼選」有依據 | 決策不可追溯 | — (TBD by 2026-05-15) |
| **US-08** | PM | 從 Dashboard 取得單一 project 的階段 / gate / 風險聚合摘要 | 不用在多個頁面拼湊進度 | 溝通斷層 | — (TBD) |
| **US-09** | RD 工程師 | 對 AI 產生的每一條建議點開來源 (KB- / WEB- citation) | 判斷 AI 是否幻覺或資料過時 | 幻覺風險、AI 不可解釋 | Cross-cutting |
| **US-10** | RD 工程師 | 將已驗證/推翻的假設回寫知識庫 | 團隊下次設計可以複用 | 經驗無法沉澱 | — (TBD) |
| **US-11** | 品質工程師 | 在 Pre-CAD Gate 看到主要失效機制與歷史失效對照 | 把 FMEA 議題提前到概念階段 | 風險後置 | Feature 3 (§失效機制) |
| **US-12** | 高階主管 | 看到一頁式的 Gate 決策摘要（MUST / WANT / Evidence） | 快速理解 go/no-go 的關鍵理由 | 溝通斷層 | — (TBD) |

### 7A.2 UAT 細則（選主要 6 條展開；其餘延後至對應 BDD）

#### UAT-01（對應 US-01）：Brief 上傳 → 自動拆解
- **Given** 使用者登入專案、未凍結 Brief
- **When** 上傳 PDF + 貼入文字 Brief 並點 "AI Extract"
- **Then**：
  - [ ] 於 10 秒內回傳 Constraints / KPIs / Contradictions 三區塊
  - [ ] 每個 Constraint 含分類 (hard / soft) 與 source (段落 / 行號)
  - [ ] 至少 1 對 Contradiction 以「improving vs worsening」格式呈現（TC-only，依 ADR-007；若 LLM 無法映射到 39 參數，該矛盾以 `type=null + rationale` 標示，UI 導引使用者回 Socratic 追問）
  - [ ] 用戶可編輯/刪除每一項；編輯後 status 改為 user_modified

#### UAT-02（對應 US-02）：TRIZ 分層解矛盾
- **Given** 已凍結 Brief 且存在 ≥1 formalized contradiction（TC-only，依 [ADR-007](../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)；使用者**不需手動選擇 TC/PC/SF**，系統自動識別 TC，後續 PC/SF 於 Create 階段派生）
- **When** 使用者點 Create Tab ①「Solve Layered」
- **Then**：
  - [ ] L1 surface card 於 5s 內串流顯示（skeleton → 實際內容）
  - [ ] L1 critic confidence < 0.6 時自動繼續 L2，否則顯示 drill-down 按鈕
  - [ ] 每 InventivePrinciple 含至少 1 筆 EvidenceReference
  - [ ] 多解情況下顯示 Phase B directive
  - [ ] 後端於 `solve_triz_layered` 入口自 TC 派生 PC/SF（使用者無感知）

#### UAT-03（對應 US-03）：Anti-Anchor 路線
- **Given** 至少一個 `confirmed` anchor solution
- **When** 使用者於 Explore 頁點 "Generate Anti-Anchor Routes"
- **Then**：
  - [ ] 回傳恰好 3 條（預設）路線，`diff_score > 0.3`
  - [ ] 每條路線有 `ac_risk_level ∈ {L, M, H, H*}`
  - [ ] `diff_score` 由高至低排序
  - [ ] 點單條路線可進入 Validation Passport（至少 2 條 assumption）

#### UAT-05（對應 US-05）：Pre-CAD 六維評分
- **Given** 已有候選方案 CR-Axxx 且 interface contract 填寫完整
- **When** 點 "AI Analyze" 產 Pre-CAD report
- **Then**：
  - [ ] MUST 6 項回傳 Pass/Conditional/Fail 三分類（非 1-5 分）
  - [ ] 定性 4 維度（Module Independence / Testability / Failure Mechanism / MVP CAD Effort）以 1-5 分呈現
  - [ ] 每項評分均附 Artifact ID 或 citation 引用
  - [ ] 若任一 MUST = Fail → UI 阻擋 "Sign & Pass Gate"

#### UAT-09（對應 US-09）：Citation 可追溯
- **Given** 頁面顯示任何 AI 建議（TRIZ / Pre-CAD / Knowledge panel）
- **When** 使用者點 citation 標籤（KB-xxx 或 WEB-xxx）
- **Then**：
  - [ ] 跳 side-panel 顯示 snippet、source_url（若 web）、retrieved_at
  - [ ] 無 citation 的建議必須標 "No source — human judgement only"
  - [ ] source_url 若有，必為 HTTPS

#### UAT-11（對應 US-11）：失效機制對照
- **Given** Pre-CAD report
- **When** 品質工程師展開「主要風險機制 (Failure Mechanism)」區塊
- **Then**：
  - [ ] 顯示「方案最可能怎麼死」條目（熱失控 / 磨損 / 雜訊干擾等）
  - [ ] 至少引用 1 筆 FMEA / 8D 歷史案例（KB-FMEA-xxx）
  - [ ] 提供跳轉至 Risk Register 的連結

> 其餘 UAT（04, 06, 07, 08, 10, 12）延後至各對應 BDD feature 補齊 — `TBD — <pm TBD> by 2026-05-15 TBD`。

---

## 8. 產品風險

### 8.1 技術風險

| 風險 | 機率 | 衝擊 | 緩解措施 |
|------|------|------|---------|
| AI 幻覺導致錯誤建議 | 中 | 高 | 強制證據鏈、人工確認、RAG 佐證 |
| 知識庫資料品質不佳 | 中 | 中 | 資料清洗、人工審核、知識回寫漸進改善 |
| AutoTRIZ 規則引擎覆蓋率不足 | 中 | 中 | LLM 補足 + 持續擴充規則庫 |
| 與現有系統整合困難 | 中 | 中 | 標準 API、階段性整合 |

### 8.2 用戶與採納風險

| 風險 | 機率 | 衝擊 | 緩解措施 |
|------|------|------|---------|
| 用戶抗拒填寫結構化資料 | 中 | 高 | 簡化輸入、提供範本、AI 預填 |
| Evidence Matrix 填寫負擔過重 | 中 | 高 | AI 預填、模板化、漸進式填寫 |
| 決策責任歸屬不清 | 低 | 高 | 明確簽核機制、教育訓練 |

### 8.3 商業風險

| 風險 | 機率 | 衝擊 | 緩解措施 |
|------|------|------|---------|
| 市場採納速度低於預期 | 中 | 高 | 先以單一 BU pilot 驗證價值，再橫向擴展 |
| 法規/合規要求（AI 輔助設計決策的責任歸屬） | 低 | 高 | 持續追蹤 EU AI Act 與產業規範，保持「人決策」架構 |
| 競品（通用 LLM 能力快速追趕）侵蝕差異化 | 中 | 中 | 持續深化「結構化流程 + 證據鏈」護城河，這不是純 LLM 能力問題 |
| 內部資源/預算不足以支撐全功能開發 | 中 | 中 | MVP 範圍聚焦 Phase I-II，Phase III 依 pilot 結果決定投入 |

---

## 9. Open Questions（待釐清問題）

以下是目前尚未有答案、但對產品方向有重大影響的問題：

| # | 問題 | 影響範圍 | 預計釐清方式 | 目標日期 |
|---|------|---------|-------------|---------|
| Q1 | 目標客戶的第一個 pilot BU 是誰？他們的設計流程成熟度如何？ | 整體產品範圍與 MVP 定義 | 客戶訪談 | TBD |
| Q2 | 客戶現有知識庫（案例/規範/失效報告）的數量與品質是否足以支撐 RAG？ | 知識增強層的價值 | 資料盤點 | TBD |
| Q3 | RD 工程師對 AI 輔助的接受度如何？是否有組織文化阻力？ | 採納策略與 change management | 用戶訪談 + 問卷 | TBD |
| Q4 | 客戶的設計審查流程（Gate Review）是否已有標準化？Copilot 需要配合還是重塑？ | 流程設計 | 客戶訪談 | TBD |
| Q5 | 多模態素材（PDF/圖片/Excel）的 AI 提取準確率是否達到可用門檻？ | F1.7 功能可行性 | 技術 PoC | TBD |
| Q6 | 部署模式（cloud / on-premise / hybrid）由客戶 IT 政策決定，目前未確認 | 技術架構 | 客戶 IT 訪談 | TBD |

---

## 變更記錄

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|---------|------|
| 0.1 | 2026-02-01 | 初版建立 | [作者] |
| 2.0 | 2026-03-12 | 全面對齊 E2E 架構：新增 Anti-Anchor Sprint、AutoTRIZ 混合架構、Pre-CAD Gate、Evidence Matrix、Gate C、證據補齊迴圈、知識增強層、Multi-Agent 架構、Interface Contract、6 核心工件資料模型、分層 MUST 證據要求、知識回寫機制 | [作者] |
| 2.1 | 2026-03-12 | 新增 F1.7 多模態素材解讀與結構化提取；F2.3 AutoTRIZ 增加矛盾收斂圖；NFR-13 擴展為用戶端上傳；AI 角色邊界更新 | [作者] |
| 3.0 | 2026-04-13 | 依五家公司審計重構 — 精簡至 Discovery 階段核心內容。移除功能需求、非功能需求、用戶旅程、資料模型、技術架構、里程碑、未來擴展至 01-define 階段文件。新增 Customer Promise、Product Principles、Scope Boundaries、Open Questions。重構 KPIs 為 HEART/GSM framework。擴充產品風險（新增商業風險）。 | [作者] |

---

**文件狀態**: Draft
**下次審查日期**: [日期]
**審核者**: [姓名]
