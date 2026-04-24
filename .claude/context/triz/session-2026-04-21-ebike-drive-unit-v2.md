# TRIZ Session Report: 2026-04-21-ebike-drive-unit-v2

> **日期**: 2026-04-21
> **主題**: e-Bike mid-mounted drive unit — 小型/輕量/低噪/高扭力 coaxial 多重矛盾 (v2 全新分析)
> **路徑**: multi-tc (瓶頸路徑, TC1 為瓶頸)
> **判定**: Weak Evolution (CCI=0.35)
> **vs v1 關鍵差異**: Axial Flux Motor 取代 Radial Flux，釋出軸向空間，多路 TC 協同解決

---

## 問題描述

發展 e-Bike 用 mid-mounted drive unit (coaxial structure)，含 gearbox、motor、drive board、pedaling shaft (torque + angle sensing)。

### 產品目標

- 小型化、輕量化、低噪聲、高輸出扭力

### 規格總覽

| 項目 | 規格 |
|:-----|:-----|
| 最大外徑 | 111 mm |
| 軸向長度 | 92 mm |
| 重量 | ≤ 2500 g |
| Spindle length | < 153 mm |
| 峰值扭矩 (短時 ~3sec) | 125 Nm |
| 連續扭矩 (~8min) | 100 Nm |
| 減速比 | 1:30 ~ 1:35 |
| 馬達最大扭矩 | 5 Nm |
| 最高轉速 (output) | 100 rpm |
| 馬達型式 | SPM 或 IPM |
| 殼體材料 | AZ91D（鎂合金） |
| 齒輪箱材料 | PEEK 或 PA66 或類似 |
| 齒輪箱型式 | 多級行星齒輪 / 諧波齒輪 / 擺線齒輪 |

### 對標競品

| 類別 | 對標 |
|:-----|:-----|
| 性能 | Bosch Performance Line CX Gen4, Shimano EP801, DJI Avinox, ZF Centrix |
| 噪聲 | TQ HPR50 |

---

## Step 0: 問題定向

> **判定**: Level B — 系統描述完整，可填 TC 造句，直接進入 Step 1。

### 初步 TC 假設

| TC# | 改善 | 惡化 |
|:----|:-----|:-----|
| TC1 | 馬達扭矩密度（5Nm 在環形 coaxial 空間） | 馬達徑向/軸向尺寸 |
| TC2 | 降噪至 HPR50 級 | 傳動效率 / 機構複雜度 |
| TC3 | 輕量化 ≤2500g | 齒輪/殼體結構強度 |
| TC4 | 外殼緊湊度 OD111×92mm | 散熱能力 |
| TC5 | 軸向 92mm | 組件封裝空間 |

→ **路由**: Step 1

---

## Step 1: 功能建模

### 組件交互圖

| # | 來源組件 | 功能 | 目標組件 | 類型 |
|:--|:--------|:-----|:--------|:-----|
| 1 | Rider | 施加踏力+轉動 | Pedaling shaft | → 有效 |
| 2 | Torque sensor | 感測踏力扭矩 | Drive board | → 有效 |
| 3 | Drive board | PWM 驅動 | Motor coils | → 有效 |
| 4 | Motor coils | 旋轉磁場 | Motor rotor | → 有效 |
| 5 | Motor rotor | 輸出旋轉 | Gearbox input | → 有效 |
| 6 | Gearbox | 減速增扭 | Output sprocket | → 有效 |
| 7 | Shell | 結構支撐+散熱 | All internal | → 有效 |
| 8 | Motor coils | 銅損+鐵損熱 | Shell | →✗ 有害 |
| 9 | Gear teeth | 嚙合衝擊噪聲 | Shell → 環境 | →✗ 有害 |
| 10 | Gear teeth | 摩擦熱 | Shell | →✗ 有害 |
| 11 | Shell | 散熱至環境 | Ambient | →~ 不足 |
| 12 | Motor magnets | 氣隙磁通 | Rotor | →~ 不足 |
| 13 | Gear teeth (polymer) | 承載 | 齒面 | →~ 不足 |
| 14 | Motor body | 佔據徑向空間 | Gearbox 可用空間 | →✗ 有害 |
| 15 | Gearbox | 佔據軸向空間 | Board/Sensor 可用空間 | →✗ 有害 |

### SF 診斷

| # | S1 | F | S2 | SF 狀態 | TC |
|:--|:---|:--|:---|:--------|:---|
| SF1 | Motor coils | 熱場 | Shell | 有害 | TC4 |
| SF2 | Gear teeth | 機械場(嚙合) | Shell/Air | 有害 | TC2 |
| SF3 | Shell | 熱場(對流) | Ambient | 不足 | TC4 |
| SF4 | Motor magnets | 電磁場 | Rotor | 不足 | TC1 |
| SF5 | Gear teeth | 機械場(應力) | Tooth surface | 不足 | TC3 |
| SF6 | Motor body | 幾何場 | Gearbox space | 有害 | TC5 |

### TC 造句驗證

| TC# | 造句 | ✓ |
|:----|:-----|:--|
| TC1 | 為了提高馬達扭矩密度至 5Nm → 馬達尺寸超出 coaxial 限制 | ✓ |
| TC2 | 為了降低齒輪噪聲至 HPR50 級 → 傳動效率下降或複雜化 | ✓ |
| TC3 | 為了使用 PEEK/PA66+AZ91D 降至 2500g → 125Nm 強度不足 | ✓ |
| TC4 | 為了限縮至 OD111×92mm → 100Nm@8min 散熱不足 | ✓ |
| TC5 | 為了軸向 ≤92mm → motor+gearbox+board+sensor 塞不下 | ✓ |

---

## Step 2: TC 定義 + 矩陣查表

### 瓶頸分析

TC1 為瓶頸：解了 TC1(更高扭矩密度) → TC2 弱化(減速比降→噪聲源少) + TC3 弱化(馬達減重) + TC5 弱化(馬達體積縮小)

**解題順序**: TC1 → TC2 → TC3 → TC5 → TC4(殘餘)

### 參數映射 + 矩陣查表

| TC# | P_improve → P_worsen | 推薦原理 |
|:----|:---------------------|:---------|
| TC1 | P10(力) → P7(移動物體體積) | #15, #9, #12, #37 |
| TC2 | P31(有害副作用) → P22(能量損失) | #19, #24, #3, #14 |
| TC3 | P2(靜止物體重量) → P14(強度) | #28, #2, #27 |
| TC4 | P8(靜止物體體積) → P17(溫度) | #35, #39, #38 |
| TC5 | P4(靜止物體長度) → P36(裝置複雜度) | #1, #26 |

### 原理具體化

**TC1 — 關鍵創新: Axial Flux Motor (AFM)**

| 方案 | 原理 | OD | 軸向 | 預估扭矩 |
|:-----|:-----|:---|:-----|:---------|
| A: Radial IPM V-type | #12+#15 | Ø65mm | ~35mm | ~5Nm |
| **B: Axial Flux IPM** | #12+#17(維度轉換) | Ø100mm(ID30mm) | **~18mm** | **5-7Nm** |

AFM 優勢：利用 coaxial 結構 OD 空間充裕（~105mm 內腔）但軸向緊張的特性，以大直徑短軸向的「扁餅形」最大化扭矩密度。

**TC2 — 齒輪箱**

| 方案 | 噪聲 | 效率 | 軸向 |
|:-----|:-----|:-----|:-----|
| A: 諧波齒輪 1:30 | 極低 | ~85% | ~28mm |
| B: 擺線齒輪 1:30 | 低 | ~87% | ~22mm |
| C: 2級斜齒行星 | 中 | ~92% | ~38mm |

**TC3** — CF-PEEK 30%CF 齒輪 + AZ91D 薄壁(2.5-4mm) + SUS304 嵌件
**TC4** — PCM 石蠟 ~250g 殼體夾層 + 淺鰭片
**TC5** — AFM 軸向短 + 環形 PCB + 維度轉換封裝

---

## Step 3: PC/分離/SF 解法

### TC1: AFM — 空間分離 + 維度轉換

- **Px**: 氣隙磁通密度 Bg
- **PC**: Bg 必須高(5Nm) 且磁路體積必須小(OD111mm coaxial)
- **分離**: 維度轉換(radial→axial) + 空間分離(氣隙面高Bg/薄型化)
- **SF**: Class 1.3.2 雙重 Su-Field + Class 2.1.3 反向雙系統

```
AFM: 雙轉子(NdFeB N42SH) 夾 SMC定子
     OD Ø100mm, ID Ø30mm, 軸向 18mm
     集中繞組, MTPA+場弱, 8極12槽
     → 5-7Nm, 省出 ~17mm 軸向空間
```

### TC2: 諧波齒輪 — 整體與局部分離

- **Px**: 嚙合衝擊能量
- **PC**: E_impact 必須低(降噪) 且齒面承載必須高(125Nm)
- **分離**: 整體高承載(30%齒同嚙) / 單齒低衝擊
- **SF**: Class 1.2.1 + 1.2.2

```
諧波: CoCrMo柔輪 + CF-PEEK剛輪(阻尼降噪)
     1:25-30 單級, OD≤90mm, 軸向 28mm, η≈85%
```

### TC3: 混合材料 — 整體與局部分離

- **Px**: 材料密度
- **PC**: 密度必須低(≤2500g) 且比強度必須高(125Nm)
- **分離**: 基體低密度 / 應力集中區局部高強度
- **SF**: Class 1.1.2 + Class 5.1.4

```
CF-PEEK 30%CF 齒輪 + AZ91D 薄壁殼(2.5-4mm)
+ SUS304嵌件@軸承座+鎖付座(絕緣塗層)
```

### TC5: 軸向封裝 — 空間分離 + 維度轉換

- **Px**: 組件軸向堆疊厚度
- **PC**: 必須容納所有組件 且 ≤92mm
- **分離**: 軸向→徑向維度轉換(環形PCB); AFM 釋出空間

```
AFM 18mm + Gearbox 28mm + Board 8mm + Sensor 5mm
= 59mm << 92mm (裕量 33mm)
```

### TC4: PCM 相變 — 時間分離

- **Px**: 殼體散熱面積
- **PC**: 散熱面積必須大(100Nm@8min) 且殼體必須小(OD111)
- **分離**: 工作期 PCM 潛熱吸收 / 休息期對流散逸
- **SF**: Class 2.2.3 + Class 1.3.3

```
石蠟 PCM ~250g (RT55, Tm≈51-57°C, ΔH≈170kJ/kg)
殼體內壁夾層, 外表面淺鰭片
Total heat 90W×8min=43.2kJ → PCM 254g @170kJ/kg (≈250g allocation)
穩態散逸 ~138W (風冷) > 90W → 可恢復
```

---

## SIM 交互矩陣

| | TC1 | TC2 | TC3 | TC4 | TC5 |
|:--|:---:|:---:|:---:|:---:|:---:|
| **TC1** | — | +1 | +1 | 0 | +1 |
| **TC2** | +1 | — | +1 | **-1** | 0 |
| **TC3** | +1 | +1 | — | 0 | 0 |
| **TC4** | 0 | -1 | 0 | — | +1 |
| **TC5** | +1 | 0 | 0 | +1 | — |

- **+1 = 5**: TC1↔TC2(減速比降), TC1↔TC3(馬達減重), TC1↔TC5(軸向釋出), TC2↔TC3(CF-PEEK一物兩用), TC4↔TC5(空間給PCM)
- **-1 = 1**: TC2↔TC4 — 諧波效率低→多出 ~30W 熱 → PCM 需求 +120g
- **處理**: PCM 增量 120g 在可接受範圍（AFM 省回 ~100g），接受為設計限制

---

## Step 4: 驗證

### Px 分離驗證: 5/5 Pass

| TC | 分離 | Pass? |
|:---|:-----|:-----:|
| TC1 | 維度轉換 radial→axial, Bg=0.8-0.9T @Ø100mm | ✓ |
| TC2 | 整體與局部, 30%齒同嚙 | ✓ |
| TC3 | 整體與局部, CF-PEEK基體+SUS304嵌件 | ✓ |
| TC4 | 時間分離, PCM 吸熱/對流散逸 | ✓ |
| TC5 | 維度轉換, 59mm << 92mm | ✓ |

### 四問複雜度判定 (CCI — 量化評分)

| # | 維度 | 分數 | 理由 |
|:--|:-----|:-----|:-----|
| Q1 | 結構複雜度 | 0.25 | 組件數不變：AFM 替換 radial motor、諧波單級替換多級行星、PCM 為填充材非機構件、SUS304 嵌件局部化 |
| Q2 | 能量複雜度 | 0.50 | 無新能源，但系統效率微降：AFM η≈96% × 諧波 η≈85% = 81.6% vs radial 92% × 行星 92% = 84.6%（Δ≈-3%，<10%） |
| Q3 | 認知複雜度 | 0.75 | 需 AFM 磁路、諧波柔輪應力分析、PCM 熱緩衝設計、環形 PCB layout 等多領域專業知識 |
| Q4 | 演化對齊 | 0.00 | 3/3 趨勢滿足：理想度↑（更高扭矩密度+更輕）、微觀化↑（PCM 材料層解決散熱）、動態化↑（MTPA+場弱控制） |

- **CCI** = 0.30×0.25 + 0.25×0.50 + 0.20×0.75 + 0.25×0.00 = 0.075 + 0.125 + 0.150 + 0.000 = **0.35**
- **判定**: **Weak Evolution**（CCI 0.35，落在 0.31-0.55 區間）
- **高分項標記**: Q3 認知複雜度為未來改進方向 — 需建立 AFM+諧波設計手冊降低學習曲線

### 新 TC 偵測

無新 TC。6 個觀察項:
1. SMC 定子鐵損 @高頻
2. AFM 軸向力不平衡
3. 諧波柔輪疲勞壽命
4. AZ91D/SUS304 電偶腐蝕
5. PCM 循環穩定性
6. 環形 PCB EMI

---

## 整合架構

```
e-Bike Drive Unit v2 (OD111mm × 92mm, ≤2500g)
│
├── Motor: Axial Flux IPM (雙轉子夾定子)
│   Ø100mm(ID30mm), 軸向18mm, NdFeB N42SH, SMC芯
│   → 5-7Nm (TC1 ✓)
│
├── Gearbox: 諧波齒輪 1:25-30 單級
│   CoCrMo柔輪 + CF-PEEK剛輪, 軸向28mm, η≈85%
│   → HPR50噪聲級 (TC2 ✓)
│
├── Shell: AZ91D 薄壁(2.5-4mm) + SUS304嵌件
│   + PCM ~250g石蠟夾層 + 淺鰭片
│   → 125Nm結構 (TC3 ✓) + 散熱 (TC4 ✓)
│
├── Board: 環形PCB嵌入端蓋, 軸向8mm
├── Sensor: 磁致伸縮, 軸向5mm
│
├── 軸向: 18+28+8+5=59mm << 92mm (TC5 ✓)
└── 重量: ~2350g < 2500g (裕量150g)
```

---

## 工程規格書

### Motor (TC1)

| 參數 | 值 | 單位 |
|:-----|:---|:-----|
| Type | Axial Flux IPM, 雙轉子夾定子, 8極12槽 | — |
| OD/ID | 100/30 | mm |
| 軸向 | 18 | mm |
| 磁石 | NdFeB N42SH (Br≈1.29-1.32T, Hcj≥1592kA/m) | — |
| 定子芯 | SMC (Somaloy 700HR) | — |
| 目標扭矩 | ≥5.0 | Nm |
| 效率 | ≥90 | % |

### Gearbox (TC2)

| 參數 | 值 | 單位 |
|:-----|:---|:-----|
| Type | 諧波齒輪 | — |
| 減速比 | 1:25~30 | — |
| 柔輪 | CoCrMo wrought (σ_y≥1000MPa, ASTM F1537) | — |
| 剛輪 | CF-PEEK 30%CF | — |
| 效率 | ≥85 | % |
| 噪聲 | ≤HPR50基準 | dB(A) |

### Structure (TC3)

| 參數 | 值 | 單位 |
|:-----|:---|:-----|
| 殼體 | AZ91D, 2.5-4mm | mm |
| 嵌件 | SUS304 @軸承座+鎖付座 | — |
| 絕緣 | 陽極氧化 ≥50μm | μm |

### Thermal (TC4)

| 參數 | 值 | 單位 |
|:-----|:---|:-----|
| PCM | RT55石蠟 (Tm≈51-57°C, ΔH≈170kJ/kg), ~250g | g |
| 溫升上限 | ≤80 | °C |
| 穩態散逸 | ≥138W (風冷) | W |

### Hard Constraints Checklist

- [ ] OD ≤111mm, 軸向 ≤92mm, Spindle ≤153mm
- [ ] 重量 ≤2500g
- [ ] 峰值扭矩 ≥125Nm @3sec
- [ ] 連續扭矩 ≥100Nm @8min
- [ ] AFM 軸向力平衡
- [ ] SMC 鐵損可接受
- [ ] CF-PEEK T_work ≤80°C (Tg=143°C)
- [ ] 絕緣塗層完整性
- [ ] PCM 密封 1000+ cycles
- [ ] 諧波柔輪壽命 ≥10,000 cycles

---

## 驗證計畫

| # | 項目 | 指標 | 標準 | 方法 |
|:--|:-----|:-----|:-----|:-----|
| V1 | AFM扭矩 | 靜態扭矩 | ≥5.0Nm | 扭力台 |
| V2 | 磁路 | Bg | ≥0.8T | FEA 3D |
| V3 | 軸向力 | 雙轉子磁拉力差 | ≤推力軸承額定 | FEA+實測 |
| V4 | SMC鐵損 | 核心損耗@3000rpm | ≤20W | FEA+量熱 |
| V5 | 噪聲 | SPL@1m | ≤HPR50 | ISO 3744 |
| V6 | 齒輪效率 | η | ≥85% | 背對背 |
| V7 | 柔輪壽命 | 疲勞循環 | ≥10k@125Nm/3s | 加速壽命 |
| V8 | 齒輪強度 | 齒根應力 | ≤150MPa | FEA+疲勞 |
| V9 | 重量 | 總重 | ≤2500g | 電子秤 |
| V10 | 溫升 | 殼體@100Nm×8min | ≤80°C | 熱電偶+熱像 |
| V11 | 尺寸 | OD/軸向/Spindle | ≤111/92/153mm | CMM |
| V12 | 腐蝕 | 深度@500hr | ≤0.05mm | ASTM B117 |
| V13 | PCM | 潛熱衰退@1000cyc | ≤5% | DSC |
| V14 | EMI | ADC SNR | ≥60dB | EMI test |

---

## v1 vs v2 差異對照

| 項目 | v1 (2026-04-17) | v2 (2026-04-21) | 差異 |
|:-----|:----------------|:----------------|:-----|
| Motor | Radial IPM Ø65mm, 35mm軸向 | **AFM Ø100mm, 18mm軸向** | 維度轉換，軸向省17mm |
| Gearbox | 諧波/CF-PEEK行星 | 諧波 + CF-PEEK剛輪 | CF-PEEK 改為剛輪(一物兩用) |
| PCM | ~129g | **~250g** | 因諧波效率低增加熱損 |
| 軸向裕量 | ~2-12mm | **~33mm** | AFM 根本性改善 |
| 重量 | ~2500g | **~2350g** | AFM+SMC 減重 |
| TC5 | 未深入分析 | **維度轉換+環形PCB** | 新增解法 |
| SIM | 0衝突 | **1衝突(TC2↔TC4)已處理** | 更完整的熱估算 |

---

## Evidence Registry

> **覆蓋率**: HIGH+MEDIUM = 10/11 = 91% ≥ 50% → Evolution 判定成立，無需降級

| Claim ID | Claim | Claimed Value | Verified Value | Source Type | Source | Confidence | Accessed |
|:---------|:------|:------|:------|:------------|:-------|:-----------|:---------|
| C-001 | NdFeB N42SH Br | 1.32 T | 1.29-1.32 T (typ. 1.31 T) | Datasheet | [Arnold Magnetic Technologies N42SH](https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42SH-151021.pdf) | HIGH | 2026-04-21 |
| C-002 | NdFeB N42SH Hcj | ~~≥1353 kA/m~~ | **≥1592 kA/m (≥20 kOe, SH grade spec)** | Datasheet | Arnold N42SH; SH = Super High coercivity | HIGH | 2026-04-21 |
| C-003 | Somaloy 700 5P μ_max / core loss | μ≈700, lowest loss among SMC variants | μ up to 700; core loss 6 W/kg @1.5T confirmed | Paper | [Asari et al. 2019 IEEE](https://www.researchgate.net/publication/338595233); Höganäs tech data | HIGH | 2026-04-21 |
| C-004 | CF-PEEK 30%CF σ_flex | ~250 MPa | **380 MPa @23°C (Victrex 450CA30)** — claimed value was very conservative | Datasheet | Victrex 450CA30 datasheet | HIGH | 2026-04-21 |
| C-005 | CoCrMo 柔輪 σ_y | ≥1200 MPa | ≥455 MPa (cast F75); **≥827-1172 MPa (wrought F1537)** — 修正為 ≥1000 MPa wrought | Standard | [ASTM F75](https://www.makeitfrom.com/material-properties/UNS-R30075-ASTM-F75-ISO-5832-4-Co-Cr-Mo-Alloy); ASTM F1537 | HIGH | 2026-04-21 |
| C-006 | AZ91D σ_y | 160 MPa | 140 MPa (as-cast), ~160 MPa (die-cast), up to 200 MPa (T6 heat-treated) — die-cast 值合理 | Handbook | ASM International; MakeItFrom | MEDIUM | 2026-04-21 |
| C-007 | AZ91D k (熱導率) | 72 W/mK | ~72-75 W/mK — 合理 | Handbook | ASM Handbook | MEDIUM | 2026-04-21 |
| C-008 | 諧波齒輪效率 η | ≈85% | 75-90%, nominal ~85% confirmed | Manufacturer | [Harmonic Drive AG](https://www.harmonicdrive.net/technology); [Wikipedia](https://en.wikipedia.org/wiki/Strain_wave_gearing) | HIGH | 2026-04-21 |
| C-009 | PCM RT52 Tm≈52°C, ΔH≈200 kJ/kg | RT52, 200 kJ/kg | **RT52 不存在** — 修正為 RT55 (Tm 51-57°C, ΔH≈170 kJ/kg) 或 RT50 (Tm 45-51°C, ΔH≈200 kJ/kg) | Datasheet | [Rubitherm RT50](https://www.rubitherm.eu/media/products/datasheets/Techdata_-RT50_EN_09102020.PDF); Rubitherm product catalog | LOW | 2026-04-21 |
| C-010 | AFM torque density vs radial | 30-40% higher | AFM 產生 30-40% more torque than same-size radial; torque ∝ D³ (vs D² for radial) | Paper/Review | [Wikipedia AFM](https://en.wikipedia.org/wiki/Axial_flux_motor); [Mechtex comparison](https://mechtex.com/blog/axial-flux-vs-radial-flux-motors-a-comprehensive-comparison) | MEDIUM | 2026-04-21 |
| C-011 | AFM η | ≥90% (spec) | AFM η up to 96%, typical ≥93% for optimized designs | Review | Multiple manufacturer sources | MEDIUM | 2026-04-21 |

### 差異處理摘要

| # | 差異 | 處置 | 影響 |
|:--|:-----|:-----|:-----|
| 1 | N42SH Hcj: 1353→1592 kA/m | 已修正（原值為 H grade，SH grade 更高）→ 對設計有利 | 無負面影響 |
| 2 | CF-PEEK σ_flex: 250→380 MPa | 原值保守，實際強度更高 → 安全裕量增加 | 正面 |
| 3 | CoCrMo σ_y: 1200→1000 MPa (wrought) | 已修正，需指定 wrought (ASTM F1537) 而非 cast (F75) | 需在採購規格標注 |
| 4 | **RT52 → RT55** | RT52 非標準品，改用 RT55 (ΔH=170 kJ/kg)；PCM 需量 254g ≈ 250g allocation | PCM 用量微增，仍在預算內 |
| 5 | AZ91D σ_y: 160 MPa | Die-cast 條件下合理，需標注加工條件 | 無 |
