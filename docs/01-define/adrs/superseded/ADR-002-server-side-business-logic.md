# ADR-002: 缺失的伺服器端業務邏輯 — 狀態機、Gate、Workflow

- **Status**: Superseded (2026-04-27)
- **Date**: 2026-03-13 (proposed) → 2026-04-21 (status updated) → 2026-04-27 (superseded)
- **Deciders**: Development Team
- **Superseded By**: ADR-006 (Harness 架構)、ADR-008 (Auto-TRIZ v2 閉環流程)

> **Superseded Notice (2026-04-27)**:
>
> 本 ADR 已封存。封存原因：
>
> 1. **8-Gate 規格使用舊步驟編號** — 本文定義的 Gate 1.1 (Step 1.1→1.2)、Gate 1.2 (Step 1.2→1.3)、Phase Gate 1-3 等，均基於舊的 Step 1.x→2.x→3.x 流程。現行系統採 Auto-TRIZ v2 的 Step 0→1→2→3→4→5 + Decision Hub + Gate P，步驟編號與 Gate 條件已完全不對應。
> 2. **原決策「Supabase DB trigger 實作」從未執行** — 實際以 FastAPI `gate_registry.py` (Python decorator) 實作，與本 ADR 的 Decision 段落（PL/pgSQL + RPC）矛盾。
> 3. **Gate 條件已由 ADR-008 重新定義** — Evidence Coverage ≥ 40%、CCI 複雜度檢查等新條件取代了原 8-Gate 中的多數退出條件。
>
> 歷史參考價值：本文記錄了 v1.0 初期的 7 項業務邏輯缺口識別，仍可作為架構演進的考古資料。

---

> **Implementation Note (2026-04-21)** *(歷史記錄)*:
> Items implemented differently from proposal — via FastAPI endpoints instead of Supabase DB Functions:
> - ✅ #1 State machine: `backend/app/core/gate_registry.py` (declarative, not Supabase trigger)
> - ✅ #2 Gate checks: `backend/app/routers/gates.py` + `core/gate_checks.py`
> - ✅ #3 Export: `backend/app/routers/exports.py`
> - ✅ #4 Knowledge Writeback: `backend/app/routers/knowledge_wb.py`
> - ✅ #5 unknown_factors: `backend/app/routers/unknown_factors.py`
> - ⏳ #6 Assumption disprove with impact analysis: Not yet implemented
> - ⏳ #7 WANT criteria auto-seed: Not yet implemented

## Context

因 ADR-001 採用 BaaS-First 架構，SOW v1.0 規劃的以下伺服器端業務邏輯未被實作：

### 缺口清單

| # | SOW 規格 | 現況 | 風險等級 |
|---|----------|------|----------|
| 1 | 伺服器端專案狀態機：`DRAFT → PHASE_1 → PHASE_2 → PHASE_3 → COMPLETED`，禁止非法轉換 | `projects.phase` 欄位可被前端任意設值，無伺服器驗證 | **高** — 資料完整性 |
| 2 | Gate 檢查 API：`GET /gates/:gate_id/check`，8 個 Gate 各有特定的 artifact 數量/狀態門檻 | 前端部分實作 Gate 邏輯，但不強制，可被繞過 | **高** — 品質關卡失效 |
| 3 | Export 端點：`POST /export`，輸出 Markdown + JSON 完整報告 | 未實作 | 中 — 非核心流程 |
| 4 | Knowledge Writeback：`POST /knowledge/writeback`，6 種 asset 自動沉澱 | 未實作，`knowledge_entries` 表存在但無自動寫入管線 | 中 — 知識累積延遲 |
| 5 | `unknown_factors` 資料持久化 | 使用 `localStorage`，Schema 中無對應表 | **高** — 資料遺失風險 |
| 6 | Assumption Disprove：`POST /assumptions/:aid/disprove`，含串聯影響分析 | 未實作 | 低 — 前端可手動操作 |
| 7 | WANT Criteria Seed：`POST /want/criteria/seed`，自動生成 W1-W6 標準 | 未實作，前端手動建立 | 低 — UX 便利性 |

### 8-Gate 規格（SOW 定義）

| Gate ID | 位置 | 通過條件 |
|---------|------|----------|
| Gate 1.1 | Step 1.1→1.2 | Mission 已定義 + ≥3 KPIs 各有量測方法 |
| Gate 1.2 | Step 1.2→1.3 | ≥10 assumptions + ≥3 high-risk + ≥3 contradictions |
| Phase Gate 1 | Phase 1→2 | ≥1 CLD + ≥3 breakpoints + contradictions 已形式化 |
| Gate 2.1 | Step 2.1→2.2 | ≥3 高風險假設有對應實驗 |
| Gate 2.2 | Step 2.2→2.3 | ≥3 alternatives + MUST 全數通過 |
| Phase Gate 2 | Phase 2→3 | ≥1 Pre-CAD overall_pass |
| Gate 3.2 | Step 3.2→3.3 | DecisionRecord 已簽核 + WANT 有佐證 |
| Phase Gate 3 | Phase 3→Done | 所有核心 artifacts 已發佈 |

## Decision

採用 **Supabase Database Function + RLS 觸發器** 實作伺服器端業務邏輯，與 ADR-001 的 BaaS-First 架構一致。

### 優先級分配

**P0（v1.0 必要）：**

1. **狀態機觸發器**：在 `projects` 表建立 `BEFORE UPDATE` 觸發器，驗證 `phase` 欄位的合法轉換。非法轉換拋出 PostgreSQL 例外，前端收到 400 錯誤。
   - 實作位置：`supabase/migrations/003_state_machine.sql`

2. **Gate 檢查 RPC**：建立 `check_gate(project_id UUID, gate_id TEXT) RETURNS JSONB` Database Function，回傳 `{ passed: boolean, failed_reasons: string[] }`。前端在轉換 Phase 前呼叫此 RPC。
   - 實作位置：`supabase/migrations/004_gate_checks.sql`

**P1（v1.0 應有）：**

3. **unknown_factors 表建立**：新增 `unknown_factors` Supabase 表 + RLS 策略，前端遷移 localStorage 至 Supabase。
   - 實作位置：`supabase/migrations/005_unknown_factors.sql`
   - 前端修改：`src/hooks/api/useTrack.ts`

4. **WANT Criteria Seed**：在 FastAPI 後端新增 `POST /want/criteria/seed` 端點，由 AI 根據 mission + constraints 生成 W1-W6 建議。
   - 實作位置：`backend/app/routers/want.py`

**P2（v1.1 延後）：**

5. Export 端點（需整合所有 Phase artifacts）
6. Knowledge Writeback 管線（需定義 6 種 asset 的沉澱觸發時機）
7. Assumption Disprove 串聯影響分析

## Consequences

### 正面

- Database-level 強制確保即使前端有 bug 或直接 API 存取也無法產生非法狀態。
- Gate RPC 可同時被前端和後端呼叫，提供統一的品質關卡邏輯。
- unknown_factors 遷移至 Supabase 後資料不會因清除瀏覽器而遺失。

### 負面

- PostgreSQL 預存程序較難進行單元測試（需要 pgTAP 或整合測試）。
- 複雜業務邏輯（如 Gate 檢查的 artifact 計數）在 PL/pgSQL 中撰寫不如 Python 直觀。
- 業務邏輯分布於三處：Supabase DB Functions + FastAPI 後端 + 前端，需清楚文件記錄各處職責。

## Action Items

- [ ] 建立 `supabase/migrations/003_state_machine.sql` — Phase 轉換驗證觸發器
- [ ] 建立 `supabase/migrations/004_gate_checks.sql` — 8-Gate RPC 函式
- [ ] 建立 `supabase/migrations/005_unknown_factors.sql` — unknown_factors 表 + RLS
- [ ] 修改 `src/hooks/api/useTrack.ts` — 將 localStorage 替換為 Supabase 呼叫
- [ ] 新增 `backend/app/routers/want.py` — WANT Criteria Seed AI 端點

## Related

- ADR-001: 根因 — BaaS-First 架構導致伺服器端邏輯缺失
- `supabase/migrations/001_full_schema.sql`: 現有 Schema
- SOW v1.0 §4.4: 8-Gate 規格定義
