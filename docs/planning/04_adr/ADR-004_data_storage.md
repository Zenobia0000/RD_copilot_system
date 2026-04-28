# ADR-004：資料儲存策略

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, ARCH, Data
**決策日期 (Date)**：2026-04-28

---

## Context & Problem Statement

選擇資料儲存方案，需支援關聯資料、向量檢索、快取、檔案。

---

## Decision Outcome

**選擇**：

| 用途 | 技術 | 理由 |
|:-----|:-----|:-----|
| 主資料庫（關聯） | PostgreSQL 15+ | 成熟、JSONB 支援好、企業內網易部署 |
| 向量檢索 | pgvector（postgres extension） | 與主庫同實例、降低運維複雜度 |
| 快取 / Session | Redis | 業界標準 |
| 檔案儲存（雲） | S3 | 標準介面 |
| 檔案儲存（本地內網） | MinIO | S3 API 相容、可內網部署 |
| 任務佇列 | Redis + Celery | 與快取共用 Redis |

---

## Consequences

### Positive
- 單一 PostgreSQL 實例支援關聯 + 向量，運維簡單
- MinIO 提供 S3 介面，雲/地端切換無痛

### Risks
- pgvector 大規模（> 10M 向量）效能可能不如 Pinecone → v3 評估獨立向量資料庫
- PostgreSQL HA 需 patroni / cloud RDS

---

## Re-evaluation Triggers

- 向量資料 > 10M → 拆出 Pinecone / Weaviate
- 跨地理 multi-region → CockroachDB 或 sharding
