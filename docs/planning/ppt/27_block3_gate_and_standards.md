# Block 3 Deep-Dive — 節點目的與國際標準對標

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：Block 3「節點目的與國際標準對標」的單頁展開稿，可獨立呈現或作為 5 頁 deck 第三頁

---

## 1. 這頁要回答的一個問題

> 系統上每個主要節點的目的是什麼？它跟業界已有的標準怎麼對齊，又補了什麼缺？

## 2. 一句話 Key Message

> 每個 Gate 都不是為了流程好看，而是確認某一種不確定性已被消除——而且這套方法可對標 APQP、VDA MLA、NASA TRL 與 Stage-Gate，但補上了傳統框架在前端發明性流程的盲區。

## 3. 版面配置建議

```
┌──────────────────────────────────────────────────────────┐
│                         頁面標題                           │
│  每個 Gate 確認一件事：某種不確定性是否已被消除               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  A. Gate 矩陣（上半頁）                                    │
│                                                          │
│  ┌─────┬──────────┬──────────────┬────────────────────┐  │
│  │Gate │ 確認什麼   │ 鎖定項        │ 關鍵退出條件        │  │
│  ├─────┼──────────┼──────────────┼────────────────────┤  │
│  │ G0  │ 問題邊界   │ ...          │ ...                │  │
│  │ ... │ ...       │ ...          │ ...                │  │
│  │ G7  │ 量產能力   │ ...          │ ...                │  │
│  └─────┴──────────┴──────────────┴────────────────────┘  │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  B. 國際標準對照表（下半頁）          C. 差異化論述         │
│                                                          │
│  RDP-8  │ APQP  │ VDA MLA │ TRL │ Stage-Gate            │
│  ...    │ ...   │ ...     │ ... │ ...                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 4. 主要內容

### A. Gate 矩陣

| Gate | 確認什麼 | 鎖定項 | 關鍵退出條件 |
|:-----|:---------|:-------|:------------|
| **G0** | 我知道問題在哪 | 問題邊界 + OZ/OT | 矛盾造句完成；Px 候選已識別 |
| **G1** | 我知道系統怎麼運作 | SF 模型 | SF 圖完成 + 改善/惡化描述 |
| **G2** | 我知道怎麼解矛盾 | TC 候選 + 控制方程式 | TC ≥1 且 ≥1 有控制方程式 |
| **G3** | 規格已凍結，可以開始做 | 概念 + 複雜度判定 | CCI ≤ 0.55；Evidence ≥50% HIGH+MEDIUM；WI/MC/ICD 已產出 |
| **G4** | 模擬證明物理可行 | FEA/CFD 結果 | 全部模擬 pass；14 V-test 模擬 pass |
| **G5** | 實體原型證明設計可行 | Alpha 原型 | 原型可組裝 + 功能正常 |
| **G6** | 工廠能穩定地做出來 | 製程能力 | DFM 修正完成 + Process FMEA + Control Plan v1 |
| **G7** | 大量生產沒問題 | 量產釋放 | Cpk ≥ 1.33 + DVP&R 完成 + SOP 簽核 + PPAP equivalent |

**Gate 規則**：
- 每個 Gate 是二元判定（PASS / FAIL / CONDITIONAL），不是打分
- FAIL = 退回前一個 Phase 補強，不是退回起點
- CONDITIONAL = 限期補齊特定項目後再判

### B. 國際標準對照表

| RDP-8 Phase | APQP | VDA MLA | NASA TRL | Stage-Gate |
|:------------|:-----|:--------|:---------|:-----------|
| **P0** SCOPE | — | ML0 | TRL 1-2 | Discovery |
| **P1** MAP | — | ML0-1 | TRL 2-3 | Scoping |
| **P2** RESOLVE | — | ML1 | TRL 3-4 | Business Case |
| **P3** SPECIFY | Phase 1 | ML2 | TRL 4-5 | Development entry |
| **P4** PROVE | Phase 2 | ML3 | TRL 5-6 | Testing & Validation |
| **P5** BUILD | Phase 3 | ML4-5 | TRL 6-7 | Testing & Validation |
| **P6** HARDEN | Phase 4 | ML5-6 | TRL 7-8 | Testing & Validation |
| **P7** SCALE | Phase 5 | ML7 | TRL 8-9 | Launch |

### C. 差異化論述

> **傳統框架的盲區**：APQP / VDA MLA / Stage-Gate 多半把前端概念階段當成一個模糊的「概念開發」黑箱。RDP-8 把這段拆成 **SCOPE → MAP → RESOLVE → SPECIFY** 四段，讓發明性流程也能被系統化管理。

| 面向 | 傳統框架 | RDP-8 |
|:-----|:---------|:------|
| 前端粒度 | 1 個階段（概念開發） | 4 個 Phase（P0-P3） |
| 前端方法 | 依賴經驗 + 頭腦風暴 | TRIZ 結構化推理 |
| 前端可追溯性 | 會議紀錄 + 簡報 | 矛盾→解法→evidence 全鏈追溯 |
| 後端對齊 | 完整（APQP/VDA 原生強項） | 完整（直接對標） |

## 5. 建議視覺元素

| 元素 | 類型 | 內容描述 |
|:-----|:-----|:---------|
| **Gate 矩陣表** | 8 列 4 欄表格 | Gate 名 / 確認什麼 / 鎖定項 / 退出條件，G3 列用強調色標示 |
| **標準對照欄** | 5 欄對照表 | RDP-8 vs APQP vs VDA vs TRL vs Stage-Gate，前端段（P0-P2）標示「傳統框架無對應」 |
| **差異化對比卡** | 左右對比框 | 左：傳統（1 階段 / 經驗驅動 / 會議紀錄），右：RDP-8（4 Phase / TRIZ / 全鏈追溯） |

## 6. 口條骨架（25 秒）

> 上面這張表是 8 個 Gate，每個都在確認一件具體的事。比如 G0 確認「我知道問題在哪」，G3 確認「規格可以凍結了」，G7 確認「量產可以釋放」。下面這張對照表說明它跟 APQP、VDA MLA、TRL 的對應關係——差別在於：傳統框架把前端當一個黑箱，我們拆成四段，讓前端也能被系統化管理。

## 7. 來源文件索引

| 內容 | 來源 |
|:-----|:-----|
| Gate 退出條件完整定義 | `docs/planning/18_flow_contract.md` §Gate Definitions |
| TRIZ 內部 Gate（G0-G4'） | `docs/methodology/DK-04--data-model-and-gate.md` §Gate Conditions |
| TR 外部 Gate（TR0-TR10） | `docs/methodology/DK-04--data-model-and-gate.md` §TR External Gates |
| 國際標準對標 | `docs/planning/18_flow_contract.md` §Standards Alignment |
| 差異化分析 | `docs/planning/ppt/19_internal_pitch_strategy.md` §Key Value Hypothesis |
