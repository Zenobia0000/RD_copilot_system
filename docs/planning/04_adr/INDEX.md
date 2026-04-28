# ADR Index — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**模板來源**：`VibeCoding_Workflow_Templates/04_architecture_decision_record_template.md`

---

## ADR 清單

| ID | 標題 | 狀態 | 決策日期 |
|:---|:-----|:-----|:---------|
| [ADR-001](./ADR-001_frontend_stack.md) | 前端技術棧（React + Tailwind + Zustand + React Query） | Proposed | 2026-04-28 |
| [ADR-002](./ADR-002_triz_skill_architecture.md) | TRIZ 推理層採 Skill-based 架構 | Accepted | 2026-04-21 |
| [ADR-003](./ADR-003_backend_stack.md) | 後端技術棧（Python + FastAPI + SQLAlchemy） | Proposed | 2026-04-28 |
| [ADR-004](./ADR-004_data_storage.md) | 資料儲存（PostgreSQL + pgvector + Redis + S3） | Proposed | 2026-04-28 |
| [ADR-005](./ADR-005_llm_abstraction.md) | LLM 抽象層（多 provider 支援） | Proposed | 2026-04-28 |
| [ADR-006](./ADR-006_production_persistence.md) | Production Persistence（in-memory → Supabase） | Proposed | 2026-04-28 |
| [ADR-007](./ADR-007_multi_tenancy.md) | Multi-tenancy（專案級隔離） | Proposed | 2026-04-28 |

---

## 新增 ADR 流程

1. 複製 `VibeCoding_Workflow_Templates/04_architecture_decision_record_template.md`
2. 編號：`ADR-NNN_kebab_case_title.md`
3. 填 metadata（Status, Deciders, Date）
4. 至少完成 Context / Options / Decision / Consequences 四節
5. 加入本 INDEX

## ADR Status 流轉

```
Proposed → In Review → Accepted / Rejected
                    ↘ Deprecated → Superseded by ADR-NNN
```
