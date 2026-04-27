# Module Spec: EvidenceRegistryService

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-04-23`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**審核者 (Reviewers):** `Tech Lead, QA Lead`
**狀態 (Status):** `Proposed`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`
**觸發 ADR:** [ADR-008](../../../01-define/adrs/ADR-008-auto-triz-v2-integration.md)

---

## 模組: `EvidenceRegistryService`

**預計原始檔**: `backend/app/services/evidence_registry.py`
**對應架構文件**: `[01-define/E3--ai-agent-detailed-design.md` §11.5.4](../../../01-define/E3--ai-agent-detailed-design.md) (v2.2 新增)
**對應 API**:

- `POST /evidence/register-claim`
- `POST /evidence/verify`
- `GET /evidence/coverage`

---

## 職責

EvidenceRegistryService 是 Auto-TRIZ v2 整合的 **cross-cutting 數據驗證層**（ADR-008 D3）。所有 LLM agent 產出的數值聲明（材料性質、物理參數、成本估算等）須經此服務註冊並驗證，降低 hallucination 風險。對應 `docs_harness/auto_triz_strategy.md` 的 Injection Point A/B 數據驗證門檻。

**核心價值**：

- 每個數值聲明有唯一 `claim_id`，可追溯至產生該 claim 的 agent + step
- 透過 Tavily WebSearch 自動驗證，標記驗證等級
- Gate 退出條件使用 Evidence Coverage 作為品質門檻

---

### 規格 1: `register_claim(req: RegisterClaimRequest) -> RegisterClaimResponse`

**描述**: 註冊一個數值聲明至 Evidence Registry。每個 claim 記錄來源 agent、step、原始數值、單位、上下文。

**契約式設計 (DbC)**:

- **前置條件**:
  1. `req.project_id` 非空且使用者有權限。
  2. `req.claim_text` 非空（數值聲明的自然語言描述，如「N42SH 永磁體殘磁 Br = 1.29T」）。
  3. `req.source_agent` ∈ {"analyst", "triz_solver", "evaluator", "knowledge"}。
  4. `req.source_step` 非空（產生此 claim 的步驟編號，如 "5a", "2c"）。
  5. `req.numerical_value` 可選（結構化數值，如 `1.29`）。
  6. `req.unit` 可選（單位，如 "T" (Tesla)）。
- **後置條件**:
  1. 回傳 `claim_id` 格式為 `CLM-{project_short}-{seq:04d}`（如 `CLM-EBIKE-0001`）。
  2. `status` 初始為 `"UNVERIFIED"`。
  3. `registered_at` 為 ISO8601 時間戳。
  4. Claim 寫入 `evidence_claims` 表。
- **不變性**:
  1. 同一 `claim_text` + `project_id` 重複註冊時，回傳既有 `claim_id`（冪等）。
  2. 註冊不觸發驗證（驗證為獨立步驟）。

---

### 規格 2: `verify_claim(req: VerifyClaimRequest) -> VerifyClaimResponse`

**描述**: 對已註冊的 claim 執行外部驗證。使用 Tavily WebSearch 搜尋佐證資料，根據搜尋結果判定驗證等級。

**契約式設計 (DbC)**:

- **前置條件**:
  1. `req.claim_id` 對應存在的 `evidence_claims` row。
  2. Tavily API key 已配置（`TAVILY_API_KEY` env var）。
- **後置條件**:
  1. `result.verification_status` ∈ {"VERIFIED", "APPROXIMATE", "UNVERIFIED"}：
    - **VERIFIED**：找到 ≥1 個可靠來源（學術論文、材料資料表、標準文件）明確支持該數值（誤差 ≤5%）。
    - **APPROXIMATE**：找到相關來源但數值有差異（5-20% 範圍內）或來源可靠度中等。
    - **UNVERIFIED**：未找到支持來源，或來源不可靠。
  2. `result.sources[]` 為驗證過程中找到的參考來源，每項含 `url`, `title`, `snippet`, `relevance_score`。
  3. `result.verified_at` 為 ISO8601 時間戳。
  4. `evidence_claims` 表的 `status` 欄位更新。
- **不變性**:
  1. 驗證結果可重跑（非冪等 — 新搜尋可能改變結果）。
  2. Tavily API 失敗時，status 保持 `"UNVERIFIED"` + 記錄 error log，不 re-raise。
  3. 單次驗證的 WebSearch 查詢次數 ≤ 3（避免 API quota 浪費）。

---

### 規格 3: `get_coverage(req: CoverageRequest) -> CoverageResponse`

**描述**: 取得特定 project 的 Evidence Coverage 統計。Coverage = (VERIFIED + APPROXIMATE) / total claims。用於 Gate 退出條件判定。

**契約式設計 (DbC)**:

- **前置條件**:
  1. `req.project_id` 非空。
  2. `req.step_filter` 可選（僅統計特定 step 的 claims）。
- **後置條件**:
  1. `result.total_claims` 為該 project（及 step filter）的 claim 總數。
  2. `result.verified_count`、`result.approximate_count`、`result.unverified_count` 三者之和 = `total_claims`。
  3. `result.coverage_ratio` = (verified + approximate) / total，∈ [0, 1]。若 total = 0 則為 0。
  4. `result.meets_threshold` 為 boolean — `coverage_ratio >= threshold`（預設 threshold = 0.4，可由 project config 覆寫）。
- **不變性**:
  1. 純查詢，無 side effect。
  2. Coverage 計算不含已刪除或歸檔的 claims。

---

## 資料模型

### `evidence_claims` 表


| 欄位                     | 型別          | 說明                                              |
| ---------------------- | ----------- | ----------------------------------------------- |
| `id`                   | UUID        | PK                                              |
| `project_id`           | UUID        | FK → projects                                   |
| `claim_id`             | TEXT        | 業務 ID，格式 `CLM-{project_short}-{seq:04d}`，UNIQUE |
| `claim_text`           | TEXT        | 數值聲明自然語言                                        |
| `numerical_value`      | FLOAT       | 結構化數值（可選）                                       |
| `unit`                 | TEXT        | 單位（可選）                                          |
| `source_agent`         | TEXT        | 產生此 claim 的 agent                               |
| `source_step`          | TEXT        | 產生此 claim 的步驟                                   |
| `source_context`       | JSONB       | 額外上下文（如 contradiction_id, solution_id）          |
| `status`               | TEXT        | `UNVERIFIED` / `APPROXIMATE` / `VERIFIED`       |
| `verification_sources` | JSONB       | 驗證來源 `[{url, title, snippet, relevance_score}]` |
| `verified_at`          | TIMESTAMPTZ | 最後驗證時間                                          |
| `created_at`           | TIMESTAMPTZ | 建立時間                                            |


**RLS**: `project_id` 對齊 project ownership。

---

## 測試情境與案例

#### 情境 1: 註冊 claim — 正常

- **測試案例 ID**: `TC-Evidence-001`
- **描述**: 註冊「N42SH Br = 1.29T」，來源 triz_solver / step 5a。
- **Assert**:
  - `result.claim_id` 格式正確（`CLM-*-0001`）
  - `result.status == "UNVERIFIED"`
  - DB 有對應 row

#### 情境 2: 註冊 claim — 冪等

- **測試案例 ID**: `TC-Evidence-002`
- **描述**: 相同 `claim_text` + `project_id` 重複註冊。
- **Assert**:
  - 第二次回傳與第一次相同的 `claim_id`
  - DB 仍只有 1 row

#### 情境 3: 驗證 claim — VERIFIED

- **測試案例 ID**: `TC-Evidence-003`
- **描述**: mock Tavily 回傳含材料資料表佐證「N42SH Br = 1.28-1.30T」。
- **Assert**:
  - `result.verification_status == "VERIFIED"`
  - `len(result.sources) >= 1`
  - DB status 更新為 VERIFIED

#### 情境 4: 驗證 claim — Tavily 失敗

- **測試案例 ID**: `TC-Evidence-004`
- **描述**: Tavily API timeout。
- **Assert**:
  - `result.verification_status == "UNVERIFIED"`
  - 不 re-raise，logger.error 被呼叫

#### 情境 5: Coverage — 門檻判定

- **測試案例 ID**: `TC-Evidence-005`
- **描述**: 10 claims，4 VERIFIED + 2 APPROXIMATE + 4 UNVERIFIED。
- **Assert**:
  - `result.coverage_ratio == 0.6`
  - `result.meets_threshold == True`（預設門檻 0.4）

---

## 與其他模組的互動


| 方向                  | 對方                                                   | 互動點                              |
| ------------------- | ---------------------------------------------------- | -------------------------------- |
| **被呼叫者 (upstream)** | 所有 Agent（analyst, triz_solver, evaluator, knowledge） | 產出數值聲明時呼叫 `register_claim`       |
| **被呼叫者 (upstream)** | Router `/evidence/`*                                 | API endpoint 層                   |
| **依賴 (downstream)** | `app.services.web_search` (Tavily)                   | `verify_claim` 用 WebSearch 做外部驗證 |
| **消費者**             | `EvaluatorAgent`                                     | Gate 判定時呼叫 `get_coverage` 檢查門檻   |
| **消費者**             | 前端 `EvidenceCoverageGauge`                           | Dashboard 顯示 coverage 統計         |


