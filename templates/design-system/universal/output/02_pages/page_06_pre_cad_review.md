# Page-Level Prompt: Pre-CAD 審查

## [PAGE META]
- **page_name**: Pre-CAD 審查
- **route_path**: `/projects/:id/pre-cad-review`
- **page_type**: 列表/詳情/審查表單
  <!-- landing / form / dashboard / report / search / detail / settings -->
- **primary_goal**: 在投入大量 CAD 繪製和詳細模擬之前，利用「可驗證的最小信息」篩選和縮減候選設計方案，並確認 Pre-CAD Confidence Score 達到 Gate P 門檻。
- **secondary_goal**: 記錄 Pre-CAD 審查過程與結果，確保決策可追溯，驗證矛盾收斂圖和約束可行性。

## [USER CONTEXT]
- **target_user_segment**:
  - 主要：RD 主管, RD 工程師
  - 次要：專案經理 (PM), 製造工程師
- **entry_point**:
  - 從「方案探索頁面」完成後自動導航，或從「專案儀表板」點擊導航進入。
  <!-- 使用者從哪裡進入此頁？哪個按鈕 / 哪個前一頁 -->
- **expected_time_on_page**: 中 (15-25 分鐘)
  <!-- 粗估停留時間，幫助決定資訊密度 -->

## [STRUCTURE: SECTIONS]
<!-- 以 top-down 順序列出所有區塊 -->

1. **Pre-CAD Confidence Score 總覽區**
   - section_type: dashboard/gauge
   - section_purpose: 顯示 Pre-CAD 信心分數（百分比進度條/儀表），呈現矛盾收斂圖摘要和約束可行性驗證狀態。

2. **候選方案列表區**
   - section_type: list/table
   <!-- hero / summary / list / form / faq / footer / stats / tabs ... -->
   - section_purpose: 展示通過 MUST 快篩的候選設計方案概覽，供審查團隊選擇。

3. **Pre-CAD 審查表單區**
   - section_type: form/checklist
   - section_purpose: 根據審查維度（MUST、解耦、可驗證性、主要風險、最小 CAD 工作量）評估並記錄審查結果。

4. **審查結論與決策區**
   - section_type: summary/action
   - section_purpose: 總結審查結果，決定保留方案，並記錄結論。Gate P 門檻驗證。

## [SECTION COMPONENT SPEC]
<!-- 每個 section 各寫一段 -->

### Section: Pre-CAD Confidence Score 總覽區
- **layout**: 頂部儀表板佈局，橫向排列關鍵指標。
  <!-- 單欄 / 左右雙欄 / 卡片網格 / 時間軸 ... -->
- **elements**:
  - `Confidence Score 儀表/進度條`: `gauge/progress bar`, `required`, `顯示 Pre-CAD 信心分數百分比。公式：Confidence = converged(Fatal+Major) / total(Fatal+Major) x 100%。`
  - `Gate P 門檻指示`: `threshold indicator`, `required`, `顯示 Gate P 門檻要求：Fatal+Major 矛盾的 Confidence 必須達到 100%。達標顯示綠色勾號，未達標顯示紅色警告。`
  - `收斂圖摘要`: `summary card`, `required`, `顯示矛盾收斂圖的概要：Fatal 矛盾已解決數/總數、Major 矛盾已解決數/總數、Minor 矛盾狀態。`
  - `約束可行性驗證狀態`: `status list`, `required`, `顯示 AI 在 Gate 1 階段對約束物理可行性的驗證結果列表，每項約束標記為已驗證/存疑/不可行。`
- **states**:
  - 正常：所有指標正常顯示。
  - gate_passed：Confidence Score = 100%，Gate P 門檻達標。
  - gate_blocked：Confidence Score < 100%，Gate P 門檻未達標，審查按鈕禁用。
  - loading：數據載入中顯示骨架屏。
- **copy_constraints**:
  - Confidence Score 顯示至小數點第一位。

### Section: 候選方案列表區
- **layout**: 響應式列表或卡片佈局。
  <!-- 單欄 / 左右雙欄 / 卡片網格 / 時間軸 ... -->
- **elements**:
  - `方案卡片/列表項`: `card/list item`, `required`, `顯示方案名稱、簡短描述、MUST 快篩結果 (以標籤或圖標表示)、操作按鈕 (查看詳情)。`
- **states**:
  - 正常：方案列表正常顯示。
  - empty：無候選方案時顯示「沒有候選方案」提示。
  - loading：方案載入中顯示骨架屏。
  - error：數據載入失敗時顯示錯誤提示。
- **copy_constraints**:
  - 方案名稱: 最長 100 個字元。

### Section: Pre-CAD 審查表單區
- **layout**: 模態框 (Modal) 或頁面內展開式表單佈局。
- **elements**:
  - `審查維度評估`: `checklist/rating`, `required`, `每個維度 (如空間約束、解耦程度) 包含評估輸入 (文字/選擇框) 和證據上傳選項。`
  - `評估摘要`: `textarea`, `optional`, `輸入此維度的簡短評估總結。`
- **states**:
  - 正常：表單可用。
  - error：評估項未完成或輸入不符合要求時顯示錯誤提示。
- **copy_constraints**:
  - 評估摘要: 最長 200 個字元。

### Section: 審查結論與決策區
- **layout**: 底部固定操作欄或獨立區塊。
- **elements**:
  - `保留方案選擇器`: `checkbox group/multi-select`, `required`, `從候選方案中選擇 3-5 條要保留的方案。`
  - `審查結論備註`: `textarea`, `optional`, `記錄審查會議的關鍵討論和決策原因。`
  - `批准審查按鈕`: `button (primary)`, `required`, `點擊後保存審查結果並推進專案階段。`
- **states**:
  - 正常：按鈕可點擊。
  - disabled：未選擇足夠方案或評估項未完成時按鈕禁用。
  - loading：提交中顯示 Loading Spinner。
- **copy_constraints**:
  - 審查結論備註: 最長 500 個字元。

## [INTERACTION & STATE FLOW]
- **主要互動流程**：
  1. 用戶進入 Pre-CAD 審查頁面，系統載入 Pre-CAD Confidence Score 總覽、約束可行性驗證狀態和通過 MUST 快篩的候選方案列表。
  2. 用戶確認 Confidence Score 和收斂圖摘要，確認所有 Fatal 和 Major 矛盾已收斂。
  3. 用戶點擊某方案，打開 Pre-CAD 審查表單進行詳細評估和記錄。
  4. 用戶完成所有評估後，從候選方案中選擇 3-5 條要保留的方案，並點擊「批准審查」按鈕。
  5. 系統驗證 Gate P 門檻：Confidence Score 必須 = 100%（所有 Fatal+Major 矛盾已收斂）。未達標時按鈕禁用並顯示缺失項提示。
  6. 審查結果成功提交後，專案狀態推進至下一階段。

- **表單驗證規則**（如適用）：
  - `保留方案選擇器`: 必須選擇 3-5 條方案 → 請至少選擇 3 條候選方案。
  - `審查維度評估`: 所有審查維度必須填寫 → 所有評估項為必填。

- **資料更新策略**：
  - 保存審查結果後，候選方案列表和專案狀態自動刷新。

- **RWD 行為差異**：
  - Desktop (>1024px): 候選方案列表和審查表單可並排顯示，提升審查效率。
  - Tablet (768px - 1023px): 佈局調整為堆疊，審查表單可能以全屏形式顯示。
  - Mobile (<768px): 列表卡片化，審查表單以全屏模態框顯示。

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  - GET `/api/projects/:id/solutions/candidates` — 獲取通過 MUST 快篩的候選方案列表。
  - GET `/api/projects/:id/confidence-score` — 獲取 Pre-CAD Confidence Score 和收斂圖摘要。
  - GET `/api/projects/:id/constraint-feasibility` — 獲取約束可行性驗證狀態。
  - POST `/api/projects/:id/pre-cad-reviews` — 提交 Pre-CAD 審查結果（含 Gate P 門檻驗證）。
- **error cases**:
  - 獲取候選方案失敗: 頁面顯示錯誤提示訊息，提供重試按鈕。
  - Confidence Score 計算失敗: 顯示計算失敗提示，Gate P 門檻驗證降級為手動確認。
  - Gate P 門檻未達標: 顯示未達標的 Fatal/Major 矛盾清單，禁止提交審查結果。
  - 提交審查結果失敗: 顯示提交失敗提示，並提供重新提交選項。

## [EXCEPTION TO GLOBAL RULES]
<!-- 如果這一頁要刻意違反 Global 規範，必須在這裡寫明並說明原因 -->
- 無特殊例外，完全遵循 Global System Prompt 規範。

## [ACCEPTANCE CRITERIA]
- [x] Pre-CAD Confidence Score 正確顯示，公式為 converged(Fatal+Major) / total(Fatal+Major) x 100%。
- [x] Gate P 門檻驗證正確：Confidence Score 必須 = 100% 才能提交審查。
- [x] 收斂圖摘要正確顯示所有 Fatal/Major 矛盾的解決狀態。
- [x] 約束可行性驗證狀態正確顯示。
- [x] 候選方案列表能正確顯示，且能選擇方案進行審查。
- [x] Pre-CAD 審查表單能完整記錄評估結果和結論。
- [x] 能夠選擇 3-5 條方案作為保留方案。
- [x] 審查結果能成功提交並更新專案狀態。
- [x] 響應式設計在不同設備上顯示良好。
