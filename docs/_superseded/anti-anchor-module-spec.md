# Module Spec: AntiAnchorAgent

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-15`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**狀態 (Status):** `Draft`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`

---

## 模組: `AntiAnchorAgent`

**原始檔**: `backend/app/routers/anti_anchor.py` + `backend/app/routers/validation.py`（主邏輯目前嵌入 router，後續預計抽 `agents/anti_anchor.py`）
**對應架構文件**: [`01-define/E3--architecture-and-design.md` Appendix C](../../../01-define/E3--architecture-and-design.md)
**對應 BDD Feature**: [`E5x--bdd-scenarios.md` §Feature 2](../../E5x--bdd-scenarios.md)
**對應 API**: `POST /alternatives/anti-anchor`, `POST /alternatives/validation-passport`

---

### 規格 1: `generate_routes(request: AntiAnchorRequest) -> AntiAnchorResponse`

**描述**: 給定已確認的 anchor solution，產生 N 條（預設 3）反向路線，打破路徑依賴。

**DbC**:
* **Preconditions**:
  1. `request.anchor_solution_id` 對應一個 `confirmed` 狀態的 solution。
  2. `request.route_count` ∈ [1, 5]，預設 3。
  3. project 已有至少一個凍結 Brief。

* **Postconditions**:
  1. 回傳 `AntiAnchorRoute[]` 長度 == `request.route_count`。
  2. 每條 route 含 `diff_score ∈ [0, 1]`（與 anchor 的差異度）。
  3. 每條 route 含 `ac_risk_level ∈ {"L","M","H","H*"}`。
  4. `diff_score` 由高至低排序。

* **Invariants**:
  1. 不同 route 的 `route_id` 不重複。
  2. `diff_score` > 0.3（完全相同 anchor 的 route 不合法）。

### 規格 2: `issue_validation_passport(route_id: str) -> ValidationPassportResponse`

**DbC**:
* **Preconditions**: `route_id` 存在且屬於使用者 project。
* **Postconditions**:
  1. 回傳 `ValidationPassport` 含 `assumptions: ValidationPassportAssumption[]`，長度 ≥ 2。
  2. 每 assumption 初始 `status = "pending"`。
  3. 每 assumption 含 `evidence_refs` (可空陣列)。

---

### 測試情境與案例

#### 情境 1: Happy Path — 產生 3 條路線
* **TC-AntiAnchor-001**: anchor=「陀螺儀平衡」→ 返回 3 條 `[彈性支撐, 主動氣動, 質心偏移]` 路線，`diff_score` 遞減。

#### 情境 2: Sad Path — 無 anchor
* **TC-AntiAnchor-002**: 傳入未 confirmed 的 solution_id → 401/400 `anchor_not_confirmed`。

#### 情境 3: 邊界 — `route_count=1`
* **TC-AntiAnchor-003**: 返回恰好 1 條，仍需 `diff_score > 0.3`。

#### 情境 4: 業務規則 — Validation Passport 自動附帶
* **TC-AntiAnchor-004**: 對高 AC 風險 (H/H*) route，`ValidationPassport.assumptions` 長度應 ≥ 3。

#### 情境 5: 冪等性 — 相同 anchor + seed 二次呼叫
* **TC-AntiAnchor-005**: 兩次 route_id 不同但 `diff_score` 分布相近（±0.05）。

---

**LLM Prompting Guide:**
> 「為 `AntiAnchorAgent.generate_routes` 生成 pytest-asyncio TDD 測試。測試 ID: TC-AntiAnchor-001。」
