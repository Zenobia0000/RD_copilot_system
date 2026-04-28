# 複雜度判定：補丁 vs 進化 (Section 6)

## 6.1 四維複雜度指標

| 維度 | 補丁信號 | 進化信號 |
| :--- | :--- | :--- |
| 結構 | 新增零件修正舊零件 | 現有零件多功能化 |
| 能量 | 引入新能量系統 | 利用環境資源替代 |
| 耦合 | 改A連帶影響BCD | 縮短轉換步驟 |
| 理想度 | 分母增長大於分子 | 分母趨近於零 |

---

## 6.2 & 6.3 快速判斷流程圖

```mermaid
graph TD
    A("Step 4 產出解法方案") --> Q1

    Q1{"Q1: 零件是否變多了？<br/>Structural"}
    Q1 -->|是| C1["計數 +1"]
    Q1 -->|否| Q2

    C1 --> Q2

    Q2{"Q2: 能量消耗是否變大了？<br/>Energy"}
    Q2 -->|是| C2["計數 +1"]
    Q2 -->|否| Q3

    C2 --> Q3

    Q3{"Q3: 別人理解邏輯的時間<br/>是否變長了？<br/>Cognitive"}
    Q3 -->|是| C3["計數 +1"]
    Q3 -->|否| Q4

    C3 --> Q4

    Q4{"Q4: 解法方向是否符合<br/>Section 8 至少一個演化趨勢？<br/>Evolution"}

    Q4 -->|否| PATCH_FORCED["判定: 補丁<br/>Q4 = 否 直接判補丁"]
    Q4 -->|是| COUNT{"Q1-Q3 中<br/>是 的數量 大於等於 2？"}

    COUNT -->|是| PATCH["判定: 補丁"]
    COUNT -->|否| EVOLVE["判定: 進化"]

    EVOLVE --> PASS("解法通過")
    style PASS fill:#2e7d32,color:#ffffff,stroke:#1b5e20

    PATCH --> TIME{"時間/成本<br/>允許重新深挖？"}
    PATCH_FORCED --> TIME

    TIME -->|是| BACK("回到 Step 3 PC<br/>重新深挖")
    style BACK fill:#e65100,color:#ffffff,stroke:#bf360c

    TIME -->|"否 出貨壓力"| DEBT["有意識地選擇補丁出貨"]
    style DEBT fill:#e65100,color:#ffffff,stroke:#bf360c

    DEBT --> D1["1. 記錄為 已知技術債"]
    D1 --> D2["2. 標記哪個 PC 未被真正解決"]
    D2 --> D3["3. 排入下一代產品 TRIZ 待辦"]
    D3 --> D4["4. 繼續出貨"]
```

> **注意：** 失敗不是選擇補丁，而是把補丁當成永久方案卻不記錄。
