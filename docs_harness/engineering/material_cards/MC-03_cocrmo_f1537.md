# MC-03: CoCrMo Wrought ASTM F1537 (Flex Spline)

> **版本**: 1.0 | **日期**: 2026-04-21
> **來源**: Evidence C-005 from TRIZ session
> **適用 WI**: WI-03
> **FEA 軟體**: ANSYS Mechanical, COMSOL Structural Mechanics, Abaqus

---

## 材料概述

鈷鉻鉬 (CoCrMo) 鍛造合金，ASTM F1537 Condition 1（熱加工 + 固溶退火態）。原為醫療器材等級（人工關節），具備優異的疲勞壽命、耐磨耗與耐腐蝕性。在本專案中用於諧波減速器撓性杯 (flex spline)，承受反覆交變彎曲應力，需通過 10,000 次以上循環驗證（峰值扭矩 125 Nm）。

- **標準**: ASTM F1537-20 Standard Specification for Wrought Cobalt-28 Chromium-6 Molybdenum Alloys for Surgical Implants
- **Condition**: Condition 1 (Hot-worked + solution annealed, 1220°C/1h/WQ)
- **化學成分 (wt%)**: Co bal., Cr 26-30%, Mo 5-7%, Ni <1%, Fe <0.75%, C <0.35%, Mn <1%, Si <1%

---

## 機械性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 密度 | 8300 | kg/m³ | 20°C | |
| 楊氏模量 (E) | 210-230 | GPa | 20°C | 設計用 220 GPa |
| 泊松比 (ν) | 0.29 | — | 20°C | |
| 降伏強度 σ_y | ≥827 | MPa | 20°C | ASTM F1537 Cond.1 最低要求 |
| 降伏強度 σ_y (typical) | ~1000 | MPa | 20°C | 鍛造冷加工態典型值 |
| 極限拉伸強度 σ_UTS | ≥1172 | MPa | 20°C | ASTM F1537 Cond.1 最低要求 |
| 延伸率 | ≥12 | % | 20°C | |
| 硬度 | 35-45 | HRC | 20°C | |
| 疲勞極限 (R=-1) | 500-600 | MPa | 10⁷ cycles, 20°C | **Goodman 圖關鍵參數** |
| 疲勞極限 (R=0.1) | ~650-700 | MPa | 10⁷ cycles, 20°C | 脈動拉伸 |
| 斷裂韌性 K_IC | ~60-80 | MPa·√m | 20°C | |

### 應力-應變曲線參數（彈塑性 FEA 用）

| 參數 | 數值 | 單位 | 備註 |
|:---|:---|:---|:---|
| E | 220 | GPa | |
| σ_y (0.2% offset) | 1000 | MPa | 設計典型值 |
| σ_UTS | 1200 | MPa | |
| Elongation at break | 15 | % | |
| Tangent modulus E_t (bilinear) | ~2500 | MPa | 降伏後線性硬化近似 |
| Ramberg-Osgood n | ~12 | — | 冪律硬化指數 |

---

## 熱性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 熱傳導率 (k) | 14 | W/mK | 20°C | 低，典型鈷合金 |
| 比熱容 (Cp) | 450 | J/kgK | 20°C | |
| 熱膨脹係數 (CTE) | 13.5 | μm/m°C | 20-200°C | |
| 熔點範圍 | 1350-1450 | °C | — | 固相線-液相線 |

---

## 電磁性質

CoCrMo F1537 為非磁性（順磁性），電磁 FEA 中可忽略。

| 性質 | 數值 | 單位 | 備註 |
|:---|:---|:---|:---|
| 相對磁導率 μ_r | ~1.0 | — | 非磁性 |
| 電阻率 | ~0.75 | μΩ·m | 20°C |

---

## FEA 輸入指引

### ANSYS Mechanical（靜態+疲勞分析）

1. **Material Model**: `Structural Steel` 模板修改 → 或新建 `User-defined`
2. **彈性**: Isotropic Elasticity → E=220 GPa, ν=0.29
3. **塑性** (若需非線性分析):
   - Bilinear Isotropic Hardening: σ_y=1000 MPa, E_t=2500 MPa
   - 或 Multilinear: 輸入真應力-真應變曲線
4. **疲勞**:
   - 使用 ANSYS nCode 或 Fatigue Tool
   - S-N 曲線: 手動輸入或使用 Goodman 修正
   - 平均應力修正: Goodman diagram → σ_e=550 MPa (R=-1), σ_UTS=1200 MPa
   - **關鍵**: Flex spline 為彎曲交變載荷，R 比接近 -1
5. **Mesh**: 撓性杯薄壁區域使用 hex-dominant mesh，至少 4 層 through-thickness
6. **接觸**: 與波發生器 (wave generator) 接觸面使用 frictional contact, μ=0.15

### COMSOL Structural Mechanics

1. **Material**: 新建 `User-defined` → 輸入 E, ν, ρ, σ_y
2. **Physics**: `Solid Mechanics (solid)` → 若大變形啟用 `Geometric Nonlinearity`
3. **Plasticity**: `Elastoplastic Material` → `Isotropic Hardening` → `Bilinear`
4. **Fatigue**: 使用 `Fatigue Module` → `Stress-Life` → S-N curve
5. **Mesh**: `Mapped` mesh on thin wall, minimum element size ≤ 0.3mm

### Goodman 疲勞評估（手動驗證用）

```
Goodman 方程: σ_a/σ_e + σ_m/σ_UTS = 1/SF

其中:
  σ_a = 交變應力振幅 (FEA 輸出)
  σ_m = 平均應力 (FEA 輸出)
  σ_e = 550 MPa (疲勞極限 @R=-1, 10⁷ cycles)
  σ_UTS = 1200 MPa
  SF = 安全因子 (建議 ≥1.5 for flex spline)

設計允許: σ_a ≤ 550 × (1 - σ_m/1200) / 1.5
```

---

## 注意事項

1. **疲勞壽命為設計關鍵**: 撓性杯每轉一圈經歷 2 次完整彎曲循環（橢圓波發生器）。100:1 減速比下，輸入端轉速 3000rpm → 撓性杯 3000×2=6000 cycles/min。1000 小時壽命需 3.6×10⁸ cycles。**必須確保 FEA 應力遠低於疲勞極限**。
2. **表面狀態**: 疲勞極限高度依賴表面粗糙度。設計值 500-600 MPa 假設 Ra ≤ 0.4μm（研磨/拋光）。若實際表面粗糙需乘以表面修正因子。
3. **尺寸效應**: ASTM F1537 數據基於標準試棒。撓性杯薄壁（~0.3-0.5mm 可撓區）可能有尺寸效應，建議疲勞安全因子 ≥1.5。
4. **加工硬化**: CoCrMo 加工硬化率高，切削加工時需使用硬質合金刀具，低速高進給。加工後表面殘留壓應力有利疲勞壽命。
5. **成本**: CoCrMo 為高價材料 (~$150-300/kg)，需精確控制用量。撓性杯淨重建議 < 100g。
6. **替代考量**: 若成本過高，可評估 17-4PH (H900) 或 Maraging Steel C300 作為降級替代，但疲勞性能與耐腐蝕性將下降。
