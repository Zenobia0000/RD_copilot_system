# 前端資訊架構 (IA) — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Pointer`（指向既有規格庫）
**模板來源**：`VibeCoding_Workflow_Templates/17_frontend_information_architecture_template.md`（1254 行）

---

## 為何此檔為 pointer 而非 full fill

VibeCoding 17 號模板涵蓋的 IA 內容已在 `docs/01-define/pages/` 完整定義（含 18 頁 spec、frontmatter SSOT、INDEX 對照表），不重複輸出。

---

## 對應關係表

| 17 號模板 Section | 對應到的既有資料 |
|:------------------|:-----------------|
| 1. Document Purpose & Scope | [`docs/01-define/pages/INDEX.md`](../01-define/pages/INDEX.md) §1 |
| 2. Core Design Principles & First Principles | [`02_prd.md §2`](./02_prd.md) + [`docs/01-define/pages/INDEX.md`](../01-define/pages/INDEX.md) §2 |
| 3. Information Architecture Overview | [`docs/01-define/pages/INDEX.md`](../01-define/pages/INDEX.md) §2-3（Forward + Reverse Mapping） |
| 4. Core User Journeys | [`docs/01-define/pages/INDEX.md`](../01-define/pages/INDEX.md) §6 + 配合各頁 spec [INTERACTION & STATE FLOW] |
| 5. Sitemap & Navigation Structure | [`docs/01-define/pages/INDEX.md`](../01-define/pages/INDEX.md) §3 IA Group 分群視圖 + §5 依賴 DAG |
| 6. Page Detailed Spec | `docs/01-define/pages/01_auth.md` ~ `18_not_found.md`（18 份） |
| 7. Component Linking & Navigation | `docs/01-define/pages/INDEX.md` §5 依賴 DAG + 各頁 [INTERACTION] section |
| 8. Data Flow & State Management | 各頁 [DATA & API] section + [`06_api_spec.md`](./06_api_spec.md) |
| 9. URL Structure & Routing | 每頁 frontmatter `route_path` + [`06_api_spec.md §7`](./06_api_spec.md) |
| 10. Implementation Checklist & AC | 每頁 [ACCEPTANCE CRITERIA] section |
| 11. Appendix（Wireframes etc.） | 部分頁含 [WIREFRAME] section（如 08_create.md, 11/12/13） |

---

## 18 頁總覽（從 docs/01-define/pages/INDEX.md 摘錄）

### IA Group 分群

| Group | 頁數 | 頁面 |
|:------|:-----|:-----|
| `public` | 2 | P01 Auth, P02 ResetPassword |
| `portfolio` | 2 | P03 ProjectList, P04 ProjectDashboard |
| `phase1-define` | 2 | P05 TaskDefinition (Gate D1), P06 Explore (Gate D2) |
| `phase2-diverge` | 3 | P07 Track (X1), P08 Create (X2), P09 PreCadReview (Gate P) |
| `phase3-converge` | 4 | P10 CadInProgress, P11 DesignReview (V1), P12 DecisionRecord (V2), P13 Feynman (V4) |
| `knowledge` | 2 | P14 KnowledgeBase, P15 ConstraintLabelDictionary |
| `system` | 2 | P16 Settings, P18 NotFound |
| `dev` | 1 | P17 DevSeed |

### Phase 流程順序

```
Phase I — Define
   P05 Brief (D1) → P06 Explore (D2) ─┐
                                       │ Phase Gate D
Phase II — Diverge                     ▼
   P07 Track (X1) → P08 Create (X2) → P09 PreCAD (Gate P) ─┐
                                                            │ Phase Gate X
Phase III — Converge                                        ▼
   P10 CadInProgress → P11 Review (V1) → P12 Decide (V2) → P13 Feynman (V4)
```

詳見 [`02_prd.md §3.3`](./02_prd.md) 用戶旅程映射。

---

## 維護指引

- **修改 IA / 頁面 spec**：直接改 `docs/01-define/pages/`，本檔不變。
- **新增頁面**：複製 `docs/01-define/pages/_template.md` → 改檔名 → 填 frontmatter → 更新 `INDEX.md` §2-§3。
- **17 號模板的「Documentation Purpose」、「Acceptance Criteria」**：本檔不重複，每頁自帶。

---

## 文件溯源

- 模板：`VibeCoding_Workflow_Templates/17_frontend_information_architecture_template.md`
- IA SSOT：`docs/01-define/pages/INDEX.md` + 18 頁 spec
- 對應 frontmatter schema：`docs/01-define/pages/_schema.md`
