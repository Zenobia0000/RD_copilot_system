---
id: WI-05
type: WI
title: 環形 Drive Board + 扭力/角度感測器整合
domain: electronics
role: cross-cutting   # 服務 TC-A 熱保護 + TC-B 馬達控制
version: 1.0
date: 2026-04-28
effort_weeks: 4
owner: EE

depends_on:
  - target: WI-01
    artifact: 繞組規格 + IL_rms
    purpose: MOSFET 額定確認
  - target: WI-03
    artifact: 熱保護邏輯
    purpose: MCU 韌體實作 NTC 閾值
supports_icd: [ICD-03]
mitigates: [R-005, R-008]
satisfies_gates: [TR1, TR2, TR3, TR5, TR6]
---

# WI-05: 環形 Drive Board + 扭力/角度感測器整合

> **版本**: 1.0 | **日期**: 2026-04-28
> **負責域**: 電子（PCB/控制）
> **前置條件**: WI-01 繞組規格、WI-03 熱保護策略
> **產出物**: PCB layout、MCU firmware spec、感測器規格、EMI 屏蔽方案
> **預估工時**: 4 週
> **阻塞下游**: WI-04（endcap 設計）、ICD-03


## Relations Graph (auto-generated)

<!-- AUTO-GRAPH:START view=ego -->

```mermaid
flowchart LR
    WI_05(["<b>WI-05</b><br/>環形 Drive Board + 扭力/角度感測器整合"]):::center

    subgraph 相關_WI["相關 WI"]
        direction TB
        WI_01(["WI-01"]):::wi
        WI_03(["WI-03"]):::wi
        WI_04(["WI-04"]):::wi
        WI_06(["WI-06"]):::wi
    end
    subgraph Interfaces["Interfaces"]
        direction TB
        ICD_03[/"ICD-03"/]:::icd
    end
    subgraph Risks["Risks"]
        direction TB
        R_005(("R-005")):::risk
        R_008(("R-008")):::risk
    end
    subgraph TR_Gates["TR Gates"]
        direction TB
        TR1{{"TR1"}}:::gate
        TR2{{"TR2"}}:::gate
        TR3{{"TR3"}}:::gate
        TR5{{"TR5"}}:::gate
        TR6{{"TR6"}}:::gate
    end

    WI_05 -->|"supports"| ICD_03
    WI_05 -->|"mitigates"| R_005
    WI_05 -->|"mitigates"| R_008
    WI_05 -->|"satisfies"| TR1
    WI_05 -->|"satisfies"| TR2
    WI_05 -->|"satisfies"| TR3
    WI_05 -->|"satisfies"| TR5
    WI_05 -->|"satisfies"| TR6
    WI_05 -->|"繞組規格 + IL_rms"| WI_01
    WI_05 -->|"熱保護邏輯"| WI_03
    ICD_03 -->|"links"| WI_05
    WI_01 -->|"feeds"| WI_05
    WI_03 -->|"feeds"| WI_05
    WI_04 -->|"depends_on"| WI_05
    WI_06 -->|"depends_on"| WI_05

    classDef wi fill:#e1f5ff,stroke:#0288d1
    classDef icd fill:#fce4ec,stroke:#ad1457
    classDef mc fill:#e8f5e9,stroke:#388e3c
    classDef tc fill:#fff3e0,stroke:#f57c00
    classDef ev fill:#f3e5f5,stroke:#7b1fa2
    classDef risk fill:#ffebee,stroke:#c62828
    classDef gate fill:#fffde7,stroke:#f9a825
    classDef kc fill:#e0f2f1,stroke:#00796b
    classDef p fill:#fafafa,stroke:#616161
    classDef center fill:#fff,stroke:#000,stroke-width:3px,font-weight:bold
```

<!-- AUTO-GRAPH:END -->

---

## 溯源

| WI 章節 | TRIZ 來源 |
|:--------|:----------|
| 環形 PCB 配合 coaxial 封裝 | 系統規格 + WI-04 |
| MCU 過熱保護邏輯 | WI-03 Step 5 |
| Pedaling Torque/Angle 感測 | FA components / 系統規格 |
| EMI 屏蔽（vs Halbach 漏磁） | R-005 緩解 |

## 設計輸入

| 參數 | 值 | 單位 | 來源 |
|:-----|:---|:-----|:-----|
| Form factor | 環形 OD ≤ 105 mm，內徑 ≥ 30 mm（讓中軸通過） | mm | WI-04 |
| Power input | 36V/48V battery | V | 標準 e-bike |
| Phase current | 從 WI-01 IL_rms | A | WI-01 |
| MOSFET T_j_max | 150 | °C | datasheet |
| Operating ambient | -20 ~ +60 | °C | 工況 |

## Step 1: PCB Layout

1. 環形 4 層板（power plane + signal + GND）
2. 6 顆 MOSFET（3-phase H-bridge）配置在外環，散熱面朝外（接 Al endcap heat path）
3. MCU + gate driver 內環
4. 扭力感測器接口 + 角度感測器接口在內環

## Step 2: MCU 韌體規格

依 WI-03 Step 5 實作熱保護：

| T_winding | 動作 |
|:----------|:-----|
| < 110°C | Normal |
| 110~115°C | 限流 80% |
| 115~118°C | 限流 50% + 騎士告警 |
| > 118°C | 切斷輸出 |

NTC 訊號鏈：3-wire bridge，ADC 12-bit，精度 ≤ ±2°C @ 工作範圍

## Step 3: 扭力/角度感測

| 元件 | 類型 | 廠商範例 |
|:-----|:-----|:---------|
| 扭力感測器 | NCTE 磁致伸縮（hollow shaft） | NCTE 2400 series |
| 角度感測器 | 磁編碼器 + 12-bit | AS5048 / AMS |

整合於中軸：
- NCTE sensor 環繞中軸 ~10 mm 段
- AS5048 + 軸端磁鐵 4 mm OD

## Step 4: EMI 屏蔽（R-005 緩解）

1. Halbach 漏磁進入 PCB 區估算（FEA-Mag from WI-01）
2. PCB 與 rotor 間距離 ≥ 8 mm + 軟磁屏蔽片（mu-metal 0.3 mm）
3. 訊號線雙絞 + ferrite bead
4. ADC 訊號線遠離 MOSFET PWM 路徑

## Step 5: 散熱介面

1. MOSFET TIM (thermal interface material) + endcap Al 散熱
2. 電解電容遠離 NdFeB 區（避高溫）

## 驗證

- V11 PCB 功能：基本通訊、PWM 輸出
- V12 EMI：訊號雜訊 < 5% baseline
- V14 系統整合：全功率輸出 + 熱保護觸發

## 交付物

| # | 交付物 | 接收者 |
|:--|:-------|:-------|
| 1 | PCB schematic + layout (Gerber) | 採購 |
| 2 | MCU firmware spec (熱保護 + control loop) | EE |
| 3 | 感測器選型 + spec sheet | 採購 |
| 4 | EMI 屏蔽方案 | WI-04, ICD-03 |
| 5 | BOM 元件清單 | 採購 |

### TR Gate Checklist

| Gate | 檢查項目 |
|:-----|:---------|
| TR1 | PCB block diagram + 熱保護邏輯確認 |
| TR2 | 元件 nominated（MOSFET、MCU、sensor）；EMI 模擬通過 |
| TR3 | Layout + Gerber 凍結；DFM PCB review |
| TR5 | PCB 上電功能 + sensor signal 確認 |
| TR6 | V11、V12、V14 |
