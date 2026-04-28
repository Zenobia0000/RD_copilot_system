# Page-Level Prompt: 假設台帳

## [PAGE META]
- **page_name**: 假設台帳
- **route_path**: `/projects/:id/assumption-ledger`
- **page_type**: 列表/表單
  <!-- landing / form / dashboard / report / search / detail / settings -->
- **primary_goal**: 管理專案設計過程中的所有假設，透過因果迴路圖 (Causal Loop Diagram) 視覺化假設與系統行為的關聯，並以結構化驗證規劃工作流追蹤驗證進度。
- **secondary_goal**: 建立假設 ↔ 矛盾 ↔ 收斂圖的完整可追溯鏈。部分假設可由 AI 自動從上傳的多模態素材中提取 (PRD F1.7)，標記來源以利追溯。蘇格拉底七類提問中的「因果追問」與「假設挑戰」結果自動回饋至本頁。

## [USER CONTEXT]
- **target_user_segment**:
  - 主要：RD 工程師, RD 主管
  - 次要：專案經理 (PM)
- **entry_point**:
  - 從「矛盾識別頁面」完成後自動導航，或從「專案儀表板」點擊導航進入。
  <!-- 使用者從哪裡進入此頁？哪個按鈕 / 哪個前一頁 -->
- **expected_time_on_page**: 長 (10-20 分鐘)
  <!-- 粗估停留時間，幫助決定資訊密度 -->

## [STRUCTURE: SECTIONS]
<!-- 以 top-down 順序列出所有區塊 -->

1. **假設列表展示區**
   - section_type: table/list
   - section_purpose: 以表格形式展示所有假設，包含編號、內容、依據來源、驗證狀態、關聯矛盾等。

2. **因果迴路圖區 (Causal Loop Diagram)**
   - section_type: interactive-diagram
   - section_purpose: 視覺化假設之間以及假設與系統行為的因果關係。節點為假設/變量，邊為正反饋 (+) 或負反饋 (−) 關係。支持 Step 3 系統建模，協助識別隱藏的循環依賴與槓桿點。

3. **假設詳情編輯區**
   - section_type: form/detail
   - section_purpose: 顯示單一假設的詳細信息，並提供編輯、規劃驗證的表單。

4. **驗證規劃工作流區 (Verification Planning)**
   - section_type: workflow/kanban
   - section_purpose: 將驗證工作從「純欄位」升級為結構化工作流。包含驗證方法選擇、資源/成本估算、時程排序、與專案時間線對齊。依據「若錯了最壞後果」自動排序驗證優先級。

5. **矛盾追溯面板 (Contradiction Traceability)**
   - section_type: panel/sidebar
   - section_purpose: 顯示當前假設與矛盾識別 (Step 2)、矛盾收斂圖 (Step 5a-6) 的關聯。當假設被推翻時，自動標記受影響的矛盾與解法路線，觸發收斂圖重新掃描。

## [SECTION COMPONENT SPEC]
<!-- 每個 section 各寫一段 -->

### Section: 假設列表展示區
- **layout**: 響應式表格佈局，支持排序和分頁。
  <!-- 單欄 / 左右雙欄 / 卡片網格 / 時間軸 ... -->
- **elements**:
  - `假設表格`: `table`, `required`, `每列顯示假設編號、內容、依據來源（含 AI 提取來源標記）、若錯了最壞後果、最小驗證方法、驗證成本/週期、狀態、操作按鈕。AI 自動提取的假設以特殊標籤區分。`
  - `新增假設按鈕`: `button (primary)`, `required`, `點擊後打開假設詳情編輯區以新增假設。`
- **states**:
  - 正常：假設列表正常顯示。
  - loading：顯示骨架屏。
  - empty：無假設時顯示「沒有假設」提示。
  - error：數據載入失敗時顯示錯誤提示。
- **copy_constraints**:
  - 假設內容: 最長 300 個字元。

### Section: 因果迴路圖區
- **layout**: 可縮放、可平移的互動式圖表，佔頁面上方或右側面板。
- **elements**:
  - `因果迴路圖 (CLD)`: `interactive-graph`, `required`, `節點 = 假設/系統變量，邊 = 因果關係 (+正反饋 / −負反饋)。點擊節點高亮相關假設。支持拖拽新增節點與連線。`
  - `迴路偵測指示器`: `badge-list`, `required`, `自動偵測並標記正反饋迴路 (增強迴路 R) 與負反饋迴路 (平衡迴路 B)，高亮潛在的系統不穩定因素。`
  - `槓桿點標記`: `highlight`, `optional`, `AI 自動識別並標記高影響力節點（改變此假設會影響最多其他假設的節點），以醒目色 (Accent) 標記。`
  - `匯出圖表`: `button`, `optional`, `匯出 CLD 為 PNG/SVG 供報告使用。`
- **states**:
  - 正常：圖表顯示所有假設與關聯。
  - empty：無假設時顯示空白畫布，提示「新增假設以開始建模」。
  - highlight：選中節點時，關聯假設在列表中高亮。
- **copy_constraints**:
  - 節點標籤最長 60 字元，邊標籤最長 30 字元。

### Section: 假設詳情編輯區
- **layout**: 模態框 (Modal) 或側邊抽屜 (Drawer) 中的表單佈局。
- **elements**:
  - `假設內容`: `textarea`, `required`, `輸入/顯示假設的詳細描述。`
  - `依據來源`: `input (text)`, `required`, `輸入假設的依據文獻或來源 ID。含 AI 提取來源標籤（若來自多模態素材）。`
  - `若錯了最壞後果`: `textarea`, `required`, `輸入若假設錯誤可能導致的最壞結果。`
  - `影響範圍`: `tag-select`, `required`, `選擇此假設影響的系統模塊/矛盾（從矛盾識別中引用），用於建立追溯鏈。`
  - `因果關聯`: `relation-picker`, `optional`, `選擇此假設在因果迴路圖中的上游/下游節點及關係類型 (+/−)。`
  - `保存/取消按鈕`: `button group`, `required`, `保存編輯或取消操作。`
- **states**:
  - 正常：表單可用。
  - loading：提交中顯示 Loading Spinner。
  - error：驗證失敗時顯示錯誤提示。
- **copy_constraints**:
  - 所有字段皆為必填（因果關聯除外），且有相應的長度限制。

### Section: 驗證規劃工作流區
- **layout**: Kanban 看板或時間線視圖，可切換。
- **elements**:
  - `驗證看板`: `kanban-board`, `required`, `四欄：待規劃 → 待驗證 → 驗證中 → 已完成/已推翻。假設卡片可拖拽移動。`
  - `驗證方法選擇`: `select`, `required`, `下拉選項：仿真分析 / 原型測試 / 專家審查 / 文獻引用 / 實測驗證 / 其他。`
  - `資源估算`: `form-group`, `required`, `包含：預估成本 (數值+單位)、預估週期 (天數)、所需設備/人力。`
  - `時程對齊`: `timeline-bar`, `required`, `與專案時間線對齊顯示，標記驗證截止日期、與 Gate P 的關聯。`
  - `優先級排序`: `auto-sort`, `required`, `依據「若錯了最壞後果」嚴重度自動排序：影響 MUST 條件者最高優先、影響 WANT >20% 者次之。`
- **states**:
  - 正常：看板/時間線正常顯示。
  - overdue：超過預定驗證時間的假設卡片標紅。
  - blocked：驗證資源不足或依賴其他驗證結果時標橙。

### Section: 矛盾追溯面板
- **layout**: 右側固定面板或底部抽屜，選中假設時展開。
- **elements**:
  - `關聯矛盾列表`: `linked-list`, `required`, `顯示該假設關聯的所有矛盾 (來自 Step 2 矛盾識別)，含矛盾嚴重度標籤 (Fatal/Major/Minor)。點擊可跳轉至矛盾識別頁。`
  - `收斂圖影響`: `impact-indicator`, `required`, `當假設被推翻時，顯示收斂圖中受影響的解法路線數量與嚴重度。觸發時顯示「此假設推翻將影響 N 條解法路線，建議重新掃描收斂圖」警告。`
  - `蘇格拉底回饋`: `feedback-list`, `optional`, `顯示來自 Step 2 七類提問中「因果追問」和「假設挑戰」的 AI 回饋結論，作為假設驗證的輔助依據。`
- **states**:
  - collapsed：未選中假設時收合。
  - expanded：選中假設時展開，顯示關聯資訊。
  - alert：假設被推翻且有關聯矛盾時，面板以 Error 色標記。

## [INTERACTION & STATE FLOW]
- **主要互動流程**：
  1. 用戶進入假設台帳頁面，系統載入所有假設（包含 AI 從多模態素材中自動提取的假設，以 `AI 提取` 標籤標記來源）+ 因果迴路圖 + 驗證看板。
  2. 用戶在因果迴路圖上查看假設間的因果關係，識別增強迴路 (R)、平衡迴路 (B)、槓桿點。可拖拽新增節點與連線。
  3. 用戶可點擊「新增假設」或編輯既有假設，在詳情編輯區填寫內容、影響範圍、因果關聯。
  4. 保存假設後，因果迴路圖自動更新，矛盾追溯面板顯示關聯矛盾與收斂圖影響。
  5. 用戶在驗證規劃看板中安排驗證工作：選擇驗證方法、估算資源、對齊時程。系統依「最壞後果」嚴重度自動排序優先級。
  6. 用戶拖拽假設卡片更新驗證狀態（待規劃 → 待驗證 → 驗證中 → 已完成/已推翻）。
  7. 當假設被推翻時，系統自動標記受影響的矛盾，並提示「建議重新掃描矛盾收斂圖」。

- **表單驗證規則**（如適用）：
  - `假設內容`: 必填，最少 10 字元 → 假設內容為必填項，且需至少 10 個字元。
  - `依據來源`: 必填 → 依據來源為必填項。
  - `驗證成本/週期`: 必填，且需為有效數值或描述 → 驗證成本/週期格式不正確。

- **資料更新策略**：
  - 新增/編輯假設後，列表數據將自動刷新。
  - 假設狀態更新後，列表數據將自動刷新。

- **RWD 行為差異**：
  - Desktop (>1024px): 表格和詳情編輯區可並排顯示，或編輯區以模態框形式展示。
  - Tablet (768px - 1023px): 表格列可能壓縮，詳情編輯區以全屏模態框或側邊抽屜形式顯示。
  - Mobile (<768px): 表格轉換為列表卡片式顯示，詳情編輯區為全屏模態框。

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  - GET `/api/projects/:id/assumptions` — 獲取指定專案的假設列表。
  - POST `/api/projects/:id/assumptions` — 創建新假設。
  - PUT `/api/projects/:id/assumptions/:assumption_id` — 更新假設信息。
  - GET `/api/projects/:id/assumptions/causal-loop` — 獲取因果迴路圖數據（節點、邊、迴路標記）。
  - PUT `/api/projects/:id/assumptions/causal-loop` — 更新因果迴路圖（新增/刪除節點與邊）。
  - GET `/api/projects/:id/assumptions/:assumption_id/contradictions` — 獲取假設關聯的矛盾列表。
  - POST `/api/projects/:id/assumptions/:assumption_id/verification-plan` — 創建/更新驗證計劃（方法、資源、時程）。
  - GET `/api/projects/:id/assumptions/verification-timeline` — 獲取驗證時程總覽（含與 Gate P 對齊資訊）。
- **error cases**:
  - API 載入或提交失敗: 頁面顯示錯誤提示訊息，提供重試按鈕。
  - 假設列表為空: 顯示「沒有假設」提示，並引導新增假設。
  - 因果迴路圖存在循環依賴: 系統標記迴路並提示用戶檢視是否為合理的反饋迴路。
  - 假設推翻後收斂圖受影響: 彈出警告，列出受影響的矛盾數量與嚴重度，提供「跳轉至矛盾收斂圖」按鈕。

## [EXCEPTION TO GLOBAL RULES]
<!-- 如果這一頁要刻意違反 Global 規範，必須在這裡寫明並說明原因 -->
- 無特殊例外，完全遵循 Global System Prompt 規範。

## [ACCEPTANCE CRITERIA]
- [x] 假設列表能正確顯示所有假設，包含詳細屬性（內容、依據來源、影響範圍、最壞後果、驗證狀態）。AI 提取的假設以標籤區分。
- [x] 能順利新增、編輯假設，包含影響範圍與因果關聯的設定。
- [x] 因果迴路圖能正確視覺化假設間的因果關係，支持拖拽新增節點/連線，自動偵測增強迴路 (R) 與平衡迴路 (B)。
- [x] 驗證規劃工作流完整：支持驗證方法選擇、資源估算、時程排序，並依「最壞後果」自動排序優先級。
- [x] 驗證看板 (Kanban) 支持拖拽更新假設驗證狀態（待規劃 → 待驗證 → 驗證中 → 已完成/已推翻）。
- [x] 矛盾追溯面板正確顯示假設關聯的矛盾及嚴重度 (Fatal/Major/Minor)，點擊可跳轉至矛盾識別頁。
- [x] 假設被推翻時，系統自動標記受影響的收斂圖解法路線，並提示重新掃描。
- [x] 蘇格拉底七類提問中「因果追問」和「假設挑戰」的 AI 回饋能正確顯示在追溯面板。
- [x] 響應式設計在不同設備上顯示良好，因果迴路圖在移動端可縮放查看。
