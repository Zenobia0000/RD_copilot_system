# Backend Harness 重構計畫

- **Status**: ✅ Implemented（Phase 0-5 完成，2026-04-24）
- **Date**: 2026-04-15（計畫）→ 2026-04-24（完成）
- **Owner**: Backend Team
- **ADR**: [ADR-006 Harness Architecture](../../../01-define/adrs/ADR-006-harness-architecture.md)
- **Scope**: `backend/app/*`（不動前端、不動 gate/evaluator registry）

## 1. 目的

將 backend 重構為「**Harness 架構**」：

- **Pydantic AI** 作為 agent 封裝 spine
- **MCP** 雙向整合（server 曝露、client 消費）
- **Skills 目錄** + **Solver Registry** 作為插件生態

詳細決策理由見 [ADR-006](../../../01-define/adrs/ADR-006-harness-architecture.md)。

## 2. 使用者決策（2026-04-15）

| 決策點 | 選項 | 理由 |
|---|---|---|
| 架構方案 | Pydantic AI + Skills + MCP | 與 Pydantic v2 idiom 一致、低框架重量 |
| 轉換 scope | **全 agent 一次轉** | 一次痛完，避免兩套 idiom 並行 |
| LLM provider | 保留多 provider dispatch | 延續 ADR-003 精神，不鎖 Anthropic |

## 3. 目標架構

```
backend/app/
├── harness/                       ← NEW：harness 核心
│   ├── __init__.py
│   ├── agent_base.py              ← HarnessAgent[Deps, Output]
│   ├── model_adapter.py           ← PydanticAI Model → _call_provider
│   ├── tool_registry.py           ← @register_tool + MCP spec
│   ├── solver_registry.py         ← @register_solver
│   ├── skill_loader.py            ← 掃 skills/*/SKILL.md
│   ├── mcp_server.py              ← stdio/SSE MCP server
│   ├── mcp_client.py              ← 消費外部 MCP
│   └── orchestrator.py            ← 線性 L1→L2→L3 orchestrator
├── agents/                        ← 大部分已改寫為 harness_call（見下方遷移狀態）
│   ├── analyst.py                 ✅ 全函式 harness_call（含 subsystem 邏輯；~~anti_anchor v10 退役~~，跨域去錨定合併至 TRIZ L1）
│   ├── triz_solver.py             ✅ L1/L2/L3 層透過 HarnessAgent + prompt_assembler
│   ├── triz_critic.py             ✅ harness_call
│   ├── evaluator.py               ✅ harness_call + HarnessAgent
│   ├── knowledge.py               ✅ harness_call
│   ├── knowledge_wb.py            ✅ harness_call
│   ├── scamper_feedback.py        ❌ v9 移除（SCAMPER 已移除）
│   └── base.py                    保留 _call_provider（model_adapter 底層）
├── skills/                        ← NEW Skill bundles（知識型）
│   ├── triz_39_parameters/SKILL.md
│   ├── triz_76_standards/SKILL.md
│   └── triz_separation_principles/SKILL.md
└── main.py                        ← lifespan 啟動 skill_loader + mcp_server
```

## 4. 分階段實作

### Phase 0 — 依賴與骨架（無行為改變）✅ 完成 2026-04-24

**任務**：
- 加入 `pydantic-ai>=0.0.14`、`mcp>=1.0` 到 `backend/pyproject.toml`
- 建立 `backend/app/harness/` 空模組 + `HarnessAgent` Protocol 雛形
- （選擇性）移除未使用的 `langgraph` / `langchain-*`

**驗收**：
- `pytest backend/tests/` 全綠
- 既有 API 無行為改變
- `python -c "from app.harness import HarnessAgent"` 不報錯

### Phase 1 — Tool Registry + MCP Server 殼 ✅ 完成 2026-04-24

**任務**：
- 實作 `harness/tool_registry.py`：`@register_tool(name, description, schema)`
  - 同時產出 MCP tool spec（`mcp.Tool`）
  - 支援 Pydantic model 作為 input/output schema
- 將 `tools/triz_kb.py` 的 `lookup_matrix`、`load_40_principles`、`build_triz_tc_context` 等標記為 tool
- `harness/mcp_server.py`：用 `mcp` SDK 啟動 stdio server，列出並呼叫 registered tools

**驗收**：
- `pytest tests/harness/test_tool_registry.py` 通過
- Claude Code MCP 設定後可呼叫 `lookup_matrix(6, 14)` 拿到 `[35, 10, 21, 16]`
- `python -m app.harness.mcp_server` 可啟動

### Phase 2 — HarnessAgent Base + Multi-Provider Model Adapter ✅ 完成 2026-04-24

> **實際遷移狀態**：原計畫「全 agent 一次轉」，實際為漸進式遷移。6/7 agent 檔案已使用 `harness_call` / `HarnessAgent`；`scamper_feedback.py` 已於 v9 隨 SCAMPER 移除（不需遷移）。`subsystem_decomposer.py` 不作為獨立檔案存在，邏輯整合至 `analyst.py`。~~`anti_anchor.py` 已於 v10 退役，跨域去錨定合併為 TRIZ L1 步驟。~~

**Phase 2a：基礎建設**

- `harness/agent_base.py`：
  ```python
  class HarnessAgent[DepsT, OutputT]:
      def __init__(self, name: str, system_prompt: str, output_type: type[OutputT]):
          self._agent = PydanticAgent(
              model=HarnessModelAdapter(),
              system_prompt=system_prompt,
              output_type=output_type,
              deps_type=...,
          )
  ```

- `harness/model_adapter.py`：自訂 Pydantic AI `Model`
  - 內部呼叫 `app.agents.base._call_provider`
  - 保留 `@retry_on_transient` exponential backoff
  - 保留 Anthropic / OpenAI / Gemini / Qwen dispatch

**Phase 2b：TRIZ solver 轉換**

- 將 `solve_triz_tc`、`solve_triz_pc`、`solve_triz_sf` 改寫為三個 `HarnessAgent`
- 輸入/輸出保留現有 `L1Surface` / `L2RootCause` / `L3StructuralCheck` Pydantic 模型（與 migration 010 欄位相容）
- 舊函式保留為 thin wrapper：
  ```python
  def solve_triz_tc(req):  # 舊 entrypoint 保留
      return _triz_tc_agent.run_sync(req, deps=...).output
  ```

**Phase 2c：其他 agent 轉換**

- `analyst.py` → HarnessAgents：`extract_brief`、`rewrite_mission`、`socratic_q_and_a`、`generate_cld`、`formalize_contradiction`、`decompose_tc_to_pcs`
- `evaluator.py` → `assess_risks`、`scan_convergence`、`evaluate_must`、`pre_cad_review`、`generate_want_seeds`、`validation_passport`
- ~~`scamper_feedback.py`~~（v9 移除）、`knowledge.py`、~~`anti_anchor`~~（v10 退役）、`subsystem_decomposer`

**驗收**：
- 既有 30+ pytest 全綠
- 同一組矛盾 refactor 前後 token / latency 差異 <5%
- Feature flag `USE_HARNESS_ORCHESTRATOR` 可切換新舊路徑（並行一週）

### Phase 3 — Orchestrator + Solver Registry ✅ 完成 2026-04-24

> **實際差異**：`solvers/` 目錄最終未獨立建立。Solver 邏輯保留在 `agents/triz_solver.py` 內，透過 `@register_solver("triz_layered")` 註冊到 `solver_registry`。`orchestrator.py` 直接引用 agent 層函式。

**任務**：

- `harness/orchestrator.py`：手寫 ~100 行線性管線
  ```
  solve_triz_layered(req):
      l1 = l1_agent.run(req)
      persist_layer(project_id, "l1", l1)          ← 每層 upsert
      if should_trigger_pc_decomposition(l1):
          l2 = l2_agent.run(l1)
          persist_layer(project_id, "l2", l2)
      l3 = l3_agent.run(req)                       ← 平行
      persist_layer(project_id, "l3", l3)
      return assemble_response(l1, l2, l3)
  ```
- 移除舊的 `triz_solver.solve_triz_layered`，改為呼叫 orchestrator
- `harness/solver_registry.py`：`@register_solver("triz_layered")`
- `routers/triz.py::solve_layered` 改為 `solver_registry.dispatch("triz_layered", req)`

**驗收**：
- `/triz/solve-layered` E2E 輸出與 refactor 前 byte-wise 相近（允許 LLM 非決定性變異）
- 換頁資料仍在（2026-04-15 Supabase 持久化不 regress）
- 三 RD flag（severity / quick_mode / force_l2）行為不變

### Phase 4 — Skill Loader + 範例 Skill ✅ 完成 2026-04-24

> **實際差異**：範例 skill 非 `ebike_reference_library`（domain-specific），改為 3 個 TRIZ 知識型 skill：`triz_39_parameters`、`triz_76_standards`、`triz_separation_principles`。符合 CLAUDE.md 域無關原則。

**任務**：

- `harness/skill_loader.py`：啟動時掃 `backend/app/skills/*/SKILL.md`
  - 解析 frontmatter（name / description / when_to_use / input_schema）
  - 登錄為 tool（via `tool_registry.register`）
- 範例 skill `skills/ebike_reference_library/`：
  - `SKILL.md`：元資料 + 使用時機
  - `data/`：原本 `services/reference_library.py` 的 JSON 資料
  - `handler.py`（選擇性）：Python 處理邏輯
- `main.py` lifespan startup 加入 `skill_loader.load_all()`

**驗收**：
- 新增 `skills/demo_skill/SKILL.md` 後重啟即可被 agent 呼叫
- 不需改核心 code

### Phase 5 — MCP Client + 文件 ✅ 完成 2026-04-24

> **實際差異**：`mcp_client.py` 已建立但為最小實作（骨架），尚未完整消費外部 `.mcp.json` 工具。文件更新部分由本次 spec 調整補齊。

**���務**：

- `harness/mcp_client.py`：啟動時讀 `.mcp.json`
  - 支援 stdio / SSE / HTTP transport
  - 掛載外部 tools（Tavily、Figma、Supabase MCP 等）
  - 工具以 `mcp__<server>__<tool>` 命名
- 文件：
  - 更新 `docs/01-define/E3--architecture-and-design.md` §11 反映 harness
  - 更新 `docs/02-design/specs/E5x--project-structure-guide.md`
  - README 新增「How to add a solver / skill」章節
  - `backend/docs/API_REFERENCE.md` 加入 MCP endpoint 說明

**驗收**：
- `.mcp.json` 配置 Tavily 後可在 agent 中呼叫 `mcp__tavily__search`
- 所有 docs PR 通過 review
- 新人照 README 可在 30 分鐘內加一個 skill

## 5. 關鍵檔案對照表

### 重用（不重寫）

| 檔案 | 用途 |
|---|---|
| `agents/base.py::_call_provider` | model_adapter 底層 |
| `core/supabase.py::get_supabase()` | HarnessAgent `Deps` |
| `core/gate_registry.py` / `evaluator_registry.py` | solver_registry 範本 |
| `agents/triz_critic.py::should_trigger_pc_decomposition` | orchestrator 直接呼叫 |
| `agents/triz_solver.py::_persist_layered_solution` | 搬進 orchestrator |

### 改寫

| 檔案 | 改動 |
|---|---|
| `agents/*.py` | 6/7 已改為 harness_call/HarnessAgent；~~scamper_feedback.py v9 移除~~ |
| `routers/triz.py::solve_layered` | 改走 solver_registry.dispatch |
| `main.py` lifespan | 加入 skill_loader + mcp_server 啟動 |
| `pyproject.toml` | 加 `pydantic-ai`、`mcp` |

### 新增

- `backend/app/harness/` × 9 檔（agent_base, model_adapter, tool_registry, solver_registry, skill_loader, mcp_server, mcp_client, orchestrator, prompt_assembler）
- ~~`backend/app/solvers/triz_layered/`~~ — 未獨立建目錄，邏輯留在 agents/triz_solver.py
- `backend/app/skills/` × 3 知識型 skill（triz_39_parameters, triz_76_standards, triz_separation_principles）
- `backend/app/tools/triz_kb_tools.py`（@register_tool 裝飾的 MCP 工具）
- `backend/tests/harness/test_*.py`（67 tests passing）

## 6. 驗證策略

### 單元 / 整合

- `pytest backend/tests/` 既有 30+ 檔全綠
- 新增 `tests/harness/`：tool_registry、solver_registry、skill_loader、mcp_server、model_adapter

### E2E

1. 啟 `uvicorn app.main:app --reload --port 8000`
2. 前端 `npm run dev`，走完 Create 頁 TRIZ 三矛盾解析：
   - L1/L2/L3 輸出與 refactor 前相同
   - 換頁後資料仍在
   - 三 RD flag 行為不變
3. **Claude Code MCP 測試**：
   ```
   claude mcp add design-copilot stdio -- python -m app.harness.mcp_server
   ```
   從 Claude 呼叫 `lookup_matrix(6, 14)` 拿到 principles
4. 放入假 skill `skills/hello_triz/SKILL.md`，重啟後在 agent loop 中可見

### 成本與延遲基準

- 同組矛盾：refactor 前 / 後 / feature-flag 開關 三組 token 與延遲比對
- 差異 <5%（Pydantic AI 應只是薄層）

## 7. 風險與對策

| 風險 | 對策 |
|---|---|
| Pydantic AI <1.0 API 不穩 | harness layer adapter；版本鎖 minor |
| MCP SDK × Anthropic SDK 版本衝突 | 獨立 venv 驗證；必要時 subprocess 隔離 |
| 重寫引入輸出漂移 | `USE_HARNESS_ORCHESTRATOR` feature flag 並行一週 |
| 團隊不熟 Pydantic AI | ADR-006 附 onboarding snippet；thin wrapper 策略 |
| 前端 `(supabase as any)` cast 未清 | 另案處理（Supabase types 重生） |

## 8. 不做的事（Scope Boundary）

- ❌ 導入 LangGraph（無 checkpoint/HITL 剛需）
- ❌ 重寫 gate / evaluator registry（已符合範式）
- ❌ 動前端 React Query 層
- ❌ 增加新 LLM provider（ADR-003 Phase 3 另案）
- ❌ 改動 Supabase schema / migrations
- ❌ 改 authentication / middleware

## 9. 後續延伸（超出本計畫）

- **v1.1**：Pre-CAD Review 自成 solver（與 TRIZ Layered 並列）
- **v1.1**：Knowledge Agent 接 vector DB（pgvector on Supabase）
- **v1.2**：LangGraph 遷移評估（若出現真實 checkpoint/HITL 需求）
- **v2.0**：Harness 獨立 package 化，其他 Delta 產品可重用
