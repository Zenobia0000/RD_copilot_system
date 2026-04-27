# TRIZ 多解併行採納策略

**一句話定位**：當 TRIZ 對同一問題產出多條矛盾解法時，如何判斷「合併採納」、「擇一篩選」、還是「分層 drill-down 組合」——提供結構化的決策框架與 Copilot 落地路徑。

> **v1.1 (2026-04-08)**：依 `docs/e2e/TRIZ_Layered_DrillDown_Optimization.md` 補上「跨層次 drill-down」維度。新增 §2 M6 情境、§5 跨層案例、§6 對應的 anti-pattern。原 M1–M5 保留為**同層內**多解合併策略；M6 處理**跨層次**（L1 TC / L2 PC / L3 SF）的 drill-down 組合。

---

## §1 為什麼一個問題會產出多個解？

TRIZ 的多解現象不是方法論的缺陷，而是**刻意設計**，且分為兩個維度：

### 1.1 同層內多解（原 M1–M5 處理）

1. **矛盾矩陣每格推薦 2–4 個發明原理**：這些原理從不同物理機制切入同一矛盾，彼此不必然互斥。
2. **物理矛盾可同時適用多個分離原則**（時間/空間/條件/整體局部），各自在不同維度消解同一矛盾。
3. **76 標準解覆蓋不同 Su-Field 改造策略**：補充場、引入中介物、轉換到超系統——可能疊加使用。

### 1.2 跨層次多解（v1.1 新增 M6 處理）

同一個矛盾在 TRIZ 經典理論中還可被三個不同層次同時表述：

| 層 | 角色 | 工具 |
|---|---|---|
| **L1 — TC** | 現象層（表象 trade-off） | 39 參數 + 矛盾矩陣 + 40 原理 |
| **L2 — PC** | 本質層（單一物理參數的兩難） | 4 大分離原則 |
| **L3 — SF** | 結構層（功能鏈完整性） | 76 標準解 |

L1 與 L2 是 **drill-down 上下層**（L1 不夠深 → 深挖為 L2，由 ARIZ 精神的 deepen_link 連結）；L3 是**平行旁路**（結構診斷，與 L1/L2 互補）。完整論述見 `TRIZ_Layered_DrillDown_Optimization.md`。

> **核心觀點**：多解不只是「選一個最好的」問題，更不只是「能否疊加」的問題。在三個層次同時看，多解是「能否組成完整的 drill-down 診斷報告」的設計機會。

---

## §2 六種情境判斷矩陣

> **v1.1 注意**：M1–M5 處理「同層內」多解；**M6 處理「跨層次」drill-down 組合**，是 v1.1 新增的維度。

| # | 情境 | 策略 | 判斷準則 | 工程範例 |
|---|------|------|---------|---------|
| **M1** | 多解作用於不同維度 | 合併採納 | 解法分別操作時間、空間、條件等獨立維度，無物理衝突 | 時間分離（爬坡 vs 巡航模式切換）+ 空間分離（承力區剛性 / 減振區柔性）同時用於 e-bike 車架 |
| **M2** | 多解互相強化 | 合併採納 | 解法 A 的輸出是解法 B 的輸入，或兩者形成正回饋迴圈 | #23 回饋控制 + #15 動態化 → 自適應懸吊系統：感測器回饋驅動動態阻尼調整 |
| **M3** | 多解針對同一矛盾的不同子系統 | 各自採納到對應子系統 | 矛盾在多個子系統中有不同表現形式，各子系統適用不同原理 | 電機子系統用 #28 機械系統替代（磁力傳動），傳動子系統用 #5 合併（齒輪整合） |
| **M4** | 多解互斥（物理上不相容） | 必須擇一 → MUST/WANT 篩選 | 解法在同一物理空間/時間/資源上互斥，無法共存 | 材料 A（鋁合金輕量）vs 材料 B（鋼高強度）用於同一結構件，無法同時為兩者 |
| **M5** | 多解都可行但資源有限 | 保留最高 Evidence 等級的路線 | 解法均可行但開發/驗證資源不足以同時推進 | 三條 Concept Route 都通過 MUST，但只有預算做兩條的原型 → 依 E0-E4 證據分級排序 |
| **M6** ✨ (v1.1) | **跨層次 drill-down 組合** | **分層採納**（不是合併）。建立 `LayeredTrizSolution`，Phase B 對同 LTS 內跨層 SKIP 互斥檢查 | 同一矛盾的解法分屬 L1 (TC)、L2 (PC)、L3 (SF) 不同層次。L1 是表象解、L2 是 ARIZ 深挖的根因解、L3 是平行的結構旁證。它們不是 M1–M5 任一情境，是**上下層級** | 馬達散熱：L1 (TC #19+#36 脈衝冷卻) → L2 (PC time 分離：雙模態功率管理) → L3 (SF 補 S3 熱管中介物)。三層各自在不同深度解決同一問題，組合採納為 drill-down 路線 |

### §2.1 M6 與 M1–M5 的關係

```
同一矛盾的多解
        │
        ▼
是否屬於不同 TRIZ 層次（TC / PC / SF）？
    │                              │
   是                              否
    │                              │
    ▼                              ▼
┌─────────┐              ┌──────────────────┐
│  M6     │              │ 走 M1–M5 流程    │
│ 分層    │              │ （同層內合併或   │
│ drill-  │              │   擇一）         │
│ down    │              └──────────────────┘
└─────────┘
    │
    └─ M6 的每一層內部仍可套 M1–M5
       例如 L1 內部的 4 條 TC 原理仍可用 M1 合併為 composite
```

**重要規則**：
- M6 與 M1–M5 **可組合**：先用 M6 把跨層解法分到對應層，再在每層內部用 M1–M5 處理同層多解。
- M6 不需要做 M4 互斥檢查：drill-down 的不同層解本來就操作在不同抽象層級，物理上不衝突。
- M6 的合法性由 `solve_triz_layered` orchestrator 與 `LayeredTrizSolution` schema 保證（見 `Forward_TRIZ_Solver_Architecture.md` §6.2 / §6.7）。

---

## §3 判斷流程

```
TRIZ 產出 N 條解法
        │
        ▼
┌─────────────────────────────────────────┐
│  Step 0: 跨層 vs 同層判斷 (v1.1 新增)    │
│  解法是否分屬 L1 (TC) / L2 (PC) /        │
│  L3 (SF) 不同層次？                      │
└───────────┬─────────────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
  跨層分布         同層分布
    │               │
    ▼               ▼
┌──────────┐  ┌─────────────────────────────────────┐
│   M6     │  │  Step A: 物理相容性檢查              │
│ 分層     │  │  各解法是否在同一物理維度上衝突？     │
│ drill-   │  └───────────┬─────────────────────────┘
│ down     │              │
│ 組合     │      ┌───────┴───────┐
│          │      ▼               ▼
│ (每層    │    衝突            不衝突
│  內部仍  │      │               │
│  可套    │      ▼               ▼
│  M1-M5)  │  ┌────────┐    ┌─────────────────────────────┐
└──────────┘  │  M4    │    │  Step B: 交互作用分析         │
              │  互斥  │    │  解法之間是否產生增益效應？    │
              │  擇一  │    └──────────┬──────────────────┘
              └────────┘               │
                               ┌───────┴───────┐
                               ▼               ▼
                            有增益           無增益
                               │               │
                               ▼               ▼
                         ┌──────────┐   ┌─────────────────────────┐
                         │  M2      │   │  Step C: 作用維度分析     │
                         │  互相強化│   │  各解法作用於哪個維度/     │
                         │  合併採納│   │  哪個子系統？              │
                         └──────────┘   └──────────┬──────────────┘
                                                   │
                                           ┌───────┴───────┐
                                           ▼               ▼
                                      不同維度/         同維度/
                                      不同子系統         同子系統
                                           │               │
                                           ▼               ▼
                                   ┌──────────────┐  ┌──────────┐
                                   │  M1 / M3     │  │  M5      │
                                   │  合併或分配   │  │  資源有限 │
                                   │  到各子系統   │  │  擇優保留 │
                                   └──────────────┘  └──────────┘
```

> **Step 0 的判定**：實作上由 `solve_triz_layered` orchestrator 自動完成 — 它本來就把同一矛盾的解法依層分到 L1/L2/L3，此處的「跨層分布」即 LTS 同時擁有兩層以上有效解。RD 只需在決策中心採納 LTS 推薦組合，Step 0 對 RD 是隱形的。

---

## §4 與 E2E 流程的整合點

### 4.1 在 X2（TRIZ Solver）後新增判斷節點

```
X2: TRIZ 產出 N 條候選解法
    │
    ▼
X2-X: 多解採納判斷 ← 本文件定義的流程
    │
    ├── 可合併 → 合併為「複合 Concept Route」
    │             標記: composite = true
    │             記錄: 組合理由 + 各解法的作用維度
    │
    ├── 分配到子系統 → 各自成為子系統層級的 Route
    │
    └── 互斥 → 各自成為獨立 Concept Route
    │
    ▼
V1: 每條 Route 進入 Evidence Matrix 驗證
```

### 4.2 Concept Route 資料模型擴展

現有 `Concept Route` 物件（定義於整合流程 §1.3）需擴展以支援複合解與分層解：

```yaml
ConceptRoute:
  id: "CR-{project}-{seq}"
  type: "single | composite | layered"  # v1.1: 新增 layered 類型

  # ─── single（單一解）───
  # 不需 composition 也不需 layered_solution

  # ─── composite（同層多解合併，M1/M2/M3）───
  composition:
    - source_principle: "#23 回饋控制"
      dimension: "控制策略"
      adoption_type: "M2-互相強化"
    - source_principle: "#15 動態化"
      dimension: "機構設計"
      adoption_type: "M2-互相強化"
  composition_rationale: "..."

  # ─── layered（跨層 drill-down，M6，v1.1 新增）───
  layered_solution:
    lts_id: "LTS-EMOTOR-007"          # 對應 LayeredTrizSolution
    adopted_layers: ["L1", "L2", "L3"] # RD 採納的層；可只採部分
    recommended_route: "L2 + L3 組合（突破路線）"
    fallback_route: "L1 單獨（快速路線）"
    layer_details:
      L1:
        type: "TC"
        principles: [19, 36, 3, 35]
        depth_indicator: "trade-off 改良"
      L2:
        type: "PC"
        deepen_link_from: "L1"
        derived_parameter: "瞬時功率 P(t)"
        separation_type: "time"
        depth_indicator: "根因突破"
      L3:
        type: "SF"
        role: "structural_lens"
        standard_solution: "2.2.1"
        depth_indicator: "功能鏈缺陷修補"
    differential_analysis: "..."       # 來自 LayeredTrizSolution
    composition_rationale: "M6 跨層 drill-down：L2 解主矛盾，L1 為 fallback，L3 補結構盲點"

  mechanism: "..."
  interface_contract: "..."
  estimated_bom: "..."
  risk: "..."
  evidence_matrix: "..."
```

**重要區別**：
- `composite` 是**同層內**的多原理融合（用 M1/M2/M3）。
- `layered` 是**跨層次**的 drill-down 組合（用 M6）。
- 一個 `layered` Route 的某層內部仍可是 `composite`（例如 L1 包含 4 條 TC 原理的合併）。

### 4.3 Evidence Matrix 對複合解的驗證要求

複合解的驗證比單一解更嚴格，因為需要額外確認**交互效應**：

| 驗證項目 | 單一解 | 複合解 |
|---------|--------|--------|
| 個別原理可行性 | E2 以上 | E2 以上（每條子解法各自驗證） |
| 子解法間無負面交互 | — | E1 以上（分析或仿真確認無干涉） |
| 組合後的整合效果 | — | E2 以上（仿真或原型驗證組合效果） |
| 系統層級整合 | E3 以上 | E3 以上（含交互效應的系統測試） |

> **Evidence Level 定義**（對齊 `Evidence_Matrix_Risk_Register_Template.md`）：
> - E0: 專家意見 / 直覺
> - E1: 工程計算 / 類比推理
> - E2: 仿真 / 模擬
> - E3: 原型測試
> - E4: 量產驗證

---

## §5 實務案例：e-bike 馬達散熱矛盾

### 問題定義

**技術矛盾**：提高馬達功率密度（改善參數 #21 功率）→ 惡化散熱（惡化參數 #17 溫度）

### TRIZ 矛盾矩陣查表結果

改善 #21 vs 惡化 #17 → 推薦原理：**#19 週期性動作, #35 參數變化, #3 局部品質, #36 相變**

### 多解判斷

| 原理 | 具體化 | 作用維度 | 與其他解的關係 |
|------|--------|---------|--------------|
| #19 週期性動作 | 脈衝冷卻：間歇式高速風扇 | 時間 | 與 #36 可在不同溫度區間配合 |
| #35 參數變化 | 溫控可變黏度冷卻液 | 條件 | 與 #3 可在不同空間區域配合 |
| #3 局部品質 | 定子繞線末端局部強化散熱 | 空間 | 與 #35 互補（不同位置不同策略） |
| #36 相變 | 相變材料吸收瞬態熱峰 | 時間（短期） | 與 #19 互補（#36 處理瞬態，#19 處理穩態） |

### 判斷結果

```
#19 + #36 → M2 互相強化（脈衝冷卻處理穩態 + 相變材料處理瞬態熱峰）
#3 + #35  → M1 不同維度（空間局部強化 + 條件響應冷卻液）
四者整合  → M1 不同維度，合併為一條複合 Concept Route
```

### 複合 Concept Route

```yaml
id: "CR-EMOTOR-007"
type: "composite"
composition:
  - source_principle: "#19 週期性動作"
    concrete: "間歇式高速風扇（依溫度觸發）"
    dimension: "時間-穩態"
    adoption_type: "M2"
  - source_principle: "#36 相變"
    concrete: "定子端蓋填充相變材料（熔點 65°C）"
    dimension: "時間-瞬態"
    adoption_type: "M2"
  - source_principle: "#3 局部品質"
    concrete: "繞線末端銅箔強化散熱路徑"
    dimension: "空間"
    adoption_type: "M1"
  - source_principle: "#35 參數變化"
    concrete: "溫控可變黏度冷卻液（高溫時黏度降低加速流動）"
    dimension: "條件"
    adoption_type: "M1"
composition_rationale: >
  四條解法分別作用於時間穩態/時間瞬態/空間/條件四個獨立維度，
  無物理衝突，且 #19+#36 形成穩態-瞬態互補的正回饋關係。
```

---

### §5.x 跨層案例（M6）：e-bike 馬達散熱的 drill-down 組合（v1.1 新增）

§5 上述案例（#19 + #36 + #3 + #35）是**同層內**合併（全部來自 TC 矩陣 cell），對應 M1。下面展示**跨層次**的 drill-down 採納（M6）。

#### 同樣的矛盾，分層分析

**矛盾**：馬達功率密度提升 30% → 定子溫度超過 145°C 絕緣上限

#### L1（TC 現象層）— 必跑

```
查矩陣 (#21 功率, #17 溫度) → [19, 35, 3, 36]
suggestions:
  #19 週期性動作：脈衝冷卻 PWM
  #36 相變：定子端蓋填 PCM
  #3 局部品質：繞線末端銅箔強化
  #35 參數變化：溫控可變黏度冷卻液
depth_indicator: "trade-off 改良"
critic 評估: "皆為折衷修補，無本質突破" → 觸發 L2
```

#### L2（PC 本質層）— 由 L1 critic 觸發 + deepen_link

```
deepen_link:
  from_tc_pair: (#21, #17)
  derived_physical_parameter: "瞬時功率 P(t)"
  contradiction_statement: "P(t) 必須 ≥ P_peak（爬坡）且必須 ≤ P_thermal（散熱上限）"
  separation_type: time   (confidence 0.85)

LLM 套分離原則 (time + #15):
  "雙模態功率管理器：爬坡 10s 允許 P_peak，巡航降回 P_thermal"
depth_indicator: "根因突破"
```

#### L3（SF 結構層）— 必跑平行旁路

```
Su-Field: S1=定子, S2=外殼, F=熱場, state=insufficient
matched: 2.2.1 (引入 S3 中介物), 2.4.1 (強化 F)

旁路建議:
  "主系統缺 S3 中介物導致熱阻瓶頸"
  "建議加入熱管陣列為 S3"

relationship_to_other_layers:
  supports L1 #19: "為脈衝冷卻提供熱容緩衝"
  supports L2 time 分離: "延長峰值功率窗口 +40%"
  standalone: "獨立改善 15%"
```

#### M6 採納決策

```yaml
ConceptRoute:
  id: "CR-EMOTOR-008"
  type: "layered"
  layered_solution:
    lts_id: "LTS-EMOTOR-008"
    adopted_layers: ["L2", "L3"]      # 採納推薦路線
    recommended_route: "L2 + L3 組合（突破路線）"
    fallback_route: "L1 單獨"
    layer_details:
      L2: {type: PC, separation: time, content: "雙模態功率管理 + #15 動態化"}
      L3: {type: SF, content: "S3 = 熱管陣列"}
    differential_analysis:
      L1_vs_L2: "L1 改善 10-15% 瞬時；L2 重新定義功率 envelope，峰值 +30%"
      L2_vs_L3: "強增效，組合峰值窗口 +40%"
      recommended_rationale: "矛盾 severity major + 韌體資源充足"
    composition_rationale: >
      M6 跨層組合：L2 透過時間分離從根因解決矛盾；L3 補上 S3 中介物消除
      結構瓶頸。L1 的 4 條 TC 原理作為 fallback，待後續驗證 L2 韌體可靠度後
      可考慮降級。
```

#### 與舊案例（M1）的差異

| 維度 | §5 舊案例（M1） | §5.x 新案例（M6） |
|---|---|---|
| **解法來源** | 全部來自 TC 矩陣同 cell | 跨 TC / PC / SF 三層 |
| **合併性質** | 同層多原理融合 | 跨層分層採納（drill-down） |
| **採納策略** | composite Concept Route | layered Concept Route |
| **Phase B 行為** | 與其他 Route 比對互斥 | 同 LTS 內跨層 SKIP 互斥 |
| **能否解決根因** | 否，僅優化既有 trade-off | 是，L2 重新定義 envelope |
| **結構盲點** | 未檢查 | L3 主動揭露 |

> **使用建議**：當矛盾 severity 為 minor 且 critic 不觸發 L2 時，繼續用 §5 舊案例的 M1 同層合併即可。當 severity ≥ major 或 L1 顯然不夠深時，新流程會自動把案例升級為 M6 跨層 drill-down。

---

## §6 Anti-Pattern：不應合併的情況

| Anti-Pattern | 描述 | 風險 |
|-------------|------|------|
| **強行合併互斥解** | 將物理上不相容的解法硬塞進同一設計 | 系統複雜度爆炸，任一解法的優勢被抵消 |
| **過度堆疊** | 所有候選原理都合併，不做篩選 | 整合成本超過各解法的邊際收益 |
| **忽略交互驗證** | 合併後未驗證子解法間的交互效應 | 隱藏的負面交互在後期才暴露 |
| **混淆「可合併」與「應合併」** | 物理上可合併但成本/時程不允許 | 資源分散導致每條解法都做不到位 |
| **微調矛盾硬跑 L2 深挖** (v1.1) | severity 為 minor、L1 已足夠的情境仍強制觸發 PC 深挖 | 工程資源浪費、L2 產生不必要的 secondary 矛盾、決策中心被低價值候選淹沒 |
| **把 M6 與 M1–M5 並列比較** (v1.1) | 把跨層 drill-down 解（M6）與同層合併解（M1–M5）放在同一決策層級對比 | 層次混淆。M6 是先做的判斷（Step 0），M1–M5 是 M6 各層內部再做的判斷 |
| **L3 自動降級為 fallback** (v1.1) | 看到 L2 已採納就把 L3 結構診斷直接 skip | 失去結構盲點檢查；L3 角色是 `structural_lens` 旁證，永遠應呈現給 RD |

> **經驗法則**：
> - **同層**合併 2–3 條解法通常是甜蜜點。超過 4 條時，交互驗證的成本通常超過邊際收益。
> - **跨層** drill-down 一次最多 3 層（L1+L2+L3 已是上限）。*(v9: SCAMPER 已移除; v10: Anti-Anchor 退役，跨域去錨定已合併為 L1 內建步驟，不再作為獨立第四層)*
> - severity = `minor` 時：預設只跑 L1 + L3，跳過 L2，避免微調矛盾被過度深挖。

---

## §7 Copilot 自動化建議

未來 Copilot 可在 X2-X 自動輔助判斷：

```yaml
自動化判斷輸入:
  - 各解法的作用維度標籤 (時間/空間/條件/整體局部)
  - 各解法的物理機制描述
  - 已知的 Hard Constraints

自動化判斷輸出:
  - 相容性矩陣 (N×N，每對解法標記: 可合併/互斥/待確認)
  - 推薦的合併分組
  - 需要額外驗證的交互效應清單
  - 建議的 Concept Route 組合方案
```

---

## 參考文件

- `RD_Design_Copilot_整合流程.md` §1.3 核心工件物件、§1.5 AutoTRIZ 混合架構
- `First_Principles_Analysis.md` §1.2 四個不可化約的子問題（S2 矛盾解決）
- `Evidence_Matrix_Risk_Register_Template.md` Evidence Level E0–E4 定義
- `MUST_Rulebook_Template.md` MUST/WANT 篩選規則
- TRIZ Knowledge Base: `04_separation_principles.md`（分離原則）、`03_40_principles.md`（40 原理）
- Jiang et al. (2025) *AutoTRIZ — Automating engineering innovation with TRIZ and large language models*

---

## Changelog

### v1.1（2026-04-09）— parent_contradiction_id 跨層不互斥備註

- 同一 `parent_contradiction_id` 下的子 PC 為 L1→L2 intra-layer drill-down 結果
- Phase B 掃描時不應將同父下的候選視為互斥衝突（`same_contradiction_intra_layer_conflict: skip`）
- 此備註由 `docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md` §9.6 產出
- **實作狀態**：Phase B 完整實作延後至 L3 WBS（`Explore_L3_SF_Parallel_Check_WBS.md` §7）
