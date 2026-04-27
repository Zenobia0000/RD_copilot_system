# Auto-TRIZ 核心概念模型 (Domain Class Diagram)

```mermaid
classDiagram
    direction TB

    class Problem {
        +type : 矛盾 | 功能缺失 | 純最佳化
        +level : A | B | C
        +subsystem : String
        routeToEntry()
    }

    class TC {
        +improveParam : P1
        +worsenParam : P2
        +candidates : Solution 2..4
        improveP1_worsensP2()
    }

    class PC {
        +px : Px
        +stateA : String
        +stateNotA : String
        pxMustBeA_andNotA()
    }

    class SF {
        +substance1 : S1
        +substance2 : S2
        +field : F
        +diagnosis : 無效 有害 不足 缺失
        matchStandardSolution()
    }

    class Px {
        +name : String
        +type : Direct | Proxy
        +sensitivity_P1 : Float
        +sensitivity_P2 : Float
    }

    class OZ {
        +location : String
    }

    class OT {
        +timepoint : String
    }

    class SeparationPrinciple {
        +type : 時間 空間 條件 系統層級
        +strategy : String
    }

    class ScientificEffect {
        +effectName : String
        +field : F
        +substance : S
    }

    class Solution {
        +field : F
        +substance : S
        +oz : OZ
        +ot : OT
    }

    class SIM {
        +phase : 粗篩 | 精篩
        +round : Int
        +maxRound : Int
        evaluate()
        totalScore()
    }

    class ComplexityCheck {
        +structural : Bool
        +energy : Bool
        +cognitive : Bool
        +evolutionAligned : Bool
        verdict()
    }

    class TechnicalDebt {
        +unresolvedPC : PC
        +reason : String
        +nextGenPriority : Int
    }

    Problem "1" --> "*" TC : 發掘
    Problem "1" --> "*" SF : 功能缺失時直接使用
    TC "1" --> "1..*" PC : OZ-OT 分析提取 Px
    PC "1" --> "1" Px : 核心參數
    PC "1" --> "1..*" SeparationPrinciple : 選擇分離策略
    SeparationPrinciple "1" --> "1" SF : 導入標準解
    SF "1" --> "*" ScientificEffect : 查找效應庫
    ScientificEffect "1" --> "1" Solution : 產出
    Px "1" -- "1" OZ : 位於
    Px "1" -- "1" OT : 發生於
    TC "*" --> "1" SIM : 多TC時評估
    Solution "1" --> "1" ComplexityCheck : Step4 驗證
    ComplexityCheck --> TechnicalDebt : 補丁且無時間
```

**概念關係說明：**

| 層級 | 工具 | 解析度 | 角色 | 產出 |
|:-----|:-----|:------|:-----|:-----|
| 1 | TC (技術矛盾) | 10x 鏡頭 | 外交官 | 啟發性方向 |
| 2 | PC (物理矛盾) | 100x 鏡頭 | 外科醫生 | 決定性分割策略 |
| 3 | SF (質-場分析) | 手術刀路徑 | 配方工程師 | 具體結構方案 |
