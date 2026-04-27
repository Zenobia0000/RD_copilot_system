# Create 頁面 UX 設計規格

> **v9.0 (2026-04-27)**：**Auto-TRIZ v2 整合（ADR-008）**。
> - 新增 **Entry Grading Modal**：專案建立時 AI 自動分級（A/B/C），決定 Explore 流程深度。
> - 新增 **Conditional Stepper**（Level A 五步引導 / Level B 三 Tab / Level C SF-only 快速路徑）。
> - Tab ① Block B 新增 **OZ-OT Panel**：顯示操作區域（OZ）、操作時間（OT）、物理矛盾變數（Px），支援 inline 編輯。
> - 矛盾卡片新增 **CCI Badge**（Concept Complexity Index）：以 evolution / patch 色彩區分複雜度等級。
> - Tab ③ Block C 新增 **Evidence Coverage Gauge**：即時顯示專案證據覆蓋率（verified / partial / unverified 三態）。
> - 前端新元件：`ConditionalStepper.tsx`、`EntryGradingModal.tsx`、`OzOtPanel.tsx`、`CciBadge.tsx`、`EvidenceCoverageGauge.tsx`。
>
> **v8.1 (2026-04-13)**：**Tab ① ConvergenceDashboard 移除**。
> - Phase A 退役後，Tab ① 已無全域收斂數據來源。Dashboard 顯示的 `Confidence 0% / 0 節點 / 0/0 Fatal` 皆為初始值，對 RD 無參考價值。
> - 品質閘門由每張 `LayeredSolutionCard` 的 **L1 critic badge** 承擔（per-card 粒度）。
> - `ConvergenceDashboard` 僅在**決策中心 Phase B 執行後**顯示（`convergenceLoop.state.phase === 'B'`）。
> - Tab ① 區塊 A 標題從「矛盾總覽 + Phase A 健康度」簡化為「矛盾總覽」。
> - `trizLayeredMode` feature flag 預設值改為 `true`，舊版 TC/PC/SF 三路徑候選 UI 移除。
>
> **v8 (2026-04-09)**：**Phase A（矛盾空間健康度）退役**。
> - 第一性原理分析：Phase A 的六項職責已被 v7 的 L1 critic（per-card 品質閘門）、severity-driven L2 trigger、differential_analysis（per-LTS 推薦路線）、Phase B `crossLtsRedundancyWarnings`（跨矛盾去重）全面覆蓋。Phase A 的全域 `convergence_score` 閘門壓縮 N 個矛盾為一個數字，反而造成資訊損失。
> - Tab ① 從「先 Phase A 掃描 → 再生成 TRIZ」的兩步流程，簡化為**一鍵直出分層 drill-down 診斷報告**。
> - 新增**輕量 client-side pre-check**（非 LLM）：TC 矛盾缺少 improving/worsening 時 toast 警告，L1 critic badge 接手後續。
> - `CONVERGENCE_SCAN_PHASE_A` prompt 退役（~105 lines，git history 保留）。
> - `useConvergenceLoop.startPhaseA()` 移除；`startPhaseB()` 保留供 Decision Hub Phase B 交叉檢查。
> - `ArchitectureHaltOverlay` 保留（phase-agnostic，Phase B 仍可觸發）。
> - 「收斂監控」面板中的 Phase A Score / Health / Fatal/Major/Minor 行移除。
>
> **v7 (2026-04-09)**：對齊 TRIZ 分層 drill-down 架構（`docs/e2e/TRIZ_Layered_DrillDown_Optimization.md` v1.0 + `TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1）。
> - **Tab ① TRIZ 解矛盾徹底重寫**：從「TC/PC/SF 三選一候選池」改為「`LayeredTrizSolution` 分層診斷報告」。RD 收到的不再是並列選擇題，而是 L1 現象 → L2 根因 → L3 結構旁路的三層 drill-down 卡片。
> - 新增 **deepen_link 視覺化**（L1 的 TC 參數對如何被 ARIZ 深挖為 L2 的物理根因）。
> - 新增 **critic badge**（L1 被判為「trade-off 折衷」時顯示紅色提示，說明為何觸發 L2）。
> - 新增 **L2 觸發狀態**（必跑 / 條件跑 / 跳過）與手動「🔽 深挖 L2」按鈕。
> - 新增 **differential_analysis 面板**（跨層差異 + 推薦路線 + fallback + rationale）。
> - 採納互動三選：`[採納推薦路線]`、`[自訂組合]`、`[只採 L1 快速路線]`。
> - 決策中心新增 **`layered` 卡片類型**（對應 M6 跨層 drill-down，與 `single` / `composite` 並列）；layered 卡片以堆疊呈現 L1/L2/L3。
> - **Phase B 邏輯更新**：同一 `LayeredTrizSolution` 內跨層解 SKIP 互斥檢查；僅跨矛盾才做衝突分析。UI 移除「同矛盾多路徑警告」，改為「跨矛盾衝突」提示。
> - 方案追溯六要素新增第 7 項「drill-down 層級」（L1/L2/L3）。
> - 新增 **quick_mode flag**（severity=minor 時只跑 L1+L3，L2 跳過）。
>
> **v6 (2026-04-08)**：對齊 architecture v10 — Tab ② 子系統定義新增 Spatial Discovery Validator UI。
> - 介面契約展開區新增 spatial 區塊（bbox + mass + confidence badge）
> - 新增 Package Map 面板（SVG 包絡圖 + clash 警示）
> - 新增 RD inline override 入口（手動修正單一 component 數字）
> - 新增 What-if Overlay 二級按鈕（試算車架包絡）
> - Pre-CAD spatial_score 改為 deterministic（validator 算術產出，非 LLM 拍腦袋）
> - 新增 Spatial Confidence 視覺對應規範
>
> **v5 (2026-03-26)**：雙軌對稱 — 各一個節點 → 候選池 → 決策中心。
> - 反向：Anti-Anchor（1 個節點，創意發散）
> - 正向：TRIZ + 子系統 + SCAMPER 合成一個 E2E 節點（內部 tab 切換），報告風格對齊 Anti-Anchor
> - 兩條路徑各產出 route-style 候選，進入同一個候選池

---

## 使用者旅程（User Journey）

```
1. 看到核心使命（Mission）— 知道自己要解什麼問題
2. 看到兩張對稱卡片 — 反向探索 / 正向分析
3. 點任一張卡片展開操作（或兩張都做）
4. 每條路徑產出候選方案（帶 Validation Passport）
5. 所有方案匯入候選池 → 決策中心攤平比較
6. RD 選擇 adopt/skip → 觸發 Phase B 交叉檢查
7. Phase B 通過 → MUST 快篩 → Pre-CAD 審查
8. Phase Gate 2 通過 → 進入 CAD
```

---

## 畫面結構（Wireframe）

```
┌──────────────────────────────────────────────────────────────────┐
│  ① 核心設計使命                                                    │
│  Mission · Constraints · KPIs · 已驗證假設 · 高風險數               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ② 雙軌分析（兩張對稱卡片）                                         │
│                                                                    │
│  ┌─────────────────────────┐  ┌─────────────────────────┐        │
│  │  ⚡ 反向探索              │  │  🎯 正向分析              │        │
│  │                          │  │                          │        │
│  │  Anti-Anchor Sprint     │  │  TRIZ → 子系統 → SCAMPER │        │
│  │  從約束出發，AI 產出      │  │  從矛盾出發，系統化產出    │        │
│  │  非典型架構概念           │  │  候選方案                 │        │
│  │                          │  │                          │        │
│  │  每條自帶                │  │  內部 tab 切換：           │        │
│  │  Validation Passport    │  │  ① TRIZ ② 子系統 ③ SCAMPER│        │
│  │                          │  │                          │        │
│  │  [點擊展開操作]          │  │  [點擊展開操作]            │        │
│  └─────────────────────────┘  └─────────────────────────┘        │
│                                                                    │
│                    ▼ 候選池匯流 ▼                                   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  ③ 候選方案決策中心                                            │ │
│  │                                                                │ │
│  │  所有候選攤平 · RD adopt/skip · Phase B 交叉檢查               │ │
│  │                                                                │ │
│  │  ┌─────────┐ ┌──────────────┐ ┌─────────┐ ┌─────────┐      │ │
│  │  │ AA 路線1 │ │ TRIZ-Layered │ │ TRIZ-L1 │ │ SCAMPER │      │ │
│  │  │ single  │ │ ▢ L1 現象層   │ │ single  │ │ single  │      │ │
│  │  │ 反向/創意│ │ ▢ L2 根因層   │ │ 正向/演繹│ │ 正向/創意│      │ │
│  │  │ 信心:65 │ │ ▢ L3 結構層   │ │ 信心:78 │ │ 信心:71 │      │ │
│  │  │         │ │ 推薦:L2+L3    │ │         │ │         │      │ │
│  │  │ [adopt] │ │ [採納推薦]    │ │ [adopt] │ │ [skip]  │      │ │
│  │  └─────────┘ └──────────────┘ └─────────┘ └─────────┘      │ │
│  │     ↑             ↑                  ↑           ↑           │ │
│  │    單一         layered            單一       composite      │ │
│  │                (M6 跨層)                      (同層合併)     │ │
│  │                                                                │ │
│  │  [執行 Phase B 收斂掃描]  → 通過 ✓ / 跨矛盾衝突 ⚠              │ │
│  │  （同一 LTS 內跨層解自動 SKIP 互斥檢查，不再觸發「同矛盾多路徑警告」）│ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ④ 統一評估                                                        │
│  [ MUST 快篩 (M1-M6) ]  →  [ Pre-CAD 審查 (5D) ]                 │
│                                                                    │
│  ⑤ 收斂監控 — v8.1: 僅在決策中心 Phase B 後顯示                        │
│  （Tab ① 不再顯示 ConvergenceDashboard；per-card critic badge 取代） │
└──────────────────────────────────────────────────────────────────┘
```

---

## 節點互動定義

### ① 核心設計使命（MissionContext）

| 元素 | 互動 | 說明 |
|------|------|------|
| Mission 文字 | 唯讀 | 從 Brief 繼承 |
| Constraints 列表 | 唯讀 | 硬約束 badge |
| KPI 列表 | 唯讀 | 目標指標 |
| 已驗證假設 / 高風險數 | 唯讀 | 來自 Track（假設追蹤）頁 |

### ② 雙軌分析卡片

**設計原則**：兩張卡片等高等寬、對稱排列。點擊後展開各自的操作內容。

#### 反向探索卡片（Anti-Anchor）

點擊後展開：

| 元素 | 互動 | 觸發 |
|------|------|------|
| [AI 生成非典型架構] | 按鈕 → loading → 顯示 ≥3 張路線卡片 | POST /alternatives/anti-anchor |
| 路線卡片 | 展開看 mechanism / why_unconventional / VP | 展開/收合 |
| Validation Passport | 每條路線自帶：assumptions + weak_points + verifications + confidence | 唯讀 |
| [重新生成] | 清空 → 重新 AI 生成 | DELETE all + POST |

**產出**：route-style 候選卡片，直接進入候選池。

#### 正向分析卡片（TRIZ E2E）

點擊後展開，內部 tab 切換三個子步驟：

```
┌─────────────────────────────────────────────────┐
│  ① TRIZ 解矛盾  │  ② 子系統定義  │  ③ SCAMPER 變形 │
├─────────────────────────────────────────────────┤
│  （當前 tab 的內容）                               │
└─────────────────────────────────────────────────┘
```

**Tab ① TRIZ 解矛盾（v7 重寫：分層 drill-down 診斷）**

> 對應架構：`Forward_TRIZ_Solver_Architecture.md` + `TRIZ_Layered_DrillDown_Optimization.md` v1.0。**關鍵觀念轉變**：TC/PC/SF 不再是「三選一候選」，而是同一矛盾的三層診斷鏡 — L1 現象層（必跑）、L2 根因層（由 critic 或 severity 條件觸發）、L3 結構層（必跑平行旁路）。RD 收到的是一份 `LayeredTrizSolution` 分層報告，不是並列 pending 候選池。

##### 區塊 A：矛盾總覽

| 元素 | 互動 | 觸發 / API |
|------|------|------|
| 矛盾列表 | 每矛盾一列，展開成「分層診斷卡」（見區塊 B） | 唯讀 |
| severity badge | `fatal` / `major` / `minor`，決定 L2 預設觸發策略 | 唯讀 |
| ~~收斂 Dashboard~~ | ~~confidence / health / fatal·major·minor~~ | v8 移除：Phase A 退役後 Tab ① 無全域收斂數據來源；per-card L1 critic badge 取代。ConvergenceDashboard 僅在決策中心 Phase B 執行後顯示 |
| quick_mode toggle | 專案層級開關：minor 矛盾只跑 L1+L3，L2 預設跳過 | setQuickMode() |

##### 區塊 B：LayeredTrizSolution 分層診斷卡（每矛盾一張）

> **結構**：一個矛盾 → 一張卡片 → 堆疊三層（L1→L2→L3）。不再用 tab 或 toggle 呈現，改用**垂直堆疊**讓 drill-down 路徑一目了然。

```
┌─ C-EBIKE-012：馬達功率密度 vs 散熱  [major]  ────────┐
│                                                      │
│ 🔵 L1 — 現象層 (TC)     [必跑 ✓]       [展開 ▼]    │
│    查表 (#21 功率 × #17 溫度) → 原理 [19,35,3,36]   │
│    4 條具體化 suggestion • effort: low-med           │
│    depth: trade-off 改良                              │
│    ⚠ critic：四條皆為折衷修補，無本質突破 → 觸發 L2 │
│    [採納全部] [採納選取] [🔽 深挖 L2]               │
│                                                      │
│ 🟡 L2 — 根因層 (PC)    [已觸發 ✓]      [展開 ▼]    │
│    deepen_link：                                      │
│      (#21, #17) ─ARIZ 深挖─▶ 瞬時功率 P(t)          │
│      P(t) 必須 ≥ P_peak 且 必須 ≤ P_thermal          │
│    分離類型：⏱ time (0.85) │ 🎚 condition (0.62)   │
│    2 條具體化 suggestion • effort: med-high          │
│    depth: 根因突破                                    │
│    [採納] [跳過] [RD 手動編輯]                       │
│                                                      │
│ 🟢 L3 — 結構層 (SF)    [必跑 ✓ 旁路]   [展開 ▼]    │
│    Su-Field: S1=定子 │ S2=外殼 │ F=熱場 [insufficient]│
│    matched: 2.2.1 / 2.4.1                             │
│    relationship to others:                            │
│      supports L1 #19: "為脈衝冷卻提供熱容緩衝"       │
│      supports L2 time: "峰值窗口 +40%"               │
│      standalone: "獨立改善 15%"                       │
│    [採納] [跳過]                                     │
│                                                      │
│ ─── ✨ differential_analysis ───                     │
│ L1 vs L2：L1 優化 10-15% 瞬時；L2 重定義 envelope +30%│
│ L1 vs L3：正交（時間 × 結構）                         │
│ L2 vs L3：強增效 → 峰值窗口 +40%                      │
│                                                      │
│ 🎯 推薦路線：L2 + L3 組合（突破路線）                │
│    fallback：L1 單獨（快速路線）                      │
│    rationale：severity=major + 韌體資源充足          │
│                                                      │
│ [採納推薦路線]  [自訂組合]  [只採 L1 快速路線]       │
└──────────────────────────────────────────────────────┘
```

| 元素 | 互動 | 觸發 / API |
|------|------|------|
| 分層卡片頂部 | 矛盾 ID + 自然語言描述 + severity badge | 唯讀 |
| 三層垂直堆疊 | L1/L2/L3 各自摺疊展開 | 本地 state |
| L1 區塊 header | 永遠顯示「必跑 ✓」狀態，配藍色 | 唯讀 |
| L1 critic badge | 若 critic 判為 `trade-off 折衷` → 紅字警示並推薦觸發 L2 | 唯讀（來自 backend critic） |
| L1 suggestions | 每條 TC 原理 + 具體化文字 + cross_domain_example + effort/expected_gain | updateTrizSolution(layer="L1") |
| L1 [🔽 深挖 L2] | 手動按鈕，即使 critic 沒觸發也能強制深挖 | POST /triz/solve-layered?force_l2=true |
| L2 區塊 header | 三種狀態：`必跑/已觸發 ✓` / `條件未達 ⊘` / `quick_mode 跳過 ⊘` | 唯讀 |
| L2 trigger_reason | hover 顯示觸發理由（critic 判定 / severity / RD 手動） | 唯讀 |
| L2 deepen_link 視覺化 | 以箭頭圖 `(參數對) → 物理根因` 呈現 ARIZ 深挖 | 唯讀 |
| L2 分離類型 chips | time/space/condition/whole_part 四種帶 confidence 分數 | 唯讀 |
| L2 suggestions | 每條 separation + principle_refs + concrete | updateTrizSolution(layer="L2") |
| L2 [RD 手動編輯] | 允許 RD 修改 derived_parameter 或分離類型後重算 | editDeepenLink() |
| L3 區塊 header | 永遠顯示「必跑 ✓ 旁路」，配綠色 | 唯讀 |
| L3 Su-Field 模型 | S1/S2/F 三角標示 + state badge（insufficient/harmful/incomplete） | 唯讀 |
| L3 standard_solutions | 76 標準解 ID + 具體化建議 | 唯讀 |
| L3 relationship_to_other_layers | 明示此 L3 建議如何強化 L1/L2，或能否 standalone | 唯讀（關鍵！） |
| differential_analysis 面板 | 三對比對（L1vs L2 / L1 vs L3 / L2 vs L3） | 唯讀 |
| recommended_route 區塊 | primary + fallback + rationale，高亮顯示 | 唯讀 |
| [採納推薦路線] | 一鍵採納 differential 建議的組合 → 產生 `layered` Concept Route | adoptLayeredSolution(mode="recommended") |
| [自訂組合] | 開啟對話框，RD 勾選 L1/L2/L3 任意子集 | adoptLayeredSolution(mode="custom") |
| [只採 L1 快速路線] | 放棄深挖與結構補強，走 fallback | adoptLayeredSolution(mode="fallback") |

##### 區塊 C：採納後的候選輸出

採納動作會產出一張 **`layered` 類型的 Concept Route 卡片**送進候選池（見 §決策中心）：

- `recommended` → 包含 L2+L3（或 differential_analysis 指定的層組合），type=`layered`
- `custom` → 包含 RD 勾選的層，type=`layered`（僅採一層時降級為 `single`）
- `fallback` → 僅 L1，若 L1 內部採納多條 TC 原理且互相強化，可進一步標為 `composite`（走 §TRIZ_Multi_Solution_Adoption_Strategy M1-M3 同層合併）

> **重要**：同一 `LayeredTrizSolution` 只會產生**一張** Concept Route 卡片（堆疊呈現內部層次），不會產生三張。這是 v7 與 v6 的根本差別 — 消除了「每矛盾選一條路徑」的選擇題語意。

**Tab ② 子系統定義（含 Spatial Discovery）**

> 對應架構：`Forward_Subsystem_Discovery_Architecture.md` v2.0 的 F2 + F2.5。F2 是 LLM 產出三層樹 + 6 維契約；F2.5 是純算術 validator 把 LLM 估計值用 layered resolver 真值覆寫，並產出 Package Map。**整個 tab 的 UI 必須讓 RD 一眼分辨「這是 LLM 拍腦袋的 / 這是 vendor 真值 / 這是我自己 override 的」**。

##### 區塊 A：三層樹 + 介面契約

| 元素 | 互動 | 觸發 / API |
|------|------|------|
| [AI 建議架構分解] | LLM 產出 System→Module→Component 樹（含 spatial） | POST /scamper/subsystem-suggestions |
| [手動新增] | 表單：名稱 / 層級 / 理由 / 關聯矛盾 / 鄰居名稱 | createSubsystem() |
| 樹狀結構 | 展開 System → Module → Component（三層皆可帶契約） | 可收合 |
| 介面契約・6 維欄位 | envelope / loadPath / signalPath / thermalPath / datumTolerance / serviceability | 唯讀 / 可編輯 |
| 介面契約・spatial 區塊 | bbox（x×y×z mm）+ mass_g + mounting_pattern | 唯讀 |
| 介面契約・confidence badge | rd_confirmed / library / estimate / llm_estimate 五色 | 唯讀（見 §Spatial Confidence） |
| 介面契約・reference_source | rd_override:&lt;key&gt; / learned:&lt;key&gt; / web:&lt;query&gt; / seed:&lt;key&gt; / llm_estimate | 唯讀 hover 顯示 trace |
| [✏ 我來給數字] | 開啟 RD inline override 對話框（輸入 bbox + mass） | POST /spatial/component-overrides |
| [📤 推升至 learned] | 把當前估計推升為跨專案 learned component | POST /spatial/learned-components |
| [確認] | confirmed → 解鎖 SCAMPER tab | updateSubsystem() |

##### 區塊 B：Package Map 面板（F2.5 discovery 輸出）

| 元素 | 互動 | 觸發 / API |
|------|------|------|
| Package Map SVG | 俯視（XY）+ 側視（XZ）兩個正交圖 | 唯讀（隨 subsystem-suggestions response 自動更新） |
| 總質量 | required.total_mass_g | 唯讀數字 |
| 最小封殼 | required.total_bbox_mm | 唯讀數字 |
| Clash 警示 | 重疊的 module pair 紅色標示 | 即時 |
| Notes | validator 補充提示 | 唯讀清單 |

##### 區塊 C：What-if Overlay（可選，F2.5 overlay）

> **設計原則**：discovery 是 descriptive、overlay 是 prescriptive。overlay **不限制**創意發想，只用來事後比較 trade-off。

| 元素 | 互動 | 觸發 / API |
|------|------|------|
| [🧪 試算車架包絡] | 二級按鈕，預設摺疊 | 開啟 overlay 對話框 |
| Zone 輸入表單 | 為每個 anchor（BB_center / downtube_top / ...）輸入 max bbox | 表單編輯 |
| Mass budget 輸入 | 為每個 module 輸入 max mass_g | 表單編輯 |
| [執行 Overlay] | 套上 overlay 重算 | POST /scamper/spatial-overlay |
| Overlay SVG | 紅 / 橘 / 綠標示 fits / tight / clash | 唯讀 |
| overlay_violations 清單 | 超界 module 列表 | 唯讀 |
| [清除 Overlay] | 回到 discovery 原始 SVG | 本地 state |

**Tab ③ SCAMPER 變形**

| 元素 | 互動 | 觸發 |
|------|------|------|
| [AI 生成] | 每子系統 × 7 動作 | POST /scamper/perform |
| 變形卡片 | S/C/A/M/P/E/R badge + 描述 | 唯讀 |
| [採用] / [跳過] | toggle | updateScamperVariant() |
| 潛在風險 | severity badge（僅顯示，不回饋收斂） | 唯讀 |
| [確認完成] | 正向分析結束，候選進入候選池 | goNext() |

**產出**：TRIZ 候選（TC/PC/SF）+ SCAMPER 候選，進入候選池。報告風格與 Anti-Anchor 對齊（每個候選帶 mechanism + VP）。

### ③ 候選方案決策中心

| 元素 | 互動 | 觸發 |
|------|------|------|
| 方案卡片 | 橫向排列，支援三種 type：`single` / `composite` / `layered` | — |
| 來源 badge | 反向(amber) / 正向(blue) + 具體步驟 | 唯讀 |
| type badge | `single` / `composite` (M1-M3 同層合併) / `layered` (M6 跨層 drill-down) | 唯讀 |
| layered 卡片的層堆疊 | 卡片內部顯示 L1/L2/L3 三個迷你層徽章（已採納的顯示實心，未採納顯示空心） | 唯讀 |
| [adopt] / [skip] | 切換採用狀態 | updateAlternative() |
| ~~⚠ 同矛盾多路徑警告~~ | **v7 移除**：同一 LTS 內跨層解為合法 drill-down 組合，Phase B 自動 SKIP 互斥 | — |
| ⚠ 跨矛盾衝突提示 | 僅在不同 `contradiction_id` 的解法互斥時顯示 | 即時 |
| [執行 Phase B] | 只送 adopted 做交叉檢查；`phase_b_directive` 控制同 LTS SKIP | startPhaseB() |
| Phase B 結果 | converged ✓ / halted ⚠ | 即時更新 |
| [確認進入 MUST] | Phase B 通過後才可按 | goNext() |

#### 方案卡片三層資訊

| 層 | single / composite | layered (新增，v7) | 展示方式 |
|----|-----|-----|----------|
| **第一眼** | 名稱 · 來源 · type · 信心 · MUST/Pre-CAD | 同左 + L1/L2/L3 採納徽章 + 推薦路線標籤 | 卡片頂部，始終可見 |
| **第二眼** | 核心機制 · 優點 · 缺點 | 每層各自的 mechanism + depth_indicator + effort；differential_analysis 精簡版 | 展開第一層 |
| **第三眼** | 假設(E0-E4) · 驗證需求 · 弱點 · VP | 每層獨立的 assumptions / VP；deepen_link 溯源；L3 relationship_to_other_layers | 展開第二層 |

#### layered 卡片範例

```
┌─ CR-EMOTOR-008  [layered]  [正向/TRIZ]  信心:84 ─┐
│ 🔵●  🟡●  🟢●   推薦路線：L2+L3 突破              │
│ 主機制：雙模態功率管理 + 熱管陣列 S3 中介物           │
│ MUST: ✓  Pre-CAD: 85%  ─────────  [skip] [adopt ✓]│
└────────────────────────────────────────────────────┘
```

- 🔵● = L1 已採納（實心）；🟡● = L2 已採納；🟢● = L3 已採納
- 🔵○ = 該層存在但未採納（空心）

### ④ 統一評估

| 元素 | 互動 | 觸發 |
|------|------|------|
| MUST 快篩 | 每方案 × M1-M6 → pass/fail/marginal | AI + RD |
| Pre-CAD 審查 | 五維雷達圖 | spatial = validator 算術產出（deterministic）；cost/safety/decoupling/supply = LLM |
| Pre-CAD spatial trace | 顯示 validator 用了哪些 module 的 bbox + clash + 總質量算出此分數 | 唯讀（hover 展開） |
| [📤 推升簽核估計] | Pre-CAD 通過後，把高 confidence 的估計批次推升至 learned | POST /spatial/learned-components ×N |
| Phase Gate 2 | ≥1 方案 overallPass → 進入 CAD | 自動 |

### ⑤ 收斂監控

| 元素 | 互動 | 說明 |
|------|------|------|
| ~~Tab ① ConvergenceDashboard~~ | ~~Confidence / Health / Fatal·Major·Minor~~ | v8.1 移除：Phase A 退役後 Tab ① 無數據來源��。ConvergenceDashboard 僅在決策中心 Phase B 執行後顯示 |
| 決策中心 ConvergenceDashboard | Confidence / Health / Fatal·Major·Minor | Phase B 掃描完成後才渲染（`phase === 'B' && status !== 'idle'`） |
| Risk Register | minor 清單 | 展開 |
| 反向無收斂分析 | 創意工具不做收斂分析 | — |

---

## 設計原則

| 原則 | 說明 |
|------|------|
| **對稱卡片** | 兩張卡片等高等寬，點擊展開各自操作內容 |
| **方法獨立** | 反向 = 創意（1 步），正向 = 演繹（3 sub-tab），不混用 |
| **E2E 節點** | 正向的 TRIZ+子系統+SCAMPER 對外是 1 個節點，對內是 3 個 tab |
| **分層而非選題** (v7) | Tab ① TRIZ 的輸出是一份 L1/L2/L3 分層診斷報告，不是並列 pending 候選池。RD 從「三選一」改為「採納 drill-down 組合」 |
| **垂直堆疊呈現 drill-down** (v7) | 同一矛盾的三層解以垂直堆疊呈現，讓 ARIZ 深挖路徑（TC→PC）視覺化為上下關係，而非左右並列 |
| **L3 永遠呈現** (v7) | 即使 L1/L2 已採納，L3 的結構旁路建議永遠顯示，避免結構盲點被 skip |
| **報告格式統一** | 兩條路徑的候選卡片格式一致（mechanism + VP） |
| **路徑色彩** | 反向 = amber（⚡暖色），正向 = blue（🎯冷色） |
| **候選池匯流** | 所有候選進同一個池，在決策中心統一比較 |
| **Discovery 不限制創意** | F2.5 spatial validator 是 descriptive，never blocking。overlay 是可選的事後 trade-off 工具 |
| **Confidence 必須可見** | 每個 spatial 數字都帶 confidence badge，RD 一眼分辨「LLM 拍腦袋 vs vendor 真值」 |
| **Trace 每一個數字** | reference_source 必須能 hover 顯示完整 trace（哪一層、哪個 key、何時被覆寫） |

---

## Spatial Confidence 視覺對應

> **來源**：`Forward_Subsystem_Discovery_Architecture.md` §6.2 reference_source 命名空間。
> **設計原則**：colour-coded by trust level，深綠 → 紅依信任度遞減。RD 看顏色就知道是否需要手動 override。

| confidence | reference_source 前綴 | Badge 配色（fill / stroke / text） | 語意 |
|---|---|---|---|
| **rd_confirmed** | `rd_override:<key>` | `#14532d` / `#052e16` / `#fff` 深綠白字 | RD 在本專案手動 override，最高信任 |
| **library** | `learned:<key>` | `#bbf7d0` / `#14532d` / `#000` 淺綠黑字 | 命中跨專案 learned components |
| **library** | `seed:<key>` | `#dcfce7` / `#14532d` / `#000` 更淺綠黑字 | 命中手工 seed JSON（backstop） |
| **estimate** | `web:<query>` | `#fde68a` / `#92400e` / `#000` 橘黃黑字 | web lookup 抓取，未經 RD 簽核 |
| **estimate** | （引用了 key 但查不到） | `#fef3c7` / `#92400e` / `#000` 淺橘黑字 | LLM 引用的 key 不存在，降級 |
| **llm_estimate** | `llm_estimate` | `#fecaca` / `#7f1d1d` / `#000` 紅黑字 | LLM 自己的數字，最後 fallback，**RD 應該 override** |

> **互動規則**：badge 上 hover 顯示完整 reference_source 字串與最後一次更新時間。點擊深綠 / 淺綠 badge 可看「這個值的來源歷史」（migration 路徑：seed → web → learned → rd_override）。

---

## Discovery vs Overlay 的職責分離

> **必須遵守的 UI 規則**：discovery 與 overlay 的視覺元素**永遠不要混在同一張圖**。

| 維度 | Discovery（區塊 B） | Overlay（區塊 C） |
|---|---|---|
| 觸發時機 | 一鍵建議子系統後**自動**算 | RD **主動**點「試算車架包絡」才算 |
| 視覺位置 | 主面板 | 二級對話框 / 抽屜 |
| 是否影響 confirmed | 否（只是資訊） | 否（只是 trade-off 試算） |
| SVG 配色 | 中性灰藍 | 紅 / 橘 / 綠（fits/tight/clash） |
| 預設顯示 | 一定顯示 | 預設摺疊 |
| 失敗時 | 退化為「無 spatial 資料」提示 | 整個 overlay 區塊不顯示 |

---

## 步驟索引映射（內部 → 顯示）

| 內部索引 | 顯示 | Stepper 層 | 內容層 |
|----------|------|-----------|--------|
| 0 | 反向探索 | 左卡片 | Anti-Anchor 操作 |
| 1 | 正向: Tab ① TRIZ | 右卡片 | TRIZ 分層 drill-down 診斷（L1/L2/L3 + differential_analysis） |
| 2 | 正向: Tab ② 子系統 | 右卡片 | 3 層架構樹 + 6 維契約 + Spatial Discovery |
| 3 | 正向: Tab ③ SCAMPER | 右卡片 | 創意變形 |
| 4 | 決策中心 | 獨立區塊 | adopt/skip + Phase B |
| 5 | MUST | 評估區 | M1-M6 |
| 6 | Pre-CAD | 評估區 | 五維雷達圖（spatial 為 deterministic 算術） |

---

## 方案追溯七要素（v7 擴充）

| # | 要素 | UI 位置 | 說明 |
|---|------|---------|------|
| 1 | 來源路徑 | 卡片 badge | 反向(amber) / 正向(blue) |
| 2 | 來源步驟 | 卡片 badge | Anti-Anchor / TRIZ-Layered / SCAMPER |
| 3 | **drill-down 層級** (v7 新增) | 卡片層堆疊徽章 | layered: L1/L2/L3 採納組合 + recommended_route；single: 純 L1 或 L2；composite: L1 內部多原理合併 |
| 4 | 解的矛盾 | 第三眼 | contradiction IDs + 描述 + severity |
| 5 | 涉及子系統 | 第三眼 | subsystem 名稱 + 層級 |
| 6 | 基於假設 | 第三眼 | evidence_level E0-E4 + is_falsifiable + 每層獨立 assumptions |
| 7 | 缺少驗證 | 第三眼 | required verifications + 成本/時長；layered 卡片需列出跨層交互驗證項 |

---

## 對齊文件對應表

| 本 spec 章節 | 對應架構文件 | 章節 |
|---|---|---|
| Tab ② 區塊 A 三層樹 | `Forward_Subsystem_Discovery_Architecture.md` | §6.4 三層樹定義 |
| Tab ② 區塊 A 6 維契約 | `Forward_Subsystem_Discovery_Architecture.md` | §6.5 六維介面契約定義 |
| Tab ② 區塊 A spatial 區塊 | `Forward_Subsystem_Discovery_Architecture.md` | §6.1 介面契約 + Spatial 擴充 |
| Tab ② 區塊 A reference_source | `Forward_Subsystem_Discovery_Architecture.md` | §6.2 命名空間 |
| Tab ② 區塊 A 我來給數字 | `Forward_Subsystem_Discovery_Architecture.md` | §7.2 RD inline override 流程 |
| Tab ② 區塊 A 推升 learned | `Forward_Subsystem_Discovery_Architecture.md` | §7.3 learned 推升流程 |
| Tab ② 區塊 B Package Map | `Forward_Subsystem_Discovery_Architecture.md` | §3.3 PackageMap 結構 |
| Tab ② 區塊 C What-if Overlay | `Forward_Subsystem_Discovery_Architecture.md` | §7.4 overlay 流程 |
| Spatial Confidence 視覺對應 | `Forward_Subsystem_Discovery_Architecture.md` | §8.2 confidence 流轉 |
| Discovery vs Overlay 職責分離 | `Forward_Subsystem_Discovery_Architecture.md` | §1.2 設計原則 #1 |
| Tab ① TRIZ 區塊 A 矛盾總覽 | `Forward_TRIZ_Solver_Architecture.md` | §6 三條路徑（作為底層 primitive） |
| Tab ① TRIZ 區塊 B 分層診斷卡 | `TRIZ_Layered_DrillDown_Optimization.md` | §4 三層 Drill-Down 架構 + §5 LayeredTrizSolution schema + §7 案例 |
| Tab ① L2 critic 觸發邏輯 | `TRIZ_Layered_DrillDown_Optimization.md` | §4.2 L2 觸發條件表 |
| Tab ① deepen_link 視覺化 | `TRIZ_Layered_DrillDown_Optimization.md` | §4.3 L1→L2 deepen_link 契約 |
| Tab ① L3 structural_lens 定位 | `TRIZ_Layered_DrillDown_Optimization.md` | §4.4 L3 旁路定位 |
| Tab ① differential_analysis 面板 | `TRIZ_Layered_DrillDown_Optimization.md` | §5 資料模型 + §7.5 案例輸出 |
| Tab ① quick_mode flag | `TRIZ_Layered_DrillDown_Optimization.md` | §10 Anti-Pattern 經驗法則 |
| 決策中心 layered 卡片類型 | `TRIZ_Multi_Solution_Adoption_Strategy.md` v1.1 | §2 M6 跨層 drill-down + §4.2 Concept Route 資料模型擴展 |
| 決策中心 Phase B 同 LTS SKIP | `TRIZ_Layered_DrillDown_Optimization.md` | §8.3 Phase B 掃描邏輯修訂 |
| ④ Pre-CAD 五維雷達 spatial 算術 | `Forward_Subsystem_Discovery_Architecture.md` | §5.2 Pre-CAD spatial_score 改算術 |

> **注意**：若架構文件版本升級（v10+），本 spec 必須同步檢查上表對應章節是否仍然成立，避免 UX 與架構脫鉤。

---

## v9.0 新增元件規格（ADR-008 Auto-TRIZ v2）

### Entry Grading Modal（`EntryGradingModal.tsx`）

**觸發時機**：專案建立後首次進入 Explore 頁。

**流程**：
1. Modal 顯示「請描述您的問題」+ 上下文欄位
2. 呼叫 `POST /analyst/entry-grading`
3. AI 回傳 Level A/B/C + reasoning + recommended_steps
4. RD 確認或手動覆寫 level
5. 結果寫入 `projects.entry_level`，控制後續 UI 路徑

**視覺**：
- Level A（症狀模糊）：顯示完整 5 步 stepper 提示
- Level B（已知 TC）：顯示「直接進入分析」提示
- Level C（功能缺失）：顯示「SF-only 快速路徑」提示

### Conditional Stepper（`ConditionalStepper.tsx`）

**位置**：Explore 頁主導航。

| Level | 呈現方式 | 步驟 |
|-------|---------|------|
| **A** | 五步線性 Stepper | ① Problem Scoping (5Why/KT) → ② Function Analysis → ③ Socratic Q&A → ④ Contradictions → ⑤ CLD |
| **B** | 三 Tab（現有 UI） | Tab ① Contradictions · Tab ② Socratic · Tab ③ CLD（FA 為 side panel） |
| **C** | 單步 SF-only | 直接進入 SF 分析，跳過 TC 流程 |

**切換邏輯**：讀取 `project.entry_level`；若未分級，先觸發 Entry Grading Modal。

### OZ-OT Panel（`OzOtPanel.tsx`）

**位置**：Tab ① Block B（正向分析卡片），矛盾展開後內嵌。

**欄位**：
| 欄位 | 來源 | 可編輯 |
|------|------|--------|
| OZ（操作區域） | `POST /analyst/oz-ot-analysis` 回傳 | 是（inline text） |
| OT（操作時間） | 同上 | 是 |
| Px（物理矛盾變數） | 同上 | 是 |
| 分離策略提示 | `separation_hints[]` | 否（唯讀 badge 列） |

**互動**：RD 編輯後自動 patch `contradictions` 表的 `oz_zone` / `ot_time` / `px_variable`。

### CCI Badge（`CciBadge.tsx`）

**位置**：矛盾卡片右上角（與 severity badge 並列）。

**資料來源**：`triz_solver.complexity_check()` 回傳的 CCI 值。

| CCI 結果 | 色彩 | 意義 |
|----------|------|------|
| Evolution | green | 系統性進化，低複雜度 |
| Patch | amber | 局部修補，需注意技術債 |
| Unknown | gray | 尚未執行 complexity check |

### Evidence Coverage Gauge（`EvidenceCoverageGauge.tsx`）

**位置**：Tab ③ Block C（候選方案決策中心）頂部。

**資料來源**：`GET /evidence/coverage/{project_id}` 回傳的 `CoverageResponse`。

**視覺**：
- 環形進度條顯示 `coverage_ratio`（0-100%）
- 內部三態分佈條：verified (green) / partial (amber) / unverified (red)
- 滑鼠 hover 顯示 by_type 明細
- 門檻線：40% 預設（低於時顯示警告 toast）
