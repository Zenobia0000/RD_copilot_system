---
description: FEA 設定輔助。提供材料卡、邊界條件、網格策略、結果判讀。
---

# TR FEA 設定輔助

載入 **tr-fea-assist** skill，輔助 FEA/CFD 分析的設定和結果判讀。

## 使用方式

```
/tr-fea WI-01              # AFM 磁路 FEA 設定
/tr-fea WI-02              # 諧波齒輪結構 FEA 設定
/tr-fea WI-03              # PCM 熱模擬設定
/tr-fea motor              # 以子系統名稱指定
/tr-fea result WI-01       # 判讀 FEA 結果
```

## 覆蓋域

- 電磁 (WI-01): Bg、扭矩、軸向力、loss map
- 結構 (WI-02, WI-04): von Mises、疲勞、接觸應力
- 熱流 (WI-03): 溫度場、PCM 相變、恢復時間
