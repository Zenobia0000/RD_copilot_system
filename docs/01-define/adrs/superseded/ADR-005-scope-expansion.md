# ADR-005: 超出 SOW 範圍的已實作功能

- **Status**: Superseded (2026-04-27)
- **Date**: 2026-03-13 (accepted) → 2026-04-27 (superseded)
- **Deciders**: Development Team
- **Superseded By**: ADR-008 (Auto-TRIZ v2 閉環流程)

> **Superseded Notice (2026-04-27)**:
>
> 本 ADR 已封存。封存原因：
>
> 1. **Evidence Retrieval Service 被 ADR-008 Evidence Registry 取代升級** — 原設計為單純的 Tavily 搜尋 + 引用附加，ADR-008 升級為 cross-cutting claim registration + auto-verify + Evidence Coverage ≥ 40% Gate 退出條件。`backend/app/services/evidence_retrieval.py` 功能已併入 `evidence_registry.py`。
> 2. **Multi-Solution Adoption (M1-M5) 併入 Decision Hub + SIM matrix** — ADR-008 的 SIM matrix（+1/0/-1 interaction scoring）取代了原 `concept_routes` + `compatibility_pairs` 的靜態相容性判斷，並新增 -1 interaction 自動回流為新 TC 的機制。
> 3. **Configurable MUST 仍有效** — 此項未被取代，但作為單一功能不足以支撐獨立 ADR，已納入現行系統基線。
>
> 歷史參考價值：本文記錄了三項超範圍功能的初始動機與設計取捨。

## Context

在開發過程中，團隊實作了三項 SOW v1.0 未規劃的功能。這些功能為有價值的增強，需正式記錄並回溯更新 SOW。

### 1. Evidence Retrieval Service（證據檢索服務）

**SOW 規劃**：RAG 搜尋基於內部知識庫（MVP 使用 LLM 內部知識，v1.1 接入向量資料庫）。

**實際實作**：

- `backend/app/services/evidence_retrieval.py` — 非同步證據檢索服務
- `backend/app/services/web_search.py` — Tavily API 網路搜尋整合
- 提供 `EvidenceReference` 結構（ref_id, ref_type, title, source, url, snippet）

整合範圍：
| 端點 | 證據類型 |
|------|----------|
| `/brief/suggest-constraints` | 安全法規、工程標準（ISO, EN, IEC） |
| `/brief/suggest-kpis` | 產業基準、測試方法 |
| `/brief/rewrite` | 規格書撰寫標準 |
| `/brief/generate-5w1h` | 設計方法論 |

**價值**：AI 建議引用實際的 ISO/EN 標準（如 EN 15194:2017），比 SOW 規劃的純 LLM 內部知識品質更高。

### 2. 多解併行採納策略（Multi-Solution Adoption）

**SOW 規劃**：Alternatives 模型為單一最佳解選擇（MUST → WANT → 決策）。

**實際實作**：

新增兩張表（非 SOW 原始 27 張表之列）：
- `concept_routes` — 概念路線（single/composite），含組成結構、反模式警告
- `compatibility_pairs` — 方案相容性矩陣（compatible / exclusive / needs_verification）

採納類型（M1-M5）：
| 類型 | 描述 |
|------|------|
| M1 | 直接合併（無衝突） |
| M2 | 參數分離（不同工況） |
| M3 | 空間分離（不同模組） |
| M4 | 時間分離（不同階段） |
| M5 | 條件分離（不同場景） |

前端實作：
- `src/components/solution/ConvergenceGraph.tsx` — 收斂圖視覺化
- `src/hooks/api/useConceptRoutes.ts` — CRUD hooks

**價值**：支援 SOW §1.3 的核心價值主張「探索 ≥3 條路線」，提供比單一最佳解更豐富的決策框架。

### 3. 可配置 MUST 標準（Configurable MUST Criteria）

**SOW 規劃**：固定 M1-M6 標準（6 條硬約束規則）。

**實際實作**：

- `MustCriterionConfig` API 介面允許前端傳入自訂標準：
  ```typescript
  interface MustCriterionConfig {
    id: string;
    label: string;
    source: string;
    threshold?: string;
  }
  ```
- `projects.must_criteria_config` JSONB 欄位儲存專案級標準配置
- 後端 `POST /must/evaluate` 接受任意數量的標準進行評估

**價值**：使平台可用於電動自行車以外的設計領域，增加通用性。

## Decision

**接受全部三項範圍擴充**，作為 v1.0 的正式功能。

理由：
1. Evidence Retrieval 在 MVP 階段比 SOW 的 RAG 方案更實用（無需建置向量資料庫即可提供高品質證據）。
2. 多解採納策略深化了產品核心價值，是 SOW 設計理念的自然延伸。
3. 可配置 MUST 是向下相容的增強，不影響固定 M1-M6 的使用情境。

## Consequences

### 正面

- AI 建議品質顯著提升（引用實際 ISO/EN 標準而非純推論）。
- 多解框架支援更複雜的設計探索場景。
- 平台通用性提升，降低未來擴展至其他產品領域的成本。

### 負面

- Tavily API 新增第三方依賴與成本（約 $0.01/search）。
- 多解表增加 Schema 複雜度（29 張表 vs SOW 原始 27 張）。
- 可配置 MUST 將標準定義責任轉移至前端，後端不驗證標準定義的合理性。

## Related

- `backend/app/services/evidence_retrieval.py`: 證據檢索服務
- `backend/app/services/web_search.py`: Tavily 網路搜尋
- `supabase/migrations/001_full_schema.sql`: concept_routes, compatibility_pairs 表定義
- `src/hooks/api/useConceptRoutes.ts`: 多解採納前端 hooks
- `backend/app/models/schemas.py`: MustCriterionConfig, MustEvaluationRequest
- SOW v1.0 §1.3: 核心設計理念（探索 ≥3 路線）
