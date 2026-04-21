# RD Design Copilot v1.0 — WBS 開發計劃 (0 → 1)

---

**文件版本 (Document Version):** `v2.1` (2026-04-15 PM/ARCH/QA 三方 reviewer 交互評估修訂版)
**最後更新 (Last Updated):** `2026-04-15`
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

本版規劃工時 **1,280h ≈ 2 FTE × 16 週**，對應本專案「小型 AI 產品快速原型」的實際人力配置。若對齊大型團隊敏捷標準（4 FTE），建議外掛 **+30% 緩衝（~1,660h）** 吸收 spike / rework / PM overhead。本文件採「精實基線」記帳，92% 完成代表 **實際交付 vs 精實基線**。ADR-008（effort baselining）待補。

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
| **總計** | **1,296h** | **1,172h** | **~90%** | **🔄** |

**狀態圖示**：✅ 已完成 / ⚡ 接近完成 / 🔄 進行中 / ⏳ 計劃中 / ⬜ 未開始 / ⏸ 暫停（降級 / v1.0.1 後補）

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
| **總計** | **1,280h** | **1,172h** | **~92%** | **🔄** |

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

#### 🔄 Week 16 (2026-04-08 → 2026-04-17)：Release Prep (current)
- 進行：移除 7 mock 殘留、Playwright E2E、Socratic prompt injection、phase state machine trigger、使用者手冊
- 目標：M4 Sprint 4 closure + M5 P0 closure + M6 Release v1.0

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
- [ADR-006](adrs/ADR-006-harness-architecture.md) — Backend Harness 架構 (Pydantic AI + MCP + Skills)
- [ADR-007](adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md) — Explore TC-only；PC/SF 於 Create 派生
- **ADR-008**（待撰）— `projects.phase` state machine trigger contract（3.4.8）
- **ADR-009**（待撰 @ v1.1）— RAG pipeline（embedding model, chunking strategy, retrieval API）（3.4.10）
- **ADR-010**（建議）— Effort baselining methodology（精實基線 vs 4-FTE 標準）

### ⚖️ 資源分配原則
- **關鍵路徑優先**：5.3 Playwright E2E > 4.3.4 Mock 清除 > 3.4.7 Socratic injection > 3.4.8 P0 trigger
- **風險緩解優先**：ISS-004 (Playwright) 列為 Week 17 第一優先
- **技能匹配**：QA 集中 E2E、FE 集中 mock 清除、BE 集中 prompt 與 backlog

### 歷史版本

- [`E3x--wbs-development-plan v1.0`](../_superseded/E3x--wbs-development-plan-v1.md) — Workstream 組織法（WS-A/B/C），已歸檔
- Superseded 獨立 WBS 留於 [`docs/_superseded/`](../_superseded/)

---

**專案管理總結**：專案整體 ~92%，核心 API（2.0 / 3.0）與前端（4.0）均已 ⚡ 接近完成；關鍵收尾集中於 Week 17–18 的 Playwright E2E、Mock 清除、Socratic prompt injection 與 Phase state machine trigger，目標 2026-04-17 Release v1.0。

**專案經理**：TaskMaster Hub
**最後更新**：2026-04-15
**下次檢討**：Week 17 Sprint 站立會
