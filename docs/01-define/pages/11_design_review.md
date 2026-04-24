# Page-Level Prompt: DesignReview 設計審查

> CAD 完成後的證據驅動設計審查，整合證據矩陣、風險登錄、最小實驗與附件，以 Gate 3.1 檢查確保設計完整性。

---

## [PAGE META]

- **page_name**: DesignReview
- **route_path**: `/projects/:id/review`
- **page_type**: review_workspace
- **primary_goal**: 讓 RD 工程師與主管在 CAD 完成後，以證據矩陣審查假設、以風險登錄管理設計風險、以最小實驗驗證關鍵假設，形成證據驅動的設計審查決策
- **secondary_goal**: 透過 AI 黑帽質疑與證據缺口分析主動發現設計盲點，通過 Gate 3.1 後銜接決策記錄階段
- **target_users**:
  - 主要：RD 工程師（建立與更新證據、風險、實驗）
  - 次要：RD 主管（審查方案去向、批准審查結論）
- **entry_point**: CadInProgress 頁面點擊「進入 Design Review」 / Dashboard 專案頁面直接進入
- **expected_time_on_page**: 10 - 30 分鐘（完整審查含多個 Tab 切換與 AI 互動）

---

## [STRUCTURE: SECTIONS]

1. **phase_header**
   - section_type: header
   - section_purpose: 顯示 Phase 3 階段標示、頁面標題、返回按鈕與 SectionIntro 說明

2. **candidate_solutions**
   - section_type: card_grid
   - section_purpose: 列出通過 MUST 的審查方案，每方案附帶去向選擇（批准/修訂/淘汰）

3. **ai_blackhat**
   - section_type: ai_panel
   - section_purpose: AI 模擬黑帽思維，自動針對設計方案提出技術質疑

4. **evidence_gap_alert**
   - section_type: alert_card
   - section_purpose: 當存在 E0/E1 證據缺口時，主動提示並引導前往規劃實驗

5. **data_source_banner**
   - section_type: info_banner
   - section_purpose: 顯示當前資料來源摘要（假設數、風險數、實驗數）與前往 Track 的連結

6. **review_tabs**
   - section_type: tabbed_content
   - section_purpose: 4 個 Tab 承載核心審查內容：證據矩陣、風險登錄、最小實驗、附件

7. **conclusion_section**
   - section_type: decision_card
   - section_purpose: 方案去向摘要、審查結論備註、批准審查按鈕

8. **knowledge_refs_panel**
   - section_type: reference_panel
   - section_purpose: 顯示相關知識參考連結（WBS 3.4.2）

9. **gate_31**
   - section_type: gate_check
   - section_purpose: Gate 3.1 設計審查完整性檢查，4 項條件全通過後可進入 Decide 階段

---

## [SECTION COMPONENT SPEC]

### Section: phase_header

- **layout**: 頂部 1px 主色條 + 標題區（返回按鈕 + 標題/副標題）
- **elements**:
  - phase_bar: Div / required / h-1 w-full rounded-full bg-primary
  - back_button: Button(variant="ghost", size="sm") / required / ArrowLeft + "返回"，導向 `/projects/:id`
  - title: H1 / required / "Review -- 設計審查" + HelpTooltip
  - phase_label: Body SM / required / "Phase 3: Converge > Step 3.1（CAD 完成後）"
  - section_intro: SectionIntro / required / 說明證據矩陣、風險、實驗的來源與用途
- **states**:
  - default: 正常顯示
- **copy_constraints**: 標題固定；HelpTooltip 說明最多 80 字

### Section: candidate_solutions

- **layout**: Card 容器，內含標題行 + 1-3 欄網格（md:2 xl:3 欄），間距 12px
- **elements**:
  - section_title: Body SM Bold / required / "審查方案列表" + Badge 顯示方案數
  - solution_card: Div(border + rounded) / required (per solution) / 包含：
    - name: Body SM Medium / required / 方案名稱，line-clamp-1
    - must_icons: IconGroup / required / 每項 MUST 標準以 CheckCircle（通過）/ XCircle（未通過）/ "--"（未評） 顯示
    - description: Caption / optional / 方案描述，line-clamp-2
    - disposition_select: Select / required / 選項：批准(approve) / 修訂(revise) / 淘汰(eliminate)
  - empty_state: Body SM / conditional / "沒有審查方案，請先完成 Pre-CAD 審查。"
- **states**:
  - default: 方案卡片正常顯示，去向 Select 未選擇
  - selected: Select 顯示對應值
- **copy_constraints**: 方案名稱 line-clamp-1；描述 line-clamp-2

### Section: ai_blackhat

- **layout**: Card 容器，border-destructive/20 bg-destructive/5 背景，紅色主題
- **elements**:
  - header: ShieldAlert icon + "AI 黑帽質疑" + Badge("AI") + HelpTooltip
  - question_list: Div[] / conditional / 每項以 "Q{n}" 紅色標籤 + 問題文字呈現，border bg-background
  - placeholder_text: Caption / conditional / 未生成時顯示 "尚未生成質疑，請點擊下方按鈕。"
  - generate_button: AiButton(variant="outline") / required / "黑帽質疑"
  - loading_state: Loader2 + "AI 正在分析設計弱點..."
- **states**:
  - idle: 顯示 placeholder 文字 + 按鈕
  - loading: Loader2 旋轉 + 文字提示，按鈕 loading 狀態
  - loaded: 顯示 Q1-Qn 質疑列表
  - error: 顯示預設質疑問題 + toast 警告
- **copy_constraints**: 每項質疑無字數限制

### Section: evidence_gap_alert

- **layout**: Card 容器，border-accent/20 bg-accent/5 背景，僅在存在 E0/E1 缺口時顯示
- **elements**:
  - header: AlertTriangle icon + "AI 證據缺口分析" + Badge("AI")
  - gap_list: Div[] / required / 每項顯示 assumptionCode Badge + summary + currentLevel Badge
  - suggestion_text: Caption / required / "建議：為上述 {N} 項假設規劃最小實驗，提升證據等級至 E2 以上。"
  - navigate_button: Button(variant="outline") / required / Beaker icon + "前往規劃實驗"，切換至 experiment Tab
- **states**:
  - visible: 存在 E0/E1 缺口時顯示
  - hidden: 所有假設 >= E2 時不渲染
- **copy_constraints**: summary 截斷顯示

### Section: data_source_banner

- **layout**: Card(bg-muted/30 border-dashed)，單列，Link2 icon + 文字
- **elements**:
  - source_text: Caption / required / "資料來源：證據矩陣（{N} 項假設），風險登錄（{N} 項），實驗（{N} 項）。"
  - track_link: Button(variant="link") / required / "前往 Track ->"，導向 `/projects/:id/track`
- **states**:
  - default: 正常顯示
- **copy_constraints**: 數字動態填充

### Section: review_tabs

- **layout**: Tabs 容器，TabsList 4 欄等寬網格
- **elements**:
  - tab_evidence: TabsTrigger / required / BarChart3 icon + "證據矩陣"
  - tab_risk: TabsTrigger / required / ShieldAlert icon + "風險登錄"
  - tab_experiment: TabsTrigger / required / Beaker icon + "最小實驗"（存在缺口時附加 AlertTriangle icon）
  - tab_attachments: TabsTrigger / required / Paperclip icon + "附件"（有附件時附加數量 Badge）

#### Tab 1: 證據矩陣 (evidence)

- **layout**: Desktop 為 heatmap 表格，Mobile 為卡片列表
- **elements**:
  - source_badges: Badge[] / optional / 前 4 項 assumptionCode，超過顯示 "+N 更多"，North Star 標記 Flag icon
  - heatmap_table (desktop): Table / required / 列 = 假設（assumptionCode + summary + NS 標記），欄 = E0-E4 五級證據
    - current_level: 實心圓（對應色彩），直徑 24px
    - has_experiment: 空心圓（對應色彩邊框），直徑 12px
  - mobile_cards: Card[] (mobile) / required / 每項假設一張卡片，顯示 assumptionCode + Badge(currentLevel) + summary + 五段進度條
  - gap_summary: Alert / required / 有缺口時琥珀色背景 + "{N} 項假設仍處於 E0/E1，存在證據缺口"；無缺口時綠色背景 + "所有假設已有充足證據"
  - empty_state: Card / conditional / "尚無數據，請先在 Track 頁建立假設" + "前往 Track" 按鈕
- **states**:
  - default: 表格/卡片正常顯示
  - empty: 空狀態 + CTA
  - has_gap: 琥珀色缺口摘要
  - no_gap: 綠色完成摘要

#### Tab 2: 風險登錄 (risk)

- **layout**: 左側 P x S 風險矩陣 + 右側風險表格（Desktop 水平排列，Mobile 垂直堆疊）
- **elements**:
  - source_note: Caption / required / 說明風險來源
  - ps_matrix: Table(5x5) / required / P(機率) x S(嚴重度) 矩陣，每格依 RPN 值填色（L/M/H/H*），有風險的格子顯示風險 ID
  - risk_table (desktop): Table / required / 欄位：ID / 描述(Input) / 失效模式(Input) / P(Select 1-5) / S(Select 1-5) / RPN(Badge) / 緩解措施(Input) / 刪除按鈕
    - high_risk_row: 背景 bg-destructive/5，mitigation 為空時 placeholder "需填寫"
  - mobile_cards: Card[] (mobile) / required / 每項風險一張卡片，包含所有欄位的 Input/Select
  - add_risk_button: Button(variant="secondary") / required / Plus icon + "新增風險"
  - ai_risk_button: AiButton / required / "識別風險"
  - empty_state: Card / conditional / "尚無風險，建議使用 AI 識別潛在風險"
- **states**:
  - default: 表格/卡片正常顯示
  - empty: 空狀態 + AI 建議
  - editing: 欄位可即時編輯，onChange 即呼叫 updateRisk
  - ai_loading: AI 按鈕 loading 狀態

#### Tab 3: 最小實驗 (experiment)

- **layout**: 1-2 欄網格（lg:2 欄），間距 12px
- **elements**:
  - source_note: Caption / required / 說明實驗資料來源
  - experiment_card: Card / required (per experiment) / 包含：
    - id_label: Caption / required / 實驗 ID
    - evidence_badge: Badge / required / 目標證據等級（E1-E4 色彩）
    - status_badge: Badge / required / Plan(計畫) / Running(執行中) / Done(已完成)
    - name: Body SM Medium / required / 實驗名稱
    - linked_assumptions: Badge[] / optional / 關聯假設代碼
    - method: Caption / optional / "方法: ..."
    - success_criteria: Caption / optional / "成功標準: ..."
    - result: Caption(bg-primary/5) / conditional / Done 狀態時顯示 "結果: ..."
    - edit_button: Button(variant="ghost") / required / "編輯"
    - delete_button: Button(variant="ghost", destructive) / required / Trash2 + "刪除"
  - add_exp_button: Button(variant="secondary") / required / Plus icon + "新增實驗"
  - ai_exp_button: AiButton / required / "建議實驗"
  - empty_state: Card / conditional / "尚無實驗，查看證據矩陣確認缺口後規劃實驗"
- **states**:
  - default: 卡片正常顯示
  - done: 卡片左側 3px 主色邊框
  - empty: 空狀態提示

#### Tab 4: 附件 (attachments)

- **layout**: AttachmentsPanel 元件，全寬
- **elements**:
  - description: Caption / required / "上傳 CAD 圖檔、仿真報告、測試數據等文件作為設計審查的佐證附件。每份文件可加上概略描述。"
  - attachments_panel: AttachmentsPanel / required / 支援上傳/下載/刪除，傳入 projectId
- **states**:
  - default: 顯示已上傳附件列表
  - empty: 無附件提示

### Section: conclusion_section

- **layout**: Card 容器，shadow 效果
- **elements**:
  - header: ClipboardCheck icon + "審查結論與決策"
  - disposition_summary: Badge[] / conditional / 每方案顯示名稱 + 去向（批准/修訂/淘汰/未決定），使用對應 variant
  - undecided_warning: Caption(destructive) / conditional / 有方案未選去向時顯示警告
  - conclusion_textarea: Textarea / optional / "審查結論備註（選填）"，maxLength=500，rows=3
  - approve_button: Button / required / "批准審查"
- **states**:
  - default: 按鈕可能 disabled（Gate 3.1 未通過或方案未全選去向）
  - submitting: Loader2 旋轉 + 按鈕 disabled
  - submitted: toast 成功 + 導向 Dashboard
- **copy_constraints**: 結論備註最多 500 字

### Section: gate_31

- **layout**: Card(border-2 border-primary/30 bg-primary/5)，醒目設計
- **elements**:
  - header: Flag icon + "Gate 3.1 -- 設計審查完整性檢查" + 狀態 Badge
  - checklist: CheckItem[] / required / 4 項檢查：
    1. 證據矩陣已建立 (>=1 假設有實驗)
    2. 所有 H*/H 風險有 mitigation
    3. North Star KPI 皆達 >= E2 證據等級
    4. MUST 已以 E2+ 證據重新驗證（無 E0）
  - proceed_button: Button / conditional / Gate 通過時："通過 -> 進入 Decide" + ArrowRight，導向 `/projects/:id/decide`
  - blocked_button: Button(disabled) / conditional / Gate 未通過時 disabled + Tooltip "請完成上方所有檢查項目"
- **states**:
  - passed: Badge "Gate 3.1 Passed" 主色背景，按鈕啟用
  - not_passed: Badge "Gate 3.1 未通過" destructive 背景，按鈕 disabled

### Section: experiment_modal

- **layout**: Dialog(max-w-md)，表單欄位垂直堆疊
- **elements**:
  - title: DialogTitle / required / 新增時 "新增實驗"，編輯時 "{id} -- 編輯實驗"
  - name_input: Input / required / 實驗名稱，maxLength=100，驗證 >= 3 字元
  - linked_assumptions_input: Input / required / 關聯假設，逗號分隔格式 "A-001, A-002"
  - evidence_level_select: Select / required / E0-E4 選項
  - method_textarea: Textarea / optional / 實驗方法，rows=2，maxLength=500
  - success_criteria_input: Input / optional / 成功標準，maxLength=200
  - status_select: Select / required / Plan / Running / Done
  - result_textarea: Textarea / conditional / Done 狀態時必填，rows=3，maxLength=500，驗證 >= 10 字元
  - save_button: Button / required / "儲存"
  - cancel_button: Button(variant="outline") / required / "取消"
- **states**:
  - new: 空白表單
  - editing: 預填現有資料
  - validation_error: toast 提示驗證錯誤

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. 使用者進入頁面 -> 平行載入 solutions、evidenceMatrix、risks、experiments 資料
2. 載入中顯示全頁 Loader2；載入失敗顯示 AlertTriangle + 重新載入按鈕
3. 審查方案列表 -> 為每方案選擇去向（approve/revise/eliminate）
4. AI 黑帽質疑 -> 點擊按鈕 -> 呼叫 socraticGenerate API -> 顯示質疑列表
5. 證據矩陣 Tab -> 檢視假設與證據等級 -> 發現 E0/E1 缺口 -> 跳轉至實驗 Tab
6. 風險登錄 Tab -> 新增/編輯/刪除風險 -> AI 識別風險 -> 填寫高風險緩解措施
7. 最小實驗 Tab -> 新增/編輯實驗（Modal） -> AI 建議實驗 -> 更新實驗狀態
8. 附件 Tab -> 上傳 CAD 圖檔/仿真報告
9. 結論區 -> 確認所有方案去向 -> 填寫結論備註 -> 點擊「批准審查」
10. Gate 3.1 全通過 -> 點擊進入 Decide 頁面

### RWD 行為差異

| 斷點 | 行為 |
|:-----|:-----|
| Desktop (>=1280px) | page-shell-medium 佈局；證據矩陣為 heatmap 表格；風險 P x S 矩陣 + 表格水平排列；實驗卡片 2 欄；方案卡片 3 欄 |
| Tablet (>=768px) | 方案卡片 2 欄；風險表格仍為表格形式；Tab icon 隱藏 |
| Mobile (<768px) | 證據矩陣改為卡片列表 + 五段進度條；風險改為卡片形式；實驗卡片 1 欄；方案卡片 1 欄；Tab 文字縮小 |

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useSolutions(projectId)` — 取得候選方案列表（篩選通過 MUST 的方案）
  - `useEvidenceMatrix(projectId)` — 取得證據矩陣行（假設 + 證據等級 + 實驗關聯）
  - `useCreateEvidenceRow()` — 新增證據矩陣行
  - `useUpdateEvidenceRow()` — 更新證據矩陣行
  - `useRisks(projectId)` — 取得風險列表
  - `useCreateRisk()` — 新增風險
  - `useUpdateRisk()` — 更新風險欄位（description / failure_mode / probability / severity / mitigation）
  - `useDeleteRisk()` — 刪除風險
  - `useExperiments(projectId)` — 取得實驗列表
  - `useCreateExperiment()` — 新增實驗
  - `useUpdateExperiment()` — 更新實驗（名稱 / 關聯假設 / 證據等級 / 方法 / 成功標準 / 狀態 / 結果）
  - `socraticGenerate({ project_id, mission, constraints })` — AI 黑帽質疑生成
  - `supabase.from('review_attachments')` — 附件 CRUD（select / insert / delete）
- **state_variables**:
  - `activeTab: string` — 當前 Tab（evidence / risk / experiment / attachments）
  - `dispositions: Record<string, string>` — 方案去向映射
  - `reviewConclusion: string` — 審查結論備註
  - `expModalOpen: boolean` — 實驗 Modal 開關
  - `editingExp: Experiment | null` — 編輯中的實驗物件
  - `aiLoading: Record<string, boolean>` — AI 各功能載入狀態（blackhat / risk / exp）
  - `attachments: any[]` — 附件列表
  - `blackhatQuestions: string[]` — AI 黑帽質疑列表
  - `isSubmitting: boolean` — 批准審查提交中
- **error_cases**:
  - API 載入失敗：顯示 AlertTriangle + 錯誤訊息 + 重新載入按鈕
  - AI 黑帽質疑失敗：降級使用預設質疑問題 + toast 警告
  - 實驗名稱 < 3 字元：toast 錯誤
  - Done 實驗結果 < 10 字元：toast 錯誤
  - 方案未全選去向：toast 錯誤阻止批准
  - Gate 3.1 未通過：toast 錯誤阻止批准

---

## [ACCEPTANCE CRITERIA]

- [ ] 頁面正確載入 solutions、evidenceMatrix、risks、experiments 四組資料
- [ ] 載入中顯示 Loader2 旋轉；載入失敗顯示錯誤訊息 + 重新載入按鈕
- [ ] 候選方案列表正確篩選通過 MUST 的方案並顯示 MUST icon 狀態
- [ ] 每方案可選擇去向（批准/修訂/淘汰），結論區正確彙總去向摘要
- [ ] AI 黑帽質疑按鈕呼叫 socraticGenerate 並顯示結果；失敗時降級顯示預設問題
- [ ] 證據缺口（E0/E1）時顯示 AI 證據缺口分析區塊 + 跳轉實驗 Tab 按鈕
- [ ] 證據矩陣 Desktop 為 heatmap 表格、Mobile 為卡片列表，正確標記 North Star KPI
- [ ] 風險登錄支援新增/編輯/刪除，P x S 矩陣正確著色，H/H* 風險無 mitigation 時行背景標紅
- [ ] 實驗支援新增/編輯（Modal），表單驗證（名稱 >= 3 字元、Done 結果 >= 10 字元）
- [ ] AI 識別風險與 AI 建議實驗按鈕正確觸發並更新資料
- [ ] 附件 Tab 支援上傳/下載/刪除（透過 AttachmentsPanel 元件）
- [ ] Gate 3.1 四項檢查正確計算：證據有實驗、H/H* 風險有 mitigation、North Star >= E2、無 E0
- [ ] Gate 3.1 全通過後啟用「進入 Decide」按鈕；未通過時 disabled + Tooltip
- [ ] 批准審查需 Gate 3.1 通過且所有方案已選去向，否則 toast 錯誤阻止
- [ ] 4 個 Tab 切換正常，Tab trigger 在 Mobile 文字縮小、icon 隱藏
