# e-Bike Mid-Mounted Drive Unit v2 — 工程執行指引

> **來源**: TRIZ Session `session-2026-04-21-ebike-drive-unit-v2.md` (CCI=0.35, Weak Evolution)
> **目的**: 將 TRIZ 概念規格轉化為 RD 可獨立執行的作業指導書

---

## 文件總覽

本目錄包含從 TR0（概念凍結）到 TR6（Alpha 驗證）所需的全部工程執行文件。

### 框架文件

| 文件 | 用途 |
|:-----|:-----|
| [TR Gate Framework](tr_gate_framework.md) | TR0-TR10 定義、退出條件、子系統成熟度 |
| [Critical Path](critical_path.md) | WI 間依賴關係、時程、里程碑 |
| [Risk Register](risk_register.md) | Top 技術風險、對策、追蹤狀態 |

### 作業指導書 (Work Instructions)

每份 WI 為步驟式程序，使用祈使語氣，目標讀者為 3-5 年經驗的域工程師。

| WI# | 名稱 | 負責域 | 狀態 |
|:----|:-----|:-------|:-----|
| [WI-01](work_instructions/WI-01_afm_magnetic_circuit.md) | AFM 磁路設計程序 | 馬達/電磁 | — |
| [WI-02](work_instructions/WI-02_harmonic_drive_design.md) | 諧波齒輪設計程序 | 機構/齒輪 | — |
| [WI-03](work_instructions/WI-03_pcm_thermal_management.md) | PCM 熱管理設計程序 | 熱流 | — |
| [WI-04](work_instructions/WI-04_structural_integration_cad.md) | 結構整合與 CAD 組裝程序 | 結構/機械 | — |
| [WI-05](work_instructions/WI-05_annular_pcb_design.md) | 環形 PCB 設計程序 | 電子/韌體 | — |
| [WI-06](work_instructions/WI-06_prototype_build_test.md) | 原型製作與測試程序 | 系統整合 | — |
| [WI-07](work_instructions/WI-07_material_procurement.md) | 材料採購與供應商管理 | 採購/品保 | — |
| [WI-08](work_instructions/WI-08_galvanic_corrosion_prevention.md) | 電偶腐蝕防護程序 | 材料/表面 | — |

### 介面控制文件 (ICD)

| ICD# | 介面 |
|:-----|:-----|
| [ICD-01](interface_control/ICD-01_motor_to_shell.md) | 馬達 ↔ 殼體 |
| [ICD-02](interface_control/ICD-02_gearbox_to_shell.md) | 齒輪箱 ↔ 殼體 |
| [ICD-03](interface_control/ICD-03_pcb_to_endcap.md) | PCB ↔ 端蓋 |
| [ICD-04](interface_control/ICD-04_shell_halves.md) | 殼體上蓋 ↔ 下蓋 |

### FEA 材料卡 (Material Cards)

| MC# | 材料 | 用途 |
|:----|:-----|:-----|
| [MC-01](material_cards/MC-01_ndfeb_n42sh.md) | NdFeB N42SH | AFM 轉子磁石 |
| [MC-02](material_cards/MC-02_smc_somaloy700_5p.md) | Somaloy 700 5P | AFM 定子芯 |
| [MC-03](material_cards/MC-03_cocrmo_f1537.md) | CoCrMo wrought | 諧波柔輪 |
| [MC-04](material_cards/MC-04_cfpeek_30cf.md) | CF-PEEK 30%CF | 諧波剛輪 |
| [MC-05](material_cards/MC-05_az91d.md) | AZ91D | 殼體 |
| [MC-06](material_cards/MC-06_rt55_pcm.md) | RT55 石蠟 | PCM 熱管理 |

---

## 系統架構速覽

```
e-Bike Drive Unit v2 (OD111mm × 92mm, ≤2500g)
│
├── Motor: Axial Flux IPM (雙轉子夾定子)
│   Ø100mm(ID30mm), 軸向18mm, NdFeB N42SH, SMC Somaloy 700 5P
│   8極12槽集中繞組, MTPA+場弱, 目標 ≥5Nm
│
├── Gearbox: 諧波齒輪 1:25-30 單級
│   CoCrMo wrought 柔輪 + CF-PEEK 30%CF 剛輪
│   軸向28mm, η≈85%, 噪聲≤HPR50
│
├── Shell: AZ91D 薄壁(2.5-4mm) + SUS304嵌件
│   PCM RT55 ~250g 石蠟夾層 + 淺鰭片
│
├── Board: 環形PCB嵌入端蓋, 軸向8mm
├── Sensor: 磁致伸縮扭矩感測器, 軸向5mm
│
├── 軸向: 18+28+8+5 = 59mm << 92mm (裕量 33mm)
└── 重量: ~2350g < 2500g (裕量 150g)
```

---

## 使用方式

1. 閱讀 [TR Gate Framework](tr_gate_framework.md) 了解當前所在階段
2. 查看 [Critical Path](critical_path.md) 確認哪些 WI 可並行、哪些有依賴
3. 依 WI 編號順序（或並行路徑）逐份執行
4. 每個 TR Gate 前，對照退出條件自查
5. 風險項目在 [Risk Register](risk_register.md) 追蹤

**關鍵原則**：WI 告訴你「怎麼做」；TRIZ session 告訴你「為什麼這樣做」。遇到設計判斷困難時，回溯 TRIZ session 中的 PC/分離策略可以找到設計意圖。
