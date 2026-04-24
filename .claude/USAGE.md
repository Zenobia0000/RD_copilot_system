# Auto-TRIZ Harness 使用指南

## 快速開始

輸入 `/triz` + 你的問題描述，系統自動路由到適當步驟。

```
/triz 馬達散熱不足但不能加大體積
```

---

## 指令一覽

| 指令 | 功能 | 何時用 |
|:-----|:-----|:------|
| `/triz` | 主入口，自動路由 | 任何 TRIZ 問題的起點 |
| `/triz-scope` | Step 0: 問題定向 | 知道不滿意但說不出 trade-off |
| `/triz-model` | Step 1: 功能建模 | 需要建立系統功能分析和 SF 診斷 |
| `/triz-solve` | Step 2+3: 解題 | 有明確的技術矛盾要解 |
| `/triz-verify` | Step 4: 驗證 | 有解法方案需要驗證品質 |
| `/triz-status` | 查看進度 | 中途想看 session 走到哪一步 |

---

## 三種入口路徑

### 路徑 A：有明確矛盾

> 「散熱面積要大（導熱好）但體積要小（空間限制）」

```
/triz 散熱面積要大但體積要小
  → 自動路由至 /triz-solve
  → Step 2: 參數映射（面積 vs 體積）→ 矩陣查表 → 候選原理
  → Step 3: OZ-OT → PC → 分離策略 → SF 標準解
  → /triz-verify 驗證
```

### 路徑 B：有問題症狀但不知根因

> 「馬達爬坡時異音」

```
/triz 馬達爬坡時異音
  → 自動路由至 /triz-scope
  → Step 0: 5Why 挖根因 → KT 鎖定 OZ/OT
  → /triz-model 建功能模型
  → /triz-solve 解題
  → /triz-verify 驗證
```

### 路徑 C：功能缺失無副作用

> 「電池缺少溫度監控功能」

```
/triz 電池缺少溫度監控功能
  → 自動路由至 /triz-solve --sf-only
  → SF-only 快速通道：直接匹配 76 標準解
  → /triz-verify 驗證
```

---

## 完整流程圖

```
                        /triz [問題描述]
                              │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
              有矛盾？    有症狀？    功能缺失？
                 │          │           │
                 ▼          ▼           ▼
           /triz-solve  /triz-scope  /triz-solve
           (TC 路徑)    (Step 0)     --sf-only
                         │
                         ▼
                    /triz-model
                    (Step 1: FA+SF)
                         │
                         ▼
                    /triz-solve
                    (Step 2+3)
                         │
                         ▼
                    /triz-verify
                    (Step 4: 驗證)
                         │
                    ┌────┴────┐
                    ▼         ▼
                 進化       補丁
              (完成!)    (記錄技術債)
```

---

## 每步驟的輸入/輸出

### Step 0: `/triz-scope`

| | 內容 |
|:--|:-----|
| **輸入** | 問題症狀描述 |
| **工具** | 5Why（必做）→ KT Is/IsNot（有對照組時）→ CECA（根因仍模糊時）|
| **輸出** | 子系統 + 根因假設 + TC 假設 + OZ/OT 候選 |
| **KB** | 無需載入 |

### Step 1: `/triz-model`

| | 內容 |
|:--|:-----|
| **輸入** | Step 0 產出 或 使用者直接描述的子系統 |
| **工具** | 組件交互圖 → SF 模型建構 → 改善/惡化造句 |
| **輸出** | 組件交互圖 + SF 診斷 + TC 造句 |
| **KB** | 無需載入 |

### Step 2+3: `/triz-solve`

| | 內容 |
|:--|:-----|
| **輸入** | Step 1 的改善/惡化描述 |
| **工具** | 參數映射 → 矩陣查表 → 原理具體化 → OZ-OT-Px → PC → 分離 → SF |
| **輸出** | 解法方案（F/S/OZ/OT + 分離策略 + 標準解編號）|
| **KB** | 39 參數(內嵌) + 40 原理(內嵌+RAG) + 分離原則(內嵌) + 矛盾矩陣(RAG) + 76 標準解(RAG) |

### Step 4: `/triz-verify`

| | 內容 |
|:--|:-----|
| **輸入** | Step 3 的解法方案 |
| **工具** | Px 分離驗證 → 四問複雜度判定 → 新 TC 偵測 |
| **輸出** | 進化/補丁判定 + 工程規格書 或 技術債記錄 |
| **KB** | 無需載入 |

---

## 知識庫注入策略

### 全量內嵌（載入 triz-contradict 時自動注入全部 5 個 KB 檔）

```
triz-contradict SKILL.md 已內嵌：
├── 39 工程參數完整表       (~1,500 tokens) — 參數映射用
├── 39x39 矛盾矩陣完整版   (~15,000 tokens) — 矩陣查表用
├── 40 發明原理完整版       (~4,000 tokens) — 原理具體化用
├── 4 大分離原則完整版      (~1,000 tokens) — 分離策略選擇用
└── 76 Su-Field 標準解完整版 (~5,000 tokens) — SF 匹配用
```

### 為什麼全量注入？

| 分析 | 結論 |
|:-----|:-----|
| 總 KB token | ~26,500 tokens |
| Context window | 200,000 tokens |
| 佔比 | ~13% |
| RAG 系統存在嗎？ | 否 — 所謂「RAG」只是 Read tool 讀檔 |
| 全量注入代價 | 低（13% context，一次載入） |
| 全量注入好處 | 零延遲查表、無需多次 Read、推理連貫不中斷 |

**結論：** 13% 的 context 換取零延遲全量可用，是最簡單且最有效的策略。無需 RAG。

---

## Session 管理

### 輸出持久化（兩層機制）

| 層級 | 檔案 | 內容 | 寫入時機 |
|:-----|:-----|:-----|:---------|
| **機器狀態** | `.claude/context/triz/.triz-state.json` | 每步 JSON 結構化數據（completed flag、參數、路由等） | 每步完成後更新 |
| **人類可讀報告** | `.claude/context/triz/session-{session_id}.md` | 每步的完整 markdown 分析輸出 | **每步完成後即時追加** |

### 報告檔逐步追加流程

```
/triz 初始化 → 建立 session-{id}.md（報告頭部）
  │
  Step 0 完成 → 追加 Step 0 區段（5Why/KT/CECA 分析）
  │
  Step 1 完成 → 追加 Step 1 區段（組件交互圖/SF/TC 造句）
  │
  Step 2+3 完成 → 追加 Step 2-3 區段（TC 定義/PC/分離/解法）
  │
  Step 4 完成 → 追加 Step 4 + 工程交付物區段，更新頭部判定
```

**好處：** 即使中途中斷，已完成步驟的完整分析都有檔案記錄。不必等到 Step 4 才落地。

### 中斷與恢復

```
# 中途離開後，下次回來：
/triz resume          # 恢復上次 session
/triz-status          # 查看走到哪一步
```

報告檔已包含中斷前所有完成步驟的輸出，可直接閱讀。

### 多 session

開始新 session 時，舊 session 自動歸檔：
- State: `.triz-state.json` → `session-{old_session_id}-state.json`
- Report: `session-{old_session_id}.md` 保持不動（已是獨立檔案）

---

## Agent 說明

| Agent | 模型 | 何時被呼叫 |
|:------|:-----|:----------|
| `triz-analyst` | Opus | `/triz-solve` 執行時，負責 TC/PC/SF 的分析推理 |

---

## 專案結構

```
auto_triz_x1c01/
├── .claude/                       # Claude Code harness
│   ├── CLAUDE.md                  # 專案指令
│   ├── USAGE.md                   # ← 本文件
│   ├── settings.json              # 權限設定
│   ├── agents/
│   │   └── triz-analyst.md        # TRIZ 分析 agent
│   ├── commands/                  # 6 個 /triz-* 指令
│   ├── skills/                    # 5 個 TRIZ Skills
│   │   ├── triz-router/           # 入口路由
│   │   ├── triz-scoping/          # Step 0
│   │   ├── triz-model/            # Step 1
│   │   ├── triz-contradict/       # Step 2+3 (含 KB 內嵌)
│   │   └── triz-verify/           # Step 4
│   └── context/triz/              # Session 狀態
│
├── docs/
│   ├── auto_triz_strategy.md      # 完整策略框架 (968 行)
│   └── uml/                      # 11 個 UML 流程圖
│
└── triz_knowledge_base/           # TRIZ 靜態參照表
    ├── 01_39_parameters.md        # 39 工程參數
    ├── 02_contradiction_matrix.md # 39x39 矛盾矩陣
    ├── 03_40_principles.md        # 40 發明原理
    ├── 04_separation_principles.md # 4 大分離原則
    └── 05_76_standard_solutions.md # 76 Su-Field 標準解
```

---

## 不適用 TRIZ 的情況

| 情況 | 替代工具 |
|:-----|:---------|
| 連系統都描述不了 | Design Thinking / JTBD |
| 純最佳化（無矛盾） | DOE / 田口 / ML |
| 純軟體架構問題 | Axiomatic Design / DDD |
| 商業模式/市場策略 | 無物理參數，TRIZ 無法著力 |
