# 10 — 多 Agent 並行 + RAG 知識庫

## Slide 標題

**Multi-Agent Orchestration + RAG：為什麼比單一 LLM 強**

---

## Speaker Notes

> 為什麼這個系統比直接問 ChatGPT 強？兩個關鍵架構決策：第一，我們用 RAG 把 TRIZ 知識庫 — 40 個發明原理、76 個標準解、矛盾矩陣 — 變成 AI 可查詢的結構化知識，不是憑印象回答，是查表加結構化推理。第二，遇到複雜問題系統會用 Map-Reduce 模式 spawn 多個 worker agent 並行求解，supervisor 負責合併。每個結論都對應 TRIZ 原理編號 + Evidence ID，可審計可回查。

**過場到下一頁**：「這些技術做給誰用？不同角色獲得不一樣⋯」

---

## 視覺布局

- **排版**：上半多 agent 拓撲，下半 RAG 知識庫
- **上半 🌐 Multi-Agent Orchestration**（佔 50%）：

  ```
                    🤝 Supervisor
                  (triz-router)
                         │
         ┌───────────────┼───────────────┐
         │               │               │
   🤖 Worker A      🤖 Worker B      🤖 Worker C
   (TC-A: 散熱)    (TC-B: 功率)    (TC-C: 噪音)
   🛠️ tools         🛠️ tools         🛠️ tools
         │               │               │
         └───────────────┼───────────────┘
                         ▼
                  📊 Reduce / Merge
                  (SIM 矩陣 + 合併解)
  ```

  - 標籤：「Map-Reduce Pattern · 3 TC → 3 worker 並行 → supervisor 合併」

- **下半 🔍 RAG (Retrieval-Augmented Generation)**（佔 50%）：

  ```
  ┌─────────────────────────────────────────┐
  │  📚 TRIZ Knowledge Base                  │
  │  ├─ 🧬 40 發明原理 (Inventive Principles) │
  │  ├─ 🔧 76 標準解 (SF Standard Solutions) │
  │  ├─ 📐 矛盾矩陣 (39×39 Contradiction TBL)│
  │  ├─ 📈 8 演化趨勢 (TESE Lines)            │
  │  └─ 🗂️ 11 UML 推理圖                      │
  └────────────────┬────────────────────────┘
                   │ retrieval
                   ▼
            🧠 LLM (Claude)  ←──🔁  🛠️ Tool Use
                   │ generation                │
                   ▼                           │
         🧬 Structured Output ─→ 📊 State ─────┘
         (TC, PC, SF, Px, OZ)
  ```

  - 標籤：「KB 不在 prompt 裡漂浮，是 retrieve-then-reason」

- **底部**：`每個結論 → TRIZ 原理編號 + 🗂️ Evidence ID + 信心等級（HIGH/MEDIUM/LOW）`

---

## 重點內容

### 為什麼比單一大 LLM 強（5 個架構決策）

| 設計決策 | AI 術語 | 解決的問題 |
|:---------|:--------|:-----------|
| 知識駐留 | 🔍 **RAG** (Retrieval-Augmented Generation) | LLM 對 TRIZ 規則的「幻覺」 |
| 任務分工 | 🌐 **Map-Reduce** + 🤝 Supervisor-Worker | 單一 LLM context 不夠 + 並行加速 |
| 結構化推理 | 🧬 **Structured Reasoning** (TC→PC→SF) | 自由發揮無法審計 |
| 工具呼叫 | 🛠️ **Tool Use** / Function Calling | LLM 無法直接讀寫檔案 / 查 KB |
| 狀態持久 | 📊 **Stateful Sessions** (JSON state) | LLM 無記憶（contextual amnesia）|
| 可稽核 | 🗂️ **Evidence Registry** + Claim ID | 結論無法回查來源 |

### eBike 案例的具體展現

- 🌐 3 個矛盾（散熱 / 功率密度 / 噪音）→ Map 階段 spawn 3 個 worker
- 🔍 每個 worker 用 RAG 查矛盾矩陣（39×39）找對應原理（如 P17×P8 → 推薦 #3, #36, #35）
- 🧬 結構化推理輸出：`TC → PC → SF Standard Solution`（強制 schema）
- 🗂️ 12 條 Claim ID + 信心等級（83% HIGH+MEDIUM）
- 📊 SIM 矩陣（+1/0/-1）自動偵測多 TC 衝突

### 越用越聰明（Compounding Effect）

- 📥 每個專案的 Evidence Registry 沉澱進知識庫
- 🧪 失效模式 / 設計規則 / 解法案例自動歸類為 6 類知識資產
- 🔁 下個專案的 RAG 可直接 retrieve 上個專案的 know-how

> 💡 **對你的意義**：你不是「跟 AI 聊天」，你是在「驅動一台有規則、有記憶、可審計的工程推理機」。

---

## Tech Glossary（給有興趣的讀者）

- 📚 **RAG** (Retrieval-Augmented Generation) — LLM 回答前先從知識庫 retrieve 相關內容塞進 context，避免「幻覺」與過時資訊。本系統 KB 結構化（不只向量），可精準查表
- 📚 **Map-Reduce Pattern** — 分散式運算經典模式：Map 階段並行處理子任務，Reduce 階段合併結果。AI agent 場景下，每個 worker 是獨立 LLM session
- 📚 **Supervisor-Worker** — 一個 supervisor agent 負責任務分派與結果合併，多個 worker agent 各自獨立執行。本系統 `triz-router` 是 supervisor，`triz-analyst` 是 worker
- 📚 **Tool Use / Function Calling** — LLM 透過結構化介面呼叫外部工具（讀檔、查 KB、呼叫子 agent），是 agent 的核心能力
- 📚 **Structured Output** — 強制 LLM 產出符合 schema 的 JSON（如 `{TC, PC, SF}`），不是自由文字。可下游解析
- 📚 **Context Engineering** — 主動設計 LLM 看到的 context（哪些 state、哪些 KB 片段、裁剪策略），對長流程任務勝率影響極大
- 📚 **Evidence Registry** — 每條 AI 產出的結論掛上 Claim ID + 來源 + 信心等級，可逐項回查與更新

---

## 數據 / 引用

- 多 Agent Map-Reduce 編排 — `docs/methodology/DK-03--multi-agent-orchestration.md` §6
- TRIZ 知識庫結構 — `knowledge/triz/`, `docs/methodology/DK-02--triz-mechanisms.md`
- Evidence Registry 12 條 / 83% — eBike session line 491-499
- 結構化推理 schema — `docs/methodology/DK-04--data-model-and-gate.md` §13 Entities
- Knowledge Agent（6 類資產自動產出）— `docs/planning/02_prd.md` US-303

---

## 素材引用

- Agent fan-out 圖：可重繪 mermaid `graph TD`
- RAG 流程：可仿 LangChain / LlamaIndex 標準圖示
- 11 張 UML 推理圖在 `docs/methodology/uml/00-11_*.md`，可選一張當配圖
- AI agent 圖示資源：可用 Mermaid 內建 icon 或 emoji 統一風格
