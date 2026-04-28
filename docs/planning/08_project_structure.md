# 專案結構規範 — RD Design Copilot

---

**文件版本**：`v2.3`（domain.yaml 解耦 + 資料夾重組 + DomainConfig）
**最後更新**：`2026-04-28`
**狀態**：`Active — reflects actual harness; new features must follow this structure`
**模板來源**：`templates/vibecoding/08_project_structure_guide.md`（本檔結構偏離模板以反映 claude-code 風 harness）

> **本文件定位**：現行 backend 架構的 SSOT。新增功能必須對齊本文件，不得回退到 Clean Architecture（Domain / Service / Repository 分層）。Backend 是仿 **claude-code CLI** 的 AI Agent Harness，不是傳統 web 服務。

---

## 1. 設計原則

1. **Harness-first**（不是 Clean Architecture）— 業務邏輯活在 markdown skills，**不在** Python domain class。
2. **Filesystem-first 配置** — `.claude/` 樹是運行設定的 SSOT；資料庫只負責使用者識別（Supabase auth-only）。
3. **三組概念分離**：
   - **Tools**（基礎設施 action）— Python 類別繼承 `Tool` ABC
   - **Skills**（領域知識）— markdown system prompt + frontmatter
   - **Commands**（使用者入口）— slash command markdown，引用 skill
4. **域無關 harness + 域特定 markdown** — harness 不寫業務語言；TRIZ / TR / 機構工程語言全部在 SKILL.md 與 `docs/engineering/`。
5. **State / Context 雙路徑**（依 `.claude/CLAUDE.md` 內容位置邊界政策）：
   - Skill 內部 state → `.claude/context/triz/.{triz,tr}-state.json`
   - 工程交付物 → `docs/engineering/`
6. **CLI 與 HTTP 共享同一個 `AgentLoop`**（不同包裝、同一核心）。
7. **Tool 失敗用 `is_error=True`**，**不丟例外** — 讓 model 看見錯誤並自行決策。
8. **Naming**：Python `snake_case` 檔案 / `PascalCase` 類別；Skill 用 `kebab-case` 目錄。

---

## 2. 後端目錄結構（記錄現況）

```
backend/
├── pyproject.toml            # FastAPI 0.115+, Anthropic 0.42+, mcp 1.0, Supabase 2.12+, PyJWT, httpx, tavily-python (optional)
├── Dockerfile                # Python 3.12-slim + uvicorn entry
├── .dockerignore
├── docs/
│   └── API_REFERENCE.md      # backend-local API 文件
├── app/
│   ├── __init__.py
│   ├── __main__.py           # 讓 `python -m app.harness` 可運作（轉發到 harness/cli.py）
│   ├── main.py               # FastAPI app + middleware stack（CORS、RequestID、Error handlers）
│   ├── settings.py           # Pydantic settings + JSON logging（讀 root /.env）
│   ├── api/                  # ── HTTP 介面層（薄包裝）──
│   │   ├── health.py         # GET /api/v1/health（公開，無 auth）
│   │   └── sessions.py       # /api/v1/sessions CRUD + /run（同步）+ /run/stream（SSE）
│   ├── harness/              # ★ Agent runtime 核心（域無關）
│   │   ├── agent.py          # AgentLoop（run + stream HarnessEvent generator）
│   │   ├── agents.py         # CustomAgent loader（.claude/agents/<name>.md）
│   │   ├── cli.py            # CLI entry（python -m app.harness <cmd> [user_input]）+ CLAUDE.md 注入
│   │   ├── command.py        # Command resolver（.claude/commands/<name>.md 含 referenced_skill）
│   │   ├── config.py         # HarnessClient（Anthropic SDK 直連 / Azure proxy 偵測）
│   │   ├── domain_config.py  # DomainConfig loader（讀 .claude/domain.yaml，解耦 harness↔domain）
│   │   ├── skill.py          # Skill loader（.claude/skills/<name>/SKILL.md）
│   │   └── tools/
│   │       ├── base.py       # Tool ABC + ToolResult dataclass
│   │       ├── registry.py   # ToolRegistry + default_registry / _with_agent / _with_triz 三級工廠
│   │       ├── fs.py         # ReadTool / WriteTool / EditTool / GlobTool / GrepTool
│   │       ├── bash.py       # BashTool（subprocess + timeout + output cap）
│   │       ├── web.py        # WebFetchTool / WebSearchTool（Tavily，缺 key 自動降級）
│   │       └── agent.py      # AgentTool（subagent dispatch；不可遞迴）
│   ├── triz/                 # ★ TRIZ 確定性邏輯（域特定 — Tool 底層模組）
│   │   ├── __init__.py
│   │   ├── tools.py          # 8 個 Tool 子類：MatrixLookup / ParamMap / CCICalculate / SIMCompute / TrizState{Read,Write,Advance} / ArtifactBundle
│   │   ├── bundle.py         # BundleManager + MANIFEST.json Pydantic models（register/validate/status/export）
│   │   ├── registry.py       # triz_tools() 工廠 → list[Tool]，供 registry.default_registry_with_triz() 使用
│   │   ├── state.py          # 20+ Pydantic v2 models（TrizState / TRState schema）
│   │   ├── state_manager.py  # Atomic R/W + step advance guard rails
│   │   ├── kb/
│   │   │   ├── loader.py     # KBLoader — 解析 markdown KB（39 參數 / 矛盾矩陣 / 40 原理 / 分離原理）
│   │   │   └── matrix.py     # lookup_principles() 純函式
│   │   ├── solve/
│   │   │   ├── param_mapper.py  # NL → 39 參數候選（TF-IDF + keyword）
│   │   │   └── sim.py        # SIM 統計 + 收斂判定
│   │   └── verify/
│   │       └── cci.py        # CCI 計算 + verdict
│   └── middleware/
│       ├── auth.py           # Supabase JWT（HS256）+ dev bypass token
│       ├── error_handler.py  # Anthropic SDK errors / validation / generic
│       └── request_id.py     # X-Request-ID ContextVar（thread-safe + async-safe）
└── tests/
    ├── conftest.py           # client / client_no_auth fixtures（FakeAnthropicClient）
    ├── unit/                 # auth / middleware / error_handling（純邏輯）
    ├── api/                  # test_health / test_sessions / test_live_skills
    ├── triz/                 # test_tools（38 tests — domain tool unit tests）
    ├── harness/              # test_agent / test_skill / test_command / test_cli / test_tools_* / test_live_agent_fanout
    └── _live_artifacts/      # 時戳快照（每次 live test 自動寫入）
        └── YYYY-MM-DD_HH-MM-SS/
            ├── .triz-state.json
            ├── .tr-state.json
            ├── session-*.md
            └── session-template.md
```

### 2.1 重要：本目錄樹是 SSOT

新增功能（無論是新 endpoint、新 tool、新 skill）都必須能對應到上述某個位置。如果無法對應，先在 `04_adr/` 寫 ADR 討論架構演化，**不要私自建立新的頂層目錄**。

---

## 3. `.claude/` 配置層（與 backend 解耦但運行時必讀）

```
.claude/
├── settings.json             # 權限、hooks、預設 model
├── CLAUDE.md                 # 專案級指令（含內容位置邊界政策）
├── domain.yaml               # 領域配置（command prefixes, paths, artifact categories）
├── skills/
│   └── <kebab-name>/
│       └── SKILL.md          # frontmatter: name, description, allowed_tools? + body 為系統提示
├── commands/
│   └── <name>.md             # slash command，含「載入 **<skill-name>** skill」regex pattern
├── agents/
│   └── <name>.md             # subagent 定義: frontmatter (name, description, model?, tools?) + body
└── context/
    └── triz/
        ├── .triz-state.json  # TRIZ session state（Skill 內部 SSOT）
        ├── .tr-state.json    # TR gate 進展（專案級持久）
        ├── session-*.md      # 跨步驟敘事記錄
        └── session-template.md
```

### 3.1 內容位置邊界（引用 `.claude/CLAUDE.md`）

| 內容性質 | 產出者 | 消費者 | 存放位置 |
|:---------|:-------|:-------|:---------|
| Session 過程記錄 | Skill | Skill（跨步驟傳遞） | `.claude/context/triz/session-*.md` |
| 流程狀態 JSON | Skill | Skill（狀態機） | `.claude/context/triz/.{triz,tr}-state.json` |
| 工程交付物（WI/ICD/MC） | Skill（如 triz-wi） | **工程師（人）** | `docs/engineering/` |
| 方法論知識庫 | 人 | Skill（參考） | `docs/methodology/` 或 `knowledge/triz/` |
| Gate review 報告 | Skill（tr-gate） | 工程師 | `docs/engineering/gate_reviews/` |

**鐵律**：狀態 JSON 只能由 Skill 修改，不可手動編輯。

---

## 4. 雙介面設計

```
                ┌─ CLI: python -m app.harness <cmd> [user_input]
                │     入口：backend/app/harness/cli.py
                │     resolve_command → load_skill → AgentLoop.run() → stdout
                │     退出碼: 0 success / 1 agent error / 2 config error
                │
        共享 AgentLoop  ◄── backend/app/harness/agent.py
                │
                └─ HTTP: POST /api/v1/sessions/{id}/run (or /run/stream)
                      入口：backend/app/api/sessions.py
                      resolve_command → load_skill → AgentLoop.stream() → SSE
                      事件：worker_status / text_delta / tool_use / tool_result / iteration_end / done / error
```

**關鍵點**：
- 兩個介面共用 `AgentLoop`，業務邏輯零重複
- HTTP 多了 session record（in-memory dict，使用者隔離）+ SSE 事件包裝
- HTTP 介面**不是**為了 production multi-tenant 設計（PoC 等級）；遷移到 Supabase 持久化是 ADR-006 的事

---

## 5. Agent Loop 生命週期（理解後再擴充）

```python
# AgentLoop 在 harness/agent.py 內，簡化版邏輯：
while iterations < max_iterations:
    response = client.messages.create(
        system=skill_body,
        tools=registry.to_anthropic_schemas(only=allowed_tools),
        messages=history,
    )

    if response.stop_reason == "end_turn":
        return AgentResult(final_text=...)

    if response.stop_reason == "tool_use":
        for tool_block in response.content:
            result = registry.dispatch(tool_block.name, tool_block.input)
            history.append(tool_result_block(result))
        continue

    if response.stop_reason == "max_tokens":
        return AgentResult(truncated=True)

    raise AgentLoopError(unknown stop_reason)
```

**特性**：
- Tool 失敗轉 `is_error=True` block，loop 不中斷，model 自行決策
- 串流版（`stream()`）yield `HarnessEvent`（frozen dataclass，可 JSON serialize）
- 不做 message 緩衝，事件即時下發

### 5.1 Domain Command 路由

CLI（`cli.py`）和 HTTP（`sessions.py`）共用同一個偵測邏輯，透過 `.claude/domain.yaml` 配置：

```python
domain_cfg = load_domain_config(project_root)    # 讀 .claude/domain.yaml
if domain_cfg.is_domain_command(cmd_name):        # 比對 command_prefixes
    paths = domain_cfg.resolve_paths(project_root)
    registry = default_registry_with_triz(
        kb_root=paths["kb_root"],
        state_dir=paths["state_dir"],
        artifact_categories=domain_cfg.artifact_categories or None,
    )
else:
    registry = default_registry_with_agent(...)   # fs + web + bash + agent（無 domain tools）
```

三級 registry 工廠（`harness/tools/registry.py`）：

| 工廠 | 內含 Tools | 使用場景 |
|:-----|:-----------|:---------|
| `default_registry()` | Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch | Subagent 預設 |
| `default_registry_with_agent()` | 上述 + Agent | 非 TRIZ 主 loop |
| `default_registry_with_triz()` | 上述 + 8 TRIZ domain tools | TRIZ/TR 主 loop |

---

## 6. 擴充指引

### 6.1 新增 Tool

**基礎設施 Tool**（域無關）放 `app/harness/tools/`：

1. 在 `backend/app/harness/tools/<name>.py` 繼承 `Tool` ABC：
   ```python
   class MyTool(Tool):
       name = "MyTool"
       description = "..."
       input_schema = { "type": "object", "properties": { ... } }
       def run(self, **kwargs) -> ToolResult:
           ...
   ```
2. 在 `harness/tools/registry.py::default_registry()` 註冊
3. 寫測試 `tests/harness/test_tools_<name>.py`（含 happy path + 失敗轉 `is_error=True`）

**域特定 Tool**（如 TRIZ）放 `app/<domain>/tools.py`：

1. 在 `app/triz/tools.py` 繼承同一個 `Tool` ABC
2. 在 `app/triz/registry.py::triz_tools()` 工廠加入
3. 寫測試 `tests/triz/test_tools.py`
4. 不要把 domain tool 放進 `harness/tools/` — harness 永遠域無關

**共通**：必要時更新 `.claude/skills/<skill>/SKILL.md` frontmatter 的 `allowed_tools`

### 6.2 新增 Skill

1. 建 `.claude/skills/<kebab-name>/SKILL.md`
2. Frontmatter：
   ```yaml
   ---
   name: my-skill
   description: 一句話 trigger 描述（when to use this skill）
   allowed_tools: [Read, Write, Glob]   # 選填，省略代表全部
   model: claude-opus-4-7              # 選填
   ---
   ```
3. Body 即系統提示：**域特定知識在這裡寫**，不在 Python
4. **禁止**在 SKILL 硬編碼產品規格（材料名、數值、測試項目） — 規格從 `docs/engineering/` 動態讀

### 6.3 新增 Command

1. 建 `.claude/commands/<name>.md`
2. Frontmatter（YAML）+ body 含「載入 **<skill-name>** skill」這個 pattern（`command.py` 用 regex 抽取 referenced_skill）
3. 一般情況下 1 command : 1 skill

### 6.4 新增 CustomAgent（subagent）

1. 建 `.claude/agents/<name>.md`，frontmatter 含 `name, description, model?, tools?`
2. 由 `Agent` tool 呼叫；**不可遞迴**（CustomAgent 的 sub_registry_factory **不能**包含 `Agent` tool）
3. 適合做平行扇出（fan-out）但目前實作為 sequential

### 6.5 反模式（不要做）

- ❌ 新增 `backend/app/domains/` 或 `backend/app/services/` — 業務邏輯放 SKILL.md
- ❌ 在 `harness/` 內寫 TRIZ / TR 領域邏輯 — harness 永遠保持域無關
- ❌ 把 SKILL body 拆成 Python 函數鏈 — Skill body 就是系統提示，model 自己決策
- ❌ 為了「型別安全」把 markdown 結構轉成 Pydantic class — 損失靈活性
- ❌ 在 `app/api/` 寫超過薄包裝的邏輯 — Endpoint 應該只做 (1) 解析請求 (2) 呼叫 harness (3) 回傳

---

## 7. 命名規範

| 類別 | 規則 | 範例 |
|:-----|:-----|:-----|
| Python module/file | snake_case | `agent.py`, `request_id.py`, `tools/fs.py` |
| Python class | PascalCase | `AgentLoop`, `ToolRegistry`, `HarnessClient` |
| Skill 目錄 | kebab-case | `triz-router/`, `tr-gate/` |
| Command 檔名 | kebab-case | `triz-solve.md` |
| Agent（subagent）檔名 | kebab-case | `triz-analyst.md` |
| Test file | `test_<module>.py` | `test_agent.py`, `test_tools_fs.py` |
| Live test marker | `@pytest.mark.live` | 預設略過，需 `pytest -m live` 啟用 |
| Live artifact 目錄 | ISO timestamp | `2026-04-28_02-10-21/` |

---

## 8. 配置文件

| 檔名 | 內容 | git? |
|:-----|:-----|:-----|
| `backend/pyproject.toml` | Python 依賴、ruff、pytest marker（`live`） | ✓ |
| `backend/Dockerfile` | Python 3.12-slim + uvicorn `app.main:app` | ✓ |
| `backend/.dockerignore` | `__pycache__`、`.env*`、tests、`*.md` | ✓ |
| `.env`（root） | `ANTHROPIC_API_KEY` / Supabase / `LLM_PROVIDER` / `AZURE_OPENAI_BASE_URL` | ✗ |
| `.env.example` | 範本（敏感值留白） | ✓ |
| `.claude/settings.json` | 權限、hooks、預設 model | ✓ |
| `.claude/domain.yaml` | 領域配置（command prefixes, paths, artifact categories） | ✓ |
| `.claude/CLAUDE.md` | 專案級指令 + 內容位置邊界政策 | ✓ |
| `supabase/`（root） | Supabase migration、policy（DB 持久化未來使用） | ✓ |

---

## 9. 測試策略

| 類別 | 位置 | 何時跑 | 內容 |
|:-----|:-----|:-------|:-----|
| Unit（純邏輯） | `tests/unit/` | 每次 push（CI） | auth, middleware, error_handling |
| API（HTTP 介面） | `tests/api/` | 每次 push | health, sessions CRUD/run/stream |
| Harness（核心） | `tests/harness/` | 每次 push | agent loop, skill/command 解析, tools 各別, subagent dispatch |
| TRIZ（domain） | `tests/triz/` | 每次 push | 8 domain tools, bundle manager, KB loader, state manager, CCI, SIM, param_mapper |
| Live（真打 LLM） | 任何加 `@pytest.mark.live` 的測試 | `pytest -m live` 手動 | E2E：真 Anthropic / Azure 呼叫 |
| Live artifacts | `tests/_live_artifacts/<timestamp>/` | live 跑時自動寫入 | `.triz-state.json` + `session-*.md` |

**Live 測試成本**：~$0.02/run（Sonnet 4.6, max_tokens=500, max_iterations=3）。
**Fakes**：`conftest.py` 提供 `FakeAnthropicClient`，可 mock `messages.create()` 回傳 tool_use blocks。

---

## 10. 與 `docs/` 的對應

| docs 路徑 | 角色 | 與 backend 關係 |
|:----------|:-----|:----------------|
| `docs/planning/08_project_structure.md`（**本檔**） | 現行架構 SSOT | 描述現況；新功能對齊本檔 |
| `docs/planning/05_architecture.md` | 系統架構（C4/DDD 視角） | §1.1.3 Component 圖對應 `app/harness/`（注：05 仍提了部分 Clean Arch 用詞，待 follow-up 對齊） |
| `docs/planning/06_api_spec.md` | API 契約 | §7 endpoints 對應 `app/api/`，多數 TRIZ endpoints 透過 harness 實現 |
| `docs/planning/04_adr/ADR-002` | TRIZ Skill 架構決策 | 對應 `.claude/skills/triz-*` |
| `docs/methodology/auto_triz_strategy.md` | TRIZ 方法策略 SSOT | Skill body 引用 |
| `docs/engineering/` | 工程交付物範本（WI/ICD/MC） | `triz-wi` skill 寫入此 |
| `docs/methodology/DK-01-05` | 方法論 KB | Skill 參考 |
| `docs/01-define/pages/` | 18 頁產品 IA | 前端實作目標（前端尚未存在） |

---

## 11. 前端章節（佔位 — 待 `frontend/` 建立後展開）

> **狀態**：尚未實作。本節記錄目標假設，對齊既有規範庫。

預設目錄目標：

```
frontend/
├── package.json / tsconfig.json / vite.config.ts / tailwind.config.ts
├── src/
│   ├── main.tsx / App.tsx / routes.tsx
│   ├── components/             # Atomic Design（atoms/molecules/organisms）— 對齊 templates/design-system/specs/01_components_spec.md
│   ├── features/               # 業務功能 feature-first — 對齊 docs/01-define/pages/ 8 個 ia_group 分組
│   ├── pages/                  # 路由葉節點 × 18 頁，與 docs/01-define/pages/ 1:1 對應（page_name 取 frontmatter）
│   ├── hooks/ services/ stores/
│   └── styles/ types/ config/
└── tests/
    ├── unit/ component/ e2e/
    └── features/               # BDD .feature 對齊 docs/planning/03_bdd_guide.md
```

**對齊規範**：
- Component / Token：`templates/design-system/specs/`
- Page IA：`docs/01-define/pages/INDEX.md` + 18 頁 frontmatter
- BDD scenarios：`docs/planning/03_bdd_guide.md`

**待補事項**：API client 對應 `06_api_spec.md` endpoints；SSE 處理對應 backend `/run/stream` 事件型別。

---

## 12. 進化原則

- **新增功能優先順序**：先寫 Skill（markdown）→ 不夠再加 Tool（Python）→ 不夠再改 AgentLoop（最後手段）
- **不擴張 `harness/`**：harness 是穩定核心；新領域邏輯放 Skill，不放 `harness/`
- **不引入 Domain class**：domain 知識留在 SKILL.md 與 `docs/engineering/`，不複製到 Python
- **重大變動先寫 ADR**：在 `docs/planning/04_adr/` 加新 ADR（例：何時引入 DB 持久化、何時拆分 TRIZ 服務、何時做多租戶）
- **不要因為「看起來不夠工程」就重構**：harness 簡單是設計，不是缺陷

---

## 13. 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-28 | v2.3 | 資料夾重組（`knowledge/` + `templates/` + `docs/methodology|engineering|research/`）+ `domain.yaml` + `domain_config.py` 解耦 harness↔domain 硬編碼；`BundleManager` categories 可配置化。 |
| 2026-04-28 | v2.2 | 加入 `ArtifactBundle` tool + `bundle.py`（MANIFEST.json 管理：register/validate/status/export），domain tools 7→8。 |
| 2026-04-28 | v2.1 | 加入 `app/triz/` domain tools layer（7 Tool 子類 + registry）、EditTool、BashTool、TRIZ command 路由（§5.1）、§6.1 domain tool 慣例。 |
| 2026-04-28 | v2.0 | 完全覆寫：對齊實際 M1-M4 harness。先前 v1.0 提的 Clean Architecture（`src/rd_copilot/` + DB ORM + BDD `.feature`）方向錯誤，全部移除。 |
| 2026-04-28 | v1.0 | 初版（VibeCoding template skeleton；方向錯誤，被 v2.0 取代） |

---

## 文件溯源

- 模板：`templates/vibecoding/08_project_structure_guide.md`
- 實作驗證：
  - `backend/app/main.py`、`settings.py`
  - `backend/app/api/{health,sessions}.py`
  - `backend/app/harness/{agent,agents,cli,command,config,domain_config,skill}.py`
  - `backend/app/harness/tools/{base,registry,fs,bash,web,agent}.py`
  - `backend/app/triz/{tools,bundle,registry,state,state_manager}.py`
  - `backend/app/triz/kb/{loader,matrix}.py`
  - `backend/app/triz/solve/{param_mapper,sim}.py`
  - `backend/app/triz/verify/cci.py`
  - `backend/app/middleware/{auth,error_handler,request_id}.py`
  - `backend/tests/{conftest,unit,api,harness,triz,_live_artifacts}/`
- 政策：`.claude/CLAUDE.md` 內容位置邊界
- M1-M4 commits：`ca61b72`（M1 Tool primitives）、`484f72e`（M2 skill+command loaders）、`24450bc`（M3 agent loop+client）、`77e7d1e`（M4 CLI entry, /triz e2e）
