# RD Design Copilot — WBS 開發計劃 (Unified)

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-24`
**主要作者 (Lead Author):** PM / TaskMaster Hub
**審核者 (Reviewers):** TL / ARCH / PO
**狀態 (Status):** Approved
**模板對應:** VibeCoding 16 (WBS Development Plan)

---

## 合併說明 (Consolidation Note)

本 WBS 為 2026-04-15 統整三份已 superseded 的獨立 WBS 而成的單一主文檔，整併為三個工作流 (Workstream)：

| Workstream | 來源檔案 (superseded) | 原狀態 |
|-----------|----------------------|-------|
| **WS-A: API 對齊** | [`_superseded/E2x--wbs-api-alignment.md`](../_superseded/E2x--wbs-api-alignment.md) | 2026-04-07 · API 100% 對齊，剩 P0/P1 缺口 |
| **WS-B: E2E 差距修正** | [`_superseded/E2x--wbs-e2e-gap-closure.md`](../_superseded/E2x--wbs-e2e-gap-closure.md) | 2026-03-12 主 WBS 100% 完成；6.0 後續強化 96% |
| **WS-C: Mock → Live 遷移** | [`_superseded/E2x--wbs-mock-to-live-migration.md`](../_superseded/E2x--wbs-mock-to-live-migration.md) | 2026-04-07 · Sprint 0-3 ✅ / Sprint 4 🟡 |

### 衝突解決 (Conflict Resolution)

| 議題 | WS-A (API) | WS-B (E2E) | WS-C (Mock→Live) | 採用 |
|------|-----------|-----------|-----------------|------|
| TRIZ Su-Field 端點 | 已實作 | 已實作 (6.1) | 已實作 (Sprint 2) | 統一 ✅ Done |
| 501 stubs (`/export`, `/knowledge/writeback`, `/scamper/feedback`) | 已完成 | 已完成 (6.7) | 已完成 (Sprint 3-4) | 統一 ✅ Done |
| `unknown_factors` 持久化 | 已實作 (WP-3.1) | 已實作 (6.2) | 已實作 (Sprint 2) | 統一 ✅ Done |
| Socratic 問答注入 prompt | 未提及 | 🔲 6.6.4 設計中 | 未提及 | 以 **WS-C (mock-to-live)** 為準規則保留未完成；歸入 WS-B-6 |
| Mock 檔案殘留 (7 份) | 未提及 | 未提及 | 🟡 殘留 | 保留為 WS-C Sprint 4 主要待辦 |

**規則**：遇三方衝突時，以 mock-to-live（較新、較大範圍）為準，並在附註說明。

---

## 目錄

1. [專案總覽](#1-專案總覽-project-overview)
2. [WBS 結構總覽](#2-wbs-結構總覽-wbs-structure-overview)
3. [詳細任務分解](#3-詳細任務分解-detailed-task-breakdown)
4. [專案進度摘要](#4-專案進度摘要-project-progress-summary)
5. [風險與議題管理](#5-風險與議題管理-risk--issue-management)
6. [品質指標與里程碑](#6-品質指標與里程碑-quality-metrics--milestones)

---

## 1. 專案總覽 (Project Overview)

### 專案基本資訊

| 項目 | 內容 |
|------|------|
| 專案名稱 | RD Design Copilot (ebike design-copilot-blueprint) |
| 專案經理 | PM / TaskMaster Hub |
| 技術主導 | TL |
| 專案狀態 | 進行中（累計 ~97% 完成） |
| 文件版本 | v1.0（合併版） |
| 最後更新 | 2026-04-15 |

### 專案角色與職責 (RACI)

| 角色 | 負責人 | 主要職責 |
|------|--------|----------|
| **PM (Project Manager)** | TaskMaster Hub | 進度追蹤、三 workstream 協調 |
| **TL (Tech Lead)** | — | 架構決策、code review、ADR 把關 |
| **ARCH** | — | Supabase schema, FastAPI 邊界, ADR-001..005 |
| **BE (Backend Dev)** | — | `backend/app/api/v1/*` AI 端點、LLMService |
| **FE (Frontend Dev)** | — | React 19 pages, hooks/api, Lovable 佈署 |
| **Data** | — | Supabase migrations 000–004, RLS |
| **QA** | — | Playwright / Vitest / pytest |
| **PO** | — | Gate 驗收、E2E 規格對齊 |

---

## 2. WBS 結構總覽 (WBS Structure Overview)

### WBS 樹狀結構

```
WS-A: API 對齊 (Backend FastAPI vs SOW)          [✅ 99% / 31 endpoints live]
├── A-1  Infrastructure (WP-1)
├── A-2  Phase 1 Define 端點 (WP-2)
├── A-3  Phase 2 Diverge 端點 (WP-3)
├── A-4  Phase 3 Converge 端點 (WP-4)
├── A-5  Frontend UI 對齊 (WP-5)
└── A-6  剩餘 Gap (P0/P1)

WS-B: E2E 差距修正 (E2E 整合流程規格)              [✅ 主 WBS 100% · 6.0 96%]
├── B-1  Artifact 骨幹建設 (1.0)
├── B-2  整合機制補齊 (2.0)
├── B-3  資料流串接 (3.0)
├── B-4  Gate 對齊 (4.0)
├── B-5  驗證與收尾 (5.0)
└── B-6  後續強化 (6.0)

WS-C: Mock → Live 遷移 (Supabase 即時 API)         [🟡 ~85% · Sprint 4 in progress]
├── C-0  基礎建設 (Sprint 0)
├── C-1  專案 + Step 1 (Sprint 1)
├── C-2  Step 2 解方探索 (Sprint 2)
├── C-3  Step 3 審查決策 (Sprint 3)
└── C-4  知識管理 + 收尾 (Sprint 4)
```

### 工作包統計概覽

| Workstream | 工作包 | 已完成 | 進行中 | 待做 | 進度 |
|-----------|-------|--------|-------|------|------|
| WS-A API 對齊 | 35 | 32 | 0 | 3 | 91% |
| WS-B E2E 差距 | 67 | 66 | 1 | 0 | 98.5% |
| WS-C Mock→Live | 26 | 21 | 5 | 0 | 81% |
| **總計** | **128** | **119** | **6** | **3** | **~93%** |

**狀態圖示**：✅ Done / 🔄 In Progress / ⏳ Pending / ⬜ Not Started / ⏸ Parked

---

## 3. 詳細任務分解 (Detailed Task Breakdown)

> 任務編號規則：`{workstream}-{section}.{seq}`。狀態採統一欄位 `Done / In Progress / Pending`。

---

### WS-A · API 對齊 Workstream

> **來源**：`_superseded/E2x--wbs-api-alignment.md`（2026-04-07）
> **目的**：FastAPI 後端對齊 SOW v1.0 的 API 端點規劃。
> **成果速覽**：31 routes live、SOW 路徑 100% 對齊、11 個 SOW 外新增、501 stubs 清零。

#### A-1 Infrastructure (WP-1)

| 任務編號 | 任務名稱 | Owner | 狀態 | 備註 |
|---------|---------|-------|------|------|
| A-1.1 | FastAPI scaffold + CORS middleware | BE | Done | — |
| A-1.2 | Supabase 31 tables + migrations 000-004 | Data | Done | 偏差：改為 Supabase，無 SQLAlchemy ORM |
| A-1.3 | LLMService (retry + token + multi-provider + prompts) | BE | Done | ADR-003 closure |
| A-1.4 | Auth (Supabase Auth + RLS) | Data | Done | 偏差：ADR-001 替代自訂 JWT |
| A-1.5 | React scaffold + 19 pages + shadcn/ui | FE | Done | 超過 SOW 預期 |

#### A-2 Phase 1 Define 端點 (WP-2)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| A-2.1 | `POST /definitions/extract` | BE | Done |
| A-2.2 | `POST /definitions/rewrite` | BE | Done |
| A-2.3 | `POST /definitions/check-feasibility` (new) | BE | Done |
| A-2.4 | `POST /definitions/suggest-constraints` | BE | Done |
| A-2.5 | `POST /definitions/suggest-kpis` | BE | Done |
| A-2.6 | `POST /definitions/generate-5w1h` | BE | Done |
| A-2.7 | `POST /questions/generate` | BE | Done |
| A-2.8 | `POST /questions/follow-up` (new) | BE | Done |
| A-2.9 | `POST /questions/brief-impact` (new) | BE | Done |
| A-2.10 | `POST /questions/auto-tag` (new) | BE | Done |
| A-2.11 | `POST /causal-loops/generate` | BE | Done |
| A-2.12 | `POST /contradictions/{cid}/formalize` | BE | Done |
| A-2.13 | `POST /assumptions/extract` | BE | Done |
| A-2.14 | `GET /gates/{gate_id}/check` (8 gates) | BE | Done |

#### A-3 Phase 2 Diverge 端點 (WP-3)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| A-3.1 | `POST /alternatives/anti-anchor` | BE | Done |
| A-3.2 | `POST /alternatives/validation-passport` (new) | BE | Done |
| A-3.3 | `POST /triz/solve` (TC/PC) | BE | Done |
| A-3.4 | `POST /triz/sufield` (Su-Field, 76 std solutions, new) | BE | Done |
| A-3.5 | `POST /scamper/perform` | BE | Done |
| A-3.6 | `POST /scamper/subsystem-suggestions` | BE | Done |
| A-3.7 | `POST /scamper/feedback-contradictions` (ex-501 stub) | BE | Done |
| A-3.8 | `POST /unknown-factors/discover` (new) | BE | Done |
| A-3.9 | `POST /convergence/scan` (new) | BE | Done |
| A-3.10 | `POST /must/evaluate` | BE | Done |
| A-3.11 | `POST /pre-cad-reviews/{rid}/ai-analyze` | BE | Done |

#### A-4 Phase 3 Converge 端點 (WP-4)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| A-4.1 | `POST /risks/analyze` | BE | Done |
| A-4.2 | `POST /actions/suggest` | BE | Done |
| A-4.3 | `POST /want/criteria/seed` | BE | Done |
| A-4.4 | `POST /knowledge/writeback` (ex-501 stub) | BE | Done |
| A-4.5 | `POST /export` Markdown/JSON/PDF (ex-501 stub) | BE | Done |
| A-4.6 | `GET /health` | BE | Done |

#### A-5 Frontend UI 對齊 (WP-5)

| 任務編號 | 頁面 | Owner | 狀態 |
|---------|------|-------|------|
| A-5.1 | Dashboard (`ProjectDashboard.tsx` + `ProjectList.tsx`) | FE | Done |
| A-5.2 | Brief (`TaskDefinition.tsx`) | FE | Done |
| A-5.3 | Explore (`Explore.tsx`) | FE | Done |
| A-5.4 | Track (`Track.tsx` + `AssumptionLedger.tsx`) | FE | Done |
| A-5.5 | Create (`Create.tsx`) | FE | Done |
| A-5.6 | Review (`DesignReview.tsx` + `PreCadReview.tsx`) | FE | Done |
| A-5.7 | Decide (`DecisionRecord.tsx`) | FE | Done |
| A-5.8 | Knowledge / Feynman / ContradictionID / SolutionExplorer / CadInProgress (SOW 外新增) | FE | Done |

#### A-6 剩餘 Gap

| 任務編號 | 項目 | 等級 | Owner | 狀態 |
|---------|------|------|-------|------|
| A-6.1 | `projects.phase` state machine trigger (Supabase BEFORE UPDATE) | P0 | Data | Pending |
| A-6.2 | `POST /assumptions/{aid}/disprove` 專屬工作流 | P1 | BE | Pending |
| A-6.3 | `GET /knowledge/rag/search` RAG pipeline | P1 | BE | Pending |

---

### WS-B · E2E 差距修正 Workstream

> **來源**：`_superseded/E2x--wbs-e2e-gap-closure.md`（2026-03-12 主 + 2026-04-07 後續強化）
> **目的**：對齊 `docs/e2e/RD_Design_Copilot_整合流程.md` 差距清單。

#### B-1 Artifact 骨幹建設 (1.0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-1.1 | ArtifactState 統一型別 (Draft→Reviewed→Verified→Baselined→Released) | FE | Done |
| B-1.2 | 6 核心 Artifact 介面 (Constraint / Contradiction / Breakpoint / ConceptRoute / Evidence / Risk) | FE | Done |
| B-1.3 | ArtifactContext 全域管理 | FE | Done |
| B-1.4 | Gate-Artifact 狀態連動 (applyGateTransition) | FE | Done |
| B-1.5 | Artifact ID 生成 `{TYPE}-{SEQ}` | FE | Done |

#### B-2 整合機制補齊 (2.0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-2.1.1 | QuestionCategory 加入 `reframing` (7 類) | FE | Done |
| B-2.1.2 | SocraticTab UI 支援 Reframing | FE | Done |
| B-2.1.3 | Explore Gate 要求 7 categories 覆蓋 | FE | Done |
| B-2.2.1 | useContradictionScan hook (Fatal/Major/Minor) | FE | Done |
| B-2.2.2 | HealthMonitor 整合至 Create | FE | Done |
| B-2.2.3 | ContradictionConvergenceCard 接入真實資料 | FE | Done |
| B-2.2.4 | ConvergenceGraph 視覺化 | FE | Done |
| B-2.3.1 | App.tsx PreCadReview 路由 (`/projects/:id/pre-cad`) | FE | Done |
| B-2.3.2 | Sidebar/MobileNav 新增 Step P | FE | Done |
| B-2.3.3 | Pre-CAD Confidence Score 計算 | FE | Done |
| B-2.3.4 | PreCadScoreGauge 接入真實值 | FE | Done |
| B-2.4.1 | Gate 3 breakpoint ≥3 | FE | Done |
| B-2.4.2 | PhaseProgress 加入 "3.1" | FE | Done |

#### B-3 資料流串接 (3.0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-3.1.1 | InterfaceContract 6 維 type 定義 | FE | Done |
| B-3.1.2 | Alternative.interfaceContract 欄位 | FE | Done |
| B-3.2.1 | W7 驗證可行性 WANT criterion | FE | Done |
| B-3.2.2 | WantScore.evidence (artifactId + evidenceLevel) | FE | Done |
| B-3.2.3 | WANT 評分 UI 證據選擇器 | FE | Done |
| B-3.3.1 | AdverseConsequence type + computeACLevel() | FE | Done |
| B-3.3.2 | AC mock data | FE | Done |
| B-3.3.3 | Decision AC Tab | FE | Done |
| B-3.4.1 | KnowledgeRefsPanel 通用化 | FE | Done |
| B-3.4.2 | 各頁面嵌入 Knowledge Panel (5 pages) | FE | Done |
| B-3.5.1 | ProjectDataContext 設計 | FE | Done |
| B-3.5.2 | 各頁面遷移至 Context | FE | Done |

#### B-4 Gate 對齊 (4.0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-4.1 | Gate 2 要求 7 類 + 10 假設 | FE | Done |
| B-4.2 | Gate C 加入 North Star KPI | FE | Done |
| B-4.3 | Gate C MUST E2+ 重新驗證 | FE | Done |
| B-4.4 | Gate 7 AC 強制 | FE | Done |
| B-4.5 | Gate 8 Artifact 狀態檢查 (6 類資產) | FE | Done |
| B-4.6.1 | TrackAssumption 加 4 欄位 (worstConsequence / verificationCost / Duration / sourceArtifactId) | FE | Done |
| B-4.6.2 | Track mock data 更新 | FE | Done |
| B-4.6.3 | Kanban UI 顯示新欄位 | FE | Done |
| B-4.7.1 | 6 類 KnowledgeAssetType union | FE | Done |
| B-4.7.2 | Feynman UI 分類顯示 + 覆蓋率 | FE | Done |

#### B-5 驗證與收尾 (5.0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-5.1 | `npx tsc --noEmit` 零錯誤 | QA | Done |
| B-5.2 | `npm run build` 成功 (Lovable 部署) | QA | Done |
| B-5.3 | Gate 條件逐項驗證 | PO | Done |
| B-5.4 | Artifact 狀態流驗證 | QA | Done |
| B-5.5 | Mock Data 一致性 | QA | Done |

#### B-6 後續強化 (6.0，2026-03-13 → 2026-04-07)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| B-6.1.1 | TRIZ Su-Field 後端端點 | BE | Done |
| B-6.1.2 | Contradictions Su-Field 欄位 (migration 004) | Data | Done |
| B-6.1.3 | TC/PC/SF 流程文件 | ARCH | Done |
| B-6.2.1 | unknown_factors 表 (migration 000) | Data | Done |
| B-6.2.2 | `/unknown-factors/discover` 端點 | BE | Done |
| B-6.2.3 | useUnknownFactors hooks + Track 整合 | FE | Done |
| B-6.3.1 | Track 假設新增/刪除寫入 DB | FE | Done |
| B-6.3.2 | Kanban UI 串接 cache invalidation | FE | Done |
| B-6.3.3 | 實驗數量顯示修正 | FE | Done |
| B-6.4.1 | Contradiction→Question source link (migration 002) | Data | Done |
| B-6.4.2 | contradiction_assumption_links N:N (migration 002) | Data | Done |
| B-6.4.3 | subsystems.level + interface_contracts (migration 003) | Data | Done |
| B-6.5.1 | anti_anchor_routes.validation_passport (migration 001) | Data | Done |
| B-6.5.2 | `/alternatives/validation-passport` 端點 | BE | Done |
| B-6.6.1 | Socratic `/questions/follow-up` | BE | Done |
| B-6.6.2 | `/questions/brief-impact` | BE | Done |
| B-6.6.3 | `/questions/auto-tag` | BE | Done |
| B-6.6.4 | Socratic 問答注入矛盾識別/CLD prompt | BE | In Progress |
| B-6.7.1 | `/scamper/feedback-contradictions` 實作 | BE | Done |
| B-6.7.2 | `/export` 實作 | BE | Done |
| B-6.7.3 | `/knowledge/writeback` 實作 | BE | Done |
| B-6.8.1 | retry_on_transient decorator | BE | Done |
| B-6.8.2 | Token estimation + 80% 警示 | BE | Done |
| B-6.8.3 | 多 provider 抽象 (Anthropic/OpenAI/Azure/Gemini/Qwen) | BE | Done |
| B-6.8.4 | 集中 prompts (analyst/evaluator/triz_solver/knowledge) | BE | Done |

---

### WS-C · Mock → Live 遷移 Workstream

> **來源**：`_superseded/E2x--wbs-mock-to-live-migration.md`（2026-04-07）
> **目的**：將 17 個 mock data 檔替換為 Supabase 即時 API（59 react-query hooks）。

#### C-0 基礎建設 (Sprint 0)

| 任務編號 | 任務名稱 | Owner | 狀態 |
|---------|---------|-------|------|
| C-0.1 | Supabase Schema 建立 (31 tables) | Data | Done |
| C-0.2 | RLS policies (全表覆蓋) | Data | Done |
| C-0.3 | Supabase types.ts 自動產生 | FE | Done |
| C-0.4 | API 基礎架構 `src/hooks/api/` + react-query | FE | Done |
| C-0.5 | QueryBoundary / ErrorFallback 統一元件 | FE | Done |
| C-0.6 | Seed data + DevSeed.tsx | FE | Done |

#### C-1 專案 + Step 1 (Sprint 1)

| 任務編號 | 任務名稱 | 功能 | Owner | 狀態 | Mock 清除 |
|---------|---------|------|-------|------|----------|
| C-1.1 | Projects API + 頁面接入 | F01, F02 | FE | Done | mockProjects / mockDashboard ✅；mockNavCards 🟡 殘留 |
| C-1.2 | Brief / Constraints / KPIs API | F03-F06 | FE | Done | mockTaskDefinition / mockExtraction ✅ |
| C-1.3 | Socratic + Contradictions API | F07-F09 | FE | Done | mockContradictions ✅；mockExplore 🟡 殘留 |
| C-1.4 | Assumptions + CLD API | F10-F12 | FE | Done | mockAssumptions ✅ |

#### C-2 Step 2 解方探索 (Sprint 2)

| 任務編號 | 任務名稱 | 功能 | Owner | 狀態 | Mock 清除 |
|---------|---------|------|-------|------|----------|
| C-2.1 | Track API (假設看板 + 未知因素 + 實驗) | F13, F14 | FE | Done | mockTrack 🟡 殘留 |
| C-2.2 | Anti-Anchor + TRIZ(TC/PC/SF) + Subsystem API | F15-F17 | FE | Done | mockCreate 🟡 殘留 |
| C-2.3 | SCAMPER + Alternatives API | F18-F20 | FE | Done | 同上 |
| C-2.4 | Convergence Loop + Multi-Solution API | F21, F22 | FE | Done | mockConvergence ✅；mockConceptRoutes 🟡 殘留 |
| C-2.5 | Solution Explorer API | F23 | FE | Done | mockSolutions ✅ |
| C-2.6 | Pre-CAD + CAD Status API | F24, F25 | FE | Done | — |

#### C-3 Step 3 審查決策 (Sprint 3)

| 任務編號 | 任務名稱 | 功能 | Owner | 狀態 | Mock 清除 |
|---------|---------|------|-------|------|----------|
| C-3.1 | Evidence Matrix API | F26 | FE | Done | mockDesignReview ✅ |
| C-3.2 | Risks + Experiments API (含 linked_assumptions/evidence_level) | F27, F28 | FE | Done | 同上 |
| C-3.3 | Decision + WANT Scoring API | F30, F31 | FE | Done | mockDecisionRecord ✅ |
| C-3.4 | AC + Signatures + Actions API | F32-F34 | FE | Done | 同上 |
| C-3.5 | Export API (`/api/v1/export`) | F35 | BE/FE | Done | — |

#### C-4 知識管理 + 收尾 (Sprint 4, 🟡 In Progress)

| 任務編號 | 任務名稱 | 功能 | Owner | 狀態 | 備註 |
|---------|---------|------|-------|------|------|
| C-4.1 | Feynman Knowledge Entries API | F36 | FE | Done | useKnowledgeEntries live |
| C-4.2 | Knowledge Base API | F37 | FE | In Progress | Hook live；KnowledgeBase.tsx 仍 import mockKnowledge 作 fallback |
| C-4.3 | Knowledge Refs 遷移 | — | FE | In Progress | mockKnowledgeRefs 仍被使用 |
| C-4.4 | Mock 檔案清除 (7 殘留 + Explore/Track/Create/KnowledgeBase refactor) | — | FE | In Progress | 待辦：Explore.tsx / Track.tsx / Create.tsx / KnowledgeBase.tsx 移除 mock import；mockNavCards / mockConceptRoutes 刪檔 |
| C-4.5 | 整合測試 + E2E 驗證 (Playwright Gate 1.1 → PG3) | — | QA | Pending | 依賴 C-4.4 完成 |

> **永久保留**：`trizParameters.ts`（TRIZ 39 工程參數靜態知識庫）不需遷移。

---

### Module 8.0 · Auto-TRIZ v2 Integration (v2.0 新增)

> **來源**：[ADR-008](adrs/ADR-008-auto-triz-v2-integration.md)（2026-04-23）
> **目的**：整合 Auto-TRIZ v2 閉環流程（FA / OZ-OT / SIM / CCI / Evidence Registry），補齊 TRIZ 方法論結構性缺口。
> **規劃工時**：193h（後端 73h + 前端 80h + 文件 40h）

#### 8.1 後端 — Analyst v2 Agents

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.1.1 | `analyst.five_why()` agent + prompt | BE | 8h | ✅ Done |
| 8.1.2 | `analyst.kt_is_is_not()` agent + prompt | BE | 8h | ✅ Done |
| 8.1.3 | `analyst.function_analysis()` agent + prompt | BE | 12h | ✅ Done |
| 8.1.4 | `analyst.oz_ot_analysis()` agent + prompt | BE | 8h | ✅ Done |
| 8.1.5 | `analyst.entry_grading()` agent + prompt | BE | 5h | ✅ Done |

#### 8.2 後端 — TRIZ v2 Extensions

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.2.1 | `triz_solver.sim_matrix()` — 多 TC SIM 交互矩陣 | BE | 10h | ✅ Done |
| 8.2.2 | `triz_solver.complexity_check()` — CCI 複雜度指標 | BE | 8h | ✅ Done |
| 8.2.3 | `solve_layered()` 擴充：接收 FA + OZ-OT context | BE | 6h | ✅ Done |

#### 8.3 後端 — Evidence Registry Service

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.3.1 | `EvidenceRegistryService` — register/verify/coverage | BE | 12h | ✅ Done |
| 8.3.2 | Evidence API 端點（3 endpoints） | BE | 6h | ✅ Done |

#### 8.4 DB Migrations

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.4.1 | `function_models` 表 | Data | 2h | ✅ Done |
| 8.4.2 | `evidence_claims` 表 | Data | 2h | ✅ Done |
| 8.4.3 | `sim_matrices` 表 | Data | 2h | ✅ Done |
| 8.4.4 | `contradictions` 新增 oz_zone/ot_time/px_variable 欄位 | Data | 1h | ✅ Done |

#### 8.5 前端 — Explore Conditional Stepper

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.5.1 | `EntryGradingModal` 組件 | FE | 8h | ✅ Done |
| 8.5.2 | `ConditionalStepper` 框架（Level A/B/C 路由） | FE | 12h | ✅ Done |
| 8.5.3 | `ProblemScopingStep`（5Why + KT UI） | FE | 10h | ✅ Done |
| 8.5.4 | `FunctionAnalysisStep`（FA 組件交互圖 UI） | FE | 12h | ✅ Done |
| 8.5.5 | `useAnalystV2` hooks（4 hooks） | FE | 6h | ✅ Done |

#### 8.6 前端 — Create v2 Enhancements

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.6.1 | `OzOtPanel` 組件 | FE | 8h | ✅ Done |
| 8.6.2 | `CciBadge` 組件 | FE | 4h | ✅ Done |
| 8.6.3 | `EvidenceCoverageGauge` 組件 | FE | 6h | ✅ Done |
| 8.6.4 | `useCreateV2` hooks（2 hooks） | FE | 4h | ✅ Done |
| 8.6.5 | Gate PG2 evidence coverage ≥40% 檢查 | FE | 4h | ✅ Done |

#### 8.7 文件更新

| 任務編號 | 任務名稱 | Owner | 工時 | 狀態 |
|---------|---------|-------|------|------|
| 8.7.1 | P1 文件更新（API spec / IA / 前端架構 / WBS / MOC / ADR-008 / SOW） | Doc | 24h | ✅ Done |
| 8.7.2 | P2 文件更新（Page-Level Spec: 06_explore / 08_create / MAPPING） | Doc | 16h | ✅ Done |

---

## 4. 專案進度摘要 (Project Progress Summary)

### 整體進度統計

| Workstream | 工作包 | Done | In Progress | Pending | 進度 |
|-----------|-------|------|-------------|---------|------|
| WS-A API 對齊 | 35 | 32 | 0 | 3 | 91% |
| WS-B E2E 差距 | 67 | 66 | 1 | 0 | 98.5% |
| WS-C Mock→Live | 26 | 21 | 5 | 0 | 81% |
| Module 8.0 Auto-TRIZ v2 | 25 | 25 | 0 | 0 | 100% |
| **總計** | **153** | **144** | **6** | **3** | **~94%** |

### 近期里程碑

- **2026-03-12**：WS-B 主 WBS (1.0-5.0) 42 工作包 100% 完成
- **2026-04-07**：WS-A API 端點 31 routes live + 501 stubs 清零；WS-C Sprint 3 完成
- **2026-04-15**：三份 WBS 合併為單一主文檔 (本檔)
- **2026-04-24**：Module 8.0 Auto-TRIZ v2 Integration 全部 25 工作包完成（後端 8.1-8.4 + 前端 8.5-8.6 + 文件 8.7）
- **目標**：Sprint 4 收尾（移除 7 mock 殘留 + Playwright E2E 驗證）後，整體達 100%

---

## 5. 風險與議題管理 (Risk & Issue Management)

### 中風險項目

| 風險項目 | 影響 | 可能性 | 緩解措施 | 負責人 |
|---------|-----|-------|---------|--------|
| `projects.phase` 可被任意更新（無 state machine trigger）| 中 | 中 | A-6.1：Supabase BEFORE UPDATE trigger | Data |
| Sprint 4 mock 殘留延遲清除影響 E2E 驗證 | 中 | 中 | 先以 C-4.4 為 release 障礙項目優先處理 | FE |
| Socratic 問答 prompt 注入設計未定（B-6.6.4）| 低 | 中 | 2026-W17 前完成設計 spike | BE |

### 低風險項目

| 風險項目 | 影響 | 可能性 | 緩解措施 |
|---------|-----|-------|---------|
| 後端無 OpenAPI → 前端型別手動同步 | 低 | 中 | 後續評估自動匯出腳本 |
| `/assumptions/{aid}/disprove` 反證端點缺失 | 低 | 低 | 目前以 status='refuted' 替代；P1 補齊 |
| RAG 知識檢索 `/knowledge/rag/search` 未實作 | 低 | 低 | P1 後續版本 |

### 議題追蹤清單

| ID | 議題 | 嚴重度 | 狀態 | Owner |
|----|------|-------|------|-------|
| ISS-001 | Sprint 4 殘留 7 mock 檔（Explore/Track/Create/KnowledgeBase 仍 import fallback）| 中 | Open | FE |
| ISS-002 | Phase state machine trigger 缺失（P0）| 中 | Open | Data |
| ISS-003 | Socratic 問答注入 prompt 設計未定 | 低 | In Progress | BE |

---

## 6. 品質指標與里程碑 (Quality Metrics & Milestones)

### 關鍵里程碑

| 里程碑 | 預定日期 | 狀態 | 驗收標準 |
|-------|---------|------|---------|
| M1: WS-B 主差距修正完成 | 2026-03-12 | Done | 42 工作包 100% + `tsc`/`build` 通過 |
| M2: API 端點對齊 + 501 清零 | 2026-04-07 | Done | 31 routes live，路徑 100% 對齊 |
| M3: Sprint 3 審查決策 live | 2026-04-07 | Done | Evidence/Risks/Decision 全 hook 化 |
| M4: Sprint 4 知識 + Mock 清零 | 2026-W17 | In Progress | 7 殘留 mock 移除、Playwright 通過 |
| M5: P0 closure (phase trigger) | 2026-W18 | Pending | A-6.1 上線 |
| M6: Release v1.0 | TBD | Pending | 全部 Gate 1.1→PG3 可重現走查 |

### 品質指標

**已達成**
- TypeScript 型別檢查：`npx tsc --noEmit` 零錯誤 ✅
- 架構合規性：8 Gate 全 UI/API 實作 ✅
- API 一致性：SOW 路徑 100% 對齊、前後端 schema 一致 ✅
- 501 stub：0 個 ✅

**待達成**
- Mock 清除率：目前 10/17，目標 16/17（trizParameters 永久保留）
- Playwright E2E 覆蓋：Gate 1.1 → PG3 全流程
- 後端 OpenAPI 匯出 → 前端型別自動同步

---

## 7. 專案管控機制

### 變更管控

所有 WBS 範疇、架構、時程變更均須建立或更新 ADR：

- [ADR-001](adrs/ADR-001-baas-first-architecture.md) — BaaS-First Architecture
- [ADR-002](adrs/ADR-002-server-side-business-logic.md) — Server-Side Business Logic
- [ADR-003](adrs/ADR-003-llm-service-hardening.md) — LLM Service Hardening (A-1.3 / B-6.8 closure)
- [ADR-004](adrs/ADR-004-qa-devops-infrastructure.md) — QA/DevOps Infrastructure
- [ADR-005](adrs/ADR-005-scope-expansion.md) — Scope Expansion
- [ADR-008](adrs/ADR-008-auto-triz-v2-integration.md) — Auto-TRIZ v2 Integration (Module 8.0)

### 歷史版本

本文合併前的三份獨立 WBS 保留於 `docs/_superseded/` 作歷史紀錄：
- [`E2x--wbs-api-alignment.md`](../_superseded/E2x--wbs-api-alignment.md)
- [`E2x--wbs-e2e-gap-closure.md`](../_superseded/E2x--wbs-e2e-gap-closure.md)
- [`E2x--wbs-mock-to-live-migration.md`](../_superseded/E2x--wbs-mock-to-live-migration.md)

---

**PM**: TaskMaster Hub
**最後更新**: 2026-04-15
**下次檢討**: Sprint 4 週五站立會
