# MC-02: SMC Somaloy 700 5P (Stator Core)

> **版本**: 1.0 | **日期**: 2026-04-21
> **來源**: Evidence C-003 from TRIZ session
> **適用 WI**: WI-02
> **FEA 軟體**: JMAG, ANSYS Maxwell, COMSOL AC/DC Module

---

## 材料概述

Soft Magnetic Composite (SMC) 軟磁複合材料，由 Höganäs 生產。Somaloy 700 5P 採用五步壓製 + 650°C 退火製程，具備三維等向磁性與極高電阻率。相比傳統矽鋼片，SMC 允許三維磁路設計且高頻鐵損顯著降低，適合軸向磁通或 claw-pole 等複雜磁路拓撲。

- **供應商**: Höganäs AB
- **等級**: Somaloy 700 5P
- **製程**: 5-step compaction + 650°C steam annealing in N₂ atmosphere
- **成型方式**: 粉末冶金壓製（近淨成型）

---

## 機械性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 密度 | 7350-7450 | kg/m³ | 壓製壓力相依 | 典型值 7400 kg/m³ @800 MPa |
| 楊氏模量 (E) | 130 | GPa | 20°C | |
| 抗拉強度 | ~50 | MPa | 20°C | **脆性**，避免拉伸載荷 |
| 抗壓強度 | ~900 | MPa | 20°C | 壓縮強度遠高於拉伸 |
| 橫向斷裂強度 (TRS) | ~100 | MPa | 20°C | 三點彎曲 |
| 硬度 | ~110 | HB | 20°C | Brinell |

---

## 熱性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 熱傳導率 (k) | ~20 | W/mK | 20°C | **等向性**，優於矽鋼片的穿層方向 (~2-4 W/mK) |
| 比熱容 (Cp) | 450 | J/kgK | 20°C | |
| CTE | ~12 | μm/m°C | 20-200°C | |
| 最大工作溫度 | 300 | °C | — | 受絕緣層限制，連續使用建議 ≤200°C |

---

## 電磁性質

| 性質 | 數值 | 單位 | 條件 | 備註 |
|:---|:---|:---|:---|:---|
| 相對磁導率 μ_r (初始) | ~700 | — | 低通量密度 | |
| 飽和磁通密度 B_sat | ~1.5 | T | — | |
| 電阻率 (ρ) | ~400 | μΩ·m | 20°C | 比矽鋼片高 ~1000 倍，SMC 核心優勢 |

### B-H 磁化曲線（Höganäs Somaloy 700 5P 近似數據）

此表為 FEA 軟體輸入之 B-H 曲線數據點：

| H (A/m) | B (T) |
|:---|:---|
| 0 | 0 |
| 200 | 0.40 |
| 500 | 0.75 |
| 1000 | 1.05 |
| 2000 | 1.25 |
| 5000 | 1.40 |
| 10000 | 1.48 |
| 20000 | 1.53 |
| 50000 | 1.60 |
| 100000 | 1.70 |

> **注意**: 上表為近似值，正式設計時應向 Höganäs 索取實測 B-H 曲線（.csv 或 .jmag-mat 格式）。密度差異將影響磁性能，需確認實際壓製密度。

### 鐵損特性

| 頻率 (Hz) | 磁通密度 (T) | 鐵損 (W/kg) | 備註 |
|:---|:---|:---|:---|
| 50 | 1.0 | ~6 | 工頻參考 |
| 100 | 1.0 | ~13 | |
| 200 | 1.0 | ~25 | |
| 400 | 1.0 | ~50 | e-Bike 典型電氣頻率 |
| 1000 | 1.0 | ~150 | 高速工況 |
| 400 | 0.5 | ~15 | 低通量參考 |
| 400 | 1.5 | ~110 | 近飽和 |

### Steinmetz 參數（修正型 iGSE）

供 FEA 鐵損後處理使用：

- **經典 Steinmetz**: P = k × f^α × B^β
  - k ≈ 3.5 (SI 單位制: W/m³, Hz, T)
  - α ≈ 1.35
  - β ≈ 2.0
  - 有效範圍: 50-1000 Hz, 0.1-1.5 T

> **注意**: SMC 鐵損中渦電流損佔比極低（高電阻率），磁滯損為主導。上述 Steinmetz 參數在高頻區可能需要修正。建議使用 Bertotti 三項模型做更精確擬合。

---

## FEA 輸入指引

### JMAG

1. **Material 設定**: `Soft Magnetic Material` → `User defined`
2. **B-H 曲線**: 手動輸入上表 10 個數據點，插值方式選 `Akima spline` 或 `Linear`
3. **鐵損模型**: 使用 `Steinmetz` 或 `Loss map` 模型
   - Steinmetz: 輸入 k, α, β 參數
   - Loss map: 輸入多頻率多磁通密度的損耗表（更精確）
4. **等向性**: SMC 為磁性等向性，**不要**設定 rolling direction
5. **Mesh**: 定子齒根、軛部至少 2-3 層元素

### ANSYS Maxwell

1. **Material**: 新增 `User-defined` → `Nonlinear Soft`
2. **B-H curve**: 輸入上表數據點
3. **Core loss model**: `Electrical Steel` → 輸入 Steinmetz 係數或 loss curve
   - Kh (hysteresis) ≈ 適當值基於 Bertotti 分離
   - Kc (classical eddy) ≈ 極小值（高電阻率）
   - Ke (excess) ≈ 適當值
4. **Conductivity**: σ = 1/(400×10⁻⁶) = 2500 S/m

### COMSOL AC/DC

1. **Domain**: `Magnetic Fields (mf)` → `Ampere's Law`
2. **Constitutive relation**: `B-H curve` (nonlinear)
3. **B-H data**: 輸入 interpolation table
4. **Loss calculation**: 使用 `Loss calculation` subnode → `Steinmetz` loss model
5. **Electrical conductivity**: 2500 S/m（渦電流效應可選擇忽略，因高電阻率影響極小）

---

## 注意事項

1. **脆性**: SMC 抗拉強度僅 ~50 MPa，設計中嚴禁懸臂或彎曲載荷。定子固定應使用壓縮配合或膠合，**不可使用螺絲直接鎖固於 SMC 本體**。
2. **密度敏感**: 壓製密度直接影響磁性能與機械強度。FEA 所用 B-H 曲線必須對應實際壓製參數。
3. **等向性優勢**: 相比矽鋼片，SMC 在 z 方向（疊層方向）無性能退化，適合三維磁路。熱傳導亦為等向性 ~20 W/mK，遠優於矽鋼片穿層方向 2-4 W/mK。
4. **高頻優勢**: 400Hz 以上 SMC 鐵損優於 0.35mm 矽鋼片。但在低頻（<200Hz）應用中，傳統矽鋼片仍有優勢。
5. **溫度效應**: μ_r 隨溫度略微增加（~5% @200°C），B_sat 略微下降。若工作溫度 >150°C 需進行溫度修正。
6. **加工限制**: SMC 壓製後不可切削加工（會破壞顆粒間絕緣層），所有特徵必須在模具中成型。最小壁厚建議 ≥2mm。
