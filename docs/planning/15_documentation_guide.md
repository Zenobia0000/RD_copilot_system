# 文件治理與維護指南 — RD Design Copilot

---

**文件版本**：`v1.1`（新增 §2.5 Frontmatter Convention）
**最後更新**：`2026-04-29`
**狀態**：`Skeleton + Frontmatter SSOT 規範已收錄`
**模板來源**：`templates/vibecoding/15_documentation_and_maintenance_guide.md`

---

## 1. 文件類型總表

| 類別 | 用途 | 位置 | 受眾 |
|:-----|:-----|:-----|:-----|
| **Planning Docs**（本目錄） | 18 份 VibeCoding 模板實例 | `docs/planning/` | All teams |
| **Product IA & Pages** | 18 頁產品規格 | `docs/01-define/pages/` | PM / FE / QA |
| **Domain Knowledge** | DK-01-05 方法論 | `docs/methodology/` | All（培訓） |
| **TRIZ Strategy** | 策略 SSOT、UML、engineering 範本 | `docs/methodology/` | TL / TRIZ-SME / RD |
| **Engineering Outputs** | 工程交付物（WI/ICD/MC/Gate） | `docs/engineering/` | RD / 工程師 |
| **API Docs** | OpenAPI 自動產出 | Swagger UI（runtime） | FE / 整合方 |
| **Code Docs** | docstring + JSDoc | 程式碼內 | Dev |
| **Design System** | Atomic Design 規格 | `templates/design-system/specs/` | Design / FE |
| **Skill Specs** | TRIZ / TR skill 規格 | `.claude/skills/*/SKILL.md` | AI / TL |
| **State / Session** | TRIZ / TR session state | `.claude/context/triz/` | Skill 內部 |

---

## 2. 內容位置邊界政策（引用 `.claude/CLAUDE.md`）

| 內容性質 | 產出者 | 消費者 | 存放位置 |
|:---------|:-------|:-------|:---------|
| Session 過程記錄 | Skill | Skill | `.claude/context/triz/session-*.md` |
| 流程狀態（TRIZ） | Skill | Skill | `.claude/context/triz/.triz-state.json` |
| 流程狀態（TR） | Skill | Skill | `.claude/context/triz/.tr-state.json` |
| 工程交付物 | Skill（triz-wi） | 工程師（人） | `docs/engineering/` |
| 方法論知識庫 | 人 | Skill（參考） | `docs/methodology/` |
| Gate review 報告 | Skill（tr-gate） | 工程師（人） | `docs/engineering/gate_reviews/` |
| 測試報告 | Skill（tr-test） | 工程師（人） | `docs/engineering/test_reports/` |
| DFM 審查報告 | Skill（tr-dfm） | 工程師（人） | `docs/engineering/dfm_reviews/` |

**核心原則**：
1. Skill 產出、Skill 消費 → `.claude/context/`
2. Skill 產出、人消費 → `docs/engineering/`
3. 人撰寫、Skill 參考 → `docs/methodology/` 或 `knowledge/triz/`
4. **狀態 JSON 只能由 Skill（透過 TrizState{Read,Write,Advance} Tool）修改，不可手動編輯** — 手動編輯會破壞 schema 驗證與 step advance guard rails

---

## 2.5 Frontmatter Convention（Engineering Outputs）

`docs/engineering/` 下的 WI/ICD/MC 是 **typed property graph** 的節點（見 [`09_file_dependencies.md §3`](./09_file_dependencies.md)）。每個檔案頂部 YAML frontmatter 是 **single source of truth**；mermaid 視圖、`_graph.json`、CI lint 全部從 frontmatter 推導。

### 2.5.1 通用必填欄位

| 欄位 | 型別 | 說明 |
|:-----|:-----|:-----|
| `id` | string | 全 graph 唯一，格式 `<TYPE>-NN`（WI-01、ICD-03、MC-06） |
| `type` | enum | `WI` / `ICD` / `MC` |
| `title` | string | 一句話標題（mermaid 節點標籤會用此）|
| `version` | string | SemVer，初版 `1.0` |
| `date` | YYYY-MM-DD | 建立或最後一次重大修改 |

### 2.5.2 WI 額外欄位

| 欄位 | 型別 | 必填 | 說明 |
|:-----|:-----|:----:|:-----|
| `domain` | string | ✓ | electromagnetic / mechanical / thermal / structural / electronics / test / procurement |
| `role` | enum | — | `cross-cutting`（橫切性 WI 例外 NO-TRACE lint） |
| `owner` | string | ✓ | EE / ME / ME-Thermal / EE-FW / QA / SCM |
| `effort_weeks` | number / "ongoing" | ✓ | 預估工時 |
| `traces_to` | list[ID] | ✓ * | TC / SOL / Principle 列表（* `cross-cutting` WI 可省）|
| `cites` | list[Claim ID] | — | 引用 Evidence Registry 條目（C-A001 等） |
| `uses` | list[MC ID] | — | 使用的材料卡 |
| `feeds` | list[obj] | — | 下游 WI（含 `target` / `artifact` / `purpose`） |
| `depends_on` | list[obj] | — | 上游 WI（同上格式） |
| `supports_icd` | list[ICD ID] | — | 支援的介面 |
| `mitigates` | list[Risk ID] | — | 關閉的 Risk |
| `satisfies_gates` | list[TR ID] | — | 滿足的 TR Gate |

### 2.5.3 ICD 額外欄位

| 欄位 | 必填 | 說明 |
|:-----|:----:|:-----|
| `links` | ✓ | 連結的 WI（雙向關係的「ICD 端」聲明） |
| `mitigates` | — | 關閉的 Risk |

### 2.5.4 MC 額外欄位

| 欄位 | 必填 | 說明 |
|:-----|:----:|:-----|
| `material_class` | ✓ | permanent_magnet / soft_magnetic_composite / composite / aluminum_alloy / copper / phase_change / ... |
| `cites` | ✓ | 引用 Evidence（C-NNN）|
| `used_by` | — | WI 列表（uses 的反向，書寫便利）|
| `mitigates` | — | 關閉的 Risk |

### 2.5.5 完整範例（WI-01）

```yaml
---
id: WI-01
type: WI
title: Halbach NdFeB 馬達 + SMC Stator + CFRP 套筒
domain: electromagnetic
version: 1.0
date: 2026-04-28
effort_weeks: 6
owner: EE/ME

traces_to:
  - TC-B           # 功率密度 vs 重量
  - SOL-TCB
  - principle:14   # 曲面化 (Halbach)
  - principle:40   # 複合材料 (CFRP)

cites:
  - C-B001         # NdFeB N42SH B_r=1.32 T (HIGH)
  - C-B002         # Halbach +30~40% (MEDIUM, 待 FEA)
  - C-B003         # SMC sat=1.6 T (HIGH)
  - C-B004         # CFRP tip speed (LOW, 待 datasheet)

uses: [MC-01, MC-02, MC-03]

feeds:
  - target: WI-03
    artifact: Loss map (CSV)
    purpose: thermal CFD 邊界條件
  - target: WI-04
    artifact: 馬達包絡尺寸
    purpose: housing 設計輸入

supports_icd: [ICD-01]
mitigates: [R-001, R-004, R-005]
satisfies_gates: [TR1, TR2, TR3, TR5, TR6]
---
```

### 2.5.6 驗證指令（必跑）

每次改完 frontmatter，跑：

```bash
python3 tools/build_graph.py --strict
```

Lint clean 才能 commit。常見失敗：

| 訊息 | 修法 |
|:-----|:-----|
| `[NO-TRACE] WI-XX has no traces_to` | 補 `traces_to` 或加 `role: cross-cutting` |
| `[OPEN-RISK] R-XXX` | 確認某 WI 的 `mitigates` 列表含此 Risk |
| `[LOW-CLAIM] C-XXX` | 補實證或在 risk_register.md 增列風險條目 |
| `[NO-FRONTMATTER] WI-XX...` | 補完整 frontmatter（參考 §2.5.5）|
| `[YAML ERROR]` | YAML 語法錯（多半是縮排或冒號後空格） |

### 2.5.7 視圖注入（請勿手寫 mermaid）

frontmatter 是 SSOT，mermaid 視圖**不可手寫**，由：

```bash
python3 tools/build_graph.py --inject
```

自動產生並注入 `<!-- AUTO-GRAPH:START view=... -->` 與 `<!-- AUTO-GRAPH:END -->` 之間。手寫視圖會在下次 inject 被覆寫。

完整工具行為見 [`09_file_dependencies.md §3`](./09_file_dependencies.md)；架構決策見 [`04_adr/ADR-008_knowledge_graph_as_ssot.md`](./04_adr/ADR-008_knowledge_graph_as_ssot.md)。

---

## 3. Living Documentation 流程

| 文件 | 變更觸發 | 同步方式 |
|:-----|:---------|:---------|
| 02_prd | PM 編輯 | 手動 + PR review |
| 03_bdd_guide | 新 user story 加入 | 手動 + PR |
| OpenAPI | code annotation | FastAPI auto-gen |
| Frontmatter index | page spec frontmatter 變更 | 半自動（INDEX.md 重建） |
| Storybook | 元件變更 | auto on PR merge |
| Changelog | release | 自動（commitlint + standard-version） |

---

## 4. 文件撰寫風格

- **Markdown 優先**（除非要 mermaid / table 才用其他）
- **Style guide**：每章一句話開頭、然後 bullet
- **詞彙統一**：用 PRD / Skill spec 中的詞（TC/PC/SF/CCI/Gate — 見 [`18_flow_contract.md §2`](./18_flow_contract.md) Gate 層級分析）
- **語言**：繁體中文為主、技術術語保留英文
- **Code block** 標明語言

---

## 5. 文件版本控制

```
SemVer：MAJOR.MINOR.PATCH
- MAJOR：結構性重組（如本次 design-system v2.0）
- MINOR：新增章節
- PATCH：修正錯字、小調整
```

---

## 6. Knowledge Base 與 FAQ

- 公開 KB：`docs/methodology/`
- 內部 FAQ：v2 規劃 Confluence / Notion
- 問答彙整：每 sprint 結束彙整 P0 用戶問答 → 加入 KB

---

## 7. Onboarding 培訓

| 角色 | 必讀 | 預估時間 |
|:-----|:-----|:---------|
| 新 PM | 02 PRD + 03 BDD + 16 WBS | 2 hr |
| 新 TL | 02 + 04 ADRs + 05 Arch + 06 API | 4 hr |
| 新 BE | 05 + 07 + 08 + 11 | 3 hr |
| 新 FE | design-system + 01-define/pages + 12 + 17 | 4 hr |
| 新 QA | 03 + 07 + 13 | 2 hr |
| 新 SRE | 13 + 14 | 2 hr |
| 新 RD-User | DK-01-05 + 02 PRD §3 | 2 hr |

---

## 8. Post-Mortem 與經驗累積

- 每次 Incident 寫 [`14_deployment_ops.md §10`](./14_deployment_ops.md) 模板
- 收進 `docs/methodology/postmortems/`
- Quarterly review

---

## 9. 文件維護 Checklist（季度）

- [ ] 各文件「Last Updated」是否在過去 6 月內？（過期 = warning）
- [ ] frontmatter / metadata 一致性（如 page spec spec_version）
- [ ] 內部連結是否仍 resolve？（用 link checker）
- [ ] Outdated screenshot / video 重拍
- [ ] Glossary 詞彙與最新 spec 同步

---

## 文件溯源

- 模板：`templates/vibecoding/15_documentation_and_maintenance_guide.md`
- 政策：`.claude/CLAUDE.md` 內容位置邊界（lines 93-121）
- §2.5 對齊：[`09_file_dependencies.md §3`](./09_file_dependencies.md)、`tools/build_graph.py`、[`04_adr/ADR-008_knowledge_graph_as_ssot.md`](./04_adr/ADR-008_knowledge_graph_as_ssot.md)

---

## 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-29 | v1.1 | 新增 §2.5 Frontmatter Convention：完整 schema（WI/ICD/MC 各別欄位）+ WI-01 範例 + `build_graph.py --strict` 驗證指引 + lint 訊息對照表。 |
| 2026-04-28 | v1.0 | 初版（VibeCoding template skeleton）|
