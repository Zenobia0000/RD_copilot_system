# Module Spec: EvaluatorAgent

---

**文件版本 (Document Version):** `v1.1`
**最後更新 (Last Updated):** `2026-04-27`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**審核者 (Reviewers):** `Tech Lead, QA Lead, RD Reviewer Lead`
**狀態 (Status):** `Draft (Pilot)`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`

---

## 模組: `EvaluatorAgent`

**原始檔**: `backend/app/agents/evaluator.py`
**對應架構文件**: `[01-define/E3--architecture-and-design.md` Appendix D](../../../01-define/E3--architecture-and-design.md)
**對應 BDD Feature**: `[docs/02-design/E5x--bdd-scenarios.md` §Feature 3 (Pre-CAD)](../../E5x--bdd-scenarios.md)
**對應素材**: `[specs/review-templates/E5x--pre-cad-review-template.md](../review-templates/E5x--pre-cad-review-template.md)`
**對應 API**: `POST /pre-cad-reviews/:rid/ai-analyze`, `GET /must/`*（`backend/app/routers/pre_cad.py`, `backend/app/routers/must.py`）

---

### Harness 遷移狀態（v1.1 新增，ADR-006）

`evaluator.py` 已完全遷移至 Harness 架構：

| 函式 | Harness 呼叫方式 | Agent Name |
|------|----------------|------------|
| `assess_risks` | `harness_call()` | `evaluator_risk` |
| `evaluate_must` | `harness_call()` | `evaluator_must` |
| `analyze_pre_cad` | `harness_call()` | `evaluator_pre_cad` |
| `generate_want_seeds` | `harness_call()` | `evaluator_want_seed` |
| `scan_convergence` | `harness_call()` | `evaluator_convergence` |
| `issue_validation_passport` | `harness_call()` | `evaluator_passport` |
| `assess_brief_quality` | `_harness_call_dict()` + `HarnessAgent` | `evaluator_brief_quality` |
| `assess_depth_quality` | `_harness_call_dict()` + `HarnessAgent` | `evaluator_depth_quality` |
| `assess_experiment_coverage` | `_harness_call_dict()` + `HarnessAgent` | `evaluator_experiment_coverage` |

所有 LLM 呼叫均透過 `harness/agent_base.py` 路由至 `model_adapter.py` 多 provider dispatch。

---

### 規格 1: `evaluate_pre_cad(request: PreCadEvaluateRequest) -> PreCadReport`

**描述**: 針對一個 Concept Route (`CR-Axxx`)，依 Pre-CAD Gate 審查模板執行「六維評分」：

- **MUST 硬限制 (M1–M6)**：空間 / 成本 / 安全餘裕 / 解耦 / 供應 / 製造路徑 → Pass / Conditional / Fail 三分類（Go/No-Go）
- **定性維度 (4 軸)**：模組獨立性、可驗證性、主要風險機制、MVP CAD 工作量 → 1–5 分

**契約式設計 (DbC)**:

- **前置條件 (Preconditions)**:
  1. `request.concept_route_id` 對應一個 `candidate` 或 `frozen` 狀態的 concept route。
  2. Concept route 的 `interface_contracts`、`bom_estimate`、`coupling_points` 至少部分填寫（完整度 ≥ 60%）。
  3. 使用者擁有 project 存取權。
  4. MUST Rulebook 已為專案凍結（見 `[E5x--must-rulebook-template.md](../review-templates/E5x--must-rulebook-template.md)`）。
- **後置條件 (Postconditions)**:
  1. 回傳 `PreCadReport` 含 `must_results: MustResult[]`（長度恰為 6）與 `qualitative_scores: QualitativeScore[]`（長度恰為 4 維度，每維度 ≥ 1 項目）。
  2. 每 `MustResult.verdict ∈ {"pass", "conditional", "fail"}`（小寫 enum，不可為空）。
  3. 每 `QualitativeScore.score ∈ [1, 5]`（整數）。
  4. 若任一 `MustResult.verdict == "fail"` → `report.gate_decision == "rejected"`；否則依業務規則映射 `approved` / `conditional`。
  5. 每項評分均含 `evidence_refs: EvidenceReference[]`（citation 可為 KB- / WEB- / Artifact-ID 格式，不可全空）。
  6. 若 `gate_decision == "conditional"`，`report.priority_validation_list` 非空（列出待驗證 MUST id）。
- **不變性 (Invariants)**:
  1. 同一 `concept_route_id` + 同 MUST Rulebook 版本多次呼叫應冪等（temperature ≤ 0.2）。
  2. MUST 與 定性維度 **不可互相抵消**（MUST=fail 不因定性=5 分而翻轉）。
  3. `evidence_refs` 的 `source_url` 若存在，必為 HTTPS。
  4. Evaluator **僅產報告**，不寫入 gate sign-off 狀態（sign-off 由前端顯式呼叫 `/pre-cad-reviews/:rid/sign`）。

---

### 測試情境與案例

#### 情境 1: Happy Path — 全 Pass，approved

- **測試案例 ID**: `TC-Evaluator-001`
- **描述**: 方案 `CR-A001` 空間 / 成本 / 安全 / 解耦 / 供應 / 製造 皆 Pass，定性平均 ≥ 4。
- **Arrange**: fixture 方案完整度 90%；mock MUST Rulebook 全通過；mock LLM 回傳 qualitative=5。
- **Act**: `await evaluator.evaluate_pre_cad(req)`。
- **Assert**:
  - `len(report.must_results) == 6 && all(r.verdict == "pass")`
  - `report.gate_decision == "approved"`
  - `report.priority_validation_list == []`

#### 情境 2: Drill — 有 Conditional，conditional 決策

- **測試案例 ID**: `TC-Evaluator-002`
- **描述**: M2 (成本) = Conditional，M3 (安全餘裕) = Conditional，其他 Pass。
- **Assert**:
  - `report.gate_decision == "conditional"`
  - `"M2" in report.priority_validation_list && "M3" in report.priority_validation_list`
  - 每 conditional 項含 `reason` 非空字串

#### 情境 3: 邊界 — 任一 MUST Fail → rejected

- **測試案例 ID**: `TC-Evaluator-003`
- **描述**: M6 (製造可行性) = Fail。
- **Assert**:
  - `report.gate_decision == "rejected"`
  - 即使定性全 5 分仍 rejected（不變性 2）
  - 回傳 `reason` 引用 MUST Rulebook rule id

#### 情境 4: 違反前置 — Concept route 完整度 < 60%

- **測試案例 ID**: `TC-Evaluator-004`
- **描述**: `interface_contracts` 為空 dict、`bom_estimate` 缺失。
- **Assert**: 422 `concept_route_incomplete` + 提示補齊欄位清單。

#### 情境 5: 業務規則 — 評分必附 citation

- **測試案例 ID**: `TC-Evaluator-005`
- **描述**: Mock Knowledge service 回傳空 citation list。
- **Assert**:
  - 任一 `MustResult.evidence_refs` 為空 → 拋 `EvidenceMissingError`（後置條件 5）
  - 或退回 `verdict = "conditional"` + `reason = "no_evidence_fallback"`（依 policy TBD — RD 決定）

#### 情境 6: 冪等性 — 同 rulebook 版本重跑

- **測試案例 ID**: `TC-Evaluator-006`
- **描述**: 同 `concept_route_id` + 同 `rulebook_version` 呼叫兩次。
- **Assert**:
  - 兩次 `must_results[*].verdict` 完全相同
  - `qualitative_scores[*].score` 差異 ≤ 1（LLM 隨機性允許小幅）

#### 情境 7: 上游失敗 — Knowledge Agent timeout

- **測試案例 ID**: `TC-Evaluator-007`
- **描述**: Knowledge RAG 5s timeout。
- **Assert**: 拋 `KnowledgeUpstreamError` → 502 + `error.code=knowledge_upstream_error`；不允許靜默降級產出無 citation 的報告。

---

**LLM Prompting Guide:**

> 「請依以下測試規格，使用 pytest + pytest-asyncio 為 `EvaluatorAgent.evaluate_pre_cad` 生成失敗的 TDD 測試。測試案例 ID: TC-Evaluator-003（MUST Fail 路徑）。」

