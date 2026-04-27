# ~~Module Spec: ScamperFeedbackAgent~~ (v9 移除)

> **v9 移除說明 (2026-04-27)**：SCAMPER 已於 v9 移除 — 其 7 動作為 TRIZ 40 原理的子集，由 TRIZ L1/L2/L3 完全覆蓋。本模組及對應的 `scamper_feedback.py` agent 已退役。~~Anti-Anchor 已於 v10 退役，合併為 TRIZ L1 跨域去錨定步驟。~~

---

**文件版本 (Document Version):** `v1.0` → `v9-deprecated`
**最後更新 (Last Updated):** `2026-04-27`
**主要作者 (Lead Author):** `Backend AI Agents Team`
**審核者 (Reviewers):** `Tech Lead, QA Lead`
**狀態 (Status):** ~~`Active (Pilot)`~~ → `Deprecated (v9)`
**對應 VibeCoding 模板:** `07_module_specification_and_tests.md`

---

## 模組: `ScamperFeedbackAgent`

**原始檔**: `backend/app/agents/scamper_feedback.py`
**對應架構文件**: [`01-define/E3--architecture-and-design.md` Appendix E (TRIZ → SCAMPER Flow)](../../../01-define/E3--architecture-and-design.md#appendix-e-triz--scamper-flow)
**對應 BDD Feature**: [`docs/02-design/E5x--bdd-scenarios.md` §Feature SCAMPER](../../E5x--bdd-scenarios.md)
**對應 API**: `POST /scamper/feedback`（`backend/app/routers/scamper.py`）
**對應 WBS**: WP-3.5 SCAMPER → 矛盾反饋閉環

> **Appendix E 背景 (v9 / 2026-03-26)**: SCAMPER 改為純創意工具，**不回饋收斂迴圈**（避免無限 re-scan）。本 agent 的職責僅在於「把 SCAMPER 七個創意動作（Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse）在子系統層產生的候選矛盾，寫回 `contradictions` table」，供下一輪矛盾健康度分析與 RD 檢視使用；但不觸發 Phase B 自動收斂。

---

### 規格 1: `process_scamper_feedback(project_id: str, new_contradictions: list[dict]) -> ScamperFeedbackResponse`

**描述**: 處理 SCAMPER 變形階段產生的新矛盾列表，先對專案既有 `contradictions.natural_description` 與批次內其他項目做 SequenceMatcher 相似度去重（threshold = 0.80），再 bulk insert 非重複項目至 Supabase `contradictions` table，最後回報 `created_count` / `deduplicated_count` / 新建 ID 列表。

**契約式設計 (DbC)**:

* **前置條件 (Preconditions)**:
  1. `project_id` 非空字串；對應一個使用者有權限的 project。
  2. `new_contradictions` 為 `list[dict]`；每個 dict 至少含 `description` 鍵。
  3. 若某項缺 `description`，agent 會把 `desc` 視為空字串（不拋例外；但空字串會進入相似度比對 → 可能 dedup）。
  4. `severity` 欄位若缺，預設 `"minor"`。
  5. Supabase client（`get_supabase()`）可連線。

* **後置條件 (Postconditions)**:
  1. 若 `new_contradictions == []`，直接回傳 `ScamperFeedbackResponse(created_count=0, deduplicated_count=0, contradiction_ids=[])`，**不呼叫 Supabase**。
  2. 回傳之 `created_count == len(contradiction_ids)`。
  3. `created_count + deduplicated_count == len(new_contradictions)`（守恆律）。
  4. 所有新建 row：`type="TC"`、`resolved=False`、`id` 為合法 UUIDv4 字串。
  5. 新建 row 之 `natural_description` 與現有庫中任何 row 的相似度 ≤ 0.80。
  6. 批次內新建 row 兩兩之 `natural_description` 相似度 ≤ 0.80。
  7. `contradiction_ids` 順序對應實際插入 DB 的順序（由 Supabase return data 取）。

* **不變性 (Invariants)**:
  1. SequenceMatcher 相似度計算使用 `.lower()` 正規化後比對（大小寫不敏感）。
  2. `SIMILARITY_THRESHOLD = 0.80` 為模組常數（寫死，非 config）— 任何調整需走 migration + RD 同意。
  3. Agent 僅寫 `contradictions` table，**不觸發** Phase B 收斂掃描（Appendix E §v9 P1：SCAMPER 不回饋收斂迴圈）。
  4. Agent 僅處理 `type="TC"`（SCAMPER 出生的矛盾預設為現象層）；PC/SF 歸類留給後續 `formalize_contradiction`。

---

### 測試情境與案例 (Test Scenarios & Cases)

#### 情境 1: Happy Path — 全新矛盾 3 條，皆 insert
* **測試案例 ID**: `TC-ScamperFB-001`
* **描述**: Project 既有 5 條矛盾，SCAMPER 產出 3 條語意完全不同的新矛盾。
* **Arrange**: mock Supabase `.select().eq().execute()` 回傳 5 條 existing；`.insert().execute()` 回傳 3 筆插入 row。
* **Act**: `await process_scamper_feedback(project_id="p1", new_contradictions=[{description:"...A"},{description:"...B"},{description:"...C"}])`。
* **Assert**:
  - `result.created_count == 3`
  - `result.deduplicated_count == 0`
  - `len(result.contradiction_ids) == 3`，每個為合法 UUID

#### 情境 2: Edge — 空輸入
* **測試案例 ID**: `TC-ScamperFB-002`
* **描述**: `new_contradictions == []`。
* **Assert**:
  - `result.created_count == 0 && result.deduplicated_count == 0`
  - Supabase 的 `get_supabase()` / `.table()` **完全未被呼叫**（mock 斷言 not_called，對應後置條件 1）

#### 情境 3: Dedup — 與既有矛盾相似
* **測試案例 ID**: `TC-ScamperFB-003`
* **描述**: 既有庫含 `"電池重量影響續航"`；新進 `"電池的重量影響續航距離"`（SequenceMatcher ratio > 0.80）。
* **Assert**:
  - `result.created_count == 0`
  - `result.deduplicated_count == 1`
  - `contradiction_ids == []`
  - Supabase `.insert()` 未被呼叫

#### 情境 4: Within-Batch Dedup — 批次內重複
* **測試案例 ID**: `TC-ScamperFB-004`
* **描述**: 既有庫空；批次輸入 `[{description:"馬達過熱"}, {description:"馬達過熱問題"}, {description:"煞車距離不足"}]`，前 2 條 ratio > 0.80。
* **Assert**:
  - `result.created_count == 2`（第 1 條 + 第 3 條）
  - `result.deduplicated_count == 1`（第 2 條被 within-batch dedup）
  - 守恆律：2 + 1 == 3 ✓

#### 情境 5: 邊界 — 相似度正好 0.80
* **測試案例 ID**: `TC-ScamperFB-005`
* **描述**: 建構兩個字串使 SequenceMatcher ratio == 0.80（threshold 邊界）。
* **Assert**:
  - 依實作 `ratio > SIMILARITY_THRESHOLD`（strict greater），0.80 **不**算 duplicate → 應被 insert
  - `result.created_count == 1`

#### 情境 6: 欄位預設 — 缺 severity
* **測試案例 ID**: `TC-ScamperFB-006`
* **描述**: 輸入 `[{description:"..."}]`，無 `severity` key。
* **Assert**:
  - 實際插入 Supabase 的 row 含 `severity="minor"`（預設值）
  - `type="TC"`、`resolved=False`

#### 情境 7: 上游失敗 — Supabase insert 拋例外
* **測試案例 ID**: `TC-ScamperFB-007`
* **描述**: `client.table("contradictions").insert(...).execute()` raise `supabase.PostgrestAPIError`。
* **Assert**:
  - Exception propagates（目前實作不吞錯；router 層轉 500）
  - **TBD (owner: Backend AI, 2026-05)**: 是否改為 partial-success（已去重計數保留 + error flag）尚未決定。

---

## 與其他 Agent / 模組的互動

| 方向 | 對方 | 互動點 |
| --- | --- | --- |
| **呼叫者 (upstream)** | `backend/app/routers/scamper.py` | `POST /scamper/feedback` 端點 |
| **上游資料來源** | 前端 SCAMPER Tab 產出的候選矛盾 list | UI 在 Explore Tab ③ 變形階段收集 |
| **被呼叫者 (downstream)** | Supabase `contradictions` table | `.select()` 取 existing + `.insert()` 寫新 row |
| **不互動 (刻意)** | `TrizSolverAgent`, Phase B convergence scanner | 依 Appendix E §v9 P1：SCAMPER 不回饋收斂迴圈 |
| **間接下游** | `AnalystAgent.formalize_contradiction` | 後續由 Analyst 將新寫入的 TC 形式化為 TRIZ 39 參數對 |
| **間接下游** | `EvaluatorAgent` | 新矛盾可能影響 MUST 健康度評分，但需 RD 觸發下一輪評估 |

---

## 連結

- E3 Appendix E §1（主流程總覽：F3 SCAMPER 變形 → 候選池，**不觸發 re-scan**）
- E3 Appendix E §v9 P1 設計決策
- WBS WP-3.5（SCAMPER 反饋閉環）

---

**LLM Prompting Guide:**
> 「請依以下測試規格，使用 pytest + pytest-asyncio 為 `process_scamper_feedback` 生成失敗的 TDD 測試。測試案例 ID: TC-ScamperFB-004（within-batch dedup 路徑）。請 mock `get_supabase()` 並斷言守恆律 created_count + deduplicated_count == len(input)。」
