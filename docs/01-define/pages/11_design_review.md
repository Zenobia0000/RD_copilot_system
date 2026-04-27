# Page-Level Prompt: DesignReview 設計審查

> Phase 3 Converge — CAD 完成後的設計審查。證據矩陣連結自 Track 假設追蹤，風險從高風險假設衍生，最小實驗驗證關鍵假設，附件上傳佐證文件。
> **對應步驟**：V1（設計審查）

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | D/X/V 編號化：Gate 3.1 → Gate V1；subtitle Step 3.1 → V1；移除 AA/SCAMPER/strikethrough 噪音；對齊 code 四 Tab 結構與 hook 清單 |

---

## [WIREFRAME]

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase bar (primary color)                                        │
│  ← 返回  Review — 設計審查                                        │
│  Phase 3: Converge > V1（CAD 完成後）                              │
├──────────────────────────────────────────────────────────────────┤
│  SectionIntro                                                      │
├──────────────────────────────────────────────────────────────────┤
│  審查方案列表                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                          │
│  │ 方案 A   │ │ 方案 B   │ │ 方案 C   │                          │
│  │ MUST ✓✓  │ │ MUST ✓✗  │ │ MUST ✓✓  │                          │
│  │ [去向 ▼] │ │ [去向 ▼] │ │ [去向 ▼] │                          │
│  └──────────┘ └──────────┘ └──────────┘                          │
├──────────────────────────────────────────────────────────────────┤
│  AI 黑帽質疑  [AI]                                                │
│  Q1: ...    Q2: ...    Q3: ...                                    │
│  [黑帽質疑] (AiButton, calls socraticGenerate)                    │
├──────────────────────────────────────────────────────────────────┤
│  AI 證據缺口分析（僅 E0/E1 存在時顯示）                            │
├──────────────────────────────────────────────────────────────────┤
│  資料來源 banner                                                   │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐       │
│  │ 證據矩陣    │ 風險登錄    │ 最小實驗    │ 附件        │       │
│  └─────────────┴─────────────┴─────────────┴─────────────┘       │
│  (Tab content area)                                                │
├──────────────────────────────────────────────────────────────────┤
│  審查結論與決策                                                    │
│  方案去向摘要 + 結論備註 + [批准審查]                              │
├──────────────────────────────────────────────────────────────────┤
│  KnowledgeRefsPanel                                                │
├──────────────────────────────────────────────────────────────────┤
│  Gate V1 — 設計審查完整性檢查                                      │
│  ☐ 證據矩陣已建立  ☐ H*/H 風險有 mitigation                      │
│  ☐ North Star KPI ≥ E2  ☐ MUST 以 E2+ 重新驗證                   │
│  [通過 → 進入 Decide]                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## [DESIGN PRINCIPLES]

| 原則 | 說明 |
|:-----|:-----|
| 證據驅動 | 所有審查結論需基於 Evidence Matrix 的 E0-E4 等級 |
| 風險可視化 | P x S 矩陣 + 顏色編碼（H*/H/M/L） |
| 實驗閉環 | 完成實驗自動提升關聯假設的證據等級 |
| Gate 守門 | Gate V1 四項條件全通過才能進入 Decide |

---

## [PAGE META]

- **page_name**: DesignReview
- **route_path**: `/projects/:id/review`
- **page_type**: review
- **primary_goal**: CAD 完成後審查設計方案的證據完整性、風險可控性，透過 AI 黑帽質疑發現盲點
- **secondary_goal**: 規劃最小實驗補足證據缺口，為設計決策提供充分依據
- **target_users**: RD 工程師、系統架構師
- **entry_point**: CadInProgress 頁完成後導航，或 Dashboard 直接進入
- **expected_time_on_page**: 20 ~ 60 分鐘

---

## [STRUCTURE: SECTIONS]

1. **Header**
   - section_type: navigation + status
   - section_purpose: 返回 Dashboard、頁面標題、subtitle "Phase 3: Converge > V1（CAD 完成後）"
2. **SectionIntro**
   - section_type: context
   - section_purpose: 說明本頁用途（證據矩陣、風險、實驗）
3. **Candidate Solutions List**
   - section_type: card-grid
   - section_purpose: 顯示通過 MUST 的候選方案，每方案可設定去向（批准/修訂/淘汰）
4. **AI Black Hat Questioning**
   - section_type: ai-analysis
   - section_purpose: 呼叫 `socraticGenerate` 對候選方案進行黑帽質疑
5. **AI Evidence Gap Detection**
   - section_type: ai-analysis (conditional)
   - section_purpose: 僅在 E0/E1 假設存在時顯示，列出證據缺口
6. **Data Source Banner**
   - section_type: info
   - section_purpose: 顯示資料來源統計，連結至 Track 頁
7. **Four-Tab Panel**
   - section_type: tabs
   - section_purpose: 證據矩陣 / 風險登錄 / 最小實驗 / 附件
8. **Conclusion & Decision**
   - section_type: form + action
   - section_purpose: 方案去向摘要、結論備註、批准審查按鈕
9. **KnowledgeRefsPanel**
   - section_type: reference
   - section_purpose: 知識參考連結
10. **Gate V1**
    - section_type: gate-check
    - section_purpose: 四項完整性檢查，通過後導航至 `/projects/:id/decide`

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center justify-between
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PhaseBar | `<div>` | required | h-1 w-full rounded-full bg-primary |
  | BackButton | `<Button variant="ghost">` | required | ArrowLeft icon，onClick → `/projects/:id` |
  | Title | `<h1>` | required | "Review — 設計審查" + HelpTooltip |
  | Subtitle | `<p>` | required | "Phase 3: Converge > V1（CAD 完成後）" |

### Section: Candidate Solutions List
- **layout**: Card > grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3
- **data_source**: `useSolutions(id)` — 篩選 projectId 匹配且有通過 MUST 的方案
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SolutionCard | card | per-solution | 方案名稱、MUST 通過/失敗圖示、描述 |
  | DispositionSelect | `<Select>` | per-solution | 去向選擇：批准/修訂/淘汰 |

### Section: AI Black Hat Questioning
- **layout**: Card with destructive/20 border
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | QuestionList | list | conditional | Q1/Q2/Q3... 質疑問題列表 |
  | BlackHatButton | `<AiButton>` | required | 呼叫 `socraticGenerate({ project_id, mission, constraints })` |
- **api_call**: `socraticGenerate` — mission 包含方案名稱，constraints 包含方案 mechanism
- **states**: idle / loading / display-questions / fallback-questions

### Section: Four-Tab Panel
- **layout**: `<Tabs>` with 4 TabsTrigger
- **tabs**:

  #### Tab 1: 證據矩陣 (Evidence Matrix)
  - **data_source**: `useEvidenceMatrix(id)`
  - **elements**: Desktop heatmap table (E0-E4 columns, assumption rows) + Mobile cards + Gap summary
  - **mutations**: `useCreateEvidenceRow`, `useUpdateEvidenceRow`
  - **visual**: North Star KPI 標記 (NS badge)，current level 以彩色圓點顯示

  #### Tab 2: 風險登錄 (Risk Registry)
  - **data_source**: `useRisksQuery(id)` (aliased from `useRisks`)
  - **elements**: P x S 矩陣 + 風險表格（Desktop table / Mobile cards）
  - **mutations**: `useCreateRisk`, `useUpdateRisk` (with camelCase→snake_case field mapping), `useDeleteRisk`
  - **fields**: description, failureMode, probability (1-5), severity (1-5), mitigation
  - **ai_action**: AI 識別風險（mock: 1800ms delay + createRisk）

  #### Tab 3: 最小實驗 (Experiment)
  - **data_source**: `useExperimentsQuery(id)` (aliased from `useExperiments`)
  - **elements**: Experiment cards (grid 1-2 cols) + Modal for create/edit
  - **mutations**: `useCreateExperiment`, `useUpdateExperiment`
  - **modal_fields**: name, linkedAssumptions, evidenceLevel, method, successCriteria, status (Plan/Running/Done), result
  - **ai_action**: AI 建議實驗（mock: 針對 E0/E1 gap 假設建議 FEA 仿真）

  #### Tab 4: 附件 (Attachments)
  - **data_source**: `supabase.from("review_attachments").select("*").eq("project_id", id)`
  - **elements**: `<AttachmentsPanel projectId={id} attachments={attachments} onRefresh={fetchAttachments} />`

### Section: Conclusion & Decision
- **layout**: Card with action buttons
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | DispositionSummary | badge-list | conditional | 所有方案去向摘要（批准/修訂/淘汰/未決定） |
  | ConclusionTextarea | `<Textarea>` | optional | 審查結論備註，maxLength=500 |
  | ApproveButton | `<Button>` | required | 批准審查（需 gate31Passed + 所有方案已決定去向） |
- **validation**: 所有方案必須選擇去向 + Gate V1 必須通過

### Section: Gate V1
- **layout**: Card border-2 border-primary/30 bg-primary/5
- **gate_items**:
  | # | 檢查項目 | 判定邏輯 |
  |:--|:---------|:---------|
  | 1 | 證據矩陣已建立 (>=1 假設有實驗) | `evidenceRows.some(r => r.experiments.length > 0) \|\| experiments.length > 0` |
  | 2 | 所有 H*/H 風險有 mitigation | `highRisksWithoutMitigation === 0` |
  | 3 | North Star KPI 皆達 >= E2 證據等級 | `northStarAllE2Plus` (E2/E3/E4) |
  | 4 | MUST 已以 E2+ 證據重新驗證（無 E0） | `allEvidenceAboveE0` |
- **pass_action**: 導航至 `/projects/:id/decide`（Decide 頁）
- **fail_action**: 按鈕 disabled + Tooltip "請完成上方所有檢查項目"

---

## [HOOKS]

| Hook | 來源 | 用途 |
|:-----|:-----|:-----|
| `useSolutions` | `@/hooks/api/useSolutions` | 載入候選方案 |
| `useEvidenceMatrix` | `@/hooks/api` | 載入證據矩陣 |
| `useCreateEvidenceRow` | `@/hooks/api` | 新增證據列 |
| `useUpdateEvidenceRow` | `@/hooks/api` | 更新證據列 |
| `useRisks` (aliased useRisksQuery) | `@/hooks/api` | 載入風險登錄 |
| `useCreateRisk` | `@/hooks/api` | 新增風險 |
| `useUpdateRisk` (aliased useUpdateRiskMutation) | `@/hooks/api` | 更新風險 |
| `useDeleteRisk` (aliased useDeleteRiskMutation) | `@/hooks/api` | 刪除風險 |
| `useExperiments` (aliased useExperimentsQuery) | `@/hooks/api` | 載入實驗 |
| `useCreateExperiment` | `@/hooks/api` | 新增實驗 |
| `useUpdateExperiment` | `@/hooks/api` | 更新實驗 |

---

## [API / LIB]

| 函式 / Endpoint | 用途 |
|:----------------|:-----|
| `socraticGenerate({ project_id, mission, constraints })` | AI 黑帽質疑：傳入方案名稱與機制，回傳 questions 陣列 |
| `supabase.from("review_attachments").select/insert` | 附件 CRUD |

---

## [SHARED COMPONENTS]

| 元件 | 來源 | 用途 |
|:-----|:-----|:-----|
| `AiButton` | `@/components/ui/ai-button` | AI 操作按鈕（黑帽質疑、識別風險、建議實驗） |
| `HelpTooltip` | `@/components/ui/help-tooltip` | 說明提示 |
| `SectionIntro` | `@/components/ui/section-intro` | 區段說明文字 |
| `KnowledgeRefsPanel` | `@/components/create/KnowledgeRefsPanel` | 知識參考面板 |
| `AttachmentsPanel` | `@/components/review/AttachmentsPanel` | 附件上傳/管理面板 |

---

## [TYPES]

| Type | 來源 | 說明 |
|:-----|:-----|:-----|
| `EvidenceLevel` | `@/types/designReview` | E0-E4 證據等級 |
| `EvidenceMatrixRow` | `@/types/designReview` | 證據矩陣列（假設 code、摘要、current level、實驗列表、isNorthStar） |
| `RiskItem` | `@/types/designReview` | 風險項目（description、failureMode、probability、severity、mitigation） |
| `Experiment` | `@/types/designReview` | 實驗（name、linkedAssumptions、evidenceLevel、method、successCriteria、status、result） |
| `ExperimentStatus` | `@/types/designReview` | Plan / Running / Done |
| `Gate31Item` | `@/types/designReview` | Gate 檢查項（label、passed） |

---

## [NAVIGATION]

| 方向 | 目標 | 觸發 |
|:-----|:-----|:-----|
| 返回 | `/projects/:id` | Header BackButton |
| 前往 Track | `/projects/:id/track` | Data Source Banner link / Evidence empty state |
| 通過 Gate V1 | `/projects/:id/decide` | Gate V1 通過按鈕 |
| 批准後返回 | `/projects/:id` | 批准審查成功後 |
