# ADR-004: 測試與 DevOps 基礎設施

- **Status**: Superseded (2026-04-27)
- **Date**: 2026-03-13 (proposed) → 2026-04-27 (superseded)
- **Deciders**: Development Team
- **Superseded By**: 待撰寫新 ADR（Harness 架構下的測試策略）

> **Superseded Notice (2026-04-27)**:
>
> 本 ADR 已封存。封存原因：
>
> 1. **從未實作** — Status 停留在 Proposed，`backend/tests/` 仍為空。
> 2. **測試目標已過時** — 本文假設 16 個 AI endpoint 的舊 router 結構（test_brief, test_socratic, test_cld...），ADR-006 Harness 重構後 backend 結構已根本改變（agents 改為 HarnessAgent、orchestrator 管線、solver registry）。
> 3. **前端測試目標已過時** — 本文假設 `useContradictionScan`、`useConvergenceLoop` 等 hooks，ADR-008 新增 8 個 hooks（useEntryGrading, useFunctionAnalysis, useOzOtAnalysis...），測試範圍需重新規劃。
>
> 下一步：需撰寫新的測試策略 ADR，覆蓋 Harness agent 單元測試、orchestrator pipeline 測試、TRIZ KB 確定性測試、以及 Auto-TRIZ v2 E2E 場景。

## Context

SOW v1.0 規劃的品質保證與部署基礎設施：

| 項目 | SOW 規格 | 現況 |
|------|----------|------|
| 後端測試 | pytest，service layer ≥80% 覆蓋率 | `backend/tests/` 目錄為空 |
| 前端測試 | Vitest + Testing Library | `vitest.config.ts` 存在但無測試檔案 |
| E2E 測試 | Playwright，完整場景覆蓋 | 無 Playwright 配置 |
| 部署 | Docker + docker-compose 一鍵啟動 | 無 Dockerfile / docker-compose.yml |
| CI/CD | 未明確規範但隱含需要 | 無 pipeline 配置 |
| API 文件 | OpenAPI（FastAPI 自動產生） | `/docs` 端點正常運作 ✅ |

### 架構對測試策略的影響

因 ADR-001 採用 BaaS-First 架構，測試策略需要調整：

- **後端僅 16 個 AI 端點**（非 35+ CRUD），測試範圍大幅縮小。
- **CRUD 邏輯在前端 + Supabase RLS**，需要不同的測試方式。
- **AI 端點的輸出不確定性**，需要 mock LLM 回應進行確定性測試。

## Decision

採用 **務實測試策略**，聚焦高價值測試，不追求 SOW 的 80% 覆蓋率。

### 後端測試（pytest）

**目標：16 個 AI 端點全覆蓋**

```
backend/tests/
├── conftest.py              # LLM mock fixtures + test client
├── routers/
│   ├── test_brief.py        # 5 endpoints
│   ├── test_socratic.py     # 1 endpoint
│   ├── test_cld.py          # 1 endpoint
│   ├── test_anti_anchor.py  # 1 endpoint
│   ├── test_triz.py         # 1 endpoint
│   ├── # test_scamper.py    # v9: removed (SCAMPER deprecated)
│   ├── test_risk.py         # 1 endpoint
│   ├── test_action.py       # 1 endpoint
│   ├── test_convergence.py  # 1 endpoint
│   └── test_must.py         # 1 endpoint
└── tools/
    └── test_triz_kb.py      # TRIZ matrix lookup 確定性測試
```

每個測試檔覆蓋：
1. Happy path（mock LLM 回傳合法 JSON）
2. LLM 回傳格式錯誤（驗證 error handling）
3. Request validation（缺少必填欄位）

### 前端測試（Vitest）

**目標：核心業務邏輯 hooks 覆蓋**

```
src/__tests__/hooks/
├── useContradictionScan.test.ts
├── useConvergenceLoop.test.ts
└── useSupabaseQuery.test.ts
```

### E2E 測試（Playwright）

**目標：1 個 smoke test 涵蓋 happy path**

- 建立專案 → 填寫 Brief → 觸發 AI 建議 → 進入 Explore → 建立 Contradiction → 進入 Create

### Docker 部署

```
docker-compose.yml
├── backend     (FastAPI + uvicorn)
├── frontend    (Vite build + nginx)
└── .env        (外部掛載)
```

Supabase 作為外部 SaaS 服務，不包含在 docker-compose 中。

### 不納入 v1.0

- 80% 覆蓋率目標（BaaS 架構下不適用傳統 service-layer 覆蓋率計算）
- 全頁面 Playwright 測試（19 頁面 × 多場景，ROI 不足）
- CI/CD pipeline（手動部署可接受，v1.1 再建立）

## Consequences

### 正面

- AI 端點測試可捕捉 prompt 回歸和 JSON 解析失敗，這是最高風險區域。
- TRIZ KB 確定性測試確保 39×39 矩陣查詢正確性。
- Docker 簡化新人 onboarding 和部署流程。
- 測試範圍聚焦，開發成本可控（預估 3-4 人天）。

### 負面

- 未達 SOW 80% 覆蓋率規格。
- Supabase CRUD 路徑無整合測試（依賴 RLS 策略正確性）。
- E2E 覆蓋率低，UI 回歸需人工驗證。

## Action Items

- [ ] 建立 `backend/tests/conftest.py` — LLM mock fixtures
- [ ] 建立 16 個 router 測試檔案
- [ ] 建立 `backend/tests/tools/test_triz_kb.py` — TRIZ KB 確定性測試
- [ ] 建立 `Dockerfile`（backend）和 `docker-compose.yml`
- [ ] 補充 `.env.example` 文件，記錄所有必要環境變數

## Related

- `backend/app/routers/`: 16 個 AI 端點
- `backend/app/tools/triz_kb.py`: TRIZ 知識庫工具
- `src/hooks/useContradictionScan.ts`: 矛盾掃描 hook
- `src/hooks/useConvergenceLoop.ts`: 收斂迴圈 hook
