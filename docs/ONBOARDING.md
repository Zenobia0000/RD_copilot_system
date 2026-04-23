# RD Design Copilot — 新人入門指南

> **版本**: v1.0 | **日期**: 2026-04-23  
> **目標讀者**: 新加入團隊的工程師（BE / FE / QA / Data）  
> **預期時間**: 3 天內建立完整專案心智模型

---

## 這個專案在做什麼？

**一句話**：AI 驅動的早期概念設計決策平台，幫 RD 工程師用 TRIZ/SCAMPER 發散解法、用 KT 決策分析收斂、用證據驅動的 8-Gate 流程確保品質。

**解決的痛點**：
- RD 設計初期架構級 rework 3-5 次/專案 → 目標 ≤2
- 設計審查 3-4 小時 → 目標 ≤2 小時
- 假設驗證覆蓋 <30% → 目標 ≥80%

**技術棧**：FastAPI + Supabase + React 18 + TypeScript + Anthropic Claude + Tavily API

---

## Day 1：理解「為什麼」

先不碰程式碼。用 1-2 小時讀完這三份文件，建立全局觀。

### 1. 專案使命與目標

**讀**: [`docs/01-define/E2--statement-of-work.md`](01-define/E2--statement-of-work.md)  
**重點看**: Mission、量化 KPI（5 個）、目標使用者（RD / PM / QA / 製造）、技術棧選型  
**讀完你會知道**: 這個產品要解什麼問題、成功長什麼樣子

### 2. 使用者怎麼走完一個任務

**讀**: [`docs/01-define/E3--system-interaction-flow.md`](01-define/E3--system-interaction-flow.md)  
**重點看**: §1 旅程總覽圖 + §2 Scenario 1 序列圖（Forward TRIZ 解矛盾的完整流程）  
**讀完你會知道**: 8 個步驟的順序、每步哪個 Agent 負責、RD 在哪裡介入

### 3. 專案進度與你的位置

**讀**: [`docs/01-define/E3--wbs-development-plan.md`](01-define/E3--wbs-development-plan.md)  
**重點看**: §2 WBS 樹狀結構（8 個模組）+ §4 進度摘要（跳過任務細節表）  
**讀完你會知道**: 哪些做完了、哪些在做、你的工作落在哪個模組

---

## Day 2：理解「做什麼」

用 2-3 小時讀架構骨幹，知道系統怎麼組裝的。

### 4. 四個 AI Agent 各做什麼

**讀**: [`docs/01-define/E3--ai-agent-detailed-design.md`](01-define/E3--ai-agent-detailed-design.md)  
**重點看**: §11.1 Agent 角色表 + §11.2 自動化對照表 + §11.5.4 API Endpoints 表  
**讀完你會知道**: Analyst / TRIZ Solver / Evaluator / Knowledge 四個 Agent 的職責邊界

### 5. 18 個頁面怎麼走

**讀**: [`docs/02-design/E5x--frontend-information-architecture.md`](02-design/E5x--frontend-information-architecture.md)  
**重點看**: §3 資訊架構總覽（路由樹）+ §5 導航結構 + §6 頁面規格（掃過表格即可）  
**讀完你會知道**: URL 怎麼組、每個頁面對應哪個 Phase、sidebar 步驟順序

### 6. 後端有哪些端點

**讀**: [`docs/02-design/E5--api-design-specification.md`](02-design/E5--api-design-specification.md)  
**重點看**: §7 全部 Router 表（§7.1~§7.14），只看表格不需讀細節  
**讀完你會知道**: 前端呼叫後端的完整 API 地圖

### 7. 36 張表的關係

**讀**: [`docs/01-define/diagrams/E4--erd.md`](01-define/diagrams/E4--erd.md)  
**重點看**: ER 圖 + 6 個語意分群（Core / Problem / Exploration / Solution / Review / Knowledge）  
**讀完你會知道**: 寫 query 時的資料地圖

---

## Day 3：理解「怎麼做」

用 1-2 小時理解核心方法論，這是本專案最獨特的部分。

### 8. TC/PC/SF 是層次不是分類

**讀**: [`docs/02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md`](02-design/specs/triz/E5x--triz-layered-drilldown-optimization.md)  
**重點看**: §1 背景（TC=現象層 / PC=本質層 / SF=結構層）+ §2 五個邏輯謬誤（前 5 頁）  
**讀完你會知道**: 為什麼系統用 L1→L2→L3 drill-down 而不是 TC/PC/SF 三選一

### 9. Explore 只做 TC、Create 派生 PC/SF

**讀**: [`docs/01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md`](01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)  
**重點看**: 全文（2 頁，很短）  
**讀完你會知道**: 矛盾識別為什麼只產出 TC、PC/SF 在 Create 階段怎麼自動派生

### 10. 最新架構方向：Auto-TRIZ v2

**讀**: [`docs/01-define/adrs/ADR-008-auto-triz-v2-integration.md`](01-define/adrs/ADR-008-auto-triz-v2-integration.md)  
**重點看**: Decision D1-D5 + Consequences  
**讀完你會知道**: FA / OZ-OT / SIM / CCI / Evidence Registry 是什麼、為什麼要加

---

## 按角色加讀

三天讀完上面 10 份後，根據你的角色再深入：

### 後端工程師 (BE)

| 優先 | 文件 | 理由 |
|------|------|------|
| 必讀 | [`specs/modules/analyst.md`](02-design/specs/modules/analyst.md) | 你要寫的 Agent — 14 個 spec 的 DbC 契約 |
| 必讀 | [`specs/modules/triz-solver.md`](02-design/specs/modules/triz-solver.md) | L1/L2/L3 + SIM + CCI 的 DbC 契約 |
| 必讀 | [`specs/modules/evidence-registry.md`](02-design/specs/modules/evidence-registry.md) | 新的 cross-cutting service 契約 |
| 必讀 | [`adrs/ADR-001-baas-first-architecture.md`](01-define/adrs/ADR-001-baas-first-architecture.md) | 理解 Supabase BaaS-first — 前端直連 DB、後端只管 AI |
| 參考 | [`specs/modules/E5x--module-spec-index.md`](02-design/specs/modules/E5x--module-spec-index.md) | 8 個 Agent 的完整索引 |

### 前端工程師 (FE)

| 優先 | 文件 | 理由 |
|------|------|------|
| 必讀 | [`E5x--frontend-architecture.md`](02-design/E5x--frontend-architecture.md) | 分層規則、hooks 結構、Context、設計系統 |
| 必讀 | [`specs/ux/E5x--create-ux-spec.md`](02-design/specs/ux/E5x--create-ux-spec.md) | Create 頁 7-step accordion + Layered 卡片 UX（最複雜的頁面） |
| 參考 | [`specs/explore/E5x--subsystem-persistence-policy.md`](02-design/specs/explore/E5x--subsystem-persistence-policy.md) | 誰寫哪張表 — 前端寫 subsystems、後端寫 overrides |

### QA 工程師

| 優先 | 文件 | 理由 |
|------|------|------|
| 必讀 | [`E5x--bdd-scenarios.md`](02-design/E5x--bdd-scenarios.md) | Gherkin 場景 — 你的驗收基準 |
| 必讀 | [`specs/review-templates/E5x--must-rulebook-template.md`](02-design/specs/review-templates/E5x--must-rulebook-template.md) | 6 個 MUST 條件怎麼判 |
| 參考 | [`E7x--e2e-manual-scripts/`](02-design/E7x--e2e-manual-scripts/) | E2E 手測腳本範例 |

### Data 工程師

| 優先 | 文件 | 理由 |
|------|------|------|
| 必讀 | [`adrs/ADR-001-baas-first-architecture.md`](01-define/adrs/ADR-001-baas-first-architecture.md) | Supabase 架構決策 + RLS 策略 |
| 必讀 | [`specs/explore/E5x--subsystem-persistence-policy.md`](02-design/specs/explore/E5x--subsystem-persistence-policy.md) | 寫入權責劃分 |
| 參考 | [`specs/explore/E5x--tc-to-multipc-type-alignment.md`](02-design/specs/explore/E5x--tc-to-multipc-type-alignment.md) | Pydantic ↔ TypeScript 欄位對照 |

---

## 不需要讀的

| 跳過 | 理由 |
|------|------|
| `VC00--workflow-manual.md` / `VC01--development-workflow-cookbook.md` | 流程管理框架，做事時查就好 |
| `E6x--schema-codegen-workflow.md` | codegen pipeline，實際操作時再看 |
| `E5x--project-structure-guide.md` | 打開 IDE 就懂 |
| `specs/E5x--file-dependencies.md` / `E5x--class-relationships.md` | PR review 時再查 |
| `docs_harness/*` | 硬體工程執行文件，軟體團隊不需要 |
| ADR-002 ~ ADR-006 | 歷史決策，遇到相關問題時再翻 |
| `_domain-knowledge/*` | 方法論原理，好奇時再讀（非 onboarding 必要） |

---

## 快速開發環境

```bash
# 後端
cd backend
cp .env.example .env          # 填入 SUPABASE_URL + ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cp .env.example .env          # 填入 VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
npm install
npm run dev                   # http://localhost:5173
```

**API 文檔**: 後端啟動後訪問 `http://localhost:8000/docs`（OpenAPI 自動生成）

---

## 有問題找誰？

| 問題類型 | 找 | 文件 |
|---------|------|------|
| 架構決策 / 為什麼這樣設計 | ARCH | `01-define/adrs/` |
| Agent 行為 / prompt 設計 | BE Lead | `02-design/specs/modules/` |
| UI/UX 互動 | FE Lead | `02-design/specs/ux/` |
| DB schema / migration | Data Lead | `01-define/diagrams/E4--erd.md` |
| Gate 驗收標準 | QA Lead | `02-design/E5x--bdd-scenarios.md` |
| 專案進度 / 優先級 | PM | `01-define/E3--wbs-development-plan.md` |
