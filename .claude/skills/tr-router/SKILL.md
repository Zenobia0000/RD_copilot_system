# TR 入口路由 + 儀表板

## Overview

本 skill 是 TR1-TR10 工程執行追蹤的入口。讀取 `.tr-state.json` 顯示專案儀表板，並路由到適當的 `tr-*` skill。

**宣告：** 「正在使用 tr-router skill — 顯示 TR 儀表板。」

---

## 行為

### 1. 讀取狀態

讀取 `.claude/context/triz/.tr-state.json`。若不存在，從 `.triz-state.json` 初始化（見下方 Bootstrap 邏輯）。

### 2. 顯示儀表板

```markdown
# TR 儀表板 — {project_id}

> TRIZ Session: {triz_session_ref}
> 更新時間: {now}

## 子系統 TR 等級

| 子系統 | 現在 TR | 目標 TR | 障礙 | 負責 WI |
|:-------|:--------|:--------|:-----|:--------|
| {name} | {current} | {target} | {blockers} | {wi} |
...

## WI 完成度

| WI | 狀態 | 已完成步驟 | 交付物 |
|:---|:-----|:-----------|:-------|
| {wi_id} | {status} | {steps} | {deliverables} |
...

## V-Test 進度

| Phase | 測試項 | 狀態 | 結果 |
|:------|:-------|:-----|:-----|
| {phase} | {V_id} | {status} | {result} |
...

## 風險摘要

| 風險 ID | 狀態 |
|:--------|:-----|
| {risk_id} | {status} |
...

## Gate Review 歷史

{gate_reviews list, or "尚無 gate review 記錄"}

## 下一步建議

- 下一個 gate 目標: {next_gate}
- HIGH 風險項: {count} 項
- 建議動作: {suggestion}
```

### 3. 路由邏輯

根據使用者輸入路由：

| 使用者意圖 | 路由目標 | 指令 |
|:-----------|:---------|:-----|
| gate review | tr-gate | `/tr-gate TRn` |
| FEA 輔助 | tr-fea-assist | `/tr-fea WI-nn` |
| 測試報告 | tr-test-report | `/tr-test Vn` |
| DFM 審查 | tr-dfm | `/tr-dfm subsystem` |
| 回到 TRIZ 分析 | triz-router | `/triz` |
| 僅看儀表板 | (不路由) | 顯示後結束 |

---

## Bootstrap 邏輯（從 .triz-state.json 初始化）

若 `.tr-state.json` 不存在：

1. 讀取 `.triz-state.json` 取得 `session_id` 和 `problem_description`
2. 從 `step5` 讀取 WI 清單
3. 從 `step4.observation_items` 讀取風險項
4. 從 `docs/engineering/tr_gate_framework.md` 讀取各子系統現況 TR 評估
5. 建立 `.tr-state.json` 初始結構
6. 回報初始化完成

---

## 狀態檔案

| 檔案 | 用途 | 生命週期 |
|:-----|:-----|:---------|
| `.claude/context/triz/.triz-state.json` | TRIZ session（step 0-5） | Session 級 |
| `.claude/context/triz/.tr-state.json` | TR gate 進展（TR0-10） | 專案級（跨 session 持續更新） |

兩者透過 `triz_session_ref` 欄位建立追溯關係。

---

## 下一步導引

儀表板顯示後，依狀態提示使用者：

| 狀態 | 提示 |
|:-----|:-----|
| 所有子系統 TR0，WI 未開始 | 「建議從 FEA 開始推進 TR1。執行 `/tr-fea WI-01` 開始馬達磁路 FEA。」 |
| 部分 WI 完成 | 「{子系統} 已具備 TR1 條件。執行 `/tr-gate TR1` 進行 gate review。」 |
| 有 HIGH 風險 | 「注意：{count} 項高風險未解決，可能阻擋 gate 通過。」 |
| Gate review 已完成 | 「最近一次 gate review: {date} — {result}。下一個目標: TR{n+1}。」 |
