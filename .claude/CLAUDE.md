# Auto-TRIZ Project Instructions

## TRIZ 工作流

本專案使用 Auto-TRIZ 閉環推理流程解決技術矛盾。所有 TRIZ 相關 skill/command 前綴為 `triz-`。

### 指令一覽

| 指令 | 用途 | 對應 Skill |
| :--- | :--- | :--------- |
| `/triz` | 主入口，自動路由到適當步驟 | triz-router |
| `/triz-scope` | Step 0: 問題定向 (5Why/KT/CECA) | triz-scoping |
| `/triz-model` | Step 1: 功能建模 (FA+SF) | triz-model |
| `/triz-solve` | Step 2+3: TC/PC/SF 解題 | triz-contradict |
| `/triz-verify` | Step 4: 驗證 + 下游交付 | triz-verify |
| `/triz-wi` | Step 5: 從 TRIZ 概念產出生成工程作業指導書 (WI) 體系 | triz-wi |
| `/triz-status` | 查看當前 TRIZ session 狀態 | (直接讀取 state) |

### 流程概覽

```
/triz [問題描述]
  │
  ├─ 有明確矛盾 → /triz-solve (TC 路徑)
  ├─ 功能缺失無副作用 → /triz-solve --sf-only
  ├─ 問題症狀 → /triz-scope → /triz-model → /triz-solve → /triz-verify → /triz-wi
  └─ 無法判斷 → 引導式問答
```

### 知識庫

TRIZ 靜態參照表位於 `triz_knowledge_base/`，策略文件位於 `docs/auto_triz_strategy.md`。

### Session 狀態

TRIZ session 狀態持久化於 `.claude/context/triz/`。

---

## TR 工程執行工作流

TR1-TR10 工程執行追蹤，從 TRIZ 概念凍結 (TR0) 銜接到量產釋放 (TR10)。所有 TR 相關 skill/command 前綴為 `tr-`。

### 指令一覽

| 指令 | 用途 | 對應 Skill |
| :--- | :--- | :--------- |
| `/tr` | TR 入口，儀表板 + 路由 | tr-router |
| `/tr-gate TRn` | Gate Review（TR1-TR10） | tr-gate |
| `/tr-fea WI-nn` | FEA 設定輔助 | tr-fea-assist |
| `/tr-test Vn` | 測試報告產生 | tr-test-report |
| `/tr-dfm subsystem` | DFM/DFA 審查 | tr-dfm |

### 完整開發流程

```
/triz ──→ /triz-scope ──→ /triz-model ──→ /triz-solve ──→ /triz-verify ──→ /triz-wi
 │         Step 0          Step 1          Step 2+3        Step 4           Step 5
 │         問題定向          功能建模         TC/PC/SF        驗證+CCI         WI 產出
 │                                                                            │
 │                                    ═══ TR0 概念凍結 ═══                    │
 │                                                                            ▼
 └──────────────────────── /tr (TR 入口) ◄──────────────────────── 銜接點
                              │
                              ├── /tr-gate TR1    (可行性)
                              ├── /tr-fea WI-01   (FEA 輔助)
                              │         ↓
                              ├── /tr-gate TR2    (參數鎖定)
                              ├── /tr-gate TR3    (詳細設計)
                              ├── /tr-gate TR4    (備料)
                              ├── /tr-gate TR5    (Alpha)
                              ├── /tr-test V1~V14 (測試報告)
                              ├── /tr-gate TR6    (Alpha 驗證)
                              ├── /tr-dfm shell   (DFM 審查)
                              ├── /tr-gate TR7-TR8 (Beta)
                              ├── /tr-test DVP&R  (PV 測試)
                              └── /tr-gate TR9-TR10 (量產)
```

### 狀態管理

| 檔案 | 用途 | 生命週期 |
|:-----|:-----|:---------|
| `.claude/context/triz/.triz-state.json` | TRIZ session（step 0-5） | Session 級 |
| `.claude/context/triz/.tr-state.json` | TR gate 進展（TR0-10） | 專案級 |

### 與國際標準的關係

TR = Technology Review（產品開發里程碑），非 NASA TRL。結構上最接近 VDA MLA (ML0-ML7)，品質交付物對齊 APQP（FMEA、Control Plan、PPAP）。詳見 `docs/engineering/tr_gate_framework.md`。

---

## 內容位置邊界（Content Boundary Policy）

### 判定規則

| 內容性質 | 產出者 | 消費者 | 存放位置 |
|:---------|:-------|:-------|:---------|
| Session 過程記錄 | Skill | Skill（跨步驟傳遞） | `.claude/context/triz/session-*.md` |
| 流程狀態（TRIZ） | Skill | Skill（狀態機） | `.claude/context/triz/.triz-state.json` |
| 流程狀態（TR） | Skill | Skill（狀態機） | `.claude/context/triz/.tr-state.json` |
| 工程交付物 | Skill（triz-wi） | **工程師**（人） | `docs/engineering/` |
| 方法論知識庫 | 人 | Skill（參考） | `docs/` 或 `triz_knowledge_base/` |
| Gate review 報告 | Skill（tr-gate） | **工程師**（人） | `docs/engineering/gate_reviews/` |
| 測試報告 | Skill（tr-test） | **工程師**（人） | `docs/engineering/test_reports/` |
| DFM 審查報告 | Skill（tr-dfm） | **工程師**（人） | `docs/engineering/dfm_reviews/` |

### 核心原則

1. **Skill 產出、Skill 消費** → `.claude/context/`（內部工作記憶）
2. **Skill 產出、人消費** → `docs/engineering/`（工程師交付物）
3. **人撰寫、Skill 參考** → `docs/` 或 `triz_knowledge_base/`（知識庫）
4. **狀態 JSON 只能由 Skill 修改**，不可手動編輯

### Skill 通用性原則

所有 Skill 必須**域無關（domain-agnostic）**：
- Skill 定義「做什麼」（方法論框架），不定義「用什麼」（產品規格）
- 產品規格從 `docs/engineering/` 的 WI/MC/ICD 動態讀取
- 禁止在 Skill 中硬編碼材料名稱、數值標準、測試項目

---

## Skill 使用規則

遇到 TRIZ 或 TR 相關問題時，**先透過 Skill tool 載入對應 skill 再行動**。

優先序：
1. **使用者明確指示** — 最高
2. **Skills** — 覆蓋預設系統行為
3. **預設系統提示** — 最低

## Agent

| Agent | 用途 |
| :--- | :--- |
| `triz-analyst` | TRIZ 分析推理（TC/PC/SF、矩陣查表、分離策略、SIM 評估）|
