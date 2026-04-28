# 模組契約與測試 — RD Design Copilot

---

**文件版本**：`v2.0`（完全覆寫，對齊 08 v2.0 harness-first）
**最後更新**：`2026-04-28`
**狀態**：`Active — replaces v1.0 Clean Arch module table`
**模板來源**：`templates/vibecoding/07_module_specification_and_tests.md`（結構偏離模板以反映 harness）

> **本檔定位**：harness-first 系統的「模組」不是 Python module 切分，而是三類契約：
> - **Tool 契約**（Python class，繼承 `Tool` ABC）
> - **Skill 契約**（markdown SKILL.md，frontmatter + body）
> - **Command 契約**（markdown，slash command + skill reference）
>
> 先前 v1.0 版用 `src/triz/contradict.py::solve_contradiction()` 這類 Python function 契約 — 不對齊實際架構，已棄用。

---

## 1. 模組總覽

### 1.1 Python 層（穩定核心，極少變動）

| 模組 | 檔案 | 職責 | 對齊 ADR |
|:-----|:-----|:-----|:---------|
| `harness.agent` | `app/harness/agent.py` | AgentLoop（run + stream） | ADR-002 |
| `harness.skill` | `app/harness/skill.py` | SKILL.md 解析 | ADR-002 |
| `harness.command` | `app/harness/command.py` | 命令解析 + skill 引用抽取 | ADR-002 |
| `harness.agents` | `app/harness/agents.py` | CustomAgent (subagent) 解析 | ADR-002 |
| `harness.config` | `app/harness/config.py` | HarnessClient（Anthropic / Azure） | ADR-005 |
| `harness.cli` | `app/harness/cli.py` | CLI entry | ADR-002 |
| `harness.tools.*` | `app/harness/tools/{base,registry,fs,web,agent}.py` | Tool ABC + 5 內建 tools | ADR-002 |
| `api.sessions` | `app/api/sessions.py` | HTTP wrapper（含 SSE） | — |
| `api.health` | `app/api/health.py` | 健康檢查 | — |
| `middleware.*` | `app/middleware/{auth,error_handler,request_id}.py` | Auth + error + request id | — |

### 1.2 Skill 層（業務邏輯所在，常變動）

| Skill | 路徑 | 對應 TRIZ Step / TR Gate | 對應 BDD Feature |
|:------|:-----|:------------------------|:-----------------|
| `triz-router` | `.claude/skills/triz-router/SKILL.md` | 主入口 | — |
| `triz-scoping` | `.claude/skills/triz-scoping/SKILL.md` | Step 0 | F1 |
| `triz-model` | `.claude/skills/triz-model/SKILL.md` | Step 1 | F1 |
| `triz-contradict` | `.claude/skills/triz-contradict/SKILL.md` | Step 2+3 | F2 |
| `triz-verify` | `.claude/skills/triz-verify/SKILL.md` | Step 4 | F3 + F4 (`cad_readiness` merged) |
| `triz-wi` | `.claude/skills/triz-wi/SKILL.md` | Step 5 | — |
| `tr-router` | `.claude/skills/tr-router/SKILL.md` | TR 主入口 | — |
| `tr-gate` | `.claude/skills/tr-gate/SKILL.md` | TR1-TR10 Gate | F2 |
| `tr-fea-assist` | `.claude/skills/tr-fea-assist/SKILL.md` | FEA 設定 | — |
| `tr-test-report` | `.claude/skills/tr-test-report/SKILL.md` | 測試報告 | — |
| `tr-dfm` | `.claude/skills/tr-dfm/SKILL.md` | DFM 審查 | — |
| `tr-sop` | `.claude/skills/tr-sop/SKILL.md` | SOP 草稿產出（TR8-9） | — |
| `tr-spc` | `.claude/skills/tr-spc/SKILL.md` | SPC/Cpk 計算（TR9-10） | — |
| `tr-ppap` | `.claude/skills/tr-ppap/SKILL.md` | PPAP 文件包組裝（TR9-10） | — |

### 1.3 Command 層（使用者入口）

每個常用 skill 都有對應 slash command（`.claude/commands/<name>.md`）。1 command : 1 skill 為主。

---

## 2. Tool 契約模板

每個 Tool 必須具備以下契約（範例：`ReadTool`）：

```python
# app/harness/tools/fs.py
class ReadTool(Tool):
    name = "Read"
    description = (
        "Read a file from the local filesystem.\n"
        "Use absolute paths.\n"
        "Returns 'cat -n' style output with line numbers."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "absolute path"}
        },
        "required": ["path"],
    }

    def run(self, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        # Preconditions
        if not path or not Path(path).is_absolute():
            return ToolResult(content="path required and must be absolute", is_error=True)
        # Action
        try:
            text = Path(path).read_text(encoding="utf-8")
            numbered = "\n".join(f"{i+1:>6}\t{line}" for i, line in enumerate(text.splitlines()))
            return ToolResult(content=numbered)
        except Exception as e:
            return ToolResult(content=f"read failed: {e}", is_error=True)
```

**契約必含**：
- `name` / `description` / `input_schema`（class vars）
- `run(**kwargs) -> ToolResult` — **永不丟例外**，錯誤轉 `is_error=True`
- 寫測試於 `tests/harness/test_tools_<name>.py`：
  - Happy path
  - Edge case（極端參數）
  - Invalid input → `is_error=True`
  - Failure（IO 錯、network 錯）→ `is_error=True`

### 2.1 內建 Tool 清單

| Tool | 檔案 | Run 行為摘要 |
|:-----|:-----|:-------------|
| `Read` | `tools/fs.py::ReadTool` | 讀絕對路徑、cat -n 風格、UTF-8 |
| `Write` | `tools/fs.py::WriteTool` | 寫絕對路徑、自動建父目錄 |
| `Glob` | `tools/fs.py::GlobTool` | 匹配 pattern、按 mtime desc 排序 |
| `WebFetch` | `tools/web.py::WebFetchTool` | HTTP GET via httpx |
| `WebSearch` | `tools/web.py::WebSearchTool` | Tavily API（缺 key 自動降級） |
| `Agent` | `tools/agent.py::AgentTool` | 派生 subagent；不可遞迴（sub registry 不含 Agent） |

---

## 3. Skill 契約模板

每個 SKILL.md 必須具備以下結構（範例：`triz-contradict`）：

```markdown
---
name: triz-contradict
description: |
  TRIZ Step 2+3 TC/PC/SF 解題管線。
  TRIGGER when: 用戶有明確矛盾要求解 / 已完成 Step 1 FA。
  SKIP: 無矛盾、純功能缺失（改用 SF-only 通道）。
allowed_tools: [Read, Write, Glob]   # 選填：白名單；省略則全部
model: claude-opus-4-7              # 選填：覆寫預設 model
---

# triz-contradict — TRIZ Step 2+3 解題

[body 是給 model 的系統提示，描述方法學]

## 前置狀態（Preconditions）
- `.claude/context/triz/.triz-state.json` 存在
- step1 FA 已完成（fa_components 非空）

## 處理流程
1. 讀取 .triz-state.json 取得 contradictions[]
2. 對每個 TC：39 參數映射 → 矛盾矩陣查表 → 原理具體化
3. 寫入 step3.solutions

## 後置狀態（Postconditions）
- step2.completed=true / step3.completed=true
- 每個 solution 含 F/S/OZ/OT/Px

## 不變式（Invariants）
- L1 必含跨域去錨定步驟
- 60s timeout per TC
- 失敗不污染 state（atomic write）
```

**契約必含**：
- frontmatter `name`、`description`（雙列 TRIGGER + SKIP）
- 選填：`allowed_tools`、`model`
- body：方法學陳述、Pre/Post/Invariant 條件
- **禁止**硬編碼產品規格（Delta 馬達某型號的扭矩值）— 從 `docs/engineering/` 動態讀

### 3.1 Skill 一致性規則

- **域無關**：不寫具體材料名、不寫具體數值閾值；具體數值留 `docs/engineering/` 的 Material Card / WI
- **狀態邊界**：Skill 只透過 Read/Write tool 操作 `.claude/context/triz/.{triz,tr}-state.json`，不直接 Python file IO
- **失敗呈現**：toast 訊息 / fallback 路線在 body 描述；model 看到 tool error 後自行決策

---

## 4. Command 契約模板

```markdown
---
description: TRIZ 主入口路由 + session 管理
---

# /triz — 主入口

請載入 **triz-router** skill，依問題類型路由至 step0/1/2 或 SF-only 通道。

## 用法
```
/triz [問題描述]
/triz                  # 互動式
```

## 預期行為
- 偵測 .triz-state.json 是否存在 → 已有 session 顯示 status 並詢問繼續
- 無 session → 引導建立
- 路由完成後將控制權交回 user
```

**契約必含**：
- frontmatter（`description` 必填）
- body 含「載入 **<skill-name>** skill」的 regex pattern（`command.py::extract_referenced_skill()` 用此抓取）

---

## 5. 測試矩陣

每類契約對應的測試重點：

| 契約類 | 測試位置 | 重點測項 |
|:-------|:---------|:---------|
| Tool | `tests/harness/test_tools_<name>.py` | happy / edge / invalid / failure 四象限；ToolResult 不為例外 |
| AgentLoop | `tests/harness/test_agent.py` | 用 FakeAnthropicClient mock；end_turn / tool_use / max_tokens / unknown stop_reason |
| Skill 解析 | `tests/harness/test_skill.py` | frontmatter 解析、缺欄位降級、allowed_tools 字串/list/null 三型 |
| Command 解析 | `tests/harness/test_command.py` | referenced_skill 抽取、缺 frontmatter 容錯 |
| API 端點 | `tests/api/test_sessions.py` | CRUD / run / SSE event 序列 |
| Live E2E | `tests/api/test_live_skills.py` + `tests/harness/test_live_*.py` | `@pytest.mark.live`，真打 Anthropic / Azure |

---

## 6. LLM Prompting Guide（給 AI 開發者）

當你要為新 Tool / Skill 產生 boilerplate：

```
請依下列契約模板，為我產出 <Tool / Skill / Command>：

[貼上 §2 / §3 / §4 模板區段]

需求：
- 不引入 Domain class / Repository / Use Case 層
- Tool 失敗用 is_error=True，不丟例外
- Skill body 為系統提示，不寫 Python function
- 測試含四象限（happy / edge / invalid / failure）
```

---

## 文件溯源

- 模板：`templates/vibecoding/07_module_specification_and_tests.md`
- 對齊：[`08_project_structure.md`](./08_project_structure.md) v2.0
- 既有 Tool 實作：`backend/app/harness/tools/{base,registry,fs,web,agent}.py`
- 既有 Skill：`.claude/skills/triz-*` / `.claude/skills/tr-*`

## 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-28 | v2.1 | §1.2 triz-verify 映射更正為 F3+F4（cad_readiness merged），triz-contradict 更正為 F2 |
| 2026-04-28 | v2.0 | 完全覆寫：模組改為 Tool / Skill / Command 三類契約。先前 v1.0 提的 Python function 契約（如 `solve_contradiction()`）已棄用。 |
| 2026-04-28 | v1.0 | 初版（Python function 契約；方向錯誤被 v2.0 取代） |
