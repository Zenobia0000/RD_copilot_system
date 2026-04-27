---
id: P16
file_id: "16"
page_name: Settings
route_path: /settings
page_type: form
phase: null
ia_group: system
gate: null
protected: true
dev_only: false
source_component: src/pages/Settings.tsx
spec_version: 1.0
ia_version: 1.2
status: stable
last_updated: 2026-04-24
api_resources: [user_profile]
modules: []
depends_on: []
absorbed_specs: []
optional_sections: []
---

# Page-Level Prompt: Settings 設定

> 使用者帳號資料、密碼變更與外觀主題偏好的統一管理頁面。

---

## [PAGE META]
- **primary_goal**: 讓使用者更新個人顯示名稱、變更密碼與切換系統主題
- **secondary_goal**: 展示帳號 Email（唯讀）與系統版本資訊
- **target_users**: 所有已登入使用者（RD 工程師、專案管理者）
- **entry_point**: 側邊欄或導覽列的「設定」連結
- **expected_time_on_page**: 30 秒 ~ 2 分鐘

---

## [STRUCTURE: SECTIONS]
1. **PageHeader**
   - section_type: header
   - section_purpose: 顯示頁面標題「設定」與副標題說明
2. **ProfileCard**
   - section_type: form
   - section_purpose: 顯示唯讀 Email 與可編輯的顯示名稱，提供儲存功能
3. **PasswordCard**
   - section_type: form
   - section_purpose: 提供新密碼輸入與更新功能
4. **ThemeCard**
   - section_type: interactive
   - section_purpose: 提供淺色/深色/跟隨系統三種主題切換
5. **Footer**
   - section_type: branding
   - section_purpose: 顯示版本號與版權資訊

---

## [SECTION COMPONENT SPEC]

### Section: PageHeader
- **layout**: 頂部區塊，無 Card 包裝
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Title | `<h1>` | required | "設定", text-2xl font-bold tracking-tight |
  | Subtitle | `<p>` | required | "管理您的帳號資訊與系統偏好", text-sm text-muted-foreground mt-1 |
- **states**: 無
- **copy_constraints**: 標題與副標題固定

### Section: ProfileCard
- **layout**: Card > CardHeader + CardContent (space-y-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CardIcon | User (lucide) | required | CardTitle 前方 h-4 w-4 icon |
  | CardTitle | `<CardTitle>` | required | "個人資料", text-lg |
  | CardDescription | `<CardDescription>` | required | "更新您的顯示名稱與帳號資訊" |
  | EmailLabel | `<Label>` | required | "Email" |
  | EmailIcon | Mail (lucide) | required | h-4 w-4 text-muted-foreground |
  | EmailText | `<span>` | required | 顯示 user.email，text-sm text-muted-foreground |
  | ReadOnlyBadge | `<Badge>` | required | variant="outline", "唯讀", text-[10px] |
  | DisplayNameLabel | `<Label>` | required | htmlFor="displayName", "顯示名稱" |
  | DisplayNameInput | `<Input>` | required | id="displayName", placeholder "您的名稱", disabled={loadingProfile} |
  | SaveButton | `<Button>` | required | "儲存", size="sm", disabled={saving \|\| loadingProfile} |
  | SaveSpinner | Loader2 (lucide) | optional | 僅 saving 時顯示，h-3.5 w-3.5 mr-1.5 animate-spin |
- **states**:
  - loading: Input disabled，等待 profile 載入
  - default: Input 可編輯，按鈕可點擊
  - saving: SaveButton disabled，顯示 Loader2
  - success: toast.success "已更新顯示名稱"
  - error: toast.error "儲存失敗: {message}"
- **copy_constraints**: Email 為唯讀欄位，不可編輯

### Section: PasswordCard
- **layout**: Card > CardHeader + CardContent (space-y-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CardIcon | Lock (lucide) | required | CardTitle 前方 h-4 w-4 icon |
  | CardTitle | `<CardTitle>` | required | "變更密碼", text-lg |
  | CardDescription | `<CardDescription>` | required | "設定新的登入密碼" |
  | PasswordLabel | `<Label>` | required | htmlFor="newPassword", "新密碼" |
  | PasswordInput | `<Input>` | required | id="newPassword", type="password", placeholder "至少 6 個字元", minLength=6 |
  | UpdateButton | `<Button>` | required | "更新密碼", size="sm", disabled={changingPw \|\| newPassword.length < 6} |
  | UpdateSpinner | Loader2 (lucide) | optional | 僅 changingPw 時顯示，h-3.5 w-3.5 mr-1.5 animate-spin |
- **states**:
  - default: Input 可輸入，按鈕 disabled 直到密碼 >= 6 字元
  - changing: UpdateButton disabled，顯示 Loader2
  - success: toast.success "密碼已更新"，清空 newPassword
  - error (validation): toast.error "密碼至少 6 個字元"
  - error (api): toast.error "密碼更新失敗: {message}"
- **copy_constraints**: 密碼最小長度 6 字元

### Section: ThemeCard
- **layout**: Card > CardHeader + CardContent > grid grid-cols-3 gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CardIcon | Sun (lucide) | required | CardTitle 前方 h-4 w-4 icon |
  | CardTitle | `<CardTitle>` | required | "外觀主題", text-lg |
  | CardDescription | `<CardDescription>` | required | "選擇系統的顯示風格" |
  | LightButton | `<button>` | required | Sun icon (h-6 w-6) + "淺色", 圓角卡片樣式 |
  | DarkButton | `<button>` | required | Moon icon (h-6 w-6) + "深色", 圓角卡片樣式 |
  | SystemButton | `<button>` | required | Monitor icon (h-6 w-6) + "跟隨系統", 圓角卡片樣式 |
- **states**:
  - active: border-primary bg-primary/5，icon 與文字 text-primary
  - inactive: border-border hover:border-muted-foreground/30，icon 與文字 text-muted-foreground
- **copy_constraints**: 三個選項標籤固定為「淺色」「深色」「跟隨系統」

### Section: Footer
- **layout**: Separator 分隔線之後，text-center text-[11px] text-muted-foreground pb-6
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | VersionText | `<div>` | required | "RD Design Copilot v1.1 · (C) 2026" |
- **states**: 無
- **copy_constraints**: 版本號需隨實際版本更新

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入 `/settings`，頁面自動載入 profile（displayName）
2. 載入中 displayName Input 為 disabled 狀態
3. 載入完成後，使用者可編輯顯示名稱並點擊「儲存」
4. 儲存成功 → toast.success "已更新顯示名稱"
5. 使用者可在密碼區塊輸入新密碼（>= 6 字元後按鈕啟用）
6. 點擊「更新密碼」→ 成功 → toast.success "密碼已更新"，清空密碼欄位
7. 使用者可點擊三個主題按鈕即時切換外觀，選中項目以 primary 色框標示

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1024px) | page-shell-narrow max-w-2xl 置中 | 三欄主題按鈕水平排列 |
| Tablet (768 ~ 1023px) | 同 Desktop | 無差異 |
| Mobile (< 768px) | max-w-2xl 自適應 | 主題按鈕 grid-cols-3 自適應縮放 |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload |
  |:-------|:---------|:--------|
  | 讀取 Profile | `supabase.from('profiles').select('display_name').eq('user_id', user.id).single()` | 無 |
  | 更新顯示名稱 | `supabase.from('profiles').update({ display_name }).eq('user_id', user.id)` | `{ display_name: string }` |
  | 更新密碼 | `supabase.auth.updateUser({ password })` | `{ password: string }` |
  | 取得當前使用者 | `useAuth()` — 從 AuthContext 取得 user 物件 | 無 |
  | 取得/設定主題 | `useTheme()` — 從 ThemeProvider 取得 theme 與 setTheme | 無 |
- **error_cases**:
  - Profile 載入失敗 → data 為 null，displayName 保持空字串
  - 儲存顯示名稱失敗 → toast.error "儲存失敗: {message}"
  - 密碼少於 6 字元 → toast.error "密碼至少 6 個字元"（前端驗證）
  - 密碼更新 API 失敗 → toast.error "密碼更新失敗: {message}"

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面標題顯示「設定」與副標題說明文字
- [ ] Profile 卡片顯示唯讀 Email（含 Badge "唯讀"）與可編輯的顯示名稱
- [ ] 載入 profile 期間 displayName Input 為 disabled
- [ ] 儲存顯示名稱時按鈕 disabled 並顯示 Loader2 旋轉動畫
- [ ] 儲存成功顯示 toast.success，失敗顯示 toast.error
- [ ] 密碼欄位輸入少於 6 字元時更新按鈕保持 disabled
- [ ] 密碼更新成功後清空密碼輸入欄位並顯示 toast.success
- [ ] 主題卡片顯示三個選項（淺色/深色/跟隨系統），選中項目有 primary 邊框高亮
- [ ] 點擊主題按鈕即時切換外觀
- [ ] 頁面底部以 Separator 分隔，顯示版本資訊
- [ ] 整體佈局 page-shell-narrow max-w-2xl
