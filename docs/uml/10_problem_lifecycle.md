# 問題生命週期狀態機 (State Machine)

```mermaid
stateDiagram
    [*] --> EntryRouting

    state EntryRouting {
        [*] --> CheckLevel
    }

    state ExternalFramework {
        [*] --> DT_JTBD_AD
        DT_JTBD_AD: 採用外部框架 DT / JTBD / AD
    }

    state Done_Evolution {
        [*] --> SolutionLanded
        SolutionLanded: 解法落地 矛盾解除 系統進化
    }

    state Ship_TechDebt {
        [*] --> PatchShip
        PatchShip: 補丁出貨 接受技術債 帶條件出貨
    }

    state Stop_Redefine {
        [*] --> RedefineRequirements
        RedefineRequirements: 重新定義需求 問題無解或需求錯誤
    }

    state Step0 {
        [*] --> FiveWhy
        FiveWhy: 五Why因果定向
        KT_IsIsNot: KT Is/Is Not
        CECA: CECA因果鏈分析
        Step0Gate: Step0決策閘門

        FiveWhy --> KT_IsIsNot
        FiveWhy --> CECA
        KT_IsIsNot --> CECA
        CECA --> Step0Gate
    }

    state Step1 {
        [*] --> FA
        FA: FA組件交互圖
        SFModel: SF模型建立
        Boundary: 子系統邊界定義

        FA --> SFModel
        SFModel --> Boundary
    }

    state Step2 {
        [*] --> TCCandidates
        TCCandidates: TC候選解法
        BottleneckJudge: 瓶頸判斷

        TCCandidates --> BottleneckJudge
    }

    state Step2b {
        [*] --> OZ_OT_PreScreen
        OZ_OT_PreScreen: OZ/OT預篩
        SIMEval: SIM評估

        OZ_OT_PreScreen --> SIMEval
    }

    state Step3 {
        [*] --> PxSearch
        PxSearch: 3a Px搜索
        PCVerify: 3b PC造句驗證
        Separation: 3c 分離原理
        SFEffect: 3d SF科學效應

        PxSearch --> PCVerify
        PCVerify --> Separation
        Separation --> SFEffect
    }

    state Step3b {
        [*] --> FineSIM
        FineSIM: 精篩SIM
        SIMConverge: SIM收斂判斷

        FineSIM --> SIMConverge
    }

    state Step4 {
        [*] --> PxSepVerify
        PxSepVerify: Px分離驗證
        FourQuestions: 複雜度四問
        NewTCCheck: 新TC檢查

        PxSepVerify --> FourQuestions
        FourQuestions --> NewTCCheck
    }

    %% Entry routing
    CheckLevel --> ExternalFramework: Level C 無法描述系統
    CheckLevel --> Step0: Level A 知道不滿意
    CheckLevel --> Step1: Level B 能填TC造句
    CheckLevel --> Step1: 功能缺失 無矛盾 SF-only快速通道

    %% Step 0 exits
    CECA --> Stop_Redefine: 無法收斂
    Step0Gate --> Step1: 涉及組件交互
    Step0Gate --> Step2: 根因已鎖定 跳步

    %% Step 1 to Step 2
    Step1 --> Step2: 功能建模完成

    %% Step 2 exits
    Step2 --> Step3: 單TC 直接深挖
    Step2 --> Step3: 有瓶頸
    Step2 --> Step2b: 多TC 需SIM預篩

    Step2b --> Step3: 預篩後進入深挖

    %% Step 3 exits
    Step3 --> Step4: 單TC 有明確Px
    Step3 --> Step4: 瓶頸已解
    Step3 --> Step3b: 多TC 需精篩SIM
    PxSearch --> Stop_Redefine: 全部耗盡且4.2.2無出路

    %% Step 3b exits
    Step3b --> Step3: -1 新TC 繼續深挖 最多2輪
    Step3b --> Step4: SIM收斂 進入驗證
    Step3b --> Stop_Redefine: SIM不收斂

    %% Step 4 exits
    Step4 --> Done_Evolution: 矛盾解除 系統進化
    Step4 --> Step3: 補丁解 還有時間
    Step4 --> Ship_TechDebt: 補丁解 無時間
    Step4 --> Step1: 發現獨立新TC

    %% Terminal states
    Done_Evolution --> [*]
    Ship_TechDebt --> [*]
    Stop_Redefine --> [*]
    ExternalFramework --> [*]
```

## 狀態說明

### 入口狀態

| 入口 | 觸發條件 | 導向 |
| :--- | :--- | :--- |
| Level C | 無法描述系統，問題本身不清晰 | 外部框架（DT / JTBD / AD） |
| Level A | 知道不滿意，但未能結構化問題 | Step 0 問題定向 |
| Level B | 能填 TC 造句，矛盾已可描述 | Step 1 功能建模 |
| 功能缺失 | 無矛盾，純功能缺失 | Step 1（SF-only 快速通道） |

### 核心步驟

| 步驟 | 主要活動 | 關鍵輸出 |
| :--- | :--- | :--- |
| Step 0 | 5Why / KT Is-Is Not / CECA | 根因鎖定或喊停 |
| Step 1 | FA 組件交互圖 / SF 模型 / 邊界定義 | 功能模型 |
| Step 2 | TC 候選解法 / 瓶頸判斷 | 矛盾清單 |
| Step 2b | OZ/OT 預篩 / SIM 評估 | 精簡後的矛盾集 |
| Step 3 | Px 搜索 / PC 造句 / 分離原理 / SF+科學效應 | 矛盾解法 |
| Step 3b | 精篩 SIM（最多 2 輪） | 收斂的矛盾集 |
| Step 4 | Px 分離驗證 / 複雜度四問 / 新 TC 檢查 | 原型驗證結果 |

### 終止狀態

| 終止狀態 | 觸發條件 | 意義 |
| :--- | :--- | :--- |
| **完成（進化）** | Step 4 矛盾解除 | 系統進化，問題根本解決 |
| **出貨（技術債）** | Step 4 補丁解 + 無時間 | 接受技術債，條件出貨 |
| **喊停（重新定義需求）** | CECA 無法收斂 / Px 耗盡 / SIM 不收斂 | 問題本身需要重新定義 |
| **外部框架** | Level C 入口 | 採用 DT / JTBD / AD 等外部方法 |
