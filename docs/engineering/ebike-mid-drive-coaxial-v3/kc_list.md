# Key Characteristics List — e-Bike Mid-Drive (v3)

> **版本**: 1.0 | **日期**: 2026-04-28
> **TRIZ Session**: 2026-04-28-1500-eBike-MidDrive-Coaxial
> **來源**: WI 設計輸入 + ICD GD&T + Risk Register
> **下游使用**: Control Plan、SPC、PPAP

---

## KC 清單

| KC ID | 特徵 | 子系統 | 規格值 | 公差 | 來源 WI/ICD | 量測方法 | 等級 |
|:------|:-----|:-------|:-------|:-----|:------------|:---------|:-----|
| KC-001 | Air gap 同心度 | 馬達 | 1.0 mm | ≤ 0.02 mm | ICD-01, WI-04 | CMM + Hall probe | **Critical** |
| KC-002 | Halbach 段磁化角度 | 馬達 | per Halbach formula | ±0.5° | WI-01, MC-01 | 磁通量測 + 角度標定 | **Critical** |
| KC-003 | NdFeB B_r | 馬達 | 1.32 T | ±2% | MC-01 | Probe @ 25°C | **Critical** |
| KC-004 | Stator 外圓圓柱度 | 馬達 | OD 92.00 mm | ≤ 0.01 mm | ICD-01 | CMM | **Critical** |
| KC-005 | Cu 嵌件過盈量 | 熱管理 | 0.05 mm | -0.05/-0.10 | ICD-01, WI-03 | 量測 + 拉脫力 | Major |
| KC-006 | 介面熱阻 R_th | 熱管理 | ≤ 0.05 K/W | — | WI-03 | thermal transient | **Critical** |
| KC-007 | PCM 熔點 | 熱管理 | 55°C | ±1°C | MC-06 | DSC | **Critical** |
| KC-008 | PCM 潛熱 | 熱管理 | 200 kJ/kg | ≥ 190 | MC-06 | DSC | Major |
| KC-009 | 齒形修形 Δδ 齒廓 | 齒輪 | 5~15 μm | ±2 μm | WI-02 | gear profile checker | **Critical** |
| KC-010 | 齒形修形 Δδ 齒向 | 齒輪 | 3~8 μm | ±1 μm | WI-02 | helix checker | **Critical** |
| KC-011 | 齒輪箱 PEE | 齒輪 | < 5 μm | — | WI-02 | encoder transmission error | **Critical** |
| KC-012 | 主軸承同軸度（前後）| 結構 | — | ≤ 0.02 mm | ICD-02, WI-04 | CMM | **Critical** |
| KC-013 | 軸承預壓力 | 結構 | 80~120 N | ±10% | ICD-02 | torque-to-rotation | Major |
| KC-014 | 油浴密封壓力 | 結構 | 0.2 bar / 5 min | 無壓降 | ICD-02 | leak test | **Critical** |
| KC-015 | IP67 防水 | 結構 | 1m / 30 min | 無進水 | ICD-04 | 浸泡 + silica gel | **Critical** |
| KC-016 | Housing 分模面平面度 | 結構 | — | ≤ 0.05 mm | ICD-04 | CMM | Major |
| KC-017 | O-ring 壓縮率 | 結構 | 15~25% | — | ICD-04 | 槽深 vs 截面 | Major |
| KC-018 | 螺絲扭矩（housing 8 顆 M5）| 結構 | 4 Nm | ±10% | ICD-04 | torque wrench | Minor |
| KC-019 | TIM 接觸面積（PCB-endcap）| 電子 | ≥ 80% | — | ICD-03 | 著色 / pressure film | Major |
| KC-020 | MOSFET T_j @ peak | 電子 | < 150°C | — | WI-05 | embedded sensor | **Critical** |
| KC-021 | EMI signal noise | 電子 | < 5% baseline | — | ICD-03, WI-05 | scope | Major |
| KC-022 | 系統重量 | 整機 | ≤ 2500 g | — | 系統規格 | 秤重 | **Critical** |
| KC-023 | Peak torque @ output | 整機 | ≥ 125 Nm | — | 系統規格 | dyno | **Critical** |
| KC-024 | Continuous torque | 整機 | ≥ 100 Nm | — | 系統規格 | dyno × 1 hr | **Critical** |
| KC-025 | 噪音水平 | 整機 | ≤ HPR50 baseline | — | 系統規格（**R-002**）| 半消音室 | Major |
| KC-026 | 系統效率 | 整機 | ≥ 80% | — | WI-06 V9 | dyno | Major |
| KC-027 | OD 包絡 | 整機 | ≤ 111 mm | — | 系統規格 | 量測 | **Critical** |
| KC-028 | Axial 包絡 | 整機 | ≤ 92 mm | — | 系統規格 | 量測 | **Critical** |
| KC-029 | NdFeB 退磁邊界 | 馬達 | T_winding < 120°C | — | MC-01, R-008 | NTC monitor | **Critical** |
| KC-030 | Housing 表面溫度 | 熱管理 | < 80°C @ cont 1hr | — | WI-03 V13 | IR + thermocouple | **Critical** |

---

## 統計

| 等級 | 數量 |
|:-----|:-----|
| **Critical** | 17 |
| **Major** | 10 |
| **Minor** | 1 |
| **N/A (informational)** | 2 |
| **合計** | **30** |

---

## 下游使用

- **TR2-3 詳設**：Critical KC 必須有公差來源（FEA / 標準 / 經驗）
- **TR7 PFMEA**：30 個 KC 全部進入 PFMEA 的 detection / control 欄位
- **TR8 Control Plan**：依等級分配管制方法（Critical = SPC 100% / Major = AQL 抽樣 / Minor = 目視）
- **TR10 PPAP**：Critical KC 必須 Cpk ≥ 1.33；Major Cpk ≥ 1.0
