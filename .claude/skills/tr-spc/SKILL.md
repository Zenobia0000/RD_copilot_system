---
name: tr-spc
description: TR SPC/Cpk 計算器。接收量測數據，計算 Xbar-R、Cp、Cpk、Ppk，判定製程能力是否達到 PPAP 要求。Use when measurement data needs statistical process capability analysis.
---

# TR SPC/Cpk 計算器

## Overview

本 skill 接收量測數據，計算 SPC 統計量（Xbar-R, Cpk, Ppk），判定製程能力是否達標。數據由使用者從外部量測系統提供，harness 負責計算和報告。

**宣告：** 「正在使用 tr-spc skill — 計算 {target} 的製程能力。」

**觸發時機**：TR9-TR10 階段，量產驗證。

---

## 輸入

```
/tr-spc KC-001              # 計算指定 KC 的 Cpk
/tr-spc all                  # 計算所有 KC 的 Cpk
/tr-spc summary              # 產出 SPC 總覽報告
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| KC-ID / all / summary | 是 | 目標 KC 或模式 |

---

## Phase 1: 載入 KC 規格

1. 讀取 `docs/engineering/kc_list.md`
2. 解析目標 KC 的：
   - **規格值**（nominal）
   - **上規格界限**（USL）和**下規格界限**（LSL）— 從公差推算
   - **管控等級**（Critical/Major/Minor）
3. 若 KC List 不存在，提示：「KC List 尚未產出。請先執行 `/triz-wi` 或手動建立 `docs/engineering/kc_list.md`。」

---

## Phase 2: 數據收集

引導使用者輸入量測數據：

```markdown
## {KC-ID}: {特徵名稱}

規格：{nominal} ± {tolerance}（USL = {usl}, LSL = {lsl}）

請提供量測數據：

| 項目 | 建議值 | 說明 |
|:-----|:-------|:-----|
| 樣本總數 (n) | ≥ 30 | PPAP 要求 |
| 子群大小 (k) | 5 | 連續取樣 |
| 量測值 | 逐筆或表格 | 可貼上 CSV 或空格分隔 |

數據格式範例：
- 逐行：`10.02 10.05 9.98 10.01 10.03 ...`
- CSV：直接貼上 Excel 複製的數據
- 子群格式：每行一個子群，空格分隔
```

### 數據驗證

收到數據後檢查：
- 樣本數 ≥ 5（最低要求），建議 ≥ 30
- 數據無明顯錯誤（如負值、量級異常）
- 若樣本數 < 30，警告：「樣本數 {n} < 30，Cpk 結果僅供參考，不符合 PPAP 正式要求。」

---

## Phase 3: 計算

### 基本統計量

- **Xbar**（總平均）= Σxi / n
- **R**（平均全距）= Σ(子群最大值 - 子群最小值) / 子群數
- **σ_within**（組內標準差）= R / d2（d2 依子群大小查表）
- **σ_overall**（整體標準差）= √(Σ(xi - Xbar)² / (n-1))

### d2 常數表

| 子群大小 | d2 |
|:---------|:---|
| 2 | 1.128 |
| 3 | 1.693 |
| 4 | 2.059 |
| 5 | 2.326 |
| 6 | 2.534 |
| 7 | 2.704 |
| 8 | 2.847 |
| 9 | 2.970 |
| 10 | 3.078 |

### 製程能力指標

- **Cp** = (USL - LSL) / (6 × σ_within)
- **Cpk** = min((USL - Xbar) / (3 × σ_within), (Xbar - LSL) / (3 × σ_within))
- **Pp** = (USL - LSL) / (6 × σ_overall)
- **Ppk** = min((USL - Xbar) / (3 × σ_overall), (Xbar - LSL) / (3 × σ_overall))

### 單邊規格處理

- 若只有 USL（無 LSL）：Cpk = (USL - Xbar) / (3 × σ_within)
- 若只有 LSL（無 USL）：Cpk = (Xbar - LSL) / (3 × σ_within)
- Cp 在單邊規格時不適用

---

## Phase 4: 判定

| Cpk 範圍 | 判定 | 說明 | 建議行動 |
|:---------|:-----|:-----|:---------|
| ≥ 1.67 | **優秀** | 製程能力充足 | 可考慮降低檢驗頻率 |
| 1.33 - 1.67 | **合格** | 達到 PPAP 要求 | 維持現行管控 |
| 1.00 - 1.33 | **邊緣** | 需改善 | 100% 檢驗 + 製程改善計劃 |
| < 1.00 | **不合格** | 製程能力不足 | 停線改善，不得出貨 |

### 製程偏移分析

- 若 Cp ≥ 1.33 但 Cpk < 1.33：**製程有偏移**，需調整中心值
- 若 Cp < 1.33 且 Cpk < 1.33：**製程散布過大**，需降低變異
- 若 Ppk ≠ Cpk（差異 > 0.1）：**製程不穩定**，有特殊原因變異

---

## Phase 5: 報告

輸出到 `docs/engineering/spc/KC-{id}_spc_{YYYY-MM-DD}.md`：

```markdown
# SPC 報告: {KC-ID} — {特徵名稱}

> **日期**: {YYYY-MM-DD}
> **子系統**: {subsystem}
> **規格**: {nominal} (USL = {usl}, LSL = {lsl})
> **判定**: {優秀 / 合格 / 邊緣 / 不合格}

---

## 數據摘要

| 統計量 | 值 |
|:-------|:---|
| 樣本數 (n) | {n} |
| 子群大小 (k) | {k} |
| 子群數 | {subgroups} |
| Xbar（平均） | {xbar} |
| σ_within | {sigma_w} |
| σ_overall | {sigma_o} |

## 製程能力指標

| 指標 | 值 | 判定 |
|:-----|:---|:-----|
| Cp | {cp} | {pass/fail} |
| **Cpk** | **{cpk}** | **{判定}** |
| Pp | {pp} | — |
| Ppk | {ppk} | — |

## 分析

{製程偏移分析、穩定性分析、建議行動}

## 數據明細

| 子群 | x1 | x2 | x3 | x4 | x5 | Xbar | R |
|:-----|:---|:---|:---|:---|:---|:-----|:--|
```

---

## Phase 6: 狀態更新

1. 更新 `.tr-state.json`：
   - 新增 `spc_results` 欄位（若不存在則建立）：
     ```json
     {
       "spc_results": {
         "KC-001": {
           "cpk": 1.45,
           "verdict": "合格",
           "date": "YYYY-MM-DD",
           "report": "docs/engineering/spc/KC-001_spc_YYYY-MM-DD.md"
         }
       }
     }
     ```

2. `summary` 模式：彙整所有已計算的 KC，產出總覽表到 `docs/engineering/spc/spc_summary_{YYYY-MM-DD}.md`

---

## 下一步導引

| 狀態 | 提示 |
|:-----|:-----|
| 全部 KC Cpk ≥ 1.33 | 「所有 KC 製程能力合格。執行 `/tr-ppap check` 檢查 PPAP 完整度。」 |
| 有 KC Cpk < 1.33 | 「{n} 個 KC 製程能力不足：{kc_list}。需製程改善後重測。」 |
| 有 KC 未量測 | 「{n} 個 KC 尚未量測：{kc_list}。執行 `/tr-spc {KC-ID}` 逐項補充。」 |

---

## 設計原則

### 域無關

KC 規格從 `kc_list.md` 動態讀取，不預設任何特徵類型或公差標準。同一 skill 可用於尺寸、力學性能、電氣參數等不同特徵。

### 計算透明

所有計算步驟和中間值都在報告中展示，便於工程師驗證。不使用黑盒計算。

### 數據來源外部

harness 不產生量測數據，只接收和計算。數據的準確性由使用者負責。
