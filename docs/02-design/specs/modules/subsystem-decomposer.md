# Module Spec: SubsystemDecomposerAgent

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-15`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**狀態 (Status):** `Draft`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`

---

## 模組: `SubsystemDecomposerAgent`

**原始檔**: 分散於 `backend/app/routers/subsystems.py` (`/subsystems/suggest`) + `backend/app/services/package_svg.py` + `backend/app/routers/spatial.py` *(v9: 原 `scamper.py` 遷移)*
**對應架構文件**: [`01-define/E3--architecture-and-design.md` Appendix A + E](../../../01-define/E3--architecture-and-design.md)
**對應 BDD Feature**: Create Tab ② subsystem 流程（E5x BDD Feature 1 Background 所依賴）
**對應 Spec**: [`specs/explore/E5x--subsystem-persistence-policy.md`](../explore/E5x--subsystem-persistence-policy.md) · [`specs/explore/E5x--three-tier-tree-review-checklist.md`](../explore/E5x--three-tier-tree-review-checklist.md)
**對應 API**: `POST /subsystems/suggest` *(v9: 原 `/scamper/subsystem-suggestions`)*, `PATCH /subsystems/{id}`

---

### 規格 1: `suggest_subsystems(request) -> SubsystemSuggestResponse`

**描述**: 依 Brief + 矛盾，建議 3-7 個子系統（含 bbox、介面契約 placeholder）。*(v9: SCAMPER 變體輸入已移除)*

**DbC**:
* **Preconditions**:
  1. project 已凍結 Brief。
  2. 至少一個 contradiction formalized。
  3. ~~若傳入 `scamper_variant_ids`，全部必須屬於同一 project。~~ *(v9: SCAMPER 參數已移除)*

* **Postconditions**:
  1. `suggestions: SuggestedSubsystem[]` 長度 ∈ [3, 7]。
  2. 每 subsystem 含 `bbox: BBox` (spatial estimate)。
  3. 每 subsystem 含 `interface_contracts: Record<string, InterfaceContract>`（可空 dict，但 key 命名必須 kebab-case）。
  4. 不同 subsystem 的 `id` 不重複。
  5. 若 `interface_contracts` 非空，每個 contract 含 `direction ∈ {"in","out","bidirectional"}`。

* **Invariants**:
  1. 不主動寫入 DB（僅 suggest；persistence 由前端 confirm 後觸發 PATCH）— 見 persistence policy spec。
  2. `bbox` 座標均為正數 (≥ 0)。

### 規格 2: `confirm_subsystem(id, patch)` *(TBD endpoint)*

**DbC Preconditions**: subsystem exists in suggestion store; user owns project.
**Postconditions**: DB `subsystems` 寫入單筆（唯一寫者原則，見 persistence-policy spec §3）。

---

### 測試情境與案例

#### 情境 1: Happy Path — 4 個子系統建議
* **TC-Subsystem-001**: Brief="e-bike 自動平衡", 1 contradiction → 返回 4 個 subsystem（`frame`, `sensor`, `actuator`, `controller`），每個含非空 bbox。

#### 情境 2: ~~邊界 — 無 SCAMPER 變體~~ *(v9: SCAMPER 移除，此情境為預設行為)*
* **TC-Subsystem-002**: 僅基於 contradiction → 返回 3 個以上建議。

#### 情境 3: 違反前置 — 未凍結 Brief
* **TC-Subsystem-003**: Brief status=draft → 422 `brief_not_frozen`。

#### 情境 4: 業務規則 — 不主動寫 DB
* **TC-Subsystem-004**: Mock DB layer 記錄所有 write call；suggest 端點呼叫完後 `db.subsystems.insert.call_count == 0`。

#### 情境 5: 介面契約 key 命名規則
* **TC-Subsystem-005**: 若 LLM 回 `{"PowerInput": {...}}` → adapter 必須轉 `power-input` 或拋 validation error。

#### 情境 6: Persistence policy 唯一寫者
* **TC-Subsystem-006**: confirm_subsystem 對同一 id 二次呼叫 → 第二次返回 `409 conflict_duplicate_write`。

---

**LLM Prompting Guide:**
> 「為 `SubsystemDecomposerAgent.suggest_subsystems` 生成 pytest 測試。TC-Subsystem-001。」
