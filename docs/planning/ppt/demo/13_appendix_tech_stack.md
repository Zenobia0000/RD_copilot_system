# 13 — Appendix · 技術深度補充

> **用途**：技術受眾 Q&A backup slide。**不是 12 分鐘主流程的一部分**，普通人讀者可跳過。
> **觸發時機**：當有人問「你們用什麼技術？」「跟 LangChain / LlamaIndex 比？」「資料怎麼存？」時翻到這頁。

---

## Slide 標題

**System Design 全景：Tech Stack + AI Agent Patterns + Data Models**

---

## Speaker Notes

> 這頁是給有興趣深入的技術同事準備的。三個面向：技術棧、AI agent 設計模式、資料模型。如果你是 PM 或主管，這頁細節可略過 — 重點是後面的 reference 文件清單，需要時可以回頭查。

---

## A. 全棧架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                      🖥️  Frontend Layer                          │
│  ⚛️  React 18 + TypeScript                                       │
│  🎨 shadcn/ui · 🎯 React Query · 🛣️  React Router               │
│  📊 Mermaid (流程圖) · 🌳 D3 (DAG 視覺化)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      ⚡ Backend Layer                            │
│  🐍 Python 3.10+ · ⚡ FastAPI · 🔄 Pydantic v2                   │
│  🤖 Anthropic SDK · 🧪 pytest · 📋 Loguru                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
┌───────────▼──────┐ ┌───────▼────────┐ ┌────▼────────────────────┐
│ 🧠 LLM Layer     │ │ 📚 Knowledge   │ │ 🗄️  Data Layer           │
│ 🔵 Claude Opus   │ │   Base (KB)    │ │ 🐘 PostgreSQL (Supabase) │
│ 🔵 Claude Sonnet │ │ 📐 Matrix      │ │ 🔐 Supabase Auth        │
│ 💾 Prompt Cache  │ │ 🧬 Principles  │ │ 📂 File Storage          │
│ 🔧 Tool Use      │ │ 🔧 SF 76 std   │ │ 📊 JSON state files      │
│ 🧬 Struct Output │ │ 📈 TESE lines  │ │ 🗂️  Evidence Registry    │
└──────────────────┘ └────────────────┘ └─────────────────────────┘
```

---

## B. AI Agent 設計模式（本系統採用的模式）

| Pattern | 應用位置 | 解決的問題 |
|:--------|:--------|:-----------|
| 🎯 **ReAct** (Reason + Act + Observe) | 每個 skill 內部迴圈 | LLM 結構化推理 |
| 🤝 **Supervisor-Worker** | `triz-router` ↔ `triz-analyst` | 任務分派與結果合併 |
| 🌐 **Map-Reduce** | 多 TC 並行求解 | 並行加速 + context 隔離 |
| 🔍 **RAG** | TRIZ KB 查詢 | 反幻覺、知識駐留 |
| 🛠️ **Tool Use / Function Calling** | 所有檔案/KB/agent 互動 | LLM 操作外部世界 |
| 🧬 **Structured Output** | TC/PC/SF schema | 可解析、可審計 |
| 📌 **Context Engineering** | Skill loader 動態裁剪 | 控制 context 雜訊 |
| 📊 **Stateful Memory** | JSON state files | 跨 session 持久化 |
| 🔁 **Plan-Execute-Reflect** | `triz-verify` 4-Q check | 自我驗證與修正 |
| 🗂️ **Provenance Tracking** | Evidence Registry | 結論可回查 |

---

## C. 資料模型（13 Core Entities）

```
Problem ─┬─→ TC (Technical Contradiction)
         │      │
         │      ├─→ PC (Physical Contradiction)
         │      │     │
         │      │     └─→ Px (Parameter)
         │      │           ├─ OZ (Operating Zone)
         │      │           └─ OT (Operating Time)
         │      │
         │      └─→ SF (Substance-Field)
         │            └─→ Solution
         │
         └─→ Evidence Registry
                │
                └─→ Claim (with confidence: HIGH/MEDIUM/LOW)

ComplexityCheck (CCI) ──→ Q1 Structural · Q2 Energy
                          Q3 Cognitive  · Q4 Evolution

SIM Matrix (Multi-TC Conflict Detection)
└─ {+1 reinforce, 0 neutral, -1 conflict}
```

完整 schema：`docs/methodology/DK-04--data-model-and-gate.md`

---

## D. Skill Catalog（13 Skills 完整清單）

### 🧪 TRIZ 引擎（6 Skills · Phase 0-3）

| Skill | Phase | 職責 | 核心輸出 |
|:------|:------|:-----|:---------|
| `triz-router` | 入口 | 🧭 問題路由（TC / SF-only / 引導）| 路由判定 |
| `triz-scoping` | P0 | 🛰️ 5Why / KT / CECA 問題定向 | 子系統 + TC 假設 |
| `triz-model` | P1 | 🧬 FA + SF 功能建模 | 組件交互圖 + SF 診斷 |
| `triz-contradict` | P2-P3 | ⚗️ TC→PC→SF 推理 + 解法 | 解法卡 + Px |
| `triz-verify` | P3 | ✅ 4-Q 複雜度 + Evidence + CCI | CCI 評分 + Gate P |
| `triz-wi` | P3→TR0 | 📝 WI / MC / ICD 工程文件產出 | 工程交付物 |

### 🏭 TR 引擎（7 Skills · Phase 4-7）

| Skill | Phase | 職責 | 核心輸出 |
|:------|:------|:-----|:---------|
| `tr-gate` | P4-P7 | ✅ Gate Review（TR1-TR10）| Gate 報告 |
| `tr-fea` | P4 | 🧮 FEA 設定輔助 | 材料卡 + 邊界條件 |
| `tr-test` | P5-P6 | 🔬 測試報告產出 | 測試結果 + correlation |
| `tr-dfm` | P6 | 🏭 DFM/DFA 審查 | DFM checklist |
| `tr-sop` | P7 | 🛠️ SOP 草稿產出 | 量產 SOP |
| `tr-spc` | P7 | 📊 SPC/Cpk 計算 | 製程能力指數 |
| `tr-ppap` | P7 | 📦 PPAP 文件包組裝 | 18 項 PPAP |

---

## E. 與業界 Agent Framework 比較

| 維度 | 本系統 | LangChain / LlamaIndex | 一般 ChatGPT Plugin |
|:-----|:-------|:----------------------|:-------------------|
| **業務邏輯位置** | Markdown skills（可審查、可版控）| Python code | Prompt 內 |
| **State 管理** | JSON file（可 git 追蹤）| In-memory / Redis | Session 內 |
| **多 agent 編排** | Skill-driven supervisor-worker | LangGraph / CrewAI | 不支援 |
| **領域知識** | 結構化 TRIZ KB（非僅向量）| Vector store | Prompt 內 |
| **可稽核性** | Evidence Registry + Claim ID | 需自行實作 | 無 |
| **跨 session 接續** | JSON state 自動恢復 | 需自行實作 | Conversation history |

> **設計取向**：harness-first（流程是資料）優於 framework-first（流程是程式碼）— 業務團隊可改流程，不必動程式。

---

## F. Reference Documents（深入閱讀）

| 主題 | 文件 |
|:-----|:-----|
| 全棧架構 + Harness 分層 | `docs/planning/05_architecture.md` |
| API 規格 (FastAPI endpoints) | `docs/planning/06_api_spec.md` |
| 模組設計 + 程式結構 | `docs/planning/07_module_spec.md`, `08_project_structure.md` |
| 前端 IA + 7 頁面流程 | `docs/planning/12_frontend_architecture.md`, `17_frontend_ia.md` |
| 資料模型 + Gate 定義 | `docs/methodology/DK-04--data-model-and-gate.md` |
| 多 Agent Orchestration 設計 | `docs/methodology/DK-03--multi-agent-orchestration.md` |
| TRIZ 機制 (40 原理 / 76 標準解 / 矩陣) | `docs/methodology/DK-02--triz-mechanisms.md`, `knowledge/triz/` |
| RDP-8 流程契約 | `docs/planning/18_flow_contract.md` |
| BDD Feature 規格 | `docs/planning/03_bdd_guide.md` |
| 11 張 UML 推理圖 | `docs/methodology/uml/00-11_*.md` |
| ADR (架構決策記錄) | `docs/planning/04_adr/` |

---

## G. 給技術受眾的 3 個常見問題答覆

**Q1：「為什麼不直接用 LangGraph / CrewAI？」**
> 我們 evaluating 過。核心差別：harness-first 讓業務邏輯（TRIZ 流程、gate 規則）以 markdown 形式存在，工程同事與領域專家都可改；framework-first 把流程鎖在 Python 裡，每次調整都要 dev cycle。對 RD 領域工具，可審查 / 可版控的流程定義價值高於框架彈性。

**Q2：「為什麼用 Claude 而不是 GPT-4 或開源模型？」**
> Claude 的 long context（200K）+ tool use 穩定度 + structured output 在多步驟 agent 場景表現最佳。但底層介面抽象（`triz-router` 不直接 call API），未來換 LLM 不需改流程，只需 swap adapter。

**Q3：「TRIZ KB 為什麼不全部用 vector embedding？」**
> TRIZ 矛盾矩陣是**精確查表**（39×39 確定值），不是相似度檢索。用 vector 反而失去精準度。我們混合策略：結構化資料用 SQL 查表，非結構化案例（過往 session）用 vector retrieve。

---

## H. 簡報結束後可給技術同事的「深入入口」

```
GitHub Repo → docs/methodology/  ← 從這裡開始
              ├─ DK-01 Auto-TRIZ 流程
              ├─ DK-02 TRIZ 機制
              ├─ DK-03 多 agent 編排  ← 推薦先看這份
              ├─ DK-04 資料模型 + Gate
              └─ DK-05 領域底盤
```
