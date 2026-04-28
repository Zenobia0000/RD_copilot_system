# 面試報告審查筆記

## 評估結論：目前不合格（Tesla / Google 標準）

結構好、深度夠，但缺乏「證據」。架構設計能力展示了，但工程實踐能力沒有。

---

## 必須補的 5 件事

### 1. 至少一個完整案例的真實 trace

不是假設的「馬達散熱」，是你真的用這套系統跑過的案例：
- 輸入了什麼
- Router 判到哪條路（附截圖或 JSON state）
- 矛盾矩陣查出什麼
- 分離策略選了哪個、為什麼
- 最終產出的工程規格書長什麼樣
- **哪裡系統判斷錯誤，你手動修正了**

> 面試官要看的不是「系統多完美」，是「你怎麼跟系統協作」。

### 2. 真實的失敗敘事（選 2-3 個，講深不講多）

把 F1-F7 砍成 2-3 個真正刻骨銘心的：

**格式**：
```
當時在做什麼 → 預期什麼結果 → 實際發生什麼（附具體現象）
→ 我的第一個假設 → 為什麼錯 → 第二個假設 → 最終發現的根因
→ 修了什麼 → 修完後的效果（有數字）
```

不要 7 個整齊的表格。要 2 個混亂但真實的故事。

### 3. 量化數據（哪怕是小樣本）

跑 5-10 個真實 TRIZ 問題，記錄：
- 路由正確率（Router 判對幾次）
- 每步的 token 用量（實際值 vs 預估值）
- 端到端耗時（分鐘）
- 解法品質（你自己用 4D 評分卡打分）
- 至少 1 個失敗案例（系統產出了錯誤答案）

> N=5 也比 N=0 強一百倍。

### 4. 技術選型比較（為什麼不用 LangChain / CrewAI）

| 方案 | 優點 | 為什麼沒選 |
|:-----|:-----|:-----------|
| LangChain + RAG | 成熟生態、文件多 | 需要 Python runtime，我的場景是 prompt-native，不需要 code execution |
| CrewAI / AutoGen | Multi-agent 框架 | 過度設計——我只需要 5 個 agent，不需要通用框架的 overhead |
| 自建 FastAPI + OpenAI API | 完全控制 | 需要寫 orchestration code、部署 server、管理 API key，ROI 不符 |
| **Claude Code Harness** | 零 infra、Skill 即邏輯、原生 session | **缺點：不可測試、不可 scale、依賴 Claude Code 平台** |

> 關鍵：**必須講出選擇的缺點**。只講優點 = 沒有工程判斷力。

### 5. 誠實的局限性章節

加一個 Part：「Known Limitations & What I'd Do Differently」

- **不可自動化測試**：Prompt 改了不知道會不會壞，目前只能人工走流程驗證
- **延遲**：每步是一次完整 Opus 呼叫，5 步走完可能 5-10 分鐘（不是 30 分鐘那個假數字）
- **精度未驗證**：矛盾矩陣查表正確率未知、分離策略選擇正確率未知
- **單人使用**：沒有多人協作、沒有權限管理、沒有版本控制（除了 git）
- **如果重做**：我會先建一個 evaluation framework，用 10 個已知答案的 TRIZ 案例做 ground truth，再迭代架構

---

## 加分項（有了會大幅提升）

### A. Evaluation Framework 設計

如果你能展示「我知道怎麼測量這套系統的品質」：

```
Ground Truth 案例庫（10 個已知解的 TRIZ 問題）
        │
        ▼
  自動化 Runner（/triz → /triz-solve → /triz-verify）
        │
        ▼
  比對產出 vs Ground Truth
        │
        ▼
  Metrics：路由正確率、參數映射正確率、
           分離策略匹配率、工程規格書完整度
```

即使還沒做完，光是「有這個設計」就展示了 Google 級別的 evaluation thinking。

### B. 成本分析

每次完整流程的 API 成本：
- Opus 每步 input/output tokens
- 5 步加總
- 對比人工 2-3 天的工程師成本

### C. 架構演進 Roadmap

V7 → V8 你會做什麼？
- 加 evaluation framework
- 加 prompt regression test
- 考慮 Sonnet 替代 Opus（成本 vs 品質取捨）
- 考慮 structured output (JSON mode) 替代自由文字

---

## 針對 Tesla vs Google 的調性差異

### Tesla 面試官在意的

- **Physics-grounded**：你的系統真的能產出物理上可行的方案嗎？有沒有物理專家驗證過？
- **First principles**：你為什麼選這個架構？從需求推導出來的，還是看到什麼 pattern 就套的？
- **Speed**：Elon 文化——你多快做出來的？迭代速度？
- **Impact**：對產品/團隊的實際影響是什麼？

→ 強調：真實案例 trace + 物理驗證 + 快速迭代的過程

### Google 面試官在意的

- **Scale**：如果 100 個工程師同時用，架構撐得住嗎？
- **Reliability**：SLA 是什麼？失敗時怎麼 graceful degrade？
- **Testing**：怎麼測？coverage 多少？regression 怎麼防？
- **Data-driven**：決策有數據支持嗎？

→ 強調：evaluation framework 設計 + 技術選型比較 + 已知局限的誠實陳述

---

## 一句話總結

> 目前的報告像「架構設計文件」，不像「工程實踐報告」。
> 差的不是深度，是**證據**和**誠實度**。
> 加上真實 trace、真實數據、真實失敗故事、和已知局限，就是合格的報告。
