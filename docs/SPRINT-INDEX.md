# Sprint Developer Index

> **用途**：拿到 JIRA ticket → 查本表 → 跟連結走。零敘事，純指標。
>
> **最後更新**：2026-04-27 · **版本**：v1.0

---

## 1. By Page（頁面 → 規格 → API → Module → BDD → Gate）


| #   | Page             | Page Spec                                                                           | API Router                                                                                                                                                                                                                                                                                                                                                                                                            | Module Spec                                                                                                                                                                           | BDD Feature        | Gate                   |
| --- | ---------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ---------------------- |
| P01 | Auth 登入/註冊       | [01_auth](01-define/pages/01_auth.md)                                               | Supabase Auth                                                                                                                                                                                                                                                                                                                                                                                                         | —                                                                                                                                                                                     | —                  | —                      |
| P02 | ResetPassword    | [02_reset_password](01-define/pages/02_reset_password.md)                           | Supabase Auth                                                                                                                                                                                                                                                                                                                                                                                                         | —                                                                                                                                                                                     | —                  | —                      |
| P03 | ProjectList      | [03_project_list](01-define/pages/03_project_list.md)                               | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |
| P04 | Dashboard        | [04_project_dashboard](01-define/pages/04_project_dashboard.md)                     | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | Gate overview          |
| P05 | TaskDefinition   | [05_task_definition](01-define/pages/05_task_definition.md)                         | [brief.py](02-design/E5--api-design-specification.md#71-資源brief--task-definition-briefpy)                                                                                                                                                                                                                                                                                                                             | [analyst](02-design/specs/modules/analyst.md)                                                                                                                                         | —                  | Gate 1.1               |
| P06 | Explore          | [06_explore](01-define/pages/06_explore.md)                                         | [socratic.py](02-design/E5--api-design-specification.md#72-資源socratic-問題-socraticpy), [cld.py](02-design/E5--api-design-specification.md#73-資源因果迴圈-cldpy), [contradictions.py](02-design/E5--api-design-specification.md#74-資源contradictions-contradictionspy)                                                                                                                                                        | [analyst](02-design/specs/modules/analyst.md)                                                                                                                                         | F5, F6             | Gate 1.2, Phase Gate 1 |
| P07 | Track            | [07_track](01-define/pages/07_track.md)                                             | [assumption/risk](02-design/E5--api-design-specification.md#79-資源assumption--risk--action)                                                                                                                                                                                                                                                                                                                            | —                                                                                                                                                                                     | —                  | Gate 2.1               |
| P08 | Create           | [08_create](01-define/pages/08_create.md)                                           | [triz.py](02-design/E5--api-design-specification.md#75-資源triz-trizpy--核心), [subsystem](02-design/E5--api-design-specification.md#76-資源subsystem原-scamperpy-v9-重構), [anti_anchor.py](02-design/E5--api-design-specification.md#77-資源anti-anchor--validation-anti_anchorpy-validationpy), [convergence.py](02-design/E5--api-design-specification.md#78-資源convergence--unknown-factors-convergencepy-unknown_factorspy) | [triz-solver](02-design/specs/modules/triz-solver.md), [anti-anchor](02-design/specs/modules/anti-anchor.md), [subsystem-decomposer](02-design/specs/modules/subsystem-decomposer.md) | F1, F2, F4, F6, F7 | Gate 2.2, Phase Gate 2 |
| P09 | PreCadReview     | [09_pre_cad_review](01-define/pages/09_pre_cad_review.md)                           | [must/pre-cad](02-design/E5--api-design-specification.md#710-資源want--must--pre-cad-gate)                                                                                                                                                                                                                                                                                                                              | [evaluator](02-design/specs/modules/evaluator.md)                                                                                                                                     | F3                 | Gate P                 |
| P10 | CadInProgress    | [10_cad_in_progress](01-define/pages/10_cad_in_progress.md)                         | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |
| P11 | DesignReview     | [11_design_review](01-define/pages/11_design_review.md)                             | —                                                                                                                                                                                                                                                                                                                                                                                                                     | [evaluator](02-design/specs/modules/evaluator.md)                                                                                                                                     | —                  | Gate 3.1               |
| P12 | DecisionRecord   | [12_decision_record](01-define/pages/12_decision_record.md)                         | [want/must](02-design/E5--api-design-specification.md#710-資源want--must--pre-cad-gate)                                                                                                                                                                                                                                                                                                                                 | [evaluator](02-design/specs/modules/evaluator.md)                                                                                                                                     | F3                 | Gate 3.2, Phase Gate 3 |
| P13 | Feynman          | [13_feynman](01-define/pages/13_feynman.md)                                         | —                                                                                                                                                                                                                                                                                                                                                                                                                     | [knowledge](02-design/specs/modules/knowledge.md)                                                                                                                                     | —                  | Gate 8                 |
| P14 | KnowledgeBase    | [14_knowledge_base](01-define/pages/14_knowledge_base.md)                           | —                                                                                                                                                                                                                                                                                                                                                                                                                     | [knowledge](02-design/specs/modules/knowledge.md)                                                                                                                                     | —                  | —                      |
| P15 | ConstraintLabels | [15_constraint_label_dictionary](01-define/pages/15_constraint_label_dictionary.md) | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |
| P16 | Settings         | [16_settings](01-define/pages/16_settings.md)                                       | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |
| P17 | DevSeed          | [17_dev_seed](01-define/pages/17_dev_seed.md)                                       | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |
| P18 | NotFound         | [18_not_found](01-define/pages/18_not_found.md)                                     | —                                                                                                                                                                                                                                                                                                                                                                                                                     | —                                                                                                                                                                                     | —                  | —                      |


---

## 2. By Scenario（跨頁 E2E 流程）

> SSOT：`[E3--system-interaction-flow.md](01-define/E3--system-interaction-flow.md)`


| Scenario            | SSOT 章節                                                                               | Pages Traversed                                 | BDD Features |
| ------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------ |
| Forward TRIZ 解矛盾    | [E3x §2](01-define/E3--system-interaction-flow.md#2-scenario-1-forward-triz)          | P01 → P03 → P04 → P08                           | F1, F6, F7   |
| Reverse 跨域去錨定 | [E3x §3](01-define/E3--system-interaction-flow.md#3-scenario-2-anti-anchor)           | P04 → P08 → P07                                 | F2           |
| Pre-CAD Gate 審查     | [E3x §4](01-define/E3--system-interaction-flow.md#4-scenario-3-decision-hub--gate-x5) | P04 → P09 → P12                                 | F3           |
| Happy Path (8-Gate) | [E3x §1](01-define/E3--system-interaction-flow.md#1-overall-journey)                  | P01→P03→P04→P05→P06→P07→P08→P09→P10→P11→P12→P13 | F1–F8        |


---

## 3. By Backend Module（模組 → 規格 → 消費頁面）

> 完整索引：`[E5x--module-spec-index.md](02-design/specs/modules/E5x--module-spec-index.md)`


| Module              | Spec                                                                       | Consumed by Pages         |
| ------------------- | -------------------------------------------------------------------------- | ------------------------- |
| TrizSolverAgent     | [triz-solver.md](02-design/specs/modules/triz-solver.md)                   | P08 (Tab ① TRIZ)          |
| AntiAnchorAgent     | [anti-anchor.md](02-design/specs/modules/anti-anchor.md)                   | P08 (TRIZ L1 跨域去錨定)   |
| SubsystemDecomposer | [subsystem-decomposer.md](02-design/specs/modules/subsystem-decomposer.md) | P08 (Tab ②)               |
| EvaluatorAgent      | [evaluator.md](02-design/specs/modules/evaluator.md)                       | P08, P09, P11, P12        |
| AnalystAgent        | [analyst.md](02-design/specs/modules/analyst.md)                           | P05, P06, P08             |
| KnowledgeAgent      | [knowledge.md](02-design/specs/modules/knowledge.md)                       | P13, P14 (全域)             |
| EvidenceRegistry    | [evidence-registry.md](02-design/specs/modules/evidence-registry.md)       | P08 (Tab ③ Evidence), P09 |


---

## 4. BDD Feature 速查

> SSOT：`[E5x--bdd-scenarios.md](02-design/E5x--bdd-scenarios.md)`


| Feature | 名稱                                  | 對應 E3x | 主要頁面     |
| ------- | ----------------------------------- | ------ | -------- |
| F1      | Forward TRIZ 解矛盾                    | §2     | P08      |
| F2      | Reverse 跨域去錨定                    | §3     | P08      |
| F3      | Pre-CAD Gate 審查                     | §4     | P09, P12 |
| F4      | Entry Grading + Conditional Stepper | —      | P06      |
| F5      | Five-Why + KT Analysis              | —      | P06      |
| F6      | Function Analysis (FA) + OZ-OT      | —      | P06, P08 |
| F7      | SIM Matrix + CCI                    | —      | P08      |
| F8      | Evidence Registry                   | —      | P08, P09 |


---

## 5. 快速導航


| 你要找…            | 去這裡                                                                                                |
| --------------- | -------------------------------------------------------------------------------------------------- |
| 跨頁 E2E 流程 + 序列圖 | `[E3--system-interaction-flow.md](01-define/E3--system-interaction-flow.md)`                       |
| 單頁元件 + 互動 + AC  | `[01-define/pages/{N}_*.md](01-define/pages/)`                                                     |
| 路由樹 + IA 骨架     | `[E5x--frontend-information-architecture.md](02-design/E5x--frontend-information-architecture.md)` |
| API 端點細節        | `[E5--api-design-specification.md](02-design/E5--api-design-specification.md)` §7                  |
| Agent 模組 DbC    | `[specs/modules/](02-design/specs/modules/E5x--module-spec-index.md)`                              |
| BDD Gherkin     | `[E5x--bdd-scenarios.md](02-design/E5x--bdd-scenarios.md)`                                         |
| IA ↔ Spec 雙向對照  | `[pages/MAPPING.md](01-define/pages/MAPPING.md)` §1-4                                              |
| 架構決策 (ADR)      | `[01-define/adrs/](01-define/adrs/)`                                                               |


