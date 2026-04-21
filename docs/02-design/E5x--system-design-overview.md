# E5 — System Design Overview (TR4 Gate 主文檔)

> **文件版本**：v1.0
> **最後更新**：2026-04-15
> **狀態**：Active（取代散落 specs 的頂層架構）
> **Gate**：TR4（Design Review）
> **模板對應**：VibeCoding **06** (API Design Specification) + **12** (Frontend Architecture Specification) 混合精神；12-style 的 IA 指引另見 [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)
> **上游**：[`01-define/E3--architecture-and-design.md`](../01-define/E3--architecture-and-design.md)
> **下游**：[`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md)、[`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/)

---

## §1 設計階段目標與範圍

02-design (TR4–TR5) 的核心問題：**「What exactly do we build?」**

| 目標 | 交付物 | Gate |
|------|--------|------|
| 凍結前端 IA（Information Architecture）與使用者流程 | [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) | TR4 |
| 凍結後端 API 契約 + schema | 本文件 §3 + [`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md) | TR4 |
| 凍結各功能模組的技術規格 | [`specs/triz/`](specs/triz/)、[`specs/explore/`](specs/explore/) | TR4 |
| 建立 review / QA 模板 | [`specs/review-templates/`](specs/review-templates/) | TR5 |
| 確保 E2E 可測 | [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/) | TR5 |

**不在範圍內**（屬於 01-define 或 03-develop）：

- 系統層架構圖 / ADR（→ `01-define/E3--architecture-and-design.md`）
- WBS 任務分解（→ `01-define/E3--wbs-development-plan.md` + wbs-workstreams/）
- 實作細節與單元測試（→ 03-develop）

---

## §2 前端 IA ↔ 後端 API 對應

```
┌──────────────────────────── Frontend (React 19) ────────────────────────────┐
│                                                                              │
│   /create  ──┬── Tab ① TRIZ 矛盾解        ──┐                              │
│              ├── Tab ② 子系統 / 介面契約  ──┤                              │
│              ├── Tab ③ 決策中心 (Phase B)  ─┤                              │
│              └── Tab ④ 三層樹 / 六維契約   ─┤                              │
│                                             │                                │
│   /explore ──┬── TC→多 PC 分解 (L2)      ──┤   API adapter                  │
│              └── L3 Su-Field 平行旁路     ──┤   (camelCase ↔ snake_case)    │
│                                             │                                │
│   /review  ──┬── MUST Rulebook           ──┤                                │
│              ├── Pre-CAD Review          ──┤                                │
│              └── Evidence Matrix / Risk   ──┘                                │
│                                              │                               │
└──────────────────────────────────────────────┼───────────────────────────────┘
                                               ▼
┌──────────────────────────── Backend (FastAPI) ──────────────────────────────┐
│                                                                              │
│   POST  /triz/solve-layered         → LayeredTrizSolution                    │
│   POST  /triz/phase-b               → 跨矛盾交叉檢查                         │
│   POST  /scamper/subsystem-suggestions → SuggestedSubsystem[]                │
│   PATCH /subsystems/{id}            → RD edit / confirm                      │
│   POST  /explore/tc-decompose       → MultiPC tree                           │
│   POST  /export, /knowledge/writeback, /scamper/feedback                     │
│   ...                                                                        │
│                                                                              │
│   Pydantic schemas (single source of truth)                                  │
│     → schemas.py ──pydantic2ts──▶ src/types/generated/*.ts                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

完整端點列表與 ADR 決策見 `01-define/E3--architecture-and-design.md` 附錄；本設計階段僅鎖定**契約形狀**與**IA 綁定**。

---

## §3 Specs 導航表

### §3.1 TRIZ 解矛盾子系統

| Spec | 解決的問題 | 對應前端區塊 | 對應後端端點 |
|------|-----------|-------------|-------------|
| [`specs/triz/E5x--triz-layered-drilldown-optimization.md`](specs/triz/E5x--triz-layered-drilldown-optimization.md) | TC/PC/SF 從「互斥分類」改為「分層 drill-down」 | Create Tab ① 區塊 B | `/triz/solve-layered` |
| [`specs/triz/E5x--triz-multi-solution-adoption-strategy.md`](specs/triz/E5x--triz-multi-solution-adoption-strategy.md) | 多解併行時的合併 / 擇一 / drill-down 決策框架 | Create Tab ① 區塊 C + Tab ③ layered 卡片 | `/triz/phase-b` |

### §3.2 子系統 / Explore 子系統

| Spec | 解決的問題 | 對應前端區塊 | 對應後端端點 |
|------|-----------|-------------|-------------|
| [`specs/explore/E5x--tc-to-multipc-type-alignment.md`](specs/explore/E5x--tc-to-multipc-type-alignment.md) | Backend Pydantic ↔ Frontend TS 欄位對照 | 全域 adapter 層 | (型別契約) |
| [`specs/explore/E5x--subsystem-persistence-policy.md`](specs/explore/E5x--subsystem-persistence-policy.md) | 凍結「誰寫 `subsystems` 表」，防雙寫競態 | Create Tab ② useSubsystemSuggestion | `/scamper/subsystem-suggestions` |
| [`specs/explore/E5x--three-tier-tree-review-checklist.md`](specs/explore/E5x--three-tier-tree-review-checklist.md) | 三層樹 + 六維契約 PR review 清單 | Create Tab ④ | (review gate) |

### §3.3 UX / IA

| Spec | 解決的問題 |
|------|-----------|
| [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) | Create 頁面完整 UX 規格（Tab ①–④、區塊 A/B/C、v8.1 Phase A 退役） |

### §3.4 Review Templates

| Spec | 觸發階段 |
|------|---------|
| [`specs/review-templates/E5x--must-rulebook-template.md`](specs/review-templates/E5x--must-rulebook-template.md) | Step 5e / Gate C (CAD) |
| [`specs/review-templates/E5x--pre-cad-review-template.md`](specs/review-templates/E5x--pre-cad-review-template.md) | Gate P (Pre-CAD) |
| [`specs/review-templates/E5x--evidence-matrix-risk-register-template.md`](specs/review-templates/E5x--evidence-matrix-risk-register-template.md) | Step 6 / 6e / 7 (KT) |

### §3.5 Workflow 基建

| Spec | 範疇 |
|------|------|
| [`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md) | Pydantic → TS 自動同步 (pydantic2ts) |
| [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/) | 手測腳本（Gate 1.1 → PG3） |

---

## §4 與 E3 (01-define) 架構的對應

| E3 架構單元 (01-define) | 本階段設計交付物 |
|------------------------|----------------|
| §Appendix A — SA 容器圖 | §2 IA↔API 對應 + `specs/ux/E5x--create-ux-spec.md` |
| §Appendix B — 資料模型 | `E6x--schema-codegen-workflow.md` + `specs/explore/E5x--tc-to-multipc-type-alignment.md` |
| §Appendix C — UC1–UC7 | `specs/explore/E5x--subsystem-persistence-policy.md` + `E7x--e2e-manual-scripts/` |
| §Appendix D — TRIZ Solver | `specs/triz/*` |
| §Appendix E — Subsystem Discovery | `specs/explore/*` + `specs/ux/E5x--create-ux-spec.md` Tab ② |

對應的 **WBS 任務分解** 已歸檔至 DEFINE：
- 主軸 (release): [`01-define/E3--wbs-development-plan.md`](../01-define/E3--wbs-development-plan.md)
- 功能軸 (feature): [`01-define/wbs-workstreams/`](../01-define/wbs-workstreams/README.md) → WS-D..H

---

## §5 TR4 Gate 通過條件

### §5.1 必要條件 (Blocker)

- [x] 所有 Create Tab 的 IA 已凍結於 `specs/ux/E5x--create-ux-spec.md` (v8.1 Phase A 退役後)
- [x] TRIZ 分層 drill-down 架構凍結於 `specs/triz/E5x--triz-layered-drilldown-optimization.md` v1.0
- [x] 多解採納策略凍結於 `specs/triz/E5x--triz-multi-solution-adoption-strategy.md` v1.1 (M1–M6)
- [x] 子系統持久化邊界凍結於 `specs/explore/E5x--subsystem-persistence-policy.md`
- [x] 型別對照表 (BE ↔ FE) 更新至 2026-04-09 版
- [x] Review Checklist (三層樹 + 六維) 可逐項勾選
- [x] MUST / Pre-CAD / Evidence 模板齊備

### §5.2 品質條件 (Quality Gate)

- [x] 前端 IA 與後端 API 一對一可追溯（§2 對應表無孤立節點）
- [x] 每個 Spec 都聲明版本、日期、上游依賴
- [ ] E6 pydantic2ts 工具鏈接上（當前 pre-codegen，Stage 2 待排）
- [ ] E7 E2E Playwright 覆蓋 Gate 1.1 → PG3 (WS-H, Skeleton)

### §5.3 TR5 進入條件（Design → Develop 橋接）

- 03-develop 的模組實作必須回引本文件某一 spec
- 任何偏離 spec 的實作 → 開 ADR 於 `01-define/adrs/`，並回頭更新本 §3 導航表

---

## §6 VibeCoding 模板對齊度

| VibeCoding 模板 | 本階段對應 | 狀態 |
|---------------|-----------|------|
| **06** API Design Specification | 本文件 §2 + §3 + E3 §Appendix B | Partial (詳細端點表在 E3) |
| **07** Module Specification & Tests | `specs/triz/*` + `specs/explore/*` + Vitest suites | Active |
| **08** Project Structure Guide | 本文件 §3 導航表 | Active |
| **12** Frontend Architecture Specification | `specs/ux/E5x--create-ux-spec.md` + §2 | Active |
| **17** Frontend Information Architecture | `specs/ux/E5x--create-ux-spec.md` Tab 結構 | Active |

---

**Last reviewed**: 2026-04-15 · **Next review**: TR5 進入前
