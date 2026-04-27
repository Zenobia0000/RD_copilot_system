# DK-03 — 多 Agent 編排架構

> 為什麼這樣切 agent / skill；何時平行、何時不該平行。
> 來源：Anthropic Claude Code 官方文件、市場平台研究（LangGraph / CrewAI / AutoGen / OpenAI Agents SDK）、Cognition 反向警告。

---

## §1 設計原則

### §1.1 兩個對立的力

| 力 | 主張 | 代表 |
|:---|:-----|:-----|
| **平行化** | 多 agent 同時跑、各司其職、結果彙整 → 速度 N 倍、視角多元 | LangGraph / CrewAI / AutoGen / Anthropic Multi-Agent Research |
| **Context Cohesion** | 每個動作嵌入隱含決策，獨立 agent 沒有共享軌跡會 drift → **「Don't Build Multi-Agents」** | Cognition（Devin） |

> 引用 Cognition："Every action embeds an unstated decision. Subagents diverge when they don't share full traces, not just messages." — [cognition.ai/blog/dont-build-multi-agents](https://cognition.ai/blog/dont-build-multi-agents)

### §1.2 取捨依據

平行不是免費的。判斷一個 step 是否該平行：

| 判據 | 平行 | 不要平行 |
|:-----|:-----|:--------|
| 子任務獨立性 | 真獨立（無 shared mutable state） | 互相依賴 |
| Context 連續性 | 任務本身不需上下文（fresh start OK） | 鏈式推理（每步依賴前步） |
| 結果可彙整 | 結構化、可機械合併 | 需要對話討論才能收斂 |
| 成本承受度 | 子任務夠大（> 500 tokens 工作量） | 子任務小（overhead > 收益） |
| 反向警告 | Drift 風險低 | Drift 風險高（需共享決策軌跡） |

**Auto-TRIZ 套用**：
- Step 0/1/4 = chain-of-thought heavy → **不該平行**（Cognition 警告會直接生效）
- Step 2 多 TC、Step 5 多檔生成、SIM 矩陣 cell = 真獨立 → **可以平行**

### §1.3 設計順序

1. 先用單 agent + skill 跑通整條流程（baseline）
2. 識別 baseline 中的瓶頸 step
3. 評估該 step 的平行判據（§1.2）
4. 滿足才升格為 agent（§4 升格判據）

**反向**：不要從「我要做 multi-agent」開始設計。先有 baseline，後有平行。

---

## §2 七種市場模式

每個模式：1 行定義 + 適用 + 不適用 + 範例。

### §2.1 Supervisor-Worker（中央路由）

**定義**：一個中央 LLM 每回合決定派哪個 worker。
- **適用**：異質專家、動態路由、需中央 audit trail
- **不適用**：高度平行的獨立工作（supervisor 變瓶頸）
- **範例**：LangGraph Supervisor、CrewAI hierarchical Process、OpenAI triage agent

### §2.2 Map-Reduce Fan-out（分發-彙整）

**定義**：產生 N 個獨立子任務 → 平行派 → 收回結果做 reduce。
- **適用**：breadth search、per-item 分析、參數掃描
- **不適用**：子任務會修改共享狀態、有先後順序
- **範例**：LangGraph `Send` API、OpenAI `asyncio.gather`、Claude Code 平行 `Agent` 呼叫、CrewAI `kickoff_for_each`

### §2.3 Sequential Handoff（Swarm 接棒）

**定義**：peer agent 之間用 handoff tool 移交控制權，誰拿到 token 誰主導。
- **適用**：「對的專家」隨對話演進變化（triage → billing → tech）
- **不適用**：平行工作；無終止守衛會 ping-pong
- **範例**：LangGraph Swarm、AutoGen Swarm、OpenAI handoffs

### §2.4 Parallel Critic / Debate（多重審查）

**定義**：多個 agent（或同 agent N 次）產候選 → 一個 judge 或投票收斂。
- **適用**：減少單模型偏誤、評估歧義輸出、self-consistency
- **不適用**：確定性流程；對成本敏感的路徑
- **範例**：AutoGen multi-agent debate、OpenAI evaluator-loop、mixture-of-agents

### §2.5 Hierarchical Planner-Executor（Magentic 模式）

**定義**：planner 建 ledger → orchestrator 逐步派 → 自我反思 + 失速恢復。
- **適用**：開放式、長 horizon、分解模糊的任務
- **不適用**：短而明確的任務（overhead > 收益）
- **範例**：AutoGen Magentic-One、Devin planner

### §2.6 Stateful Graph（狀態圖）

**定義**：state 是合約；node 是純函式；channel 有顯式 merge 語意。
- **適用**：可審計流程、確定性 replay、混合平行/序列分支
- **不適用**：探索式對話（圖的剛性 > 收益）
- **範例**：LangGraph `StateGraph`、CrewAI Flows

### §2.7 Blackboard / Shared Filesystem（黑板）

**定義**：agent 透過讀寫共享檔案 / store 通訊，不直接傳訊息。
- **適用**：大型工件（程式碼、文件、資料集）超過訊息容量；跨 session 持久化
- **不適用**：併發寫衝突；需要鎖機制紀律
- **範例**：Claude Code 用 filesystem 協調、CrewAI memory store

---

## §3 Claude Code 平行機制

本系統建在 Claude Code 之上（`backend/app/harness/` 是 Claude Code 風格 agent loop），所以平行的具體實作以 Claude Code 機制為主。

### §3.1 Agent tool 平行 spawn

> **單訊息多 `Agent` 呼叫 = 平行 spawn**。Claude Code runtime 會把同一訊息中的多個 Agent tool calls 並發執行，不是 sequential。

```
main agent
└─ 一條訊息發出 [Agent(TC1), Agent(TC2), Agent(TC3)]
   └─ runtime 並發跑 3 個 subagent
      └─ 全部完成 → main 收到 3 個 summary（同步阻塞）
```

來源：[code.claude.com/docs/en/subagents.md](https://code.claude.com/docs/en/subagents.md)

### §3.2 Subagent 類型

**內建**（無需設定）：
- `general-purpose`：完整能力
- `Explore`：唯讀工具（Glob / Grep / Read），用於 investigation
- `Plan`：planning mode 邏輯
- `code-reviewer`：code review 專用

**自訂**（在 `.claude/agents/*.md`）：

```yaml
---
name: triz-analyst
description: 何時應該派這個 agent 接手（main agent 用此判斷）
model: opus  # 可指定 haiku 省成本
tools: ["Read", "Grep", "Glob"]  # 工具白名單；省略 = 全工具
---

# Markdown body — 此 agent 的 system prompt
```

### §3.3 Context 隔離

**Subagent 看得到**：
- spawn prompt（main 給的指令）
- 專案 `CLAUDE.md`
- `.claude/skills/`、`.claude/agents/` 定義
- 連線的 MCP servers

**Subagent 看不到**：
- main agent 的對話歷史
- sibling subagent 的結果
- 其他環境狀態（除 cwd 之外）

**回報**：subagent 結束時返回**精煉 summary**（不是原始 tool output），main 把多個 summary 整合進對話。

### §3.4 Blocking Aggregation

> Subagent 回應**不是 streaming**。main 要等所有 subagent 完成才能看到結果。

意義：Step 2 派 5 個 TC analyst → main 等到 5 個都回來才彙整。預估時間 = max(5 個 agent 時間)，不是 sum。

### §3.5 成本模型

| 規模 | 成本 | 適用 |
|:-----|:-----|:-----|
| 3-5 subagent | 線性 3-5x | **甜蜜點**（research、review、competing hypotheses） |
| 10+ subagent | 邊際遞減 + 協調 overhead | 警示 |
| 50+ subagent | 不切實際 | 改用 workflow orchestration |

每個 subagent 有獨立 context window（~2-6K token），加上 main 等待時也消耗 token，**總成本約等於 N+1 倍單次呼叫**。

### §3.6 不能做的事

| 限制 | 影響 |
|:-----|:-----|
| Subagent 不能再 spawn subagent | 無 nested fan-out |
| Subagent 之間不能直接通訊 | 必須走 main 彙整或 filesystem 黑板 |
| 無共享 state | 黑板要靠檔案系統 |
| 始終 blocking | 無真背景執行（背景任務改用 TaskCreate） |
| 無 spawn-time 模型切換 | model 寫死在 agent 定義 |

### §3.7 Foreground vs Background

| 模式 | 用途 |
|:-----|:-----|
| Foreground（預設）| Step 2-3-4 都用這個。要彙整就阻塞等。 |
| Background | 長時間獨立任務（如 research watch）。**Auto-TRIZ 不需要**。 |

---

## §4 Agent vs Skill 設計分野

兩者並存於 `.claude/`，不是替代關係。

| 面向 | Agent | Skill |
|:-----|:------|:------|
| 觸發 | main 判斷自動派 | 使用者打 `/skill-name` 或 main 自動載入 |
| 執行 | 平行（多個同訊息 spawn）| 序列（inline 進對話） |
| Context | 獨立 window | inline 載入 |
| 用途 | 需要獨立 investigation、避免 context flood、真平行 | 知識參照、檢查清單、領域慣例、流程模板 |
| 回傳 | 精煉 summary | 完整內容變成對話一部分 |

### §4.1 Skill → Agent 升格判據

當一個 skill 出現以下信號 → 考慮升為 agent：

1. **執行超過 5-10 turns** → context 變大，inline 不划算
2. **會 flood main context**（大量 search log / 中間產出）
3. **真獨立**（不需要與 main 對話，spawn 後自己跑完）
4. **需要平行**（同一段時間跑 N 個實例）

如果只是「想模組化」但 inline 跑得好好的 → **保持 skill**。Cognition 警告：把不需要平行的東西做成 multi-agent，是引入 drift 的最常見方式。

### §4.2 Auto-TRIZ 範例

| 元件 | 為什麼 | 形態 |
|:-----|:-------|:-----|
| `triz-router`（入口路由） | 短決策、需 context 連續 | **Skill** |
| `triz-scoping`（Step 0） | 5Why 鏈式、人在環裡 | **Skill** |
| `triz-model`（Step 1） | FA + SF 建模需上下文 | **Skill** |
| `triz-contradict`（Step 2 supervisor + Step 3） | 派多 TC、彙整 SIM | **Skill 內呼叫 Agent**（hybrid） |
| `triz-analyst`（單 TC worker） | 真獨立 + 可平行 | **Agent** |
| `triz-verify`（Step 4） | 中央 rubric，需 cohesion | **Skill** |
| `triz-wi`（Step 5） | 多檔產出，可平行 | **Skill 內呼叫 Agent**（hybrid） |

---

## §5 反模式

### §5.1 Unbounded fan-out

「對每個 39 參數派一個 agent 評分」= 39 subagent。
- 成本：39× 單次呼叫
- Context flood：39 個 summary 回來淹掉 main
- 替代：用 KB 查表（規則引擎），LLM 只在需要具體化時跑

### §5.2 Deep nesting

希望 subagent 再 spawn subagent。**Claude Code 不支援**。  
- 替代：所有 spawn 從 main 發出，subagent 把需要的子任務透過黑板回報，main 再派下一輪

### §5.3 Sequential fake-parallelism

迴圈內每次 spawn 一個 subagent → 等回來 → 再 spawn 下一個。
- 這是序列，不是平行，沒省時間，還白付 N 倍 context overhead
- 替代：一條訊息發 N 個 Agent calls

### §5.4 Cognition Drift（共享軌跡缺失）

派兩個 agent 各做「設計左半邊」「設計右半邊」，期待結果視覺一致。
- 真實：兩個 agent 各自做隱含決策（顏色、字體、間距），結果不一致
- 替代：要嘛單 agent 做完整體再分塊細化，要嘛把樣式約束做成 skill 讓兩 agent 共同讀

### §5.5 用 Agent 做應該是 Skill 的事

把「載入 39 參數表」做成 agent。
- 後果：每次都付一份 subagent context overhead
- 替代：skill 載入即可

---

## §6 Auto-TRIZ Step 對應編排（核心表）

下表是兩份研究 + Cognition 警告綜合後的最終建議。

| Step | 模式 | 形態 | 平行度 | 理由 |
|:-----|:-----|:-----|:-------|:-----|
| **0 問題定向** | Single-thread + 唯讀證據 sub | Skill（人在環）| 1 + 偶發 1 | 5Why 鏈式推理；fan-out 會斷思路。可選派一個唯讀 `Explore` sub 撈證據。 |
| **1 功能建模** | Hierarchical Planner-Executor 輕量 | Skill 主導 | 1 主 +（可選）edges 平行 | FA 拓撲先定，子邊（mechanical / thermal / signal）可平行填，但通常不必要。 |
| **2 多 TC 識別** | **Map-Reduce Fan-out** | Skill 派 N 個 `triz-analyst` Agent | **N = 3-5** | 每個 TC 獨立做 39×39 矩陣查表 + 原理具體化。**最強平行候選**。 |
| **3 PC 深挖 + 原理具體化** | Parallel Critic / Debate | Agent 內子段 + 收尾 judge | 2-4 | 候選原理通常 2-4 個，每個獨立做具體化，再 judge 排名。 |
| **3b 精篩 SIM** | Map-Reduce + reducer | Skill 內 `asyncio.gather` 風 | M×N cells | 每個 (TCᵢ, 解法ⱼ) 獨立評分，reducer 拼回矩陣。 |
| **4 驗證** | Supervisor-Worker | Skill 主導 | 1 + 3 critic（可選）| 中央 rubric 防 drift；critic 平行做 feasibility / cost / manufacturability 各一份。 |
| **5 工程輸出** | Stateful Graph + Blackboard | Skill 主導，內派多檔生成 Agent | WI / MC / ICD 各一 | 跨檔互引（MC 餵 WI、ICD 引 MC），用黑板協議避免 race。 |
| **SIM 矩陣彙整** | Map-Reduce + 收尾 critic | Skill | M×N + 1 sanity | 每 cell 獨立平行；收尾 critic 檢查鄰接 cell 評分一致性。 |

### §6.1 為什麼 Step 0/1/4 不大量平行

對應 Cognition 警告：

- **Step 0（5Why）**：每個 why 依賴前一個答案。fan-out 不知道「前一答」是什麼 → 切斷因果鏈。
- **Step 1（FA）**：組件交互需要全局視圖。子邊平行填看似可行，但實際填的時候會發現「這條邊的功能依賴另一條邊的副產品」，獨立 agent 看不到。
- **Step 4（驗證）**：驗證需要對「整個方案」做 4 問複雜度判定。獨立 critic 看不到全局時容易 over-call「補丁」或漏看「進化」。

→ 這三步保持 single-thread，必要時用 read-only sub agent 撈資料但不做決策。

### §6.2 為什麼 Step 2/3b/5 適合平行

- **Step 2（多 TC）**：每 TC 的 39 參數對 + 矩陣查表 + 原理具體化是**完全機械的獨立作業**，不需 cross-TC 上下文。
- **Step 3b（SIM cell）**：每 cell 是「解法 A vs 解法 B 在 OZ/OT 重疊時的 +1/0/-1 判定」，看 4-5 行就能評分。
- **Step 5（WI/MC/ICD）**：每份檔的內容來源不同（WI ← 流程；MC ← 物性；ICD ← 介面），獨立性高。跨檔引用透過黑板協議（§8）在彙整階段對齊。

---

## §7 現有 `.claude/{skills,agents}` 重組建議

### §7.1 現況盤點

```
.claude/skills/
├── triz-router/        skill（路由）
├── triz-scoping/       skill（Step 0）
├── triz-model/         skill（Step 1）
├── triz-contradict/    skill（Step 2-3）
├── triz-verify/        skill（Step 4）
├── triz-wi/            skill（Step 5）
├── tr-router/          skill（TR 入口）
├── tr-gate/            skill（TR gate review）
├── tr-fea-assist/      skill（FEA 輔助）
├── tr-test-report/     skill（測試報告）
└── tr-dfm/             skill（DFM 審查）

.claude/agents/
└── triz-analyst.md     agent（單一 TRIZ 分析）
```

### §7.2 重組對應 §6 的建議

| 現有 | 重組後 | 動作 |
|:-----|:-------|:-----|
| `triz-router` skill | 不動 | Skill 形態正確 |
| `triz-scoping` skill | 不動 | Step 0 不平行 |
| `triz-model` skill | 不動 | Step 1 不平行 |
| `triz-contradict` skill | **保留 skill 但 Step 2 內呼叫 `triz-analyst` agent fan-out** | skill 變 supervisor，agent 變 worker |
| `triz-analyst` agent | **改寫為 Step 2 worker**（per TC 一個實例）| 見下文 §7.3 + 改寫 `.claude/agents/triz-analyst.md` |
| 新增 `triz-critic` agent | **Step 3 原理具體化的 judge** | 用 Parallel Critic 模式時必要；可先延後 |
| `triz-verify` skill | 不動 | Step 4 用 supervisor + 可選 critic agent |
| `triz-wi` skill | **保留 skill 但 Step 5 內呼叫多個 doc-generator agent** | 三個檔（WI/MC/ICD）平行產出，黑板協議彙整 |
| `tr-*` skill 群 | 不動 | TR 流程是 gate-by-gate，不平行 |

### §7.3 `triz-analyst` agent 新角色

定位：**Step 2 fan-out 的 worker**，每個 TC 派一個實例。

關鍵特徵：
- **不知道 sibling worker 的存在**
- **不對話**，直接接 Step 2 supervisor 派的單一 TC，產出 TC→PC→SF 推理鏈
- **黑板讀寫協議**（§8）：讀 session 上下文 + 寫 per-TC 解法檔
- 完成即回 summary，由 main 彙整

實際 agent definition file 改寫見 `.claude/agents/triz-analyst.md`（本次同步更新）。

---

## §8 Filesystem 黑板協議

Claude Code 沒有原生 shared state，黑板靠檔案系統。本系統的黑板位於 `.claude/context/triz/`。

### §8.1 黑板檔命名

| 檔型 | 命名 | 寫入者 | 讀取者 |
|:-----|:-----|:-------|:-------|
| TRIZ session 主檔 | `.triz-state.json` | 各 skill / agent | 全體 |
| TR gate 主檔 | `.tr-state.json` | tr-* skill | 全體 |
| Step 過程記錄 | `session-{step}-{YYYYMMDD-HHMM}.md` | 該 step skill | 下一個 step |
| Step 2 per-TC 解法 | `session-step2-tc{N}-{YYYYMMDD}.md` | `triz-analyst` worker N | Step 2 supervisor |
| Step 5 doc 產出 | 落地在 `docs/_harness/engineering/` | `triz-wi` 內的 doc-generator | 工程師 |

### §8.2 寫入順序與鎖

Claude Code 沒有檔案鎖原語，靠**約定**：

1. **單寫者規則**：每個 session 黑板檔只有一個負責 skill / agent 寫
2. **Append-only 規則**：跨 step 中間記錄用 append（用 timestamp 標記），不要 overwrite
3. **State JSON 集中變更**：`.triz-state.json` 只由 router skill 變更，其他 skill 經由 router 提交變更請求
4. **平行 worker 用獨立檔**：Step 2 派 5 個 worker，產出 5 份 `session-step2-tc{N}-*.md`，避免寫衝突

### §8.3 跨 Agent 交接格式

當 Step 2 supervisor 派 worker 時，spawn prompt 必須包含：

```
- TC 編號（TC1 / TC2 / TC3）
- 改善參數 + 惡化參數的自然語言描述
- 黑板路徑（讀：session-step1-*.md 取 SF 圖；寫：session-step2-tc{N}-*.md）
- 期望產出格式（DK-02 §5.4 SF 標準解格式）
- 終止條件（完成 SF 標準解 + 科學效應導入；不做 Step 4 驗證）
```

Worker 完成後回給 main：
- summary：「TC{N} 產出 X 個候選方案，最優方案在 OZ=[...] / OT=[...]」
- 完整解法檔路徑：`session-step2-tc{N}-*.md`

Main 彙整 N 個 summary → 進入 §6 Step 3b 精篩 SIM。

### §8.4 衝突處理

| 衝突 | 偵測 | 處理 |
|:-----|:-----|:-----|
| 兩個 worker 寫同檔 | 違反 §8.2 單寫者 | 設計錯誤，重派 |
| Worker 產出格式不對 | Supervisor 解析失敗 | 重派該 worker，prompt 加 explicit format constraint |
| Worker 找不到必要輸入 | Worker 回 summary 標 BLOCKED | Supervisor 補資料後重派 |

---

## §9 與 backend harness 實作的關係

當前 `backend/app/harness/` 是 Claude Code 風格 single-agent loop（看 `agent.py`、`cli.py`），**還沒有實作 multi-agent 編排**。本 DK 是設計層的指引；實作層的 multi-agent 等 backend 後續 milestone（不在本次 scope）。

過渡期作法：
- main agent 透過 Claude Code 原生 `Agent` tool 平行呼叫 — 這是「使用 Claude Code 平台能力」，不需要 backend 實作
- backend harness 維持 single-agent，做 router + skill 載入；多 agent 由 Claude Code runtime 處理

當 backend 要實作 multi-agent 時，可參考 §2 七種模式選一個對應的：
- 最簡單：Map-Reduce Fan-out（Step 2/3b/5 都適用）
- 進階：Stateful Graph（Step 5 多檔互引時）

---

## §10 速查

**何時平行？**
- 子任務真獨立 + dimension > 500 token + 結果可彙整 → Map-Reduce 派 3-5 agent

**何時不平行？**
- 鏈式推理（Step 0 5Why） / 全局視圖（Step 1 FA / Step 4 驗證） / 子任務小 → 保持 skill 線性

**Skill 還是 Agent？**
- Inline 知識 / 檢查清單 / 流程模板 → Skill
- 可平行 + context 隔離 + 真獨立 → Agent

**現有 `.claude/` 該怎麼動？**
- 保留所有 skill（11 個）
- 改寫 `triz-analyst` agent 為 Step 2 worker（本次同步進行）
- Step 2/5 在 skill 內透過 main agent 的 `Agent` tool 平行 spawn 呼叫，不需新增 agent 檔
