# RDP-8 — Resolution-Driven Product Development

---

**文件版本**：`v2.1`
**最後更新**：`2026-04-28`
**主要作者**：架構師 + 產品經理
**狀態**：`Active`
**前身**：v1.0 Flow Contract（合約式映射）→ v2.0 統一框架（第一性原理重建）

---

## 設計哲學

### 為什麼需要新框架？

現有產品開發方法論各有盲區：

| 方法論 | 擅長 | 盲區 |
|--------|------|------|
| **Stage-Gate** (Cooper) | 專案管理節奏 | 不教你怎麼發明 |
| **TRIZ** (Altshuller) | 發明性問題解決 | 止步於概念，不管工程落地 |
| **APQP** (AIAG) | 品質交付物管理 | 假設你已知道要做什麼 |
| **VDA MLA** (ML0-7) | 成熟度分級 | 前端只有「概念」一個大階段 |
| **Design Thinking** | 發現需求 | 不處理物理矛盾 |

**RDP-8 的獨特定位**：將 **TRIZ 的矛盾解析引擎** 嵌入 **TR 的工程成熟度管線**，形成一條從「症狀」到「量產」的完整閉環。每一步消除恰好一種不確定性，不多不少。

### 核心公理

> **產品開發 = 8 種不確定性的依序消除。**

| # | 不確定性類型 | 回答的問題 | 消除手段 |
|---|------------|-----------|---------|
| 0 | 問題不確定性 | 「真正的問題在哪？」 | 根因定位（5Why/KT/CECA） |
| 1 | 系統不確定性 | 「系統裡誰對誰做了什麼？」 | 功能分析 + 質場建模 |
| 2 | 解法不確定性 | 「矛盾要怎麼解？」 | TC→PC→SF 嵌套解析 |
| 3 | 規格不確定性 | 「要做什麼、做到多少？」 | 驗證 + WI/MC/ICD 產出 |
| 4 | 物理不確定性 | 「物理上行不行得通？」 | FEA/CFD 模擬驗證 |
| 5 | 整合不確定性 | 「組在一起能不能用？」 | Alpha 原型 + 實測 |
| 6 | 製程不確定性 | 「能不能穩定地做出來？」 | DFM/FMEA + Beta 驗證 |
| 7 | 規模不確定性 | 「能不能大量做？」 | PV 測試 + PPAP |

**0-3 是發明性前端**（TRIZ 引擎驅動），**4-7 是工程性後端**（TR 引擎驅動）。
橋接點 Gate 3 = 概念凍結 = 從「想」轉向「做」。

---

## Phase 定義

### Phase 0: SCOPE（定向）

> **消除問題不確定性** — 從症狀到根因

| 項目 | 內容 |
|------|------|
| **原始意圖** | TRIZ 認為：大多數「問題」其實是症狀。真正的問題藏在因果鏈的上游。不先定位根因，後續所有求解都在打錯誤的靶。 |
| **你在做什麼** | 把「我的馬達太熱」轉化為「在[系統]中，為了[改善 A]，導致[B 惡化]」的矛盾造句。 |
| **知識狀態變化** | 未結構化的不滿 → 定位到具體子系統 + 操作區(OZ) + 操作時間(OT) + 候選物理量(Px) |
| **方法工具** | 5-Why 根因分析、KT Is/IsNot 範圍界定、CECA 因果鏈分析 |
| **跳過條件** | Level B（已能填完矛盾造句）→ 直入 Phase 1 |
| **對應實作** | `triz-scoping` skill |

#### Gate 0: 問題鎖定（Problem Framed）

| 退出條件 | 判定方式 |
|---------|---------|
| 矛盾造句完成 | 「在[系統]中，為了[改善 A]，導致[B 惡化]」可填完 |
| OZ + OT 已定位 | 操作區和操作時間已鎖定 |
| Px 候選已識別 | 至少一個物理量被識別為矛盾核心 |
| 子系統邊界明確 | 分析範圍鎖定在 OZ 周邊，而非整個 BOM |

---

### Phase 1: MAP（建模）

> **消除系統不確定性** — 從直覺到結構化

| 項目 | 內容 |
|------|------|
| **原始意圖** | TRIZ 的 FA+SF 不是學術練習。它迫使工程師把「我覺得這裡有問題」轉化為「組件 A 對組件 B 的作用是有效/有害/不足/缺失」。沒有這一步，後面的矛盾矩陣查表就是碰運氣。 |
| **你在做什麼** | 繪製組件交互圖（FA），標記每個交互為有效/有害/不足/過量。對關鍵交互進行質場三角（SF）診斷：什麼場(F)作用在什麼物質(S)上，產生什麼效應。 |
| **知識狀態變化** | 模糊的系統理解 → 結構化的功能依賴圖 + SF 拓撲 |
| **SF-only 岔路** | 如果 SF 診斷 = 「功能缺失」或「功能不足」且無副作用 → 直接走 76 標準解，跳 Phase 2 進入 Phase 3 |
| **對應實作** | `triz-model` skill |

#### Gate 1: 系統理解（System Mapped）

| 退出條件 | 判定方式 |
|---------|---------|
| FA 組件交互圖完成 | 所有組件交互已標記為有效/有害/不足/過量/缺失 |
| SF 診斷完成 | 每個關鍵交互有 SF 三角（S1-F-S2，診斷狀態） |
| 改善/惡化描述完成 | 自然語言描述可供 Phase 2 參數映射 |
| 子系統邊界鎖定在 OZ | 不是整個產品的 BOM |

---

### Phase 2: RESOLVE（解析）

> **消除解法不確定性** — 從矛盾到分離策略

| 項目 | 內容 |
|------|------|
| **原始意圖** | TRIZ 的核心信念：**矛盾不該被「trade-off」折衷，而該被「分離」消除**。TC 找到衝突的兩個參數；PC 找到衝突的物理根源（Px）；SF 找到用什麼場和物質去實現分離。三者是嵌套式放大鏡（10x → 100x → 手術刀），不是平行選單。 |
| **你在做什麼** | (a) 39 參數映射 → 矛盾矩陣查表 → 候選原理；(b) OZ-OT-Px 提取 → PC 造句；(c) 分離策略選擇（時間/空間/條件/系統層級）；(d) SF 標準解匹配 → 具體 F+S 配置 |
| **知識狀態變化** | 抽象矛盾 → 物理量二元對立(Px) → 分離策略 → 具體的場(F)+物質(S)+操作區(OZ)+操作時間(OT) |
| **多矛盾路由** | Bottleneck 路徑（一個 TC 主導）或 SIM 矩陣路徑（多獨立 TC 交互評估）。SIM 最多 2 輪，剩餘 -1 視為設計約束或升級為新 TC。 |
| **品質守護** | L1 跨域去錨定（每個原理具體化前必須問：控制方程？邊界條件？跨域冷效應？）；Evidence Registry 即時驗證數據宣稱。 |
| **對應實作** | `triz-contradict` skill + `triz-analyst` subagent（多 TC 並行） |

#### Gate 2: 矛盾解除（Contradiction Resolved）

| 退出條件 | 判定方式 |
|---------|---------|
| Px 已鎖定 | PC 造句可填完：「若 Px=A 則 P1 行但 P2 壞；若 Px=¬A 則 P2 行但 P1 壞」 |
| ≥1 分離策略通過三重驗證 | 控制方程存在 + 邊界條件合理 + 跨域案例佐證 |
| 每個解法含 F+S+OZ+OT | 不是抽象原理，是可計算的場+物質+操作域 |
| Evidence Registry 覆蓋 ≥ 50% | 數據宣稱有 HIGH+MEDIUM 來源佐證 |

---

### Phase 3: SPECIFY（凍結）

> **消除規格不確定性** — 從概念到可執行的工程文件

| 項目 | 內容 |
|------|------|
| **原始意圖** | TRIZ 的 Step 4（驗證 + 複雜度檢查）和 Step 5（WI 產出）合在一起回答：**「這個解法夠好嗎？如果夠好，寫成工程師看得懂的規格。」** 這是從「想」到「做」的分水嶺。 |
| **你在做什麼** | (a) Px 分離邏輯驗證（P1 達標且 P2 不超基線？）；(b) 四問複雜度評分（零件增加？能耗增加？認知負荷增加？符合演化趨勢？）→ Evolution/Patch 判定；(c) CCI 評分；(d) CAD 就緒評估；(e) WI/MC/ICD/Risk Register 文件產出 |
| **知識狀態變化** | 驗證過的解法 → 工程規格書（WI: 場+控制方程+數值 → MC: 物質+等級+性質 → ICD: 子系統邊界） |
| **Evolution vs Patch** | Q1-3 任兩個為 Yes（零件增/能耗增/認知增）或 Q4=No（不符演化）→ Patch（記為 TechnicalDebt）。否則 → Evolution。 |
| **Gate P 已合併在此** | CAD 就緒評估（cad_readiness）在此 Phase 完成，不另設獨立 Gate。 |
| **對應實作** | `triz-verify` skill（Phase 1-6）+ `triz-wi` skill（文件產出） |

#### Gate 3: 概念凍結（Concept Frozen）

> 這是全流程最重要的一個 Gate。它是發明性前端和工程性後端的分水嶺。
> 在此之前，改變方向的代價是「重新思考」。在此之後，改變方向的代價是「重做模具」。

| 退出條件 | 判定方式 |
|---------|---------|
| 複雜度判定 = Evolution 或 Weak Evolution | 四問複雜度 + 演化趨勢 |
| CCI ≤ 0.55 | Composite Complexity Index |
| Evidence Registry ≥ 50% HIGH+MEDIUM | 數據品質門檻 |
| CAD 就緒 = Go 或 Conditional | cad_readiness 三維評估 |
| WI + MC + ICD ≥ 1 of each | 工程文件產出完成且通過 schema 驗證 |
| TechnicalDebt 全部登記 | 已知 Patch 已記錄觸發條件 + 優先級 |

**等價聲明**：Gate 3 ≡ 舊 Gate P ≡ 舊 TR0。三個名稱描述同一個工程決策點。

---

### Phase 4: PROVE（驗證物理）

> **消除物理不確定性** — 從規格到模擬證明

| 項目 | 內容 |
|------|------|
| **原始意圖** | TR 的 TR1-TR2 本質上在問：**「紙上的設計在物理模擬中能否站住腳？」** 這是在投入實體加工之前，用最低代價（模擬）測試物理假設。 |
| **你在做什麼** | (a) 各子系統獨立 FEA/CFD/電磁模擬；(b) 14 項 V-test 模擬通過；(c) 模擬結果與 WI 規格對比（偏差 < 20%）；(d) 關鍵設計參數鎖定（軸承、齒形、封裝方式等）；(e) ICD 簽核 + 供應商能力確認 |
| **知識狀態變化** | 工程規格（紙上）→ 物理驗證（模擬中）。規格中的數值宣稱首次被數學模型驗證。 |
| **對應實作** | `tr-gate`（TR1/TR2 gate review）+ `tr-fea-assist`（FEA 設定輔助） |

#### Gate 4: 物理驗證（Physics Proven）

| 退出條件 | 判定方式 |
|---------|---------|
| WI-01~03 FEA/CFD 全部完成 | 各子系統模擬結果 vs 規格偏差 < 20% |
| 14 項 V-test 模擬通過 | 模擬中全部 pass |
| 設計參數已鎖定 | 主要尺寸、材料、工藝不再變動 |
| 4 份 ICD 已簽核 | 子系統介面凍結 |
| 供應商能力已確認 | 關鍵材料/工藝有供應商背書 |

---

### Phase 5: BUILD（建構驗證）

> **消除整合不確定性** — 從模擬到實體

| 項目 | 內容 |
|------|------|
| **原始意圖** | TR 的 TR3-TR6 本質上在問：**「模擬裡行得通的，在真實世界中也行得通嗎？」** 模擬永遠有假設（理想邊界、均勻材料、無裝配誤差）。只有實體原型才能暴露整合問題。 |
| **你在做什麼** | (a) 完整 3D CAD + BOM 凍結（TR3）；(b) GD&T 標註 + 公差鏈分析 + Design FMEA（TR3）；(c) 長交期物料採購 + 治工具設計（TR4，與 Phase 4 並行）；(d) Alpha 原型組裝（TR5）；(e) V1-V14 實測 + 量測值 vs 模擬偏差（TR6） |
| **知識狀態變化** | 模擬驗證 → 實體原型驗證。理論數值首次與實測數值對比。 |
| **對應實作** | `tr-gate`（TR3-TR6 gate review）+ `tr-test-report`（V-test 報告） |

#### Gate 5: 實體驗證（Alpha Verified）

| 退出條件 | 判定方式 |
|---------|---------|
| 3D CAD + BOM 完成且凍結 | Design FMEA 完成 |
| Alpha 原型功能正常 | 各子系統可運作（馬達轉、齒輪嚙合、PCM 吸熱） |
| V1-V14 實測通過 | 量測值 vs 模擬偏差 < 20% |
| 長交期物料已下單 | 供應鏈就緒 |

---

### Phase 6: HARDEN（製程固化）

> **消除製程不確定性** — 從原型到可重複製造

| 項目 | 內容 |
|------|------|
| **原始意圖** | TR 的 TR7-TR8 本質上在問：**「實驗室做出來的，工廠能穩定做出來嗎？」** Alpha 原型用的是實驗室工藝（CNC、手工組裝），量產需要的是壓鑄/射出/自動化——完全不同的製程物理。 |
| **你在做什麼** | (a) 壓鑄/射出/機加工供應商 DFM review（TR7）；(b) Process FMEA（TR7）；(c) Control Plan 初版（TR7）；(d) 量產意圖原型（Beta prototype，使用量產模具/工藝）（TR8）；(e) Beta 原型尺寸 + 功能驗證 + Control Plan 驗證（TR8） |
| **知識狀態變化** | 實驗室可行 → 工廠可行。製程參數（溫度、壓力、速度、冷卻時間）首次被鎖定。 |
| **對應實作** | `tr-gate`（TR7-TR8 gate review）+ `tr-dfm`（DFM/DFA 審查） |

#### Gate 6: 製程就緒（Manufacturing Ready）

| 退出條件 | 判定方式 |
|---------|---------|
| DFM review 完成 | 所有供應商 DFM 報告簽回 |
| Process FMEA 完成 | 製程風險識別 + 緩解 |
| Beta 原型尺寸 + 功能 pass | 使用量產模具/工藝製作的原型通過驗證 |
| Control Plan 驗證通過 | 量測系統 + 製程控制參數已確認 |

---

### Phase 7: SCALE（量產釋放）

> **消除規模不確定性** — 從小批量到大量穩定

| 項目 | 內容 |
|------|------|
| **原始意圖** | TR 的 TR9-TR10 本質上在問：**「幾十件做得出來，幾千件還行嗎？」** 規模帶來的是統計問題（Cpk）和供應鏈問題（來料波動、多批次一致性），不是設計問題。 |
| **你在做什麼** | (a) DVP&R 全項完成：耐久、環境、安全（TR9）；(b) PV 測試通過（TR9）；(c) Cpk ≥ 1.33（TR10）；(d) 量產 SOP 簽核（TR10）；(e) PPAP 等效文件包完成（TR10） |
| **知識狀態變化** | 小批量可行 → 大量穩定可行。從「能做」到「能穩定地一直做」。 |
| **對應實作** | `tr-gate`（TR9-TR10 gate review）+ `tr-test-report`（PV/DVP&R 報告） |

#### Gate 7: 量產釋放（Production Released）

| 退出條件 | 判定方式 |
|---------|---------|
| DVP&R 全項完成 | 耐久 + 環境 + 安全 全部 pass |
| Cpk ≥ 1.33 | 量產能力指標 |
| 量產 SOP 簽核 | 作業標準書已定案 |
| PPAP 等效完成 | 全套品質文件包 |

---

## 全景圖

```
 發明性前端（TRIZ 引擎）                    工程性後端（TR 引擎）
 ┌──────────────────────────┐              ┌──────────────────────────────────────┐
 │                          │              │                                      │
 │  P0       P1      P2     │    P3        │  P4      P5       P6        P7       │
 │ SCOPE → MAP → RESOLVE →│→ SPECIFY →  │→ PROVE → BUILD → HARDEN → SCALE    │
 │  ↓        ↓       ↓     │     ↓        │   ↓       ↓        ↓        ↓       │
 │ G0      G1      G2      │    G3        │  G4      G5       G6       G7       │
 │ 問題     系統    矛盾    │   概念       │  物理    實體     製程     量產      │
 │ 鎖定     理解    解除    │   凍結       │  驗證    驗證     就緒     釋放      │
 │                          │   ═══        │                                      │
 │                          │  分水嶺      │                                      │
 └──────────────────────────┘              └──────────────────────────────────────┘

 ← 改變方向的代價：重新思考 →   ← 改變方向的代價：重做模具 →
```

---

## 與舊命名的對照表

### Phase 對照

| RDP-8 Phase | 舊 TRIZ Step | 舊 TR Gate | 舊 BDD Gate | 消除的不確定性 |
|-------------|-------------|-----------|------------|--------------|
| **P0 SCOPE** | Step 0 | — | D1 `[absorbed]` | 問題 |
| **P1 MAP** | Step 1 | — | D2 `[absorbed]` | 系統 |
| **P2 RESOLVE** | Step 2+3 | — | X1/X2 `[absorbed]` | 解法 |
| **P3 SPECIFY** | Step 4+5 | TR0 | P `[absorbed]` | 規格 |
| **P4 PROVE** | — | TR1+TR2 | — | 物理 |
| **P5 BUILD** | — | TR3+TR4+TR5+TR6 | V1 `[absorbed]` | 整合 |
| **P6 HARDEN** | — | TR7+TR8 | V2 `[absorbed]` | 製程 |
| **P7 SCALE** | — | TR9+TR10 | V4 `[absorbed]` | 規模 |

### Gate 對照

| RDP-8 Gate | 舊 TRIZ Gate | 舊 TR Gate | 舊 BDD Gate | 確認的信心 |
|-----------|-------------|-----------|------------|-----------|
| **G0** | G0/G0'/G0'' | — | D1 | 「我知道問題在哪」 |
| **G1** | G1/G1' | — | D2 | 「我知道系統怎麼運作」 |
| **G2** | G2/G2'/G3/G3' | — | X1/X2 | 「我知道怎麼解矛盾」 |
| **G3** | G4/G4' | TR0 | P | 「規格已凍結，可以開始做」 |
| **G4** | — | TR1+TR2 | — | 「模擬證明物理可行」 |
| **G5** | — | TR3-TR6 | V1 | 「實體原型證明設計可行」 |
| **G6** | — | TR7-TR8 | V2 | 「工廠能穩定地做出來」 |
| **G7** | — | TR9-TR10 | V4 | 「大量生產沒問題」 |

---

## 與國際標準的對齊

| RDP-8 | APQP Phase | VDA MLA | NASA TRL | Stage-Gate (Cooper) |
|-------|-----------|---------|----------|-------------------|
| P0 SCOPE | — | ML0 | TRL 1-2 | Discovery |
| P1 MAP | — | ML0 | TRL 2-3 | Scoping |
| P2 RESOLVE | — | ML1 | TRL 3-4 | Business Case |
| P3 SPECIFY | Phase 1 | ML2 | TRL 4-5 | Development (概念) |
| P4 PROVE | Phase 2 | ML3 | TRL 5-6 | Development (模擬) |
| P5 BUILD | Phase 3 | ML4-5 | TRL 6-7 | Testing |
| P6 HARDEN | Phase 4 | ML6 | TRL 7-8 | Testing (DFM) |
| P7 SCALE | Phase 5 | ML7 | TRL 8-9 | Launch |

**RDP-8 的獨特貢獻**：APQP/VDA/Stage-Gate 在 P0-P2（發明性前端）只有一個模糊的「概念」階段。RDP-8 將其展開為 3 個結構化的 Phase（SCOPE→MAP→RESOLVE），每個都有明確的知識轉換和退出條件。這是傳統方法論的盲區。

---

## State 架構

### 雙狀態機

```
┌─ TRIZ Session State (.triz-state.json) ──────────────────┐
│  管轄：P0 SCOPE → P1 MAP → P2 RESOLVE → P3 SPECIFY      │
│  Scope：Session 級（每次推理一個 .json）                    │
│  操作者：triz-* skills                                    │
│  核心欄位：current_step, contradictions[], solutions[],    │
│           complexity_check, evidence_registry, cad_readiness│
└──────────────────────────────────────────────────────────┘
                    ↓ G3 凍結後
┌─ TR Gate State (.tr-state.json) ─────────────────────────┐
│  管轄：P4 PROVE → P5 BUILD → P6 HARDEN → P7 SCALE       │
│  Scope：專案級（一個專案一個 .json）                        │
│  操作者：tr-* skills                                      │
│  核心欄位：gates.TR1-TR10 per subsystem, v_tests[],       │
│           risks[], wi_status[]                            │
└──────────────────────────────────────────────────────────┘
```

### Phase 推導規則

不需要第三個 state file。Phase 可從現有兩個 state 推導：

```
if .triz-state.json 不存在            → Pre-P0（尚未開始）
if current_step ∈ {step0}             → P0 SCOPE
if current_step ∈ {step1}             → P1 MAP
if current_step ∈ {step2, step3}      → P2 RESOLVE
if current_step ∈ {step4, step5}      → P3 SPECIFY
if .tr-state.json 存在 + TR1 未通過    → P4 PROVE
if TR1-TR2 通過 + TR6 未通過           → P5 BUILD
if TR6 通過 + TR8 未通過               → P6 HARDEN
if TR8 通過                           → P7 SCALE
```

---

## Skill 實作對照

| RDP-8 Phase | Skills | Subagents |
|-------------|--------|-----------|
| P0 SCOPE | `triz-router`, `triz-scoping` | — |
| P1 MAP | `triz-model` | — |
| P2 RESOLVE | `triz-contradict` | `triz-analyst` (multi-TC fan-out) |
| P3 SPECIFY | `triz-verify`, `triz-wi` | — |
| P4 PROVE | `tr-gate` (TR1/TR2), `tr-fea-assist` | — |
| P5 BUILD | `tr-gate` (TR3-TR6), `tr-test-report` | — |
| P6 HARDEN | `tr-gate` (TR7/TR8), `tr-dfm`, `tr-sop` | — |
| P7 SCALE | `tr-gate` (TR9/TR10), `tr-test-report`, `tr-spc`, `tr-ppap` | — |

### 擴展路線（分階段建設）

| 階段 | 觸發條件 | 新增 Skill | RDP-8 位置 |
|------|---------|-----------|-----------|
| MVP Q3 | 多人使用、需正式 Pre-CAD UX | `precad-review` | P3 SPECIFY 的獨立 UX |
| Beta Q4 | 跨部門決策追溯 | `kt-decision` | P3-P5 之間的治理層 |
| Beta Q4 | Post-CAD 審查 | `devil-advocate` | P5 BUILD 後的品質守護 |
| GA Q1/27 | ≥5 完成專案 | `knowledge-agent` | P7 SCALE 後的知識回寫 |
| 規模化 | 多租戶 + 審計 | `product-gate` | 跨 Phase 的編排層 |

---

## 外力介入需求清單（External Dependency Roadmap）

> 以下項目無法由 harness 系統（LLM + 檔案讀寫）獨立完成，需要**物理設備、外部軟體、供應商互動、工廠產線**等外力資源。
> 本節作為產品開發 roadmap 的持久記錄，確保這些需求不被遺忘。

### 分 Phase 外力需求總覽

```
P0-P3 TRIZ 前端
  └─ 無外力需求（純推理 + 文件產出）✅

P4 PROVE — 物理驗證
  ├─ [EXT-01] FEA/CFD 模擬執行
  └─ [EXT-02] 材料實測驗證

P5 BUILD — 原型整合
  ├─ [EXT-03] 供應商報價/交期/能力確認
  ├─ [EXT-04] 原型實物製作（CNC/3D Print/模具）
  └─ [EXT-05] Alpha 測試執行（實驗室設備 + 治具）

P6 HARDEN — 製程強化
  ├─ [EXT-06] Beta 原型製作（量產意圖製程）
  ├─ [EXT-07] 量測數據取得（CMM/量具/SPC 系統）
  └─ [EXT-08] DFM 供應商互動（模流/鑄造/加工回饋）

P7 SCALE — 量產釋放
  ├─ [EXT-09] PV 測試執行（耐久/環境/安全/防水）
  ├─ [EXT-10] Cpk/SPC 量產數據收集
  ├─ [EXT-11] PPAP 外部項（客戶簽核/實物樣品/量具）
  ├─ [EXT-12] SOP 現場驗證 + 操作員訓練
  └─ [EXT-13] 量產移轉（工廠/設備/人員）
```

### 逐項詳細說明

#### EXT-01: FEA/CFD 模擬執行

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P4 PROVE |
| **Gate** | G4（TR1-TR2） |
| **需要什麼** | ANSYS/Abaqus/COMSOL/JMAG 等 CAE 軟體授權 + 工程師操作 |
| **Harness 已做** | `tr-fea-assist` 提供材料卡（MC）、邊界條件建議、網格策略、結果判讀 |
| **Harness 不能做** | 實際執行 FEA solver、產出結果檔 |
| **銜接方式** | 工程師用 `tr-fea-assist` 產出的設定 → 在 CAE 軟體中執行 → 結果回填到 WI → `tr-gate TR1` 驗證 |

#### EXT-02: 材料實測驗證

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P4 PROVE |
| **Gate** | G4（TR1-TR2） |
| **需要什麼** | 萬能試驗機、DSC/TGA、金相分析等材料測試設備 |
| **Harness 已做** | `triz-wi` 產出 MC（Material Card）含 Confidence 等級 |
| **Harness 不能做** | 實際量測材料性質、驗證 MC 中 Confidence = LOW 的數據 |
| **銜接方式** | MC 中標記 LOW confidence 的性質 → 安排實測 → 更新 MC → `tr-gate TR2` 確認參數凍結 |

#### EXT-03: 供應商報價/交期/能力確認

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P5 BUILD |
| **Gate** | G5（TR2-TR4） |
| **需要什麼** | 供應商聯繫、RFQ 流程、產能評估、合約簽訂 |
| **Harness 已做** | `triz-wi` 在 WI-procurement 中提供 BOM 骨架 + 供應商評估要點；`tr-gate TR2` checklist 含「供應商 nominated + 能力確認」 |
| **Harness 不能做** | 實際詢價、比價、簽約、確認交期 |
| **銜接方式** | WI-procurement BOM → 採購部門執行 RFQ → 結果回填 `.tr-state.json` supplier 記錄 → `tr-gate TR2` 驗證 |

#### EXT-04: 原型實物製作

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P5 BUILD |
| **Gate** | G5（TR4-TR5） |
| **需要什麼** | CNC 加工中心 / 3D 列印機 / 射出模具 / 組裝工站 |
| **Harness 已做** | `triz-wi` 產出 WI-structural（CAD 組裝指引）+ BOM + 公差鏈 |
| **Harness 不能做** | 實際製造零件、組裝原型 |
| **銜接方式** | WI-04 CAD 指引 → 製造 → 組裝 → `tr-gate TR5` Alpha 原型確認 |

#### EXT-05: Alpha 測試執行

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P5 BUILD |
| **Gate** | G5（TR5-TR6） |
| **需要什麼** | 測試台架、扭矩感測器、溫度記錄器、振動台、環境箱等 |
| **Harness 已做** | `tr-test-report` 產出測試計劃模板（`/tr-test plan`）、引導數據輸入、自動 PASS/FAIL 判定、FEA correlation |
| **Harness 不能做** | 實際執行 V1-V14 測試、取得量測數據 |
| **銜接方式** | `/tr-test plan` 產出計劃 → 實驗室執行 → 數據回填 `/tr-test V1` → `tr-gate TR6` 驗證 |

#### EXT-06: Beta 原型製作（量產意圖製程）

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P6 HARDEN |
| **Gate** | G6（TR7-TR8） |
| **需要什麼** | 量產模具/治工具 + 量產供應商 + 量產製程（壓鑄/射出/精加工） |
| **Harness 已做** | `tr-dfm` 提供 DFM/DFA checklist；`tr-sop` 產出 SOP 草稿 |
| **Harness 不能做** | 製作量產意圖原型（需要量產模具而非 prototype tooling） |
| **銜接方式** | DFM review → 供應商修改模具 → Beta 原型 → 尺寸+功能測試 → `tr-gate TR8` |

#### EXT-07: 量測數據取得

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P6 HARDEN / P7 SCALE |
| **Gate** | G6-G7（TR8-TR10） |
| **需要什麼** | CMM（三次元量測儀）、輪廓儀、表面粗度計、GR&R 量具分析設備 |
| **Harness 已做** | `tr-spc` 可計算 Cpk/Ppk（只需數據輸入）；KC List 定義了量什麼 |
| **Harness 不能做** | 實際量測零件、取得原始數據 |
| **銜接方式** | KC List → 品保量測 → 數據輸入 `/tr-spc KC-001` → 計算報告 → `tr-gate TR9` |

#### EXT-08: DFM 供應商互動

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P6 HARDEN |
| **Gate** | G6（TR7） |
| **需要什麼** | 壓鑄/射出/加工供應商的 DFM 回饋（拔模角、壁厚、澆口位置、纖維方向、切削策略） |
| **Harness 已做** | `tr-dfm` 產出通用 DFM checklist + 製程參數建議 |
| **Harness 不能做** | 取得供應商的專有製程限制和經驗回饋 |
| **銜接方式** | `tr-dfm` checklist → 供應商 review → 回饋整合到 DFM report → `tr-gate TR7` |

#### EXT-09: PV 測試執行

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P7 SCALE |
| **Gate** | G7（TR9） |
| **需要什麼** | 耐久測試台（100k cycles）、環境箱（-20°C~+50°C）、安全測試（EN 15194）、IP67 防水測試 |
| **Harness 已做** | `tr-test-report` DVP&R 總表 + 自動 PASS/FAIL 判定 |
| **Harness 不能做** | 實際執行 PV 測試（樣本數 ≥ 30，需要量產線零件） |
| **銜接方式** | DVP&R 計劃 → 量產線取樣 → PV 測試 → 數據回填 `/tr-test dvpr` → `tr-gate TR9` |

#### EXT-10: Cpk/SPC 量產數據收集

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P7 SCALE |
| **Gate** | G7（TR9-TR10） |
| **需要什麼** | 量產線 SPC 系統、連續生產數據（≥ 30 件 × 每個 KC） |
| **Harness 已做** | `tr-spc` 計算 Cpk/Ppk + 製程偏移分析 + 判定報告 |
| **Harness 不能做** | 從量產線收集連續量測數據 |
| **銜接方式** | KC List → 產線量測 → 數據匯出 → `/tr-spc all` → SPC 報告 → `tr-ppap assemble` |

#### EXT-11: PPAP 外部項

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P7 SCALE |
| **Gate** | G7（TR10） |
| **需要什麼** | 客戶工程核准(#3)、合格實驗室文件(#12)、外觀核准(#13)、樣品零件(#14)、留樣(#15)、檢具(#16)、客戶特殊要求(#17) |
| **Harness 已做** | `tr-ppap` 掃描所有 18 項完整度、標記 EXTERNAL 項、產出 PSW + 索引 |
| **Harness 不能做** | 取得客戶簽核、準備實物樣品、校驗檢具 |
| **銜接方式** | `/tr-ppap check` 列出缺口 → 逐項補齊 → `/tr-ppap assemble` 產出完整包 → 客戶審查 |
| **PPAP 項次明細** | #3, #12, #13, #14, #15, #16, #17（共 7 項 EXTERNAL） |

#### EXT-12: SOP 現場驗證 + 操作員訓練

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P7 SCALE |
| **Gate** | G7（TR9-TR10） |
| **需要什麼** | 工廠工站、操作員、現場試跑、修訂迴圈 |
| **Harness 已做** | `tr-sop` 產出 SOP 草稿（含步驟、管控點、異常處理） |
| **Harness 不能做** | 現場試跑驗證 SOP 可行性、訓練操作員、正式簽核發行 |
| **銜接方式** | SOP 草稿 → 現場試跑 → 修訂 → 主管簽核 → `tr-gate TR10` 確認 SOP signed off |

#### EXT-13: 量產移轉

| 項目 | 說明 |
|:-----|:-----|
| **Phase** | P7 SCALE |
| **Gate** | G7（TR10） |
| **需要什麼** | 量產工廠就緒、設備安裝校驗、人員訓練完成、品質系統建立 |
| **Harness 已做** | `tr-gate TR10` checklist 含量產移轉確認項 |
| **Harness 不能做** | 實際的工廠準備、設備採購、人員到位 |
| **銜接方式** | TR10 gate review 通過 = 量產釋放（所有前置條件已滿足） |

### Harness ↔ 外力 銜接矩陣

| EXT-ID | Harness 上游輸出 | 外力執行 | Harness 下游輸入 | 驗證 Gate |
|:-------|:----------------|:---------|:----------------|:----------|
| EXT-01 | `tr-fea-assist` MC + 設定 | CAE 執行 | WI FEA 結果段落 | G4 (TR1) |
| EXT-02 | MC Confidence 標記 | 材料實測 | MC 數據更新 | G4 (TR2) |
| EXT-03 | WI-procurement BOM | 採購 RFQ | `.tr-state` supplier 記錄 | G5 (TR2) |
| EXT-04 | WI-04 CAD 指引 | 製造+組裝 | 組裝報告 | G5 (TR5) |
| EXT-05 | `/tr-test plan` | 實驗室測試 | `/tr-test Vn` 數據 | G5 (TR6) |
| EXT-06 | `tr-dfm` + `tr-sop` | 量產模具製造 | Beta 尺寸報告 | G6 (TR8) |
| EXT-07 | KC List | CMM 量測 | `/tr-spc` 數據 | G6-G7 |
| EXT-08 | `tr-dfm` checklist | 供應商回饋 | DFM report 更新 | G6 (TR7) |
| EXT-09 | DVP&R 計劃 | PV 測試 | `/tr-test dvpr` 數據 | G7 (TR9) |
| EXT-10 | KC List | 產線 SPC | `/tr-spc` 數據 | G7 (TR9-10) |
| EXT-11 | `/tr-ppap check` 缺口 | 客戶+實物 | PPAP 補齊 | G7 (TR10) |
| EXT-12 | `tr-sop` 草稿 | 現場試跑 | SOP 正式版 | G7 (TR10) |
| EXT-13 | TR10 checklist | 工廠準備 | 量產移轉確認 | G7 (TR10) |

---

## 設計原則

### 1. 每個 Phase 只問一個問題

如果一個 Phase 要回答兩個獨立的問題，它應該被拆成兩個 Phase。
如果兩個相鄰 Phase 回答的是同一類問題，它們應該被合併。

### 2. Gate 是二元判定，不是評分

Gate 的答案只有 Pass / Fail / Conditional。
不是「你的物理驗證得了 78 分」，而是「模擬偏差 < 20%？是/否」。

### 3. Gate 失敗 = 回到上一個 Phase，不是跳回起點

G4 失敗（模擬不通過）→ 回到 P3 SPECIFY 修改規格，不需要回到 P0 SCOPE。
G2 失敗（找不到分離策略）→ 回到 P1 MAP 重新建模或重定義子系統邊界。

### 4. 發明性前端不可跳過

P4-P7（工程後端）建立在 P0-P3（發明性前端）的輸出上。
跳過 P0-P3 直接做 P4 = 在沒有矛盾解析的情況下做 FEA，等於在優化一個可能錯誤的設計。

### 5. 工程後端可並行

P4 PROVE 中的不同子系統 FEA 可以並行。
P4（長交期物料採購）可與 P5（詳細設計）並行。
但 P5 BUILD → P6 HARDEN → P7 SCALE 是嚴格順序的。

---

## CLI/HTTP 一致性

所有 Phase 通過同一個 `AgentLoop` 執行，差異僅在入口包裝：

```
CLI:  python -m app.harness <cmd> [input]
      → resolve_command() → build_system_prompt() → AgentLoop.run() → stdout

HTTP: POST /api/v1/sessions/{id}/run (or /run/stream)
      → resolve_command() → build_system_prompt() → AgentLoop.stream() → SSE
```

新增 Skill = 新增 `SKILL.md` 檔 → 兩個介面自動可用（skill loader 自動發現）。

---

## 文件溯源

- v1.0 Flow Contract：本文件前身，合約式映射（PRD Epic ↔ TRIZ/TR Step）
- PRD：[`02_prd.md`](./02_prd.md)
- BDD：[`03_bdd_guide.md`](./03_bdd_guide.md)
- TRIZ 方法論：[`DK-01`](../../docs/_domain-knowledge/DK-01--auto-triz-process.md), [`DK-02`](../../docs/_domain-knowledge/DK-02--triz-mechanics.md)
- TR 框架：[`tr_gate_framework.md`](../../docs/_harness/engineering/tr_gate_framework.md)
- Gate 定義：[`DK-04`](../../docs/_domain-knowledge/DK-04--data-model-and-gate.md)
- Skills 索引：[`.claude/skills/INDEX.md`](../../.claude/skills/INDEX.md)
- 國際標準對齊：APQP (AIAG), VDA MLA (ML0-ML7), ISO 16290 (TRL)

## 變更紀錄

| 日期 | 版本 | 變更 |
|:-----|:-----|:-----|
| 2026-04-28 | v2.1 | 新增 §外力介入需求清單（13 項 EXT-01~13）+ Skill 對照表更新（+tr-sop/tr-spc/tr-ppap）+ 銜接矩陣 |
| 2026-04-28 | v2.0 | 從合約式映射重建為 RDP-8 統一框架：8 Phase + 8 Gate + 不確定性消除公理 |
| 2026-04-28 | v1.0 | 初版 Flow Contract：PRD Epic ↔ TRIZ/TR 映射 + BDD Gate 層級分析 |
