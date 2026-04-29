# Auto-TRIZ + TR Harness 使用指南

> 本系統將「**TRIZ 發明性前端**」（Step 0-5）與「**TR 工程執行後端**」（TR1-TR10）串成單一閉環，銜接點為 TR0 概念凍結。
> 完整方法論見 `docs/methodology/DK-01~05`，統一框架（RDP-8）見 `docs/planning/18_flow_contract.md`。

---

## 快速開始

### 入口最簡單：輸入 `/triz` + 問題描述

```
/triz 馬達散熱不足但不能加大體積
```

系統會自動偵測問題類型並路由到適當步驟。流程跑完一輪 TRIZ（Step 0-5）後產生 22 份工程交付物，接著用 `/tr` 進入 gate review。

---

## 指令一覽（12 個）

### TRIZ 發明性前端（7 個）

| 指令 | 步驟 | 用途 |
|:-----|:----:|:-----|
| `/triz` | 入口 | 主入口，自動路由 |
| `/triz-scope` | Step 0 | 問題定向（5Why / KT / CECA） |
| `/triz-model` | Step 1 | 功能建模（FA + SF 診斷 + TC 造句） |
| `/triz-solve` | Step 2+3 | TC/PC/SF 解題（參數映射 + 矩陣 + 分離策略 + 標準解） |
| `/triz-verify` | Step 4 | 驗證 + CCI + 工程交付物 + Gate P CAD 就緒 |
| `/triz-wi` | Step 5 | 從 TRIZ 概念產出 WI/ICD/MC 工程指導書體系（≈22 份文件） |
| `/triz-status` | — | 查看 session 狀態 |

### TR 工程執行後端（5 個 slash + 3 個 Skill-only）

| 指令 | TR 階段 | 用途 |
|:-----|:--------|:-----|
| `/tr` | 儀表板 | TR 入口，顯示 TR0-10 進展並路由 |
| `/tr-gate TRn` | TR1-TR10 | Gate review，逐項檢查退出條件 |
| `/tr-fea WI-nn` | TR1-2 | FEA 設定輔助（材料卡、邊界、網格） |
| `/tr-test Vn` | TR5-9 | 測試報告產生（V1-V14、DVP&R） |
| `/tr-dfm subsystem` | TR2-7 | DFM/DFA 審查 |
| *(Skill: tr-sop)* | TR8-9 | SOP 草稿（從 WI + Process FMEA + Control Plan 合成） |
| *(Skill: tr-spc)* | TR8-10 | SPC/Cpk 計算（Xbar-R, Cp, Cpk, Ppk） |
| *(Skill: tr-ppap)* | TR9-10 | PPAP 18 項文件包組裝 |

---

## 完整流程圖

```
                /triz [問題描述]
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       有矛盾?    有症狀?    功能缺失?
          │           │            │
          ▼           ▼            ▼
     /triz-solve  /triz-scope  /triz-solve
     (TC 路徑)    (Step 0)     --sf-only
                    │
                    ▼
                /triz-model
                (Step 1: FA+SF)
                    │
                    ▼
                /triz-solve
                (Step 2+3: TC/PC/SF)
                    │
                    ▼
                /triz-verify
                (Step 4: 驗證 + Gate P)
                    │
                    ▼
                /triz-wi
                (Step 5: 22 份工程文件)
                    │
            ═══ TR0 概念凍結 ═══
                    │
                    ▼
                /tr (TR 入口)
                    │
        ┌───────────┼─────────────┐
        ▼           ▼             ▼
   /tr-gate     /tr-fea       /tr-test
   /tr-dfm      (FEA 輔助)    (測試報告)
   (gate review)
                    │
                    ▼
              TR1 → TR10 → 量產釋放
```

---

## 三種典型入口路徑

### 路徑 A：有明確矛盾 → 直接 TC 解題

> 「散熱面積要大但體積要小」

```
/triz 散熱面積要大但體積要小
  → 自動路由 /triz-solve（TC 路徑）
  → Step 2: 參數映射 + 矩陣查表
  → Step 3: OZ-OT-Px + PC + 分離策略 + SF 標準解
  → /triz-verify → /triz-wi → TR0
```

### 路徑 B：問題症狀（需先挖根因）

> 「馬達爬坡時異音」

```
/triz 馬達爬坡時異音
  → 自動路由 /triz-scope（Step 0）
  → 5Why → KT Is/IsNot → CECA
  → /triz-model → /triz-solve → /triz-verify → /triz-wi
```

### 路徑 C：功能缺失無副作用 → SF-only 快車道

> 「電池缺少溫度監控功能」

```
/triz 電池缺少溫度監控功能
  → /triz-solve --sf-only
  → 直接匹配 76 標準解
  → /triz-verify
```

---

## 每步驟的輸入 / 輸出

### Step 0 `/triz-scope`

| | 內容 |
|:--|:-----|
| 輸入 | 問題症狀描述 |
| 工具 | 5Why（必做）→ KT Is/IsNot（有對照組）→ CECA（根因仍模糊） |
| 輸出 | 子系統 + 根因假設 + TC 假設 + OZ/OT 候選 |
| KB | 無需 |

### Step 1 `/triz-model`

| | 內容 |
|:--|:-----|
| 輸入 | Step 0 產出 / 使用者直接描述的子系統 |
| 工具 | 組件交互圖 → SF 模型建構 → 改善/惡化造句 |
| 輸出 | 組件交互圖 + SF 診斷 + 對應到 39 參數的 TC 造句 |
| KB | 無需 |

### Step 2+3 `/triz-solve`

| | 內容 |
|:--|:-----|
| 輸入 | Step 1 的改善/惡化描述 |
| 工具 | 參數映射 → 矩陣查表 → 原理排序 → OZ-OT-Px → PC → 分離策略 → SF 標準解 |
| 輸出 | 解法方案（F/S/OZ/OT + 分離策略 + 標準解編號 + Evidence Registry） |
| KB | **全量內嵌**（39 參數 + 矛盾矩陣 + 40 原理 + 4 大分離 + 76 標準解） |

### Step 4 `/triz-verify`

| | 內容 |
|:--|:-----|
| 輸入 | Step 3 的解法方案 |
| 工具 | Px 分離驗證 → Evidence 覆蓋率 → 四問複雜度（CCI）→ 補丁/進化判定 → 新 TC 偵測 → 工程規格書 → **Gate P CAD 就緒** |
| 輸出 | 進化/補丁判定 + 工程規格書 + 驗證計畫 + Gate P Go/Conditional/No-Go |
| KB | 無需 |

### Step 5 `/triz-wi`

| | 內容 |
|:--|:-----|
| 輸入 | Step 4 的工程規格書 |
| 工具 | 子系統分類 → 框架文件 → WI 並行產出 → ICD/MC 並行產出 |
| 輸出 | 22 份工程文件（4 框架 + 7 WI + 4 ICD + 6 MC + 1 KC List） |
| 輸出位置 | `docs/engineering/`（首次執行時建立） |

### TR1-TR10 `/tr-gate TRn`

| | 內容 |
|:--|:-----|
| 輸入 | 對應 TR 階段的交付物 + WI/ICD/MC |
| 工具 | 退出條件 checklist 比對 + 風險評估 |
| 輸出 | Gate Review 報告 → `docs/engineering/gate_reviews/` |

---

## 知識庫注入策略

### 全量內嵌（5 個 KB 自動載入到 triz-contradict）

```
triz-contradict SKILL.md 已內嵌：
├── 39 工程參數                  (~1,500 tokens) — 參數映射用
├── 39×39 矛盾矩陣                (~15,000 tokens) — 矩陣查表用
├── 40 發明原理                  (~4,000 tokens) — 原理具體化用
├── 4 大分離原則                 (~1,000 tokens) — 分離策略選擇用
└── 76 Su-Field 標準解            (~5,000 tokens) — SF 匹配用
```

| 分析 | 結論 |
|:-----|:-----|
| 總 KB token | ~26,500 |
| 200K context 占比 | ~13% |
| 替代方案（RAG/多次 Read） | 增加延遲、推理可能斷鏈 |

→ **13% context 換零延遲全量可用**，不採用 RAG。

---

## Session 與狀態管理

### 兩層狀態

| 層級 | 檔案 | 內容 | 寫入時機 |
|:-----|:-----|:-----|:---------|
| **TRIZ session** | `.claude/context/triz/.triz-state.json` | Step 0-5 結構化數據 | 每步完成後更新 |
| **TR project** | `.claude/context/triz/.tr-state.json` | TR0-10 gate 進展 | TR0 凍結時建立 |
| **人類可讀報告** | `.claude/context/triz/session-{id}.md` | 每步完整 markdown 分析 | **每步完成後即時追加** |

### Context 規範性檔

| 檔案 | 角色 | 消費者 |
|:-----|:-----|:------|
| `BLACKBOARD_PROTOCOL.md` | Multi-agent fan-out 讀寫規則 | triz-contradict supervisor + triz-analyst worker |
| `session-template.md` | Session 報告模板 | 各 step skill 追加用 |
| `schema/triz-state.schema.md` | `.triz-state.json` schema 定義 | skill（人類讀）+ backend Pydantic（程式碼鏡像） |
| `archive/` | 過往 session 歸檔 | — |

### 中斷與恢復

報告檔（`session-{id}.md`）每步完成即落地，中途中斷不會丟資料。下次回來：

```
/triz-status        # 查看走到哪一步
/triz {問題}        # 開新 session（舊的自動歸檔）
```

---

## Agent

| Agent | 模型 | 何時被呼叫 |
|:------|:-----|:----------|
| `triz-analyst` | Opus | Step 2 多 TC 並行（fan-out 模式）；現況下 main 通常 inline 跑，agent 為未來擴展契約 |

---

## RDP-8 統一框架

```
P0 SCOPE  → P1 MAP   → P2 RESOLVE → P3 SPECIFY  ║ P4 PROVE → P5 BUILD → P6 HARDEN → P7 SCALE
[triz-scope] [triz-model] [triz-solve] [triz-verify+wi] ║  [tr-gate TR1-TR4] [TR5-TR6] [TR7-TR8] [TR9-TR10]
                                            G3 概念凍結 (TR0)
```

每個 Phase 消除恰好一種不確定性。Gate 3 是分水嶺：之前由 TRIZ 引擎驅動，之後由 TR 引擎驅動。完整定義見 `docs/planning/18_flow_contract.md`。

### 與國際標準對應

- **TR** = Technology Review（產品開發里程碑）— 結構上接近 VDA MLA (ML0-ML7)
- **品質交付物** 對齊 APQP（FMEA、Control Plan、PPAP）
- 案例參考：`docs/engineering/tr_gate_framework.md`

---

## 內容位置邊界（重要）

| 內容性質 | 存放位置 | 消費者 |
|:---------|:---------|:------|
| Session 過程記錄 | `.claude/context/triz/session-*.md` | Skill（跨步傳遞） |
| 流程狀態 JSON | `.claude/context/triz/.{triz,tr}-state.json` | Skill（狀態機，**禁手動編輯**） |
| 工程交付物（WI/ICD/MC）| `docs/engineering/` | **工程師（人）** |
| Gate Review 報告 | `docs/engineering/gate_reviews/` | 工程師 |
| 測試 / DFM 報告 | `docs/engineering/{test_reports,dfm_reviews}/` | 工程師 |
| 方法論知識 | `docs/methodology/` 或 `knowledge/triz/` | Skill（參考） |

→ **Skill 產出 + Skill 消費** 進 `.claude/context/`；**Skill 產出 + 人消費** 進 `docs/engineering/`。

---

## 專案結構

```
RD_copilot_system/
├── .claude/                        # Claude Code harness
│   ├── CLAUDE.md                   # 專案指令（SSOT）
│   ├── USAGE.md                    # ← 本文件
│   ├── settings.json               # 權限設定
│   ├── agents/triz-analyst.md      # 1 個 agent
│   ├── commands/                   # 12 個 slash commands
│   ├── skills/                     # 14 個 Skills
│   │   ├── triz-router/            # 入口路由
│   │   ├── triz-scoping/           # Step 0
│   │   ├── triz-model/             # Step 1
│   │   ├── triz-contradict/        # Step 2+3（KB 全內嵌）
│   │   ├── triz-verify/            # Step 4 + Gate P
│   │   ├── triz-wi/                # Step 5
│   │   ├── tr-router/              # TR 入口
│   │   ├── tr-gate/                # TR1-10 gate review
│   │   ├── tr-fea-assist/          # FEA 輔助
│   │   ├── tr-test-report/         # 測試報告
│   │   ├── tr-dfm/                 # DFM/DFA
│   │   ├── tr-sop/                 # SOP 草稿
│   │   ├── tr-spc/                 # SPC/Cpk
│   │   └── tr-ppap/                # PPAP 文件包
│   └── context/triz/               # Session 狀態 + 規範文件
│       ├── .triz-state.json        # TRIZ session 狀態
│       ├── .tr-state.json          # TR gate 進展
│       ├── session-*.md            # 各 session 報告
│       ├── BLACKBOARD_PROTOCOL.md  # multi-agent 契約
│       ├── session-template.md     # 報告模板
│       ├── schema/                 # state JSON schema
│       └── archive/                # 過往 session
│
├── knowledge/triz/                 # TRIZ 靜態 KB（5 份）
│   ├── 01_39_parameters.md
│   ├── 02_contradiction_matrix.md
│   ├── 03_40_principles.md
│   ├── 04_separation_principles.md
│   └── 05_76_standard_solutions.md
│
├── docs/
│   ├── methodology/                # DK-00~05 + auto_triz_strategy + UML
│   ├── engineering/                # 工程交付物（runtime 產出）
│   │   ├── work_instructions/      # WI-01~07
│   │   ├── interface_control/      # ICD-01~04
│   │   ├── material_cards/         # MC-01~06
│   │   ├── gate_reviews/           # tr-gate 輸出
│   │   ├── test_reports/           # tr-test 輸出
│   │   ├── dfm_reviews/            # tr-dfm 輸出
│   │   └── tr_gate_framework.md    # TR1-10 退出條件
│   ├── research/                   # 研究素材 + UAT + 推理拆解
│   │   ├── interview/
│   │   ├── presentation/
│   │   ├── uat/
│   │   └── triz_reasoning_walkthrough_*.md
│   ├── planning/                   # 規劃文件（含 RDP-8 flow contract）
│   └── pages/                      # 對外文件頁
│
├── backend/                        # Python harness（鏡像 .claude 跑 skill）
├── supabase/                       # 資料庫 schema
├── templates/                      # 文件模板
└── README.md
```

---

## 不適用 TRIZ 的情況

| 情況 | 替代工具 |
|:-----|:---------|
| 連系統都描述不了 | Design Thinking / JTBD |
| 純最佳化（無矛盾） | DOE / 田口 / ML |
| 純軟體架構問題 | Axiomatic Design / DDD |
| 商業模式 / 市場策略 | 無物理參數，TRIZ 無法著力 |

---

## 故障排除

| 症狀 | 可能原因 | 處理 |
|:-----|:---------|:-----|
| `/triz` 沒有路由到正確 step | session state 殘留 | `/triz-status` 查看狀態，必要時手動歸檔舊 session |
| TC 造句一直不通過 | improve/worsen 對應不到 39 參數 | 退回 `/triz-scope` 重做 5Why |
| Step 4 判定 Conscious Patch | CCI > 0.55 | 回 Step 3 重新挑分離策略，或記錄技術債繼續 |
| Step 4 判定 No-Go | Evidence < 50% | 補強 Evidence Registry（datasheet / FEA / 文獻） |
| Gate P 卡 CAD = HIGH | 結構複雜度高 | 拆子系統並行進 TR1-TR2 |
| TR1 阻塞 | 風險登記冊有 HIGH | 對應 R-XXX 解除（FEA 模擬 / 實測 baseline） |

---

## 參考文件

- 方法論：`docs/methodology/DK-01~05`
- 統一框架：`docs/planning/18_flow_contract.md`
- 案例 walkthrough：`docs/research/triz_reasoning_walkthrough_ebike_mid_drive_coaxial.md`
- TR 框架：`docs/engineering/tr_gate_framework.md`
- 策略 SSOT：`docs/methodology/auto_triz_strategy.md`
