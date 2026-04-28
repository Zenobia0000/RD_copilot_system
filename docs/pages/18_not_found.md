---
id: P18
file_id: "18"
page_name: NotFound
route_path: "*"
page_type: error
phase: null
ia_group: system
gate: null
protected: false
dev_only: false
source_component: src/pages/NotFound.tsx
spec_version: 1.0
ia_version: 1.2
status: stable
last_updated: 2026-04-24
api_resources: []
modules: []
depends_on: []
absorbed_specs: []
optional_sections: []
---

# Page-Level Prompt: NotFound 404 頁面未找到

> 當使用者訪問不存在的路由時顯示的 404 錯誤頁面，提供返回首頁的連結。

---

## [PAGE META]
- **primary_goal**: 告知使用者該頁面不存在，引導返回首頁
- **secondary_goal**: 記錄無效路由訪問至 console 以供除錯
- **target_users**: 所有使用者（誤訪無效路徑時）
- **entry_point**: 輸入任何未匹配的 URL 路徑
- **expected_time_on_page**: 5 秒 ~ 15 秒

---

## [STRUCTURE: SECTIONS]
1. **ErrorContent**
   - section_type: informational
   - section_purpose: 顯示 404 錯誤碼、提示訊息與返回首頁連結

---

## [SECTION COMPONENT SPEC]

### Section: ErrorContent
- **layout**: auth-shell bg-muted > div (text-center)，垂直水平置中
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ErrorCode | `<h1>` | required | "404", text-4xl font-bold mb-4 |
  | ErrorMessage | `<p>` | required | "Oops! Page not found", text-xl text-muted-foreground mb-4 |
  | HomeLink | `<a>` | required | "Return to Home", href="/", text-primary underline hover:text-primary/90 |
- **states**: 無（靜態頁面）
- **copy_constraints**: 錯誤碼與訊息使用英文，保持簡潔

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者訪問不存在的路由路徑
2. React Router catch-all 匹配，渲染 NotFound 元件
3. useEffect 觸發 `console.error` 記錄無效路徑 (`location.pathname`)
4. 使用者閱讀 404 訊息後點擊 "Return to Home" 連結返回首頁 (`/`)

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | auth-shell 全頁置中 | 內容垂直水平置中 |
| Tablet (768 ~ 1023px) | 同 Desktop | 無差異 |
| Mobile (< 768px) | 同 Desktop | 無差異，文字自適應 |

---

## [DATA & API]
- **uses_api**: false
- **endpoints**: 無
- **error_cases**: 無（頁面本身即為錯誤處理）

---

## [ACCEPTANCE CRITERIA]
- [ ] 訪問任何未定義路由時正確顯示此頁面
- [ ] 顯示 "404" 大標題（text-4xl font-bold）
- [ ] 顯示 "Oops! Page not found" 提示訊息
- [ ] 顯示 "Return to Home" 連結，點擊後導向 `/`
- [ ] 連結 hover 時顏色變化為 text-primary/90
- [ ] 頁面載入時 console.error 記錄無效的 pathname
- [ ] 整體佈局使用 auth-shell bg-muted，垂直水平置中
- [ ] 頁面為無狀態（stateless），無需任何 API 呼叫
