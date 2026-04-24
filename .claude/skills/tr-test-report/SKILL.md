# TR 測試報告產生器

## Overview

本 skill 協助工程師產出測試報告，引導數據輸入、判定 pass/fail、執行 FEA correlation、更新風險狀態。**不內建任何測試項目或判定標準** — 全部從 WI-test 文件動態讀取。

**宣告：** 「正在使用 tr-test-report skill — 產出 {test_id} 測試報告。」

---

## 輸入

```
/tr-test V1                # 產出 V1 測試報告
/tr-test V5-V8             # 產出一組測試報告
/tr-test phase-A           # 產出指定 Phase 全部測試報告
/tr-test all               # 產出所有已完成測試的報告
/tr-test dvpr              # 產出 DVP&R 總表（TR9 用）
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| Vn / Vn-Vm / phase-X / all / dvpr | 是 | 目標測試項 |

---

## Phase 1: 載入測試規格（資料驅動）

1. 在 `docs/engineering/work_instructions/` 中尋找測試相關的 WI 文件
   - 搜尋策略：檔名包含 `test` / `prototype` / `驗證` 的 WI
   - 或從 `.tr-state.json` 的 `wi_status` 中找到 WI-test 類型
2. 讀取該 WI 文件，從中提取：
   - **測試矩陣**（V-test 列表、Phase 分組）
   - **每個 V-test 的規格**（方法、判定標準、設備需求）
   - **Phase 判定邏輯**（Phase pass/fail 條件、失敗對策）
3. 讀取 `.tr-state.json` 取得已有測試結果
4. 讀取 `docs/engineering/risk_register.md` 取得風險項對照

---

## Phase 2: 數據收集

引導使用者輸入實測數據。對每個 V-test：

```markdown
## V{n}: {test_name}（從 WI 讀取）

請提供以下實測數據：

| 需要資料 | 格式 | 範例 |
|:---------|:-----|:-----|
| {從 WI 測試規格推斷所需數據} | {format} | {example} |

測試條件:
- 日期: ___
- 設備: ___
- 環境溫度: ___°C
- 操作者: ___
- 備註: ___
```

**數據需求推斷規則：**
- WI 判定標準中有數值比較 → 需要該數值的實測值
- WI 方法描述中提到量測設備 → 需要量測數據
- WI 有「與 FEA 對比」要求 → 需要對應 FEA 預測值

---

## Phase 3: 判定

對每個 V-test，從 WI 提取的判定標準進行比較：

| 判定 | 條件 |
|:-----|:-----|
| **PASS** | 實測值滿足 WI 判定標準 |
| **MARGINAL** | 實測值在判定標準的 90-100% 範圍（接近邊界） |
| **FAIL** | 實測值未滿足判定標準 |

---

## Phase 4: FEA Correlation

對 WI 中標記「與 FEA 對比」的 V-test，計算偏差：

```
偏差 = |實測值 - FEA 值| / FEA 值 × 100%
```

| 偏差範圍 | 評估 | 動作 |
|:---------|:-----|:-----|
| ≤ 10% | 良好 | FEA 模型可信 |
| 10-20% | 可接受 | 記錄偏差原因，模型微調 |
| > 20% | **需修正** | 標紅，FEA 模型必須修正 |

---

## Phase 5: 產出報告

報告輸出到 `docs/engineering/test_reports/V{n}_report_{YYYY-MM-DD}.md`：

```markdown
# V{n} 測試報告: {test_name}

> **日期**: {test_date}
> **報告產出**: {YYYY-MM-DD}
> **判定**: {PASS / MARGINAL / FAIL}
> **對應 WI**: {wi_file}

---

## 測試條件

| 項目 | 內容 |
|:-----|:-----|
| 設備 | {equipment} |
| 環境溫度 | {temp}°C |
| 操作者 | {operator} |
| 日期 | {date} |

## 測試結果

| 量測項 | 實測值 | 判定標準 | 判定 |
|:-------|:-------|:---------|:-----|
| {metric} | {measured} | {criterion} | PASS/MARGINAL/FAIL |

## FEA Correlation（若適用）

| 參數 | FEA 預測 | 實測值 | 偏差 | 評估 |
|:-----|:---------|:-------|:-----|:-----|
| {param} | {fea} | {measured} | {delta}% | {assessment} |

## 觀察與建議

{測試過程觀察、異常現象、改善建議}

---

## 風險影響

| 風險 ID | 測試前狀態 | 測試後建議 | 理由 |
|:--------|:-----------|:-----------|:-----|
| {risk_id} | {before} | {after} | {reason} |
```

---

## Phase 6: DVP&R 總表（TR9 用）

當使用者輸入 `dvpr` 時，彙整所有 V-test + PV 測試為 DVP&R 總表：

```markdown
# DVP&R — Design Verification Plan & Report

> **產品**: {從 .tr-state.json 讀取 project_id}
> **日期**: {YYYY-MM-DD}

| # | 測試項目 | 規格 | 方法 | 樣本數 | Alpha 結果 | PV 結果 | 判定 |
|:--|:---------|:-----|:-----|:-------|:-----------|:--------|:-----|
```

Alpha 結果從已有的 V-test 報告讀取。PV 結果引導使用者輸入。

額外追加 `tr_gate_framework.md` 中 TR9→TR10 退出條件要求的測試項（耐久、環境、安全、防水等），引導使用者補充。

---

## 狀態更新

測試完成後更新 `.tr-state.json`：

1. **v_tests**: 更新狀態和結果
```json
{
  "V{n}": { "status": "tested", "result": "pass", "date": "YYYY-MM-DD", "report": "docs/engineering/test_reports/V{n}_report_YYYY-MM-DD.md" }
}
```

2. **risk_status**: 根據測試結果調整
   - V-test pass → 對應風險降級
   - V-test fail → 對應風險升級 + 標記 blocker

3. **subsystem_tr**: 若 Phase 全部 pass → 更新子系統 TR

---

## 下一步導引

| 狀態 | 提示 |
|:-----|:-----|
| Phase 全 pass | 「Phase {X} 全部通過。下一步: {根據 WI 中的 Phase 判定邏輯}。」 |
| 有 fail 項 | 「V{n} 未通過。{從 WI 讀取失敗對策}。修正後使用 `/tr-test V{n}` 重測。」 |
| 全部 V-test pass | 「全部通過！執行 `/tr-gate TR{n}` 進行 gate review。」 |
| DVP&R 完成 | 「DVP&R 全項通過。執行 `/tr-gate TR9` 進行量產驗證 gate review。」 |
