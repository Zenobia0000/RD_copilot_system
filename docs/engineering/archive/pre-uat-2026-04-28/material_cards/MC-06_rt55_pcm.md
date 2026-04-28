# MC-06: Rubitherm RT55 Phase Change Material (Thermal Management)

> **版本**: 1.0 | **日期**: 2026-04-21
> **來源**: Evidence C-009 from TRIZ session (corrected from RT52 which doesn't exist)
> **適用 WI**: WI-06
> **FEA 軟體**: ANSYS Fluent (Solidification/Melting), COMSOL Heat Transfer Module, STAR-CCM+

---

## 材料概述

Rubitherm RT55 為有機石蠟基相變材料 (Phase Change Material, PCM)，相變溫度峰值約 55°C。利用固液相變的潛熱儲存，在馬達連續大負載運轉時吸收峰值熱量，延緩溫升。本設計將 250g RT55 填充於殼體夾層腔內，可在 8 分鐘連續運轉中吸收約 43 kJ 熱量。

- **供應商**: Rubitherm Technologies GmbH (德國)
- **產品型號**: RT55
- **類型**: 有機石蠟基 PCM，非危險品，化學穩定
- **相變類型**: 固-液

---

## 機械性質

PCM 無結構功能，以下僅列流變相關參數：

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 密度 (固態) | 880 | kg/m³ | <45°C | |
| 密度 (液態) | 770 | kg/m³ | >57°C | |
| 體積膨脹率 (固→液) | ~12 | % | — | **腔體設計必須預留膨脹空間** |
| 動態黏度 (液態) | ~3.5 | mPa·s | 60°C | 近似水的 3.5 倍 |
| 表面張力 | ~0.025 | N/m | 液態 | |

---

## 熱性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 相變溫度範圍 | 51-57 | °C | — | DSC 量測 onset-endset |
| 相變峰值溫度 | ~55 | °C | — | DSC 峰值 |
| 潛熱 ΔH | 170 | kJ/kg | — | 固液相變 |
| 比熱容 (固態) Cp_s | 2.0 | kJ/kgK | <45°C | |
| 比熱容 (液態) Cp_l | 2.0 | kJ/kgK | >57°C | |
| 熱傳導率 k (固態) | ~0.2 | W/mK | <45°C | **極低，為主要限制** |
| 熱傳導率 k (液態) | ~0.2 | W/mK | >57°C | |
| 閃火點 | >200 | °C | — | 安全性 |
| 最大建議工作溫度 | 70 | °C | — | 長期穩定性考量 |
| 循環穩定性 | >10,000 | cycles | — | 無顯著性能衰退 |

### 焓-溫度關係（FEA 輸入核心數據）

```
T < 45°C (固態):
  H(T) = Cp_s × T = 2000 × T  [J/kg]

45°C ≤ T ≤ 57°C (相變區):
  H(T) = H(45°C) + 170000 × (T - 45) / 12  [J/kg]
  H(45°C) = 2000 × 45 = 90,000 J/kg
  H(57°C) = 90,000 + 170,000 = 260,000 J/kg

T > 57°C (液態):
  H(T) = H(57°C) + Cp_l × (T - 57)
  H(T) = 260,000 + 2000 × (T - 57)  [J/kg]
```

### 焓-溫度對照表（直接輸入 FEA 用）

| T (°C) | H (kJ/kg) | 狀態 |
|:---|:---|:---|
| 0 | 0 | 固態 |
| 20 | 40 | 固態 |
| 40 | 80 | 固態 |
| 45 | 90 | 固態（相變開始） |
| 48 | 132.5 | 相變中 (~25% 液態) |
| 51 | 175 | 相變中 (~50% 液態) |
| 54 | 217.5 | 相變中 (~75% 液態) |
| 57 | 260 | 液態（相變結束） |
| 60 | 266 | 液態 |
| 70 | 286 | 液態 |

---

## 電磁性質

PCM 為電絕緣體，電磁 FEA 中無需建模。

---

## FEA 輸入指引

### ANSYS Fluent（相變熱管理模擬 — 推薦）

1. **模型選擇**: `Models` → `Solidification & Melting` → 啟用
2. **材料設定**:
   - `Density`: 使用 Boussinesq 近似或 piecewise-linear (880→770 kg/m³)
   - `Specific Heat (Cp)`: 2000 J/kgK (固態與液態皆同)
   - `Thermal Conductivity`: 0.2 W/mK
   - `Viscosity`: 0.0035 Pa·s (液態)
   - `Solidus Temperature`: 45°C (318.15 K)
   - `Liquidus Temperature`: 57°C (330.15 K)
   - `Pure Solvent Melting Heat (Latent Heat)`: 170000 J/kg
3. **Mushy Zone 參數**: `Mushy Zone Constant` = 10⁵ (預設值，可能需調整)
4. **自然對流**: 啟用 `Gravity` 和 `Boussinesq` 近似，β ≈ 0.001 1/K
5. **時間步**: 初始 Δt = 0.1s，自動調整。相變前沿推進速度慢，可逐步增大至 1s
6. **Mesh**:
   - **PCM 厚度方向至少 5 層元素**（捕捉相變前沿）
   - 建議元素尺寸 ≤ 1mm
   - 與殼體壁面接觸面需 inflation layer
7. **收斂監控**: 監控 `Liquid Fraction` 全域平均值隨時間變化

> **重要**: 不要使用 Equivalent Specific Heat (Cp_eff) 方法！該方法在相變溫度範圍窄時會產生嚴重數值振盪。必須使用 Solidification/Melting 模型的焓法 (enthalpy-porosity method)。

### COMSOL Heat Transfer Module

1. **Physics**: `Heat Transfer in Solids and Fluids (ht)`
2. **Material**: 使用 `Phase Change Material` node (COMSOL 5.6+)
   - 或手動設定: `Phase Transition` = `Thermal Properties` → 輸入相變溫度與潛熱
3. **設定方式**:
   - `Phase 1 (solid)`: ρ=880, Cp=2000, k=0.2
   - `Phase 2 (liquid)`: ρ=770, Cp=2000, k=0.2
   - `Transition temperature`: 51°C
   - `Transition interval`: 6°C (半寬)
   - `Latent heat`: 170000 J/kg
4. **若需考慮自然對流**: 加入 `Laminar Flow (spf)` → `Non-isothermal Flow` 耦合
5. **Mesh**: `Extremely Fine` 或自訂，PCM domain 至少 5 層

### STAR-CCM+

1. **Physics**: `Segregated Enthalpy` model
2. **Material**: `Melting-Solidification` 材料模型
3. **設定**: Solidus=318.15K, Liquidus=330.15K, Latent Heat=170000 J/kg

---

## 設計計算參考

### 熱能儲存容量計算

```
PCM 質量: m = 250 g = 0.25 kg
可用潛熱: Q_latent = m × ΔH = 0.25 × 170 = 42.5 kJ ≈ 43 kJ
可用溫升顯熱 (20°C → 45°C): Q_sensible = 0.25 × 2.0 × 25 = 12.5 kJ
總熱容 (20°C → 57°C): Q_total = 12.5 + 42.5 = 55 kJ

若馬達持續損耗 100W:
  純潛熱可吸收時間: 42.5 kJ / 100 W = 425 s ≈ 7 min
  含顯熱: 55 kJ / 100 W = 550 s ≈ 9 min
```

### 熱傳導時間尺度

```
PCM 厚度: δ = 5 mm (假設)
熱擴散率: α = k/(ρ·Cp) = 0.2/(880×2000) = 1.14×10⁻⁷ m²/s
Fourier number Fo = α·t/δ² = 1 → t = δ²/α = (0.005)²/(1.14×10⁻⁷) ≈ 220 s

→ 5mm 厚的 PCM 完全融化約需 220s，與 8min 運轉時間匹配。
  若厚度 >8mm，中心區可能未完全融化，潛熱利用率下降。
```

---

## 注意事項

1. **熱傳導率極低 (0.2 W/mK)**: 這是 PCM 應用的核心挑戰。建議在 PCM 腔體中加入金屬泡沫 (Al foam, 10 PPI) 或鋁翅片以增強導熱。加入後等效熱傳導率可提升至 2-5 W/mK，但會佔用 5-10% 體積。FEA 中可用等效熱傳導率建模。
2. **體積膨脹 12%**: 固液相變時體積膨脹約 12%。腔體設計必須預留膨脹空間（建議 PCM 充填率 ≤85-88%），否則可能導致殼體內壓上升甚至破裂。
3. **洩漏防護**: 液態 PCM 為低黏度流體，腔體密封必須可靠。建議使用 O-ring (FKM/Viton) + 平面密封。所有開孔螺絲需塗布厭氧膠。
4. **長期穩定性**: 有機 PCM 在 >10,000 次循環後性質穩定，但需避免持續 >70°C 曝露（可能加速氧化降解）。
5. **與鎂合金相容性**: RT55 石蠟與 AZ91D 鎂合金在 <70°C 下化學相容。但建議 PCM 腔體內壁施加 PEO 處理或陽極氧化，防止長期接觸可能的緩慢反應。
6. **重力方向**: 自然對流受重力方向影響。FEA 中需正確設定安裝姿態（e-Bike 中置馬達通常傾斜安裝）。
7. **PCM 回充/更換**: 設計壽命期內 PCM 不應需要更換（>10,000 cycles 穩定）。但建議設計可拆卸的注入孔以備維護。
