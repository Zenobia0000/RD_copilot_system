# Playwright E2E 補測 WBS（skeleton）

> **版本**：0.1 | **日期**：2026-04-09 | **狀態**：Skeleton · 待排程
> **前置**：`Subsystem_Interface_Development_WBS.md` 11.3 已於 Wave 5 降級為 Vitest + Testing Library component tests。此文件紀錄 Playwright E2E **被延後的原因** 與 **恢復時的待辦**。

---

## 為什麼延後

1. **Harness 從零建**：repo 目前沒有 Playwright 設定、沒有 browser download workflow、沒有 dev server 啟動 fixture、沒有 Supabase seed 資料檔。
2. **Session scope**：單一 agentic session 難以穩定完成「裝 deps → 下載 browser → 寫 config → 寫 spec → 在無頭瀏覽器裡過完流程」的全鏈路，會大量耗 token 且 debug 迴圈難收斂。
3. **Vitest 已提供 32 個 component tests**：覆蓋 4 個關鍵對話框/面板的行為層，Playwright 真正增加的價值只在「跨頁面流程 + 真瀏覽器互動」。

## 恢復時的待辦（Definition of Ready）

### Infrastructure

- `npm install -D @playwright/test`
- `npx playwright install --with-deps chromium`（或依 CI 環境選）
- `playwright.config.ts` 於 repo root，指定 `baseURL`、`webServer` 自動啟 dev server
- `e2e/` 目錄於 repo root，設為 Playwright testDir
- `package.json` scripts 新增：`test:e2e`、`test:e2e:headed`
- CI workflow：Playwright job 獨立於 unit test job，artifact 上傳 trace

### Backend stub/mock 策略

- 決定 E2E 是對真後端還是 stub：
  - **(a) 真後端**：需要 `.env.test`、seed Supabase schema、LLM mock（Anthropic 測試 key 或 httpx hook）
  - **(b) MSW（推薦）**：瀏覽器端攔截 `fetch` 讓 E2E 不依賴 backend 實例
- 若選 (b)：`src/mocks/handlers.ts` 定義 `POST /subsystems/suggest` 等 endpoint 的 canned 回應 *(v9: 原 `/scamper/subsystem-suggestions`)*
- 若選 (a)：建立 `backend/scripts/seed_e2e.py` 產生固定 brief / contradictions / project

### 必測流程（從 WBS 11.3 原始描述：Suggest → Map → Override → Confirm → 決策中心 enabled）*(v9: 原 SCAMPER enabled)*

1. **登入 / 進 project**
  - 已有 `id` 的 project landing 頁可直達 `/create?projectId=...`
2. **完成 Brief 與 TRIZ**
  - 用 canned brief + 至少 1 個矛盾跳到 Tab ②
3. **Suggest**
  - 點「AI 建議子系統」
  - 等待 `POST /subsystems/suggest` 完成 *(v9: 原 `/scamper/subsystem-suggestions`)*
  - 斷言三層樹渲染、至少 1 個 module 可見
4. **Package Map**
  - 斷言 `PackageMapPanel` 的 inline SVG 存在
  - 若有 clash，斷言紅色 banner 出現
5. **Override**
  - 點任一 module 的「我來給數字」
  - 填 bbox + mass_g → 送出
  - 斷言該 module 的 badge 變「RD 簽核」或 reference_source 有 `rd_override:` 前綴
6. **Confirm**
  - 勾選 ≥1 個 module 的 confirmed checkbox
7. **決策中心解鎖** *(v9: 原 SCAMPER 解鎖)*
  - 斷言「下一步」按鈕 `disabled === false`
  - 點下一步，斷言成功進入決策中心步驟

### 次要流程

- Overlay 對話框開啟 → 填 zone → 試算 → 關閉 → 主 Package Map 不變
- 推升 learned → toast 成功
- 無 spatial 資料時 PackageMapPanel 顯示佔位符不報錯
- 決策中心解鎖閘：未確認任何 module 時「下一步」`disabled === true` + 提示文字 *(v9: 原 SCAMPER 解鎖閘)*

### 非功能性

- 每個 spec 平均執行時間 < 10 秒
- CI artifact 上 trace.zip + screenshot on failure
- flaky retry ≤ 1
- 並行度 = 1（subsystems 共用同一個 project id 情境下避免競態）

## 預估工作量


| 任務                      | 估時       |
| ----------------------- | -------- |
| Infrastructure + config | 0.5 day  |
| MSW handlers + fixtures | 0.5 day  |
| 5 個主流程 spec             | 1 day    |
| CI 整合 + debug flaky     | 0.5 day  |
| 文件（本文件補齊實際結果）           | 0.25 day |


**總計**：~ 2.75 day（一人）

## 依賴

- 本 WBS 10.1（決策中心讀契約，v9: 原 SCAMPER）完成後 E2E 流程才能走到最後一步的 enabled 斷言
- 本 WBS 10.3（PreCadReview wiring）若未完成，Pre-CAD 相關 E2E 需 skip 或僅測 trace 為 null 的佔位表現

---

**修訂紀錄**

- 2026-04-09 v0.1：skeleton，紀錄 Wave 5 延後決策與恢復條件。

