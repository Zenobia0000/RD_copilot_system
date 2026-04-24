---
name: triz-router
description: TRIZ 工作流入口路由。自動偵測問題類型並路由到適當步驟（Step 0/1/2 或 SF-only），管理 session 狀態。Use as the main entry point for any TRIZ problem-solving session.
---

# TRIZ Router: 入口路由與 Session 管理

## Overview

本 skill 是 Auto-TRIZ 閉環流程的主入口。分析使用者輸入，決定路由到哪個步驟，並管理跨步驟的 session 狀態。

**宣告：** 「正在使用 triz-router skill — 分析問題並決定路由。」

---

## Phase 1: Session 狀態檢查

首先檢查是否有既有 session：

```
讀取 .claude/context/triz/.triz-state.json
│
├─ 存在 + 未完成 → 詢問使用者：
│  「偵測到進行中的 TRIZ session：[session_id]
│   目前在 [current_step]，主題：[topic]
│   [1] 恢復此 session 繼續
│   [2] 開始新 session（舊 session 會歸檔）」
│
├─ 存在 + 已完成 → 直接開始新 session
│
└─ 不存在 → 開始新 session
```

---

## Phase 2: 入口路由

分析使用者輸入，決定路由：

### 路由決策樹

```
使用者輸入分析
│
├─ 偵測到「改善 X 會惡化 Y」或「X 和 Y 衝突」模式
│  └─ Level B：TC 已知
│     → 路由至 /triz-solve (triz-contradict skill)
│     → 建議先做 Step 1 驗證完整性
│
├─ 偵測到「做不到 X，但沒有副作用」或「功能缺失」
│  └─ SF-only 快速通道
│     → 路由至 /triz-solve --sf-only (triz-contradict skill, SF mode)
│
├─ 偵測到問題症狀描述（異常、故障、不滿意）
│  └─ Level A：知道不滿意但說不出 trade-off
│     → 路由至 /triz-scope (triz-scoping skill)
│
├─ 偵測到系統描述但無明確矛盾或缺失
│  └─ 需要功能建模
│     → 路由至 /triz-model (triz-model skill)
│
├─ 連系統都描述不了
│  └─ Level C：不適用 TRIZ
│     → 建議替代框架：
│       - Design Thinking / JTBD（尋找痛點）
│       - Axiomatic Design（功能獨立性）
│       - System Evolution Trends（下一代預測）
│
├─ 「要讓某指標更好，沒有副作用」
│  └─ 不是矛盾問題
│     → 建議最佳化工具：DOE / 田口 / ML
│     → 除非：優化到極限撞牆 → 那個牆就是 TC
│
└─ 無法判斷
   → 引導式問答：
     1. 「能否描述你的系統？（誰對誰做了什麼）」
     2. 「你最不滿意的是什麼？」
     3. 「如果直接改善它，會有什麼副作用嗎？」
```

### Level B 造句驗證

當使用者看起來是 Level B 時，用造句確認：

> 「在 **[系統]** 中，為了 **[改善 A]**，會導致 **[B 惡化]**。」

能填完 → 確認是 TC，路由至 Step 2。
不確定 → 路由至 Step 0。

---

## Phase 3: Session 初始化

確定路由後，執行兩件事：

### 3a: 建立 session state

```json
{
  "session_id": "{YYYY-MM-DD-HHmm}-{topic}",
  "created_at": "{ISO timestamp}",
  "current_step": "{routed step}",
  "path": "{tc-main | sf-only | unknown}",
  "problem_description": "{使用者原始描述}",
  "report_file": ".claude/context/triz/session-{session_id}.md",
  "step0": { "completed": false },
  "step1": { "completed": false },
  "step2": { "completed": false },
  "step3": { "completed": false },
  "step4": { "completed": false }
}
```

寫入 `.claude/context/triz/.triz-state.json`。

### 3b: 建立 session 報告檔

使用 Write tool 建立 `.claude/context/triz/session-{session_id}.md`，寫入報告頭部：

```markdown
# TRIZ Session Report: {session_id}

> **日期**: {YYYY-MM-DD}
> **主題**: {一句話主題}
> **路徑**: {path}
> **判定**: 未完成

---
```

**重要：** 此報告檔在後續每個 step 完成時由該 step 的 skill **即時追加**對應區段。不必等到 Step 4 才寫入。每步完成後，使用 Read tool 讀取報告檔現有內容，再用 Write tool 追加該步驟的完整 markdown 輸出。

---

## Phase 4: 路由執行

告知使用者路由結果並提示下一步：

```markdown
## TRIZ Session 已建立

- **Session**: {session_id}
- **問題**: {一句話摘要}
- **路由**: {Step 0 / Step 1 / Step 2 / SF-only}
- **理由**: {為什麼選這個入口}

### 下一步

請執行 `/triz-scope`（或 `/triz-model` / `/triz-solve`）開始分析。
```

---

## Session 歸檔

當開始新 session 且有舊 session 時：

1. 將舊 `.triz-state.json` 重命名為 `session-{old_session_id}-state.json`
2. 建立新的 `.triz-state.json`

---

## 適用問題類型速查

| 問題類型 | 適用度 | 切入點 |
|:---------|:-------|:------|
| 現有產品改良 | 最適合 | Step 1 → 全流程 |
| 製程優化 | 最適合 | Step 0 (KT) → TC/PC |
| 故障分析 | 高度適用 | Step 0 (5Why + KT) |
| 新產品開發 | 部分適用 | Step 1，搭配 DT/JTBD |
| 成本削減 | 適用 | Step 2 (TC) |
| 下一代產品預測 | 間接適用 | 演化趨勢分析 |
| 純軟體架構 | 低適用 | 用 AD 或 DDD |
| 商業模式/市場策略 | 不適用 | 無物理參數 |
