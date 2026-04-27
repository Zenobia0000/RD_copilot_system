# RD Design Copilot｜Stakeholder Brief

> **版本**：v2.0 ｜ **日期**：2026-04-13
> **對象**：RD 主管 / PM / 決策層 / 合作夥伴
> **說明**：合併 Executive Summary v1.0 + BD Pitch v1.0，消除與 PRD 重複內容
> **配套文件**：`docs/e2e/PRD_RD_Design_Copilot.md`（完整產品需求規格）

---

## 1. Value Proposition

RD Design Copilot 是專為 e-Bike 產品線打造的**工程設計副駕**，將 RD 團隊的隱性知識、隱性假設與隱性決策，轉化為可追溯（Traceable）、可審查（Auditable）、可重用（Reusable）的數位工程資產。系統以 TRIZ 三層求解（含 L1 跨域去錨定反偏誤探索）、純算術驗證（不依賴 LLM 產數字）為兩大技術支柱，在概念設計階段即完成方案發散、假設驗證與證據閉環——將方案探索從 2 天壓縮至 0.5 天，架構級返工從 3-5 次降至 2 次以下，並實現 100% 決策可追溯。

> **一句話**：別的 AI 幫你「生想法」，這套系統幫你**生證據、生追溯、生反偏誤**。

---

## 2. Why Now — 市場時機

| 驅動力 | 說明 |
|---|---|
| **e-Bike 競爭白熱化** | 各品牌產品規格趨同，設計差異化只剩概念階段的探索深度與速度 |
| **LLM 落地窗口** | GPT-4 / Claude 等模型已具備結構化推理能力，但缺乏工程驗證層——現在是加上「純算術驗證 + 企業知識」的最佳時機 |
| **經驗流失風險** | 資深 RD 退休或轉職後，隱性知識歸零；越早建立 Knowledge Asset 機制，累積越厚 |
| **前置風險成為產業共識** | Shift-Left 趨勢要求在 CAD 前完成假設驗證，本系統正是這層基礎設施 |

---

## 3. How This Differs from ChatGPT

> 這是 RD 最常問的問題——以下逐維度對照。

| 維度 | ChatGPT / Gemini | **RD Design Copilot** |
|---|---|---|
| **知識來源** | 網路雜訊 | 企業 RAG + TRIZ KB + 種子資料 |
| **數字可信度** | LLM 幻覺 | 純算術驗證 + 資料庫真值覆寫 |
| **流程結構** | 無狀態對話 | 8 Step x 8 Gate 狀態機 |
| **假設管理** | 隱性 | Validation Passport + Evidence Matrix |
| **決策追溯** | 無 | KT Decision Record（100% 可追溯） |
| **反偏誤** | 無 | TRIZ L1 跨域去錨定 + 矛盾收斂掃描 |
| **產出可審查** | 段落文字 | 結構化工件 + Gate 判定 |

**核心差異總結**：ChatGPT 是通用對話工具；RD Design Copilot 是嵌入工程流程的決策基礎設施——LLM 負責創造、純算術負責驗證、資料庫負責累積。

---

## 4. Quantified Benefits — KPI Before / After

| 指標 | Before | After |
|---|---|---|
| 方案探索時間 | 2 天 | **0.5 天** |
| 架構級返工 | 3-5 次 | **<=2 次** |
| 假設驗證覆蓋率 | <30% | **>=80%** |
| 決策追溯率 | ~0% | **100%** |
| 單次設計評審 | 3-4 hr | **<=2 hr** |
| 經驗資產化 | 個人腦袋 | **團隊 artifact** |

**ROI 邏輯**：每次架構級返工平均消耗 2-3 週工期 + 重新打樣成本；將返工從 3-5 次降至 <=2 次，單一專案即可回收系統建置投入。

---

## 5. What We Need From Partners

### RD 側需投入

| # | 項目 | 說明 |
|---|---|---|
| 1 | **Brief 與約束** | 硬目標 / 軟目標 / 非目標 / KPI 門檻 |
| 2 | **歷史設計 Artifact** | 舊專案的矛盾、假設、決策 → 冷啟動 Seed |
| 3 | **關鍵零件真值** | datasheet、尺寸、熱/電參數 → 覆寫 LLM 幻覺 |
| 4 | **2-3 位 Senior RD** | 擔任 Design Partner，參與 Gate 審核迭代 |
| 5 | **1-2 個 Pilot 專案** | 建議選「中風險」專案作為試點 |

### BD 側負責

| # | 項目 | 說明 |
|---|---|---|
| 1 | **開發團隊** | 後端 AI (2) + 前端 (1) + BD/PM (1) |
| 2 | **外部服務採購** | LLM API (OpenAI/Claude) + Tavily + Supabase |
| 3 | **TRIZ 知識庫建置** | 39 參數、矛盾矩陣、40 原理、4 分離原則、76 標準解 |

> **RD 永遠是最終決策者**——AI 負責消除重複腦力勞動與盲點，不取代工程判斷。

---

## 6. Timeline & Phases

### 總體：6 個月、3 階段，每階段可獨立驗收

```
M1 ──── M2 ──── M3 ──── M4 ──── M5 ──── M6
├─ Phase A ──┤├─ Phase B ──┤├─ Phase C ──┤
  MVP 正向     反向 + 匯流    證據 + 結案
```

| 階段 | 期程 | 主要交付 | Gate 驗收 |
|---|---|---|---|
| **Phase A** | M1-M2 | TRIZ KB + Forward 軌 MVP + Analyst Agent | Pilot Brief → 核心矛盾自動化識別 |
| **Phase B** | M3-M4 | TRIZ L1 跨域去錨定 + Decision Hub + Pre-CAD Review | >=3 條非對標路線 + MUST 快篩通過 |
| **Phase C** | M5-M6 | Evidence Matrix + Risk Register + 知識回寫 | Pilot 結案 + 知識沉澱進企業 RAG |

### Go / No-Go 決策點

- **M2 結束**：Gate A 通過 → 繼續；未通過 → 調整範圍重跑（沉沒成本僅 6 週）
- **M4 結束**：Gate B 通過 → 繼續；未通過 → 延長 1 個月補強
- **M6 結束**：Gate C 通過 → 進入 Future Extension（設計審查自動化、製造可行性、Simulation 介接）

### 關鍵風險與緩解

| 風險 | 緩解措施 |
|---|---|
| RD 不願投入時間配合 | Phase A 結束 6 週可看成果，降低沉沒成本 |
| 歷史 Artifact 缺乏 | 內建 eBike 種子庫 + 退化路徑保證永遠有輸出 |
| LLM 幻覺影響可信度 | 純算術驗證器 + 真值覆寫（Phase A 即上線） |

---

## 7. Next Steps / Call to Action

1. **本週**：雙方確認 Pilot 專案選擇（建議 1-2 個中風險專案）
2. **下週**：Kick-off 會議，RD 指派 2-3 位 Design Partner
3. **M2 結束（6 週後）**：Gate A 驗收——看到可驗證成果，再決定是否繼續

> **Externalize. Trace. Audit.**
> 讓你的每一個設計決策，都成為下一次設計的加速器。

---

*詳細技術規格、流程定義與系統架構請參閱 `docs/e2e/PRD_RD_Design_Copilot.md`*
