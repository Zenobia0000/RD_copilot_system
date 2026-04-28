# 開發工作流哲學手冊 — RD Design Copilot

---

**文件版本**：`v1.1`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**模板來源**：`VibeCoding_Workflow_Templates/01_development_workflow_cookbook.md`

---

## 1. 核心哲學

RD Design Copilot 採用 **BDD + DDD + Clean Architecture + TDD** 四方法論組合：

### 1.1 BDD（Behavior-Driven Development）

> 從用戶行為出發，三方對齊（PM / Engineer / QA）

- **入口**：[`02_prd.md §3 User Stories`](./02_prd.md)
- **產出**：[`03_bdd_guide.md`](./03_bdd_guide.md) 7 個 Feature × N Scenarios
- **驅動**：每個 PR 必須對應到 ≥ 1 個 BDD scenario

### 1.2 DDD（Domain-Driven Design）

> 把業務語言（TRIZ、TR、Phase Gate）變成程式碼結構

- **Bounded Context**：見 [`05_architecture.md §1.2`](./05_architecture.md)
- **Ubiquitous Language**：TC/PC/SF、OZ-OT-Px、CCI、Gate（D1 `[COVERED by G0]` / D2 `[COVERED by G1]` / X1 `[COVERED by navigation]` / X2 `[COVERED by G2]` / P `[SIMPLIFIED → triz-verify cad_readiness]` / V1 `[DEFER → Beta]` / V2 `[DEFER → Beta]` / V4 `[DEFER → GA]`）、TR0-TR10。Gate 層級分析見 [`18_flow_contract.md §2`](./18_flow_contract.md)
- **聚合根（Aggregate Root）**：Project（含 Brief/Contradictions/Alternatives/DecisionRecord）

### 1.3 Harness-first Architecture

> 業務邏輯在 Skill（markdown），不在 Python class；Python 層是穩定的執行引擎

```
Command（使用者入口）→ Skill（業務邏輯 SKILL.md）→ Tool（Python ABC）
```

- 詳見 [`08_project_structure.md`](./08_project_structure.md) v2.0 + [`07_module_spec.md`](./07_module_spec.md) v2.0
- 先前 Clean Architecture 提案（Domain/Application/Infrastructure）已被 harness-first 取代

### 1.4 TDD（Test-Driven Development）

> 先寫測試、再寫實作；TDD 不是寫測試，是設計工具

- **Red → Green → Refactor**
- BDD scenarios → 拆解到模組層 unit tests（[`07_module_spec.md`](./07_module_spec.md)）

---

## 2. 四個開發階段

```
Planning      Design       Development     Quality & Deployment
─────────    ─────────    ─────────────   ─────────────────────
02 PRD       04 ADR       11 Code Review   13 Security
03 BDD       05 Arch      (持續)           14 Deployment
16 WBS       06 API                        15 Documentation
             07 Module
             08-10 Detail
             12 FE Arch
             17 FE IA
```

---

## 3. 支援文件

| 用途 | 文件 |
|:-----|:-----|
| 整體工作流 | [`00_workflow_manual.md`](./00_workflow_manual.md) |
| 設計系統規範 | [`design-system-specs/`](../../rd_assistant_design_system/design-system-specs/) |
| TRIZ 方法學 | `docs/_harness/auto_triz_strategy.md` |
| TR 工程框架 | `docs/_harness/engineering/tr_gate_framework.md` |
| 領域知識 | `docs/_domain-knowledge/DK-01-05` |

---

## 4. 哲學原則

### 4.1 Linus Torvalds 三大鐵律（引用 `~/.claude/CLAUDE.md`）

1. **"Good Taste"**：消除特殊情況 > 增加條件判斷
2. **"Never Break Userspace"**：向後相容神聖不可侵犯
3. **實用主義**：解決真問題，不為論文而 code

### 4.2 「先架構，再設計」

PRD（02）→ 架構（05）→ 細部（07-10），每層下沉

### 4.3 「先立憲，再寫法」

Foundation tokens（00 design-system）→ Components（01）→ Patterns（02）→ Templates（03）

### 4.4 「一頁一 PRD，一次一任務」

每個 PR 解決一個 BDD scenario，不混功能

### 4.5 「全域約束 > 在地細節」

Global System Prompt（design-system 01_GLOBAL）不可被 Page Prompt 推翻

### 4.6 「資料有源頭」

所有 KPI / 數值聲明必須在 Evidence Registry 有 source；確認等級分 4 級

---

## 文件溯源

- 模板：`VibeCoding_Workflow_Templates/01_development_workflow_cookbook.md`
- 整合：`~/.claude/CLAUDE.md` Linus 思考流程 + `docs/_harness/auto_triz_strategy.md` Evidence 等級
