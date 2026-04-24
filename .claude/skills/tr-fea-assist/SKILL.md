# TR FEA 設定輔助

## Overview

本 skill 輔助工程師設定和判讀 FEA/CFD 分析。**不內建任何產品規格** — 所有材料、數值、判定標準從 WI 和 MC 文件動態讀取。

**宣告：** 「正在使用 tr-fea-assist skill — 輔助 {WI/domain} 的 FEA 設定。」

---

## 輸入

```
/tr-fea WI-01              # 針對 WI-01 的 FEA 輔助
/tr-fea motor              # 以子系統名稱指定（從 .tr-state.json 反查 WI）
/tr-fea result WI-01       # 判讀 WI-01 的 FEA 結果
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| WI-nn 或 domain | 是 | 目標 WI 或子系統名稱 |
| result | 否 | 切換到結果判讀模式 |

---

## Phase 1: 載入上下文（資料驅動）

1. 讀取目標 WI 文件（`docs/engineering/work_instructions/WI-xx_*.md`）
2. 從 WI 中提取：
   - **設計輸入表** → 所有參數值和 pass/fail 標準
   - **FEA 設定指引段落**（若存在）→ 軟體、分析類型、網格建議
   - **溯源表** → 追溯到 TRIZ 解法的 F/S/OZ/OT
3. 讀取 WI 引用的所有 Material Card（`docs/engineering/material_cards/MC-xx_*.md`）
4. 讀取 `.tr-state.json` 取得 WI 狀態
5. 讀取 `docs/engineering/tr_gate_framework.md` 取得目標 gate 退出條件

---

## Phase 2: FEA 域自動識別

根據 WI 內容自動判斷 FEA 類型，**不硬編碼域清單**：

| WI 內容特徵 | FEA 域 | 典型求解器 |
|:-----------|:-------|:---------|
| 包含 magnetic/electromagnetic/磁/電磁/B-H/Bg/反EMF | **電磁** | JMAG, ANSYS Maxwell, Motor-CAD |
| 包含 stress/strain/fatigue/von Mises/應力/疲勞 | **結構** | ANSYS Mechanical, Abaqus, SolidWorks Sim |
| 包含 thermal/temperature/heat/PCM/溫度/散熱/相變 | **熱流** | ANSYS Fluent, COMSOL, Star-CCM+ |
| 包含 modal/vibration/frequency/模態/振動 | **動力學** | ANSYS Modal, Abaqus Frequency |
| 包含 CFD/flow/pressure/fluid/流場/壓力 | **流體** | Fluent, OpenFOAM |

---

## Phase 3: 輔助輸出（通用模板）

對識別到的 FEA 域，從 WI + MC 動態組裝以下輸出：

### 3.1 材料卡指定

```markdown
## 材料卡對應

| 組件 | 材料 | MC 檔案 | 關鍵輸入 |
|:-----|:-----|:--------|:---------|
```

**填充規則：**
- 從 WI 「設計輸入」表提取組件和材料名稱
- 從 WI 「溯源」表提取 Evidence ID
- 讀取對應 MC 檔案，提取 FEA 需要的關鍵性質值
- 若 MC 中有 `FEA 輸入指引` 段落，直接引用

### 3.2 邊界條件

根據 FEA 域類型，從 WI 的設計輸入和步驟中提取：

**電磁域：**
- 從 WI 提取：極槽配置、幾何尺寸、電流/扭矩工作點
- 建議模型對稱性（利用極數對稱）
- 載荷步：空載 → 額定 → 峰值 → 場弱（若有）→ 敏感度分析（若有風險項）

**結構域：**
- 從 WI 提取：載荷值（扭矩、力、壓力）、配合規格、安全係數要求
- 從 ICD 提取：介面約束條件
- 分析類型：靜態 / 疲勞 / 接觸 / 模態（依 WI 步驟推斷）

**熱流域：**
- 從 WI 提取：熱源功率、工況持續時間、溫度上限
- 從 MC 提取：相變參數（若有 PCM 類材料）
- 邊界條件：對流係數、輻射率、環境溫度

### 3.3 網格策略

**通用原則（域無關）：**

| 區域類型 | 建議尺寸 | 理由 |
|:---------|:---------|:-----|
| 高梯度區（氣隙/接觸面/應力集中） | 特徵尺寸的 1/10 ~ 1/20 | 捕捉梯度 |
| 中梯度區（表面/薄壁） | 特徵尺寸的 1/5 | 平衡精度與計算量 |
| 低梯度區（塊材內部） | 特徵尺寸的 1/2 ~ 1/3 | 減少元素數 |
| 薄壁/腔體厚度方向 | ≥ 3-5 層 | 彎曲/梯度解析 |

**域特定補充：**

| FEA 域 | 額外網格要點 |
|:-------|:------------|
| 電磁 | 氣隙至少 3 層；旋轉域需滑動網格或 master/slave |
| 結構接觸 | 接觸面需 surface-to-surface，尺寸 ≤ 赫茲接觸寬度/2 |
| 熱流相變 | 相變介面需足夠解析度（≥ 5 層穿越相變區） |
| 疲勞 | 應力集中區用 hex mesh preferred |

### 3.4 收斂準則

| FEA 域 | 建議收斂準則 |
|:-------|:------------|
| 電磁 | 非線性殘差 < 1e-4；暫態步長 ≤ 電角度 1° |
| 結構靜態 | 力殘差 < 1e-3；位移殘差 < 1e-4 |
| 結構接觸 | 穿透量 < 最小網格尺寸/10 |
| 熱流穩態 | 能量殘差 < 1e-6 |
| 熱流暫態 | 能量殘差 < 1e-6；步長 ≤ 總時間/50 |

### 3.5 Pass/Fail 標準

**從 WI 動態提取，不硬編碼：**

```markdown
## Pass/Fail 標準（從 WI-{nn} 提取）

| 指標 | Pass 條件 | 來源 |
|:-----|:---------|:-----|
```

**提取規則：**
1. WI 「設計輸入」表中有「目標」或「判定」欄位 → 直接提取
2. WI 步驟中有「判定」段落 → 提取閾值
3. `tr_gate_framework.md` 中目標 gate 的退出條件 → 提取 FEA 相關項
4. `risk_register.md` 中的高風險項 → 對應指標需額外敏感度分析

### 3.6 常見陷阱

根據 MC 中的「注意事項」段落動態產出：

```
對每個 MC 的「注意事項」：
  → 轉為 FEA 設定的「常見陷阱」提醒
  → 特別關注：
     - Confidence = LOW 的性質 → 「需敏感度分析」
     - 異向性材料 → 「確認取值方向」
     - 溫度相依性 → 「確認使用工作溫度的物性」
     - 製程影響（如 weld line、加工硬化）→ 「強度折減」
```

---

## Phase 4: 結果判讀模式

當使用者使用 `result` 參數時：

1. 讀取 WI + MC（同 Phase 1）
2. 請使用者提供 FEA 結果（截圖、數據表、或文字描述）
3. 對比 Phase 3.5 中提取的 Pass/Fail 標準
4. 產出判讀報告：

```markdown
## FEA 結果判讀 — {WI-nn}

### 結果摘要

| 指標 | FEA 值 | Pass 條件 | 判定 | 備註 |
|:-----|:-------|:---------|:-----|:-----|
| {metric} | {value} | {criterion} | PASS/FAIL | {note} |

### FEA vs WI 預測對比

| 參數 | WI 預測/估算 | FEA 結果 | 偏差 | 評估 |
|:-----|:-------------|:---------|:-----|:-----|
| {param} | {predicted} | {fea_result} | {delta_pct}% | OK / 需檢查 |

### 建議下一步

{基於結果的具體建議}
```

5. 更新 `.tr-state.json` 的 WI 狀態

---

## Phase 5: 求解器 Input Snippet（可選）

從 MC 的 `FEA 輸入指引` 段落提取求解器 snippet。

支援格式：ANSYS APDL / Fluent UDF / Abaqus / JMAG / COMSOL。

**注意**: Snippet 從 MC 提取後需使用者確認，每個 snippet 附帶「使用前請確認」清單。

---

## 狀態更新

FEA 完成後更新 `.tr-state.json`：

```json
{
  "wi_status": {
    "WI-{nn}": {
      "status": "in_progress",
      "steps_completed": ["fea_setup", "fea_run"],
      "deliverables": {}
    }
  }
}
```

deliverables 的 key-value 從 WI 的「交付物清單」動態提取。

---

## 下一步導引

| 狀態 | 提示 |
|:-----|:-----|
| FEA 設定完成 | 「FEA 設定已輸出。執行模擬後，使用 `/tr-fea result WI-{nn}` 判讀結果。」 |
| FEA 結果全 pass | 「WI-{nn} FEA 全部通過。此子系統已具備 TR{n} 條件。執行 `/tr-gate TR{n}` 進行 gate review。」 |
| FEA 結果有 fail | 「{指標} 未通過（{actual} vs {required}）。建議: {specific_action}。」 |
