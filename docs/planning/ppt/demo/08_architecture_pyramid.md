# 08 — 架構四層金字塔

## Slide 標題

**系統長這樣：四層分層架構（Harness-first Design）**

---

## Speaker Notes

> 這頁用最簡單的金字塔說明系統怎麼跑。最上面是你看到的介面，下一層是工作流引擎把 TRIZ 5 步加上 TR 10 階段串起來，再下一層是多 agent 編排，最底層是 LLM 加上 TRIZ 知識庫。架構採 harness-first 設計 — 業務邏輯寫在 markdown skill 裡可審查可版控，Python runtime 只負責調度，技術可換但流程不變。

**過場到下一頁**：「中間那層工作流引擎，我們再拉開看看⋯」

---

## 視覺布局

- **排版**：四層金字塔（左側），技術棧標註（右側）
- **左側金字塔**：

  ```
       ┌─────────────────────────────────────────┐
   L1  │  🖥️  互動層 (Interface)                  │
       │  ⚛️ React 18 · ⚡ FastAPI · 🔌 CLI       │
       ├─────────────────────────────────────────┤
   L2  │  🔄 工作流引擎 (Workflow Engine)         │
       │  📋 13 Markdown Skills · ⚙️ State Machine│
       ├─────────────────────────────────────────┤
   L3  │  🤖 編排層 (Orchestration)               │
       │  🤝 Supervisor-Worker · 🌐 Map-Reduce   │
       │  🛠️ Tool Registry · 🧭 Skill Loader     │
       ├─────────────────────────────────────────┤
   L4  │  🧠 底層 (Foundation)                    │
       │  🔵 Claude API · 📚 TRIZ KB · 🐘 Supabase│
       └─────────────────────────────────────────┘
  ```

- **配色**：頂層淺色（熟悉）、底層深色（抽象）；icon 用統一色系
- **底部標籤**：`Harness-first：邏輯在 markdown，runtime 只調度，state 在 filesystem`

---

## 重點內容

### 四層分層（每層職責 + 技術棧）

| 層 | 名稱 | 你看到的 | 技術棧 | 關鍵概念 |
|:---|:-----|:---------|:-------|:---------|
| **L1** | 🖥️ 互動層 | Web 頁面、上傳框、進度條 | ⚛️ React 18 · ⚡ FastAPI · 🔌 CLI / Slash Commands | RESTful API |
| **L2** | 🔄 工作流引擎 | 「正在 Step 2 求解」進度 | 📋 13 Markdown Skills · ⚙️ JSON State Machine | 📚 [Workflow as Markdown] |
| **L3** | 🤖 編排層 | （透明）多 agent 協作 | 🤝 Supervisor-Worker Pattern · 🌐 Map-Reduce · 🛠️ Tool Registry | 📚 [Multi-Agent Orchestration] |
| **L4** | 🧠 底層 | （透明）AI + 知識 | 🔵 Claude API (Anthropic SDK) · 📚 TRIZ Knowledge Base · 🐘 Supabase / PostgreSQL | 📚 [LLM + RAG] |

### Harness-first 三原則

- 📝 **業務邏輯在 markdown** — 流程定義與 gate 規則寫在 skill 檔案，可獨立版控與審查
- ⚙️ **Runtime 只做調度** — Python 載入 skill、呼叫 tool、管理 state，不寫死業務流程
- 🗄️ **State 在 filesystem** — `.triz-state.json` / `.tr-state.json` 用 JSON 持久化，可 git 追蹤

> 💡 **對你的意義**：流程文件 = 可執行流程。換掉 Claude 改用其他 LLM，TRIZ 流程不變；改變流程定義，不需 redeploy 程式碼。

---

## Tech Glossary（給有興趣的讀者）

- 📚 **Harness-first Architecture** — 業務邏輯、編排規則、知識庫都以「資料」形式存在（markdown / JSON），runtime 是輕量 harness 負責動態載入。對比傳統「邏輯寫在 code 裡」的設計
- 📚 **Skill Loader** — 動態載入 markdown 定義的 skill 作為 LLM system prompt（類似 plugin 機制）
- 📚 **State Machine（外置式）** — 狀態不在記憶體裡，存在 JSON file，跨 session 可恢復
- 📚 **Tool Registry** — 把可呼叫的「工具」（讀檔、寫檔、查 KB、呼叫子 agent）統一註冊，LLM 透過 function calling 介面使用

---

## 數據 / 引用

- 5 層完整堆疊（含 Tool Registry / SSOT 分層）— `docs/planning/ppt/28_block4_harness_architecture.md` §A
  - 普通人版簡化為 4 層（Tool Registry 併入 L3、SSOT 併入 L4）
- 13 個 Skills 清單 — `28_block4_harness_architecture.md` §C
- Harness 設計理念 — `docs/planning/05_architecture.md`
- 內容位置邊界（為何選 markdown + JSON）— `.claude/CLAUDE.md` §Content Boundary Policy

---

## 素材引用

- 五層完整圖（backup slide for 工程同事）— `28_block4_harness_architecture.md` §3 版面配置
- 完整 13 skills 對應 Phase 表 — `28_block4_harness_architecture.md` §C
