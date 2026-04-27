# E5x — 專案結構指南 (Project Structure Guide)

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-15`
**主要作者 (Lead Author):** `Tech Lead / Architecture`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `08_project_structure_guide.md`

---

## 目錄

- [1. 指南目的](#1-指南目的)
- [2. 核心設計原則](#2-核心設計原則)
- [3. 頂層目錄結構](#3-頂層目錄結構)
- [4. 目錄詳解](#4-目錄詳解)
- [5. 文件命名約定](#5-文件命名約定)
- [6. 演進原則](#6-演進原則)

---

## 1. 指南目的

為 **RD Design Copilot Blueprint**（monorepo: React 19 SPA + FastAPI backend + 設計知識庫 + 文檔）提供一致可預測的目錄/檔案結構，加速新人上手、減少跨模組混淆。

## 2. 核心設計原則

- **按功能組織 (Organize by Feature)**：`src/components/{create,explore,review,...}` 以頁面功能切分，而非 `controllers/views/models` 按類型切分。
- **明確職責**：`backend/` 純 API；`src/` 純前端；`docs/` 純文檔；`rd_assistant_design_system/` 純知識庫 / 模板。
- **一致命名**：TS = `PascalCase.tsx` / `camelCase.ts`；Python = `snake_case.py`；Markdown = `kebab-case.md`；docs 編號前綴 `E{n}[x]--`。
- **配置外部化**：後端用 `pyproject.toml` + env；前端用 `vite.config` + `.env`。
- **根目錄簡潔**：根目錄僅放 monorepo 級檔案（README, package.json, pnpm-lock, `.gitignore`）。

## 3. 頂層目錄結構

```plaintext
design-copilot-blueprint/
├── .github/                          # CI/CD workflows
├── backend/                          # FastAPI backend
│   ├── app/
│   ├── tests/
│   ├── docs/
│   ├── Dockerfile
│   └── pyproject.toml
├── src/                              # React 19 frontend
│   ├── pages/                        # Route-level pages
│   ├── components/                   # Feature + UI 組件
│   ├── hooks/
│   ├── types/                        # 含 generated/ (from pydantic2ts)
│   ├── integrations/
│   ├── lib/, utils/, contexts/, config/
│   └── main.tsx, App.tsx
├── docs/                             # 5D 框架文檔
│   ├── 00-discover/
│   ├── 01-define/ (+ adrs/)
│   ├── 02-design/ (+ specs/)
│   ├── 03-develop/  (TBD)
│   └── 04-deliver/  (TBD)
├── rd_assistant_design_system/       # 知識庫 / 模板 / TRIZ KB
│   ├── VibeCoding_Workflow_Templates/
│   └── triz_knowledge_base/
├── public/
├── package.json / pnpm-lock.yaml
├── vite.config.ts / tsconfig*.json
├── tailwind.config.ts / postcss.config.js
└── README.md
```

## 4. 目錄詳解

### 4.1 `backend/app/` — FastAPI 原始碼（Clean-ish Architecture）

```plaintext
backend/app/
├── main.py                   # FastAPI 入口 + router wiring
├── core/                     # 設定、auth、supabase client、gate registry
│   ├── config.py
│   ├── supabase.py
│   ├── logging.py
│   ├── gate_registry.py / gate_checks.py
│   └── evaluator_registry.py
├── middleware/               # auth, error_handler, request_id
├── models/
│   └── schemas.py            # ★ 單一事實來源（所有 Pydantic）
├── routers/                  # API endpoints（依資源切分）
│   ├── brief.py, socratic.py, cld.py
│   ├── contradictions.py, triz.py, subsystems.py  # v9: scamper.py → subsystems.py
│   ├── anti_anchor.py, validation.py
│   ├── convergence.py, unknown_factors.py
│   ├── assumptions.py, risk.py, action.py
│   ├── want.py, must.py, pre_cad.py, gates.py
│   ├── spatial.py, exports.py, knowledge_wb.py
├── agents/                   # AI agents（多 agent 編排）
│   ├── base.py, analyst.py, evaluator.py
│   ├── triz_solver.py, triz_critic.py
│   ├── knowledge.py, knowledge_wb.py  # v9: scamper_feedback.py removed
├── tools/                    # TRIZ KB、contradiction tree、separation principles
├── services/                 # evidence_retrieval, web_search, spatial_*, package_svg, reference_library
├── prompts/                  # LLM prompt templates
└── observability/            # metrics
```

### 4.2 `src/` — React 19 前端

```plaintext
src/
├── pages/                    # 每條 route 一個 .tsx
│   ├── Create.tsx, Explore.tsx, PreCadReview.tsx, DecisionRecord.tsx
│   ├── TaskDefinition.tsx, Track.tsx, DesignReview.tsx
│   ├── ProjectList.tsx, ProjectDashboard.tsx, KnowledgeBase.tsx
│   ├── Auth.tsx, ResetPassword.tsx, Settings.tsx
│   └── NotFound.tsx, Feynman.tsx, CadInProgress.tsx, DevSeed.tsx
├── components/
│   ├── ui/                  # shadcn/ui 原子組件
│   ├── layouts/
│   ├── create/              # Create 頁 Tab ①–④
│   ├── explore/             # Explore 頁 L2/L3 + Anti-Anchor
│   ├── review/, precad/, solution/, assumption/, contradiction/, evidence/, track/
│   ├── dashboard/, projects/, auth/, brief/, task-definition/
│   ├── NavLink.tsx, ErrorBoundary.tsx, ThemeProvider.tsx
├── hooks/                    # useLayeredTrizSolve, useSubsystemSuggestion, ...
├── types/                    # 手寫 + generated/（pydantic2ts 產物）
├── integrations/             # API fetch wrapper + adapter (snake ↔ camel)
├── contexts/, config/, data/, lib/, utils/
├── test/                     # Vitest + Testing Library
└── main.tsx, App.tsx, App.css, index.css
```

### 4.3 `docs/` — 5D Framework 文檔

```plaintext
docs/
├── 00-discover/              # E0/E1/E2 痛點、需求、PRD
├── 01-define/                # E3 架構 + ADR + WBS
│   └── adrs/ADR-001..ADR-005
├── 02-design/                # 本階段（TR4–TR5）
│   ├── E5--api-design-specification.md
│   ├── E5x--system-design-overview.md
│   ├── E5x--bdd-scenarios.md
│   ├── E5x--frontend-architecture.md
│   ├── E5x--frontend-information-architecture.md
│   ├── E5x--project-structure-guide.md (本檔)
│   ├── E6x--schema-codegen-workflow.md
│   ├── E7x--e2e-manual-scripts/
│   └── specs/
│       ├── ux/, triz/, explore/, review-templates/
│       ├── modules/         # 模組規格 index + pilots
│       ├── E5x--file-dependencies.md
│       └── E5x--class-relationships.md
├── 03-develop/               # TBD (TR5–TR7)
└── 04-deliver/               # TBD (TR8+)
```

### 4.4 `rd_assistant_design_system/` — 知識庫

- `VibeCoding_Workflow_Templates/` — 00–17 模板（本 E5x 系列即對齊此）
- `triz_knowledge_base/` — 矛盾矩陣、40 原理、76 標準解

### 4.5 `tests/`（前後端各自獨立）

- Backend: `backend/tests/` — pytest, 與 `app/` 結構對稱
- Frontend: `src/test/` + 各元件旁 `.test.tsx` — Vitest + Testing Library
- E2E: `TBD — <qa TBD> by 2026-05-15 TBD`（Playwright, WS-H）

## 5. 文件命名約定

| 類型 | 規則 | 範例 |
|---|---|---|
| Python 模組 | `snake_case.py` | `triz_solver.py` |
| Python 測試 | `test_*.py` | `test_triz_solver.py` |
| React 元件 | `PascalCase.tsx` | `LayeredTrizPanel.tsx` |
| React hook | `useCamelCase.ts` | `useLayeredTrizSolve.ts` |
| Markdown | `kebab-case.md` | `pre-cad-review-template.md` |
| docs 前綴 | `E{n}[x]--<slug>.md`；`x` = 衛星文 | `E5x--bdd-scenarios.md` |
| ADR | `ADR-{NNN}-<slug>.md` | `ADR-003-schema-codegen.md` |

## 6. 演進原則

- 任何頂層目錄新增/重組 → 必須新 ADR（於 `docs/01-define/adrs/`）並更新本檔 §3。
- `backend/app/agents/` 新 agent → 同步在 [`specs/modules/E5x--module-spec-index.md`](specs/modules/E5x--module-spec-index.md) 追加一列。
- `src/pages/` 新頁面 → 同步更新 [`E5x--frontend-information-architecture.md`](E5x--frontend-information-architecture.md) 網站地圖。
- 結構一致性 > 完美；優先保持可預測，其次才是最佳實踐細節。
