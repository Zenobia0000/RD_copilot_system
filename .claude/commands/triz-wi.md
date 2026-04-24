---
description: TRIZ Step 5 工程作業指導書。從 TRIZ 概念產出生成 WI 體系。
---

# TRIZ Step 5: 工程作業指導書 (WI) 產出

載入 **triz-wi** skill，從 TRIZ 概念產出生成工程作業指導書 (WI) 體系。

## 使用方式

```
/triz-wi                           # 根據當前 TRIZ session 產出全部 WI
/triz-wi motor gear                # 僅產出 motor 與 gear 領域 WI
/triz-wi --framework-only          # 僅產出框架文件（README、TR gate、critical path、risk register）
```

## 產出內容

1. **領域 WI** — 各子系統的工程作業指導書
2. **框架文件** — README、TR gate checklist、critical path、risk register
3. **追溯連結** — 從 WI 回溯到 TRIZ 解法方案與驗證結果
