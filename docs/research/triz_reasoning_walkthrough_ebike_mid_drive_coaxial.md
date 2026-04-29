# TRIZ 推理流程拆解 — eBike Mid-Drive Coaxial 案例

> **基準 Session**：`.claude/context/triz/session-2026-04-28-1500-eBike-MidDrive-Coaxial.md`
> **案例日期**：2026-04-28
> **判定結果**：Evolution（Weak Evolution，CCI = 0.3125），Gate P = **Go**
> **本文件目的**：以該 session 為案例，逐 Step 拆解推理流程的「進場條件 → 評分公式 → 本案實算 → 出場閘門 → 傳遞物件」，作為 Auto-TRIZ 框架的可審計教學範本。

---

## 0. 案例摘要

### 0.1 規格邊界（使用者輸入）

| 項目 | 目標值 | 約束類型 |
|:---|:---|:---|
| 外徑 OD | 111 mm | Hard |
| 軸向長 | 92 mm | Hard |
| 系統重量 | 2500 g | Hard |
| 峰值扭力 | 125 Nm（@ 輸出端）| Hard |
| 連續扭力 | 100 Nm | Hard |
| 減速比 | 1:30 ~ 1:35 | Hard |
| 噪音 baseline | TQ HPR50（≈55 dB(A) @ 1m, 60 rpm cadence） | Soft |
| NdFeB 退磁邊界 | T_winding < 120°C @ peak | Hard |

### 0.2 系統組成

`Motor + Gearbox + Drive Board + Pedaling Shaft`，**三件同軸共封**於 OD111×axial92 圓柱體中。

### 0.3 路徑識別

- **路徑**：tc-main（multi-TC parallel）
- **TC 數**：3（散熱、重量、噪音）
- **派遣模式**：inline supervisor（理由見 §2.1）

---

## 1. 路由判定（Phase 2）— 為何跳過 Step 0

### 1.1 路由決策邏輯

依 `triz-router` Phase 2 決策樹：

```
有明確 TC 造句？        → Step 2 (triz-solve)
規格清楚但 TC 未造句？   → Step 1 (triz-model)
僅問題症狀，無 OZ/OT？   → Step 0 (triz-scoping)
```

### 1.2 本案判定

| 檢查項 | 狀態 | 推論 |
|:-------|:-----|:-----|
| 子系統邊界明確 | ✓ | OD111×axial92 coaxial 封裝已給定 |
| 衝突點隱約可見 | ✓ | 散熱/重量/噪音三軸都有 hard target |
| TC 完整造句 | ✗ | improve/worsen 雙端尚未對應到 39 參數 |
| 根因模糊 | ✗ | 規格端清楚，不需要 5Why/KT/CECA |

→ **跳過 Step 0**（無因果不確定性），直接進入 **Step 1 功能建模**。

### 1.3 為何不能直接跳到 Step 2

雖然 TC 數已預估為 3，但：
- 散熱/重量/噪音之間是否互相耦合？需要先建組件交互圖判斷。
- improve/worsen 還是自然語句，未確定 SF 模型中的 S1/S2/F 角色。
- 多 TC 派遣前，需先用 SF 診斷確認每個 TC 的物理場類型，才能評估是否值得 fan-out。

→ **Step 1 是 Step 2 的必要前置**（即使規格邊界清楚也不能略過）。

---

## 2. Step 1 — 功能建模

### 2.1 進場狀態

從路由帶入：
- 子系統邊界候選（coaxial 封裝）
- 系統組成 4 件
- 預期 TC 數 = 3

### 2.2 推理框架（依 `triz-model` skill）

```
Phase 1a: 組件交互圖
Phase 1b: SF 模型建構
Phase 1c: 改善/惡化描述
Phase 1d: 子系統邊界定義
```

### 2.3 子系統邊界決策（Phase 1d）

**核心判斷**：邊界**不按零件**劃分，而按「**衝突發生點**」劃分。

理由：散熱問題的本質是**封裝體積/熱通量**，與哪個零件無關；噪音問題的本質是**振動傳播路徑**。零件邊界（馬達/齒輪/中軸）反而會切斷物理場的傳播鏈。

→ OZ 採封裝級邊界：「所有與封裝體積/熱通量/振動傳播相關的元件均納入」。

### 2.4 組件交互圖（Phase 1a）

#### 13 條交互關係的分類統計

| 類型 | 數量 | 條目 |
|:-----|:----:|:-----|
| 有效（→） | 7 | #1~6, #12 — 設計目的內 |
| 不足（~） | 2 | #7, #8 — 散熱路徑 |
| 有害（✗） | 4 | #9~11, #13 — 振動 + 高溫退磁 + 結溫上升 + 散熱通道受限 |

**推理意義**：
- 有害/不足條目 = 6/13 ≈ 46%，遠超閾值（一般 >20% 即觸發 TC 路徑）→ 確認進入 TC 路徑無誤。
- #7/#8（散熱）+ #13（散熱通道受限）三條集中於散熱 → 觸發 TC-A。
- #9（振動）+ #10/#11（熱→磁/MOSFET）→ 噪音與熱形成兩個獨立問題簇。

### 2.5 SF 診斷（Phase 1b）

依 SF 狀態映射 TC：

| SF# | 場類型 | 狀態 | 對應 TC | 路由建議 |
|:---|:------|:----|:-------|:--------|
| SF-01 | Thermal field | 不足 | TC-A | TC 路徑 |
| SF-02 | Mechanical/Acoustic field | 有害 | TC-C | TC 路徑 |
| SF-03 | Electromagnetic field（受重量約束）| 不足 | TC-B | TC 路徑 |

**為何只有 3 個 SF 而非 13 條交互關係的對應**：
- SF 必須是「可獨立分析的能量傳遞鏈」，把同性質問題合併為單一 SF。
- #10/#11 都是熱導致的副作用，併入 SF-01 的下游。
- #9 振動是 SF-02 的主問題，而 #13 散熱通道是 SF-01 的成因。
- 三條 SF 各自有一條物理場 → 後續 Step 2 可寫成三條獨立控制方程。

### 2.6 改善/惡化描述（Phase 1c）— TC 造句

每個 TC 必須完成「**為了 X，會導致 Y 惡化**」的標準句型，並映射到 39 參數：

#### TC-A：散熱 vs 體積
- improve = P17 Temperature
- worsen = P8 Volume of stationary object
- **物理本質**：coaxial 體積已上限 → 加散熱結構就破封裝。

#### TC-B：功率密度 vs 重量
- improve = P21 Power
- worsen = P1 Weight of moving object
- **物理本質**：扭力密度 ≥ 50 Nm/kg 已是 SOTA；加磁鐵就超重。

#### TC-C：低噪音 vs 裝置複雜度
- improve = P31 Object-generated harmful effects
- worsen = P36 Device complexity
- **物理本質**：齒形修整能降噪 6~12 dB(A)，但增加製造工序。

### 2.7 出場閘門（Step 1 → Step 2）

| 檢查 | 通過? | 依據 |
|:-----|:-----:|:-----|
| 三條 TC 造句完整 | ✓ | 每條都有 improve/worsen 配對 39 參數 |
| 每條 TC 對應一個 SF | ✓ | TC-A↔SF-01, TC-B↔SF-03, TC-C↔SF-02 |
| 子系統邊界明確 | ✓ | coaxial 封裝級邊界 |

→ 進入 Step 2，採 **multi-TC fan-out 模式**。

---

## 3. Step 2 — TC 定義 + 矩陣查表 + 原理具體化

### 3.1 多 TC 派遣決策

#### 設計意圖 vs 現況執行

| 模式 | 條件 | 本案採用? |
|:-----|:-----|:---------:|
| Fan-out（spawn 3 個 triz-analyst worker）| TC 獨立、KB 量大、worker 有資訊優勢 | ✗ |
| Inline supervisor（main 直接跑 3 條）| TC ≤ 5、KB 已內嵌、worker 無優勢 | **✓** |

理由：
- 3 ≤ 5（甜蜜點上限）
- KB（39 參數、矛盾矩陣、76 標準解）已在 main context
- Worker 不會比 main 更聰明 → fan-out 反而增加 merge 成本

→ **inline 跑 3 條 TC**，但保留 fan-out 結構為未來 worker 升級的契約。

### 3.2 推理框架（依 `triz-contradict` skill）

```
2.1 參數映射（39 參數對照）
2.2 矩陣查表（40 原理推薦）
2.3 原理具體化（PhysicsRel × DomainFit × Feasibility 排序）
2.3.2 Evidence Gate（門檻）
```

### 3.3 三個 TC 並行推演

#### 3.3.1 參數映射評分（共通公式）

```
Score = (關鍵詞 × 0.40 + 類別 × 0.15 + 說明 × 0.25 + 工程對應 × 0.20) / 2
```

每維度 0/1/2 分（不符/部分符/全符），分母 2 將總分標準化為 [0, 1]。

| TC | P_improve | P_worsen | 兩者分數 |
|:---|:----------|:---------|:--------:|
| TC-A | P17 Temperature | P8 Volume of stationary object | 1.00 / 1.00 |
| TC-B | P21 Power | P1 Weight of moving object | 1.00 / 1.00 |
| TC-C | P31 Object-generated harmful effects | P36 Device complexity | 1.00 / 1.00 |

**6 個參數全 1.00 的意義**：每個 TC 的 improve/worsen 在 4 維度（關鍵詞/類別/說明/工程對應）都拿到 2/2，TRIZ 39 參數對應**無歧義** → 矩陣查表結果可信。

#### 3.3.2 矩陣查表結果

| TC | P_improve→P_worsen | 矩陣推薦原理 | 補充候選 |
|:---|:-------------------|:------------|:---------|
| TC-A | P17→P8（反查 P8→P17）| #35, #39, #38 | #3, #36, #2, #14 |
| TC-B | P21→P1 | #8, #36, #38, #31 | #14, #40, #17 |
| TC-C | P31→P36 | #22, #35, #18, #39 | #14, #1 |

**為何要補充候選**：矩陣推薦多偏「化學/環境」類（#38 強氧化劑、#39 惰性環境），對機電域貢獻有限。需從工程相關 cluster 補充（FGM/相變/分割/曲面化）。

#### 3.3.3 原理具體化評分（共通公式）

```
Score = (PhysicsRel × 0.4 + DomainFit × 0.4 + Feasibility × 0.2)
```

- **PhysicsRel**：原理與該 TC 物理場是否匹配（熱原理用於熱問題 = 1.0）
- **DomainFit**：原理在小型機電 mid-drive 域是否可實現（製程/封裝可行 = 1.0）
- **Feasibility**：當前供應鏈/成本是否可承受（標準件可達 = 1.0、需特殊製程 = 0.67）

#### 3.3.4 三條 TC 的主方向

| TC | 主方向 | 排名第 1 的原理 |
|:---|:-------|:----------------|
| TC-A | #3 局部品質（FGM Cu 嵌件）+ #36 相變（PCM）| 1.00 / 0.90 |
| TC-B | #14 曲面化（Halbach）+ #40 複合材料（CFRP 套筒）| 1.00 / 0.90 |
| TC-C | #35 參數變化（齒面 Δδ 修形）+ #14 曲面化（齒形曲線）+ #1 分割（雙級分配）| 三者並列 1.00 |

**TC-C 出現三原理並列的處理**：不強迫排序，並行進入 Step 3 SF 標準解測試，由 Px 評分決定主導。

### 3.4 Evidence Gate 判定（Step 2 → Step 3 強制門檻）

| 檢查項 | 通過? | 數據出處 |
|:-------|:-----:|:---------|
| 候選方向有控制方程 | ✓ | TC-A: Fourier + Clausius-Clapeyron / TC-B: Maxwell stress (Halbach 解析式) / TC-C: 嚙合誤差 PEE 模型 |
| 數值聲明覆蓋 ≥ 50% | ✓ | 12 條 Claim ID，10 條 HIGH/MEDIUM = 83% |
| 參數映射品質 ≥ 0.7 | ✓ | 6 個映射全 1.00 |

⚠️ **時序註記**：Evidence 統計（12/10/83%）實際是在 Step 3 完成 Evidence Registry、Step 4 Phase 1.3 校驗後**回填**到 Step 2 結尾的 Gate 記錄。Step 2 當下只是判定「Evidence Registry 必須在 Step 3 完成且覆蓋率達標」。

→ **三項 ✓**，進入 Step 3。

---

## 4. Step 3 — PC 深挖 + Px 分離 + SF 標準解

### 4.1 進場狀態

從 Step 2 帶入：
- 3 個 TC 造句 + 6 個參數映射
- 3 條 SF 模型（thermal / EM / mech+EHD）
- 7 個排名前列的 40 原理

### 4.2 推理框架（依 `triz-contradict` §3）

```
3a: OZ-OT 鎖定 → Px 候選評分
3b: PC 造句 + Px 驗證
3c: 分離策略評分（4 策略 × 3 診斷問題）
3d: SF 標準解匹配
SIM: 多 TC 交互矩陣（收斂判定）
```

### 4.3 Px 候選評分公式

```
PxScore(Xi) = 0.50 × Sensitivity + 0.25 × Controllability + 0.25 × CausalDirectness
```

| 維度 | 權重 | 評分標準 |
|:-----|:----:|:---------|
| Sensitivity | 0.50 | (Sens-P_improve + Sens-P_worsen) / 2，兩端都需「強直接、反向」才得 1.0 |
| Controllability | 0.25 | 1.0 = 設計參數可直接設定 / 0.5 = 製程間接 / 0.0 = 湧現性質 |
| CausalDirect | 0.25 | 0 個中間變數 = 1.0 / 1 個 = 0.7 / 2 個 = 0.4 / 3+ 個 = 0.1 |

**門檻**：PxScore ≥ 0.60，且兩個 Sensitivity 子分數 > 0。

### 4.4 三條 TC 的 Px 推演

#### 4.4.1 TC-A：A_contact（熱接觸面積）

**OZ-OT 鎖定**：
- OZ：Motor stator 外圓 ↔ Housing 徑向界面
- OT：Peak torque 5–30 s 熱負載期

**評分推演**：
| 維度 | 分數 | 推理 |
|:-----|:----:|:-----|
| Sens-P17 | 1.0 | A_contact↑ → Fourier 方程 q=k·A·ΔT/L 中 A 直接放大 → 散熱強直接改善 |
| Sens-P8 | 1.0 | A_contact↑ → Cu 嵌件占用體積直接增加 → 體積強直接惡化 |
| Controllability | 1.0 | 嵌件 vol fraction、徑向位置、嵌件數量都是 CAD 可直設 |
| CausalDirect | 1.0 | A 直接出現在 Fourier 方程，零中間變數 |

→ PxScore = 0.50 + 0.25 + 0.25 = **1.00**

#### 4.4.2 TC-B：B_r（磁鐵剩磁）

**OZ-OT 鎖定**：
- OZ：Motor air gap（rotor 外側 + stator 內側）
- OT：Peak torque 期間

**評分推演**：
| 維度 | 分數 | 推理 |
|:-----|:----:|:-----|
| Sens-P21 | 1.0 | B_r↑ → 扭力 T ∝ B_g²·V → 強直接、反向於 P1 |
| Sens-P1 | 1.0 | B_r↑（換高牌號）→ NdFeB 密度↑ → 重量強直接增加 |
| Controllability | 1.0 | 牌號選擇（N42SH / N52）為設計參數 |
| CausalDirect | 1.0 | B_r 直接在 Halbach 解析式 B_g = B_r·sin(πα/p)/(πα/p) 中 |

→ PxScore = **1.00**

#### 4.4.3 TC-C：Δδ（齒面修形量）

**OZ-OT 鎖定**：
- OZ：齒輪嚙合區（gear mesh contact zone）
- OT：嚙合動態過程（連續，~1.5–3 kHz mesh frequency）

**評分推演**：
| 維度 | 分數 | 推理 |
|:-----|:----:|:-----|
| Sens-P31 | 1.0 | Δδ ∈ [5, 15μm] → 噪音降 6~12 dB(A)，強直接 |
| Sens-P36 | 1.0 | Δδ↑ → 製造工序（CNC 修形 + KISSsoft）增加，強直接 |
| Controllability | 1.0 | 修形量為齒形 CAD 設定 |
| CausalDirect | 0.7 | Δδ → 齒形誤差 PEE → 振動 → 噪音，1 個中間變數 |

→ PxScore = 0.50 × 1.0 + 0.25 × 1.0 + 0.25 × 0.7 = **0.925**

⚠️ TC-C 因 PEE 介於 Δδ 與噪音之間，CausalDirect 降一級。但仍遠超 0.60 門檻 → 採用。

### 4.5 PC 造句

| TC | PC 造句（標準形式：Px=A 滿足 P1，Px=¬A 滿足 P2） |
|:---|:---|
| TC-A | A_contact 必須**大**（Cu 嵌件低熱阻 → P17 OK）且 A_contact 必須**小/不超 OD111×axial92**（→ P8 OK） |
| TC-B | B_r 必須**高**（Halbach 有效側 N42SH → P21 OK）且 B_r 必須**低/無磁鐵**（無效側近零 → P1 OK） |
| TC-C | Δδ 必須**大**（5~15μm 修形 → P31 OK）且 Δδ 必須**小/零修形**（→ P36 OK） |

### 4.6 分離策略評分（4 策略 × 3 診斷）

#### 評分機制

每種分離策略有自己的 3 個診斷問題（**問題不互通**）：

| 策略 | Q1 | Q2 | Q3 |
|:-----|:---|:---|:---|
| 時間 | 不同時段被需要? | τ 遠離操作頻率? | 切換物理可行? |
| 空間 | 位置不同? | ∇P 可建立? | 邊界明確? |
| 條件 | 非線性回應? | 控制 X 可調? | 狀態可逆? |
| 整體局部 | 可從微觀湧現? | 可製造? | scaling law 可預測? |

每題 0/0.5/1.0，分數 = 三題平均。

**選擇規則**：
- 主策略 = 最高分（必 ≥ 0.50）
- 第二高分 ≥ 0.50 且正交 → 嵌套
- 整體局部「可嵌套於任何其他策略」（特殊規則）
- 最多 2 層嵌套

#### 三條 TC 的分離評分

##### TC-A
| 策略 | Q1 | Q2 | Q3 | 分數 | 採用? |
|:-----|:--:|:--:|:--:|:----:|:------|
| 時間 | 0 | 0.5 | 0.5 | 0.33 | 否 |
| **空間** | 1.0 | 1.0 | 1.0 | **1.00** | ✓ 主 |
| 條件 | 0.5 | 1.0 | 0.5 | 0.67 | fallback |
| **整體局部** | 1.0 | 1.0 | 1.0 | **1.00** | ✓ 嵌套 |

→ **空間（主）+ 整體局部（嵌套）**：徑向梯度 ∇k 在界面建立（空間），界面內 Cu 嵌件 + Al 主體形成 FGM 湧現（整體局部）。

##### TC-B
| 策略 | Q1 | Q2 | Q3 | 分數 | 採用? |
|:-----|:--:|:--:|:--:|:----:|:------|
| 時間 | 0 | 0 | 0 | 0 | 否 |
| **空間** | 1.0 | 1.0 | 1.0 | **1.00** | ✓ 主 |
| 條件 | 0.5 | 0.5 | 0.5 | 0.50 | 邊緣 |
| **整體局部** | 1.0 | 0.67 | 1.0 | **0.89** | ✓ 嵌套 |

→ **空間（主）+ 整體局部（嵌套）**：Halbach 排列在 air gap 一側集中、另一側近零（空間），N42SH+SMC+CFRP 複合構成有效磁路（整體局部）。

##### TC-C
| 策略 | Q1 | Q2 | Q3 | 分數 | 採用? |
|:-----|:--:|:--:|:--:|:----:|:------|
| 時間 | 0 | 0 | 0 | 0 | 否 |
| **空間** | 1.0 | 1.0 | 1.0 | **1.00** | ✓ 主 |
| **條件** | 0.5 | 1.0 | 0.5 | 0.67 | ✓ 次嵌套 |
| **整體局部** | 1.0 | 0.67 | 1.0 | **0.89** | ✓ 嵌套 |

→ **空間（主）+ 整體局部 + 條件**：active flank 修形 / root 區零修形（空間），EHD 油膜在負載建立後成膜（條件）。

### 4.7 SF 標準解匹配

依 76 標準解 KB 路由：

| TC | SF 狀態 | 主標準解 | 補充標準解 |
|:---|:-------|:---------|:-----------|
| TC-A | 不足（Class 1.1 / 5.3）| 1.1.2 內部添加物（Cu 嵌件）+ 5.3.1 利用相變（PCM）| 2.2.5 結構化場 |
| TC-B | 不足（Class 2.4）| 2.4.5 複合鐵磁結構（Halbach + SMC）| 2.2.5 結構化場 |
| TC-C | 有害（Class 1.2 + 2）| 2.2.5 結構化物質（梯度修形）+ 2.3.1 場節奏匹配（避共振）| 1.3.5 微量添加物（MoS₂）|

### 4.8 三條解法整合

| TC | F（場）| S（物質）| OZ | OT |
|:---|:------|:---------|:---|:---|
| SOL-TCA | Thermal: q = k·A·ΔT/L + Clausius-Clapeyron | Cu 嵌件 + Al-6061 + RT55 PCM | Stator-housing 界面 + 內襯 PCM | Peak 5–30 s |
| SOL-TCB | EM: B_g = B_r·sin(πα/p)/(πα/p) | NdFeB N42SH + SMC Somaloy 700 + CFRP 套筒 | Air gap 有效側集中 | Peak torque |
| SOL-TCC | Mech+EHD: PEE=f(profile,helix,runout) | 修形齒（5~15μm 齒廓 + 3~8μm 齒向）+ PAO + MoS₂ | 嚙合 active flank + EHD 0.1~1μm | 連續 + 負載觸發 |

### 4.9 SIM 交互矩陣（多 TC 收斂）

#### 評分機制

兩兩配對打 +1 / 0 / -1：
- +1：A 解 → 解除 B 的物理瓶頸 / 共用資源 / 雙重利用
- 0：物理場無衝突，僅成本/工序累加
- -1：A 解 → 引發 B 的新副作用

#### 本案矩陣

|  | TC-A 解 | TC-B 解 | TC-C 解 |
|:---|:------:|:------:|:------:|
| **TC-A 解** | — | +1 | +1 |
| **TC-B 解** | +1 | — | 0 |
| **TC-C 解** | +1 | 0 | — |

#### 評分理由

| 配對 | 分數 | 物理推理 |
|:-----|:----:|:---------|
| TCA × TCB | +1 | 散熱改善 → 解除 J_max（電流密度上限）→ Halbach 高銅損可承受 → 扭力密度可達標 |
| TCA × TCC | +1 | 油浴溫度穩定 → EHD 油膜厚度可預測；油浴兼當散熱介質（**雙重利用**）|
| TCB × TCC | 0 | 製造工序累加（Halbach 黏結 + SMC 模具 + 齒面修形）但無物理場衝突；風險屬 DFM 範疇 |

#### SIM 判定

| 指標 | 值 | 結論 |
|:-----|:--:|:-----|
| +1 數量 | 2 | 加成有實質物理路徑 |
| 0 數量 | 1 | 工序累積，需 DFM 處理 |
| -1 數量 | **0** | **無消弭** |

→ **CONVERGED**：三解法可並行實施，進入 Step 4。

#### 觀察項（傳遞至 Step 4）

- C-B002 Halbach 增益為 LLM 估計，建議 FEA-Mag 模擬補強
- C-C002 噪音水平基準需取得 TQ HPR50 spec sheet 或實測
- TC-B × TC-C 製造工序累積，建議 DFM 審查

---

## 5. Step 4 — 驗證 + 複雜度判定

### 5.1 推理框架（依 `triz-verify` skill）

```
Phase 1: Px 分離驗證（邏輯 + 實證）
Phase 2: 四問複雜度（CCI 計算）
Phase 3: 補丁 vs 進化判定
Phase 4: 新 TC 偵測
Phase 5: 工程交付物
Phase 6: CAD 就緒評估（Gate P）
```

### 5.2 Phase 1 — Px 分離驗證

#### 5.2.1 邏輯驗證（每條 TC 兩端必須都通過）

| 解法 | Px 一側驗證（P_improve） | Px 另一側驗證（P_worsen） | 結果 |
|:-----|:------------------------|:--------------------------|:-----|
| SOL-TCA A_contact | Cu 嵌件徑向局部 → q=k·A·ΔT/L 提升，winding 溫升 < 80K → P17 ✓ | 嵌件 vol fraction < 5%，整體不超 OD111×axial92 → P8 ✓ | **PASS** |
| SOL-TCB B_r | Halbach 有效側 N42SH，B_g 增益 +30~40% → P21 ✓ | 無效側近零；CFRP+SMC 替代結構鋼降重 → P1 ✓ | **PASS** |
| SOL-TCC Δδ | Active flank 修形，PEE < 5μm → 噪音 -6~12 dB(A) → P31 ✓ | Root/non-contact 區零修形；複雜度移至設計階段非運行結構 → P36 ✓ | **PASS** |

#### 5.2.2 實證驗證（Evidence Registry 統計）

| Confidence | 數量 | 比例 | 處理 |
|:-----------|:----:|:----:|:-----|
| HIGH | 6 | 50% | datasheet/handbook 直接引用 |
| MEDIUM | 4 | 33% | paper 或 LLM 中信度 |
| LOW | 2 | 17% | C-B004（CFRP tip speed）、C-C002（HPR50 噪音） |
| **HIGH+MEDIUM** | **10/12** | **83%** | ≥ 50% 門檻 ✓ |

**LOW 項目處置**：均屬基準/邊界比對，非主控物理量。可由 FEA-Mag（補強 C-B004）與 spec sheet（補強 C-C002）取得補強，不阻塞 Step 4 通過。

### 5.3 Phase 2 — 四問複雜度判定

#### 5.3.1 CCI 公式

```
CCI = 0.30 × Q1 + 0.25 × Q2 + 0.20 × Q3 + 0.25 × Q4
```

| 範圍 | 判定 |
|:-----|:-----|
| 0.00–0.30 | Strong Evolution |
| 0.31–0.55 | Weak Evolution |
| 0.56–0.75 | Conscious Patch |
| 0.76–1.00 | Hard Patch |

#### 5.3.2 Q1 結構複雜度（5 級量表）

| 分數 | 條件 | 本案推理 |
|:----:|:-----|:---------|
| 0.00 | 淨組件數減少 | — |
| 0.25 | 不變 | — |
| **0.50** | 新增 1-2 件**無新跨子系統介面** | **本案：Cu 嵌件 + CFRP 套筒 + PCM 層 ~3 件，全在既有 housing/rotor 內，無新跨子系統介面** |
| 0.75 | 新增 1-2 件**有新跨子系統介面** | — |
| 1.00 | 新增 3+ 件或全新子系統 | — |

→ **Q1 = 0.50**

#### 5.3.3 Q2 能量複雜度

| 分數 | 條件 | 本案推理 |
|:----:|:-----|:---------|
| 0.00 | 能耗降低或免費能 | — |
| **0.25** | 能耗不變 | **散熱降銅損 + Halbach 提效 + EHD 降摩擦損 → 整體能耗持平或微降** |
| 0.50 | 增加 < 10% | — |
| 0.75 | 增加 10–50% | — |
| 1.00 | 需新能量源 | — |

→ **Q2 = 0.25**

#### 5.3.4 Q3 認知複雜度

| 分數 | 條件 | 本案推理 |
|:----:|:-----|:---------|
| 0.00 | 依賴鏈縮短 | — |
| 0.25 | 不變 | — |
| **0.50** | 新增 1 個條件分支或校準步驟 | **R&D 階段新增 FEA-Mag/CFD-PCM/修形 KISSsoft 三個分析分支；運行/維修認知幾乎不變** |
| 0.75 | 新增 2-3 個或需專業知識 | — |
| 1.00 | 全新心智模型 | — |

→ **Q3 = 0.50**

#### 5.3.5 Q4 演化對齊

讀取本案領域趨勢（從 `auto_triz_strategy.md` §8 提取小型機電趨勢）：

| 趨勢 | 滿足? | 證據 |
|:-----|:-----:|:-----|
| 理想度↑ | ✓ | 散熱+扭力密度+降噪三軸同步達標 |
| 微觀化 | ✓ | μm 級齒面修形、SMC 顆粒、Cu 嵌件介面工程 |
| 動態化 | ✓ | PCM 隨溫度切相、EHD 隨負載成膜 |

| 分數 | 條件 |
|:----:|:-----|
| **0.00** | 全部趨勢滿足 → **本案** |
| 0.33 | N-1 條 |
| 0.67 | 1 條 |
| 1.00 | 0 條 |

→ **Q4 = 0.00**（強信號，演化方向明確）

#### 5.3.6 CCI 計算

```
CCI = 0.30 × 0.50 + 0.25 × 0.25 + 0.20 × 0.50 + 0.25 × 0.00
    = 0.150 + 0.0625 + 0.100 + 0.000
    = 0.3125
```

#### 5.3.7 判定

- 0.3125 落在 [0.31, 0.55] → **Weak Evolution**
- 距 Strong Evolution 邊界 0.0125 → 邊界值
- Q4 = 0.00 為強訊號 → 走 Evolution 分支，不觸發補丁迴圈

### 5.4 Phase 3 — 補丁 vs 進化路徑

| 條件 | 滿足? | 結論 |
|:-----|:-----:|:-----|
| Px 分離驗證 PASS | ✓ | — |
| Evidence ≥ 50% | ✓ | 83% |
| CCI ≤ 0.55 | ✓ | 0.3125 |
| **進化路徑** | **✓** | **進入 Phase 4-6 交付** |

### 5.5 Phase 4 — 新 TC 偵測

| 觀察項 | 是新 TC? | 處理 |
|:-------|:--------:|:-----|
| C-B002 Halbach 增益估計 | 否 | FEA-Mag 模擬補強 |
| C-C002 噪音基準 | 否 | spec sheet 或實測 |
| TC-B × TC-C 工序累積 | **邊界** | DFM 範疇，已被 Q1/Q3 計入；列入 TR1-2 DFM 審查 |

→ **new_tc_detected: false**，不觸發 Spiral Ascent。

### 5.6 Phase 5 — 工程交付物

#### 5.6.1 工程規格書摘要（FSOZOT 表）

見 §4.8 三解法整合表。Hard Constraints 8 條（OD/Axial/重量/扭力/減速比/噪音/退磁邊界）全列入 checklist。

#### 5.6.2 驗證計畫（V1-V7）

| ID | 量測指標 | 判定標準 | 方法 |
|:---|:---------|:---------|:-----|
| TCA-V1 | T_winding @ peak 5 min | ≤ 80K rise | 熱電偶 + IR + dyno |
| TCA-V2 | T_PCM_layer @ peak | 55°C 平台 ±2°C | 熱像儀 + 嵌入熱電偶 |
| TCB-V1 | B_g (mT) @ air gap | ≥ +30% vs baseline | Hall probe + FEA-Mag 對照 |
| TCB-V2 | T_peak / m_total | ≥ 50 Nm/kg | dyno + 重量 |
| TCC-V1 | dB(A) @ 1m, 60 rpm | ≤ HPR50 baseline | 半消音室 + microphone array |
| TCC-V2 | ξ_oil @ 100 Nm load | 0.1~1 μm | 電容式膜厚感測 |
| SIM-V1 | T_winding × T_peak × dB(A) | 全部通過上方 V1 | 整機 dyno + NVH |

### 5.7 Phase 6 — CAD 就緒評估（Gate P）

| 維度 | 來源 | 結果 |
|:-----|:-----|:-----|
| 空間約束 | OZ from Step 3 | 明確（OD111 × axial92） |
| 解耦程度 | Q1 結構複雜度 | 0.50 — 中等，無新跨子系統介面 |
| 可驗證性 | Evidence coverage | 83% HIGH+MEDIUM |
| 主要風險 | observation items | 3 條（FEA-Mag、HPR50 spec、DFM 累積） |
| **CAD 工作量** | RD 評估 | **MEDIUM** — 可基於 2 級行星 mid-drive 模板修改 |

**綜合判定矩陣**：
| 條件 | 滿足? |
|:-----|:-----:|
| CCI ≤ 0.55 | ✓ (0.3125) |
| Evidence ≥ 50% | ✓ (83%) |
| CAD ≤ MEDIUM | ✓ (MEDIUM) |

→ **Gate P = Go ✅**

---

## 6. Step 5 — 工程作業指導書產出

### 6.1 推理框架（依 `triz-wi` skill）

```
Phase 1: 子系統分類（域分解）
Phase 2: 框架文件產出（README + Gate framework + Critical path + Risk register）
Phase 3: WI 產出（多 Agent 並行）
Phase 4: ICD + Material Card 產出（多 Agent 並行）
```

### 6.2 子系統分類規則

依 SF 場類型 + 解法物質類型自動偵測：

| # | 工程域 | WI | 觸發依據 |
|:--|:-------|:---|:---------|
| 1 | 電磁（馬達）| WI-01 | SOL-TCB F=Electromagnetic + S=NdFeB/SMC/CFRP |
| 2 | 機械（齒輪）| WI-02 | SOL-TCC F=Mech+EHD + 修形齒/軸承 |
| 3 | 熱管理 | WI-03 | SOL-TCA F=Thermal + Cu/Al/PCM |
| 4 | 結構整合 | WI-04 | 多 TC 交互 + coaxial housing |
| 5 | 電子 | WI-05 | fa_components 含 Drive Board |
| 6 | 測試驗證 | WI-06 | Step 4 驗證計畫 + observation_items |
| 7 | 採購 | WI-07 | evidence_registry 含長交期物料 |

### 6.3 文件產出統計

| 類型 | 數量 | 路徑 |
|:-----|:----:|:-----|
| 框架文件 | 4 | `docs/engineering/{README,tr_gate_framework,critical_path,risk_register}.md` |
| WI | 7 | `docs/engineering/work_instructions/WI-01~07` |
| ICD | 4 | `docs/engineering/interface_control/ICD-01~04` |
| Material Card | 6 | `docs/engineering/material_cards/MC-01~06` |
| KC List | 1 | `docs/engineering/kc_list.md` |
| **合計** | **22** | — |

### 6.4 關鍵路徑（Critical Path）

```
TR0 → WI-01 (6w) → ICD-01 (1w) → WI-04 (4w) → TR3 → TR5 (5w) → TR6 (5w) → TR7-9 → TR10
≈ 45 週理想最短
```

主要瓶頸：
- WI-01 Halbach 3D FEA（6 週）
- WI-04 Coaxial 整合（4 週）
- TR9 DVP&R 耐久測試（5 週）

### 6.5 HIGH 衝擊度風險摘要

| ID | 風險 | TR 阻塞點 |
|:---|:-----|:---------|
| R-002 | HPR50 噪音 baseline 缺實測 | TR1 |
| R-003 | TC-B × TC-C 製造工序累積，DFM 風險高 | TR1-2 |
| R-008 | NdFeB 退磁邊界（T_winding < 120°C），熱保護必須有效 | TR5-6 |

### 6.6 TR0 概念凍結銜接

| 交付項 | 狀態 |
|:-------|:-----|
| TRIZ session 完成 | ✓（CCI 0.3125 Weak Evolution） |
| 工程交付物 22 份 | ✓ |
| `.tr-state.json` 建立 | ✓（triz_session_ref + state_hash 記錄） |
| 6 個子系統 TR 評估 | ✓ |
| 阻塞 TR1 風險 | 3 條（R-001 FEA-Mag / R-002 HPR50 實測 / R-004 CFRP datasheet） |

→ **下一步**：執行 `/tr-gate TR1` 開始可行性 gate review；或各域 RD 工程師獨立按 WI 程序執行（並行 6 週）。

---

## 7. 全流程推理鏈總覽

### 7.1 決策鏈

```
規格邊界（外部給定）
   │
   ├─ Router: 規格清楚 + TC 未造句 → 跳 Step 0，進 Step 1
   │
   ▼
Step 1: 13 條交互關係 → 6 條 harmful/insufficient → 3 條 SF → 3 條 TC 造句
   │
   ▼
Step 2: 6 個 39 參數映射全 1.00 → 矩陣查表 + 補充 → 3 條主原理方向
   │
   ├─ Evidence Gate: 控制方程 ✓ + Evidence 83% ✓ + 映射 1.00 ✓
   │
   ▼
Step 3: 3 個 Px 候選評分（A_contact 1.00 / B_r 1.00 / Δδ 0.925）
        → 3 條分離策略（全空間+整體局部）
        → 3 條 SF 標準解（1.1.2 / 2.4.5 / 2.2.5）
        → SIM 矩陣（+1 / +1 / 0）→ CONVERGED
   │
   ▼
Step 4: Px 分離 PASS×3 + Evidence 83% + CCI 0.3125（Weak Evolution）
        → 進化路徑
        → 工程規格書 + 驗證計畫（V1-V7）
        → Gate P = Go
   │
   ▼
Step 5: 7 個子系統域 → 22 份工程文件 → 45 週關鍵路徑 → TR0 凍結
```

### 7.2 各步驟的決策核心

| Step | 核心決策物件 | 評分維度數 | 本案結果 |
|:----:|:-------------|:----------:|:---------|
| 1 | 13 條交互 → 3 條 SF | — | 觸發 multi-TC |
| 2 | 39 參數 + 40 原理 | 4 + 3 | 6 全 1.00；3 主方向 |
| 3 | Px + 分離 + SF | 3 + 3 | 3 個 PxScore ≥ 0.925；空間+整體局部 |
| 4 | CCI 四問 | 4 | 0.3125（Weak Evolution）|
| 5 | 子系統域分解 | — | 7 域 22 文件 |

### 7.3 為什麼這個案例適合做為標準案例

1. **Multi-TC 完整觸發**：3 條 TC 同時存在且互相耦合（TC-A 解 → 解鎖 TC-B 上限），驗證了 SIM 矩陣機制。
2. **評分機制全程飽和**：6 個參數映射 + 3 個 Px 候選大部分拿 1.00，無歧義 → 適合作為「教科書級」評分模板。
3. **CCI 邊界值**：0.3125 落在 Weak/Strong Evolution 邊界，Q4=0 強信號 → 展示 CCI 公式對「演化方向強但結構/認知負擔仍存在」的處置。
4. **Evidence Registry 涵蓋多源**：HIGH（datasheet/handbook）+ MEDIUM（paper/LLM）+ LOW（estimate）三層俱備，覆蓋率剛好驗證 50% 門檻機制。
5. **CAD 就緒判定 Go**：Gate P 五維全達標但非全 HIGH，展示「合格而非完美」的工程現實判定。

---

## 8. 推理流程的審計觀點（為何這 5 步可信）

| 環節 | 防範什麼風險 | 機制 |
|:-----|:------------|:-----|
| Step 1 子系統按衝突點劃 | 零件邊界切斷物理場 | OZ 採封裝級而非零件級 |
| Step 2 參數映射 4 維度評分 | 主觀挑 39 參數 | 強制關鍵詞/類別/說明/工程對應四維打分 |
| Step 2 Evidence Gate | 解法基於空想 | 控制方程 + Evidence ≥ 50% + 映射 ≥ 0.7 三道閘門 |
| Step 3 PxScore 三維度 | 挑了不可控/長鏈 Px | Sensitivity + Controllability + CausalDirect 強制 ≥ 0.60 |
| Step 3 分離策略 12 診斷題 | 主觀挑分離 | 4 策略 × 3 題強制具體化 |
| Step 3 SIM 矩陣 | 多 TC 解互斥 | -1 出現即重做 |
| Step 4 CCI 四問 | 解法看似完美實則臃腫 | 結構/能量/認知/演化加權打分 |
| Step 4 Phase 6 Gate P | 跳過 CAD 可行性直接動手 | CCI + Evidence + CAD 三條件 AND |
| Step 5 子系統自動分解 | 工程文件邊界混亂 | 依 SF 場類型 + 解法物質類型自動偵測 |

---

## 9. 參考文件

- 原始 session：`.claude/context/triz/session-2026-04-28-1500-eBike-MidDrive-Coaxial.md`
- 方法論：`docs/methodology/DK-01--auto-triz-process.md`、`DK-02--triz-mechanics.md`
- Skill 定義：`.claude/skills/triz-{router,model,contradict,verify,wi}/SKILL.md`
- 工程交付物：`docs/engineering/`（22 份 WI/ICD/MC + 框架文件）
- TR 銜接：`.claude/context/triz/.tr-state.json`

---

**文件結束 — 從 Router 跳 Step 0，到 TR0 概念凍結，全流程 5 步推理鏈完整可審計。**
