# Page-Level Prompt: 任務定義頁面

## [PAGE META]
- **page_name**: 任務定義頁面
- **route_path**: `/projects/:id/task-definition`
- **page_type**: 功能/表單
  <!-- landing / form / dashboard / report / search / detail / settings -->
- **primary_goal**: 協助用戶透過多模態素材上傳與 AI 自動提取，結構化地定義新專案的需求、約束與目標，並通過約束可行性驗證 (Gate 1)。
- **secondary_goal**: 識別關鍵 KPI，為後續決策提供依據。支援 AI 自動從上傳素材中提取約束與假設。

## [USER CONTEXT]
- **target_user_segment**:
  - 主要：RD 工程師
  - 次要：RD 主管, 專案經理 (PM)
- **entry_point**:
  - 從「專案儀表板」點擊「定義任務」按鈕進入，或從專案創建後的導引流程進入。
  <!-- 使用者從哪裡進入此頁？哪個按鈕 / 哪個前一頁 -->
- **expected_time_on_page**: 中 (5-15 分鐘)
  <!-- 粗估停留時間，幫助決定資訊密度 -->

## [STRUCTURE: SECTIONS]
<!-- 以 top-down 順序列出所有區塊 -->

1. **多模態素材上傳區塊**
   - section_type: upload/form
   - section_purpose: 讓用戶上傳 PDF、圖片、Excel、規格書等多模態素材，AI 自動提取約束、假設與數據 (PRD F1.7)。

2. **AI 提取結果展示區塊**
   - section_type: summary/review
   - section_purpose: 展示 AI 從上傳素材中自動提取的約束條件、假設、數據，供用戶確認或修改。

3. **約束可行性驗證區塊 (Gate 1)**
   - section_type: validation/report
   - section_purpose: AI 驗證約束組合的物理可行性 (PRD F1.8)，顯示驗證結果 (通過/衝突/警告)，攔截不可能的約束組合。

4. **任務定義表單區塊**
   - section_type: form
   <!-- hero / summary / list / form / faq / footer / stats / tabs ... -->
   - section_purpose: 讓用戶輸入或確認專案的核心使命、硬約束、軟目標和非目標，並定義關鍵衡量指標。表單可預填 AI 提取結果。

## [SECTION COMPONENT SPEC]
<!-- 每個 section 各寫一段 -->

### Section: 多模態素材上傳區塊
- **layout**: 單欄響應式佈局，拖放上傳區域 + 已上傳檔案列表。
- **elements**:
  - `拖放上傳區域`: `dropzone`, `required`, `支援 PDF、圖片 (JPG/PNG)、Excel (XLSX)、規格書等檔案上傳，支援多檔案同時上傳。最大 20MB/檔案。`
  - `已上傳檔案列表`: `list`, `required`, `顯示已上傳檔案的名稱、類型、大小、上傳狀態 (上傳中/完成/失敗)，支援刪除操作。`
  - `開始 AI 提取按鈕`: `button (primary)`, `required`, `上傳完成後，觸發 AI 自動提取約束/假設/數據。`
- **states**:
  - 正常：拖放區域顯示提示文字。
  - hover：拖放區域邊框高亮。
  - loading：AI 提取進行中，顯示進度條與 Loading 動畫。
  - error：檔案格式不支援或超過大小限制時顯示錯誤提示。
  - success：上傳成功，檔案列表更新。

### Section: AI 提取結果展示區塊
- **layout**: 卡片式佈局，分類展示提取結果 (約束、假設、數據)。
- **elements**:
  - `提取約束列表`: `editable list`, `required`, `顯示 AI 從素材中提取的硬約束/軟目標，每條可編輯、刪除或確認。標記來源檔案。`
  - `提取假設列表`: `editable list`, `optional`, `顯示 AI 推斷的假設，每條可編輯、刪除或確認。`
  - `提取數據摘要`: `card`, `optional`, `顯示 AI 提取的關鍵數值與參數。`
  - `全部接受按鈕`: `button (primary)`, `optional`, `一鍵接受所有 AI 提取結果，填入任務定義表單。`
  - `逐條審查模式`: `toggle`, `optional`, `切換至逐條確認模式。`
- **states**:
  - 正常：提取結果正常顯示。
  - empty：AI 未提取到有效內容時顯示提示。
  - loading：AI 正在處理中。

### Section: 約束可行性驗證區塊 (Gate 1)
- **layout**: 報告式佈局，頂部為總體驗證結果，下方為詳細分析。
- **elements**:
  - `驗證結果摘要`: `badge/card`, `required`, `顯示總體結果：✅ 通過 / ⚠️ 警告 / ❌ 衝突。`
  - `衝突詳情列表`: `list`, `conditional`, `當存在約束衝突時，列出衝突的約束組合與物理原因說明。`
  - `AI 建議修正方案`: `card`, `conditional`, `當約束衝突時，AI 提供可能的修正建議。`
  - `覆寫確認按鈕`: `button (warning)`, `optional`, `用戶確認了解衝突風險後，可選擇覆寫繼續 (需填寫覆寫原因)。`
- **states**:
  - pass：所有約束通過可行性驗證，顯示綠色通過標記。
  - warning：部分約束組合存在風險，顯示橙色警告與建議。
  - conflict：約束組合物理不可行，顯示紅色衝突，阻止進入下一步直到解決或覆寫。
  - loading：AI 正在驗證中。

### Section: 任務定義表單區塊
- **layout**: 單欄響應式表單佈局，各輸入框垂直排列，底部為操作按鈕組。
  <!-- 單欄 / 左右雙欄 / 卡片網格 / 時間軸 ... -->
- **elements**:
  - `Mission (核心使命)`: `textarea`, `required`, `輸入專案的核心使命與目標，支持多行輸入。`
  - `Hard Constraints (硬約束)`: `textarea`, `optional`, `輸入專案必須遵守的不可妥協的限制，如成本上限、尺寸限制、法規要求。`
  - `Soft Objectives (軟目標)`: `textarea`, `optional`, `輸入專案希望達成但可權衡的目標，如效能提升、重量輕量化、噪音降低。`
  - `Non-Goals (非目標)`: `textarea`, `optional`, `明確定義本版專案不追求的功能或範圍，以避免範圍蔓延。`
  - `三個最不能失敗指標 (Critical KPIs)`: `kpi-input-list (自定義組件)`, `required`, `可動態新增/刪除關鍵指標，每個指標包含名稱、目標值和衡量方式。`
  - `確認任務定義按鈕`: `button`, `required`, `提交表單內容，保存任務定義並進入下一階段。`
  - `取消按鈕`: `button`, `optional`, `放棄當前操作，返回專案儀表板。`
- **states**:
  - 正常：所有輸入框為空或已填寫。
  - hover：操作按鈕有背景色加深效果或輕微陰影。
  - loading：提交按鈕顯示 Loading Spinner，表單處於禁用狀態，防止重複提交。
  - empty：文本框顯示 Placeholder 提示，引導用戶輸入。
  - error：輸入驗證失敗的字段下方顯示紅色錯誤提示文字，表單按鈕禁用。
- **copy_constraints**:
  - Mission: 最少 10 個字元，最多 500 字元。
  - Hard Constraints / Soft Objectives / Non-Goals: 每條限制最少 5 個字元，最多 200 字元，支持多條輸入。
  - Critical KPIs: 每個指標名稱最少 3 個字元，目標值和衡量方式必填。

## [INTERACTION & STATE FLOW]
- **主要互動流程**：
  1. 用戶進入頁面，系統載入專案現有任務定義數據（如有），並顯示在表單中。
  2. 用戶上傳多模態素材 (PDF/圖片/Excel/規格書) 至拖放上傳區域。
  3. 上傳完成後，用戶點擊「開始 AI 提取」，AI 自動提取約束、假設與數據，結果展示於 AI 提取結果展示區塊。
  4. 用戶審查 AI 提取結果，可逐條確認/編輯/刪除，或一鍵全部接受。接受的內容自動填入任務定義表單。
  5. 用戶填寫或修改表單內容，系統即時進行前端驗證，並顯示錯誤提示（若有）。
  6. 用戶點擊「確認任務定義」按鈕，系統觸發約束可行性驗證 (Gate 1)。AI 驗證約束組合的物理可行性。
  7. Gate 1 通過：數據提交至後端，導航至「矛盾識別」頁面。Gate 1 衝突：顯示衝突詳情與 AI 建議修正方案，用戶需修正約束或覆寫確認後方可繼續。

- **表單驗證規則**（如適用）：
  - `Mission`: 必填，最少 10 字元 → 核心使命為必填項，且需至少 10 個字元。
  - `Critical KPIs`: 至少一個 KPI，每個 KPI 需有名稱、目標值和衡量方式 → 請至少定義一個關鍵指標，並確保其名稱、目標值和衡量方式皆已填寫。

- **資料更新策略**：
  - 提交成功後，本地狀態更新，並通過 React Query 或類似機制使相關專案數據重新請求或失效。

- **RWD 行為差異**：
  - Desktop (>1024px): 完整表單顯示，各字段清晰可見，可考慮彈性佈局或輔助信息側邊顯示。
  - Tablet (768px - 1023px): 表單字段可能從多欄佈局變為單欄堆疊，確保在較小螢幕寬度下仍有良好可讀性。
  - Mobile (<768px): 單欄佈局，所有表單元素垂直堆疊，文字大小和間距調整以適應最小支援寬度。

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  - GET `/api/projects/:id/constraints` — 獲取指定專案的任務定義數據。
  - PUT `/api/projects/:id/constraints` — 更新指定專案的任務定義數據。
  - POST `/api/projects/:id/sources` — 上傳多模態素材 (PDF/圖片/Excel/規格書)，支援 multipart/form-data。
  - GET `/api/projects/:id/sources` — 獲取已上傳素材列表。
  - DELETE `/api/projects/:id/sources/:source_id` — 刪除已上傳素材。
  - POST `/api/projects/:id/sources/extract` — 觸發 AI 自動提取約束/假設/數據。
  - GET `/api/projects/:id/sources/extraction-results` — 獲取 AI 提取結果。
  - POST `/api/projects/:id/constraints/feasibility-check` — 觸發約束可行性驗證 (Gate 1)。
- **error cases**:
  - API 數據載入失敗: 頁面顯示錯誤提示訊息，並提供重試按鈕。
  - 表單提交失敗 (例如 400 Bad Request, 422 Unprocessable Entity): 顯示後端返回的字段級錯誤訊息，或彈出通用錯誤提示。
  - 檔案上傳失敗: 顯示失敗檔案名稱與原因 (格式不支援/超過大小限制)，支援重試。
  - AI 提取失敗: 顯示錯誤提示，用戶可手動填寫表單或重試提取。
  - 約束可行性驗證失敗 (Gate 1): 顯示衝突約束組合詳情與物理原因，提供 AI 建議修正方案。

## [EXCEPTION TO GLOBAL RULES]
<!-- 如果這一頁要刻意違反 Global 規範，必須在這裡寫明並說明原因 -->
- 無特殊例外，完全遵循 Global System Prompt 規範。

## [ACCEPTANCE CRITERIA]
- [x] 多模態素材上傳區支援 PDF/圖片/Excel/規格書，可拖放或點選上傳，顯示上傳進度與狀態。
- [x] AI 提取功能可從上傳素材中自動提取約束/假設/數據，結果可逐條審查、編輯或一鍵接受。
- [x] 約束可行性驗證 (Gate 1) 可正確識別不可行的約束組合，並顯示衝突原因與 AI 建議修正方案。
- [x] 任務定義表單所有必填欄位可正常填寫與提交，支援 AI 提取結果自動預填。
- [x] 「三個最不能失敗指標」可新增、編輯、刪除，並能設定其判斷方式。
- [x] 提交後數據能正確保存並更新專案狀態，並正確導航至假設台帳頁面。
