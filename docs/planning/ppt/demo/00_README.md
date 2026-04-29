# Demo Deck（普通人版）— 使用說明

> **用途**：對跨部門同事與主管做 10-15 分鐘 demo，召募試用者 / 內部推廣
> **受眾**：非技術背景同事與主管，對 TRIZ / RDP-8 不熟悉
> **基礎**：以 eBike mid-drive coaxial 真實 session（CCI 0.3125 / Gate P Go / 22 份工程交付物）為案例貫穿
> **與既有 deck 區別**：`19_~34_*.md` 是內部 pitch / leadership 版本，技術深度高；本 deck（`demo/`）是面向**普通人**的精簡版

---

## 為什麼有這份 deck

`docs/planning/ppt/` 下既有 16 份簡報素材偏內部審查、技術深度高，缺一份「**從痛點故事 → 解法 → 技術 → 行動**」一氣呵成的精簡敘事弧線版本。本 deck 12 頁、控制在 10-15 分鐘，目的是讓不熟此產品的同事或主管在一場會議內接收完整訊息並產生試用意願。

---

## 大綱（時間配比 3+4+3+2 分鐘）

| 區塊 | 頁碼 | 主題 | 預計時間 |
|:-----|:-----|:-----|:--------|
| **A. WHY**（痛點與承諾）| 01-04 | 場景故事 → 三大痛點 → 我們的承諾 | 3 min |
| **B. WHAT**（解法 + 案例）| 05-07 | 流程一覽 + eBike 真實案例 | 4 min |
| **C. HOW**（技術分層）| 08-10 | 架構金字塔 + 雙引擎 + 多 Agent | 3 min |
| **D. IMPACT + CTA**（價值 + 行動）| 11-12 | 分眾價值 + 試用 CTA | 2 min |

---

## 每頁明細

| # | 檔案 | 訊息 | 視覺類型 |
|:--|:-----|:-----|:--------|
| 01 | `01_cover.md` | 從點子到量產，AI 陪你少走 6 個月冤枉路 | Hero icon + tagline |
| 02 | `02_scene_story.md` | 一個 RD 啟動新專案的真實困境 | 時間軸故事 |
| 03 | `03_three_pain_points.md` | 試錯貴 / 迷航 / 失憶 | 三欄痛點卡 |
| 04 | `04_our_answer.md` | 從「事後消防」到「事前體檢」 | Before/After 對比 |
| 05 | `05_flow_overview.md` | 問題 → 矛盾 → 方案 → 工程交付 | 4 段流程圖 |
| 06 | `06_ebike_case_part1.md` | eBike 中置馬達 4 個衝突目標 | 規格 + 矛盾標註 |
| 07 | `07_ebike_case_part2.md` | AI 拆解 3 個矛盾，產出 22 份工程文件 | 量化結果卡片 |
| 08 | `08_architecture_pyramid.md` | 系統長這樣（四層金字塔）| 4 層金字塔圖 |
| 09 | `09_dual_engine_workflow.md` | TRIZ + TR 雙引擎，G3 是分水嶺 | 雙引擎流程圖 |
| 10 | `10_agents_and_knowledge.md` | 多 AI 並行 + 知識庫 = 越用越聰明 | Agent 拓撲圖 |
| 11 | `11_role_value.md` | PM / RD / 主管 / 製造 / 品保 各得其所 | 5 角色卡片 |
| 12 | `12_cta_get_started.md` | 三步驟開始試用 | 行動清單 |
| **A1** | `13_appendix_tech_stack.md` | **Appendix**：Tech Stack + AI Agent Patterns + Data Models | 技術深度補充（不在 12 分鐘主流程，Q&A backup）|

---

## 每頁 Markdown 結構

每個 .md 檔遵循以下結構：

```markdown
# {頁碼}_{slug}.md

## Slide 標題
（這頁要傳達的核心訊息，不是空話）

## Speaker Notes
- 講者口條 1-2 句（口語化）
- 與上一頁的銜接 / 與下一頁的鉤子

## 視覺布局
- 主視覺類型 / 排版方向 / 配色提示

## 重點內容
- ≤ 5 條 bullet（每條 ≤ 15 字）

## 數據 / 引用
- 數字出自哪份文件（line number）

## 素材引用
- 圖檔路徑或既有 mermaid / UML 檔
```

---

## 如何串成 deck

### 選項 1：Marp（推薦）

```bash
# 先合併 12 頁成單一檔（不含 README）
cat 01_*.md 02_*.md 03_*.md 04_*.md 05_*.md \
    06_*.md 07_*.md 08_*.md 09_*.md 10_*.md \
    11_*.md 12_*.md > _combined.md

# 用 Marp 渲染 PDF
marp _combined.md --pdf
```

### 選項 2：Reveal.js / Slidev

12 個檔案各為一個 slide，用 `---` 分隔可直接餵給 Slidev。

### 選項 3：人工搬到 PowerPoint / Google Slides

每個 .md 提供：標題、講者 notes、視覺布局描述、bullet 重點。設計師可依此排版。

---

## 驗收標準

1. **可讀性**：找一位不熟此產品的同事讀完 12 頁，5 分鐘內能回答：
   - 這個產品解決什麼問題？
   - 它怎麼做到？
   - 我為什麼要試用？

2. **時長**：講完一輪落在 10-15 分鐘區間（每頁 1 分鐘 ±20%）

3. **技術深度**：技術頁（08, 09, 10）共 3 頁，且每頁都有「為什麼這對你重要」的業務語言收尾

4. **eBike 案例可信度**：頁 06-07 的數據與 `.claude/context/triz/session-2026-04-28-1500-eBike-MidDrive-Coaxial.md` 完全一致

5. **CTA 明確**：頁 12 有具體三步驟 + 真實聯絡方式

---

## 後續可選擴充

- 製作 5 頁超短版（電梯演講）— 從 12 頁挑核心：01 / 04 / 07 / 10 / 12
- 加入競對比較頁（vs CAD/CAE / vs 一般 LLM 助手）
- 加入 ROI 模型（節省時間 × 人力成本 × 案件數）

## Appendix 使用方式

- `13_appendix_tech_stack.md` 不放在主流程裡跑，**只在 Q&A 階段被問到時翻出來**
- 適用情境：技術同事問「跟 LangChain 比？」「為什麼用 Claude？」「資料怎麼存？」
- 內容包含：全棧架構、10 種 AI agent design pattern、13 entity 資料模型、13 skill catalog、與業界 framework 比較、3 個常見問題答覆
- 主流程的 08-10 頁也已加入 AI agent 術語（ReAct / RAG / Map-Reduce / Tool Use / Structured Reasoning 等）+ icon，但保持普通人可懂

---

## 來源素材

| 用途 | 路徑 |
|:-----|:-----|
| 4 大價值支柱 + KPI | `docs/planning/ppt/19_internal_pitch_strategy.md`, `25_block1_problem_and_value.md` |
| RDP-8 8 階段流程 | `docs/planning/18_flow_contract.md`, `docs/planning/ppt/26_block2_rdp8_core_flow.md` |
| eBike session 完整資料 | `.claude/context/triz/session-2026-04-28-1500-eBike-MidDrive-Coaxial.md` |
| Harness 5 層架構 + Skill 清單 | `docs/planning/ppt/28_block4_harness_architecture.md` |
| 6 類目標用戶 user stories | `docs/planning/02_prd.md` US-101~402 |
| 11 張 Mermaid UML | `docs/methodology/uml/00-11_*.md` |
