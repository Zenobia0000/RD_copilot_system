# Direction Terms — UI 名詞單一來源

> 版本：2026-05 (Glossary v1)
> 對應實作：
> - 資料源：[`src/components/create/directionTerms.ts`](../../src/components/create/directionTerms.ts)
> - 展示元件：[`src/components/create/DirectionTermsGlossary.tsx`](../../src/components/create/DirectionTermsGlossary.tsx)
> - 消費端：
>   - [`src/components/create/DirectionResultCard.tsx`](../../src/components/create/DirectionResultCard.tsx)
>   - [`src/components/create/DecisionCardPanel.tsx`](../../src/components/create/DecisionCardPanel.tsx) (`ContradictionManifest`)
> - 後端 enum 對應：
>   - [`backend/app/models/schemas.py`](../../backend/app/models/schemas.py)
>   - [`backend/app/prompts/triz_solver.py`](../../backend/app/prompts/triz_solver.py)
>   - [`backend/app/agents/triz_solver.py::RESOLUTION_STATUS_MULTIPLIER`](../../backend/app/agents/triz_solver.py)

---

## 1. 為什麼需要單一資料源

Create 頁「解矛盾」區塊大量使用顏色徽章 + 短標籤承載語意：

| 類別 | 種類數 | 對應後端型別 |
|---|---|---|
| Resolution Status | 5 | `ResolutionStatus` literal |
| Addresses Layer | 4 | `AddressesLayer` literal |
| Per-SR Verdict | 6 | `PerSrVerdict` literal |
| SR Kind | 4 | `SubRequirementKind` literal |
| Score Columns | 4 | `DirectionScore` 欄位 |
| Sort Mode | 4 | 純 UI 狀態 |
| Filter Mode | 4 | 純 UI 狀態 |
| Severity | 4 | `severity` 欄位 |

過去這些徽章的 label/顏色/說明散落在 3 個元件 + 後端 prompt，加一種新狀態要同步動 4 個檔。
本次重構把所有 UI 文案集中到 [`directionTerms.ts`](../../src/components/create/directionTerms.ts)，由 Card / Glossary / ContradictionManifest 共同消費。

---

## 2. 加新狀態的流程

假設要新增第 6 種 `ResolutionStatus = "needs_escalation"`：

1. **後端**：
   - [`schemas.py`](../../backend/app/models/schemas.py) 的 `ResolutionStatus` literal 加成員
   - [`triz_solver.py::RESOLUTION_STATUS_MULTIPLIER`](../../backend/app/agents/triz_solver.py) 補對應 multiplier
   - [`triz_solver.py` prompt](../../backend/app/prompts/triz_solver.py) `RESOLUTION_COVERAGE_AUDIT_PROMPT` 教 LLM 何時使用該狀態
2. **前端 type**：
   - [`src/types/directedTriz.ts`](../../src/types/directedTriz.ts) 的 `ResolutionStatus` literal 加成員
3. **前端文案（一個檔）**：
   - 在 [`directionTerms.ts`](../../src/components/create/directionTerms.ts) 的 `RESOLUTION_STATUS_TERMS` 加一筆，含 `label / className / description / example`
4. **完成** — `DirectionResultCard`、`DirectionTermsGlossary` 都自動讀到新狀態。

> ⚠ 不需要動 Glossary Sheet 元件本身，因為 `ResolutionStatusSection` 是用 `Object.entries(RESOLUTION_STATUS_TERMS)` 動態渲染。

---

## 3. UI 出口（給 RD 看的）

### 第 1 層：就地 Tooltip
- 5 色 Resolution Status 徽章、Addresses Layer 徽章、Per-SR Verdict 小圓點、SR Kind tag、Severity 徽章、4 個分數格、Sort / Filter 下拉
- 全部 hover 即出，內容來自 `directionTerms.ts` 的 `description` 欄位

### 第 2 層：「📖 名詞說明」拉桿
- 入口：[`DirectionResultCard`](../../src/components/create/DirectionResultCard.tsx) 卡頭右上方按鈕
- 元件：[`DirectionTermsGlossary`](../../src/components/create/DirectionTermsGlossary.tsx)
- 結構：右側 Sheet (`sm:max-w-md`) + Accordion 分 8 節
- 跨節錨點：分數格 / Sort / Filter 旁的 `?` icon 會直接開到對應節
- 狀態記憶：上次展開的節記 localStorage `directionGlossary.lastSection`

---

## 4. 設計哲學提醒

> **單一方向解掉幾條 SR ≠ 矛盾被解。**

`DirectionResultCard` 顯示的所有徽章、評語都是「方向級的閱讀背景」，
不是驗收條件。真正驗收要 RD 勾完方向 → 跨矛盾整併 →
[`EngineeringVerdictCard`](../../src/types/directedTriz.ts) Q1–Q8。

Glossary 的最後一節 `why_not_verdict` 就是強化這個概念，避免 RD 誤把
方向卡的「✓ 直接解決」徽章當作 ship-it signal。

---

## 5. 對照表（debug / handover 時可參照）

| UI 出現位置 | Glossary section id |
|---|---|
| 卡頭虛線框「矛盾說明書」+ SR 清單 | `manifest` |
| 方向卡標題列 5 色徽章 | `resolution_status` |
| 方向卡標題列「解根因 / 解機制 / 解症狀」 | `addresses_layer` |
| 展開方向後每條 SR 的小圓點 + 「本方案：✓ 直接解 ...」| `per_sr_verdict` |
| 展開方向後最上排 4 個分數格 | `score_columns` |
| 方向卡頂端「排序」/「篩選」下拉 | `sort_filter` |
| 卡頭右上嚴重度徽章（致命/主要/次要/未知）| `severity` |
| 為什麼這頁不是驗收 → 真正驗收在 VerdictCard | `why_not_verdict` |
