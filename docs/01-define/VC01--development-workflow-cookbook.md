# 開發流程總覽手冊 (Development Workflow Cookbook) — RD Design Copilot

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-15`
**主要作者 (Lead Author):** RD Copilot Core Team
**狀態 (Status):** `活躍 (Active)`

> 本文件為 VibeCoding 模板 `01_development_workflow_cookbook.md` 的專案落地版，將「規劃 → 設計 → 開發 → 品質部署」四階段映射到本專案 5D 框架。
> 原始模板：[`rd_assistant_design_system/VibeCoding_Workflow_Templates/01_development_workflow_cookbook.md`](../../rd_assistant_design_system/VibeCoding_Workflow_Templates/01_development_workflow_cookbook.md)
> 配套手冊：[`VC00--workflow-manual.md`](VC00--workflow-manual.md)

---

## 目錄 (Table of Contents)

- [開發流程總覽手冊 (Development Workflow Cookbook)](#開發流程總覽手冊-development-workflow-cookbook)
  - [目錄 (Table of Contents)](#目錄-table-of-contents)
  - [Ⅰ. 核心理念：從商業價值到高品質程式碼](#ⅰ-核心理念從商業價值到高品質程式碼)
  - [Ⅱ. 開發階段與文件產出](#ⅱ-開發階段與文件產出)
    - [**第一階段：規劃 (Planning) - 定義「為何」與「什麼」**](#第一階段規劃-planning---定義為何與什麼)
    - [**第二階段：設計 (Design) - 定義「如何」的藍圖**](#第二階段設計-design---定義如何的藍圖)
    - [**第三階段：開發 (Development) - 精確實現**](#第三階段開發-development---精確實現)
    - [**第四階段：品質與部署 (Quality \& Deployment)**](#第四階段品質與部署-quality--deployment)
  - [Ⅲ. 支援文件](#ⅲ-支援文件)

---

## Ⅰ. 核心理念：從商業價值到高品質程式碼

**目的**：本手冊提供 RD Design Copilot 專案的頂層開發導航，把 BDD/DDD/Clean Architecture/TDD 融入 5D gate 體系。

本專案的「為何 → 什麼 → 如何」對應：
- **為何 (Why)**：解決 RD 在 TRIZ/KT 方法論上的操作障礙——見 [`E1--project-brief-and-prd`](../00-discover/E1--project-brief-and-prd.md) 與 [`E1x--user-journey-map`](../00-discover/E1x--user-journey-map.md)。
- **什麼 (What)**：使用者在 Forward TRIZ / Reverse Anti-Anchor / Pre-CAD 三場景取得可用解——見 [`E3x--system-interaction-flow`](../01-define/E3x--system-interaction-flow.md)。
- **如何 (How)**：以 BaaS-first（ADR-001）+ Server-side logic（ADR-002）+ LLM hardening（ADR-003）+ QA/DevOps（ADR-004）+ Harness Architecture（ADR-006）+ Auto-TRIZ v2（ADR-008）實現——見 [`01-define/adrs/`](../01-define/adrs/)。

**品質內建原則**：Pre-CAD Gate、MUST Rulebook、Evidence Matrix 三層 review，見 [`02-design/specs/review-templates/`](../02-design/_MOC.md)。

**AI 輔助就緒**：_domain-knowledge/ 驅動 AI Agent（[DK-01 流程](../_domain-knowledge/DK-01--design-philosophy-and-process.md)、[DK-02 TRIZ](../_domain-knowledge/DK-02--triz-scamper-divergence-engine.md)、[DK-03 KT 決策](../_domain-knowledge/DK-03--kt-decision-framework.md)、[DK-04 資料模型](../_domain-knowledge/DK-04--data-model-and-gate-reference.md)）。

---

## Ⅱ. 開發階段與文件產出

本專案將 VibeCoding 四階段映射到 5D：Planning = DISCOVER、Design = DEFINE + DESIGN、Development = DEVELOP、Quality & Deployment = DELIVER。

### **第一階段：規劃 (Planning) - 定義「為何」與「什麼」**

**目標**：確保開發方向與 RD 研發方法論與企業用戶需求對齊。對應 5D DISCOVER（TR0–TR1）。

1.  **專案簡報與產品需求 (PRD)** → [`00-discover/E1--project-brief-and-prd.md`](../00-discover/E1--project-brief-and-prd.md) (v3.0, Approved)
    *   **狀態**：TR1 已通過。
    *   **周邊**：[`E1x--stakeholder-brief`](../00-discover/E1x--stakeholder-brief.md)、[`E1x--competitive-landscape`](../00-discover/E1x--competitive-landscape.md)、[`E1x--assumption-risk-register`](../00-discover/E1x--assumption-risk-register.md)、[`E1x--market-sizing`](../00-discover/E1x--market-sizing.md)（Draft）、[`E1x--user-research-synthesis`](../00-discover/E1x--user-research-synthesis.md)（Draft）、[`E1x--privacy-compliance-seed`](../00-discover/E1x--privacy-compliance-seed.md)（Seed）。
    *   **補強項**：market sizing 數據驗證、user research 訪談 — TBD — <owner TBD> by <YYYY-MM-DD TBD>。

2.  **行為驅動情境 (BDD Scenarios)**
    *   **專案落地**：E2E 手測腳本位於 [`02-design/E7x--e2e-manual-scripts/`](../02-design/E7x--e2e-manual-scripts/)。
    *   **Gherkin `.feature` 檔**：TBD — <owner TBD> by <YYYY-MM-DD TBD>（目前以手測腳本與 [`E3x--system-interaction-flow`](../01-define/E3x--system-interaction-flow.md) 3 scenarios 代替）。

### **第二階段：設計 (Design) - 定義「如何」的藍圖**

**目標**：把業務需求轉為可擴展技術藍圖。對應 5D DEFINE（TR2–TR3）+ DESIGN（TR4–TR5）。

3.  **架構與設計文檔 (SAD & SDD)** → 整合於 [`01-define/E3--architecture-and-design.md`](../01-define/E3--architecture-and-design.md) (Approved)
    *   **Appendices A–E**（已合併進 E3）：
        *   A · Forward Subsystem Discovery Architecture
        *   B · Forward TRIZ Solver Architecture
        *   C · Reverse Anti-Anchor Architecture
        *   D · State Machine
        *   E · TRIZ Flow（~~SCAMPER v9 移除~~）
    *   **SoW**：[`01-define/E2--statement-of-work.md`](../01-define/E2--statement-of-work.md) (Approved, TR2 passed)
    *   **架構決策記錄 (ADR)**：[`01-define/adrs/`](../01-define/adrs/)
        *   ADR-001 BaaS-First Architecture
        *   ADR-002 Server-Side Business Logic
        *   ADR-003 LLM Service Hardening
        *   ADR-004 QA/DevOps Infrastructure
        *   ADR-005 Scope Expansion
        *   ADR-006 Harness Architecture — Pydantic AI spine + MCP + Skills（Accepted & Implemented 2026-04-24）
        *   ADR-007 TC-Only Contract — Explore 僅 TC，PC/SF 於 Create 派生
        *   ADR-008 Auto-TRIZ v2 Integration — FA/OZ-OT/SIM/CCI/Evidence Registry（觸發 WS-I + Module 8.0）
    *   **API 設計規格**：收斂於 [`02-design/E5--system-design-overview.md`](../02-design/E5--system-design-overview.md) §2-3 (Active, TR4 passed)
    *   **Schema Codegen Workflow**：[`02-design/E6x--schema-codegen-workflow.md`](../02-design/E6x--schema-codegen-workflow.md)（Pydantic → TS）

4.  **領域 Specs（TR5 進行中 `~`）**
    *   UX：[`02-design/specs/ux/E5x--create-ux-spec`](../02-design/specs/ux/E5x--create-ux-spec.md)（Tab ①–④）
    *   TRIZ：[`specs/triz/E5x--triz-layered-drilldown-optimization`](../02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md)（L1/L2/L3）、[`E5x--triz-multi-solution-adoption-strategy`](../02-design/specs/triz/E5x--triz-multi-solution-adoption-strategy.md)（M1–M6）
    *   Explore：[`specs/explore/E5x--tc-to-multipc-type-alignment`](../02-design/specs/explore/E5x--tc-to-multipc-type-alignment.md)、[`E5x--subsystem-persistence-policy`](../02-design/specs/explore/E5x--subsystem-persistence-policy.md)、[`E5x--three-tier-tree-review-checklist`](../02-design/specs/explore/E5x--three-tier-tree-review-checklist.md)
    *   Review Templates：[`specs/review-templates/E5x--must-rulebook-template`](../02-design/specs/review-templates/E5x--must-rulebook-template.md)、[`E5x--pre-cad-review-template`](../02-design/specs/review-templates/E5x--pre-cad-review-template.md)、[`E5x--evidence-matrix-risk-register-template`](../02-design/specs/review-templates/E5x--evidence-matrix-risk-register-template.md)

    **待補**：E4 ERD（`01-define/diagrams/E4--06_erd`）— Planned — TBD — <owner TBD> by <YYYY-MM-DD TBD>。

### **第三階段：開發 (Development) - 精確實現**

**目標**：透過契約設計與 schema codegen 保證模組精確實現。對應 5D DEVELOP（TR6–TR7，尚未啟動 `.`）。

5.  **模組規格與測試**
    *   **模組 Spec 位置**：[`02-design/specs/triz/`](../02-design/_MOC.md) + [`specs/explore/`](../02-design/_MOC.md)
    *   **WBS 任務分解（契約式開發的入口）**：
        *   主 WBS（release 軸）[`01-define/E3x--wbs-development-plan.md`](../01-define/E3x--wbs-development-plan.md) — WS-A API 對齊 / WS-B E2E 差距 / WS-C Mock→Live（2026-04-15 統整）
        *   Addendum（feature 軸）[`E3x--wbs-development-plan-addendum`](../01-define/E3x--wbs-development-plan-addendum.md) — WS-D..I
            *   [WS-D TRIZ 分層開發](../01-define/wbs-workstreams/WS-D--triz-layered-drilldown-development.md)
            *   [WS-E 子系統介面](../01-define/wbs-workstreams/WS-E--subsystem-interface-development.md)
            *   [WS-F TC→多 PC 分解](../01-define/wbs-workstreams/WS-F--tc-to-multipc-decomposition.md)
            *   [WS-G L3 Su-Field 平行旁路](../01-define/wbs-workstreams/WS-G--l3-sf-parallel-check.md)
            *   [WS-H Playwright E2E 補測](../01-define/wbs-workstreams/WS-H--playwright-e2e-followup.md)
            *   [WS-I Auto-TRIZ v2 Integration](../01-define/wbs-workstreams/WS-I--auto-triz-v2-integration.md)（193h，ADR-008）
    *   **Migrations**：[`03-develop/migrations/`](../03-develop/_MOC.md)（001 MUST criteria、002 KPI current value、003 evidence entries）
    *   **Gate Review 模板**：GR6 Code Complete / GR7 Integration — Template 狀態，待填寫 — TBD — <owner TBD> by <YYYY-MM-DD TBD>

### **第四階段：品質與部署 (Quality & Deployment)**

**目標**：安全、隱私與生產就緒。對應 5D DELIVER（TR8–TR10）。

6.  **安全與上線檢查清單**
    *   **專案對應**：`04-deliver/E8--security-and-readiness-checklists` — **Planned**（尚未建立），種子來源 [`E1x--privacy-compliance-seed`](../00-discover/E1x--privacy-compliance-seed.md)
    *   **Owner / Due**：TBD — <owner TBD> by <YYYY-MM-DD TBD>

7.  **部署與運維**
    *   `04-deliver/E9--deployment-and-operations-guide` — Draft
    *   Runbooks：[`04-deliver/operations/runbook_pc_decomposition`](../04-deliver/operations/runbook_pc_decomposition.md)、[`TRIZ_Layered_Rollout_Runbook`](../04-deliver/operations/TRIZ_Layered_Rollout_Runbook.md)
    *   User Manual：[`04-deliver/E9x--user-manual-v0.1`](../04-deliver/E9x--user-manual-v0.1.md)
    *   GR10 GA Readiness — Template，待填 — TBD — <owner TBD> by <YYYY-MM-DD TBD>

---

## Ⅲ. 支援文件

*   **專案結構指南** → TBD — <owner TBD> by <YYYY-MM-DD TBD>（目前以 [`docs/README.md`](../README.md) 的 5D 導航 + 各階段 `_MOC.md` 作為結構索引）
*   **各階段 MOC**：
    *   [`00-discover/_MOC.md`](../00-discover/_MOC.md)
    *   [`01-define/_MOC.md`](../01-define/_MOC.md)
    *   [`02-design/_MOC.md`](../02-design/_MOC.md)
    *   [`03-develop/_MOC.md`](../03-develop/_MOC.md)
    *   [`04-deliver/_MOC.md`](../04-deliver/_MOC.md)
*   **Domain Knowledge**（驅動 AI Agent）：[`_domain-knowledge/DK-00--index.md`](../_domain-knowledge/DK-00--index.md)
*   **Gap / Meeting / Superseded**：[`_gap-analysis/`](../_gap-analysis/)、[`_meeting-minutes/`](../_meeting-minutes/)、[`_superseded/_MOC.md`](../_superseded/_MOC.md)
*   **配套工作流手冊**：[`VC00--workflow-manual.md`](VC00--workflow-manual.md)

---

**Gate 狀態快照（2026-04-15）**：
```
DISCOVER   DEFINE     DESIGN     DEVELOP    DELIVER
TR0 TR1    TR2 TR3    TR4 TR5    TR6 TR7    TR8 TR9 TR10
 *   *      *   *      *   ~      .   .      ~   ~   .
```
`*` passed | `~` in progress | `.` not started
