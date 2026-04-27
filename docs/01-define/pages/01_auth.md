---
id: P01
file_id: "01"
page_name: Auth
route_path: /auth
page_type: auth
phase: null
ia_group: public
gate: null
protected: false
dev_only: false
source_component: src/pages/Auth.tsx
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

# Page-Level Prompt: Auth 登入/註冊

> 統一的身份驗證頁面，提供登入、註冊與忘記密碼三種視圖切換，使用 Supabase Auth 進行身份管理。

---

## [PAGE META]
- **primary_goal**: 讓使用者透過 Email/Password 登入系統或建立新帳號
- **secondary_goal**: 提供忘記密碼流程，寄送重設連結至信箱
- **target_users**: 所有未登入的使用者（RD 工程師、專案管理者）
- **entry_point**: 應用程式根路徑未登入時自動導向、或使用者手動訪問
- **expected_time_on_page**: 30 秒 ~ 2 分鐘

---

## [STRUCTURE: SECTIONS]
1. **LogoHeader**
   - section_type: branding
   - section_purpose: 顯示應用程式 Logo、名稱與當前視圖提示文字
2. **AuthForm**
   - section_type: form
   - section_purpose: 根據 view 狀態切換登入/註冊/忘記密碼表單
3. **ViewSwitcher**
   - section_type: navigation
   - section_purpose: 提供切換 login/signup/forgot 視圖的文字連結
4. **Footer**
   - section_type: branding
   - section_purpose: 顯示版本號與系統描述

---

## [SECTION COMPONENT SPEC]

### Section: LogoHeader
- **layout**: 垂直置中，space-y-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Logo | `<img>` | required | logo-delta.svg, 56x56px, rounded-2xl, shadow-card |
  | Title | `<h1>` | required | "RD Design Copilot", text-2xl font-bold tracking-tight |
  | Subtitle | `<p>` | required | 依 view 動態切換："登入以繼續" / "建立帳號" / "重設密碼" |
- **states**: 無特殊狀態
- **copy_constraints**: Title 固定為品牌名稱，不可更改

### Section: AuthForm
- **layout**: Card > CardContent (p-6) > form (space-y-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | `<button>` | optional | 僅 forgot view 顯示，ArrowLeft icon + "返回登入"，切回 login view |
  | DisplayNameInput | Input | optional | 僅 signup view 顯示，User icon，placeholder "你的名稱"，required |
  | EmailInput | Input | required | Mail icon，type="email"，placeholder "you@example.com"，required |
  | PasswordInput | Input | optional | 非 forgot view 顯示，Lock icon，type="password"，placeholder "至少 6 個字元"，minLength=6，required |
  | SubmitButton | Button | required | w-full，disabled={isLoading}，文字依 view 切換："登入" / "註冊" / "寄送重設連結" |
  | LoadingSpinner | Loader2 | optional | 僅 isLoading 時顯示，h-4 w-4 mr-2 animate-spin |
- **states**:
  - default: 表單可輸入，按鈕可點擊
  - loading: SubmitButton disabled，顯示 Loader2 旋轉圖示
  - error: toast.error 顯示錯誤訊息（如密碼錯誤、帳號已存在等）
  - success (login): toast.success "登入成功" 後導向 /projects
  - success (signup): toast.success "註冊成功！請檢查 Email 完成驗證。"
  - success (forgot): toast.success "重設連結已寄送至您的信箱"
- **copy_constraints**: 所有 Input 的 label 與 placeholder 使用繁體中文，icon 使用 lucide-react

### Section: ViewSwitcher
- **layout**: mt-4 space-y-2 text-center，位於 form 下方 CardContent 內
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ForgotLink | `<button>` | optional | 僅 login view 顯示，"忘記密碼？"，切換至 forgot view |
  | SignupLink | `<button>` | optional | 僅 login view 顯示，"還沒有帳號？點此註冊"，切換至 signup view |
  | LoginLink | `<button>` | optional | 僅 signup view 顯示，"已有帳號？點此登入"，切換至 login view |
- **states**: hover 時 text-muted-foreground -> text-primary，transition-colors
- **copy_constraints**: 連結文字需清晰表達目的動作

### Section: Footer
- **layout**: text-center，text-[11px] text-muted-foreground
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | VersionText | `<p>` | required | "RD Design Copilot v1.1 · AI 輔助概念設計系統" |
- **states**: 無
- **copy_constraints**: 版本號需隨實際版本更新

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入 `/auth`，預設顯示 login view
2. 輸入 Email 與 Password，點擊「登入」
3. 成功 → toast.success "登入成功" → `navigate("/projects")`
4. 失敗 → toast.error 顯示錯誤訊息
5. 點擊「還沒有帳號？點此註冊」→ 切換至 signup view，顯示 DisplayName 欄位
6. 填寫 DisplayName、Email、Password，點擊「註冊」
7. 成功 → toast.success "註冊成功！請檢查 Email 完成驗證。"（emailRedirectTo 為 window.location.origin）
8. 點擊「忘記密碼？」→ 切換至 forgot view，隱藏 Password 欄位
9. 輸入 Email，點擊「寄送重設連結」
10. 成功 → toast.success "重設連結已寄送至您的信箱"（redirectTo 為 `/reset-password`）

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | 全頁置中，max-w-sm (384px) | auth-shell 全高置中 |
| Tablet (768 ~ 1023px) | 同 Desktop | 無差異 |
| Mobile (< 768px) | 同 Desktop，max-w-sm 自適應 | 表單寬度隨螢幕縮放，padding 保持一致 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload |
  |:-------|:---------|:--------|
  | 登入 | `supabase.auth.signInWithPassword` | `{ email, password }` |
  | 註冊 | `supabase.auth.signUp` | `{ email, password, options: { data: { display_name }, emailRedirectTo } }` |
  | 忘記密碼 | `supabase.auth.resetPasswordForEmail` | `(email, { redirectTo: origin + "/reset-password" })` |
- **error_cases**:
  - 無效的 Email 格式 → 瀏覽器原生驗證
  - 密碼少於 6 字元 → 瀏覽器原生 minLength 驗證
  - 帳號不存在 / 密碼錯誤 → Supabase 回傳 error.message，toast.error 顯示
  - 帳號已存在（註冊）→ Supabase 回傳 error.message，toast.error 顯示
  - 網路錯誤 → catch 區塊顯示 "操作失敗"

---

## [ACCEPTANCE CRITERIA]
- [ ] 預設進入頁面顯示 login view，含 Email 和 Password 欄位
- [ ] 可切換至 signup view，額外顯示 DisplayName 欄位
- [ ] 可切換至 forgot view，僅顯示 Email 欄位與「寄送重設連結」按鈕
- [ ] forgot view 頂部顯示「返回登入」按鈕（ArrowLeft icon）
- [ ] 所有 Input 前方有對應 lucide icon（Mail / Lock / User）
- [ ] 表單送出時按鈕 disabled 並顯示 Loader2 旋轉動畫
- [ ] 登入成功導向 `/projects`，並顯示 toast.success
- [ ] 註冊成功顯示 Email 驗證提示 toast
- [ ] 忘記密碼成功顯示重設連結已寄送 toast
- [ ] 所有 API 錯誤以 toast.error 呈現
- [ ] 頁面底部顯示版本資訊
- [ ] 整體佈局垂直水平置中，最大寬度 max-w-sm
