# E5x — 前端資訊架構 (Frontend Information Architecture)

---

**文件版本 (Document Version):** `v1.2`
**最後更新 (Last Updated):** `2026-04-27`
**主要作者 (Lead Author):** `UX / Frontend Lead`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `17_frontend_information_architecture_template.md`
**上游:** [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) · [`01-define/E3x--system-interaction-flow.md`](../01-define/E3x--system-interaction-flow.md)

> **說明**：本檔為 IA 骨架；各頁面細節（尤其 Create）在 [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) 已充分覆蓋。

---

## 目錄

- [1. 文檔目的與範圍](#1-文檔目的與範圍)
- [2. 核心設計原則](#2-核心設計原則)
- [3. 資訊架構總覽](#3-資訊架構總覽)
- [4. 核心用戶旅程](#4-核心用戶旅程)
- [5. 網站地圖與導航結構](#5-網站地圖與導航結構)
- [6. 頁面詳細規格](#6-頁面詳細規格)
- [7. 組件連結與導航系統](#7-組件連結與導航系統)
- [8. 數據流與狀態管理](#8-數據流與狀態管理)
- [9. URL 結構與路由規範](#9-url-結構與路由規範)
- [10. 實施檢查清單與驗收標準](#10-實施檢查清單與驗收標準)
- [11. 附錄](#11-附錄)

---

## 1. 文檔目的與範圍

為 **RD Design Copilot** 前端所有頁面定義統一 IA，作為導航 / 組件連結 / 狀態流 / URL 規範的權威參考；對齊 E3x 三大 Scenario 與 Create UX spec 的 Tab 結構。

**包含**：所有路由、導航、跨頁狀態、URL 規範。  
**排除**：Create 頁 Tab ①–④ 細節互動（見 UX spec）。

## 2. 核心設計原則

- **任務導向**：以 RD 核心任務（解矛盾、跨域去錨定、審查 gate）為分區。
- **Progressive disclosure**：複雜流程以 Tab + drill-down 分層揭露。
- **可追溯**：URL 可還原精確狀態（project_id / tab / contradiction_id 等）。
- **最短路徑**：核心兩流程（TRIZ 含跨域去錨定 / Pre-CAD）從 dashboard 最多 2 次點擊抵達。
- **一致性**：所有頁面共用 `layouts/` 與 sidebar/topbar。

## 3. 資訊架構總覽

```
RD Design Copilot
├── 認證 (Auth)
│   ├── /auth (登入/註冊)
│   └── /reset-password
├── 專案入口
│   ├── /projects            (ProjectList)
│   └── /projects/:id        (ProjectDashboard)
├── 5D 階段流程
│   ├── /projects/:id/brief             (Define: Brief + 5W1H)
│   ├── /projects/:id/explore           (Explore: TRIZ L1 跨域去錨定 + L2/L3)
│   ├── /projects/:id/create            (Design: TRIZ + Subsystem + 3 tier tree)
│   │   ├── ?tab=triz        Tab ①
│   │   ├── ?tab=subsystem   Tab ②
│   │   ├── ?tab=decision    Tab ③
│   │   └── ?tab=tree        Tab ④
│   ├── /projects/:id/track             (假設追蹤 / 實驗)
│   ├── /projects/:id/pre-cad           (Review Gate)
│   ├── /projects/:id/cad               (CAD 階段佔位)
│   ├── /projects/:id/review            (設計審查)
│   └── /projects/:id/decide            (KT 決策)
├── 知識庫 / 輔助
│   ├── /knowledge-base
│   ├── /projects/:id/constraint-labels
│   └── /projects/:id/feynman           (learning / explainer)
├── 系統
│   ├── /settings
│   └── /dev/seed                       (dev only)
└── /* (NotFound)
```

## 4. 核心用戶旅程

> 完整 scenario 敘事（序列圖 + 互動對照 + 頁面軌跡）：見 [`E3--system-interaction-flow.md`](../01-define/E3--system-interaction-flow.md) §2-4。
> Sprint 速查：見 [`SPRINT-INDEX.md`](../SPRINT-INDEX.md) §2 By Scenario。

| Journey | E3x | 路由軌跡 |
|:--------|:----|:---------|
| Forward TRIZ | §2 | `/projects` → `/:id` → `/:id/create?tab=triz` |
| TRIZ L1 跨域去錨定具體化 | §3 | `/:id` → `/:id/create?tab=triz` → `/:id/track` |
| Pre-CAD Gate | §4 | `/:id` → `/:id/pre-cad` → `/:id/decide` |

## 5. 網站地圖與導航結構

### 全域導航
- **Topbar**：Logo / Project picker / User menu / Theme toggle。
- **Sidebar**（專案內）：Dashboard / Brief / Explore / Create / Track / Pre-CAD / CAD / Review / Decide / Feynman / Settings。
- **Breadcrumb**：`Projects > [Name] > [Stage]`。

### 底層結構
- 所有 `/projects/:id/*` 受 `ProtectedRoute` + project ownership 檢查保護。
- `/auth`、`/reset-password` 為 public。
- `/dev/seed` dev-only。

## 6. 頁面詳細規格

> 每頁以結構化小表呈現 **URL / Purpose / Key Components / State / Related API**。Key Components 優先列出 `src/pages/*.tsx` 內實際 import 的 feature 組件；若頁面只 import UI primitives 或檔案不存在則標 **TBD**。

### 6.1 Auth

| 欄位 | 內容 |
|---|---|
| **URL** | `/auth`, `/reset-password` |
| **Purpose** | 使用者登入 / 註冊 / 密碼重置（public route） |
| **Key Components** | `Button`, `Input`, `Card`（shadcn UI；無 feature 組件） |
| **State** | Supabase Auth session（`AuthContext`）；表單 state 為 local `useState` |
| **Related API** | Supabase Auth（`supabase.auth.*`） |
| **Source** | `src/pages/Auth.tsx`, `src/pages/ResetPassword.tsx` |

### 6.2 ProjectList

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects` |
| **Purpose** | 所有 project 列表、篩選、新建入口 |
| **Key Components** | `ProjectCard`, `ProjectFilters`, `CreateProjectModal`（`src/components/projects/*`） |
| **State** | `useProjects()` server state + filter local state |
| **Related API** | `/projects/*`（`TBD — CRUD spec 正式化`） |
| **Source** | `src/pages/ProjectList.tsx` |

### 6.3 ProjectDashboard

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id` |
| **Purpose** | 單一專案聚合視圖（階段進度、Gate、KPI、矛盾收斂） |
| **Key Components** | `PhaseProgressBar`, `QuickStatsGrid`, `GateDonut`, `NavCards`, `ProjectTimeline`, `KpiCards`, `MissionSummaryCard`, `PreCadScoreGauge`, `ContradictionConvergenceCard`, `EvidenceEntryDialog` |
| **State** | 多個 `useSupabaseQuery`（project / stats / gates）+ `ProjectDataContext` |
| **Related API** | 聚合多端點：`/projects/:id`, `/stats/*`, `/gates/*` |
| **Source** | `src/pages/ProjectDashboard.tsx`（import 段 L17–L32） |

### 6.4 TaskDefinition

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/brief` |
| **Purpose** | Brief 凍結 + 5W1H + 素材上傳 → Constraints / KPIs / Contradictions 提取 |
| **Key Components** | `ConstraintsTable`, `KpiList`, `AITaskDefinitionCard`, `GateChecklist`, `AISuggestionCard`, `EvidenceRefsInline`, `FileUploadZone`, `AIExtractionResults`, `FeasibilityValidation`, `MultiItemInput` |
| **State** | `useTaskDefinitionForm` (react-hook-form)；`useBrief` server state |
| **Related API** | `/definitions/*`, `/questions/*`, `/knowledge/ingest-source` |
| **Source** | `src/pages/TaskDefinition.tsx` |

### 6.5 Explore

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/explore` |
| **Purpose** | Conditional Stepper：依入口分級（Level A/B/C）切換模式 — Level A 5-step 引導（Problem Scoping → FA → Socratic → Contradictions → CLD）；Level B 原有 3-tab 快速通道；Level C 導向 Create SF-only |
| **Key Components** | `EntryGradingModal` (v2.0 新增), `ConditionalStepper` (v2.0 新增), `ProblemScopingStep` (v2.0 新增), `FunctionAnalysisStep` (v2.0 新增), `SocraticTab`, `ContradictionTab`, `CldTab`, `ExploreGates`, `KnowledgeRefsPanel` |
| **State** | `entryLevel: A\|B\|C\|null`（from DB）；Level A: `currentStep: 0-4`；Level B: Tab 狀態（URL `?tab=`）；`useExplore` server state |
| **Related API** | `/analyst/entry-grading` (v2.0 新增), `/analyst/five-why` (v2.0 新增), `/analyst/kt-analysis` (v2.0 新增), `/analyst/function-analysis` (v2.0 新增), `/unknown-factors/*`, `/causal-loops/*` |
| **Source** | `src/pages/Explore.tsx` |

### 6.6 Create

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/create?tab={triz\|subsystem\|decision\|tree}` |
| **Purpose** | TRIZ 分層解 + Subsystem + Decision Center + 三層樹 |
| **Key Components** | `LayeredSolutionCard`, `MissionContext`, `CreateStepper`, `KnowledgeRefsPanel`, `SubsystemHierarchyView`, `PackageMapPanel`, `SpatialOverlayDialog`, `SpatialOverrideDialog`, `PromoteToLearnedDialog`, `ConvergenceDashboard`, `HumanReviewPanel`, `ArchitectureHaltOverlay`, `MultiSolutionAdoptionPanel`, `ConvergenceGraph`, `OzOtPanel` (v2.0 新增), `CciBadge` (v2.0 新增), `EvidenceCoverageGauge` (v2.0 新增)（其餘見 UX spec） |
| **State** | 提議 `useCreateStore` (Zustand) 管 tab/drill-down；`useLayeredTrizSolve`, `useSubsystemSuggestion` server state；`useOzOtAnalysis`, `useSimMatrix`, `useComplexityCheck`, `useEvidenceCoverage` (v2.0 新增) |
| **Related API** | `/triz/solve-layered`, `/triz/sim-matrix` (v2.0 新增), `/triz/complexity-check` (v2.0 新增), `/analyst/oz-ot-analysis` (v2.0 新增), `/evidence/coverage` (v2.0 新增), `/subsystems/*` *(v9: `/scamper/*` 移除)*, `/contradictions/*` |
| **參考 Spec** | **[create-ux-spec](specs/ux/E5x--create-ux-spec.md)**（完整 Tab ①–④） |
| **Source** | `src/pages/Create.tsx` |

### 6.7 PreCadReview

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/pre-cad` |
| **Purpose** | Pre-CAD Gate 六維評分 + MUST 判定 + 簽核 |
| **Key Components** | `SpatialTraceHover`（實作中）；TBD `MustChecklist`, `QualitativeScoreTable`, `CitationDrawer` — `TBD — <fe-lead TBD> by 2026-05-15 TBD`。目前主要使用 `Accordion`, `RadioGroup`, `Progress`, `Dialog` 組件 |
| **State** | `usePreCadReview` server state；local form state |
| **Related API** | `/pre-cad-reviews/:rid/ai-analyze`, `/pre-cad-reviews/:rid/sign`, `/must/*` |
| **參考 Spec** | [pre-cad template](specs/review-templates/E5x--pre-cad-review-template.md), [`evaluator` module](specs/modules/evaluator.md) |
| **Source** | `src/pages/PreCadReview.tsx` |

### 6.8 DecisionRecord

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/decide` |
| **Purpose** | KT 決策記錄 + Evidence Matrix + Action/Risk 關聯 |
| **Key Components** | `KnowledgeRefsPanel`；TBD `KtDecisionTable`, `EvidenceMatrixTable`, `ActionRiskList` — `TBD — <fe-lead TBD> by 2026-05-15 TBD`。目前使用 `Table`, `Accordion`, `Dialog` |
| **State** | `useDecisionRecord` server state |
| **Related API** | `/actions/*`, `/risks/*`, `/evidence/*` |
| **Source** | `src/pages/DecisionRecord.tsx` |

### 6.9 Track

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/track` |
| **Purpose** | 假設台帳 / 實驗追蹤 / Unknown Factors / Validation Passport |
| **Key Components** | `KanbanBoard`, `UnknownFactors`, `TrackGate`, `KnowledgeRefsPanel` |
| **State** | `useAssumptions`, `useTrack` server state |
| **Related API** | `/assumptions/*`, `/alternatives/validation-passport`, `/unknown-factors/*` |
| **Source** | `src/pages/Track.tsx` |

### 6.10 DesignReview

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/review` |
| **Purpose** | CAD Gate 後的設計審查（黑帽質疑、Evidence 複核） |
| **Key Components** | `KnowledgeRefsPanel`, `AttachmentsPanel`；TBD `BlackHatPanel` — `TBD — <fe-lead TBD> by 2026-06-15 TBD` |
| **State** | `useDesignReview` server state |
| **Related API** | TBD — review router 正式化（by 2026-06） |
| **Source** | `src/pages/DesignReview.tsx` |

### 6.11 CadInProgress

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/cad` |
| **Purpose** | CAD 繪製階段佔位頁（顯示候選 alternatives 進度） |
| **Key Components** | 僅 `Button`, `Card`, `Progress`, `Badge`, `HelpTooltip`（無 feature 組件） |
| **State** | `useAlternatives`, `useUpdateAlternative` |
| **Related API** | `/alternatives/*` |
| **Source** | `src/pages/CadInProgress.tsx` |

### 6.12 KnowledgeBase

| 欄位 | 內容 |
|---|---|
| **URL** | `/knowledge-base` |
| **Purpose** | 跨專案知識庫搜尋 / citation 瀏覽 |
| **Key Components** | 僅 UI primitives (`Button`, `Card`, `Badge`, `Input`, `Skeleton`)；TBD `KbSearchBar`, `CitationList` — `TBD — <fe-lead TBD> by 2026-06 TBD` |
| **State** | `useKnowledge` search state |
| **Related API** | `/knowledge/search`, `/knowledge/*` |
| **參考 Spec** | [`knowledge` module](specs/modules/knowledge.md) |
| **Source** | `src/pages/KnowledgeBase.tsx` |

### 6.13 ConstraintLabelDictionary

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/constraint-labels` |
| **Purpose** | 約束標籤（hard/soft、領域）字典管理 |
| **Key Components** | UI primitives only (`Select`, `Badge`, `Card`, `Skeleton`) |
| **State** | local filter state + `useSupabaseQuery` |
| **Related API** | `/constraint-labels/*` (TBD) |
| **Source** | `src/pages/ConstraintLabelDictionary.tsx` |

### 6.14 Feynman

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/feynman` |
| **Purpose** | 知識沉澱 / 內化教學介面（將決策 explainer 化） |
| **Key Components** | `KnowledgeRefsPanel`, `AiButton`, `HelpTooltip`, `SectionIntro` |
| **State** | local content state |
| **Related API** | TBD — Knowledge writeback 端點 by 2026-06 |
| **Source** | `src/pages/Feynman.tsx` |

### 6.15 Settings

| 欄位 | 內容 |
|---|---|
| **URL** | `/settings` |
| **Purpose** | 個人設定（主題、偏好、帳號） |
| **Key Components** | `ThemeProvider` consumer；`Card`, `Input`, `Label`, `Separator`（無 feature 組件） |
| **State** | `useTheme`（Context） |
| **Related API** | Supabase user profile |
| **Source** | `src/pages/Settings.tsx` |

### 6.16 DevSeed / NotFound

| Page | URL | Purpose | Key Components | State | Related API |
|---|---|---|---|---|---|
| **DevSeed** | `/dev/seed` | Dev-only 資料種入工具 | `Button`, `Card`（+ seed script hooks） | local | `/seed/*` (dev) |
| **NotFound** | `/*` | 404 fallback | 靜態頁 | — | — |

> Wireframe / 完整互動細節：除 Create 已在 [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) 定案外，其餘頁面 `TBD — <fe-lead TBD> by 2026-05-15 TBD`。

## 7. 組件連結與導航系統

- **NavLink.tsx**：所有頁間連結；自動高亮當前路由。
- **Breadcrumb**：衍生自 route meta — `TBD` 是否集中 meta 或每頁宣告。
- **Cross-link 規則**：
  - Contradiction 卡 → 可跳 Create Tab ① 對應 contradiction。
  - TRIZ L1 跨域去錨定路線 → 可跳 Track 頁對應 Validation Passport。
  - Pre-CAD 評分 → 可跳 Decide 頁當前 gate。
- **Command Menu**：`TBD — <fe-lead TBD> by 2026-Q3 TBD`（cmd+k 全局搜尋）。

## 8. 數據流與狀態管理

- **Server state**：`@tanstack/react-query`；per-page hooks in `src/hooks/`。
- **Client UI state**：Zustand store per feature（e.g. `createStore` 管 Tab 切換、drill-down 狀態）— 具體劃分 TBD。
- **Global context**：`AuthContext`, `ThemeContext`（`src/contexts/`）。
- **URL as state**：主要 state（tab、當前 contradiction、filter）寫入 query string，可分享/回復。
- **Form state**：`react-hook-form` + `zod`。

## 9. URL 結構與路由規範

- **Pattern**：`/projects/:projectId/:stage[/:resourceId][?tab=X&...]`
- **stage** ∈ `brief | explore | create | track | pre-cad | cad | review | decide | feynman | constraint-labels`。
- **Query params**：`tab`, `contradictionId`, `subsystemId`, `view`；均需為 URL-safe (kebab / short slug)。
- **404 fallback**：`NotFound.tsx`。

## 10. 實施檢查清單與驗收標準

- [ ] 每個 Route 有對應 page 元件
- [ ] 所有 `/projects/:id/*` 受 auth guard
- [ ] Breadcrumb 可還原層級
- [ ] 關鍵 state 可由 URL 重建（深連結測試）
- [ ] 側欄 active 狀態準確
- [ ] BDD scenarios 覆蓋三大 Journey
- [ ] E7x 手測腳本覆蓋核心 URL

## 11. 附錄

### A. 延伸閱讀
- Create 頁完整 UX → [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)
- 前端架構 → [`E5x--frontend-architecture.md`](E5x--frontend-architecture.md)
- BDD scenarios → [`E5x--bdd-scenarios.md`](E5x--bdd-scenarios.md)
- E3x 三大 scenario → [`../01-define/E3x--system-interaction-flow.md`](../01-define/E3x--system-interaction-flow.md)

### B. TBD 清單
- 各頁面（除 Create）完整 wireframe · command menu · breadcrumb meta · Zustand store 劃分
