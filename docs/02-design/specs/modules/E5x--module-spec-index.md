# E5x — Module Specification Index

---

**文件版本 (Document Version):** `v1.1`
**最後更新 (Last Updated):** `2026-04-27`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`
**上游:** `[01-define/E3--architecture-and-design.md](../../../01-define/E3--architecture-and-design.md)` Appendix A–E

---

## 目的

將 E3 Appendix 架構拆成可機器執行、可 TDD 的模組規格清單。每一欄對應 `backend/app/` 或 `src/` 下的實體模組。**七個 pilot 模組**已展開完整 DbC + 測試案例（見下表 `✓ Pilot` 欄）。

---

## 模組索引 (全部識別到的 Agent / Service / Router)

### Backend Agents (`backend/app/agents/`)


| #   | 模組                                           | 原始檔                                             | 職責                                | 對應 E3 Appendix | Pilot spec                                                        |
| --- | -------------------------------------------- | ----------------------------------------------- | --------------------------------- | -------------- | ----------------------------------------------------------------- |
| 1   | `TrizSolverAgent`                            | `agents/triz_solver.py`                         | TRIZ 分層 drill-down 解矛盾 (L1/L2/L3) | Appendix B     | ✓ `[triz-solver.md](triz-solver.md)`                              |
| 2   | `AnalystAgent`                               | `agents/analyst.py`                             | Brief → 結構化約束/KPI                 | Appendix A     | ✓ `[analyst.md](analyst.md)`                                      |
| 3   | `EvaluatorAgent`                             | `agents/evaluator.py`                           | MUST/WANT/AC 六維評分                 | Appendix D     | ✓ `[evaluator.md](evaluator.md)`                                  |
| 4   | `TrizCriticAgent`                            | `agents/triz_critic.py`                         | L1 層信心度評估、觸發 drill-down           | Appendix B     | (subsumed by TrizSolver pilot)                                    |
| 5   | `KnowledgeAgent` / `KnowledgeWritebackAgent` | `agents/knowledge.py`, `agents/knowledge_wb.py` | RAG + 知識回寫                        | Appendix A §3  | ✓ `[knowledge.md](knowledge.md)` (search + ingest; writeback TBD) |
| ~~6~~ | ~~`ScamperFeedbackAgent`~~                 | ~~`agents/scamper_feedback.py`~~                | ~~SCAMPER → 新矛盾反饋~~ **(v9 移除)** | Appendix E     | ~~`[scamper-feedback.md](scamper-feedback.md)`~~ (deprecated)     |
| 7   | `AntiAnchorAgent`                            | (embedded in router `anti_anchor.py`)           | 反向路線生成                            | Appendix C     | ✓ `[anti-anchor.md](anti-anchor.md)`                              |
| 8   | `SubsystemDecomposerAgent`                   | (service in `subsystems.py` + `spatial_`*) *(v9: 原 `scamper.py`)* | 子系統發現與介面契約                        | Appendix A + E | ✓ `[subsystem-decomposer.md](subsystem-decomposer.md)`            |


### Backend Harness (`backend/app/harness/`) — v1.1 新增（ADR-006）

| 模組 | 職責 |
| --- | --- |
| `agent_base.py` | `HarnessAgent[DepsT, OutputT]` 型別安全 LLM 封裝 + `harness_call()` 便利函式 |
| `model_adapter.py` | Pydantic AI Model → 多 provider dispatch |
| `tool_registry.py` | `@register_tool` 裝飾器 + 自動 MCP spec |
| `solver_registry.py` | `@register_solver` 可插拔解題器 |
| `skill_loader.py` | 掃描 `skills/*/SKILL.md` 載入知識 |
| `mcp_server.py` | FastMCP stdio server |
| `orchestrator.py` | L1→critic→L2→L3 管線 |
| `prompt_assembler.py` | Cache-aware 上下文組裝 |


### Backend Services (`backend/app/services/`)


| 模組                                          | 職責                         |
| ------------------------------------------- | -------------------------- |
| `evidence_retrieval.py`                     | citation / evidence ref 查詢 |
| `evidence_registry.py`                      | 證據主張註冊 + WebSearch 驗證 + 覆蓋率統計（v1.1 ADR-008） |
| `web_search.py`                             | 外部 web 補充                  |
| `reference_library.py`                      | TRIZ 40 原理 / 76 標準解 靜態資料   |
| `package_svg.py`                            | 子系統視覺化 (SVG)               |
| `spatial_lookup.py`, `spatial_validator.py` | Spatial overlay            |


### Backend Tools (`backend/app/tools/`)


| 模組                         | 職責               |
| -------------------------- | ---------------- |
| `triz_kb.py`               | 矛盾矩陣 / 39×39 知識庫 |
| `triz_kb_tools.py`         | `@register_tool` MCP 工具（v1.1） |
| `contradiction_tree.py`    | 矛盾分解樹            |
| `separation_principles.py` | 4 種分離原理          |


### Frontend Hooks / Adapters (`src/`)


| 模組                             | 職責                               | 對應 spec                                                                                                         |
| ------------------------------ | -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `hooks/useLayeredTrizSolve`    | 呼叫 `/triz/solve-layered` 並映射至 UI | `[specs/triz/E5x--triz-layered-drilldown-optimization.md](../triz/E5x--triz-layered-drilldown-optimization.md)` |
| `hooks/useSubsystemSuggestion` | Tab ② subsystem 建議               | `[specs/explore/E5x--subsystem-persistence-policy.md](../explore/E5x--subsystem-persistence-policy.md)`         |
| `components/create/*`          | Create Tab ①–④ UI                | `[specs/ux/E5x--create-ux-spec.md](../ux/E5x--create-ux-spec.md)`                                               |


---

## Pilot Spec 選擇理由

七個 pilot 覆蓋 Discover → Deliver 全鏈路的核心 agent：

- **Forward TRIZ** → `triz-solver.md`（最複雜 AI 編排）
- **Reverse Anti-Anchor** → `anti-anchor.md`（路徑依賴打破邏輯）
- **Subsystem Decomposer** → `subsystem-decomposer.md`（跨 agent/service 協作）
- **Pre-CAD Evaluator** → `evaluator.md`（Gate 決策 + MUST/WANT 六維評分）
- **Knowledge RAG** → `knowledge.md`（citation / 多模態 ingest，所有 agent 共用）
- **Analyst** → `analyst.md`（Discover/Define 主 LLM actor；Brief / Socratic / Formalize / Decompose / Anti-Anchor prompt 入口）— 2026-04-15 補齊
- **ScamperFeedback** → `scamper-feedback.md`（Appendix E 非收斂迴圈閉環，相似度去重 + Supabase 寫回）— 2026-04-15 補齊
- **EvidenceRegistry** → `[evidence-registry.md](evidence-registry.md)`（ADR-008 證據主張註冊/驗證/覆蓋率）— 2026-04-23 新增（v1.1）

`TrizCriticAgent` 的 DbC 已內嵌於 `triz-solver.md` drill-down 邏輯（不獨立 pilot）。其餘模組（services / tools / frontend hooks）採 lazy-spec 策略：進 WBS 前由 owner 依 `[VibeCoding 07 模板](../../../../rd_assistant_design_system/VibeCoding_Workflow_Templates/07_module_specification_and_tests.md)` 填寫。

---

## 延伸閱讀

- 測試規範 → `[E7x--e2e-manual-scripts/](../../E7x--e2e-manual-scripts/)`
- 類別關係圖 → `[specs/E5x--class-relationships.md](../E5x--class-relationships.md)`
- 檔案依賴圖 → `[specs/E5x--file-dependencies.md](../E5x--file-dependencies.md)`

