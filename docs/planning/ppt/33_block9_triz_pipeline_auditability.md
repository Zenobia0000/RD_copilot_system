# Block 9 Deep-Dive — TRIZ 發明性前端的可審計性

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-29`
**狀態**：`Active`
**用途**：Block 9「TRIZ 流程可審計性」的單頁展開稿，獨立呈現給資深工程師、技術主管、品保 / 審計，補足 Block 3 在前端評分機制的細節。

---

## 1. 這頁要回答的一個問題

> 這套方法論看起來很完整，但它怎麼證明自己**不是包了 TRIZ 名詞的玄學**？

## 2. 一句話 Key Message

> 每個 Step 都有**進場條件、評分公式、Evidence 門檻、出場 Gate** — 全流程不靠經驗直覺，主觀偏見被結構化機制壓制；任何結論都能被反向稽核到原始評分與證據鏈。

## 3. 版面配置建議

```
┌─────────────────────────────────────────────────────────────────┐
│                          頁面標題                                 │
│  TRIZ 前端可審計：每個結論都有公式、門檻、證據鏈                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A. Step Gate 矩陣（橫向 Pipeline）                              │
│                                                                 │
│  S0 → S1 → S2 → S3 → S4 → S5  ═══►  TR0 凍結                   │
│  G0    G1    G2          G3                                     │
│  ┌────┬────┬────┬────┬────┬────┐                                │
│  │產出│公式│門檻│風險│ ...│ ...│                                │
│  └────┴────┴────┴────┴────┴────┘                                │
│                                                                 │
├──────────────────────────────────┬──────────────────────────────┤
│                                  │                              │
│  B. 三層可審計機制                │  C. 風控四道                  │
│                                  │                              │
│  1. 決策鏈透明化                  │  1. Spiral Ascent             │
│  2. 評分公式（4 公式）            │  2. Conscious Patch (技術債)  │
│  3. Evidence Registry (HML)      │  3. 新 TC 偵測               │
│                                  │  4. Gate P No-Go             │
├──────────────────────────────────┴──────────────────────────────┤
│  D. TR0 銜接交付（4 主線 × 22 份）                                │
│  E. eBike 案例實證一行                                           │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 主要內容

### A. Step Gate 矩陣

| Step | 對應 Gate | 核心產出 | Gate 評分/判定 | 出場門檻 | 防範什麼風險 |
|:-----|:---------:|:---------|:---------------|:---------|:-------------|
| **S0** 問題定向 | G0 | 5Why / KT / CECA → 子系統 + OZ/OT + 根因 | 因果鏈閉合（定性） | ≥1 條可操作根因節點 | 解錯問題 |
| **S1** 功能建模 | G1 | 組件交互圖（FA）+ SF 診斷 + 改善/惡化造句 | FA 完整 + SF 三要素齊 | ≥1 條 TC 造句完整對應 39 參數 | 跳過系統理解直接解 |
| **S2** TC + 矩陣 | G2-候選 | 39 參數映射 + 矩陣推薦 + 40 原理排序 | `(關鍵詞×0.4 + 類別×0.15 + 說明×0.25 + 工程對應×0.2)/2` | 映射 ≥ 0.7 + 候選有控制方程 + Evidence ≥ 50% | 矩陣查表結果不可信 |
| **S3** PC + Px + SF | G2-完成 | OZ/OT/Px + PC 造句 + 分離策略 + SF 標準解 | `PxScore = 0.5×Sens + 0.25×Ctrl + 0.25×CausalDirect` | PxScore ≥ 0.60 + 兩 Sens 子分 > 0 + 分離策略 ≥ 0.50 | 挑了不可控/長鏈 Px |
| **S4** 驗證 + CCI | G3-候選 | Px 分離驗證 + 四問複雜度 + 工程規格書 + Gate P | `CCI = 0.30×Q1 + 0.25×Q2 + 0.20×Q3 + 0.25×Q4` | CCI ≤ 0.55 + Evidence ≥ 50% + CAD ≤ MEDIUM | 補丁包成進化、解法臃腫 |
| **S5** WI 產出 | G3-完成 | 22 份工程文件（WI/ICD/MC/KC List） | 子系統域分類完整覆蓋 | schema 通過 + TR0 state 寫入 | 工程文件邊界混亂 |

**Gate 規則**：
- 每個 Gate 是**閘門式判定**（PASS / FAIL / CONDITIONAL），且任一公式分數可獨立稽核
- FAIL 退回**前一個 Step**補強，不退回起點
- CONDITIONAL 需限期補齊特定項目（如 LOW Evidence 補測）

---

### B. 三層可審計機制

#### B-1. 決策鏈透明化

每個 Step 都有**進場條件 → 推理動作 → 評分依據 → 出場條件 → 傳遞物件**五段結構，全部寫進 `.triz-state.json`：

```
.triz-state.json
├── step0: { completed, routing, root_causes, tc_hypothesis }
├── step1: { fa_components, sf_diagnosis, improve_worsen_nl }
├── step2: { tc_definitions, parameter_mappings, principles }
├── step3: { px_candidates, pc_statements, separation_strategies }
├── step4: { px_validation, cci_score, gate_p_decision }
└── step5: { wi_files, icd_files, mc_files, tr0_handoff }
```

→ 稽核者可從任何結論反查到原始評分與證據。

#### B-2. 評分公式（四個強制公式）

| 公式 | 維度 | 防範 |
|:-----|:-----|:-----|
| **參數映射** | 關鍵詞 (0.40) + 類別 (0.15) + 說明 (0.25) + 工程對應 (0.20) | 主觀挑 39 參數 |
| **PxScore** | Sensitivity (0.50) + Controllability (0.25) + CausalDirectness (0.25) | 挑了不可控變數 / 長鏈耦合 |
| **分離策略** | 4 策略 × 3 診斷題（時間 / 空間 / 條件 / 整體局部） | 主觀選分離方式 |
| **CCI** | Q1 結構 (0.30) + Q2 能量 (0.25) + Q3 認知 (0.20) + Q4 演化 (0.25) | 補丁偽裝成進化 |

#### B-3. Evidence Registry（三級門檻）

| Confidence | 來源 | 範例 |
|:-----------|:-----|:-----|
| **HIGH** | Datasheet / Handbook 直接引用 | NIST Cu 熱導率 401 W/mK |
| **MEDIUM** | Peer-reviewed paper / LLM 中信度 | IEEE Trans Magnetics Halbach 增益 |
| **LOW** | LLM 估計 / 待實測 | CFRP tip speed 200 m/s |

**門檻**：HIGH + MEDIUM ≥ 50%，否則 Step 4 強制降級為 Weak Evolution 或 No-Go。

---

### C. 風控四道

| # | 機制 | 觸發條件 | 動作 |
|:--|:-----|:---------|:-----|
| 1 | **Spiral Ascent** | Step 4 偵測到新 TC（解 A → 出現新副作用 B） | 回 Step 1 重新建模，`spiral_iteration++` |
| 2 | **Conscious Patch** | CCI ∈ (0.55, 1.00] | 強制登記技術債（PC 未解 + 觸發條件 + 優先級） |
| 3 | **新 TC 偵測** | Step 4 Phase 4 檢查 | 邊界案例轉 DFM 範疇；獨立新 TC 觸發 Spiral |
| 4 | **Gate P No-Go** | CCI > 0.55 或 Evidence < 50% 或 CAD = HIGH | 阻擋進入 CAD，回 Step 3 重深挖 |

→ 沒有「失敗即丟棄」，只有「失敗即回滾到對應深度」，且**回滾路徑可在 state JSON 重現**。

---

### D. TR0 銜接交付

S5 結束時，4 條主線文件齊備（共 22 份），對應 4 種審計視角：

| 主線 | 數量 | 內容 | 審計用途 |
|:-----|:----:|:-----|:---------|
| **WI** Work Instruction | 7 | 各子系統工程作業指導書（電磁 / 機械 / 熱 / 結構 / 電子 / 測試 / 採購） | 製造可行性審計 |
| **ICD** Interface Control | 4 | 子系統邊界 + 公差 + GD&T | 介面解耦審計 |
| **MC** Material Card | 6 | 材料物性 + Confidence + FEA 輸入 | 物料可信度審計 |
| **Risk Register** | 1（含框架文件 4 份） | 風險登記冊 + 關鍵路徑 + Gate framework | 戰略風險審計 |

**TR0 state 寫入 `.tr-state.json`**，包含 `triz_session_ref` + `state_hash`，TR1-TR10 引擎以此為入口。

---

### E. eBike Mid-Drive Coaxial 案例實證

| 指標 | 數值 | 解讀 |
|:-----|:-----|:-----|
| 參數映射飽和度 | **6/6 全 1.00** | TC-A/B/C 兩端共 6 個 39 參數對應無歧義 |
| Px 候選評分 | A_contact 1.00 / B_r 1.00 / Δδ 0.925 | 三條 TC 的 Px 全 ≥ 0.925，遠超 0.60 門檻 |
| 分離策略覆蓋 | 全空間 1.00 + 整體局部 1.00 / 0.89 / 0.89 | 主+嵌套組合明確 |
| CCI 複雜度指數 | **0.3125**（Weak Evolution）| Q4=0 強訊號，演化方向明確 |
| Evidence 覆蓋率 | **83%** (10/12 HIGH+MEDIUM) | 遠高於 50% 門檻 |
| Gate P 判定 | **Go** ✅ | CCI + Evidence + CAD 三條件 AND 滿足 |
| 工程交付物 | **22 份** | 7 WI + 4 ICD + 6 MC + 4 框架 + 1 KC List |

→ 案例完整推理鏈見 `docs/research/triz_reasoning_walkthrough_ebike_mid_drive_coaxial.md`，每個分數都可反向稽核到原始公式與 Evidence 出處。

---

## 5. 收束陳述

> **「黑箱方法論」與「可審計方法論」的分水嶺，不在於用了 TRIZ 還是別的工具，而在於每個結論能否被反向稽核到原始評分與證據鏈。** 這套系統選的是後者：4 個強制公式 × 3 級 Evidence × 4 道風控 × 22 份交付物 = 任何技術主管或品保稽核都能在 30 分鐘內驗證任一結論的合理性。

---

## 引用文件

- 方法論：`docs/methodology/DK-01--auto-triz-process.md` §3-§8、`DK-04--data-model-and-gate.md`
- 案例：`docs/research/triz_reasoning_walkthrough_ebike_mid_drive_coaxial.md`
- 公式定義：`.claude/skills/triz-contradict/SKILL.md`、`.claude/skills/triz-verify/SKILL.md`
- 對標標準：`docs/planning/27_block3_gate_and_standards.md`（APQP / VDA MLA / TRL 對照）
