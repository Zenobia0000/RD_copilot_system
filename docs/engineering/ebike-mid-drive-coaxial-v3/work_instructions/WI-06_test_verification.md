---
id: WI-06
type: WI
title: V1-V14 測試與驗證計畫
domain: test
version: 1.0
date: 2026-04-28
effort_weeks: 8
owner: QA/Test

# 橫切 WI — 驗證所有 TC 解法
traces_to: [TC-A, TC-B, TC-C, SOL-TCA, SOL-TCB, SOL-TCC]
depends_on:
  - target: WI-01
    artifact: Halbach 馬達 (V1-V4)
  - target: WI-02
    artifact: 齒輪箱 (V5-V8)
  - target: WI-03
    artifact: 熱管理 (V10, V13)
  - target: WI-05
    artifact: PCB + 整機 (V11, V12, V14)
mitigates: [R-002, R-008, R-009, R-010]
satisfies_gates: [TR4, TR6, TR9]
---

# WI-06: V1-V14 測試與驗證計畫

> **版本**: 1.0 | **日期**: 2026-04-28
> **負責域**: 測試與驗證
> **前置條件**: WI-01~05 子系統設計凍結
> **產出物**: 驗證矩陣、測試規格、治具設計、Pass/Fail 判定
> **預估工時**: 4 週測試治具 + 4-6 週實測
> **阻塞下游**: TR6 Alpha 驗證 → TR9 DVP&R


## Relations Graph (auto-generated)

<!-- AUTO-GRAPH:START view=ego -->

```mermaid
flowchart LR
    WI_06(["<b>WI-06</b><br/>V1-V14 測試與驗證計畫"]):::center

    subgraph TRIZ_溯源["TRIZ 溯源"]
        direction TB
        SOL_TCA["SOL-TCA"]:::tc
        SOL_TCB["SOL-TCB"]:::tc
        SOL_TCC["SOL-TCC"]:::tc
        TC_A["TC-A"]:::tc
        TC_B["TC-B"]:::tc
        TC_C["TC-C"]:::tc
    end
    subgraph 相關_WI["相關 WI"]
        direction TB
        WI_01(["WI-01"]):::wi
        WI_02(["WI-02"]):::wi
        WI_03(["WI-03"]):::wi
        WI_05(["WI-05"]):::wi
    end
    subgraph Risks["Risks"]
        direction TB
        R_002(("R-002")):::risk
        R_008(("R-008")):::risk
        R_009(("R-009")):::risk
        R_010(("R-010")):::risk
    end
    subgraph TR_Gates["TR Gates"]
        direction TB
        TR4{{"TR4"}}:::gate
        TR6{{"TR6"}}:::gate
        TR9{{"TR9"}}:::gate
    end

    WI_06 -->|"traces_to"| TC_A
    WI_06 -->|"traces_to"| TC_B
    WI_06 -->|"traces_to"| TC_C
    WI_06 -->|"traces_to"| SOL_TCA
    WI_06 -->|"traces_to"| SOL_TCB
    WI_06 -->|"traces_to"| SOL_TCC
    WI_06 -->|"mitigates"| R_002
    WI_06 -->|"mitigates"| R_008
    WI_06 -->|"mitigates"| R_009
    WI_06 -->|"mitigates"| R_010
    WI_06 -->|"satisfies"| TR4
    WI_06 -->|"satisfies"| TR6
    WI_06 -->|"satisfies"| TR9
    WI_06 -->|"Halbach 馬達 (V1-V4)"| WI_01
    WI_06 -->|"齒輪箱 (V5-V8)"| WI_02
    WI_06 -->|"熱管理 (V10, V13)"| WI_03
    WI_06 -->|"PCB + 整機 (V11, V12, V14)"| WI_05

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

## 溯源（從 Step 4 驗證計畫）

| 驗證 ID | 對應 TC / SOL | TRIZ 來源 |
|:--------|:--------------|:----------|
| V1 (B_g) | SOL-TCB | TC-B Halbach 增益 |
| V2 (peak torque density) | SOL-TCB | TC-B 扭力密度 |
| V3 (cogging) | SOL-TCB | Halbach 製造容差 R-005 |
| V4 (efficiency map) | SOL-TCB / Loss map | WI-01 |
| V5 (peak torque hold) | SOL-TCC | TC-C |
| V6 (gearbox efficiency) | SOL-TCC | EHD |
| V7 (NVH dB(A)) | SOL-TCC | 噪音目標（**R-002 待 baseline**） |
| V8 (durability initial 1k cycles) | SOL-TCC | 修形齒疲勞 |
| V9 (system efficiency) | 全 TC | 整機 |
| V10 (peak 30s 溫升) | SOL-TCA | TC-A PCM |
| V11 (PCB function) | WI-05 | 控制 |
| V12 (EMI) | R-005 | 漏磁干擾 |
| V13 (cont 1hr housing T) | SOL-TCA | PCM 飽和邊界 |
| V14 (system integrated) | 全 TC + SIM 協同 | A×B、A×C |

## 驗證矩陣

| ID | 項目 | 量測指標 | Pass 標準 | 設備 | TR Gate |
|:---|:-----|:---------|:----------|:-----|:--------|
| **V1** | Halbach B_g | T (air gap 中心) | ≥ 0.85 T | Hall probe (Lakeshore) | TR6 Phase A |
| **V2** | Peak torque density | T_peak / m | ≥ 50 Nm/kg | Dyno (Magtrol) + 重量 | TR6 Phase A |
| **V3** | Cogging torque | % peak | ≤ 5% | Dyno 微調轉速 | TR6 Phase A |
| **V4** | Efficiency map | η vs (RPM, T) | ≥ 88% peak | Dyno + power analyzer | TR6 Phase A |
| **V5** | Gearbox peak hold | torque @ 125 Nm × 10s | 無破壞 | Dyno | TR6 Phase B |
| **V6** | Gearbox efficiency | η_gear | ≥ 92% (1:32.5) | Dyno 雙端扭矩 | TR6 Phase B |
| **V7** | NVH | dB(A) @ 1m, 60 rpm cadence | ≤ HPR50 baseline | 半消音室 + microphone array | TR6 Phase B |
| **V8** | Durability initial | 1,000 cycles 100 Nm | 無齒面磨耗超 spec | Dyno cycle | TR6 Phase B |
| **V9** | System efficiency | wheel power / battery power | ≥ 80% | 整機 dyno | TR6 Phase D |
| **V10** | Peak 30s 溫升 | T_winding | < 120°C | 嵌入式 NTC + IR | TR6 Phase C |
| **V11** | PCB function | Phase current, comm | 基本功能 | bench test | TR6 Phase D |
| **V12** | EMI | sensor noise | < 5% signal | scope + EMI 環境 | TR6 Phase D |
| **V13** | Cont 1hr housing T | T_surface | ≤ 80°C | thermal couple + IR | TR6 Phase C |
| **V14** | Integrated | 同步通過 V1-V13 | 全 PASS | full setup | TR6 Phase D |

## DVP&R 計畫骨架（TR9）

| 類別 | 測試 | 標準 |
|:-----|:-----|:-----|
| 耐久 | 100,000 cycles 125 Nm peak | 無破壞、無 retention loss > 5% |
| 環境 | -20 / +50°C 全溫域功能 | spec 達標 |
| 防水 | IP67 浸泡 30 min | 無進水 |
| 安全 | EN 15194 / ISO 4210 | 通過 |
| EMC | EN 15194 EMC 部分 | 通過 |

## 測試治具

| 治具 | 用途 | 備註 |
|:-----|:-----|:-----|
| Coaxial dyno 接口 | 接 motor input + output sprocket | 兩端扭矩量測 |
| Hall probe fixture | air gap 量測 | 可旋轉量測軸向均勻性 |
| 半消音室固定架 | NVH | 振動隔離 + microphone 1m 標定 |
| Climatic chamber | -20/+50 環境測試 | TR9 |

## 交付物

| # | 交付物 | 接收者 |
|:--|:-------|:-------|
| 1 | V1-V14 測試規格 + 治具 | 測試實驗室 |
| 2 | 測試報告（每項 1 份） | TR6 review |
| 3 | DVP&R 計畫（TR9 用） | TR9 |
| 4 | FEA-vs-實測對比報告 | 模型修正 |

### TR Gate Checklist

| Gate | 檢查項目 |
|:-----|:---------|
| TR4 | 治具設計完成；測試實驗室排程 |
| TR6 | V1-V14 全 pass；FEA 偏差 < 20% |
| TR9 | DVP&R 全項通過 |
