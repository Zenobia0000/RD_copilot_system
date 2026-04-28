# One-Page STRIKE Prompt — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：生成面向跨部門與內部技術架構受眾的 one-page 說明與簡報骨架

---

## 1. 使用目的

這份 STRIKE prompt 的用途不是生成長版簡報，而是把 RD Design Copilot 壓縮成一頁也能說清楚的高層說明。

適用對象：

1. 跨部門利害關係人
2. 內部技術架構角色
3. 需要快速理解專案價值、核心流程、系統架構與協作接口的人

## 2. One-Page 必留訊息

one-page 只保留以下五塊：

1. 問題與價值
2. RDP-8 核心 flow
3. 系統節點目的與 gate/state
4. Harness-first 架構
5. 跨部門協作接口與下一步

## 3. STRIKE Prompt

```text
S — Situation
你正在協助整理一份 RD Design Copilot 的 one-page 說明，用於跨部門溝通與內部技術架構對齊。受眾不是專案直接參與者，但需要快速理解：這個系統在解什麼問題、產品開發流程如何被重構、系統架構如何支撐這件事、以及跨部門可以怎麼接入。這份輸出不是長版簡報，也不是技術白皮書，而是一頁內可讀懂的高層說明。

T — Task
請輸出一份 one-page 簡報架構，內容必須同時涵蓋：
1. 為什麼值得做
2. RDP-8 核心流程
3. 系統上每個主要節點的目的
4. 與國際標準的對標
5. harness-first 系統架構
6. 跨部門協作接口與下一步

若輸入不足，先指出資訊缺口，不要自行腦補。輸出必須是 one-page 視角，不得展開成 8 到 10 頁長版簡報。

R — Role
你是同時懂產品策略、產品開發流程與 AI/harness 架構的內部簡報顧問。你的工作是把方法論、產品流程與系統架構翻譯成跨部門可理解的 one-page 說明。

I — Input
專案背景如下：
1. 專案名稱：RD Design Copilot。
2. 核心問題：RD 前期概念設計存在高試錯成本、方向不明、知識分散三重困境。
3. 核心定位：不是 AI demo，而是把 RD 前端決策流程標準化、可追溯化、可累積化的工程流程升級平台。
4. 產品流程主軸：RDP-8，將產品開發拆成 8 種不確定性的依序消除，從 SCOPE → MAP → RESOLVE → SPECIFY → PROVE → BUILD → HARDEN → SCALE。
5. 系統節點主軸：TRIZ Session 負責前端推理閉環，TR Gate 負責後段工程執行；兩者由雙層 state/gate 串接。
6. 架構主軸：系統採 harness-first，業務邏輯主要活在 markdown skills，不在 Python domain class；CLI 與 HTTP 共用同一個 AgentLoop。
7. 對標主軸：需可對照 APQP、VDA MLA、NASA TRL、Stage-Gate。
8. 使用場景：跨部門對齊、內部技術架構說明、one-page briefing。

K — KPI
輸出必須滿足以下條件：
1. 一頁內可理解，不可過度展開。
2. 每個區塊都要回答明確問題，而不是堆砌術語。
3. 技術詞若出現，需立即翻成管理或產品開發語言。
4. 同時能讓跨部門角色與技術架構角色看懂自己關心的部分。
5. 必須清楚區分「產品流程」、「系統節點目的」與「系統實作架構」三個層次。
6. 最後要有明確的協作或下一步建議。

E — Example
請用以下格式輸出：
- One-page 總標題
- 一句話定位
- 版面分區（5 塊以內）
- 每塊回答的核心問題
- 每塊 key message
- 每塊建議視覺元素
- 建議資訊層級（先看什麼、後看什麼）
- 最後的 cross-team action / CTA
```

## 4. 建議輸入來源

生成時優先引用下列文件：

1. `docs/planning/02_prd.md`
2. `docs/planning/18_flow_contract.md`
3. `docs/methodology/DK-04--data-model-and-gate.md`
4. `docs/planning/05_architecture.md`
5. `docs/planning/08_project_structure.md`
6. `docs/planning/ppt/19_internal_pitch_strategy.md`

## 5. 使用提醒

1. 不要把 one-page 寫成功能列表。
2. 不要把 one-page 寫成純架構圖說。
3. 先讓人看懂「為什麼重要」，再讓人看懂「怎麼運作」與「怎麼接入」。
4. 若受眾更偏技術架構，可加重 harness 分層；若更偏跨部門，可加重流程與接口，但不可丟掉系統主體。
