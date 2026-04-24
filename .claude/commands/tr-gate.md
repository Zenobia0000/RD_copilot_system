---
description: TR Gate Review。逐項檢查退出條件，產出 Gate Review 報告。
---

# TR Gate Review

載入 **tr-gate** skill，對指定 TR gate 執行退出條件檢查並產出報告。

## 使用方式

```
/tr-gate TR1               # 執行 TR0→TR1 gate review
/tr-gate TR3               # 執行 TR2→TR3 gate review
/tr-gate TR1 motor         # 僅針對 motor 子系統
```

## 產出

- Gate Review 報告 → `docs/engineering/gate_reviews/TRn_review_YYYY-MM-DD.md`
- 判定：GO / CONDITIONAL GO / NO-GO
- 更新 `.tr-state.json` 子系統 TR 等級
