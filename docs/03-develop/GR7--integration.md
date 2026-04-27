# GR7 — Integration Gate Review

| Field     | Value                                                                 |
|-----------|-----------------------------------------------------------------------|
| Version   | v1.0                                                                  |
| Date      | 2026-04-15                                                            |
| Status    | Draft                                                                 |
| Gate      | TR7 (Integration)                                                     |
| Chair     | Engineering Lead TBD — by gate date TBD                                |

> **Template** — 於 TR7 gate 會議逐條確認；任一 Fail 需回退至 GR6 或延後。

---

## §1 進入條件 / Entry Criteria

- [ ] **GR6 Pass** 或 Pass-with-conditions 且條件已全部 close（見 [GR6](GR6--code-complete.md) §7）
- [ ] 整合測試環境（staging）可用，資料已按 ERD（[E4](../01-define/diagrams/E4--erd.md)）部署
- [ ] Observability 骨架就位（log / trace / metric 基本可觀察）

---

## §2 E2E Scenarios Pass Checklist

從 [E7x E2E manual scripts](../02-design/E7x--e2e-manual-scripts/) + [E5x BDD](../02-design/E5x--bdd-scenarios.md) 抽出。

### 2.1 Manual E2E
- [ ] **E2E-01** `explore_pc_decomposition.md` 完整腳本通過
- [ ] **E2E-02** Forward TRIZ 流程（Brief → Contradictions → Layered drill-down → Solutions）（[E3x system-interaction-flow](../01-define/E3--system-interaction-flow.md) Scenario 1）
- [ ] **E2E-03** Reverse 跨域去錨定流程（Scenario 2）
- [ ] **E2E-04** Pre-CAD 審查流程（Scenario 3，含 six-dim scoring + citations + signatures）

### 2.2 BDD Features（對應 US-01..12）
- [ ] **BDD-Feature-1** TRIZ drill-down 所有 scenario 通過
- [ ] **BDD-Feature-2** 跨域去錨定所有 scenario 通過
- [ ] **BDD-Feature-3** Pre-CAD Gate 所有 scenario 通過
- [ ] **BDD Background** Brief → 硬約束/矛盾/假設自動拆解通過
- [ ] 其餘未實作的 BDD scenario（US-07/08/10/12）有 Waiver 記錄

---

## §3 API Contract Verification

- [ ] **Schema drift = 0**：`schemas.py` → `openapi.json` → TS type 三者一致（codegen 腳本 run 無 diff）
- [ ] Pydantic `model_validate` 全部 endpoint request/response 在整合測試中 pass
- [ ] 對 [E5 API Design Spec](../02-design/E5--api-design-specification.md) 所列 endpoint，每條至少 1 條整合測試覆蓋
- [ ] Breaking change（若有）已記錄於 CHANGELOG + 前端 API client 已同步
- [ ] OpenAPI JSON 產物納入 CI artifact 保存

---

## §4 Cross-Module Integration

參考 [E3x--system-interaction-flow.md](../01-define/E3--system-interaction-flow.md)。

- [ ] **Agent 協作**：Subsystem Discovery → TRIZ Solver（含跨域去錨定）→ Pre-CAD 評分 agent 串接驗證
- [ ] **State Machine**：[E3 Appendix D](../01-define/E3--architecture-and-design.md#appendix-d-state-machine) 所有 transition 可觀察 + 可逆
- [ ] **Convergence Loop**：`convergence_snapshots.state` JSONB 正確讀寫、斷線續跑
- [ ] **Spatial Resolver 三層**：`project_component_overrides` → `learned_components` → web 查詢 層級順序正確（[006/007 migration](../../supabase/migrations/007_learned_components.sql)）
- [ ] **跨子系統流程**：Brief → Contradictions → Assumptions → Layered TRIZ → Alternatives → Decision → Signatures，端到端資料流無斷點
- [ ] **前端 ↔ 後端 ↔ Supabase** RLS 跨租戶整合測試 pass（對應 E8 AI-14）

---

## §5 Data Migration Sync

- [ ] `supabase/migrations/000`–`010` 全部套用後無錯誤（fresh DB）
- [ ] [E4 ERD](../01-define/diagrams/E4--erd.md) §4 FK 清單與實際 DB 一致（用 `information_schema.table_constraints` 比對）
- [ ] [E4 ERD §5](../01-define/diagrams/E4--erd.md) RLS 清單與實際 policy 一致（`pg_policies` 比對）
- [ ] 所有 `UNIQUE`、`NOT NULL`、`CHECK` 約束在整合測試中至少 1 條 negative test 驗證
- [ ] Storage bucket `review-attachments` 存取政策驗證通過

---

## §6 Performance / Load Baseline

> 非 GA 前硬性門檻，列作基線觀察 — TBD — Performance Lead TBD by TBD。

- [ ] 關鍵 API P95 latency < target（target TBD）
- [ ] LLM Solver endpoint timeout / retry 行為驗證（對應 [ADR-003](../01-define/adrs/ADR-003-llm-service-hardening.md)）
- [ ] 單 project 1000 entity 載入 UI 無卡頓
- [ ] 長時間連線（SSE / Supabase realtime）穩定性 ≥ 30 min
- [ ] Load baseline 數據已存入 observability（儀表板 link TBD）

---

## §7 Gate Decision

| Field           | Value                                           |
|-----------------|-------------------------------------------------|
| 會議日期        | TBD — PM TBD by TBD                             |
| 主席 / Chair    | Engineering Lead TBD                             |
| Reviewers       | ARCH TBD / QA TBD / Security TBD / Ops TBD       |
| Decision        | [ ] Pass  [ ] Pass-with-conditions  [ ] Fail     |
| Conditions      | TBD                                              |
| 重測日期（若 Fail） | TBD                                         |
| Signed-off      | TBD                                              |

> Pass → 進入 TR8 → TR9 → GR10（GA Readiness）；Fail → 定位缺口回到 GR6 或本階段重做。
