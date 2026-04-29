# 09 — 雙引擎工作流

## Slide 標題

**雙引擎工作流：先想清楚（TRIZ），再做出來（TR）— 由 13 個 Skill 接力**

---

## Speaker Notes

> 工作流分成兩半，中間 G3 概念凍結是分水嶺。左半 TRIZ 引擎 6 個 skill 處理「想清楚」— 問題定向、功能建模、矛盾求解、驗證、文件產出。右半 TR 引擎 7 個 skill 處理「做出來」— Gate 審查、FEA、測試、DFM、SPC、PPAP。每個 skill 都採 ReAct 模式（觀察→推理→行動→更新狀態），共用一套 JSON state，前後端零斷層。

**過場到下一頁**：「兩個引擎內部怎麼協作？多 agent 並行加 RAG 知識庫⋯」

---

## 視覺布局

- **排版**：水平雙引擎流程圖 + 底部 state 持久層
- **左半 🧪 TRIZ 引擎**（淺藍）：

  ```
  P0 SCOPE  →  P1 MAP   →  P2 RESOLVE  →  P3 SPECIFY
  🧭 router    🔍 scope    🧬 model       ✅ verify
               🛰️ scoping   ⚗️ contradict   📝 wi
  ```

- **G3 分水嶺**（粗紅線）：「🔒 Concept Frozen / TR0 Handoff」
- **右半 🏭 TR 引擎**（深藍）：

  ```
  P4 PROVE  →  P5 BUILD  →  P6 HARDEN   →  P7 SCALE
  🧮 fea      🔬 test     🏭 dfm         📊 spc
              ✅ gate     📋 gate         📦 ppap
                                          🛠️ sop
  ```

- **底部 State 持久層**：

  ```
  📊 .triz-state.json (session 級)  ──🔗──  📊 .tr-state.json (專案級)
  └─ Step 0-5 進度、Evidence、TC/PC/SF        └─ TR0-TR10 Gate 進展
  ```

- **配色**：TRIZ 藍綠（創造），TR 深藍（嚴謹），G3 紅線（警示）

---

## 重點內容

### 雙引擎對照（含 AI agent 模式）

| | 🧪 左半（G3 之前 · 發明性前端）| 🏭 右半（G3 之後 · 工程性後端）|
|:--|:------------------------------|:-----------------------------|
| **驅動引擎** | 🧠 TRIZ Reasoning Engine | 🚦 TR Gate Engine |
| **AI 模式** | 🎯 ReAct + 🧬 Structured Reasoning（TC→PC→SF）| 🎯 ReAct + 📋 Checklist Verification |
| **核心 Skill** | 6 個（🧭 router / 🛰️ scope / 🧬 model / ⚗️ contradict / ✅ verify / 📝 wi）| 7 個（✅ gate / 🧮 fea / 🔬 test / 🏭 dfm / 🛠️ sop / 📊 spc / 📦 ppap）|
| **State 模型** | 📊 `.triz-state.json` (session 級) | 📊 `.tr-state.json` (專案級) |
| **資料模型** | 13 Entity（Problem / TC / PC / SF / Px / OZ / OT / Solution / SIM / CCI ⋯）| Gate Review / FMEA / Control Plan / DVP&R |
| **變更成本** | ⏱️ 分鐘級（改 markdown）| ⏰ 週級（改模具/製程）|

### 13 Skill 接力的核心機制

- 🔄 **ReAct Loop** — 每個 skill 都是「Reason → Act → Observe」迭代
- 🔗 **Skill Handoff** — 上一個 skill 的 state 直接餵給下一個（不需人工轉譯）
- 🗂️ **Evidence Registry** — 每條結論掛 Claim ID，跨 skill 可追溯
- 📌 **Context Engineering** — 系統自動裁剪 context，只把相關 state 餵給當前 skill

> 💡 **對你的意義**：13 個 skill 像 13 個專業同事接力跑馬拉松，每人專精一段，共用一份病歷（state JSON），不會有資訊在交接時掉地上。

---

## Tech Glossary（給有興趣的讀者）

- 📚 **ReAct Pattern**（Reasoning + Acting）— LLM agent 經典範式：每步先思考、再行動、再觀察結果，迴圈推進。本系統每個 skill 都是 ReAct loop
- 📚 **Skill Handoff** — 不同 agent / skill 之間透過共享 state 傳遞工作，避免「LLM 接龍」常見的脈絡丟失
- 📚 **Context Engineering** — 主動管理塞進 LLM 的 context（只給相關的、剪掉雜訊），對長流程任務至關重要
- 📚 **Structured Reasoning（TC→PC→SF）** — 不是讓 LLM 自由發揮，而是強制走 TRIZ 三段式推理鏈（技術矛盾 → 物理矛盾 → 物質場），可審計
- 📚 **State Persistence (JSON)** — Session 不靠 LLM 記憶（會遺忘），靠外置 JSON 檔保存進度與決策

---

## 數據 / 引用

- 雙引擎銜接 — `docs/planning/ppt/26_block2_rdp8_core_flow.md` §B
- 6 + 7 Skills 完整清單 — `docs/planning/ppt/28_block4_harness_architecture.md` §C
- G3 分水嶺定義 — `docs/planning/18_flow_contract.md` §Global Panorama
- 雙層狀態機架構 — `docs/methodology/DK-04--data-model-and-gate.md`
- 13 Entity 資料模型 — `docs/methodology/DK-04--data-model-and-gate.md` §Data Model
- ReAct + Multi-agent 編排設計 — `docs/methodology/DK-03--multi-agent-orchestration.md`

---

## 素材引用

- 8-Phase + 雙引擎水平流程圖 — `26_block2_rdp8_core_flow.md` §3 視覺
- Cost-of-change 曲線（強化 G3 分水嶺意義）
- 13 Skill 完整 phase 對應表 — backup slide
