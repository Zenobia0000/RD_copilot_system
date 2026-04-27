# E5 — API Design Specification (RD Design Copilot Backend)

---

**文件版本 (Document Version):** `v1.2`
**最後更新 (Last Updated):** `2026-04-24`
**主要作者/設計師 (Lead Author/Designer):** `RD Design Copilot Backend Team`
**審核者 (Reviewers):** `架構團隊、前端團隊、QA`
**狀態 (Status):** `Active`
**相關 SD 文檔:** [`01-define/E3--architecture-and-design.md`](../01-define/E3--architecture-and-design.md) (Appendix A–E)
**OpenAPI 定義文件:** `backend/app/main.py` (FastAPI 自動生成 `/openapi.json` · Schema 源 → `backend/app/models/schemas.py`)
**對應 VibeCoding 模板:** `06_api_design_specification.md`

---

## 目錄 (Table of Contents)

1. [引言 (Introduction)](#1-引言-introduction)
2. [設計原則與約定 (Design Principles and Conventions)](#2-設計原則與約定-design-principles-and-conventions)
3. [認證與授權 (Authentication and Authorization)](#3-認證與授權-authentication-and-authorization)
4. [通用 API 行為 (Common API Behaviors)](#4-通用-api-行為-common-api-behaviors)
5. [錯誤處理 (Error Handling)](#5-錯誤處理-error-handling)
6. [安全性考量 (Security Considerations)](#6-安全性-考量-security-considerations)
7. [API 端點詳述 (API Endpoint Definitions)](#7-api-端點詳述-api-endpoint-definitions)
8. [資料模型/Schema 定義 (Data Models / Schema Definitions)](#8-資料模型schema-定義-data-models--schema-definitions)
9. [API 生命週期與版本控制](#9-api-生命週期與版本控制)
10. [附錄 (Appendix)](#10-附錄-appendix)

---

## 1. 引言 (Introduction)

### 1.1 目的 (Purpose)
為 RD Design Copilot 的前端（React 19 SPA）與後端（FastAPI）提供統一、可機器驗證的 API 契約，並透過 `pydantic2ts` 將 Pydantic schema 單向同步至 TypeScript，確保 BE/FE 型別零漂移。

### 1.2 目標讀者 (Target Audience)
前端工程師、後端工程師、QA、Agent 開發者（TRIZ Solver / Anti-Anchor / Subsystem Decomposer）。

### 1.3 快速入門 (Quick Start)
- **第 1 步**：啟動本地 backend `cd backend && uvicorn app.main:app --reload --port 8000`
- **第 2 步**：
  ```bash
  curl -X POST http://localhost:8000/triz/solve-layered \
    -H 'Content-Type: application/json' \
    -d '{"contradiction_id":"C-01","improving":"weight","worsening":"rigidity"}'
  ```
- **預期回應**: `SolveTrizLayeredResponse`（含 `l1_surface`、`l2_root_cause`、`l3_sufield` 分層）

---

## 2. 設計原則與約定 (Design Principles and Conventions)

### 2.1 API 風格
- **風格**：RESTful + 部分 RPC-flavored (`/triz/solve-layered`, `/scamper/perform`)。
- **核心原則**：資源導向（`/subsystems/{id}`、`/contradictions/{cid}`）；AI 計算類端點使用動詞命名。

### 2.2 基本 URL (Base URL)
- **Dev**: `http://localhost:8000`
- **Staging**: `TBD — <infra-lead TBD> by <2026-05-01 TBD>`
- **Production**: `TBD — <infra-lead TBD> by <2026-05-01 TBD>`
- **版本策略**：v1 目前隱含在路徑前；未來破壞性變更導入 `/v2/`。

### 2.3 請求與回應格式
- `application/json` (UTF-8)；Pydantic `model_config.populate_by_name=True` → 接受 snake_case（BE 原生）與 camelCase（FE adapter）。
- 詳見 [`specs/explore/E5x--tc-to-multipc-type-alignment.md`](specs/explore/E5x--tc-to-multipc-type-alignment.md)。

### 2.4 標準 HTTP Headers
- `Authorization: Bearer <supabase-jwt>`（見 `backend/app/middleware/auth.py`）
- `X-Request-ID`（`backend/app/middleware/request_id.py` 自動生成）
- `Content-Type: application/json`、`Accept: application/json`

### 2.5 命名約定
- 路徑：kebab-case 複數名詞（`/pre-cad-reviews/`, `/anti-anchor/`, `/unknown-factors/`）
- JSON 欄位（後端真相）：`snake_case`
- 前端 adapter 層轉 `camelCase`

### 2.6 日期時間格式
ISO 8601 + UTC（e.g. `2026-04-15T10:00:00Z`）。

---

## 3. 認證與授權 (Authentication and Authorization)

### 3.1 認證機制
- **機制**：Supabase Auth（JWT Bearer）。
- **實作**：`backend/app/middleware/auth.py` 驗證 JWT，注入 `user_id` 至 request state。

### 3.2 授權模型
- **模型**：Supabase RLS（Row-Level Security）+ `project_id` 歸屬檢查。
- **詳情**：`TBD — <security-lead TBD> by <2026-05-15 TBD>`（RBAC scope 尚未正式編目）。

---

## 4. 通用 API 行為 (Common API Behaviors)

### 4.1 分頁
目前多數列表端點為「單一 project 下完整返回」模式；若單 project 列表 > 500，轉 offset 分頁。預設 `TBD — <be-lead TBD>`。

### 4.2 排序 / 4.3 過濾
多數 AI 端點為一次性計算，非列表；列表端點（如 `/spatial/component-overrides`）以 query param `project_id` 過濾。

### 4.4 部分回應 / 4.5 關聯擴展
暫不支援 `fields` / `expand`；Phase B 需求再導入。

### 4.6 冪等性
- `POST /export`、`POST /knowledge/writeback` 建議帶 `Idempotency-Key`（header），避免重複寫入。
- 現況：`TBD — <be-lead TBD>`（尚未強制驗證）。

---

## 5. 錯誤處理 (Error Handling)

### 5.1 標準錯誤回應格式
由 `backend/app/middleware/error_handler.py` 統一包裝：
```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "parameter_missing",
    "message": "contradiction_id is required",
    "param": "contradiction_id",
    "request_id": "req_01HXYZ..."
  }
}
```

### 5.2 通用 HTTP 狀態碼
- 2xx: `200 OK`, `201 Created`, `204 No Content`
- 4xx: `400`, `401`, `403`, `404`, `409`, `422`, `429`
- 5xx: `500`, `502`（LLM upstream 失敗）, `503`

### 5.3 錯誤碼字典
| `error.code` | HTTP | 描述 |
|---|---|---|
| `parameter_missing` | 400 | 必填缺失 |
| `parameter_invalid` | 422 | Pydantic validation fail |
| `authentication_failed` | 401 | JWT 無效/過期 |
| `permission_denied` | 403 | 不屬於此 project |
| `resource_not_found` | 404 | contradiction/subsystem/review 不存在 |
| `llm_upstream_error` | 502 | Anthropic/OpenAI 調用失敗 |
| `rate_limit_exceeded` | 429 | 單 user/project 超速 |
| `internal_server_error` | 500 | 未知錯誤 |

---

## 6. 安全性考量 (Security Considerations)

### 6.1 TLS
生產環境強制 HTTPS (TLS 1.2+)；本地 dev 可 HTTP。

### 6.2 HTTP 安全 Headers
`TBD — <infra-lead TBD> by <2026-05-15 TBD>`（HSTS / CSP 部署於 edge proxy）。

### 6.3 Rate Limiting
現況：`TBD — <be-lead TBD>`（規劃在 middleware 以 Redis token bucket 實作；優先限制 LLM-heavy 端點）。

### 6.4 OWASP API Top 10
- BOLA：以 Supabase RLS + project_id 綁定緩解
- Excessive Data Exposure：Pydantic response_model 嚴格白名單
- 其餘：`TBD — <security-lead TBD>`

---

## 7. API 端點詳述 (API Endpoint Definitions)

以下端點從 `backend/app/routers/*.py` 實際掃描。對應 E3 Appendix A/B 架構。

### 7.1 資源：Brief / Task Definition (`brief.py`)
| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/definitions/extract` | `BriefExtractionRequest` | `BriefExtractionResponse` |
| POST | `/definitions/rewrite` | `BriefRewriteRequest` | `BriefRewriteResponse` |
| POST | `/definitions/check-feasibility` | `ConstraintFeasibilityRequest` | `ConstraintFeasibilityResponse` |
| POST | `/definitions/suggest-constraints` | `ConstraintSuggestRequest` | `ConstraintSuggestResponse` |
| POST | `/definitions/suggest-kpis` | `KpiSuggestRequest` | `KpiSuggestResponse` |
| POST | `/definitions/generate-5w1h` | `TaskDef5W1HRequest` | `TaskDef5W1HResponse` |

### 7.2 資源：Socratic 問題 (`socratic.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/questions/generate` | `SocraticResponse` |
| POST | `/questions/follow-up` | `SocraticFollowUpResponse` |
| POST | `/questions/brief-impact` | `SocraticBriefImpactResponse` |
| POST | `/questions/auto-tag` | `SocraticAutoTagResponse` |

### 7.3 資源：因果迴圈 (`cld.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/causal-loops/generate` | `CldGenerationResponse` |

### 7.4 資源：Contradictions (`contradictions.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/contradictions/{cid}/formalize` | `ContradictionFormalizeResponse` |
| POST | `/contradictions/{cid}/decompose` | `ContradictionDecomposeResponse` |

> **ADR-007 (2026-04-15)**: `/contradictions/{cid}/formalize` 已改為 TC-only 合約：
> - **Response schema**: `type: "TC" | null`（移除 `"PC"` / `"SF"` 舊值）；新增 `rationale: str` 欄位（成功時說明映射理由，失敗時解釋為何無法映射到 39 參數）。
> - **Deprecated 欄位**（仍保留於 schema 供舊資料讀取，但新寫入不填）：`physical_contradiction`、`sf_substance_1`、`sf_substance_2`、`sf_field`。
> - **成功條件**：`type="TC"` 且 `improving_param`, `worsening_param` ∈ [1, 39]。
> - **失敗條件**（不再 downgrade 至 PC）：`type=null` + `rationale` 非空，由前端導引使用者回 Socratic 追問。
> - 詳見 [ADR-007](../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md) 與 E3 Appendix B §B.0。

### 7.5 資源：TRIZ (`triz.py`) ★ 核心
| Method | Path | Response |
|---|---|---|
| POST | `/triz/solve` | `TrizLookupResponse` |
| POST | `/triz/sufield` | `SuFieldResponse` |
| POST | `/triz/solve-layered` | `SolveTrizLayeredResponse` |

> **ADR-007 (2026-04-15)**: `/triz/solve-layered` 若 request 缺 `sf_substance_1/2`、`sf_field`、`physical_contradiction` 欄位，後端於 agent 入口**自動派生**（`analyst.derive_su_field_from_tc` + `analyst.decompose_tc_to_pcs`）。派生產物僅於本次 response 回傳，**不回寫** `contradictions` 表。若 SF 派生失敗，L3 降級為 warning，L1/L2 不受影響。詳見 [ADR-007](../01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md) 與 E3 Appendix B §B.0。

### 7.6 資源：SCAMPER / Subsystem (`scamper.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/scamper/perform` | `ScamperResponse` |
| POST | `/scamper/subsystem-suggestions` | `SubsystemSuggestResponse` |
| POST | `/scamper/spatial-overlay` | `SpatialOverlayResponse` |
| POST | `/scamper/feedback-contradictions` | `ScamperFeedbackResponse` |

### 7.7 資源：Anti-Anchor / Validation (`anti_anchor.py`, `validation.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/alternatives/anti-anchor` | `AntiAnchorResponse` |
| POST | `/alternatives/validation-passport` | `ValidationPassportResponse` |

### 7.8 資源：Convergence / Unknown Factors (`convergence.py`, `unknown_factors.py`)
| Method | Path | Response |
|---|---|---|
| POST | `/convergence/scan` | `ConvergenceScanResponse` |
| POST | `/unknown-factors/discover` | `UnknownFactorDiscoverResponse` |

### 7.9 資源：Assumption / Risk / Action
| Method | Path | Response |
|---|---|---|
| POST | `/assumptions/extract` | `AssumptionExtractResponse` |
| POST | `/risks/analyze` | `RiskAnalysisResponse` |
| POST | `/actions/suggest` | `ActionSuggestResponse` |

### 7.10 資源：Want / MUST / Pre-CAD Gate
| Method | Path | Response |
|---|---|---|
| POST | `/want/criteria/seed` | `WantSeedResponse` |
| POST | `/must/evaluate` | `MustEvaluationResponse` |
| POST | `/pre-cad-reviews/{rid}/ai-analyze` | `PreCadAnalyzeResponse` |
| GET | `/gates/{gate_id}/check` | `GateCheckResponse` |

### 7.11 資源：Spatial (`spatial.py`)
| Method | Path | 用途 |
|---|---|---|
| POST | `/spatial/component-overrides` | 新增 override |
| GET | `/spatial/component-overrides` | 列出 |
| DELETE | `/spatial/component-overrides` | 刪除 |
| POST | `/spatial/learn` | 學習新元件 |
| GET | `/spatial/learned-components` | 列學習記錄 |

### 7.12 資源：Knowledge Writeback / Export
| Method | Path | Response |
|---|---|---|
| POST | `/knowledge/writeback` | `KnowledgeWritebackResponse` |
| POST | `/export` | `ExportResponse` |

> **未列出端點**：`TBD — <be-lead TBD> by <2026-05-01 TBD>`（若有 router 漏掃請於 PR 補）

### 7.13 資源：Analyst v2 (`analyst.py`) (Auto-TRIZ v2 新增)

> **ADR-008 (2026-04-23)**：Auto-TRIZ v2 閉環流程整合，新增問題定向 + 功能建模 + 入口分級端點。

| Method | Path | Request | Response | 說明 |
|---|---|---|---|---|
| POST | `/api/v1/analyst/five-why` | `FiveWhyRequest` | `FiveWhyResponse` | 5Why 根因分析，產出 5 層 Why chain |
| POST | `/api/v1/analyst/kt-analysis` | `KtAnalysisRequest` | `KtAnalysisResponse` | KT Is/Is Not 範圍界定 |
| POST | `/api/v1/analyst/function-analysis` | `FunctionAnalysisRequest` | `FunctionAnalysisResponse` | FA 功能建模，產出組件交互圖 + SF 診斷 |
| POST | `/api/v1/analyst/oz-ot-analysis` | `OzOtAnalysisRequest` | `OzOtAnalysisResponse` | OZ-OT 時空分析，鎖定每個 TC 的 Px 變量 |
| POST | `/api/v1/analyst/entry-grading` | `EntryGradingRequest` | `EntryGradingResponse` | 入口等級判定（Level A/B/C），驅動 Explore Conditional Stepper |

### 7.14 資源：TRIZ v2 (`triz.py` 擴充) (Auto-TRIZ v2 新增)

> **ADR-008 (2026-04-23)**：多 TC 交互評估 + 概念複雜度指標。

| Method | Path | Request | Response | 說明 |
|---|---|---|---|---|
| POST | `/api/v1/triz/sim-matrix` | `SimMatrixRequest` | `SimMatrixResponse` | 解法交互矩陣（+1/0/-1），評估多 TC 間候選解法交互效應 |
| POST | `/api/v1/triz/complexity-check` | `ComplexityCheckRequest` | `ComplexityCheckResponse` | CCI 概念複雜度指標（0-1 連續值），判定 Evolution / Weak Evolution / Patch |

### 7.15 資源：Evidence Registry (`evidence.py`) (Auto-TRIZ v2 新增)

> **ADR-008 (2026-04-23)**：LLM 數值聲明驗證，降低 hallucination 風險。

| Method | Path | Request | Response | 說明 |
|---|---|---|---|---|
| POST | `/api/v1/evidence/claims` | `EvidenceClaimRequest` | `EvidenceClaimResponse` | 登記 evidence claim（數值聲明） |
| POST | `/api/v1/evidence/claims/{id}/verify` | — | `EvidenceVerifyResponse` | 觸發 WebSearch 驗證 claim，標記 VERIFIED/APPROXIMATE/UNVERIFIED |
| GET | `/api/v1/evidence/coverage/{project_id}` | — | `EvidenceCoverageResponse` | 查詢專案 evidence 覆蓋率（VERIFIED + APPROXIMATE 佔比） |

---

## 8. 資料模型/Schema 定義 (Data Models / Schema Definitions)

**事實來源**：`backend/app/models/schemas.py`（單檔，~80+ Pydantic 類別）。
**前端鏡像**：`src/types/generated/*.ts`（`pydantic2ts` 產出，見 [`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md)）。

### 8.1 核心 Schema 索引（抽樣）

| Schema | 用途 | 位置 |
|---|---|---|
| `EvidenceReference` | 所有 AI 答案的 citation 標準結構 | `schemas.py` L15 |
| `LayeredTrizSolution` | L1/L2/L3 分層輸出 | `schemas.py` L639 |
| `SolveTrizLayeredRequest/Response` | 主 TRIZ 端點 I/O | `schemas.py` L659/679 |
| `AntiAnchorRoute` / `AntiAnchorResponse` | 反向路線 | `schemas.py` L376/392 |
| `ValidationPassport` | 假設清單 | `schemas.py` L356 |
| `ScamperVariant` / `ScamperResponse` | SCAMPER 變體 | `schemas.py` L708/727 |
| `CldNode/Edge/Loop/Breakpoint` | 因果迴圈圖 | `schemas.py` L280–299 |

### 8.1b 新增 Schema 索引 (Auto-TRIZ v2 新增)

| Schema | 用途 | 對應端點 |
|---|---|---|
| `FunctionModel` | FA 功能建模結果（組件交互圖 + SF 診斷） | `/analyst/function-analysis` |
| `OzOtResult` | OZ-OT 時空分析結果（zone/time/px_variable） | `/analyst/oz-ot-analysis` |
| `SimMatrixResult` | 多 TC SIM 交互矩陣（+1/0/-1 評分陣列） | `/triz/sim-matrix` |
| `ComplexityCheckResult` | CCI 複雜度判定（score + verdict） | `/triz/complexity-check` |
| `EvidenceClaim` | 數值聲明（claim_text + source_agent + verification_status） | `/evidence/claims` |

### 8.1c 新增 DB 表 (Auto-TRIZ v2 新增)

| 表名 | 用途 | 關聯 |
|---|---|---|
| `function_models` | FA 功能模型持久化 | `project_id` → `projects` |
| `evidence_claims` | LLM 數值聲明登記與驗證 | `project_id` → `projects` |
| `sim_matrices` | 多 TC SIM 交互矩陣結果 | `project_id` → `projects` |

> `contradictions` 表新增欄位：`oz_zone`（Operating Zone）、`ot_time`（Operating Time）、`px_variable`（鎖定的物理參數）。

### 8.2 範例：`LayeredTrizSolution` （節錄）
```python
class LayeredTrizSolution(BaseModel):
    l1_surface: L1Surface | None
    l2_root_cause: L2RootCause | None
    l3_sufield: SuFieldModel | None
    differential: DifferentialAnalysis | None
    phase_b_directive: PhaseBDirective | None
    # ... 詳見 schemas.py L639+
```

---

## 9. API 生命週期與版本控制

### 9.1 生命週期階段
| 端點類別 | 階段 |
|---|---|
| Brief / TaskDef / Socratic / CLD | GA |
| TRIZ (solve, solve-layered, sufield) | GA |
| SCAMPER / Subsystem Suggestions | Beta |
| Anti-Anchor / Validation Passport | Beta |
| Spatial Overlay / Learn | Alpha |
| Analyst v2 (5Why / KT / FA / OZ-OT / Entry Grading) | Beta (Auto-TRIZ v2) |
| TRIZ v2 (SIM Matrix / Complexity Check) | Beta (Auto-TRIZ v2) |
| Evidence Registry (Claims / Verify / Coverage) | Beta (Auto-TRIZ v2) |

### 9.2 版本控制策略
URL 路徑版本（未來 `/v2/`）；目前僅一版。  
**向後兼容變更**：新增端點、response 新增可選欄位 → 不升版。  
**破壞性變更**：改欄位名、刪欄位、改型別 → 必升主版；同步 Pydantic schema + pydantic2ts 重新生成 TS。

### 9.3 棄用策略
`TBD — <be-lead TBD>`（目前無正式棄用，OLD `/triz/solve` 已標記 deprecated；Phase A 掃描已於 v8 退役移除）。

---

## 10. 附錄 (Appendix)

### 10.1 請求/回應範例
見 [`E7x--e2e-manual-scripts/`](E7x--e2e-manual-scripts/) 中對應 cURL；E3 Appendix A 的容器圖呈現完整資料流。

### 10.2 客戶端庫
- 前端：`src/integrations/`（fetch wrapper + camelCase adapter）
- 後端間：`TBD — <be-lead TBD>`

---

**文件審核記錄 (Review History):**

| 日期 | 審核人 | 版本 | 變更摘要 |
|---|---|---|---|
| 2026-04-15 | Backend Team | v1.0 | 初版；對齊 VibeCoding 06 模板 |
| 2026-04-24 | Backend Team | v1.2 | (Auto-TRIZ v2) 新增 §7.13 Analyst v2、§7.14 TRIZ v2、§7.15 Evidence Registry 共 10 端點；§8.3 新增 5 個 Schema；§9.1 更新生命週期 |
