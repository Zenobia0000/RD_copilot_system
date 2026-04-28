# ADR-007：Multi-tenancy（專案級隔離）

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, ARCH, BE, SEC
**決策日期 (Date)**：2026-04-28
**諮詢 (Consulted)**：PM, RD-SME
**知會 (Informed)**：All

---

## Context & Problem Statement

現況（M1-M4）：
- **單租戶 PoC**：所有 user 共用同一個 `.claude/` 樹（skills、commands、agents、context）
- TRIZ session state 寫到 `.claude/context/triz/.{triz,tr}-state.json` — 全域共享
- in-memory `_SESSIONS` 用 `user_sub` key 切分，但 TRIZ state 仍是「全域單一 session」
- 多 user 同時跑 `/triz` 會互相覆寫 `.triz-state.json`

未來（Beta 起）：
- 多 RD 用戶同時跑各自 TRIZ session
- 同一公司多專案隔離（A 專案的 contradictions 不該漏到 B 專案）
- 跨公司部署（v3+）的完全 tenant 隔離

需要決定：
1. **Tenancy 粒度**：user-level / project-level / org-level？
2. **資料隔離方式**：邏輯（RLS）/ schema 隔離 / DB 隔離？
3. **TRIZ state 怎麼分**：filesystem 怎麼切 namespace？
4. **何時做**：MVP 不做 → Beta 做？

---

## Considered Options

| 維度 | Option A：user-level | **Option B：project-level（推薦）** | Option C：org-level |
|:-----|:--------------------|:------------------------------------|:--------------------|
| 隔離單位 | user | **project（含 collaborators）** | tenant org |
| 適用 | 個人工具 | **企業內團隊協作（本系統定位）** | SaaS 多客戶 |
| 資料隔離 | DB row 帶 user_id | **DB row 帶 project_id + RLS** | 每 tenant 一個 schema/DB |
| TRIZ state 命名 | `.../user_<id>/.triz-state.json` | `.../project_<id>/.triz-state.json` | `.../tenant_<id>/project_<id>/.triz-state.json` |
| 複雜度 | 低 | 中 | 高 |
| 何時 | — | **Beta** | v3+ SaaS |

---

## Decision Outcome

**選擇**：**Option B — project-level multi-tenancy**

**理由**：
- PRD §3.1 多用戶情境是「**RD + RD 主管 + PM + 製造工程**共用一個專案」 — 隔離單位是 project，不是 user
- Supabase RLS 原生支援 row-level 政策，與 [ADR-006](./ADR-006_production_persistence.md) 同源
- TRIZ state 與 project 1:1 對應，分目錄即可
- 預留 v3+ org-level（加一層 tenant_id 即可，不破壞 project_id）

---

## 觸發條件

任一達成即啟動實作：

1. **跨 user 共用專案**出現實際請求（≥ 1 個 Beta 客戶有此需求）
2. **TRIZ state 互相覆寫**事件發生
3. **進入 Beta（≥ 5 客戶）**

**不觸發 → 維持單租戶 PoC**：MVP 階段獨立用戶測試已足。

---

## 資料隔離設計

### A. Supabase RLS（行級）

延伸 [ADR-006](./ADR-006_production_persistence.md) schema：

```sql
-- 加 project 主表
CREATE TABLE projects (
    project_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name         text NOT NULL,
    owner_id     uuid NOT NULL REFERENCES auth.users(id),
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- 專案協作者
CREATE TABLE project_members (
    project_id   uuid NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id      uuid NOT NULL REFERENCES auth.users(id),
    role         text NOT NULL CHECK (role IN ('owner','editor','viewer')),
    PRIMARY KEY (project_id, user_id)
);

-- 為 sessions 加 project_id
ALTER TABLE sessions ADD COLUMN project_id uuid REFERENCES projects(project_id);

-- RLS：使用者僅能看到自己 owner 或 member 的 project
ALTER TABLE projects        ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_member_visible ON projects
    USING (
        owner_id = auth.uid()
        OR project_id IN (SELECT project_id FROM project_members WHERE user_id = auth.uid())
    );

CREATE POLICY sessions_project_scoped ON sessions
    USING (
        project_id IN (
            SELECT project_id FROM projects WHERE owner_id = auth.uid()
            UNION
            SELECT project_id FROM project_members WHERE user_id = auth.uid()
        )
    );
```

### B. TRIZ State 命名空間

將 `.claude/context/triz/` 切成子目錄：

```
.claude/context/triz/
├── shared/
│   └── session-template.md
├── projects/
│   ├── <project_id_1>/
│   │   ├── .triz-state.json
│   │   ├── .tr-state.json
│   │   └── session-*.md
│   └── <project_id_2>/
│       └── ...
```

**規則變動**：
- Skill 必須先解析「當前 project_id」再決定 state 路徑
- HTTP route 帶 `project_id`：`POST /api/v1/projects/{project_id}/sessions/{session_id}/run`
- CLI 加 `--project <id>` 旗標
- ToolRegistry 的 Read/Write tool 路徑要被 project_id 限縮（不可跨 project 寫入）

### C. docs/engineering/ 命名空間

工程交付物也需 project 切分：

```
docs/engineering/
├── <project_slug>/
│   ├── README.md
│   ├── critical_path.md
│   ├── work_instructions/WI-*.md
│   ├── interface_control/ICD-*.md
│   ├── material_cards/MC-*.md
│   └── gate_reviews/TR*-review-*.md
```

triz-wi skill 寫入時以 project_slug 為頂層。

---

## Migration Plan

```
Phase A：Schema + RLS（與 ADR-006 同步上線）
  - projects + project_members 表
  - sessions 加 project_id
  - RLS policies

Phase B：Skill 改寫
  - 所有 triz-* skill 加上「先取 project_id 再寫 state」邏輯
  - .claude/context/triz/projects/<id>/ 目錄結構建立

Phase C：HTTP / CLI 介面變動
  - 加 project_id path param / --project flag
  - 既有 PoC sessions 遷移到「default project」

Phase D：docs/engineering/ 重組
  - 既有檔遷移到 default project_slug
  - triz-wi 預設寫入 <current_project>/

Phase E：UI 加 project picker（前端配合）
```

---

## Security Considerations

- **路徑遊走攻擊**：Read/Write tool 必須拒絕 `..` 路徑、必須限定在 `<project_root>` 內
- **RLS 旁路**：所有 query 走 supabase-py（自動帶 JWT），絕不用 service role key 跳過 RLS（除非 admin endpoint）
- **subagent 隔離**：CustomAgent 派生時需傳遞 project_id；不可跨 project 操作

---

## Consequences

### Positive
- 多 user / 多專案並行不互相干擾
- 審計可達 project 級
- 對齊企業常見隔離習慣（按 project / cost center）

### Risks / Mitigation
- Skill 改寫負擔大（11 個 skill 都要動） → 抽 helper：`get_project_context()` 包裝
- 既有 PoC 資料遷移 → migration script + dry-run 驗證
- 跨 project 引用（A 專案參考 B 專案知識）→ 透過 RLS-aware query 而非檔案路徑

### Re-evaluation Triggers
- v3+ SaaS：加 tenant_id 上層（org-level）
- Project 數 > 10K：分區策略（hash / 時間）
- 跨地理：multi-region 部署需評估資料駐留法規

---

## References

- 現況：`backend/app/api/sessions.py`（_SESSIONS dict 用 user_sub key）、`.claude/context/triz/`（全域共享）
- PRD：[`02_prd.md §3.1`](../02_prd.md) 多用戶情境
- 連帶決策：[`ADR-006`](./ADR-006_production_persistence.md) Production Persistence
- 內容位置邊界：`.claude/CLAUDE.md`
- 結構 SSOT：[`08_project_structure.md`](../08_project_structure.md)
