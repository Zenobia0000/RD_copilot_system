# 前端架構規格 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Pointer`（指向既有規格庫）
**模板來源**：`templates/vibecoding/12_frontend_architecture_specification.md`（1801 行）

---

## 為何此檔為 pointer 而非 full fill

VibeCoding 12 號模板涵蓋的內容已在 `templates/design-system/specs/` 完整實踐並從 universal_template 提煉重構（v2.0，2026-04-28），不重複輸出避免 SSOT 分裂。

---

## 對應關係表

| 12 號模板 Section | 對應到的既有規格 |
|:------------------|:-----------------|
| Part 1：First Principles（KPIs、四維目標、因果鏈） | [`02_prd.md §2.3`](./02_prd.md) + [`05_architecture.md §1`](./05_architecture.md) |
| Part 2.1：Perception Layer（視覺渲染） | [`templates/design-system/specs/00_foundations_spec.md`](../../templates/design-system/specs/00_foundations_spec.md) |
| Part 2.2：Interaction Layer（事件、手勢） | [`templates/design-system/specs/02_patterns_spec.md`](../../templates/design-system/specs/02_patterns_spec.md) §11 RD Copilot 專用模式 |
| Part 2.3：State Management Layer | [`05_architecture.md §4.1`](./05_architecture.md)（Zustand + React Query + React Hook Form） |
| Part 2.4：Data Communication Layer | [`06_api_spec.md`](./06_api_spec.md) |
| Part 2.5：Infrastructure Layer | [`05_architecture.md §6`](./05_architecture.md) + [`14_deployment_ops.md`](./14_deployment_ops.md) |
| Part 3：Design System | [`templates/design-system/specs/00_foundations_spec.md`](../../templates/design-system/specs/00_foundations_spec.md) + [`01_components_spec.md`](../../templates/design-system/specs/01_components_spec.md) |
| Part 4：Tech Selection | [`05_architecture.md §4`](./05_architecture.md) + [`04_adr/ADR-001_frontend_stack.md`](./04_adr/ADR-001_frontend_stack.md) |
| Part 5：Performance（Core Web Vitals） | [`02_prd.md §4.2 NFR`](./02_prd.md) + [`05_architecture.md §2.3`](./05_architecture.md) |
| Part 6：Usability & A11y | [`templates/design-system/specs/00_foundations_spec.md §2.6`](../../templates/design-system/specs/00_foundations_spec.md) WCAG 2.1 AA |
| Part 7：Engineering Practices | [`08_project_structure.md`](./08_project_structure.md) + [`11_code_review.md`](./11_code_review.md) |
| Part 8：Front-Back Contract | [`06_api_spec.md`](./06_api_spec.md) |
| Part 9：Monitoring & Security | [`05_architecture.md §7`](./05_architecture.md) + [`13_security_checklist.md`](./13_security_checklist.md) |
| Part 10：Development Checklist | [`templates/design-system/specs/99_documentation_spec.md §4 Design QA`](../../templates/design-system/specs/99_documentation_spec.md) |

---

## 設計系統規格庫總覽

| 檔案 | 用途 | 主要內容 |
|:-----|:-----|:---------|
| `00_foundations_spec.md` | 基礎 token | Color/Typography/Spacing/Radius/Shadow/Motion |
| `01_components_spec.md` | 元件庫 | P0/P1/P2 元件 + RD Copilot 16 個業務元件 |
| `02_patterns_spec.md` | 互動模式 | 10 個通用 + §11 RD 專用（Header、Phase Bar、AI 按鈕、Evidence Link 等） |
| `03_templates_spec.md` | 頁模板 | 8 個通用 + §11 RD Copilot 10 頁業務頁映射 |
| `99_documentation_spec.md` | 治理 | Do/Don't、QA、Versioning、Pipeline 整合 |
| `AI_DESIGN_INDUSTRIAL_PLAYBOOK.md` | Meta workflow | Pencil + Figma MCP + Claude Code 工作流 |

---

## 維護指引

- **不在本檔修改前端架構規範**：所有實質內容統一在 `templates/design-system/specs/`。
- **本檔變更時機**：當 `templates/design-system/specs/` 新增/移除主要章節時更新本對應表。
- **新增前端元件 / 模式 / 頁模板**：加入 `templates/design-system/specs/`，本檔自動生效。

---

## 文件溯源

- 模板：`templates/vibecoding/12_frontend_architecture_specification.md`
- 規格 SSOT：`templates/design-system/specs/`
