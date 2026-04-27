# Page-Level Prompt: TaskDefinition 任務定義 / Brief

> Phase 1 Define 的起點頁，結構化定義 Mission、硬約束、軟目標、非目標與 KPI，支援 AI 自動提取與建議，通過 Gate D1 可行性驗證後進入探索階段。

---

## [PAGE META]

- **page_name**: TaskDefinition
- **route_path**: `/projects/:id/brief`
- **page_type**: form
- **primary_goal**: 引導設計工程師完成結構化任務定義——上傳素材讓 AI 提取約束，定義 Mission Statement、硬約束、軟目標、非目標與 KPI，並通過約束可行性驗證 (Gate D1)
- **secondary_goal**: 透過 AI 改寫建議、約束建議與 KPI 建議降低人工填寫負擔，同時以 5W1H 自動產生任務摘要供團隊對齊
- **target_users**:
  - 主要：設計工程師（專案初始化時填寫）
  - 次要：專案主管（審閱 Gate D1 通過狀態）
- **entry_point**: 從 ProjectDashboard NavCard 點擊 "Brief" / Quick Stats 空狀態 CTA / URL 直接存取
- **expected_time_on_page**: 10 - 30 分鐘（首次完整填寫）；2 - 5 分鐘（後續修訂）

---

## [STRUCTURE: SECTIONS]

1. **page_header**
   - section_type: header
   - section_purpose: 返回按鈕、後端健康檢查狀態、儲存狀態指示、頁面標題與步驟說明

2. **section_intro**
   - section_type: intro_banner
   - section_purpose: SectionIntro 元件以簡短文字說明本頁流程

3. **backend_warning**
   - section_type: alert
   - section_purpose: 當後端不可用時顯示警告橫幅與重新檢查按鈕

4. **file_upload**
   - section_type: upload_zone
   - section_purpose: 多模態素材上傳區，支援拖放檔案並觸發 AI 提取

5. **ai_extraction**
   - section_type: ai_results
   - section_purpose: 顯示 AI 從上傳素材中提取的約束與假設，支援全部採納或逐項操作

6. **mission_statement**
   - section_type: text_input
   - section_purpose: 核心使命文字輸入區，含模板提示、字數統計與 AI 改寫建議

7. **hard_constraints**
   - section_type: table_input
   - section_purpose: 硬約束表格，支援手動新增與 AI 建議約束

8. **soft_objectives**
   - section_type: multi_item_input
   - section_purpose: 軟目標多項輸入，按 Enter 新增

9. **non_goals**
   - section_type: multi_item_input
   - section_purpose: 非目標多項輸入，明確定義不追求的範圍

10. **kpi_list**
    - section_type: table_input
    - section_purpose: 關鍵績效指標列表，支援手動新增與 AI 建議 KPI

11. **ai_5w1h**
    - section_type: ai_card
    - section_purpose: AITaskDefinitionCard 自動產生 5W1H 任務摘要

12. **feasibility_validation**
    - section_type: validation
    - section_purpose: 約束可行性驗證（Gate D1），檢查約束間衝突並可覆寫

13. **gate_checklist**
    - section_type: gate_check
    - section_purpose: Gate D1 Checklist 作為唯一出口，所有條件通過才可提交進入下一階段

---

## [SECTION COMPONENT SPEC]

### Section: page_header

- **layout**: flex row，左側返回按鈕，右側後端檢查按鈕 + 狀態 Badge + 儲存狀態；下方標題行含 phase 色條 + 標題 + HelpTooltip + 步驟描述
- **elements**:
  - back_button: Button(ghost) / required / `<ArrowLeft>` 圖標 + "返回 Dashboard"，導航至 `/projects/:id`
  - backend_check_btn: Button(outline) / required / `<RefreshCw>` 圖標 + "後端檢查"，觸發 `runBackendHealthCheck(true)`
  - backend_badge: Badge / required / 依 backendStatus 顯示 "Backend 正常"(default) / "Backend 異常"(destructive) / "Backend 檢查中"(secondary)
  - save_indicator: Span / conditional / saveStatus 為 saving 時顯示 "Saving..."；saved 時顯示 `<Check>` + "Saved"
  - phase_bar: Div / required / `h-8 w-1 rounded-full bg-phase-1` 相位色條
  - title: H1 / required / "任務定義" + HelpTooltip
  - subtitle: P / required / "D1 · 結構化定義 Mission、約束與 KPI，支援 AI 自動提取"
- **states**:
  - loading: 整頁替換為 Skeleton（標題 + 4 組輸入區骨架）
  - load_error: AlertCircle + "載入失敗" + 重試按鈕
  - backend_checking: RefreshCw 圖標旋轉動畫
- **copy_constraints**: 標題固定 "任務定義"；步驟編號 "D1"

### Section: file_upload

- **layout**: FileUploadZone 元件，拖放區域
- **elements**:
  - upload_zone: FileUploadZone / required / 傳入 files、onFilesChange、onExtract、isExtracting
- **states**:
  - empty: 顯示拖放提示
  - has_files: 顯示已上傳檔案列表
  - extracting: 載入指示器
- **copy_constraints**: 無特殊限制

### Section: ai_extraction

- **layout**: AIExtractionResults 元件，條件渲染（`showExtraction` 為 true 時顯示）
- **elements**:
  - results: AIExtractionResults / conditional / 傳入 items、onItemsChange、onAcceptAll、visible
- **states**:
  - hidden: visible=false 時不渲染
  - showing: 顯示提取項目列表，每項可個別接受/忽略，頂部有 "全部採納" 按鈕
- **copy_constraints**: 無特殊限制

### Section: mission_statement

- **layout**: Card 包裹，CardHeader 含標題 + 必填標記 + 模板提示；CardContent 含 Textarea + 字數統計 + AI 改寫按鈕 + 建議卡片
- **elements**:
  - title: CardTitle / required / "核心使命 (Mission Statement)" + 紅色星號
  - template_hint: P / required / 斜體模板文字 "在 [情境] 下，系統必須 [行為]，且 [指標] 不得超標"
  - textarea: Textarea / required / 4 行，placeholder 同模板，mission >= 10 字時左側綠色邊框
  - char_count: Span / required / 右對齊顯示字數
  - validation_hint: Span / conditional / mission 長度 1-9 字時顯示 "Mission 需至少 10 個字元"（紅色）
  - rewrite_btn: AiButton / conditional / mission >= 10 字且無 suggestion 時顯示 "改寫 Mission"
  - suggestion_card: AISuggestionCard / conditional / AI 改寫建議，含 "採用" / "跳過" 按鈕
  - evidence_refs: EvidenceRefsInline / conditional / 改寫建議的參考來源
- **states**:
  - empty: placeholder 顯示
  - valid: 左側 3px 綠色邊框
  - rewriting: AiButton loading 狀態
  - suggestion_shown: 顯示改寫建議卡片
- **copy_constraints**: Mission 最少 10 字元；模板格式固定

### Section: hard_constraints

- **layout**: Card 包裹，CardHeader 含標題 + 必填標記 + "建議約束" AI 按鈕；CardContent 含 ConstraintsTable + AI 建議列表
- **elements**:
  - title: CardTitle / required / "硬約束 (Hard Constraints)" + 紅色星號
  - suggest_btn: AiButton / required / "建議約束"，觸發 `handleConstraintSuggest`
  - table: ConstraintsTable / required / 傳入 constraints、onChange、onRemove
  - suggestion_cards: AISuggestionCard[] / conditional / 每張建議含描述 + 來源 + 理由 + "採用" / "跳過"
  - evidence_refs: EvidenceRefsInline / conditional / 建議的參考來源
  - close_btn: Button(ghost) / conditional / "關閉建議"
- **states**:
  - default: 表格顯示現有約束
  - suggesting: 載入中建議卡片
  - suggestions_shown: 建議列表展開
  - adopting: 單張建議卡片 loading（其餘 disabled）
- **copy_constraints**: 無特殊限制

### Section: soft_objectives

- **layout**: Card 包裹，CardHeader 含標題 + 說明文字；CardContent 含 MultiItemInput
- **elements**:
  - title: CardTitle / required / "軟目標 (Soft Objectives)"
  - description: P / required / "可權衡的目標，如效能提升、重量輕量化"
  - input: MultiItemInput / required / placeholder "輸入軟目標，按 Enter 新增"
- **states**:
  - default: 已輸入項目列表 + 輸入框
  - empty: 僅輸入框
- **copy_constraints**: 無特殊限制

### Section: non_goals

- **layout**: Card 包裹，CardHeader 含標題 + 說明文字；CardContent 含 MultiItemInput
- **elements**:
  - title: CardTitle / required / "非目標 (Non-Goals)"
  - description: P / required / "明確定義本版專案不追求的範圍，避免範圍蔓延"
  - input: MultiItemInput / required / placeholder "輸入非目標，按 Enter 新增"
- **states**:
  - default: 已輸入項目列表 + 輸入框
  - empty: 僅輸入框
- **copy_constraints**: 無特殊限制

### Section: kpi_list

- **layout**: Card 包裹，CardHeader 含標題 + 必填標記 + "建議 KPI" AI 按鈕；CardContent 含 KpiList + AI 建議列表
- **elements**:
  - title: CardTitle / required / "關鍵績效指標 (Critical KPIs)" + 紅色星號
  - suggest_btn: AiButton / required / "建議 KPI"，觸發 `handleKpiSuggest`
  - list: KpiList / required / 傳入 kpis、onChange、onRemove
  - suggestion_cards: AISuggestionCard[] / conditional / 每張建議含 kpi_name、target_value、unit、measurement_method、rationale + "採用" / "跳過"
  - evidence_refs: EvidenceRefsInline / conditional / 建議的參考來源
  - close_btn: Button(ghost) / conditional / "關閉建議"
- **states**:
  - default: KPI 列表
  - suggesting: 載入中建議卡片
  - suggestions_shown: 建議列表展開
  - adopting: 單張建議卡片 loading（其餘 disabled）
- **copy_constraints**: 無特殊限制

### Section: ai_5w1h

- **layout**: AITaskDefinitionCard 元件
- **elements**:
  - card: AITaskDefinitionCard / required / 傳入 data（5W1H 資料）、missionReady、onRegenerate
- **states**:
  - disabled: mission 未就緒時無法觸發
  - generated: 顯示 5W1H 分析結果
  - regenerating: 載入狀態
- **copy_constraints**: 由 AI 產生，無硬性限制

### Section: feasibility_validation

- **layout**: FeasibilityValidation 元件
- **elements**:
  - validation: FeasibilityValidation / required / 傳入 status、conflicts、stale、onCheck、onOverride
- **states**:
  - unchecked: 尚未執行檢查
  - checking: 執行中
  - pass: 無衝突
  - fail: 列出衝突項目，可 override
  - stale: 約束變更後需重新檢查
- **copy_constraints**: 衝突描述由 AI 產生

### Section: gate_checklist

- **layout**: GateChecklist 元件，作為頁面唯一出口
- **elements**:
  - checklist: GateChecklist / required / 傳入 items（Gate D1 條件列表）、onNavigateNext、isSubmitting
- **states**:
  - incomplete: 部分條件未通過，提交按鈕 disabled
  - complete: 所有條件通過，提交按鈕可點擊
  - submitting: 提交中 loading 狀態
- **copy_constraints**: Gate 條件文案由 useTaskDefinitionForm 定義

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. **頁面載入** → `useTaskDefinitionForm(id)` 初始化，載入 brief / constraints / kpis 等既有資料 → Loading skeleton → 資料就緒後渲染表單
2. **檔案上傳** → 拖放或選擇檔案 → 點擊提取 → AI 分析上傳素材 → AIExtractionResults 顯示提取項目 → 可逐項或全部採納至約束 / KPI
3. **Mission 填寫** → 輸入 >= 10 字 → 左側綠色邊框 → 可觸發 "改寫 Mission" → AI 產生建議 → 採用或跳過
4. **硬約束編輯** → 手動在表格新增 / 編輯 / 刪除 → 或觸發 "建議約束" → AI 產生建議卡片 → 逐張採用或跳過
5. **KPI 編輯** → 手動在列表新增 / 編輯 / 刪除 → 或觸發 "建議 KPI" → AI 產生建議卡片 → 逐張採用或跳過
6. **5W1H 產生** → Mission 就緒後可觸發 → AI 自動產生 5W1H 摘要
7. **可行性驗證** → 點擊檢查 → AI 分析約束間衝突 → 通過或列出衝突（可 override）
8. **Gate D1 提交** → 所有 Gate 條件通過 → 點擊提交 → 導航至 Explore 頁面
9. **自動儲存** → 表單變更時自動 debounce 儲存至後端

### RWD 行為差異

- **Desktop**: 表單寬度受 `page-shell-narrow` 約束（max-width ~720px），居中排列
- **Tablet**: 同 Desktop 佈局
- **Mobile**: 單欄全寬，AI 建議卡片堆疊顯示

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useTaskDefinitionForm(id)` — 自定義 hook，統一管理所有表單狀態與 API 互動，包含：
    - Brief CRUD（mission, constraints, softObjectives, nonGoals, kpis）
    - 檔案上傳提取 API（`handleExtract`）
    - Mission AI 改寫 API（`handleMissionRewrite`）
    - 約束建議 API（`handleConstraintSuggest`）
    - KPI 建議 API（`handleKpiSuggest`）
    - 5W1H 產生 API（`handleRegenerate5W1H`）
    - 可行性檢查 API（`handleFeasibilityCheck`）
    - 後端健康檢查（`runBackendHealthCheck`）
    - Gate 提交（`handleSubmit`）
- **state** (managed by useTaskDefinitionForm):
  - `mission: string` — Mission 文字
  - `constraints: Constraint[]` — 硬約束列表
  - `softObjectives: string[]` — 軟目標
  - `nonGoals: string[]` — 非目標
  - `kpis: Kpi[]` — KPI 列表
  - `uploadedFiles: File[]` — 已上傳檔案
  - `extractedItems: ExtractedItem[]` — AI 提取項目
  - `showExtraction: boolean` — 是否顯示提取結果
  - `missionSuggestion: string` — AI 改寫建議文字
  - `showMissionSuggestion: boolean` — 是否顯示改寫建議
  - `constraintSuggestionList: ConstraintSuggestion[]` — AI 約束建議列表
  - `showConstraintSuggestions: boolean` — 是否顯示約束建議
  - `kpiSuggestionList: KpiSuggestion[]` — AI KPI 建議列表
  - `showKpiSuggestions: boolean` — 是否顯示 KPI 建議
  - `taskDef5W1H: TaskDef5W1H` — 5W1H 資料
  - `feasibilityStatus: string` — 可行性檢查狀態
  - `feasibilityConflicts: Conflict[]` — 可行性衝突列表
  - `backendStatus: 'ok' | 'down' | 'checking'` — 後端狀態
  - `saveStatus: 'idle' | 'saving' | 'saved'` — 儲存狀態
  - `isSubmitting: boolean` — 提交中狀態
  - `gateItems: GateCheckItem[]` — Gate D1 條件列表
- **error_cases**:
  - 頁面載入失敗 → AlertCircle + "載入失敗" + 重試按鈕
  - 後端不可用 → 頂部紅色警告橫幅 + 重新檢查按鈕；AI 功能無法使用
  - AI 建議 API 失敗 → AISuggestionCard 顯示錯誤狀態
  - 可行性檢查失敗 → 顯示衝突列表，可 override 跳過
  - 提交失敗 → isSubmitting 重設，toast 錯誤訊息

---

## [ACCEPTANCE CRITERIA]

- [ ] 頁面載入時正確從後端還原既有 brief 資料（mission、constraints、kpis 等）
- [ ] Loading 狀態顯示 Skeleton 佔位符
- [ ] 載入失敗顯示錯誤頁面與重試按鈕
- [ ] 後端健康檢查按鈕可手動觸發，狀態 Badge 即時反映結果
- [ ] 後端不可用時頂部顯示紅色警告橫幅
- [ ] FileUploadZone 支援拖放與檔案選擇，觸發 AI 提取
- [ ] AIExtractionResults 顯示提取項目，支援逐項接受與全部採納
- [ ] Mission textarea 輸入 >= 10 字時顯示綠色左邊框
- [ ] Mission < 10 字時顯示紅色驗證提示
- [ ] AI 改寫 Mission 按鈕正確觸發且建議卡片可採用 / 跳過
- [ ] 硬約束表格支援新增 / 編輯 / 刪除行
- [ ] AI 約束建議可逐張採用（寫入表格）或跳過，採用中其餘按鈕 disabled
- [ ] 軟目標與非目標 MultiItemInput 按 Enter 新增、可刪除
- [ ] KPI 列表支援新增 / 編輯 / 刪除
- [ ] AI KPI 建議可逐張採用或跳過
- [ ] 5W1H 卡片在 Mission 就緒後可觸發產生
- [ ] 約束可行性驗證正確執行並顯示衝突或通過狀態
- [ ] 約束變更後可行性狀態標記為 stale
- [ ] Gate D1 Checklist 所有條件通過才可提交
- [ ] 提交成功後導航至下一頁面
- [ ] 表單變更自動儲存，儲存狀態指示器正確切換 Saving / Saved
