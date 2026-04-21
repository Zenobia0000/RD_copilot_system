# E5x — BDD 情境與測試規格 (Behavior-Driven Development Scenarios)

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-15`
**主要作者 (Lead Author):** `RD Design Copilot Team`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `03_behavior_driven_development_guide.md`
**上游依據:** [`01-define/E3x--system-interaction-flow.md`](../01-define/E3--system-interaction-flow.md) (3 scenarios) · [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)

---

## 目錄 (Table of Contents)

- [Ⅰ. BDD 核心原則](#-bdd-核心原則)
- [Ⅱ. Gherkin 語法速查](#-gherkin-語法速查)
- [Ⅲ. BDD 範本 (`.feature` file)](#-bdd-範本-feature-file)
- [Ⅳ. 最佳實踐](#-最佳實踐)

---

**目的**: 以 Gherkin 結構化描述 RD Design Copilot 的三大使用情境（Forward TRIZ / Reverse Anti-Anchor / Pre-CAD Gate），作為前後端 E2E 測試、`E7x--e2e-manual-scripts/` 手測腳本與 Playwright 自動化的共同事實來源。

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

**延伸閱讀**:
- E3x 完整 scenario 敘述 → [`01-define/E3x--system-interaction-flow.md`](../01-define/E3--system-interaction-flow.md)
- 對應手測腳本 → [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/)
- WBS WS-H Playwright 自動化 → [`01-define/wbs-workstreams/WS-H`](../01-define/wbs-workstreams/WS-H--playwright-e2e-followup.md)
