# Page-Level Prompt: ProjectDashboard 專案儀表板

> 進入專案後的主控台，以 Gate Donut、Phase Progress、KPI 卡片與矛盾收斂為核心，一覽專案全貌並快速導航至各功能模組。

---

## [PAGE META]

- **page_name**: ProjectDashboard
- **route_path**: `/projects/:id`
- **page_type**: dashboard
- **primary_goal**: 以結構化儀表板呈現單一專案的整體進度、Gate 通過率、KPI 現況、矛盾收斂狀態與 Pre-CAD 信心分數，讓設計工程師在 30 秒內掌握專案健康度
- **secondary_goal**: 透過 6+1 NavCards 提供功能模組入口，以專案歷程時間軸追蹤關鍵里程碑，並支援 Evidence 快速登錄
- **target_users**:
  - 主要：設計工程師（每日查看專案進度）
  - 次要：專案主管（週期性檢視 Gate 與 KPI 達標狀態）
- **entry_point**: 從專案列表頁點擊專案卡片 / URL 直接存取 `/projects/:id`
- **expected_time_on_page**: 30 秒 - 2 分鐘（瀏覽摘要後進入子功能頁）

---

## [STRUCTURE: SECTIONS]

1. **project_header**
   - section_type: header
   - section_purpose: 顯示返回按鈕、專案名稱、狀態 Badge、建立者、建立日期與 GateDonut 圖表

2. **phase_progress**
   - section_type: progress_bar
   - section_purpose: 以 PhaseProgressBar 視覺化各階段完成百分比

3. **project_overview**
   - section_type: summary_cards
   - section_purpose: MissionSummaryCard 顯示核心使命、硬約束與軟目標；KpiCards 顯示各 KPI 當前值與達標狀態

4. **precad_convergence**
   - section_type: gauge_cards
   - section_purpose: PreCadScoreGauge 顯示 Pre-CAD 信心分數；ContradictionConvergenceCard 顯示矛盾嚴重度分佈與健康警告

5. **quick_stats**
   - section_type: stats_grid
   - section_purpose: QuickStatsGrid 以數字卡片呈現關鍵統計（約束數、KPI 數、矛盾數、假設數等）

6. **nav_cards**
   - section_type: navigation_grid
   - section_purpose: 6+1 導航卡片（Brief / Explore / Track / Create / PreCad / Review / Decide）作為功能模組入口

7. **project_timeline**
   - section_type: timeline
   - section_purpose: 以時間軸呈現專案歷程事件（建立、Brief 確認、矛盾分析、TRIZ 解法、SCAMPER 變形、Pre-CAD 審查等）

8. **evidence_dialog**
   - section_type: modal_dialog
   - section_purpose: EvidenceEntryDialog 供使用者針對特定 KPI 快速登錄實證資料

---

## [SECTION COMPONENT SPEC]

### Section: project_header

- **layout**: 垂直排列，頂部返回按鈕，下方標題行（左對齊名稱 + Badge，右對齊 GateDonut），再下方 meta 資訊行
- **elements**:
  - back_button: Button(ghost) / required / `<ArrowLeft>` 圖標 + "返回專案列表"，導航至 `/projects`
  - project_name: H1 / required / `text-2xl font-bold tracking-tight`
  - status_badge: Badge / required / 依 `project.status` 顯示對應狀態文字（PROJECT_STATUS_LABELS），completed 用 secondary variant
  - creator_info: Span / required / `<User>` 圖標 + `project.createdBy`
  - date_info: Span / required / `<Calendar>` 圖標 + 建立日期（zh-TW locale）
  - gate_donut: GateDonut / required / 傳入 `passed` / `total` 顯示 Gate 通過比例
- **states**:
  - loading: 所有元素替換為 Skeleton（h-8 w-32 標題 + h-6 w-16 badge + 6 張 h-32 卡片）
  - error: 顯示 `<AlertCircle>` 圖標 + 錯誤訊息 + 重試按鈕 + 返回按鈕
  - not_found: 顯示「專案不存在」訊息 + 返回按鈕
- **copy_constraints**: 專案名稱無字數限制；狀態標籤依 PROJECT_STATUS_LABELS 對應

### Section: phase_progress

- **layout**: 單張 Card 包裹，CardContent 內含 PhaseProgressBar 元件
- **elements**:
  - progress_bar: PhaseProgressBar / required / 傳入 `project.phase_progress` 物件
- **states**:
  - default: 依各階段百分比渲染彩色分段進度條
  - zero: 所有階段均為 0%
- **copy_constraints**: 階段名稱由 PhaseProgressBar 內部定義

### Section: project_overview

- **layout**: 垂直排列，`space-y-3`，標題 "專案概覽" + MissionSummaryCard + KpiCards
- **elements**:
  - section_title: H2 / required / "專案概覽"
  - mission_card: MissionSummaryCard / conditional / 當 `brief` 或 `project.mission` 存在時顯示，傳入 projectId、projectOwnerId、mission、hardConstraints、softObjectives
  - kpi_cards: KpiCards / conditional / 當 `criticalKPIs.length > 0` 時顯示，傳入 kpis 陣列與 `onLogEvidence` callback
- **states**:
  - default: 顯示 mission 摘要與 KPI 卡片
  - empty: 當無 brief 且無 mission 時整區不渲染
  - kpi_status: 每張 KPI 卡依 currentStatus 顯示 on-track / at-risk / unknown 等狀態色
- **copy_constraints**: mission 截斷由 MissionSummaryCard 內部處理

### Section: precad_convergence

- **layout**: 雙欄 grid `md:grid-cols-2 gap-4`，左側 PreCadScoreGauge，右側 ContradictionConvergenceCard
- **elements**:
  - precad_gauge: PreCadScoreGauge / conditional / 傳入 score、fatalResolved/Total、majorResolved/Total
  - convergence_card: ContradictionConvergenceCard / conditional / 傳入 totalNodes、fatal/major/minorCount、hasCircularDependency、healthWarning
- **states**:
  - default: 兩張卡片並排
  - partial: 僅一張卡片時自動填滿
  - hidden: 當無矛盾資料時整區不渲染
- **copy_constraints**: 分數以百分比顯示；警告訊息由元件內部決定

### Section: quick_stats

- **layout**: 標題 "Quick Stats" + QuickStatsGrid 或空狀態卡片
- **elements**:
  - section_title: H2 / required / "Quick Stats"
  - stats_grid: QuickStatsGrid / conditional / 當 quickStats 非全零時顯示
  - empty_cta: Card + Button / conditional / 全零時顯示「從 Brief 開始你的設計旅程」+ "開始 Brief" 按鈕導航至 `/projects/:id/brief`
- **states**:
  - default: 數字卡片 grid
  - zero_data: 居中文字 + CTA 按鈕
- **copy_constraints**: CTA 文案固定 "從 Brief 開始你的設計旅程"

### Section: nav_cards

- **layout**: 標題 "功能導航" + NavCards 元件（grid 佈局）
- **elements**:
  - section_title: H2 / required / "功能導航"
  - cards: NavCards / required / 傳入 `getMockNavCards(project.phase_progress)` 產生的 6+1 卡片陣列（Brief / Explore / Track / Create / PreCad / Review / Decide）
- **states**:
  - default: 所有卡片可點擊
  - locked: 依 phase_progress 鎖定尚未解鎖的階段卡片
- **copy_constraints**: 卡片標題與描述由 mockNavCards 資料定義

### Section: project_timeline

- **layout**: Card 包裹，CardHeader 標題 "專案歷程" + CardContent 內含 ProjectTimeline
- **elements**:
  - timeline: ProjectTimeline / conditional / 傳入 projectId 與 history 陣列（依日期倒序排列）
- **states**:
  - default: 時間軸列表，每筆事件含日期、標題、摘要、作者、類型（milestone / task / review / decision）
  - empty: 當 `history.length === 0` 時整張 Card 不渲染
- **copy_constraints**: 事件摘要超過 60 字截斷加省略號

### Section: evidence_dialog

- **layout**: Modal dialog，由 `evidenceDialogOpen` state 控制開關
- **elements**:
  - dialog: EvidenceEntryDialog / required / 傳入 open、onOpenChange、projectId、defaultKpiId
- **states**:
  - closed: 預設關閉
  - open: 由 KpiCards 的 "Log Evidence" callback 觸發，自動帶入對應 kpiId
- **copy_constraints**: 無特殊限制

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. **頁面載入** → 以 `useEffect` 在 mount 時 invalidate 該專案所有相關 query cache → 全部 hook 平行發起 API 請求 → Loading skeleton 顯示 → 資料到位後渲染各區塊
2. **Gate Donut 點擊** → 無直接互動（僅視覺指示）
3. **KPI 卡片 "Log Evidence"** → 設定 `evidenceDefaultKpiId` + 開啟 `EvidenceEntryDialog`
4. **NavCard 點擊** → `navigate` 至對應子頁面路由
5. **Quick Stats 空狀態 CTA** → 導航至 `/projects/:id/brief`
6. **Timeline 事件 relatedPage** → ProjectTimeline 內部可導航至相關頁面
7. **返回按鈕** → 導航至 `/projects`
8. **錯誤重試** → 呼叫 `refetch()` 重新載入專案資料

### RWD 行為差異

- **Desktop (lg+)**: NavCards 以 3 欄 grid 排列；PreCad + Convergence 雙欄並排；header 標題與 GateDonut 同行
- **Tablet (sm-lg)**: NavCards 以 2 欄排列；標題與 GateDonut 垂直堆疊
- **Mobile (<sm)**: 所有區塊單欄堆疊；header flex-col；NavCards 單欄全寬

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useProject(id)` → 專案基本資料（name, status, createdBy, createdAt, phase_progress, gates_passed, gates_total, quick_stats, mission, hardConstraints, softObjectives）
  - `useProjectStats(id)` → 即時統計數據（覆蓋 project.quick_stats）
  - `useBrief(id)` → Brief mission、updatedAt、createdAt
  - `useConstraints(id)` → 約束條件列表（type, description）
  - `useKpis(id)` → KPI 列表（kpiName, targetValue, currentValue, currentStatus, unit）
  - `useContradictions(id)` → 矛盾列表（severity, resolved, createdAt）
  - `useAntiAnchorRoutes(id)` → Anti-Anchor 非典型架構路線
  - `useTrizSolutions(id)` → TRIZ 解法（status, path: TC/PC/SF）
  - `useSubsystems(id)` → 子系統定義（name, confirmed）
  - `useScamperVariants(id)` → SCAMPER 變異（adopted, newContradictions）
  - `useAlternatives(id)` → 概念方案（name, mustScores, overallPass）
  - `useConceptRoutes(id)` → Concept Routes（type: composite/single）
  - `useTrackAssumptions(id)` → 假設追蹤（verificationStatus）
- **state**:
  - `evidenceDialogOpen: boolean` — Evidence 登錄 dialog 開關
  - `evidenceDefaultKpiId: string | null` — 預設帶入的 KPI ID
- **error_cases**:
  - API 載入失敗 → 顯示 AlertCircle 圖標 + "載入失敗" 訊息 + 重試按鈕
  - 專案不存在 → 顯示 "專案不存在" 訊息 + 返回按鈕
  - 部分資料缺失（brief / contradictions / kpis） → 對應區塊不渲染，不影響其他區塊

---

## [ACCEPTANCE CRITERIA]

- [ ] 進入頁面時自動 invalidate 所有該專案相關 query cache，確保儀表板顯示最新資料
- [ ] Loading 狀態顯示 Skeleton 佔位符（標題 + 6 張卡片骨架）
- [ ] 專案不存在或 API 錯誤時顯示對應錯誤頁面與重試 / 返回按鈕
- [ ] 專案名稱、狀態 Badge、建立者、日期正確顯示於 header
- [ ] GateDonut 正確顯示 gates_passed / gates_total 比例
- [ ] PhaseProgressBar 正確渲染各階段進度百分比
- [ ] MissionSummaryCard 顯示 mission、硬約束與軟目標（優先使用 DB brief，fallback 至 project 欄位）
- [ ] KpiCards 顯示所有 KPI 的名稱、目標值、當前值與狀態，無當前值時顯示 "待測試"
- [ ] PreCadScoreGauge 依 fatal/major 矛盾解決比例計算並顯示分數
- [ ] ContradictionConvergenceCard 顯示 fatal / major / minor 數量與健康警告（>5 矛盾或有 fatal 時）
- [ ] QuickStatsGrid 全零時顯示空狀態 CTA 引導至 Brief 頁
- [ ] 6+1 NavCards 正確渲染且依 phase_progress 決定鎖定狀態
- [ ] ProjectTimeline 整合 Phase 1 + Phase 2 事件並依日期倒序排列
- [ ] KpiCards 的 "Log Evidence" 按鈕正確觸發 EvidenceEntryDialog 並帶入 kpiId
- [ ] RWD：Desktop 3 欄 / Tablet 2 欄 / Mobile 1 欄切換正確
