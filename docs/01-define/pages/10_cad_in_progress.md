# Page-Level Prompt: CadInProgress CAD 進行中

> Phase 2.5 — 通過 Pre-CAD 審查的方案在此階段由 RD 進行 CAD 建模，追蹤完成狀態後進入設計審查。

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | Phase 2.5 保留（不屬於 D/X/V 範圍）；subtitle 對齊 code；route 確認為 `/projects/:id/cad`；移除 AA/SCAMPER 殘留 |
| v2.0 | 2026-04-20 | 初版 page spec |

---

## [PAGE META]

- **page_name**: CadInProgress
- **route_path**: `/projects/:id/cad`
- **page_type**: tracker
- **primary_goal**: 讓 RD 工程師追蹤已通過 Pre-CAD 審查方案的 CAD 繪製進度，逐一更新狀態（未開始 / 繪製中 / 已完成），至少 1 方案完成後即可進入設計審查
- **secondary_goal**: 以進度條即時呈現整體 CAD 完成比例，提供明確的階段銜接入口
- **target_users**:
  - 主要：RD 工程師（每日更新 CAD 繪製狀態）
  - 次要：RD 主管（檢視整體 CAD 進度）
- **entry_point**: Dashboard 專案頁面點擊進入 / Pre-CAD 審查完成後自動導向
- **expected_time_on_page**: 30 秒 - 2 分鐘（更新狀態後離開或進入 Design Review）

---

## [STRUCTURE: SECTIONS]

1. **back_navigation**
   - section_type: navigation
   - section_purpose: 提供返回 Dashboard 的按鈕，維持頁面層級導航

2. **page_header**
   - section_type: header
   - section_purpose: 顯示頁面標題「CAD 繪製階段」與 Phase 2.5 階段標示，附帶 HelpTooltip 說明

3. **cad_progress_bar**
   - section_type: stats_card
   - section_purpose: 以進度條呈現 CAD 完成比例（已完成數 / 總方案數），讓使用者一眼掌握整體進度

4. **cad_items_list**
   - section_type: card_list
   - section_purpose: 列出所有通過 Pre-CAD 審查的方案，每張卡片顯示名稱、當前 CAD 狀態 Badge、狀態切換按鈕

5. **design_review_entry**
   - section_type: cta_card
   - section_purpose: 引導使用者在至少 1 方案完成 CAD 後進入 Design Review 階段

---

## [SECTION COMPONENT SPEC]

### Section: back_navigation

- **layout**: 頁面頂部左對齊，負左邊距 -8px
- **elements**:
  - back_button: Button(variant="ghost", size="sm") / required / ArrowLeft icon + "Dashboard" 文字，點擊導向 `/projects/:id`
- **states**:
  - default: 灰色文字，ghost 樣式
  - hover: 背景淺灰色
- **copy_constraints**: 按鈕文字固定 "Dashboard"

### Section: page_header

- **layout**: 單列，標題 + 副標題上下排列
- **elements**:
  - title: H1 / required / "CAD 繪製階段"，font: 24px/700，附帶 HelpTooltip（內容："通過 Pre-CAD 審查的方案在此階段由 RD 進行 CAD 建模。完成後進入設計審查。"）
  - phase_label: Body SM / required / "Phase 2.5 · Pre-CAD → CAD → Design Review"，灰色次要文字
- **states**:
  - default: 標題 + 副標題正常顯示
- **copy_constraints**: 標題固定；副標題最多 50 字

### Section: cad_progress_bar

- **layout**: Card 容器，bg-muted/30 背景，padding 20px，內含標籤行 + Progress 元件
- **elements**:
  - progress_label: Body SM / required / 左側 "CAD 完成進度"，右側 "{completedCount}/{totalCount} 方案"
  - progress_bar: Progress(height=8px) / required / 百分比 = (completedCount / totalCount) * 100
- **states**:
  - default: 進度條依完成比例填充
  - all_completed: 進度條 100%，填滿主色
  - none_completed: 進度條 0%
- **copy_constraints**: 進度文字格式固定 "N/M 方案"

### Section: cad_items_list

- **layout**: 垂直堆疊卡片列表，間距 16px
- **elements**:
  - cad_card: Card / required (per item) / 每張包含：
    - alt_name: Body SM Bold / required / 方案名稱（無名稱時顯示 "(未命名方案 N)"）
    - status_badge: Badge / required / 依狀態顯示：
      - not_started: Clock icon + "未開始"，variant="outline"
      - in_progress: PenTool icon + "繪製中"，variant="secondary"
      - completed: CheckCircle icon + "已完成"，variant="default"
    - status_hint: Caption Italic / conditional / 僅 not_started 時顯示 "等待 RD 開始 CAD 建模"
    - action_buttons: ButtonGroup / required / 依當前狀態顯示可切換按鈕：
      - 非 in_progress 時：PenTool icon + "開始繪製" (outline)
      - 非 completed 時：CheckCircle icon + "標記完成" (outline)
  - empty_state: Card / conditional / 當無通過 Pre-CAD 審查的方案時顯示：
    - AlertTriangle icon + "沒有通過 Pre-CAD 審查的方案" + "請先在方案創造頁面完成 MUST 快篩與 Pre-CAD 審查" + 按鈕 "前往方案創造"
- **states**:
  - default: 白色卡片，正常邊框
  - completed: 卡片左側 3px 主色邊框，視覺強調已完成
  - loading: 全頁 Loader2 旋轉 + "載入 CAD 階段資料中..."
  - empty: 空狀態卡片，居中圖標 + 文字 + CTA 按鈕
- **copy_constraints**: 方案名稱無上限但 UI 可能截斷；狀態標籤固定中文

### Section: design_review_entry

- **layout**: Card 容器，border-2 border-primary/30 bg-primary/5，padding 20px
- **elements**:
  - section_icon: PenTool / required / 主色 icon，20x20
  - section_title: Body SM Bold / required / "進入設計審查"
  - status_badge: Badge / required / 依狀態顯示 "可進入"（主色背景）或 "需完成至少 1 方案 CAD"（灰色背景）
  - description: Body SM / required / "至少 1 個方案完成 CAD 繪製後，即可進入設計審查階段（證據矩陣、風險登錄、最小實驗）。"
  - proceed_button: Button / required / "進入 Design Review" + ArrowRight icon
- **states**:
  - can_proceed: 按鈕可點擊，Badge 顯示 "可進入"，點擊導向 `/projects/:id/review`
  - blocked: 按鈕 disabled + opacity-50，Badge 顯示 "需完成至少 1 方案 CAD"
- **copy_constraints**: 說明文字固定；Badge 文字二選一

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. 使用者進入頁面 -> 系統載入 alternatives 資料，篩選通過 MUST 快篩的方案
2. 若無通過方案 -> 顯示空狀態卡片 + CTA 導向方案創造頁
3. 使用者點擊「開始繪製」-> 呼叫 useUpdateAlternative(cad_status: "in_progress") -> Badge 更新為 "繪製中"
4. 使用者點擊「標記完成」-> 呼叫 useUpdateAlternative(cad_status: "completed") -> Badge 更新為 "已完成"，卡片左側出現主色邊框
5. completedCount >= 1 -> Design Review entry card 啟用 -> 使用者點擊「進入 Design Review」-> 導向 `/projects/:id/review`

### RWD 行為差異

| 斷點 | 行為 |
|:-----|:-----|
| Desktop (>=768px) | page-shell-narrow 佈局，卡片全寬堆疊 |
| Mobile (<768px) | 同 Desktop 佈局（頁面結構簡單，無需額外適配） |

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useAlternatives(projectId)` — 取得專案所有方案，前端篩選通過 MUST 且至少一項非 null 的 mustScores
  - `useUpdateAlternative()` — 更新方案 cad_status 欄位（not_started / in_progress / completed）
- **data_derivation**:
  - cadItems: 從 alternatives 篩選 mustScores 無 "fail" 且至少一項非 null，映射為 CadItem 物件
  - completedCount: cadItems 中 cadStatus === "completed" 的數量
  - progress: Math.round((completedCount / cadItems.length) * 100)
  - canProceed: completedCount >= 1
- **error_cases**:
  - API 載入失敗：顯示全頁 Loader2 旋轉（目前無獨立錯誤處理）
  - 無通過方案：顯示空狀態卡片 + CTA

---

## [ACCEPTANCE CRITERIA]

- [ ] 頁面正確篩選通過 MUST 快篩的方案（mustScores 無 "fail" 且至少一項非 null）
- [ ] 三種 CAD 狀態（not_started / in_progress / completed）正確顯示對應 icon、label、Badge variant
- [ ] 點擊「開始繪製」/「標記完成」按鈕正確呼叫 useUpdateAlternative 並即時更新 UI
- [ ] 進度條百分比正確反映已完成方案佔比
- [ ] 至少 1 方案 completed 時，Design Review 入口按鈕啟用；否則 disabled
- [ ] 無通過方案時顯示空狀態卡片與「前往方案創造」CTA
- [ ] 返回按鈕正確導向 Dashboard (`/projects/:id`)
- [ ] 載入中狀態顯示 Loader2 旋轉 + 文字提示
