# Domain Knowledge — Auto-TRIZ R&D Copilot 方法論基底

> 5 份 MECE 文件 + 對齊 `docs/methodology/` SSOT。每份各有專屬領域，無內容重複。

---

## 閱讀順序

| 文件 | 專屬領域 | 讀完你會知道 |
|:-----|:---------|:------------|
| [DK-01 Auto-TRIZ 流程](DK-01--auto-triz-process.md) | 入口判定、Step 0-5 閉環、多 TC 路由、停止條件 | 整個系統怎麼運作（what + when） |
| [DK-02 TRIZ 機制](DK-02--triz-mechanics.md) | 39 參數、矩陣、40 原理、OZ-OT-Px、SF 76 標準解、SIM 評分 | TRIZ 引擎怎麼推理（how） |
| [DK-03 多 Agent 編排](DK-03--multi-agent-orchestration.md) | 七種市場模式、Claude Code 平行機制、Step 對應策略、反模式 | 為什麼這樣切 agent / skill（架構） |
| [DK-04 資料模型 / Gate](DK-04--data-model-and-gate.md) | 13 entity schema、TRIZ 內部 gate、TR 外部 gate、state JSON、黑板協議 | 欄位叫什麼、gate 要什麼（data） |
| [DK-05 領域底盤](DK-05--domain-fundamentals.md) | AICBD 工業 CV、5 心智模型、3 層 KPI、製造約束 | 為什麼某些方案在工廠根本跑不起來（domain） |

---

## SSOT 對應

| DK 檔 | 主要 SSOT 來源 |
|:------|:--------------|
| DK-01 | `docs/methodology/auto_triz_strategy.md` §0-9、`uml/02_main_flow.md`、`uml/05_multi_tc_strategy.md` |
| DK-02 | `docs/methodology/auto_triz_strategy.md` §3-5 + 附錄、`knowledge/triz/01-05_*.md` |
| DK-03 | Anthropic Claude Code 官方文件、市場平台研究（LangGraph / CrewAI / AutoGen / OpenAI Agents SDK / Cognition） |
| DK-04 | `docs/methodology/uml/00_domain_model.md`、`engineering/tr_gate_framework.md`、`uml/10_problem_lifecycle.md` |
| DK-05 | `docs/research/interview/domain_fundamentals.md` + `interview/domain_research/{battle_manual,industrial_cv_paradigms}.md` |

---

## MECE 邊界

- **DK-01**：每個 Step 該做什麼、Step 間怎麼路由（流程層）
- **DK-02**：TRIZ 工具如何執行 — TC 參數映射、PC Px 提取、SF 標準解（機制層）
- **DK-03**：把 Step 切成 agents/skills 的依據、何時平行、何時不該平行（架構層）
- **DK-04**：Step 之間傳遞什麼資料、gate 用什麼欄位判定（資料層）
- **DK-05**：在工業 CV 場景下，哪些 TRIZ 方案會被製造約束擋住（領域層）

跨文件引用：每個邊界點最多一句（例「TRIZ 機制細節：見 DK-02」），不重抄內容。

---

## Agent / Skill 對應

| Agent / Skill | 主要參考 DK |
|:--------------|:-----------|
| `triz-router` skill（入口路由） | DK-01 §2 入口判定 |
| `triz-scoping` skill（Step 0） | DK-01 §3 + DK-05（製造約束影響邊界） |
| `triz-model` skill（Step 1） | DK-01 §4 + DK-02 §1 |
| `triz-contradict` skill（Step 2-3） | DK-01 §5-6 + DK-02 §2-6 |
| `triz-analyst` agent（Step 2 worker） | DK-02 全部 + DK-03 §6 |
| `triz-verify` skill（Step 4） | DK-01 §7 + DK-04 §3 |
| `triz-wi` skill（Step 5） | DK-01 §8 + DK-04 §6 |
| `tr-router` / `tr-gate` skill（TR0-10） | DK-04 §3 + §6 |

---

## 維護規則

- DK-01..05 由人撰寫；skill / agent 只讀，不寫
- 內容變更必須先確認 SSOT (`docs/methodology/`) 是否有同步變動
- 跨檔引用用 `§n` 章節編號，不用行號（內容會變動）
