# One-Page 跨部門技術架構版 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：面向跨部門協作與內部技術架構角色的一頁式完整稿

---

## 標題

**RD Design Copilot：把產品流程、系統節點與 harness 架構接成同一條可執行管線**

## 一句話定位

RD Design Copilot 正在把 RD 前期高試錯、低追溯、知識分散的設計流程，轉成一條由 `RDP-8` 流程框架、`雙層 gate/state`、以及 `harness-first runtime` 共同支撐的工程決策系統。

## 1. 為什麼這件事重要

### 問題不在於工具少，而在於流程沒有被工程化
- 問題常在後段才被看見，返工成本高
- 前期判斷過度依賴資深工程師經驗
- 矛盾、假設、證據與決策記錄沒有形成可追溯主線
- 知識散落在專案、會議與文件中，難以累積成組織能力

### 這個系統要換來的結果
- 讓高成本風險更早暴露
- 讓方案探索與 gate 判斷可追溯
- 讓設計知識能回寫與複用
- 讓跨部門協作有共同節點與共同語言

## 2. 產品流程主線：RDP-8

### 核心概念
RDP-8 把產品開發拆成 8 種不確定性的依序消除，而不是把「概念設計」當成一個模糊黑箱。

### 主線
- `P0 SCOPE`：問題不確定性
- `P1 MAP`：系統不確定性
- `P2 RESOLVE`：解法不確定性
- `P3 SPECIFY`：規格不確定性
- `P4 PROVE`：物理不確定性
- `P5 BUILD`：整合不確定性
- `P6 HARDEN`：製程不確定性
- `P7 SCALE`：規模不確定性

### 重點
`P0-P3` 是發明性前端，`P4-P7` 是工程性後端，兩者的橋接點是 `G3 / TR0 / Concept Frozen`。

## 3. 系統節點主線：雙層 gate / state

### 前端推理層
`TRIZ Session`
- 管轄 `P0 → P3`
- 代表每次問題求解的 session 級推理狀態
- 核心關注：矛盾、解法、complexity、evidence、cad readiness

### 後端工程層
`TR Gate`
- 管轄 `P4 → P7`
- 代表專案級的工程成熟度推進
- 核心關注：TR1-TR10 gate、v-test、風險、文件狀態

### 每個 gate 實際在確認什麼
- `G0`：我知道問題在哪
- `G1`：我知道系統怎麼運作
- `G2`：我知道怎麼解矛盾
- `G3`：規格已凍結，可以開始做
- `G4`：模擬證明物理可行
- `G5`：實體原型證明設計可行
- `G6`：工廠能穩定地做出來
- `G7`：大量生產沒問題

## 4. 對標國際標準

### 這套方法不是憑空發明
它可對照現有國際產品開發框架，但補上前端發明性流程的缺口。

### 對標關係
- `APQP`：對齊後段品質交付物與量產治理
- `VDA MLA`：對齊 milestone / maturity 評估
- `NASA TRL`：對齊技術成熟度推進
- `Stage-Gate`：對齊產品開發節奏與 gate 管理

### 差異化價值
傳統框架多半把前端概念階段處理得太粗，RDP-8 則把前端拆成 `SCOPE → MAP → RESOLVE` 三段，讓發明性流程也能被系統化管理。

## 5. 系統架構主線：Harness-first

### 核心原則
- 業務邏輯活在 markdown skills，不在 Python domain class
- harness runtime 負責載入、執行、調度與事件流
- state 用 filesystem JSON 持久化
- CLI 與 HTTP 共用同一個 `AgentLoop`

### 主要分層
- Interface：CLI / HTTP
- Core Runtime：`AgentLoop`
- Loaders：skill / command / agent
- Tooling：filesystem / web / agent / TRIZ domain tools
- SSOT：`.claude/`、`docs/methodology/`、`docs/engineering/`

### 架構意義
這種做法把「流程文件」變成「可執行流程」，讓方法論、系統 runtime 與工程交付物放在同一條鏈上。

## 6. 跨部門怎麼接入

### PM / 產品
- 提供問題場景、優先順序、導入節點

### RD / Domain
- 提供真實案例、約束、失效模式、設計規則

### 架構 / Backend
- 穩定 runtime、管理 tool 邊界、規劃擴充與持久化演化

### 品質 / 測試 / 製造
- 補後段 gate、驗證策略、導入條件、實際量產接口

## 7. 建議下一步

1. 選一個真實試點問題
2. 指定跨部門接口窗口
3. 用一輪完整流程驗證：
   - `問題定義`
   - `矛盾解析`
   - `規格凍結`
   - `gate 交接`
   - `工程文件產出`

## 最後一句

這個專案真正的價值，不只是讓 AI 參與設計，而是讓產品流程、系統節點與系統架構第一次被接成同一條可執行、可追溯、可擴張的工程主線。
