# Page-Level Prompt: Explore 探索 / Socratic 問答

> Phase 1 Define 的深化探索頁，透過蘇格拉底式問答挖掘問題空間，識別技術 / 物理 / 物場矛盾，並建立因果迴路圖視覺化變量關係。

---

## [PAGE META]

- **page_name**: Explore
- **route_path**: `/projects/:id/explore`
- **page_type**: workspace
- **primary_goal**: 引導設計工程師透過 7 類蘇格拉底問答深入探索問題空間，識別並分類矛盾（TC / PC / SF），建立因果迴路圖標記斷路點，完成 Gate 1.2 與 Phase Gate 1 退出條件
- **secondary_goal**: 自動將問答中標記的假設同步至 Assumption Ledger，將標記的矛盾自動 formalize 為結構化矛盾記錄，並提供知識參考面板輔助決策
- **target_users**:
  - 主要：設計工程師（問題分析與矛盾識別）
  - 次要：團隊成員（審閱矛盾分類與因果圖）
- **entry_point**: 從 TaskDefinition 頁 Gate 1.1 通過後自動導航 / ProjectDashboard NavCard 點擊 "Explore" / URL 直接存取
- **expected_time_on_page**: 20 - 60 分鐘（首次完整探索）；5 - 15 分鐘（追加問答或修訂矛盾）

---

## [STRUCTURE: SECTIONS]

1. **page_header**
   - section_type: header
   - section_purpose: 返回按鈕、儲存狀態指示、頁面標題與步驟說明

2. **tab_navigation**
   - section_type: tabs
   - section_purpose: 3 個 Tab 切換（蘇格拉底問答 / 矛盾識別 / 因果迴路圖），各 Tab 含統計 Badge

3. **socratic_tab**
   - section_type: questionnaire
   - section_purpose: 7 類蘇格拉底問答列表，支援回答、假設標記、矛盾標記與 AI 輔助

4. **contradiction_tab**
   - section_type: list_workspace
   - section_purpose: 矛盾列表，支援 TC / PC / SF 分類、嚴重度標記、AI 自動 formalize

5. **cld_tab**
   - section_type: diagram
   - section_purpose: 因果迴路圖編輯器，含節點 / 邊操作與斷路點標記

6. **knowledge_panel**
   - section_type: reference_panel
   - section_purpose: KnowledgeRefsPanel 顯示頁面相關的知識參考資料

7. **gate_section**
   - section_type: gate_check
   - section_purpose: ExploreGates 元件包含 Gate 1.2 與 Phase Gate 1 兩組退出條件

---

## [SECTION COMPONENT SPEC]

### Section: page_header

- **layout**: flex row，左側返回按鈕，右側儲存狀態；下方標題行含 phase 色條（藍色）+ 標題 + HelpTooltip + 步驟描述
- **elements**:
  - back_button: Button(ghost) / required / `<ArrowLeft>` 圖標 + "返回 Dashboard"，導航至 `/projects/:id`
  - save_indicator: Span / conditional / saveStatus 為 saving 時顯示 "Saving..."；saved 時顯示 `<Check>` + "Saved"
  - phase_bar: Div / required / `h-8 w-1 rounded-full bg-blue-500` 相位色條
  - title: H1 / required / "Explore — 問題探索" + HelpTooltip
  - subtitle: P / required / "Step 1.2–1.3 · 蘇格拉底問答 → 矛盾識別 → 因果迴路圖"
- **states**:
  - loading: 整頁替換為 Skeleton（標題 + tabs 骨架 + 3 組 h-32 內容骨架）
  - default: 完整 header 渲染
- **copy_constraints**: 標題固定 "Explore — 問題探索"；步驟編號 "Step 1.2–1.3"

### Section: tab_navigation

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

### Section: socratic_tab

- **layout**: SocraticTab 元件，TabsContent value="socratic"，mt-5 間距
- **elements**:
  - socratic_tab: SocraticTab / required / 傳入 questions、onUpdateQuestions、onDeleteQuestion、isBriefStale、briefUpdatedAt、projectId、mission、constraints
- **states**:
  - default: 7 類問題按類別分組顯示（boundary, function, resource, time, environment, human, counter）
  - answering: 輸入回答中
  - tagging: 標記為假設或矛盾 → 觸發同步寫入 assumptions / contradictions 表
  - brief_stale: 當 Brief 更新時間晚於最新問題建立時間時顯示陳舊警告
  - deleting: 刪除問題後顯示 undo toast（5 秒內可復原）
- **copy_constraints**: 問題文字由 AI 或預設產生；回答需 >= 5 字元才計入已回答

### Section: contradiction_tab

- **layout**: ContradictionTab 元件，TabsContent value="contradictions"，mt-5 間距
- **elements**:
  - contradiction_tab: ContradictionTab / required / 傳入 contradictions、onUpdateContradictions、hasAnswers、projectId、mission、constraints、kpis、socraticAnswers
- **states**:
  - default: 矛盾列表，每項顯示類型 Badge（TC / PC / SF）、嚴重度、描述
  - empty: 無矛盾時提示使用者從問答中標記
  - formalizing: AI 自動 formalize 中（improving_param, worsening_param, engineering_statement, SF 模型等）
  - formalize_failed: 顯示 toast 警告 "AI 暫時無法自動分類此矛盾，請至矛盾識別手動指定類型"
- **copy_constraints**: 矛盾工程描述由 AI formalize 產生

### Section: cld_tab

- **layout**: CldTab 元件，TabsContent value="cld"，mt-5 間距
- **elements**:
  - cld_tab: CldTab / required / 傳入 causalLoop、onUpdateCausalLoop、projectId、contradictions（字串陣列）、assumptions（字串陣列）、mission、constraints、kpis、socraticAnswers
- **states**:
  - default: 因果迴路圖顯示節點與邊
  - empty: 無節點時顯示空白畫布
  - editing: 新增 / 移動節點、建立邊連結
  - breakpoint_marking: 標記斷路點（節點 isBreakpoint = true）
- **copy_constraints**: 無特殊限制

### Section: knowledge_panel

- **layout**: KnowledgeRefsPanel 元件
- **elements**:
  - panel: KnowledgeRefsPanel / required / 傳入 `mockPageKnowledgeRefs.explore` 參考資料陣列（TODO: Sprint 5+ 替換為 useKnowledgeRefs hook）
- **states**:
  - default: 顯示參考資料列表
  - empty: 無參考資料時不渲染
- **copy_constraints**: 無特殊限制

### Section: gate_section

- **layout**: ExploreGates 元件，包含兩組 Gate 檢查
- **elements**:
  - explore_gates: ExploreGates / required / 傳入 gate12Items、phaseGate1Items、onNavigateNext
- **Gate 1.2 條件**:
  - 累計 >= 10 個回答（含 >= 10 假設已辨識）
  - 矛盾已處理（>= 1 個已確認，或確認無矛盾）
  - 7 類問題皆有回答
- **Phase Gate 1 條件**:
  - 至少 1 個因果迴路圖已建立
  - 至少 3 個斷路點已標記
  - 所有矛盾已分類為 TC / PC / SF（或無矛盾）
- **states**:
  - incomplete: 部分條件未通過，導航按鈕 disabled
  - complete: 所有條件通過，點擊導航至 `/projects/:id/track`
- **copy_constraints**: Gate 條件文案固定如上

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

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
6. **Gate 通過** → 點擊導航按鈕 → 導航至 `/projects/:id/track`

### RWD 行為差異

- **Desktop**: `page-shell-kb` 佈局（含知識面板空間）；Tab Badge 完整顯示
- **Tablet**: Tab Badge 完整顯示；知識面板可能摺疊
- **Mobile**: Tab Badge 隱藏（`hidden sm:inline-flex`）；Tab 觸發器文字縮小 (`text-xs`)；知識面板堆疊於底部

---

## [DATA & API]

- **uses_api**: true
- **endpoints**:
  - `useSocraticQuestions(id)` → 蘇格拉底問題列表（category, text, answer, taggedAsAssumption, taggedAsContradiction, aiSuggestedTag）
  - `useUpdateSocraticQuestion()` → 更新單一問題
  - `useCreateSocraticQuestion()` → 新增問題
  - `useDeleteSocraticQuestion()` → 刪除問題
  - `useExploreContradictions(id)` → 矛盾列表（type, severity, status, engineeringStatement, source_question_id, SF 模型欄位等）
  - `useCldNodes(id)` → CLD 節點列表（isBreakpoint 等）
  - `useCldEdges(id)` → CLD 邊列表
  - `useBrief(id)` → Brief mission / updatedAt
  - `useConstraints(id)` → 約束列表
  - `useKpis(id)` → KPI 列表
  - `useTrackAssumptions(id)` → 假設追蹤列表
  - `contradictionFormalize(payload)` → AI 矛盾 formalize API（回傳 type, improving_param, worsening_param, engineering_statement, PC / SF 模型欄位）
  - Supabase direct: `assumptions` 表 insert / delete / select（假設同步）
  - Supabase direct: `contradictions` 表 insert / update / delete / select（矛盾同步）
- **state**:
  - `activeTab: TabKey` — 當前 Tab（'socratic' | 'contradictions' | 'cld'），由 URL hash 初始化
  - `saveStatus: 'idle' | 'saving' | 'saved'` — 儲存狀態指示
- **derived_data**:
  - `constraintStrings` — 約束格式化字串（傳入 AI API）
  - `kpiStrings` — KPI 格式化字串（傳入 AI API）
  - `contradictionStrings` — 矛盾格式化字串（傳入 CLD Tab）
  - `assumptionStrings` — 假設格式化字串（傳入 CLD Tab）
  - `socraticQaStrings` — 已回答問答格式化字串（傳入 AI formalize）
  - `isBriefStale: boolean` — Brief 更新時間是否晚於最新問題建立時間
  - `causalLoop: CausalLoop | null` — 從 cldNodes + cldEdges 組合而成
  - `gate12Items: GateCheckItem[]` — Gate 1.2 條件計算結果
  - `phaseGate1Items: GateCheckItem[]` — Phase Gate 1 條件計算結果
- **error_cases**:
  - 資料載入失敗 → Skeleton 持續顯示（依 TanStack Query 重試策略）
  - AI formalize 失敗 → toast.warning 提示手動分類
  - 假設 / 矛盾同步寫入失敗 → console.error 記錄（不阻斷主流程）
  - 問題刪除失敗 → 由 deleteQuestionMut 的 onError 處理

---

## [ACCEPTANCE CRITERIA]

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
- [ ] Gate 1.2 條件：>= 10 回答、矛盾已處理、7 類皆有回答
- [ ] Phase Gate 1 條件：>= 1 CLD、>= 3 斷路點、所有矛盾已分類
- [ ] 零矛盾專案可合法通過 Gate（矛盾相關條件視為通過）
- [ ] 所有 Gate 通過後可導航至 `/projects/:id/track`
- [ ] RWD：Mobile 下 Tab Badge 隱藏、Tab 文字縮小
