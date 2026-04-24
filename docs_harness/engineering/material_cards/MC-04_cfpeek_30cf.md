# MC-04: CF-PEEK 30%CF Victrex 450CA30 (Rigid Spline)

> **版本**: 1.0 | **日期**: 2026-04-21
> **來源**: Evidence C-004 from TRIZ session
> **適用 WI**: WI-04
> **FEA 軟體**: ANSYS Mechanical, COMSOL Structural Mechanics, Moldex3D (mold flow)

---

## 材料概述

碳纖維增強聚醚醚酮 (CF-PEEK)，Victrex PEEK 450CA30，含 30% 短碳纖維（射出成型級）。具備高強度、高模量、優異的耐熱性與尺寸穩定性。用於諧波減速器剛性齒輪 (rigid spline/circular spline)，射出成型製造。

- **供應商**: Victrex plc
- **等級**: PEEK 450CA30
- **基材**: PEEK 450G (Mw ~100,000, MFI ~25 g/10min @400°C)
- **纖維**: 短碳纖維 (chopped CF), 30 wt%
- **成型**: 射出成型 (injection molding), 模溫 180-200°C, 料溫 380-400°C

---

## 機械性質

> **重要**: 射出成型 CF-PEEK 為**各向異性**材料。纖維沿流動方向 (MD) 取向，性質與橫向 (TD) 差異顯著。以下標示 MD/TD 表示流動方向/橫向。

| 性質 | 數值 (MD) | 數值 (TD) | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|:---|
| 密度 | 1410 | 1410 | kg/m³ | 23°C | |
| 彎曲模量 | 28 | 22 | GPa | 23°C | ISO 178 |
| 拉伸模量 | 26 | 18 | GPa | 23°C | ISO 527 |
| 彎曲強度 σ_flex | 380 | ~280 | MPa | 23°C | ISO 178 |
| 拉伸強度 σ_tensile | 212 | ~160 | MPa | 23°C | ISO 527 |
| 延伸率 | 1.5-2.5 | 1.0-1.5 | % | 23°C | 脆性斷裂 |
| 壓縮強度 | ~250 | ~200 | MPa | 23°C | |
| 衝擊強度 (Charpy notched) | ~8 | ~5 | kJ/m² | 23°C | ISO 179 |
| 疲勞 (R=0.1, 10⁶ cycles) | ~100 | ~70 | MPa | 23°C, 乾態 | 參考值，需實測驗證 |

### FEA 各向異性彈性常數（射出成型件近似）

若使用正交異性 (Orthotropic) 材料模型：

| 參數 | 數值 | 單位 | 備註 |
|:---|:---|:---|:---|
| E₁ (MD, 流動方向) | 26 | GPa | |
| E₂ (TD, 橫向) | 18 | GPa | |
| E₃ (ND, 厚度方向) | 16 | GPa | 近似 ≈ 0.6 × E₁ |
| G₁₂ | 7.5 | GPa | 近似 |
| G₂₃ | 6.0 | GPa | 近似 |
| G₁₃ | 7.0 | GPa | 近似 |
| ν₁₂ | 0.38 | — | |
| ν₂₃ | 0.42 | — | |
| ν₁₃ | 0.40 | — | |

> **注意**: 上述正交異性常數為近似值。精確值需透過 Moldex3D / Moldflow 模流分析取得纖維取向張量 (FOT)，再映射至結構 FEA。

---

## 熱性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 熱傳導率 (k) - 沿纖維 | 0.92 | W/mK | 23°C | MD 方向 |
| 熱傳導率 (k) - 橫向 | ~0.4 | W/mK | 23°C | TD 方向 |
| 比熱容 (Cp) | 1150 | J/kgK | 23°C | |
| CTE - MD (流動方向) | 15 | μm/m°C | 23-150°C | 纖維約束膨脹 |
| CTE - TD (橫向) | 40 | μm/m°C | 23-150°C | 接近基材 PEEK |
| Tg | 143 | °C | — | 玻璃轉化溫度 |
| Tm | 343 | °C | — | 熔點 |
| HDT @1.8MPa | 315 | °C | ISO 75 | |
| 成型收縮率 - MD | 0.1 | % | — | |
| 成型收縮率 - TD | 0.3 | % | — | 異向收縮需注意齒形精度 |
| 吸水率 (24h) | 0.06 | % | 23°C 浸水 | 極低，尺寸穩定 |

---

## 電磁性質

CF-PEEK 為非導磁材料，但碳纖維具有導電性，在電磁環境中可能需考慮：

| 性質 | 數值 | 單位 | 備註 |
|:---|:---|:---|:---|
| 體積電阻率 | ~10 | Ω·m | 各向異性，沿纖維方向更低 |
| 相對介電常數 | ~4 | — | 1 MHz |
| 磁性 | 非磁性 | — | μ_r ≈ 1.0 |

---

## FEA 輸入指引

### ANSYS Mechanical（齒根應力分析）

1. **Material Model - 簡化（等向性近似）**:
   - 若纖維取向資訊不可得，使用保守值: E=18 GPa (TD), σ_flex=280 MPa (TD)
   - 這確保在最弱方向仍滿足強度要求

2. **Material Model - 精確（各向異性）**:
   - 使用 `Orthotropic Elasticity` 輸入 E₁, E₂, E₃, G₁₂, G₂₃, G₁₃, ν₁₂, ν₂₃, ν₁₃
   - **纖維取向映射**: 先用 Moldex3D/Moldflow 做射出成型分析 → 輸出纖維取向張量 → 匯入 ANSYS 做 mapping
   - ANSYS 工具: `Engineering Data` → `Fiber orientation data` 或使用 Digimat-RP 介面

3. **齒根應力設計準則**:
   - 齒根最大等效應力 ≤ 150 MPa（含安全因子）
   - 依據 TD 方向強度 280 MPa，安全因子 SF = 280/150 ≈ 1.87

4. **Mesh**: 齒根圓角處使用 refinement，元素尺寸 ≤ 0.1mm，至少 3 層元素沿齒厚

### COMSOL Structural Mechanics

1. **Material**: `User-defined` → `Orthotropic` linear elastic
2. **座標系**: 建立 local coordinate system 對齊纖維流動方向
3. **Physics**: `Solid Mechanics` → `Linear Elastic Material` → `Orthotropic`
4. **Failure criterion**: `Tsai-Wu` 或 `Max Stress` for short fiber composite

### Moldex3D / Moldflow（射出成型模流分析）

1. **用途**: 預測纖維取向分佈、熔接線位置、收縮翹曲
2. **材料資料庫**: Victrex 450CA30 已收錄於 Moldex3D/Moldflow 材料庫
3. **關鍵輸出**:
   - 纖維取向張量 (a₁₁, a₂₂, a₃₃ components)
   - 熔接線 (weld line) 位置 → 此處強度可能降低 30-50%
   - 體積收縮率分佈 → 影響齒形精度

---

## 注意事項

1. **各向異性是設計核心問題**: 齒根應力方向與纖維取向的關係直接決定強度。Gate 位置設計必須確保齒根關鍵區域的纖維取向有利。
2. **熔接線弱化**: 射出成型件不可避免的熔接線 (weld line) 處，強度可能僅為標稱值的 50-70%。齒根不可出現熔接線。模具設計時需使用模流分析優化 gate 位置。
3. **脆性斷裂**: CF-PEEK 延伸率低（1.5-2.5%），無明顯塑性變形。FEA 中應使用最大應力準則或 Tsai-Wu 準則判斷失效，**不要使用** von Mises 等延性材料準則。
4. **溫度效應**: 雖然 HDT 高達 315°C，但 Tg=143°C 以上模量顯著下降。e-Bike 工作溫度 <80°C 時性質穩定，不需額外溫度修正。
5. **蠕變**: PEEK 在高應力長時間載荷下存在蠕變。齒根應力若持續 >80 MPa (23°C)，需評估蠕變效應。
6. **成型公差**: 射出成型齒輪的齒形精度通常 JIS N10-N11 級。若需更高精度，考慮成型後精密加工（但會切斷表面纖維）。
7. **CTE 匹配**: 剛性齒輪 (CF-PEEK) 與外殼 (AZ91D Mg) 的 CTE 差異 (15 vs 26 μm/m°C) 需在配合設計中考量熱膨脹干涉量變化。
