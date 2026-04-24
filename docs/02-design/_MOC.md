# 02-design — What exactly do we build?

> Gates: TR4-TR5
> Last restructured: 2026-04-15 (VibeCoding 03/06/07/08/09/10/12/17 模板對齊)

## Gate 主檔 (TR4 Gate 核心)

- **[E5--api-design-specification](E5--api-design-specification.md)** — API Design Specification（取代舊 E5；VibeCoding 06）
- [E5x--system-design-overview](E5x--system-design-overview.md) — 系統設計總覽（IA↔API 對應、specs 導航、TR4 gate 條件）

## IA + Frontend

> **文件分工**：`E5--api-design-specification` 為前後端共用契約（endpoints / schemas / errors）。
> 下方兩份為前端內部規格——architecture 管「怎麼蓋」，IA 管「蓋什麼頁面」。

- [E5x--frontend-architecture](E5x--frontend-architecture.md) — 前端架構規格：分層、技術選型、效能、工程實踐 (VibeCoding 12)
- [E5x--frontend-information-architecture](E5x--frontend-information-architecture.md) — 前端資訊架構：路由樹、頁面規格、使用者旅程 (VibeCoding 17)
- [specs/ux/E5x--create-ux-spec](specs/ux/E5x--create-ux-spec.md) — Create 頁完整 UX 規格 (Tab ①–④)

## BDD + 工程規範

- [E5x--bdd-scenarios](E5x--bdd-scenarios.md) — BDD 情境 (Gherkin；VibeCoding 03)
- [E5x--project-structure-guide](E5x--project-structure-guide.md) — 專案結構指南 (VibeCoding 08)
- [E6x--schema-codegen-workflow](E6x--schema-codegen-workflow.md) — Schema Codegen Workflow (Pydantic → TS)
- [E7x--e2e-manual-scripts/](E7x--e2e-manual-scripts/) — E2E 手測腳本

## Specs — 跨領域結構分析

- [specs/E5x--file-dependencies](specs/E5x--file-dependencies.md) — 檔案/模組依賴 + Mermaid 圖 (VibeCoding 09)
- [specs/E5x--class-relationships](specs/E5x--class-relationships.md) — 類別關係 + Pydantic/TS 圖 (VibeCoding 10)

## Specs — 模組規格 (VibeCoding 07)

- [specs/modules/E5x--module-spec-index](specs/modules/E5x--module-spec-index.md) — 模組清單（Agent/Service/Router/Hook）
  - Pilot 1: [`triz-solver`](specs/modules/triz-solver.md) — Forward TRIZ 分層解矛盾
  - Pilot 2: [`anti-anchor`](specs/modules/anti-anchor.md) — 反向路線生成
  - Pilot 3: [`subsystem-decomposer`](specs/modules/subsystem-decomposer.md) — 子系統分解 + 介面契約
  - Pilot 4: [`evaluator`](specs/modules/evaluator.md) — Pre-CAD 六維評分 + Gate 決策
  - Pilot 5: [`knowledge`](specs/modules/knowledge.md) — RAG citation + 多模態 ingest

## Specs — 依領域分組

### TRIZ 解矛盾子系統
- [specs/triz/E5x--triz-layered-drilldown-optimization](specs/triz/E5x--triz-layered-drilldown-optimization.md) — 分層 Drill-Down 架構優化 (L1/L2/L3)
- [specs/triz/E5x--triz-multi-solution-adoption-strategy](specs/triz/E5x--triz-multi-solution-adoption-strategy.md) — 多解併行採納策略 (M1–M6)

### Explore / 子系統
- [specs/explore/E5x--tc-to-multipc-type-alignment](specs/explore/E5x--tc-to-multipc-type-alignment.md) — BE Pydantic ↔ FE TS 型別對照
- [specs/explore/E5x--subsystem-persistence-policy](specs/explore/E5x--subsystem-persistence-policy.md) — Subsystem 持久化策略
- [specs/explore/E5x--three-tier-tree-review-checklist](specs/explore/E5x--three-tier-tree-review-checklist.md) — 三層樹 + 六維契約 Review Checklist

### Review / Gate 模板
- [specs/review-templates/E5x--must-rulebook-template](specs/review-templates/E5x--must-rulebook-template.md) — MUST 可機器執行規則模板
- [specs/review-templates/E5x--pre-cad-review-template](specs/review-templates/E5x--pre-cad-review-template.md) — Pre-CAD Gate 審查模板
- [specs/review-templates/E5x--evidence-matrix-risk-register-template](specs/review-templates/E5x--evidence-matrix-risk-register-template.md) — 證據矩陣 & 風險登記

## Auto-TRIZ v2 (Module 8.0) 相關文件 (v2.0 新增)

- [ADR-008](../01-define/adrs/ADR-008-auto-triz-v2-integration.md) — Auto-TRIZ v2 閉環流程整合（FA / OZ-OT / SIM / CCI / Evidence Registry）
- [pages/06_explore](../01-define/pages/06_explore.md) — Explore 頁 Page-Level Spec（Conditional Stepper）
- [pages/08_create](../01-define/pages/08_create.md) — Create 頁 Page-Level Spec（OZ-OT / SIM / CCI / Evidence）
- [pages/MAPPING](../01-define/pages/MAPPING.md) — Page Spec ↔ IA 雙向對照索引

## 其他位置 (交叉引用)

**WBS 任務分解** 已統一歸檔至 DEFINE 階段：
- [01-define/E3--wbs-development-plan](../01-define/E3--wbs-development-plan.md) — 主 WBS v2.1 (module axis)
- [01-define/wbs-workstreams/](../01-define/wbs-workstreams/README.md) — Feature workstreams (WS-D..H)

## VibeCoding 模板對齊總表

| Template | 對應 02-design 文件 | 狀態 |
|----------|---------------------|------|
| 03 BDD Guide | `E5x--bdd-scenarios.md` | Active |
| 06 API Design | `E5--api-design-specification.md` | Active |
| 07 Module Spec & Tests | `specs/modules/E5x--module-spec-index.md` + 5 pilots | Active |
| 08 Project Structure | `E5x--project-structure-guide.md` | Active |
| 09 File Dependencies | `specs/E5x--file-dependencies.md` | Active |
| 10 Class Relationships | `specs/E5x--class-relationships.md` | Active |
| 12 Frontend Architecture | `E5x--frontend-architecture.md` + `specs/ux/E5x--create-ux-spec.md` | Active |
| 17 Frontend IA | `E5x--frontend-information-architecture.md` | Active |
