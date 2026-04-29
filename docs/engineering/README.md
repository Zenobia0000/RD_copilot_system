# Engineering Deliverables — e-Bike Mid-Drive Unit (Coaxial v3)

> **TRIZ Session**: 2026-04-28-1500-eBike-MidDrive-Coaxial
> **Verdict**: Evolution (Weak Evolution, CCI=0.3125) — Gate P **Go**
> **產生日期**: 2026-04-28
> **整體信心**: Weak Evolution — 部分項目（C-B002 Halbach FEA、C-B004 CFRP、C-C002 HPR50 噪音）需實驗補強

---

## 系統架構（Coaxial Topology）

```
                      OD 111 mm × Axial 92 mm
    ┌───────────────────────────────────────────┐
    │  ┌─────────────────────────────────────┐  │
    │  │  Pedaling Shaft + Torque/Angle Sensor│  │  ← 中軸感測 (WI-05)
    │  └────────────┬────────────────────────┘  │
    │               │ coaxial through                 │
    │  ┌──────────────────────────────────────┐  │
    │  │  Halbach NdFeB Rotor + CFRP Sleeve   │  │  ← 馬達 (WI-01)
    │  │  ┌──────────────────────────────┐    │  │
    │  │  │ SMC Somaloy 700-5P Stator    │    │  │
    │  │  │ + Cu Hairpin Winding         │    │  │
    │  │  └──────────────────────────────┘    │  │
    │  └──────────────────────────────────────┘  │
    │  ┌──────────────────────────────────────┐  │
    │  │  Stage 1: Planetary 1:5              │  │  ← 齒輪 (WI-02)
    │  │  Stage 2: Eccentric Cycloidal 1:6.5  │  │     雙級 = 1:32.5
    │  └──────────────────────────────────────┘  │
    │  ┌──────────────────────────────────────┐  │
    │  │  Cu Insert + RT55 PCM Layer          │  │  ← 熱管理 (WI-03)
    │  │  in Al-6061 Housing                  │  │
    │  └──────────────────────────────────────┘  │
    │  ┌──────────────────────────────────────┐  │
    │  │  Annular Drive Board (MOSFET + MCU)  │  │  ← 電子 (WI-05)
    │  └──────────────────────────────────────┘  │
    └───────────────────────────────────────────┘
                Output Sprocket → Chain
```

---

## 文件索引

### 框架文件（4 份）

| 檔案 | 用途 |
|:-----|:-----|
| `README.md` | 本檔案，工程體系總覽 |
| `tr_gate_framework.md` | TR0-TR10 閘門定義（唯一權威來源） |
| `critical_path.md` | WI 依賴 DAG + 關鍵路徑 |
| `risk_register.md` | 風險登記冊 |

### Work Instructions（7 份，`work_instructions/`）

| WI | 域 | 對應 TC | 負責 |
|:---|:---|:--------|:-----|
| WI-01 | Halbach 馬達 + SMC + CFRP | TC-B | EE/ME |
| WI-02 | 雙級減速 + 齒面修形 + EHD | TC-C | ME |
| WI-03 | Cu 嵌件 + RT55 PCM 熱管理 | TC-A | ME/Thermal |
| WI-04 | Al-6061 Coaxial Housing 結構整合 | 多 TC | ME |
| WI-05 | 環形 Drive Board + 扭力感測 | — | EE |
| WI-06 | V1-V14 測試與驗證計畫 | 全 TC | QA/Test |
| WI-07 | 採購與長交期物料 | — | SCM |

### Interface Control Documents（4 份，`interface_control/`）

| ICD | 介面 |
|:----|:-----|
| ICD-01 | Motor Stator ↔ Housing（Cu 嵌件熱接觸） |
| ICD-02 | Gearbox ↔ Housing（軸承座 + 油浴密封） |
| ICD-03 | Drive Board ↔ Endcap（PCB 散熱 + EMI 屏蔽） |
| ICD-04 | Housing Halves（外殼分模 + O-ring 密封 + IP 等級） |

### Material Cards（6 份，`material_cards/`）

| MC | 材料 | 對應 Evidence |
|:---|:-----|:--------------|
| MC-01 | NdFeB N42SH（Halbach 磁鐵） | C-B001 |
| MC-02 | SMC Somaloy 700-5P（Stator iron） | C-B003 |
| MC-03 | CFRP T700（轉子套筒） | C-B004 |
| MC-04 | Al-6061-T6（Housing） | C-A002 |
| MC-05 | Cu C11000（熱嵌件） | C-A001 |
| MC-06 | RT55（PCM） | C-A003, C-A004 |

### KC List

| 檔案 | 內容 |
|:-----|:-----|
| `kc_list.md` | Key Characteristics 清單，Critical/Major/Minor 分類 |

---

## TRIZ 溯源摘要

3 個 TC 的解法摘要：

| TC | 解法 (一句話) | 主分離 | 嵌套 |
|:---|:--------------|:-------|:-----|
| TC-A | Cu 嵌件 + RT55 PCM 在 Al housing 內襯 | 空間 | 整體局部 |
| TC-B | Halbach NdFeB N42SH + SMC stator + CFRP 套筒 | 空間 | 整體局部 |
| TC-C | 齒面 Δδ 修形 + 雙級減速分配 + EHD 油膜 | 空間 | 整體局部 + 條件 |

**SIM 收斂**：第 1 輪 -1 數=0 → CONVERGED；2 條協同效應（A×B 散熱解鎖功率密度；A×C 油浴雙重利用）。

完整 TRIZ session 報告見 `.claude/context/triz/session-2026-04-28-1500-eBike-MidDrive-Coaxial.md`。

---

## 閱讀指引

| 角色 | 起點 |
|:-----|:-----|
| PM/系統工程師 | README → critical_path → tr_gate_framework |
| 馬達 EE | WI-01 → MC-01/02/03 → ICD-01 |
| 機械 ME | WI-02 → WI-04 → MC-04/05 → ICD-02/04 |
| 熱工程師 | WI-03 → MC-04/05/06 → ICD-01 |
| 電子工程師 | WI-05 → ICD-03 |
| 測試 QA | WI-06 → kc_list |
| 供應鏈 | WI-07 → 全部 MC |
