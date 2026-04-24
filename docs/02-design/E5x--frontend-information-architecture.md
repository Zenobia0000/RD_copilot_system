# E5x — 前端資訊架構 (Frontend Information Architecture)

---

**文件版本 (Document Version):** `v1.1`
**最後更新 (Last Updated):** `2026-04-23`
**主要作者 (Lead Author):** `UX / Frontend Lead`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `17_frontend_information_architecture_template.md`
**上游:** [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) · [`01-define/E3x--system-interaction-flow.md`](../01-define/E3--system-interaction-flow.md)

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

> 跨頁面通用原則（user-centric、progressive disclosure、observable state 等）見 [`E5x--frontend-architecture.md` §1](E5x--frontend-architecture.md#第一部分前端架構的第一性原理)。以下為 IA 層獨有原則：

- **可追溯**：URL 可還原精確狀態（project_id / tab / contradiction_id 等）。
- **最短路徑**：核心三流程（TRIZ / Anti-Anchor / Pre-CAD）從 dashboard 最多 2 次點擊抵達。

## 3. 資訊架構總覽

```
RD Design Copilot
├── 認證 (Auth) — public routes
│   ├── /auth                         (登入/註冊)
│   └── /reset-password               (密碼重置)
├── / → redirect → /projects
├── 受保護路由 (ProtectedRoute + AppLayout)
│   ├── 專案入口
│   │   ├── /projects                 (ProjectList)
│   │   └── /projects/:id            (ProjectDashboard)
│   ├── Phase 1 — Define
│   │   ├── /projects/:id/brief       (TaskDefinition: Brief + 5W1H + AI 提取)
│   │   └── /projects/:id/explore     (Explore: Conditional Stepper — Entry Grading Modal 驅動)
│   │   │                              Level A: 5-step stepper (Problem Scoping → FA → Socratic → Contradictions → CLD)
│   │   │                              Level B: 3-tab (#socratic / #contradictions / #cld) + FA 可選側面板
│   │   │                              Level C: SF-only 提示導向 Create
│   ├── Phase 2 — Diverge
│   │   ├── /projects/:id/track       (Track: 假設追蹤 Kanban + Unknown Factors)
│   │   ├── /projects/:id/create      (Create: 7-step accordion stepper)
│   │   │   ├── Step 0: 反向探索 Anti-Anchor    (zone: reverse)
│   │   │   ├── Step 1: TRIZ 解矛盾             (zone: forward)
│   │   │   │   ├── OZ-OT 前置 accordion section（鎖定 Px，矩陣查表前）
│   │   │   │   └── SIM Matrix conditional view（≥2 TC 自動觸發）
│   │   │   ├── Step 2: 子系統定義              (zone: forward)
│   │   │   ├── Step 3: SCAMPER 變形            (zone: forward)
│   │   │   ├── Step 4: 候選方案決策中心         (zone: hub)
│   │   │   │   ├── CCI Badge（Evolution / Weak Evolution / Patch）
│   │   │   │   └── Evidence Coverage Gauge（cross-cutting 指標）
│   │   │   ├── Step 5: MUST 快篩               (zone: eval)
│   │   │   └── Step 6: Pre-CAD 審查            (zone: eval)
│   │   └── /projects/:id/pre-cad     (PreCadReview: 六維評分 + 簽核)
│   ├── Phase 3 — Converge
│   │   ├── /projects/:id/cad         (CadInProgress: CAD 階段佔位)
│   │   ├── /projects/:id/review      (DesignReview: 風險登記 + 證據矩陣)
│   │   ├── /projects/:id/decide      (DecisionRecord: KT 決策 + 簽名)
│   │   └── /projects/:id/feynman     (Feynman: 知識內化 / 教學)
│   ├── 專案輔助
│   │   └── /projects/:id/constraint-labels  (ConstraintLabelDictionary)
│   ├── 知識庫
│   │   ├── /knowledge-base           (KnowledgeBase: 搜尋)
│   │   └── /knowledge-base/:slug     (KnowledgeBase: 文章詳情)
│   ├── 系統
│   │   └── /settings                 (Settings: 主題 / 帳號)
│   └── 開發
│       └── /dev/seed                 (DevSeed: dev-only 資料種入)
└── /* (NotFound: 404 fallback)
```

## 4. 核心用戶旅程

### Journey 1: Forward TRIZ 解矛盾（對應 E3x §2）
1. `/projects` → 選 project → `/projects/:id`
2. Dashboard → 點 "Create" → `/projects/:id/create`（進入 7-step accordion）
3. Step 1 (TRIZ)：選 contradiction → "Solve Layered" → L1 卡顯示
4. 若需 → 手動或自動 drill-down → L2/L3
5. Step 4 (決策中心)：攤平所有方案，橫向比較採納策略

### Journey 2: Reverse Anti-Anchor（對應 E3x §3）
1. `/projects/:id` → "Create" → `/projects/:id/create`
2. Step 0 (Anti-Anchor)：選 anchor solution → AI 產出 3 條非典型路線
3. 點 "Validation Passport" → Track 頁追蹤假設
4. `/projects/:id/track`

### Journey 3: Pre-CAD Gate（對應 E3x §4）
1. Dashboard → "Pre-CAD" → `/projects/:id/pre-cad`
2. "AI Analyze" → 六維評分 + citations
3. "Sign & Pass Gate" → `/projects/:id/decide`

## 5. 網站地圖與導航結構

### 全域導航（`src/config/navigationSteps.ts`）

**Global Nav**：
| Label | Path | Icon |
|---|---|---|
| 專案列表 | `/projects` | `FolderKanban` |
| 知識庫 | `/knowledge-base` | `BookOpen` |
| 設定 | `/settings` | `Settings` |

**Project Sidebar Steps**（按 phase 分組）：
| Phase | Step | Label | zhLabel | Route |
|---|---|---|---|---|
| 1 (Define) | brief | Brief | 定義簡報 | `/projects/:id/brief` |
| 1 (Define) | explore | Explore | 問題探索 | `/projects/:id/explore` |
| 2 (Diverge) | track | Track | 假設追蹤 | `/projects/:id/track` |
| 2 (Diverge) | create | Create | 方案創造 | `/projects/:id/create` |
| 2 (Diverge) | pre-cad | Pre-CAD | Pre-CAD 審查 | `/projects/:id/pre-cad` |
| 3 (Converge) | review | Review | 設計審查 | `/projects/:id/review` |
| 3 (Converge) | decide | Decide | 最終決策 | `/projects/:id/decide` |
| 3 (Converge) | feynman | Feynman | 內化傳達 | `/projects/:id/feynman` |

Step 狀態由 `getStepStatus()` 根據 `pathname` + `PhaseProgress` 判斷：`"active"` / `"completed"` / `"not_started"`。

### 底層結構
- 所有 `/projects/*` 路由受 `ProtectedRoute` + `AppLayout` 包裹。
- `/auth`、`/reset-password` 為 public（不包在 AppLayout 內）。
- `/dev/seed` 僅 `import.meta.env.DEV` 時註冊。

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
| **Purpose** | Conditional Stepper：依 Entry Grading 結果切換 Level A（5-step 引導流）或 Level B（3-tab 快速通道），完成問題探索與矛盾識別 |
| **Entry Grading** | 首次進入觸發 Modal，判定 Level A（症狀級）/ B（已知 TC）/ C（功能缺失→SF-only），結果存入 `projects.entry_level` |
| **Level A 模式** | 5-step stepper：① Problem Scoping（5Why + KT）→ ② Function Analysis（FA 組件交互圖）→ ③ Socratic Q&A → ④ Contradictions → ⑤ CLD |
| **Level B 模式** | 原 3-tab 佈局（#socratic / #contradictions / #cld）+ FA 可選側面板 |
| **Level C 模式** | 提示訊息導向 Create SF-only 通道 |
| **Key Components** | `EntryGradingModal`（新增）, `ProblemScopingStep`（新增）, `FunctionAnalysisStep`（新增）, `SocraticTab`, `ContradictionTab`, `CldTab`, `ExploreGates`, `KnowledgeRefsPanel`, `HelpTooltip` |
| **State** | `entry_level: 'A' \| 'B' \| 'C'`（from DB）；Level A: `currentStep` (0-4)；Level B: Tab 狀態（URL hash）；`useSocraticQuestions`, `useExploreContradictions`, `useCldNodes`, `useCldEdges`, `useEntryGrading`, `useFiveWhy`, `useKtAnalysis`, `useFunctionAnalysis` server state；`useAiOperationGuard` AI 操作鎖 |
| **Related API** | `/analyst/entry-grading`, `/analyst/five-why`, `/analyst/kt-analysis`, `/analyst/function-analysis`, `/alternatives/anti-anchor`, `/unknown-factors/*`, `/causal-loops/*` |
| **Source** | `src/pages/Explore.tsx` |

### 6.6 Create

| 欄位 | 內容 |
|---|---|
| **URL** | `/projects/:id/create` |
| **Purpose** | 7-step accordion stepper：反向探索 + TRIZ 分層解（含 OZ-OT/SIM）+ 子系統 + SCAMPER + 決策中心（含 CCI/Evidence）+ MUST 快篩 + Pre-CAD 審查 |
| **Step 結構** | Step 0: Anti-Anchor (reverse) · Step 1: TRIZ 解矛盾 (forward) — 內含 OZ-OT 前置 accordion + SIM Matrix conditional view · Step 2: 子系統定義 (forward) · Step 3: SCAMPER 變形 (forward) · Step 4: 候選方案決策中心 (hub) — 內含 CCI Badge + Evidence Coverage Gauge · Step 5: MUST 快篩 (eval) · Step 6: Pre-CAD 審查 (eval) |
| **Key Components** | `MissionContext`, `CreateStepper`, `LayeredSolutionCard`, `DirectionResultCard`, `ConsolidationPanel`, `OzOtPanel`（新增）, `SimMatrixView`（新增）, `CciBadge`（新增）, `EvidenceCoverageGauge`（新增）, `KnowledgeRefsPanel`, `SubsystemHierarchyView`, `PackageMapPanel`, `SpatialOverlayDialog`, `SpatialOverrideDialog`, `PromoteToLearnedDialog`, `ConvergenceDashboard`, `HumanReviewPanel`, `ArchitectureHaltOverlay`, `MultiSolutionAdoptionPanel`, `ConvergenceGraph` |
| **State** | `useState`：`currentStep` (0–6)、`activeTrack` (reverse/forward)；server state：`useAntiAnchorRoutes`, `useTrizSolutions`, `useLayeredTrizSolutions`, `useDirectedTrizSolutions`, `useOzOtAnalysis`（新增）, `useSimMatrix`（新增）, `useComplexityCheck`（新增）, `useEvidenceRegistry`（新增）, `useSubsystems`, `useScamperVariants`, `useAlternatives`, `useConceptRoutes`, `useConvergenceLoop`；`useContradictions`, `useBrief`, `useConstraints`, `useKpis`, `useTrackAssumptions` |
| **Related API** | `antiAnchorGenerate`, `trizSolveLayered`, `trizSolveDirected`, `trizConsolidate`, `/analyst/oz-ot-analysis`（新增）, `/triz/sim-matrix`（新增）, `/triz/complexity-check`（新增）, `/evidence/register-claim`（新增）, `/evidence/coverage`（新增）, `scamperTransform`, `riskAnalyze`, `mustEvaluate`, `validationPassportGenerate`, `scamperSpatialOverlay`, `spatialComponentOverride`, `spatialLearnedComponent` |
| **參考 Spec** | **[create-ux-spec](specs/ux/E5x--create-ux-spec.md)** |
| **Source** | `src/pages/Create.tsx`（最大頁面，700+ LOC） |

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
| **DevSeed** | `/dev/seed` | Dev-only 資料種入工具（僅 `import.meta.env.DEV` 時註冊） | `Button`, `Card`（+ seed script hooks） | local | `/seed/*` (dev) |
| **NotFound** | `/*` | 404 fallback | 靜態頁 | — | — |

> Wireframe / 完整互動細節：除 Create 已在 [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) 定案外，其餘頁面 `TBD — <fe-lead TBD> by 2026-05-15 TBD`。

## 7. 組件連結與導航系統

- **AppSidebar** (`src/components/layouts/AppSidebar.tsx`)：專案內導航，根據 `projectSteps` 渲染步驟連結，以 `getStepStatus()` 判斷 active/completed/not_started 狀態（dot / pulse / hollow 視覺指示）。
- **MobileNav**：響應式抽屜導航。
- **Cross-link 規則**：
  - Contradiction 卡 → 可跳 Create Step 1 (TRIZ) 對應 contradiction。
  - Anti-Anchor 路線 → 可跳 Track 頁對應 Validation Passport。
  - Pre-CAD 評分 → 可跳 `/projects/:id/decide` 當前 gate。
- **Command Menu**：`TBD — <fe-lead TBD> by 2026-Q3 TBD`（cmd+k 全局搜尋）。

## 8. 數據流與狀態管理

> 完整狀態架構（Context API、React Query config、技術版本）見 [`E5x--frontend-architecture.md`](E5x--frontend-architecture.md)：§2.1(c)（Context）、§4（技術選型）、§5（React Query / 效能）。以下僅列 IA 層特有的狀態模式。

- **URL as state**：Explore 頁 tab 寫入 URL hash（`#socratic`、`#contradictions`、`#cld`）；Create 頁以 `useState` 管理 `currentStep`（0–6）。
- **Theme**：`ThemeProvider`（`src/components/ThemeProvider.tsx`）使用 `next-themes`，存 `localStorage` key `rd-theme`。
- **AI Operation Guard**：`useAiOperationGuard` hook 管理 AI 操作鎖（startOp / endOp），防止並行 AI 呼叫。

## 9. URL 結構與路由規範

- **Pattern**：`/projects/:id/:stage`
- **stage** ∈ `brief | explore | track | create | pre-cad | cad | review | decide | feynman | constraint-labels`。
- **Global routes**：`/projects`、`/knowledge-base`、`/knowledge-base/:slug`、`/settings`、`/dev/seed`（dev only）。
- **Hash params**：Explore 頁用 `#socratic` / `#contradictions` / `#cld` 切換 tab。
- **404 fallback**：`NotFound.tsx`。

## 10. 實施檢查清單與驗收標準

> 統一檢查清單已合併至 [`E5x--frontend-architecture.md` §10](E5x--frontend-architecture.md#第十部分前端開發檢查清單)（含架構層 + IA / 導航層 + 驗收項目）。

## 11. 附錄

### A. 延伸閱讀
- Create 頁完整 UX → [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)
- 前端架構 → [`E5x--frontend-architecture.md`](E5x--frontend-architecture.md)
- BDD scenarios → [`E5x--bdd-scenarios.md`](E5x--bdd-scenarios.md)
- E3x 三大 scenario → [`../01-define/E3--system-interaction-flow.md`](../01-define/E3--system-interaction-flow.md)

### B. TBD 清單
- 各頁面（除 Create）完整 wireframe · command menu (cmd+k) · breadcrumb meta 集中化
