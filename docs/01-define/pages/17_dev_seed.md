# Page-Level Prompt: DevSeed 開發種子資料

> 開發環境專用工具頁面，用於快速建立或清除 Supabase 中的展示專案資料。

---

## [PAGE META]
- **page_name**: DevSeed
- **route_path**: `/dev/seed`
- **page_type**: utility (DEV only)
- **primary_goal**: 讓開發者一鍵 seed 3 個不同生命週期階段的展示專案
- **secondary_goal**: 提供清除所有展示資料的功能，保持開發環境整潔
- **target_users**: 前端/後端開發者（僅開發環境可見）
- **entry_point**: 直接輸入 URL `/dev/seed`，僅在 `import.meta.env.DEV` 為 true 時可存取
- **expected_time_on_page**: 10 秒 ~ 30 秒

---

## [STRUCTURE: SECTIONS]
1. **SeedCard**
   - section_type: action-panel
   - section_purpose: 提供 seed 與 clear 兩個操作按鈕，並顯示操作結果

---

## [SECTION COMPONENT SPEC]

### Section: SeedCard
- **layout**: page-shell-narrow py-10 > Card > CardHeader + CardContent (space-y-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CardTitle | `<CardTitle>` | required | "Dev Seed Tool" |
  | Description | `<p>` | required | "Seed 3 showcase projects at different lifecycle stages into Supabase.", text-sm text-muted-foreground |
  | SeedButton | `<Button>` | required | "Seed Showcase Projects", disabled={loading}, default variant |
  | ClearButton | `<Button>` | required | "Clear All Showcase", disabled={loading}, variant="destructive" |
  | StatusOutput | `<pre>` | optional | 僅 status 非空時顯示，mt-4 p-3 bg-muted rounded text-xs whitespace-pre-wrap |
- **states**:
  - idle: 兩按鈕可點擊，無 status 輸出
  - loading (seed): 兩按鈕 disabled，status 顯示 "Seeding 3 showcase projects..."
  - loading (clear): 兩按鈕 disabled，status 顯示 "Clearing all showcase data..."
  - success (seed): status 顯示 "Done! Created {n} projects:\n{ids}"
  - success (clear): status 顯示 "All showcase data cleared."
  - error: status 顯示 "Error: {message}"
- **copy_constraints**: 所有文字為英文（開發者工具頁面）

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 開發者進入 `/dev/seed`（僅開發環境可用）
2. 點擊「Seed Showcase Projects」→ 呼叫 `seedShowcaseProjects()`
3. 操作進行中兩按鈕皆 disabled，status 顯示進度訊息
4. 成功 → status 顯示建立的專案數量與 ID 列表
5. 失敗 → status 顯示 Error 訊息
6. 點擊「Clear All Showcase」→ 呼叫 `clearAllShowcaseData()`
7. 成功 → status 顯示 "All showcase data cleared."

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | page-shell-narrow 置中 | 兩按鈕水平排列 (flex gap-3) |
| Tablet (768 ~ 1023px) | 同 Desktop | 無差異 |
| Mobile (< 768px) | 同 Desktop，自適應寬度 | 按鈕可能換行 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload |
  |:-------|:---------|:--------|
  | Seed 展示專案 | `seedShowcaseProjects()` | 無（內建 3 個專案定義） |
  | 清除展示資料 | `clearAllShowcaseData()` | 無 |
- **error_cases**:
  - Supabase 連線失敗 → catch 區塊，status 顯示 "Error: {message}"
  - 權限不足 → 同上
  - 重複 seed → 依 API 實作決定（可能產生重複資料）

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面僅在開發環境 (`import.meta.env.DEV`) 下可存取
- [ ] 卡片標題顯示 "Dev Seed Tool" 與說明文字
- [ ] 「Seed Showcase Projects」按鈕點擊後建立 3 個展示專案
- [ ] 「Clear All Showcase」按鈕使用 destructive variant 樣式
- [ ] 操作進行中兩個按鈕皆為 disabled 狀態
- [ ] 操作結果以 `<pre>` 區塊顯示，支援多行格式化輸出
- [ ] 錯誤訊息以 "Error: {message}" 格式顯示在 status 區塊
- [ ] 整體佈局 page-shell-narrow py-10
