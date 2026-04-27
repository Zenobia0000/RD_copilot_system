---
id: P02
file_id: "02"
page_name: ResetPassword
route_path: /reset-password
page_type: auth
phase: null
ia_group: public
gate: null
protected: false
dev_only: false
source_component: src/pages/ResetPassword.tsx
spec_version: 1.0
ia_version: 1.2
status: stable
last_updated: 2026-04-24
api_resources: []
modules: []
depends_on: [P01]
absorbed_specs: []
optional_sections: []
---

# Page-Level Prompt: ResetPassword 重設密碼

> 接收 Email 中的密碼重設連結，讓使用者輸入新密碼完成重設後自動導向首頁。

---

## [PAGE META]
- **primary_goal**: 讓使用者透過重設連結安全地更新密碼
- **secondary_goal**: 對無效連結提供明確的錯誤提示與返回登入導航
- **target_users**: 已發起忘記密碼流程的使用者
- **entry_point**: 從重設密碼 Email 中的連結點擊進入（帶有 recovery hash）
- **expected_time_on_page**: 15 秒 ~ 1 分鐘

---

## [STRUCTURE: SECTIONS]
1. **InvalidLinkState**
   - section_type: error
   - section_purpose: 當 URL 不含有效 recovery token 時，顯示錯誤提示與返回登入按鈕
2. **LogoHeader**
   - section_type: branding
   - section_purpose: 顯示應用程式 Logo、標題「重設密碼」與輔助說明文字
3. **ResetForm**
   - section_type: form
   - section_purpose: 提供新密碼輸入欄位與送出按鈕，完成密碼更新

---

## [SECTION COMPONENT SPEC]

### Section: InvalidLinkState
- **layout**: auth-shell 置中，Card > CardContent (p-6 text-center space-y-3)，max-w-sm
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ErrorText | `<p>` | required | "無效的重設連結"，text-muted-foreground |
  | BackButton | Button | required | variant="outline"，"返回登入"，onClick navigate("/auth") |
- **states**:
  - default: isRecovery = false 時顯示此區塊
- **copy_constraints**: 錯誤文字需簡潔，明確告知連結無效

### Section: LogoHeader
- **layout**: 垂直置中，space-y-2
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Logo | `<img>` | required | logo-delta.svg, h-12 w-12, rounded-2xl, shadow-card |
  | Title | `<h1>` | required | "重設密碼"，text-2xl font-bold tracking-tight |
  | Subtitle | `<p>` | required | "請輸入新的密碼"，text-sm text-muted-foreground |
- **states**: 僅在 isRecovery = true 時顯示
- **copy_constraints**: 標題固定為「重設密碼」

### Section: ResetForm
- **layout**: Card > CardContent (p-6) > form (space-y-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PasswordInput | Input | required | Lock icon，type="password"，label "新密碼"，placeholder "至少 6 個字元"，minLength=6，required |
  | SubmitButton | Button | required | w-full，disabled={isLoading}，文字 "重設密碼" |
  | LoadingSpinner | Loader2 | optional | 僅 isLoading 時顯示，h-4 w-4 mr-2 animate-spin |
- **states**:
  - default: 表單可輸入，按鈕可點擊
  - loading: SubmitButton disabled，顯示 Loader2 旋轉圖示
  - validation_error: 密碼少於 6 字元 → toast.error "密碼至少 6 個字元"（前端檢查）
  - api_error: Supabase updateUser 失敗 → toast.error 顯示 error.message
  - success: toast.success "密碼已重設，將自動導向首頁" → 1.5 秒後 navigate("/projects")
- **copy_constraints**: 按鈕文字固定 "重設密碼"，密碼欄位 label 為 "新密碼"

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者從 Email 點擊重設連結，帶有 recovery hash 進入 `/reset-password`
2. 頁面 useEffect 檢查 `window.location.hash` 是否包含 `type=recovery`
3. 同時監聽 `supabase.auth.onAuthStateChange`，等待 `PASSWORD_RECOVERY` 事件
4. 若 recovery 有效 (isRecovery = true) → 顯示 LogoHeader + ResetForm
5. 若 recovery 無效 (isRecovery = false) → 顯示 InvalidLinkState
6. 使用者輸入新密碼（至少 6 字元），點擊「重設密碼」
7. 前端檢查：密碼 < 6 字元 → toast.error "密碼至少 6 個字元"，中止送出
8. 呼叫 `supabase.auth.updateUser({ password })` 更新密碼
9. 成功 → toast.success "密碼已重設，將自動導向首頁" → setTimeout 1500ms 後 navigate("/projects")
10. 失敗 → toast.error 顯示錯誤訊息

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | 全頁置中，max-w-sm (384px) | auth-shell 全高置中 |
| Tablet (768 ~ 1023px) | 同 Desktop | 無差異 |
| Mobile (< 768px) | 同 Desktop，max-w-sm 自適應 | 表單寬度隨螢幕縮放 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload |
  |:-------|:---------|:--------|
  | 監聽恢復事件 | `supabase.auth.onAuthStateChange` | 監聽 `PASSWORD_RECOVERY` 事件 |
  | 更新密碼 | `supabase.auth.updateUser` | `{ password }` |
- **error_cases**:
  - 無效的 recovery token → isRecovery 維持 false，顯示 InvalidLinkState
  - 密碼少於 6 字元 → 前端阻擋，toast.error "密碼至少 6 個字元"
  - Supabase updateUser 失敗 → toast.error 顯示 error.message
  - Recovery token 過期 → Supabase 回傳錯誤，toast.error 顯示

---

## [ACCEPTANCE CRITERIA]
- [ ] 有效 recovery 連結進入時顯示重設密碼表單（Logo + 密碼輸入 + 送出按鈕）
- [ ] 無效連結進入時顯示「無效的重設連結」錯誤畫面與「返回登入」按鈕
- [ ] 透過 URL hash 和 onAuthStateChange 雙重偵測 PASSWORD_RECOVERY 事件
- [ ] 密碼欄位前方顯示 Lock icon
- [ ] 密碼少於 6 字元送出時顯示 toast.error 錯誤提示
- [ ] 表單送出時按鈕 disabled 並顯示 Loader2 旋轉動畫
- [ ] 密碼重設成功後顯示 toast.success 並於 1.5 秒後自動導向 `/projects`
- [ ] API 錯誤以 toast.error 呈現
- [ ] 頁面 unmount 時正確取消 onAuthStateChange subscription
- [ ] 整體佈局垂直水平置中，最大寬度 max-w-sm，與 Auth 頁面風格一致
