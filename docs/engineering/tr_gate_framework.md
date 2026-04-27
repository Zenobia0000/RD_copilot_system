# TR Gate Framework — e-Bike Drive Unit v2

> **適用範圍**: 從 TRIZ 概念規格到量產釋放的全生命週期
> **TR = Technology Review**：產品開發里程碑 gate review，每個 Gate 有明確退出條件，通過後才能進入下一階段

### 與國際標準的關係

本框架是**客製化混合框架**，非任何單一國際標準的直接實作：

| 國際標準 | 我們的對應 | 關係 |
|:---------|:-----------|:-----|
| **NASA TRL** (ISO 16290) | TR0-TR1 ≈ TRL 3-5 | TRL 評估「技術能否用」；我們的 TR 評估「產品開發到哪了」— 性質不同 |
| **APQP** (AIAG) | TR3→TR10 ≈ Phase 2-5 | 品質交付物要求（FMEA、Control Plan、PPAP）已納入退出條件 |
| **VDA MLA** (ML0-ML7) | TR0-TR10 ≈ ML0-ML7 | 最接近的對標 — 同為 milestone-based gate review，有明確退出條件 |

> **注意**：TR ≠ NASA TRL。NASA TRL 是技術成熟度量表（9 級），評估單一技術是否可用於任務。
> 我們的 TR 是產品開發 gate system，涵蓋從概念到量產的完整生命週期，結構上更接近 VDA MLA。

---

## TR Gate 定義

| TR | 名稱 | 範疇 | 退出條件 | 預估工時 |
|:---|:-----|:-----|:---------|:---------|
| TR0 | 概念凍結 | TRIZ spec accepted | TRIZ session 判定 Evolution/Weak Evolution，Evidence Registry ≥50% HIGH+MEDIUM | **Done** |
| TR1 | 可行性分析 | 各子系統獨立 FEA/CFD 通過 | WI-01~03 完成，14 項 V-test 在模擬中全部 pass | +6-8 週 |
| TR2 | 設計參數鎖定 | 關鍵設計決策定案 | 軸承選定、齒形確定、PCM 封裝方式決定、4 份 ICD 簽核、**供應商能力確認** | +2-3 週 |
| TR3 | 詳細設計 | 完整 3D CAD + BOM | WI-04 完成，GD&T 標註、公差鏈分析、BOM 凍結、**Design FMEA 完成** | +4-6 週 |
| TR4 | 原型備料 | 供應鏈就緒 | WI-07 長交期物料全部下單、治工具設計完成 | 與 TR1 並行 |
| TR5 | Alpha 原型 | 功能原型組裝 | 馬達可旋轉、齒輪箱可嚙合、PCM 可吸熱、系統可組裝 | +4-6 週 |
| TR6 | Alpha 驗證 | V1-V14 實測 | WI-06 Phase A-D 全部通過 | +4-6 週 |
| TR7 | Beta 設計 | DFM 修正 | 壓鑄/射出/機加工供應商 DFM review 完成、**Process FMEA 完成**、**Control Plan 初版** | +4 週 |
| TR8 | Beta 原型 | 量產意圖原型 | 使用量產模具/工藝製作，尺寸+功能 pass、**Control Plan 驗證** | +6 週 |
| TR9 | 量產驗證 | PV 測試 | DVP&R 全項完成（耐久、環境、安全） | +8-12 週 |
| TR10 | 量產釋放 | PPAP 等效 | Cpk ≥ 1.33，量產 SOP 簽核 | +4 週 |

---

## 各子系統現況 TR 評估

| 子系統 | 現在 TR | 下一個目標 | 主要障礙 | 負責 WI |
|:-------|:--------|:-----------|:---------|:--------|
| AFM 馬達 | **TR0** | TR1 | 全新拓撲，需 3D 電磁 FEA + 軸向力驗證 | WI-01 |
| 諧波齒輪 | TR0.5 | TR1 | 商用技術但 CoCrMo+CF-PEEK 材料組合需驗證 | WI-02 |
| PCM 熱管理 | **TR0** | TR1 | 概念新穎，無殼體夾層 PCM 的熱原型數據 | WI-03 |
| AZ91D 殼體 | TR0.5 | TR2 | 鎂合金壓鑄成熟，但 2.5mm 薄壁+嵌件+PCM 腔體是新挑戰 | WI-04, WI-08 |
| 環形 PCB | TR0.5 | TR2 | 環形 layout + EMI 屏蔽有挑戰但無基本未知數 | WI-05 |
| 扭矩感測器 | TR1 | TR2 | 商用品(NCTE等)，整合+EMI 隔離是重點 | WI-05 |

---

## TR Gate Review 檢查清單

### TR0 → TR1 Gate Review

- [ ] WI-01 AFM 磁路 FEA 完成：Bg ≥ 0.8T, 扭矩 ≥ 5Nm, 軸向力 < 推力軸承額定
- [ ] WI-02 諧波齒輪 FEA 完成：柔輪 von Mises < S-N 安全係數 3×, 剛輪齒根 ≤ 150MPa
- [ ] WI-03 PCM 熱模擬完成：100Nm@8min 殼溫 ≤ 80°C, 恢復時間合理
- [ ] WI-01 Loss map 已交付 WI-03
- [ ] 6 份 Material Card 已建立並標註資料來源
- [ ] Risk Register 已更新（風險概率是否需修正）

### TR1 → TR2 Gate Review

- [ ] 軸承型號選定（主軸承 + 推力軸承 + 波發生器軸承）
- [ ] 諧波齒形參數鎖定（齒數、模數、壓力角）
- [ ] PCM 封裝方式決定（焊接/釺焊密封）
- [ ] 4 份 ICD 完成並經各域工程師確認
- [ ] **供應商能力確認**：關鍵零件（柔輪、剛輪、殼體）供應商已 nominated 並確認製程能力
- [ ] 無 showstopper 風險（所有 "致命" 風險已降至 "中等" 或以下）

### TR2 → TR3 Gate Review

- [ ] WI-04 完整 3D CAD 組裝完成
- [ ] 公差鏈分析完成：同心度、軸向堆疊、氣隙均在容許範圍
- [ ] GD&T 標註完成 (ASME Y14.5)
- [ ] BOM 凍結（含物料號、供應商、單價估算）
- [ ] **Design FMEA 完成**：涵蓋所有子系統關鍵失效模式（RPN 排序、前 10 項有改善對策）
- [ ] DFM 初步確認（壓鑄、射出、機加工各供應商已 review 圖面）

### TR3 → TR5 Gate Review (含 TR4 備料確認)

- [ ] WI-07 長交期物料已到料或有明確交期
- [ ] 治工具設計完成
- [ ] 原型 BOM 和 production BOM 差異已記錄（替代材料清單）
- [ ] WI-06 測試治具設計完成

### TR5 → TR6 Gate Review

- [ ] WI-06 Phase A (馬達): V1-V4 全 pass
- [ ] WI-06 Phase B (齒輪): V5-V8 全 pass
- [ ] WI-06 Phase C (熱): V10, V13 全 pass
- [ ] WI-06 Phase D (系統): V9, V11, V12, V14 全 pass
- [ ] 所有實測數據 vs 模擬預測的偏差 < 20%（否則模型需修正）
- [ ] Evidence Registry 更新為實測數據

### TR6 → TR7 Gate Review

- [ ] Alpha 測試 issue list 已建立並分類（design issue vs process issue）
- [ ] **Design FMEA 更新**：納入 Alpha 測試中發現的失效模式
- [ ] 各子系統 DFM 初步評估完成（壓鑄、射出、機加工）
- [ ] 供應商已收到圖面並回覆初步可行性
- [ ] FEA 模型已依 Alpha 實測數據修正（偏差 >20% 的項目）

### TR7 → TR8 Gate Review

- [ ] 壓鑄供應商 (AZ91D 殼體) DFM review 完成：壁厚、拔模角、澆口位置確認
- [ ] 射出供應商 (CF-PEEK 剛輪) DFM review 完成：纖維方向、熔接線、收縮補償確認
- [ ] 機加工供應商 (CoCrMo 柔輪) DFM review 完成：表面粗度、刀具選型、熱處理工序確認
- [ ] **Process FMEA 完成**：涵蓋所有關鍵製程步驟
- [ ] **Control Plan 初版完成**：涵蓋進料檢驗、製程管制、出貨檢驗
- [ ] DFA (Design for Assembly) 審查完成：組裝順序、干涉檢查、緊固規格
- [ ] Beta BOM 凍結（量產材料、量產供應商）

### TR8 → TR9 Gate Review

- [ ] Beta 原型使用量產模具/工藝製作
- [ ] Beta 原型尺寸量測全 pass (GD&T per ASME Y14.5)
- [ ] Beta 原型功能測試 pass（V1-V14 重測）
- [ ] **Control Plan 驗證**：Beta 原型依 Control Plan 執行，確認管制點有效
- [ ] 量產組裝 SOP 草案完成
- [ ] 包裝規格確認

### TR9 → TR10 Gate Review

- [ ] DVP&R (Design Verification Plan & Report) 全項完成
  - [ ] 耐久測試：10 萬次 125Nm 循環 pass
  - [ ] 環境測試：-20°C ~ +50°C 全溫域 pass
  - [ ] 安全測試：EN 15194 / ISO 4210 相關項目 pass
  - [ ] 防水測試：IP67 pass
- [ ] PV (Production Validation) 測試：使用量產線產品，n ≥ 30 件
- [ ] **Cpk ≥ 1.33**（關鍵尺寸：殼體同心度、氣隙、齒輪嚙合間隙）
- [ ] **PPAP 等效文件包完成**：
  - [ ] Part Submission Warrant (PSW)
  - [ ] Design FMEA (最終版)
  - [ ] Process FMEA (最終版)
  - [ ] Control Plan (最終版)
  - [ ] Measurement System Analysis (GR&R)
  - [ ] 尺寸報告
  - [ ] 材料/性能測試報告
- [ ] 量產 SOP 簽核
- [ ] Risk Register 所有 open 項目已關閉或有明確接受記錄
