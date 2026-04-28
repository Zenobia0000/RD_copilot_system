# Block 8 Deep-Dive — 實際產出與能力展示

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：Block 8「實際產出與能力展示」的單頁展開稿，展示系統已經真正產出了什麼

---

## 1. 這頁要回答的一個問題

> 這套系統不只是概念——它到目前為止實際產出了哪些可交付的工程文件？

## 2. 一句話 Key Message

> 系統已從一個真實案例中產出 8 份 Work Instruction、6 份 Material Card、4 份 Interface Control Document，加上完整的 Gate 框架與風險登記——這不是 demo，是可工程審查的交付物。

## 3. 版面配置建議

```
┌──────────────────────────────────────────────────────────────┐
│                           頁面標題                             │
│  不只是概念：系統已產出 18+ 份可工程審查的交付物                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  A. 五大能力區塊（上方橫列）                                     │
│                                                              │
│  約束萃取 → 矛盾解析 → 方案探索 → 狀態追溯 → 工程文件橋接        │
│                                                              │
├───────────────────────────┬──────────────────────────────────┤
│                           │                                  │
│  B. 交付物清單             │  C. 文件流向圖                    │
│  (WI/MC/ICD 列表)         │  (TRIZ → WI/MC/ICD → TR Gate)   │
│                           │                                  │
├───────────────────────────┴──────────────────────────────────┤
│                                                              │
│  D. 數字摘要列                                                │
│  8 WI │ 6 MC │ 4 ICD │ 10 Gate │ 1 Risk Register             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 4. 主要內容

### A. 五大能力區塊

| # | 能力 | 對應 Phase | 說明 |
|:--|:-----|:----------|:-----|
| 1 | **約束萃取** | P0 SCOPE | 從問題描述自動識別設計約束、OZ/OT、操作參數 |
| 2 | **矛盾解析** | P1-P2 | FA + SF 功能建模 → TC 識別 → PC 物理矛盾 → 分離策略 |
| 3 | **方案探索** | P2-P3 | 三路徑解題（TC/PC/SF）、科學效應匹配、SIM 矩陣 |
| 4 | **狀態追溯** | 全程 | 雙層 state machine 追蹤 TRIZ session + TR gate 進展 |
| 5 | **工程文件橋接** | P3→TR0 | 從 TRIZ 解法自動產出 WI / MC / ICD，銜接 TR 工程執行 |

### B. 已產出交付物清單

**Work Instructions（8 份）**

| 編號 | 名稱 | 涵蓋子系統 |
|:-----|:-----|:----------|
| WI-01 | AFM Magnetic Circuit Design | 馬達 / 電磁設計 |
| WI-02 | Harmonic Drive Design | 減速機構 |
| WI-03 | PCM Thermal Management | 熱管理 |
| WI-04 | Structural Integration CAD | 結構整合 |
| WI-05 | Annular PCB Design | 電路板 |
| WI-06 | Prototype Build & Test | 原型組裝測試 |
| WI-07 | Material Procurement | 材料採購 |
| WI-08 | Galvanic Corrosion Prevention | 防蝕處理 |

**Material Cards（6 份）**

| 編號 | 材料 | 用途 |
|:-----|:-----|:-----|
| MC-01 | NdFeB N42SH 永磁 | 馬達轉子 |
| MC-02 | SMC Somaloy 700 5P | 馬達定子鐵芯 |
| MC-03 | CoCrMo F1537 | 高強度結構件 |
| MC-04 | CF-PEEK 30% Carbon Fiber | 輕量化殼體 |
| MC-05 | AZ91D Magnesium Alloy | 外殼 |
| MC-06 | RT55 Phase-Change Material | 熱管理介質 |

**Interface Control Documents（4 份）**

| 編號 | 介面 | 管控什麼 |
|:-----|:-----|:---------|
| ICD-01 | Motor ↔ Shell | 馬達與殼體介面公差、密封、散熱路徑 |
| ICD-02 | Gearbox ↔ Shell | 減速機與殼體配合、軸承座、潤滑 |
| ICD-03 | PCB ↔ Endcap | 電路板與端蓋固定、訊號走線、EMI |
| ICD-04 | Shell Halves | 上下殼接合、密封膠、螺栓佈局 |

**其他交付物**

| 類型 | 數量 | 說明 |
|:-----|:-----|:-----|
| Gate 框架（TR0-TR10） | 10 個 Gate 定義 | 完整退出條件 + 驗證邏輯 |
| Critical Path Analysis | 1 份 | 專案關鍵路徑識別 |
| Risk Register | 1 份 | 技術債 + 風險追蹤 |

### C. 文件從哪裡來、到哪裡去

```
TRIZ 推理引擎                        TR 工程引擎
─────────────                        ──────────

Step 0-3                              TR1-TR10
矛盾分析 → Solution                    Gate Review
    │                                     ↑
    ▼                                     │
Step 5 (triz-wi)                         │
    ├── WI-01~08  ──────────────────────→ │ FEA/測試/DFM 的輸入
    ├── MC-01~06  ──────────────────────→ │ 材料選用/供應商的依據
    ├── ICD-01~04 ──────────────────────→ │ 系統整合的介面規格
    └── Risk Register ──────────────────→ │ 風險追蹤的起點
```

### D. 數字摘要

| 指標 | 數值 | 意義 |
|:-----|:-----|:-----|
| Work Instructions | **8** 份 | 涵蓋電磁、機構、熱、結構、電路、組裝、採購、防蝕 |
| Material Cards | **6** 份 | 涵蓋磁性材料、SMC、合金、複合材料、相變材料 |
| Interface Control Docs | **4** 份 | 涵蓋所有主要子系統介面 |
| Gate 定義 | **10** 個 | TR1-TR10 完整退出條件 |
| 總交付物 | **20+** 件 | 從一個真實案例（e-Bike drive unit）產出 |

## 5. 建議視覺元素

| 元素 | 類型 | 內容描述 |
|:-----|:-----|:---------|
| **五能力橫列** | 5 格圖標列 | 每格一個能力名 + icon，用箭頭串連 |
| **交付物數字卡** | 底部大字數字列 | 8 WI / 6 MC / 4 ICD / 10 Gate，用不同色塊 |
| **文件流向圖** | 左→右箭頭流程 | TRIZ Solution → triz-wi → {WI, MC, ICD} → TR Gate |
| **WI/MC/ICD 清單** | 三欄表格並排 | 左：WI 列表、中：MC 列表、右：ICD 列表 |

## 6. 口條骨架（25 秒）

> 這一頁是實際產出。上面五個區塊是系統目前已具備的能力——從約束萃取到工程文件橋接。下面是從一個真實案例——e-Bike drive unit——實際產出的文件：8 份 Work Instruction、6 份 Material Card、4 份 Interface Control Document，加上完整的 Gate 框架跟風險登記。這些不是 demo——每一份都可以拿去做工程審查。右邊這張圖說明文件怎麼從 TRIZ 推理流到 TR 工程執行。

## 7. 來源文件索引

| 內容 | 來源 |
|:-----|:-----|
| 五大能力區塊 | `docs/planning/ppt/19_internal_pitch_strategy.md` §Current Capabilities |
| WI/MC/ICD 清單 | `docs/engineering/tr_gate_framework.md` |
| 實際交付物存檔 | `docs/engineering/archive/pre-uat-2026-04-28/` |
| 文件產出流程（triz-wi） | `docs/methodology/DK-04--data-model-and-gate.md` §TRIZ Step 5 → TR0 Handoff |
| 功能模組範圍 | `docs/planning/02_prd.md` §Functional Requirements |
