# 資料模型與 Gate 條件參考

**一句話定位**：快速查閱 7 個核心工件的欄位定義、狀態生命週期、以及 8 個 Gate 的通過條件。

**代碼對齊**：`backend/app/models/schemas.py` (92 Pydantic models) · `backend/app/core/gate_checks.py` · `backend/app/prompts/*.py`

---

## 1. Project 狀態機

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| name | String(200) | 專案名稱 |
| phase | Enum | DRAFT → PHASE_I → PHASE_II → PHASE_III → COMPLETED |

```
DRAFT ──Gate 1──▶ PHASE_I ──Gate 3──▶ PHASE_II ──Gate P──▶ PHASE_III ──Gate 8──▶ COMPLETED
```

---

## 2. 七大核心工件 (Schema Reference)

### 2.1 Constraint (Step 1 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK → Project | |
| mission | Text | 一句話任務聲明 |
| hard_constraints | JSON `[{name, value, source}]` | 硬約束 |
| soft_objectives | JSON `[{name, priority}]` | 軟目標 |
| non_goals | JSON `[{item}]` | 非目標 |
| critical_metrics | JSON `[{name, target, method}]` | 最不能失敗指標 (≥3) |

**狀態**：Draft (建立) → Reviewed (RD 確認)

### 2.2 Contradiction (Step 2-3 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| code | String | C-001, C-002... |
| type | Enum | `TC` / `PC` / `SF` |
| improve_param | String | TRIZ 39 參數之一 (TC only) |
| worsen_param | String | TRIZ 39 參數之一 (TC only) |
| engineering_desc | Text | 工程表述 |
| physical_contradiction | Text | 物理矛盾 (PC only) |
| attribute_a / attribute_¬a | Text | PC 對立屬性 |
| substance_1 / substance_2 | Text | SF: S1, S2 |
| field_type | String | SF: 場類型 |
| interaction_type | Enum | 有用/有害/不足/缺失 |
| completeness_state | Enum | 完整/不完整/有害完整 |
| severity | Enum | `fatal` / `major` / `minor` |
| parent_contradiction_id | FK → Contradiction | PC 可從 TC 派生 |

**狀態**：Draft → Reviewed → Verified

### 2.3 FunctionModel (Step 3 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| code | String | FM-001... |
| system_function | Text | 系統功能 |
| s1_tool | Text | 工具物質 |
| s2_product | Text | 產品物質 |
| field_type | String | 機械/熱/電/磁/化學 |
| interaction_type | Enum | 有用/有害/不足/缺失 |
| sufield_completeness | Enum | 完整/不完整/有害完整 |

**狀態**：Draft → Reviewed

### 2.4 Breakpoint (Step 3 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| code | String | BP-001... |
| location | Text | 介入位置 |
| lever_param | Text | 可操作參數 |
| triz_hint | Text | TRIZ 原理提示 |
| related_contradiction_ids | JSON `[UUID]` | 關聯矛盾 |

**狀態**：Draft → Reviewed

### 2.5 Concept Route (Step 5 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| name | String | 方案名稱 |
| source | Enum | `triz` / `scamper` / `anti_anchor` / `manual` |
| mechanism | Text | 物理機制說明 |
| interface_contract | JSON (6 維) | Envelope/Load/Signal/Thermal/Datum/Service |
| bom_estimate | JSON | 預估 BOM |
| assumptions | JSON `[{id, content, evidence_level}]` | 假設清單 |
| risk_ids | JSON `[UUID]` | 關聯風險 |
| validation_passport | JSON | assumptions[], weak_points[], required_verifications[], confidence_level |
| must_results | JSON | M1-M6 篩選結果 |
| pre_cad_score | JSON | spatial/cost/safety/decoupling/supply (1-5) |

**狀態**：Draft → Reviewed → Verified (Gate P) → Baselined (Gate 7) → Released (Gate 8)

### 2.6 Evidence (Step 6/6e 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| artifact_id | String | e.g., Sim-Torque001, Exp-Motor001 |
| type | Enum | simulation / calculation / test_report / supplier_data / measurement |
| quality | Enum | E0 / E1 / E2 / E3 / E4 |
| description | Text | |
| source_ref | JSON | RAG/Web 引用資訊 |

**狀態**：Draft → Reviewed → Verified

### 2.7 Risk (Step 6 產出)

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID | PK |
| project_id | FK | |
| code | String | Risk-A001... |
| description | Text | |
| failure_mode | Text | 失效模式 |
| probability | Enum | Low / Medium / High |
| severity | Enum | Low / Medium / High |
| level | Enum | L / M / H / H* |
| mitigation | Text | 緩解措施 |
| mitigation_evidence_id | FK → Evidence | |
| owner | String | |
| due_date | Date | |

**狀態**：Draft → Reviewed → Mitigated

---

## 3. 輔助工件

### Decision Record (Step 7 產出)

| 欄位 | 說明 |
|------|------|
| decision_statement | 決策聲明 |
| must_results | 各方案 MUST 通過/淘汰記錄 |
| want_results | 各方案加權分 + 證據連結 |
| adverse_consequences | 風險評估 + 緩解 |
| primary_route_id | 主路線 Concept Route ID |
| backup_route_id | 備援路線 |
| rationale | 決策理由 |
| action_items | 行動項目 `[{task, owner, due}]` |

**狀態**：Draft → Reviewed → Released

### Assumption (Step 4 產出)

| 欄位 | 說明 |
|------|------|
| content | 假設內容 |
| source | 依據來源 (Artifact ID) |
| worst_consequence | 若錯了最壞後果 |
| min_verification | 最小驗證方法 |
| cost_cycle | 驗證成本/週期 |

**狀態**：Draft → Reviewed → Verified (驗證完成) / Refuted (被推翻)

---

## 4. Gate 條件一覽表

| Gate | 位置 | 關鍵通過條件 | Phase 轉換 |
|------|------|------------|-----------|
| **Gate 1** | Step 1 完成 | `critical_metrics` ≥ 3，每個有 target + method | DRAFT → PHASE_I |
| **Gate 2** | Step 2 完成 | 假設 ≥ 10 條，Top 3 已標記；核心矛盾 ≥ 3 | — |
| **Gate 3** | Step 3 完成 | 斷路點 ≥ 3，每條矛盾有 TRIZ 正式句 + 類型標註；FM 已建構 | PHASE_I → PHASE_II |
| **Gate 4** | Step 4 完成 | Top 3 假設各有 1-2 週可完成的驗證設計 | — |
| **Gate P** | Step 5 完成 | ≥ 3 條架構路線 (含 ≥1 Anti-Anchor)；Pre-CAD Confidence = 100% | PHASE_II → PHASE_III |
| **Gate C** | Step 6 完成 | 北極星 KPI 證據 ≥ E2；Evidence Matrix 所有 row 達標 | — (→ KT 決策) |
| **Gate 7** | Step 7 完成 | WANT 評分有 Artifact ID (≠E0)；H 風險有緩解(≥E1)；KT 記錄已簽核 | — |
| **Gate 8** | Step 8 完成 | 新人/老闆/工程師都看得懂；所有工件 Baselined → Released | PHASE_III → COMPLETED |

---

## 5. Prompt 模板對照表

| Agent | Prompt 檔案 | 對應 Step |
|-------|------------|----------|
| Analyst | `backend/app/prompts/analyst.py` | Step 1-2 (brief extraction, mission rewrite, constraint/KPI suggestion) |
| TRIZ Solver | `backend/app/prompts/triz_solver.py` | Step 3, 5a (TC/PC/SF instantiation) |
| Evaluator | `backend/app/prompts/evaluator.py` | Step 5e, 7 (MUST verification, risk analysis, Pre-CAD scoring) |
| Knowledge WB | `backend/app/prompts/knowledge_wb.py` | Step 8 (knowledge asset generation) |
| TRIZ Critic | `backend/app/agents/triz_critic.py` | Step 5a-6 (secondary contradiction scan) |
| SCAMPER Feedback | `backend/app/agents/scamper_feedback.py` | Step 5c (SCAMPER contradiction integration) |

---

## 6. API 路由概覽

完整 API 規格（端點、Request/Response schema）已移至 `docs/02-design/specs/` 系統規格定義書。以下為路由分組快照：

| 分組 | 路由前綴 | 對應 Step |
|------|---------|----------|
| Brief & Definition | `/api/v1/projects/{pid}/definitions` | Step 1 |
| Socratic Questions | `/api/v1/projects/{pid}/questions` | Step 2 |
| Causal Loops | `/api/v1/projects/{pid}/causal-loops` | Step 3a |
| Contradictions | `/api/v1/projects/{pid}/contradictions` | Step 3b |
| Breakpoints | `/api/v1/projects/{pid}/breakpoints` | Step 3c |
| Assumptions | `/api/v1/projects/{pid}/assumptions` | Step 4 |
| TRIZ Solve | `/api/v1/projects/{pid}/triz` | Step 5a |
| Subsystems | `/api/v1/projects/{pid}/subsystems` | Step 5b |
| SCAMPER | `/api/v1/projects/{pid}/scamper` | Step 5c |
| Alternatives | `/api/v1/projects/{pid}/alternatives` | Step 5d |
| MUST | `/api/v1/projects/{pid}/must` | Step 5e |
| Convergence | `/api/v1/projects/{pid}/convergence` | Step 5a (Phase A/B) |
| Evidence | `/api/v1/projects/{pid}/evidence` | Step 6 |
| Risk | `/api/v1/projects/{pid}/risks` | Step 6 |
| WANT & Decision | `/api/v1/projects/{pid}/want`, `/decision` | Step 7 |
| Exports | `/api/v1/projects/{pid}/exports` | Step 8 |
| Gates | `/api/v1/projects/{pid}/gates` | All |

---

**版本**: v2.0
**最後更新**: 2026-04-21
**變更紀錄**: 從系統規格定義書提取核心 data model 與 gate 條件；API 端點細節保留在 02-design/specs
