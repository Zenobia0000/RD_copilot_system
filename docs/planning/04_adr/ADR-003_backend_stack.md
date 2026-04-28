# ADR-003：後端技術棧

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, ARCH, BE
**決策日期 (Date)**：2026-04-28

---

## Context & Problem Statement

選擇後端技術棧，需支援 RESTful API、LLM 整合、長任務、向量檢索。

---

## Considered Options

| Option | Pros | Cons |
|:-------|:-----|:-----|
| **Python + FastAPI + SQLAlchemy** | LLM 生態最強、async、自動 OpenAPI、TRIZ skill 已 Python | 性能略遜 Go |
| Node.js + NestJS | 與前端同語言、TS 一致 | LLM 生態較弱 |
| Go + Gin | 性能最佳 | LLM 生態最弱、團隊不熟 |

---

## Decision Outcome

**選擇**：Python 3.11+ + FastAPI + SQLAlchemy 2.x + Pydantic + Celery

**理由**：
1. TRIZ skill 已用 Python（LangChain、Anthropic SDK）
2. FastAPI async + 自動 OpenAPI 配 [`06_api_spec.md`](../06_api_spec.md) 完美
3. 團隊熟悉度高
4. 性能可用 uvloop / async / Celery 優化

---

## Consequences

### Positive
- 與 TRIZ skill 共享虛擬環境
- 自動 OpenAPI → 前端 type generation
- Pydantic 與 [`06_api_spec.md §5 錯誤處理`](../06_api_spec.md) 嚴格對齊

### Risks
- GIL 限制 → 用 async / 多 worker 緩解
- 大檔案處理性能 → 用 Celery 後台

---

## References

- [`05_architecture.md §4.2 後端`](../05_architecture.md)
- [`06_api_spec.md`](../06_api_spec.md)
