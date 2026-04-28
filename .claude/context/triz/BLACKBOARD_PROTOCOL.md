# Blackboard Protocol — Multi-Agent 讀寫規則

> 適用於 triz-contradict (supervisor) + triz-analyst (worker) 的 fan-out 場景。
> 設計依據：DK-03 §8 + DK-04 §5。

## 角色定義

| 角色 | Agent | 數量 |
|:-----|:------|:----:|
| **Supervisor** | triz-contradict skill (main agent) | 1 |
| **Worker** | triz-analyst agent | N (per TC) |

## 讀寫權限矩陣

| 檔案/路�� | Supervisor | Worker | 說明 |
|:----------|:----------:|:------:|:-----|
| `.triz-state.json` | RW | R | Worker 禁止寫入 state JSON |
| `.tr-state.json` | R | — | Worker 不需存取 TR state |
| `session-step2-tc{N}-*.md` | R | W (僅自己的 N) | 每個 Worker 只寫自己的 TC |
| `session-step3-tc{N}-*.md` | R | W (僅自己的 N) | 每個 Worker 只寫自己的 TC |
| `session-step2-summary.md` | W | — | Supervisor 彙整用 |
| `session-step1-*.md` | R | R | Step 1 輸出，所有人唯讀 |
| `session-step0-*.md` | R | R | Step 0 輸出，所有人唯讀 |
| `session-template.md` | R | R | 模板，所有人唯讀 |
| `triz_knowledge_base/*` | R | R | KB 檔，所有人唯讀 |
| `docs/_domain-knowledge/*` | R | R | DK 檔，所有人唯讀 |
| `docs/_harness/*` | R | R | 策略/框架，所有人唯讀 |

## 檔案命名規則

### Worker 黑板檔

格式：`session-step{STEP}-tc{N}-{YYYYMMDD-HHMMss}.md`

- `{STEP}`: `2` 或 `3`
- `{N}`: TC 編號（1-based）
- `{YYYYMMDD-HHMMss}`: **秒級** timestamp（避免同分鐘碰撞）

範例：
- `session-step2-tc1-20260428-143022.md`
- `session-step3-tc3-20260428-143045.md`

### Supervisor 彙整檔

格式：`session-step2-summary.md`（固定名稱，每輪 SIM 覆寫）

## 衝突預防規則

1. **單寫者原則**：每個 per-TC 檔只有一個 Worker 可寫。Worker 不得寫入其他 TC 的檔案
2. **State JSON 集中寫入**：只有 Supervisor 可修改 `.triz-state.json`，在 Post-Fan-Out Merge 時統一更新
3. **Append-only for Workers**：Worker 不覆寫已有檔案，每次產出新的 timestamp 檔
4. **秒級 timestamp**：避免分鐘級碰撞（N 個 Worker 可能在同一分鐘內啟動）

## Supervisor Merge 流程

```
Fan-out dispatch (N 個 Agent tool calls in one message)
    │
    ▼
Workers 平行執行（各自寫黑板檔）
    │
    ▼
Workers 回報 summary（< 200 字/個）
    │
    ▼
Supervisor Post-Fan-Out Merge:
  M1. Glob 收集所有 session-step3-tc* 檔
  M2. Read 每個檔案，提取 Solution entry
  M3. 組裝 SIM 交互矩陣
  M4. 處理 BLOCKED workers
  M5. 寫回 .triz-state.json (step2 + step3)
  M6. 追加 session 報告檔
```

## Worker BLOCKED 處理

| BLOCKED 原因 | Supervisor 動作 |
|:------------|:---------------|
| Px 找不到 | 記錄為 observation item，該 TC 暫擱 |
| 數據驗證失敗 | 降級為 APPROXIMATE/UNVERIFIED |
| 領域檢核失敗 | 升格至使用者人工決策 |
| 工具失敗 (WebSearch timeout) | 標記 UNVERIFIED，繼續 |
