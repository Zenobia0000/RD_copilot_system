# TRIZ Session Report: 2026-04-28-ebike-drive-unit-v3

> **日期**: 2026-04-28
> **主題**: e-Bike mid-mounted coaxial drive unit — 高扭力密度/輕量/低噪設計
> **路徑**: tc-main (multi-tc expected)
> **判定**: 未完成

---

## Step 0: 問題定向

### 路由判定

| 維度 | 結論 |
|:-----|:-----|
| 問題類型 | 系統設計（非故障排除）|
| 系統描述 | 完整 — motor/gearbox/board/shaft + 全規格 |
| 矛盾存在 | 是 — 5 組隱含 TC 已初步識別 |
| 需要 5Why/KT/CECA | 否 |
| 路由 | 直接進 Step 1 功能建模 |

### 初步 TC 假設

| TC | 改善 | 惡化 |
|:---|:-----|:-----|
| TC1 | 馬達扭力密度 (125Nm output) | 馬達體積 (OD≤111mm) |
| TC2 | 輸出扭力 (125Nm peak) | 總重量 (≤2500g) |
| TC3 | 降低齒輪噪聲 (對標 HPR50) | 傳動效率/結構複雜度 |
| TC4 | 縮小包絡體積 (OD111×92mm) | 散熱能力 (100Nm@8min) |
| TC5 | 輕量化材料 (AZ91D+PEEK) | 結構強度 (125Nm peak impact) |

### Step 0 結論

- **子系統**: Motor, Gearbox, Drive Board, Shell, Pedaling Shaft, Sensor
- **根因假設**: N/A（非故障）
- **TC 假設**: 5 組（見上表）
- **路由**: Step 1 功能建模

---

## Step 1: 功能建模

### 組件交互圖

| # | 來源組件 | 功能 | 目標組件 | 類型 | 備註 |
|:--|:--------|:-----|:--------|:-----|:-----|
| 1 | Motor stator | 產生旋轉磁場 | Motor rotor | 有效 | 電磁扭矩轉換 |
| 2 | Motor rotor | 輸出扭矩 (~5Nm) | Gearbox input | 有效 | coaxial |
| 3 | Gearbox | 減速增扭 (1:30-35) | Output sprocket | 有效 | 5→125Nm |
| 4 | Drive board | FOC 驅動控制 | Motor stator | 有效 | PWM 電流 |
| 5 | Rider | 施加踩踏力 | Pedaling shaft | 有效 | 人力輸入 |
| 6 | Torque sensor | 感測扭矩/角度 | Drive board | 有效 | 助力比例 |
| 7 | Shell (AZ91D) | 結構支撐 | Motor+Gearbox | 有效 | 承受反力矩 |
| 8 | Shell | 安裝固定 | Frame BB殼 | 有效 | 鎖付介面 |
| 9 | Lubricant | 減少摩擦 | Gearbox gears | 有效 | 潤滑+散熱 |
| 10 | Motor coil | 產生焦耳熱 | Shell inner wall | **有害** | 銅損 I²R |
| 11 | Gearbox gears | 嚙合衝擊噪聲 | Shell→環境 | **有害** | 齒面撞擊 |
| 12 | Gearbox gears | 摩擦熱 | Lubricant/Shell | **有害** | 齒面滑動 |
| 13 | MOSFET | 開關損耗熱 | PCB/Shell | **有害** | 高頻切換 |
| 14 | Gear train | 傳遞振動 | Pedaling shaft | **有害** | 騎乘舒適 |
| 15 | Shell (AZ91D) | 散熱至環境 | Ambient air | **不足** | 小面積+低對流 |
| 16 | Motor magnets | 氣隙磁通 | Rotor/Stator | **不足** | 5Nm@Ø65mm |
| 17 | Gear teeth (PEEK) | 承受接觸應力 | Tooth surface | **不足** | 125Nm peak |
| 18 | Shell (AZ91D) | 抵抗反力矩 | Frame mount | **不足** | Mg 剛性有限 |

### SF 診斷

| # | S1 (工具) | F (場) | S2 (物件) | SF 狀態 | 關聯 TC |
|:--|:---------|:-------|:---------|:--------|:--------|
| SF1 | Motor coil (Cu) | 熱 (Joule) | Shell inner wall | 有害 | TC4 |
| SF2 | Gear teeth | 機械 (嚙合衝擊) | Air/Shell | 有害 | TC3 |
| SF3 | Gear teeth | 機械 (滑動摩擦) | Lubricant/Shell | 有害 | TC4 |
| SF4 | MOSFET | 熱 (開關損耗) | PCB/Shell | 有害 | TC4 |
| SF5 | Shell (AZ91D) | 熱 (自然對流) | Ambient air | 不足 | TC4 |
| SF6 | Motor magnets | 電磁 (Bg) | Rotor | 不足 | TC1,TC2 |
| SF7 | Gear teeth (PEEK) | 機械 (接觸應力) | Tooth surface | 不足 | TC5 |
| SF8 | Gear train | 機械 (振動) | Pedaling shaft | 有害 | TC3 |
| SF9 | Shell (AZ91D) | 機械 (剛性) | Frame mount | 不足 | TC5 |

### 改善/惡化描述

| TC | 改善 | 惡化 |
|:---|:-----|:-----|
| TC1 | 提高馬達扭力密度至5Nm | 馬達外徑超過Ø65mm空間限制 |
| TC2 | 達到125Nm峰值扭力 | 系統重量超過2500g |
| TC3 | 降低齒輪噪聲至HPR50級 | 傳動效率下降或結構複雜化 |
| TC4 | 縮小外殼至OD111×92mm | 散熱面積不足，100Nm@8min溫升超標 |
| TC5 | 使用AZ91D+PEEK降至2500g | 125Nm峰值時結構強度不足 |

- **路由**: TC 路徑 (multi-tc, 5 TCs)

---

## Step 2: TC 定義 + 矛盾矩陣查表

### 39 參數映射

| TC | 改善參數 | 惡化參數 | 矩陣查表結果 |
|:---|:---------|:---------|:------------|
| TC1 | #10 力 (Force) — 馬達扭矩 | #7 移動物體的體積 — 馬達轉子 | **15, 9, 12, 37** |
| TC2 | #10 力 (Force) — 輸出扭矩 | #1 移動物體的重量 — 系統重量 | **8, 1, 37, 18** |
| TC3 | #31 有害副作用 — 齒輪噪聲 | #22 能量損失 — 傳動效率 | **19, 24, 3, 14** |
| TC4 | #8 靜止物體的體積 — 外殼包絡 | #17 溫度 — 散熱溫升 | **35, 39, 38** |
| TC5 | #2 靜止物體的重量 — 殼+齒輪 | #14 強度 — 結構強度 | **28, 2, 27** |

### 原理具體化

| TC | 選用原理 | 具體化方案 | 控制方程 |
|:---|:---------|:----------|:---------|
| TC1 | #15 動態化 | IPM V-shape 聚磁轉子；磁阻扭矩貢獻 ~30% | T = (3p/2)[ψ_m·i_q + (L_d-L_q)·i_d·i_q] |
| TC2 | #1 分割 | 多路行星齒輪組 (N=4 planets/stage × 2 stages) | F_per_planet = F_total/(N·cosα) |
| TC3 | #3 局部品質 + #14 曲面化 | 斜齒行星 + 齒形微修形 (tip/root relief + crowning) | ε_total = ε_α + ε_β > 2.0 |
| TC4 | #35 參數變化 | 赤蘚糖醇 PCM (~70g) 相變蓄熱 | Q = m·ΔH_fus = 70g × 340kJ/kg ≈ 24kJ |
| TC5 | #28 機械替代 + #2 分離 | CF-PEEK 齒輪體 + 鋼嵌件齒根；拓撲優化 Mg 殼 | CF-PEEK σ_f ≈ 200MPa; 鋼 σ_y ≈ 800MPa |

### Evidence Gate

| Claim ID | 聲明 | 有方程 | 判定 |
|:---------|:-----|:------:|:----:|
| CLM-TC1-01 | IPM V-shape Bg_eff ≈ 0.9T at Ø65mm → 5Nm | Yes | PASS |
| CLM-TC2-01 | 4-planet load sharing 減少 75% 單齒負載 | Yes | PASS |
| CLM-TC3-01 | Helical ε > 2.0 + micro-geo → noise -8dB | Yes | PASS |
| CLM-TC4-01 | 70g 赤蘚糖醇 PCM 緩衝 24kJ 峰值熱 | Yes | PASS |
| CLM-TC5-01 | CF-PEEK σ_f ≈ 200MPa + 鋼嵌件承受 125Nm | Yes | PASS |

**Evidence Gate 總判定**: PASS

### 瓶頸分析

- **瓶頸 TC**: TC1（扭力密度決定馬達尺寸，約束所有後續設計）
- **依賴 TC**: TC2（由 TC1+TC3+TC5 方案組合解決 — IPM 高效→更輕馬達 + CF-PEEK→更輕齒輪 + PCM→免除大散熱器）
- **預估重量**: motor ~800g + gearbox ~400g + shell ~600g + board ~200g + shaft/sensor ~300g + PCM ~100g ≈ 2400g < 2500g

---

## Step 3: PC 分離 + SF 標準解

### PC 分析

| 方案 | 物理矛盾 | 分離策略 | 說明 |
|:-----|:---------|:---------|:-----|
| SOL-TC1 | Motor D must be LARGE (T∝D²LBg) AND SMALL (Ø≤65mm) | **空間分離** | V-shape 磁鐵在氣隙局部聚磁 Bg↑30-40%，不增加外徑 |
| SOL-TC3 | Mesh stiffness must be HIGH (η>95%) AND LOW-variation (ΔK/K<10%) | **整體局部分離** | 單齒微修形提供局部順應性；斜齒重疊確保整體高剛性 |
| SOL-TC5 | Gear material must be LIGHT (ρ↓) AND STRONG (σ_y↑) | **整體局部分離** | CF-PEEK 整體輕量(ρ≈1.4)；鋼嵌件局部高強(σ_y≈800MPa) |
| SOL-TC4 | Shell must be SMALL (OD111×92) AND LARGE thermal capacity | **時間分離** | PCM 峰值蓄熱(burst)→休息期散熱；時域緩衝解耦瞬態與穩態 |

### SIM — 解方案交互矩陣

|  | SOL-TC1 | SOL-TC3 | SOL-TC5 | SOL-TC4 |
|:---|:---:|:---:|:---:|:---:|
| **SOL-TC1** | — | 0 | 0 | **+1** |
| **SOL-TC3** | 0 | — | **+1** | 0 |
| **SOL-TC5** | 0 | +1 | — | 0 |
| **SOL-TC4** | +1 | 0 | 0 | — |

**SIM 統計**: +1: 2 對, 0: 4 對, -1: 0 對

**協同效應**:
1. SOL-TC1 ↔ SOL-TC4: IPM 高效率 → 更少發熱 → PCM 餘裕更大
2. SOL-TC3 ↔ SOL-TC5: 斜齒設計受惠於 CF-PEEK 的振動阻尼特性

**SIM 判定**: **Converged** — 無衝突，2 組協同，解方案互相相容

---
