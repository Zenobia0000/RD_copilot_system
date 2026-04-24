# Page-Level Prompt: Explore 探索 / Conditional Stepper

> Phase 1 Define 的深化探索頁。透過 **Entry Grading** 判定問題成熟度，自動切換 **Level A（5-step 引導流）** 或 **Level B（3-tab 快速通道）**，完成問題定向、功能建模、問答探索、矛盾識別與因果迴路圖。

---

## [PAGE META]

- **page_name**: Explore
- **route_path**: `/projects/:id/explore`
- **page_type**: conditional workspace（Level A: stepper / Level B: tabs）
- **primary_goal**: 依問題成熟度自動路由至適當模式 — Level A 引導工程師從問題定向（5Why/KT）→ 功能建模（FA）→ 問答探索 → 矛盾識別 → CLD 完整走完；Level B 維持原 3-tab 快速通道，供已知 TC 的資深 RD 直接操作
- **secondary_goal**: 自動將問答中標記的假設同步至 Assumption Ledger，將標記的矛盾自動 formalize 為結構化矛盾記錄，並提供知識參考面板輔助決策
- **target_users**:
  - 主要：設計工程師（問題分析與矛盾識別）
  - 次要：團隊成員（審閱矛盾分類與因果圖）
- **entry_point**: 從 TaskDefinition 頁 Gate 1.1 通過後自動導航 / ProjectDashboard NavCard 點擊 "Explore" / URL 直接存取
- **expected_time_on_page**: Level A: 30 - 90 分鐘（首次完整引導流）；Level B: 20 - 60 分鐘（原有 3-tab 流程）；追加修訂 5 - 15 分鐘

---

## [CONDITIONAL RENDERING: Entry Grading]

### 觸發條件

首次進入 Explore 頁時（`projects.entry_level` 為 null），自動彈出 **EntryGradingModal**。

### Entry Grading Modal

- **目的**：判定使用者的問題成熟度（Level A / B / C），決定 Explore 的渲染模式
- **問句**：「您能填寫以下句型嗎？在 [系統] 中，為了改善 [改善參數]，[惡化參數] 會惡化。」
  - **能填寫** → Level B（已知 TC，快速通道）
  - **不確定 / 只有症狀** → Level A（需引導定向）
  - **功能缺失，無副作用** → Level C（SF-only 通道）
- **API**: `POST /analyst/entry-grading` → 回傳 `{ level: 'A' | 'B' | 'C', reasoning: string }`
- **持久化**：結果存入 `projects.entry_level`，後續進入不再觸發 Modal（可在 header 手動重新觸發）
- **可覆寫**：header 區域提供「切換模式」按鈕，允許 Level B 使用者手動切到 Level A，反之亦然

### 渲染路由

| Level | 渲染模式 | 說明 |
|:------|:---------|:-----|
| **A** | 5-step stepper | Problem Scoping → FA → Socratic → Contradictions → CLD |
| **B** | 3-tab 佈局（v1.0 原樣） | #socratic / #contradictions / #cld + FA 可選側面板 |
| **C** | 提示訊息 + 導向按鈕 | 顯示「此問題為功能缺失類型，建議直接進入 Create SF-only 通道」，按鈕導至 `/projects/:id/create?mode=sf-only` |

---

## [STRUCTURE: SECTIONS]

### 共用 Sections（Level A & B）

1. **page_header**
   - section_type: header
   - section_purpose: 返回按鈕、儲存狀態指示、頁面標題與步驟說明、Level 切換按鈕

2. **knowledge_panel**
   - section_type: reference_panel
   - section_purpose: KnowledgeRefsPanel 顯示頁面相關的知識參考資料

3. **gate_section**
   - section_type: gate_check
   - section_purpose: ExploreGates 元件包含 Gate 1.2 與 Phase Gate 1 兩組退出條件

### Level A 專屬 Sections（5-step stepper）

4. **stepper_navigation**
   - section_type: stepper
   - section_purpose: 5 步驟導航條，顯示當前進度與各步驟完成狀態

5. **step_0_problem_scoping**
   - section_type: analysis
   - section_purpose: 5 Why 根因分析 + KT Is/Is Not 範圍界定，產出根因假設與子系統聚焦

6. **step_1_function_analysis**
   - section_type: modeling
   - section_purpose: FA 功能建模，產出組件交互圖與 SF 診斷，確保矛盾定義在正確系統粒度

7. **step_2_socratic_tab**
   - section_type: questionnaire
   - section_purpose: 同 Level B 的 socratic_tab（共用元件）

8. **step_3_contradiction_tab**
   - section_type: list_workspace
   - section_purpose: 同 Level B 的 contradiction_tab（共用元件）

9. **step_4_cld_tab**
   - section_type: diagram
   - section_purpose: 同 Level B 的 cld_tab（共用元件）

### Level B 專屬 Sections（3-tab 原有佈局）

10. **tab_navigation**
    - section_type: tabs
    - section_purpose: 3 個 Tab 切換（蘇格拉底問答 / 矛盾識別 / 因果迴路圖），各 Tab 含統計 Badge

11. **socratic_tab**
    - section_type: questionnaire
    - section_purpose: 7 類蘇格拉底問答列表，支援回答、假設標記、矛盾標記與 AI 輔助

12. **contradiction_tab**
    - section_type: list_workspace
    - section_purpose: 矛盾列表，支援 TC / PC / SF 分類、嚴重度標記、AI 自動 formalize

13. **cld_tab**
    - section_type: diagram
    - section_purpose: 因果迴路圖編輯器，含節點 / 邊操作與斷路點標記

14. **fa_side_panel**
    - section_type: optional_panel
    - section_purpose: Level B 可選 FA 側面板，供已知 TC 的使用者補充功能建模（不阻擋 Gate）

---

## [SECTION COMPONENT SPEC]

### Section: page_header

- **layout**: flex row，左側返回按鈕，右側儲存狀態 + Level 切換按鈕；下方標題行含 phase 色條（藍色）+ 標題 + HelpTooltip + 步驟描述
- **elements**:
  - back_button: Button(ghost) / required / `<ArrowLeft>` 圖標 + "返回 Dashboard"，導航至 `/projects/:id`
  - save_indicator: Span / conditional / saveStatus 為 saving 時顯示 "Saving..."；saved 時顯示 `<Check>` + "Saved"
  - level_switcher: Button(outline) / required / 顯示當前 Level（如 "Level B · 快速模式"），點擊可切換至 Level A 或 Level B
  - phase_bar: Div / required / `h-8 w-1 rounded-full bg-blue-500` 相位色條
  - title: H1 / required / "Explore — 問題探索" + HelpTooltip
  - subtitle: P / required / Level A: "Step 0–1.3 · 問題定向 → 功能建模 → 問答 → 矛盾 → 因果圖"；Level B: "Step 1.2–1.3 · 蘇格拉底問答 → 矛盾識別 → 因果迴路圖"
- **states**:
  - loading: 整頁替換為 Skeleton（標題 + stepper/tabs 骨架 + 3 組 h-32 內容骨架）
  - default: 完整 header 渲染
- **copy_constraints**: 標題固定 "Explore — 問題探索"；subtitle 依 Level 動態調整

### Section: stepper_navigation（Level A only）

- **layout**: 水平步驟條，5 步驟，每步顯示序號 + 名稱 + 完成狀態圖標
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | step_0 | step | required | "問題定向" (5Why + KT)，圖標 `<Search>` |
  | step_1 | step | required | "功能建模" (FA)，圖標 `<GitFork>` |
  | step_2 | step | required | "問答探索" (Socratic)，圖標 `<MessageSquare>` |
  | step_3 | step | required | "矛盾識別" (Contradictions)，圖標 `<AlertTriangle>` |
  | step_4 | step | required | "因果迴路" (CLD)，圖標 `<Workflow>` |
- **states**:
  - pending: 灰色圓圈 + 灰色文字
  - current: 藍色圓圈（pulse 動畫）+ 黑色粗體文字
  - completed: 綠色勾選圓圈 + 灰色文字
  - skipped: 虛線圓圈 + "已跳過" 標記
- **skip 機制**: 每步底部提供「跳過此步驟」連結。跳過 FA（Step 1）時顯示確認提示：「跳過功能建模可能導致矛盾定義在錯誤粒度，建議完成。確定跳過？」
- **copy_constraints**: 步驟名稱使用繁體中文

### Section: step_0_problem_scoping（Level A only）

- **layout**: 雙欄佈局 — 左欄 5 Why Chain，右欄 KT Is/Is Not 矩陣
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | FiveWhyChain | card-list | required | 5 層 Why 鏈式卡片，每層可編輯原因描述 |
  | GenerateFiveWhyButton | AiButton | required | 觸發 `POST /analyst/five-why`，AI 基於 Brief 自動產出 5 Why chain |
  | KtMatrix | table | required | 4×2 矩陣（Is / Is Not × What / Where / When / Extent） |
  | GenerateKtButton | AiButton | required | 觸發 `POST /analyst/kt-analysis`，AI 基於 Brief + 5Why 產出 KT 分析 |
  | RootCauseSummary | card | conditional | 5Why + KT 完成後自動產出根因摘要（子系統 + TC 假設） |
  | SkipLink | link | optional | "跳過此步驟 →" |
- **states**:
  - empty: 初始狀態，顯示說明文字與生成按鈕
  - generating: AiButton 顯示 loading spinner
  - completed: 顯示 5Why chain + KT 矩陣 + 根因摘要
  - editing: 手動修改 5Why 或 KT 欄位
- **completion_criteria**: 至少 3 層 5Why 已填寫 且 KT 矩陣至少 2 個 Is/IsNot 配對已填
- **copy_constraints**: 使用繁體中文

### Section: step_1_function_analysis（Level A only）

- **layout**: 組件交互圖（React Flow / 力導向圖）+ SF 診斷面板
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ComponentGraph | diagram | required | 組件交互圖，節點 = 組件，邊 = 功能交互（有用/有害/不足） |
  | GenerateFaButton | AiButton | required | 觸發 `POST /analyst/function-analysis`，AI 基於 Brief + 5Why/KT + constraints 產出 FA |
  | SfDiagnosisPanel | panel | conditional | SF 三角模型診斷面板（S1-Field-S2，標記缺失/有害/不足） |
  | SubsystemBoundary | highlight | conditional | 在組件圖上高亮標記建議的系統邊界 |
  | SkipLink | link | optional | "跳過此步驟 →"（含警告確認） |
- **states**:
  - empty: 初始狀態，顯示說明文字與生成按鈕
  - generating: AI 分析中
  - completed: 顯示組件交互圖 + SF 診斷 + 系統邊界標記
  - editing: 手動調整組件/邊/邊界
- **completion_criteria**: 至少 3 個組件 且 至少 1 個 SF 三角已識別
- **copy_constraints**: 組件名稱使用英文（工程慣例），說明使用繁體中文

### Section: tab_navigation（Level B only）

- **layout**: Tabs 元件，3 欄等寬 grid TabsList（h-11），每個 TabsTrigger 含文字 + Badge
- **elements**:
  - tab_socratic: TabsTrigger / required / "蘇格拉底問答" + Badge 顯示 `{answeredCount}/{questions.length}`
  - tab_contradictions: TabsTrigger / required / "矛盾識別" + Badge 顯示 `{tcCount} TC + {pcCount} PC` (+ SF 數量 if > 0)
  - tab_cld: TabsTrigger / required / "因果迴路圖" + Badge 顯示 `{breakpointsCount} 斷路點`
- **states**:
  - active: 底部 3px 藍色邊框 (`border-b-blue-500`)
  - inactive: 預設樣式
  - badge_hidden: sm 以下螢幕 Badge 隱藏 (`hidden sm:inline-flex`)
- **copy_constraints**: Tab 標籤固定為中文；Badge 數字即時反映資料

### Section: socratic_tab（共用）

- **layout**: SocraticTab 元件，Level A 在 step_2 渲染，Level B 在 TabsContent value="socratic" 渲染，mt-5 間距
- **elements**:
  - socratic_tab: SocraticTab / required / 傳入 questions、onUpdateQuestions、onDeleteQuestion、isBriefStale、briefUpdatedAt、projectId、mission、constraints
- **states**:
  - default: 7 類問題按類別分組顯示（boundary, function, resource, time, environment, human, counter）
  - answering: 輸入回答中
  - tagging: 標記為假設或矛盾 → 觸發同步寫入 assumptions / contradictions 表
  - brief_stale: 當 Brief 更新時間晚於最新問題建立時間時顯示陳舊警告
  - deleting: 刪除問題後顯示 undo toast（5 秒內可復原）
- **copy_constraints**: 問題文字由 AI 或預設產生；回答需 >= 5 字元才計入已回答

### Section: contradiction_tab（共用）

- **layout**: ContradictionTab 元件，Level A 在 step_3 渲染，Level B 在 TabsContent value="contradictions" 渲染，mt-5 間距
- **elements**:
  - contradiction_tab: ContradictionTab / required / 傳入 contradictions、onUpdateContradictions、hasAnswers、projectId、mission、constraints、kpis、socraticAnswers
- **Level A 增強**：若 FA（Step 1）已完成，ContradictionTab 頂部顯示 FA 摘要橫幅：「系統邊界：[boundary]，建議聚焦子系統：[subsystem]。FA 已識別 N 個有害/不足交互。」
- **states**:
  - default: 矛盾列表，每項顯示類型 Badge（TC / PC / SF）、嚴重度、描述
  - empty: 無矛盾時提示使用者從問答中標記
  - formalizing: AI 自動 formalize 中（improving_param, worsening_param, engineering_statement, SF 模型等）
  - formalize_failed: 顯示 toast 警告 "AI 暫時無法自動分類此矛盾，請至矛盾識別手動指定類型"
  - fa_hint: Level A 且 FA 未完成時顯示建議提示：「建議先完成功能建模（Step 2），確保矛盾定義在正確粒度」
- **copy_constraints**: 矛盾工程描述由 AI formalize 產生

### Section: cld_tab（共用）

- **layout**: CldTab 元件，Level A 在 step_4 渲染，Level B 在 TabsContent value="cld" 渲染，mt-5 間距
- **elements**:
  - cld_tab: CldTab / required / 傳入 causalLoop、onUpdateCausalLoop、projectId、contradictions（字串陣列）、assumptions（字串陣列）、mission、constraints、kpis、socraticAnswers
- **states**:
  - default: 因果迴路圖顯示節點與邊
  - empty: 無節點時顯示空白畫布
  - editing: 新增 / 移動節點、建立邊連結
  - breakpoint_marking: 標記斷路點（節點 isBreakpoint = true）
- **copy_constraints**: 無特殊限制

### Section: fa_side_panel（Level B only）

- **layout**: 可展開/收合側面板（Drawer 或 Sheet），從右側滑入
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ToggleButton | Button(outline) | required | 在 header 或 tab 區域旁，圖標 `<GitFork>` + "功能建模（選填）" |
  | FaContent | panel | conditional | 展開後顯示與 Level A step_1_function_analysis 相同的 ComponentGraph + SfDiagnosisPanel |
- **states**:
  - collapsed: 僅顯示 ToggleButton
  - expanded: 側面板展開，顯示 FA 內容
- **copy_constraints**: 按鈕標籤明確標示「選填」，不造成 Level B 使用者壓力

### Section: knowledge_panel

- **layout**: KnowledgeRefsPanel 元件
- **elements**:
  - panel: KnowledgeRefsPanel / required / 傳入頁面知識參考資料（TODO: Sprint 5+ 替換為 useKnowledgeRefs hook）
- **states**:
  - default: 顯示參考資料列表
  - empty: 無參考資料時不渲染
- **copy_constraints**: 無特殊限制

### Section: gate_section

- **layout**: ExploreGates 元件，包含兩組 Gate 檢查
- **elements**:
  - explore_gates: ExploreGates / required / 傳入 gate12Items、phaseGate1Items、onNavigateNext、entryLevel
- **Gate 1.2 條件（共用）**:
  - 累計 >= 10 個回答（含 >= 10 假設已辨識）
  - 矛盾已處理（>= 1 個已確認，或確認無矛盾）
  - 7 類問題皆有回答
- **Gate 1.2 條件（Level A 額外）**:
  - 5 Why chain 至少 3 層已填寫（或已跳過）
  - FA 至少 1 個 SF 三角已識別（或已跳過）
- **Phase Gate 1 條件**:
  - 至少 1 個因果迴路圖已建立
  - 至少 3 個斷路點已標記
  - 所有矛盾已分類為 TC / PC / SF（或無矛盾）
- **states**:
  - incomplete: 部分條件未通過，導航按鈕 disabled
  - complete: 所有條件通過，點擊導航至 `/projects/:id/track`
- **copy_constraints**: Gate 條件文案固定如上；Level A 額外條件標註 "(Level A)"

---

## [INTERACTION & STATE FLOW]

### Entry Grading 流程

1. **頁面進入** → 檢查 `projects.entry_level`
2. **entry_level 為 null** → 彈出 EntryGradingModal → 使用者回答 → `POST /analyst/entry-grading` → 存入 DB → 關閉 Modal → 依 Level 渲染
3. **entry_level 已存在** → 直接依 Level 渲染（無 Modal）
4. **手動切換** → 點擊 level_switcher → 更新 `projects.entry_level` → 頁面重新渲染

### Level A 互動流程

1. **頁面載入** → 平行載入所有資料源 → Loading skeleton → 渲染 5-step stepper，預設在 Step 0
2. **Step 0 (Problem Scoping)** → 點擊 AI 生成 5Why → 編輯/確認 → 點擊 AI 生成 KT → 編輯/確認 → 根因摘要自動產出 → 「下一步」或「跳過」
3. **Step 1 (FA)** → 點擊 AI 生成 FA → 組件交互圖 + SF 診斷 → 編輯/確認 → 「下一步」或「跳過」（含警告）
4. **Step 2 (Socratic)** → 同 Level B 的蘇格拉底問答流程
5. **Step 3 (Contradictions)** → 同 Level B 的矛盾識別流程（增強：顯示 FA 摘要橫幅）
6. **Step 4 (CLD)** → 同 Level B 的因果迴路圖流程
7. **Gate 通過** → 導航至 `/projects/:id/track`

### Level B 互動流程（v1.0 原有，不變）

1. **頁面載入** → 平行載入 socratic questions / contradictions / CLD nodes & edges / brief / constraints / kpis / trackAssumptions → Loading skeleton → 資料就緒後渲染
2. **Tab 切換** → 更新 `activeTab` state + URL hash（`#socratic` / `#contradictions` / `#cld`）→ 觸發 save 狀態動畫
3. **蘇格拉底問答**:
   - 回答問題 → `handleUpdateQuestions` 呼叫 `updateQuestion.mutate` 更新 DB
   - 新增問題 → `createQuestion.mutate` 寫入 DB
   - 刪除問題 → `deleteQuestionMut.mutate` + 同步刪除關聯 assumption / contradiction + undo toast
   - 標記為假設 → 自動寫入 assumptions 表（含防重複檢查）
   - 標記為矛盾 → 自動寫入 contradictions 表 + 觸發 AI formalize（含防重複檢查，counter 類問題排除）
   - 取消假設標記 → 從 assumptions 表刪除
   - 取消矛盾標記 → 從 contradictions 表刪除
4. **矛盾識別**: ContradictionTab 內部處理 mutation，query 自動 refresh
5. **因果迴路圖**: CldTab 內部處理節點 / 邊 mutation，query 自動 refresh
6. **FA 側面板**（選填）：點擊 ToggleButton 展開 → 操作同 Level A Step 1 → 不影響 Gate
7. **Gate 通過** → 點擊導航按鈕 → 導航至 `/projects/:id/track`

### RWD 行為差異

- **Desktop**: `page-shell-kb` 佈局（含知識面板空間）；Level A stepper 水平顯示；Level B Tab Badge 完整顯示
- **Tablet**: Level A stepper 可能簡化為 shortLabel；Level B Tab Badge 完整顯示；知識面板可能摺疊
- **Mobile**: Level A stepper 改為垂直或下拉選單；Level B Tab Badge 隱藏（`hidden sm:inline-flex`）；Tab 觸發器文字縮小 (`text-xs`)；知識面板堆疊於底部

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - **Entry Grading（新增）**:
    - `useEntryGrading(projectId)` → 觸發 `POST /analyst/entry-grading`，回傳 `{ level: 'A' | 'B' | 'C', reasoning: string }`
  - **Problem Scoping（新增，Level A）**:
    - `useFiveWhy(projectId)` → 觸發 `POST /analyst/five-why`，回傳 5Why chain 結構
    - `useKtAnalysis(projectId)` → 觸發 `POST /analyst/kt-analysis`，回傳 KT Is/Is Not 矩陣
  - **Function Analysis（新增，Level A + Level B 側面板）**:
    - `useFunctionAnalysis(projectId)` → 觸發 `POST /analyst/function-analysis`，回傳組件交互圖 + SF 診斷
  - **Socratic（既有）**:
    - `useSocraticQuestions(id)` → 蘇格拉底問題列表（category, text, answer, taggedAsAssumption, taggedAsContradiction, aiSuggestedTag）
    - `useUpdateSocraticQuestion()` → 更新單一問題
    - `useCreateSocraticQuestion()` → 新增問題
    - `useDeleteSocraticQuestion()` → 刪除問題
  - **Contradictions（既有）**:
    - `useExploreContradictions(id)` → 矛盾列表（type, severity, status, engineeringStatement, source_question_id, SF 模型欄位等）
    - `contradictionFormalize(payload)` → AI 矛盾 formalize API（回傳 type, improving_param, worsening_param, engineering_statement, PC / SF 模型欄位）
  - **CLD（既有）**:
    - `useCldNodes(id)` → CLD 節點列表（isBreakpoint 等）
    - `useCldEdges(id)` → CLD 邊列表
  - **Context（既有）**:
    - `useBrief(id)` → Brief mission / updatedAt
    - `useConstraints(id)` → 約束列表
    - `useKpis(id)` → KPI 列表
    - `useTrackAssumptions(id)` → 假設追蹤列表
  - **Supabase direct（既有）**:
    - `assumptions` 表 insert / delete / select（假設同步）
    - `contradictions` 表 insert / update / delete / select（矛盾同步）
    - `projects` 表 update `entry_level` 欄位
    - `function_models` 表 insert / select（FA 結果持久化）
- **state**:
  - `entryLevel: 'A' | 'B' | 'C' | null` — 入口分級（from DB）
  - `showEntryModal: boolean` — EntryGradingModal 是否顯示
  - Level A: `currentStep: 0 | 1 | 2 | 3 | 4` — 當前 stepper 步驟
  - Level B: `activeTab: TabKey` — 當前 Tab（'socratic' | 'contradictions' | 'cld'），由 URL hash 初始化
  - `saveStatus: 'idle' | 'saving' | 'saved'` — 儲存狀態指示
  - `faExpanded: boolean` — Level B FA 側面板展開狀態
- **derived_data**:
  - `constraintStrings` — 約束格式化字串（傳入 AI API）
  - `kpiStrings` — KPI 格式化字串（傳入 AI API）
  - `contradictionStrings` — 矛盾格式化字串（傳入 CLD Tab）
  - `assumptionStrings` — 假設格式化字串（傳入 CLD Tab）
  - `socraticQaStrings` — 已回答問答格式化字串（傳入 AI formalize）
  - `isBriefStale: boolean` — Brief 更新時間是否晚於最新問題建立時間
  - `causalLoop: CausalLoop | null` — 從 cldNodes + cldEdges 組合而成
  - `gate12Items: GateCheckItem[]` — Gate 1.2 條件計算結果（依 Level 調整）
  - `phaseGate1Items: GateCheckItem[]` — Phase Gate 1 條件計算結果
  - `fiveWhyCompleted: boolean` — Level A Step 0 完成判定
  - `faCompleted: boolean` — Level A Step 1 完成判定
  - `stepStatuses: StepStatus[]` — Level A 各步驟狀態（pending / current / completed / skipped）
- **error_cases**:
  - Entry Grading API 失敗 → 預設為 Level B（最安全 fallback），顯示 toast 提示
  - 5 Why / KT / FA 生成失敗 → toast.error 顯示錯誤訊息，保留當前狀態，提供重試按鈕
  - 資料載入失敗 → Skeleton 持續顯示（依 TanStack Query 重試策略）
  - AI formalize 失敗 → toast.warning 提示手動分類
  - 假設 / 矛盾同步寫入失敗 → console.error 記錄（不阻斷主流程）
  - 問題刪除失敗 → 由 deleteQuestionMut 的 onError 處理

---

## [ACCEPTANCE CRITERIA]

### Entry Grading & Conditional Rendering（新增）

- [ ] 首次進入 Explore 時（entry_level 為 null），自動彈出 EntryGradingModal
- [ ] Modal 正確呼叫 `POST /analyst/entry-grading` 並將結果存入 `projects.entry_level`
- [ ] Entry Grading API 失敗時 fallback 為 Level B，顯示 toast 提示
- [ ] Level A → 渲染 5-step stepper 模式
- [ ] Level B → 渲染原 3-tab 佈局（與 v1.0 完全一致）
- [ ] Level C → 顯示提示訊息 + 導向 Create SF-only 按鈕
- [ ] header 提供 Level 切換按鈕，點擊可在 A/B 間切換
- [ ] 再次進入 Explore 時不重複彈出 Modal（讀取已存 entry_level）

### Level A Stepper（新增）

- [ ] stepper 正確顯示 5 步驟，各步驟有完成/當前/待完成/已跳過狀態
- [ ] Step 0: 5Why AI 生成正確回傳並渲染 chain 卡片
- [ ] Step 0: KT AI 生成正確回傳並渲染 4×2 矩陣
- [ ] Step 0: 根因摘要在 5Why + KT 完成後自動產出
- [ ] Step 1: FA AI 生成正確回傳組件交互圖（節點 + 邊）
- [ ] Step 1: SF 診斷面板正確標記 S1-Field-S2 狀態
- [ ] 跳過 FA 時顯示確認提示
- [ ] Gate 1.2 對 Level A 額外檢查 5Why + FA 條件（已跳過視為通過）

### Level B 原有功能（不變）

- [ ] 頁面載入時平行請求所有資料源，Loading 顯示 Skeleton
- [ ] URL hash 正確初始化 activeTab（`#socratic` / `#contradictions` / `#cld`）
- [ ] Tab 切換時 URL hash 同步更新且不觸發頁面跳轉
- [ ] 蘇格拉底問答支援 7 個類別，回答 >= 5 字元計入已回答
- [ ] Tab Badge 即時反映：已回答數 / 總問題數、TC + PC + SF 數量、斷路點數量
- [ ] 問答中標記為假設 → 自動寫入 assumptions 表（含重複檢查）
- [ ] 問答中標記為矛盾 → 自動寫入 contradictions 表 + 觸發 AI formalize（counter 類排除）
- [ ] 取消假設 / 矛盾標記 → 自動從對應表刪除
- [ ] 刪除問題 → 同步刪除關聯 assumption 與 contradiction + 顯示 undo toast
- [ ] Undo 復原 → 使用原始 ID 重新插入問題及關聯記錄
- [ ] AI formalize 失敗時顯示 toast 警告，矛盾記錄保留待手動分類
- [ ] Brief 陳舊偵測：Brief 更新時間 > 最新問題建立時間時顯示警告
- [ ] ContradictionTab 顯示矛盾列表含類型 Badge 與嚴重度
- [ ] CldTab 支援節點 / 邊操作與斷路點標記
- [ ] KnowledgeRefsPanel 顯示頁面知識參考（目前為 mock 資料）
- [ ] FA 側面板可展開/收合，操作不影響 Gate 條件

### Gate 條件

- [ ] Gate 1.2 共用條件：>= 10 回答、矛盾已處理、7 類皆有回答
- [ ] Gate 1.2 Level A 額外條件：5Why >= 3 層 + FA >= 1 SF 三角（已跳過視為通過）
- [ ] Phase Gate 1 條件：>= 1 CLD、>= 3 斷路點、所有矛盾已分類
- [ ] 零矛盾專案可合法通過 Gate（矛盾相關條件視為通過）
- [ ] 所有 Gate 通過後可導航至 `/projects/:id/track`

### RWD

- [ ] Level A stepper：Desktop 水平 / Tablet 簡化 / Mobile 垂直或下拉
- [ ] Level B tabs：Mobile 下 Tab Badge 隱藏、Tab 文字縮小
