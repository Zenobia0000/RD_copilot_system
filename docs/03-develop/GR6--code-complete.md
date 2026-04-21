# GR6 — Code Complete Gate Review


| Field   | Value                                                 |
| ------- | ----------------------------------------------------- |
| Version | v1.0                                                  |
| Date    | 2026-04-15                                            |
| Status  | Draft                                                 |
| Gate    | TR6 (Code Complete)                                   |
| Chair   | Engineering Lead TBD — by gate date TBD               |
| 對應指引    | [GR6x--code-review-guide](GR6x--code-review-guide.md) |


> **Template** — 於 TR6 gate 會議逐條確認；未勾選者需附 Waiver 或延至 GR7。

---

## §1 Gate 目的與進入條件

**目的**：確認所有 WBS workstream 的 feature code 已完成 → 測試綠燈 → 文檔同步 → UAT 對應可驗證。進入 GR6 = 可進入 Integration（GR7）的前置。

**進入條件 / Entry Criteria**：

- [ ] 所有 WBS workstream（WS-A…WS-H）狀態 = Done 或有明確 Waiver（見 [E3 WBS](../01-define/E3--wbs-development-plan.md) + [workstreams](../01-define/wbs-workstreams/README.md)）
- [ ] main 分支 CI 最近 3 次 build 連續綠燈
- [ ] 所有已標為 P0 的 assumption 皆有 verification_stage ≠ 'unplanned'
- [ ] Code freeze 公告已發佈（日期 TBD — PM TBD by TBD）

---

## §2 Feature Completion Checklist（從 WBS 抽出 ~15 項）

- [ ] **F-01 (WS-A)** Backend API alignment：所有 endpoint 與 `E5--api-design-specification.md` 一致
- [ ] **F-02 (WS-A)** Pydantic schemas 已 codegen 對應 TS 型別無 drift
- [ ] **F-03 (WS-B)** E2E 手測腳本（`02-design/E7x--e2e-manual-scripts/`）至少 1 輪通過
- [ ] **F-04 (WS-C)** 所有 Mock data 移除 → Live Supabase 整合完成
- [ ] **F-05 (WS-D)** TRIZ 分層 drill-down（L1/L2/L3）前後端閉環
- [ ] **F-06 (WS-D)** `layered_triz_solutions` schema 寫入/讀取路徑 E2E 驗證
- [ ] **F-07 (WS-E)** 子系統介面定義 UI + interface_contract JSONB 持久化
- [ ] **F-08 (WS-F)** TC → 多 PC decomposition（`contradictions.parent_id`）可視化 + 編輯
- [ ] **F-09 (WS-G)** L3 Su-Field 平行旁路 scanner 上線
- [ ] **F-10 (WS-H)** Playwright E2E 補測覆蓋關鍵 3 scenarios
- [ ] **F-11** Anti-Anchor validation_passport 欄位完整寫入（003 migration 欄位）
- [ ] **F-12** Pre-CAD 六維評分 + citations UI 完整
- [ ] **F-13** Dashboard aggregates（gates_passed / quick_stats）正確
- [ ] **F-14** MUST criteria 自動產生（Brief → must_criteria_config）
- [ ] **F-15** Evidence Matrix：E0–E5 level 升降邏輯 + evidence_entries 寫入

---

## §3 Code Quality Checklist

參考 [GR6x--code-review-guide](GR6x--code-review-guide.md) 所列命令。

### 3.1 Lint / Type / Format

- [ ] **前端** `npm run lint` pass（eslint 9 + typescript-eslint）
- [ ] **前端** `npm run build` pass（Vite + tsc 型別檢查）
- [ ] **後端** `ruff check backend/app` pass（rules `E, F, I, N, W`, line-length=120）
- [ ] **後端** `ruff format backend/app --check` pass
- [ ] **後端** mypy / pyright type check pass（TBD — 若未接入則列 Waiver）

### 3.2 Test

- [ ] **後端** `pytest backend/tests` 綠燈（`asyncio_mode=auto`）
- [ ] **後端** test coverage ≥ 70%（門檻 TBD — QA Lead TBD by TBD）
- [ ] **前端** unit test（Vitest）綠燈
- [ ] **前端** Playwright smoke 綠燈

### 3.3 Security / Static

- [ ] `pip-audit` 無 High/Critical（對應 E8 AI-03）
- [ ] `npm audit --audit-level=high` 無 High/Critical
- [ ] 無硬編碼 secrets（grep `SUPABASE_SERVICE_KEY|ANTHROPIC_API_KEY|.env` 在 source）

---

## §4 UAT 對應檢查（US-01..US-12）

對應 [E1 §7A](../00-discover/E1--project-brief-and-prd.md#7a-使用者故事與允收標準-user-stories--uat)。

- [ ] **US-01** Brief 上傳 → 自動拆解硬約束/矛盾/假設（UAT-01 主要路徑）
- [ ] **US-02** Create 頁分層 drill-down（L1→L2→L3）（UAT-02）
- [ ] **US-03** Anti-Anchor Sprint 產生 ≥3 條路線（UAT-03）
- [ ] **US-04** Validation Passport 追蹤假設狀態
- [ ] **US-05** Pre-CAD Gate 六維評分 + citations（UAT-05）
- [ ] **US-06** MUST 硬限制 Pass/Conditional/Fail 分類
- [ ] **US-07** Evidence Matrix KT 決策關聯證據（BDD TBD — PM TBD by 2026-05-15 TBD）
- [ ] **US-08** Dashboard 單 project 階段/gate/風險摘要（BDD TBD）
- [ ] **US-09** AI 建議可點開 citation（UAT-09）
- [ ] **US-10** 假設回寫知識庫（BDD TBD）
- [ ] **US-11** Pre-CAD 失效機制對照（UAT-11）
- [ ] **US-12** Gate 決策一頁摘要（BDD TBD）

---

## §5 Documentation Updated

- [ ] [E3 架構](../01-define/E3--architecture-and-design.md) 已同步最新組件與 state machine
- [ ] [E4 ERD](../01-define/diagrams/E4--erd.md) 反映最新 migration
- [ ] [E5 API Spec](../02-design/E5--api-design-specification.md) endpoint 清單無 drift
- [ ] [E5x BDD](../02-design/E5x--bdd-scenarios.md) feature 對應 US-01..12 完備
- [ ] ADR：本階段新增重大決策皆已落 ADR（`01-define/adrs/`）
- [ ] CHANGELOG / Release note 草稿就緒

---

## §6 Outstanding Issues / Waivers


| ID  | Issue                             | Severity | Waiver Owner | Target (GR7/後續) |
| --- | --------------------------------- | -------- | ------------ | --------------- |
| TBD | TBD — Engineering Lead TBD by TBD | —        | —            | —               |


---

## §7 Gate Decision


| Field        | Value                                      |
| ------------ | ------------------------------------------ |
| 會議日期         | TBD — PM TBD by TBD                        |
| 主席 / Chair   | Engineering Lead TBD                       |
| Reviewers    | ARCH TBD / QA TBD / PM TBD / Security TBD  |
| Decision     | [ ] Pass [ ] Pass-with-conditions [ ] Fail |
| Conditions   | TBD                                        |
| 重測日期（若 Fail） | TBD                                        |
| Signed-off   | TBD                                        |


> 決策後：Pass → 進入 GR7（Integration）；Pass-with-conditions → 列出補救項，追蹤至 GR7；Fail → 回到 WBS 補 code，重排 GR6。

