# 03_Templates — 頁面模板規格

> Templates 是「半成品模型」。
> 做新功能頁，不是從空白開始，而是從模板改。
>
> **本文件來源**：§1-10 為通用 Atomic Design 頁型模板（v1.0 保留）；§11 為 RD Copilot 專用業務頁模板，從 `universal_template/00_FRONTEND_BLUEPRINT.template.md §14 詳細頁面規格` + `02_PAGE_PROMPT.template.md` 提煉。
> **產品上下文**：universal_template 規範的 RD Design Copilot 涵蓋 10 個核心頁（含 Phase I-III 流程），對應通用模板 + 業務語意。

---

## 目錄

1. [模板使用原則](#1-模板使用原則)
2. [Dashboard Template](#2-dashboard-template)
3. [List Page Template](#3-list-page-template)
4. [Detail Page Template](#4-detail-page-template)
5. [Settings Page Template](#5-settings-page-template)
6. [Form / Wizard Template](#6-form--wizard-template)
7. [Landing Page Template](#7-landing-page-template)
8. [Auth Page Template](#8-auth-page-template)
9. [Error Page Template](#9-error-page-template)
10. [Template Selection Guide](#10-template-selection-guide)
11. [RD Copilot 業務頁模板對照](#11-rd-copilot-業務頁模板對照)

---

## 1. 模板使用原則

```
原則 1：模板是「約束」不是「裝飾」
  - 模板定義的是資訊架構和區塊排列，不是視覺風格
  - 視覺風格來自 00_Foundations 的 tokens

原則 2：模板可嵌套
  - Dashboard Template 內可嵌入 Data Table Pattern
  - Detail Template 內可嵌入 Form Pattern

原則 3：模板有 RWD 行為
  - 每個模板定義 Desktop / Tablet / Mobile 的 reflow 規則

原則 4：模板可組合
  - Sidebar Layout + List Template = 後台列表頁
  - Full Width + Landing Template = 行銷頁
```

---

## 2. Dashboard Template

### Layout

```
Desktop：
┌──────────────────────────────────────────────────┐
│ [Header: Logo + Nav + User Menu]          64px   │
├────────┬─────────────────────────────────────────┤
│        │ Page Title          [Action Button]     │
│        ├─────────────────────────────────────────┤
│ Sidebar│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
│ 240px  │ │Stat │ │Stat │ │Stat │ │Stat │       │
│        │ │Card │ │Card │ │Card │ │Card │       │
│        │ └─────┘ └─────┘ └─────┘ └─────┘       │
│        ├─────────────────────────────────────────┤
│        │ ┌───────────────────┐ ┌───────────────┐ │
│        │ │                   │ │               │ │
│        │ │   Main Chart      │ │  Side Panel   │ │
│        │ │                   │ │               │ │
│        │ └───────────────────┘ └───────────────┘ │
│        ├─────────────────────────────────────────┤
│        │ ┌─────────────────────────────────────┐ │
│        │ │         Recent Activity Table       │ │
│        │ └─────────────────────────────────────┘ │
└────────┴─────────────────────────────────────────┘

Tablet：Sidebar 收合為 icon-only (64px)
Mobile：Sidebar 隱藏為 hamburger, Stat Cards 2→1 col, Side Panel 移到下方
```

### Spec

| 區塊 | 元件 | 規則 |
|------|------|------|
| Stat Cards | Card (4 個) | `grid-cols-4` → `grid-cols-2` → `grid-cols-1` |
| Main Chart | Chart Container | 佔 2/3 寬度，高度 320px |
| Side Panel | Card | 佔 1/3 寬度，放 Top 5 list 或 quick actions |
| Activity Table | Data Table | 最近 5-10 筆，有「查看全部」link |
| Page Title | text.heading.lg | 包含 Breadcrumb（若需要） |

### 內容規則

```
Stat Card 結構：
  ┌──────────────────┐
  │ 📊 Revenue       │ ← Label (caption)
  │ $12,580          │ ← Value (heading.lg, tabular-nums)
  │ ↑ 12.5%          │ ← Trend (success/error color)
  └──────────────────┘

  - 數字使用 tabular-nums（等寬數字）
  - Trend：正數綠 ↑ / 負數紅 ↓ / 持平灰 →
  - 比較期間寫在 tooltip 或 caption（vs 上月）
```

---

## 3. List Page Template

### Layout

```
Desktop：
┌──────────────────────────────────────────────────┐
│ [Header]                                         │
├────────┬─────────────────────────────────────────┤
│        │ Page Title           [+ Create] [⚙️]    │
│        ├─────────────────────────────────────────┤
│Sidebar │ [🔍 Search] [Filter ▼] [Sort ▼]         │
│        ├─────────────────────────────────────────┤
│        │ ┌─────────────────────────────────────┐ │
│        │ │ [Table / Card Grid]                 │ │
│        │ │                                     │ │
│        │ │                                     │ │
│        │ │                                     │ │
│        │ └─────────────────────────────────────┘ │
│        ├─────────────────────────────────────────┤
│        │ Showing 1-10 of 156   < 1 2 3 ... >    │
└────────┴─────────────────────────────────────────┘
```

### Spec

| 區塊 | 元件 | 規則 |
|------|------|------|
| Page Header | Title + CTA + Settings | CTA 用 Primary Button |
| Toolbar | Search + Filter + Sort | 水平排列，mobile 收合為 icon buttons |
| Content Area | Data Table 或 Card Grid | 使用 02_Patterns 的 Data Table Pattern |
| Pagination | Pagination component | 底部固定 |

### View 切換

```
某些列表支援 Table View ↔ Card Grid View 切換：
  ┌────────────────────────────────┐
  │ [☰ List] [▦ Grid]   View      │
  └────────────────────────────────┘
```

---

## 4. Detail Page Template

### Layout

```
Desktop：
┌──────────────────────────────────────────────────┐
│ [Header]                                         │
├────────┬─────────────────────────────────────────┤
│        │ ← Back to List                          │
│        ├─────────────────────────────────────────┤
│        │ [Avatar] Title          [Edit] [⋮]      │
│Sidebar │ Status: Active  |  Created: 2024-01-01  │
│        ├─────────────────────────────────────────┤
│        │ ┌──────────┬──────────┬──────────┐      │
│        │ │Overview ▬│ Activity │ Settings │      │
│        ├─┴──────────┴──────────┴──────────┤      │
│        │                                   │      │
│        │   Tab Content                     │      │
│        │                                   │      │
│        │   ┌────────────┐ ┌──────────────┐ │      │
│        │   │ Main (2/3) │ │ Aside (1/3)  │ │      │
│        │   └────────────┘ └──────────────┘ │      │
└────────┴───────────────────────────────────┘      │
```

### Spec

| 區塊 | 元件 | 規則 |
|------|------|------|
| Back link | Text link + ← icon | `← Back to {List Name}` |
| Header | Avatar + Title + Metadata + Actions | Actions 用 icon buttons 或 dropdown |
| Tabs | Tab component | 2-5 個 tabs |
| Main Content | 寬 2/3 | 主要資訊區 |
| Aside | 寬 1/3 | Metadata、Related items、Quick actions |
| Mobile | Aside 移到 main 下方 | 單欄 stack |

---

## 5. Settings Page Template

### Layout

```
Desktop：
┌──────────────────────────────────────────────────┐
│ [Header]                                         │
├────────┬─────────────────────────────────────────┤
│        │ Settings                                 │
│        ├──────────┬──────────────────────────────┤
│Sidebar │ Settings │ Section Title                │
│        │ Nav      │ Section description           │
│        │          │                              │
│        │ General ▬│ ┌──────────────────────────┐ │
│        │ Profile  │ │ Form Fields...           │ │
│        │ Team     │ └──────────────────────────┘ │
│        │ Billing  │                              │
│        │ Notif.   │ Section Title 2              │
│        │ Security │ ┌──────────────────────────┐ │
│        │          │ │ Form Fields...           │ │
│        │          │ └──────────────────────────┘ │
│        │          │                              │
│        │          │ ┌────────┐ ┌──────────────┐  │
│        │          │ │ Cancel │ │ Save Changes │  │
│        │          │ └────────┘ └──────────────┘  │
└────────┴──────────┴──────────────────────────────┘
```

### Spec

| 區塊 | 元件 | 規則 |
|------|------|------|
| Settings Nav | Vertical nav links | 左側 200px，sticky |
| Content | Form sections | 每個 section 有 title + description |
| Form Layout | 2/3 寬度 form | 不要佔滿全寬（太寬不好讀） |
| Save | Sticky bottom bar 或 section-level save | 顯示 unsaved changes indicator |
| Mobile | Settings Nav 轉為頂部 select 或 accordion | |

### Unsaved Changes

```
用戶修改後未儲存，離開前：
  ┌─────────────────────────────┐
  │ 你有未儲存的變更              │
  │                             │
  │ 離開此頁面將丟失你的變更。     │
  │                             │
  │  ┌──────────┐ ┌──────────┐  │
  │  │ 不儲存   │ │ 儲存並離開 │  │
  │  └──────────┘ └──────────┘  │
  └─────────────────────────────┘
```

---

## 6. Form / Wizard Template

### Single Page Form

```
┌──────────────────────────────────────────────────┐
│ [Header]                                         │
├──────────────────────────────────────────────────┤
│               max-width: 640px                   │
│                                                  │
│  Create New {Item}                               │
│  Fill in the details below.                      │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ Form Section 1                             │  │
│  │ [Fields...]                                │  │
│  │                                            │  │
│  │ Form Section 2                             │  │
│  │ [Fields...]                                │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────┐ ┌────────────────────────────────┐ │
│  │ Cancel   │ │        Create {Item}           │ │
│  └──────────┘ └────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Multi-Step Wizard

```
┌──────────────────────────────────────────────────┐
│ [Header]                                         │
├──────────────────────────────────────────────────┤
│                                                  │
│  ① Basic Info ── ② Configuration ── ③ Review     │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ Step 1: Basic Info                         │  │
│  │                                            │  │
│  │ [Fields...]                                │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│            ┌──────────┐ ┌──────────────────┐     │
│            │ 上一步   │ │    下一步 →      │     │
│            └──────────┘ └──────────────────┘     │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Spec

| 屬性 | 值 |
|------|-----|
| Form 最大寬度 | 640px（置中） |
| Section 間距 | `space.8` (32px) |
| Field 間距 | `space.5` (20px) |
| Footer | Sticky bottom（mobile）或 page bottom（desktop） |

---

## 7. Landing Page Template

### Layout

```
Full Width (no sidebar)：
┌──────────────────────────────────────────────────┐
│ [Top Nav]                                        │
├──────────────────────────────────────────────────┤
│                                                  │
│                   HERO SECTION                   │
│              Headline + Subline                  │
│           [Primary CTA] [Secondary]              │
│               Hero Image / Video                 │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│               SOCIAL PROOF                       │
│         Logo bar / Testimonial strip             │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│              FEATURES SECTION                    │
│       ┌──────┐ ┌──────┐ ┌──────┐                │
│       │Feat 1│ │Feat 2│ │Feat 3│                │
│       └──────┘ └──────┘ └──────┘                │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│              HOW IT WORKS                        │
│          Step 1 → Step 2 → Step 3                │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│             PRICING SECTION                      │
│       ┌──────┐ ┌──────┐ ┌──────┐                │
│       │Free  │ │Pro ★ │ │Enterp│                │
│       └──────┘ └──────┘ └──────┘                │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│            TESTIMONIALS                          │
│     ┌──────┐ ┌──────┐ ┌──────┐                   │
│     │Quote │ │Quote │ │Quote │                   │
│     └──────┘ └──────┘ └──────┘                   │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│                FAQ SECTION                       │
│           [Accordion items]                      │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│            FINAL CTA SECTION                     │
│          Headline + [CTA Button]                 │
│                                                  │
├──────────────────────────────────────────────────┤
│ [Footer: Links + Social + Legal]                 │
└──────────────────────────────────────────────────┘
```

### Section 規格

| Section | Padding | 背景 | 寬度 |
|---------|---------|------|------|
| Hero | `space.20` (80px) top/bottom | 可有背景色/漸層/圖片 | Full width |
| Features | `space.16` (64px) | 白色或淺灰 | Container (1280px) |
| Pricing | `space.16` (64px) | 對比背景色 | Container |
| Testimonials | `space.12` (48px) | 白色 | Container |
| FAQ | `space.12` (48px) | 淺灰 | Container (max 768px) |
| Final CTA | `space.16` (64px) | Brand color bg | Full width |

---

## 8. Auth Page Template

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  ┌───────────────────┬────────────────────────┐  │
│  │                   │                        │  │
│  │    Brand Visual    │    Auth Form           │  │
│  │    / Illustration  │    (Login / Register)  │  │
│  │                   │                        │  │
│  │    [Logo]         │    [Form Component]    │  │
│  │    [Tagline]      │                        │  │
│  │                   │                        │  │
│  └───────────────────┴────────────────────────┘  │
│                                                  │
└──────────────────────────────────────────────────┘

Mobile：隱藏 Brand Visual，只顯示 Logo + Form
```

---

## 9. Error Page Template

```
┌──────────────────────────────────────────────────┐
│ [Header (minimal)]                               │
├──────────────────────────────────────────────────┤
│                                                  │
│              ┌──────────────┐                    │
│              │  [Illustration]                   │
│              └──────────────┘                    │
│                                                  │
│               404 / 500                          │
│           找不到這個頁面                           │
│     你要找的頁面可能已被移動或刪除。                  │
│                                                  │
│         ┌──────────┐ ┌──────────┐                │
│         │ 回首頁   │ │ 回上一頁  │                │
│         └──────────┘ └──────────┘                │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Error 頁面文案

| 代碼 | 標題 | 說明 |
|------|------|------|
| 400 | 請求有誤 | 請檢查你輸入的資訊是否正確。 |
| 401 | 需要登入 | 請登入後再試。 |
| 403 | 權限不足 | 你沒有存取此頁面的權限。 |
| 404 | 找不到頁面 | 你要找的頁面可能已被移動或刪除。 |
| 500 | 系統錯誤 | 我們正在處理中，請稍後再試。 |
| 503 | 維護中 | 系統正在進行維護，預計 {time} 恢復。 |

---

## 10. Template Selection Guide

**白話版：你要做什麼頁面 → 用什麼模板**

| 你要做的頁面 | 用這個模板 | 搭配的 Patterns |
|-------------|-----------|----------------|
| 後台總覽 / 首頁 | Dashboard | Stat Cards + Chart + Recent Table |
| 用戶列表 / 訂單列表 / 商品列表 | List Page | Data Table + Search + Filter |
| 用戶詳情 / 訂單詳情 / 文章內容 | Detail Page | Tabs + Content Sections |
| 系統設定 / 個人設定 / 偏好 | Settings Page | Sidebar Nav + Form Sections |
| 新增項目 / 編輯項目 | Form | Single/Multi Column Form |
| 多步驟流程（註冊、結帳） | Wizard | Stepper Form |
| 產品首頁 / 行銷頁 | Landing Page | Hero + Features + Pricing + CTA |
| 登入 / 註冊 / 忘記密碼 | Auth Page | Auth Form Pattern |
| 404 / 500 / 維護中 | Error Page | Error State Pattern |

---

## 11. RD Copilot 業務頁模板對照

> 從 `universal_template/00_FRONTEND_BLUEPRINT §14 頁面總覽矩陣` 提煉，將 RD Design Copilot 10 個核心頁映射到 §2-9 通用頁型模板。
> 每頁的詳細區塊規格、互動流程、API 對應在 `universal_template/02_PAGE_PROMPT.template.md` 各 page spec 中定義。

### 11.1 對照矩陣

| # | RD Copilot 頁 | 路徑 | Phase | Gate | 通用模板 | 業務元件 (§01.5.5) | 主要 Pattern (§02) |
|:--|:-------------|:-----|:------|:-----|:---------|:-------------------|:------------------|
| 0 | 專案列表 | `/projects` | — | — | List Page | — | Standard Data Table + Card Grid |
| 1 | 專案儀表板 | `/projects/:id` | — | overview | Dashboard | `MissionContextPanel` | Dashboard Pattern + Stat Cards |
| 2 | 任務定義 / Brief | `/projects/:id/define` | I | D1 | Form | `KpiInputList`, `ConstraintFeasibilityChecker`, `AiButton` | Single-Column Form + AI 按鈕 |
| 3 | 假設台帳 | `/projects/:id/assumptions` | I | — | List Page (kanban) | `AssumptionCard` | Kanban Board (P2) + Filter |
| 4 | 矛盾識別 | `/projects/:id/contradictions` | I | — | Detail (workspace) | `ContradictionCard`, `SocraticQuestionCard`, `ContradictionConvergenceGraph` | Tab Navigation + Workspace |
| 5 | 方案探索 / Create | `/projects/:id/create` | II | X2 | Wizard (5-step) | `LayeredSolutionCard`, `CciBadge`, `EvidenceCoverageGauge` | Stepper Form + AI 按鈕 + Evidence Link |
| 6 | Pre-CAD 審查 | `/projects/:id/pre-cad` | II | P | Detail (review) | `PreCadConfidenceGauge`, `EvidenceLink` | Review Pattern + Gate Checklist |
| 7 | 設計審查 | `/projects/:id/review` | III | V1 | Detail (review) | `EvidenceLink` | AI 黑帽質疑 + Tab + Evidence |
| 8 | 決策記錄 | `/projects/:id/decide` | III | V2 | Form | — | Multi-Section Form + Lock Pattern |
| 9 | 知識庫 | `/knowledge-base[/:slug]` | — | — | List + Detail | — | Search + Card Grid + Detail |

### 11.2 Phase 色帶對照（§02.11.2）

每頁 Phase Bar 顏色由 `phase` 決定：
- Phase I (Define) → `color.brand.primary` 藍
- Phase II (Diverge) → `color.brand.accent` 橘
- Phase III (Converge) → `color.success` 綠
- Phase 無關（Auth/Portfolio/Knowledge/System）→ 灰或不顯示

### 11.3 模板選擇決策樹

```
新增 RD Copilot 頁面？
├── 屬於某個 Phase Gate 流程？
│   ├── 結構化輸入（KPI、約束、決策）→ Form Template + AI 按鈕
│   ├── 多步驟探索（TRIZ 方案）→ Wizard Template + Conditional Stepper
│   ├── 審查證據完整性 → Detail (review) + Evidence Link + Gate Checklist
│   └── 追蹤多項目（假設 / 任務）→ List Page (kanban) + Filter
├── 跨 Phase 總覽 → Dashboard Template + MissionContextPanel
├── 全域工具（知識庫 / 設定）→ List + Detail / Settings
└── 系統頁（404/Auth）→ Error / Auth Template
```

### 11.4 共用結構（所有 RD Copilot 頁）

```
Page Shell：
  ┌────────────────────────────────────────┐
  │ Header（含 Project Selector）  §02.11.1 │  ← Sticky 64px
  ├────────────────────────────────────────┤
  │ Phase Bar（色條 + 標題）       §02.11.2 │  ← 8px 高
  ├────────────────────────────────────────┤
  │ ┌──────────────────────┬─────────────┐ │
  │ │                      │             │ │
  │ │  Main Content        │ Knowledge   │ │  ← Knowledge Panel
  │ │  (依該頁模板)          │ Refs Panel  │ │     (§00.1.4)
  │ │                      │  320px      │ │
  │ │                      │             │ │
  │ └──────────────────────┴─────────────┘ │
  ├────────────────────────────────────────┤
  │ Gate Checklist（如該頁有 Gate） §02.11.5│  ← Sticky 底部
  └────────────────────────────────────────┘
```

---

## Figma 結構建議

```
📁 03_Templates（Figma Page）
├── 📄 Dashboard Template
│   ├── Desktop layout
│   ├── Tablet layout
│   └── Mobile layout
├── 📄 List Page Template
│   ├── Table view
│   ├── Card Grid view
│   └── Mobile card list
├── 📄 Detail Page Template
├── 📄 Settings Page Template
├── 📄 Form Templates
│   ├── Single Page Form
│   └── Multi-Step Wizard
├── 📄 Landing Page Template
│   └── All sections
├── 📄 Auth Page Template
│   ├── Login
│   └── Register
└── 📄 Error Pages
    ├── 404
    ├── 500
    └── Maintenance
```

---

**版本**：v2.0（從 universal_template 提煉重構，新增 §11 RD Copilot 業務頁模板對照）
**最後更新**：2026-04-28
**內容來源**：
- §1-10 通用 Atomic Design 模板 — 保留 v1.0 內容
- §11 RD Copilot 業務頁模板對照 — 從 `universal_template/00_FRONTEND_BLUEPRINT §11.2 頁面總覽矩陣` + `02_PAGE_PROMPT.template.md` 14 份 page spec 提煉

**相關文件**：[`00_foundations_spec.md`](./00_foundations_spec.md)、[`01_components_spec.md`](./01_components_spec.md)、[`02_patterns_spec.md`](./02_patterns_spec.md)、[`99_documentation_spec.md`](./99_documentation_spec.md)
