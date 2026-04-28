# One-Page 文案版 — 可直接貼進 PPT

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Active`
**用途**：可直接貼進 one-page PPT 的文案版

---

## 建議總標題

**RD Design Copilot：把前端設計決策流程變成可工程化的系統**

## 一句話定位

RD Design Copilot 正在把 RD 前期高試錯、低追溯、知識分散的設計流程，轉成一條可追溯、可驗證、可累積的工程決策與執行管線。

## Block 1｜問題與價值

### 小標
**RD 前期最大的成本，不是工具不夠，而是問題太晚被看見**

### 文案
- 高試錯成本：很多設計問題在後段才暴露，返工代價高
- 初期方向不明：缺少系統化方法提早判斷 trade-off
- 知識分散難利用：經驗、失效、規則沒有沉澱成可複用系統

### 對應價值
- 更早看見風險
- 更少架構級返工
- 更快前期判斷
- 更可累積的組織知識

## Block 2｜核心流程

### 小標
**RDP-8：把產品開發拆成 8 種不確定性的依序消除**

### 文案
- `SCOPE`：定義真正的問題
- `MAP`：理解系統怎麼運作
- `RESOLVE`：找出矛盾怎麼解
- `SPECIFY`：把概念凍結成規格
- `PROVE`：確認物理上行得通
- `BUILD`：確認整合後能運作
- `HARDEN`：確認製程可穩定複製
- `SCALE`：確認量產可釋放

### 補一句
這不是多一套流程術語，而是把原本靠經驗跳躍的決策，改成可逐步驗證的開發主線。

## Block 3｜節點目的與對標

### 小標
**每個 Gate 都在確認一件事：某種不確定性是否已被消除**

### 文案
- `G0`：我知道問題在哪
- `G1`：我知道系統怎麼運作
- `G2`：我知道怎麼解矛盾
- `G3`：規格已凍結，可以開始做
- `G4-G7`：一路驗證物理、整合、製程與量產能力

### 對標語句
這套方法可對照 `APQP`、`VDA MLA`、`NASA TRL` 與 `Stage-Gate`，但補強了傳統方法在前端發明性流程的盲區。

## Block 4｜系統架構

### 小標
**Harness-first：讓流程知識可執行，而不是只停在文件裡**

### 文案
- Interface：CLI / HTTP
- Core Runtime：`AgentLoop`
- Loader：skill / command / agent loaders
- Tools：filesystem / web / agent / TRIZ domain tools
- SSOT：`.claude/` + `docs/engineering/`

### 核心原則
- 業務邏輯活在 markdown skills
- Python runtime 負責執行、調度與狀態流轉
- state 以 filesystem JSON 持久化，不靠人腦記憶

## Block 5｜跨部門接口與下一步

### 小標
**這件事要變成組織能力，需要跨部門一起補齊**

### 文案
- 產品 / PM：定義場景、優先順序、導入節點
- RD / Domain：提供真實案例、約束、設計規則
- 架構 / Backend：穩定 harness runtime、tooling、擴充邊界
- 品質 / 測試 / 製造：補後段 gate 驗證與導入接口

### CTA
- 選一個試點場景
- 選一個合作接口
- 定義下一輪要驗證的 gate / capability

## 版面建議

- 左上：問題與價值
- 中央：RDP-8 flow
- 右上：節點目的與國際標準對標
- 左下：harness 架構
- 右下：跨部門 action

## 備註

這份文案刻意控制在 one-page 可用密度，適合直接拆成單頁 PPT 文字框，不適合再展開成長段落。
