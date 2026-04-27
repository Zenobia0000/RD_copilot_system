# RD Design Copilot — Documentation Hub

## TR Gate View — Where Are We?

```
DISCOVER        DEFINE         DESIGN         DEVELOP           DELIVER
TR0  TR1       TR2  TR3      TR4  TR5       TR6    TR7        TR8  TR9  TR10
 *    *         *    *        *    ~         .      .          ~    ~    .
```
`*` = gate passed | `~` = in progress | `.` = not started

## 9 Essential Documents + 3 Gate Reviews

| #    | Gate | Document | Status |
|------|------|----------|--------|
| E1   | TR1  | [00-discover/E1--project-brief-and-prd](00-discover/E1--project-brief-and-prd.md) | Approved |
| E2   | TR2  | [01-define/E2--statement-of-work](01-define/E2--statement-of-work.md) + [01-define/adrs/](01-define/adrs/) | Approved |
| E3   | TR3  | [01-define/E3--architecture-and-design](01-define/E3--architecture-and-design.md) (v2.0 · 2026-04-15 · VibeCoding 05 三部分骨架) | Active |
| E4   | TR3  | [01-define/diagrams/E4--erd](01-define/diagrams/E4--erd.md) | Draft |
| E5   | TR4  | [02-design/E5--api-design-specification](02-design/E5--api-design-specification.md) + [E5x--system-design-overview](02-design/E5x--system-design-overview.md) | Active |
| E6   | TR5  | [02-design/E6x--schema-codegen-workflow](02-design/E6x--schema-codegen-workflow.md) | Active |
| E7   | TR5  | [02-design/E7x--e2e-manual-scripts/](02-design/E7x--e2e-manual-scripts/) | Active |
| GR6  | TR6  | [03-develop/GR6--code-complete](03-develop/GR6--code-complete.md) | Draft |
| GR7  | TR7  | [03-develop/GR7--integration](03-develop/GR7--integration.md) | Draft |
| E8   | TR8  | [04-deliver/E8--security-and-readiness-checklists](04-deliver/E8--security-and-readiness-checklists.md) | Draft |
| E9   | TR9  | [04-deliver/E9--deployment-and-operations-guide](04-deliver/E9--deployment-and-operations-guide.md) | Draft |
| GR10 | TR10 | [04-deliver/GR10--ga-readiness](04-deliver/GR10--ga-readiness.md) | Draft |

## The 5D Phases

| Phase    | Folder | Question | Gates |
|----------|--------|----------|-------|
| DISCOVER | [00-discover/](00-discover/_MOC.md) | What problem are we solving? | TR0-TR1 |
| DEFINE   | [01-define/](01-define/_MOC.md) | How does the system work? | TR2-TR3 |
| DESIGN   | [02-design/](02-design/_MOC.md) | What exactly do we build? | TR4-TR5 |
| DEVELOP  | [03-develop/](03-develop/_MOC.md) | Does the code work? | TR6-TR7 |
| DELIVER  | [04-deliver/](04-deliver/_MOC.md) | Can we ship and operate it? | TR8-TR10 |

## Supporting Zones

| Zone | Purpose |
|------|---------|
| [_domain-knowledge/](_domain-knowledge/DK-00--index.md) | RD 設計方法論專業知識 — MECE 4 文件：哲學流程 (DK-01)、TRIZ (DK-02)、KT 決策 (DK-03)、資料模型 (DK-04) |
| [_gap-analysis/](_gap-analysis/) | 缺口分析 vs 投資人/合約需求 |
| [_meeting-minutes/](_meeting-minutes/) | 會議決策紀錄 |
| [_superseded/](_superseded/_MOC.md) | 已被取代的文件版本 |

## Knowledge Flow

```
00-discover (WHY)
    |
    v
01-define (HOW) <---> _domain-knowledge (WHAT WE KNOW)
    |
    v
02-design (WHAT TO BUILD)
    |
    v
03-develop (CODE & VERIFY)
    |
    v
04-deliver (SHIP & OPERATE)

_gap-analysis <--- validates all zones
```

## Reading Paths

### Path A: New Team Member
1. [E1--project-brief-and-prd](00-discover/E1--project-brief-and-prd.md) — What we are building and why
2. [E1x--user-journey-map](00-discover/E1x--user-journey-map.md) — How users interact with the system
3. [E3--architecture-and-design](01-define/E3--architecture-and-design.md) — Technical architecture overview
4. [E6x--schema-codegen-workflow](02-design/E6x--schema-codegen-workflow.md) — How we work

### Path B: Investor / Stakeholder
1. [RD_Copilot_Executive_Summary](00-discover/presentations/RD_Copilot_Executive_Summary.md) — One-page architecture
2. [RD_Copilot_BD_Pitch_v1](00-discover/presentations/RD_Copilot_BD_Pitch_v1.md) — Competitive advantages
3. [E2--statement-of-work](01-define/E2--statement-of-work.md) — Timeline and progress

### Path C: Building a Feature
1. [02-design/specs/](02-design/_MOC.md) — Find the technical spec
2. [01-define/E3--architecture-and-design § Appendix](01-define/E3--architecture-and-design.md#appendix架構細節整合) — Visual references + SA architecture appendices (A-E, integrated into E3)

### Path D: Understanding the Domain
1. [_domain-knowledge/](_domain-knowledge/DK-00--index.md) — 方法論知識庫 (MECE 4 文件)

## VibeCoding Template Coverage (18/18)

| # | Template | Project Doc |
|---|----------|-------------|
| 00 | workflow_manual | [01-define/VC00--workflow-manual](01-define/VC00--workflow-manual.md) |
| 01 | development_workflow_cookbook | [01-define/VC01--development-workflow-cookbook](01-define/VC01--development-workflow-cookbook.md) |
| 02 | project_brief_and_prd | [00-discover/E1--project-brief-and-prd](00-discover/E1--project-brief-and-prd.md) |
| 03 | bdd_guide | [02-design/E5x--bdd-scenarios](02-design/E5x--bdd-scenarios.md) |
| 04 | adr_template | [01-define/adrs/](01-define/adrs/) |
| 05 | architecture_and_design | [01-define/E3--architecture-and-design](01-define/E3--architecture-and-design.md) |
| 06 | api_design_specification | [02-design/E5--api-design-specification](02-design/E5--api-design-specification.md) |
| 07 | module_specification_and_tests | [02-design/specs/modules/](02-design/specs/modules/E5x--module-spec-index.md) |
| 08 | project_structure_guide | [02-design/E5x--project-structure-guide](02-design/E5x--project-structure-guide.md) |
| 09 | file_dependencies | [02-design/specs/E5x--file-dependencies](02-design/specs/E5x--file-dependencies.md) |
| 10 | class_relationships | [02-design/specs/E5x--class-relationships](02-design/specs/E5x--class-relationships.md) |
| 11 | code_review_and_refactoring | [03-develop/GR6x--code-review-guide](03-develop/GR6x--code-review-guide.md) |
| 12 | frontend_architecture | [02-design/E5x--frontend-architecture](02-design/E5x--frontend-architecture.md) |
| 13 | security_and_readiness_checklists | [04-deliver/E8--security-and-readiness-checklists](04-deliver/E8--security-and-readiness-checklists.md) |
| 14 | deployment_and_operations | [04-deliver/E9--deployment-and-operations-guide](04-deliver/E9--deployment-and-operations-guide.md) |
| 15 | documentation_and_maintenance | [04-deliver/E9x--documentation-maintenance-guide](04-deliver/E9x--documentation-maintenance-guide.md) |
| 16 | wbs_development_plan | [01-define/E3--wbs-development-plan](01-define/E3--wbs-development-plan.md) |
| 17 | frontend_information_architecture | [02-design/E5x--frontend-information-architecture](02-design/E5x--frontend-information-architecture.md) |

## Document Status Legend

| Status | Meaning |
|--------|---------|
| Approved | Reviewed and accepted |
| Active | Living document, updated regularly |
| Draft | Work in progress |
| Template | Gate review checklist, fill in during gate review |
| Planned | Identified but not yet created |
| Superseded | Replaced by newer version (see [_superseded/](_superseded/_MOC.md)) |
