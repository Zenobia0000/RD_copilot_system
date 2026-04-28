# Block 4 Deep-Dive — Harness-first 系統架構

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：Block 4「Harness-first 系統架構」的單頁展開稿，可獨立呈現或作為 5 頁 deck 第四頁

---

## 1. 這頁要回答的一個問題

> 這套流程不是只存在概念上——系統主體到底怎麼把它跑起來？

## 2. 一句話 Key Message

> 系統採 harness-first 架構：流程知識活在 markdown skills，Python runtime 負責載入與調度，state 用 filesystem 持久化——讓「流程文件」變成「可執行流程」。

## 3. 版面配置建議

```
┌────────────────────────────────────────────────────────────┐
│                          頁面標題                            │
│  Harness-first：讓流程知識可執行，而不是只停在文件裡            │
├───────────────────────────┬────────────────────────────────┤
│                           │                                │
│  A. 5 層堆疊圖             │  B. 設計原則 + 資料流           │
│                           │                                │
│  ┌─────────────────────┐  │  原則 1: 業務邏輯在 markdown    │
│  │   Interface Layer   │  │  原則 2: Runtime 只做調度       │
│  │   (CLI / HTTP)      │  │  原則 3: State 在 filesystem   │
│  ├─────────────────────┤  │                                │
│  │   Agent Loop        │  │  ┌──────┐    ┌──────┐         │
│  │   (run / stream)    │  │  │ Skill │──→│ Tool │         │
│  ├─────────────────────┤  │  └──────┘    └──┬───┘         │
│  │   Loaders           │  │                 │              │
│  │   (skill/cmd/agent) │  │           ┌─────▼─────┐       │
│  ├─────────────────────┤  │           │   State    │       │
│  │   Tool Registry     │  │           │  (.json)   │       │
│  │   (fs/web/triz)     │  │           └─────┬─────┘       │
│  ├─────────────────────┤  │                 │              │
│  │   SSOT Layer        │  │           ┌─────▼─────┐       │
│  │   (.claude/ + docs/)│  │           │  Output    │       │
│  └─────────────────────┘  │           │  (docs/    │       │
│                           │           │ engineering)│       │
│                           │           └───────────┘       │
├───────────────────────────┴────────────────────────────────┤
│                                                            │
│  C. Skill 與 Tool 組成一覽                                   │
│                                                            │
│  TRIZ Skills: router/scope/model/solve/verify/wi            │
│  TR Skills:   gate/fea/test/dfm/sop/spc/ppap               │
│  Tools:       filesystem / web / agent / TRIZ domain        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 4. 主要內容

### A. 5 層堆疊架構

| 層 | 名稱 | 職責 | 關鍵元件 |
|:---|:-----|:-----|:---------|
| **L1** | Interface | 使用者進入點 | CLI（terminal）/ HTTP（API） |
| **L2** | Agent Loop | 核心執行迴圈 | `AgentLoop` run/stream，管理 turn-by-turn 對話 |
| **L3** | Loaders | 動態載入可執行流程 | Skill Loader / Command Loader / Agent Loader |
| **L4** | Tool Registry | 工具調度層 | filesystem tools / web tools / agent tools / TRIZ domain tools |
| **L5** | SSOT | 唯一真相來源 | `.claude/`（state + context）/ `docs/`（methodology + engineering） |

### B. 三大設計原則

| 原則 | 說明 | 為什麼這樣設計 |
|:-----|:-----|:-------------|
| **業務邏輯在 markdown skills** | 方法論、流程定義、gate 規則都寫在 skill 檔案中 | Skill 可獨立版控、審查、更新，不需改 Python code |
| **Runtime 只做調度** | Python 負責載入 skill、呼叫 tool、管理 state 流轉 | 邏輯與執行分離，降低耦合 |
| **State 在 filesystem** | Session 狀態用 JSON 持久化在 `.claude/context/` | 可 git 追蹤、可離線存取、不依賴外部 DB |

### C. Skill 與 Tool 組成

**TRIZ 引擎（6 Skills）**：

| Skill | 對應 Phase | 職責 |
|:------|:----------|:-----|
| `triz-router` | 入口 | 問題路由（TC / SF-only / 引導） |
| `triz-scoping` | P0 | 5Why / KT / CECA 問題定向 |
| `triz-model` | P1 | FA + SF 功能建模 |
| `triz-contradict` | P2-P3 | TC→PC→SF 推理 + 解法產出 |
| `triz-verify` | P3 | 4-Q 複雜度 + evidence + CCI |
| `triz-wi` | P3→TR0 | WI / MC / ICD 工程文件產出 |

**TR 引擎（7 Skills）**：

| Skill | 對應 Phase | 職責 |
|:------|:----------|:-----|
| `tr-gate` | P4-P7 | Gate Review（TR1-TR10） |
| `tr-fea` | P4 | FEA 設定輔助（材料卡 + 邊界條件） |
| `tr-test` | P5-P6 | 測試報告產出 |
| `tr-dfm` | P6 | DFM/DFA 審查 |
| `tr-sop` | P7 | SOP 草稿產出 |
| `tr-spc` | P7 | SPC/Cpk 計算 |
| `tr-ppap` | P7 | PPAP 文件包組裝 |

### D. 資料流概要

```
使用者輸入
    ↓
Skill（方法論邏輯）
    ↓
Tool（執行動作：讀寫檔案、查詢知識庫、呼叫子 agent）
    ↓
State 更新（.triz-state.json / .tr-state.json）
    ↓
Output（docs/engineering/ 工程交付物）
```

## 5. 建議視覺元素

| 元素 | 類型 | 內容描述 |
|:-----|:-----|:---------|
| **5 層堆疊圖** | 垂直方塊堆疊 | 5 層由上到下，每層標示名稱 + 關鍵元件，用不同色塊區分 |
| **資料流箭頭** | 垂直流程圖 | Skill → Tool → State → Output，右側放置 |
| **Skill 一覽表** | 雙欄表格 | 左欄 TRIZ Skills（6 個），右欄 TR Skills（7 個），標示對應 Phase |
| **三原則標籤** | 三張小卡 | 各一句話 + icon（文件、齒輪、資料夾） |

## 6. 口條骨架（25 秒）

> 左邊是系統的 5 層架構。最上面是使用者進入的 CLI 或 HTTP 介面；中間是 AgentLoop 負責執行調度；下面是 13 個 Skill——6 個 TRIZ、7 個 TR——各自對應流程中的一段。右邊三條原則：業務邏輯寫在 markdown 裡、Python 只做調度、狀態存在 filesystem。這代表流程可以被版控、被審查、被追溯——而不是鎖在某個人的 notebook 或某場會議裡。

## 7. 來源文件索引

| 內容 | 來源 |
|:-----|:-----|
| Harness 分層定義 | `docs/planning/05_architecture.md` §Harness Layering |
| Skill/Tool 組件圖 | `docs/planning/05_architecture.md` §TRIZ Service Components |
| SSOT 策略 | `docs/planning/08_project_structure.md` |
| State JSON 結構 | `docs/methodology/DK-04--data-model-and-gate.md` §State JSON Schema |
| 內容位置邊界 | `.claude/CLAUDE.md` §Content Boundary Policy |
