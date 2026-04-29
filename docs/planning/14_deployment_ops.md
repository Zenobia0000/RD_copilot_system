# 部署與運維指南 — RD Design Copilot

---

**文件版本**：`v1.2`（新增 §3.1 Graph Lint in CI + §3.2 pre-commit hook）
**最後更新**：`2026-04-29`
**狀態**：`Skeleton + Graph CI 步驟已收錄`
**模板來源**：`templates/vibecoding/14_deployment_and_operations_guide.md`

> **注意**：當前 MVP 為單進程 Docker Compose（`uvicorn app.main:app`）+ in-memory session store。下文 Kubernetes / Celery / RDS 等描述為未來 production 目標架構（v3 roadmap），非現行部署方式。

---

## 1. 環境策略

| 環境 | 用途 | URL | 部署 |
|:-----|:-----|:----|:-----|
| Dev | 開發本機 | localhost:3000 / :8000 | Docker Compose |
| Staging | 整合測試 | staging.copilot.delta.com | K8s（小規模 1-2 replica）|
| Production | 正式 | copilot.delta.com | K8s HA（含 LB / CDN） |

---

## 2. 基礎設施組件

```
Internet → CloudFlare CDN → AWS ALB (or 內網 nginx)
                              ↓
                    Kubernetes Cluster
                      ├── Web Pods (3 replicas)
                      ├── API Pods (5 replicas, HPA)
                      ├── TRIZ Pods (2 replicas, GPU optional)
                      ├── Worker Pods (Celery, 3 replicas)
                      ↓
                    Managed Services
                      ├── PostgreSQL (RDS / patroni)
                      ├── Redis (ElastiCache / standalone)
                      └── S3 / MinIO
```

---

## 3. CI/CD Pipeline（GitHub Actions）

```yaml
# .github/workflows/ci.yml
name: CI/CD
on: [push, pull_request]

jobs:
  lint-typecheck:
    steps:
      - ESLint + ruff
      - tsc + mypy
      - graph-lint: python3 tools/build_graph.py --strict   # 見 §3.1

  test:
    needs: lint-typecheck
    steps:
      - Vitest unit tests
      - pytest unit + integration

  bdd:
    needs: test
    steps:
      - Run pytest-bdd features

  build:
    needs: bdd
    steps:
      - Vite build
      - Docker build + push

  e2e-staging:
    needs: build
    if: branch == main
    steps:
      - Deploy to staging
      - Playwright E2E

  deploy-prod:
    needs: e2e-staging
    if: tagged release
    environment: production  # GitHub manual approval
    steps:
      - Helm upgrade
      - Smoke test
```

---

### 3.1 Graph Lint in CI（`docs/engineering/` frontmatter 驗證）

`docs/engineering/` 下 WI/ICD/MC 的 YAML frontmatter 是 typed property graph 的 SSOT（見 [`05_architecture.md §5.5`](./05_architecture.md)、[ADR-008](./04_adr/ADR-008_knowledge_graph_as_ssot.md)）。任何 PR 修改這些檔必須通過 lint，否則 graph 視圖與 CI 一致性會崩。

**CI step 完整寫法**：

```yaml
- name: Engineering Knowledge Graph lint
  run: |
    pip install pyyaml
    python3 tools/build_graph.py --strict
  # exit code: 0 = lint clean / 1 = lint warnings (will fail CI)
```

**檢查項目**（詳見 [`09_file_dependencies.md §3.6`](./09_file_dependencies.md)）：
- 所有 WI/ICD/MC 必含 frontmatter（framework files 例外）
- ID 唯一、ID 前綴合法
- WI 必含 `traces_to`（除非 `role: cross-cutting`）
- 每個 Risk 必須被某 WI/MC `mitigates`
- Confidence=LOW 的 Claim 仍被引用 → 警告
- frontmatter YAML 解析無錯

**PR check 行為**：

| 情境 | CI 結果 | 處理 |
|:-----|:--------|:-----|
| 改 frontmatter 後 lint clean | ✅ pass | 自動 review |
| 新增 WI 但沒跑 `--inject` | ⚠️ pass（lint 通過但視圖過時）| 建議 PR 評論提醒跑 `--inject` |
| frontmatter YAML 語法錯 | ❌ fail | 修語法後重提 |
| 引用不存在的 ID（拼錯） | ⚠️ `[UNKNOWN-PREFIX]` warning | strict 模式擋下，需修正 |
| Risk 沒被任何 WI 關閉 | ⚠️ `[OPEN-RISK]` | 補 mitigates 或刪除孤兒 risk |

### 3.2 Pre-commit Hook（建議）

Local commit 前自動跑 graph lint，避免 push 後 CI fail：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: build-graph-strict
        name: Engineering Knowledge Graph lint
        entry: python3 tools/build_graph.py --strict
        language: system
        files: '^docs/engineering/.*\.md$'
        pass_filenames: false
```

啟用：

```bash
pip install pre-commit
pre-commit install
```

之後每次 `git commit` 都會自動跑 lint，失敗則阻擋 commit。

---

## 4. 部署清單

### Pre-Deploy
- [ ] 通過 [`13_security_checklist.md`](./13_security_checklist.md)
- [ ] DB migration dry-run
- [ ] Rollback plan 確認
- [ ] Stakeholders 通知

### During Deploy
- [ ] Health check 持續監控
- [ ] Error rate / latency 對比 baseline
- [ ] Canary 5% → 25% → 100%

### Post-Deploy
- [ ] Smoke test 全綠
- [ ] User-facing 驗證（建立一個專案到 Brief）
- [ ] On-call 巡檢 1 小時

---

## 5. 部署策略

| 場景 | 策略 |
|:-----|:-----|
| 小變更 | Rolling Update（K8s default） |
| 重大變更 | Blue-Green |
| 高風險 | Canary（5% → 25% → 50% → 100%） |
| Feature flag | LaunchDarkly / 自建 |

---

## 6. DB Migration

- 工具：Alembic（SQLAlchemy）
- 規則：永遠 backwards-compatible（先加欄位，舊 code 仍可讀；下次 release 才刪舊欄位）
- 大表 migration：分批（zero downtime）

---

## 7. Rollback 與 DR

### Rollback
- App：Helm rollback（< 2 min）
- DB：reverse migration（多數情況不執行，前向相容為主）

### DR（災難恢復）
- RTO：4 hr（NFR-11）
- RPO：1 hr（每小時 DB snapshot）
- 異地備份：每日 → 異地 7 天保留
- 演練：每季度

---

## 8. 監控與告警

| 指標 | 目標 | 告警閾值 |
|:-----|:-----|:---------|
| API p95 latency | < 500ms | > 1s 持續 5 min |
| Error rate | < 0.5% | > 2% 持續 5 min |
| TRIZ skill p95 | < 60s（KPI-7） | > 90s |
| LLM cost | 每日預算 | 超過 80% |
| DB connections | < 80% pool | > 90% |
| Pod 重啟頻率 | < 3/hr | > 10/hr |

工具：Prometheus + Grafana + AlertManager → PagerDuty / Slack

---

## 9. On-call 與 Incident Response

### Severity
| Level | 描述 | Response Time |
|:------|:-----|:--------------|
| SEV-1 | 全站不可用 | 15 min |
| SEV-2 | 核心功能受損 | 1 hr |
| SEV-3 | 非核心功能 | 1 day |

### Incident Lifecycle
```
Detect → Acknowledge → Mitigate → Resolve → Post-Mortem
```

---

## 10. Post-Mortem 模板

```markdown
## Incident: [標題]
- Severity: SEV-N
- Duration: ... → ...
- Affected: 用戶數 / 功能

## Timeline
- HH:MM Detected
- HH:MM Acknowledged
- HH:MM Mitigated
- HH:MM Resolved

## Root Cause
（5-Why 分析）

## What Went Well
## What Went Wrong

## Action Items
- [ ] 預防
- [ ] 偵測
- [ ] 修復
```

---

## 文件溯源

- 模板：`templates/vibecoding/14_deployment_and_operations_guide.md`
- 對應：[`13_security_checklist.md`](./13_security_checklist.md), [`05_architecture.md §6`](./05_architecture.md)
- §3.1-3.2 對齊：[`09_file_dependencies.md §3`](./09_file_dependencies.md)、[`04_adr/ADR-008_knowledge_graph_as_ssot.md`](./04_adr/ADR-008_knowledge_graph_as_ssot.md)、`tools/build_graph.py`

---

## 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-29 | v1.2 | 新增 §3.1 Graph Lint in CI（`build_graph.py --strict` 整合 GitHub Actions 的 lint-typecheck job）+ §3.2 Pre-commit Hook 配置範例。 |
| 2026-04-28 | v1.1 | 標註 K8s / Celery / RDS 為 v3 roadmap，非當前 MVP 架構 |
| 2026-04-28 | v1.0 | 初版 |
