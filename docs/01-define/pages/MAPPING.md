# 頁面規格對應表 (Page Specification Mapping)

> **用途：** 作為 `docs/02-design/E5x--frontend-information-architecture.md`（IA 18 頁定義）與本目錄 `pages/*.md`（18 份 page spec）之間的**雙向對照索引**。
> **維護原則：** IA 新增/刪除頁面時同步更新本檔；新增 spec 檔時新增對應列。
>
> **最後更新：** 2026-04-27 · **版本：** v3.1 · **對應 IA 版本：** v1.2 · **對應前端架構版本：** v1.1 · **對應 API 規格版本：** v1.2

---

## 1. 快速總覽

| 指標 | 數字 |
|:-----|:----|
| IA 定義頁面總數 | **18 頁**（Auth 2 + Project 入口 2 + Phase 1 Define 2 + Phase 2 Diverge 3 + Phase 3 Converge 4 + 輔助 2 + 系統 2 + 開發 1） |
| Page spec 檔數 | **18 份**（`01_auth.md` — `18_not_found.md`） |
| 已覆蓋頁面 | 18 / 18 |
| 受保護路由（ProtectedRoute） | 14 頁 |
| 公開路由 | 3 頁（Auth, ResetPassword, NotFound） |
| DEV-only 路由 | 1 頁（DevSeed） |

---

## 2. IA 頁面 → Page Spec 檔（Forward Mapping）

### 2.1 認證（Public Routes，2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P01 | `/auth` | 登入/註冊 | — | `01_auth.md` | `src/pages/Auth.tsx` |
| P02 | `/reset-password` | 重設密碼 | — | `02_reset_password.md` | `src/pages/ResetPassword.tsx` |

### 2.2 專案入口（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P03 | `/projects` | 專案列表 | — | `03_project_list.md` | `src/pages/ProjectList.tsx` |
| P04 | `/projects/:id` | 專案儀表板 | — | `04_project_dashboard.md` | `src/pages/ProjectDashboard.tsx` |

### 2.3 Phase 1 — Define（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P05 | `/projects/:id/brief` | 任務定義 / Brief | 1 | `05_task_definition.md` | `src/pages/TaskDefinition.tsx` |
| P06 | `/projects/:id/explore` | 探索 / Socratic 問答 | 1 | `06_explore.md` | `src/pages/Explore.tsx` |

### 2.4 Phase 2 — Diverge（3 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P07 | `/projects/:id/track` | 假設追蹤 | 2 | `07_track.md` | `src/pages/Track.tsx` |
| P08 | `/projects/:id/create` | 方案創造 | 2 | `08_create.md` | `src/pages/Create.tsx` |
| P09 | `/projects/:id/pre-cad` | Pre-CAD 審查 | 2 | `09_pre_cad_review.md` | `src/pages/PreCadReview.tsx` |

### 2.5 Phase 3 — Converge（4 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P10 | `/projects/:id/cad` | CAD 進行中 | 2.5 | `10_cad_in_progress.md` | `src/pages/CadInProgress.tsx` |
| P11 | `/projects/:id/review` | 設計審查 | 3 | `11_design_review.md` | `src/pages/DesignReview.tsx` |
| P12 | `/projects/:id/decide` | 決策記錄 | 3 | `12_decision_record.md` | `src/pages/DecisionRecord.tsx` |
| P13 | `/projects/:id/feynman` | 費曼學習 / 知識內化 | 3 | `13_feynman.md` | `src/pages/Feynman.tsx` |

### 2.6 專案輔助 + 全域知識（2 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P14 | `/knowledge-base`, `/knowledge-base/:slug` | 知識庫 | — | `14_knowledge_base.md` | `src/pages/KnowledgeBase.tsx` |
| P15 | `/projects/:id/constraint-labels` | 約束標籤字典 | — | `15_constraint_label_dictionary.md` | `src/pages/ConstraintLabelDictionary.tsx` |

### 2.7 系統與開發（3 頁）

| IA # | 路徑 | 頁面名稱 | Phase | Spec 檔 | Source |
|:-----|:-----|:---------|:------|:--------|:-------|
| P16 | `/settings` | 設定 | — | `16_settings.md` | `src/pages/Settings.tsx` |
| P17 | `/dev/seed` | 開發種子資料 | — | `17_dev_seed.md` | `src/pages/DevSeed.tsx` |
| P18 | `/*` | 404 頁面未找到 | — | `18_not_found.md` | `src/pages/NotFound.tsx` |

---

## 3. Page Spec 檔 → IA 頁面（Reverse Mapping）

| # | Spec 檔 | 覆蓋 IA 頁 | 頁面類型 | Gate 覆蓋 |
|:--|:--------|:-----------|:---------|:----------|
| 01 | `01_auth.md` | **P01** | auth | — |
| 02 | `02_reset_password.md` | **P02** | auth | — |
| 03 | `03_project_list.md` | **P03** | list | — |
| 04 | `04_project_dashboard.md` | **P04** | dashboard | Gate overview |
| 05 | `05_task_definition.md` | **P05** | form | Gate 1.1 |
| 06 | `06_explore.md` | **P06** | wizard | Gate 1.2, Phase Gate 1 |
| 07 | `07_track.md` | **P07** | kanban | Gate 2.1 |
| 08 | `08_create.md` | **P08** | wizard | Gate 2.2, Phase Gate 2 |
| 09 | `09_pre_cad_review.md` | **P09** | review | Gate P |
| 10 | `10_cad_in_progress.md` | **P10** | progress | — |
| 11 | `11_design_review.md` | **P11** | review | Gate 3.1 |
| 12 | `12_decision_record.md` | **P12** | form | Gate 3.2, Phase Gate 3 |
| 13 | `13_feynman.md` | **P13** | detail | Gate 8 |
| 14 | `14_knowledge_base.md` | **P14** | list + detail | — |
| 15 | `15_constraint_label_dictionary.md` | **P15** | utility | — |
| 16 | `16_settings.md` | **P16** | form | — |
| 17 | `17_dev_seed.md` | **P17** | utility | — |
| 18 | `18_not_found.md` | **P18** | error | — |

---

## 4. 主題分群視圖

### 4.1 認證層（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P01 `/auth` | `01_auth.md` |
| P02 `/reset-password` | `02_reset_password.md` |

### 4.2 專案管理（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P03 `/projects` 專案列表 | `03_project_list.md` |
| P04 `/projects/:id` 專案儀表板 | `04_project_dashboard.md` |

### 4.3 Phase 1 Define — 問題定義（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P05 Brief / 任務定義 | `05_task_definition.md` |
| P06 Explore / Socratic 問答 | `06_explore.md` |

### 4.4 Phase 2 Diverge — 方案發散（3 頁 / 3 檔）

| IA | Spec |
|:---|:-----|
| P07 Track / 假設追蹤 | `07_track.md` |
| P08 Create / 方案創造（5-step wizard） | `08_create.md` |
| P09 PreCadReview / Pre-CAD 審查 | `09_pre_cad_review.md` |

### 4.5 Phase 3 Converge — 收斂決策（4 頁 / 4 檔）

| IA | Spec |
|:---|:-----|
| P10 CadInProgress / CAD 進行中 | `10_cad_in_progress.md` |
| P11 DesignReview / 設計審查 | `11_design_review.md` |
| P12 DecisionRecord / 決策記錄 | `12_decision_record.md` |
| P13 Feynman / 知識內化 | `13_feynman.md` |

### 4.6 知識與輔助工具（2 頁 / 2 檔）

| IA | Spec |
|:---|:-----|
| P14 KnowledgeBase / 知識庫 | `14_knowledge_base.md` |
| P15 ConstraintLabelDictionary / 約束標籤字典 | `15_constraint_label_dictionary.md` |

### 4.7 系統設定與開發（3 頁 / 3 檔）

| IA | Spec |
|:---|:-----|
| P16 Settings / 設定 | `16_settings.md` |
| P17 DevSeed / 開發種子 | `17_dev_seed.md` |
| P18 NotFound / 404 | `18_not_found.md` |

---

## 5. 關鍵互動路徑

> **完整 scenario 敘事（序列圖 + 互動對照表）**：見 [`E3--system-interaction-flow.md`](../E3--system-interaction-flow.md) §2-4。
> **Sprint 開發者速查**：見 [`SPRINT-INDEX.md`](../../SPRINT-INDEX.md) §2 By Scenario。

| Journey | E3x 章節 | 涉及 Spec |
|:--------|:---------|:----------|
| Forward TRIZ 解矛盾 | §2 | `01` → `03` → `04` → `08` |
| TRIZ 跨域去錨定具體化 | §3 | `04` → `08` → `07` |
| Pre-CAD Gate | §4 | `04` → `09` → `12` |
| 完整 8-Gate Happy Path | §1 | `01` → `03` → … → `13`（全 13 頁） |
| 知識庫查詢 | — | `14` |

---

## 6. 前端細節索引

> 以下索引的 SSOT 位於各自的上游文件。本節僅提供快速指標。
> **Sprint 開發者速查**：見 [`SPRINT-INDEX.md`](../../SPRINT-INDEX.md) §1 By Page。

| 索引類型 | SSOT | 說明 |
|:---------|:-----|:-----|
| 業務元件清單 | [`E5x--frontend-architecture.md`](../../02-design/E5x--frontend-architecture.md) §2 | Feature-first 元件對應 |
| API Router → 頁面 | [`E5--api-design-specification.md`](../../02-design/E5--api-design-specification.md) §7 | 端點 → 消費頁面 |
| React Context / Hook | [`E5x--frontend-architecture.md`](../../02-design/E5x--frontend-architecture.md) §3 | Context + Hook 索引 |
| 8-Gate 系統 | [`E3--system-interaction-flow.md`](../E3--system-interaction-flow.md) §5 + [`E3--ai-agent-detailed-design.md`](../E3--ai-agent-detailed-design.md) §11.2a | Gate 判定邏輯 |
| Code Splitting | [`E5x--frontend-architecture.md`](../../02-design/E5x--frontend-architecture.md) §5 | Eager/Lazy 配置 |

---

## 7. 驗證檢查清單

- [x] 所有 18 個 IA 頁面都有對應 spec 檔
- [x] 所有 spec 檔都能對應回 IA 頁面
- [x] Phase 分組（Define / Diverge / Converge）對齊 IA 與 sidebar navigation
- [x] 舊 §6-10 內容已指向 SSOT（E5x-frontend-architecture / E5-api-spec / E3x）

---

## 8. 變更記錄

| 日期 | 版本 | 變更摘要 |
|:-----|:-----|:---------|
| 2026-04-27 | v3.0 | 去重瘦身：§5 journey 改為 E3x pointer 摘要表；舊 §6-10 改為 §6 SSOT pointer 表。新增 SPRINT-INDEX.md 指標。 |
| 2026-04-24 | v2.0 | 完全重寫：從舊專案遷移至 RD Design Copilot（18 頁 IA）。建立全維度對照。 |
