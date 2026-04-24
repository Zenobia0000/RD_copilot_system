# TRIZ Skills 索引

## TRIZ 閉環推理流程

| 步驟 | Skill | 用途 | 指令 |
| :--- | :---- | :--- | :--- |
| 入口路由 | **triz-router** | 偵測問題類型 → 路由到適當步驟 | `/triz` |
| Step 0 | **triz-scoping** | 5Why + KT Is/IsNot + CECA 問題定向 | `/triz-scope` |
| Step 1 | **triz-model** | 功能分析 + SF 診斷 + TC 造句 | `/triz-model` |
| Step 2+3 | **triz-contradict** | TC/PC/SF 解題管線（含 KB 注入） | `/triz-solve` |
| Step 4 | **triz-verify** | 驗證 + 複雜度判定 + 下游交付 | `/triz-verify` |
| Step 5 | **triz-wi** | TRIZ 概念產出 → 工程作業指導書 (WI) 體系 | `/triz-wi` |

---

## TR 工程執行追蹤

| 功能 | Skill | 用途 | 指令 |
| :--- | :---- | :--- | :--- |
| 入口儀表板 | **tr-router** | TR 等級總覽 + 路由 | `/tr` |
| Gate Review | **tr-gate** | 通用 gate review（TR1-TR10） | `/tr-gate TRn` |
| FEA 輔助 | **tr-fea-assist** | FEA 設定、材料卡、結果判讀 | `/tr-fea` |
| 測試報告 | **tr-test-report** | V-test + DVP&R 報告產生 | `/tr-test` |
| DFM 審查 | **tr-dfm** | DFM/DFA checklist + BOM 驗證 | `/tr-dfm` |

---

## 知識庫注入策略

全部 5 個 KB 檔全量內嵌於 triz-contradict SKILL.md（~26.5k tokens，佔 context window 13%）。

| KB 檔案 | Token 量 | 載入時機 |
| :--- | :--- | :--- |
| 39 參數 | ~1.5k | Step 2 參數映射 |
| 矛盾矩陣 | ~15k | Step 2 矩陣查表 |
| 40 原理 | ~4k | Step 2 原理具體化 |
| 分離原則 | ~1k | Step 3c 分離策略 |
| 76 標準解 | ~5k | Step 3d SF 匹配 |
