---
id: P08
file_id: "08"
page_name: Create
route_path: /projects/:id/create
page_type: wizard
phase: 2
ia_group: phase2-diverge
gate: X2
protected: true
dev_only: false
source_component: src/pages/Create.tsx
spec_version: 10.0
ia_version: 1.2
status: stable
last_updated: 2026-04-27
api_resources: [triz_solutions, subsystems, alternatives, contradictions, brief, constraints, kpis, evidence, oz_ot, sim_matrix, complexity_check]
modules: [analyst, triz, evidence, spatial]
depends_on: [P07]
absorbed_specs: ["02-design/specs/ux/E5x--create-ux-spec.md"]
optional_sections: [wireframe, design_principles, changelog]
---

# Page-Level Prompt: Create 創建 / 方案生成

> Phase 2 最複雜頁面 — 方案創造精靈，整合 TRIZ 三路徑（含 L1 跨域去錨定）、子系統定義、決策中心與統一評估，完成概念方案收斂。
> **整合來源**：本檔合併了原 `02-design/specs/ux/E5x--create-ux-spec.md` 的 wireframe + 互動定義 + 設計原則（v3.0）。

---

## [CHANGELOG]

> 設計演化記錄（原 UX spec 版本歷程）。

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v10.0 | 2026-04-27 | v3.0 對標：移除 AA/SCAMPER strikethrough 噪音；步驟從 Step 1-5 重編（對應 X2/X3/X4/X5-P1/X5-P2）；API 表僅保留活躍 endpoints |
| v9.0 | 2026-04-27 | ADR-008：Entry Grading Modal、Conditional Stepper、OZ-OT Panel、CCI Badge、Evidence Coverage Gauge |
| v8.1 | 2026-04-13 | Tab ① ConvergenceDashboard 移除（Phase A 退役，per-card critic badge 取代） |
| v8 | 2026-04-09 | Phase A 退役：Tab ① 簡化為一鍵直出分層 drill-down |
| v7 | 2026-04-09 | Tab ① 重寫：LayeredTrizSolution 分層診斷（L1/L2/L3 垂直堆疊 + differential_analysis + critic badge） |
| v6 | 2026-04-08 | Tab ② Spatial Discovery Validator（Package Map + inline override + What-if Overlay） |
| v5 | 2026-03-26 | TRIZ 三路徑 + 決策中心匯流（原雙軌 Anti-Anchor/TRIZ 合併為單一 TRIZ 路徑） |

---

## [WIREFRAME]

```
┌──────────────────────────────────────────────────────────────────┐
│  ① 核心設計使命                                                    │
│  Mission · Constraints · KPIs · 已驗證假設 · 高風險數               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ② TRIZ 分析（含 L1 跨域去錨定）                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  🎯 TRIZ 解矛盾（L1 含跨域去錨定）→ 子系統                      │ │
│  │  從矛盾出發，系統化產出候選方案                                    │ │
│  │  L1 instantiation 內建去錨定步驟                                  │ │
│  │  內部 tab：① TRIZ ② 子系統                                      │ │
│  │  [點擊展開操作]                                                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│                    ▼ 候選池匯流 ▼                                   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  ③ 候選方案決策中心                                            │ │
│  │  所有候選攤平 · RD adopt/skip · CCI 標籤 · 橫向比較            │ │
│  │  ┌─────────┐ ┌──────────────┐ ┌─────────┐ ┌─────────┐      │ │
│  │  │ 去錨定  │ │ TRIZ-Layered │ │ TRIZ-L1 │ │ 正向    │      │ │
│  │  │ 路線1  │ │ ▢ L1 ▢ L2 ▢ L3│ │ single  │ │ single  │      │ │
│  │  │ [adopt] │ │ [採納推薦]    │ │ [adopt] │ │ [skip]  │      │ │
│  │  └─────────┘ └──────────────┘ └─────────┘ └─────────┘      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ④ 統一評估                                                        │
│  [ MUST 快篩 (M1-M6) ]  →  [ Pre-CAD 審查 (5D) ]                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## [DESIGN PRINCIPLES]

| 原則 | 說明 |
|:-----|:-----|
| 分層而非選題 (v7) | Tab ① TRIZ 輸出是 L1/L2/L3 分層診斷報告，不是並列候選池 |
| 垂直堆疊呈現 drill-down | 同矛盾三層以垂直堆疊呈現，ARIZ 深挖路徑視覺化為上下關係 |
| L3 永遠呈現 | 即使 L1/L2 已採納，L3 結構旁路永遠顯示 |
| 路徑色彩 | TRIZ 三層 = blue（🎯冷色）；去錨定標記 = amber（⚡暖色輔助標識） |
| Discovery 不限制創意 | Spatial validator 為 descriptive，never blocking |
| Confidence 必須可見 | 每個 spatial 數字帶 confidence badge（深綠→紅，信任度遞減） |
| Trace 每一個數字 | reference_source hover 顯示完整 trace |

### Spatial Confidence 配色

| confidence | reference_source | Badge 配色 | 語意 |
|:-----------|:-----------------|:-----------|:-----|
| rd_confirmed | `rd_override:<key>` | 深綠白字 `#14532d` | RD 手動 override |
| library | `learned:<key>` | 淺綠黑字 `#bbf7d0` | 跨專案 learned |
| estimate | `web:<query>` | 橘黃黑字 `#fde68a` | web lookup |
| llm_estimate | `llm_estimate` | 紅黑字 `#fecaca` | LLM fallback，**RD 應 override** |

---

## [PAGE META]
- **primary_goal**: 引導使用者透過 TRIZ 三路徑（含 L1 跨域去錨定）產生候選方案，經決策中心橫向比較後以 MUST 快篩淘汰不可行方案
- **secondary_goal**: 支援 TRIZ 分層診斷、子系統分解、跨方案收斂分析，為 Pre-CAD 審查做準備
- **target_users**: RD 工程師、系統架構師
- **entry_point**: Track 頁面 Gate X1 通過後導航，或 Dashboard 直接進入
- **expected_time_on_page**: 30 ~ 120 分鐘（多次進出）

---

## [STRUCTURE: SECTIONS]

> 5 步驟 wizard，對應系統步驟 X2→X3→X4→X5(P1)→X5(P2)。

1. **Header**
   - section_type: navigation + status
   - section_purpose: 返回 Dashboard 按鈕、頁面標題、儲存狀態指示器
2. **MissionContext**
   - section_type: context-panel
   - section_purpose: 顯示問題陳述、矛盾摘要、假設驗證進度，提供任務背景
3. **CreateStepper**
   - section_type: step-navigation
   - section_purpose: 5 步驟導航，分為三個區域（TRIZ 路徑 / 決策中心 / 統一評估）
4. **Step 1: TRIZ 解矛盾（含 L1 跨域去錨定）** → X2
   - section_type: analysis + generation
   - section_purpose: 分層 drill-down 診斷（L1 現象/L2 根因/L3 結構），方向求解與跨矛盾整併
5. **Step 2: 子系統定義** → X3
   - section_type: modeling
   - section_purpose: 識別受矛盾影響的子系統（System → Module → Component），定義介面合約
6. **Step 3: 候選方案決策中心** → X4
   - section_type: comparison + decision
   - section_purpose: 攤平所有方案，橫向比較來源、機制、假設、驗證需求與信心等級
7. **Step 4: MUST 快篩** → X5-P1
   - section_type: evaluation
   - section_purpose: 以必要條件（M1-M6）快速淘汰不可行方案
8. **Step 5: Pre-CAD 審查** → X5-P2
   - section_type: evaluation
   - section_purpose: 五維審查：MUST/解耦/可驗證性/失效機制/MVP CAD
9. **KnowledgeRefsPanel**
    - section_type: reference
    - section_purpose: 依當前步驟顯示對應的知識參考連結

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center justify-between
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | BackButton | `<Button variant="ghost">` | required | ArrowLeft icon，onClick 導航至 `/projects/:id` |
  | Title | `<h1>` | required | "Create — 方案生成"，text-2xl font-bold |
  | SaveStatus | `<span>` | optional | idle/saving/saved 三態顯示 |
- **states**: saveStatus 三態切換
- **copy_constraints**: 標題固定

### Section: MissionContext
- **layout**: MissionContext 元件，可收合面板
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ProblemStatement | text | required | 專案任務描述（from useBrief） |
  | ContradictionList | list | required | 已識別矛盾摘要 |
  | AssumptionProgress | progress | required | 已驗證假設 / 總假設數、高風險假設數 |
  | Constraints | list | required | 專案約束條件（from useConstraints） |
  | KPIs | list | required | 關鍵績效指標（from useKpis） |
- **states**: 收合/展開
- **copy_constraints**: 使用繁體中文

### Section: CreateStepper
- **layout**: CreateStepper 元件，水平步驟條
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | Step_1 | step | required | "TRIZ 解矛盾（含 L1 跨域去錨定）"，zone=triz（blue） |
  | Step_2 | step | required | "子系統定義"，zone=triz（blue） |
  | Step_3 | step | required | "候選方案決策中心"，zone=hub（violet） |
  | Step_4 | step | required | "MUST 快篩"，zone=eval（green） |
  | Step_5 | step | required | "Pre-CAD 審查"，zone=eval（green） |
- **states**: 各步驟顯示完成狀態（pending/in-progress/done），當前步驟高亮
- **copy_constraints**: Zone badge 使用繁體中文（TRIZ 路徑 / 決策中心 / 統一評估）

### Section: Step 1 — TRIZ 解矛盾（含 L1 跨域去錨定）〔X2〕
- **layout**: OZ-OT 前置 accordion → 矛盾清單 + 分層診斷卡片（L1 含跨域去錨定）+ 方向分析結果 + SIM 矩陣 + 整併面板
- **sub-sections**:

  #### 1a. OZ-OT 前置分析（ADR-008 新增）
  - **layout**: Accordion section，展開後顯示 OZ-OT 分析面板，位於矛盾清單上方
  - **觸發條件**: 頁面載入時若有 ≥1 formalized TC，自動展開；無 TC 則摺疊隱藏
  - **elements**:
    | Element | Type | Required | Description |
    |:--------|:-----|:---------|:------------|
    | OzOtPanel | accordion-section | conditional | OZ-OT 分析面板：顯示每個 TC 的 Operating Zone (OZ)、Operating Time (OT)、鎖定的 Px 變量 |
    | RunOzOtButton | AiButton | optional | 觸發 `POST /analyst/oz-ot-analysis`，AI 基於 TC + FA context 產出 OZ-OT 分析 |
    | OzOtResultCards | card-list | conditional | 每個 TC 的 OZ-OT 結果卡片，顯示 zone / time / px_variable |
  - **states**:
    - hidden: 無 formalized TC
    - collapsed: 有 TC 但使用者摺疊
    - analyzing: AI OZ-OT 分析中
    - completed: 顯示各 TC 的 OZ/OT/Px 結果
  - **copy_constraints**: OZ/OT 術語使用英文，描述使用繁體中文

  #### 1b. 矛盾求解（既有）
  - **elements**:
    | Element | Type | Required | Description |
    |:--------|:-----|:---------|:------------|
    | ContradictionList | list | required | 從 useContradictions 載入的矛盾清單，按 TC > PC > SF 排序。若有 OZ-OT 結果，每行顯示 Px Badge |
    | QuickModeToggle | toggle | optional | trizQuickMode 開關 |
    | SolveAllButton | AiButton | required | 觸發 `handleDirectedSolveAll`，逐一解題所有頂層 TC（自動注入 OZ-OT context） |
    | SolveSingleButton | Button | optional | 每行矛盾旁的單獨求解按鈕 |
    | LayeredSolutionCard | card | optional | 分層診斷結果卡片（L1/L2/L3），支援 adoption mode 切換 |
    | DirectionResultCard | card | optional | 方向分析結果，顯示 top1 推薦 |
    | ConsolidationPanel | panel | optional | 跨矛盾整併結果（compatible/resolved_with_swap/conflict） |

  #### 1c. SIM 矩陣（ADR-008 新增，≥2 TC 條件觸發）
  - **layout**: 條件渲染區塊，位於 ConsolidationPanel 下方
  - **觸發條件**: 當 project 有 ≥2 formalized TC 且至少 1 個已求解
  - **elements**:
    | Element | Type | Required | Description |
    |:--------|:-----|:---------|:------------|
    | SimMatrixView | matrix | conditional | +1/0/-1 交互矩陣，行列為各 TC 的候選解法 |
    | RunSimButton | AiButton | conditional | 觸發 `POST /triz/sim-matrix`，AI 評估多 TC 間解法交互 |
    | ConflictAlert | alert | conditional | -1 交互項提示：「偵測到解法衝突，建議回流處理」 |
  - **states**:
    - hidden: < 2 TC 或無已求解 TC
    - evaluating: SIM 評估中
    - completed: 顯示矩陣 + 衝突標記
  - **copy_constraints**: 矩陣使用 +1/0/-1 數值顯示，hover 顯示評估理由

- **states**（Step 1 整體）:
  - pending: 矛盾列出但未求解
  - oz_ot_analyzing: OZ-OT 分析中
  - solving: 單一矛盾求解中（solvingIds），顯示 spinner
  - done: 顯示 LayeredSolutionCard / DirectionResultCard
  - failed: 顯示錯誤訊息與重試按鈕
  - consolidating: 整併運算中
  - sim_evaluating: SIM 矩陣評估中
- **copy_constraints**: 嚴重度標籤（fatal/major/minor）使用英文 Badge

### Section: Step 2 — 子系統定義〔X3〕
- **layout**: SubsystemHierarchyView（diagram/list 切換）+ 手動新增表單 + PackageMapPanel
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ViewToggle | SegmentedControl | required | diagram/list 視圖切換（LayoutGrid/List icon） |
  | SubsystemHierarchyView | tree-view | required | System → Module → Component 層級顯示 |
  | SuggestButton | AiButton | optional | AI 建議子系統分解（useSubsystemSuggestion） |
  | AddSubsystemForm | form | optional | 手動新增子系統（名稱、原因、關聯矛盾、介面、層級、父元件） |
  | InterfaceContractsPanel | panel | optional | 顯示子系統間的 6 維介面合約 |
  | PackageMapPanel | panel | optional | 空間佈局圖（PackageMap），AI 建議生成 |
  | SpatialOverlayDialog | dialog | optional | 空間覆蓋分析對話框 |
  | SpatialOverrideDialog | dialog | optional | RD 手動覆寫空間估計 |
  | PromoteToLearnedDialog | dialog | optional | 將空間估計提升為 learned component |
- **states**:
  - empty: 無子系統，顯示新增提示
  - diagram: 樹狀圖模式
  - list: 清單模式
  - editing: 編輯表單展開
  - suggesting: AI 建議產生中
- **copy_constraints**: 層級名稱使用英文（system/module/component），說明使用繁體中文

### Section: Step 3 — 候選方案決策中心〔X4〕
- **layout**: Evidence Coverage Gauge（頂部）→ 方案網格（含 CCI Badge）→ 比較面板 + ConvergenceDashboard + HumanReviewPanel
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | EvidenceCoverageGauge | gauge | conditional | （ADR-008 新增）頂部橫幅，顯示 Evidence Registry 覆蓋率（VERIFIED + APPROXIMATE 佔比），閾值 ≥ 40% 為綠色，< 40% 為橘色警告。觸發 `GET /evidence/coverage` |
  | AlternativeGrid | card-grid | required | 所有候選方案卡片，顯示來源、機制、假設、信心等級 |
  | CciBadge | badge | conditional | （ADR-008 新增）每張方案卡片右上角，顯示 CCI 分數與判定：≤0.3 綠色 "Evolution" / 0.3-0.6 橘色 "Weak Evolution" / >0.6 紅色 "Patch"。觸發 `POST /triz/complexity-check` |
  | CompareCheckbox | Checkbox | optional | 勾選進行橫向比較 |
  | DifferentialAnalysis | panel | optional | 差異分析面板 |
  | ConvergenceDashboard | dashboard | required | 收斂狀態儀表板，顯示 Fatal/Major/Minor 解決進度 |
  | ConvergenceGraph | chart | optional | 收斂趨勢圖 |
  | CompatibilityMatrix | matrix | optional | 方案相容性矩陣 |
  | MultiSolutionAdoptionPanel | panel | optional | 多方案採用面板，含反模式檢查 |
  | HumanReviewPanel | panel | optional | 人工審查面板，確認採用決策 |
  | ArchitectureHaltOverlay | overlay | optional | 架構衝突阻擋覆蓋層 |
  | CrossLtsWarnings | alert | optional | 跨 LTS 冗餘警告 |
- **CCI 互動**: 方案首次進入 Decision Hub 時，自動為每個已 adopted 的方案觸發 `POST /triz/complexity-check`。CCI Badge 為 "Patch" 時，hover 顯示 tooltip：「此方案為複雜度堆疊（CCI={score}），建議記錄技術債」
- **Evidence 互動**: Evidence Coverage Gauge 在 < 40% 時顯示建議：「建議回到相關步驟補充數值聲明的外部驗證」
- **states**:
  - empty: 無候選方案
  - comparing: 選中多個方案進行比較
  - converging: 收斂分析執行中
  - halted: 架構衝突偵測到，顯示阻擋覆蓋層
  - cci_loading: CCI 計算中（每張卡片獨立 loading）
  - evidence_low: Evidence 覆蓋率 < 40%，Gauge 顯示橘色
- **copy_constraints**: 方案來源標籤使用英文（TRIZ / TRIZ-L1-去錨定）；CCI 判定標籤使用英文（Evolution/Weak Evolution/Patch）

### Section: Step 4 — MUST 快篩〔X5-P1〕
- **layout**: 方案列表 + MUST 條件矩陣
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | AlternativeList | list | required | 候選方案清單 |
  | MustMatrix | grid | required | M1-M6 必要條件評估矩陣（pass/fail/pending） |
  | AiEvalButton | AiButton | optional | 觸發 `mustEvaluate` AI 評估 |
  | FilteredResult | summary | optional | 篩選結果摘要（通過/淘汰數量） |
- **states**:
  - pending: 未評估
  - evaluating: AI 評估中
  - evaluated: 顯示通過/不通過結果
- **copy_constraints**: MUST 條件使用專案自定義（from must_criteria_config）或預設值

### Section: Step 5 — Pre-CAD 審查〔X5-P2〕
- **layout**: 雷達圖 + 五維評分
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | RadarChart | chart | required | 使用 recharts RadarChart，最多 4 條方案重疊比較 |
  | DimensionScores | form | required | PRECAD_DIMENSIONS 五維評分（空間約束/解耦/可驗證性/風險/最小 CAD） |
  | ValidationPassport | panel | optional | 驗證護照（from `validationPassportGenerate`） |
- **states**: 評分中/已完成
- **copy_constraints**: 五維標籤使用繁體中文

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. 使用者進入頁面，預設在 Step 1（TRIZ 解矛盾，含 L1 跨域去錨定），MissionContext 顯示任務背景
2. Step 1（X2）:
   - 1a. OZ-OT 前置分析：有 TC 時自動展開 → 點擊 RunOzOtButton → AI 產出 OZ/OT/Px → 結果注入後續求解 context
   - 1b. 查看矛盾清單（含 Px Badge）→ 點擊「全部求解」或單獨求解 → 分層診斷/方向分析結果 → 自動整併
   - 1c. SIM 矩陣：≥2 TC 已求解時自動顯示 → 點擊 RunSimButton → +1/0/-1 矩陣 → -1 衝突項提示回流
3. Step 2（X3）: AI 建議子系統分解 → 查看/編輯子系統樹 → 定義介面合約 → 查看 PackageMap
4. Step 3（X4）: 決策中心攤平所有方案 → Evidence Coverage Gauge 顯示覆蓋率 → 每張方案卡顯示 CCI Badge → 橫向比較 → 收斂分析 → 人工確認
5. Step 4（X5-P1）: MUST 快篩淘汰不可行方案
6. Step 5（X5-P2）: Pre-CAD 五維審查 → 雷達圖比較
7. 所有步驟完成後 → Gate X2 通過 → 導航至 Pre-CAD Review 頁面

### RWD 行為差異
- **Desktop (≥1024px)**: Stepper 水平顯示所有步驟，方案網格 3 欄，雷達圖完整展示
- **Tablet (768-1023px)**: Stepper 可能簡化為 shortLabel，方案網格 2 欄
- **Mobile (<768px)**: Stepper 可能改為下拉選單或簡化導航，方案網格 1 欄，雷達圖縮小

---

## [DATA & API]
- **uses_api**: true
- **endpoints**:
  | Hook / Function | Method | Purpose |
  |:-----------------|:-------|:--------|
  | `useContradictions(projectId)` | GET | 取得矛盾清單 |
  | `useTrizSolutions(projectId)` | GET | 取得 TRIZ 解法 |
  | `useCreateTrizSolution()` | POST | 建立 TRIZ 解法 |
  | `useUpdateTrizSolution()` | PATCH | 更新 TRIZ 解法 |
  | `useLayeredTrizSolutions(projectId)` | GET | 取得分層 TRIZ 解法（L1 含跨域去錨定具體化結果） |
  | `useDirectedTrizSolutions(projectId)` | GET | 取得方向分析結果 |
  | `useTrizConsolidationResult(projectId)` | GET | 取得整併結果 |
  | `useSubsystems(projectId)` | GET | 取得子系統 |
  | `useCreateSubsystem()` | POST | 建立子系統 |
  | `useUpdateSubsystem()` | PATCH | 更新子系統 |
  | `useDeleteSubsystem()` | DELETE | 刪除子系統 |
  | `useSubsystemSuggestion(projectId)` | POST | AI 建議子系統分解 |
  | `useAlternatives(projectId)` | GET | 取得候選方案 |
  | `useCreateAlternative()` | POST | 建立方案 |
  | `useUpdateAlternative()` | PATCH | 更新方案 |
  | `useDeleteAlternative()` | DELETE | 刪除方案 |
  | `useConceptRoutes(projectId)` | GET | 取得概念路線 |
  | `useCompatibilityPairs(projectId)` | GET | 取得相容性配對 |
  | `useTrackAssumptions(projectId)` | GET | 取得假設（用於決策中心關聯） |
  | `useBrief(projectId)` | GET | 取得專案簡報 |
  | `useConstraints(projectId)` | GET | 取得約束條件 |
  | `useKpis(projectId)` | GET | 取得 KPI |
  | `useProject(projectId)` | GET | 取得專案設定（must_criteria_config） |
  | `useSocraticQuestions(projectId)` | GET | 取得蘇格拉底問答 |
  | `useConvergenceLoop(config)` | hook | 收斂迴圈運算 |
  | `trizSolveLayered(payload)` | POST | 分層 TRIZ 求解（L1 含跨域去錨定 prompt） |
  | `trizSolveDirected(payload)` | POST | 方向 TRIZ 求解 |
  | `trizConsolidate(payload)` | POST | 跨矛盾整併 |
  | `riskAnalyze(payload)` | POST | 風險分析 |
  | `mustEvaluate(payload)` | POST | MUST 快篩評估 |
  | `validationPassportGenerate(payload)` | POST | 驗證護照生成 |
  | `subsystemSpatialOverlay(payload)` | POST | 子系統空間覆蓋分析 |
  | `spatialComponentOverride(payload)` | POST | 空間元件覆寫 |
  | `spatialLearnedComponent(payload)` | POST | 提升為 learned component |
  | `useOzOtAnalysis(projectId)` | POST | （ADR-008）OZ-OT 分析，鎖定每個 TC 的 Px 變量 |
  | `useSimMatrix(projectId)` | POST | （ADR-008）多 TC SIM 交互矩陣（+1/0/-1） |
  | `useComplexityCheck(alternativeId)` | POST | （ADR-008）CCI 複雜度判定（0-1 連續指標） |
  | `useEvidenceCoverage(projectId)` | GET | （ADR-008）Evidence Registry 覆蓋率統計 |
- **error_cases**:
  - AI 生成失敗: toast.error 顯示錯誤訊息，保留當前狀態
  - 分層求解部分失敗: 個別矛盾標記 failed，其餘不受影響，提供重試按鈕
  - 整併失敗: toast.error，不影響已完成的個別求解結果
  - 子系統刪除衝突: 有下層元件時提示確認
  - 網路斷線: optimistic UI 回滾，toast.error 提示
  - OZ-OT 分析失敗: toast.error，不阻擋 TRIZ 求解（降級為無 Px context 求解）
  - SIM 矩陣評估失敗: toast.error，不影響個別矛盾求解結果
  - CCI 計算失敗: 方案卡 Badge 顯示 "N/A"，不阻擋採用決策
  - Evidence Coverage API 失敗: Gauge 不渲染，不阻擋 Gate

---

## [ACCEPTANCE CRITERIA]
- [ ] 頁面載入時顯示 Skeleton loading 狀態
- [ ] CreateStepper 正確顯示 5 個步驟，分三個區域色碼標示
- [ ] MissionContext 正確顯示專案任務、矛盾、假設、約束、KPI
- [ ] Step 1: 矛盾清單正確載入並按 TC > PC > SF 排序
- [ ] Step 1: 可全部求解或單獨求解，顯示 per-contradiction loading 狀態
- [ ] Step 1: LayeredSolutionCard 正確顯示 L1/L2/L3 分層結果
- [ ] Step 1: DirectionResultCard 顯示方向分析 top1 推薦
- [ ] Step 1: ConsolidationPanel 顯示跨矛盾整併結果
- [ ] Step 1: OZ-OT 面板在有 TC 時自動展開，AI 分析回傳 OZ/OT/Px 正確渲染（ADR-008）
- [ ] Step 1: OZ-OT 結果注入 TRIZ 求解 context（Px Badge 顯示在矛盾列表）（ADR-008）
- [ ] Step 1: SIM 矩陣在 ≥2 TC 已求解時條件渲染，顯示 +1/0/-1 交互矩陣（ADR-008）
- [ ] Step 1: SIM 矩陣 -1 衝突項顯示回流提示（ADR-008）
- [ ] Step 2: SubsystemHierarchyView 支援 diagram/list 切換
- [ ] Step 2: 可手動新增/編輯/刪除子系統，支援三層架構
- [ ] Step 2: InterfaceContractsPanel 顯示 6 維介面合約
- [ ] Step 2: PackageMapPanel 顯示空間佈局圖
- [ ] Step 3: 決策中心攤平所有來源方案，支援橫向比較
- [ ] Step 3: ConvergenceDashboard 正確顯示收斂狀態
- [ ] Step 3: CCI Badge 正確顯示每張方案卡的複雜度判定（Evolution/Weak Evolution/Patch）（ADR-008）
- [ ] Step 3: CCI "Patch" 方案 hover 顯示技術債提示（ADR-008）
- [ ] Step 3: Evidence Coverage Gauge 頂部渲染，< 40% 顯示橘色警告（ADR-008）
- [ ] Step 3: ArchitectureHaltOverlay 在架構衝突時正確阻擋
- [ ] Step 4: MUST 快篩矩陣正確評估，支援 AI 自動評估
- [ ] Step 5: RadarChart 正確渲染五維比較圖
- [ ] 所有 optimistic UI 更新在 API 失敗時正確回滾
- [ ] KnowledgeRefsPanel 依當前步驟顯示對應知識參考
- [ ] 步驟間可自由切換，狀態不遺失
