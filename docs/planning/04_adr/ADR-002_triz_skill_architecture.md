# ADR-002：TRIZ 推理層採 Skill-based 架構

---

**狀態 (Status)**：`Accepted`
**決策者 (Deciders)**：TL, ARCH, AI, TRIZ-SME
**決策日期 (Date)**：2026-04-21
**諮詢 (Consulted)**：RD-SME
**知會 (Informed)**：All

---

## Context & Problem Statement

TRIZ 推理閉環包含 6 個邏輯步驟（Step 0-5）+ TR 工程執行 5 個工具，需要可組合、可獨立測試、可被 AI agent 直接呼叫的架構。

**驅動因素**：
- TRIZ 步驟有清楚邊界（Step N 的輸出 = Step N+1 的輸入）
- 用戶可能跳步驟（e.g. 已知 TC 直接 Step 2，跳過 Step 0/1）
- AI agent（Claude Code）可直接 invoke 各 skill
- 不同步驟有不同 LLM 需求（Step 0 對話、Step 3 結構化）

---

## Considered Options

| Option | Pros | Cons |
|:-------|:-----|:-----|
| **Skill-based（每 step 一個 skill）** | 可組合、可獨立測試、AI agent 友好 | session state 管理複雜 |
| Monolithic TRIZ Service | 邏輯集中、好 debug | 重啟時 state 易遺失、不易選擇性執行 |
| Pipeline / DAG（Airflow/Prefect） | 工作流可視化 | overkill（任務粒度太細） |

---

## Decision Outcome

**選擇**：Skill-based — 6 個 `triz-*` skill + 5 個 `tr-*` skill

**Skill 清單**：

| Skill | 對應 | 職責 |
|:------|:-----|:-----|
| `triz-router` | 主入口 | 偵測問題類型、路由 |
| `triz-scoping` | Step 0 | 5Why / KT / CECA |
| `triz-model` | Step 1 | FA + SF 建模 |
| `triz-contradict` | Step 2+3 | TC/PC/SF 求解 |
| `triz-verify` | Step 4 | Px 驗證 + CCI |
| `triz-wi` | Step 5 | WI/ICD/MC 產出 |
| `tr-router` | TR 主入口 | 儀表板 + 路由 |
| `tr-gate` | — | TR1-TR10 Gate Review |
| `tr-fea-assist` | — | FEA 設定輔助 |
| `tr-test-report` | — | 測試報告產生 |
| `tr-dfm` | — | DFM/DFA 審查 |

---

## Consequences

### Positive
- 已驗證可行（ebike-drive-unit-v2 全 5 步完成）
- 用戶可以選擇性執行（如 SF-only 通道）
- AI agent 可直接 invoke 各 skill
- 內容位置邊界清晰：state JSON → `.claude/context/`，工程交付物 → `docs/engineering/`

### Risks
- session state 跨 skill 傳遞需嚴格契約（用 `.triz-state.json` 為 SSOT）
- skill 數量多，需 INDEX 維護（`.claude/skills/INDEX.md`）

---

## References

- TRIZ 策略 SSOT：`docs/_harness/auto_triz_strategy.md`
- Skill 規格：`.claude/skills/triz-*/SKILL.md` + `.claude/skills/tr-*/SKILL.md`
- 案例驗證：`.claude/context/triz/.triz-state.json`（ebike-drive-unit-v2）
