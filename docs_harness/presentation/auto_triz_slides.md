# Auto-TRIZ 技術面試報告

> 用 Claude Code Harness Engineering 實作 Multi-Agent TRIZ 自動化系統

---

## Part 1 — 問題定義與目標

### 業務問題

電動自行車機電設計中，工程師頻繁面對「改善 A 必然惡化 B」的矛盾（例：改善散熱 → 體積增大）。TRIZ 是成熟方法論，但人工執行耗時 2-3 天、需要專家資格、過程不可追溯。

### 技術挑戰

把一套 **非線性、有回退、有多路分支** 的專家方法論，編碼成 LLM 可穩定執行的自動化管線。

核心難點不是「讓 LLM 懂 TRIZ」，而是：
- 流程有 5 步 × 4 個決策閘門 × 3 種路徑分支——LLM 在長流程中容易**偏離軌道**
- 知識庫共 ~26,500 tokens——全量注入會**超出有效推理區間**
- 多矛盾場景下方案互相衝突——LLM 容易**進入推理迴圈**
- Session 跨多次對話——LLM **天生無狀態**

### 交付物總覽

| 項目 | 規模 |
|:-----|:-----|
| 方法論策略文件 | 968 行（47KB），完整閉環流程 + 決策規則 |
| UML 架構圖 | 12 份（領域模型、狀態機、決策樹、流程圖） |
| Harness 系統 | 6 commands + 5 skills + 1 agent + state store |
| 知識庫 | 5 份結構化 TRIZ 參照表，含分層注入策略 |

---

## Part 2 — 系統架構

### 2.1 整體架構圖

```
                        ┌─────────────────────────────────────────┐
                        │          Claude Code Harness            │
                        │                                         │
  User Input            │   Commands        Skills        Agent   │
  ─────────────┐        │   (Entry)         (Logic)      (Reason) │
               │        │                                         │
               ▼        │   ┌────────┐     ┌──────────┐          │
         /triz ─────────┼──▶│ triz   │────▶│ triz-    │          │
         /triz-scope ───┼──▶│ triz-  │────▶│ router   │          │
         /triz-model ───┼──▶│ scope  │────▶│ triz-    │          │
         /triz-solve ───┼──▶│ triz-  │────▶│ scoping  │   ┌────┐│
         /triz-verify ──┼──▶│ model  │────▶│ triz-    │──▶│triz││
         /triz-status ──┼──▶│ ...    │────▶│ contra-  │   │ana-││
                        │   └────────┘     │ dict     │   │lyst││
                        │    Thin          │ triz-    │   └────┘│
                        │    Wrapper       │ verify   │  Opus   │
                        │                  └─────┬────┘  Agent  │
                        │                        │      (Stateless)
                        │                        ▼              │
                        │    ┌───────────────────────────┐      │
                        │    │     State Store            │      │
                        │    │  .triz-state.json          │      │
                        │    │  (Session 持久化)           │      │
                        │    └───────────────────────────┘      │
                        │                        ▼              │
                        │    ┌───────────────────────────┐      │
                        │    │     Knowledge Base (RAG)   │      │
                        │    │  01_39_parameters.md       │      │
                        │    │  02_contradiction_matrix.md│      │
                        │    │  03_40_principles.md       │      │
                        │    │  04_separation_principles  │      │
                        │    │  05_76_standard_solutions  │      │
                        │    └───────────────────────────┘      │
                        └─────────────────────────────────────────┘
```

### 2.2 分層架構（為什麼這樣拆）

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Command Layer（進入點）                     │
│  · 6 個 /triz-* 指令，每個 ~30 行                     │
│  · 職責：載入對應 Skill，不做任何邏輯                   │
│  · 設計原因：使用者介面與業務邏輯解耦                    │
├─────────────────────────────────────────────────────┤
│  Layer 2: Skill Layer（編排層）                       │
│  · 5 個 Skill（155-401 行），管理流程 + 決策閘門         │
│  · 職責：讀寫狀態、注入知識庫、呼叫 Agent、驗證產出       │
│  · 設計原因：流程邏輯集中管理，Agent 保持無狀態           │
├─────────────────────────────────────────────────────┤
│  Layer 3: Agent Layer（推理層）                       │
│  · 1 個 triz-analyst（Opus），純推理、無狀態              │
│  · 職責：TC/PC/SF 深度推理、矩陣查表、分離策略選擇       │
│  · 設計原因：推理與編排分離，Agent 可替換模型              │
├─────────────────────────────────────────────────────┤
│  Layer 4: Data Layer（持久化 + 知識庫）                │
│  · State Store：.triz-state.json（Session 狀態機）      │
│  · Knowledge Base：5 份 TRIZ 參照表（RAG + 全量混合）    │
│  · 設計原因：LLM 無狀態，需要外部持久化；KB 太大需分層    │
└─────────────────────────────────────────────────────┘
```

---

## Part 3 — Trigger 設計

### 3.1 Domain Trigger vs Data Trigger

系統中有兩類觸發機制，驅動流程推進：

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Trigger（領域觸發）                  │
│                                                             │
│  基於「問題的性質」決定走哪條路：                               │
│                                                             │
│  ┌──────────────┐     ┌─────────────────────────────────┐  │
│  │ 使用者輸入     │────▶│ Router 判定樹                    │  │
│  │ 問題描述       │     │                                 │  │
│  └──────────────┘     │  能填 TC 句型？──Y──▶ Solve Agent │  │
│                       │       │                           │  │
│                       │       N                           │  │
│                       │       │                           │  │
│                       │  有症狀？──Y──▶ Scope Agent        │  │
│                       │       │                           │  │
│                       │       N                           │  │
│                       │       │                           │  │
│                       │  功能缺失？──Y──▶ SF-only          │  │
│                       │       │                           │  │
│                       │       N ──▶ 拒絕 + 建議替代方法    │  │
│                       └─────────────────────────────────┘  │
│                                                             │
│  觸發條件：問題類型（Level A/B/C + 6 種問題分類）             │
│  觸發者：triz-router skill                                  │
│  設計意義：不靠 LLM 自由判斷，用結構化決策樹做分類            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Data Trigger（資料觸發）                   │
│                                                             │
│  基於「上一步的產出資料」決定下一步行為：                       │
│                                                             │
│  Step 0 產出                      觸發行為                   │
│  ───────────────                  ────────────              │
│  root_cause = 物理參數             → 跳 Step 1，直進 Step 2  │
│  root_cause = 組件交互             → 走 Step 1               │
│  root_cause = 模糊                → 觸發 CECA 子流程         │
│                                                             │
│  Step 1 產出                      觸發行為                   │
│  ───────────────                  ────────────              │
│  sf_diagnosis.status = missing    → SF-only 快車道            │
│  sf_diagnosis.status = harmful    → TC 主路徑                 │
│                                                             │
│  Step 2 產出                      觸發行為                   │
│  ───────────────                  ────────────              │
│  tcs.length = 1                   → 直接 Step 3              │
│  tcs.length > 1 + 有瓶頸          → 瓶頸路徑                  │
│  tcs.length > 1 + 無瓶頸          → SIM 路徑                  │
│  matrix_cell = empty              → 跳過矩陣，直進分離策略     │
│                                                             │
│  Step 4 產出                      觸發行為                   │
│  ───────────────                  ────────────              │
│  verdict = evolution              → 產出工程規格書             │
│  verdict = patch + 有時間          → 回退 Step 3              │
│  verdict = patch + 沒時間          → 產出技術債記錄            │
│  new_tc_detected = true           → 回退 Step 1（螺旋上升）   │
│                                                             │
│  觸發條件：.triz-state.json 中的欄位值                       │
│  觸發者：每個 Skill 的決策閘門                                │
│  設計意義：流程推進由資料驅動，不由 LLM「覺得」應該做什麼      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 兩種 Trigger 的協作

```
Domain Trigger              Data Trigger
（進入時判斷一次）           （每步結束時判斷）

  問題描述 ──▶ Router        Step 0 產出 ──▶ Gate 0
               │                              │
               ▼                              ▼
           分配 Agent ──▶ 執行 ──▶ 寫入狀態 ──▶ 讀取狀態 ──▶ 下一步
                                                    ▲
                                                    │
                                            State Store
                                         (.triz-state.json)
```

**關鍵設計**：Domain Trigger 只在入口用一次；後續全部由 Data Trigger 驅動。這確保流程中段不會因為 LLM 重新「理解」問題而偏離路徑。

---

## Part 4 — Harness Engineering 導入

### 4.1 為什麼選 Claude Code Harness？

| 需求 | 傳統方案 | Claude Code Harness |
|:-----|:---------|:-------------------|
| 流程編排 | 自建 orchestrator + API 呼叫 | **Skill = 流程邏輯容器**，原生支援 |
| 知識庫注入 | 自建 RAG pipeline + vector DB | **Skill 內嵌 KB 路徑 + Read tool**，零基建 |
| 狀態持久化 | 自建 DB + ORM | **JSON 檔 + Skill 讀寫**，輕量 |
| Agent 呼叫 | API orchestration code | **Agent 定義檔 + Skill 呼叫**，聲明式 |
| 使用者介面 | Web UI / CLI app | **Command = 使用者入口**，零開發 |

> **核心決策**：不寫應用程式碼，把 Claude Code 本身當成 runtime。
> Skill 即邏輯、Command 即 API、Agent 即推理引擎、JSON 即 DB。

### 4.2 Harness 元件對照表

| Claude Code 原生元件 | 在本系統中的角色 | 數量 |
|:--------------------|:----------------|:-----|
| **Command** (`/triz-*`) | 使用者進入點，薄封裝 | 6 |
| **Skill** (`triz-*/SKILL.md`) | 流程邏輯 + 決策閘門 + KB 注入 | 5（Router + 4 Step） |
| **Agent** (`triz-analyst`) | 無狀態深度推理（Opus） | 1 |
| **Context Store** (`.triz-state.json`) | Session 狀態機 | 1 |
| **Rules** (`CLAUDE.md`) | Skill 調用優先序 + Agent 定義 | 1 |

### 4.3 Prompt-Native Orchestration 模式

```
傳統 Agent 系統：
  Code → API Call → LLM → Parse Response → Code → API Call → ...
  （需要應用程式碼做 glue）

本系統（Prompt-Native）：
  Command → Skill（prompt 即邏輯）→ Agent（prompt 即推理）→ JSON（prompt 即狀態）
  （沒有應用程式碼，全部在 prompt layer 完成）
```

**這意味著**：
- 修改流程 = 編輯 Skill markdown，不需要重新部署
- 新增步驟 = 新增 Skill 檔案，不需要改 orchestrator
- 替換模型 = 改 Agent 定義檔的一行 model 欄位

---

## Part 5 — 失敗、迭代與優化

### 5.1 失敗紀錄

| # | 嘗試的方法 | 失敗現象 | 根因分析 | 修正方案 |
|:--|:----------|:---------|:---------|:---------|
| **F1** | 單一大 Prompt 塞入所有 TRIZ 流程 + 知識庫 | LLM 在 Step 3 後開始跳步、混淆步驟間的產出 | Context window 超過有效推理區間（~26.5K KB + 流程邏輯），注意力稀釋 | **拆成 5 個 Skill**，每個只載入當步需要的 KB |
| **F2** | 矛盾矩陣全量注入（15,000 tokens） | 推理品質下降，LLM 開始「自由發揮」忽略矩陣建議 | 大量無關行干擾 attention，LLM 傾向忽略長表格中段內容 | **RAG 策略**：確認參數後只注入對應行（~200 tokens） |
| **F3** | 讓 LLM 自行判斷「現在該走哪一步」 | 路由不穩定，同一問題多次輸入走不同路徑 | LLM 分類能力不穩定，對模糊輸入敏感度高 | **結構化判定樹**：Domain Trigger 用規則不用推理 |
| **F4** | 用 LLM context 記住 session 狀態 | 跨對話後狀態丟失；長對話後早期步驟的產出被壓縮消失 | LLM 是無狀態的；context compression 會丟棄早期資訊 | **外部 State Store**：JSON 持久化，每步讀寫 |
| **F5** | 多 TC 場景讓 LLM 自己管理方案交互 | TC1 和 TC2 的解法互相打架，LLM 進入 A→B→A 迴圈 | LLM 缺乏結構化的衝突偵測機制，傾向「再試一次」 | **SIM 矩陣 + 迴圈偵測**：OZ/OT/Px 重疊度比對 |
| **F6** | 解法直接交付，沒有驗證閘門 | 產出看似合理但物理上不可行的方案 | LLM 擅長生成 plausible text，但不會自我驗證物理可行性 | **4D 複雜度評分 + Px 分離驗證**：結構化 post-validation |
| **F7** | Skill 和 Agent 混在同一層 | Agent prompt 越來越長，既要管流程又要做推理 | 編排邏輯和推理邏輯的 prompt 需求不同：編排要穩定、推理要創意 | **Skill/Agent 分離**：Skill 管流程（確定性），Agent 管推理（創意性） |

### 5.2 關鍵優化路徑

```
V1: 單一大 Prompt
    │
    │ F1: Context overflow + 跳步
    ▼
V2: 拆成 5 個 Skill，每步獨立 prompt
    │
    │ F2: KB 全量注入干擾推理
    ▼
V3: KB 分層注入（全量 / RAG / 混合）
    │
    │ F3: 路由不穩定
    ▼
V4: Domain Trigger 用規則引擎，Data Trigger 用狀態機
    │
    │ F4: 跨對話狀態丟失
    ▼
V5: 外部 State Store（JSON 持久化）
    │
    │ F5+F6: 迴圈 + 無驗證
    ▼
V6: 迴圈偵測 + 4D 品質閘門 + 5 個停止條件
    │
    │ F7: Skill 太胖
    ▼
V7（最終）: Command / Skill / Agent / Data 四層分離
```

### 5.3 優化前後對比

| 維度 | V1（單一 Prompt） | V7（最終架構） |
|:-----|:-----------------|:--------------|
| 路由穩定性 | ~60%（同一問題不同次走不同路） | ~95%（結構化判定樹） |
| KB Token 用量/次 | ~26,500（全量注入） | ~2,500-4,500（按需注入） |
| 推理品質 | Step 3 後明顯下降 | 各步驟品質一致 |
| Session 恢復 | 不支援 | 完整支援（JSON 狀態機） |
| 迴圈偵測 | 無 | OZ/OT/Px 重疊度偵測 + SIM 2 輪上限 |
| 輸出可靠性 | 無驗證，靠人工判斷 | 4D 評分 + Px 分離驗證 + 5 停止條件 |
| 修改成本 | 改一處可能影響全流程 | 改 Skill 不影響其他步驟 |

---

## Part 6 — Lessons Learned

### 6.1 LLM 工程

| Lesson | 細節 |
|:-------|:-----|
| **Structured Routing > Free-form Reasoning** | LLM 強在推理，弱在穩定分類。把分類邏輯抽出來用規則引擎，LLM 只負責推理。F3 的教訓。 |
| **KB 注入有「有效推理區間」** | 不是 context window 夠大就全塞。超過 ~4,000 tokens 的單一表格，LLM 開始忽略中段內容。F2 的教訓。 |
| **LLM Output ≠ Final Answer** | 用領域規則做 post-validation，把 LLM 的創意發散收束到工程可行範圍。F6 的教訓。 |
| **Guard Rail 在推理結構層，不只在 output 層** | 「不要說壞話」是 output guard rail；「偵測推理迴圈」是 structure guard rail。後者才是 agent 系統的真正挑戰。F5 的教訓。 |
| **Prompt 即架構** | 知識庫結構 = prompt 結構 = 推理路徑。不是 prompt engineering（調措辭），是 prompt architecture（設計資訊流）。整個系統的核心洞見。 |

### 6.2 系統架構

| Lesson | 細節 |
|:-------|:-----|
| **編排與推理必須分離** | Skill 管流程（要穩定可預測），Agent 管推理（要創意有彈性）。混在一起兩邊都做不好。F7 的教訓。 |
| **外部狀態 > LLM 記憶** | LLM 是無狀態的，不要假裝它有記憶。JSON State Store 比 context window 可靠。F4 的教訓。 |
| **設計「什麼時候該停」比「怎麼解」更重要** | 5 個硬停止條件 + 技術債記錄。系統的價值不只在「解出來」，也在「知道什麼時候該停，並留下可追溯的紀錄」。 |
| **Prompt-Native 架構的取捨** | 優點：零應用程式碼、修改即部署、低基建成本。缺點：偵錯靠讀 prompt、效能受限於 LLM 延遲、測試靠人工走流程。適合原型和內部工具，不適合高頻低延遲場景。 |

### 6.3 方法論

| Lesson | 細節 |
|:-------|:-----|
| **先寫策略文件，再寫 prompt** | 968 行的策略文件是所有 Skill prompt 的「source of truth」。先把方法論理清，prompt 就是「策略文件的可執行版」。 |
| **12 份 UML 圖是給自己看的** | 不是文檔形式主義——領域模型、狀態機、決策樹是設計 Skill 邏輯的藍圖。寫圖的過程逼自己想清楚每個分支和邊界條件。 |
| **迭代比規劃重要** | V1→V7 經歷 7 次架構調整。每次失敗（F1-F7）都指向一個具體的架構決策錯誤。沒有一次能事先預見所有問題。 |

---

## Part 7 — 能力映射

### 系統架構師能力

| 能力項 | 體現 | 對應章節 |
|:-------|:-----|:---------|
| 領域建模 | 60 年 TRIZ 方法論 → 12 個核心概念 + 狀態機 + 決策樹 | Part 2 |
| 分層架構設計 | Command / Skill / Agent / Data 四層分離，各層可獨立替換 | Part 2.2 |
| Trigger 設計 | Domain Trigger（入口分類）+ Data Trigger（閘門推進）雙軌機制 | Part 3 |
| 失敗模式設計 | 5 個停止條件 + 迴圈偵測 + 技術債記錄 + Graceful Rejection | Part 5.1 F5/F6 |
| 可觀測性設計 | State Store 每步可查、Session 可恢復、Agent 活動可追蹤 | Part 4.2 |

### LLM 工程師能力

| 能力項 | 體現 | 對應章節 |
|:-------|:-----|:---------|
| Multi-Agent Orchestration | Router + 4 Step Agent，Skill 管編排、Agent 管推理 | Part 2 |
| Context Window 管理 | 5 份 KB 用 3 種注入策略，總量 26.5K → 每次 2.5-4.5K | Part 5.1 F2 |
| Guard Rail（結構層） | 不只是 output filter，在推理鏈層偵測邏輯迴圈 | Part 5.1 F5 |
| LLM 邊界認知 | 分類用規則（穩定性）、推理用 LLM（創意性）——知道什麼時候不該用 LLM | Part 5.1 F3 |
| Prompt Architecture | KB 結構 = prompt 結構 = 推理路徑，不是調措辭是設計資訊流 | Part 6.1 |
| Harness Engineering | Claude Code 的 Command/Skill/Agent/Context 當 runtime，零應用程式碼 | Part 4 |

### 問題解決能力

| 能力項 | 體現 |
|:-------|:-----|
| 系統性迭代 | V1→V7 共 7 次架構調整，每次有明確的失敗根因和修正方案 |
| 失敗根因分析 | 每個失敗（F1-F7）都追到具體的架構決策錯誤，不是表面症狀 |
| 取捨判斷 | Prompt-Native 架構的優缺點有明確認知，知道適用邊界 |
| 技術債管理 | 不只是系統功能——「Patch ≠ 失敗，不記錄才是失敗」是設計原則 |

---

## 附錄 — 架構圖索引

| 圖 | 內容 | 檔案 |
|:---|:-----|:-----|
| 領域模型 | 12 個核心概念 + 關係 | `docs/uml/00_domain_model.md` |
| 入口決策樹 | Level A/B/C + 6 種問題路由 | `docs/uml/01_entry_decision.md` |
| 主流程圖 | 5 步閉環 + 決策閘門 | `docs/uml/02_main_flow.md` |
| 問題定向 | 5Why / KT / CECA 子流程 | `docs/uml/03_step0_scoping.md` |
| Px 搜尋 | OZ-OT-Px 提取 + 3 種失敗處理 | `docs/uml/04_px_search.md` |
| 多矛盾策略 | 瓶頸 vs SIM 決策 | `docs/uml/05_multi_tc_strategy.md` |
| SIM 迭代 | +1/0/-1 評分 + 收斂規則 | `docs/uml/06_sim_iteration.md` |
| 迴圈診斷 | TC 打架 = PC 被誤認 | `docs/uml/07_loop_diagnosis.md` |
| 複雜度檢查 | 4D 評分 + Patch vs Evolution | `docs/uml/08_complexity_check.md` |
| 停止/繼續 | 5 個 STOP + CONTINUE 條件 | `docs/uml/09_stop_continue.md` |
| 生命週期 | 狀態機 + 4 種終態 | `docs/uml/10_problem_lifecycle.md` |
| KB 注入點 | 知識庫 × 步驟 × Token 策略 | `docs/uml/11_kb_integration.md` |
