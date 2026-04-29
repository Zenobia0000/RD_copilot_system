# ICD-03: Drive Board ↔ Endcap（散熱 + EMI 屏蔽）

> **版本**: 1.0 | **日期**: 2026-04-28
> **相關 WI**: WI-05 (Drive Board), WI-04 (Housing/Endcap)
> **介面雙方**: 環形 PCB ↔ Al endcap

---

## 介面概述

```
                ┌──────────────────────┐
                │  Endcap (Al-6061)    │ ← 散熱 + 屏蔽
                ├──────────────────────┤
                │  TIM (thermal pad)   │
                ├──────────────────────┤
   ┌────────────┤  Annular PCB         ├────────────┐
   │MOSFET ×6  │  4 layers            │  Sensor IF │
   │(外環)     │  OD 105 / ID 30      │  (內環)    │
   └────────────┴──────────────────────┴────────────┘
                      ↑
                      mu-metal 屏蔽片（vs Halbach 漏磁）
```

## 配合規格

| 參數 | PCB 側 | Endcap 側 | 公差 |
|:-----|:-------|:----------|:-----|
| OD / ID | 105 / 30 mm | 配合 sink 105.2 / 30 (含間隙) | +0.1/0 |
| MOSFET 散熱面積 | 6× ~25 mm² | 6× 散熱柱 | — |
| TIM 厚度 | — | 0.5 mm 壓縮後 0.3 mm | ±0.1 |
| TIM 熱導率 | — | ≥ 6 W/mK | datasheet |
| mu-metal 屏蔽片 | — | 0.3 mm，OD 110 | 安裝在 PCB 與 rotor 間 |
| 螺絲固定 | M3×8 | 6 顆 | 扭矩 0.5 Nm |

## 熱路徑

```
MOSFET T_j → 焊點 → PCB Cu plane → TIM → Endcap Al → 外表面 ambient
```

預期：T_j_max 150°C / T_endcap < 80°C @ peak load

## EMI 屏蔽路徑

```
Halbach 漏磁 → mu-metal 屏蔽 → PCB ADC 訊號保護
PCB GND → endcap → housing GND → 騎乘車架 (chassis ground)
```

## GD&T

| 特徵 | 公差 |
|:-----|:-----|
| Endcap 散熱面平面度 | ≤ 0.1 mm（影響 TIM 接觸）|
| Endcap-PCB 螺絲孔位置度 | ≤ 0.2 mm |
| mu-metal 屏蔽片位置 | ±0.5 mm（安裝在 PCB 與 rotor 8mm 間隙） |

## 驗收條件

| 項目 | 方法 | 判定 |
|:-----|:-----|:-----|
| TIM 接觸 | 著色法 / pressure film | ≥ 80% 面積接觸 |
| EMI noise | scope @ ADC | < 5% signal |
| MOSFET T_j | embedded sensor / IR | < 150°C @ peak |
| 螺絲扭矩 | torque wrench | 0.5 Nm ±10% |

## 變更管控

- TIM 規格變更 → WI-05 + WI-04 簽核
- 屏蔽片厚度變更 → 重做 EMI 模擬
