# 01-define — How does the system work?

> Gates: TR2–TR3
> 模板對應：VibeCoding 04 (ADR) · 05 (Architecture & Design) · 16 (WBS)

---

## Core Documents


| #   | Gate | Document                                                                                                                  | Status   |
| --- | ---- | ------------------------------------------------------------------------------------------------------------------------- | -------- |
| E2  | TR2  | [E2--statement-of-work](E2--statement-of-work.md)                                                                         | Approved |
| E3  | TR3  | [E3--architecture-and-design](E3--architecture-and-design.md) — Part 1: 架構總覽 (C4, Tech Stack, NFR)                        | Active   |
| E3  | TR3  | [E3--ai-agent-detailed-design](E3--ai-agent-detailed-design.md) — Part 2: AI Agent 協作架構 (§11)                             | Active   |
| E3  | TR3  | `diagrams/` — SA 視角附錄: [A](diagrams/appendix-a--forward-subsystem-discovery.md) / [B](diagrams/appendix-b--forward-triz-solver.md) / ~~[C](diagrams/appendix-c--reverse-anti-anchor.md)~~ *(已退役，AA 併入 TRIZ L1 跨域去錨定)* / [D](diagrams/appendix-d--state-machine.md) / [E](diagrams/appendix-e--triz-scamper-flow.md) | Active   |
| E3  | TR3  | [E3--system-interaction-flow](E3--system-interaction-flow.md) — 3 scenarios: Forward TRIZ / ~~Reverse Anti-Anchor~~ *(已退役)* / Pre-CAD | Active   |
| E4  | TR3  | [diagrams/E4--erd](diagrams/E4--erd.md) — Supabase migration 權威 ERD (36 tables, 41 FK, RLS)                               | Draft    |


---

## Architecture (E3 三部曲)


| 文件                                                                  | 內容                                                    | 行數    |
| ------------------------------------------------------------------- | ----------------------------------------------------- | ----- |
| [E3--architecture-and-design](E3--architecture-and-design.md)       | Part 1: §1-§10 架構總覽 (C4, Tech Stack, Data, NFR, Risk) | ~650  |
| [E3--ai-agent-detailed-design](E3--ai-agent-detailed-design.md)     | Part 2: §11 AI Agent 協作架構詳設                           | ~635  |
| [Appendix A](diagrams/appendix-a--forward-subsystem-discovery.md) | Forward Subsystem Discovery Architecture | ~1183 |
| [Appendix B](diagrams/appendix-b--forward-triz-solver.md) | Forward TRIZ Solver Architecture | ~1374 |
| ~~[Appendix C](diagrams/appendix-c--reverse-anti-anchor.md)~~ | ~~Reverse Anti-Anchor Architecture~~ *(已退役，AA 併入 TRIZ L1 跨域去錨定)* | ~~~966~~ |
| [Appendix D](diagrams/appendix-d--state-machine.md) | State Machine (Process + Artifact) | ~226 |
| [Appendix E](diagrams/appendix-e--triz-scamper-flow.md) | TRIZ Flow + 雙軌決策中心 | ~408 |


---

## ADRs (VibeCoding 04)


| ADR                                                               | Decision                                     | Status      | Code Impact                                        |
| ----------------------------------------------------------------- | -------------------------------------------- | ----------- | -------------------------------------------------- |
| [001](adrs/ADR-001-baas-first-architecture.md)                    | BaaS-First (Supabase)                        | Accepted    | `core/supabase.py`, all DB access                  |
| [002](adrs/ADR-002-server-side-business-logic.md)                 | Server-Side Business Logic                   | **Partial** | `core/gate_registry.py` done; export/SM pending    |
| [003](adrs/ADR-003-llm-service-hardening.md)                      | LLM Service Hardening                        | **Partial** | Phase 1 done (retry/validation); Phase 2-3 pending |
| [004](adrs/ADR-004-qa-devops-infrastructure.md)                   | QA/DevOps Infrastructure                     | **Partial** | pytest active; Playwright deferred (WS-H)          |
| [005](adrs/ADR-005-scope-expansion.md)                            | Scope Expansion                              | Accepted    | `services/evidence_retrieval.py`, `web_search.py`  |
| [006](adrs/ADR-006-harness-architecture.md)                       | Backend Harness (Pydantic AI + MCP + Skills) | Accepted    | Future-facing; implementation pending              |
| [007](adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md) | TC-Only Explore; PC/SF in Create             | Accepted    | `agents/analyst.py`, `triz_solver.py`              |


---

## WBS (VibeCoding 16)

### Primary Plan

**[E3--wbs-development-plan](E3--wbs-development-plan.md)** — 主 WBS v2.1（0→1 模組結構 1.0–7.0；1,280h baseline；~93% complete）

### Feature Workstreams (WS-D..H)

詳見 [wbs-workstreams/README.md](wbs-workstreams/README.md)


| WS                                                                  | 範圍                              | 完成度      |
| ------------------------------------------------------------------- | ------------------------------- | -------- |
| [WS-D](wbs-workstreams/WS-D--triz-layered-drilldown-development.md) | TRIZ 分層 L1/L2/L3 (Create Tab ①) | 88.6%    |
| [WS-E](wbs-workstreams/WS-E--subsystem-interface-development.md)    | 子系統介面 (Create Tab ②)            | Draft    |
| [WS-F](wbs-workstreams/WS-F--tc-to-multipc-decomposition.md)        | TC→多 PC 分解 (Explore)            | Draft    |
| [WS-G](wbs-workstreams/WS-G--l3-sf-parallel-check.md)               | L3 Su-Field 平行旁路                | Skeleton |
| [WS-H](wbs-workstreams/WS-H--playwright-e2e-followup.md)            | Playwright E2E 補測               | Skeleton |


---

## Process Documents


| Doc                                                                           | Purpose                                |
| ----------------------------------------------------------------------------- | -------------------------------------- |
| [VC00--workflow-manual](VC00--workflow-manual.md)                             | 雙模式流程治理 (Full Process / Lean MVP × 5D) |
| [VC01--development-workflow-cookbook](VC01--development-workflow-cookbook.md) | 開發流程總覽 (Planning → QA × 5D)            |


---

## Relocated Files (Historical)

> - `E3x--methodology-overview` → `[_domain-knowledge/DK-01~04](../_domain-knowledge/DK-00--index.md)`
> - `E3x--wbs-development-plan v1.0` → `[_superseded/](../_superseded/E3x--wbs-development-plan-v1.md)` (被 v2.1 取代)
> - `E3x--first-principles-analysis` → `[00-discover/](../00-discover/E3x--first-principles-analysis.md)`
> - `E2x--wbs-`* (3 份) → 已刪除 (2026-04-21，內容已在 WBS v2.1 中)

