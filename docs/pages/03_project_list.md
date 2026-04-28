---
id: P03
file_id: "03"
page_name: ProjectList
route_path: /projects
page_type: list
phase: null
ia_group: portfolio
gate: null
protected: true
dev_only: false
source_component: src/pages/ProjectList.tsx
spec_version: 1.0
ia_version: 1.2
status: stable
last_updated: 2026-04-24
api_resources: [projects]
modules: []
depends_on: [P01]
absorbed_specs: []
optional_sections: []
---

# Page-Level Prompt: ProjectList 專案列表

> 專案管理主頁面，提供統計概覽、搜尋篩選、專案卡片網格、新增與刪除功能。

---

## [PAGE META]
- **primary_goal**: 讓使用者瀏覽、搜尋、篩選所有概念設計專案並快速掌握整體狀態
- **secondary_goal**: 提供新增專案與刪除專案的操作入口
- **target_users**: 已登入的 RD 工程師、專案管理者
- **entry_point**: 登入成功後自動導向、側邊欄導航、密碼重設後導向
- **expected_time_on_page**: 1 ~ 5 分鐘

---

## [STRUCTURE: SECTIONS]
1. **PageHeader**
   - section_type: header
   - section_purpose: 顯示頁面標題與說明文字
2. **StatsSummary**
   - section_type: dashboard
   - section_purpose: 以 4 張統計卡片呈現專案數量概覽（全部/進行中/已完成/已封存）
3. **ProjectFilters**
   - section_type: filter
   - section_purpose: 提供搜尋、階段篩選、建立者篩選與新增專案按鈕
4. **ResultsCount**
   - section_type: info
   - section_purpose: 顯示目前篩選結果數量
5. **ProjectGrid**
   - section_type: list
   - section_purpose: 以卡片網格呈現專案清單
6. **CreateProjectModal**
   - section_type: modal
   - section_purpose: 新增專案的對話框
7. **DeleteAlertDialog**
   - section_type: modal
   - section_purpose: 刪除專案的確認對話框，含高風險警告

---

## [SECTION COMPONENT SPEC]

### Section: PageHeader
- **layout**: space-y-1
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Title | `<h1>` | required | "專案列表"，text-h2 tracking-tight |
  | Description | `<p>` | required | "管理您的概念設計專案，追蹤進度與決策。"，text-sm text-muted-foreground |
- **states**: 無特殊狀態
- **copy_constraints**: 標題與描述文字固定

### Section: StatsSummary
- **layout**: grid grid-cols-2 sm:grid-cols-4 gap-2.5
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | StatCard: 全部專案 | Card | required | FolderKanban icon，text-primary，顯示 projects.length |
  | StatCard: 進行中 | Card | required | PlayCircle icon，text-phase-2，顯示 status="in_progress" 數量 |
  | StatCard: 已完成 | Card | required | CheckCircle2 icon，text-success，顯示 status="completed" 數量 |
  | StatCard: 已封存 | Card | required | Archive icon，text-muted-foreground，顯示 status="archived" 數量 |
- **states**:
  - default: 顯示即時統計數據
  - loading: 數值為 0（等待 API 回傳）
- **copy_constraints**: 每張卡片內含 icon (h-5 w-5)、數值 (text-xl font-semibold)、標籤 (text-[11px] text-muted-foreground)

### Section: ProjectFilters
- **layout**: 由 `<ProjectFilters>` 子元件封裝
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SearchInput | Input | required | 搜尋專案名稱或描述，controlled by `search` state |
  | PhaseFilter | Select | required | 篩選專案階段，"all" 為預設值 |
  | CreatorFilter | Select | required | 篩選建立者，選項從 projects 動態提取並排序，"all" 為預設值 |
  | CreateButton | Button | required | 觸發 CreateProjectModal 開啟 |
- **states**:
  - default: 所有 filter 為 "all"，搜尋為空
  - active: 有任一篩選條件啟用
- **copy_constraints**: 篩選邏輯為 AND 組合（搜尋 AND 階段 AND 建立者）

### Section: ResultsCount
- **layout**: text-[11px] text-muted-foreground
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CountText | `<p>` | optional | "顯示 N 個專案"，有篩選時額外顯示 "（共 M 個）" |
- **states**:
  - hidden: isLoading 或 isError 或 filteredProjects.length = 0 時不顯示
  - filtered: 有篩選條件時顯示總數
- **copy_constraints**: 無

### Section: ProjectGrid
- **layout**: grid gap-4 sm:grid-cols-2 lg:grid-cols-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ProjectCard | `<ProjectCard>` | required | 接收 project 資料、onDelete callback、isDeleting 狀態 |
- **states**:
  - loading: 顯示 6 個 Skeleton 佔位卡片（含標題、描述、進度條、metadata 骨架）
  - error: 顯示 AlertCircle icon (h-12 w-12 text-destructive) + "載入失敗" + "無法取得專案列表，請稍後再試。" + RefreshCw 重試按鈕
  - empty (no filter): 顯示 FolderOpen icon + "尚無專案" + "建立你的第一個專案，開始概念設計旅程。" + 新增專案按鈕
  - empty (with filter): 顯示 FolderOpen icon + "找不到符合條件的專案" + "嘗試調整搜尋或篩選條件。"（無新增按鈕）
  - data: 正常顯示 ProjectCard 網格
- **copy_constraints**: Skeleton 卡片結構需模擬實際 ProjectCard 的佈局

### Section: CreateProjectModal
- **layout**: 由 `<CreateProjectModal>` 子元件封裝
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Modal | CreateProjectModal | required | controlled by `createOpen` state，`onOpenChange={setCreateOpen}` |
- **states**:
  - closed: createOpen = false
  - open: createOpen = true
- **copy_constraints**: 詳見 CreateProjectModal 元件規格

### Section: DeleteAlertDialog
- **layout**: AlertDialog > AlertDialogContent
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Title | AlertDialogTitle | required | "確認刪除專案？" |
  | Description | AlertDialogDescription | required | "專案「{name}」將被永久刪除，且無法復原。" |
  | RiskWarning | `<div>` | required | border-destructive/30, bg-destructive/10, AlertTriangle icon, "高風險操作" 標題 + "刪除後將移除該專案及其關聯資料，請再次確認。" |
  | CancelButton | AlertDialogCancel | required | "取消"，disabled={deleteProject.isPending} |
  | ConfirmButton | AlertDialogAction | required | bg-destructive，文字 "確認刪除" / "刪除中..."，disabled={deleteProject.isPending} |
- **states**:
  - closed: projectPendingDelete = null
  - open: projectPendingDelete 有值
  - deleting: deleteProject.isPending = true，按鈕文字變為 "刪除中..."，兩按鈕皆 disabled
- **copy_constraints**: 風險警告區塊必須明確告知「永久刪除」與「無法復原」

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入 `/projects`，觸發 `useProjects()` 載入專案列表
2. 載入中 → 顯示 6 個 Skeleton 佔位卡片
3. 載入成功 → 顯示 StatsSummary 統計卡片 + ProjectFilters + ProjectGrid
4. 載入失敗 → 顯示錯誤畫面與「重試」按鈕，點擊觸發 `refetch()`
5. 使用者在 SearchInput 輸入關鍵字 → 即時篩選專案名稱與描述（case-insensitive）
6. 使用者切換 PhaseFilter → 依階段或完成狀態篩選
7. 使用者切換 CreatorFilter → 依建立者篩選
8. 篩選結果為空 → 顯示空狀態提示
9. 點擊 ProjectFilters 中的新增按鈕 → 開啟 CreateProjectModal
10. 在 CreateProjectModal 中填寫資料並送出 → 關閉 modal，列表自動刷新
11. 點擊 ProjectCard 上的刪除按鈕 → 設定 projectPendingDelete → 開啟 DeleteAlertDialog
12. DeleteAlertDialog 中點擊「確認刪除」→ 呼叫 `deleteProject.mutateAsync({ id })` → 成功後關閉 dialog
13. DeleteAlertDialog 中點擊「取消」→ 關閉 dialog，清除 projectPendingDelete

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | StatsSummary 4 欄，ProjectGrid 3 欄 | grid-cols-4 / lg:grid-cols-3 |
| Tablet (640 ~ 1023px) | StatsSummary 4 欄，ProjectGrid 2 欄 | sm:grid-cols-4 / sm:grid-cols-2 |
| Mobile (< 640px) | StatsSummary 2 欄，ProjectGrid 1 欄 | grid-cols-2 / 預設 1 欄 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | Hook / API Call | Description |
  |:-------|:----------------|:------------|
  | 取得專案列表 | `useProjects()` | TanStack Query hook，GET 所有專案，回傳 `Project[]` |
  | 刪除專案 | `useDeleteProject()` | TanStack Query mutation，DELETE 指定 project by id |
- **error_cases**:
  - 專案列表載入失敗 → isError = true，顯示錯誤畫面與重試按鈕
  - 刪除專案失敗 → toast 由 useDeleteProject hook 內部處理
  - 網路斷線 → TanStack Query 自動重試機制

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面頂部顯示標題「專案列表」與說明文字
- [ ] 4 張統計卡片正確顯示全部/進行中/已完成/已封存數量，各有對應 icon 與顏色
- [ ] 搜尋欄位可依專案名稱和描述即時篩選（case-insensitive）
- [ ] 階段篩選與建立者篩選正確過濾專案，篩選為 AND 組合
- [ ] 建立者篩選選項從專案資料動態提取並排序
- [ ] 篩選啟用時 ResultsCount 顯示「顯示 N 個專案（共 M 個）」
- [ ] 載入中顯示 6 個 Skeleton 佔位卡片，模擬 ProjectCard 佈局
- [ ] 載入失敗顯示 AlertCircle 錯誤畫面與「重試」按鈕
- [ ] 無專案時顯示 FolderOpen 空狀態與「新增專案」按鈕
- [ ] 有篩選但無結果時顯示「找不到符合條件的專案」（無新增按鈕）
- [ ] 點擊新增按鈕開啟 CreateProjectModal
- [ ] 刪除確認 dialog 含「高風險操作」警告區塊（AlertTriangle icon + destructive 樣式）
- [ ] 刪除進行中時按鈕顯示「刪除中...」且兩按鈕皆 disabled
- [ ] RWD：Desktop 3 欄 / Tablet 2 欄 / Mobile 1 欄專案卡片網格
- [ ] RWD：StatsSummary Desktop/Tablet 4 欄 / Mobile 2 欄
