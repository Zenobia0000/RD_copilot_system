# 流程合約（Flow Contract）— RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**主要作者**：架構師 + 產品經理
**狀態**：`Active`
**方法論**：第一性原理分析（Elon Musk 5-Step + 蘇格拉底式質問）

---

## 目的

本文件是**產品生命週期與底層 Skill 引擎的統一合約 SSOT**。

它回答三個問題：
1. PRD 的 4 個 Epic 如何映射到現有 TRIZ + TR skills？
2. BDD 的 8 個 Gates 哪些已被底層覆蓋、哪些需要新建、哪些應延後？
3. 未來擴展（F4-F7）何時觸發、如何銜接現有引擎？

本文件**不新增任何軟體層**。它文件化兩層引擎如何組合成完整產品流程。

---

## §1 產品生命週期 ↔ TRIZ/TR 映射

### 1.1 PRD Epic → TRIZ/TR Step 對照

```
PRD Epic                    TRIZ/TR Step             Skills                      狀態
────────────────────────────────────────────────────────────────────────────────────────
Epic 1: Define (Phase I)    Step 0 + Step 1          triz-scoping + triz-model   ✅ 已建
  US-101 多模態萃取         Step 0 入口              triz-router + triz-scoping  ✅
  US-102 蘇格拉底提問       Step 0-1 問答            triz-scoping + triz-model   ✅
  US-103 Gate D2            TRIZ G1 (SF+FA 完成)     （內部 gate，非獨立 skill）    ✅

Epic 2: Diverge (Phase II)  Step 2-3 + Step 4        triz-contradict + verify    ✅ 已建
  US-201 TRIZ 三路徑        Step 2-3 TC/PC/SF        triz-contradict             ✅
  US-202 Decision Hub       Step 3 SIM + Step 4 CCI  triz-contradict + verify    ✅
  US-203 Pre-CAD 五維       Step 4 verify 擴展       triz-verify (+ cad_readiness) ⚡ 微擴展

Epic 3: Converge (Phase III) Step 4-5 + 治理層       triz-verify + triz-wi       部分
  US-301 黑帽質疑           證據缺口偵測             triz-verify observation     ⏳ 延後
  US-302 KT 決策            正式決策記錄             待建 kt-decision            ⏳ 延後
  US-303 知識回寫           6 類資產合成             待建 knowledge-agent        ⏳ 延後

Epic 4: TR Engineering      TR0-TR10                 tr-* skills (5 個)          ✅ 已建
  US-401 Gate Review        TR1-TR10 gate            tr-gate                     ✅
  US-402 WI/ICD/MC          Step 5 產出 = TR0        triz-wi                     ✅
```

### 1.2 核心洞察

**Phase 不是獨立的軟體層，而是 TRIZ Steps 的 UI 視圖：**

| PRD Phase | 實際上是... | 需要的「新東西」 |
|-----------|-----------|---------------|
| Phase I (Define) | triz-scoping + triz-model 的輸出展示 | 前端 UI（非後端邏輯） |
| Phase II (Diverge) | triz-contradict + triz-verify 的輸出展示 | 前端 UI + cad_readiness 微擴展 |
| Phase III (Converge) | triz-verify + triz-wi + 治理層 | 治理 skills（Beta/GA） |
| TR Engineering | tr-* skills 直接對應 | 已完成 |

**Gate P ≈ TR0**：Gate P（Pre-CAD 通過 → 可投入 CAD）在工程意義上等同於 TR0（概念凍結）。兩者的退出條件高度重疊：

| Gate P 條件（BDD F4） | TR0 條件（DK-04 §3.2） | 重疊？ |
|---------------------|---------------------|--------|
| Fatal TC 100% 解決 | TRIZ verdict = Evolution/Weak Evolution | ✅ 等價 |
| Major TC ≥ 90% 解決 | 同上 | ✅ 等價 |
| Evidence ≥ 50% HIGH+MEDIUM | Evidence Registry ≥ 50% HIGH+MEDIUM | ✅ 相同 |
| 五維評分通過 | CCI ≤ 0.55 | ✅ CCI 覆蓋 4/5 |
| CAD 工作量可接受 | （無對應） | ❌ 需新增 |

**結論**：Gate P 只需在 triz-verify 增加一個 `cad_readiness` 欄位即可覆蓋。

---

## §2 Gate 層級分析

### 2.1 三層 Gate 全景

```
┌─ BDD 產品流 Gates（上層，守護用戶旅程轉換）─────────────┐
│  D1  D2  X1  X2  P  V1  V2  V4                        │
│  ↓   ↓   ↓   ↓   ↓                                    │
│  已   已   已   已   簡                                 │
│  刪   刪   刪   刪   化                                 │
│  除   除   除   除   ↓                                  │
├─ TRIZ 內部 Gates（中層，守護推理品質）──────────────────┤
│  G0  G0' G0'' G1  G1' G2  G2' G3  G3' G4  G4'         │
│  ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅          │
├─ TR 外部 Gates（底層，守護工程成熟度）──────────────────┤
│  TR0  TR1  TR2  TR3  TR4  TR5  TR6  TR7  TR8  TR9  TR10│
│  ✅    ✅   ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅   │
└────────────────────────────────────────────────────────┘
```

### 2.2 BDD Gate 逐項審查

| Gate | BDD 描述 | 蘇格拉底質問 | TRIZ/TR 層已有的覆蓋 | 判定 |
|------|---------|-----------|-------------------|------|
| **D1** | Brief 完成 | 「填完表單」是 gate 嗎？ | triz-scoping 的輸入驗證（specs 非空 + problem_description 非空） | **DELETE** — 輸入驗證取代 |
| **D2** | ≥10 假設、矛盾全分類、≥1 因果圖、≥3 斷路點 | TRIZ G1 已要求 SF+FA 完成，為何第二層？ | TRIZ G1：「SF 圖完成 + 改善/惡化描述完成」 | **DELETE** — G1 取代 |
| **X1** | Track 入口 | 頁面導航是 gate 嗎？ | Step 1→2 的 TRIZ G2 已守護 | **DELETE** — 導航事件 |
| **X2** | Create 入口 | TRIZ G2 已要求 TC candidates ≥ 1 | TRIZ G2：「TC 候選方向 ≥ 1 + 至少一個能寫控制方程」 | **DELETE** — G2 取代 |
| **P** | Pre-CAD 五維通過 | CCI 已覆蓋 4/5 維度，只缺 CAD 工作量 | triz-verify CCI + Evidence Registry 覆蓋率 | **SIMPLIFY** — 加 cad_readiness |
| **V1** | Post-CAD 設計審查 | TR0 沒有 CAD | 不適用 | **DEFER** → TR3+ |
| **V2** | KT 決策簽核 | 單人 PoC 無多方簽核 | triz-verify verdict 已是最小決策記錄 | **DEFER** → Beta |
| **V4** | 知識回寫完成 | 零實驗數據的知識回寫？ | session 歸檔已存在 | **DEFER** → GA |

### 2.3 BDD Gates 與 TRIZ 內部 Gates 的映射

| BDD Gate | 對應 TRIZ Gate | Gate 條件比較 |
|----------|--------------|-------------|
| D1 | G0/G0'/G0'' | D1 = 「有輸入」，G0 = 「判定問題等級並路由」。G0 更精確。 |
| D2 | G1 | D2 要求量化指標（≥10 假設），G1 要求結構化完成（SF+FA）。G1 更實質。 |
| X1 | （無對應） | X1 純粹是頁面轉場，TRIZ 無此概念。 |
| X2 | G2 | 等價：兩者都要求 TC candidates 存在。 |
| P | G4 + cad_readiness | G4 要求 verdict + TechnicalDebt 登記。P 額外要求五維評估。 |

---

## §3 擴展路線圖

### 3.1 分階段建設

| 階段 | 時程 | 觸發條件 | 新增能力 | 涉及檔案 |
|------|------|---------|---------|---------|
| **TR0 (NOW)** | 2026-Q2 | — | triz-verify 增加 `cad_readiness` 欄位 | `.claude/skills/triz-verify/SKILL.md` |
| **MVP** | 2026-Q3 | 多人使用、需要正式 Pre-CAD gate | `precad-review` stub skill（從 triz-verify 拆出獨立 UX） | `.claude/skills/precad-review/` |
| **Beta** | 2026-Q4 | 跨部門決策需追溯 + Post-CAD 審查 | `kt-decision` + `devil-advocate` skills | `.claude/skills/kt-decision/`, `devil-advocate/` |
| **GA** | 2027-Q1 | ≥5 完成專案、知識複用需求浮現 | `knowledge-agent` skill | `.claude/skills/knowledge-agent/` |
| **規模化** | 2027+ | 多租戶、合規審計、多專案編排 | `.product-state.json` + `product-gate` skill | `.claude/context/triz/` |

### 3.2 每階段的「如果不做會怎樣」

| 階段 | 不做的後果 | 做的 ROI |
|------|---------|---------|
| TR0 cad_readiness | Gate P 無法形式化回答「可以投 CAD 嗎」 | 1 個欄位，10 分鐘工作 |
| MVP precad-review | Pre-CAD 審查嵌在 triz-verify 中，UX 不夠直觀 | 專門的審查 UI flow |
| Beta kt-decision | 決策記錄散落在 session 報告中，無正式追溯 | 多人簽核 + 審計軌跡 |
| Beta devil-advocate | 認知偏差未被系統性挑戰 | AI 自動產出質疑 + 證據缺口 |
| GA knowledge-agent | 知識靠人工整理，跨專案複用困難 | 6 類資產自動合成 |
| 規模化 product-state | Phase 狀態需手動推導（從 triz-state 的 current_step） | 獨立的產品流狀態機 |

### 3.3 擴展點的 Interface 預設計

為避免未來新建 skill 時與現有引擎不相容，預先定義 interface 契約：

**precad-review（MVP 觸發時建）：**
- 讀取：`.triz-state.json` → step4（CCI + evidence_registry + cad_readiness）
- 輸出：session 報告追加 Pre-CAD 區段 + `docs/engineering/precad_reviews/`
- Gate 條件：Fatal TC 100% 解決 + CCI ≤ 0.55 + cad_readiness ≠ "no-go"

**devil-advocate（Beta 觸發時建）：**
- 讀取：`.triz-state.json` → step3 solutions + step4 evidence_registry
- 輸出：challenge questions + evidence gaps + suggested experiments
- 觸發時機：Gate P 通過後（或 TR3 CAD 完成後）

**kt-decision（Beta 觸發時建）：**
- 讀取：全部 triz-state（solutions + CCI + evidence）
- 輸出：`docs/engineering/decision_records/` + 簽核追溯
- 觸發時機：所有 TC 已求解 + 方案已收斂

**knowledge-agent（GA 觸發時建）：**
- 讀取：`.triz-state.json` + `.tr-state.json` + `docs/engineering/` 全部產出
- 輸出：6 類知識資產條目
- 觸發時機：Gate V2 通過（決策已簽核）

---

## §4 CLI/HTTP 一致性

### 4.1 架構保證

CLI 和 HTTP 共享同一個 `AgentLoop`，差異僅在入口包裝：

```
CLI:  python -m app.harness <cmd> [input]
      → resolve_command() → build_system_prompt() → AgentLoop.run() → stdout

HTTP: POST /api/v1/sessions/{id}/run (or /run/stream)
      → resolve_command() → build_system_prompt() → AgentLoop.stream() → SSE
```

兩者共享：
- `resolve_command()`：command → skill 解析
- `build_system_prompt()`：skill SKILL.md → system prompt 組裝
- `AgentLoop`：LLM 呼叫 + tool 執行循環
- Tool registry：Read/Write/Glob/Grep/Web/Agent

差異只在：
- CLI → `run()` → 一次性文字輸出
- HTTP → `stream()` → SSE events（worker_status / text_delta / tool_use / tool_result）

### 4.2 一致性保證

**所有新增/修改的 skill 自動被兩個介面支援**。原因：skill loader（`discover_skills()`）掃描 `skills_root` 下所有 `<dir>/SKILL.md`，不區分 CLI/HTTP。新增 SKILL.md 即同時在兩個介面可用。

**不需要為每個 skill 分別實作 CLI 和 HTTP 路徑。**

---

## §5 BDD 修訂建議

### 5.1 階段標記

建議為 03_bdd_guide.md 的每個 Feature/Scenario 加上可驗證階段標記：

| BDD Feature | 現有 Tags | 建議新增 Tag | 理由 |
|-------------|----------|------------|------|
| F1 早期問題定義 | @triz-step-0, @triz-step-1 | `@tr0-ready` | triz-scoping + triz-model 已建 |
| F2 Phase Gate | @gate | `@tr0-ready`（部分） | tr-gate 已建；D/X/P/V gates 由 TRIZ 內部 gates 覆蓋 |
| F3 TRIZ 求解 | @triz-step-2, @triz-step-3 | `@tr0-ready` | triz-contradict 已建 |
| F4 Pre-CAD | @gate-p | `@mvp-target` | TR0 由 triz-verify cad_readiness 覆蓋；獨立 skill 等 MVP |
| F5 黑帽質疑 | @ai | `@beta-target` | 需 Post-CAD，TR0 無 CAD |
| F6 KT 決策 | @kt, @signoff | `@beta-target` | 需多人協作 |
| F7 知識回寫 | @knowledge | `@ga-target` | 需累積專案數據 |

### 5.2 BDD 與底層 Gate 的對齊聲明

BDD Feature 2（Phase Gate 退出檢查）描述的 8 個 Gates（D1/D2/X1/X2/P/V1/V2/V4）是**產品 UX 層的 gate**。它們的工程實質由兩層底層 gate 保障：

- **TRIZ 內部 Gates**（G0-G4）：守護推理品質，確保每個 TRIZ step 的輸入合格
- **TR 外部 Gates**（TR0-TR10）：守護工程成熟度，確保每個開發階段的退出條件

BDD Gates 是底層 gates 的**聚合視圖**（aggregate view），不是獨立的第三層。
BDD Gates **包含** TR Gates：D→X→P 對應 TRIZ G0-G4 + TR0，V1-V4 對應 TR 鏈上的驗證節點。

---

## §6 State 檔案歸屬（現況）

| 檔案 | Scope | 內容 | 讀取者 | 寫入者 |
|------|-------|------|--------|--------|
| `.triz-state.json` | Session | Steps 0-5, TCs, solutions, CCI, evidence, **cad_readiness（新增）** | triz-* skills | triz-* skills |
| `.tr-state.json` | Project | TR0-10 per subsystem, WI status, V-tests, risks | tr-* skills | tr-* skills |

**未來（規模化觸發時）**：
| `.product-state.json` | Project | 產品流 Gates (D/X/P/V) + F4-F7 artifact 指針 | product-* skills | product-* skills |

**Phase 推導規則**（不需要額外 state）：
- `current_step` ∈ {step0, step1} → Phase I (Define)
- `current_step` ∈ {step2, step3} → Phase II (Diverge)
- `current_step` ∈ {step4, step5} → Phase III (Converge)
- TRIZ session 完成 + `.tr-state.json` 存在 → TR Engineering

---

## 文件溯源

- PRD：[`02_prd.md`](./02_prd.md)（4 Epic + 8 User Stories）
- BDD：[`03_bdd_guide.md`](./03_bdd_guide.md)（7 Features + 8 Gates）
- 架構：[`05_architecture.md`](./05_architecture.md)（C4 模型 + 概念域）
- Gate 定義：[`DK-04`](../docs/_domain-knowledge/DK-04--data-model-and-gate.md)（§3 TRIZ G0-G4 + TR0-TR10）
- TR 框架：[`tr_gate_framework.md`](../docs/_harness/engineering/tr_gate_framework.md)
- Skills 索引：[`.claude/skills/INDEX.md`](../../.claude/skills/INDEX.md)
