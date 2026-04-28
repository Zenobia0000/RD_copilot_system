# RD Design Copilot — 完整規劃索引（VibeCoding Workflow）

> **產出來源**：依 `rd_assistant_design_system/VibeCoding_Workflow_Templates/` 的 18 份模板，針對 RD Design Copilot 產品做完整規劃。
> **產品定位**：AI 輔助的早期概念設計系統 — 把「未知」變成「可追蹤的假設」、「靈感」變成「可審查的方案」、「試錯」變成「最小驗證」。TRIZ 推理閉環 + TR0-TR10 工程執行雙軌。
> **建立日期**：2026-04-28
> **版本**：v1.0
> **狀態**：Draft（核心 6 份 full，其餘 12 份 skeleton 供 follow-up 擴充）

---

## 1. 文件對應表

| # | 模板來源（VibeCoding） | 本目錄產出 | 深度 | 備註 |
|:--|:----------------------|:----------|:-----|:-----|
| 00 | `00_workflow_manual.md` | [`00_workflow_manual.md`](./00_workflow_manual.md) | skeleton | 模式選擇（Full vs MVP）+ 對齊 RD Copilot 用 Full Mode |
| 01 | `01_development_workflow_cookbook.md` | [`01_cookbook.md`](./01_cookbook.md) | skeleton | 哲學對齊（BDD + DDD + Clean Arch + TDD） |
| 02 | `02_project_brief_and_prd.md` | [`02_prd.md`](./02_prd.md) | **FULL** | 收斂 `rd_assistant_design_system/rd_設計文稿.md` |
| 03 | `03_behavior_driven_development_guide.md` | [`03_bdd_guide.md`](./03_bdd_guide.md) | **FULL** | 7 個核心 Feature（對齊 18 頁 IA 與 8-Gate） |
| 04 | `04_architecture_decision_record_template.md` | [`04_adr/`](./04_adr/) | skeleton | 7 個 ADR（v1.1：加 ADR-006/007） |
| 05 | `05_architecture_and_design_document.md` | [`05_architecture.md`](./05_architecture.md) | **Updated v1.1** | 對齊 08 v2.0：頂部加現況/演化警告；§1.2 改概念域圖（markdown-only）；§1.3 改 Harness 分層 |
| 06 | `06_api_design_specification.md` | [`06_api_spec.md`](./06_api_spec.md) | **FULL** | 提綱 RESTful API + TRIZ skill endpoints |
| 07 | `07_module_specification_and_tests.md` | [`07_module_spec.md`](./07_module_spec.md) | **Updated v2.0** | 完全覆寫：模組改為 Tool / Skill / Command 三類契約 |
| 08 | `08_project_structure_guide.md` | [`08_project_structure.md`](./08_project_structure.md) | **Updated v2.0** | 對齊實際 M1-M4 harness（claude-code 風）；先前 Clean Arch 提案已覆寫 |
| 09 | `09_file_dependencies_template.md` | [`09_file_dependencies.md`](./09_file_dependencies.md) | **Updated v2.0** | 完全覆寫：DAG 改為 harness 內部依賴 + filesystem 運行時依賴 |
| 10 | `10_class_relationships_template.md` | [`10_class_relationships.md`](./10_class_relationships.md) | **Updated v2.0** | 完全覆寫：UML 改為實際 harness 類別（AgentLoop/Tool/Registry/Skill/...）|
| 11 | `11_code_review_and_refactoring_guide.md` | [`11_code_review.md`](./11_code_review.md) | skeleton | Code Review 流程與標準 |
| 12 | `12_frontend_architecture_specification.md` | [`12_frontend_architecture.md`](./12_frontend_architecture.md) | pointer | 指向 `rd_assistant_design_system/design-system-specs/` |
| 13 | `13_security_and_readiness_checklists.md` | [`13_security_checklist.md`](./13_security_checklist.md) | skeleton | Pre-launch 安全與就緒檢查 |
| 14 | `14_deployment_and_operations_guide.md` | [`14_deployment_ops.md`](./14_deployment_ops.md) | skeleton | CI/CD + Runbook 範本 |
| 15 | `15_documentation_and_maintenance_guide.md` | [`15_documentation_guide.md`](./15_documentation_guide.md) | skeleton | 文件治理規範 |
| 16 | `16_wbs_development_plan_template.md` | [`16_wbs.md`](./16_wbs.md) | **FULL** | 雙軸 WBS：TRIZ Step 0-5 + TR0-TR10 |
| 17 | `17_frontend_information_architecture_template.md` | [`17_frontend_ia.md`](./17_frontend_ia.md) | pointer | 指向 `docs/01-define/pages/INDEX.md`（既有 18 頁規格） |
| 18 | — (自訂) | [`18_flow_contract.md`](./18_flow_contract.md) | **FULL** | 產品生命週期 ↔ TRIZ/TR 映射 + Gate 層級分析 + 擴展路線圖 |

---

## 2. 文件依賴圖

```
                   ┌──────────────────┐
                   │ 00_workflow_manual│
                   └─────────┬────────┘
                             │
                   ┌─────────▼────────┐
                   │ 01_cookbook       │
                   └─────────┬────────┘
                             │
                   ┌─────────▼────────┐
                   │ 02_prd (FULL)     │ ◄── 商業/用戶定義 SSOT
                   └─────────┬────────┘
              ┌──────────────┼──────────────┐
              │              │              │
   ┌──────────▼──┐  ┌────────▼────┐  ┌──────▼────┐
   │ 03_bdd_guide │  │ 16_wbs       │  │ 17_fe_ia │
   │  (FULL)      │  │  (FULL)      │  │  (ptr)   │
   └──────┬───────┘  └──────┬───────┘  └──────────┘
          │                 │
          │     ┌───────────▼─────────┐
          │     │ 04_adr (5 ADR stubs)│
          │     └───────────┬─────────┘
          │                 │
          │     ┌───────────▼─────────┐
          └────►│ 05_architecture (F) │ ◄── 技術 SSOT
                └─┬───────────────────┘
                  │
       ┌──────────┼──────────────┬──────────────┐
       │          │              │              │
┌──────▼─┐ ┌──────▼──┐ ┌─────────▼──┐ ┌─────────▼─┐
│ 06_api │ │ 07_module│ │ 08_struct │ │ 12_fe_arch│
│ (FULL) │ │ (skel)   │ │ (skel)    │ │  (ptr)    │
└────┬───┘ └─┬────────┘ └───────────┘ └───────────┘
     │       │
     │   ┌───▼─────────┐
     │   │ 09_deps     │
     │   │ 10_class    │
     │   │ 11_review   │
     │   └─────────────┘
     │
     └────────────┬───────────────┐
                  │               │
            ┌─────▼──────┐  ┌─────▼─────┐
            │ 13_security│  │ 14_deploy │
            │  (skel)    │  │  (skel)   │
            └────────────┘  └─────┬─────┘
                                  │
                            ┌─────▼─────┐
                            │ 15_doc    │
                            └───────────┘
```

---

## 3. 與既有 docs 的關係

本目錄不重複既有資料，所有交叉引用以 link 方式處理：

| 既有資料夾 | 角色 | 本目錄如何引用 |
|:----------|:-----|:--------------|
| `docs/01-define/pages/` | 18 頁產品規格 SSOT | 17_frontend_ia 直接 pointer，03_bdd 為 6 個核心頁產 BDD |
| `docs/01-define/pages/INDEX.md` | 頁面對照索引 | 02_prd / 17_fe_ia 引用 |
| `docs/_domain-knowledge/` | DK-01-05 方法論 KB | 02_prd 用 DK-01 流程，05_architecture 用 DK-02 機制 |
| `docs/_harness/auto_triz_strategy.md` | TRIZ 主策略 SSOT | 05_architecture 整合，16_wbs 雙軸引用 |
| `docs/_harness/engineering/` | TR0-10 工程執行範本 | 16_wbs 引用 TR Gate 框架，05_architecture §9 |
| `docs/_harness/uml/` | 11 張流程 UML | 05_architecture 引用 |
| `docs/engineering/gate_reviews/` | TR Gate 實際產出 | 16_wbs 追蹤實際進度 |
| `rd_assistant_design_system/design-system-specs/` | 設計系統 6 份規格 | 12_frontend_architecture pointer |
| `rd_assistant_design_system/rd_設計文稿.md` | 原始 PRD 草稿 | 02_prd 收斂這份 |
| `.claude/skills/triz-*` | TRIZ 6 skill | 05_architecture §2 內部 AI 服務層 |
| `.claude/skills/tr-*` | TR 5 skill | 05_architecture §2，16_wbs 工具鏈 |
| `.claude/context/triz/.triz-state.json` | TRIZ session state | 16_wbs 追蹤 active session |
| `.claude/context/triz/.tr-state.json` | TR gate state | 16_wbs 追蹤 TR1 NO-GO 等 |

---

## 4. 閱讀順序建議

### 4.1 PM / 產品角色
1. [`02_prd.md`](./02_prd.md) — 產品定義
2. [`16_wbs.md`](./16_wbs.md) — 進度與里程碑
3. [`03_bdd_guide.md`](./03_bdd_guide.md) — 用戶故事 ↔ BDD 對應
4. [`17_frontend_ia.md`](./17_frontend_ia.md) → 跳到 `docs/01-define/pages/INDEX.md`

### 4.2 技術負責人 / 架構師
1. [`02_prd.md`](./02_prd.md) §3 — 用戶故事
2. [`05_architecture.md`](./05_architecture.md) — 系統架構
3. [`04_adr/`](./04_adr/) — 關鍵決策記錄
4. [`06_api_spec.md`](./06_api_spec.md) — API 契約
5. [`12_frontend_architecture.md`](./12_frontend_architecture.md) → 跳到 `design-system-specs/`

### 4.3 開發工程師
1. [`05_architecture.md`](./05_architecture.md) §2.5 模組職責
2. [`07_module_spec.md`](./07_module_spec.md) — 模組契約模板
3. [`08_project_structure.md`](./08_project_structure.md) — 目錄規範
4. [`11_code_review.md`](./11_code_review.md) — 提交前自檢

### 4.4 SRE / Ops
1. [`13_security_checklist.md`](./13_security_checklist.md)
2. [`14_deployment_ops.md`](./14_deployment_ops.md)
3. [`15_documentation_guide.md`](./15_documentation_guide.md)

### 4.5 QA
1. [`03_bdd_guide.md`](./03_bdd_guide.md) — 接受標準
2. [`07_module_spec.md`](./07_module_spec.md) §測試案例
3. [`13_security_checklist.md`](./13_security_checklist.md)

---

## 5. 維護指引

- **修改本目錄任一檔**：同步更新 §1 表格（特別是「深度」與「狀態」）
- **新增文件**：複製對應 VibeCoding 模板，填 frontmatter，更新 §1 表格 + §2 依賴圖
- **既有資料移動**：本目錄改 link，不複製內容
- **TRIZ session 推進**：16_wbs 同步 `.triz-state.json` / `.tr-state.json` 進展

---

## 6. 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-28 | v1.0 | 初版建立：6 份 FULL（02/03/05/06/16）+ 2 份 pointer（12/17）+ 10 份 skeleton（00/01/04/07-11/13-15） |
| 2026-04-28 | v1.1 | 08_project_structure 升 v2.0：發現先前 Clean Arch 提案與實際 backend（claude-code 風 harness）方向相反，完全覆寫對齊 M1-M4 現況。05/07/09/10 仍含 Clean Arch 用詞，待 follow-up 對齊。 |
| 2026-04-28 | v1.2 | F1+F3+F4 follow-up 完成：05_architecture v1.1（surgical：加現況/演化警告 + §1.1.2/1.2/1.3 改寫）、07/09/10 全面覆寫到 v2.0、新增 ADR-006 Production Persistence + ADR-007 Multi-tenancy。F2（前端目錄）與 F5（HARNESS_INTERNALS.md）留待後續。 |
| 2026-04-28 | v1.4 | docs/planning 全面對齊 Flow Contract：10 份文件加 gate 狀態標記、階段就緒度 tag、harness-first 語言替換（01/03/05/06/07/11/15/16/17 + 00）。 |
| 2026-04-28 | v1.3 | 新增 18_flow_contract.md：第一性原理分析 BDD→Skill 映射、Gate 層級審查（8→1 簡化）、擴展路線圖。triz-verify 增加 cad_readiness 區塊（Gate P 合併）。 |
