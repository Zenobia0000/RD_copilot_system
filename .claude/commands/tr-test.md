---
description: 測試報告產生器。引導數據輸入、判定 pass/fail、FEA correlation。
---

# TR 測試報告

載入 **tr-test-report** skill，產出 V-test 和 DVP&R 測試報告。

## 使用方式

```
/tr-test V1                # V1 (AFM 靜態扭矩) 測試報告
/tr-test V5-V8             # Phase B (齒輪) 全部測試
/tr-test phase-A           # Phase A (馬達) 全部測試
/tr-test all               # 所有已完成測試
/tr-test dvpr              # DVP&R 總表 (TR9 用)
```

## 產出

- 測試報告 → `docs/engineering/test_reports/Vn_report_YYYY-MM-DD.md`
- DVP&R 總表 → `docs/engineering/test_reports/DVPR_YYYY-MM-DD.md`
- 風險狀態更新
