# 文件治理與維護指南 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Skeleton`
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
