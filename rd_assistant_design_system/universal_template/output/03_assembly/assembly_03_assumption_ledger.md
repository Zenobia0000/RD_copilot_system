# Assembly Prompt — 假設台帳

> **使用方式**：填完後，將下方 ``` 區塊內的完整內容複製貼到 Lovable / Claude / GPT-4 等 AI 工具。

---

```markdown
=== GLOBAL PROJECT GUIDELINE (DO NOT OVERRIDE) ===

你是「RD Design Copilot」專案的資深產品設計師與前端工程師，負責維護整個專案的設計一致性。

### 核心設計系統
- **配色**：Primary(#007bff) / Secondary(#6c757d) / Accent(#fd7e14) / Error(#dc3545)
- **字體**："Noto Sans TC", "Helvetica Neue", Arial, "Segoe UI", sans-serif，模組化比例 1.25
- **元件風格**：圓角 8px (0.5rem)，輕微陰影，增加層次感 (e.g., box-shadow: 0 4px 6px rgba(0,0,0,0.1))，1px solid $color-divider
- **語氣**：專業精準、結構化、數據驅動、實用主義
- **技術棧**：React (Frontend)

### 重要規範
- 本區段定義整個專案的設計系統與風格
- 所有頁面相關需求都必須遵守這裡的規範
- 除非在 [EXCEPTION TO GLOBAL RULES] 中明確說明，否則不准違反

=== CURRENT TASK: BUILD ONE PAGE ===

本次任務：根據上方 Global Guideline，設計並實作「假設台帳」。

### [PAGE SPECIFICATION]

**頁面元資料**：
- 路徑：`/projects/:id/assumption-ledger`
- 類型：列表/表單
- 主要目標：管理專案所有假設，透過因果迴路圖 (CLD) 視覺化假設與系統行為的關聯，以結構化驗證規劃工作流追蹤驗證進度。支持從多模態來源（PDF/圖片/Excel）AI 自動提取假設。
- 次要目標：建立假設 ↔ 矛盾 ↔ 收斂圖的完整可追溯鏈。蘇格拉底七類提問中「因果追問」與「假設挑戰」結果自動回饋至本頁。AI 作為主動挑戰者角色，質疑隱性假設。

**目標用戶**：
- 主要：RD 工程師, RD 主管
- 次要：專案經理 (PM)

**進入方式**：
- 從「矛盾識別頁面」完成後自動導航，或從「專案儀表板」點擊導航進入。
- 預估停留時間：長 (10-20 分鐘)

**頁面結構**（由上至下）：

1. **假設列表展示區**
   - 用途：以表格形式展示所有假設，包含編號、內容、依據來源、關聯矛盾、驗證狀態。
   - 佈局：響應式表格佈局，支持排序和分頁。
   - 元件：
     - `假設表格` (table, required)：每列顯示假設編號、內容（最長 300 字元）、依據來源（含 AI 提取來源標籤）、影響範圍、若錯了最壞後果、驗證狀態、操作按鈕。
     - `新增假設按鈕` (button primary, required)：點擊後打開假設詳情編輯區。
     - `AI 自動提取假設` (button secondary, optional)：從多模態來源中 AI 自動提取隱含假設。
   - 狀態：正常、loading（骨架屏）、empty（無假設提示）、error（載入失敗）

2. **因果迴路圖區 (Causal Loop Diagram)**
   - 用途：視覺化假設之間及假設與系統行為的因果關係。支持 Step 3 系統建模。
   - 佈局：可縮放、可平移的互動式圖表。
   - 元件：
     - `因果迴路圖 CLD` (interactive-graph, required)：節點=假設/系統變量，邊=因果關係(+正反饋/−負反饋)。點擊節點高亮相關假設。支持拖拽新增。
     - `迴路偵測指示器` (badge-list, required)：自動偵測增強迴路(R)與平衡迴路(B)，標記潛在系統不穩定因素。
     - `槓桿點標記` (highlight, optional)：AI 識別高影響力節點，以 Accent 色標記。

3. **假設詳情編輯區**
   - 用途：編輯假設詳細信息，包含影響範圍與因果關聯。
   - 佈局：模態框 (Modal) 或側邊抽屜 (Drawer)。
   - 元件：
     - `假設內容` (textarea, required)：假設詳細描述。
     - `依據來源` (input text, required)：依據文獻/來源 ID，含 AI 提取來源標籤。
     - `若錯了最壞後果` (textarea, required)：假設錯誤的最壞結果。
     - `影響範圍` (tag-select, required)：選擇影響的系統模塊/矛盾，建立追溯鏈。
     - `因果關聯` (relation-picker, optional)：選擇 CLD 中上游/下游節點及關係類型。
     - `保存/取消按鈕` (button group, required)。

4. **驗證規劃工作流區 (Verification Planning)**
   - 用途：結構化驗證工作流，含方法選擇、資源估算、時程排序。
   - 佈局：Kanban 看板或時間線視圖，可切換。
   - 元件：
     - `驗證看板` (kanban-board, required)：四欄（待規劃→待驗證→驗證中→已完成/已推翻），卡片可拖拽。
     - `驗證方法選擇` (select, required)：仿真分析/原型測試/專家審查/文獻引用/實測驗證/其他。
     - `資源估算` (form-group, required)：成本、週期、設備/人力。
     - `時程對齊` (timeline-bar, required)：與專案時間線及 Gate P 對齊顯示。
     - `優先級排序` (auto-sort, required)：依「最壞後果」嚴重度自動排序。

5. **矛盾追溯面板 (Contradiction Traceability)**
   - 用途：顯示假設與矛盾識別 (Step 2)、矛盾收斂圖 (Step 5a-6) 的關聯。
   - 佈局：右側固定面板或底部抽屜，選中假設時展開。
   - 元件：
     - `關聯矛盾列表` (linked-list, required)：顯示關聯矛盾及嚴重度 (Fatal/Major/Minor)，可跳轉。
     - `收斂圖影響` (impact-indicator, required)：假設推翻時顯示受影響的解法路線數量與警告。
     - `蘇格拉底回饋` (feedback-list, optional)：七類提問中「因果追問」和「假設挑戰」的 AI 結論。

**互動要求**：
1. 進入頁面，系統載入假設列表（含 AI 提取假設）+ 因果迴路圖 + 驗證看板。
2. 用戶在因果迴路圖上查看假設因果關係，識別增強迴路(R)、平衡迴路(B)、槓桿點。可拖拽新增。
3. 新增/編輯假設時，設定影響範圍與因果關聯。保存後 CLD 自動更新。
4. 矛盾追溯面板顯示關聯矛盾與收斂圖影響。
5. 在驗證看板安排驗證工作：選方法、估資源、對齊時程。系統依「最壞後果」自動排序。
6. 拖拽卡片更新驗證狀態（待規劃→待驗證→驗證中→已完成/已推翻）。
7. 假設推翻時，系統標記受影響矛盾，提示「建議重新掃描矛盾收斂圖」。

**表單驗證規則**：
- `假設內容`: 必填，最少 10 字元 → 假設內容為必填項，且需至少 10 個字元。
- `依據來源`: 必填 → 依據來源為必填項。
- `驗證成本/週期`: 必填，且需為有效數值或描述 → 驗證成本/週期格式不正確。

**資料更新策略**：
- 新增/編輯假設後，列表數據將自動刷新。
- 假設狀態更新後，列表數據將自動刷新。

**資料處理**：
- API 端點：
  - GET `/api/projects/:id/assumptions` — 獲取假設列表。
  - POST `/api/projects/:id/assumptions` — 創建新假設。
  - PUT `/api/projects/:id/assumptions/:assumption_id` — 更新假設。
  - GET `/api/projects/:id/assumptions/causal-loop` — 獲取因果迴路圖數據。
  - PUT `/api/projects/:id/assumptions/causal-loop` — 更新因果迴路圖。
  - GET `/api/projects/:id/assumptions/:assumption_id/contradictions` — 獲取假設關聯矛盾。
  - POST `/api/projects/:id/assumptions/:assumption_id/verification-plan` — 創建/更新驗證計劃。
  - GET `/api/projects/:id/assumptions/verification-timeline` — 獲取驗證時程總覽。
- 載入策略：漸進式載入 (Skeleton Screen)，關鍵數據優先。
- 錯誤處理：
  - API 載入或提交失敗：錯誤提示 + 重試按鈕。
  - 假設列表為空：引導新增假設。
  - 因果迴路圖循環依賴：標記迴路並提示用戶檢視。
  - 假設推翻後收斂圖受影響：彈出警告，列出受影響矛盾，提供「跳轉收斂圖」按鈕。

**RWD 行為差異**：
- Desktop (>1024px)：表格和詳情編輯區可並排顯示，或編輯區以模態框形式展示。
- Tablet (768px - 1023px)：表格列可能壓縮，詳情編輯區以全屏模態框或側邊抽屜形式顯示。
- Mobile (<768px)：表格轉換為列表卡片式顯示，詳情編輯區為全屏模態框。

=== EXCEPTION RULES ===

本頁面允許的例外（如有）：
- 無特殊例外，完全遵循 Global System Prompt 規範。

=== OUTPUT REQUIREMENTS ===

請依照以下步驟輸出：

### Step 1: 結構確認
列出本頁面的：
- 主要 sections 及其用途
- 每個 section 的關鍵元件
- 資料流與狀態管理策略

### Step 2: 設計決策說明
說明 2-3 個關鍵設計決策：
- 決策點與選擇理由
- 如何確保與 Global 規範一致
- 任何必要的權衡考量

### Step 3: 實作方案
產出完整的 React 程式碼，包含：
- 元件結構與 props 定義
- 狀態管理邏輯
- 互動處理與錯誤處理
- 響應式設計
- 關鍵區塊註解

### 品質檢查清單
- [ ] 色彩系統一致性
- [ ] 字體層級正確
- [ ] 元件風格統一
- [ ] 響應式設計完整
- [ ] 狀態處理完善（loading / error / empty）
```

---

**執行優先順序**：
1. Global 規範為最高優先級
2. Page 特定需求次之
3. Exception 需明確說明且最小化

**版本資訊**：
- Global System Prompt 版本：v1.0
- Assembly 日期：2026-03-12
- 負責人：AI Agent
