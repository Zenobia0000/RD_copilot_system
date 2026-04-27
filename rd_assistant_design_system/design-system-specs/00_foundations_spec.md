# 00_Foundations — 基礎系統規格

> **本文件來源**：從 `universal_template/` 的 RD Design Copilot 設計規格（00_FRONTEND_BLUEPRINT §3 + 01_GLOBAL_SYSTEM_PROMPT [VISUAL DESIGN SYSTEM LAYER]）提煉，依 Atomic Design 規格重新產出。
> **作用**：定義 RD Design Copilot 全站的物理定律。像地球重力一樣 — 不會在不同頁面突然換重力。本文件不是「設計稿」，而是定義所有 UI 遵循的底層規則。
> **產品定位**：RD Design Copilot — AI 輔助的早期概念設計系統，把「未知」變成「可追蹤的假設」，把「靈感」變成「可審查的方案」，把「試錯」變成「最小實驗」。

---

## 目錄

1. [Grid & Layout System](#1-grid--layout-system)
2. [Color System](#2-color-system)
3. [Typography System](#3-typography-system)
4. [Spacing System](#4-spacing-system)
5. [Border & Radius System](#5-border--radius-system)
6. [Elevation & Shadow System](#6-elevation--shadow-system)
7. [Iconography](#7-iconography)
8. [Motion & Animation](#8-motion--animation)
9. [Design Tokens 命名規範](#9-design-tokens-命名規範)
10. [Token Mode 管理](#10-token-mode-管理)

---

## 1. Grid & Layout System

### 1.1 Container

| 屬性 | 值 | 說明 |
|------|-----|------|
| `layout.container.max-width` | 1280px | 主內容區最大寬度 |
| `layout.container.padding` | 16px (mobile) / 24px (tablet) / 32px (desktop) | 容器左右內距 |
| `layout.container.center` | `margin: 0 auto` | 居中策略 |

### 1.2 Grid

| 斷點 | 欄數 | Gutter | Margin | Container |
|------|------|--------|--------|-----------|
| Mobile (< 640px) | 4 | 16px | 16px | 100% |
| Tablet (640px–1024px) | 8 | 24px | 24px | 100% |
| Desktop (> 1024px) | 12 | 24px | 32px | 1280px max |
| Wide (> 1440px) | 12 | 32px | auto | 1280px max |

### 1.3 Breakpoints（對齊 universal_template）

| Token | 值 | 說明 |
|-------|-----|------|
| `breakpoint.sm` | 640px | Mobile → Tablet |
| `breakpoint.md` | 768px | Tablet 中間點 |
| `breakpoint.lg` | 1024px | Tablet → Desktop |
| `breakpoint.xl` | 1280px | Desktop 標準 |
| `breakpoint.2xl` | 1536px | Wide Desktop |

> 最小支援寬度：320px（universal_template 01_GLOBAL [VISUAL] 規範）。

### 1.4 Layout Primitives

| 名稱 | 規則 | 用途 |
|------|------|------|
| Page Shell | `min-h-screen` + `flex flex-col` | 頁面外殼（header + main + footer） |
| Content Area | `max-w-container` + `mx-auto` + `px-container` | 主內容區 |
| Section | `py-section` (48px desktop / 32px mobile) | 頁面區段間距 |
| Sidebar Layout | `grid grid-cols-[240px_1fr]` (desktop) → `stack` (mobile) | 左側欄 + 主內容 |
| Split Layout | `grid grid-cols-2` (desktop) → `stack` (mobile) | 50/50 雙欄 |
| Knowledge Panel Layout | `grid grid-cols-[1fr_320px]` (desktop) → `stack` (mobile) | 主內容 + 右側知識面板（RD Copilot 多頁適用） |

### 1.5 RWD 行為規則（Mobile-First）

```
規則 1：Mobile First
  - 所有樣式從 mobile 開始寫，向上覆蓋

規則 2：斷點行為
  - Sidebar：desktop 展開 (240px)，tablet 收合為 64px icon-only 或 hamburger
  - Table：desktop 橫向，mobile 轉為 card list
  - Form：desktop 雙欄，mobile 單欄
  - Modal：desktop 居中彈窗，mobile 全螢幕 sheet
  - Stepper：desktop 水平顯示完整步驟，mobile 改為下拉選單或簡化導航

規則 3：圖片策略
  - 使用 srcset + sizes
  - Mobile 載入較小圖片
  - Hero 圖片：desktop 16:9，mobile 4:3 裁切
```

---

## 2. Color System

> **顏色策略來源**：universal_template/01_GLOBAL [VISUAL DESIGN SYSTEM LAYER] + 00_BLUEPRINT §3.2。採用 Bootstrap 語意化調色盤，主色傳達「技術可靠」、強調色用於警示、語義色對齊 WCAG AA。

### 2.1 Brand Colors

| Token | 色值 | 用途 | 對比規則 |
|-------|------|------|---------|
| `color.brand.primary` | `#007BFF` | 主要行動按鈕、品牌識別、重要連結、選中狀態 | 與白底對比 ≥ 4.5:1 |
| `color.brand.primary.hover` | `#0069D9` | 主色 hover（加深 ~10%） | — |
| `color.brand.primary.active` | `#0056B3` | 主色 active（加深 ~15%） | — |
| `color.brand.secondary` | `#6C757D` | 次要按鈕、邊框、非強調文字、輔助資訊 | — |
| `color.brand.accent` | `#FD7E14` | 強調資訊、警告、高亮元素、AI 推薦標記 | — |

### 2.2 Semantic Colors

| Token | Light 色值 | Dark 色值 | 用途 |
|-------|-----------|----------|------|
| `color.success` | `#28A745` | `#34D058` | 成功、Gate 通過、正面、約束可行性 OK |
| `color.success.bg` | `#F0FDF4` | `#052E16` | 成功狀態背景 |
| `color.warning` | `#FFC107` | `#FACC15` | 警告、待辦、Major 矛盾、需注意 |
| `color.warning.bg` | `#FEFCE8` | `#422006` | 警告狀態背景 |
| `color.error` | `#DC3545` | `#F87171` | 錯誤、Fatal 矛盾、危險、負面操作 |
| `color.error.bg` | `#FEF2F2` | `#450A0A` | 錯誤狀態背景 |
| `color.info` | `#17A2B8` | `#60A5FA` | 資訊、提示、AI 中立建議 |
| `color.info.bg` | `#EFF6FF` | `#172554` | 資訊狀態背景 |

> **RD Copilot 語義延伸**（universal_template 14 頁規格用詞）：
> - `Fatal` 矛盾 → `color.error`
> - `Major` 矛盾 → `color.warning`
> - `Minor` 矛盾 → `color.text.tertiary`
> - `Pre-CAD Confidence Score` 進度條：≥ 80% green / 60-79% warning / < 60% error

### 2.3 Surface Colors

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `color.bg.page` | `#F8F9FA` | `#0A0A0A` | 頁面底色（universal_template 規範使用 Bootstrap light） |
| `color.bg.surface` | `#FFFFFF` | `#18181B` | 卡片/容器底色 |
| `color.bg.elevated` | `#FFFFFF` | `#27272A` | 浮層/Modal 底色 |
| `color.bg.muted` | `#F3F4F6` | `#27272A` | 低調背景（disabled 區、Skeleton） |
| `color.bg.overlay` | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal 遮罩層 |

### 2.4 Text Colors

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `color.text.primary` | `#212529` | `#F9FAFB` | 主要文字（標題、正文） |
| `color.text.secondary` | `#6C757D` | `#9CA3AF` | 次要文字、說明、placeholder |
| `color.text.tertiary` | `#9CA3AF` | `#6B7280` | 弱化文字、Minor 矛盾標記 |
| `color.text.disabled` | `#D1D5DB` | `#3F3F46` | 停用狀態 |
| `color.text.inverse` | `#FFFFFF` | `#0A0A0A` | 反轉文字（在深色/淺色底上） |
| `color.text.link` | `#007BFF` | `#60A5FA` | 連結（對齊 brand.primary） |
| `color.text.link.hover` | `#0056B3` | `#93C5FD` | 連結 hover |

### 2.5 Border Colors

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `color.border.default` | `#E9ECEF` | `#3F3F46` | 預設邊框、分隔線 |
| `color.border.hover` | `#D1D5DB` | `#52525B` | hover 邊框 |
| `color.border.focus` | `color.brand.primary` | `color.brand.primary` | Focus 邊框 |
| `color.border.error` | `color.error` | `color.error` | 錯誤邊框 |

### 2.6 對比度規則

```
必須遵守 WCAG 2.1 AA 標準：
- 一般文字（< 18px）：對比度 ≥ 4.5:1
- 大文字（≥ 18px bold 或 ≥ 24px）：對比度 ≥ 3:1
- UI 元件（按鈕邊框、輸入框邊框）：對比度 ≥ 3:1
- Focus indicator：對比度 ≥ 3:1（相對於背景）

工具：
- Figma 插件：Contrast Checker
- 線上：webaim.org/resources/contrastchecker
```

---

## 3. Typography System

### 3.1 字體堆疊（對齊 universal_template）

| 用途 | 字體 | Fallback |
|------|------|----------|
| 中文（主要） | `Noto Sans TC` | `'PingFang TC', 'Microsoft JhengHei', sans-serif` |
| 英文 / Fallback | `Helvetica Neue, Arial, Segoe UI` | `-apple-system, BlinkMacSystemFont, sans-serif` |
| 程式碼 / 表格數字 | `JetBrains Mono` | `'Fira Code', 'SF Mono', Consolas, monospace` |

> universal_template 01_GLOBAL 完整 stack：
> ```css
> font-family: "Noto Sans TC", "Helvetica Neue", Arial, "Segoe UI", sans-serif;
> ```

### 3.2 字級階梯（模組化比例 1.25 — Major Third）

> **比例來源**：universal_template/00_BLUEPRINT §3.2 採用 1.25 ratio，base 1rem (16px)。

| Token | 字級 | 行高 | 字重 | Letter Spacing | 用途 |
|-------|------|------|------|---------------|------|
| `text.display` | 48px / 3rem | 1.1 | 700 | -0.02em | Hero 大標題 |
| `text.heading.xl` | 39px / 2.441rem | 1.2 | 700 | -0.01em | H1 頁面標題 |
| `text.heading.lg` | 31px / 1.953rem | 1.2 | 700 | -0.01em | H2 區塊標題 |
| `text.heading.md` | 25px / 1.563rem | 1.3 | 600 | 0 | H3 小節標題 |
| `text.heading.sm` | 20px / 1.25rem | 1.4 | 600 | 0 | H4 |
| `text.body.md` | 16px / 1rem | 1.5 | 400 | 0 | 標準段落 |
| `text.body.sm` | 13px / 0.8rem | 1.5 | 400 | 0 | 小字說明、表格輔助 |
| `text.caption` | 10px / 0.64rem | 1.4 | 400 | 0.01em | 標註、時間戳、徽章 |
| `text.overline` | 12px / 0.75rem | 1.4 | 600 | 0.05em | 上標、分類標籤（大寫） |

### 3.3 中英混排規則

```
規則 1：字體順序
  - font-family: "Noto Sans TC", "Helvetica Neue", Arial, "Segoe UI", sans-serif
  - 中文字體在前，瀏覽器自動 fallback 至英文字體

規則 2：行高
  - 純英文段落：line-height 1.5
  - 中文或中英混排：line-height 1.5–1.8（中文字高較大）
  - 標題（heading）：1.2

規則 3：標點符號
  - 使用全形中文標點（，。；：「」）
  - 數字和英文之間加半形空格（例：共 3 個項目、使用 React 框架）

規則 4：數字
  - 表格、KPI、金額：使用 tabular-nums（等寬數字）
  - 內文：使用 proportional-nums
```

### 3.4 RWD 字級調整

| Token | Desktop | Tablet | Mobile |
|-------|---------|--------|--------|
| `text.display` | 48px | 40px | 32px |
| `text.heading.xl` | 39px | 32px | 26px |
| `text.heading.lg` | 31px | 26px | 22px |
| `text.heading.md` | 25px | 22px | 20px |
| 其餘 | 不變 | 不變 | 不變 |

---

## 4. Spacing System

### 4.1 Spacing Scale（4px 基數）

| Token | 值 | 用途範例 |
|-------|-----|---------|
| `space.0.5` | 2px | 微調 |
| `space.1` | 4px | icon 與文字間距、元素內微間距 |
| `space.1.5` | 6px | 緊湊元件內距 |
| `space.2` | 8px | 元素內標準間距、相關元素間距 |
| `space.3` | 12px | 標籤與文字、列表項間距 |
| `space.4` | 16px | 元件間距、Card padding（universal_template Card 標準） |
| `space.5` | 20px | 元件群組間距 |
| `space.6` | 24px | 區塊間距、Section 內 padding |
| `space.8` | 32px | 大區塊間距、Section 間距（mobile） |
| `space.10` | 40px | Section 間距（mobile→tablet） |
| `space.12` | 48px | Section 間距（desktop） |
| `space.16` | 64px | 頁面級間距 |
| `space.20` | 80px | Hero 區域間距 |
| `space.24` | 96px | 超大間距 |

### 4.2 使用規則

```
規則 1：鄰近原則
  - 相關元素間距 < 不相關元素間距
  - 例：標題與副標題之間 space.2 (8px)，標題與下一個區塊之間 space.6 (24px)

規則 2：一致性原則
  - 同層級元素使用相同間距
  - Card 列表中每張 Card 的間距一致

規則 3：層級對應
  - 元素內部 → space.1–3 (4–12px)
  - 元件間 → space.4–6 (16–24px)
  - Section 間 → space.8–16 (32–64px)
  - Page 間 → space.16–24 (64–96px)

規則 4：Padding vs Margin
  - Padding：用在容器內部（Card padding、Button padding）
  - Margin：用在容器外部（元件間距、Section 間距）
  - 永遠用 token，不要寫 magic number
```

---

## 5. Border & Radius System

### 5.1 Border

| Token | 值 | 用途 |
|-------|-----|------|
| `border.width.default` | 1px | 標準邊框（universal_template 規範 `1px solid $color-divider`） |
| `border.width.thick` | 2px | 強調邊框（Focus、Active Tab） |
| `border.style` | solid | 統一使用 solid |

### 5.2 Border Radius（universal_template 主軸 8px）

| Token | 值 | 用途 |
|-------|-----|------|
| `radius.none` | 0px | 無圓角 |
| `radius.sm` | 4px | 小元素（Tag, Badge, Tooltip） |
| `radius.md` | 6px | 按鈕、輸入框 |
| `radius.lg` | 8px | **卡片、容器（universal_template 主軸）** |
| `radius.xl` | 12px | Modal、大容器 |
| `radius.2xl` | 16px | 大圓角卡片 |
| `radius.full` | 9999px | 圓形（Avatar, Pill Badge） |

### 5.3 Radius 使用規則

```
規則：外層圓角 > 內層圓角
  - 例：Card radius.lg (8px) 內的 Button radius.md (6px)
  - 內層 radius = 外層 radius - padding
  - 避免「假圓角」視覺問題
```

---

## 6. Elevation & Shadow System

> **主軸**：universal_template 規範「輕微陰影，增加層次感」`box-shadow: 0 4px 6px rgba(0,0,0,0.1)`，對應 `shadow.md`。

| Token | 值 | 用途 | Z-Index |
|-------|-----|------|---------|
| `shadow.none` | none | 平面元素 | 0 |
| `shadow.xs` | `0 1px 2px rgba(0,0,0,0.05)` | 輕微浮起（Input focus） | — |
| `shadow.sm` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` | 卡片預設 | 1 |
| `shadow.md` | `0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)` | **universal_template 主軸 / 懸浮卡片、hover** | 2 |
| `shadow.lg` | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)` | Dropdown、Popover | 3 |
| `shadow.xl` | `0 20px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.04)` | Modal、Dialog | 4 |
| `shadow.2xl` | `0 25px 50px rgba(0,0,0,0.25)` | Toast、最高層 | 5 |

### Z-Index 規則

| Layer | Z-Index | 元素 |
|-------|---------|------|
| Base | 0 | 頁面內容 |
| Sticky | 10 | Sticky header、Sticky sidebar |
| Dropdown | 20 | Select dropdown、Popover |
| Overlay | 30 | Modal backdrop |
| Modal | 40 | Modal、Dialog、Drawer |
| Toast | 50 | Toast、Snackbar |
| Tooltip | 60 | Tooltip |

---

## 7. Iconography

### 7.1 Icon 規格

| 屬性 | 值 |
|------|-----|
| 風格 | Outline（線條風格），一致線寬 |
| 線寬 | 1.5px |
| 尺寸 | 16px / 20px / 24px / 32px（universal_template 預設 16/24/32） |
| 顏色 | 繼承 `currentColor` |
| 圓角 | 與系統圓角一致 |
| 推薦庫 | Lucide Icons（universal_template 提到 Material Icons 為相容選項） |

### 7.2 Icon 使用規則

```
規則 1：尺寸對應
  - 16px：行內 icon（Badge 內、表格操作）
  - 20px：按鈕內 icon、導航項
  - 24px：獨立 icon（空狀態配圖、Feature icon）
  - 32px：大型展示用

規則 2：間距
  - Icon + Text：space.1 (4px) 到 space.2 (8px)
  - Icon button padding：space.2 (8px)

規則 3：可及性
  - 純 icon 按鈕必須有 aria-label
  - 裝飾性 icon 使用 aria-hidden="true"
```

### 7.3 RD Copilot 語義 Icon 對應

| 語義 | 推薦 Icon | 用途 |
|------|----------|------|
| 矛盾識別 | `alert-octagon` | Phase I 矛盾 / Fatal 標記 |
| 假設台帳 | `clipboard-list` | Phase I 假設管理 |
| 方案探索 | `git-branch` | Phase II 發散候選 |
| 證據鏈 | `link` | 證據連結（universal_template 強調可追溯） |
| Pre-CAD 審查 | `shield-check` | Gate P |
| 決策記錄 | `gavel` 或 `bookmark-check` | Phase III 收斂 |
| 知識庫 | `book-open` | Phase III 沉澱 |
| AI 建議 | `sparkles` 或 `brain` | AI 主動挑戰者標記 |

---

## 8. Motion & Animation

### 8.1 Duration

| Token | 值 | 用途 |
|-------|-----|------|
| `motion.duration.instant` | 100ms | Hover 狀態變化 |
| `motion.duration.fast` | 150ms | Toggle、Checkbox |
| `motion.duration.normal` | 200ms | Button press、Fade in |
| `motion.duration.slow` | 300ms | Modal 開合、Drawer 滑入 |
| `motion.duration.slower` | 500ms | Page transition |

### 8.2 Easing

| Token | 值 | 用途 |
|-------|-----|------|
| `motion.ease.default` | `cubic-bezier(0.4, 0, 0.2, 1)` | 通用 |
| `motion.ease.in` | `cubic-bezier(0.4, 0, 1, 1)` | 元素離開 |
| `motion.ease.out` | `cubic-bezier(0, 0, 0.2, 1)` | 元素進入 |
| `motion.ease.spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 彈跳效果（謹慎使用） |

> **動畫框架**：universal_template 技術棧指定 **Framer Motion**（聲明式動畫，與 React 整合）。

### 8.3 動效規則

```
規則 1：目的性
  - 動效必須有功能目的（引導注意力、回饋操作、表示狀態變化）
  - 不做純裝飾性動畫

規則 2：可中斷
  - 使用者操作可以中斷任何動畫
  - 不要讓使用者等動畫跑完

規則 3：減少動態偏好
  - 遵守 prefers-reduced-motion
  - 替代方案：用 opacity fade 取代 slide/scale

規則 4：常見模式
  - Fade in/out：opacity 0→1 / 1→0
  - Slide up：translateY(8px→0) + opacity
  - Scale：scale(0.95→1) + opacity（Modal 用）
  - Collapse：height auto→0（Accordion 用）
```

---

## 9. Design Tokens 命名規範

### 9.1 命名結構

```
{category}.{property}.{variant}.{state}

範例：
  color.bg.surface          ← 類別.屬性.變體
  color.text.primary        ← 類別.屬性.變體
  color.border.focus        ← 類別.屬性.狀態
  text.heading.lg           ← 類別.屬性.尺寸
  space.4                   ← 類別.值
  radius.md                 ← 類別.尺寸
  shadow.lg                 ← 類別.尺寸
  motion.duration.normal    ← 類別.屬性.值
```

### 9.2 命名規則

```
規則 1：小寫 + 點分隔
  ✅ color.bg.surface
  ❌ Color.Bg.Surface
  ❌ color-bg-surface

規則 2：語意化而非描述值
  ✅ color.text.primary（語意：主要文字色）
  ❌ color.gray.900（描述：灰色 900）

規則 3：可預測性
  - 同類 token 遵循相同結構
  - 新增 token 時使用者能「猜到」名字

規則 4：避免縮寫（除非公認）
  ✅ color.background → 可縮寫為 color.bg（公認）
  ❌ color.brd → 應寫 color.border
```

### 9.3 Token 類別總表

| 類別 | Prefix | 範例 |
|------|--------|------|
| 顏色 | `color.*` | `color.brand.primary`, `color.text.secondary` |
| 間距 | `space.*` | `space.4`, `space.8` |
| 字型 | `text.*` | `text.body.md`, `text.heading.lg` |
| 圓角 | `radius.*` | `radius.md`, `radius.lg` |
| 陰影 | `shadow.*` | `shadow.sm`, `shadow.xl` |
| 邊框 | `border.*` | `border.width.default` |
| 動效 | `motion.*` | `motion.duration.fast` |
| 佈局 | `layout.*` | `layout.container.max-width` |
| 斷點 | `breakpoint.*` | `breakpoint.lg` |
| Z 軸 | `z.*` | `z.modal`, `z.tooltip` |

---

## 10. Token Mode 管理

### 10.1 Mode 定義

| Mode 名稱 | 說明 | 切換方式 |
|-----------|------|---------|
| `light` | 淺色模式（預設） | `prefers-color-scheme` / 手動 toggle |
| `dark` | 深色模式 | 同上 |
| `high-contrast` | 高對比模式 | `prefers-contrast` |

### 10.2 Token 覆蓋結構

```json
{
  "color.brand.primary": {
    "light": "#007BFF",
    "dark": "#3B9EFF"
  },
  "color.bg.page": {
    "light": "#F8F9FA",
    "dark": "#0A0A0A",
    "high-contrast": "#000000"
  },
  "color.text.primary": {
    "light": "#212529",
    "dark": "#F9FAFB",
    "high-contrast": "#FFFFFF"
  }
}
```

### 10.3 Figma 對應

```
Figma Variables → Collections:
  ├── Primitives（原始值：gray-50, gray-100, blue-500...）
  ├── Semantic-Light（語意對應：bg.page = gray-50）
  ├── Semantic-Dark（語意對應：bg.page = gray-950）
  └── Component-Specific（元件專用：button.primary.bg = brand.primary）

Figma Modes:
  - 每個 Variable Collection 可設定 Mode
  - Frame 上切換 Mode = 全部子元素自動切換
```

### 10.4 與工程的對應

| 設計端（Figma） | 工程端（CSS/Tailwind） | 同步方式 |
|----------------|----------------------|---------|
| Figma Variables | CSS Custom Properties | Token Studio / Style Dictionary |
| Figma Styles | Tailwind theme config | 手動或 token pipeline |
| Figma Components | React 元件（universal_template 指定 React 18 + Tailwind CSS） | Figma MCP / Code Connect |

```
同步流程：
  Figma Variables
    ↓ Token Studio plugin export
  tokens.json (W3C Design Token 格式)
    ↓ Style Dictionary / Token Transformer
  CSS variables / Tailwind config
    ↓ Git commit
  工程端自動生效
```

---

## Figma 結構建議

```
📁 00_Foundations（Figma Page）
├── 📄 Grid & Layout
│   ├── Grid 展示（Desktop / Tablet / Mobile）
│   ├── Container 規則圖示
│   └── Layout Primitives 範例（含 Knowledge Panel Layout）
├── 📄 Colors
│   ├── Brand Colors（#007BFF Bootstrap 家族）
│   ├── Semantic Colors（Success/Warning/Error/Info）
│   ├── Surface Colors
│   ├── Text Colors
│   └── Dark Mode 對照
├── 📄 Typography
│   ├── 字級階梯展示（1.25 ratio）
│   ├── 中英混排範例（Noto Sans TC + Helvetica Neue）
│   └── RWD 字級對照
├── 📄 Spacing
│   ├── Spacing Scale 視覺化
│   └── 使用規則圖示
├── 📄 Borders & Radius（主軸 8px）
├── 📄 Shadows & Elevation（主軸 shadow.md）
├── 📄 Icons
│   ├── Icon 尺寸展示
│   └── RD Copilot 語義 Icon 對應
└── 📄 Motion
    ├── Duration & Easing 表
    └── 常見動效模式（Framer Motion 示例）
```

---

## 交付產出清單

| 文件 | 格式 | 給誰 | 說明 |
|------|------|------|------|
| Foundation Spec | Markdown（本文件） | 設計 + 工程 | 規格全文 |
| Design Token Sheet | JSON / YAML | 工程 | 可直接被 build pipeline 消費的 token 檔 |
| Figma Variables | Figma Library | 設計 | 可直接在設計檔中使用 |
| Tailwind Config | JS/TS | 工程 | 對應 token 的 Tailwind 設定 |
| Token Change Log | Markdown | 全團隊 | token 變更紀錄 |

---

**版本**：v2.0（從 universal_template 提煉重構）
**最後更新**：2026-04-28
**內容來源**：
- `universal_template/00_FRONTEND_BLUEPRINT.template.md` §3 設計系統 + §6.1 RWD 斷點
- `universal_template/01_GLOBAL_SYSTEM_PROMPT.template.md` [VISUAL DESIGN SYSTEM LAYER]

**相關文件**：[`01_components_spec.md`](./01_components_spec.md)、[`02_patterns_spec.md`](./02_patterns_spec.md)、[`03_templates_spec.md`](./03_templates_spec.md)、[`99_documentation_spec.md`](./99_documentation_spec.md)
