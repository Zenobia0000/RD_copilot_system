# Code Review 與 Refactoring 指南 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Skeleton`
**模板來源**：`templates/vibecoding/11_code_review_and_refactoring_guide.md`

---

## 1. PR 提交前 self-review checklist

- [ ] 對應 BDD scenario？（[`03_bdd_guide.md`](./03_bdd_guide.md)）
- [ ] 通過所有測試（unit + integration + 對應 BDD）
- [ ] Lint + Type check 全綠
- [ ] 無 console.log / print debug 殘留
- [ ] 無 `any` / `# type: ignore`（有則寫理由註解）
- [ ] 模組依賴未產生循環（[`09_file_dependencies.md`](./09_file_dependencies.md)）
- [ ] 新增/修改 token 對齊 [`templates/design-system/specs/00_foundations_spec.md`](../../templates/design-system/specs/00_foundations_spec.md)
- [ ] PR 大小 < 400 行（超過拆分）
- [ ] commit message 含 WHY/WHAT/IMPACT 三段

---

## 2. Review 重點

### 2.1 程式碼品質

- 無 magic number（用 token / constant）
- 函式 < 50 行、< 3 層縮排
- 命名語意化（不縮寫除非公認）
- Edge case / null / error 都已處理

### 2.2 架構與設計

- Skill（業務邏輯）不依賴特定 Tool 實作（harness-first 原則，見 [`08_project_structure.md`](./08_project_structure.md) v2.1）
- 基礎設施 Tool 放 `app/harness/tools/`；域特定 Tool 放 `app/<domain>/tools.py`（如 `app/triz/tools.py`）
- LLM 呼叫由 AgentLoop 統一處理，不另設 LLMProvider 介面
- HTTP 層目前 in-memory；遷移到 DB 持久化為 [ADR-006](./04_adr/ADR-006_production_persistence.md) 範疇（未實作）

### 2.3 性能與安全

- N+1 query 檢查
- 大資料用分頁 / 虛擬化
- 用戶輸入經過 Pydantic / Zod 驗證
- 無 SQL injection / XSS 風險（OWASP Top 10）

### 2.4 測試

- BDD scenario 必有對應 test
- Coverage：unit ≥ 80%、component ≥ 70%
- E2E 含 happy + 1 個 sad path

---

## 3. Refactoring 時機

| 訊號 | 動作 |
|:-----|:-----|
| 重複 3 次 | Extract function/component |
| 函式 > 50 行 | Extract method |
| 元件 > 200 行 | Extract sub-component |
| Magic number | Extract token / constant |
| if/else > 3 層 | 重新設計資料結構 |
| 出現 `// FIXME` 超過 1 個 sprint | 寫成 risk register 條目並排程 |

---

## 4. PR 模板

```markdown
## Summary
1-3 句話：解決什麼問題

## Changes
- [ ] 主要變更 1
- [ ] 主要變更 2

## BDD Scenario
對應 `features/X.feature::Scenario_Name`

## Test Plan
- [ ] Unit tests pass
- [ ] BDD scenario pass
- [ ] Manual test：步驟...

## Screenshots / Videos（前端 PR 必填）

## Breaking Changes / Migration
（若有）
```

---

## 5. Feedback 框架

```
✅ Praise：先寫好的部分
🤔 Question：澄清而非命令（"你考慮過 X 嗎？" vs "改成 X"）
💡 Suggestion：標註為 nit / non-blocking 或 must-fix
🚨 Block：違反規範、安全風險、Breaking Change
```

---

## 文件溯源

- 模板：`templates/vibecoding/11_code_review_and_refactoring_guide.md`
- 對應：[`03_bdd_guide.md`](./03_bdd_guide.md), [`05_architecture.md`](./05_architecture.md)
