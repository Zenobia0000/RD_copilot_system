---
description: 查看當前 TRIZ session 狀態，追蹤各步驟進度。
---

# TRIZ Session 狀態

讀取 `.claude/context/triz/.triz-state.json`，顯示當前 TRIZ session 的進度。

## 使用方式

```
/triz-status                       # 顯示當前 session 狀態
```

## 操作

1. 讀取 `.claude/context/triz/.triz-state.json`
2. 如果檔案不存在 → 顯示「無進行中的 TRIZ session。使用 `/triz` 開始新 session。」
3. 如果檔案存在 → 顯示以下資訊：

```markdown
## TRIZ Session 狀態

- **Session**: {session_id}
- **問題**: {problem_description}
- **路徑**: {path}
- **當前步驟**: {current_step}

### 各步驟進度

| Step | 狀態 | 關鍵產出 |
|:-----|:-----|:---------|
| Step 0: 問題定向 | {completed/pending} | {tc_hypothesis / -} |
| Step 1: 功能建模 | {completed/pending} | {sf_diagnosis count / -} |
| Step 2: TC 定義 | {completed/pending} | {tc count + principles / -} |
| Step 3: PC/SF 解題 | {completed/pending} | {solution summary / -} |
| Step 4: 驗證 | {completed/pending} | {verdict / -} |

### 下一步建議
{根據 current_step 建議下一個 /triz-* 指令}
```
