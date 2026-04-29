# ADR-008：Engineering Knowledge Graph 採 Frontmatter SSOT + Tool-Derived Views

---

**狀態 (Status)**：`Accepted`
**決策者 (Deciders)**：TL, ARCH, RD-SME
**決策日期 (Date)**：2026-04-29
**諮詢 (Consulted)**：AI, TRIZ-SME
**知會 (Informed)**：All

---

## Context & Problem Statement

`docs/engineering/` 在每次 TRIZ session（Step 5）後產出 22+ 份工程交付物：WI（Work Instructions）、ICD（Interface Control Documents）、MC（Material Cards）、Risk Register、KC List、TR Gate Framework。

這些檔案彼此**不是樹結構**，而是 **typed property graph**：

| 樹的假設 | 實際違反 |
|:---------|:---------|
| 每節點唯一父節點 | ICD-01 同時被 WI-01 / WI-03 / WI-04 引用 |
| 引用單向 | WI-01 ↔ WI-03 雙向（Loss map → 熱設計、熱限 → 馬達設計約束） |
| 同質節點 | 12+ 種節點類型（WI / ICD / MC / TC / SOL / Claim / Risk / KC / Gate / ...） |
| 無環 | 設計反饋形成循環（電熱耦合、製造↔公差） |

**核心問題**：散文 cross-reference（「見 WI-03」「對應 R-001」「使用 MC-04」）散落各檔，**易漂移**。改一個 WI 後，相關 ICD/MC/Risk 引用是否仍正確？人類 review 不可靠且耗時。

**驅動因素**：
- TRIZ 概念→工程交付物的**溯源性**是 PPAP / 審計需求
- 新進工程師需要快速看清「我這份檔跟誰相關」
- 未來 skill（`triz-graph-audit`、`triz-trace-explain`）需要可消費的結構化資料
- 變更影響分析（「改 MC-04 影響哪些 WI？」）需可查詢的圖結構

---

## Considered Options

| Option | Pros | Cons |
|:-------|:-----|:-----|
| **Frontmatter SSOT + 自動衍生視圖**（本決策） | 人讀人寫、git diff 友善、零基礎設施、CI 可驗證 | 需 lint 防止 ID 漂移、新人需學 schema |
| 純散文 cross-reference（現狀延續） | 零工具、寫起來最自由 | 易漂移、無法驗證、變更影響分析靠人腦 |
| 獨立 graph file（`graph.yaml` 集中管理）| 邏輯集中、統一 schema | 兩套真實來源（散文 + yaml）反而更容易不一致 |
| 關聯式資料庫（PostgreSQL + ORM） | 可 SQL 查詢 | 重基礎設施、非 markdown-first 失去 git diff 便利 |
| 圖資料庫（Neo4j / Memgraph） | 原生圖演算法、Cypher 查詢 | 重維運、單專案 over-engineered |
| 三元組 / RDF（語義網） | 形式化、可推理 | 工具鏈重、團隊學習曲線高 |

---

## Decision Outcome

**選擇**：Frontmatter SSOT + Tool-Derived Views

### 設計三要素

1. **YAML frontmatter = single source of truth**
   每個 WI/ICD/MC 檔頂端用 YAML frontmatter 宣告 typed relations（`traces_to` / `cites` / `uses` / `feeds` / `supports_icd` / `mitigates` / `satisfies_gates` / `links` / `used_by` / `depends_on` / `measures`）。Schema 見 [`15_documentation_guide.md §2.5`](../15_documentation_guide.md)。

2. **`tools/build_graph.py` 是衍生工具**
   - `--scan`（默認）：解析 frontmatter → 寫 `docs/engineering/_graph.json`
   - `--inject`：上述 + 渲染 mermaid 視圖到 `<!-- AUTO-GRAPH:START -->` markers
   - `--scaffold`：自動在缺 marker 的檔插入注入點
   - `--strict`：lint 失敗 exit 1（CI / pre-commit 用）

3. **三種衍生視圖（mermaid 投影）**
   - `topology`（README.md）：WI × ICD 主架構
   - `risk-matrix`（risk_register.md）：WI × Risk 緩解矩陣
   - `ego`（每份 WI/ICD/MC）：1-hop 鄰居 by type subgraph

### Lint 規則

| 規則 | 用途 |
|:-----|:-----|
| `[NO-TRACE]` | WI 必須有 `traces_to`（cross-cutting WI 例外） |
| `[OPEN-RISK]` | Risk 必須被某 WI/MC mitigates |
| `[LOW-CLAIM]` | Confidence=LOW 的 Claim 仍被引用 → 警告 |
| `[NO-FRONTMATTER]` | WI/ICD/MC 必須有 frontmatter（framework files 例外） |
| `[DUP]` / `[YAML ERROR]` | 錯誤級別 |

---

## Consequences

### 正面

- **單一事實來源**：frontmatter 變動 → 重跑 build_graph → 視圖 + `_graph.json` 自動同步，無漂移空間
- **CI 可驗證**：`build_graph.py --strict` 進 pre-commit hook，PR 階段擋下無效引用
- **變更影響分析**：「改 MC-04 影響哪些檔？」可由 `_graph.json` 反向遍歷 `uses` 邊回答
- **新人 onboarding**：每份檔開啟即見 ego graph，1-hop 鄰居一目了然
- **未來可消費**：`_graph.json` 可被 future skill（`triz-graph-audit` 等）直接讀取做語義審查
- **零基礎設施**：純 Python stdlib + PyYAML，不需要 DB / Neo4j / 雲服務
- **Markdown-first**：保留 git diff、code review、blame 等所有 git 工具的便利

### 負面 / 維護成本

- **Schema 學習**：新進工程師需熟悉 frontmatter 規範（~10 個 relation 欄位）
- **build_graph.py 維護**：~360 行 Python，未來新增 relation 類型需更新 `RELATION_FIELDS`
- **lint warning 處理**：cross-cutting WI 的例外處理（`role: cross-cutting`）需文件化
- **mermaid 渲染依賴**：viewer 需支援 mermaid（GitHub / VS Code with extension / PyCharm 內建）

### 中性

- 採用後僅產生**衍生產物**（`_graph.json` + mermaid blocks），不取代任何既有人讀內容；若工具壞掉，散文仍可讀

---

## Alternatives Considered（被否決原因）

### 純散文 cross-reference
**否決原因**：本決策觸發點。session 在 22+ 份檔之間累積數百條 cross-reference，人腦無法保證一致性。

### 獨立 graph file（`graph.yaml`）
**否決原因**：兩套真實來源（散文 + yaml）反而更容易不同步。frontmatter 直接寫在檔頭、`.read` 一次就有，比集中式 yaml 更不容易漂移。

### Neo4j / 圖資料庫
**否決原因**：基礎設施重（需要 DB server + 認證 + 備份）、單專案規模 over-engineered；未來若要跨專案知識資產（DK-04 §F7 knowledge-agent）再考慮升級。

### RDF / SPARQL
**否決原因**：團隊無語義網經驗、工具鏈重、ROI 不對稱。

### 關聯式 DB（PostgreSQL + ORM）
**否決原因**：失去 markdown-first 的 git diff、code review 便利；schema migration 比 frontmatter 改動麻煩。

---

## Implementation Notes

### 已實作（commit `c64150d`）

- `tools/build_graph.py`（~360 行）
- 17 個節點 / 161 條邊全 lint clean
- 16 份 frontmatter 補完（7 WI + 4 ICD + 6 MC + 已有的 WI-01）
- README + risk_register 注入 aggregate 視圖
- 17 份 ego graph 注入

### 後續

- **CI 整合**：在 GitHub Actions 加 `python3 tools/build_graph.py --strict` step（見 [`14_deployment_ops.md §3`](../14_deployment_ops.md)）
- **Pre-commit hook**：建議用 `pre-commit` 框架，commit 前自動跑 strict
- **未來 skill**：`triz-graph-audit`（語義審查溯源是否合理）、`triz-trace-explain`（自然語言回答「為什麼這樣設計」）

### 升級路徑

若未來規模需要：
1. 多專案 → 把 `_graph.json` 灌進 SQLite 做跨專案查詢
2. 語義級審查 → 在 graph 上跑 LLM skill（不需要換存儲）
3. 真的長到需要 Neo4j → frontmatter 仍是 SSOT，只是多一個 ETL 到 graph DB 的步驟

**SSOT 不變，視圖層可升級**是這個決策的關鍵彈性。

---

## References

- 實作：`tools/build_graph.py`
- 衍生產物：`docs/engineering/_graph.json`
- Schema：[`15_documentation_guide.md §2.5`](../15_documentation_guide.md)
- 工作流：[`09_file_dependencies.md §3`](../09_file_dependencies.md)
- 相關 ADR：ADR-002（TRIZ Skill 架構）、ADR-006（Production Persistence — Skill state 持久化）

---

## Changelog

| Date | Change |
|:-----|:-------|
| 2026-04-29 | 初版 — 對應 commit `c64150d`（feat(docs): build typed property graph from frontmatter + auto mermaid） |
