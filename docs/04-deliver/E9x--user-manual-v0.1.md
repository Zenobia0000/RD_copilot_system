# RD Design Copilot -- 使用者手冊

> Version 0.1.0

---

## 1. 系統簡介

**RD Design Copilot** 是一套 AI 輔助的研發設計決策平台，協助工程師透過三階段結構化流程——**Define（定義）、Diverge（發散）、Converge（收斂）**——從任務簡報到最終設計決策，系統性地管理假設、矛盾、風險與方案評估。

### 三階段流程概覽

| 階段 | 目的 | 涵蓋頁面 |
|------|------|----------|
| **Define** | 釐清任務、提取約束條件與 KPI、發現隱藏假設 | Dashboard, Brief |
| **Diverge** | 產生多元方案、TRIZ 求解、子系統定義 *(v9: SCAMPER 已移除)* | Explore, Track |
| **Converge** | MUST/WANT 評估、Pre-CAD 審查、風險分析、最終決策 | Create, Review, Decide |

---

## 2. 安裝與啟動

### 2.1 系統需求

| 項目 | 版本 |
|------|------|
| Node.js | 22 或以上 |
| Python | 3.12 或以上 |
| Docker | 選用（可用 docker-compose 一鍵啟動） |

### 2.2 環境變數設定

在專案根目錄建立 `.env` 檔案，設定以下變數：

```env
# Supabase（前端認證 + 資料庫）
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbG...

# AI 服務（後端 LLM 呼叫）
ANTHROPIC_API_KEY=sk-ant-...

# JWT 驗證（後端 auth middleware）
JWT_SECRET=your-jwt-secret
```

### 2.3 前端啟動

```bash
npm install
npm run dev
```

前端預設運行於 `http://localhost:5173`。

### 2.4 後端啟動

```bash
cd backend
pip install -e .
uvicorn app.main:app --port 8000
```

後端 API 預設運行於 `http://localhost:8000`。可至 `http://localhost:8000/docs` 查看自動產生的 Swagger UI。

### 2.5 Docker 啟動（一鍵部署）

```bash
docker-compose up
```

Docker Compose 會同時啟動前後端服務，無需分別安裝依賴。

---

## 3. 操作流程

以下為系統的七個主要頁面，依照設計流程順序說明。

### 3.1 Dashboard（儀表板）

**用途**：專案總覽與進度追蹤。

- 顯示所有專案清單，每個專案卡片包含 8-Gate 通過狀態
- KPI 指標摘要卡片，顯示目前達成率
- 點擊專案卡片進入該專案的詳細流程
- 可從 KPI 卡片直接登錄 Evidence（詳見第 4 節）

### 3.2 Brief（任務定義）

**用途**：定義設計任務的 Mission、約束條件、KPI。

操作步驟：
1. 貼上或上傳原始需求文件（規格書、客戶信件等）
2. 點擊「AI 提取」，系統自動擷取約束條件、KPI 與假設
3. 檢視 AI 建議，手動新增或修改
4. 點擊「AI 改寫 Mission」取得精準工程語言版本
5. 使用「建議約束」和「建議 KPI」補充遺漏項目
6. 點擊「產生 5W1H」自動建立任務定義
7. 完成後，Gate 1.1 自動檢查：Mission 已定義 + KPI >= 3 且皆有量測方法

### 3.3 Explore（探索）

**用途**：透過蘇格拉底問答發現隱藏假設與矛盾。

操作步驟：
1. 系統根據 Mission 與約束自動產生 7 類蘇格拉底問題
2. 逐一回答問題，系統標記哪些答案暗含假設或矛盾
3. 點擊「提取假設」將回答中的假設自動寫入假設台帳
4. 將發現的矛盾移至矛盾清單，使用「AI 形式化」轉為 TRIZ 語句
5. 產生因果迴路圖（CLD），辨識系統槓桿點（Breakpoints）
6. Gate 1.2 檢查：假設 >= 10、高風險假設 >= 3、矛盾 >= 3
7. Phase Gate PG1 檢查：CLD 已建立 + Breakpoints >= 3

### 3.4 Track（假設追蹤）

**用途**：管理假設的驗證實驗與證據。

操作步驟：
1. 檢視假設台帳，依嚴重度排序（critical > high > medium > low）
2. 對高風險假設設計驗證實驗
3. 記錄實驗結果，登錄 Evidence（詳見第 4 節）
4. 更新假設狀態：validated / invalidated / pending
5. Gate 2.1 檢查：>= 3 個高風險假設有對應實驗

### 3.5 Create（方案創建）

**用途**：產生多元設計方案。

操作步驟：
1. 使用「Anti-Anchor Sprint」產生 3+ 個非典型方案，打破路徑依賴
2. 對每個矛盾使用 TRIZ 求解（TC 或 PC 路徑）
3. ~~選擇子系統進行 SCAMPER 7 動作變形~~ *(v9: 已移除，TRIZ 40 原理完全覆蓋)*
4. ~~SCAMPER 發現的新矛盾自動回饋至矛盾清單~~ *(v9: 已移除)*
5. Gate 2.2 檢查：方案 >= 3

### 3.6 Review（審查）

**用途**：篩選與評估設計方案。

操作步驟：
1. **MUST 篩選**：對每個方案進行 Go/No-Go 判定
   - AI 預填判定結果（含信心度與推理）
   - 工程師確認或覆寫 AI 判定
   - 未通過 MUST 的方案自動淘汰
2. **Pre-CAD 5D 審查**：空間、成本、安全、解耦、供應鏈五維評分
   - AI 提供初步分數與分析
   - 工程師調整分數後確認
3. **WANT 評分**：AI 產生 W1-W6 期望條件
   - 設定權重（1-10）
   - 對存活方案逐一評分
4. **風險分析**：FMEA 風格，機率 x 嚴重度評分
5. **收斂掃描**：偵測二階矛盾，評估架構健康度
   - 若 `force_pause = true`，系統強制暫停並要求解決致命矛盾
6. Phase Gate PG2 檢查：>= 1 個方案通過 Pre-CAD

### 3.7 Decide（決策）

**用途**：做出最終設計決策並產生行動項目。

操作步驟：
1. 依據 MUST + WANT + 風險 + Pre-CAD 總分選定最佳方案
2. 記錄決策理由
3. AI 自動建議後續行動項目（含負責角色與建議工期）
4. 簽核決策記錄
5. 使用「匯出」功能產出完整設計報告（Markdown 或 JSON）
6. 執行「知識回寫」將本次專案成果寫入知識庫
7. Gate 3.2 檢查：決策記錄已簽核
8. Phase Gate PG3 檢查：所有核心 artifacts 已發佈（需人工確認）

---

## 4. Evidence Entry 使用方式

Evidence（證據）是支持假設驗證、KPI 達成的關鍵資料。可從兩個入口登錄：

### 4.1 從 Dashboard KPI 卡片登錄

1. 在 Dashboard 找到目標 KPI 卡片
2. 點擊「登錄證據」按鈕
3. 選擇證據類型：`web_search`（網路搜尋）、`uploaded_doc`（上傳文件）、`engineering_reasoning`（工程推理）
4. 填寫標題、來源、摘要
5. 提交後，KPI 卡片自動更新達成狀態

### 4.2 從 Track 假設詳情登錄

1. 在 Track 頁面點擊某個假設展開詳情
2. 在實驗記錄區塊點擊「新增證據」
3. 填寫實驗結果與證據資料
4. 提交後，假設的驗證狀態自動更新

---

## 5. 8-Gate 系統

系統設有 8 個品質關卡，確保設計流程的完整性與嚴謹度。每個 Gate 必須通過才能進入下一階段。

| Gate | 階段 | 通過條件 |
|------|------|----------|
| **1.1** | Define | Mission 已定義 + KPI >= 3 且皆有量測方法 |
| **1.2** | Define | 假設 >= 10 + 高風險假設 >= 3 + 矛盾 >= 3 |
| **PG1** | Define → Diverge | CLD 已建立 + Breakpoints >= 3 |
| **2.1** | Diverge | >= 3 個高風險假設有對應驗證實驗 |
| **2.2** | Diverge | 設計方案 >= 3 |
| **PG2** | Diverge → Converge | >= 1 個方案通過 Pre-CAD 審查 |
| **3.2** | Converge | 決策記錄已簽核（confirmed 或 signed） |
| **PG3** | Converge → Release | 所有核心 artifacts 已發佈（需人工確認） |

### 如何檢查 Gate 狀態

- **自動檢查**：切換頁面時系統自動呼叫 Gate API
- **手動檢查**：在 Dashboard 點擊 Gate 狀態圖標，查看各項 checklist 的通過/未通過明細
- 未通過的 Gate 會顯示具體原因（例如「KPI 不足：需要 >= 3，目前 1」）

---

## 6. FAQ 常見問題

### Q1: 如何新增專案？

在 Dashboard 頁面點擊「新增專案」按鈕，輸入專案名稱後即可建立。新專案會自動建立於 Supabase 資料庫中。

### Q2: 如何匯出設計報告？

在 Decide 頁面（或任何階段）使用「匯出」功能：
- 選擇匯出格式：Markdown 或 JSON
- 選擇要匯出的區段（預設全部）
- 系統產生完整報告檔案供下載

### Q3: LLM 回應超時怎麼辦？

AI 呼叫（如 TRIZ 求解、子系統建議）可能因 Anthropic API 回應延遲而超時。解決方式：

1. **重試**：大多數情況下重新點擊即可成功
2. **檢查 API Key**：確認 `.env` 中的 `ANTHROPIC_API_KEY` 正確且有足夠額度
3. **查看錯誤代碼**：
   - `503 RATE_LIMIT`：API 被限流，請等待 1-2 分鐘後重試
   - `503 SERVICE_UNAVAILABLE`：Anthropic 服務暫時不可用
   - `503 AI_SERVICE_ERROR`：Anthropic 回傳錯誤，請檢查 API 狀態頁
4. **縮短輸入**：若送出的文字過長，嘗試精簡後重試

### Q4: AI 判定結果可以修改嗎？

可以。所有 AI 輔助功能（MUST 評分、Pre-CAD 5D 分析、風險評估等）都是「AI 建議 + 人工確認」模式。工程師可以：
- 覆寫 AI 的 Pass/Fail 判定
- 調整分數與權重
- 新增 AI 未提到的項目

### Q5: 如何將知識回寫到知識庫？

在 Decide 頁面完成決策後，點擊「知識回寫」按鈕。系統會自動將以下 6 類資產寫入知識庫：
- 約束條件 (Constraints)
- 假設 (Assumptions)
- 矛盾與解法 (Contradictions & Solutions)
- 風險 (Risks)
- 實驗記錄 (Experiments)
- 決策記錄 (Decisions)

### Q6: 可以多人同時使用同一專案嗎？

可以。系統使用 Supabase 作為後端資料庫，支援多人同時操作。每位使用者需透過 Supabase Auth 登入，操作紀錄會綁定使用者身分。

### Q7: Docker 部署後如何存取？

使用 `docker-compose up` 啟動後：
- 前端：`http://localhost:5173`
- 後端 API：`http://localhost:8000`
- Swagger 文件：`http://localhost:8000/docs`
