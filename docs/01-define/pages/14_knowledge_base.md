---
id: P14
file_id: "14"
page_name: KnowledgeBase
route_path: /knowledge-base
page_type: list-detail
phase: null
ia_group: knowledge
gate: null
protected: true
dev_only: false
source_component: src/pages/KnowledgeBase.tsx
spec_version: 1.0
ia_version: 1.2
status: stable
last_updated: 2026-04-24
api_resources: [knowledge_articles]
modules: [knowledge]
depends_on: []
absorbed_specs: []
optional_sections: []
---

# Page-Level Prompt: KnowledgeBase 知識庫

> 全域知識庫瀏覽頁面，提供搜尋、分類篩選與文章閱讀功能，非專案範疇。

---

## [PAGE META]
- **primary_goal**: 讓使用者瀏覽並閱讀 Playbook、歷史案例、決策模板與矛盾收斂模式
- **secondary_goal**: 透過搜尋與分類篩選快速找到所需知識
- **target_users**: 所有已登入使用者（RD 工程師、專案管理者）
- **entry_point**: 全域導覽列、Feynman 頁面「查看知識庫」按鈕
- **expected_time_on_page**: 2 ~ 15 分鐘
- **route_paths**: `/knowledge-base`（列表）、`/knowledge-base/:slug`（詳情）

---

## [STRUCTURE: SECTIONS]
1. **ListHeader**
   - section_type: header
   - section_purpose: 顯示頁面標題與副標題（僅列表視圖）
2. **SearchAndFilter**
   - section_type: filter
   - section_purpose: 提供搜尋輸入框與分類篩選按鈕（僅列表視圖）
3. **ArticleGrid**
   - section_type: content-grid
   - section_purpose: 以網格形式顯示文章卡片（僅列表視圖）
4. **Pagination**
   - section_type: navigation
   - section_purpose: 分頁導覽（僅列表視圖，每頁 6 篇）
5. **DetailHeader**
   - section_type: navigation + meta
   - section_purpose: 顯示返回按鈕、分類 badge、標籤、標題、作者與日期（僅詳情視圖）
6. **ArticleContent**
   - section_type: content
   - section_purpose: 渲染 Markdown 格式的文章內容（僅詳情視圖）
7. **RelatedLinks**
   - section_type: navigation
   - section_purpose: 顯示相關文檔連結（僅詳情視圖，有資料時）

---

## [SECTION COMPONENT SPEC]

### Section: ListHeader
- **layout**: 無特殊容器，直接在 page-shell-kb 內
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Title | `<h1>` | required | "知識庫"，text-2xl font-bold tracking-tight |
  | Subtitle | `<p>` | required | "瀏覽 Playbook、歷史案例、決策模板與矛盾收斂模式"，text-sm text-muted-foreground |
- **states**: 無
- **copy_constraints**: 副標題需涵蓋所有分類名稱

### Section: SearchAndFilter
- **layout**: flex flex-col sm:flex-row gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SearchInput | Input | required | Search icon (left)，placeholder "搜尋知識庫..."，maxLength=100，搜尋 title/description/tags |
  | CategoryButtons | Button x5 | required | 分類篩選按鈕群，flex gap-1.5 flex-wrap |
- **categories**:
  | Value | Label | Icon |
  |:------|:------|:-----|
  | all | 全部 | 無 |
  | playbook | Playbook | BookOpen |
  | case-study | 案例 | Lightbulb |
  | template | 模板 | FileText |
  | convergence-pattern | 收斂模式 | GitBranch |
- **states**:
  - activeCategory: 當前選中的按鈕為 variant="default"，其餘為 variant="outline"
  - 切換分類或搜尋時自動重設 page 至 1
- **copy_constraints**: 搜尋限制 100 字元

### Section: ArticleGrid
- **layout**: grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ArticleCard | Card | required | 可點擊，hover:shadow-md transition-shadow |
  | CategoryBadge | Badge (secondary) | required | 分類圖示 + 標籤 |
  | CardTitle | `<h3>` | required | font-semibold text-sm line-clamp-2 |
  | CardDescription | `<p>` | required | text-sm text-muted-foreground line-clamp-2 |
  | AuthorDate | `<span>` x2 | required | 作者（左）與日期（右），text-xs text-muted-foreground |
  | Tags | Badge (outline) x3 | required | 最多顯示前 3 個標籤，text-xs |
- **states**:
  - 有結果: 顯示網格
  - 無結果: 顯示空狀態卡片 — "沒有找到相關知識" + "請嘗試調整搜尋條件或分類篩選。"
  - 載入中: 顯示 6 個 Skeleton (h-48)
- **copy_constraints**: 標題與描述各最多 2 行（line-clamp-2）

### Section: Pagination
- **layout**: flex items-center justify-center gap-2 pt-2
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PrevButton | Button (outline, sm) | required | ChevronLeft icon，disabled={page <= 1} |
  | PageIndicator | `<span>` | required | "{page} / {totalPages}"，text-sm text-muted-foreground |
  | NextButton | Button (outline, sm) | required | ChevronRight icon，disabled={page >= totalPages} |
- **states**: 僅 totalPages > 1 時顯示
- **copy_constraints**: 每頁 PAGE_SIZE = 6

### Section: DetailHeader
- **layout**: flex items-center gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | Button (ghost, icon) | required | ArrowLeft icon，導航至 `/knowledge-base` |
  | CategoryBadge | Badge (secondary) | required | 分類圖示 + 標籤 |
  | TagBadges | Badge (outline) | required | 所有標籤，text-xs |
  | Title | `<h1>` | required | text-2xl font-bold tracking-tight |
  | Author | `<span>` | required | User icon + 作者名稱，text-sm text-muted-foreground |
  | PublishDate | `<span>` | required | Calendar icon + 日期，text-sm text-muted-foreground |
- **states**: 載入中顯示 Skeleton (h-8 + h-96)
- **copy_constraints**: 無

### Section: ArticleContent
- **layout**: Card > CardContent (p-6 prose prose-sm max-w-none)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ContentRenderer | 動態渲染 | required | 依行首字元解析：`## ` → h2、`### ` → h3、`- ` → li (disc)、數字序號 → li (decimal)、`| ` → mono p、空行 → br、其餘 → p |
- **states**: 無
- **copy_constraints**: 支援 Markdown 子集（h2/h3/ul/ol/table-like/paragraph）

### Section: RelatedLinks
- **layout**: Card > CardContent (p-4)
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SectionTitle | `<h3>` | required | "相關文檔"，text-sm font-semibold mb-2 |
  | LinkBadges | Badge (outline) | required | 可點擊，hover:bg-accent transition-colors，點擊導航至 link.url |
- **states**: 僅當 relatedLinks.length > 0 時顯示此區塊
- **copy_constraints**: 無

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入 `/knowledge-base`，顯示列表視圖
2. 頁面載入時呼叫 `useKnowledgeArticles()` 從 Supabase 取得文章列表
3. 若 Supabase 有資料 → 使用 liveArticles；否則 → 使用 mockKnowledgeArticles
4. 使用者可在搜尋框輸入關鍵字 → 即時篩選 title/description/tags
5. 使用者可點擊分類按鈕篩選 → 切換 activeCategory，自動重設頁碼至 1
6. 點擊文章卡片 → 導航至 `/knowledge-base/:slug`
7. 詳情視圖呼叫 `useKnowledgeArticle(slug)` 從 Supabase 取得單篇文章
8. 若 Supabase 無資料 → 從 mockKnowledgeArticles 中以 slug 查找
9. 點擊返回按鈕 → 導航回 `/knowledge-base`
10. 點擊相關文檔 badge → 導航至對應 URL

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (>= 1280px) | page-shell-kb，grid 3 欄 | 搜尋與篩選同行排列 |
| Tablet (768 ~ 1279px) | grid 2 欄 | 搜尋與篩選可能分兩行 (flex-col → flex-row at sm) |
| Mobile (< 768px) | grid 1 欄 | 搜尋與篩選各自獨立一行，分類按鈕 flex-wrap |

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Action | API Call | Payload / Params |
  |:-------|:---------|:-----------------|
  | 取得所有文章 | `useKnowledgeArticles()` | 無參數，回傳 `{ id, slug, title, description, author, publishedAt, category, tags, content, relatedLinks }[]` |
  | 取得單篇文章 | `useKnowledgeArticle(slug)` | slug: string，回傳單一文章物件 |
- **fallback**: liveArticles 為空時降級至 mockKnowledgeArticles；liveArticle 為 null 時從 mock 中以 slug 查找
- **error_cases**:
  - Supabase 查詢失敗 → 自動降級至 mock 資料
  - slug 不存在 → selectedArticle 為 null，不渲染詳情（回到列表邏輯）
  - 網路異常 → Skeleton 載入狀態持續顯示

---

## [ACCEPTANCE CRITERIA]
- [ ] 列表視圖顯示標題「知識庫」與副標題
- [ ] 搜尋框可即時篩選文章（依 title、description、tags 匹配）
- [ ] 5 個分類按鈕可切換篩選，選中項為 default 樣式
- [ ] 切換分類或搜尋條件時自動重設頁碼至第 1 頁
- [ ] 文章卡片以 grid 佈局排列（xl:3 欄、md:2 欄、sm:1 欄）
- [ ] 卡片顯示分類 badge、標題（line-clamp-2）、描述（line-clamp-2）、作者、日期、最多 3 個標籤
- [ ] 卡片 hover 時有 shadow-md 效果
- [ ] 無搜尋結果時顯示空狀態提示
- [ ] 分頁導覽在 totalPages > 1 時顯示，每頁 6 篇
- [ ] 點擊卡片導航至 `/knowledge-base/:slug` 詳情視圖
- [ ] 詳情視圖顯示返回按鈕、分類 badge、所有標籤、標題、作者、日期
- [ ] 文章內容依 Markdown 行首字元正確渲染 h2/h3/ul/ol/paragraph
- [ ] 相關文檔區塊僅在有連結時顯示，badge 可點擊導航
- [ ] 列表載入中顯示 6 個 Skeleton；詳情載入中顯示 Skeleton
- [ ] Supabase 無資料時自動降級至 mock 資料
