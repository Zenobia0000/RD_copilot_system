# Auto-TRIZ 技術摘要

> **對象**：技術副總 ｜ **閱讀時間**：5 分鐘 ｜ **深度**：可應對技術細節提問

---

## 1. 系統是什麼

- **定位**：針對電動自行車機電系統的系統性矛盾解決框架——當「改善 A 必然惡化 B」時，用結構化方法找到不妥協的解。
- **三層工具嵌套，不是平行選擇**：TC（技術矛盾，10x 放大鏡）定方向 → PC（物理矛盾，100x）找分離策略 → SF（物質-場模型，手術刀）落地為具體結構與材料。解析度逐層遞進，不可跳級。
- **六個核心概念**：
  - **TC**（Technical Contradiction）：改善參數 A 導致參數 B 惡化的取捨關係
  - **PC**（Physical Contradiction）：同一物理量需要同時大又小的自我矛盾
  - **Px**（中間物理變數）：控制 TC 兩端參數的關鍵旋鈕，是 PC 的載體
  - **OZ / OT**（操作區域 / 操作時間）：Px 發生作用的空間與時間邊界
  - **SIM**（Solution Interaction Matrix）：多矛盾場景下評估方案交互影響的矩陣
  - **SF**（Substance-Field）：用「物質 + 場」描述功能的最小物理模型

---

## 2. 怎麼運作

- **主流程（閉環 5 步）**：
  - Step 0：問題定界（5Why / KT 分析鎖定根因）
  - Step 1：功能建模（功能分析 + SF 模型 + 系統邊界）
  - Step 2：辨識 TC，從 39 參數 × 矛盾矩陣產出 2-4 個候選方向
  - Step 3：深鑽 PC — 搜尋 Px → 驗證 PC → 四種分離原理 → SF 標準解 + 科學效應
  - Step 4：原型驗證 + 4D 複雜度檢查 → 演進（出貨）或迭代回 Step 3
- **快車道**：功能缺失但無矛盾時，跳過 TC/PC，直接走 SF-only 路徑（76 標準解路由表）。
- **多矛盾策略**：先判斷是否有瓶頸 TC（解它就能削弱其他）→ 有則優先攻瓶頸；無則進 SIM 矩陣，Step 2b 預篩 + Step 3b 細篩，最多 2 輪收斂。
- **知識庫注入點**：Step 2 載入 39 參數表 + 矛盾矩陣 + 40 原理；Step 3c 載入分離原理；Step 3d 載入 76 標準解。大表用 RAG 按需注入，小表全量載入。

---

## 3. 關鍵決策閘門

- **進入分流（Entry Gate）**：問題分三級——Level C（連系統都描述不了）→ 退回用 Design Thinking；Level A（能描述但抓不到取捨）→ 從 Step 0 開始；Level B（能填 TC 句型）→ 直接進 Step 1。另有 6 種問題類型路由（已知取捨、未知故障、功能缺失、純優化、成本削減、完全未知），各走不同入口。
- **Step 2 閘門**：單一 TC → 直接進 Step 3；多 TC → 判斷有無瓶頸，有走瓶頸路徑，無走 SIM。
- **Step 4 閘門（4D 複雜度評分）**：問四題——零件增加？能源增加？認知負擔增加？符合演進趨勢？不符演進趨勢強制判 Patch；符合且 Q1-Q3 中 ≥2 個 YES 也是 Patch；其餘為 Evolution（可出貨）。
- **迴圈診斷（Loop Trap）**：表面上 TC1 和 TC2 互相打架（改 A 壞 B、改 B 壞 A），實際上是同一個 Px 的兩面——本質是一個被誤認為兩個 TC 的 PC。回到 OZ/OT 重新提取 Px 即可打破迴圈。

---

## 4. 風險控制與停止條件

- **5 個 STOP 信號**：
  1. 違反物理定律（能指出哪條定律）→ 重新定義需求
  2. 找不到解且不確定物理上是否可能 → 暫停，標記知識邊界，尋求專家
  3. 理想度持續下降（成本+危害 >> 功能）→ 重新定義需求
  4. Px 找到但四種分離原理全部失敗 → 停止
  5. SIM 兩輪後仍有 -1 且 OZ/OT 重疊 → 停止，重新思考架構
- **技術債原則**：Patch ≠ 失敗——有意識地選擇 Patch 並記錄進下一代 TRIZ backlog 是合理決策；**不記錄**才是真正的失敗。
- **早期預警**：若矛盾落在 39 參數的高難度衝突區域，提前預警需要破壞性創新預算；若場負向干涉，預警系統需要重新劃分邊界。

---

## 深入閱讀指引


| 想了解...                        | 讀這份                                                | 對應上方區塊  |
| ----------------------------- | -------------------------------------------------- | ------- |
| 所有概念的定義與關係                    | [00_domain_model.md](00_domain_model.md)           | 1       |
| 問題進入的分流邏輯                     | [01_entry_decision.md](01_entry_decision.md)       | 3       |
| 完整閉環主流程                       | [02_main_flow.md](02_main_flow.md)                 | 2       |
| Step 0 問題定界細節                 | [03_step0_scoping.md](03_step0_scoping.md)         | 2       |
| Px 搜尋與三種找不到的情境                | [04_px_search.md](04_px_search.md)                 | 2, 3    |
| 多矛盾瓶頸 vs. SIM 策略              | [05_multi_tc_strategy.md](05_multi_tc_strategy.md) | 2, 3    |
| SIM 迭代與收斂規則                   | [06_sim_iteration.md](06_sim_iteration.md)         | 2, 3    |
| 矛盾迴圈的診斷與打破                    | [07_loop_diagnosis.md](07_loop_diagnosis.md)       | 3       |
| 4D 複雜度評分（Patch vs. Evolution） | [08_complexity_check.md](08_complexity_check.md)   | 3       |
| 停止 vs. 繼續的決策框架                | [09_stop_continue.md](09_stop_continue.md)         | 4       |
| 問題全生命週期狀態機                    | [10_problem_lifecycle.md](10_problem_lifecycle.md) | 2, 3, 4 |
| 知識庫注入點與 Token 策略              | [11_kb_integration.md](11_kb_integration.md)       | 2       |


