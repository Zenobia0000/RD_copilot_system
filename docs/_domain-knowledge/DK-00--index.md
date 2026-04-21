# Domain Knowledge — RD 設計方法論專業知識

> 驅動 AI Agent 的領域知識庫。4 份 MECE 文件，各有專屬領域，無重複內容。

---

## 閱讀順序

| 文件 | 專屬領域 | 讀完你會知道 |
|------|---------|------------|
| [DK-01 設計哲學與流程](DK-01--design-philosophy-and-process.md) | 核心哲學、8 步驟流程、Phase/Gate、知識增強 | 整個系統怎麼運作（what + when） |
| [DK-02 TRIZ/SCAMPER 發散引擎](DK-02--triz-scamper-divergence-engine.md) | AutoTRIZ 架構、TC/PC/SF、SCAMPER、Anti-Anchor、收斂圖 | 如何結構化產生候選方案（how to diverge） |
| [DK-03 KT 決策框架](DK-03--kt-decision-framework.md) | MUST/WANT/Adverse Consequences、7 大 WANT 條件、AI 邊界 | 如何結構化篩選與決策（how to converge） |
| [DK-04 資料模型與 Gate 參考](DK-04--data-model-and-gate-reference.md) | 7 核心工件 schema、Gate 條件、Prompt 對照 | 欄位叫什麼、Gate 要什麼（data reference） |

---

## MECE 邊界規則

- **DK-01**：每個 Step 產出什麼、Gate 要什麼（流程層）
- **DK-02**：TRIZ/SCAMPER 怎麼執行（發散機制層）
- **DK-03**：KT 決策怎麼打分（收斂機制層）
- **DK-04**：欄位定義與 API 路由快照（資料層）

跨文件引用限制：每個邊界點最多一句（e.g.,「TRIZ 執行細節：見 DK-02」）。

---

## Agent 對應

| Agent | 主要參考 |
|-------|---------|
| Analyst (analyst.py) | DK-01 (Steps 1-2) |
| TRIZ Solver (triz_solver.py) | DK-02 |
| TRIZ Critic (triz_critic.py) | DK-02 (convergence graph) |
| SCAMPER Feedback (scamper_feedback.py) | DK-02 (SCAMPER 7-column) |
| Evaluator (evaluator.py) | DK-03 |
| Knowledge WB (knowledge_wb.py) | DK-01 (Step 8) |

---

## 相關文件（已移出 _domain-knowledge）

| 文件 | 新位置 | 性質 |
|------|--------|------|
| VC00--workflow-manual | `docs/01-define/` | 產品開發流程手冊（5D gate 映射） |
| VC01--development-workflow-cookbook | `docs/01-define/` | 開發流程總覽（Planning→QA × 5D） |
| 系統規格定義書 | `docs/02-design/specs/` | API 端點 + REST 路由完整規格 |
