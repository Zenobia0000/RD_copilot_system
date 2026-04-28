---
name: tr-sop
description: TR SOP 產出器。從 WI + Process FMEA + Control Plan 合成量產 SOP 草稿，整合為工廠操作員可執行的標準作業程序。Use when production SOPs need to be drafted from engineering deliverables.
---

# TR SOP 產出器

## Overview

本 skill 從工程交付物自動合成量產 SOP 草稿。讀取 WI 程序步驟 + Process FMEA 管控點 + Control Plan 檢查項，整合為工廠操作員可執行的標準作業程序。

**宣告：** 「正在使用 tr-sop skill — 產出 {subsystem} SOP 草稿。」

**觸發時機**：TR8-TR9 階段，Beta 原型驗證後。

---

## 輸入

```
/tr-sop {subsystem}        # 產出指定子系統的 SOP
/tr-sop all                 # 產出所有子系統的 SOP
```

| 參數 | 必要 | 說明 |
|:-----|:-----|:-----|
| subsystem / all | 是 | 目標子系統名稱或 "all" |

---

## Phase 1: 資料收集

1. 讀取 `.tr-state.json` 確認目標子系統的 TR 等級 ≥ TR8（否則警告：「建議在 Beta 驗證後才產出 SOP」）
2. 讀取目標子系統的 WI 文件 → 提取操作步驟序列
3. 搜尋 `docs/engineering/` 中的 Process FMEA 文件 → 提取每步驟的管控點和潛在失效模式
4. 搜尋 `docs/engineering/` 中的 Control Plan 文件 → 提取檢查頻率、量測方法、反應計劃
5. 搜尋 `docs/engineering/dfm_reviews/` 中對應子系統的 DFM review → 提取製程參數建議

若 Process FMEA 或 Control Plan 不存在，**警告但不阻擋**，在 SOP 中標記對應管控欄位為「待 FMEA/CP 完成後補充」。

---

## Phase 2: SOP 合成

對每個組裝/製程步驟，從三個來源合成：

| 來源 | 提取內容 | SOP 中的角色 |
|:-----|:---------|:-------------|
| WI | 程序步驟、工具、參數 | 「做什麼」— 操作指令 |
| Process FMEA | 失效模式、嚴重度、改善行動 | 「注意什麼」— 風險警示 |
| Control Plan | 管控項、量測方法、頻率、反應計劃 | 「檢查什麼」— 品質管控 |
| DFM review | 製程參數建議、供應商特殊要求 | 「怎麼做」— 製程條件 |

### 語言轉換規則

WI 用工程師語言撰寫（含公式、FEA 參考）。SOP 需轉換為操作員語言：
- 移除理論推導，保留操作參數
- 公差用「上限/下限」表示，不用 ± 符號
- 設備名稱用工廠實際名稱（從 DFM review 或 Control Plan 推斷）
- 加入視覺提示（如「確認指示燈亮綠色」）

---

## Phase 3: 產出

輸出到 `docs/engineering/sop/{subsystem}_sop_{YYYY-MM-DD}.md`：

```markdown
# {子系統名稱} — 量產標準作業程序 (SOP)

> **版本**: 1.0（草稿）
> **日期**: {YYYY-MM-DD}
> **子系統**: {subsystem}
> **對應 WI**: {wi_list}
> **狀態**: 草稿 — 需現場驗證後正式發行

---

## 適用範圍

{本 SOP 適用的產品、工站、操作員資格}

## 安全注意事項

{從 FMEA severity ≥ 9 的項目提取安全警告}

## 所需工具與設備

| # | 工具/設備 | 規格 | 校驗週期 | 備註 |
|:--|:---------|:-----|:---------|:-----|
| 1 | {tool} | {spec} | {cal_cycle} | {note} |

## 作業步驟

| 步驟 | 操作 | 工具/設備 | 管控點 | 判定標準 | 異常處理 |
|:-----|:-----|:---------|:-------|:---------|:---------|
| 1 | {操作描述} | {tool} | {control_point} | {criteria} | {reaction_plan} |
| 2 | {操作描述} | {tool} | {control_point} | {criteria} | {reaction_plan} |

## 最終檢查

| 檢查項 | 方法 | 判定標準 | 記錄 |
|:-------|:-----|:---------|:-----|

## 包裝與標識

{包裝要求、標籤內容、追溯碼規則}

## 記錄與追溯

{需保留的記錄、保存期限、歸檔方式}

## 變更履歷

| 版本 | 日期 | 變更內容 | 核准 |
|:-----|:-----|:---------|:-----|
| 1.0 | {date} | 初版草稿（由 harness 自動產出） | 待簽 |
```

---

## Phase 4: 狀態更新

1. 更新 `.tr-state.json`：
   - 在對應子系統下新增 `sop_draft` 欄位：
     ```json
     {
       "sop_draft": {
         "file": "docs/engineering/sop/{subsystem}_sop_{YYYY-MM-DD}.md",
         "date": "YYYY-MM-DD",
         "status": "draft",
         "signed_off": false
       }
     }
     ```

---

## 下一步導引

| 狀態 | 提示 |
|:-----|:-----|
| 草稿完成 | 「SOP 草稿已產出。需現場操作員試跑後修訂，正式發行需主管簽核。」 |
| 缺 FMEA/CP | 「SOP 中有 {n} 個管控欄位標記『待補充』。建議先完成 Process FMEA 和 Control Plan。」 |
| 全部子系統完成 | 「所有子系統 SOP 草稿已產出。執行 `/tr-ppap check` 檢查 PPAP 文件包完整度。」 |

---

## 設計原則

### 域無關

SOP 步驟從 WI 動態讀取，不預設任何製程類型。同一 skill 可用於組裝、機加工、注塑、電子組裝等不同製程。

### 草稿定位

harness 產出的 SOP 是**草稿**，不是正式文件。正式發行需要：
1. 現場操作員試跑驗證
2. 工藝工程師修訂
3. 主管簽核

SOP 版本號固定為 `1.0（草稿）`，正式版由人工遞增。
