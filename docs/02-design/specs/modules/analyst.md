# Module Spec: AnalystAgent

---

**文件版本 (Document Version):** `v1.1`
**最後更新 (Last Updated):** `2026-04-23`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**審核者 (Reviewers):** `Tech Lead, QA Lead, RD Reviewer Lead`
**狀態 (Status):** `Active (Pilot)`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`

---

## 模組: `AnalystAgent`

**原始檔**: `backend/app/agents/analyst.py`
**對應架構文件**: [`01-define/E3--architecture-and-design.md` Appendix A (Forward Subsystem Discovery) + §11 Analyst Agent](../../../01-define/E3--architecture-and-design.md#appendix-a-forward-subsystem-discovery-architecture)
**對應 BDD Feature**: [`docs/02-design/E5x--bdd-scenarios.md` §Feature Brief / Socratic / Anti-Anchor](../../E5x--bdd-scenarios.md)
**對應 Prompt**: `backend/app/prompts/analyst.py`
**對應 API**:
- `POST /analyst/extract-brief`, `POST /analyst/rewrite-mission`
- `POST /analyst/suggest-constraints`, `POST /analyst/suggest-kpis`
- `POST /analyst/constraint-feasibility`, `POST /analyst/5w1h`
- `POST /analyst/socratic`, `POST /analyst/socratic/follow-up`, `POST /analyst/socratic/brief-impact`, `POST /analyst/socratic/auto-tag`
- `POST /analyst/cld`, `POST /analyst/anti-anchor`
- `POST /analyst/formalize-contradiction`, `POST /analyst/decompose-tc`
- `POST /analyst/extract-assumptions`, `POST /analyst/discover-unknowns`
- **v1.1 (ADR-008) Analyst v2 endpoints** (`backend/app/routers/analyst_v2.py`):
- `POST /analyst/five-why` — 5Why 根因分析
- `POST /analyst/kt-analysis` — KT Is/IsNot 問題範圍界定
- `POST /analyst/function-analysis` — 功能分析（FA + SF 診斷）
- `POST /analyst/oz-ot-analysis` — OZ-OT-Px 分析
- `POST /analyst/entry-grading` — 問題複雜度分級（Level A/B/C）

---

## 職責

Analyst Agent 是 Discover/Define 階段的主要 LLM actor，負責把自然語言 Brief 轉成結構化的約束 / KPI / 假設 / 矛盾，並驅動蘇格拉底問答、矛盾形式化（TC-only，依 [ADR-007](../../../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)）、TC → multi-PC drill-down、TC → SF 派生（Create 階段入口用）、CLD 因果圖、Anti-Anchor 反向路徑、未知因子探索。所有方法共用 `ANALYST_SYSTEM` prompt 與 `call_llm_json` JSON-mode LLM call；產生結構化資料均經 Pydantic schema（`app.models.schemas`）驗證。

---

### 規格 1: `extract_brief(req: BriefExtractionRequest) -> BriefExtractionResponse`

**描述**: 從 `raw_text`（或 file_urls，尚未實作）抽取 `constraints[]` / `kpis[]` / `assumptions[]` / `feasibility_warnings[]` 4 類結構化欄位。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.project_id` 非空且使用者有權限。
  2. `req.raw_text` 或 `req.file_urls` 至少一者非空；若兩者皆空，填入 fallback prompt `"(無文字，請根據 file_urls 推斷)"`。
* **後置條件**:
  1. 回傳 `BriefExtractionResponse` 4 個欄位皆為 list（可為空）。
  2. 僅回傳 prompt 要求的 4 個 key；其他多餘 LLM key 被過濾丟棄（防 Pydantic `extra="forbid"` 爆錯）。
  3. `constraints[*]` 結構符合 `ExtractedConstraint`（code / description / source / type / feasibility）。
* **不變性**:
  1. Agent 不落資料庫；落庫由 router 層 `pre_analyst.py` 負責。

---

### 規格 2: `formalize_contradiction(req: ContradictionFormalizeRequest) -> ContradictionFormalizeResponse`

**描述**: 依 [ADR-007](../../../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)，把一條自然語言矛盾形式化為 TRIZ **TC**（工程矛盾，對應 39 參數）；若 LLM 無法映射到兩個 `improving/worsening_param`，**拒絕**並回傳 `type=null + rationale`（不再 downgrade 至 PC/SF）。PC/SF 於 Create 階段由 `solve_triz_layered` 入口派生。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.natural_description` 非空字串。
  2. `req.contradiction_id` 對應存在於 `contradictions` table 的 row。
* **後置條件** (ADR-007):
  1. 成功：`type == "TC"` AND `improving_param, worsening_param ∈ [1, 39]` AND `rationale` 非空。
  2. 失敗：`type is None` AND `rationale` 非空（解釋為何無法映射到 39 參數）。
  3. `confidence ∈ [0, 1]`。
  4. **不再產出** PC/SF 情境；`physical_contradiction` / `sf_substance_1/2` / `sf_field` 欄位標記為 Explore-階段 deprecated（仍保留於 schema 供舊資料讀取）。
* **不變性**:
  1. **TC MUST have both params**；無法映射即 reject，不 downgrade。
  2. `socraticAnswers` 若提供，需先經 `_extract_socratic_insights` 轉為 bullet 字串注入 prompt。
  3. 派生產物不回寫 `contradictions` 表（避免污染 Explore source of truth）。

---

### 規格 2a: `derive_su_field_from_tc(req: TrizLookupRequest) -> SuFieldModel | None`

**描述**: 依 [ADR-007](../../../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md)，於 `solve_triz_layered` 入口以 TC（含 `improving_param` / `worsening_param` / `engineering_statement`）派生 L3 用的 Substance-Field 模型（S1 / S2 / F）。失敗時回 `None` 並 log warning，L3 降級；L1/L2 不受影響。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.improving_param`, `req.worsening_param` ∈ [1, 39]（已由 `formalize_contradiction` 驗證）。
  2. `req.engineering_statement` 非空。
* **後置條件**:
  1. 成功：回傳 `SuFieldModel(substance_1, substance_2, field)`，三欄皆非空字串。
  2. 失敗（LLM 無法推出有意義 S1/S2/F）：回傳 `None` + `logger.warning`；由 orchestrator 降級 L3 為 warning-only。
* **不變性**:
  1. **不回寫** `contradictions` 表；派生結果僅於本次 solve response 帶回。
  2. 任何 exception 不得逃逸（error isolation，與 `decompose_tc_to_pcs` 一致）。

---

### 規格 3: `decompose_tc_to_pcs(req: ContradictionDecomposeRequest) -> ContradictionDecomposeResponse`

**描述**: Explore 階段 TC → multi-PC drill-down。先跑 L1 rule-based critic 判定是否值得分解；若觸發，再呼叫 LLM 取得 `DecomposedPC[]`，並對 `derived_parameter` 去重、對 `separation_principle_id` 驗證（必屬 canonical 16 項集合）。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.engineering_statement` 非空。
  2. `req.severity ∈ {"minor", "major", "critical"}`。
* **後置條件**:
  1. 若 critic 判定 `triggered=False`，回傳 `decomposed_pcs=[]` 且 `reasoning="L1 critic judged drill-down unnecessary."`。
  2. 若 critic 觸發但 LLM 或驗證失敗，回傳 `triggered=True, decomposed_pcs=[], reasoning="Decomposition failed: {exc}"`（error isolation per WBS §3.3）。
  3. 回傳 `decomposed_pcs[*].derived_parameter` **兩兩相異**（in-list dedup）。
  4. 每個 PC 的 `separation_principle_id` 屬於 canonical 16 項（由 Pydantic validator 自動拒絕）。
* **不變性**:
  1. 任何 exception 不得逃逸至 router（EVERY branch wrapped in try/except）。
  2. `enable_llm_critic=False` — decomposition 內部僅用 rule layer 做 gating 以節省 token。

---

### 規格 4: `generate_anti_anchor(req: AntiAnchorRequest) -> AntiAnchorResponse`

**描述**: 從 mission + current_constraints + existing_alternatives 產生 ≥3 條非典型架構候選（Anti-Anchor routes），每條附 mechanism / why_unconventional / potential_advantage / cross_domain_source。對應 E3 Appendix C。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.mission` 非空；`req.current_constraints` 至少 1 條。
  2. 呼叫端應預先用 `get_contradiction_leaves()` 把 contradictions 過濾到葉節點，避免 parent + child 重複（見 §9.4 及 analyst.py L390–393）。
* **後置條件**:
  1. `result.alternatives` 長度 ≥ 1（理想 ≥ 3，實際以 LLM 為準）。
  2. 每 alternative 的 4 個文字欄位（`mechanism` / `why_unconventional` / `potential_advantage` / `cross_domain_source`）必為 `str` — 若 LLM 返回 dict，agent 以 `_flatten_to_str` 壓平。
  3. 每條 alternative 的 `is_non_typical` 預設為 `True`。
* **不變性**:
  1. Anti-Anchor 產出直接進候選池（Appendix E §R1），不回跑 TRIZ 收斂迴圈。

---

### 規格 5: `generate_socratic_questions(req: SocraticRequest) -> SocraticResponse` (+ follow_up / brief_impact / auto_tag 三姊妹)

**描述**: 產生七類固定類別的蘇格拉底問題：`clarification` / `assumption` / `consequence` / `counter` / `origin` / `action` / `reframing`。LLM 以 dict keyed by category 返回；agent 在 `analyst.py` L221–228 把 dict 轉為 list 並附上 `type_class`。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.mission` 非空；`req.constraints` 可為空。
* **後置條件**:
  1. `result.questions[*].type_class ∈ _VALID_CATEGORIES`（7 類）；非屬此集合者被丟棄。
  2. 每個 question 物件為 dict（含 LLM 產出欄位如 `text`）。
* **不變性**:
  1. 問題類別集合 `_VALID_CATEGORIES` 為寫死 constant，不隨 LLM 漂移。

---

### 其他方法（lazy-spec，內部職責摘要）

| 方法 | 職責 | TBD |
| --- | --- | --- |
| `check_constraint_feasibility` | 兩兩約束矛盾檢測 | DbC 契約 TBD — owner: Backend AI, 2026-05 |
| `rewrite_mission` / `suggest_constraints` / `suggest_kpis` / `generate_5w1h` | 帶 `evidence_retrieval` citation 的 Brief 補強 | Citation 必附 — DbC TBD 2026-05 |
| `generate_cld` | 因果環路圖（Causal Loop Diagram） | 節點 / 箭頭 schema 驗證 TBD |
| `extract_assumptions` | 從 Q&A 萃取假設 | evidence_level 欄位契約 TBD |
| `discover_unknown_factors` | 從上下文缺口找未知因子 | Dedup 策略 TBD |

---

### 規格 14 (v2.2): `five_why(req: FiveWhyRequest) -> FiveWhyResponse`

**描述**: 從症狀出發，執行 5 Why 根因分析。5 分鐘內從症狀挖到可操作的因果節點，判斷要分析哪個子系統。產出 TC 初步假設。對應 Auto-TRIZ v2 Step 0a。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.project_id` 非空且使用者有權限。
  2. `req.symptom_description` 非空（症狀描述）。
  3. `req.brief_context` 可選（已有的 mission / constraints / kpis 作為上下文）。
* **後置條件**:
  1. `result.why_chain` 為 list，長度 3-7（每層 why + answer）。
  2. `result.root_cause_hypothesis` 非空（可操作的根因假設）。
  3. `result.target_subsystem` 非空（要分析的子系統名稱）。
  4. `result.tc_hypothesis` 可選 — 若根因已是兩參數 trade-off，直接產出 TC 候選（`improving_desc` + `worsening_desc`）。
* **不變性**:
  1. 5 Why 僅做定向，不定義矛盾。TC 假設需經 `formalize_contradiction` 正式化。
  2. Agent 不落資料庫。

---

### 規格 15 (v2.2): `kt_is_is_not(req: KtAnalysisRequest) -> KtAnalysisResponse`

**描述**: 當有對照組（好的 vs 壞的、有問題的 vs 沒問題的）時，執行 KT Is/Is Not 差異分析。用差異比較縮小搜索空間，產出 Px 候選清單 + OZ/OT 初步鎖定。對應 Auto-TRIZ v2 Step 0b。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.project_id` 非空。
  2. `req.is_description` 非空（有問題的情境描述）。
  3. `req.is_not_description` 非空（沒問題的對照情境描述）。
  4. `req.five_why_result` 可選（若已做 5 Why，帶入根因假設作為上下文）。
* **後置條件**:
  1. `result.analysis_matrix` 為 4 維矩陣（What / Where / When / Extent），每維含 IS / IS_NOT / unique_difference。
  2. `result.px_candidates` 為 list（1-5 個 Px 候選物理變數），每個含 `variable_name` + `rationale`。
  3. `result.oz_hint` 可選（Where IS vs IS NOT 差異 → 操作空間初步鎖定）。
  4. `result.ot_hint` 可選（When IS vs IS NOT 差異 → 操作時間初步鎖定）。
* **不變性**:
  1. 無對照組時不應呼叫此方法（前端 UI 提供「是否有對照組」判斷）。
  2. Agent 不落資料庫。

---

### 規格 16 (v2.2): `function_analysis(req: FunctionAnalysisRequest) -> FunctionAnalysisResponse`

**描述**: 繪製組件交互圖（有效/有害/不足/過度/缺失功能）+ 建立 Substance-Field 模型 + 定義子系統邊界。確保矛盾定義在正確系統粒度。對應 Auto-TRIZ v2 Step 1。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.project_id` 非空。
  2. `req.brief_context` 非空（mission + constraints + kpis）。
  3. `req.five_why_result` 可選（若已做 5 Why，帶入子系統假設）。
  4. `req.bom_components` 可選（若有 BOM，加速建模；否則從功能反推）。
* **後置條件**:
  1. `result.component_interactions[]` 非空，每項含 `source_component`, `target_component`, `function_type` ∈ {"useful", "harmful", "insufficient", "excessive", "missing"}, `description`。
  2. `result.sf_diagnosis` 含 `substance_1`, `substance_2`, `field`, `status` ∈ {"effective", "harmful", "insufficient", "missing"}。
  3. `result.subsystem_boundary` 含 `name`, `included_components[]`, `boundary_rationale`。
  4. `result.improvement_description` 非空（「改善什麼」自然語言）。
  5. `result.worsening_description` 非空（「惡化什麼」自然語言）。
* **不變性**:
  1. 子系統邊界圍繞 OZ（操作空間）建立，非按 BOM 零件劃分。
  2. `improvement_description` + `worsening_description` 為 Step 2 TC 參數映射的直接輸入。
  3. Agent 不落資料庫；結果由前端持有或經 `function_models` 表持久化（TBD）。

---

### 規格 17 (v2.2): `oz_ot_analysis(req: OzOtRequest) -> OzOtResponse`

**描述**: 鎖定操作空間 (Operational Zone) + 操作時間 (Operational Time)，萃取核心物理變數 Px。Px 是 TC→PC 轉換的橋樑 — 「P1 和 P2 共同受什麼物理量控制？」。對應 Auto-TRIZ v2 Step 3a。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.contradiction_id` 對應存在的 TC row（`type="TC"`, `improving_param` + `worsening_param` 非空）。
  2. `req.function_analysis_result` 可選（若已做 FA，帶入組件交互 + SF 狀態）。
  3. `req.kt_result` 可選（若已做 KT，帶入 Px 候選 + OZ/OT hint）。
* **後置條件**:
  1. `result.oz` 含 `zone_description`（操作空間自然語言）+ `physical_location`（具體位置）。
  2. `result.ot` 含 `time_description`（操作時間自然語言）+ `time_window`（具體時間範圍）。
  3. `result.px` 含 `variable_name`（物理變數名稱）+ `rationale`（為何此變數同時控制 P1 和 P2）+ `sensitivity`（`[dP1/dPx, dP2/dPx]` 方向性描述）。
  4. `result.pc_sentence` 含 `state_a`（Px 需為 [State A] 以改善 P1）+ `state_not_a`（Px 需為 [NOT A] 以改善 P2）→ 即 PC 造句。
  5. `result.px_found` 為 boolean：
     - `true`：Px 鎖定成功，可進入 Step 3b PC 驗證。
     - `false`：Px 鎖定失敗，附 `fallback_strategy` ∈ {"broaden_oz", "split_tc", "reframe_problem"}。
* **不變性**:
  1. OZ-OT 結果不回寫 `contradictions` 表（與 ADR-007 一致）；可暫存於 solve response 或新表。
  2. Px 為 TC→PC 的唯一橋樑；若 Px 找不到，TC 仍可用 L1 表面解，但 L2 深挖會降級。

---

### 規格 18 (v2.2): `entry_grading(req: EntryGradingRequest) -> EntryGradingResponse`

**描述**: 判定問題成熟度等級（Level A / B / C），路由至合適的分析框架。對應 Auto-TRIZ v2 §1.1 入口判定。

**契約式設計 (DbC)**:
* **前置條件**:
  1. `req.project_id` 非空。
  2. `req.problem_description` 非空（使用者對問題的自然語言描述）。
* **後置條件**:
  1. `result.level` ∈ {"A", "B", "C"}：
     - **C**：連系統都描述不了 → 回傳 `recommended_framework` ∈ {"design_thinking", "axiomatic_design", "evolution_trends"}。
     - **A**：能描述系統但說不出 trade-off → 回傳 `recommended_entry = "step_0"`（必做 5 Why）。
     - **B**：能填完「在 [系統] 中，為了 [改善 A]，會導致 [B 惡化]」→ 回傳 `recommended_entry = "step_1"`（可跳 Step 0）。
  2. `result.verification_sentence` 可選 — Level B 時附完整造句供 RD 確認。
  3. `result.rationale` 非空。
* **不變性**:
  1. Level C 不進入 TRIZ 流程。前端顯示替代框架建議後停止。
  2. Level 判定為建議性質，RD 可覆寫。

---

## 測試情境與案例

#### 情境 1: Happy Path — Brief 抽取
* **測試案例 ID**: `TC-Analyst-001`
* **描述**: `raw_text = "電動自行車 250W，續航 80km，重量 <25kg"`。
* **Arrange**: mock `call_llm_json` 返回 `{constraints:[{code:"C1",description:"重量<25kg",...}], kpis:[{...}], assumptions:[], feasibility_warnings:[]}`。
* **Act**: `extract_brief(req)`。
* **Assert**:
  - `len(result.constraints) >= 1 && result.constraints[0].code == "C1"`
  - `result` 不含 LLM 多餘欄位（後置條件 2）

#### 情境 2: TC 正常映射（ADR-007）
* **測試案例 ID**: `TC-Analyst-01x`
* **描述**: 自然語言「重量 vs 剛性」，LLM 映射到 Param 1 (Weight) / Param 14 (Strength)。
* **Act**: `formalize_contradiction(req)`。
* **Assert**:
  - `result.type == "TC"`
  - `result.improving_param == 1` 且 `result.worsening_param == 14`
  - `result.rationale` 非空
  - `result.physical_contradiction is None`（ADR-007 不再產出 PC）

#### 情境 2b: LLM 無法映射 → reject（ADR-007）
* **測試案例 ID**: `TC-Analyst-02x`
* **描述**: 自然語言「這個專案的士氣低落」，LLM 無法映射到 39 參數任一。
* **Act**: `formalize_contradiction(req)`。
* **Assert**:
  - `result.type is None`（**不再** downgrade 至 PC）
  - `result.rationale` 非空（解釋為何無法映射）
  - logger.warning 被發射；前端據此回 Socratic 追問

#### 情境 2c: derive_su_field_from_tc 成功（ADR-007）
* **測試案例 ID**: `TC-Analyst-03x`
* **描述**: 輸入有效 TC（improving=1, worsening=14, engineering_statement 非空），LLM 推出合理 S1/S2/F。
* **Act**: `derive_su_field_from_tc(req)`。
* **Assert**:
  - `result` 為 `SuFieldModel`（非 None）
  - `result.substance_1`, `result.substance_2`, `result.field` 皆為非空 `str`
  - 無回寫 `contradictions` 表的 side effect

#### 情境 2d: derive_su_field_from_tc 失敗 → None（ADR-007）
* **測試案例 ID**: `TC-Analyst-04x`
* **描述**: LLM 推不出有意義的 S1/S2/F（回傳空字串或 exception）。
* **Act**: `derive_su_field_from_tc(req)`。
* **Assert**:
  - `result is None`
  - `logger.warning` 被呼叫（失敗訊息含 TC 的 contradiction_id）
  - 不 re-raise exception（error isolation）

#### 情境 3: Drill-down — TC→PC critic 不觸發
* **測試案例 ID**: `TC-Analyst-003`
* **描述**: `severity="minor"`，critic rule layer 判定不需分解。
* **Assert**:
  - `result.triggered == False`
  - `result.decomposed_pcs == []`
  - `result.reasoning == "L1 critic judged drill-down unnecessary."`
  - **不呼叫** LLM decomposition prompt（省 token）

#### 情境 4: Error Isolation — decomposition LLM 拋例外
* **測試案例 ID**: `TC-Analyst-004`
* **描述**: critic 觸發但 `call_llm_json` raise timeout。
* **Assert**:
  - **不** re-raise；回傳 `triggered=True, decomposed_pcs=[], reasoning="Decomposition failed: ..."`
  - logger.exception 被呼叫（WBS §3.3 error isolation）

#### 情境 5: Anti-Anchor — LLM 返回 dict 欄位被壓平
* **測試案例 ID**: `TC-Analyst-005`
* **描述**: LLM 在 `alternatives[0].mechanism` 回傳 `{"core":"...","detail":"..."}` dict。
* **Assert**:
  - `result.alternatives[0].mechanism` 為 `str`（被 `_flatten_to_str` 壓平為 `"Core: ... | Detail: ..."`）
  - Pydantic 驗證通過不拋 `ValidationError`

#### 情境 6: Socratic — 非法類別被丟棄
* **測試案例 ID**: `TC-Analyst-006`
* **描述**: LLM 返回 `questions = {"clarification":{...}, "invalid_cat":{...}}`。
* **Assert**:
  - `result.questions` 長度 == 1
  - `result.questions[0].type_class == "clarification"`
  - `"invalid_cat"` 被默默丟棄

#### 情境 7: Decomposition — derived_parameter 去重
* **測試案例 ID**: `TC-Analyst-007`
* **描述**: LLM 返回 2 個 PC 皆 `derived_parameter="重量"`。
* **Assert**:
  - `len(result.decomposed_pcs) == 1`（第 2 個被 dedup 丟棄 + logger.warning）

#### 情境 8 (v2.2): Five-Why — 根因假設含 TC 候選
* **測試案例 ID**: `TC-Analyst-008`
* **描述**: 症狀「馬達在爬坡時異音」，LLM 產出 5 層 why chain 並鎖定根因「為了減重選用了輕量化軸承 → 剛性不足」。
* **Assert**:
  - `len(result.why_chain) >= 3 and len(result.why_chain) <= 7`
  - `result.root_cause_hypothesis` 含「軸承」或「剛性」
  - `result.tc_hypothesis` 非 None，含 `improving_desc` 和 `worsening_desc`

#### 情境 9 (v2.2): Function Analysis — 產出完整 SF 診斷
* **測試案例 ID**: `TC-Analyst-009`
* **描述**: Brief 上下文為 e-bike 馬達散熱，期望產出馬達→殼體的有害熱交互 + SF 效能不足診斷。
* **Assert**:
  - `len(result.component_interactions) >= 2`
  - 至少一項 `function_type` 為 "harmful" 或 "insufficient"
  - `result.sf_diagnosis.status` ∈ {"harmful", "insufficient", "missing"}
  - `result.improvement_description` 和 `result.worsening_description` 皆非空

#### 情境 10 (v2.2): OZ-OT — Px 鎖定成功
* **測試案例 ID**: `TC-Analyst-010`
* **描述**: TC (improving=19 溫度, worsening=1 重量)，期望 Px 鎖定為散熱路徑相關物理量。
* **Assert**:
  - `result.px_found == True`
  - `result.px.variable_name` 非空
  - `result.pc_sentence.state_a` 和 `result.pc_sentence.state_not_a` 皆非空
  - `result.oz.zone_description` 和 `result.ot.time_description` 皆非空

#### 情境 11 (v2.2): Entry Grading — Level C 導向替代框架
* **測試案例 ID**: `TC-Analyst-011`
* **描述**: 問題描述「我們想做一個新產品但不知道做什麼」，應判定 Level C。
* **Assert**:
  - `result.level == "C"`
  - `result.recommended_framework` ∈ {"design_thinking", "axiomatic_design", "evolution_trends"}
  - `result.rationale` 非空

---

## 與其他 Agent 的互動

| 方向 | 對方 | 互動點 |
| --- | --- | --- |
| **呼叫者 (upstream)** | Router `pre_analyst.py`, `analyst.py`, `explore.py` | 所有 `/analyst/*` endpoint |
| **被呼叫者 (downstream)** | `TrizCriticAgent.should_trigger_pc_decomposition` | L1 critic gating（analyst.py L35, L442） |
| **共享工具** | `app.services.evidence_retrieval` | `rewrite_mission` / `suggest_constraints` / `suggest_kpis` / `generate_5w1h` 取 citation |
| **共享工具** | `app.tools.triz_kb`, `app.tools.separation_principles` | `decompose_tc_to_pcs` prompt context |
| **下游消費者** | `TrizSolverAgent` | 吃 `formalize_contradiction` 產出之 TC/PC → 解矛盾 |
| **下游消費者** | `AntiAnchorAgent` (router-embedded) | 吃 `generate_anti_anchor` 產出候選進池 |
| **下游消費者** | `ScamperFeedbackAgent` | 吃本 agent 形式化的矛盾作為 dedup baseline |

---

**LLM Prompting Guide:**
> 「請依以下測試規格，使用 pytest + pytest-asyncio 為 `AnalystAgent.formalize_contradiction` 生成失敗的 TDD 測試。測試案例 ID: TC-Analyst-002（TC 自動降級 PC 路徑）。」
