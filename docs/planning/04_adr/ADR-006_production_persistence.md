# ADR-006：Production Persistence（in-memory → Supabase）

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, ARCH, BE, SRE
**決策日期 (Date)**：2026-04-28
**諮詢 (Consulted)**：PM
**知會 (Informed)**：All

---

## Context & Problem Statement

現況（M1-M4）：
- `app/api/sessions.py::_SESSIONS` 是 **in-memory dict + thread lock**
- 過程：使用者登入 → 建 session → 跑 /run → SessionRecord 留在記憶體
- 重啟 backend = session 全失
- 多 process 部署無法共享（無法 horizontal scale）
- TRIZ skill state 走另一條路徑（`.claude/context/triz/.{triz,tr}-state.json` 寫入 filesystem）

這對 PoC 階段足夠（單機 + 短週期測試），但 production 需要：
1. 重啟後 session 不丟
2. 多 worker / 多 pod 共享 session
3. 跨日 session 復原（某些 TRIZ 流程跨多日）
4. 審計（誰在何時跑了哪個 command）

**Supabase 已在現況**：JWT auth-only。資料庫實例已存在，只是還沒寫業務表。

---

## Considered Options

| Option | Pros | Cons |
|:-------|:-----|:-----|
| 維持 in-memory + 接受重啟丟資料 | 零改動 | 不能 production；不能 multi-pod |
| **Supabase（PostgreSQL）持久化 SessionRecord/RunSummary** | 已有實例、與 auth 同源、PG-native RLS | 需建 schema + 寫 repository |
| Redis（純 cache）| 重啟 ms 級恢復、橫向擴展容易 | 仍是揮發；不適合審計；需多一個元件 |
| 檔案系統 JSON（同 `.claude/context/`） | 與 TRIZ state 一致 | 多 pod 需共享 volume；併發鎖煩 |

---

## Decision Outcome

**選擇**：Supabase PostgreSQL 為 SessionRecord / RunSummary SSOT；Redis 作為 hot cache（選用，視效能評估）。

**TRIZ skill state 不動**：`.claude/context/triz/.{triz,tr}-state.json` 仍由 Skill 透過 Read/Write tool 操作；Supabase 只持久化 HTTP session 與 RunSummary 元資料，**不複製 TRIZ 內部 state**（內容位置邊界政策）。

---

## 觸發條件（什麼時候開始遷移）

任一達成即啟動：

1. **Beta 用戶 ≥ 5 人**：跨用戶 session 衝突開始出現
2. **平均 session 時長 > 1 hr**：意外重啟造成的損失明顯
3. **需要 horizontal scaling**：單 pod CPU 持續 > 70%、需要 ≥ 2 worker
4. **需要審計**：合規要求記錄「何人何時跑何 command」
5. **跨日 session 需求**：用戶反映「昨天的 session 找不回來」

**不觸發 → 維持 in-memory**：避免過早優化。

---

## Schema 草案

```sql
-- 對應 SessionRecord
CREATE TABLE sessions (
    session_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES auth.users(id),
    title        text NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

-- 對應 RunSummary
CREATE TABLE session_runs (
    run_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    uuid NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    command       text NOT NULL,
    iterations    int,
    tool_calls    text[],
    stop_reason   text,
    final_text    text,
    error_message text
);

-- RLS
ALTER TABLE sessions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_runs  ENABLE ROW LEVEL SECURITY;

CREATE POLICY sessions_owner_only ON sessions
    USING (user_id = auth.uid());

CREATE POLICY runs_via_session ON session_runs
    USING (session_id IN (SELECT session_id FROM sessions WHERE user_id = auth.uid()));
```

詳細多租戶（專案級）見 [`ADR-007`](./ADR-007_multi_tenancy.md)。

---

## Migration Plan

```
Phase A：Schema + Repo 上線（feature-flagged off）
  - 建立 Supabase migration 檔
  - 寫 SessionRepository / RunRepository（無依賴 ORM，直 supabase-py）
  - 加 env flag: PERSISTENCE_MODE=memory|supabase（預設 memory）

Phase B：雙寫測試（dev/staging）
  - PERSISTENCE_MODE=supabase 在 staging 開啟
  - 對比 in-memory 與 Supabase 的 SessionRecord 一致性
  - 跑 live tests 確認 SSE 不退化

Phase C：生產切換
  - PERSISTENCE_MODE=supabase
  - 移除 in-memory dict
  - 監控 24-48 hr

Phase D：(可選) 加 Redis cache
  - 熱 sessions cache
  - 視性能決定
```

---

## Consequences

### Positive
- 重啟不丟 session
- 多 pod 共享
- 審計可達
- 與 auth 同源（user_id = auth.uid() RLS 自動）

### Risks / Mitigation
- Supabase 失效 → DB outage 影響全功能；緩解：監控 + 自動重試
- Schema migration 風險 → 用 Supabase migration 工具 + 雙寫期間驗證
- TRIZ skill state 與 Supabase 不一致 → **強制邊界**：TRIZ state 永遠在 filesystem，Supabase 只記元資料

### Re-evaluation Triggers
- 多租戶需求（[`ADR-007`](./ADR-007_multi_tenancy.md)）
- 跨地理 multi-region → CockroachDB 或 sharding
- 寫入 QPS > 100 → 評估 PG → Cassandra / DynamoDB

---

## References

- 現況：`backend/app/api/sessions.py::_SESSIONS`
- Supabase auth：`backend/app/middleware/auth.py`
- 內容位置邊界：`.claude/CLAUDE.md`
- 結構 SSOT：[`08_project_structure.md`](../08_project_structure.md) §3 「狀態 JSON 只能由 Skill 修改」
- 連帶決策：[`ADR-007`](./ADR-007_multi_tenancy.md) Multi-tenancy
