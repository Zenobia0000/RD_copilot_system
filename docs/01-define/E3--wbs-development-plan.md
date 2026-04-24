# RD Design Copilot v1.0 — WBS 開發計劃 (0 → 1)

---

**文件版本 (Document Version):** `v2.3` (2026-04-24 納入 Module 9.0 Harness Architecture Refactoring)
**最後更新 (Last Updated):** `2026-04-24`
**主要作者 (Lead Author):** PM / TaskMaster Hub
**審核者 (Reviewers):** TL, ARCH, PO, QA Lead, DevOps Lead
**狀態 (Status):** Approved
**模板對應:** VibeCoding 16 (WBS Development Plan)
**取代對象:** [`E3x--wbs-development-plan v1.0`](../_superseded/E3x--wbs-development-plan-v1.md) (workstream 組織法；已歸檔 _superseded/)

---

## 合併與重組說明 (Restructuring Note)

v1.0 (workstream 組織法 WS-A/B/C) 為**事後回溯型** WBS，追蹤三份 superseded 文檔合併後的當前進度。但該組織法與 VibeCoding 模板 16（七大模組 1.0–7.0 前瞻式結構）格式不符。

本 v2 改以**資深軟體 PM 0→1 規劃視角**，將整個系統架構從零展開，並在狀態欄同時標註「規劃工時 → 實際狀態」雙軌資訊，使：
- **新進成員**可從本文件理解完整系統藍圖與任務切割邏輯
- **PMO / Release 管理**可依模板格式納入跨專案 portfolio 追蹤
- **回溯進度**仍可透過狀態欄與 v1.0 的 workstream 對照表交叉驗證

### ⚠️ Effort Envelope Baseline

本版規劃工時 **1,649h**（原 1,280h + Module 8.0 Auto-TRIZ v2 Integration 193h + Module 9.0 Harness Architecture Refactoring 176h），對應本專案「小型 AI 產品快速原型」的實際人力配置。v2.2 新增 Module 8.0 由 [ADR-008](adrs/ADR-008-auto-triz-v2-integration.md) 觸發。v2.3 新增 Module 9.0 由 [ADR-006](adrs/ADR-006-harness-architecture.md) 觸發，將 backend 重構為 Pydantic AI + MCP + Skills 的 Harness 架構，含 Token 監控、Prompt Skill 化、Context Engineering。

### 🔒 Critical Path (M6 Release v1.0)

`5.3.1 Playwright setup → 5.3.2 Gate 1.1→PG3 E2E smoke → 4.3.4 Mock 清除 → 6.2.3 smoke test → 6.2.4 Rollback playbook → M6`

此鏈路 **零浮時**；任一環節延誤直接衝擊 M6。W17 中若 5.3.1 未完成，觸發 QA 降級方案（見 5.3.2 備註）。

---

## 目錄

1. [專案總覽 (Project Overview)](#1-專案總覽-project-overview)
2. [WBS 結構總覽 (WBS Structure Overview)](#2-wbs-結構總覽-wbs-structure-overview)
3. [詳細任務分解 (Detailed Task Breakdown)](#3-詳細任務分解-detailed-task-breakdown)
4. [專案進度摘要 (Project Progress Summary)](#4-專案進度摘要-project-progress-summary)
5. [風險與議題管理 (Risk & Issue Management)](#5-風險與議題管理-risk--issue-management)
6. [品質指標與里程碑 (Quality Metrics & Milestones)](#6-品質指標與里程碑-quality-metrics--milestones)
7. [專案管控機制](#7-專案管控機制)

---

## 1. 專案總覽 (Project Overview)

### 🎯 專案基本資訊

| 項目 | 內容 |
|------|------|
| **專案名稱** | RD Design Copilot v1.0 (ebike design-copilot-blueprint) |
| **專案經理** | PM / TaskMaster Hub |
| **技術主導** | TL |
| **專案狀態** | 進行中（累計 ~93% 完成） |
| **文件版本** | v2.0（0→1 重組版） |
| **最後更新** | 2026-04-15 |

### ⏱️ 專案時程規劃（原始 0→1 規劃）

| 項目 | 日期/時間 |
|------|----------|
| **總工期** | 16 週 (2025-12-23 → 2026-04-17) |
| **目前進度** | ~93% 完成（實際累計工時 ~1,180h / 規劃 1,280h） |
| **預計交付** | 2026-04-17 (Release v1.0) |

### 👥 專案角色與職責 (RACI)

| 角色 | 負責人 | 主要職責 |
|------|--------|----------|
| **專案經理 (PM)** | TaskMaster Hub | 專案協調、進度追蹤、風險管理、跨 workstream 仲裁 |
| **技術負責人 (TL)** | — | 技術決策、架構守門、code review、ADR 把關 |
| **產品經理 (PO)** | — | SOW/PRD 擁有者、Gate 驗收、E2E 規格對齊 |
| **架構師 (ARCH)** | — | FastAPI 邊界、Supabase schema、8 Gate 狀態機、ADR-001..005 |
| **後端開發 (BE)** | — | 21 routers + 8 AI agents + LLMService |
| **前端開發 (FE)** | — | React 18 + 18 pages + 20 react-query hooks + 3 contexts |
| **資料工程 (Data)** | — | Supabase 29 tables + 11 migrations + RLS policies |
| **質量控制 (QA)** | — | pytest (34 modules) + vitest + Playwright E2E |
| **DevOps** | — | Docker compose + CI/CD + Lovable deployment |
| **Security** | — | Supabase Auth + RLS + JWT middleware 審計 |

### 專案範圍要點

- **核心價值**：AI 驅動的早期概念設計決策平台，整合 SCAMPER/TRIZ 發散 + KT 決策收斂 + 證據驅動 8-Gate 流程
- **量化目標**：架構級 rework 3–5 次/專案 → ≤2；設計審查 3–4h → ≤2h；假設驗證覆蓋 <30% → ≥80%；方案探索 1–2 → ≥3；決策可追溯性 → 100%
- **交付物範圍**：31 個 API 端點（backend 20 routers）、7 AI agents（analyst/evaluator/knowledge/knowledge_wb/scamper_feedback/triz_solver/triz_critic，共用 base.py）、18 個前端頁面（20 react-query hooks、3 contexts）、29 個 DB tables、11 個 migrations、8 個 Gate、6 類 Artifact（Constraint/Contradiction/Breakpoint/ConceptRoute/Evidence/Risk）、6 類 Knowledge Asset

> **Note (ARCH review 2026-04-15)**：原草稿將 router 計為 21、agents 計為 8，已修正為實際倉儲計數 20/7。

---

## 2. WBS 結構總覽 (WBS Structure Overview)

### 📊 WBS 樹狀結構

```
1.0 專案管理與規劃 (Project Management)                       [60h]
├── 1.1 專案啟動與規劃
├── 1.2 需求分析與文檔 (Discover → Define)
└── 1.3 專案監控與報告

2.0 系統架構與設計 (System Architecture)                      [140h]
├── 2.1 技術架構設計 (ADR-001..005)
├── 2.2 資料庫設計 (Supabase 29 tables)
└── 2.3 API 設計規範 (31 endpoints + 8 Gates)

3.0 後端開發 (Backend Development)                            [400h]
├── 3.1 基礎架構建置 [Week 1-3]
├── 3.2 Phase 1 Define 模組 [Week 4-6]
├── 3.3 Phase 2 Diverge 模組 [Week 6-10]
└── 3.4 Phase 3 Converge 模組 + 整合優化 [Week 10-13]

4.0 前端開發 (Frontend Development)                           [380h]
├── 4.1 使用者介面設計與設計系統
├── 4.2 互動功能實作 (18 pages + 20 hooks)
└── 4.3 使用者體驗優化

5.0 測試與品質保證 (Testing & QA)                             [180h]
├── 5.1 單元測試 (pytest + vitest)
├── 5.2 整合測試
├── 5.3 端到端測試 (Playwright)
└── 5.4 效能測試

6.0 部署與上線 (Deployment)                                   [80h]
├── 6.1 部署環境準備 (Docker + Lovable)
├── 6.2 生產部署
└── 6.3 監控與維護

7.0 文檔與培訓 (Documentation)                                [40h]
├── 7.1 技術文檔 (ADRs + API Spec + DB Schema)
├── 7.2 使用者手冊
└── 7.3 維護手冊

8.0 Auto-TRIZ v2 方法論整合 (ADR-008)                         [193h]
├── 8.1 資料庫遷移 (function_models + evidence_claims + sim_matrices)
├── 8.2 AnalystAgent 擴充 (5Why / KT / FA / OZ-OT / EntryGrading)
├── 8.3 TrizSolverAgent 擴充 (SIM Matrix / CCI)
├── 8.4 Evidence Registry Service
├── 8.5 前端 Explore 擴充 (Conditional Stepper: Entry Grading + Level A 5-step / Level B 3-tab)
├── 8.6 前端 Create 擴充 (OZ-OT + SIM + CCI + Evidence — Step 1/4 內嵌)
└── 8.7 文件 Phase 2-3 + BDD + 驗收

9.0 Harness Architecture Refactoring (ADR-006)                 [176h]
├── 9.1 Phase 0: 依賴與骨架 (pydantic-ai + mcp + harness/ stub)
├── 9.2 Phase 1: Tool Registry + MCP Server
├── 9.3 Phase 2a: Model Adapter + Prompt Assembler + Token 監控
├── 9.4 Phase 2b: HarnessAgent Base + TRIZ Solver 試刀
├── 9.5 Phase 2c: 全 Agent 轉換
├── 9.6 Phase 3: Orchestrator + Solver Registry
├── 9.7 Phase 4: Skill Loader + 知識型 Prompt Skill 化
└── 9.8 Phase 5: MCP Client + 清理 + 文件
```

### 📈 工作包統計概覽

| WBS 模組 | 規劃工時 | 已完成 | 進度 | 狀態 |
|---------|--------|--------|------|------|
| 1.0 專案管理 | 60h | 55h | 92% | 🔄 |
| 2.0 系統架構 | 140h | 140h | 100% | ✅ |
| 3.0 後端開發 | 416h | 380h | 91% | ⚡ |
| 4.0 前端開發 | 380h | 360h | 95% | ⚡ |
| 5.0 測試品保 | 160h | 130h | 81% | 🔄 |
| 6.0 部署上線 | 100h | 72h | 72% | 🔄 |
| 7.0 文檔培訓 | 40h | 35h | 88% | 🔄 |
| 8.0 Auto-TRIZ v2 | 193h | 0h | 0% | ⏳ |
| 9.0 Harness 重構 | 176h | 8h | 5% | 🔄 |
| **總計** | **1,665h** | **1,180h** | **~71%** | **🔄** |

**狀態圖示**：✅ 已完成 / ⚡ 接近完成 / 🔄 進行中 / ⏳ 計劃中 / ⬜ 未開始 / ⏸ 暫停（降級 / v1.0.1 後補）

> **Note (v2.3)**：Module 9.0 Harness Architecture Refactoring 新增 176h。Phase 0（依賴+骨架 8h）已完成。9.0 為 backend 架構強化，與 8.0 可部分並行（9.1-9.2 獨立；9.4+ 需等 8.0 agent 變更穩定後再轉換）。

---

## 3. 詳細任務分解 (Detailed Task Breakdown)

> 任務編號規則：`{模組}.{子模組}.{序號}`；ADR 欄位指向 `docs/01-define/adrs/`。
> WS 對照欄位對應 v1.0 workstream (WS-A 對齊 / WS-B E2E / WS-C Mock→Live)。

---

### 1.0 專案管理與規劃 (Project Management)

#### 1.1 專案啟動與規劃

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 1.1.1 | 專案章程制定（Brief + Vision + KPI） | PM / PO | 8 | ✅ | 2025-12-23 | - | - |
| 1.1.2 | WBS 結構設計（本文件） | PM | 16 | ✅ | 2026-04-15 | 1.1.1 | - |
| 1.1.3 | 專案時程規劃（16 週 Roadmap） | PM | 8 | ✅ | 2025-12-25 | 1.1.2 | - |
| 1.1.4 | 風險識別與假設登記 (`E1x--assumption-risk-register.md`) | TL / PO | 12 | ✅ | 2025-12-30 | 1.1.3 | - |

#### 1.2 需求分析與文檔 (Discover → Define)

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 1.2.1 | PRD/SOW 撰寫 (`E2--statement-of-work.md`) | PO | 16 | ✅ | 2026-01-05 | 1.1.1 | - |
| 1.2.2 | 使用者故事與 Persona（RD/PM/QA/Mfg） | PO | 8 | ✅ | 2026-01-07 | 1.2.1 | - |
| 1.2.3 | 驗收標準（8 Gate + MUST criteria） | PM / PO | 8 | ✅ | 2026-01-10 | 1.2.2 | - |
| 1.2.4 | 需求變更控制（ADR 流程） | PM | 4 | ✅ | 2026-01-12 | 1.2.3 | ADR-process |

#### 1.3 專案監控與報告

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 1.3.1 | 週報告制度（每週站立會） | PM | 2 | ✅ | 2026-01-05 | - | - |
| 1.3.2 | 進度追蹤儀表板（WBS 狀態欄） | PM | 4 | ✅ | 2026-01-05 | 1.3.1 | - |
| 1.3.3 | 里程碑審查機制（6 milestones） | PM / PO | 4 | 🔄 | 週期性 | - | - |
| 1.3.4 | 專案結案報告（Release v1.0 retro） | PM | 4 | ⏳ | 2026-04-20 | 全模組完成 | - |

**1.0 小計**：60h / 55h 已完成（92%）

---

### 2.0 系統架構與設計 (System Architecture)

#### 2.1 技術架構設計

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 2.1.1 | 技術選型（FastAPI / React 18 / Supabase / Claude Sonnet-4.6） | ARCH | 12 | ✅ | 2026-01-15 | 1.2.1 | ADR-001 |
| 2.1.2 | 系統架構設計 (`E3--architecture-and-design.md`) | ARCH | 20 | ✅ | 2026-01-20 | 2.1.1 | ADR-001 |
| 2.1.3 | 模組化設計（8 Gate 狀態機 + 6 Artifact 生命週期） | ARCH | 16 | ✅ | 2026-01-22 | 2.1.2 | ADR-002 |
| 2.1.4 | 部署架構（Docker + Lovable + Supabase BaaS） | ARCH / DevOps | 8 | ✅ | 2026-01-25 | 2.1.3 | ADR-004 |
| 2.1.5 | 擴展性規劃（多 LLM provider 抽象） | ARCH | 8 | ✅ | 2026-03-20 | 2.1.4 | ADR-003 |

#### 2.2 資料庫設計 (Supabase)

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 2.2.1 | ER 圖與 29 tables 設計 | Data / ARCH | 16 | ✅ | 2026-01-28 | 2.1.2 | ADR-001 |
| 2.2.2 | 核心 schema migration 000 (full deploy) | Data | 12 | ✅ | 2026-01-30 | 2.2.1 | - |
| 2.2.3 | 增量 migrations 001–010 (10 份) | Data | 20 | ✅ | 2026-04-07 | 2.2.2 | - |
| 2.2.4 | RLS policies（全 29 表覆蓋） | Data / Security | 12 | ✅ | 2026-02-05 | 2.2.3 | ADR-001 |
| 2.2.5 | 備份恢復策略 (Supabase PITR) | Data / DevOps | 4 | ✅ | 2026-02-06 | 2.2.4 | - |

#### 2.3 API 設計規範

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 2.3.1 | 31 RESTful endpoints 規範（對齊 SOW §8） | TL / ARCH | 12 | ✅ | 2026-02-01 | 2.1.2 | - |
| 2.3.2 | Pydantic v2 schema + OpenAPI 自動生成 | BE / TL | 8 | ✅ | 2026-02-03 | 2.3.1 | - |
| 2.3.3 | 錯誤處理標準 (problem+json) | TL | 4 | ✅ | 2026-02-03 | 2.3.2 | - |
| 2.3.4 | API 版本控制 (`/api/v1/*`) | TL | 2 | ✅ | 2026-02-03 | 2.3.3 | - |
| 2.3.5 | 認證授權設計 (Supabase Auth + JWT middleware) | Security | 8 | ✅ | 2026-02-05 | 2.3.4 | ADR-001 |

**2.0 小計**：140h / 140h 已完成（100%） ✅

---

### 3.0 後端開發 (Backend Development)

#### 3.1 基礎架構建置 [Week 1–3]

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR | WS |
|---------|---------|--------|---------|------|----------|------|-----|-----|
| 3.1.1 | FastAPI scaffold + CORS middleware | BE | 8 | ✅ | 2026-02-08 | 2.1.3 | - | WS-A A-1.1 |
| 3.1.2 | Supabase client + settings (env loader) | BE | 6 | ✅ | 2026-02-09 | 3.1.1, 2.2.2 | ADR-001 | WS-A A-1.2 |
| 3.1.3 | JWT auth middleware + RLS pass-through | BE / Security | 12 | ✅ | 2026-02-13 | 3.1.2, 2.3.5, 3.1.4 | ADR-001 | WS-A A-1.4 |
| 3.1.4 | Pydantic models (`models/schemas.py`) — **必須先於 auth middleware 完成 token payload schemas** | BE | 20 | ✅ | 2026-02-11 | 2.3.2 | - | - |
| 3.1.5 | LLMService base (Anthropic + multi-provider) (`agents/base.py`) | BE | 24 | ✅ | 2026-02-18 | 3.1.1 | ADR-003 | WS-A A-1.3 |
| 3.1.6 | Retry decorator (tenacity exponential backoff) | BE | 6 | ✅ | 2026-02-20 | 3.1.5 | ADR-003 | WS-B B-6.8.1 |
| 3.1.7 | Token estimation + 80% warning | BE | 4 | ✅ | 2026-02-20 | 3.1.5 | ADR-003 | WS-B B-6.8.2 |
| 3.1.8 | 集中 prompts (analyst/evaluator/triz_solver/knowledge) | BE | 12 | ✅ | 2026-02-22 | 3.1.5 | ADR-003 | WS-B B-6.8.4 |
| 3.1.9 | Observability (counters/timers/phase tracking) | BE | 8 | ✅ | 2026-02-23 | 3.1.5 | - | - |
| 3.1.10 | 開發環境 + OpenAPI 文檔自動生成 | BE / DevOps | 4 | ✅ | 2026-02-23 | 3.1.4 | - | - |

#### 3.2 Phase 1 Define 模組 [Week 4–6]

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | WS |
|---------|---------|--------|---------|------|----------|------|-----|
| 3.2.1 | Analyst agent (brief/socratic/CLD) | BE | 20 | ✅ | 2026-02-28 | 3.1.5 | - |
| 3.2.2 | `/definitions/*` router (6 endpoints) | BE | 16 | ✅ | 2026-03-01 | 3.2.1 | WS-A A-2.1..6 |
| 3.2.3 | `/questions/*` Socratic router (4 endpoints, 7 categories) | BE | 16 | ✅ | 2026-03-03 | 3.2.1 | WS-A A-2.7..10 |
| 3.2.4 | `/causal-loops/generate` CLD router | BE | 8 | ✅ | 2026-03-04 | 3.2.1 | WS-A A-2.11 |
| 3.2.5 | `/contradictions/{cid}/formalize` router | BE | 8 | ✅ | 2026-03-05 | 3.2.1 | WS-A A-2.12 |
| 3.2.6 | `/assumptions/extract` + `/unknown-factors/discover` | BE | 12 | ✅ | 2026-03-06 | 3.2.1 | WS-A A-2.13, A-3.8 |
| 3.2.7 | `/gates/{gate_id}/check` 8-Gate engine 初版（Gate 1.1, 1.2, PG1 僅 Phase 1 依賴） | BE | 12 | ✅ | 2026-03-08 | 3.2.2..6 | WS-A A-2.14 |
| 3.2.8 | 8-Gate engine Phase 2/3 back-edge（Gate 2.1, 2.2, PG2, 3.2, PG3 接入 TRIZ/SCAMPER/Evidence/Decision） | BE | 8 | ✅ | 2026-04-03 | 3.2.7, 3.3.7, 3.4.4 | WS-A A-2.14 |

#### 3.3 Phase 2 Diverge 模組 [Week 6–10]

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR | WS |
|---------|---------|--------|---------|------|----------|------|-----|-----|
| 3.3.1 | TRIZ solver agent (matrix + principle instantiation) | BE | 24 | ✅ | 2026-03-12 | 3.1.5 | ADR-005 | WS-A A-3.3 |
| 3.3.2 | TRIZ Su-Field 76 standard solutions | BE | 16 | ✅ | 2026-03-15 | 3.3.1 | ADR-005 | WS-A A-3.4, B-6.1.1 |
| 3.3.3 | TRIZ critic (TC→PC drill-down trigger) | BE | 12 | ✅ | 2026-03-18 | 3.3.1 | - | - |
| 3.3.4 | TRIZ layered drill-down (migration 010) | BE / Data | 16 | ✅ | 2026-04-03 | 3.3.3 | - | - |
| 3.3.5 | `/alternatives/anti-anchor` + `/alternatives/validation-passport` | BE | 16 | ✅ | 2026-03-20 | 3.2.1 | - | WS-A A-3.1..2, B-6.5 |
| 3.3.6 | SCAMPER router + scamper_feedback agent | BE | 20 | ✅ | 2026-03-22 | 3.3.1 | - | WS-A A-3.5..7, B-6.7.1 |
| 3.3.7 | `/convergence/scan` 二次矛盾偵測 | BE | 8 | ✅ | 2026-03-24 | 3.2.7 | - | WS-A A-3.9 |
| 3.3.8 | Evaluator agent (risk/convergence/MUST/pre-CAD) | BE | 20 | ✅ | 2026-03-26 | 3.1.5 | - | - |
| 3.3.9 | `/must/evaluate` MUST Go/No-Go | BE | 8 | ✅ | 2026-03-27 | 3.3.8 | - | WS-A A-3.10 |
| 3.3.10 | `/pre-cad-reviews/{rid}/ai-analyze` | BE | 8 | ✅ | 2026-03-28 | 3.3.8 | - | WS-A A-3.11 |
| 3.3.11 | Spatial lookup + validator (learned_components migrations 006-007) | BE / Data | 16 | ✅ | 2026-04-05 | 3.3.10 | - | - |

#### 3.4 Phase 3 Converge 模組 + 整合優化 [Week 10–13]

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | WS |
|---------|---------|--------|---------|------|----------|------|-----|
| 3.4.1 | `/risks/analyze` FMEA | BE | 8 | ✅ | 2026-03-29 | 3.3.8 | WS-A A-4.1 |
| 3.4.2 | `/actions/suggest` knowledge agent | BE | 8 | ✅ | 2026-03-30 | 3.3.8 | WS-A A-4.2 |
| 3.4.3 | `/want/criteria/seed` | BE | 6 | ✅ | 2026-03-30 | 3.3.8 | WS-A A-4.3 |
| 3.4.4 | `/knowledge/writeback` 6-asset pipeline | BE | 16 | ✅ | 2026-04-02 | 3.4.1..3 | WS-A A-4.4, B-6.7.3 |
| 3.4.5 | `/export` Markdown/JSON/PDF | BE | 8 | ✅ | 2026-04-03 | 3.4.4 | WS-A A-4.5, B-6.7.2 |
| 3.4.6 | `/health` + Tavily web search service | BE | 6 | ✅ | 2026-04-03 | 3.1.1 | WS-A A-4.6 |
| 3.4.7 | Socratic prompt injection for contradiction/CLD（**目前 FE 4.2.8 Explore 以 stub prompt 上線；此為補強非阻塞**） | BE | 16 | 🔄 | 2026-W17 | 3.2.3 | WS-B B-6.6.4 |
| 3.4.8 | `projects.phase` state machine trigger (Supabase BEFORE UPDATE) — **需獨立 ADR (待撰)** | Data | 8 | ⏳ | 2026-W18 | 2.2.3 | WS-A A-6.1 **P0** |
| 3.4.9 | `POST /assumptions/{aid}/disprove` 反證工作流 | BE | 8 | ⏳ | Backlog v1.1 | 3.2.6 | WS-A A-6.2 **P1** |
| 3.4.10 | `GET /knowledge/rag/search` RAG pipeline — **需獨立 ADR (待撰：embedding/chunking/retrieval contract)** | BE | 12 | ⏳ | Backlog v1.1 | 3.4.4 | WS-A A-6.3 **P1** |
| 3.4.11 | OpenAPI → TS 型別自動同步腳本（**P1 tech debt，消除前後端手動型別漂移**） | BE / FE | 8 | ⏳ | 2026-W18 | 3.1.10 | - |

**3.0 小計**：416h / 380h 已完成（91%，含新增 3.2.8/3.4.11 兩項） ⚡

---

### 4.0 前端開發 (Frontend Development)

#### 4.1 使用者介面設計與設計系統

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 4.1.1 | UI/UX 規範（Delta design system） | Designer | 12 | ✅ | 2026-02-05 | 1.2.2 |
| 4.1.2 | 響應式設計（Desktop + Tablet 主場景） | Designer / FE | 8 | ✅ | 2026-02-08 | 4.1.1 |
| 4.1.3 | 設計系統建立（shadcn/ui + Tailwind） | FE | 12 | ✅ | 2026-02-10 | 4.1.2 |
| 4.1.4 | 共用組件庫（16 目錄 + 17 Radix primitives） | FE | 24 | ✅ | 2026-02-15 | 4.1.3 |

#### 4.2 互動功能實作 (18 pages + 20 hooks)

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | WS |
|---------|---------|--------|---------|------|----------|------|-----|
| 4.2.1 | React Router 路由 + App scaffold | FE | 6 | ✅ | 2026-02-16 | 4.1.4 | WS-A A-1.5 |
| 4.2.2 | AuthContext + 登入頁 (Auth, ResetPassword) | FE | 12 | ✅ | 2026-02-18 | 4.2.1, 2.3.5 | - |
| 4.2.3 | ProjectDataContext + ArtifactContext | FE | 16 | ✅ | 2026-03-10 | 4.2.1 | WS-B B-1.3, B-3.5 |
| 4.2.4 | TanStack Query 基礎架構 (`hooks/api/*`) | FE | 8 | ✅ | 2026-02-20 | 4.2.1 | WS-C C-0.4 |
| 4.2.5 | QueryBoundary / ErrorFallback 統一元件 | FE | 4 | ✅ | 2026-02-20 | 4.2.4 | WS-C C-0.5 |
| 4.2.6 | Projects API + Dashboard (ProjectDashboard, ProjectList) | FE | 16 | ✅ | 2026-02-25 | 4.2.4 | WS-C C-1.1 |
| 4.2.7 | Brief 頁 (TaskDefinition) + useBrief hook | FE | 20 | ✅ | 2026-02-28 | 3.2.2 | WS-C C-1.2 |
| 4.2.8 | Explore 頁 + Socratic/Contradiction hooks | FE | 24 | ✅ | 2026-03-05 | 3.2.3..5 | WS-C C-1.3 |
| 4.2.9 | Track 頁 + Assumptions/Unknown-factors hooks | FE | 20 | ✅ | 2026-03-10 | 3.2.6 | WS-C C-1.4, C-2.1 |
| 4.2.10 | Create 頁 + TRIZ/SCAMPER/Subsystem hooks | FE | 32 | ✅ | 2026-03-20 | 3.3.* | WS-C C-2.2..3 |
| 4.2.11 | Convergence + SolutionExplorer 頁 | FE | 16 | ✅ | 2026-03-25 | 3.3.7 | WS-C C-2.4..5 |
| 4.2.12 | PreCadReview + CadInProgress 頁 | FE | 16 | ✅ | 2026-03-28 | 3.3.10 | WS-C C-2.6 |
| 4.2.13 | DesignReview 頁 (Evidence/Risks) | FE | 16 | ✅ | 2026-03-30 | 3.4.1 | WS-C C-3.1..2 |
| 4.2.14 | DecisionRecord 頁 (WANT/AC/Signatures/Actions) | FE | 20 | ✅ | 2026-04-03 | 3.4.2..3 | WS-C C-3.3..4 |
| 4.2.15 | Feynman + KnowledgeBase 頁 | FE | 16 | 🔄 | 2026-W17 | 3.4.4 | WS-C C-4.1..3 |
| 4.2.16 | Settings + DevSeed + NotFound | FE | 8 | ✅ | 2026-03-15 | 4.2.1 | - |
| 4.2.17 | ContradictionID + ConstraintLabelDictionary（SOW 外） | FE | 12 | ✅ | 2026-03-25 | 4.2.10 | WS-A A-5.8 |
| 4.2.18 | ArtifactState 統一型別 + Gate 連動 | FE | 16 | ✅ | 2026-03-08 | 4.2.3 | WS-B B-1.1..5 |

#### 4.3 使用者體驗優化

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | WS |
|---------|---------|--------|---------|------|----------|------|-----|
| 4.3.1 | Vite manual chunk splitting（效能） | FE | 4 | ✅ | 2026-04-05 | 4.2.* | - |
| 4.3.2 | 無障礙（Radix a11y primitives 審計） | FE | 8 | ✅ | 2026-04-07 | 4.1.4 | - |
| 4.3.3 | 瀏覽器相容性（Chrome/Edge/Safari） | FE / QA | 8 | ✅ | 2026-04-10 | 4.3.1 | - |
| 4.3.4 | Mock → Live 清除（7 殘留 mock 檔） | FE | 16 | 🔄 | 2026-W17 | 4.2.15 | WS-C C-4.4 |

**4.0 小計**：380h / 360h 已完成（95%） ⚡

---

### 5.0 測試與品質保證 (Testing & QA)

#### 5.1 單元測試

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 5.1.1 | pytest 框架 + conftest mock fixtures | QA | 8 | ✅ | 2026-02-15 | 3.1.1 |
| 5.1.2 | Pydantic schema 測試 | QA | 6 | ✅ | 2026-02-18 | 5.1.1, 3.1.4 |
| 5.1.3 | 21 router 端點測試（34 test modules，~9,000 lines） | QA / BE | 40 | ✅ | 2026-04-07 | 5.1.2, 3.2..4 |
| 5.1.4 | TRIZ + SCAMPER + Gate 業務邏輯測試 | BE | 20 | ✅ | 2026-04-05 | 5.1.3 |
| 5.1.5 | Vitest 前端組件測試（12 tests） | QA / FE | 16 | ✅ | 2026-04-07 | 4.1.4 |

#### 5.2 整合測試

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 5.2.1 | Supabase migration + RLS 整合測試 | QA / Data | 12 | ✅ | 2026-02-10 | 2.2.4 |
| 5.2.2 | 31 API 整合測試（TestClient） | QA | 16 | ✅ | 2026-04-07 | 5.1.3 |
| 5.2.3 | 前後端整合測試（vitest + MSW） | QA / FE | 12 | ✅ | 2026-04-10 | 5.2.2, 4.2.* |

#### 5.3 端到端測試 (Playwright)

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | WS |
|---------|---------|--------|---------|------|----------|------|-----|
| 5.3.1 | Playwright framework setup（**M6 release-blocking**） | QA | 12 | ⏳ | 2026-W17 | 5.2.3 | WS-C C-4.5 |
| 5.3.2 | **降級後**：3 條 critical smoke flows (Brief→Gate1, Explore→Contradiction, Review→Decision) ~12h | QA | 12 | ⏳ | 2026-W17 | 5.3.1 | WS-C C-4.5 |
| 5.3.2-alt | （原計畫）Gate 1.1 → PG3 全流程 E2E — **若 5.3.1 W17 中前未完成，觸發改為手動腳本走查 + automation 延後到 v1.0.1** | QA | 24 | ⏸ | v1.0.1 | 5.3.1 | - |
| 5.3.3 | 跨瀏覽器 + 響應式 E2E — **QA review 建議 descope 至 v1.0.1** | QA | 8 | ⏸ | v1.0.1 | 5.3.2 | - |
| 5.3.4 | FE↔BE contract tests（2 條：useBrief/brief router, useContradictions/contradictions router，補償 E2E 縮減） | QA / BE | 6 | ⏳ | 2026-W17 | 5.2.2 | - |

#### 5.4 效能測試

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 5.4.1 | LLM token 預算 + cost 基準測試 | QA / BE | 8 | ✅ | 2026-04-07 | 3.1.7 |
| 5.4.2 | API 回應時間基準（p95 < 3s for LLM endpoints） | QA | 6 | ✅ | 2026-04-10 | 5.2.2 |
| 5.4.3 | 壓力測試（並發 10 projects × 3 users） | QA | 4 | ⏳ | 2026-W18 | 5.4.2 |

**5.0 小計**：160h / 130h 已完成（81%，已 descope 5.3.2-alt 與 5.3.3 到 v1.0.1） 🔄

---

### 6.0 部署與上線 (Deployment)

#### 6.1 部署環境準備

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 6.1.1 | Docker + docker-compose（backend + nginx） | DevOps | 12 | ✅ | 2026-02-25 | 3.1.10 | ADR-004 |
| 6.1.2 | CI/CD（GitHub Actions：lint → test → build） | DevOps | 16 | ✅ | 2026-03-01 | 6.1.1, 5.1.1 | ADR-004 |
| 6.1.3 | Supabase 環境（dev / staging / prod）配置 | DevOps / Data | 8 | ✅ | 2026-02-28 | 6.1.2 | - |
| 6.1.4 | 安全設定（RLS 審計 + secrets 管理） | Security | 8 | ✅ | 2026-03-05 | 6.1.3 | - |
| 6.1.5 | **Security hardening**：dep audit (npm/pip-audit CI) + JWT/RLS 負面測試 + Socratic prompt-injection test-set | Security / QA | 12 | ⏳ | 2026-W18 | 6.1.4, 3.4.7 | - |

#### 6.2 生產部署

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 6.2.1 | Lovable 前端部署（Vite build） | DevOps / FE | 8 | ✅ | 2026-03-12 | 6.1.4, 5.2.3 |
| 6.2.2 | Backend prod deploy + 域名 + SSL | DevOps | 8 | ✅ | 2026-03-15 | 6.2.1 |
| 6.2.3 | 上線驗證（smoke test） | QA / DevOps | 4 | ⏳ | 2026-W18 | 5.3.2 |
| 6.2.4 | **Rollback playbook + staged canary**（Lovable FE + backend + Supabase migration rollback 程序、RTO ≤ 30min / RPO ≤ 15min） | DevOps | 4 | ⏳ | 2026-W18 | 6.2.3 |

#### 6.3 監控與維護

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 6.3.1 | 日誌監控 (llm_usage_logs + Supabase logs) | DevOps | 8 | ✅ | 2026-04-01 | 3.1.9 |
| 6.3.2 | 效能監控告警（API p95 / LLM failure rate） | DevOps | 4 | ✅ | 2026-04-03 | 6.3.1 |
| 6.3.3 | 備份策略（Supabase PITR + 每週 dump） | DevOps / Data | 4 | ✅ | 2026-04-03 | 2.2.5 |
| 6.3.4 | **LLM cost dashboard** (daily $ alert、token trend) + on-call runbook (incident playbook) | DevOps | 4 | ⏳ | 2026-W18 | 6.3.1 |

**6.0 小計**：100h / 72h 已完成（72%，含新增 6.1.5 / 6.2.4 / 6.3.4 三項 release 強化） 🔄

---

### 7.0 文檔與培訓 (Documentation)

#### 7.1 技術文檔

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 7.1.1 | 架構設計文檔 (`E3--architecture-and-design.md`) | Doc / ARCH | 8 | ✅ | 2026-01-25 | 2.1.2 |
| 7.1.2 | 5 份 ADRs (001–005) | ARCH | 12 | ✅ | 2026-03-13 | 2.1.* |
| 7.1.3 | API 規格（OpenAPI 自動匯出） | BE / Doc | 4 | ✅ | 2026-02-23 | 3.1.10 |
| 7.1.4 | 資料庫 schema + ER 圖文檔 | Data / Doc | 4 | ✅ | 2026-02-05 | 2.2.1 |
| 7.1.5 | 部署指南 (`docs/04-deliver/`) | DevOps / Doc | 4 | ✅ | 2026-03-15 | 6.2.2 |

#### 7.2 使用者手冊

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 7.2.1 | 使用者操作手冊（Brief → Decision 走查） | Doc / PO | 4 | 🔄 | 2026-W17 | 5.3.2 |
| 7.2.2 | FAQ + 疑難排解 | Doc | 2 | ⏳ | 2026-W18 | 7.2.1 |

#### 7.3 維護手冊

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 |
|---------|---------|--------|---------|------|----------|------|
| 7.3.1 | 系統維護手冊（監控 / 備份 / 恢復） | DevOps / Doc | 1 | ✅ | 2026-04-07 | 6.3.3 |
| 7.3.2 | 版本升級指南（migration + LLM prompt 版控） | BE / Doc | 1 | ✅ | 2026-04-07 | 7.1.2 |

**7.0 小計**：40h / 35h 已完成（88%） 🔄

---

### 8.0 Auto-TRIZ v2 方法論整合 (ADR-008)

> **觸發**：[ADR-008](adrs/ADR-008-auto-triz-v2-integration.md) — 將 `docs_harness/auto_triz_strategy.md` 的方法論嚴謹度注入現有自動化架構
> **詳細 WBS**：[WS-I--auto-triz-v2-integration.md](wbs-workstreams/WS-I--auto-triz-v2-integration.md)
> **前置依賴**：WS-D (TRIZ Layered, 88.6%) + Tavily API (existing)

#### 8.1 資料庫遷移

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 8.1.1 | 新增 `function_models` 表 (project_id, component_interactions, sf_diagnosis, subsystem_boundary) | Data | 2 | ⏳ | — | 2.2.3 | ADR-008 |
| 8.1.2 | 新增 `evidence_claims` 表 (claim_id, status, verification_sources) + RLS | Data | 3 | ⏳ | — | 2.2.3 | ADR-008 |
| 8.1.3 | 新增 `sim_matrices` 表 (contradiction_ids, matrix, optimal_combination) | Data | 2 | ⏳ | — | 2.2.3 | ADR-008 |
| 8.1.4 | `contradictions` 表新增 `oz_zone`, `ot_time`, `px_variable` (nullable) | Data | 1 | ⏳ | — | 2.2.3 | ADR-008 |

#### 8.2 AnalystAgent 擴充

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.2.1 | `five_why()` 實作 + prompt + schema | BE | 6 | ⏳ | — | 3.1.5 | P1 |
| 8.2.2 | `kt_is_is_not()` 實作 + prompt + schema | BE | 6 | ⏳ | — | 3.1.5 | P1 |
| 8.2.3 | `function_analysis()` 實作 + prompt + schema | BE | 8 | ⏳ | — | 3.1.5 | **P0** |
| 8.2.4 | `oz_ot_analysis()` 實作 + prompt + schema | BE | 8 | ⏳ | — | 3.1.5 | **P0** |
| 8.2.5 | `entry_grading()` 實作 + prompt + schema | BE | 4 | ⏳ | — | 3.1.5 | P2 |
| 8.2.6 | Router endpoints (5 POST) + integration tests | BE | 6 | ⏳ | — | 8.2.1-5 | P0 |
| 8.2.7 | Pilot tests (TC-Analyst-008 ~ 011) | QA | 4 | ⏳ | — | 8.2.6 | P0 |

#### 8.3 TrizSolverAgent 擴充

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.3.1 | `sim_matrix()` 實作 + prompt + schema | BE | 10 | ⏳ | — | 3.3.1 | P1 |
| 8.3.2 | `complexity_check()` (CCI) 實作 + prompt + schema | BE | 8 | ⏳ | — | 3.3.1 | P1 |
| 8.3.3 | `solve_layered()` 擴充 — 接收 FA + OZ-OT context | BE | 4 | ⏳ | — | 8.2.3, 8.2.4 | **P0** |
| 8.3.4 | Router endpoints (2 POST) + integration tests | BE | 4 | ⏳ | — | 8.3.1-2 | P1 |
| 8.3.5 | Pilot tests (TC-TrizSolve-008 ~ 011) | QA | 4 | ⏳ | — | 8.3.4 | P1 |

#### 8.4 Evidence Registry Service

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.4.1 | `evidence_registry.py` service (register + verify + coverage) | BE | 10 | ⏳ | — | 8.1.2 | **P0** |
| 8.4.2 | Router endpoints (2 POST + 1 GET) | BE | 3 | ⏳ | — | 8.4.1 | P0 |
| 8.4.3 | Integration with existing agents — inject `register_claim` | BE | 6 | ⏳ | — | 8.4.1 | P1 |
| 8.4.4 | Gate check 擴充 — coverage threshold | BE | 3 | ⏳ | — | 8.4.1 | P1 |
| 8.4.5 | Pilot tests (TC-Evidence-001 ~ 005) | QA | 3 | ⏳ | — | 8.4.2 | P0 |

#### 8.5 前端 Explore 擴充（Conditional Stepper）

> **設計變更**：原方案為新增 2 個 Tab（#problem-scoping / #function-analysis），經 UX 分析後改為 **Conditional Stepper**（Entry Grading 驅動 Level A 5-step stepper / Level B 原 3-tab）。詳見 ADR-008 §D6。

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.5.1 | `useEntryGrading` + `useFiveWhy` + `useKtAnalysis` + `useFunctionAnalysis` hooks | FE | 6 | ⏳ | — | 8.2.6 | P2 |
| 8.5.2 | `EntryGradingModal` 元件（Level A/B/C 判定 + 持久化） | FE | 4 | ⏳ | — | 8.5.1, 8.2.5 | P2 |
| 8.5.3 | Explore Conditional Stepper 骨架（Level A stepper / Level B tabs 分支渲染 + Level 切換） | FE | 6 | ⏳ | — | 8.5.2 | P2 |
| 8.5.4 | Level A Step 0: `ProblemScopingStep`（5 Why chain + KT Is/Is Not 矩陣） | FE | 8 | ⏳ | — | 8.5.1, 8.5.3 | P2 |
| 8.5.5 | Level A Step 1: `FunctionAnalysisStep`（組件交互圖 + SF 診斷）+ Level B FA 側面板 | FE | 10 | ⏳ | — | 8.5.1, 8.5.3 | P2 |
| 8.5.6 | Gate 1.2 條件擴充（Level A 額外條件：5Why + FA）+ skip 機制 | FE | 3 | ⏳ | — | 8.5.4, 8.5.5 | P2 |

#### 8.6 前端 Create 擴充（Step 1/4 內嵌）

> **設計原則**：Create 維持 7 steps 不變。OZ-OT/SIM 作為 Step 1 TRIZ 內部的 progressive disclosure；CCI/Evidence 作為 Step 4 Decision Hub 的輕量增強。

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.6.1 | `useOzOtAnalysis` + `useSimMatrix` + `useComplexityCheck` + `useEvidenceCoverage` hooks | FE | 5 | ⏳ | — | 8.2.6, 8.3.4, 8.4.2 | P2 |
| 8.6.2 | `OzOtPanel` accordion section（Step 1 TRIZ 內部，矩陣查表前） | FE | 6 | ⏳ | — | 8.6.1 | P2 |
| 8.6.3 | `SimMatrixView` conditional view（Step 1 TRIZ 內部，≥2 TC 觸發） | FE | 8 | ⏳ | — | 8.6.1 | P2 |
| 8.6.4 | `CciBadge`（Step 4 方案卡右上角，Evolution/Weak Evolution/Patch） | FE | 4 | ⏳ | — | 8.6.1 | P2 |
| 8.6.5 | `EvidenceCoverageGauge`（Step 4 Decision Hub 頂部，覆蓋率 ≥40% 閾值） | FE | 4 | ⏳ | — | 8.6.1 | P2 |

#### 8.7 文件 Phase 2-3 + 驗收

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | 優先級 |
|---------|---------|--------|---------|------|----------|------|--------|
| 8.7.1 | Phase 2 文件更新 (11 份 P1 文件) | Doc | 16 | ⏳ | — | 8.2-8.4 | P1 |
| 8.7.2 | Phase 3 文件更新 (5 份 P2 文件) | Doc | 8 | ⏳ | — | 8.5-8.6 | P2 |
| 8.7.3 | BDD 新增 Feature 4-8 場景 | QA | 4 | ⏳ | — | 8.2-8.4 | P1 |
| 8.7.4 | E2E 手測腳本 (FA → OZ-OT → SIM → CCI 完整路徑) | QA | 4 | ⏳ | — | 8.5-8.6 | P1 |

**8.0 小計**：193h / 0h 已完成（0%） ⏳

**P0 關鍵路徑**：8.1 (8h) → 8.2.3+8.2.4 FA+OZ-OT (16h) → 8.3.3 solve_layered 擴充 (4h) → 8.4 Evidence Registry (25h) → 8.2.6+8.2.7 tests (10h) ≈ **63h**

---

### 9.0 Harness Architecture Refactoring (ADR-006)

> **觸發**：[ADR-006](adrs/ADR-006-harness-architecture.md) — Backend 重構為 Pydantic AI + MCP + Skills 的 Harness 架構
> **設計參考**：Hermes Agent 選擇性器官移植（Tool Registry / Toolset 掃描 / Subagent 隔離）
> **詳細計畫**：[E5x--harness-refactor-plan.md](../02-design/specs/backend-harness/E5x--harness-refactor-plan.md)
> **前置依賴**：Module 3.0 backend 基礎架構穩定

#### 9.1 Phase 0: 依賴與骨架

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.1.1 | `pyproject.toml` 加 `pydantic-ai`, `mcp`; 移除未用 `langgraph`, `langchain-*` | BE | 2 | ✅ | 2026-04-24 | 3.1.1 | ADR-006 |
| 9.1.2 | 建立 `backend/app/harness/` + `HarnessAgentProtocol` stub + 8 空 stub 模組 | BE | 4 | ✅ | 2026-04-24 | 9.1.1 | ADR-006 |
| 9.1.3 | 驗證 pytest 全綠 + import 成功 | QA | 2 | ✅ | 2026-04-24 | 9.1.2 | — |

#### 9.2 Phase 1: Tool Registry + MCP Server

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.2.1 | `harness/tool_registry.py` — `@register_tool` decorator + `ToolDefinition` + JSON Schema 自動產生 | BE | 8 | ⏳ | — | 9.1.2 | ADR-006 |
| 9.2.2 | `harness/mcp_server.py` — stdio MCP server, 列出/呼叫 registered tools | BE | 8 | ⏳ | — | 9.2.1 | ADR-006 |
| 9.2.3 | `tools/triz_kb.py` 標記 `@register_tool`（lookup_matrix, load_40_principles, build_triz_tc_context） | BE | 4 | ⏳ | — | 9.2.1 | ADR-006 |
| 9.2.4 | `tests/harness/test_tool_registry.py` + MCP server E2E 驗證 | QA | 4 | ⏳ | — | 9.2.2, 9.2.3 | — |

#### 9.3 Phase 2a: Model Adapter + Prompt Assembler + Token 監控

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.3.1 | `harness/model_adapter.py` — Pydantic AI `Model` protocol 包裝 `_call_provider` + cache 分離 | BE | 10 | ⏳ | — | 9.2.1, 3.1.5 | ADR-006 |
| 9.3.2 | `harness/prompt_assembler.py` — assemble_prompt(template, skills, context, budget) + token budget 截斷 | BE | 6 | ⏳ | — | 9.3.1 | ADR-006 |
| 9.3.3 | Token 監控骨架 — emit_token_usage(agent_name, input_tokens, output_tokens, cost) | BE | 4 | ⏳ | — | 9.3.1, 3.1.9 | ADR-006 |

#### 9.4 Phase 2b: HarnessAgent Base + TRIZ Solver 試刀

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.4.1 | `harness/agent_base.py` — `HarnessAgent[DepsT, OutputT]` 泛型 class + context 隔離 | BE | 8 | ⏳ | — | 9.3.1 | ADR-006 |
| 9.4.2 | `core/config.py` 加 `USE_HARNESS_AGENTS` feature flag | BE | 1 | ⏳ | — | 9.4.1 | ADR-006 |
| 9.4.3 | `agents/triz_solver.py::_solve_tc()` 雙路徑轉換（harness vs legacy） | BE | 12 | ⏳ | — | 9.4.1, 9.4.2 | ADR-006 |
| 9.4.4 | A/B 比對驗證（同矛盾 harness vs legacy token/latency <5%） | QA | 3 | ⏳ | — | 9.4.3 | — |

#### 9.5 Phase 2c: 全 Agent 轉換

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.5.1 | `knowledge.py` + `knowledge_wb.py` 轉換 (2 fns) | BE | 4 | ⏳ | — | 9.4.3 | ADR-006 |
| 9.5.2 | `triz_critic.py` 轉換 (helper fns) | BE | 4 | ⏳ | — | 9.4.3 | ADR-006 |
| 9.5.3 | `evaluator.py` 轉換 (6 fns) | BE | 8 | ⏳ | — | 9.4.3 | ADR-006 |
| 9.5.4 | `scamper_feedback.py` 轉換 (1 fn) | BE | 4 | ⏳ | — | 9.4.3 | ADR-006 |
| 9.5.5 | `analyst.py` 轉換 (~20 fns) | BE | 16 | ⏳ | — | 9.4.3 | ADR-006 |
| 9.5.6 | 全 agent 轉換後迴歸測試 | QA | 4 | ⏳ | — | 9.5.1-5 | — |

#### 9.6 Phase 3: Orchestrator + Solver Registry

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.6.1 | `harness/solver_registry.py` — `@register_solver` decorator | BE | 4 | ⏳ | — | 9.5.6 | ADR-006 |
| 9.6.2 | `harness/orchestrator.py` — 萃取 L1→critic→L2→L3 管線 + context 隔離 + token 累計 | BE | 10 | ⏳ | — | 9.6.1, 9.4.3 | ADR-006 |
| 9.6.3 | `routers/triz.py` 改走 `solver_registry.dispatch()` | BE | 2 | ⏳ | — | 9.6.2 | ADR-006 |
| 9.6.4 | Orchestrator E2E 驗證（3 RD flag 行為不變） | QA | 4 | ⏳ | — | 9.6.3 | — |

#### 9.7 Phase 4: Skill Loader + 知識型 Prompt Skill 化

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.7.1 | `harness/skill_loader.py` — 掃 `skills/*/SKILL.md`, YAML frontmatter, 註冊 tool + prompt content | BE | 8 | ⏳ | — | 9.2.1 | ADR-006 |
| 9.7.2 | `skills/triz_39_parameters/SKILL.md` + `triz_76_standards/SKILL.md` + `separation_principles/SKILL.md` 知識型 Skill 化 | BE | 6 | ⏳ | — | 9.7.1 | ADR-006 |
| 9.7.3 | `skills/ebike_reference_library/` 範例 Skill（handler + data） | BE | 4 | ⏳ | — | 9.7.1 | ADR-006 |
| 9.7.4 | `main.py` lifespan 加 `skill_loader.load_all()` + hot-reload 驗證 | BE | 2 | ⏳ | — | 9.7.1 | ADR-006 |
| 9.7.5 | Skill loader 測試（放入 test skill → 重啟 → 可見） | QA | 4 | ⏳ | — | 9.7.4 | — |

#### 9.8 Phase 5: MCP Client + 清理 + 文件

| 任務編號 | 任務名稱 | 負責人 | 工時(h) | 狀態 | 完成日期 | 依賴 | ADR |
|---------|---------|--------|---------|------|----------|------|-----|
| 9.8.1 | `harness/mcp_client.py` — 讀 `.mcp.json`, 掛載外部 MCP tools | BE | 6 | ⏳ | — | 9.2.2 | ADR-006 |
| 9.8.2 | 移除 `USE_HARNESS_AGENTS` feature flag（全面切換） | BE | 2 | ⏳ | — | 9.5.6, 9.6.4 | ADR-006 |
| 9.8.3 | Token 監控儀表板規劃（per-agent breakdown + provider cost comparison） | BE / DevOps | 4 | ⏳ | — | 9.3.3 | — |
| 9.8.4 | 文件更新（architecture doc + README + API reference） | Doc | 4 | ⏳ | — | 9.8.1 | — |

**9.0 小計**：176h / 8h 已完成（5%） 🔄

**關鍵路徑**：9.1 (8h) → 9.2 (24h) → 9.3 (20h) → 9.4 (24h) → 9.5 (40h) → 9.6 (20h) → 9.8.2 (2h) ≈ **138h**

**可並行分支**：9.7 (24h) 可與 9.6 並行；9.8.1 (6h) 可與 9.7 並行

---

## 4. 專案進度摘要 (Project Progress Summary)

### 🎯 整體進度統計

| WBS 模組 | 規劃工時 | 已完成 | 進度 | 狀態 |
|---------|--------|--------|------|------|
| 1.0 專案管理 | 60h | 55h | 92% | 🔄 |
| 2.0 系統架構 | 140h | 140h | 100% | ✅ |
| 3.0 後端開發 | 400h | 380h | 95% | ⚡ |
| 4.0 前端開發 | 380h | 360h | 95% | ⚡ |
| 5.0 測試品保 | 180h | 130h | 72% | 🔄 |
| 6.0 部署上線 | 80h | 72h | 90% | ⚡ |
| 7.0 文檔培訓 | 40h | 35h | 88% | 🔄 |
| 8.0 Auto-TRIZ v2 | 193h | 0h | 0% | ⏳ |
| 9.0 Harness 重構 | 176h | 8h | 5% | 🔄 |
| **總計** | **1,649h** | **1,180h** | **~72%** | **🔄** |

### 📅 週度進度分析（16 週 sprint summary）

#### ✅ Week 1–3 (2025-12-23 → 2026-01-12)：Discover + Define
- 完成：SOW、Persona、WBS、風險登記、技術選型、ADR-001 核心決策
- 成就：BaaS-first 架構定案、8 Gate 規格對齊

#### ✅ Week 4–6 (2026-01-13 → 2026-02-02)：Architecture + DB
- 完成：`E3` 架構文檔、29 tables migration 000–004、RLS 覆蓋
- 成就：Supabase schema 穩定

#### ✅ Week 7–9 (2026-02-03 → 2026-02-23)：Infrastructure
- 完成：FastAPI scaffold、LLMService、multi-provider、Auth、前端 scaffold
- 成就：ADR-003 LLM hardening closure（retry + token + prompt）

#### ✅ Week 10–12 (2026-02-24 → 2026-03-15)：Phase 1 + Phase 2 Build
- 完成：31 routes live (SOW 路徑 100% 對齊)、501 stubs 清零、18 pages mock 版
- 成就：2026-03-12 WS-B 主 E2E 差距 42 工作包 100% 完成（M1）

#### ✅ Week 13–15 (2026-03-16 → 2026-04-07)：Phase 3 + Mock→Live
- 完成：Evidence/Risks/Decision hooks、Sprint 3 審查決策 live、migrations 005–010
- 成就：M2 API 對齊 + M3 Sprint 3 live

#### 🔄 Week 16 (2026-04-08 → 2026-04-17)：Release Prep
- 進行：移除 7 mock 殘留、Playwright E2E、Socratic prompt injection、phase state machine trigger、使用者手冊
- 目標：M4 Sprint 4 closure + M5 P0 closure + M6 Release v1.0

#### ⏳ Week 17+ (2026-04-23 →)：Auto-TRIZ v2 Integration (Module 8.0) + Harness Refactoring (Module 9.0)
- 啟動：ADR-008 已建立、Phase 1 文件（10 份）已完成
- 目標：8.0 P0 關鍵路徑 63h — DB migration → FA + OZ-OT agents → solve_layered 擴充 → Evidence Registry
- 里程碑：M7 Auto-TRIZ v2 Phase 1 Backend
- 啟動：ADR-006 Phase 0 已完成（8h）— `pydantic-ai` + `mcp` 依賴、`harness/` 骨架建立
- 目標：9.0 關鍵路徑 138h — Tool Registry → Model Adapter → HarnessAgent → 全 Agent 轉換 → Orchestrator
- 里程碑：M9 Harness Phase 1 (Tool Registry + MCP)、M10 Harness Full Migration

---

## 5. 風險與議題管理 (Risk & Issue Management)

### 🔴 高風險項目

| 風險項目 | 影響度 | 可能性 | 緩解措施 | 負責人 |
|---------|--------|--------|----------|--------|
| Playwright E2E 未啟動，Release 前缺全流程自動驗證 | 高 | 中 | 5.3.1 Week 17 前啟動；W17 中未完成則觸發 5.3.2-alt 手動腳本 fallback | QA |
| M6 Release critical path 零浮時 | 高 | 中 | 明確標記 critical path (§2)；W17 每日站立會追蹤 | PM |
| **無 rollback playbook**（Release 失敗無法快速回退） | 高 | 低 | 6.2.4 W18 前完成 playbook + canary 測試 | DevOps |

### 🟡 中風險項目

| 風險項目 | 影響度 | 可能性 | 緩解措施 | 負責人 |
|---------|--------|--------|----------|--------|
| `projects.phase` state machine trigger 缺失（P0） | 中 | 中 | 3.4.8 Supabase BEFORE UPDATE trigger @ Week 18 + ADR-008 | Data |
| Mock 殘留 7 檔延遲清除影響 E2E | 中 | 中 | 4.3.4 優先處理為 release 障礙項 | FE |
| Socratic 問答 prompt 注入設計未定 | 中 | 中 | 3.4.7 2026-W17 完成設計 spike | BE |
| **LLM vendor lock-in + pricing 波動**（Anthropic API 若配額/價格變動） | 中 | 低 | 2.1.5 multi-provider 抽象已存在；6.3.4 cost dashboard 早期警示 | BE / DevOps |
| **Token cost overrun**（無明確 $ budget 對照） | 中 | 中 | 6.3.4 daily cost alert + 5.4.1 cost 基準；月預算 TBD by PO | DevOps / PO |
| **Key-person bus factor**（單一 owner 角色） | 中 | 中 | 1.1.4 假設登記 + 7.3.1 維護手冊；後續 onboarding pairing | PM |
| **RACI 所有角色 owner 為 "—"**（名字未指派） | 中 | 高 | M4 前補齊實名，加設 backup owner | PM |

### 🟡 中風險項目 — Auto-TRIZ v2 (Module 8.0)

| 風險項目 | 影響度 | 可能性 | 緩解措施 | 負責人 |
|---------|--------|--------|----------|--------|
| FA prompt 品質不足 → 組件交互圖粒度錯誤 | 高 | 中 | 先用 e-bike 案例驗證 prompt，逐步調教 | BE |
| OZ-OT Px 鎖定失敗率高 → L2 深挖降級 | 中 | 中 | 提供 3 種 fallback (broaden_oz, split_tc, reframe) | BE |
| SIM 矩陣 LLM 評分不穩定 | 中 | 低 | temperature=0.2 + 固定 prompt 結構 | BE |
| 流程步驟增加 → RD 覺得繁瑣 | 高 | 中 | 入口分級自動跳步 + progressive disclosure | FE / PO |
| Evidence Registry 增加 API latency | 低 | 低 | register_claim 非同步，不阻塞主流程 | BE |

### 🟡 中風險項目 — Harness Refactoring (Module 9.0)

| 風險項目 | 影響度 | 可能性 | 緩解措施 | 負責人 |
|---------|--------|--------|----------|--------|
| Pydantic AI <1.0 API 不穩定 | 中 | 中 | `model_adapter.py` 為唯一接觸點；pin minor 版本 | BE |
| `mcp` + `anthropic` SDK 版本衝突 | 高 | 低 | Phase 0 已驗證共存；衝突時 subprocess 隔離 MCP server | BE |
| 全 agent 一次轉換風險 | 中 | 中 | `USE_HARNESS_AGENTS` feature flag 並行一週；thin wrapper 保留舊路徑 | BE |
| Context 汙染（層間 raw text 洩漏） | 高 | 低 | HarnessAgent 天然隔離 + Orchestrator 只傳 Pydantic model | BE |
| Module 8.0 agent 變更與 9.5 轉換衝突 | 中 | 中 | 9.4-9.5 排在 8.0 agent 擴充穩定後；或 worktree 隔離開發 | BE |

### 🟢 低風險項目

| 風險項目 | 影響度 | 可能性 | 緩解措施 | 負責人 |
|---------|--------|--------|----------|--------|
| 後端型別漂移（OpenAPI→TS 手動同步） | 低 | 中 | **升級為 P1**：3.4.11 W18 前導入 `openapi-typescript` 生成腳本 | BE |
| `/assumptions/{aid}/disprove` 反證端點缺失（P1） | 低 | 低 | 目前以 status='refuted' 替代；3.4.9 v1.1 補齊 | BE |
| `/knowledge/rag/search` RAG 未實作（P1） | 低 | 低 | 3.4.10 v1.1 版本排入 + ADR-009 | BE |
| Compliance / data privacy（PII in prompts） | 低 | 低 | Socratic prompt 目前無 PII 欄位；後續 review 加入 policy 檢查 | Security |

### 📋 議題追蹤清單

| 議題ID | 議題描述 | 嚴重程度 | 狀態 | 負責人 | 目標日期 |
|--------|----------|----------|------|--------|----------|
| ISS-001 | Sprint 4 殘留 7 mock 檔（Explore/Track/Create/KnowledgeBase 仍 import fallback） | 中 | Open | FE | 2026-W17 |
| ISS-002 | Phase state machine trigger 缺失（P0） | 中 | Open | Data | 2026-W18 |
| ISS-003 | Socratic 問答注入 prompt 設計未定 | 低 | In Progress | BE | 2026-W17 |
| ISS-004 | Playwright E2E 未啟動 | 高 | Open | QA | 2026-W17 |
| ISS-005 | RACI 所有角色名字待指派 | 中 | Open | PM | M4 前 |
| ISS-006 | M6 Rollback playbook 缺失 | 高 | Open | DevOps | 2026-W18 |
| ISS-007 | ADR-008 (phase trigger) / ADR-009 (RAG) 待撰 | 中 | Open | ARCH | M5 前 |

---

## 6. 品質指標與里程碑 (Quality Metrics & Milestones)

### 🎯 關鍵里程碑

| 里程碑 | 預定日期 | 狀態 | 驗收標準 |
|--------|----------|------|----------|
| **M1**: E2E 主差距修正（WS-B 42 工作包） | 2026-03-12 | ✅ | `tsc` 零錯誤 + `build` 通過 + 8 Gate UI/API 實作 |
| **M2**: API 端點對齊 + 501 清零 | 2026-04-07 | ✅ | 31 routes live，SOW 路徑 100% 對齊 |
| **M3**: Sprint 3 審查決策 live | 2026-04-07 | ✅ | Evidence/Risks/Decision 全 hook 化 |
| **M4**: Sprint 4 知識 + Mock 清零 | 2026-W17 | 🔄 | 7 殘留 mock 全清、Playwright 3 smoke flows CI 綠燈、0 P0 issues（簽核：QA Lead + FE Lead） |
| **M5**: P0 closure（phase trigger + Socratic injection） | 2026-W18 | ⏳ | 3.4.7 + 3.4.8 上線 + ADR-006 merged + phase trigger 負面測試通過（簽核：ARCH + Data Lead） |
| **M6**: Release v1.0 | 2026-04-17 | ⏳ | (a) 0 P0 issues；(b) Playwright smoke CI 綠；(c) LLM failure rate <2% 測 50 calls；(d) rollback drill 實際演練；(e) security hardening 6.1.5 完成（簽核：PM + TL + QA Lead + DevOps Lead） |
| **M7**: Auto-TRIZ v2 Phase 1 Backend | 2026-W26 | ⏳ | (a) 8.1 DB migration 完成；(b) 8.2.3+8.2.4 FA+OZ-OT agents 上線；(c) 8.4 Evidence Registry 上線；(d) 8.3.3 solve_layered 接收 FA+OZ-OT context；(e) pilot tests 全通過（簽核：BE Lead + QA Lead） |
| **M8**: Auto-TRIZ v2 Full Stack | 2026-W30 | ⏳ | (a) 8.5+8.6 前端擴充完成；(b) 8.3.1+8.3.2 SIM+CCI 上線；(c) 8.7 文件 Phase 2-3 完成；(d) BDD Feature 4-8 全通過；(e) E2E 手測腳本走查通過（簽核：PM + TL + FE Lead） |
| **M9**: Harness Phase 1 (Tool Registry + MCP) | 2026-W28 | 🔄 | (a) 9.1 Phase 0 完成 ✅；(b) 9.2 Tool Registry + MCP Server 上線；(c) Claude Code 可呼叫 `lookup_matrix`；(d) 9.3 Model Adapter + Token 監控骨架上線（簽核：BE Lead + ARCH） |
| **M10**: Harness Full Migration | 2026-W34 | ⏳ | (a) 全 agent 轉換完成 (9.5)；(b) Orchestrator + Solver Registry 上線 (9.6)；(c) Skill Loader + 知識型 Skill 上線 (9.7)；(d) MCP Client 可消費外部 tools (9.8)；(e) Feature flag 移除；(f) token/latency <5% 回歸（簽核：PM + TL + ARCH） |

### 📈 品質指標監控

#### ✅ 已達成指標
- **TypeScript 型別檢查**：`npx tsc --noEmit` 零錯誤 ✅
- **架構合規性**：8 Gate 全 UI/API 實作 ✅
- **API 一致性**：SOW 路徑 100% 對齊、前後端 schema 一致 ✅
- **501 stub**：0 個 ✅
- **pytest 覆蓋**：34 modules / ~9,000 lines，核心 router 全覆蓋 ✅

#### ⏳ 待達成指標
- **Mock 清除率**：目前 10/17 → 目標 16/17（trizParameters 永久保留）
- **Playwright E2E 覆蓋**：Gate 1.1 → PG3 全流程（0% → 目標 100%）
- **API p95 回應時間**：LLM endpoints < 3s、non-LLM < 500ms
- **LLM failure rate**：< 2%（目前含 retry）
- **使用者滿意度**：目標 ≥ 4/5（Release 後 user study）

### 💡 改善建議

#### 立即行動項目（M4/M5）
1. **Playwright E2E 啟動（5.3.1）**：Release 前最大風險，需 Week 17 前啟動
2. **7 mock 殘留清除（4.3.4）**：優先清 `mockNavCards`/`mockExplore`/`mockTrack`/`mockCreate`/`mockConceptRoutes`/`mockKnowledge`/`mockKnowledgeRefs`
3. **P0 trigger 補齊（3.4.8）**：Data 排入 Week 18 sprint

#### 中長期優化（v1.1+）
1. **RAG 知識檢索（3.4.10）**：補齊 `/knowledge/rag/search` 端點
2. **反證工作流（3.4.9）**：`POST /assumptions/{aid}/disprove` 專屬流
3. **OpenAPI → TS 自動同步**：消除前後端型別手動維護

---

## 7. 專案管控機制

### 📊 進度報告週期
- **日報**：開發團隊內部 Slack 同步
- **週報**：Sprint 站立會 + 本 WBS 狀態欄更新
- **月報**：PO + 高階 stakeholder
- **里程碑報告**：M1..M6 每個關鍵節點深度分析

### 🔄 變更管控流程（ADR 機制）

所有 WBS 範疇 / 技術 / 架構變更須建立或更新 ADR：

1. **變更請求** → 2. **影響評估** → 3. **ARCH/TL/PM 三方審核** → 4. **批准 (ADR 建立) / 拒絕** → 5. **WBS 更新 + 執行追蹤**

**現有 ADR**：

- [ADR-001](adrs/ADR-001-baas-first-architecture.md) — BaaS-First Architecture (Supabase 取代 SQLAlchemy)
- [ADR-002](adrs/ADR-002-server-side-business-logic.md) — Server-Side Business Logic (DB triggers, gate RPC)
- [ADR-003](adrs/ADR-003-llm-service-hardening.md) — LLM Service Hardening (3.1.5–3.1.9 closure)
- [ADR-004](adrs/ADR-004-qa-devops-infrastructure.md) — QA/DevOps Infrastructure
- [ADR-005](adrs/ADR-005-scope-expansion.md) — Scope Expansion (Evidence retrieval + multi-solution MUST)
- [ADR-006](adrs/ADR-006-harness-architecture.md) — Backend Harness 架構 (Pydantic AI + MCP + Skills) — 觸發 Module 9.0
- [ADR-007](adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md) — Explore TC-only；PC/SF 於 Create 派生
- [ADR-008](adrs/ADR-008-auto-triz-v2-integration.md) — ✅ Auto-TRIZ v2 Integration（FA / OZ-OT / SIM / CCI / Evidence Registry）— 觸發 Module 8.0
- **ADR-009**（待撰 @ v1.1）— RAG pipeline（embedding model, chunking strategy, retrieval API）（3.4.10）
- **ADR-010**（待撰）— `projects.phase` state machine trigger contract（3.4.8）
- **ADR-011**（建議）— Effort baselining methodology（精實基線 vs 4-FTE 標準）

### ⚖️ 資源分配原則
- **關鍵路徑優先**：5.3 Playwright E2E > 4.3.4 Mock 清除 > 3.4.7 Socratic injection > 3.4.8 P0 trigger
- **風險緩解優先**：ISS-004 (Playwright) 列為 Week 17 第一優先
- **技能匹配**：QA 集中 E2E、FE 集中 mock 清除、BE 集中 prompt 與 backlog

### 歷史版本

- [`E3x--wbs-development-plan v1.0`](../_superseded/E3x--wbs-development-plan-v1.md) — Workstream 組織法（WS-A/B/C），已歸檔
- Superseded 獨立 WBS 留於 [`docs/_superseded/`](../_superseded/)

---

**專案管理總結**：v1.0 範圍（Module 1.0–7.0）整體 ~92%，核心 API 與前端均已接近完成。v2.2 新增 Module 8.0 Auto-TRIZ v2 Integration（193h），v2.3 新增 Module 9.0 Harness Architecture Refactoring（176h）。兩者均為 v1.0 之後的架構強化，不影響 M6 Release v1.0 交付。

- **8.0 關鍵路徑**（DB → FA+OZ-OT → Evidence Registry）約 63h，目標 M7 (W26) 後端上線、M8 (W30) 全棧完成
- **9.0 關鍵路徑**（Tool Registry → Model Adapter → HarnessAgent → 全 Agent 轉換 → Orchestrator）約 138h，Phase 0 已完成（8h），目標 M9 (W28) Tool Registry + MCP、M10 (W34) 全面遷移

**專案經理**：TaskMaster Hub
**最後更新**：2026-04-24
**下次檢討**：Week 17 Sprint 站立會（v1.0 收尾）→ Week 18+ 轉入 Module 8.0 + 9.0 並行
