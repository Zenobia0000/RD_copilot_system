# Pre-CAD Review Report Template

## 說明
此模板用於 RD Design Copilot 流程中 Gate P (Pre-CAD Gate) 的審查。其目的在於發想階段利用「可驗證的最小資訊」篩選和縮減候選設計方案，並在投入大量 CAD 繪製和詳細模擬之前，淘汰不具可行性的方案。

> **MUST 項目為 Go/No-Go 判定**（Pass / Conditional / Fail），與 KT Decision Analysis 一致。非 MUST 維度使用 1-5 分制定性評估。

## Pre-CAD 審查表

**方案 ID**：`CR-A001` (連結到 Concept Route 工件)

### 1. MUST 硬限制 (Go/No-Go)

| MUST ID | 審查項目 | 評估內容 (基於方案規格 & Interface Contract) | 證據 (Artifact ID / 描述) | 判定 (Pass / Conditional / Fail) | 評語/建議 |
|---|---|---|---|---|---|
| M1 | 空間約束 | 方案預估幾何包絡是否能置入目標空間？ | CR-A001.Interface.Envelope.Description | Pass | 初步判斷可行，需進一步 MVP CAD 確認 |
| M2 | 成本預估 | 方案核心零組件粗估成本是否符合預期？ | CR-A001.BOM.Estimated_Cost | Conditional | 成本尚可控，但有潛在風險零組件，需供應商報價確認 |
| M3 | 安全餘裕 | 北極星指標是否有初步安全餘裕判斷？ | CR-A001.Safety_Margin.KPI_ID (Expert Judgement) | Conditional | 某關鍵指標餘裕較低，需早期實驗驗證 |
| M4 | 解耦程度 | 關鍵耦合點數量是否符合要求？ | CR-A001.Coupling_Points (CLD-001) | Pass | 模組化程度高，耦合點控制良好 |
| M5 | 供應可行性 | 關鍵零組件供應鏈是否可行？ | CR-A001.Key_Components.Supplier_Audit_ID | Pass | 需開發新供應商，但技術可行 |
| M6 | 製造路徑可行性 | 核心製造工藝是否初步可行？ | CR-A001.Manufacturing.Process_Complexity (DFM Pre-Assessment) | Conditional | 有挑戰性工藝，需早期製程驗證 |

> **判定說明**：
> - **Pass**：以現有資訊判斷可行，可進入下一階段。
> - **Conditional**：初步可行但存在不確定性，需在 MVP CAD / V2 階段補足證據。方案保留，但標記為需優先驗證。
> - **Fail**：以現有資訊明顯不通過，方案淘汰。

**MUST 總結**：任一項 Fail → 方案淘汰。有 Conditional 項 → 方案保留，但 Conditional 項列入 V1 優先驗證清單。

---

### 2. 定性評估 (1-5 分制)

| 審查維度 | 審查項目 | 評估內容 | 證據 (Artifact ID / 描述) | 評分 (1-5, 5為最佳) | 評語/建議 |
|---|---|---|---|---|---|
| **模組獨立性 (Module Independence)** | 關鍵模組間的介面是否清晰？ | CR-A001.Interface.Description | 5 | 介面定義清晰，獨立性高 |
| | 更改一個模組是否會劇烈影響其他模組？ | CR-A001.Risk.Source_Artifact_ID (CLD-001) | 4 | 部分介面變更會影響，但可控 |
| **可驗證性 (Testability)** | 核心假設能否透過 1-2 週小實驗驗證？ | CR-A001.Min_Experiment (Exp-A001) | 4 | 大部分核心假設可快速驗證 |
| | 是否有不可驗證的「黑箱」機制？ | CR-A001.Mechanism.Physical_Principle | 5 | 所有機制都有可驗證的物理原理 |
| **主要風險機制 (Failure Mechanism)** | 方案最可能怎麼死？ (e.g., 熱失控, 早期磨損, 雜訊干擾) | CR-A001.Risk.Failure_Mode (Risk-A001) | 3 | 熱管理風險較高，需早期仿真 |
| | 是否有類似產品的歷史失效經驗？ | Historical Failure Database (FFMEA-001) | 4 | 有參考案例，可學習避免 |
| **最小 CAD 工作量 (MVP CAD Effort)** | 需要繪製哪些最小幾何模型以進行粗仿真？ | CR-A001.Interface.Envelope.Description | 5 | 只需繪製核心結構，約 2 天工時 |
| | 是否需要製作實體原型進行概念驗證？ | CR-A001.Min_Experiment | 3 | 建議製作簡單物理模型驗證關鍵運動學 |

---

## Pre-CAD Gate 決策總結

**概念路線 ID**：`CR-A001`

**MUST 判定結果**：[全部 Pass / 有 Conditional / 有 Fail]

**決策結果**：[通過 / 通過但需優先驗證 / 淘汰]

**關鍵理由**：
*   **優勢**：在模組獨立性和可驗證性方面表現優異，能有效降低早期開發風險。
*   **風險**：M3 (安全餘裕) 和 M6 (製造可行性) 為 Conditional，需在後續 MVP CAD 階段重點關注。

**Conditional 項優先驗證清單**：
*   M2 (成本)：需在 V1 取得供應商報價確認。
*   M3 (安全餘裕)：需在 V2 規劃最小實驗驗證關鍵 KPI。
*   M6 (製造可行性)：需在 V1 進行 DFM Pre-Assessment。

**後續行動**：
*   進行 MVP CAD 繪製，聚焦在核心結構和關鍵介面。
*   針對 Conditional 項，規劃 V2 的最小實驗。

**審查人**：
*   [姓名/角色]：__________
*   [姓名/角色]：__________
*   日期：__________

---

**版本**: v1.1
**最後更新**: 2026-03-12
**適用範圍**: RD Design Copilot Gate P (Pre-CAD Gate)
