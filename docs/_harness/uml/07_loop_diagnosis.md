# 矛盾迴圈診斷與處理 (Section 5.3)

## 關鍵洞察

矛盾迴圈 (解A→惡化B→解B→惡化A) **不是新問題類型**，而是 TC 定義不完整的診斷信號。

**早期攔截原則：** 大部分定義期迴圈應在 Step 2b (OZ/OT 預篩 TC 去重) 就被合併為 PC。  
本流程處理：① 漏過預篩的殘餘　② Step 4 才浮現的解法期迴圈

## 迴圈本質

| 層次 | 描述 |
| :--- | :--- |
| **表面** | TC1 改善 A → 惡化 B；TC2 改善 B → 惡化 A（兩個 TC 在打架） |
| **實際** | 同一個底層 Px：Px↑ → A好B壞，Px↓ → B好A壞（一個未被正確定義的 PC） |

## 流程圖

```mermaid
graph TD
    START("偵測到矛盾迴圈<br/>TC1: 改善A 則 惡化B<br/>TC2: 改善B 則 惡化A")

    NATURE["迴圈本質分析<br/>表面: 兩個TC在打架<br/>實際: 同一底層Px未正確定義"]

    INTERCEPT{"攔截點確認<br/>迴圈來源？"}

    EARLY["定義期迴圈<br/>來源: TC 定義不完整<br/>應在 Step 2b 攔截"]
    LATE["解法期迴圈<br/>來源: Step 4 解法衝突<br/>需 5.3 診斷處理"]

    OVERLAP_CHECK["OZ / OT / Px 重疊檢查<br/>比較兩個 TC 的:<br/>OZ 操作區域<br/>OT 操作工具<br/>Px 參數X"]

    OVERLAP{"重疊？"}

    SAME_PC["判斷: 兩個 TC 其實是<br/>同一個 PC<br/><br/>同一底層 Px 控制兩側:<br/>Px上升 則 A好B壞<br/>Px下降 則 B好A壞"]

    REEXTRACT["回到 Section 4 OZ-OT<br/>重新提取 Px<br/>以分離原理解 PC"]

    SEPARATE{"分離原理<br/>可行？"}

    SOLVED("PC 已解決<br/>to Step 4 驗證")

    STOP_7("Section 7 喊停<br/>問題超出當前 TRIZ 範疇")

    INDEPENDENT["判斷: 不是迴圈<br/>而是兩個獨立 TC<br/>OZ/OT/Px 各不相同"]

    REORDER["回到 Section 5.1<br/>瓶頸路徑做排序<br/>依優先序逐一解決"]

    START --> NATURE
    NATURE --> INTERCEPT

    INTERCEPT -->|"Step 2b 已應處理"| EARLY
    INTERCEPT -->|"Step 4 浮現"| LATE

    EARLY -->|"若未攔截則繼續診斷"| OVERLAP_CHECK
    LATE --> OVERLAP_CHECK

    OVERLAP_CHECK --> OVERLAP

    OVERLAP -->|是| SAME_PC
    OVERLAP -->|否| INDEPENDENT

    SAME_PC --> REEXTRACT
    REEXTRACT --> SEPARATE

    SEPARATE -->|是| SOLVED
    SEPARATE -->|否| STOP_7

    INDEPENDENT --> REORDER

    style SOLVED fill:#2d6a2d,color:#ffffff,stroke:#1a4a1a
    style STOP_7 fill:#8b1a1a,color:#ffffff,stroke:#5a0a0a
    style SAME_PC fill:#4a3f6b,color:#ffffff,stroke:#2e2a4a
    style NATURE fill:#1a3a5a,color:#ffffff,stroke:#0f2540
    style OVERLAP_CHECK fill:#3a5a7a,color:#ffffff,stroke:#263f57
```

## 攔截點對照表

| 迴圈來源 | 攔截點 |
| :--- | :--- |
| 定義期迴圈 | Step 2b OZ/OT 預篩 |
| 解法期迴圈 | Step 4 → 5.3 診斷 |

## 補充說明

- **OZ/OT 重疊** 是判斷「同一 PC」的核心依據，重疊代表兩個 TC 描述的是同一物理矛盾的兩側。
- **分離原理** 包含時間分離、空間分離、條件分離、系統層次分離，任一可行即可解 PC。
- **Section 7 喊停** 表示當前問題定義框架無法容納此矛盾，需重新 scoping 或提升系統層次。
