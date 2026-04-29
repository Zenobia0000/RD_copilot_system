# RD Design Copilot — 完整規劃索引（VibeCoding Workflow）

> **產出來源**：依 `templates/vibecoding/` 的 18 份模板，針對 RD Design Copilot 產品做完整規劃。
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
| 02 | `02_project_brief_and_prd.md` | [`02_prd.md`](./02_prd.md) | **FULL** | 收斂 `templates/rd_設計文稿.md` |
| 03 | `03_behavior_driven_development_guide.md` | [`03_bdd_guide.md`](./03_bdd_guide.md) | **FULL** | 7 個核心 Feature（對齊 18 頁 IA 與 8-Gate） |
| 04 | `04_architecture_decision_record_template.md` | [`04_adr/`](./04_adr/) | skeleton | 7 個 ADR（v1.1：加 ADR-006/007） |
| 05 | `05_architecture_and_design_document.md` | [`05_architecture.md`](./05_architecture.md) | **Updated v1.1** | 對齊 08 v2.0：頂部加現況/演化警告；§1.2 改概念域圖（markdown-only）；§1.3 改 Harness 分層 |
| 06 | `06_api_design_specification.md` | [`06_api_spec.md`](./06_api_spec.md) | **FULL** | 提綱 RESTful API + TRIZ skill endpoints |
| 07 | `07_module_specification_and_tests.md` | [`07_module_spec.md`](./07_module_spec.md) | **Updated v2.0** | 完全覆寫：模組改為 Tool / Skill / Command 三類契約 |
| 08 | `08_project_structure_guide.md` | [`08_project_structure.md`](./08_project_structure.md) | **Updated v2.0** | 對齊實際 M1-M4 harness（claude-code 風）；先前 Clean Arch 提案已覆寫 |
| 09 | `09_file_dependencies_template.md` | [`09_file_dependencies.md`](./09_file_dependencies.md) | **Updated v2.0** | 完全覆寫：DAG 改為 harness 內部依賴 + filesystem 運行時依賴 |
| 10 | `10_class_relationships_template.md` | [`10_class_relationships.md`](./10_class_relationships.md) | **Updated v2.0** | 完全覆寫：UML 改為實際 harness 類別（AgentLoop/Tool/Registry/Skill/...）|
| 11 | `11_code_review_and_refactoring_guide.md` | [`11_code_review.md`](./11_code_review.md) | skeleton | Code Review 流程與標準 |
| 12 | `12_frontend_architecture_specification.md` | [`12_frontend_architecture.md`](./12_frontend_architecture.md) | pointer | 指向 `templates/design-system/specs/` |
| 13 | `13_security_and_readiness_checklists.md` | [`13_security_checklist.md`](./13_security_checklist.md) | skeleton | Pre-launch 安全與就緒檢查 |
| 14 | `14_deployment_and_operations_guide.md` | [`14_deployment_ops.md`](./14_deployment_ops.md) | skeleton | CI/CD + Runbook 範本 |
| 15 | `15_documentation_and_maintenance_guide.md` | [`15_documentation_guide.md`](./15_documentation_guide.md) | skeleton | 文件治理規範 |
| 16 | `16_wbs_development_plan_template.md` | [`16_wbs.md`](./16_wbs.md) | **FULL** | 雙軸 WBS：TRIZ Step 0-5 + TR0-TR10 |
| 17 | `17_frontend_information_architecture_template.md` | [`17_frontend_ia.md`](./17_frontend_ia.md) | pointer | 指向 `docs/01-define/pages/INDEX.md`（既有 18 頁規格） |
| 18 | — (自訂) | [`18_flow_contract.md`](./18_flow_contract.md) | **FULL v2.0** | RDP-8 統一框架：8 Phase + 8 Gate + 不確定性消除公理 |
| 19 | — (自訂) | [`19_internal_pitch_strategy.md`](./19_internal_pitch_strategy.md) | **FULL** | 面向非專案參與者的簡報策略：主敘事、10 頁頁綱、STRIKE prompts |
| 20 | — (自訂) | [`ppt/20_onepage_strike_prompt.md`](./ppt/20_onepage_strike_prompt.md) | **FULL** | 面向跨部門與內部技術架構受眾的 one-page STRIKE prompt |
| 21 | — (自訂) | [`ppt/21_onepage_slide_structure.md`](./ppt/21_onepage_slide_structure.md) | **FULL** | 面向跨部門與內部技術架構受眾的 one-page 簡報骨架 |
| 22 | — (自訂) | [`ppt/22_onepage_ppt_ready_copy.md`](./ppt/22_onepage_ppt_ready_copy.md) | **FULL** | 可直接貼進 PPT 的 one-page 文案版 |
| 23 | — (自訂) | [`ppt/23_onepage_leadership_summary.md`](./ppt/23_onepage_leadership_summary.md) | **FULL** | 面向主管 / 決策者的一頁式摘要 |
| 24 | — (自訂) | [`ppt/24_onepage_cross_team_tech_arch.md`](./ppt/24_onepage_cross_team_tech_arch.md) | **FULL** | 面向跨部門與內部技術架構的一頁式完整稿 |

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
| `docs/methodology/` | DK-01-05 方法論 KB | 02_prd 用 DK-01 流程，05_architecture 用 DK-02 機制 |
| `docs/methodology/auto_triz_strategy.md` | TRIZ 主策略 SSOT | 05_architecture 整合，16_wbs 雙軸引用 |
| `docs/engineering/` | TR0-10 工程執行範本 + **typed property graph SSOT**（YAML frontmatter）| 16_wbs 引用 TR Gate 框架；`tools/build_graph.py` 自動產生 `_graph.json` + mermaid 視圖（見 §6） |
| `docs/methodology/uml/` | 11 張流程 UML | 05_architecture 引用 |
| `docs/engineering/gate_reviews/` | TR Gate 實際產出 | 16_wbs 追蹤實際進度 |
| `templates/design-system/specs/` | 設計系統 6 份規格 | 12_frontend_architecture pointer |
| `templates/rd_設計文稿.md` | 原始 PRD 草稿 | 02_prd 收斂這份 |
| `.claude/skills/triz-*` | TRIZ 6 skill | 05_architecture §2 內部 AI 服務層 |
| `.claude/skills/tr-*` | TR 5 skill | 05_architecture §2，16_wbs 工具鏈 |
| `.claude/context/triz/.triz-state.json` | TRIZ session state | 16_wbs 追蹤 active session |
| `.claude/context/triz/.tr-state.json` | TR gate state | 16_wbs 追蹤 TR1 NO-GO 等 |

---

## 4. 閱讀順序建議

### 4.1 PM / 產品角色
1. [`02_prd.md`](./02_prd.md) — 產品定義
2. [`19_internal_pitch_strategy.md`](./19_internal_pitch_strategy.md) — 對內簡報 / 合作敘事模板
3. [`ppt/20_onepage_strike_prompt.md`](./ppt/20_onepage_strike_prompt.md) — one-page 簡報生成 prompt
4. [`ppt/21_onepage_slide_structure.md`](./ppt/21_onepage_slide_structure.md) — one-page 版面骨架
5. [`ppt/22_onepage_ppt_ready_copy.md`](./ppt/22_onepage_ppt_ready_copy.md) — 可直接貼進投影片的文案版
6. [`ppt/23_onepage_leadership_summary.md`](./ppt/23_onepage_leadership_summary.md) — 主管版摘要
7. [`ppt/24_onepage_cross_team_tech_arch.md`](./ppt/24_onepage_cross_team_tech_arch.md) — 跨部門技術架構版
8. [`16_wbs.md`](./16_wbs.md) — 進度與里程碑
9. [`03_bdd_guide.md`](./03_bdd_guide.md) — 用戶故事 ↔ BDD 對應
10. [`17_frontend_ia.md`](./17_frontend_ia.md) → 跳到 `docs/01-define/pages/INDEX.md`

### 4.2 技術負責人 / 架構師
1. [`02_prd.md`](./02_prd.md) §3 — 用戶故事
2. [`05_architecture.md`](./05_architecture.md) — 系統架構
3. [`04_adr/`](./04_adr/) — 關鍵決策記錄
4. [`06_api_spec.md`](./06_api_spec.md) — API 契約
5. [`12_frontend_architecture.md`](./12_frontend_architecture.md) → 跳到 `templates/design-system/specs/`

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
- **`docs/engineering/` 變動**：改完 frontmatter 後跑 `python3 tools/build_graph.py --inject` 重新產 mermaid 視圖（見 §6）

---

## 6. Graph 工具鏈（`docs/engineering/` 自動化）

`docs/engineering/` 下的 WI/ICD/MC 是 **typed property graph**（多類型節點 + 多類型邊 + 環）— 不是樹結構。為避免散文 cross-reference 漂移，採「frontmatter = SSOT、視圖 = 投影」設計。詳見 [`09_file_dependencies.md §3`](./09_file_dependencies.md) 與 [`15_documentation_guide.md §2.5`](./15_documentation_guide.md)。

**工具**：`tools/build_graph.py`（stdlib + PyYAML）

| 命令 | 用途 | 何時跑 |
|:-----|:-----|:------|
| `python3 tools/build_graph.py` | scan + lint + 產出 `docs/engineering/_graph.json` | 改 frontmatter 後 |
| `python3 tools/build_graph.py --inject` | 上述 + 重新渲染 README/risk_register/各 ego graph mermaid | 視圖需要更新時 |
| `python3 tools/build_graph.py --scaffold` | 自動在缺 marker 的 WI/ICD/MC 插入 `<!-- AUTO-GRAPH:START -->` | 新增 WI/ICD/MC 後 |
| `python3 tools/build_graph.py --strict` | 上述 + lint 失敗時 exit 1 | CI / pre-commit |

**架構決策**：見 [`04_adr/ADR-008_knowledge_graph_as_ssot.md`](./04_adr/ADR-008_knowledge_graph_as_ssot.md)。

---

## 7. 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-29 | v1.8 | 新增 §6「Graph 工具鏈」對齊 `tools/build_graph.py` 與 `docs/engineering/` frontmatter SSOT 工作流；§3 表格 `docs/engineering/` 行加 graph 註記；§5 加維護指引一條；新增 ADR-008 (Knowledge Graph as SSOT)。 |
| 2026-04-28 | v1.7 | 新增 `ppt/22_onepage_ppt_ready_copy.md`、`ppt/23_onepage_leadership_summary.md`、`ppt/24_onepage_cross_team_tech_arch.md`：補齊可直接貼進投影片、主管版、跨部門技術架構版 three-pack。 |
| 2026-04-28 | v1.6 | 新增 `ppt/20_onepage_strike_prompt.md` 與 `ppt/21_onepage_slide_structure.md`：面向跨部門與內部技術架構受眾的 one-page prompt 與簡報骨架。 |
| 2026-04-28 | v1.5 | 新增 19_internal_pitch_strategy：面向非專案參與者的簡報方向規劃，含主敘事、10 頁頁綱與 STRIKE prompt 模板。 |
| 2026-04-28 | v1.0 | 初版建立：6 份 FULL（02/03/05/06/16）+ 2 份 pointer（12/17）+ 10 份 skeleton（00/01/04/07-11/13-15） |
| 2026-04-28 | v1.1 | 08_project_structure 升 v2.0：發現先前 Clean Arch 提案與實際 backend（claude-code 風 harness）方向相反，完全覆寫對齊 M1-M4 現況。05/07/09/10 仍含 Clean Arch 用詞，待 follow-up 對齊。 |
| 2026-04-28 | v1.2 | F1+F3+F4 follow-up 完成：05_architecture v1.1（surgical：加現況/演化警告 + §1.1.2/1.2/1.3 改寫）、07/09/10 全面覆寫到 v2.0、新增 ADR-006 Production Persistence + ADR-007 Multi-tenancy。F2（前端目錄）與 F5（HARNESS_INTERNALS.md）留待後續。 |
| 2026-04-28 | v1.4 | docs/planning 全面對齊 Flow Contract：10 份文件加 gate 狀態標記、階段就緒度 tag、harness-first 語言替換（01/03/05/06/07/11/15/16/17 + 00）。 |
| 2026-04-28 | v1.3 | 新增 18_flow_contract.md：第一性原理分析 BDD→Skill 映射、Gate 層級審查（8→1 簡化）、擴展路線圖。triz-verify 增加 cad_readiness 區塊（Gate P 合併）。 |
