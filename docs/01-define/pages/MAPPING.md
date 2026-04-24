# 頁面規格對應表 (Page Specification Mapping)

> **用途：** 作為 `docs/02-design/E5x--frontend-information-architecture.md`（IA 18 頁定義）與本目錄 `pages/*.md`（18 份 page spec）之間的**雙向對照索引**。
> **維護原則：** IA 新增/刪除頁面時同步更新本檔；新增 spec 檔時新增對應列。
>
> **最後更新：** 2026-04-24 · **版本：** v2.0 · **對應 IA 版本：** v1.1 · **對應前端架構版本：** v1.1 · **對應 API 規格版本：** v1.2

---

## 1. 快速總覽

| 指標 | 數字 |
|:-----|:----|
| IA 定義頁面總數 | **18 頁**（Auth 2 + Project 入口 2 + Phase 1 Define 2 + Phase 2 Diverge 3 + Phase 3 Converge 4 + 輔助 2 + 系統 2 + 開發 1） |
| Page spec 檔數 | **18 份**（`01_auth.md` — `18_not_found.md`） |
| 已覆蓋頁面 | 18 / 18 |
| 受保護路由（ProtectedRoute） | 14 頁 |
| 公開路由 | 3 頁（Auth, ResetPassword, NotFound） |
| DEV-only 路由 | 1 頁（DevSeed） |

---

## 2. IA 頁面 → Page Spec 檔（Forward Mapping）

### 2.1 認證（Public Routes，2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P01 | `/auth` | 登入/註冊 | — | `01_auth.md` | `src/pages/Auth.tsx` |
| P02 | `/reset-password` | 重設密碼 | — | `02_reset_password.md` | `src/pages/ResetPassword.tsx` |

### 2.2 專案入口（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P03 | `/projects` | 專案列表 | — | `03_project_list.md` | `src/pages/ProjectList.tsx` |
| P04 | `/projects/:id` | 專案儀表板 | — | `04_project_dashboard.md` | `src/pages/ProjectDashboard.tsx` |

### 2.3 Phase 1 — Define（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P05 | `/projects/:id/brief` | 任務定義 / Brief | 1 | `05_task_definition.md` | `src/pages/TaskDefinition.tsx` |
| P06 | `/projects/:id/explore` | 探索 / Socratic 問答 | 1 | `06_explore.md` | `src/pages/Explore.tsx` |

### 2.4 Phase 2 — Diverge（3 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P07 | `/projects/:id/track` | 假設追蹤 | 2 | `07_track.md` | `src/pages/Track.tsx` |
| P08 | `/projects/:id/create` | 方案創造 | 2 | `08_create.md` | `src/pages/Create.tsx` |
| P09 | `/projects/:id/pre-cad` | Pre-CAD 審查 | 2 | `09_pre_cad_review.md` | `src/pages/PreCadReview.tsx` |

### 2.5 Phase 3 — Converge（4 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P10 | `/projects/:id/cad` | CAD 進行中 | 2.5 | `10_cad_in_progress.md` | `src/pages/CadInProgress.tsx` |
| P11 | `/projects/:id/review` | 設計審查 | 3 | `11_design_review.md` | `src/pages/DesignReview.tsx` |
| P12 | `/projects/:id/decide` | 決策記錄 | 3 | `12_decision_record.md` | `src/pages/DecisionRecord.tsx` |
| P13 | `/projects/:id/feynman` | 費曼學習 / 知識內化 | 3 | `13_feynman.md` | `src/pages/Feynman.tsx` |

### 2.6 專案輔助 + 全域知識（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P14 | `/knowledge-base`, `/knowledge-base/:slug` | 知識庫 | — | `14_knowledge_base.md` | `src/pages/KnowledgeBase.tsx` |
| P15 | `/projects/:id/constraint-labels` | 約束標籤字典 | — | `15_constraint_label_dictionary.md` | `src/pages/ConstraintLabelDictionary.tsx` |

### 2.7 系統與開發（3 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P16 | `/settings` | 設定 | — | `16_settings.md` | `src/pages/Settings.tsx` |
| P17 | `/dev/seed` | 開發種子資料 | — | `17_dev_seed.md` | `src/pages/DevSeed.tsx` |
| P18 | `/*` | 404 頁面未找到 | — | `18_not_found.md` | `src/pages/NotFound.tsx` |

---

## 3. Page Spec 檔 → IA 頁面（Reverse Mapping）

| # | Spec 檔 | 覆蓋 IA 頁 | 頁面類型 | Gate 覆蓋 |
|:--|:--------|:-----------|:---------|:----------|
| 01 | `01_auth.md` | **P01** | auth | — |
| 02 | `02_reset_password.md` | **P02** | auth | — |
| 03 | `03_project_list.md` | **P03** | list | — |
| 04 | `04_project_dashboard.md` | **P04** | dashboard | Gate overview |
| 05 | `05_task_definition.md` | **P05** | form | Gate 1.1 |
| 06 | `06_explore.md` | **P06** | wizard | Gate 1.2, Phase Gate 1 |
| 07 | `07_track.md` | **P07** | kanban | Gate 2.1 |
| 08 | `08_create.md` | **P08** | wizard | Gate 2.2, Phase Gate 2 |
| 09 | `09_pre_cad_review.md` | **P09** | review | Gate P |
| 10 | `10_cad_in_progress.md` | **P10** | progress | — |
| 11 | `11_design_review.md` | **P11** | review | Gate 3.1 |
| 12 | `12_decision_record.md` | **P12** | form | Gate 3.2, Phase Gate 3 |
| 13 | `13_feynman.md` | **P13** | detail | Gate 8 |
| 14 | `14_knowledge_base.md` | **P14** | list + detail | — |
| 15 | `15_constraint_label_dictionary.md` | **P15** | utility | — |
| 16 | `16_settings.md` | **P16** | form | — |
| 17 | `17_dev_seed.md` | **P17** | utility | — |
| 18 | `18_not_found.md` | **P18** | error | — |

---

## 4. 主題分群視圖

### 4.1 認證層（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P01 `/auth` | `01_auth.md` |
| P02 `/reset-password` | `02_reset_password.md` |

### 4.2 專案管理（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P03 `/projects` 專案列表 | `03_project_list.md` |
| P04 `/projects/:id` 專案儀表板 | `04_project_dashboard.md` |

### 4.3 Phase 1 Define — 問題定義（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P05 Brief / 任務定義 | `05_task_definition.md` |
| P06 Explore / Socratic 問答 | `06_explore.md` |

### 4.4 Phase 2 Diverge — 方案發散（3 頁 / 3 檔）

| IA | Spec |
|:---|:-----|
| P07 Track / 假設追蹤 | `07_track.md` |
| P08 Create / 方案創造（7-step wizard） | `08_create.md` |
| P09 PreCadReview / Pre-CAD 審查 | `09_pre_cad_review.md` |

### 4.5 Phase 3 Converge — 收斂決策（4 頁 / 4 檔）

| IA | Spec |
|:---|:-----|
| P10 CadInProgress / CAD 進行中 | `10_cad_in_progress.md` |
| P11 DesignReview / 設計審查 | `11_design_review.md` |
| P12 DecisionRecord / 決策記錄 | `12_decision_record.md` |
| P13 Feynman / 知識內化 | `13_feynman.md` |

### 4.6 知識與輔助工具（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P14 KnowledgeBase / 知識庫 | `14_knowledge_base.md` |
| P15 ConstraintLabelDictionary / 約束標籤字典 | `15_constraint_label_dictionary.md` |

### 4.7 系統設定與開發（3 頁 / 3 檔）

| IA | Spec |
|:---|:-----|
| P16 Settings / 設定 | `16_settings.md` |
| P17 DevSeed / 開發種子 | `17_dev_seed.md` |
| P18 NotFound / 404 | `18_not_found.md` |

---

## 5. 關鍵互動路徑與檔案對照（核心使用者旅程）

### 5.1 Journey 1: Forward TRIZ 解矛盾（E3x §2）

```
01 登入 → 03 專案列表 → 04 專案儀表板 → 08 Create Step 1 (TRIZ)
                                         ↓
                                    L1 → L2 → L3 分層 drill-down
                                         ↓
                                    08 Create Step 4 (決策中心) → 比較採納
```

**涉及 Spec**：`01` → `03` → `04` → `08`

### 5.2 Journey 2: Reverse Anti-Anchor（E3x §3）

```
04 專案儀表板 → 08 Create Step 0 (Anti-Anchor)
                    ↓
               AI 產出 3 條非典型路線
                    ↓
               07 Track → Validation Passport 假設追蹤
```

**涉及 Spec**：`04` → `08` → `07`

### 5.3 Journey 3: Pre-CAD Gate（E3x §4）

```
04 專案儀表板 → 09 Pre-CAD 審查 → AI 六維評分
                                    ↓
                              12 DecisionRecord → KT 決策 + 簽名
```

**涉及 Spec**：`04` → `09` → `12`

### 5.4 Journey 4: 完整 8-Gate 流程（Happy Path）

```
01 登入 → 03 列表 → 04 儀表板
  → 05 Brief (Gate 1.1)
  → 06 Explore (Gate 1.2 → Phase Gate 1)
  → 07 Track (Gate 2.1)
  → 08 Create (Gate 2.2 → Phase Gate 2)
  → 09 Pre-CAD (Gate P)
  → 10 CAD 進行中
  → 11 DesignReview (Gate 3.1)
  → 12 DecisionRecord (Gate 3.2 → Phase Gate 3)
  → 13 Feynman (Gate 8 知識內化)
```

**涉及 Spec**：`01` → `03` → `04` → `05` → `06` → `07` → `08` → `09` → `10` → `11` → `12` → `13`

### 5.5 Journey 5: 知識庫查詢

```
任一頁面 sidebar → 14 知識庫列表 → 14 知識庫文章詳情
```

**涉及 Spec**：`14`

---

## 6. 業務元件與 Spec 對應

> 對齊 `E5x--frontend-architecture.md §2`（Feature-first organization）。基礎 UI 元件（`src/components/ui/*`，shadcn/ui 50+）不在本表追蹤。

### 6.1 業務元件清單

| 元件 | 所屬 Feature | 用途 | 被引用 Spec |
|:-----|:------------|:-----|:------------|
| `ProjectCard` | projects | 專案卡片（名稱、狀態、Phase） | 03 |
| `ProjectFilters` | projects | 搜尋 + Phase 篩選 + Creator 篩選 | 03 |
| `CreateProjectModal` | projects | 新建專案 Modal | 03 |
| `GateDonut` | dashboard | Gate 通過率甜甜圈圖 | 04 |
| `PhaseProgressBar` | dashboard | 階段進度條 | 04 |
| `MissionSummaryCard` | dashboard | 任務摘要卡（使命 + 約束 + KPI） | 04 |
| `KpiCards` | dashboard | KPI 指標卡片組 | 04 |
| `PreCadScoreGauge` | dashboard | Pre-CAD 信心分數儀表 | 04 |
| `ContradictionConvergenceCard` | dashboard | 矛盾收斂狀態卡 | 04 |
| `QuickStatsGrid` | dashboard | 快速統計網格 | 04 |
| `NavCards` | dashboard | 6+1 導航卡片（各階段入口） | 04 |
| `ProjectTimeline` | dashboard | 專案時間軸（里程碑 + 事件） | 04 |
| `StageNavigation` | dashboard | 階段導航 | 04 |
| `EvidenceEntryDialog` | evidence | 證據輸入對話框 | 04, 11 |
| `ConstraintsTable` | brief | 硬約束表格（含 AI 建議） | 05 |
| `KpiList` | brief | 關鍵績效指標列表 | 05 |
| `AITaskDefinitionCard` | task-definition | AI 5W1H 定義卡 | 05 |
| `AISuggestionCard` | brief | AI 建議卡片 | 05 |
| `EvidenceRefsInline` | brief | 行內證據引用 | 05 |
| `GateChecklist` | brief | Gate 檢查清單 | 05, 06 |
| `FileUploadZone` | task-definition | 檔案上傳區 | 05 |
| `AIExtractionResults` | task-definition | AI 提取結果 | 05 |
| `FeasibilityValidation` | task-definition | 可行性驗證 | 05 |
| `MultiItemInput` | task-definition | 多項目輸入（軟目標 / 非目標） | 05 |
| `SocraticTab` | explore | Socratic 問答 Tab | 06 |
| `ContradictionDisplayCard` | explore | 矛盾展示卡片 | 06 |
| `DecomposedPCCard` | explore | 分解 PC 卡片 | 06 |
| `CldTab` | explore | 因果迴圈圖 Tab | 06 |
| `ExploreGates` | explore | Explore Gate 檢查 | 06 |
| `SocraticPanel` | contradiction | Socratic 面板 | 06 |
| `KanbanBoard` | track | 4 欄假設看板 | 07 |
| `UnknownFactors` | track | 未知因素管理 | 07 |
| `TrackGate` | track | Track Gate 檢查 | 07 |
| `CreateStepper` | create | 7-step 步進器 | 08 |
| `MissionContext` | create | 任務脈絡面板 | 08 |
| `LayeredSolutionCard` | create | 分層 TRIZ 解法卡片 | 08 |
| `SubsystemHierarchyView` | create | 子系統層次圖 | 08 |
| `PackageMapPanel` | create | 封裝映射面板 | 08 |
| `InterfaceContractsPanel` | create | 介面契約面板 | 08 |
| `SpatialOverlayDialog` | create | 空間疊加對話框 | 08 |
| `SpatialOverrideDialog` | create | 空間覆寫對話框 | 08 |
| `PromoteToLearnedDialog` | create | 晉升為學習元件 | 08 |
| `ConvergenceDashboard` | create | 收斂儀表板 | 08 |
| `ConvergenceGraph` | solution | 收斂圖（React Flow） | 08 |
| `HumanReviewPanel` | create | 人工審查面板 | 08 |
| `MultiSolutionAdoptionPanel` | create | 多方案採納面板 | 08 |
| `BranchExplorationPanel` | create | 分支探索面板 | 08 |
| `ArchitectureHaltOverlay` | create | 架構暫停覆蓋層 | 08 |
| `DifferentialAnalysisPanel` | create | 差異分析面板 | 08 |
| `CompatibilityMatrix` | create | 相容性矩陣 | 08 |
| `ConceptRouteCard` | create | 概念路線卡片 | 08 |
| `KnowledgeRefsPanel` | create | 知識引用面板 | 06, 07, 08, 13 |
| `SpatialTraceHover` | precad | 空間追蹤懸浮卡 | 09 |
| `SpatialConfidenceBadge` | create | 空間信心徽章 | 08 |
| `AttachmentsPanel` | review | 附件上傳面板 | 11 |
| `HealthMonitor` | solution | 健康監控 | 08 |
| `AssumptionEditor` | assumption | 假設編輯器 | 07 |
| `VerificationKanban` | assumption | 驗證看板 | 07 |
| `CausalLoopDiagram` | assumption | 因果迴圈圖 | 06 |
| `ContradictionTraceability` | assumption | 矛盾可追溯性 | 06 |

### 6.2 跨頁共用元件

| 元件 | 用途 | 被引用 Spec |
|:-----|:-----|:------------|
| `AppLayout` | 受保護路由 Layout（Sidebar + Outlet） | 所有受保護頁面 |
| `AppSidebar` | 側邊欄導航（Phase 步驟） | 所有 `/projects/:id/*` |
| `MobileNav` | 響應式抽屜導航 | 所有受保護頁面 |
| `ProtectedRoute` | 認證守衛 | 所有受保護頁面 |
| `NavLink` | 導航連結 | 所有頁面 |
| `ErrorBoundary` | 全域錯誤邊界 | App 層 |
| `ThemeProvider` | 主題切換（Light/Dark/System） | App 層, 16 |

### 6.3 治理規則

- **新增業務元件：** PR 必須同步更新本表一列（Feature / 用途 / 被引用 Spec）
- **刪除業務元件：** PR 必須先確認本表「被引用 Spec」皆已改用替代方案
- **重新命名：** 新舊名並列一個 release 後刪除舊名列

---

## 7. API 端點與 Spec 對應

> 對齊 `E5--api-design-specification.md` v1.2 的端點清單。

### 7.1 後端 Router → 頁面消費對應

| Router / API 分群 | API Base | 消費 Spec |
|:-------------------|:---------|:----------|
| `brief.py` | `/api/v1/definitions/*` | **05** (TaskDefinition) |
| `socratic.py` | `/api/v1/questions/*` | **06** (Explore), **11** (DesignReview — AI blackhat) |
| `cld.py` | `/api/v1/causal-loops/*` | **06** (Explore) |
| `contradictions.py` | `/api/v1/contradictions/*` | **06** (Explore), **08** (Create) |
| `triz.py` | `/api/v1/triz/*` | **08** (Create) |
| `scamper.py` | `/api/v1/scamper/*` | **08** (Create) |
| `anti_anchor.py` | `/api/v1/alternatives/anti-anchor` | **08** (Create) |
| `validation.py` | `/api/v1/alternatives/validation-passport` | **08** (Create) |
| `convergence.py` | `/api/v1/convergence/*` | **08** (Create) |
| `unknown_factors.py` | `/api/v1/unknown-factors/*` | **07** (Track) |
| `spatial.py` | `/api/v1/spatial/*` | **08** (Create) |
| `gates.py` | `/api/v1/gates/*` | **05, 06, 07, 08, 09, 11, 12, 13** |
| `pre_cad.py` | `/api/v1/pre-cad-reviews/*` | **09** (PreCadReview) |
| `must.py` | `/api/v1/must/*` | **08** (Create), **09** (PreCadReview) |
| `want.py` | `/api/v1/want/*` | **12** (DecisionRecord) |
| `risks.py` | `/api/v1/risks/*` | **08** (Create), **11** (DesignReview) |
| `actions.py` | `/api/v1/actions/*` | **12** (DecisionRecord) |
| `assumptions.py` | `/api/v1/assumptions/*` | **06** (Explore), **07** (Track) |
| `knowledge.py` | `/api/v1/knowledge/*` | **13** (Feynman), **14** (KnowledgeBase) |
| `export.py` | `/api/v1/export` | **12** (DecisionRecord) |
| `health.py` | `/api/v1/health` | 系統 |
| `analyst.py` (v1.2) | `/api/v1/analyst/*` | **06** (Explore — future 8.5) |
| `evidence.py` (v1.2) | `/api/v1/evidence/*` | **11** (DesignReview), **08** (Create — future 8.6) |
| Supabase Auth | `supabase.auth.*` | **01** (Auth), **02** (ResetPassword), **16** (Settings) |
| Supabase Direct | `supabase.from(table).*` | **03-13, 15, 16** (各頁面 CRUD) |

### 7.2 ADR-008 新增端點（Module 8.0 Auto-TRIZ v2）

| 端點 | 說明 | 未來消費 Spec |
|:-----|:-----|:--------------|
| `POST /analyst/five-why` | 5 Why 根因分析 | 06 (Explore 擴充 #problem-scoping) |
| `POST /analyst/kt-analysis` | KT Is/Is Not | 06 (Explore 擴充 #problem-scoping) |
| `POST /analyst/function-analysis` | FA 功能建模 | 06 (Explore 擴充 #function-analysis) |
| `POST /analyst/oz-ot-analysis` | OZ-OT 分析 | 08 (Create TRIZ 前置) |
| `POST /analyst/entry-grading` | 入口成熟度分級 | 06 (Explore 入口分級) |
| `POST /triz/sim-matrix` | 多 TC SIM 交互矩陣 | 08 (Create SIM 面板) |
| `POST /triz/complexity-check` | CCI 複雜度判定 | 08 (Create CCI badge) |
| `POST /evidence/register-claim` | 數值聲明註冊 | 08, 11 (Evidence Registry) |
| `POST /evidence/verify` | Claim 驗證 | 08, 11 |
| `GET /evidence/coverage` | 覆蓋率統計 | 08, 11 |

---

## 8. Context / Hook 與 Spec 對應

### 8.1 React Context

| Context | 檔案 | 消費 Spec |
|:--------|:-----|:----------|
| `AuthContext` | `src/contexts/AuthContext.tsx` | **01, 02, 16**（Auth 系列）+ 全域（user/session） |
| `ArtifactContext` | `src/contexts/ArtifactContext.tsx` | **04-13**（Artifact 狀態機：Draft → Released） |
| `ProjectDataContext` | `src/contexts/ProjectDataContext.tsx` | **05-13**（跨步驟資料共享） |

### 8.2 主要 API Hook 索引

| Hook | 消費 Spec | 對應 Router |
|:-----|:----------|:------------|
| `useProjects`, `useDeleteProject` | 03 | Supabase `projects` |
| `useProject`, `useProjectStats` | 04 | Supabase `projects` |
| `useBrief`, `useConstraints`, `useKpis` | 04, 05, 06, 08 | `brief.py` + Supabase |
| `useTaskDefinitionForm` | 05 | `brief.py` |
| `useSocraticQuestions` | 06 | `socratic.py` + Supabase |
| `useExploreContradictions` | 06 | Supabase `contradictions` |
| `useCldNodes`, `useCldEdges` | 06 | `cld.py` + Supabase |
| `useTrackAssumptions`, `useUpdateTrackAssumptionStatus` | 07 | Supabase `assumptions` |
| `useUnknownFactors`, `useCreateUnknownFactor`, `useConvertUnknownToAssumption` | 07 | Supabase `unknown_factors` |
| `useContradictions` | 06, 08 | Supabase `contradictions` |
| `useAntiAnchorRoutes` | 04, 08 | `anti_anchor.py` + Supabase |
| `useTrizSolutions`, `useLayeredTrizSolutions`, `useDirectedTrizSolutions` | 04, 08 | `triz.py` + Supabase |
| `useSubsystems` | 04, 08 | Supabase `subsystems` |
| `useScamperVariants` | 04, 08 | `scamper.py` + Supabase |
| `useAlternatives`, `useUpdateAlternative` | 04, 08, 09, 10, 11 | Supabase `alternatives` |
| `useConceptRoutes` | 04, 08 | Supabase `concept_routes` |
| `useConvergenceLoop` | 08 | `convergence.py` |
| `usePreCadSolutions`, `usePreCadConvergenceStats` | 09 | Supabase + `pre_cad.py` |
| `useEvidenceMatrix`, `useCreateEvidenceRow`, `useUpdateEvidenceRow` | 11 | Supabase `evidence_matrix` |
| `useRisks`, `useCreateRisk`, `useUpdateRisk`, `useDeleteRisk` | 11 | Supabase `risks` |
| `useExperiments`, `useCreateExperiment`, `useUpdateExperiment` | 11 | Supabase `experiments` |
| `useSolutions` | 11 | Supabase `alternatives` |
| `useDecision` | 12 | Supabase `decisions` |
| `useWantCriteria`, `useWantScores` | 12 | `want.py` + Supabase |
| `useSignatures` | 12 | Supabase `signatures` |
| `useActionItems` | 12 | Supabase `action_items` |
| `useKnowledgeEntries`, `useUpdateKnowledgeEntry` | 13 | `knowledge.py` + Supabase |
| `useKnowledgeArticles`, `useKnowledgeArticle` | 14 | Supabase `knowledge_articles` |
| `useConstraintLabelMap`, `useConstraintLabelHistory` | 15 | Supabase `constraint_label_*` |
| `useAuth` | 01, 02, 16 | Supabase Auth |
| `useTheme` | 16 | localStorage |

---

## 9. 8-Gate 系統與頁面對應

> 對齊 E3 架構 — 8 Gate + 3 Phase Gate 的狀態機。

| Gate | 名稱 | 檢查頁面 | 前置條件摘要 |
|:-----|:-----|:---------|:-------------|
| Gate 1.1 | Brief 完備 | **P05** TaskDefinition | Mission + ≥1 Constraint + ≥1 KPI |
| Gate 1.2 | Explore 完備 | **P06** Explore | ≥1 Contradiction formalized |
| Phase Gate 1 | Define 完成 | **P06** Explore | Gate 1.1 + 1.2 passed |
| Gate 2.1 | Track 完備 | **P07** Track | ≥1 Assumption verified |
| Gate 2.2 | Create 完備 | **P08** Create | ≥1 TRIZ solution adopted |
| Phase Gate 2 | Diverge 完成 | **P08** Create | Gate 2.1 + 2.2 passed |
| Gate P | Pre-CAD 通過 | **P09** PreCadReview | Confidence ≥ threshold + solutions selected |
| Gate 3.1 | Design Review | **P11** DesignReview | Evidence matrix + risks reviewed |
| Gate 3.2 | Decision 凍結 | **P12** DecisionRecord | KT decision confirmed + signed |
| Phase Gate 3 | Converge 完成 | **P12** DecisionRecord | Gate 3.1 + 3.2 passed |
| Gate 8 | Knowledge 內化 | **P13** Feynman | ≥1 knowledge entry reviewed |

---

## 10. Code Splitting 策略與 Spec 對應

> 對齊 `E5x--frontend-architecture.md §5`（效能策略）與 `src/App.tsx` 的 lazy/eager 配置。

| 載入策略 | 頁面 | Spec | 理由 |
|:---------|:-----|:-----|:-----|
| **Eager** (critical path) | Auth, ResetPassword, ProjectList, ProjectDashboard, NotFound | 01, 02, 03, 04, 18 | 首屏 / 認證 / 404 |
| **Lazy** (route-level) | TaskDefinition, Explore, Track, Create, PreCadReview, CadInProgress, DesignReview, DecisionRecord, Feynman, KnowledgeBase, ConstraintLabelDictionary, Settings, DevSeed | 05-17 | 非首屏，按需載入 |

---

## 11. 驗證檢查清單

- [x] 所有 18 個 IA 頁面都有對應 spec 檔
- [x] 所有 spec 檔都能對應回 IA 頁面
- [x] Phase 分組（Define / Diverge / Converge）對齊 IA 與 sidebar navigation
- [x] Gate 覆蓋完整（8 Gate + 3 Phase Gate）
- [x] API Router → Spec 反向索引建立
- [x] Context / Hook → Spec 反向索引建立
- [x] Code splitting 策略對齊 App.tsx 實際配置
- [x] 業務元件清單對齊 `src/components/` 實際結構
- [ ] （待辦）Module 8.0 Auto-TRIZ v2 前端頁面擴充時，同步更新 Spec 06/08 + 本表

---

## 12. 變更記錄

| 日期 | 版本 | 變更摘要 |
|:-----|:-----|:---------|
| 2026-04-24 | v2.0 | 完全重寫：從舊專案（鎖匠工單管理系統 52 頁 IA）遷移至 RD Design Copilot（18 頁 IA）。建立 Forward/Reverse/主題分群/使用者旅程/業務元件/API 對應/Context-Hook 索引/8-Gate 對應/Code Splitting 策略 全維度對照。對齊 E5 API v1.2、E5x 前端架構 v1.1、E5x IA v1.1 |
