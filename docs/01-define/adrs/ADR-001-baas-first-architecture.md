# ADR-001: BaaS-First Architecture — Supabase 取代 SQLAlchemy ORM 後端

- **Status**: Accepted
- **Date**: 2026-03-13
- **Deciders**: Development Team

## Context

SOW v1.0 規劃的後端架構為：


| 層級        | SOW 規格                                           |
| --------- | ------------------------------------------------ |
| Framework | FastAPI (Python 3.11+)                           |
| ORM       | SQLAlchemy 2.0+                                  |
| Database  | SQLite (MVP) → PostgreSQL (v1.1)                 |
| Auth      | 自訂 JWT (`POST /auth/login`, `GET /user/profile`) |
| API 端點    | 35+ REST CRUD 端點，涵蓋所有 27 個實體                     |
| 資料存取      | 後端為唯一資料存取層，前端僅透過 REST API 操作資料                   |


實際開發選擇了 **Supabase BaaS** 架構：


| 層級        | 實際實作                                                      |
| --------- | --------------------------------------------------------- |
| Framework | FastAPI（僅 AI 編排層）                                         |
| ORM       | 無 — 前端用 Supabase JS Client，後端用 supabase-py (service-role) |
| Database  | Supabase PostgreSQL（Day-one 即為 PostgreSQL）                |
| Auth      | Supabase Auth（email/password, OAuth, 密碼重設）                |
| API 端點    | 16 個 AI 端點（10 routers），CRUD 由前端直接操作 Supabase              |
| 資料存取      | 雙路徑 — 前端 Supabase JS + 後端 supabase-py                     |


此偏差的根因是開發效率考量：前端可直接 CRUD 不需等待後端 API，且 Supabase 提供 RLS、Auth、Realtime 等開箱即用功能。

## Decision

**接受 BaaS-First 架構作為 v1.0 正式方案。** 這是有意的架構決策，非待修復的缺口。

具體影響：

1. **消除 ~35 個 CRUD 端點開發**：所有實體的 CREATE / READ / UPDATE / DELETE 由前端 `useSupabaseQuery` 和 `useSupabaseMutation` 通用 hooks 處理（`src/hooks/api/useSupabaseQuery.ts`）。
2. **消除 SQLite → PostgreSQL 遷移路徑**：Supabase 從第一天即提供 PostgreSQL。
3. **RLS 取代自訂權限中介層**：27 張表的 Row-Level Security 策略定義於 `supabase/migrations/002_rls_policies.sql`。
4. **Supabase Auth 取代自訂認證**：無需實作 `POST /auth/login`、JWT 簽發、密碼雜湊等。
5. **FastAPI 後端專注於 AI 編排**：16 個端點分布於 brief / socratic / cld / ~~anti_anchor~~ / triz / subsystems / risk / action / convergence / must 共 10 個 routers。*(v9: `scamper` router 移除，子系統端點遷移至 `subsystems`；Anti-Anchor 已退役，併入 TRIZ L1 跨域去錨定)*

## Consequences

### 正面

- 開發速度大幅提升：前端開發者可自主完成 CRUD 功能，不受後端開發進度限制。
- React Query 整合（`useSupabaseQuery`）提供快取、樂觀更新、錯誤處理。
- 27 張表的 Schema 與 SOW 完全對齊，資料模型未因架構變更而縮減。
- PostgreSQL Day-one 可用，包含 JSONB、Array、觸發器等進階功能。

### 負面

- **業務邏輯分散**：驗證邏輯分布於前端元件、Supabase RLS、FastAPI 後端三處，增加維護複雜度。
- **伺服器端業務規則缺失**：SOW 規劃的狀態機、Gate 檢查等伺服器端強制邏輯未實作（詳見 ADR-002）。
- **前端耦合 Supabase**：`@supabase/supabase-js` SDK 直接嵌入前端，更換 BaaS 供應商需大規模重構。
- **雙路徑存取風險**：同一張表可能被前端（anon key + RLS）和後端（service-role key，繞過 RLS）同時存取，需注意一致性。

## Related

- ADR-002: 因本決策衍生的伺服器端業務邏輯缺口
- `supabase/migrations/001_full_schema.sql`: 27 張表的完整 Schema
- `supabase/migrations/002_rls_policies.sql`: RLS 策略定義
- `src/hooks/api/useSupabaseQuery.ts`: 前端通用 CRUD hooks
- `backend/app/main.py`: 後端 16 AI 端點的 router 註冊

