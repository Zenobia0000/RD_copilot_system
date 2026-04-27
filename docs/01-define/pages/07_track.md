# Page-Level Prompt: Track 追蹤 / 假設驗證

> X1 — 透過 Kanban 看板追蹤假設驗證進度，並以「未知集合 U」管理尚未歸類的不確定因素。

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | D/X/V 編號化：Step 2.1 → X1；Gate 2.1 → Gate X1；移除 AA/SCAMPER 殘留 |
| v2.0 | 2026-04-20 | 初版 page spec |

---

## [PAGE META]
- **page_name**: Track
- **route_path**: `/projects/:id/track`
- **page_type**: workflow
- **primary_goal**: 讓使用者透過拖曳式 Kanban 管理設計假設的驗證狀態（未驗證 → 驗證中 → 已驗證 / 已推翻），通過 Gate X1 後進入方案創造
- **secondary_goal**: 收集「未知集合 U」中尚未歸類的不確定因素，支援一鍵轉換為假設進行追蹤
- **target_users**: RD 工程師、專案負責人
- **entry_point**: Dashboard 專案卡片進入，或由前一步驟（Explore）自動導航
- **expected_time_on_page**: 5 ~ 15 分鐘

---

## [STRUCTURE: SECTIONS]
1. **Header**
   - section_type: navigation + status
   - section_purpose: 返回 Dashboard 的導航按鈕、頁面標題、儲存狀態指示器
2. **SectionIntro**
   - section_type: guidance
   - section_purpose: 說明頁面操作方式（拖曳假設至對應階段、未知因素轉換）
3. **TabSwitcher**
   - section_type: tab-navigation
   - section_purpose: 切換「假設 Kanban」與「未知集合 U」兩個子頁面
4. **KanbanBoard**
   - section_type: interactive-board
   - section_purpose: 四欄式看板顯示假設卡片，支援拖曳更新驗證狀態
5. **UnknownFactors**
   - section_type: list-management
   - section_purpose: 管理未知因素清單，支援建立/編輯/轉換為假設
6. **KnowledgeRefsPanel**
   - section_type: reference
   - section_purpose: 顯示與當前頁面相關的知識參考連結（WBS 3.4.2）
7. **TrackGate**
   - section_type: gate-check
   - section_purpose: Gate X1 檢查項目，通過後可導航至 Create 頁面

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: space-y-3，上方為返回按鈕 + 儲存狀態（flex justify-between），下方為標題區（flex items-center gap-3）
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | `<Button variant="ghost">` | required | ArrowLeft icon + "返回 Dashboard"，onClick 導航至 `/projects/:id` |
  | SaveStatus | `<span>` | optional | 僅非 idle 時顯示。saving: "Saving..."；saved: Check icon + "Saved"（2 秒後回 idle） |
  | AccentBar | `<div>` | required | h-8 w-1 rounded-full bg-amber-500，視覺標記 |
  | Title | `<h1>` | required | "Track — 假設追蹤"，text-2xl font-bold tracking-tight，附 HelpTooltip |
  | Subtitle | `<p>` | required | "X1 · 假設 Kanban + 未知集合 U"，text-sm text-muted-foreground |
- **states**: saveStatus 三態切換 idle/saving/saved
- **copy_constraints**: HelpTooltip 說明文字需涵蓋「高風險假設需有實驗計畫」及 Gate X1 通過條件

### Section: SectionIntro
- **layout**: SectionIntro 元件，單行說明文字
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | IntroText | SectionIntro | required | 說明拖曳操作與未知集合 U 的用途 |
- **states**: 無
- **copy_constraints**: 文字需簡潔描述：「將設計假設拖曳到對應的驗證階段（未驗證 → 驗證中 → 已驗證/已推翻）。「未知集合 U」收集尚未歸類的不確定因素，可一鍵轉為假設進行追蹤。」

### Section: TabSwitcher
- **layout**: Tabs 元件，TabsList 為 w-full grid grid-cols-2 h-11
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | KanbanTab | TabsTrigger | required | value="kanban"，文字「假設 Kanban」，附 Badge 顯示假設總數 |
  | UnknownTab | TabsTrigger | required | value="unknown"，文字「未知集合 U」，附 Badge 顯示 open 狀態因素數 |
- **states**: active tab 以 amber-500 底線（3px）標示；Badge 在 sm 以下斷點隱藏
- **copy_constraints**: Tab 標籤使用繁體中文

### Section: KanbanBoard
- **layout**: 四欄水平排列（flex gap-3），每欄對應一個驗證狀態
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Column_Unverified | KanbanColumn | required | 「未驗證」欄位 |
  | Column_Verifying | KanbanColumn | required | 「驗證中」欄位 |
  | Column_Verified | KanbanColumn | required | 「已驗證」欄位 |
  | Column_Negated | KanbanColumn | required | 「已推翻」欄位 |
  | AssumptionCard | DraggableCard | required | 顯示假設內容、風險等級（H/H*/L）、實驗計數 |
- **states**:
  - default: 卡片可拖曳
  - dragging: 卡片半透明，目標欄位高亮
  - optimistic: 拖曳後立即更新 UI，背景執行 API mutation
- **copy_constraints**: 欄位標題使用繁體中文

### Section: UnknownFactors
- **layout**: 因素清單，每項顯示狀態與操作按鈕
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | FactorList | list | required | 顯示所有未知因素，含狀態標示（open/investigating/resolved/dismissed） |
  | CreateButton | Button | required | 新增未知因素 |
  | EditForm | inline-form | optional | 編輯因素描述、影響程度、備註 |
  | ConvertButton | Button | optional | 一鍵將因素轉換為假設，加入 Kanban 追蹤 |
- **states**:
  - empty: 顯示空狀態提示
  - editing: 顯示內嵌編輯表單
  - converting: 轉換中，按鈕 disabled
- **copy_constraints**: 操作按鈕文字使用繁體中文

### Section: KnowledgeRefsPanel
- **layout**: Collapsible 面板，位於 Tabs 下方
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | RefsPanel | KnowledgeRefsPanel | required | 顯示 mockPageKnowledgeRefs.track 的知識參考連結 |
- **states**: 可收合/展開
- **copy_constraints**: 無

### Section: TrackGate
- **layout**: Gate 檢查卡片，底部固定區域
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | GateItem | check-item | required | 「至少 1 個假設處於「驗證中」或以上」，顯示 current/target 與通過狀態 |
  | NextButton | Button | required | 通過 Gate 後啟用，導航至 `/projects/:id/create` |
- **states**:
  - not-passed: 門檻項目未滿足，NextButton disabled
  - passed: 所有項目綠色勾選，NextButton 啟用
- **copy_constraints**: Gate 項目描述使用繁體中文

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者從 Dashboard 進入 Track 頁面，預設顯示「假設 Kanban」tab
2. 拖曳假設卡片至不同欄位 → 觸發 optimistic UI 更新 → 背景呼叫 `useUpdateTrackAssumptionStatus` mutation
3. 切換至「未知集合 U」tab → URL hash 更新為 `#unknown`
4. 建立新未知因素 → 呼叫 `useCreateUnknownFactor` mutation
5. 編輯因素狀態/備註 → 呼叫 `useUpdateUnknownFactor` mutation
6. 一鍵轉換因素為假設 → 呼叫 `useConvertUnknownToAssumption` mutation → 因素從清單移除，假設出現在 Kanban
7. Gate X1 條件滿足後，點擊下一步 → 導航至 Create 頁面

### RWD 行為差異
- **Desktop (>=1024px)**: Kanban 四欄水平排列，Badge 全數顯示
- **Tablet (768-1023px)**: Kanban 可能需要水平滾動
- **Mobile (<768px)**: Tab 標籤文字縮小（text-xs），Badge 隱藏（hidden sm:inline-flex），Kanban 欄位堆疊或水平滾動

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Hook | Method | Purpose |
  |:-----|:-------|:--------|
  | `useTrackAssumptions(projectId)` | GET | 取得專案所有假設 |
  | `useUpdateTrackAssumptionStatus(projectId)` | PATCH | 更新假設驗證狀態（Kanban 拖曳） |
  | `useConstraints(projectId)` | GET | 取得專案約束條件（顯示於 Kanban 卡片） |
  | `useUnknownFactors(projectId)` | GET | 取得未知因素清單 |
  | `useCreateUnknownFactor(projectId)` | POST | 建立新未知因素 |
  | `useUpdateUnknownFactor(projectId)` | PATCH | 更新因素狀態/備註 |
  | `useConvertUnknownToAssumption(projectId)` | POST | 將未知因素轉換為假設 |
- **error_cases**:
  - API 請求失敗: Optimistic UI 回滾至上一狀態，toast.error 顯示錯誤訊息
  - 網路斷線: 本地狀態保留，重新連線後自動同步
  - 轉換失敗: 因素保留原狀態，toast.error 提示

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面載入時顯示 Skeleton loading 狀態
- [ ] Kanban 四欄正確顯示：未驗證、驗證中、已驗證、已推翻
- [ ] 假設卡片可拖曳至不同欄位，UI 即時更新（optimistic）
- [ ] 假設卡片顯示風險等級（H/H*/L）與實驗計數
- [ ] Tab 切換正確更新 URL hash（#kanban / #unknown）
- [ ] 可建立、編輯未知因素
- [ ] 可將未知因素一鍵轉換為假設
- [ ] Gate X1 條件正確計算：至少 1 個假設處於「驗證中」或以上
- [ ] Gate 未通過時下一步按鈕 disabled
- [ ] Gate 通過後可正確導航至 `/projects/:id/create`
- [ ] 儲存狀態指示器正確顯示 saving/saved 狀態
- [ ] KnowledgeRefsPanel 正確顯示知識參考連結
- [ ] RWD：Mobile 下 Badge 隱藏，Tab 文字縮小
