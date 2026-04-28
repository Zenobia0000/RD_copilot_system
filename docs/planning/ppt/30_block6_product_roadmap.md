# Block 6 Deep-Dive — 產品 Roadmap

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：Block 6「產品 Roadmap」的單頁展開稿，說明系統從現在到 GA 的能力演化路線

---

## 1. 這頁要回答的一個問題

> 這個系統的能力會怎麼長出來？現在在哪裡、下一步去哪裡、最終長什麼樣子？

## 2. 一句話 Key Message

> 系統不是一次做完的——它沿著 RDP-8 的 Phase 逐步長出能力，從 TRIZ 前端推理，到 TR 工程執行，再到跨專案知識累積。

## 3. 版面配置建議

```
┌──────────────────────────────────────────────────────────────┐
│                           頁面標題                             │
│  從 PoC 到 GA：能力沿著 RDP-8 逐步長出來                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  A. 三階段時間軸（上半頁）                                      │
│                                                              │
│  PoC 已完成        MVP 2026-Q3        Beta 2026-Q4    GA 2027-Q1│
│  ──●──────────────────●──────────────────●──────────────●──  │
│    │                  │                  │              │     │
│    TRIZ 引擎          Pre-CAD UX         KT Decision   Knowledge│
│    RDP-8 框架         多用戶             Devil's        Agent   │
│    雙層 Gate/State    正式 Gate UI       Advocate       跨專案  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  B. 四大 Epic 能力疊加圖（左下）    C. Skill 擴充路線（右下）    │
│                                                              │
│  Define → Diverge → Converge → TR    新 Skill 對應 Phase      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 4. 主要內容

### A. 三階段里程碑

| 階段 | 時間 | 狀態 | 核心能力 | RDP-8 覆蓋 |
|:-----|:-----|:-----|:---------|:-----------|
| **PoC** | 已完成 | Done | TRIZ 推理閉環（Step 0-5）、RDP-8 流程框架、雙層 gate/state、WI/MC/ICD 產出 | P0-P3 + TR0 |
| **MVP** | 2026-Q3 | Next | 多用戶使用、正式 Pre-CAD UX、Gate Review UI、完整 TR1-TR10 流程 | P0-P7 全覆蓋 |
| **Beta** | 2026-Q4 | Planned | KT Decision 追溯、Devil's Advocate 挑戰、跨部門決策可見度 | P3-P5 強化 |
| **GA** | 2027-Q1 | Planned | Knowledge Agent（跨專案知識回寫）、≥5 個完成專案驗證 | P7 + 跨專案 |

### B. 四大 Epic 能力疊加

| Epic | 名稱 | 覆蓋範圍 | 關鍵 User Story | 上線階段 |
|:-----|:-----|:---------|:----------------|:---------|
| **Epic 1** | Define（問題定義） | P0 SCOPE | US-101 多模態上傳 + AI 約束萃取、US-102 七類蘇格拉底問答、US-103 Gate D2 | PoC → MVP |
| **Epic 2** | Diverge（解法發散） | P1-P2 | US-201 TRIZ 三路徑解題、US-202 Decision Hub、US-203 Pre-CAD 5D 審查 | PoC → MVP |
| **Epic 3** | Converge（收斂決策） | P3 | US-301 CAD 完成度確認、US-302 Black Hat 挑戰、US-303 KT Decision Log | Beta |
| **Epic 4** | TR Engineering | P4-P7 | US-401 Gate Review 自動報告、US-402 WI/ICD/MC 自動產出 | MVP → GA |

### C. Skill 擴充路線

| 觸發條件 | 新 Skill | 對應 Phase | 上線目標 |
|:---------|:---------|:----------|:---------|
| 多用戶使用 + 正式 Pre-CAD UX | `precad-review` | P3 SPECIFY | MVP Q3 |
| 跨部門決策追溯需求 | `kt-decision` | P3-P5 | Beta Q4 |
| Post-CAD 審查需求 | `devil-advocate` | P5 BUILD | Beta Q4 |
| ≥5 個完成專案 | `knowledge-agent` | P7 SCALE + 跨專案 | GA Q1/27 |

### D. 架構演化路線

| 版本 | 架構型態 | 特徵 |
|:-----|:---------|:-----|
| **v1.0**（現在） | Harness monolith | 單進程、filesystem SSOT、CLI 為主 |
| **v2.0**（MVP） | TRIZ service 分離 | TRIZ 引擎獨立、HTTP API、多用戶 |
| **v3.0**（GA+） | Full microservices | 各 skill 獨立部署、事件驅動、水平擴展 |

## 5. 建議視覺元素

| 元素 | 類型 | 內容描述 |
|:-----|:-----|:---------|
| **時間軸** | 水平箭頭 + 4 個里程碑點 | PoC（已完成）→ MVP（Q3）→ Beta（Q4）→ GA（Q1/27），每點下方列能力 |
| **Epic 疊加圖** | 4 層漸層條 | 從下到上：Define → Diverge → Converge → TR，標示上線階段 |
| **Skill 擴充路線** | 時間軸 + 方塊 | 4 個新 Skill 掛在時間軸對應位置，標示觸發條件 |
| **架構演化** | 3 格演進箭頭 | v1.0 → v2.0 → v3.0，每格一句話 |

## 6. 口條骨架（25 秒）

> 這頁是產品路線圖。最左邊 PoC 已完成——TRIZ 推理引擎跟 RDP-8 框架都已經跑起來了。下一個里程碑是 Q3 的 MVP，主要補上多用戶支持跟正式的 Gate Review UI。Q4 Beta 加入 Devil's Advocate 跟 KT Decision 追溯。最終目標是明年 Q1 的 GA，到時候系統要能做到跨專案的知識回寫。下面是 4 個 Epic 的能力疊加順序——從問題定義開始，一路疊到 TR 工程執行。

## 7. 來源文件索引

| 內容 | 來源 |
|:-----|:-----|
| 時程目標（MVP/Beta/GA） | `docs/planning/02_prd.md` §Project Overview |
| 四大 Epic 定義 | `docs/planning/02_prd.md` §4 Core Epics |
| Skill 擴充觸發條件 | `docs/planning/18_flow_contract.md` §Phased Skill Build-Out |
| 架構演化路線 | `docs/planning/05_architecture.md` §Architecture Evolution |
| 目前已完成能力 | `docs/planning/ppt/19_internal_pitch_strategy.md` §Current Capabilities |
