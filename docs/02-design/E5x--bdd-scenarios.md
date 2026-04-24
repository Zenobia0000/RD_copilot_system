# E5x — BDD 情境與測試規格 (Behavior-Driven Development Scenarios)

---

**文件版本 (Document Version):** `v2.0`
**最後更新 (Last Updated):** `2026-04-24`
**主要作者 (Lead Author):** `RD Design Copilot Team`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `03_behavior_driven_development_guide.md`
**上游依據:** [`01-define/E3x--system-interaction-flow.md`](../01-define/E3x--system-interaction-flow.md) (3 scenarios) · [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)

---

## 目錄 (Table of Contents)

- [Ⅰ. BDD 核心原則](#-bdd-核心原則)
- [Ⅱ. Gherkin 語法速查](#-gherkin-語法速查)
- [Ⅲ. BDD 範本 (`.feature` file)](#-bdd-範本-feature-file)
  - [Feature 1: Forward TRIZ 解矛盾](#feature-1-forward-triz-解矛盾對應-e3x-2)
  - [Feature 2: Reverse Anti-Anchor](#feature-2-reverse-anti-anchor對應-e3x-3)
  - [Feature 3: Pre-CAD Gate 審查](#feature-3-pre-cad-gate-審查對應-e3x-4)
  - [Feature 4: Entry Grading + Conditional Stepper](#feature-4-entry-grading--conditional-stepper入口等級評估--條件式步進器)
  - [Feature 5: Five-Why + KT Analysis](#feature-5-five-why--kt-analysis問題定向)
  - [Feature 6: Function Analysis (FA) + OZ-OT](#feature-6-function-analysis-fa--oz-ot)
  - [Feature 7: SIM Matrix + CCI](#feature-7-sim-matrix--cci解法交互矩陣--概念信心指標)
  - [Feature 8: Evidence Registry](#feature-8-evidence-registry證據登記簿)
- [Ⅳ. 最佳實踐](#-最佳實踐)

---

**目的**: 以 Gherkin 結構化描述 RD Design Copilot 的八大使用情境（Forward TRIZ / Reverse Anti-Anchor / Pre-CAD Gate / Entry Grading / Problem Scoping / Function Analysis / SIM Matrix / Evidence Registry），作為前後端 E2E 測試、`E7x--e2e-manual-scripts/` 手測腳本與 Playwright 自動化的共同事實來源。

---

## Ⅰ. BDD 核心原則

1. **從對話開始**：每個 Feature 對應 E3x §2/§3/§4 的 Scenario；變更前由 RD / PM / QA 三方確認。
2. **由外而內**：情境用 UI 可觀察的行為描述，不涉及 Phase A/B 內部編排。
3. **通用語言 (Ubiquitous Language)**：
   - `分層 drill-down`（TRIZ L1/L2/L3）
   - `子系統 (subsystem)`、`介面契約 (interface contract)`
   - `反向路線 (anti-anchor route)`、`Validation Passport`
   - `MUST / WANT / AC`（Pre-CAD Gate 評分）

---

## Ⅱ. Gherkin 語法速查

- `Feature` → 對應 E3x 中一個 Scenario 或 Create/Explore/Review 頁面下的一個功能群
- `Background` → 共用初始化（已登入、已有 brief 凍結）
- `Scenario / Scenario Outline / Examples` → 具體行為
- `Given / When / Then / And / But` → Arrange-Act-Assert

---

## Ⅲ. BDD 範本 (`.feature` file)

### Feature 1: Forward TRIZ 解矛盾（對應 E3x §2）

**檔案名稱**: `forward_triz_solve.feature`

```gherkin
# Feature: Forward TRIZ 分層解矛盾
# 對應 E3x: §2 Scenario 1
# 對應 Spec: specs/triz/E5x--triz-layered-drilldown-optimization.md
# 對應 API: POST /triz/solve-layered

Feature: Forward TRIZ layered drill-down

  # ADR-007 (2026-04-15): Explore 階段 Contradiction 改為 TC-only；
  # Create 階段 solve_triz_layered 入口自動派生 PC/SF，使用者不需手動選擇分類。

  Background:
    Given I am a logged-in RD user
    And I have a project with frozen Brief and at least one TC-typed Contradiction "C-01" (ADR-007 TC-only)
    And I am on the "/create" page, Tab ① TRIZ

  @happy-path @smoke
  Scenario: L1 surface 解即可滿足，不需往下鑽
    Given Contradiction "C-01" improves "重量" and worsens "剛性"
    When I click "Solve Layered" on "C-01"
    Then I should see an "L1 Surface" card within 8 seconds
    And the card should list at least 1 "InventivePrinciple" recommendation
    And the card should show a "Stop / Drill-Down" decision toggle defaulting to "Stop"

  @drill-down
  Scenario: L1 不滿足時進入 L2 分離原理
    Given the L1 surface critic returns confidence < 0.6
    When the system auto-triggers drill-down
    Then an "L2 Root Cause" card should appear
    And it should list one of "Space / Time / Condition / System-Level" separation candidates
    And each candidate should link to an "L3 Su-Field" slot

  @adr-006 @tc-only
  Scenario: TC-only request → 後端自動派生 PC/SF（ADR-007）
    Given Contradiction "C-01" has only TC fields (improving_param, worsening_param, engineering_statement)
    And PC / SF fields are absent from the request payload
    When I click "Solve Layered" on "C-01"
    Then the backend should derive PC via "analyst.decompose_tc_to_pcs"
    And the backend should derive SF via "analyst.derive_su_field_from_tc"
    And the derived PC/SF should appear in the response but NOT be written back to the "contradictions" table
    And all three layers (L1/L2/L3) should be populated when derivation succeeds

  @adr-006 @degraded
  Scenario: SF 派生失敗 → L3 降級但 L1/L2 正常
    Given Contradiction "C-01" has only TC fields
    And "analyst.derive_su_field_from_tc" returns None (LLM cannot produce meaningful S1/S2/F)
    When I click "Solve Layered" on "C-01"
    Then "l1_surface" and "l2_root_cause" should still be populated
    And "l3_sufield" should be None
    And the response should include a warning "SF derivation failed, L3 degraded"

  @phase-b
  Scenario Outline: 多解併行採納策略
    Given I have <n> layered solutions for "C-01"
    When I open Tab ③ Decision Center
    Then I should see "<strategy>" as the recommended option
    And the Phase B directive should be "<directive>"

    Examples:
      | n | strategy           | directive                     |
      | 1 | adopt              | merge-to-subsystem            |
      | 2 | merge              | cross-check-then-merge        |
      | 3 | pick-one-drilldown | run-phase-b-cross-validation  |
```

### Feature 2: Reverse Anti-Anchor（對應 E3x §3）

**檔案名稱**: `reverse_anti_anchor.feature`

```gherkin
# Feature: Reverse Anti-Anchor 反向路線探索
# 對應 E3x: §3 Scenario 2
# 對應 API: POST /alternatives/anti-anchor, POST /alternatives/validation-passport

Feature: Reverse Anti-Anchor exploration

  Background:
    Given I am a logged-in RD user on the "/explore" page
    And the project has an anchor solution "A-01 (陀螺儀平衡)"

  @happy-path
  Scenario: 產生 3 條反向路線並發放 Validation Passport
    When I click "Anti-Anchor Routes"
    Then I should receive exactly 3 "AntiAnchorRoute" cards
    And each card should display a "差異性 (diff)" score and an "AC 風險" level
    When I click "Validation Passport" on the top route
    Then a ValidationPassport with at least 2 assumptions should be attached
    And each assumption's status should be "pending"

  @sad-path
  Scenario: anchor 不存在時的保護
    Given the project has no confirmed anchor
    When I click "Anti-Anchor Routes"
    Then I should see an error banner "Please confirm an anchor solution first"
```

### Feature 3: Pre-CAD Gate 審查（對應 E3x §4）

**檔案名稱**: `pre_cad_gate_review.feature`

```gherkin
# Feature: Pre-CAD Gate 六維審查
# 對應 E3x: §4 Scenario 3
# 對應 Spec: specs/review-templates/E5x--pre-cad-review-template.md
# 對應 API: POST /pre-cad-reviews/{rid}/ai-analyze

Feature: Pre-CAD Gate six-dimension review

  Background:
    Given I am a logged-in RD manager
    And there is a Pre-CAD review "R-42" with 2 candidate solutions
    And I am on "/pre-cad-review/R-42"

  @happy-path @gate
  Scenario: AI 分析完成並通過 Gate
    When I click "AI Analyze"
    Then each solution should receive 6 dimension scores
    And each dimension should cite at least 1 evidence reference
    When I click "Sign & Pass Gate"
    Then the review status should become "passed"
    And a KT decision record should be created

  @blocker
  Scenario: MUST rule 不達標阻擋 Gate
    Given solution "S-1" violates MUST rule "MUST-safety-001"
    When I click "Sign & Pass Gate"
    Then I should see an error "MUST rule MUST-safety-001 not satisfied"
    And the review status should remain "in_review"
```

---

## Ⅳ. 最佳實踐

1. **一個 Scenario 只測一件事** — 跨多 tab 的流程拆成多個 `Scenario`，避免連鎖斷點模糊。
2. **用陳述式而非命令式** — `Then the L1 card is visible`，不寫 `Then the system renders the L1 card`。
3. **避免 UI 細節** — 不要測試按鈕顏色/DOM id；測試可觀察的結果（文字、角色、狀態）。
4. **從 RD 使用者角度編寫** — Gherkin 必須能讓 PM 讀懂。
5. **tag 規範**：`@happy-path` / `@sad-path` / `@edge-case` / `@smoke` / `@gate` / `@drill-down` / `@phase-b`
6. **同步 E7x**：每個 `@smoke` Scenario 必須在 [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/) 有對應手測步驟。

**LLM Prompting Guide:**
> 「請根據以下 BDD Scenario，為 React 19 前端組件生成失敗的 Vitest + Testing Library 測試。情境：[貼上 Gherkin]」

---

### Feature 4: Entry Grading + Conditional Stepper（入口等級評估 + 條件式步進器）

**檔案名稱**: `entry_grading_stepper.feature`

```gherkin
# Feature: Entry Grading + Conditional Stepper
# 對應 WBS: 8.7.3
# 對應 API: POST /projects/{pid}/entry-grading

Feature: Entry Grading 入口等級評估與條件式步進器

  Background:
    Given I am a logged-in RD user
    And I have a project with frozen Brief
    And I am on the "/explore" page

  @happy-path @smoke
  Scenario: RD 輸入問題描述後系統判定 Level A
    When 點擊「入口等級評估」按鈕
    And 輸入問題描述並提交
    Then 系統回傳 Level A/B/C 判定
    And 根據等級顯示對應的步驟流程

  @happy-path
  Scenario: Level A 啟動 5-step stepper
    Given 入口判定為 Level A
    Then Explore 頁切換為 5-step stepper
    And stepper 包含步驟「問題定向 → 功能分析 → 蘇格拉底 → 矛盾 → CLD」
    And 當前步驟高亮為「問題定向」

  @happy-path
  Scenario: Level B 啟動 3-step stepper
    Given 入口判定為 Level B
    Then Explore 頁切換為 3-step stepper
    And stepper 包含步驟「矛盾識別 → TRIZ 求解 → CLD」

  @happy-path
  Scenario: Level C 直接進入快速模式
    Given 入口判定為 Level C
    Then Explore 頁顯示快速模式介面
    And 使用者可直接輸入已知矛盾進行求解

  @sad-path
  Scenario: 問題描述過短無法判定等級
    When 點擊「入口等級評估」按鈕
    And 輸入少於 10 個字的描述並提交
    Then 系統顯示錯誤提示「問題描述不足，請提供更詳細的情境說明」
```

### Feature 5: Five-Why + KT Analysis（問題定向）

**檔案名稱**: `problem_scoping.feature`

```gherkin
# Feature: Five-Why + KT Analysis (Problem Scoping)
# 對應 WBS: 8.7.3
# 對應 API: POST /projects/{pid}/five-why, POST /projects/{pid}/kt-analysis

Feature: Five-Why 與 KT Is/Is Not 問題定向分析

  Background:
    Given I am a logged-in RD user
    And 入口判定為 Level A
    And I am on the "Problem Scoping" step of the Explore stepper

  @happy-path @smoke
  Scenario: RD 執行 5Why 分析
    When 輸入問題陳述並執行 5Why
    Then 顯示 5 層 Why-Because 鏈
    And 每層 Why 包含「現象」與「因果關係」欄位
    And 列出根因和建議下一步
    And 根因自動填入 stepper 的下一步驟作為輸入

  @happy-path
  Scenario: RD 執行 KT Is/Is Not 分析
    When 點擊「KT 分析」tab
    And 填入 Is（發生的現象）與 Is Not（未發生的現象）
    And 點擊「分析差異」
    Then 系統顯示 Is/Is Not 對照表
    And 自動推斷可能原因至少 1 條
    And 每條可能原因附帶信心分數

  @edge-case
  Scenario: 5Why 鏈中某層使用者手動修正
    Given 5Why 分析已產出 5 層鏈
    When 使用者編輯第 3 層的 Why 描述
    Then 第 4-5 層自動重新推導
    And 根因更新為修正後的推導結果

  @sad-path
  Scenario: 問題陳述為空時拒絕執行
    When 未輸入問題陳述直接點擊「執行 5Why」
    Then 顯示驗證錯誤「請先輸入問題陳述」
    And 5Why 分析不會被觸發
```

### Feature 6: Function Analysis (FA) + OZ-OT

**檔案名稱**: `function_analysis_oz_ot.feature`

```gherkin
# Feature: Function Analysis (FA) + OZ-OT
# 對應 WBS: 8.7.3
# 對應 API: POST /projects/{pid}/function-analysis, POST /projects/{pid}/oz-ot

Feature: 功能分析 (FA) 與 OZ-OT 操作區域/時間分析

  Background:
    Given I am a logged-in RD user
    And I have a project with frozen Brief and completed Problem Scoping

  @happy-path @smoke
  Scenario: RD 執行功能分析
    Given I am on the "Function Analysis" step of the Explore stepper
    When 輸入系統描述和組件清單
    And 點擊「產生功能模型」
    Then 顯示組件交互圖
    And 交互圖中以綠色箭頭標示「有用功能」
    And 以紅色箭頭標示「有害功能」
    And 以虛線箭頭標示「不足功能」
    And 顯示 SF（物質-場）診斷摘要

  @happy-path
  Scenario: FA 結果自動識別問題組件
    Given 功能分析已完成
    Then 有害功能和不足功能的組件自動標記為「問題組件」
    And 問題組件列表供後續矛盾識別使用

  @happy-path @smoke
  Scenario: RD 在 Create 執行 OZ-OT 分析
    Given I am on the "/create" page, TRIZ 區段
    And 已選定一條矛盾 "C-01"
    When 展開 OZ-OT 面板並觸發分析
    Then 顯示操作區域 (OZ) — 至少列出 1 個空間區域
    And 顯示操作時間 (OT) — 至少列出 1 個時間窗口
    And 顯示可控參數 (Px) — 至少列出 1 個可調參數
    And OZ/OT/Px 各項均附帶簡要說明

  @edge-case
  Scenario: 組件清單為空時的提示
    Given I am on the "Function Analysis" step
    When 輸入系統描述但組件清單為空
    And 點擊「產生功能模型」
    Then 系統顯示提示「請至少輸入 2 個組件以進行功能分析」
    And 功能分析不會被觸發
```

### Feature 7: SIM Matrix + CCI（解法交互矩陣 + 概念信心指標）

**檔案名稱**: `sim_matrix_cci.feature`

```gherkin
# Feature: SIM Matrix + CCI
# 對應 WBS: 8.7.3
# 對應 API: POST /projects/{pid}/sim-matrix, GET /projects/{pid}/solutions/{sid}/cci

Feature: SIM 解法交互矩陣與 CCI 概念信心指標

  Background:
    Given I am a logged-in RD user
    And I am on the "/create" page
    And 專案已有至少 2 條 TC 矛盾且各有解法

  @happy-path @smoke
  Scenario: 多矛盾時觸發 SIM 矩陣
    When 執行 SIM 矩陣分析
    Then 顯示解法交互矩陣
    And 矩陣中每個交叉格顯示 +1（協同）/ 0（無關）/ -1（衝突）
    And 推薦最佳不衝突組合
    And 推薦組合以高亮方式標示

  @happy-path
  Scenario: 方案卡顯示 CCI 評定
    Given SIM 矩陣分析已完成
    When 查看個別方案卡
    Then 每張方案卡顯示 CCI badge
    And badge 標籤為「Evolution」（演化型）或「Patch」（修補型）
    And badge 旁顯示概念信心分數（0-100）

  @edge-case
  Scenario: 僅 1 條矛盾時 SIM 矩陣不可用
    Given 專案僅有 1 條 TC 矛盾
    When 嘗試觸發 SIM 矩陣分析
    Then 顯示提示「SIM 矩陣需要至少 2 條矛盾的解法才能進行交互分析」
    And SIM 矩陣按鈕為禁用狀態

  @sad-path
  Scenario: 矛盾有解法但未全部完成求解
    Given 專案有 3 條 TC 矛盾但僅 1 條已完成求解
    When 嘗試觸發 SIM 矩陣分析
    Then 顯示警告「尚有 2 條矛盾未完成求解，建議先完成所有求解再進行 SIM 分析」
    And 提供「僅分析已有解法」的選項
```

### Feature 8: Evidence Registry（證據登記簿）

**檔案名稱**: `evidence_registry.feature`

```gherkin
# Feature: Evidence Registry
# 對應 WBS: 8.7.3
# 對應 API: POST /projects/{pid}/evidence, PATCH /projects/{pid}/evidence/{eid}, GET /projects/{pid}/evidence/coverage

Feature: Evidence Registry 證據登記與覆蓋率追蹤

  Background:
    Given I am a logged-in RD user
    And I have a project with at least 1 completed TRIZ solution

  @happy-path @smoke
  Scenario: AI 分析自動登記 evidence claim
    When AI 完成一次 TRIZ 求解分析
    Then Evidence Registry 自動新增至少 1 條 claim
    And 每條 claim 包含「來源步驟」「聲明內容」「信心等級」
    And claim 預設狀態為「pending」

  @happy-path
  Scenario: RD 驗證一條 claim
    Given Evidence Registry 有一條狀態為「pending」的 claim
    When RD 點擊該 claim 的「驗證」按鈕
    And 上傳驗證附件或填入驗證說明
    And 選擇結果為「confirmed」或「rejected」
    Then claim 狀態更新為選擇的結果
    And 顯示驗證者名稱與時間戳

  @gate @smoke
  Scenario: Gate PG2 檢查 evidence 覆蓋率 ≥ 40%
    Given 專案進入 Pre-Gate 2 (PG2) 審查
    When 系統計算 evidence 覆蓋率
    Then 若覆蓋率 ≥ 40%，Gate PG2 顯示「通過」
    And 覆蓋率數值顯示在 Gate 報告的 Evidence 區段
    And 覆蓋率計算方式為 confirmed_claims / total_claims × 100%

  @gate @blocker
  Scenario: Gate PG2 覆蓋率不足阻擋通過
    Given 專案 evidence 覆蓋率 = 25%（低於 40% 門檻）
    When 嘗試通過 Gate PG2
    Then 顯示阻擋訊息「Evidence 覆蓋率 25% 未達 40% 門檻」
    And Gate 狀態維持「blocked」
    And 列出尚未驗證的 pending claims 清單

  @sad-path
  Scenario: 無任何 claim 時覆蓋率顯示 N/A
    Given Evidence Registry 為空（0 條 claim）
    When 查看 evidence 覆蓋率
    Then 覆蓋率顯示為「N/A」
    And 提示「尚無 AI 分析產出，請先執行 TRIZ 分析流程」
```

---

**延伸閱讀**:
- E3x 完整 scenario 敘述 → [`01-define/E3x--system-interaction-flow.md`](../01-define/E3x--system-interaction-flow.md)
- 對應手測腳本 → [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/)
- WBS WS-H Playwright 自動化 → [`01-define/E3x--wbs-development-plan-addendum.md`](../01-define/E3x--wbs-development-plan-addendum.md)
