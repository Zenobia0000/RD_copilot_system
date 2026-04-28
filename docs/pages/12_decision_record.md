---
id: P12
file_id: "12"
page_name: DecisionRecord
route_path: /projects/:id/decide
page_type: form
phase: 3
ia_group: phase3-converge
gate: V2
protected: true
dev_only: false
source_component: src/pages/DecisionRecord.tsx
spec_version: 3.0
ia_version: 1.2
status: stable
last_updated: 2026-04-27
api_resources: [decision, must_evaluations, want_scores, risks, ac_evaluations, alternatives]
modules: [analyst]
depends_on: [P11]
absorbed_specs: []
optional_sections: [wireframe, design_principles, changelog]
---

# Page-Level Prompt: DecisionRecord 決策記錄

> Phase 3 Converge — KT 決策流程完整記錄。整合 MUST/WANT 分析、風險評估、負面後果 (AC) 評估、矛盾收斂摘要，支援方案選定、行動計畫、簽核與報告匯出。
> **對應步驟**：V2（KT 決策）

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | D/X/V 編號化：Gate 3.2 → Gate V2；Phase Gate 3 → Phase Gate V；subtitle Step 3.2 → V2；移除 AA/SCAMPER/strikethrough 噪音；對齊 code 完整 hook 清單（20+ hooks）與 AC 評估區 |

---

## [WIREFRAME]

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase bar (primary color)                                        │
│  ← 返回  決策記錄  [草稿/已確認/已簽核]                           │
│  Phase 3: Converge > V2（KT 決策）                                │
├──────────────────────────────────────────────────────────────────┤
│  SectionIntro                                                      │
├──────────────────────────────────────────────────────────────────┤
│  Section 1: 決策概覽                                               │
│  決策聲明 · 決策者 · 決策日期 · 狀態                               │
├──────────────────────────────────────────────────────────────────┤
│  Section 2: KT 決策分析結果                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 2a. MUST 結果表格（通過/淘汰）                                │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ 2b. WANT 評分結果                                            │ │
│  │     Bar Chart (horizontal) + Radar Chart                     │ │
│  │     推薦方案 Badge                                           │ │
│  │     [展開評分表] — 可收合 WANT 評分矩陣                       │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ 2c. 風險評估表格 + 負面後果分析 (AC)                          │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ 2d. 矛盾收斂摘要                                            │ │
│  │     Confidence Score · Fatal/Major/Minor 進度                │ │
│  └──────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│  Section 3: 決策結論與行動                                        │
│  3a. 主路線 + 備援方案選擇                                        │
│  3b. 選擇理由 + 風險接受聲明                                      │
│  3c. 行動項目列表 (Accordion)                                     │
│  3d. [確認決策] / [回到草稿]                                      │
│  3e. 匯出報告 (PDF / JSON)                                        │
│  3f. 審查人簽核                                                    │
├──────────────────────────────────────────────────────────────────┤
│  KnowledgeRefsPanel                                                │
├──────────────────────────────────────────────────────────────────┤
│  Gate V2 — 決策記錄完整性檢查                                      │
│  Phase Gate V — Converge 階段完成檢查                              │
│  [Phase Gate V 通過 → 進入 Feynman 內化]                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## [DESIGN PRINCIPLES]

| 原則 | 說明 |
|:-----|:-----|
| KT 決策四階段 | MUST 篩選 → WANT 評分 → AC 負面後果 → 決策確認 |
| 鎖定保護 | 決策確認後表單鎖定（isLocked），僅可回到草稿解鎖 |
| 簽核追溯 | 每位簽核人記錄姓名、角色、簽核時間，支援撤回 |
| 匯出閘控 | 需先確認決策才能匯出 PDF/JSON |
| 雙 Gate | Gate V2（決策完整性）+ Phase Gate V（階段完成） |

---

## [PAGE META]

- **primary_goal**: 完整記錄設計決策過程（KT 方法），確保決策可追溯、可解釋
- **secondary_goal**: 支援 MUST/WANT 分析結果呈現、風險評估、行動計畫管理、簽核與報告匯出
- **target_users**: RD 工程師、RD 主管、PM、品質工程師
- **entry_point**: DesignReview 頁 Gate V1 通過後導航，或 Dashboard 直接進入
- **expected_time_on_page**: 30 ~ 90 分鐘

---

## [STRUCTURE: SECTIONS]

1. **Header**
   - section_type: navigation + status
   - section_purpose: 返回 Dashboard、頁面標題、決策狀態 Badge（草稿/已確認/已簽核）
2. **SectionIntro**
   - section_type: context
   - section_purpose: 說明 MUST/WANT/風險/矛盾收斂整合用途
3. **Section 1: 決策概覽**
   - section_type: summary-card
   - section_purpose: 決策聲明、決策者、決策日期、狀態一覽
4. **Section 2: KT 決策分析結果**
   - section_type: analysis-results
   - section_purpose: MUST 結果 + WANT 評分 + 風險評估 + AC 評估 + 矛盾收斂
5. **Section 3: 決策結論與行動**
   - section_type: form + action
   - section_purpose: 方案選定、理由填寫、行動計畫、確認/匯出/簽核
6. **KnowledgeRefsPanel**
   - section_type: reference
   - section_purpose: 知識參考連結
7. **Gate V2 + Phase Gate V**
   - section_type: gate-check
   - section_purpose: 決策完整性檢查 + 階段完成檢查

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center justify-between
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PhaseBar | `<div>` | required | h-1 w-full rounded-full bg-primary |
  | BackButton | `<Button variant="ghost">` | required | ArrowLeft icon，onClick → `/projects/:id` |
  | Title | `<h1>` | required | "決策記錄" + HelpTooltip |
  | Subtitle | `<p>` | required | "Phase 3: Converge > V2（KT 決策）" |
  | StatusBadge | `<Badge>` | required | 草稿 (secondary) / 已確認 (primary) / 已簽核 (accent) |

### Section 1: 決策概覽
- **layout**: Card with CardHeader + CardContent
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | DecisionStatement | text | conditional | "選定方案：{name}" 或 "尚未選定方案" |
  | DecisionMaker | icon + text | required | 從 signatures 中取 role="RD 主管" 的 name |
  | DecisionDate | icon + text | required | decision.decisionDate |
  | StatusDisplay | icon + badge | required | decision.status |

### Section 2a: MUST 結果表格
- **layout**: Card > Table
- **data_source**: `useAlternatives(id)` — 衍生 mustResults（從 mustScores 計算通過/淘汰）
- **columns**: 方案 | 結果 (通過/淘汰 Badge) | 原因

### Section 2b: WANT 評分結果
- **layout**: Card with collapsible scoring table
- **data_source**: `useWantCriteria(id)`, `useWantScores(id)`
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BarChart | recharts BarChart (horizontal) | conditional | 各方案加權總分比較 |
  | RadarChart | recharts RadarChart | conditional | 各方案多維雷達圖 |
  | TopAltBadge | info-box | conditional | "推薦方案：{name} (總分: {score})" |
  | ScoringTable | table (collapsible) | optional | 完整 WANT 評分矩陣（條件 x 方案，含權重） |
  | LoadTemplateBtn | `<Button>` | optional | 載入 W1-W6 標準模板 |
- **mutations**: `useCreateWantCriterion`, `useUpdateWantCriterion`, `useDeleteWantCriterion`, `useUpsertWantScore`

### Section 2c: 風險評估 + 負面後果 (AC)
- **data_source**: `useRisks(id)`, `useAdverseConsequences(id)`
- **risk_table_columns**: 風險 ID | 描述 | 嚴重度 | 機率 | 等級 | 緩解措施 | 監控指標
- **ac_table_columns**: AC ID | 方案 | 負面後果 | 機率 | 嚴重度 | 等級 | 緩解措施
- **ac_level_computation**: `computeACLevel(probability, severity)` from `@/types/decisionRecord`

### Section 2d: 矛盾收斂摘要
- **data_source**: `usePreCadConvergenceStats(id)`
- **layout**: 4-column grid (Confidence Score / Fatal / Major / Minor) with Progress bars

### Section 3a: 方案選定
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PrimarySelect | `<Select>` | required | 主路線方案選擇（按 WANT 排名） |
  | BackupSelect | `<Select>` | optional | 備援方案選擇 |
  | DecisionDate | `<Input type="date">` | required | 決策日期 |
  | Rationale | `<Textarea>` | required | 選擇理由，minLength=20，maxLength=2000 |
  | RiskAcceptance | `<Textarea>` | optional | 風險接受聲明，maxLength=1000 |
- **mutations**: `useUpsertDecision`
- **lock_behavior**: isLocked (confirmed/signed) 時所有欄位 disabled

### Section 3b: 行動項目
- **layout**: Accordion list
- **elements**: 每項包含 description (required), assignee (required), dueDate (optional)
- **mutations**: `useCreateActionItem`, `useUpdateActionItem`, `useDeleteActionItem`
- **ai_action**: AI 建議行動（mock: 1800ms delay + 2 items）

### Section 3c: 確認 / 匯出 / 簽核
- **confirm_flow**: confirmDecision() → validation (方案+理由+行動) → Dialog → doConfirm() → status='confirmed'
- **revert**: revertDraft() → status='draft'
- **export**: handleExport('pdf'|'json') — 需 isLocked
- **signature_flow**: addSignature() → updateSignature() → signSignature(idx) → revertSignature(idx)
- **signature_roles**: RD 工程師 / RD 主管 / PM / 品質工程師 / 高階主管 / 其他

---

## [HOOKS]

| Hook | 來源 | 用途 |
|:-----|:-----|:-----|
| `useAlternatives` | `@/hooks/api` | 載入方案清單 |
| `usePreCadSolutions` | `@/hooks/api` | 載入 Pre-CAD 方案（MUST 結果） |
| `usePreCadConvergenceStats` | `@/hooks/api` | 載入矛盾收斂統計 |
| `useRisks` | `@/hooks/api` | 載入風險登錄 |
| `useDecision` | `@/hooks/api` | 載入決策記錄 |
| `useUpsertDecision` | `@/hooks/api` | 新增/更新決策 |
| `useWantCriteria` | `@/hooks/api` | 載入 WANT 標準 |
| `useCreateWantCriterion` | `@/hooks/api` | 新增 WANT 標準 |
| `useUpdateWantCriterion` | `@/hooks/api` | 更新 WANT 標準 |
| `useDeleteWantCriterion` | `@/hooks/api` | 刪除 WANT 標準 |
| `useWantScores` | `@/hooks/api` | 載入 WANT 評分 |
| `useUpsertWantScore` | `@/hooks/api` | 新增/更新 WANT 評分 |
| `useAdverseConsequences` | `@/hooks/api` | 載入負面後果 (AC) |
| `useSignatures` | `@/hooks/api` | 載入簽核清單 |
| `useCreateSignature` | `@/hooks/api` | 新增簽核人 |
| `useUpdateSignature` | `@/hooks/api` | 更新簽核 |
| `useActionItems` | `@/hooks/api` | 載入行動項目 |
| `useCreateActionItem` | `@/hooks/api` | 新增行動項目 |
| `useUpdateActionItem` | `@/hooks/api` | 更新行動項目 |
| `useDeleteActionItem` | `@/hooks/api` | 刪除行動項目 |

---

## [SHARED COMPONENTS]

| 元件 | 來源 | 用途 |
|:-----|:-----|:-----|
| `AiButton` | `@/components/ui/ai-button` | AI 操作按鈕（建議行動） |
| `HelpTooltip` | `@/components/ui/help-tooltip` | 說明提示 |
| `SectionIntro` | `@/components/ui/section-intro` | 區段說明文字 |
| `KnowledgeRefsPanel` | `@/components/create/KnowledgeRefsPanel` | 知識參考面板 |

---

## [TYPES]

| Type | 來源 | 說明 |
|:-----|:-----|:-----|
| `WantCriterion` | `@/types/decisionRecord` | WANT 標準（id, name, weight, description） |
| `WantScore` | `@/types/decisionRecord` | WANT 評分（alternativeId, alternativeName, scores, weightedTotal） |
| `KtDecision` | `@/types/decisionRecord` | KT 決策（selectedAlternativeId/Name, rationale, riskAcceptance, actionItems, decisionDate, status） |
| `Signature` | `@/types/decisionRecord` | 簽核（name, role, status, signedAt, note） |
| `SignatureStatus` | `@/types/decisionRecord` | pending / signed |
| `ActionItem` | `@/types/decisionRecord` | 行動項目（id, description, assignee, dueDate） |
| `DecideGateItem` | `@/types/decisionRecord` | Gate 檢查項（label, passed） |
| `AdverseConsequence` | `@/types/decisionRecord` | 負面後果（id, alternativeId, description, probability, severity, level, mitigation） |
| `ACProbability` / `ACSeverity` | `@/types/decisionRecord` | AC 機率/嚴重度等級 |
| `DEFAULT_WANT_TEMPLATE` | `@/types/decisionRecord` | W1-W7 標準模板 |

---

## [GATE CHECKS]

### Gate V2 — 決策記錄完整性檢查

| # | 檢查項目 | 判定邏輯 |
|:--|:---------|:---------|
| 1 | WANT 評分已完成 (含 W7 驗證可行性) | `allScored && criteria.length >= 3` |
| 2 | 負面後果 (AC) 已評估 | `adverseConsequences.length > 0` |
| 3 | 決策方案已選擇 | `!!decision.selectedAlternativeId` |
| 4 | 決策理由已填寫 (>=20 字元) | `decision.rationale.length >= 20` |
| 5 | 至少 1 項行動計畫 | `decision.actionItems.length >= 1` |

### Phase Gate V — Converge 階段完成檢查

| # | 檢查項目 | 判定邏輯 |
|:--|:---------|:---------|
| 1 | Gate V2 已通過 | `gate32Passed` |
| 2 | 決策已確認 (Confirmed) | `decision.status === 'confirmed' \|\| decision.status === 'signed'` |
| 3 | 決策報告已匯出 | `exported === true` |

- **pass_action**: 導航至 `/projects/:id/feynman`（Feynman 內化頁）
- **fail_action**: 按鈕 disabled + Tooltip "請完成所有條件"

---

## [NAVIGATION]

| 方向 | 目標 | 觸發 |
|:-----|:-----|:-----|
| 返回 | `/projects/:id` | Header BackButton |
| 通過 Phase Gate V | `/projects/:id/feynman` | Phase Gate V 通過按鈕 |
