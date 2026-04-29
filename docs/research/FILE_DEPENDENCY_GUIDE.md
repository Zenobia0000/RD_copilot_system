# Engineering Deliverables — 檔案相依與閱讀導引

> **適用對象**: 接手本專案的 RD / 系統工程師 / PM / QA
> **建立日期**: 2026-04-29
> **TRIZ Session 範例**: 2026-04-28-1500-eBike-MidDrive-Coaxial
> **目的**: 一頁看懂 `docs/engineering/` 與 `.claude/context/triz/` 內所有檔案的角色、相依與使用順序，避免新進工程師亂找檔。

---

## 0. 為什麼有這份文件

本專案採用 **Auto-TRIZ + TR Gate** 框架。從 TRIZ 概念到量產釋放會產出兩類檔案：

- **`docs/engineering/`**：工程師可直接使用的設計/驗證/品保交付物（22 份起跳）。
- **`.claude/context/triz/`**：Skill 之間傳遞的工作記憶（state、推理過程）。

兩個目錄**同源**（同一個 TRIZ session）但**讀者不同、修改規則不同**。本文件把這層映射說清楚。

---

## 1. 兩大目錄全景圖

```
┌────────────────────── 工作記憶（Skill 寫、Skill 讀） ──────────────────────┐
│  .claude/context/triz/                                                    │
│  ├── session-{date}-{topic}.md   完整 TRIZ 推理逐字稿（Step 1-5）         │
│  ├── .triz-state.json            TRIZ 狀態機（Step 0-5 進度 + 產出清單） │
│  ├── .tr-state.json              TR 狀態機（TR0-TR10 工程進度 + 子系統）│
│  ├── BLACKBOARD_PROTOCOL.md      多 agent fan-out 黑板協議               │
│  ├── schema/triz-state.schema.md State JSON schema 定義                  │
│  └── session-template.md         模板                                    │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ Step 5 完成時
                                   │ 由 triz-wi skill 一次性產出 22 檔
                                   ▼
┌────────────────────── 工程交付物（Skill 寫、人讀） ────────────────────────┐
│  docs/engineering/                                                       │
│  ├── README.md                   入口 + 系統架構圖 + 角色閱讀指引       │
│  ├── FILE_DEPENDENCY_GUIDE.md    本檔（檔案相依導引）                   │
│  ├── tr_gate_framework.md        TR0-TR10 Gate 退出條件權威定義         │
│  ├── critical_path.md            WI 依賴 DAG + 關鍵路徑時程             │
│  ├── risk_register.md            R-001~R-NNN 風險清單（掛 TR Gate）     │
│  ├── kc_list.md                  Key Characteristics 30 項（串 SPC/PPAP）│
│  ├── work_instructions/          WI-NN（設計 / 整合 / 橫切 三類混合）   │
│  ├── interface_control/          ICD-NN（跨子系統介面）                 │
│  ├── material_cards/             MC-NN（材料規格 + FEA 輸入）           │
│  ├── gate_reviews/               TR Gate 通過記錄（tr-gate skill 產出） │
│  ├── dfm_reviews/                DFM 審查報告（tr-dfm skill 產出）       │
│  └── test_reports/               V1-V14 測試報告（tr-test skill 產出）   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. `.claude/context/triz/` — 工作記憶層（3 個關鍵檔）

| 檔案 | 角色 | 給誰讀 | 修改者 |
|:-----|:-----|:------|:------|
| `session-{date}-{topic}.md` | TRIZ 推理逐字稿（FA→SF→TC→PC→Px→CCI→WI 全程） | 想理解「為什麼選這個方案」的工程師、Lead Reviewer | **凍結**（產出後不修改） |
| `.triz-state.json` | TRIZ 狀態機，記載 Step 0-5 進度、TC 數、CCI、22 檔產出清單 | TRIZ skills（triz-router/scoping/model/contradict/verify/wi） | 只能由 TRIZ skill 修改 |
| `.tr-state.json` | TR 工程執行狀態機，6 個 subsystem × 11 個 TR Gate 進度 | TR skills（tr-router/gate/fea/test/dfm/sop/spc/ppap） | 只能由 TR skill 修改 |

### 三檔之間的關係

```
session-*.md ── 法理依據（人類可讀的故事）
       │ 結構化萃取
       ▼
.triz-state.json ── Skill 可讀的狀態 + 落地清單（output_dir = docs/engineering/）
       │ Step 5 完成時，把 SHA-256 hash 寫入 .tr-state.json
       ▼
.tr-state.json ── 接手後的 TR Phase 進度（triz_state_hash 防 TRIZ 結果偷改）
```

### 讀懂 `.triz-state.json` 的關鍵欄位

```json
{
  "session_id": "...",
  "current_step": "step5",          ← 當前進度
  "path": "tc-main",                 ← 解題路徑（tc-main / sf-only / multi-tc）
  "step4": {
    "verdict": "evolution",          ← 必須是 evolution 才能產 WI
    "cci_verdict": "Weak Evolution", ← Weak = 部分項目要實驗補強
    "observation_items": [...]       ← 自動轉成 risk_register 的 R-NNN
  },
  "step5": {
    "wi_files": [...],               ← 22 檔產出清單
    "icd_files": [...],
    "mc_files": [...],
    "output_dir": "docs/engineering/"
  }
}
```

### 讀懂 `.tr-state.json` 的關鍵欄位

```json
{
  "current_tr": "TR0",                ← 整體 TR 進度
  "triz_state_hash": "ab4ae09...",    ← 防 TRIZ 結果竄改
  "subsystems": {
    "halbach_motor": {
      "current_tr": "TR0",            ← 子系統 TR 進度（可不同步）
      "next_target": "TR1",
      "wi": "WI-01"                   ← 對應 docs/engineering/ 的哪份 WI
    }
  },
  "tr_gates": {
    "TR1": {
      "blocking_risks": ["R-001"]     ← 直接引用 risk_register.md
    }
  }
}
```

---

## 3. `docs/engineering/` — 工程交付物層（22 檔起跳，動態擴張）

### 3.1 四層架構

```
Layer 0 框架層（4 檔，本案固定）— 給 PM/系統工程師
├── README.md
├── tr_gate_framework.md
├── critical_path.md
└── risk_register.md

Layer 1 規範層（11 檔，動態）— 給工程師執行
├── work_instructions/        7 份 WI（混合三類，見 §4）
└── interface_control/        4 份 ICD（介面合約）

Layer 2 資源層（6 檔，動態）— 給採購/材料工程師
└── material_cards/           6 份 MC（材料 spec + FEA 輸入）

Layer 3 量測層（1 檔）— 串接所有層到品質系統
└── kc_list.md                30 個 KC（Critical 17 / Major 10 / Minor 1+2）

Layer 4 後續執行層（gate_reviews/ dfm_reviews/ test_reports/）
                              由 TR skills 增量產出，TR Phase 推進時才有
```

### 3.2 數量決定機制（動態）

| 類別 | 數量公式 | 觸發條件 | 本案結果 |
|:-----|:---------|:---------|:---------|
| WI | 偵測到的設計域數 + 2 強制（test、procurement） | TRIZ Step 3 解法的 F/S 模式匹配 | **7** |
| ICD | WI-structural 與其他 WI 的交叉介面對 | 多子系統共享物理空間 | **4** |
| MC | `evidence_registry` 中所有材料項目去重 | TRIZ 解法引用的材料 | **6** |
| KC | WI 設計輸入 HIGH + ICD GD&T + Risk HIGH | 萃取 + 等級判定 | **30** |

> 同一套 skill 跑工業馬達可能 6 WI / 3 ICD / 4 MC；跑消費電子可能 4 WI / 2 ICD / 3 MC。**沒有固定上下限**。

---

## 4. WI 為什麼「種類混合」— 三類正交容器

WI 編號連續（01~07）但**性質正交**，分三類：

### 4.1 設計型（Design）— 對應 TRIZ TC 解
| WI | 域 | TRIZ 來源 | 觸發條件 |
|:---|:---|:---------|:---------|
| WI-01 馬達 | 電磁 | TC-B (功率密度 vs 重量) | F=磁/電磁 + S=磁鐵/線圈 |
| WI-02 齒輪 | 機械 | TC-C (噪音 vs 複雜度) | F=機械 + S=齒輪/軸承 |
| WI-03 熱管理 | 熱 | TC-A (散熱 vs 體積) | F=熱 + S=PCM/散熱 |
| WI-05 Drive Board | 電子 | 無 TC（被動配合） | S=PCB/MCU/感測器 |

### 4.2 整合型（Integration）— 系統封裝
| WI | 角色 | 觸發條件 |
|:---|:-----|:---------|
| WI-04 Coaxial Housing | 把所有設計型 WI 的包絡塞進同一個殼 | 多子系統交互 + S=外殼/框架 |

### 4.3 橫切型（Cross-cutting）— 流程文件，**永遠產出**
| WI | 角色 |
|:---|:-----|
| WI-06 V1-V14 測試與驗證 | 跨所有設計型 WI 的驗證流程 |
| WI-07 採購 | 跨所有 MC 的採購流程 |

### 4.4 看到 WI 編號時的判讀法
讀檔內 §溯源表：
- 有 `TC-N` → 設計型
- 多 TC + 包絡 → 整合型
- 無 TC → 橫切型

---

## 5. 跨檔引用關係（誰 require 誰）

```
WI-01 馬達 ──┬──► MC-01 NdFeB, MC-02 SMC, MC-03 CFRP
              ├──► ICD-01 (馬達↔殼)
              └──► R-001, R-004, R-005, R-008（風險回鎖）

WI-03 熱  ──┬──► MC-04 Al, MC-05 Cu, MC-06 PCM
              ├──► ICD-01
              └──► R-008, R-010

WI-02 齒  ──┬──► ICD-02
              └──► R-002, R-009

WI-04 殼 ◄── 整合 WI-01/02/03 包絡 ──► ICD-01, ICD-02, ICD-04
                                       └──► R-006

WI-05 PCB ──► ICD-03 ──► R-008

WI-06 測試 ──► 消費 WI-01~05 的 KC（V1-V14 對應 KC-001~030）
WI-07 採購 ──► 消費 6 份 MC

kc_list.md       ◄── 從 WI/ICD 反向萃取（Critical/Major/Minor 分級）
critical_path.md ◄── 用 DAG 排序所有 WI（時程依賴）
risk_register.md ◄── 每個 R-NN 掛在 WI 上 + 標 TR Gate blocking
tr_gate_framework.md ◄── 每個 TR 退出條件引用 WI/ICD/MC/KC
README.md        ◄── 整份目錄 + 角色閱讀路徑入口
```

### 反向：哪個 TR Gate 用到哪些檔

| TR Gate | 必要檔案 |
|:--------|:---------|
| TR0 概念凍結 | session-*.md + `.triz-state.json` (verdict=evolution) |
| TR1 可行性 | WI-01~03 + 6 MC + risk_register R-001/002/004 |
| TR2 參數鎖定 | 4 ICD + 供應商選定 + risk_register R-003/005 |
| TR3 詳細設計 | WI-04 完整 CAD + Design FMEA |
| TR5 Alpha 原型 | WI-07 物料到位 + 治工具 |
| TR6 Alpha 驗證 | WI-06 V1-V14 + test_reports/ |
| TR7 Beta 設計 | dfm_reviews/ + Process FMEA + Control Plan |
| TR10 量產釋放 | kc_list 全 Critical Cpk≥1.33 + PPAP 等效文件包 |

---

## 6. 編號系統與命名規則

| 前綴 | 全名 | 撰寫者 | 範例 |
|:-----|:-----|:-------|:-----|
| WI-NN | Work Instruction | triz-wi skill | WI-01_halbach_motor.md |
| ICD-NN | Interface Control Document | triz-wi skill | ICD-01_motor_to_housing.md |
| MC-NN | Material Card | triz-wi skill | MC-01_ndfeb_n42sh.md |
| KC-NNN | Key Characteristic | triz-wi skill（kc_list 內列項） | KC-001 Air gap 同心度 |
| R-NNN | Risk | triz-wi skill（risk_register 內列項） | R-001 Halbach 增益 |
| TRn | Technology Review Gate | 系統定義（tr_gate_framework） | TR0~TR10 |
| C-NNN | Evidence | triz-contradict skill | C-B001 (NdFeB B_r) |
| TC-X | Technical Contradiction | triz-model skill | TC-A/B/C |
| V-NN | Verification Test | triz-wi skill（WI-06 內列項） | V1~V14 |

**編號規則**：前綴標角色，數字標順序。**前綴決定意義**，不能僅靠數字猜（WI-01 ≠ TR1 ≠ KC-001）。

---

## 7. 場景化閱讀指引

### 7.1 第一次接觸專案（30 分鐘上手）
1. 本檔 §1-3（全景圖）
2. `README.md`（系統架構圖 + 角色入口）
3. `tr_gate_framework.md`（產品開發階段認識）

### 7.2 接手單一子系統（如馬達 EE）
1. `WI-01_halbach_motor.md`（看 §溯源表理解設計依據）
2. `MC-01/02/03`（材料 spec + FEA 輸入）
3. `ICD-01_motor_to_housing.md`（介面約束）
4. `risk_register.md` 過濾「負責 WI = WI-01」
5. `.tr-state.json` 看 `subsystems.halbach_motor` 當前進度

### 7.3 PM 追蹤專案進度
1. `.tr-state.json`（看 current_tr + 6 subsystems）
2. `critical_path.md`（DAG + 預估時程）
3. `risk_register.md` 過濾 H/H 致命風險
4. `gate_reviews/`（最近一次 gate review 結論）

### 7.4 QA 準備 Gate Review
1. `tr_gate_framework.md` 找該 TR 的退出條件
2. `kc_list.md` 過濾該 TR 涉及的 KC
3. `test_reports/` V-test 結果
4. 執行 `/tr-gate TRn`（skill 自動產出 review 報告）

### 7.5 想知道「為什麼選這個方案」
1. `WI-NN` §溯源表（Halbach → 原理 #14、SMC → 標準解 2.4.5）
2. `session-{date}-{topic}.md` Step 2-3 區段（完整推理）
3. `.triz-state.json` step3.solutions（結構化結果）

### 7.6 採購要下單長交期物料
1. `WI-07_procurement.md`
2. `critical_path.md`「並行機會」區段
3. 6 份 `MC-NN`（供應商評估要點）

---

## 8. 變更與維護注意事項

### 8.1 不可手動編輯的檔案
- `.triz-state.json` / `.tr-state.json` — **只能由 TRIZ/TR skill 修改**，手改會破壞 hash 校驗
- `session-*.md` — **凍結歷史檔**，產出後不修改（如要重跑就開新 session）

### 8.2 修改 WI/ICD/MC 的影響
| 修改項 | 必須同步更新 |
|:--------|:--------------|
| WI 名稱/路徑 | README、kc_list、risk_register、critical_path、tr_gate_framework、ICD「相關 WI」、MC「適用 WI」、`.triz-state.json` `step5.wi_files`、`.tr-state.json` `subsystems[*].wi`，共 220+ 處引用 |
| ICD 配合規格 | 雙方 WI 負責人簽核 + risk_register 影響評估 |
| MC 物性數值 | 引用該 MC 的 WI 全部須重跑 FEA |
| KC 規格/公差 | Control Plan、SPC、PPAP 同步 |

### 8.3 新增 WI 的時機
- 新增子系統（如 firmware、外觀件） → 新增設計型 WI，編號連續遞增
- 切出獨立流程（如 EOL 測試） → 新增橫切型 WI

### 8.4 後續產出檔（增量寫入）
| 檔案 | 產出時機 | 由誰寫 |
|:-----|:---------|:------|
| `gate_reviews/TR{n}_review.md` | 每次 `/tr-gate TR{n}` | tr-gate skill |
| `test_reports/V{nn}_report.md` | 每次 `/tr-test V{nn}` | tr-test skill |
| `dfm_reviews/{subsystem}_dfm.md` | 每次 `/tr-dfm {subsystem}` | tr-dfm skill |
| `kc_list.md` 增列 | TR1 後 KC 細化、TR6 後實測值補充 | 工程師人工 + skill 輔助 |

### 8.5 「Weak Evolution」狀態的特殊處理
本案 CCI=0.3125（Weak Evolution）→ 部分項目（C-B002 Halbach FEA、C-B004 CFRP、C-C002 HPR50 噪音）需實驗補強。所有 WI 內標記「未來改進方向」，TR1 Gate 必須關閉 R-001/002/004。詳見 `risk_register.md`。

---

## 9. 快速參考表

| 你想知道... | 看哪個檔 |
|:------------|:---------|
| 整個系統長什麼樣 | `README.md` 系統架構圖 |
| 我這個子系統怎麼做 | `work_instructions/WI-NN_*.md` |
| 介面長怎樣、公差是什麼 | `interface_control/ICD-NN_*.md` |
| 材料 spec、FEA 怎麼設 | `material_cards/MC-NN_*.md` |
| 哪些尺寸要管制 | `kc_list.md` |
| 為什麼選這個方案 | `WI` §溯源 + `session-*.md` |
| 我這 Gate 過了沒 | `tr_gate_framework.md` + `.tr-state.json` |
| 哪些風險要追蹤 | `risk_register.md` |
| 排程跟關鍵路徑 | `critical_path.md` |
| TRIZ 解出來是什麼 | `.triz-state.json` `step3.solutions` |
| TR 整體進度 | `.tr-state.json` `current_tr` |

---

## 10. 相關 Slash Command

| 指令 | 用途 | 對應狀態檔 |
|:-----|:-----|:----------|
| `/triz-status` | 看 TRIZ session 進度 | `.triz-state.json` |
| `/tr` | 看 TR 整體儀表板 + 路由 | `.tr-state.json` |
| `/tr-gate TR{n}` | 跑 Gate Review | 寫入 `gate_reviews/` |
| `/tr-fea WI-{nn}` | FEA 設定輔助 | 引用 `MC-NN` |
| `/tr-test V{nn}` | 產出測試報告 | 寫入 `test_reports/` |
| `/tr-dfm {subsystem}` | DFM 審查 | 寫入 `dfm_reviews/` |
| `/tr-spc KC-{id}` | SPC/Cpk 計算 | 引用 `kc_list.md` |
| `/tr-ppap check/assemble` | PPAP 文件包組裝 | 跨多檔聚合 |

---

**維護者**: 接手本專案的 RD Lead
**更新觸發**: 新增/重新命名 WI/ICD/MC、TR Gate 框架調整、新 skill 加入時更新本檔。
