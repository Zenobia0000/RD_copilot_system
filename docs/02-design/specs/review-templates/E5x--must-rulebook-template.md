# MUST Rulebook Template (可機器執行)

## 說明
此模板用於定義可機器執行的 MUST 條件，作為 RD Design Copilot 流程中 **X5 (MUST 快篩)** 及 **V1 / Gate C (CAD Gate)** 的依據。每條 MUST 規則都應詳細定義其輸入、判定邏輯、所需證據類型及不通過時的處理方式。

> **分層證據要求**：同一條 MUST 規則在不同階段有不同的證據門檻。X5 階段尚無 CAD/仿真，允許以 E0-E1 等級（工程估算 / Expert Judgement）進行初篩；V1 / Gate C 階段則要求 E2+ 等級（仿真 / Bench Test）的正式驗證。

## MUST 規則定義

| 欄位名稱 | 說明 | 範例數據類型 / 結構 |
|---|---|---|
| **MUST ID** | 唯一識別碼 | String |
| **條件描述** | MUST 條件的簡潔描述 | String |
| **Input 欄位** | 判定所需數據的來源。可引用其他工件的特定欄位。 | String / Array of Strings |
| **判定邏輯 / 公式** | 用於判斷 MUST 條件是否通過的具體邏輯或計算公式。應盡量量化。 | String (e.g., Python-like expression) |
| **X5 證據要求** | X5 快篩階段所需的最低證據類型（E0-E1 等級）。 | Enum |
| **V1 / Gate C 證據要求** | V1 設計審查 / Gate C 通過所需的證據類型（E2+ 等級）。 | Enum |
| **Fail 處置** | 若 MUST 條件不通過，系統應採取的動作。 | Enum (淘汰, 降級, 列為風險) |

---

## MUST 規則範例

| MUST ID | 條件描述 | Input 欄位 (Schema Path) | 判定邏輯 / 公式 | X5 證據要求 (E0-E1) | V1 / Gate C 證據要求 (E2+) | Fail 處置 |
|---|---|---|---|---|---|---|
| **M1** | **空間約束**：方案概念必須能置入目標空間包絡內 | `Concept Route.Interface.Envelope.Description`, `Constraint.Hard_Constraints.Volume` | 幾何包絡估算 (X5) 或 `CAD_Model.Interference_Check()` (V1) | `Envelope Description` + `Expert Judgement` | `CAD Model (Verified)` + 干涉檢查報告 | `淘汰` |
| **M2** | **成本預估**：方案概念的預估 BOM 成本不得超過目標上限 | `Concept Route.BOM.Estimated_Cost`, `Constraint.Hard_Constraints.Cost_Upper_Limit` | `Concept Route.BOM.Estimated_Cost <= Constraint.Hard_Constraints.Cost_Upper_Limit` | `Spreadsheet (Draft)` — 粗估 BOM | `Spreadsheet (Reviewed)` — 供應商報價 BOM | `淘汰` |
| **M3** | **安全餘裕**：核心北極星指標必須具備合理的設計安全餘裕 | `Concept Route.Safety_Margin.KPI_ID`, `Constraint.Soft_Objectives.Min_Safety_Margin_Factor` | `Concept Route.Safety_Margin.KPI_ID >= Constraint.Soft_Objectives.Min_Safety_Margin_Factor` | `Expert Judgement` / `Calculation (Draft)` | `Simulation Report (Verified)` / `Bench Test Report` | `淘汰` |
| **M4** | **解耦程度**：方案概念不應引入過多的關鍵耦合點，避免系統複雜性失控 | `Concept Route.Coupling_Points`, `Breakpoint.CLD_ID`, `Constraint.Hard_Constraints.Max_Coupling_Points` | `COUNT(Concept Route.Coupling_Points WHERE Is_Critical = TRUE) <= Constraint.Hard_Constraints.Max_Coupling_Points` | `CLD (Draft)` / `Expert Judgement` | `CLD (Verified)` + 模組測試結果 | `淘汰` |
| **M5** | **供應可行性**：方案概念的關鍵零組件必須具備基本的供應韌性 | `Concept Route.Key_Components.Supplier_Audit_ID` | `Approved_Suppliers.Count >= 2` (Gate C) 或初步確認可行 (X5) | `SC Initial Inquiry` / `Expert Judgement` | `Supplier Audit Report (Reviewed)` / `SC Response (Verified)` | `淘汰` |
| **M6** | **製造路徑可行性**：方案概念的關鍵製造工藝必須具備初步的可行性 | `Concept Route.Manufacturing.Process_Complexity`, `Constraint.Hard_Constraints.Mfg_Capability` | `Process_Complexity` 與 `Mfg_Capability` 匹配度評估 | `Mfg Expert Judgement` | `DFM Pre-Assessment Report (Reviewed)` | `淘汰` |

---

## 分層執行說明

### X5 (MUST 快篩) — 粗篩
- **目的**：快速淘汰明顯不可行的方案，降低後續 CAD 投入浪費。
- **證據等級**：E0 (推論) ~ E1 (計算/估算) 即可。
- **判定原則**：若以現有粗略資訊即可判斷「明顯不通過」，則淘汰；若「無法確定」，則保留進入 Pre-CAD Gate。
- **Machine-Executable**：M2 (成本比較)、M4 (耦合點計數) 可自動執行；M1/M3/M5/M6 在此階段多依賴 Expert Judgement，系統記錄判斷結果即可。

### V1 / Gate C (CAD Gate) — 精篩
- **目的**：基於 MVP CAD 和初步仿真，嚴格驗證 MUST 條件。
- **證據等級**：E2 (仿真/Bench Test) 以上。
- **判定原則**：所有 MUST 都必須有 E2+ 證據支撐，否則觸發 V2 證據補齊迴圈。
- **Machine-Executable**：M1 (CAD 干涉檢查)、M2 (BOM 比較)、M4 (耦合點計數) 可自動執行；M3/M5/M6 需審查人確認。

---

**版本**: v1.1
**最後更新**: 2026-03-12
**適用範圍**: RD Design Copilot X5 (MUST 快篩) 及 V1 / Gate C (CAD Gate)
