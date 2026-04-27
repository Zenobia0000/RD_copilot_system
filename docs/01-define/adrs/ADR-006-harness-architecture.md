# ADR-006: Backend Harness 架構 — Pydantic AI + MCP + Skills

- **Status**: Accepted & Implemented (2026-04-24)
- **Date**: 2026-04-15 (proposed) → 2026-04-22 (deferred) → 2026-04-24 (implemented)
- **Deciders**: RD + Development Team
- **Supersedes**: ADR-002（Gate 實作策略）、ADR-003 Phase 2-3（prompt 外部化 + model routing）
- **Related**: ADR-008（Auto-TRIZ v2，建立在 Harness 之上）

## Implementation Status (2026-04-27)

> **All phases (Phase 0-5) implemented.** Commit `3ce5738` (2026-04-24) 完成 Harness 架構全部階段。
>
> 已實作模組（`backend/app/harness/`）：
> - `agent_base.py` — `HarnessAgent[Deps, Output]` typed agent wrapper (Phase 2a)
> - `model_adapter.py` — Pydantic AI `Model` wrapping `_call_provider` (Phase 2a)
> - `prompt_assembler.py` — Context engineering with cache budget (Phase 2a)
> - `tool_registry.py` — Decorator-based tool registration + MCP spec gen (Phase 1)
> - `solver_registry.py` — Pluggable solver dispatch (Phase 3)
> - `orchestrator.py` — L1→Critic→L2→L3 pipeline coordinator (Phase 3)
> - `skill_loader.py` — Filesystem-based skill discovery (Phase 4)
> - `mcp_server.py` — FastMCP stdio server (Phase 1)
> - `mcp_client.py` — External MCP tool consumer (Phase 5)
>
> 已實作 Skills（`backend/app/skills/`）：
> - `triz_39_parameters/` — 39 工程參數知識庫
> - `triz_76_standards/` — 76 標準解知識庫
> - `triz_separation_principles/` — 分離原理知識庫
>
> Agents 已全部重構為 `HarnessAgent` 封裝。*(v9: `scamper_feedback.py` 已移除)*

## Context

截至 2026-04-15，backend (`/backend/app/`) 採「FastAPI + 直接函式呼叫」的 agent 架構：

- 18 個 router 直接呼叫 `app/agents/*.py`（analyst / triz_solver / evaluator / knowledge / ~~anti_anchor~~ / subsystem_decomposer） *(v9: scamper 已移除；Anti-Anchor 已退役，併入 TRIZ L1 跨域去錨定)*
- LLM 呼叫集中於 `app/agents/base.py`（`call_llm_json` / `call_llm_structured` / `_call_provider`），已支援 Anthropic / OpenAI / Azure / Gemini / Qwen 多 provider + 指數退避重試
- 已有兩個小型 registry pattern：`core/gate_registry.py` 與 `core/evaluator_registry.py`（decorator 註冊）
- `tools/triz_kb.py` 以靜態檔案 + `@lru_cache` 注入 prompt 上下文（不是 function-calling）
- `langgraph` 列於 `pyproject.toml` 但**未使用**
- TRIZ solver (`solve_triz_layered`) 是硬編碼的 L1→L2→L3 線性 pipeline
- **無** MCP server / client、**無** agent Protocol / ABC、**無** Claude Skills 目錄

### 問題陳述

三個需求正在浮現：

1. **外部工具整合**：要讓 Claude Code、其他 LLM client 能驅動我們的 TRIZ solver（MCP server 方向），同時要能消費 Tavily / Figma / Supabase 等 MCP 工具（MCP client 方向）。
2. **第三方解題器插件**：QFD、Taguchi、Axiomatic Design、以及 TRIZ 變體應能以「放入目錄 + 重啟」的方式擴充，不改核心 code。
3. **Skills 生態對齊**：Anthropic 2025 Q4 推出的 Skills 機制（filesystem-based，`SKILL.md` 漸進式揭露）是未來可預期的標準；若架構不對齊，日後遷移成本會暴增。

當前架構三者皆未支援。

### 架構選型研究

研究四大 agent harness 原型（詳見 `/home/os-sunnie.gd.weng/.claude/plans/snoopy-dazzling-marble.md` 研究段）：

| Archetype | 代表 | 本系統適配度 |
|---|---|---|
| Event-loop harness | Claude Agent SDK / Aider | 高（但 Anthropic-locked，與 FastAPI 服務化矛盾） |
| Graph harness | LangGraph | 中（pipeline 僅 5 節點，框架重量過高） |
| Handoff / multi-agent | OpenAI Agents SDK / CrewAI | 低（無明顯 role 分離需求） |
| Code-agent | Smolagents | 低（沙箱風險 > 收益） |

## Decision

**採用 Hybrid 架構：Pydantic AI spine + Skills 目錄約定 + MCP 雙向**

### 核心決策

1. **Orchestration spine**：使用 **Pydantic AI** 作為 agent 封裝層
   - 與現有 Pydantic v2 / FastAPI idiom 一致
   - 提供 typed `Agent[Deps, Output]`，支援 dependency injection
   - 模型無關（model-agnostic），透過自訂 `Model` adapter 接回現有 `_call_provider`

2. **Pipeline 形狀**：**手寫線性 orchestrator**（非 LangGraph）
   - TRIZ L1→L2→L3 僅 5 節點，圖框架過重
   - 每層完成即 upsert 到 Supabase（已於 2026-04-15 修復的 `_persist_layered_solution`）
   - 未來若需 checkpoint/HITL，Pydantic AI agent 可直接塞入 LangGraph node，遷移成本低

3. **Plugin surface**：**Skills 目錄 + Solver Registry**
   - `backend/app/skills/*/SKILL.md`：第三方 skill bundles（對齊 Anthropic Skills 規範）
   - `backend/app/solvers/*/`：內建與插件 solver（如 `triz_layered`、`qfd`、`taguchi`）
   - 啟動時掃描並註冊，無需改核心 code

4. **MCP 雙向整合**：
   - **Server 側**：`harness/mcp_server.py` 把 registered tools / agents 曝露為 MCP，Claude Code 可直接驅動
   - **Client 側**：`harness/mcp_client.py` 讀 `.mcp.json` 掛載外部 MCP tools

5. **LLM Provider 策略**：**保留多 provider dispatch**
   - 不鎖 Anthropic
   - `harness/model_adapter.py` 包現有 `_call_provider`，保留 retry + fallback chain

### 目標目錄結構

```
backend/app/
├── harness/                  ← NEW
│   ├── agent_base.py         ← HarnessAgent[Deps, Output]
│   ├── model_adapter.py      ← PydanticAI Model → _call_provider
│   ├── tool_registry.py      ← @register_tool + MCP spec 產生
│   ├── solver_registry.py    ← @register_solver
│   ├── skill_loader.py       ← 掃 skills/*/SKILL.md
│   ├── mcp_server.py         ← 曝露 tools/agents 為 MCP
│   ├── mcp_client.py         ← 消費外部 MCP
│   └── orchestrator.py       ← 手寫線性管線
├── agents/                   ← 轉寫為 HarnessAgent
├── solvers/                  ← NEW 可插拔 solver
├── skills/                   ← NEW Skill bundles
└── main.py                   ← lifespan 啟動 skill_loader + mcp_server
```

### 分階段執行（≈6 phases）

詳細計畫見 `docs/02-design/specs/backend-harness/E5x--harness-refactor-plan.md`。要點：

- **Phase 0**：加入 `pydantic-ai` + `mcp` 依賴、建立 `harness/` 空模組（無行為改變）
- **Phase 1**：Tool registry + MCP server 殼；`triz_kb` 工具曝露 MCP
- **Phase 2**：`HarnessAgent` base + model adapter；**全 agent 一次轉**（使用者決策）
- **Phase 3**：Orchestrator + solver_registry；`/triz/solve-layered` 改走 registry
- **Phase 4**：Skill loader + `ebike_reference_library` 範例
- **Phase 5**：MCP client + doc 更新

## Consequences

### 正面

- **Plugin 生態就緒**：第三方 solver / skill 以檔案放入即生效
- **Claude Code 原生可驅動**：RD 可以從 Claude Code 直接呼叫我們的 TRIZ matrix、Separation Principles
- **Typed end-to-end**：PydanticAI + Pydantic v2 消除 ad-hoc JSON parsing
- **與現有 registry pattern 一致**：學習曲線低
- **不鎖 Anthropic**：multi-provider dispatch 保留，ADR-003 精神延續
- **未來遷移 LangGraph 成本低**：PydanticAI agent 可直接作為 graph node

### 負面

- **新依賴**：`pydantic-ai` (<1.0，API 尚不穩定)、`mcp` SDK
  - 對策：harness layer 做 adapter，版本鎖 minor，日後可替換
- **學習曲線**：團隊需熟悉 Pydantic AI idiom
  - 對策：ADR 附 30 分鐘 onboarding snippet；thin wrapper 策略讓舊 entrypoint 並行
- **Phase 2 一次轉全 agent** 風險較高
  - 對策：feature flag `USE_HARNESS_ORCHESTRATOR` 並行一週；舊函式保留為 thin wrapper 轉呼新 agent
- **MCP SDK + Anthropic SDK 版本相容性** 未知
  - 對策：獨立 venv 驗證；若衝突則以 subprocess 起 MCP server

### 中性

- TRIZ solver 輸出格式與 migration 010 欄位保持不變（`L1Surface` / `L2RootCause` / `L3StructuralCheck` Pydantic 模型複用）
- 前端 React Query 層 **不動**（harness 純 backend 事項）
- Gate / Evaluator registry **不動**（已符合 registry 範式）

## Alternatives Considered

### A. 純 LangGraph 重構（拒絕）
- 理由：pipeline 僅 5 節點，圖框架 ceremony 過重；LangChain 版本歷史性 churn 對小團隊維護不利
- 保留路徑：未來若 TRIZ pipeline 擴展為真正圖狀（多 solver 交叉、HITL、checkpoint/resume 成為剛需）再遷移

### B. 全面擁抱 Claude Agent SDK（拒絕）
- 理由：Anthropic-locked 與 ADR-003 多 provider 精神衝突；FastAPI 服務化下 subagent 的 context 管理與延遲可預測性是硬傷
- 保留部分：Skills 目錄約定是 Anthropic 精神，本 ADR 採納

### C. 維持現狀 + 外掛 MCP server（拒絕）
- 理由：沒解決 plugin 擴充與 agent 標準化；短期省事，長期技術債
- 保留部分：短期 Phase 0-1 事實上就是此方案

## Related

- `/home/os-sunnie.gd.weng/.claude/plans/snoopy-dazzling-marble.md`：本決策背後的完整研究（四大 harness 架構比較 + 決策矩陣）
- `docs/02-design/specs/backend-harness/E5x--harness-refactor-plan.md`：分階段實作計畫
- `backend/app/agents/base.py::_call_provider`：多 provider dispatch（將被 model_adapter 包裝）
- `backend/app/agents/triz_solver.py::_persist_layered_solution`：2026-04-15 新增的 Supabase upsert（將搬入 orchestrator）
- `backend/app/core/gate_registry.py`、`core/evaluator_registry.py`：既有 registry pattern，本 harness 沿用
- ADR-003 Phase 3：LLM 介面層抽象，部分由本 ADR 的 `model_adapter` 實現
