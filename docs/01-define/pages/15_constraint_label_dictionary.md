# Page-Level Prompt: ConstraintLabelDictionary 約束標籤字典

> 管理與分類專案的硬約束標籤，支援自動分類、合併標籤、版本升級與歷史回滾。

---

## [PAGE META]
- **page_name**: ConstraintLabelDictionary
- **route_path**: `/projects/:id/constraint-labels`
- **page_type**: utility
- **primary_goal**: 讓專案擁有者管理硬約束 (Hard Constraints) 的標籤分類映射
- **secondary_goal**: 提供標籤合併、版本升級、操作歷史回滾與差異預覽功能
- **target_users**: 專案擁有者 (owner)、系統管理者 (admin)；其他使用者為唯讀模式
- **entry_point**: 專案 Dashboard 的約束管理入口
- **expected_time_on_page**: 2 ~ 8 分鐘

---

## [STRUCTURE: SECTIONS]
1. **Header**
   - section_type: navigation + access-control
   - section_purpose: 返回按鈕、頁面標題、唯讀模式提示
2. **MappingVersion**
   - section_type: info + action
   - section_purpose: 顯示 Schema 版本與 Classifier 版本，提供升級按鈕
3. **MergeLabels**
   - section_type: form
   - section_purpose: 合併重複標籤（來源 → 目標）
4. **LabelDistribution**
   - section_type: content-list
   - section_purpose: 顯示當前標籤分佈，按標籤分組並列出例項
5. **OperationHistory**
   - section_type: content-list + action
   - section_purpose: 操作歷史記錄，支援回滾與差異預覽
6. **RollbackDiffPreview**
   - section_type: detail
   - section_purpose: 展示回滾差異的 before/after 對比

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center justify-between gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | Button (ghost, sm) | required | ArrowLeft icon + "回 Dashboard"，導航至 `/projects/:id` |
  | Title | `<h1>` | required | "標籤字典"，text-xl font-semibold |
  | ReadOnlyBadge | Badge (outline) | optional | 僅非 owner/admin 時顯示："唯讀模式（僅專案擁有者或 Admin 可編輯）" |
- **states**: canManageLabels = isProjectOwner || isAdmin → 控制所有寫入操作
- **copy_constraints**: 無

### Section: MappingVersion
- **layout**: Card > CardHeader (pb-2) + CardContent (flex flex-wrap items-center gap-2)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | CardTitle | required | "映射版本"，text-base |
  | SchemaBadge | Badge (outline) | required | "Schema v{schemaVersion}" |
  | ClassifierBadge | Badge (outline) | required | "Classifier {classifierVersion}" |
  | UpgradeButton | Button (outline, sm) | optional | 僅 isLegacyPayload && canManageLabels 時顯示，"升級至 {CONSTRAINT_LABEL_CLASSIFIER_VERSION}" |
- **states**:
  - 最新版本: 僅顯示兩個版本 badge
  - 舊版本且有權限: 額外顯示升級按鈕
  - 點擊升級: 呼叫 persistLabelMap → toast.success "已升級映射版本至目前分類器版本"
- **copy_constraints**: 無

### Section: MergeLabels
- **layout**: Card > CardHeader (pb-2) + CardContent (flex flex-wrap items-center gap-2)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | CardTitle | required | "合併重複標籤"，text-base |
  | FromSelect | Select | required | placeholder "來源標籤"，w-[180px]，選項來自 labelOptions |
  | Arrow | `<span>` | required | "→"，text-sm text-muted-foreground |
  | ToSelect | Select | required | placeholder "目標標籤"，w-[180px]，選項來自 labelOptions |
  | MergeButton | Button | required | GitMerge icon + "合併"，disabled={!canManageLabels} |
- **states**:
  - 未選擇: 兩個 Select 為空，合併按鈕可點擊但會 toast.error 提示
  - 相同標籤: toast.error "來源與目標標籤不能相同"
  - 成功: 更新 localLabelMap，persistLabelMap，toast.success，重設 Select
  - 無權限: MergeButton disabled，點擊 toast.error "你沒有權限修改標籤字典"
- **copy_constraints**: 無

### Section: LabelDistribution
- **layout**: Card > CardHeader (pb-2) + CardContent (space-y-2)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | CardTitle | required | "目前標籤分佈"，text-base |
  | GroupCard | `<div>` (rounded border p-3) | required | 每個標籤一組 |
  | GroupLabel | `<p>` | required | 標籤名稱，text-sm font-medium |
  | GroupCount | Badge (secondary) | required | 該標籤下的項目數量 |
  | ItemList | `<ul>` (list-disc) | required | 最多顯示 6 項，超過顯示 "... 還有 {n} 項" |
- **states**:
  - 有 Hard Constraints: 按標籤分組顯示
  - 無 Hard Constraints: 顯示 "目前沒有 Hard Constraints。"
- **copy_constraints**: 每組最多顯示 6 個範例項目

### Section: OperationHistory
- **layout**: Card > CardHeader (pb-2) + CardContent (space-y-2)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | CardTitle | required | "操作歷史（可一鍵回滾）"，text-base |
  | HistoryItem | `<div>` (rounded border p-3) | required | flex flex-wrap items-center justify-between gap-2 |
  | ActionBadge | Badge (outline) | required | 操作類型標籤 |
  | SourceBadge | Badge (secondary) | required | 來源標籤 |
  | Timestamp | `<p>` | required | 日期時間（zh-TW locale），附註 note 若有 |
  | ActorInfo | `<p>` | required | "by {displayName} ({email})"，text-xs text-muted-foreground |
  | PreviewDiffButton | Button (ghost, sm) | required | 切換 "預覽差異" / "收合差異" |
  | RollbackButton | Button (outline, sm) | required | RotateCcw icon + "回滾到此版本"，disabled={!canManageLabels} |
- **action_types**:
  | Action | Label |
  |:-------|:------|
  | auto_classify_sync | 自動分類同步 |
  | manual_override | 手動改標籤 |
  | merge_labels | 合併標籤 |
  | upgrade_classifier_version | 升級分類器版本 |
  | rollback | 回滾 |
- **states**:
  - 有歷史記錄: 依時間列出操作記錄
  - 無歷史記錄: 顯示 "目前尚無操作歷史。"
  - 回滾: 呼叫 handleRollback → toast.success "已回滾到指定版本"
- **copy_constraints**: 歷史記錄上限取最近 30 筆

### Section: RollbackDiffPreview
- **layout**: Card > CardHeader (pb-2) + CardContent (space-y-2)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | CardTitle | required | "回滾差異預覽"，text-base |
  | DiffSummary | `<p>` | required | "共 {n} 個 key 會改變（顯示前 20 筆）"，text-muted-foreground |
  | DiffRow | `<div>` (rounded border p-2) | required | 每行顯示 key (font-mono)、from 值、to 值 |
- **states**: 僅當 previewHistoryId 有值且找到對應 previewItem 時顯示
- **copy_constraints**: 最多顯示前 20 筆差異

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者從專案 Dashboard 進入 `/projects/:id/constraint-labels`
2. 頁面載入時平行呼叫 `useConstraints(projectId)` 取得約束列表與 `useConstraintLabelMap(projectId)` 取得標籤映射
3. 載入完成後初始化 localLabelMap，自動執行 `classifyHardConstraints` 對未分類的約束進行自動分類
4. 若有新分類結果 (hasUpdates) 且有權限 → 自動 persistLabelMap 並記錄操作歷史 (auto_classify_sync)
5. 使用者可選擇來源與目標標籤，點擊「合併」→ 更新 localLabelMap、persistLabelMap、記錄歷史 (merge_labels)
6. 若為舊版 payload (isLegacyPayload) → 顯示升級按鈕 → 點擊升級至最新 classifier 版本
7. 操作歷史區域可點擊「預覽差異」→ 展開 RollbackDiffPreview 顯示 before/after 對比
8. 點擊「回滾到此版本」→ handleRollback → 更新 localLabelMap 並 persistLabelMap、記錄歷史 (rollback)

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | page-shell-wide，單欄 | Select 元件水平排列 |
| Tablet (768 ~ 1023px) | 同 Desktop | Select 元件可能換行 (flex-wrap) |
| Mobile (< 768px) | 同 Desktop | 所有 flex 容器自動換行，操作歷史項目垂直堆疊 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload / Params |
  |:-------|:---------|:-----------------|
  | 取得約束列表 | `useConstraints(projectId)` | 回傳 `{ id, type, description }[]`，篩選 type="hard" |
  | 取得標籤映射 | `useConstraintLabelMap(projectId)` | 回傳 `{ entryId, labelMap, classifierVersion, schemaVersion, isLegacyPayload }` |
  | 取得操作歷史 | `useConstraintLabelHistory(projectId, 30)` | 回傳最近 30 筆 `{ id, createdAt, payload: { action, source, actor, before, after, classifierVersion, note } }[]` |
  | 建立標籤映射 | `useCreateConstraintLabelMap(projectId)` | `{ project_id, asset_type, title, content, reviewed }` |
  | 更新標籤映射 | `useUpdateConstraintLabelMap(projectId)` | `{ id, content, reviewed }` |
  | 建立操作歷史 | `useCreateConstraintLabelHistory(projectId)` | `{ project_id, asset_type, title, content, reviewed }` |
  | 用戶端分類 | `classifyHardConstraints(items, labelMap)` | 純前端邏輯，回傳 `{ groups, nextLabelMap, hasUpdates }` |
  | 取得標籤建議 | `getConstraintLabelSuggestions(labelMap)` | 純前端邏輯，回傳可用標籤字串陣列 |
- **error_cases**:
  - 約束或標籤映射載入失敗 → Skeleton 持續顯示
  - 無權限執行寫入操作 → toast.error 提示權限不足
  - 合併時來源與目標相同 → toast.error "來源與目標標籤不能相同"
  - 合併時未選擇標籤 → toast.error "請先選擇來源標籤與目標標籤"
  - mutation 正在進行中 (isPending) → 防止重複提交

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面顯示返回按鈕「回 Dashboard」，可導航至 `/projects/:id`
- [ ] 非 owner/admin 使用者看到「唯讀模式」badge，所有寫入按鈕 disabled
- [ ] 映射版本卡片正確顯示 Schema 版本與 Classifier 版本
- [ ] 舊版 payload 時且有權限顯示升級按鈕，點擊後 toast 成功
- [ ] 合併標籤區域有兩個 Select（來源/目標）與合併按鈕
- [ ] 合併時驗證：未選擇標籤 → 錯誤提示；相同標籤 → 錯誤提示
- [ ] 合併成功後更新 localLabelMap、persistLabelMap、重設 Select、toast 成功
- [ ] 標籤分佈卡片按標籤分組，每組顯示標籤名、數量 badge、最多 6 個範例項目
- [ ] 無 Hard Constraints 時顯示空狀態文字
- [ ] 操作歷史顯示操作類型 badge、來源 badge、時間戳、操作者資訊
- [ ] 「預覽差異」按鈕可切換展開/收合差異預覽區塊
- [ ] 差異預覽顯示 key、from、to，最多 20 筆
- [ ] 「回滾到此版本」按鈕可回滾標籤映射並記錄歷史
- [ ] 自動分類同步 (auto_classify_sync) 在初始化後自動執行（有更新且有權限時）
- [ ] 載入中顯示 Skeleton（標題 + 版本卡片 + 分佈卡片佔位）
- [ ] 所有 mutation 防止重複提交 (isPending 檢查)
