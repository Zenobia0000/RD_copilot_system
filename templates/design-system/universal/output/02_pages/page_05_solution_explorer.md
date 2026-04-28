# Page-Level Prompt: 方案探索

## [PAGE META]
- **page_name**: 方案探索
- **route_path**: `/projects/:id/solution-explorer`
- **page_type**: 列表/詳情/工具
  <!-- landing / form / dashboard / report / search / detail / settings -->
- **primary_goal**: 協助用戶基於已識別的矛盾，生成、篩選和評估多個設計方案，並透過 Contradiction Convergence Graph (DAG) 追蹤二次矛盾直至完全收斂。
- **secondary_goal**: 記錄方案的機制、假設、風險、最小驗證，進行 MUST 快篩，並監控架構健康度（Architecture Health Monitor）。

## [USER CONTEXT]
- **target_user_segment**:
  - 主要：RD 工程師
  - 次要：RD 主管
- **entry_point**:
  - 從「矛盾識別頁面」完成後自動導航，或從「專案儀表板」點擊導航進入。
  <!-- 使用者從哪裡進入此頁？哪個按鈕 / 哪個前一頁 -->
- **expected_time_on_page**: 長 (20-40 分鐘)
  <!-- 粗估停留時間，幫助決定資訊密度 -->

## [STRUCTURE: SECTIONS]
<!-- 以 top-down 順序列出所有區塊 -->

1. **矛盾選擇與方案生成區**
   - section_type: form/action
   <!-- hero / summary / list / form / faq / footer / stats / tabs ... -->
   - section_purpose: 選擇矛盾作為輸入，觸發 AI 生成初始方案集。

2. **Contradiction Convergence Graph 視覺化區**
   - section_type: visualization/dashboard
   - section_purpose: 以 DAG（有向無環圖）展示矛盾→方案→二次矛盾的收斂追蹤圖，顯示每個矛盾的嚴重度分類（Fatal/Major/Minor）和收斂狀態。

3. **Architecture Health Monitor 面板**
   - section_type: status/monitor
   - section_purpose: 監控矛盾圖的健康狀態，以交通燈（綠/黃/紅）顯示節點數量警示，並提供強制動作觸發。

4. **方案列表與篩選區**
   - section_type: list/filter
   - section_purpose: 展示 AI 生成的方案集，支持查看詳情和 MUST 快篩，顯示矛盾嚴重度標籤。

5. **方案詳情與編輯區**
   - section_type: detail/form
   - section_purpose: 顯示單一方案的詳細信息，並允許用戶編輯、添加更多細節，包含二次矛盾掃描結果。

## [SECTION COMPONENT SPEC]
<!-- 每個 section 各寫一段 -->

### Section: 矛盾選擇與方案生成區
- **layout**: 頂部操作區，包含下拉選單和按鈕。
  <!-- 單欄 / 左右雙欄 / 卡片網格 / 時間軸 ... -->
- **elements**:
  - `矛盾選擇器`: `dropdown`, `required`, `從該專案已識別的矛盾中選擇一個或多個。`
  - `生成方案按鈕`: `button (primary)`, `required`, `點擊後觸發 AI 生成方案。`
- **states**:
  - 正常：下拉選單可用，按鈕可點擊。
  - loading：生成方案中，按鈕禁用並顯示 Loading Spinner。
  - error：選擇矛盾失敗或生成方案失敗時顯示錯誤提示。
- **copy_constraints**:
  - 矛盾選擇器: 必須選擇至少一個矛盾。

### Section: Contradiction Convergence Graph 視覺化區
- **layout**: 中央主要區域，DAG 圖視覺化佈局，支持縮放和拖拽。
- **elements**:
  - `DAG 收斂圖`: `graph/visualization`, `required`, `以有向無環圖展示矛盾→方案→二次矛盾的完整追蹤鏈。每個節點顯示矛盾嚴重度分類。`
  - `嚴重度標籤 (Fatal/Major/Minor)`: `badge`, `required`, `Fatal (紅色, MUST 相關, 必須解決) / Major (橙色, WANT >20%, 強烈建議解決) / Minor (灰色, WANT ≤20% 且有緩解 → 僅登錄 Risk Register)。`
  - `收斂狀態指示器`: `status indicator`, `required`, `顯示整體收斂狀態：已收斂（所有葉節點無新矛盾）/ 進行中（仍有未解決矛盾）/ 發散警告（節點數超標）。`
  - `節點詳情 Tooltip`: `tooltip/popover`, `optional`, `懸停節點時顯示矛盾詳情、關聯方案、嚴重度分類。`
- **states**:
  - 正常：DAG 圖正常渲染，節點可互動。
  - empty：無矛盾數據時顯示空白提示。
  - converged：所有葉節點已收斂，圖表邊框顯示綠色。
  - diverging：節點數量超過警戒值，圖表邊框顯示黃色/紅色。
- **copy_constraints**:
  - 節點標籤: 最長 50 字元，懸停顯示完整描述。
  - 退出條件：所有葉節點收斂（無新矛盾產生），取代固定迭代次數限制。

### Section: Architecture Health Monitor 面板
- **layout**: 側邊或頂部固定面板，交通燈顯示。
- **elements**:
  - `健康狀態燈號`: `traffic light (green/yellow/red)`, `required`, `綠色: 節點數 ≤3（健康）/ 黃色: 節點數 4-5（警告）/ 紅色: 節點數 >5（強制停止，需返回 Step 1 重新定義）。`
  - `節點計數器`: `counter/badge`, `required`, `顯示當前活躍矛盾節點數量。`
  - `循環矛盾偵測`: `alert`, `conditional`, `偵測到循環矛盾時，顯示紅色警告並強制要求架構重構。`
  - `強制動作按鈕`: `button (warning)`, `conditional`, `紅燈狀態下顯示「返回任務定義」按鈕，觸發回到 Step 1。`
- **states**:
  - healthy (綠燈)：節點數 ≤3，正常操作。
  - warning (黃燈)：節點數 4-5，顯示警告訊息。
  - critical (紅燈)：節點數 >5，強制停止並顯示返回按鈕。
  - circular：偵測到循環矛盾，強制架構重構。

### Section: 方案列表與篩選區
- **layout**: 響應式卡片或表格佈局，支持查看詳情和篩選。
- **elements**:
  - `方案卡片/列表項`: `card/list item`, `required`, `顯示方案名稱、簡短描述、MUST 快篩結果 (以標籤或圖標表示)、矛盾嚴重度標籤 (Fatal/Major/Minor badge)、操作按鈕 (查看詳情)。`
  - `MUST 快篩標籤/篩選器`: `tag/filter`, `optional`, `顯示方案是否通過各項 MUST 快篩，支持按 MUST 條件篩選。`
  - `嚴重度篩選器`: `filter`, `optional`, `支持按矛盾嚴重度 (Fatal/Major/Minor) 篩選方案。`
- **states**:
  - 正常：方案列表正常顯示。
  - empty：無方案時顯示「沒有方案」提示。
  - loading：方案數據載入中顯示骨架屏。
  - error：數據載入失敗時顯示錯誤提示。
- **copy_constraints**:
  - 方案名稱: 最長 100 個字元。
  - 簡短描述: 最長 200 個字元。

### Section: 方案詳情與編輯區
- **layout**: 側邊抽屜 (Drawer) 或模態框 (Modal) 中的詳情佈局。
- **elements**:
  - `方案名稱`: `input (text)`, `required`, `顯示/編輯方案名稱。`
  - `機制說明`: `textarea`, `required`, `詳細描述方案的物理原理和結構。`
  - `假設清單`: `list`, `required`, `顯示方案基於的假設，可連結到假設台帳，支持編輯。`
  - `風險評估`: `table`, `required`, `顯示方案引入的新風險和評估，支持編輯。`
  - `最小驗證`: `textarea`, `required`, `描述驗證此方案所需的最小實驗。`
  - `MUST 快篩結果`: `checklist/badges`, `required`, `顯示此方案通過/未通過的 MUST 條件，可交互。`
  - `二次矛盾掃描結果`: `list/alert`, `required`, `AI 掃描該方案後識別的二次矛盾列表。若有新矛盾，顯示警告並引導用戶回到矛盾解決流程。`
  - `矛盾嚴重度標記`: `badge group`, `required`, `顯示此方案解決的矛盾嚴重度分類 (Fatal/Major/Minor)。`
  - `保存/取消按鈕`: `button group`, `required`, `保存編輯或取消操作。`
- **states**:
  - 正常：詳情信息正常顯示。
  - loading：數據保存中顯示 Loading Spinner。
  - error：驗證失敗或保存失敗時顯示錯誤提示。
  - secondary_contradiction_found：AI 掃描發現二次矛盾，顯示警告並引導再次解決。
- **copy_constraints**:
  - 各字段有相應長度限制，假設清單、風險評估、最小驗證支持多項輸入。

## [INTERACTION & STATE FLOW]
- **主要互動流程**：
  1. 用戶進入方案探索頁面，系統載入已生成的方案列表（如有）和 Contradiction Convergence Graph。
  2. 用戶從下拉選單中選擇一個或多個矛盾，點擊「生成方案」按鈕，觸發 AI 根據選擇的矛盾和知識庫生成一系列初步設計方案。
  3. AI 生成方案後，自動掃描每個方案的二次矛盾（secondary contradictions），並更新 Convergence Graph。
  4. 若發現新的二次矛盾，系統自動將其加入 DAG 圖並分類嚴重度（Fatal/Major/Minor）。用戶需針對新矛盾再次生成方案，重複解決直至所有葉節點收斂。
  5. Architecture Health Monitor 即時監控圖的健康度：綠燈(≤3節點) → 正常；黃燈(4-5節點) → 警告；紅燈(>5節點) → 強制返回 Step 1 重新定義；循環矛盾 → 強制架構重構。
  6. 方案會自動進行 MUST 快篩，篩選結果即時顯示在卡片/列表項上，並標記矛盾嚴重度。
  7. 收斂完成條件：所有葉節點收斂（無新矛盾產生），不設固定迭代次數上限。

- **表單驗證規則**（如適用）：
  - `方案名稱`: 必填，最少 5 字元 → 方案名稱為必填項，且需至少 5 個字元。
  - `機制說明`: 必填，最少 50 字元 → 機制說明為必填項，且需至少 50 個字元。

- **資料更新策略**：
  - AI 生成新方案後，方案列表自動刷新。
  - 用戶編輯方案並保存後，該方案的詳細信息自動刷新。

- **RWD 行為差異**：
  - Desktop (>1024px): 矛盾選擇與生成區、方案列表可並排顯示，方案詳情以側邊抽屜形式展示。
  - Tablet (768px - 1023px): 佈局調整為堆疊，方案列表可能簡化顯示，方案詳情以模態框形式展示。
  - Mobile (<768px): 所有區塊垂直堆疊，方案列表卡片式顯示，方案詳情為全屏模態框。

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  - GET `/api/projects/:id/contradictions` — 獲取指定專案的矛盾列表，用於矛盾選擇器。
  - POST `/api/projects/:id/solutions/generate` — 根據選定的矛盾觸發 AI 生成方案。
  - GET `/api/projects/:id/solutions` — 獲取指定專案的方案列表。
  - PUT `/api/projects/:id/solutions/:solution_id` — 更新方案信息。
  - GET `/api/projects/:id/convergence-graph` — 獲取矛盾收斂圖 (DAG) 數據。
  - POST `/api/projects/:id/solutions/:solution_id/scan-contradictions` — AI 掃描方案的二次矛盾。
  - GET `/api/projects/:id/architecture-health` — 獲取架構健康度監控數據（節點數、循環偵測）。
- **error cases**:
  - AI 生成失敗: 顯示 AI 處理失敗提示，建議用戶重新嘗試或調整輸入。
  - MUST 快篩服務失敗: 顯示快篩失敗提示，或標記方案為「待手動審核」。
  - 方案數據載入失敗: 頁面顯示錯誤提示訊息，提供重試按鈕。
  - 收斂圖載入失敗: 顯示圖表載入失敗提示，方案列表仍可正常操作。
  - 二次矛盾掃描失敗: 顯示掃描失敗提示，標記方案為「待手動掃描」。

## [EXCEPTION TO GLOBAL RULES]
<!-- 如果這一頁要刻意違反 Global 規範，必須在這裡寫明並說明原因 -->
- 無特殊例外，完全遵循 Global System Prompt 規範。

## [ACCEPTANCE CRITERIA]
- [x] 能夠選擇矛盾並成功觸發 AI 生成方案，並將結果顯示在列表中。
- [x] 方案列表能清晰展示方案名稱、MUST 快篩結果、矛盾嚴重度標籤等關鍵信息，並支持查看詳情。
- [x] 方案詳情能完整記錄所有必要信息（機制、假設、風險、最小驗證、二次矛盾掃描結果），並支持編輯和保存。
- [x] Contradiction Convergence Graph (DAG) 正確顯示矛盾→方案→二次矛盾追蹤鏈，支持縮放和互動。
- [x] 矛盾嚴重度分類（Fatal/Major/Minor）正確標記並影響收斂判斷。
- [x] Architecture Health Monitor 正確顯示交通燈狀態，紅燈時強制返回 Step 1。
- [x] 收斂條件基於「所有葉節點收斂」而非固定迭代次數。
- [x] 響應式設計在不同設備上顯示良好，信息呈現合理。
