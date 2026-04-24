# TR Gate Reviewer — 通用 Gate Review

## Overview

本 skill 是參數化的 Gate Reviewer，支援所有 TR0→TR10 gate review。讀取 `tr_gate_framework.md` 的退出條件，逐項檢查交付物，產出 Gate Review 報告。

**宣告：** 「正在使用 tr-gate skill — 執行 TR{n} Gate Review。」

---

## 輸入

```
/tr-gate TR1              # 執行 TR0→TR1 gate review
/tr-gate TR3              # 執行 TR2→TR3 gate review
/tr-gate TR1 motor        # 僅針對 motor 子系統的 TR1 review
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| TRn | 是 | 目標 gate (TR1-TR10) |
| subsystem | 否 | 指定子系統（預設：全部） |

---

## 行為

### Phase 1: 載入退出條件

1. 讀取 `docs/engineering/tr_gate_framework.md`
2. 找到目標 gate 的 Gate Review 檢查清單（`TR{n-1} → TR{n} Gate Review`）
3. 解析每一項退出條件為 checklist item

### Phase 2: 逐項檢查

對每項退出條件：

```
退出條件 → 對應交付物 → 存在？ → 內容 pass？
```

**檢查邏輯：**

| 交付物類型 | 檢查方式 |
|:-----------|:---------|
| WI FEA 結果 | 讀取 WI 文件，檢查是否有 FEA 結果段落且數值 pass |
| Material Card | 檢查 `docs/engineering/material_cards/MC-xx.md` 是否存在且有完整數據 |
| ICD | 檢查 `docs/engineering/interface_control/ICD-xx.md` 是否存在且已簽核 |
| Risk Register | 讀取 `docs/engineering/risk_register.md`，檢查 showstopper 風險狀態 |
| V-test 結果 | 讀取 `.tr-state.json` 的 `v_tests` 欄位 |
| FMEA | 檢查 FMEA 文件是否存在（TR3: Design FMEA, TR7: Process FMEA） |
| Control Plan | 檢查 Control Plan 文件是否存在（TR7: 初版, TR8: 驗證, TR10: 最終版） |
| 供應商確認 | 檢查 `.tr-state.json` 或相關文件中的供應商記錄 |

### Phase 3: 風險檢查

1. 讀取 `docs/engineering/risk_register.md`
2. 識別所有狀態為 `open` 且等級為「高」的風險
3. 判斷是否為 showstopper（會阻擋目標 gate 通過）

### Phase 4: 判定

| 條件 | 判定 | 說明 |
|:-----|:-----|:-----|
| 所有退出條件 pass，無 showstopper | **GO** | 通過，進入下一階段 |
| ≥80% 退出條件 pass，剩餘有明確計畫 | **CONDITIONAL GO** | 有條件通過，附帶 action items |
| <80% pass 或有 showstopper | **NO-GO** | 不通過，列出未完成項 |

### Phase 5: 產出報告

報告輸出到 `docs/engineering/gate_reviews/TR{n}_review_{YYYY-MM-DD}.md`：

```markdown
# TR{n-1} → TR{n} Gate Review Report

> **日期**: {YYYY-MM-DD}
> **目標 Gate**: TR{n} ({gate_name})
> **判定**: {GO / CONDITIONAL GO / NO-GO}
> **TRIZ Session**: {triz_session_ref}

---

## 退出條件檢查

| # | 退出條件 | 狀態 | 證據 | 備註 |
|:--|:---------|:-----|:-----|:-----|
| 1 | {condition} | PASS/FAIL/N/A | {evidence_ref} | {note} |
| 2 | {condition} | PASS/FAIL/N/A | {evidence_ref} | {note} |
...

### 通過率

- **總項目**: {total}
- **PASS**: {pass_count} ({pass_pct}%)
- **FAIL**: {fail_count}
- **N/A**: {na_count}

---

## 風險評估

### Showstopper 風險

| 風險 ID | 描述 | 等級 | 狀態 | 影響 |
|:--------|:-----|:-----|:-----|:-----|
| {id} | {desc} | {level} | {status} | {impact} |

### 其他 Open 風險

| 風險 ID | 描述 | 等級 | 狀態 |
|:--------|:-----|:-----|:-----|
| {id} | {desc} | {level} | {status} |

---

## 判定理由

{判定為 GO/CONDITIONAL GO/NO-GO 的具體理由}

### Action Items（CONDITIONAL GO 時必填）

| # | Action | 負責 | 期限 | 追蹤 |
|:--|:-------|:-----|:-----|:-----|
| 1 | {action} | {owner} | {deadline} | {tracking} |

---

## 子系統 TR 更新建議

| 子系統 | 現在 TR | 建議更新至 | 理由 |
|:-------|:--------|:-----------|:-----|
| {name} | {current} | {proposed} | {reason} |

---

## 附件

- Gate checklist 來源: `docs/engineering/tr_gate_framework.md`
- Risk Register: `docs/engineering/risk_register.md`
- TRIZ Session: `.claude/context/triz/.triz-state.json`
```

### Phase 6: 更新狀態

1. 更新 `.tr-state.json`：
   - `gate_reviews` 陣列追加新記錄
   - 若判定 GO：更新相關子系統的 `current` TR 等級
   - 更新 `risk_status`（若有風險狀態變化）

2. Gate review 記錄格式：
```json
{
  "gate": "TR1",
  "date": "2026-MM-DD",
  "verdict": "GO | CONDITIONAL GO | NO-GO",
  "pass_rate": 0.85,
  "report_file": "docs/engineering/gate_reviews/TR1_review_2026-MM-DD.md",
  "action_items": []
}
```

---

## Gate-Specific 檢查重點（資料驅動）

以下為各 gate 的重點檢查邏輯，實際 checklist 項目從 `tr_gate_framework.md` 動態讀取：

| Gate | 重點交付物 | 特殊檢查 |
|:-----|:-----------|:---------|
| TR0→TR1 | WI-01/02/03 FEA, MC×6 | Loss map 交付鏈：WI-01 → WI-03 |
| TR1→TR2 | 軸承選型, ICD×4 | 供應商 nominated + 能力確認 |
| TR2→TR3 | 3D CAD, BOM, GD&T | Design FMEA 完成 |
| TR3→TR5 | WI-07 物料, 治具 | 原型 vs 量產 BOM 差異記錄 |
| TR5→TR6 | V1-V14 實測 | FEA vs 實測偏差 <20% |
| TR6→TR7 | Alpha issue list | Design FMEA 更新 |
| TR7→TR8 | DFM review, BOM | Process FMEA + Control Plan 初版 |
| TR8→TR9 | Beta 尺寸+功能 | Control Plan 驗證 |
| TR9→TR10 | DVP&R, PV, Cpk | PPAP 等效文件包 |

---

## 下一步導引

| 判定 | 提示 |
|:-----|:-----|
| GO | 「TR{n} Gate Review **通過**。子系統 TR 已更新。下一個目標: TR{n+1}。執行 `/tr` 查看更新後的儀表板。」 |
| CONDITIONAL GO | 「TR{n} Gate Review **有條件通過**。{count} 項 action items 需完成。執行 `/tr` 追蹤進度。」 |
| NO-GO | 「TR{n} Gate Review **未通過**。{fail_count} 項退出條件未滿足。建議優先處理: {top_blocker}。」 |
