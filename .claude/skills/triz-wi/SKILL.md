---
name: triz-wi
description: TRIZ Step 5 工程作業指導書產出。將 Step 4 驗證通過的 TRIZ 概念轉化為 WI、ICD、FEA Material Card，橋接 TRIZ 分析與 RD 工程執行。Use when TRIZ concept output needs to be translated into actionable engineering Work Instructions, Interface Control Documents, and Material Cards.
---

# TRIZ Step 5: 工程作業指導書產出 (WI / ICD / Material Card)

## Overview

正在使用 triz-wi skill — 執行 Step 5: 工程作業指導書產出。

本 skill 實作 Auto-TRIZ 閉環流程的 Step 5，銜接 Step 4 驗證通過的概念規格，產出 RD 工程師可直接執行的作業指導書體系。

**前提條件（強制）：**
- Step 4 必須已完成（`step4.completed === true`）
- Step 4 判定必須為 evolution（`step4.verdict === "evolution"`）
- 若 verdict 為 patch → **拒絕執行**，告知使用者：「Step 4 判定為補丁，請先執行 `/triz-solve` 解決根本矛盾後再產出工程指導書。」

---

## 輸入要求

從 `.claude/context/triz/.triz-state.json` 讀取以下資料：

| 必要輸入 | JSON 路徑 | 說明 |
|:---------|:----------|:-----|
| Step 4 完成狀態 | `step4.completed` | 必須為 `true` |
| Step 4 判定結果 | `step4.verdict` | 必須為 `"evolution"` |
| CCI 判定 | `step4.cci_verdict` | Strong/Weak Evolution |
| TC 解法方案 | `step3.solutions` | 每個 TC 的 F/S/OZ/OT |
| Evidence Registry | `step4.evidence_registry` | 已驗證的材料/性能聲明 |
| 觀察項目 | `step4.observation_items` | 風險與待觀察事項 |
| 系統規格 | `specs` | 系統層級規格參數 |
| 報告檔路徑 | `report_file` | Session 報告檔路徑 |

另外讀取 session 報告檔（從 `state.report_file` 取得路徑），取得完整的 TRIZ 分析上下文。

### 入口檢查流程

```
讀取 .claude/context/triz/.triz-state.json
│
├─ step4.completed !== true
│  └─ 拒絕：「Step 4 尚未完成。請先執行 /triz-verify 完成驗證。」
│
├─ step4.verdict === "patch"
│  └─ 拒絕：「Step 4 判定為補丁（{cci_verdict}），無法產出工程指導書。
│           請先執行 /triz-solve 重新深挖矛盾，或以 /triz-verify 重新驗證。」
│
├─ step4.verdict === "evolution"
│  ├─ cci_verdict === "Strong Evolution"
│  │  └─ 正常執行，所有 WI 標記「高信心」
│  │
│  └─ cci_verdict === "Weak Evolution"
│     └─ 正常執行，但在每份 WI 中標記高分項為「未來改進方向」
│
└─ 其他 → 拒絕：「無法辨識 Step 4 判定狀態，請執行 /triz-status 檢查。」
```

---

## Phase 1: 子系統分類（域分解）

分析 Step 3 的 TRIZ 解法（F/S/OZ/OT），自動辨識涉及哪些工程域。

### 偵測規則

| 工程域 | 偵測規則 | WI 類型 |
|:-------|:---------|:--------|
| 電磁（馬達/致動器） | F 包含 "magnetic"/"electromagnetic"/"磁"/"電磁"，S 包含 magnet/coil/iron/磁鐵/線圈/鐵芯 | WI-motor |
| 機械（齒輪/機構） | F 包含 "mechanical"/"機械"，S 包含 gear/bearing/shaft/齒輪/軸承/軸 | WI-gear |
| 熱管理（散熱/冷卻） | F 包含 "thermal"/"熱"，S 包含 PCM/heatsink/fin/散熱/相變/鰭片 | WI-thermal |
| 結構（外殼/框架） | 多子系統交互 + S 包含 shell/housing/frame/外殼/框架/機殼 | WI-structural |
| 電子（PCB/控制） | S 包含 PCB/MCU/driver/sensor/電路板/微控制器/驅動器/感測器 | WI-electronics |
| 測試與驗證 | **永遠產出**（若 step4 有 observation_items 或驗證計畫） | WI-test |
| 採購 | **永遠產出**（若 evidence_registry 中有材料項目） | WI-procurement |
| 表面/防蝕 | observation_items 包含 corrosion/galvanic/腐蝕/電化學 | WI-corrosion |

### 執行步驟

1. 遍歷 `step3.solutions` 中所有 TC 的 F/S/OZ/OT 欄位
2. 對每個域，用上表的偵測規則進行模式匹配（不區分大小寫）
3. 額外檢查 `step4.observation_items` 和 `step4.evidence_registry`
4. 彙整結果，列出識別到的工程域清單

### 使用者確認（必要）

呈現分類結果給使用者，格式如下：

```markdown
## 子系統分類結果

根據 TRIZ 解法分析，識別到以下工程域：

| # | 工程域 | WI 類型 | 觸發依據 |
|:--|:-------|:--------|:---------|
| 1 | {domain} | WI-{type} | {哪個 TC/F/S 觸發} |
| 2 | ... | ... | ... |

請確認此分類是否正確，或需要新增/移除域。
[1] 確認，繼續產出
[2] 需要調整（請說明）
```

**等待使用者確認後才進入 Phase 2。**

---

## Phase 2: 框架文件產出（循序）

框架文件必須在 WI 之前完成，因為 WI 會引用框架內容。

產出以下 4 份框架文件至 `docs/engineering/`：

### 2.1 `docs/engineering/README.md` — 工程體系總覽

內容包含：
- 系統架構圖（ASCII art，標示各子系統與介面）
- WI/ICD/MC 文件索引表
- TRIZ session 溯源（session_id、TC 摘要、verdict）
- 各域負責範圍與交付物總覽
- 閱讀指引（誰該看哪些文件）

### 2.2 `docs/engineering/tr_gate_framework.md` — TR 閘門定義

定義 TR0 到 TR10 各閘門的退出條件。**此檔案是 TR 定義的唯一權威來源**，所有 WI 的 TR Gate Checklist 必須引用此檔案。

```markdown
| 閘門 | 名稱 | 退出條件 | 必要交付物 |
|:-----|:-----|:---------|:-----------|
| TR0 | 概念凍結 | TRIZ 概念通過 CCI 驗證（Evolution） | 工程規格書、Evidence Registry |
| TR1 | 可行性分析 | 各子系統 FEA/CFD 獨立通過 | WI-01~03 FEA 報告、Loss map、MC 確認 |
| TR2 | 設計參數鎖定 | 軸承選定、齒形確定、ICD 簽核 | 4 份 ICD、軸承規格、齒輪參數表 |
| TR3 | 詳細設計 | 完整 3D CAD + GD&T + BOM 凍結 | WI-04 CAD 組裝、公差鏈、BOM |
| TR4 | 原型備料 | 長交期物料下單、治工具設計 | WI-07 採購狀態、治具圖面 |
| TR5 | Alpha 原型 | 功能原型組裝 | 組裝報告、手轉功能確認 |
| TR6 | Alpha 驗證 | V1-V14 全項實測通過 | WI-06 測試報告、FEA-vs-實測對比 |
| TR7 | Beta 設計 | DFM 修正完成 | 供應商 DFM review 報告 |
| TR8 | Beta 原型 | 量產意圖原型通過 | 尺寸+功能 pass 報告 |
| TR9 | 量產驗證 | DVP&R 全項完成 | PV 測試報告（耐久/環境/安全） |
| TR10 | 量產釋放 | PPAP 等效 | Cpk ≥ 1.33、量產 SOP |
```

各子系統 TR 現況評估表（動態更新）：

```markdown
| 子系統 | 現在 TR | 下一目標 | 主要障礙 | 負責 WI |
|:-------|:--------|:---------|:---------|:--------|
```

### 2.3 `docs/engineering/critical_path.md` — 關鍵路徑

從 WI 的輸入/輸出依賴鏈推導關鍵路徑：
- 繪製 WI 間的依賴圖（ASCII DAG）
- 標示哪些 WI 可並行、哪些必須循序
- 識別最長路徑（即關鍵路徑）
- 標示各 WI 的預估工時與里程碑

### 2.4 `docs/engineering/risk_register.md` — 風險登記冊

來源：
- `step4.observation_items`（每個觀察項轉為風險項）
- Evidence Registry 中 Confidence = LOW 的項目
- Weak Evolution 的高分維度

格式：

```markdown
| Risk ID | 風險描述 | 來源 | 影響域 | 可能性 | 衝擊度 | 緩解措施 | 負責 WI |
|:--------|:---------|:-----|:-------|:-------|:-------|:---------|:--------|
| R-001 | {描述} | {observation/evidence/CCI} | {WI-XX} | H/M/L | H/M/L | {措施} | WI-{XX} |
```

---

## Phase 3: WI 產出（多 Agent 並行）

框架文件完成後，為每個識別到的工程域產出 WI。

### 並行策略

使用 Agent tool 為每個域平行產出 WI：

```
對每個識別到的工程域：
  Agent({
    description: "Generate WI-{domain} work instruction",
    prompt: "
      你是工程作業指導書撰寫專家。請根據以下 TRIZ session 資料，
      為 {domain} 域撰寫 WI 文件。

      TRIZ 解法資料：{step3.solutions}
      Evidence Registry：{step4.evidence_registry}
      觀察項目：{step4.observation_items}
      系統規格：{specs}
      CCI 判定：{step4.cci_verdict}

      嚴格遵守以下 WI 格式要求，產出至 docs/engineering/WI-{NN}_{domain}.md
    "
  })
```

### WI 格式要求（每份 WI 必須遵守）

每份 WI 檔案命名為 `docs/engineering/WI-{NN}_{domain}.md`，編號從 01 開始。

```markdown
# WI-{NN}: {標題}

> **版本**: 1.0 | **日期**: {today, YYYY-MM-DD}
> **負責域**: {domain}
> **前置條件**: {上游 WI 列表，若無則填「無」}
> **產出物**: {本 WI 的交付物清單}
> **預估工時**: {估計值，含單位}
> **阻塞下游**: {下游 WI 列表，若無則填「無」}

---

## 溯源

| WI 章節 | TRIZ 來源 | 類型 | 說明 |
|:--------|:----------|:-----|:-----|
| {章節名} | TC-{N} / PC-{N} / SF-{N} / C-{NNN} | TC/PC/SF/Evidence | {一句話說明為什麼此章節追溯到此 TRIZ 元素} |

## 設計輸入

| 參數 | 值 | 單位 | 來源 | Confidence |
|:-----|:---|:-----|:-----|:-----------|
| {參數名} | {數值} | {單位} | {TRIZ spec / 上游 WI / 標準} | {HIGH/MEDIUM/LOW} |

## Step 1: {程序步驟標題}

{命令式語氣，具體到 3-5 年經驗的 RD 工程師可獨立執行。
 包含：操作步驟、工具/軟體、判定標準、異常處理。}

## Step 2: {程序步驟標題}
...

## Step N: {程序步驟標題}
...

## FEA 設定指引（若適用）

| 項目 | 設定 |
|:-----|:-----|
| 軟體 | {ANSYS/Abaqus/COMSOL/...} |
| 分析類型 | {靜態/瞬態/模態/...} |
| 網格建議 | {元素類型、尺寸、加密區域} |
| 邊界條件 | {載荷、約束、接觸} |
| 材料卡 | MC-{NN}（見 Material Card） |
| 收斂條件 | {能量誤差 / 殘差閾值} |

## 設計凍結與交付

### 交付物清單

| # | 交付物 | 格式 | 接收者 |
|:--|:-------|:-----|:-------|
| 1 | {交付物名稱} | {CAD/PDF/Excel/...} | {ME/EE/QA/...} |

### TR Gate Checklist

（引用 `docs/engineering/tr_gate_framework.md` 定義，僅列出本 WI 涉及的 gate）

| TR Gate | 檢查項目 | 狀態 |
|:--------|:---------|:-----|
| TR1 可行性 | {FEA/CFD 通過、Loss map 完成} | [ ] |
| TR2 參數鎖定 | {軸承選定、ICD 簽核} | [ ] |
| TR3 詳細設計 | {3D CAD + GD&T + BOM 凍結} | [ ] |
| TR5 Alpha | {原型組裝功能確認} | [ ] |
| TR6 驗證 | {V-test 實測 pass} | [ ] |
```

### WI 特殊域說明

#### WI-test（測試與驗證）

除上述格式外，額外包含：
- 驗證矩陣（從 step4 驗證計畫展開）
- 測試規格（量測方法、設備、精度）
- 判定標準（pass/fail 閾值，來自 TRIZ 規格）
- DVT/PVT 計畫骨架

#### WI-procurement（採購）

除上述格式外，額外包含：
- 材料清單（BOM 骨架，從 evidence_registry 展開）
- 供應商評估要點（基於 Evidence Confidence）
- 長交期項目標示
- 替代材料建議（若 Evidence Confidence = LOW）

---

## Phase 4: ICD + Material Card 產出（多 Agent 並行）

WI 全部完成後，產出介面控制文件與材料卡。

### 4.1 ICD 產出

從 WI-structural 與其他 WI 的交叉引用中，識別所有跨域介面。每個介面產出一份 ICD。

使用 Agent tool 並行產出。

ICD 檔案命名為 `docs/engineering/ICD-{NN}_{interface_name}.md`。

```markdown
# ICD-{NN}: {介面名稱}

> **版本**: 1.0 | **日期**: {today, YYYY-MM-DD}
> **相關 WI**: WI-{NN}, WI-{MM}
> **介面雙方**: {子系統 A} <-> {子系統 B}

---

## 介面概述

{一段描述 + ASCII 剖面圖}

```
    ┌──────────┐     ┌──────────┐
    │ 子系統 A  │─────│ 子系統 B  │
    │          │ ←介面→ │          │
    └──────────┘     └──────────┘
```

## 配合規格

| 參數 | A 側 | B 側 | 公差 |
|:-----|:-----|:-----|:-----|
| {尺寸/電氣/熱} | {值} | {值} | {公差} |

## 公差與 GD&T

| 特徵 | 基準 | 公差類型 | 值 |
|:-----|:-----|:---------|:---|
| {特徵名} | {基準面} | {位置度/平面度/...} | {值} |

## 熱/電/密封路徑

{描述熱傳導路徑、電氣連接路徑、密封方案}

## 驗收條件

| 項目 | 方法 | 判定標準 |
|:-----|:-----|:---------|
| {檢查項} | {量測/目視/功能測試} | {pass/fail 標準} |

## 變更管控

- 變更需雙方 WI 負責人簽核
- 影響分析需更新 risk_register.md
- 版本遞增規則：配合規格變更 = 主版本號遞增
```

### 4.2 Material Card 產出

從 `step4.evidence_registry` 中提取所有材料項目，每個材料產出一份 Material Card。

使用 Agent tool 並行產出。

MC 檔案命名為 `docs/engineering/MC-{NN}_{material_name}.md`。

```markdown
# MC-{NN}: {材料名稱}

> **版本**: 1.0 | **日期**: {today, YYYY-MM-DD}
> **來源**: Evidence {C-NNN}
> **適用 WI**: WI-{NN}, WI-{MM}
> **FEA 軟體**: {ANSYS / Abaqus / COMSOL / 通用}

---

## 材料概述

{材料描述、選用理由（追溯到 TRIZ 解法的 S 參數）、適用場景}

## 機械性質

| 性質 | 值 | 單位 | 溫度條件 | 來源 | Confidence |
|:-----|:---|:-----|:---------|:-----|:-----------|
| 楊氏模量 (E) | {值} | GPa | {溫度} | {C-NNN} | {H/M/L} |
| 蒲松比 (v) | {值} | - | {溫度} | {C-NNN} | {H/M/L} |
| 降伏強度 (Sy) | {值} | MPa | {溫度} | {C-NNN} | {H/M/L} |
| 抗拉強度 (Su) | {值} | MPa | {溫度} | {C-NNN} | {H/M/L} |
| 疲勞極限 | {值} | MPa | {R 比、循環數} | {C-NNN} | {H/M/L} |
| 密度 (rho) | {值} | kg/m3 | {溫度} | {C-NNN} | {H/M/L} |

## 熱性質

| 性質 | 值 | 單位 | 溫度範圍 | 來源 | Confidence |
|:-----|:---|:-----|:---------|:-----|:-----------|
| 熱傳導係數 (k) | {值} | W/(m*K) | {範圍} | {C-NNN} | {H/M/L} |
| 比熱容 (Cp) | {值} | J/(kg*K) | {範圍} | {C-NNN} | {H/M/L} |
| 熱膨脹係數 (CTE) | {值} | 1/K | {範圍} | {C-NNN} | {H/M/L} |
| 最高工作溫度 | {值} | C | - | {C-NNN} | {H/M/L} |

## 電磁性質（若適用）

| 性質 | 值 | 單位 | 條件 | 來源 | Confidence |
|:-----|:---|:-----|:-----|:-----|:-----------|
| 電阻率 | {值} | Ohm*m | {溫度} | {C-NNN} | {H/M/L} |
| 相對磁導率 | {值} | - | {頻率} | {C-NNN} | {H/M/L} |
| B-H 曲線 | {參考} | T vs A/m | {溫度} | {C-NNN} | {H/M/L} |
| 鐵損係數 | {值} | W/kg | {頻率、磁通密度} | {C-NNN} | {H/M/L} |

## FEA 輸入指引

### ANSYS Mechanical
```
MP, EX, {mat_id}, {E_value}
MP, PRXY, {mat_id}, {v_value}
MP, DENS, {mat_id}, {rho_value}
MP, KXX, {mat_id}, {k_value}
...
```

### Abaqus
```
*MATERIAL, NAME={material_name}
*ELASTIC
{E_value}, {v_value}
*DENSITY
{rho_value}
*CONDUCTIVITY
{k_value}
...
```

### 通用格式（其他軟體）
{表格格式的參數彙整，便於手動輸入}

## 注意事項

- {Confidence = LOW 的性質需實驗驗證，標記具體項目}
- {溫度相依性說明：哪些性質在工作溫度範圍內變化顯著}
- {異向性說明：若材料有方向性，標記取值方向}
- {供應商差異：不同供應商的物性範圍}
- {相容性警告：與相鄰材料的電化學/熱膨脹相容性}
```

---

## Phase 5: 狀態更新

所有文件產出完成後，更新 `.claude/context/triz/.triz-state.json`。

### 5.1 更新 state JSON

在現有 state 中新增 `step5` 區段：

```json
{
  "step5": {
    "completed": true,
    "subsystems_identified": ["motor", "gear", "thermal", "..."],
    "wi_files": ["WI-01_motor.md", "WI-02_gear.md", "..."],
    "icd_files": ["ICD-01_motor_housing.md", "..."],
    "mc_files": ["MC-01_{material}.md", "..."],
    "framework_files": ["README.md", "tr_gate_framework.md", "critical_path.md", "risk_register.md"],
    "total_files": 0,
    "output_dir": "docs/engineering/"
  }
}
```

其中 `total_files` = len(wi_files) + len(icd_files) + len(mc_files) + len(framework_files)。

### 5.2 追加寫入 session 報告檔

從 `.triz-state.json` 讀取 `report_file` 路徑，用 Read tool 讀取報告檔現有內容，再用 Write tool 將以下 Step 5 區段**追加到報告檔末尾**：

```markdown
## Step 5: 工程作業指導書

### 子系統分類
| # | 工程域 | WI 類型 |
|:--|:-------|:--------|
| 1 | {domain} | WI-{type} |
| ... | ... | ... |

### 產出文件統計
| 類型 | 數量 | 文件列表 |
|:-----|:-----|:---------|
| 框架文件 | 4 | README.md, tr_gate_framework.md, critical_path.md, risk_register.md |
| WI | {N} | {列表} |
| ICD | {N} | {列表} |
| Material Card | {N} | {列表} |
| **合計** | **{total}** | |

### 關鍵路徑摘要
{從 critical_path.md 提取的最長路徑}

### 風險摘要
{從 risk_register.md 提取的 HIGH 風險項目}

所有文件位於 `docs/engineering/`。
```

---

## 完成訊息

所有 Phase 完成後，輸出：

```
Step 5 完成 — 工程作業指導書體系已產出。
- WI: {N} 份（{domain list}）
- ICD: {N} 份
- Material Card: {N} 份
- 框架文件: 4 份

所有文件位於 docs/engineering/。
可執行 `/triz-status` 查看完整 pipeline 狀態。
下一步：執行 `/tr` 進入 TR1→TR10 工程執行追蹤，或各域 RD 工程師按 WI 程序獨立執行開發。
```

---

## 設計原則

### 1. 域無關（Domain-Agnostic）

子系統分類使用 TRIZ F/S/OZ/OT 的模式匹配，而非硬編碼的專案域。同一套偵測規則可適用於電動自行車、工業馬達、消費電子等不同專案。若偵測規則未涵蓋某域，使用者可在 Phase 1 確認時手動新增。

### 2. 多 Agent 並行

- **Phase 2（框架文件）**：循序產出（後續 WI 需引用框架內容）
- **Phase 3（WI）**：多 Agent 並行（各域 WI 獨立，無交叉依賴）
- **Phase 4（ICD/MC）**：在 WI 完成後並行產出（需引用 WI 內容）

執行順序：Phase 2 → Phase 3 → Phase 4 → Phase 5

### 3. TRIZ 溯源（Traceability）

每份 WI 的「溯源」表必須將每個章節追溯到具體的 TC/PC/SF/Evidence。這是 TRIZ 概念（WHAT）與工程執行（HOW）之間的關鍵橋樑。沒有溯源的 WI 章節視為無效。

### 4. 狀態連續性

step5 擴展現有 `.triz-state.json`，不使用獨立的狀態檔。完整 pipeline 為：step0 → step1 → step2 → step3 → step4 → step5。

### 5. 輸出位置分離

- **TRIZ 分析狀態** → `.claude/context/triz/`（session state，不交付）
- **工程交付物** → `docs/engineering/`（專案交付物，供 RD 使用）

WI/ICD/MC 是專案產出物，必須放在 `docs/engineering/`，不得放在 `.claude/context/triz/`。

### 6. Weak Evolution 處理

當 `step4.cci_verdict === "Weak Evolution"` 時：
- 所有 WI 正常產出
- 在 CCI 高分維度對應的 WI 章節中，加入「未來改進方向」備注
- 在 risk_register.md 中為 Weak Evolution 的高分維度新增風險項
- 在 README.md 中標注整體信心等級為「Weak Evolution — 部分項目需實驗補強」
