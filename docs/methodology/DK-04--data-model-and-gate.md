# DK-04 — 資料模型 / Gate 參考

> 13 核心 entity schema、TRIZ 內部 gate、TR 外部 gate、state JSON 規格、黑板協議、TRIZ→TR 工件交接。
> SSOT: `docs/methodology/uml/00_domain_model.md`、`engineering/tr_gate_framework.md`、`uml/10_problem_lifecycle.md`。

---

## §1 雙層狀態機

Project 同時運行兩層狀態機：

```
┌─── TRIZ Session（內部 / 推理層）────┐
│  Step 0 → 1 → 2 → 3 → 4 → 5         │
│  state: .triz-state.json             │
│  by: triz-* skills + agents          │
└──────────────────────────────────────┘
              ↓ Step 5 完成
              ↓ = TR0 概念凍結輸入
┌─── TR Gate（外部 / 工程層）──────────┐
│  TR0 → TR1 → ... → TR10              │
│  state: .tr-state.json               │
│  by: tr-* skills                     │
└──────────────────────────────────────┘
```

兩層獨立：TRIZ session 可以重跑（同問題第二次嘗試）而不重置 TR；TR 可以針對不同子系統獨立推進。

問題生命週期 mermaid 圖見 `docs/methodology/uml/10_problem_lifecycle.md`。

---

## §2 13 核心 Entity Schema

完整 class diagram 見 `docs/methodology/uml/00_domain_model.md`。本節列每個 entity 的關鍵欄位 + 哪個 step 產出 + 哪個 step 消費。

### §2.1 Problem

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `type` | `矛盾` / `功能缺失` / `純最佳化` | Step 0 路由 | 決定走 TC 路徑或 SF-only |
| `level` | `A` / `B` / `C` | Step 0 入口判定 | C 走外部框架；A 必過 Step 0；B 跳 Step 1 |
| `subsystem` | string | 使用者輸入 | 多子系統時各自獨立 routing |

### §2.2 TC（Technical Contradiction）

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `improveParam` | P1（39 參數其一） | Step 2 KB-01 映射 | 矩陣行索引 |
| `worsenParam` | P2（39 參數其一） | Step 2 KB-01 映射 | 矩陣列索引 |
| `candidates` | Solution × 2-4 | Step 2 KB-03 具體化 | Step 3 深挖入口 |
| `bottleneckRank` | int (Optional) | Step 2 多 TC 路由 | 瓶頸路徑排序 |

### §2.3 PC（Physical Contradiction）

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `px` | Px 物件 | Step 3 OZ-OT 提取 | 分離原理輸入 |
| `stateA` | string | Step 3 PC 造句 | 對應 P1 需求 |
| `stateNotA` | string | Step 3 PC 造句 | 對應 P2 需求 |

PC 為 1 對多關係：一個 TC 經 OZ-OT 分析可能拆出多個 PC（若有 Px 多變數共控）。

### §2.4 Px

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `name` | string | Step 3 OZ-OT | 物理變數命名 |
| `type` | `Direct` / `Proxy` | Step 3 三情境分支 | 長鏈耦合用 Proxy |
| `sensitivity_P1` | float | Step 3 量化評分 | ∂P1/∂Px |
| `sensitivity_P2` | float | Step 3 量化評分 | ∂P2/∂Px |

### §2.5 SF（Substance-Field / Su-Field）

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `substance1` | S1（工具） | Step 1 建模 | 質-場主動方 |
| `substance2` | S2（物件） | Step 1 建模 | 質-場接收方 |
| `field` | F | Step 1 建模 | 能量類型（電/磁/熱/機械/化學/光） |
| `diagnosis` | `無效` / `有害` / `不足` / `缺失` | Step 1 SF 診斷 | 76 標準解大類路由 |

### §2.6 OZ / OT

| Entity | 欄位 | 用途 |
|:-------|:-----|:-----|
| OZ | `location` (string) | 衝突發生位置；§5 SIM 重疊判斷依據 |
| OT | `timepoint` (string) | 衝突發生時間；同上 |

### §2.7 SeparationPrinciple

| 欄位 | 型別 | 來源 |
|:-----|:-----|:-----|
| `type` | `時間` / `空間` / `條件` / `系統層級` | Step 3c 四問觸發 |
| `strategy` | string | 具體分離策略描述 + 控制方程 + 邊界條件 |

### §2.8 ScientificEffect

| 欄位 | 型別 | 來源 |
|:-----|:-----|:-----|
| `effectName` | string | 科學效應庫 / WebSearch |
| `field` | F | 對應產生的場 |
| `substance` | S | 對應需要的物質 |

### §2.9 Solution

| 欄位 | 型別 | 來源 | 用途 |
|:-----|:-----|:-----|:-----|
| `field` | F + 控制方程 + 數值 | Step 3 SF 標準解導入 | TR0 工程規格輸入 |
| `substance` | S + 牌號 + 物性 | Step 3 SF + 科學效應 | TR0 Material Card 輸入 |
| `oz` | OZ | Step 3 | TR0 幾何規格輸入 |
| `ot` | OT | Step 3 | TR0 時序規格輸入 |
| `evidenceRefs` | Claim ID list | Step 3 數據驗證 | 所有數值聲明的證據鏈 |

### §2.10 SIM（Solution Interaction Matrix）

| 欄位 | 型別 | 來源 |
|:-----|:-----|:-----|
| `phase` | `粗篩 (Step 2b)` / `精篩 (Step 3b)` | 流程位置 |
| `round` | int | 當前迭代輪次（≤ maxRound） |
| `maxRound` | int = 2 (default) | DK-02 §7.5 收斂規則 |
| `cells` | M×N matrix of {-1, 0, +1} | Step 3b 評分 |

### §2.11 ComplexityCheck

| 欄位 | 型別 | 來源 | 判定 |
|:-----|:-----|:-----|:-----|
| `structural` | bool | 零件是否變多 | 補丁信號 |
| `energy` | bool | 能量消耗是否變大 | 補丁信號 |
| `cognitive` | bool | 理解時間是否變長 | 補丁信號 |
| `evolutionAligned` | bool | 是否符合演化趨勢 | 進化信號 |
| `verdict` | `Patch` / `Evolution` | 四問規則（DK-01 §7.2） | Step 4 出口 |
| `cci` | float ∈ [0, 1] | v2 量化指數 | 補丁強度（取代二元判定） |

### §2.12 TechnicalDebt

| 欄位 | 型別 | 來源 |
|:-----|:-----|:-----|
| `debtId` | TD-{project}-{seq} | Step 4 補丁路徑 |
| `unresolvedPC` | PC reference | 哪個 PC 未真正解 |
| `patchDescription` | string | 當前補丁方案 |
| `patchCost` | list[`structural` / `energy` / `cognitive`] | 四問哪些「是」 |
| `triggerCondition` | string | 什麼情況下必須回來解 |
| `priority` | `P1`（下一代必解）/ `P2`（觀察）/ `P3`（接受） | 排程優先級 |

### §2.13 Entity 關係速查

```
Problem 1 ─*→ TC（多 TC 場景）
Problem 1 ─*→ SF（功能缺失走 SF-only）
TC      1 ─1..*→ PC（OZ-OT 提取）
PC      1 ─1→ Px
PC      1 ─1..*→ SeparationPrinciple
Sep.    1 ─1→ SF
SF      1 ─*→ ScientificEffect
ScieEff 1 ─1→ Solution
Px      1 ─1→ OZ + 1→ OT
TC      *  →1 SIM（多 TC）
Solution 1 →1 ComplexityCheck
ComplexityCheck → TechnicalDebt（Patch 且無時間時）
```

---

## §3 Gate 條件

### §3.1 TRIZ 內部 gate（Step 進場條件）

| Gate | 從 → 到 | 進場條件 |
|:-----|:--------|:---------|
| G0 | 入口 → Step 0 | Level A，且問題類型未明 |
| G0' | 入口 → Step 1 | Level B（造句通過）；或 Step 0 結果根因涉及組件交互 |
| G0'' | 入口 → Step 2 | Step 0 根因鎖定為物理參數（⚠️ 跳步風險，建議產出後回補 Step 1） |
| G1 | Step 1 → Step 2 | SF 圖完成 + 改善/惡化描述完成 |
| G1' | Step 1 → SF-only | SF 診斷為「缺失」或「不足」+ 無副作用 |
| G2 | Step 2 → Step 3 | TC 候選方向 ≥ 1 + 至少一個能寫控制方程 |
| G2' | Step 2 → Step 2b | 多 TC 且選 SIM 路徑 |
| G3 | Step 3 → Step 4 | Px 鎖定 + PC 造句通過 + 至少一個分離策略可行 + Solution 含 F+S+OZ+OT |
| G3' | Step 3 → Step 3b | 多 TC + SIM 路徑 + Step 3 各 TC 已產出具體 F/S |
| G4 | Step 4 → Step 5 | ComplexityCheck.verdict = Evolution，**或**= Patch + TechnicalDebt 已登記 |
| G4' | Step 4 → STOP | 違反 5 STOP 信號之一（DK-01 §9.1） |

### §3.2 TR 外部 gate（TR0-TR10）

完整退出條件見 `docs/engineering/tr_gate_framework.md`。本節為摘要：

| TR | 名稱 | 退出條件（摘要） |
|:---|:-----|:---------------|
| **TR0** | 概念凍結 | TRIZ session 判定 Evolution / Weak Evolution，Evidence Registry ≥ 50% HIGH+MEDIUM |
| TR1 | 可行性 | 各子系統 FEA/CFD 通過，14 項 V-test 模擬 pass |
| TR2 | 參數鎖定 | 關鍵零件選定，ICD 簽核，供應商能力確認 |
| TR3 | 詳細設計 | 完整 3D CAD + BOM 凍結 + Design FMEA |
| TR4 | 原型備料 | 長交期物料下單，治工具設計完成 |
| TR5 | Alpha 原型 | 功能原型可組裝可運作 |
| TR6 | Alpha 驗證 | V1-V14 實測 pass |
| TR7 | Beta 設計 | DFM 修正，Process FMEA + Control Plan 初版 |
| TR8 | Beta 原型 | 量產意圖原型 + Control Plan 驗證 |
| TR9 | 量產驗證 | DVP&R 全項完成 |
| TR10 | 量產釋放 | Cpk ≥ 1.33，量產 SOP 簽核（PPAP 等效） |

### §3.3 TR 與國際標準對應

| 標準 | 我們的對應 | 關係 |
|:-----|:----------|:-----|
| NASA TRL（ISO 16290）| TR0-TR1 ≈ TRL 3-5 | 性質不同（TRL 評估「技術能否用」；TR 評估「產品開發到哪」） |
| APQP（AIAG）| TR3→TR10 ≈ Phase 2-5 | FMEA / Control Plan / PPAP 已納入退出條件 |
| **VDA MLA**（ML0-ML7）| TR0-TR10 ≈ ML0-ML7 | **最接近的對標**（同為 milestone-based gate） |

---

## §4 State JSON Schema

### §4.1 `.claude/context/triz/.triz-state.json`

```json
{
  "session_id": "triz-20260428-001",
  "project": "ebike-drive-unit",
  "subsystem": "afm-motor",
  "current_step": "step3",
  "problem": {
    "type": "矛盾",
    "level": "B",
    "description": "..."
  },
  "step0": { "completed": true, "fiveWhyChain": [...], "ktAnalysis": {...} },
  "step1": { "completed": true, "faGraph": "...", "sfDiagnoses": [...] },
  "step2": {
    "completed": true,
    "route": "sim",
    "tcs": [
      { "id": "TC1", "improveParam": "P9", "worsenParam": "P26", "candidates": [...] },
      { "id": "TC2", "improveParam": "P17", "worsenParam": "P5", "candidates": [...] }
    ],
    "step2b": { "deduplicated": [...], "preScreen": {...} }
  },
  "step3": {
    "in_progress": true,
    "perTC": {
      "TC1": { "px": {...}, "pc": {...}, "separations": [...], "solutions": [...] },
      "TC2": { ... }
    },
    "step3b": { "round": 1, "matrix": [[...]], "verdict": "ongoing" }
  },
  "step4": null,
  "step5": null,
  "stops": [],
  "technical_debts": [],
  "evidence_registry": "session-step2-evidence-20260428.md"
}
```

### §4.2 `.claude/context/triz/.tr-state.json`

```json
{
  "project": "ebike-drive-unit",
  "subsystems": {
    "afm-motor": { "current_tr": "TR0", "next_target": "TR1", "wis": ["WI-01"] },
    "harmonic-gear": { "current_tr": "TR0.5", "next_target": "TR1", "wis": ["WI-02"] },
    "pcm-thermal": { "current_tr": "TR0", "next_target": "TR1", "wis": ["WI-03"] }
  },
  "gate_reviews": [
    { "tr": "TR0", "subsystem": "afm-motor", "report": "docs/engineering/gate_reviews/TR0_afm_review_2026-04-28.md", "verdict": "pass" }
  ],
  "risks": "docs/engineering/risk_register.md",
  "critical_path": "docs/engineering/critical_path.md"
}
```

### §4.3 變更權責

| 檔 | 寫入者 | 規則 |
|:---|:-------|:-----|
| `.triz-state.json` | 各 triz-* skill 經由 `triz-router` | 集中變更，避免 race |
| `.tr-state.json` | `tr-router` + 各 tr-* skill | 集中變更 |
| `session-{step}-*.md` | 該 step 的 skill / agent | append-only，timestamp 標記 |

---

## §5 Session Blackboard 規範

詳見 DK-03 §8。本節補充與 schema 相關的部分：

### §5.1 Per-step 黑板檔對應 entity

| 黑板檔 | 對應產出 entity | 下游消費 |
|:-------|:--------------|:--------|
| `session-step0-*.md` | Problem + 5Why chain | Step 1 邊界定義 |
| `session-step1-*.md` | FA 圖 + SF 診斷 | Step 2 參數映射輸入 |
| `session-step2-tc{N}-*.md` | TC + 候選方向（per TC 一份）| Step 3 TC worker 輸入 |
| `session-step3-tc{N}-*.md` | PC + Px + 分離 + SF + Solution | Step 3b SIM cell 輸入 |
| `session-step3b-sim-*.md` | SIM 矩陣 | Step 4 輸入 |
| `session-step4-*.md` | ComplexityCheck + TechnicalDebt | Step 5 輸入 |
| `session-step5-*.md` | 工程交付清單 | TR0 概念凍結輸入 |

### §5.2 平行 worker 寫入規則

Step 2 / Step 5 派 N 個 worker 平行：每個 worker 寫**獨立**檔（per-TC 或 per-doc-type），不共寫同一檔。Supervisor 彙整時讀 N 份檔。

### §5.3 衝突偵測

| 衝突 | 偵測點 | 處理 |
|:-----|:-------|:-----|
| 兩 worker 寫同檔 | Supervisor 看到檔已存在 | 重派該 worker，加 explicit filename constraint |
| Schema 不符 | Supervisor 解析失敗 | 重派，prompt 加 schema 引用 |
| Worker 缺輸入 | Worker 自報 BLOCKED | Supervisor 補資料後重派 |

---

## §6 TRIZ Step 5 → TR0 工件交接

### §6.1 工件對應表

| TRIZ 產出（Solution 欄位）| TR 工件 | 落地路徑 |
|:------------------------|:--------|:---------|
| F + 控制方程 + OZ + OT | Work Instruction（WI）| `docs/engineering/work_instructions/WI-NN_*.md` |
| S + 牌號 + 物性 | Material Card（MC）| `docs/engineering/material_cards/MC-NN_*.md` |
| 子系統介面（雙系統 OZ 共界面）| Interface Control Document（ICD）| `docs/engineering/interface_control/ICD-NN_*.md` |
| TechnicalDebt（補丁）| Risk Register 條目 | `docs/engineering/risk_register.md` |
| EvidenceRegistry | Evidence 對照表（embedded in WI） | WI 內 §Evidence Registry |

### §6.2 Step 5 平行產出（DK-03 §6 Step 5 對應）

`triz-wi` skill 在 Step 5 同時派多個 doc-generator agent：

```
triz-wi skill (supervisor)
├─ Agent: WI 產生器 → 寫 WI-NN_*.md
├─ Agent: MC 產生器 → 寫 MC-NN_*.md
├─ Agent: ICD 產生器 → 寫 ICD-NN_*.md
└─ 收尾：黑板協議對齊跨檔引用（MC 餵 WI、ICD 引 MC）
```

### §6.3 TR0 進場條件回扣

TR0 退出條件需要：
- TRIZ session.step4.verdict ∈ {Evolution, Weak Evolution（cci ≤ 0.4）}
- Evidence Registry HIGH+MEDIUM coverage ≥ 50%
- Step 5 工件齊備（WI / MC / ICD 各至少一份且通過 schema 驗證）

→ Step 5 完成 = TR0 進場 = `tr-state.json` 標記對應 subsystem `current_tr: TR0`。

---

## §7 與 Skill / Agent 的 schema 引用

| Skill / Agent | 讀取 schema | 寫入 schema |
|:--------------|:-----------|:-----------|
| `triz-router` | 全部 | `.triz-state.json` 集中變更 |
| `triz-scoping` | Problem | `session-step0-*.md` |
| `triz-model` | Problem | SF + FA → `session-step1-*.md` |
| `triz-contradict`（supervisor）| SF + 自然描述 | TC + SIM → `.triz-state.json` 經 router |
| `triz-analyst`（per-TC worker）| TC（單一）| PC + Px + Solution → `session-step{2,3}-tc{N}-*.md` |
| `triz-verify` | Solution | ComplexityCheck + TechnicalDebt → `session-step4-*.md` |
| `triz-wi` | Solution + ComplexityCheck | WI / MC / ICD → `docs/engineering/` |
| `tr-gate` | TR 退出條件 + 工件 | `gate_reviews/TR{n}_review_*.md` |
| `tr-test-report` | WI 測試項 | `test_reports/V{n}_report_*.md` |
| `tr-fea-assist` | WI + MC | （引導工程師，無檔產出）|
| `tr-dfm` | 各子系統圖面 | `dfm_reviews/{subsystem}_dfm_*.md` |
