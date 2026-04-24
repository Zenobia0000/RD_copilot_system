# E2E 手測腳本：Auto-TRIZ v2 完整路徑 (FA → OZ-OT → SIM → CCI)

> **版本**：1.0 | **日期**：2026-04-24
> **對應 WBS**：8.7.4
> **前置**：本地 backend + frontend + Supabase 均啟動

---

## 測試情境：多矛盾專案完整 Auto-TRIZ v2 流程

### 前置條件

- 已有專案，Brief 已凍結
- 已在 Explore 完成至少 2 條 TC 矛盾識別（例：TC-01「重量 vs 剛性」、TC-02「散熱效率 vs 體積」）
- 使用者已登入且具有 RD 角色

---

### Step 1：Explore — 觸發 Entry Grading → 選擇 Level A

1. 進入 Explore 頁面
2. 點擊「入口等級評估」按鈕
3. 輸入問題描述（至少 10 字以上的完整情境說明）
4. 提交後等待系統回傳等級判定

**驗證清單**：
- [ ] 系統回傳 Level A/B/C 判定結果
- [ ] 判定結果附帶簡要說明（為何判定為該等級）
- [ ] 選擇 Level A 後，Explore 頁切換為 5-step stepper
- [ ] stepper 顯示 5 個步驟：問題定向 → 功能分析 → 蘇格拉底 → 矛盾 → CLD
- [ ] 當前步驟高亮為「問題定向」

---

### Step 2：Explore — 執行 5Why 分析 → 驗證 5 層鏈顯示

1. 在 Problem Scoping 步驟中輸入問題陳述
2. 點擊「執行 5Why」
3. 等待 AI 回傳 5 層 Why-Because 鏈

**驗證清單**：
- [ ] 顯示完整 5 層 Why-Because 鏈
- [ ] 每層 Why 包含「現象」與「因果關係」欄位
- [ ] 根因（第 5 層 Why 的結論）明確標示
- [ ] 建議下一步動作列出（例：「建議進行功能分析以識別問題組件」）
- [ ] 可切換至 KT 分析 tab，Is/Is Not 對照表可正常顯示
- [ ] stepper 可正常前進到下一步

---

### Step 3：Explore — 執行 Function Analysis → 驗證組件交互圖

1. 進入 Function Analysis 步驟
2. 輸入系統描述和組件清單（至少 2 個組件）
3. 點擊「產生功能模型」

**驗證清單**：
- [ ] 顯示組件交互圖
- [ ] 有用功能以綠色箭頭標示
- [ ] 有害功能以紅色箭頭標示
- [ ] 不足功能以虛線箭頭標示
- [ ] 顯示 SF（物質-場）診斷摘要
- [ ] 問題組件（有害/不足功能相關）自動標記
- [ ] 組件清單為空時顯示提示「請至少輸入 2 個組件」

---

### Step 4：Create — 展開 OZ-OT Panel → 驗證 OZ/OT/Px 顯示

1. 進入 Create 頁面 TRIZ 區段
2. 選擇矛盾 "TC-01"
3. 展開 OZ-OT 面板
4. 點擊觸發 OZ-OT 分析

**驗證清單**：
- [ ] 操作區域 (OZ) 至少列出 1 個空間區域，附帶簡要說明
- [ ] 操作時間 (OT) 至少列出 1 個時間窗口，附帶簡要說明
- [ ] 可控參數 (Px) 至少列出 1 個可調參數，附帶簡要說明
- [ ] OZ/OT/Px 資料與選定矛盾的上下文一致
- [ ] 面板可正常收合/展開

---

### Step 5：Create — 觸發 TRIZ 方向導向分析 → 驗證解法產出

1. 在 Create 頁面，對 TC-01 點擊「Solve Layered」
2. 等待 AI 回傳解法建議
3. 對 TC-02 重複相同操作

**驗證清單**：
- [ ] TC-01 解法卡片正常顯示（至少 1 個 InventivePrinciple 推薦）
- [ ] TC-02 解法卡片正常顯示
- [ ] 解法卡片包含 L1 Surface 層級建議
- [ ] 若 L1 信心 < 0.6，自動觸發 L2 drill-down
- [ ] 解法產出時間 ≤ 15 秒

---

### Step 6：Create — 觸發 SIM Matrix → 驗證交互矩陣

1. 確認 TC-01 和 TC-02 均已有解法
2. 點擊「SIM 矩陣分析」按鈕
3. 等待交互矩陣生成

**驗證清單**：
- [ ] 顯示解法交互矩陣表格
- [ ] 矩陣中每個交叉格顯示 +1（協同）/ 0（無關）/ -1（衝突）
- [ ] 協同（+1）以綠色標示
- [ ] 衝突（-1）以紅色標示
- [ ] 推薦最佳不衝突組合，以高亮方式標示
- [ ] 矩陣對角線為空或標示為 N/A

---

### Step 7：Create — 檢查方案卡 CCI Badge → 驗證 Evolution/Patch 標籤

1. 在 SIM 分析完成後，查看個別方案卡

**驗證清單**：
- [ ] 每張方案卡顯示 CCI badge
- [ ] badge 標籤為「Evolution」（演化型）或「Patch」（修補型）
- [ ] badge 旁顯示概念信心分數（0-100 數值）
- [ ] Evolution 型方案的信心分數 ≥ Patch 型方案（一般預期）
- [ ] 點擊 badge 可查看 CCI 評定依據明細

---

### Step 8：Create — 檢查 Evidence Coverage Gauge → 驗證覆蓋率百分比

1. 查看 Evidence Registry 區段
2. 確認 AI 分析過程中自動登記的 evidence claims

**驗證清單**：
- [ ] Evidence Registry 顯示至少 1 條自動登記的 claim
- [ ] 每條 claim 包含「來源步驟」「聲明內容」「信心等級」
- [ ] claim 預設狀態為「pending」
- [ ] 覆蓋率百分比正確顯示（confirmed / total × 100%）
- [ ] 手動驗證一條 claim（點擊「驗證」→ 選擇 confirmed）後，覆蓋率更新
- [ ] 若覆蓋率 = 0%（全部 pending），Gate PG2 顯示為 blocked 狀態

---

## 通過標準

- [ ] **Step 1-8 全部步驟無錯誤**（無 console error、無 500 回應）
- [ ] **資料正確持久化**：重新整理頁面後，所有分析結果仍正確顯示
- [ ] **Entry Grading 判定結果持久化**：重新進入 Explore 頁面後等級與 stepper 狀態一致
- [ ] **SIM Matrix 結果持久化**：重新進入 Create 頁面後矩陣資料仍在
- [ ] **Evidence claims 持久化**：重新整理後 claim 列表與狀態不變
- [ ] **API 回應時間**：所有 AI 分析步驟回應時間 ≤ 30 秒

---

## 已知限制

- Entry Grading 的 Level 判定閾值可能需要根據實際測試調整
- SIM Matrix 在解法數量 > 10 時的效能尚未驗證
- Evidence Registry 的自動 claim 登記觸發時機依賴後端事件機制
- CCI 評定的 Evolution/Patch 分類邏輯為 AI 推斷，可能需要人工校正

---

## 下游銜接驗證

### Step 9：Pre-CAD Gate 與 Evidence 覆蓋率整合

1. 進入 Pre-CAD Gate Review 頁面
2. 觸發 AI Analyze

**驗證清單**：
- [ ] Gate 報告的 Evidence 區段顯示覆蓋率百分比
- [ ] 覆蓋率 < 40% 時，Gate 顯示 blocked 警告
- [ ] 覆蓋率 ≥ 40% 時，Gate 該維度可正常通過
- [ ] pending claims 清單可在 Gate 報告中展開查看
