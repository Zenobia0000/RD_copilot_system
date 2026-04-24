---
description: TR 工程執行追蹤入口。顯示儀表板並路由到 gate review、FEA、測試、DFM 等 skill。
---

# TR 工程執行追蹤入口

載入 **tr-router** skill，顯示 TR 儀表板並路由到適當的工程執行步驟。

## 使用方式

```
/tr                        # 顯示儀表板 + 路由
/tr gate TR1               # 直接路由到 TR1 gate review
/tr fea WI-01              # 直接路由到 WI-01 FEA 輔助
```

## 覆蓋範圍

- TR1-TR10 gate review（`/tr-gate`）
- FEA 設定輔助（`/tr-fea`）
- 測試報告產生（`/tr-test`）
- DFM/DFA 審查（`/tr-dfm`）
