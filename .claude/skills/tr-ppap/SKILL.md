---
name: tr-ppap
description: TR PPAP 文件包組裝器。收集散落各處的 PPAP 18 項子文件，檢查完整度，產出組裝索引和缺口報告。Use when PPAP equivalent document package needs assembly or completeness audit.
---

# TR PPAP 文件包組裝器

## Overview

本 skill 組裝 PPAP 等效文件包。**不產出新的工程文件** — 收集已存在的交付物，檢查完整度，產出索引和缺口報告。唯一產出的新文件是 PSW（Part Submission Warrant）。

**宣告：** 「正在使用 tr-ppap skill — {check/assemble} PPAP 文件包。」

**觸發時機**：TR9-TR10 階段。

---

## 輸入

```
/tr-ppap check              # 檢查完整度（唯讀，不產出）
/tr-ppap assemble           # 組裝文件包 + 產出索引 + PSW
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| check / assemble | 是 | 模式選擇 |

---

## PPAP 18 項對照表

| # | PPAP Element | 對應檔案位置 | 產出 Skill | 類型 |
|:--|:-------------|:------------|:-----------|:-----|
| 1 | Design Records | `docs/engineering/work_instructions/WI-04*.md`（CAD 參考段落） | triz-wi | HARNESS |
| 2 | Engineering Change Docs | `docs/engineering/gate_reviews/` 中的 CONDITIONAL GO action items | tr-gate | HARNESS |
| 3 | Customer Engineering Approval | 外部 | — | EXTERNAL |
| 4 | Design FMEA | `docs/engineering/fmea/design_fmea*.md` 或 `docs/engineering/` 下含 "design_fmea" 的文件 | tr-gate 觸發產出 | HARNESS |
| 5 | Process Flow Diagram | `docs/engineering/sop/` 步驟序列（SOP 中的作業步驟表即為 PFD） | tr-sop | HARNESS |
| 6 | Process FMEA | `docs/engineering/fmea/process_fmea*.md` 或 `docs/engineering/` 下含 "process_fmea" 的文件 | tr-gate 觸發產出 | HARNESS |
| 7 | Control Plan | `docs/engineering/control_plan*.md` 或含 "control_plan" 的文件 | tr-gate 觸發產出 | HARNESS |
| 8 | MSA (GR&R) | `docs/engineering/test_reports/grr_*.md` | 外部數據 + tr-test | HYBRID |
| 9 | Dimensional Results | `docs/engineering/test_reports/` 中 Beta 原型尺寸報告 | tr-test | HARNESS |
| 10 | Material/Performance Test Results | `docs/engineering/test_reports/V*_report_*.md` | tr-test | HARNESS |
| 11 | Initial Process Studies (Cpk) | `docs/engineering/spc/spc_summary_*.md` 或 `docs/engineering/spc/KC-*_spc_*.md` | tr-spc | HARNESS |
| 12 | Qualified Lab Documentation | 外部 | — | EXTERNAL |
| 13 | Appearance Approval | 外部 | — | EXTERNAL |
| 14 | Sample Production Parts | 外部（實物） | — | EXTERNAL |
| 15 | Master Sample | 外部（實物） | — | EXTERNAL |
| 16 | Checking Aids | 外部（量具/治具） | — | EXTERNAL |
| 17 | Customer-Specific Requirements | 外部 | — | EXTERNAL |
| 18 | Part Submission Warrant (PSW) | `docs/engineering/ppap/psw_{YYYY-MM-DD}.md` | **本 skill 產出** | HARNESS |

---

## Phase 1: 掃描

逐項檢查 18 項文件：

1. 對每個 HARNESS/HYBRID 項，按「對應檔案位置」搜尋 `docs/engineering/` 目錄
2. 檢查策略：
   - **存在性**：檔案是否存在
   - **非空性**：檔案大小 > 0
   - **基本完整性**：檔案是否有預期的結構標記（如表頭、段落標題）
3. 對 EXTERNAL 項，檢查 `.tr-state.json` 是否有對應的 `external_docs` 記錄

---

## Phase 2: 完整度報告

產出完整度報告（`check` 和 `assemble` 模式都執行）：

```markdown
# PPAP 文件包完整度報告

> **日期**: {YYYY-MM-DD}
> **專案**: {從 .tr-state.json 讀取 project_id}

## 完整度總覽

| 狀態 | 數量 | 比例 |
|:-----|:-----|:-----|
| ✅ COMPLETE | {n} | {pct}% |
| ⚠️ PARTIAL | {n} | {pct}% |
| ❌ MISSING | {n} | {pct}% |
| ⏸ EXTERNAL | {n} | {pct}% |

## 逐項檢查

| # | PPAP Element | 狀態 | 檔案路徑 | 備註 |
|:--|:-------------|:-----|:---------|:-----|
| 1 | Design Records | {status} | {path} | {note} |
| 2 | Engineering Change Docs | {status} | {path} | {note} |
...
| 18 | PSW | {status} | {path} | {note} |

## 缺口清單（Action Required）

| # | 缺口 | 建議行動 | 對應指令 |
|:--|:-----|:---------|:---------|
| 1 | {gap} | {action} | `/tr-{skill} {args}` |
```

**狀態判定規則：**

| 狀態 | 定義 |
|:-----|:-----|
| ✅ COMPLETE | 文件存在、非空、結構完整 |
| ⚠️ PARTIAL | 文件存在但結構不完整（缺少預期段落）或標記為草稿 |
| ❌ MISSING | 文件不存在或為空 |
| ⏸ EXTERNAL | 需外部資源，harness 無法產出（不計入缺口） |

`check` 模式到此結束，輸出報告後結束。

---

## Phase 3: PSW 產出（僅 `assemble` 模式）

產出 Part Submission Warrant，彙整所有已完成項的摘要。

輸出到 `docs/engineering/ppap/psw_{YYYY-MM-DD}.md`：

```markdown
# Part Submission Warrant (PSW)

> **日期**: {YYYY-MM-DD}
> **專案**: {project_id}
> **提交等級**: Level 3（含支持文件）

---

## 零件資訊

| 項目 | 內容 |
|:-----|:-----|
| 零件名稱 | {從 .tr-state.json 或 README 讀取} |
| 零件編號 | {若有} |
| 設計變更等級 | {從 gate_reviews 推導} |
| 圖面日期 | {最新 WI 日期} |
| 供應商 | {從 .tr-state.json 讀取} |

## 提交文件清單

| # | PPAP Element | 狀態 | 附件引用 |
|:--|:-------------|:-----|:---------|
| 1 | Design Records | {status} | {path} |
...
| 18 | PSW | ✅ | 本文件 |

## 聲明

本 Part Submission Warrant 確認：
- 以上列出的零件和材料符合所有適用的設計規格和工程要求
- 初始製程研究（Cpk）結果達到客戶要求
- 所有測試結果在規格範圍內

**簽核區（待人工填寫）：**

| 角色 | 姓名 | 簽名 | 日期 |
|:-----|:-----|:-----|:-----|
| 供應商品質代表 | ___ | ___ | ___ |
| 客戶品質代表 | ___ | ___ | ___ |
```

---

## Phase 4: 索引產出（僅 `assemble` 模式）

產出文件包索引到 `docs/engineering/ppap/ppap_index_{YYYY-MM-DD}.md`：

```markdown
# PPAP 文件包索引

> **日期**: {YYYY-MM-DD}
> **PSW**: [psw_{YYYY-MM-DD}.md](./psw_{YYYY-MM-DD}.md)
> **完整度**: {complete_count}/18 ({pct}%) — EXTERNAL 項 {ext_count} 個不計入

## 文件目錄

| # | Element | 檔案路徑 | 版本 | 日期 |
|:--|:--------|:---------|:-----|:-----|
| 1 | Design Records | {relative_path} | {ver} | {date} |
...
```

---

## Phase 5: 狀態更新

更新 `.tr-state.json`：
- 新增 `ppap` 欄位（若不存在則建立）：
  ```json
  {
    "ppap": {
      "last_check": "YYYY-MM-DD",
      "complete_count": 12,
      "total_harness": 11,
      "total_external": 7,
      "missing": ["item3", "item8"],
      "psw_file": "docs/engineering/ppap/psw_YYYY-MM-DD.md",
      "index_file": "docs/engineering/ppap/ppap_index_YYYY-MM-DD.md"
    }
  }
  ```

---

## 下一步導引

| 狀態 | 提示 |
|:-----|:-----|
| 全部 HARNESS 項 COMPLETE | 「PPAP harness 項全部完成。剩餘 {n} 個 EXTERNAL 項需外部提供。」 |
| 有 MISSING 項 | 「{n} 項缺口需補完：{gap_list}。建議優先執行：{top_action}。」 |
| PSW 已產出 | 「PSW 已產出，待人工簽核。完成後可執行 `/tr-gate TR10` 進行量產釋放 gate review。」 |

---

## 設計原則

### 不重複產出

本 skill 不產出 FMEA、Control Plan、測試報告等文件 — 這些由對應 skill 負責。本 skill 只做**收集、檢查、組裝**。

### 域無關

18 項對照表的搜尋路徑使用模式匹配（如 `*fmea*`、`*control_plan*`），不硬編碼具體檔名。

### EXTERNAL 項透明

EXTERNAL 項不計入完整度百分比，但在報告中清楚列出，讓使用者知道還需要什麼外部資源。
