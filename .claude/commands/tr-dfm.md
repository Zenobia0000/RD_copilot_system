---
description: DFM/DFA 審查。依製程產出 checklist、BOM 驗證。
---

# TR DFM/DFA 審查

載入 **tr-dfm** skill，執行 DFM (Design for Manufacturability) 和 DFA (Design for Assembly) 審查。

## 使用方式

```
/tr-dfm shell              # AZ91D 殼體 DFM (壓鑄)
/tr-dfm gearbox            # CF-PEEK 剛輪 (射出) + CoCrMo 柔輪 (機加工)
/tr-dfm motor              # SMC 定子 (粉末壓制)
/tr-dfm all                # 全部子系統
/tr-dfm assembly           # DFA 組裝審查
/tr-dfm bom                # BOM 交叉驗證
```

## 覆蓋製程

- 壓鑄 (AZ91D): 壁厚、拔模角、澆口、氣密
- 射出 (CF-PEEK): 纖維方向、熔接線、收縮
- 機加工 (CoCrMo): 薄壁、齒形精度、熱處理
- SMC 壓制 (Somaloy): 密度均勻、脫模
