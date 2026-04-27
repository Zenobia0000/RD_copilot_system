# E1x — Competitive Landscape (競品分析)

| 項目 | 內容 |
|------|------|
| **版本** | v0.1 (Draft) |
| **日期** | 2026-04-13 |
| **狀態** | 初版 — 部分欄位待補充 |
| **擁有者** | [PM 姓名] |

---

## §1 競品分類

### Tier 1 — 直接競品 (Direct Competitors)
> 提供工程設計階段系統化創新或 TRIZ 輔助的專業軟體。

- CREAX Innovation Suite
- IFR TRIZ Software (Goldfire / TechOptimizer 後繼)

### Tier 2 — 鄰近工具 (Adjacent Tools)
> PLM/知識管理平台，含 AI 或設計決策追蹤功能，但非專注早期概念階段。

- Ansys Minerva (Simulation Process & Data Management)
- Siemens Teamcenter (PLM + AI Assist)
- Jira + AI Plugins (專案追蹤 + AI 輔助)
- Notion AI (知識管理 + AI 輔助)

### Tier 3 — 通用 LLM (General-Purpose AI)
> 可被工程師用於設計探索，但無結構化流程、無證據鏈、無 Gate 機制。

- ChatGPT (OpenAI)
- Gemini (Google)
- Claude (Anthropic)

---

## §2 競品功能矩陣

| 產品 | TRIZ Support | Evidence Tracking | Gate System | AI Agent | Knowledge Reuse | 定價模式 |
|------|-------------|-------------------|-------------|----------|-----------------|---------|
| **RD Design Copilot** | AutoTRIZ (規則引擎 + LLM 混合) | Evidence Matrix (E0–E4) | 雙層 Gate (Gate X5 / Gate C) | Multi-Agent (Orchestrator + 專家 Agent) | 企業知識庫 RAG + 知識回寫 | [TBD — SaaS per-seat] |
| **CREAX Innovation Suite** | 完整 TRIZ 工具集 (矛盾矩陣, 分離原則, 76 標準解) | 無結構化證據追蹤 | 無 | 無 AI Agent | 案例庫 (需手動維護) | [TBD — Enterprise License] |
| **IFR TRIZ Software** | 經典 TRIZ 工具 + 專利分析 | 無 | 無 | 無 | 專利資料庫搜尋 | [TBD — Per-seat License] |
| **Ansys Minerva** | 無 TRIZ | 模擬結果追蹤 (非設計決策層) | 模擬工作流 Gate | 無 AI Agent (有自動化腳本) | 模擬知識庫 | [TBD — Enterprise] |
| **Siemens Teamcenter** | 無原生 TRIZ (有第三方整合) | 變更追蹤 (Change Management) | PLM Gate 流程 | Industrial Copilot (預覽) | 完整 PLM 知識庫 | [TBD — Enterprise] |
| **Notion AI** | 無 | 無 | 無 | AI 寫作助手 (非工程領域) | 團隊 Wiki | Free / Plus $10/mo / Enterprise |
| **Jira + AI** | 無 | Issue 追蹤 (非證據層) | Workflow Gate (可自訂) | Atlassian Intelligence | Confluence 知識庫 | Free / Standard $8.15/user/mo |
| **ChatGPT / Gemini** | 可對話式使用 TRIZ 但無結構化引導 | 無 | 無 | 無流程約束 | 無企業知識庫 (無 RAG) | $20/mo (Plus) / Enterprise 方案 |

---

## §3 定位圖 (Positioning Map)

```
  高 │                          ┌─────────────────┐
  流 │                          │ RD Design Copilot│
  程 │               Siemens    │ (目標位置)       │
  結 │            Teamcenter ●  └────────●─────────┘
  構 │                 ●
  化 │            Ansys Minerva    ● CREAX
  程 │                              ● IFR TRIZ
  度 │     Jira+AI ●
     │
     │  Notion AI ●
     │
  低 │  ChatGPT/Gemini ●
     │
     └──────────────────────────────────────────────
       低          領域專業度 (Domain Specificity)         高
```

> **RD Design Copilot 目標象限**: 高流程結構化 + 高領域專業度。
> 目前該象限無直接競品 — CREAX/IFR 有領域專業度但缺乏流程結構化與 AI Agent；Teamcenter 有流程但缺乏早期概念設計深度。

---

## §4 差異化楔子 (Differentiation Wedge)

### 1. 「證據鏈 + Gate」—— 唯一將 Evidence Matrix 內建於 AI 工作流的產品
- 每個 AI 建議都綁定證據等級 (E0–E4)，設計審查有跡可循。
- 競品的 AI 輸出是「一次性建議」，RD Design Copilot 的輸出是「可審查記錄」。

### 2. 「AutoTRIZ 混合架構」—— 規則引擎精確度 + LLM 泛化能力
- 傳統 TRIZ 軟體靠手動查表；通用 LLM 靠自由生成但缺乏結構。
- AutoTRIZ = 矛盾矩陣/分離原則 (規則引擎) + LLM 語意理解/原理具體化 → 兼具精確度與彈性。

### 3. 「知識回寫 + 複用」—— 設計經驗自動沉澱為企業資產
- 每個專案完成後，設計決策、矛盾解法、假設驗證結果自動回寫知識庫。
- 下一個專案可直接搜尋「類似矛盾的過往解法」，實現跨專案知識複用。

---

## §5 競爭風險

### 風險 1: Siemens / Ansys 加入 AI Copilot 功能
- **機率**: 高 — Siemens 已發布 Industrial Copilot 預覽。
- **影響**: 中 — 大廠 Copilot 可能先聚焦 CAD/CAE 層 (詳細設計)，而非早期概念階段。
- **因應**: 深耕「概念設計 + 證據驅動 Gate」利基，建立用戶黏性後再向下游擴展。

### 風險 2: 通用 LLM 能力持續增強
- **機率**: 確定 — GPT-5、Gemini 2.0 等持續升級。
- **影響**: 中 — 通用 LLM 可能做到「更好的 TRIZ 對話」，但缺乏流程約束與企業知識庫整合。
- **因應**: 競爭力來自「流程結構 + 證據鏈 + 知識回寫」，非來自「LLM 本身的聰明程度」。

### 風險 3: 客戶內部自建 (Build In-House)
- **機率**: 中 — 大型 OEM 可能嘗試用 API 自建。
- **影響**: 高 — 直接失去客戶。
- **因應**: 提供 domain-specific 方法論 (TRIZ/KT) 整合深度 + 持續迭代，使自建成本 > 採購成本。

### 風險 4: CREAX / IFR 加入 AI 能力
- **機率**: 中 — 傳統 TRIZ 軟體商可能整合 LLM。
- **影響**: 中 — 若 CREAX 加入 LLM + Evidence Tracking，將成為直接威脅。
- **因應**: 速度優勢 — 先建立用戶社群與企業知識庫護城河。

---

**下一步行動**:
- [ ] 補齊 [TBD] 定價資訊（競品官網 / 銷售詢價）
- [ ] 取得 CREAX / IFR 試用帳號進行功能深度比較
- [ ] 追蹤 Siemens Industrial Copilot 發展動態
- [ ] 季度更新本文件
