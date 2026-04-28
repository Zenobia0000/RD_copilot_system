# 02_Patterns — 互動模式規格

> Components 是「零件」，Patterns 是「常用組裝方法」。
> 有了 Patterns，團隊討論的是「選哪個」，不是「從零開始吵」。
>
> **本文件來源**：從 `universal_template/01_GLOBAL_SYSTEM_PROMPT [UX PATTERN LAYER]` + `[INTERACTION & ACCESSIBILITY LAYER]` + `[DATA PATTERN LAYER]` + 14 頁 page spec 提煉而來。§1-10 為通用 Atomic Design 模式；§11 為 RD Copilot 專用業務模式。

---

## 目錄

1. [Form Patterns](#1-form-patterns)
2. [Data Table Patterns](#2-data-table-patterns)
3. [Search & Filter Patterns](#3-search--filter-patterns)
4. [Navigation Patterns](#4-navigation-patterns)
5. [Feedback Patterns](#5-feedback-patterns)
6. [Empty / Error / Loading States](#6-empty--error--loading-states)
7. [Authentication Patterns](#7-authentication-patterns)
8. [Content Display Patterns](#8-content-display-patterns)
9. [Action Patterns](#9-action-patterns)
10. [Permission / Access Patterns](#10-permission--access-patterns)

---

## Pattern 文件結構（每個 Pattern 的標準格式）

```
### [Pattern 名稱]

**When to use**：什麼情境使用此 pattern
**Structure**：用哪些元件組成
**Behavior rules**：互動規則
**Edge cases**：例外處理（錯誤、無權限、loading）
**Copy rules**：文案模板
**Do / Don't**：常見錯法
```

---

## 1. Form Patterns

### 1.1 Single-Column Form（單欄表單）

**When to use**：
- 欄位 < 8 個的簡單表單（登入、聯絡、設定）
- Mobile-first 設計

**Structure**：
```
┌─────────────────────────┐
│ Form Title              │
│ Form Description        │
├─────────────────────────┤
│ Label                   │
│ ┌─────────────────────┐ │
│ │ Input               │ │
│ └─────────────────────┘ │
│ Helper text             │
│                         │
│ Label *                 │
│ ┌─────────────────────┐ │
│ │ Input               │ │
│ └─────────────────────┘ │
│ ❌ Error message        │
│                         │
│ ... more fields ...     │
│                         │
│ ┌───────┐ ┌───────────┐ │
│ │Cancel │ │  Submit ▶  │ │
│ └───────┘ └───────────┘ │
└─────────────────────────┘
```

**Behavior rules**：
- 欄位間距：`space.5` (20px)
- 必填標示：Label 後加紅色 `*`
- Validation timing：
  - 首次：submit 時驗證全部
  - 修正後：onChange 即時驗證（已觸發過的欄位）
- Error display：欄位下方紅色文字 + 紅色邊框
- Error summary：表單頂部顯示「有 N 個欄位需要修正」（超過 5 個錯誤時）
- Submit button：
  - 未修改 → disabled
  - 送出中 → loading spinner + disabled
  - 成功 → success toast + redirect / close
  - 失敗 → error toast + 保留表單內容

**Copy rules**：
| 場景 | 模板 | 範例 |
|------|------|------|
| 必填未填 | `請輸入{欄位名稱}` | 「請輸入電子郵件」 |
| 格式錯誤 | `{欄位名稱}格式不正確` | 「電子郵件格式不正確」 |
| 超過限制 | `{欄位名稱}不可超過{N}個字` | 「姓名不可超過 50 個字」 |
| 送出成功 | `{動作}成功` | 「設定已儲存」 |
| 送出失敗 | `{動作}失敗，請稍後再試` | 「儲存失敗，請稍後再試」 |

### 1.2 Multi-Column Form（多欄表單）

**When to use**：
- Desktop 上欄位多（> 8 個）且有邏輯分組
- 例：個人資料、地址填寫

**Structure**：
```
Desktop (> 1024px)：
┌──────────────────┬──────────────────┐
│ First Name       │ Last Name        │
│ [Input]          │ [Input]          │
├──────────────────┴──────────────────┤
│ Email                               │
│ [Input]                             │
├──────────────────┬──────────────────┤
│ City             │ Zip Code         │
│ [Input]          │ [Input]          │
└──────────────────┴──────────────────┘

Mobile (< 640px)：自動轉為 Single-Column
```

**Rules**：
- 只在邏輯相關時才並排（名+姓、城市+郵遞區號）
- 不要為了省空間而亂並排（Email 和電話不該並排）
- Grid: `grid-cols-2 gap-4` (desktop) → `grid-cols-1` (mobile)

### 1.3 Stepper / Wizard Form（步驟式表單）

**When to use**：
- 欄位多（> 12 個）且可分成邏輯步驟
- 例：註冊流程、結帳流程、設定精靈

**Structure**：
```
┌─────────────────────────────────────┐
│  ① 基本資料  ─── ② 偏好設定  ─── ③ 確認  │
│  (current)       (upcoming)    (upcoming)  │
├─────────────────────────────────────┤
│                                     │
│  Step 1 Content                     │
│  [Form Fields...]                   │
│                                     │
├─────────────────────────────────────┤
│         ┌────────┐  ┌────────────┐  │
│         │ 上一步 │  │  下一步 ▶  │  │
│         └────────┘  └────────────┘  │
└─────────────────────────────────────┘
```

**Behavior rules**：
- 步驟指示器：顯示當前步驟 + 總步驟數
- 每步驗證：按「下一步」時驗證當前步驟
- 可回退：已完成的步驟可點擊回去修改
- 最後一步：顯示所有填寫內容的摘要
- 離開保護：填寫中離開頁面要有確認 dialog

### 1.4 Inline Edit（行內編輯）

**When to use**：
- 修改單一欄位（如用戶暱稱、標題）
- 避免打開整個表單

**Structure**：
```
View 模式：
  [顯示值] [✏️ Edit]

Edit 模式：
  ┌──────────────┐ ┌────┐ ┌────┐
  │ [Input]      │ │ ✓  │ │ ✕  │
  └──────────────┘ └────┘ └────┘
```

**Rules**：
- 點擊 Edit → Input 出現 + auto focus
- Enter 確認、Esc 取消
- 儲存成功 → 恢復 View 模式 + 短暫綠色 flash

---

## 2. Data Table Patterns

### 2.1 Standard Data Table

**Structure**：
```
┌─────────────────────────────────────────┐
│ 📋 Table Title          [+ Add] [⚙️]   │
├─────────────────────────────────────────┤
│ 🔍 Search...   [Filter ▼] [Sort ▼]     │
├────┬───────────┬────────┬───────┬──────┤
│ ☐  │ Name ↕    │ Status │ Date  │ ...  │
├────┼───────────┼────────┼───────┼──────┤
│ ☐  │ Item 1    │ 🟢 Active │ 2024-01 │ ⋮ │
│ ☐  │ Item 2    │ 🔴 Inactive│ 2024-02 │ ⋮ │
│ ☐  │ Item 3    │ 🟡 Pending │ 2024-03 │ ⋮ │
├────┴───────────┴────────┴───────┴──────┤
│ Showing 1-10 of 156   < 1 2 3 ... 16 > │
└─────────────────────────────────────────┘
```

**Behavior rules**：
- 排序：點擊 column header 切換 asc/desc/none
- 篩選：Dropdown filter，可複選，套用後顯示 active filter tag
- 搜尋：300ms debounce，支援模糊搜尋
- 選取：Checkbox + Shift 可多選，選取後頂部出現 bulk action bar
- Row action：hover 顯示 action icons 或 「⋮」 more menu
- 分頁：底部分頁器 + 每頁筆數選擇（10/25/50/100）

**Edge cases**：
| 狀態 | 處理 |
|------|------|
| 載入中 | 5 行 skeleton rows |
| 無資料 | 插圖 + 「目前沒有任何{資料}」 + [新增] CTA |
| 搜尋無結果 | 「找不到符合的結果」 + 建議調整關鍵字 |
| 錯誤 | 「載入失敗」 + [重試] 按鈕 |
| 無權限 | 「你沒有檢視{資料}的權限」 + 聯繫管理員 |

**Mobile**：
- < 768px 轉為 Card List
- 每張 Card 顯示：主要欄位 + 狀態 + Action 按鈕
- 不顯示次要欄位（可展開查看）

### 2.2 Bulk Action Bar

```
選取 3 項時浮出：
┌─────────────────────────────────────────┐
│ ✓ 已選取 3 項   [刪除] [匯出] [更多 ▼]   │ [✕ 取消選取] │
└─────────────────────────────────────────┘
```

**Rules**：
- 固定在表格頂部或螢幕底部（sticky）
- 破壞性操作（刪除）需二次確認 dialog
- 「全選」= 選取當前頁 / 「選取全部 156 項」link

---

## 3. Search & Filter Patterns

### 3.1 Search Bar

**When to use**：全站搜尋或列表內搜尋

**Structure**：
```
┌──🔍──────────────────────────────┐
│   Search...                  [✕] │
└──────────────────────────────────┘
↓ 輸入 2+ 字元後出現建議
┌──────────────────────────────────┐
│ Recent: keyword1, keyword2       │
├──────────────────────────────────┤
│ 🔍 suggestion 1                  │
│ 🔍 suggestion 2                  │
│ 🔍 suggestion 3                  │
└──────────────────────────────────┘
```

**Rules**：
- Debounce 300ms
- 最少輸入 2 個字元才觸發搜尋
- 顯示最近搜尋（max 5）
- Empty → 「輸入關鍵字開始搜尋」
- No result → 「找不到 "{keyword}" 的結果」+ 建議

### 3.2 Filter Panel

**When to use**：多條件篩選（電商、後台列表）

**Types**：
| 類型 | 適用 | 說明 |
|------|------|------|
| Inline Filter | 條件 < 4 個 | 水平排列 dropdown |
| Filter Drawer | 條件 4-8 個 | 側邊滑出面板 |
| Advanced Filter | 條件 > 8 個 | 獨立篩選頁或 Modal |

**Behavior**：
- 選擇條件後立即篩選（不需按「套用」，除非是 Advanced Filter）
- Active filter 顯示為可關閉的 Tag：`[Status: Active ✕] [Date: Last 7 days ✕]`
- 「清除全部篩選」按鈕
- URL 同步（篩選條件反映在 URL query string）

---

## 4. Navigation Patterns

### 4.1 Top Navigation Bar

```
Desktop：
┌──────────────────────────────────────────────┐
│ [Logo]  Home  Products  About  Contact  [🔍] │ [Login]│
└──────────────────────────────────────────────┘

Mobile：
┌──────────────────────────────────────────────┐
│ [☰]  [Logo]                          [🔍] [👤] │
└──────────────────────────────────────────────┘
```

**Rules**：
- Desktop：水平排列，sticky top，高度 64px
- Mobile：hamburger → full-screen menu overlay
- Active page：底部 border 或文字色加深
- 超過 6 個項目：使用 More dropdown

### 4.2 Sidebar Navigation

```
展開（240px）：           收合（64px）：
┌──────────────────┐    ┌────────┐
│ [Logo + Name]    │    │ [Logo] │
├──────────────────┤    ├────────┤
│ 🏠 Dashboard     │    │  🏠    │
│ 📊 Analytics     │    │  📊    │
│ 👥 Users         │    │  👥    │
│ ▼ Settings       │    │  ⚙️    │
│   • General      │    │        │
│   • Team         │    │        │
├──────────────────┤    ├────────┤
│ 👤 Profile       │    │  👤    │
│ 🚪 Logout        │    │  🚪    │
└──────────────────┘    └────────┘
```

**Rules**：
- Desktop：展開 240px，可收合為 64px icon-only
- Mobile：overlay drawer，hamburger 觸發
- Active item：背景色 + 左側 indicator bar
- 分群：用 divider 或 group label 分組
- Sub-navigation：Accordion 展開子項目

### 4.3 Breadcrumb

```
Home / Products / Category / Current Page
```

**Rules**：
- 超過 4 層：`Home / ... / Parent / Current`
- 最後一項（當前頁）不可點擊，字色較深
- Mobile：只顯示「← Back to [Parent]」

### 4.4 Tab Navigation

```
┌─────────┬──────────┬──────────┐
│ Tab 1 ▬ │ Tab 2    │ Tab 3    │
├─────────┴──────────┴──────────┤
│                                │
│  Tab 1 Content                │
│                                │
└────────────────────────────────┘
```

**Rules**：
- Tab 數量 2-6 個
- 超過 6 個 → 考慮 sidebar 或 dropdown
- Mobile：可水平 scroll 或轉為 dropdown select
- URL：每個 tab 對應一個 URL fragment（#tab-name）

---

## 5. Feedback Patterns

### 5.1 回饋工具選用指南

| 情境 | 使用 | 原因 |
|------|------|------|
| 操作成功確認 | Toast (success) | 非阻斷，自動消失 |
| 操作失敗 | Toast (error) | 不自動消失，需手動關閉 |
| 需要確認的破壞性操作 | Confirm Dialog | 阻斷，必須回應 |
| 頁面級的系統通知 | Banner / Alert | 持續顯示在頁面頂部 |
| 欄位級錯誤 | Inline Error | 直接在欄位下方 |
| 額外說明 / 提示 | Tooltip | hover/focus 觸發 |
| 長任務進度 | Progress bar + Toast | 即時進度 + 完成通知 |

### 5.2 Toast 使用規則

```
位置：右上角（desktop），頂部居中（mobile）
堆疊：最多 3 個，新的推舊的向下
Duration：
  - Success/Info：5 秒自動消失
  - Warning：8 秒自動消失
  - Error：不自動消失，需手動關閉
Action：可帶一個 action button（如「撤銷」）
```

### 5.3 Confirm Dialog 模板

```
┌─────────────────────────────┐
│ ⚠️ 刪除{項目}？              │
│                             │
│ 此操作將永久刪除{項目名稱}。  │
│ 此操作無法復原。              │
│                             │
│    ┌────────┐ ┌──────────┐  │
│    │ 取消   │ │ 確定刪除  │  │
│    └────────┘ └──────────┘  │
└─────────────────────────────┘
```

**Rules**：
- 標題：動詞 + 對象（「刪除課程？」）
- 說明：後果（「此操作無法復原。」）
- 確認按鈕：用 Danger variant，文案要具體（「確定刪除」而非「確定」）
- 高危操作：要求輸入名稱（如 GitHub 刪除 repo）

---

## 6. Empty / Error / Loading States

### 6.1 Loading

| 類型 | 使用場景 | 元件 |
|------|---------|------|
| Skeleton | 首次載入頁面/列表 | Skeleton rows/cards |
| Spinner | 按鈕操作中、小區塊載入 | Spinner icon |
| Progress bar | 檔案上傳、長任務 | Progress component |
| Shimmer overlay | 區塊重新載入 | 半透明 overlay + spinner |

**Rules**：
- 優先 Skeleton（保留布局結構，降低感知等待時間）
- Spinner 只用於小區塊（不要整頁只放一個 spinner）
- > 10 秒：顯示「仍在處理中…」文案
- > 30 秒：顯示「似乎比預期久，你可以稍後再查看」+ 離開按鈕

### 6.2 Empty State

```
┌─────────────────────────────┐
│                             │
│          [插圖]              │
│                             │
│     還沒有任何{項目}          │
│   {鼓勵性的說明文案}          │
│                             │
│     ┌─────────────────┐     │
│     │  + 建立第一個{項目} │   │
│     └─────────────────┘     │
│                             │
└─────────────────────────────┘
```

| 類型 | 文案模板 | CTA |
|------|---------|-----|
| 首次使用 | 「還沒有任何{項目}，立即建立你的第一個{項目}！」 | [+ 建立{項目}] |
| 搜尋無結果 | 「找不到符合 "{keyword}" 的結果」 | [清除搜尋] |
| 篩選無結果 | 「目前的篩選條件沒有符合的{項目}」 | [清除篩選] |
| 無權限 | 「你沒有檢視此{項目}的權限」 | [聯繫管理員] |
| 無網路 | 「無法連線，請檢查網路連線」 | [重試] |

### 6.3 Error State

| 層級 | 處理 |
|------|------|
| 欄位級 | Input 下方紅色文字 + 紅色邊框 |
| 區塊級 | 區塊內 inline alert + [重試] |
| 頁面級 | 全頁面錯誤頁（404/500） |
| 系統級 | 頂部 Banner（如：系統維護中） |

**Error 頁面模板**：
```
┌─────────────────────────────┐
│                             │
│          [插圖]              │
│                             │
│   {錯誤代碼}：{簡短說明}      │
│   {詳細說明 / 建議動作}       │
│                             │
│  ┌──────────┐ ┌───────────┐ │
│  │ 回首頁   │ │ 重試      │ │
│  └──────────┘ └───────────┘ │
│                             │
└─────────────────────────────┘
```

---

## 7. Authentication Patterns

### 7.1 Login

```
┌─────────────────────────────┐
│         [Logo]              │
│     歡迎回來                 │
│                             │
│ Email                       │
│ ┌─────────────────────────┐ │
│ │ name@example.com        │ │
│ └─────────────────────────┘ │
│                             │
│ 密碼                        │
│ ┌─────────────────────────┐ │
│ │ ••••••••         [👁]   │ │
│ └─────────────────────────┘ │
│                忘記密碼？    │
│                             │
│ ┌─────────────────────────┐ │
│ │       登入              │ │
│ └─────────────────────────┘ │
│                             │
│ ─────── 或 ───────         │
│                             │
│ ┌─────────────────────────┐ │
│ │ 🇬 使用 Google 登入      │ │
│ └─────────────────────────┘ │
│                             │
│    還沒有帳號？立即註冊      │
└─────────────────────────────┘
```

### 7.2 Registration

- 最少必要欄位（email + password），其餘 onboarding 時再收集
- 密碼強度指示器（weak / medium / strong）
- 同意條款 checkbox（必填）

---

## 8. Content Display Patterns

### 8.1 Card Grid

```
Desktop (3 columns)：
┌──────┐ ┌──────┐ ┌──────┐
│ Card │ │ Card │ │ Card │
│      │ │      │ │      │
└──────┘ └──────┘ └──────┘
┌──────┐ ┌──────┐ ┌──────┐
│ Card │ │ Card │ │ Card │
└──────┘ └──────┘ └──────┘

Tablet (2 columns) → Mobile (1 column)
```

**Rules**：
- Gap: `space.4` (16px) 或 `space.6` (24px)
- 所有 Card 等高（使用 `min-height` 或 flexbox `stretch`）
- Card 內容截斷規則：標題 2 行、描述 3 行

### 8.2 Detail Page

```
┌─────────────────────────────────────────┐
│ ← Back to List                          │
├─────────────────────────────────────────┤
│ [Title]                    [Edit] [⋮]   │
│ [Metadata: date, author, status]        │
├─────────────────────────────────────────┤
│ ┌─────────────┬───────────────────────┐ │
│ │ Tab 1 ▬     │ Tab 2  │ Tab 3       │ │
│ ├─────────────┴───────────────────────┤ │
│ │                                     │ │
│ │  Main Content                       │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 9. Action Patterns

### 9.1 CRUD 操作一致性

| 操作 | 觸發 | 回饋 | 確認 |
|------|------|------|------|
| Create | Primary Button | Success Toast | 不需確認 |
| Read | 點擊進入 detail | — | — |
| Update | Edit → Save | Success Toast | 不需確認（除非影響他人） |
| Delete | Danger Button | Success Toast | 需 Confirm Dialog |

### 9.2 Row Actions

```
Hover 顯示：
│ Item Name │ Status │ Date │ [✏️] [🗑] [⋮] │

⋮ More Menu：
┌──────────────┐
│ 📋 複製       │
│ 📥 匯出       │
│ ──────────── │
│ 🗑 刪除       │  ← 紅色
└──────────────┘
```

---

## 10. Permission / Access Patterns

### 10.1 無權限狀態

| 情境 | 處理 |
|------|------|
| 頁面級 | 403 頁 + 「你沒有權限」 + [聯繫管理員] |
| 功能級 | 按鈕 disabled + Tooltip 說明原因 |
| 資料級 | 欄位顯示 "—" 或 "[權限不足]" |
| 可升級 | 「升級到 Pro 方案以使用此功能」+ [升級] CTA |

**Rules**：
- 永遠告訴用戶「為什麼」不能操作
- 永遠告訴用戶「怎麼辦」（聯繫誰、升級什麼）
- 不要直接隱藏功能（用戶不知道有這個功能存在）

---

## 11. RD Copilot 專用模式

> 從 `universal_template/01_GLOBAL_SYSTEM_PROMPT [UX PATTERN LAYER]` + 14 頁 page spec 提煉。這些模式不是通用 Atomic Design 詞彙，而是 RD Copilot 業務語言的具現。

### 11.1 全域 Header（含專案選擇器）

```
┌────────────────────────────────────────────────────────────────────┐
│ [Logo]  [📁 Project Selector ▼]   ⌬ TaskDef   ⌬ Explore   ⌬ Track │
│                                                          [👤] [🔔] │
└────────────────────────────────────────────────────────────────────┘
```

**Rules**（universal_template 01_GLOBAL [UX PATTERN LAYER]）：
- Sticky top，高度 64px
- Logo 左對齊，**Project Selector** 緊鄰 Logo（核心：使用者可隨時切換專案 context）
- 中間放 Phase 導航 chips：TaskDef / Explore / Track / Create / PreCAD / Review / Decide / Feynman
- 右側：使用者頭像、通知 bell（未讀數 badge）
- 當前 Phase chip 用 `color.brand.primary` 高亮，其他為 `color.text.secondary`

### 11.2 Phase Bar（相位指示帶）

```
┌────────────────────────────────────────────────────────────────────┐
│ ▌ Phase 1: Define ─ D2 (問題探索)                                   │  ← 4px 高的色條 + 標題
└────────────────────────────────────────────────────────────────────┘
```

**Rules**：
- 緊接在 Header 下方，4-8px 高色條
- Phase I (藍 `color.brand.primary`)、Phase II (橘 `color.brand.accent`)、Phase III (綠 `color.success`)
- 副標題：「Phase X: {Phase 名稱} > {Gate 編號}（{階段描述}）」

### 11.3 AI 按鈕（AiButton）

```
[ ✨ AI 建議 ]      ←  default
[ ⏳ 分析中...   ]   ←  loading（含 spinner + dimmed）
[ ✓ 已建議      ]   ←  completed（短暫顯示後恢復）
```

**Rules**：
- 必含 `sparkles` 或 `brain` icon（區分於一般按鈕）
- 變體：`primary` (主要 AI 行動)、`secondary` (輔助 AI 建議)
- Loading state：spinner + 「分析中…」/「生成中…」/「求解中…」具體動詞
- Failure state：toast.error 顯示，按鈕恢復可點，不阻擋手動編輯
- AI 產出永遠標記「AI 生成」chip，可被 RD 編輯/覆寫

### 11.4 證據連結（Evidence Link）

```
推薦方案 X        🔗  ← 點擊跳轉原文件
                    ↑ hover 顯示：
                    ┌──────────────────┐
                    │ 📋 來源：...        │
                    │ 摘錄："..."       │
                    │ 信心：HIGH         │
                    │ [查看原始文件 ▶]   │
                    └──────────────────┘
```

**Rules**（universal_template 強調可追溯性）：
- 任何 AI 生成的數值、推薦、警告，必須附 Evidence Link
- 鏈狀 icon `link`，懸浮顯示來源摘要 + 信心等級
- Confidence levels：`rd_confirmed` (深綠) / `library` (淺綠) / `estimate` (橘黃) / `llm_estimate` (紅，需 RD 覆寫)

### 11.5 Gate Checklist Pattern

```
┌─ Gate D2 退出條件 ────────────────────────────┐
│  ☑ 已回答 ≥ 10 個問題                       │
│  ☑ 矛盾已分類為 TC/PC/SF（或無矛盾）          │
│  ☐ 7 類問題皆有回答（5/7 已完成）             │
│  ─────────────────────────────────────────  │
│  進度：71%（5/7）                            │
│  [檢視未完成項目]  [通過 → 進入下一階段]      │
└──────────────────────────────────────────────┘
```

**Rules**：
- 條件達成用 ☑ 綠色，未達成用 ☐ 灰色
- 進度條：達成數/總數 + 百分比
- 「通過」按鈕 disabled until 100%（除非 Gate 允許部分通過）
- 不通過時顯示「{條件} 尚未達成」+ 直達連結

### 11.6 嚴重度標籤（Severity Badge）

| 等級 | 顏色 | 用途 |
|:---|:---|:---|
| `Fatal` | `color.error` (#DC3545) | 致命矛盾、必須在 Gate P 前 100% 解決 |
| `Major` | `color.warning` (#FFC107) | 重要矛盾、建議在 Gate P 前 90% 解決 |
| `Minor` | `color.text.tertiary` | 次要矛盾、可延後處理 |

```
[Fatal]  [Major]  [Minor]
```

### 11.7 資料格式規範（universal_template [DATA PATTERN LAYER]）

| 類型 | 格式 | 範例 |
|:-----|:-----|:-----|
| 日期 | `YYYY-MM-DD` | `2026-04-28` |
| 日期時間 | `YYYY-MM-DD HH:mm` | `2026-04-28 14:30` |
| 數字（整數） | 千位分隔符 | `1,234,567` |
| 數字（小數） | 千位分隔符 + 小數兩位 | `1,234.56` |
| 百分比 | 小數點後兩位 | `25.50%` |
| 金額 | 貨幣符號 + 千位 + 兩位小數 | `NT$ 1,234.50` / `$ 12,345.67 USD` |
| 表格數字 | 等寬字體（tabular-nums），右對齊 | `1,234.56` |

### 11.8 檔案上傳（多模態素材）

> universal_template 核心需求：上傳 PDF/圖片/Excel/規格書 → AI 自動約束提取（PRD F1.7）。

```
┌─────────────────────────────────────┐
│         📁 拖放檔案至此              │
│         或 [選擇檔案]                │
│                                     │
│  支援格式：PDF, DOCX, XLSX, JPG, PNG │
│  單檔 ≤ 20MB                         │
└─────────────────────────────────────┘
```

**狀態流**：
- `idle` → `dragover`（虛線變實線、背景色變化）→ `uploading`（顯示進度條）→ `processing`（AI 解析中）→ `success`（顯示提取結果預覽）/ `error`（提供重試）

### 11.9 AI 黑帽質疑面板（Devil's Advocate Pattern）

```
┌─ AI 黑帽質疑 ──────────────────────────────────┐
│ Q1: 此設計在極端高溫下是否仍可靠？               │
│ Q2: 若供應商 A 缺料，B/C 替代方案的成本影響？      │
│ Q3: 用戶若誤操作步驟 3，系統是否有保護機制？      │
│ ────────────────────────────────────────────  │
│ [✨ 生成更多質疑]                              │
└────────────────────────────────────────────────┘
```

**Rules**：
- AI 主動扮演「挑戰者」角色（universal_template 01_GLOBAL [PRODUCT LAYER]）
- 用於 Pre-CAD Review、Design Review 階段
- RD 可標記某問題為「已回應」並關聯實驗或證據

### 11.10 Loading 策略

> universal_template [INTERACTION & ACCESSIBILITY LAYER] 規範。

| 場景 | 策略 | 工具 |
|:-----|:-----|:-----|
| 頁面首次載入 | Skeleton screen（保留布局） | 自訂 Skeleton 元件 |
| 跨頁切換 | 全域 Loading Bar | NProgress |
| 區塊重新載入 | Shimmer overlay | 半透明 overlay + spinner |
| AI 生成（< 5s） | Inline spinner + 文字 | Loading button |
| AI 生成（5-30s） | Skeleton + 進度提示 | 進度文字 + 取消按鈕 |
| 長任務（> 30s） | 進度條 + 「可離開頁面」 | Progress bar + Background notice |

---

## Figma 結構建議

```
📁 02_Patterns（Figma Page）
├── 📄 Forms
│   ├── Single Column Form（含所有 validation 狀態）
│   ├── Multi Column Form
│   ├── Stepper / Wizard
│   └── Inline Edit
├── 📄 Data Tables
│   ├── Standard Table（含 sort/filter/pagination）
│   ├── Bulk Actions
│   ├── Table → Card List（Mobile）
│   └── All States（loading/empty/error）
├── 📄 Search & Filter
│   ├── Search Bar + Suggestions
│   ├── Inline Filters
│   └── Filter Drawer
├── 📄 Navigation
│   ├── Top Nav（Desktop + Mobile）
│   ├── Sidebar（展開 + 收合）
│   ├── Breadcrumb
│   └── Tab Navigation
├── 📄 Feedback
│   ├── Toast（all variants）
│   ├── Confirm Dialog
│   └── Feedback 選用決策表
├── 📄 States
│   ├── Loading（Skeleton / Spinner / Progress）
│   ├── Empty States（all types）
│   └── Error States（field / block / page）
├── 📄 Auth
│   ├── Login
│   └── Registration
└── 📄 Permission
    ├── No Access States
    └── Upgrade Prompts
```

---

**版本**：v2.0（從 universal_template 提煉重構，新增 §11 RD Copilot 專用模式）
**最後更新**：2026-04-28
**內容來源**：
- §1-10 通用 Atomic Design 模式 — 保留 v1.0 內容
- §11 RD Copilot 專用模式 — 從 `universal_template/01_GLOBAL_SYSTEM_PROMPT [UX PATTERN LAYER] / [INTERACTION & ACCESSIBILITY LAYER] / [DATA PATTERN LAYER]` + 14 頁 page spec 提煉

**相關文件**：[`00_foundations_spec.md`](./00_foundations_spec.md)、[`01_components_spec.md`](./01_components_spec.md)、[`03_templates_spec.md`](./03_templates_spec.md)、[`99_documentation_spec.md`](./99_documentation_spec.md)
