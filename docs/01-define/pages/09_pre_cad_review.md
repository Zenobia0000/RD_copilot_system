# Page-Level Prompt: PreCadReview Pre-CAD 審查

> X5-P2 (Gate P) — 評估候選方案的五維品質，確認 Gate P 門檻後選擇存活方案進入 CAD 階段。

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | D/X/V 編號化：Phase 2 收尾 → X5-P2 (Gate P)；route 確認為 `/projects/:id/pre-cad`；SpatialTraceHover 已實作（移除「實作中」標記）；移除 AA/SCAMPER 殘留；選擇條件由 3-5 條更正為 >=1 條（對齊 code） |
| v2.0 | 2026-04-20 | 初版 page spec |

---

## [PAGE META]
- **page_name**: PreCadReview
- **route_path**: `/projects/:id/pre-cad`
- **page_type**: evaluation + approval
- **primary_goal**: 讓審查者針對每個候選方案完成五維審查（空間約束/解耦程度/可驗證性/主要風險/最小 CAD 工作量），並選擇存活方案進入 CAD
- **secondary_goal**: 確認 Gate P 門檻（Fatal+Major 矛盾 100% 收斂），提供 AI 空間追蹤分析輔助決策
- **target_users**: RD 工程師、專案主管、審查委員
- **entry_point**: Create 頁面完成後導航，或 Dashboard 直接進入
- **expected_time_on_page**: 15 ~ 45 分鐘

---

## [STRUCTURE: SECTIONS]
1. **Header**
   - section_type: navigation
   - section_purpose: 返回 Dashboard 按鈕、頁面標題與副標題
2. **OverviewCards**
   - section_type: dashboard
   - section_purpose: 四張概覽卡片 — Pre-CAD Confidence Score、Gate P 門檻、收斂圖摘要、約束可行性
3. **CandidateList**
   - section_type: selection + review
   - section_purpose: 候選方案卡片列表，支援勾選與審查
4. **ConclusionApproval**
   - section_type: approval
   - section_purpose: 顯示已選方案、審查結論備註、批准按鈕
5. **ReviewDialog**
   - section_type: modal
   - section_purpose: 五維審查對話框，含 AI 空間追蹤分析

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | `<Button variant="ghost" size="icon">` | required | ArrowLeft icon，onClick 導航至 `/projects/:id` |
  | Title | `<h1>` | required | "Pre-CAD 審查"，text-2xl font-bold tracking-tight，Noto Sans TC 字型 |
  | Subtitle | `<p>` | required | "評估候選方案，確認 Gate P 門檻後選擇 3-5 條進入 CAD 階段"，text-sm text-muted-foreground |
- **states**: 無
- **copy_constraints**: 標題使用繁體中文

### Section: OverviewCards
- **layout**: grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ConfidenceScoreCard | Card | required | 顯示 Pre-CAD Confidence Score（百分比），Progress bar，公式說明 |
  | GatePThresholdCard | Card | required | 顯示 Gate P 達標/未達標狀態，ShieldCheck/ShieldAlert icon |
  | ConvergenceSummaryCard | Card | required | Fatal/Major/Minor 已解決/總數，分色 Badge 顯示 |
  | ConstraintFeasibilityCard | Card | required | 約束可行性驗證列表（已驗證/存疑/不可行），可捲動 |
- **states**:
  - ConfidenceScore: 色碼 — >=100% emerald，>=50% amber，<50% destructive
  - GateP: 達標（emerald border + ShieldCheck）/ 未達標（destructive border + ShieldAlert）
  - ConstraintFeasibility: 各約束狀態 Badge 色碼 — verified(emerald)/questionable(amber)/infeasible(red)
- **copy_constraints**: 公式描述「converged(Fatal+Major) / total(Fatal+Major)」，門檻要求「Fatal+Major 矛盾 Confidence = 100%」

### Section: CandidateList
- **layout**: grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | CandidateCard | Card | required | 每個候選方案一張卡片 |
  | SelectCheckbox | Checkbox | required | 勾選方案進入最終選擇 |
  | SolutionName | `<h3>` | required | 方案名稱，font-semibold text-sm line-clamp-1 |
  | Description | `<p>` | required | 方案描述，text-sm text-muted-foreground line-clamp-2 |
  | ReviewStatusBadge | Badge | required | 已審查/審查中/待審查 三態 |
  | MustStatusIcons | icon-row | required | 各 MUST 條件通過/不通過/未評估 icon |
  | ReviewButton | Button | required | Eye icon + "審查"/"查看"，開啟 ReviewDialog |
- **states**:
  - unselected: 預設卡片樣式
  - selected: ring-2 ring-primary 高亮
  - reviewed: Badge 顯示「已審查」
  - partial: Badge 顯示「審查中」（部分維度已評分）
  - pending: Badge 顯示「待審查」
  - empty: 無候選方案時顯示空狀態卡片
- **copy_constraints**: 空狀態提示「請先在方案探索頁面生成並通過 MUST 快篩」

### Section: ConclusionApproval
- **layout**: Card > CardHeader + CardContent，ClipboardCheck icon 標題
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | SelectedCount | `<p>` | required | 已選擇 N 條方案（需 3-5 條） |
  | SelectedBadges | Badge-row | optional | 已選方案名稱 Badge 列表 |
  | ConclusionTextarea | Textarea | optional | 審查結論備註，maxLength=500，placeholder "記錄審查會議的關鍵討論和決策原因..." |
  | ApproveButton | Button | required | "批准審查"，disabled 條件：selectedIds < 3 或 > 5 / 未全部審查 / Gate P 未達標 |
  | GateWarning | `<p>` | optional | Gate P 未達標時顯示紅色警告，ShieldAlert icon |
  | ReviewWarning | `<p>` | optional | 未完成所有審查時顯示提示 |
- **states**:
  - can-approve: 所有條件滿足，ApproveButton 啟用
  - blocked-gate: Gate P 未達標，顯示紅色警告
  - blocked-review: 尚有未審查方案，顯示提示
  - blocked-count: 選擇數量不在 3-5 範圍
  - submitting: ApproveButton 顯示 Loader2 spinner，disabled
  - approved: toast.success 後導航至 Dashboard
- **copy_constraints**: 批准條件明確列出，使用繁體中文

### Section: ReviewDialog
- **layout**: Dialog > DialogContent (max-w-lg max-h-[90vh] overflow-y-auto) > Accordion
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | DialogTitle | `<DialogTitle>` | required | "{方案名稱} — 審查評估" |
  | Description | `<p>` | required | 方案描述 |
  | DimensionAccordion | Accordion (type="multiple") | required | 5 個審查維度，預設全部展開 |
  | DimensionLabel | `<span>` | required | 維度標題 + rating icon（pass=Check/concern=AlertTriangle/fail=X） |
  | SpatialTraceHover | `SpatialTraceHover` | optional | 僅空間約束維度顯示，AI 空間追蹤結果（WBS 10.3）；已實作，顯示 spatial_trace + spatial_score |
  | RatingRadioGroup | RadioGroup | required | 三選一：通過/有疑慮/不通過 |
  | SummaryTextarea | Textarea | optional | 評估摘要，maxLength=200 |
  | CompleteButton | Button | required | "完成審查"，需所有維度已評分 |
  | CloseButton | Button | required | "關閉" |
- **states**:
  - loading: SpatialTraceHover 顯示「空間追蹤計算中...」
  - done: SpatialTraceHover 顯示分析結果（trace + score）
  - error: SpatialTraceHover 顯示「AI 分析失敗」
  - incomplete: 完成審查時 toast.error "請完成所有審查維度的評估"
  - complete: 標記方案為已審查，關閉 Dialog
- **copy_constraints**: 五維度標籤與描述使用繁體中文；Rating 選項：通過/有疑慮/不通過

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入頁面，載入候選方案、收斂統計、約束條件
2. 查看四張概覽卡片了解整體狀態（Confidence Score、Gate P、收斂摘要、約束可行性）
3. 瀏覽候選方案卡片列表，勾選 Checkbox 選擇方案
4. 點擊「審查」按鈕 → 開啟 ReviewDialog → 同時觸發 `preCadAnalyze` AI 分析
5. 在 Dialog 中逐一評估五個維度（空間約束/解耦/可驗證性/風險/最小 CAD），選擇 rating + 填寫摘要
6. 空間約束維度自動顯示 SpatialTraceHover，提供 AI 空間追蹤得分
7. 完成所有維度評分後點擊「完成審查」→ 方案標記為已審查
8. 重複步驟 4-7 直到所有方案已審查
9. 在結論區域填寫備註（選填），確認選擇 3-5 條方案
10. Gate P 達標 + 全部已審查 + 數量正確 → 點擊「批准審查」→ 導航至 Dashboard

### RWD 行為差異
- **Desktop (>=1280px)**: 概覽卡片 4 欄，候選方案 3 欄
- **Tablet (768-1279px)**: 概覽卡片 2 欄，候選方案 2 欄
- **Mobile (<768px)**: 概覽卡片 1 欄，候選方案 1 欄，ReviewDialog 全螢幕

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Hook / Function | Method | Purpose |
  |:-----------------|:-------|:--------|
  | `usePreCadSolutions(projectId)` | GET | 取得候選方案清單（已通過 MUST 快篩） |
  | `usePreCadConvergenceStats(projectId)` | GET | 取得收斂統計（confidenceScore, fatal/major/minor resolved/total） |
  | `useConstraints(projectId)` | GET | 取得專案約束條件（含 feasibility 狀態） |
  | `preCadAnalyze(solutionId, payload)` | POST | AI 空間追蹤分析（stateless，結果不持久化），回傳 spatial_trace + spatial_score |
- **error_cases**:
  - 候選方案為空: 顯示空狀態卡片，提示返回方案探索頁面
  - AI 分析失敗: SpatialTraceHover 顯示「AI 分析失敗」，不阻擋審查流程
  - Gate P 未達標: ApproveButton disabled，顯示紅色警告訊息
  - 選擇方案數量不符: toast.error 提示具體原因（少於 3 / 多於 5）
  - 提交失敗: toast.error，保留當前狀態

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面載入時顯示 Loader2 loading 狀態
- [ ] Confidence Score 卡片正確計算並顯示百分比與 Progress bar
- [ ] Confidence Score 色碼正確：>=100% emerald，>=50% amber，<50% destructive
- [ ] Gate P 門檻正確判斷：confidenceScore === 100 為達標
- [ ] 收斂摘要正確顯示 Fatal/Major/Minor 解決數與總數
- [ ] 約束可行性卡片正確顯示各約束狀態 Badge
- [ ] 候選方案卡片正確顯示名稱、描述、MUST 狀態、審查狀態
- [ ] 可勾選方案，選中時顯示 ring-2 ring-primary 高亮
- [ ] ReviewDialog 正確顯示五個審查維度，預設全部展開
- [ ] 每個維度支援 pass/concern/fail 三選一 + 摘要文字
- [ ] 空間約束維度正確觸發 `preCadAnalyze` 並顯示 SpatialTraceHover
- [ ] AI 分析狀態正確顯示：loading → done/error
- [ ] 完成審查需所有維度已評分，否則 toast.error 提示
- [ ] 批准條件：3-5 條方案 + 全部已審查 + Gate P 達標
- [ ] 不滿足條件時 ApproveButton disabled 並顯示對應提示
- [ ] 批准成功後 toast.success 並導航至 `/projects/:id`
- [ ] 審查結論備註支援 maxLength=500
- [ ] AI 分析結果按 solutionId 快取，同一方案不重複呼叫
