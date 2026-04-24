# Page-Level Prompt: DecisionRecord 決策記錄

> 整合 KT 決策分析（MUST/WANT/AC）、風險評估與矛盾收斂狀態，完成正式決策記錄、簽核與報告匯出。

---

## [PAGE META]

- **page_name**: DecisionRecord
- **route_path**: `/projects/:id/decide`
- **page_type**: decision_workspace
- **primary_goal**: 讓 RD 工程師與決策者基於 KT 決策分析（MUST 通過/淘汰、WANT 加權評分、負面後果評估）完成方案選定，記錄決策理由與行動項目，通過 Gate 3.2 與 Phase Gate 3 完成 Converge 階段
- **secondary_goal**: 支援決策報告匯出（PDF/JSON）與多角色簽核，確保決策可追溯、可解釋
- **target_users**:
  - 主要：RD 工程師（填寫決策內容、行動項目）
  - 次要：RD 主管（確認決策、簽核）
  - 次要：PM / 品質工程師 / 高階主管（簽核）
- **entry_point**: DesignReview 頁面 Gate 3.1 通過後點擊「進入 Decide」 / Dashboard 專案頁面直接進入
- **expected_time_on_page**: 15 - 45 分鐘（完整決策含評分、填寫理由、行動項目、簽核）

---

## [STRUCTURE: SECTIONS]

1. **phase_header**
   - section_type: header
   - section_purpose: Phase 3 階段標示、頁面標題、狀態 Badge（草稿/已確認/已簽核）、返回按鈕與 SectionIntro

2. **decision_overview**
   - section_type: summary_card
   - section_purpose: 決策概覽：選定方案、決策者、決策日期、當前狀態

3. **kt_analysis_results**
   - section_type: analysis_section
   - section_purpose: 承載 KT 決策分析四大子區塊：MUST 結果、WANT 評分、風險評估、負面後果分析、矛盾收斂摘要

4. **decision_conclusion**
   - section_type: form_card
   - section_purpose: 選定主路線/備援方案、填寫決策日期與理由、風險接受聲明

5. **action_items**
   - section_type: accordion_list
   - section_purpose: 行動項目列表（新增/AI 建議/編輯/刪除），每項含描述、負責人、到期日

6. **confirm_decision**
   - section_type: cta
   - section_purpose: 確認決策按鈕（鎖定記錄）或回到草稿按鈕

7. **export_section**
   - section_type: export_card
   - section_purpose: 匯出 PDF / JSON 報告（需先確認決策）

8. **signature_section**
   - section_type: signature_panel
   - section_purpose: 多角色簽核（新增簽核人、簽核、撤回）

9. **knowledge_refs_panel**
   - section_type: reference_panel
   - section_purpose: 相關知識參考連結（WBS 3.4.2）

10. **gate_32**
    - section_type: gate_check
    - section_purpose: Gate 3.2 決策記錄完整性檢查（5 項條件）

11. **phase_gate_3**
    - section_type: phase_gate
    - section_purpose: Phase Gate 3 Converge 階段完成檢查（3 項條件），通過後進入 Feynman 內化

---

## [SECTION COMPONENT SPEC]

### Section: phase_header

- **layout**: 頂部 1px 主色條 + 標題區（返回按鈕 + 標題/副標題 + 狀態 Badge）
- **elements**:
  - phase_bar: Div / required / h-1 w-full rounded-full bg-primary
  - back_button: Button(variant="ghost", size="sm") / required / ArrowLeft + "返回"，導向 `/projects/:id`
  - title: H1 / required / "決策記錄" + HelpTooltip（"完整記錄設計決策的過程、依據、結論和後續行動，確保決策可追溯和可解釋。"）
  - phase_label: Body SM / required / "Phase 3: Converge > Decide"
  - status_badge: Badge / required / 草稿(secondary) / 已確認(primary) / 已簽核(accent)
  - section_intro: SectionIntro / required / 說明頁面整合 MUST/WANT、風險、矛盾收斂的用途
- **states**:
  - draft: Badge 顯示 "草稿"
  - confirmed: Badge 顯示 "已確認"
  - signed: Badge 顯示 "已簽核"
- **copy_constraints**: 標題固定；HelpTooltip 最多 60 字

### Section: decision_overview

- **layout**: Card 容器，CardHeader + CardContent，3 欄網格（sm:3）
- **elements**:
  - header_icon: Flag icon / required / 主色，16x16
  - card_title: CardTitle / required / "決策概覽"
  - decision_statement: Body LG Bold / conditional / 已選方案時顯示 "選定方案：{name}"；未選時 "尚未選定方案，請在下方 KT 決策分析中完成選擇。"
  - decision_maker: InfoItem / required / User icon + "決策者" + 簽核人中 role="RD 主管" 的姓名，未指定時 "待指定"
  - decision_date: InfoItem / required / CalendarDays icon + "決策日期" + 日期值
  - decision_status: InfoItem / required / TrendingUp icon + "狀態" + 狀態 Badge
- **states**:
  - no_selection: 決策聲明為 italic muted 提示文字
  - selected: 決策聲明為 bold 正常文字
- **copy_constraints**: 決策聲明最多 100 字

### Section: kt_analysis_results

- **layout**: 垂直堆疊子區塊，h2 標題 + Trophy icon

#### Sub-section: MUST 結果表格

- **layout**: Card + Table
- **elements**:
  - table: Table / required / 欄位：方案 / 結果(Badge: 通過=primary, 淘汰=destructive) / 原因
- **states**:
  - default: 表格正常顯示
- **copy_constraints**: 原因欄自動生成文字

#### Sub-section: WANT 評分結果

- **layout**: Card + 可展開評分表
- **elements**:
  - bar_chart: Recharts BarChart(vertical) / conditional / 各方案加權總分橫條圖，排名第一為主色，其餘灰色
  - radar_chart: Recharts RadarChart / conditional / 各方案各維度雷達圖，排名第一為主色填充
  - recommendation: Alert(bg-primary/5) / conditional / Trophy icon + "推薦方案：{name} (總分: {score})"
  - expand_toggle: Button(variant="ghost") / required / "展開評分表" / "收起評分表" 切換
  - scoring_table (expanded): Table / conditional / 欄位：條件(Input) / 權重(Input 1-10) / 各方案評分(Input 1-10 + 加權分) / 刪除按鈕
    - total_row: 加權總分匯總行，排名第一標記 "*"
  - template_button: Button(variant="secondary") / optional / "載入標準模板 (W1-W6)"
  - add_criterion_button: Button(variant="ghost") / optional / Plus + "新增標準"
- **states**:
  - collapsed: 僅顯示圖表 + 推薦方案
  - expanded: 顯示完整評分表
  - locked: 決策已確認時所有 Input disabled
- **copy_constraints**: 條件名稱最多 80 字；雷達圖軸標籤截斷至 6 字

#### Sub-section: 風險評估表格

- **layout**: Card + Table
- **elements**:
  - table: Table / required / 欄位：風險 ID(mono) / 描述 / 嚴重度(Badge) / 機率 / 等級(Badge: 重大=destructive) / 緩解措施 / 監控指標
- **states**:
  - default: 唯讀表格顯示

#### Sub-section: 負面後果分析 (AC)

- **layout**: Card + Table
- **elements**:
  - header: AlertTriangle icon + "負面後果分析 (AC)" + HelpTooltip
  - table: Table / required / 欄位：AC ID(mono) / 方案 / 負面後果 / 機率(高/中/低) / 嚴重度(高/中/低) / 等級(Badge: H*/H=destructive, M=secondary, L=outline) / 緩解措施
  - empty_state: Caption / conditional / "尚無負面後果評估"
- **states**:
  - default: 表格正常顯示
  - empty: 空狀態提示

#### Sub-section: 矛盾收斂摘要

- **layout**: Card + 4 欄網格（sm:4）
- **elements**:
  - confidence_score: StatCard / required / "{N}%" 大字 + "Confidence Score"
  - fatal_progress: StatCard / required / "{resolved}/{total}" + "Fatal 已解決" + Progress bar
  - major_progress: StatCard / required / "{resolved}/{total}" + "Major 已解決" + Progress bar
  - minor_progress: StatCard / required / "{resolved}/{total}" + "Minor 已解決" + Progress bar
- **states**:
  - default: 各統計卡片正常顯示

### Section: decision_conclusion

- **layout**: Card(border-l-4 border-l-primary)，表單佈局
- **elements**:
  - main_route_select: Select / required / "主路線（選定方案）*"，選項為按 WANT 排名的方案 + 分數
  - backup_route_select: Select / optional / "備援方案"，排除已選主路線
  - date_input: Input(type="date") / required / "決策日期 *"，寬度 160px
  - rationale_textarea: Textarea / required / "選擇理由 *"（至少 20 字元），rows=4，maxLength=2000，附字數計數器
  - risk_acceptance_textarea: Textarea / optional / "風險接受聲明"，rows=3，maxLength=1000
- **states**:
  - draft: 所有欄位可編輯
  - locked: 決策已確認時所有欄位 disabled
- **copy_constraints**: 選擇理由最少 20 字元、最多 2000 字元；風險接受最多 1000 字元

### Section: action_items

- **layout**: Card + Accordion 列表
- **elements**:
  - card_title: CardTitle / required / "行動項目"
  - accordion_item: AccordionItem / required (per item) / 包含：
    - trigger: Badge(序號) + 描述文字
    - content: description Input(maxLength=100) + assignee Input(maxLength=50) + dueDate Input(type="date") + 刪除按鈕
  - add_button: Button(variant="ghost") / required / Plus + "新增行動"
  - ai_button: AiButton / required / "建議行動"
  - empty_state: Body SM / conditional / "尚無行動計畫"
- **states**:
  - default: Accordion 可展開/收合
  - locked: 決策已確認時隱藏新增/AI/刪除按鈕，欄位 disabled
  - ai_loading: AI 按鈕 loading 狀態
- **copy_constraints**: 描述最多 100 字；負責人最多 50 字

### Section: confirm_decision

- **layout**: 按鈕列，水平排列
- **elements**:
  - confirm_button: Button(primary) / conditional / Check icon + "確認決策"（草稿時顯示）
  - revert_button: Button(variant="outline") / conditional / "回到草稿"（已確認時顯示）
- **states**:
  - draft: 顯示確認按鈕，驗證：需選方案 + 理由 >= 20 字元 + 至少 1 行動
  - confirmed: 顯示回到草稿按鈕
- **copy_constraints**: 按鈕文字固定

### Section: export_section

- **layout**: Card 容器
- **elements**:
  - card_title: CardTitle / required / "匯出報告"
  - pdf_button: Button / required / FileDown icon + "匯出 PDF"，需先確認決策
  - json_button: Button(variant="secondary") / required / FileJson icon + "匯出 JSON"，需先確認決策
  - export_success: Alert(bg-primary/5) / conditional / CheckCircle + "報告已匯出"
- **states**:
  - locked_required: 未確認決策時按鈕 disabled + Tooltip "請先確認決策"
  - exporting: Loader2 旋轉 + 按鈕 disabled
  - exported: 顯示成功提示
- **copy_constraints**: 按鈕文字固定

### Section: signature_section

- **layout**: Card 容器，垂直堆疊簽核人列
- **elements**:
  - card_title: CardTitle / required / "審查人簽核"
  - signature_row: Div(border rounded-lg) / required (per signer) / 包含：
    - name_input: Input / required / "姓名 *"，maxLength=50
    - role_select: Select / required / 選項：RD 工程師 / RD 主管 / PM / 品質工程師 / 高階主管 / 其他
    - sign_button: Button(variant="outline") / conditional / "簽核"（未簽時顯示，名稱 >= 2 字元啟用）
    - signed_badge: Badge(primary/10) / conditional / Check icon + "已簽核" + 簽核日期（已簽時顯示）
    - revert_button: Button(variant="ghost") / conditional / "撤回"（已簽時顯示）
  - add_signer_button: Button(variant="ghost") / required / Plus + "新增簽核人"
  - signed_count: Caption / conditional / "{signed}/{total} 已簽核"
  - empty_state: Body SM / conditional / "尚無簽核人"
- **states**:
  - pending: 姓名/角色可編輯 + 簽核按鈕
  - signed: 欄位 disabled + 已簽核 Badge + 撤回按鈕
- **copy_constraints**: 姓名最多 50 字

### Section: gate_32

- **layout**: 圓角邊框區塊，左側 1px 主色豎條
- **elements**:
  - header: "Gate 3.2 -- 決策記錄完整性檢查" + 狀態 Badge
  - checklist: CheckItem[] / required / 5 項檢查：
    1. WANT 評分已完成 (含 W7 驗證可行性)
    2. 負面後果 (AC) 已評估
    3. 決策方案已選擇
    4. 決策理由已填寫 (>=20 字元)
    5. 至少 1 項行動計畫
- **states**:
  - passed: Badge "Gate 3.2 Passed" 主色
  - not_passed: Badge "Gate 3.2 未通過" destructive

### Section: phase_gate_3

- **layout**: 圓角邊框區塊，border-2 double 樣式，border-primary bg-primary/5
- **elements**:
  - header: Flag icon + "Phase Gate 3 -- Converge 階段完成檢查" + 狀態 Badge
  - checklist: CheckItem[] / required / 3 項檢查：
    1. Gate 3.2 已通過
    2. 決策已確認 (Confirmed)
    3. 決策報告已匯出
  - proceed_button: Button(primary, large) / conditional / "Phase Gate 3 通過 -> 進入 Feynman 內化" + ArrowRight，導向 `/projects/:id/feynman`
  - blocked_button: Button(disabled) / conditional / "專案完成 ->" + Tooltip "請完成所有條件"
- **states**:
  - passed: Badge "Phase 3 Passed *" 主色，按鈕啟用
  - not_passed: Badge "Phase 3 未通過" destructive，按鈕 disabled

### Section: confirm_modal

- **layout**: Dialog(max-w-sm)
- **elements**:
  - title: DialogTitle / required / "確認決策"
  - message: Body SM / required / "確認後決策記錄將鎖定，是否繼續？"
  - cancel_button: Button(variant="outline") / required / "取消"
  - confirm_button: Button(primary) / required / "確認"
- **states**:
  - open: Modal 顯示
  - closed: Modal 隱藏

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. 使用者進入頁面 -> 平行載入 alternatives、preCadSolutions、convergenceStats、risks、decision、criteria、scores、adverseConsequences、signatures、actionItems（共 10+ 組 API）
2. 載入中顯示全頁 Loader2
3. 決策概覽區顯示當前選定方案（若有）、決策者、日期、狀態
4. KT 分析：檢視 MUST 結果表 -> 展開 WANT 評分表進行評分（或載入模板） -> 查看風險評估 -> 查看 AC 評估 -> 查看矛盾收斂摘要
5. WANT 評分：可新增/刪除標準、調整權重（1-10）、為每方案每標準打分（1-10） -> 系統即時計算加權總分 -> 圖表即時更新
6. 決策結論：選擇主路線 + 備援方案 -> 填寫日期 -> 填寫選擇理由 (>= 20 字) -> 填寫風險接受聲明
7. 行動項目：新增行動 / AI 建議行動 -> 填寫描述+負責人+到期日
8. 確認決策 -> Modal 確認 -> 記錄鎖定（confirmed 狀態）
9. 匯出報告 -> PDF / JSON 按鈕（需先確認）
10. 簽核 -> 新增簽核人 -> 選角色 -> 簽核 -> 追蹤簽核進度
11. Gate 3.2 + Phase Gate 3 全通過 -> 進入 Feynman 內化

### RWD 行為差異

| 斷點 | 行為 |
|:-----|:-----|
| Desktop (>=768px) | page-shell-medium 佈局；決策概覽 3 欄；WANT 圖表 2 欄（Bar + Radar）；決策結論主路線/備援 2 欄；簽核人列 flex-row |
| Mobile (<768px) | 決策概覽 1 欄堆疊；WANT 圖表 1 欄堆疊；決策結論 1 欄堆疊；簽核人列 flex-col；評分表格水平捲動 |

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useAlternatives(projectId)` — 取得方案列表（id + name），用於 MUST 結果推導與 WANT 評分欄
  - `usePreCadSolutions(projectId)` — 取得 Pre-CAD 方案資料
  - `usePreCadConvergenceStats(projectId)` — 取得矛盾收斂統計（confidenceScore / fatal / major / minor 解決數與總數）
  - `useRisks(projectId)` — 取得風險列表，推導風險評估表
  - `useDecision(projectId)` — 取得決策記錄（selectedAlternativeId / name / rationale / riskAcceptance / decisionDate / status）
  - `useUpsertDecision()` — 新增或更新決策記錄
  - `useWantCriteria(projectId)` — 取得 WANT 標準列表
  - `useCreateWantCriterion()` — 新增 WANT 標準
  - `useUpdateWantCriterion()` — 更新 WANT 標準（name / weight）
  - `useDeleteWantCriterion()` — 刪除 WANT 標準（最少保留 3 項）
  - `useWantScores(projectId)` — 取得各方案各標準評分
  - `useUpsertWantScore()` — 更新評分
  - `useAdverseConsequences(projectId)` — 取得負面後果列表
  - `useSignatures(projectId)` — 取得簽核人列表
  - `useCreateSignature()` — 新增簽核人
  - `useUpdateSignature()` — 更新簽核狀態
  - `useActionItems(projectId, decisionId)` — 取得行動項目列表
  - `useCreateActionItem()` — 新增行動項目
  - `useUpdateActionItem()` — 更新行動項目
  - `useDeleteActionItem()` — 刪除行動項目
- **state_variables**:
  - `criteria: WantCriterion[]` — WANT 標準（從 hook 同步至 local state）
  - `scores: WantScore[]` — 各方案各標準評分（從 hook 同步至 local state）
  - `decision: KtDecision` — 決策記錄（selectedAlternativeId / name / rationale / riskAcceptance / actionItems / decisionDate / status）
  - `decisionId: string | undefined` — DB 決策記錄 ID
  - `signatures: Signature[]` — 簽核人列表
  - `exported: boolean` — 是否已匯出報告
  - `confirmModalOpen: boolean` — 確認決策 Modal 開關
  - `aiLoading: Record<string, boolean>` — AI 功能載入狀態（action / pdf / json）
  - `wantExpanded: boolean` — WANT 評分表展開/收合
  - `adverseConsequences: AdverseConsequence[]` — 負面後果列表
- **error_cases**:
  - 未選方案時確認決策：toast 錯誤 "請選擇方案"
  - 決策理由 < 20 字元：toast 錯誤
  - 無行動項目：toast 錯誤 "至少 1 項行動計畫"
  - WANT 標準 < 3 項時刪除：toast 錯誤 "至少保留 3 項標準"
  - 載入模板覆蓋確認：confirm dialog

---

## [ACCEPTANCE CRITERIA]

- [ ] 頁面正確載入 10+ 組 API 資料並同步至 local state
- [ ] 載入中顯示 Loader2；各 hook 資料到齊後正常渲染
- [ ] 決策概覽正確顯示選定方案、決策者（RD 主管角色簽核人）、日期、狀態 Badge
- [ ] MUST 結果表正確從 alternatives 推導通過/淘汰（mustScores 無 fail = 通過）
- [ ] WANT 評分表支援新增/刪除標準（最少 3 項）、載入 W1-W6 模板、調整權重與評分
- [ ] WANT Bar Chart 與 Radar Chart 即時反映評分變化，排名第一方案主色標記
- [ ] 風險評估表正確從 risks 推導嚴重度/機率/等級
- [ ] 負面後果分析 (AC) 表格正確顯示，空時顯示提示
- [ ] 矛盾收斂摘要 4 格統計卡正確顯示 Confidence Score 與 Fatal/Major/Minor 解決進度
- [ ] 決策結論：主路線/備援方案 Select 按 WANT 排名排序，已選主路線從備援排除
- [ ] 選擇理由驗證 >= 20 字元，字數計數器顯示 {N}/2000
- [ ] 行動項目 Accordion 可展開/收合，支援新增/刪除/AI 建議
- [ ] 確認決策後記錄鎖定（所有表單 disabled / 隱藏新增刪除按鈕），可回到草稿
- [ ] 匯出 PDF/JSON 需先確認決策，否則 disabled + Tooltip
- [ ] 簽核支援新增簽核人（6 種角色）、簽核（名稱 >= 2 字元）、撤回、追蹤已簽/總數
- [ ] Gate 3.2 五項檢查正確計算
- [ ] Phase Gate 3 三項檢查正確計算（Gate 3.2 + confirmed + exported）
- [ ] Phase Gate 3 通過後啟用「進入 Feynman 內化」按鈕；未通過時 disabled + Tooltip
- [ ] 確認決策 Modal 顯示警告文字，支援取消/確認
- [ ] 決策已確認（locked）時所有表單欄位 disabled，匯出按鈕啟用
