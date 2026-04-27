# DK-05 — 領域底盤（AICBD 工業電腦視覺）

> 製造現場的硬約束，TRIZ 解法在此 gate 失敗時設計就被擋下。
> SSOT: `docs/_harness/interview/domain_fundamentals.md` + `interview/domain_research/{battle_manual.md, industrial_cv_paradigms.md}`。

---

## §1 應用場景

本系統設計用於 **AICBD（AI Computer-Based Detection）工業電腦視覺**，特別是製造產線的品檢與組裝直通率提升。

### §1.1 AICBD 三大使命

| 使命 | 描述 |
|:-----|:-----|
| **提升組裝直通率（FPY）** | AI 平台蒐集分析工站影像，減少錯漏裝與重工 |
| **提高產品品質** | 關鍵步驟導入 AI 視覺檢測，穩定出貨品質 |
| **縮短新產品導入時間（NPI）** | AI 技術加速新品導入流程 |

### §1.2 為什麼 TRIZ 推理必須讀 DK-05

工業 CV 的物理約束會直接 **gate** TRIZ 解法的可行性：

- Step 0（問題定向）：節拍時間（takt time）會限制「解法的最大延遲」這個邊界條件
- Step 4（驗證）：標記成本決定「retrain 頻率」是否可承受 → 影響補丁/進化判定
- Step 5（工程輸出）：drift detection 工具鏈是 ICD 必填項

→ 任何 TRIZ 候選方案如果在 §3 KPI 上跨界，需回到 Step 3 重挖或記為技術債。

---

## §2 五大心智模型

工業 CV AI 系統架構師必須先內化這五個觀念，才能正確設定 TRIZ 邊界。

### §2.1 Yield-Driven Thinking（良率驅動）

**核心**：製造業 AI 的存在意義只有一個 — **良率上升、重工下降**。

| 取捨 | 說明 |
|:-----|:-----|
| **漏檢（Escape）** 比 **誤報（False Alarm）** 嚴重 100 倍 | 漏檢 = 不良品出貨 = 客訴 = 賠錢 |
| **誤報太多** = 現場停線複檢 | 產能損失 → 沒人信任系統 |
| 兩者 trade-off 不是數學問題 | 是商業決策（不同客戶、不同產品線容忍度不同）|

> **TRIZ 推理應用**：Escape vs False Alarm 是典型的 TC（改善 Escape → 惡化 False Alarm）。在 Step 2 必須明確哪個方向對此產品線更不可接受，否則矛盾矩陣查表結果不可用。

### §2.2 Takt Time Constraint（節拍時間約束）

**核心**：產線節拍是硬約束，CV 推理必須在這個時間窗口內完成。

| 後果 | 影響 |
|:-----|:-----|
| 推理太慢 | 擋住產線 → 比沒有 AI 還糟 |
| 批次離線檢 | 延遲發現不良 → 重工成本暴增 |

意義：**模型大小、推理延遲、硬體選型不是事後優化，是架構設計的第一約束**。

> **TRIZ 推理應用**：Solution 的 OT（操作時間）必須 ≤ takt time。Step 3 SF 標準解選型時，需檢查 ScientificEffect 的響應時間。

### §2.3 Domain Shift is the Norm（場域漂移是常態）

**核心**：製造現場不是固定實驗室。

| 漂移源 | 表現 |
|:-------|:-----|
| 光源變化 | 白班 vs 夜班、燈管老化、季節日照 |
| 物料批次差異 | 同料號不同供應商，外觀微妙不同 |
| 治具磨損 | 夾具老化導致定位偏移 |
| 產品換線 | 今天 A 機種，明天 B 機種，後天全新 |
| 作業員差異 | 放料角度、力道不同 |

意義：**模型上線第一天的準確率是最高點，之後只會退化**。

> **TRIZ 推理應用**：DK-01 §9.1 「理想度遞減」STOP 信號需要監控 Drift Score。任何 Solution 必須附帶 retrain pipeline 設計，否則 Step 4 視為補丁。

### §2.4 Labeling Cost is the Real Bottleneck（標記成本是瓶頸）

**核心**：

| 約束 | 影響 |
|:-----|:-----|
| 標記需領域專家（品保工程師）| 不是隨便找人就能標 |
| 不良品是長尾分佈 | 良品 99%+，不良品稀少且樣態多變 |
| 每個新機種 = 從零開始標 | 成本不可攤銷 |
| 標記品質直接決定模型天花板 | 一致性 > 數量 |

> **TRIZ 推理應用**：「降低標記成本」是反覆出現的 TC 改善方向，配對的惡化方向通常是「模型準確率」或「上線時間」。可平行查 KB-02 矩陣。

### §2.5 Closed-Loop Feedback（閉環回饋）

**核心**：工業 CV 不是「部署完就結束」，是閉環。

```
影像採集 → 模型推理 → 判定（OK/NG）→ 人工複檢 → 回饋標記 → 模型更新 → ...
```

斷掉任一段：
- 沒人工複檢 → 不知模型錯在哪
- 複檢結果沒回流 → 模型永遠不會進步
- 沒版本管理 → 不知哪個模型在哪條線、效果如何

> **TRIZ 推理應用**：Step 5 工程輸出（WI）必須含閉環設計。任何「一次訓練永久使用」的 Solution 在 §3 KPI 視角下必為補丁。

---

## §3 三層 KPI 體系

### §3.1 業務層北極星（直接對應 AICBD 三使命）

| 指標 | 定義 | 為什麼是北極星 |
|:-----|:-----|:--------------|
| **First Pass Yield (FPY)** | 產品第一次通過所有工站檢測的比率 | AICBD 存在的終極理由；AI 投入要能回答「FPY 提升了多少」 |
| **NPI Cycle Time** | 新產品從立項到量產的時間 | 衡量「AI 是否加速新品導入」；含模型開發 / 標記 / 驗證 / 上線 |
| **Outgoing Quality Level (OQL)** | 出貨後客訴 / 退貨率 | 漏檢的終極後果；惡化 = AI 檢測系統失敗 |

### §3.2 系統層指標（架構師儀表板）

| 指標 | 定義 | 閾值 |
|:-----|:-----|:-----|
| **Escape Rate（漏檢率）** | 真實不良品被判 OK 的比率 | 通常 < 0.1%（最致命） |
| **False Call Rate（誤報率）** | 良品被判 NG 的比率 | 通常 < 1-2%（太高 → 現場關掉系統）|
| **Inference Latency** | 單張影像從輸入到判定 | 必須 < takt time |
| **Model Drift Score** | 在線準確率相對上線時的衰退 | 觸發 retrain 的關鍵 |
| **Labeling Efficiency** | 每張可用標記的平均耗時（含 pre-label + 修正）| 衡量人機協作效率 |
| **Time-to-Deploy** | 新機種模型從需求到上線的天數 | 直接影響 NPI |

### §3.3 營運層指標（每日/每週追蹤）

| 指標 | 用途 |
|:-----|:-----|
| Daily Inspection Volume | 系統穩定性脈搏 |
| Human Override Rate | 過高 = 模型不可信；過低 = 沒人在看 |
| Retrain Frequency | 衡量維護負擔 |
| Active Learning Hit Rate | 標記策略精準度 |
| Cross-Site Variance | 同模型在不同廠區的差異（差異大 = domain shift 嚴重）|

---

## §4 因果回饋迴路

```
Labeling Efficiency ──→ Time-to-Deploy ──→ NPI Cycle Time
        │                                        │
        ▼                                        ▼
Model Accuracy ──→ Escape Rate ──→ OQL（客訴率）
        │               │
        ▼               ▼
False Call Rate ──→ 現場信任度 ──→ 系統是否被真正使用
        │
        ▼
Human Override Rate（信號：模型該更新了）
        │
        ▼
Model Drift Score ──→ Retrain 觸發 ──→ 閉環
```

**最關鍵的兩條鏈**：

1. **Escape Rate 惡化 → OQL 下降 → 客訴 → AI 系統被質疑**
2. **False Call Rate 過高 → 現場關掉系統 → AI 投入歸零**

整個系統的生死線。所有 §2 心智模型最終都是在守住這兩條線。

---

## §5 製造約束如何 Gate TRIZ 解法

### §5.1 與 Step 0（問題定向）的接口

Step 0 必須先問：

| 問題 | 影響 |
|:-----|:-----|
| 此問題影響哪個 §3.1 北極星？（FPY / NPI / OQL）| 決定 TC 改善方向的優先級 |
| 此產品線的 Escape ↔ False Call 容忍度比？ | TC 矩陣查表前必須先定 |
| 此工站的 takt time？ | 設定 OT 上限 |
| 此機種的歷史 Drift Score？ | 評估 retrain 頻率上限 |

→ 這些答案是 Problem entity 的延伸欄位（schema 在 DK-04 §2.1 沒列，由 Step 0 skill 寫入 `session-step0-*.md`）。

### §5.2 與 Step 4（驗證）的接口

Step 4 四問複雜度（DK-01 §7.2）需加入製造約束第五問：

| 問題 | 補丁信號 | 進化信號 |
|:-----|:---------|:---------|
| 5. 解法上線後 Drift Rate 預估如何？ | 需頻繁 retrain（>1 次/月）| 可承受 retrain 週期（≤1 次/季）|

若第 5 問為「需頻繁 retrain」→ 即使 1-4 問通過，仍視為**領域層補丁**（不是 TRIZ 層補丁，但必須記錄到 TechnicalDebt）。

### §5.3 與 Step 5（工程輸出）的接口

Step 5 產出 WI / MC / ICD 時，每份必須有以下欄位涉及 §3 KPI：

| 文件 | 必填 KPI 欄位 |
|:-----|:------------|
| WI | 預期 Inference Latency 上限、Drift 監控頻率、Retrain 觸發條件 |
| MC | 不適用（材料層）|
| ICD | 跨子系統的 Latency budget 拆分、Active Learning hook 介面 |

---

## §6 技術選型參考

下表整理工業 CV 落地常用工具鏈，TRIZ 解法在 SF 標準解導入階段需檢查工具是否在此清單內（不在 → 需評估自建成本）。

### §6.1 模型層

| 範式 | 代表模型 | 適用場景 |
|:-----|:--------|:---------|
| 監督式偵測 | YOLOv8 / v11、RT-DETR | 全檢場景、有大量標記 |
| 無監督異常偵測 | PatchCore、EfficientAD | 標記稀缺、零樣本啟動 |
| Few-shot / Zero-shot | AnomalyCLIP、AnomalyGPT | 新機種快速上線 |
| 生成式增強 | Stable Diffusion + LoRA | 稀有缺陷影像合成 |
| 通用分割 | SAM、SAM-LAD | 邏輯異常偵測 |

### §6.2 MLOps 工具鏈

| 類別 | 工具 | 用途 |
|:-----|:-----|:-----|
| Drift Detection | Evidently AI、NannyML | 監控 §3.2 Drift Score |
| Experiment Tracking | MLflow | 模型版本管理 |
| Pipeline Orchestration | Airflow、Kubeflow | retrain pipeline |
| Dashboard | Grafana | 系統層指標可視化 |
| Active Learning | modAL、BAAL | 主動學習採樣（§2.4 解標記瓶頸）|
| Edge Inference | TensorRT、ONNX Runtime、OpenVINO | takt time 約束下的部署 |
| 模型壓縮 | torch.ao（pruning / quantization）、distillation 框架 | 推理加速 |

### §6.3 Benchmark 資料集

| 資料集 | 用途 |
|:-------|:-----|
| MVTec AD / MVTec AD 2 | 工業異常偵測標準 benchmark |
| MVTec LOCO AD | 邏輯異常偵測 |

---

## §7 與 TRIZ Workflow 的接口

### §7.1 哪些 Step 必讀 DK-05

| Step | 必讀章節 | 用途 |
|:-----|:--------|:-----|
| Step 0 | §2.1 + §2.2 + §3.1 | 設定 Problem 邊界 + KPI 優先級 |
| Step 1 | §2.5 | SF 圖必含閉環回饋路徑 |
| Step 2 | §2.4 | 標記成本是高頻 TC 改善方向 |
| Step 3 | §3.2 | 候選 Solution 必須對齊系統層 KPI 閾值 |
| Step 4 | §5.2 | 加入第五問領域複雜度 |
| Step 5 | §5.3 + §6 | WI / ICD 必填 KPI 欄位 + 工具鏈檢核 |

### §7.2 哪些 Skill / Agent 必讀 DK-05

| Skill / Agent | 讀 DK-05 段落 |
|:--------------|:------------|
| `triz-scoping`（Step 0）| §2 全部 + §3.1 |
| `triz-contradict`（Step 2-3 supervisor）| §2.4 + §3.2 |
| `triz-analyst`（Step 2 worker）| §3.2（系統層 KPI 閾值參考）|
| `triz-verify`（Step 4）| §5.2 第五問 |
| `triz-wi`（Step 5）| §5.3 + §6 |
| `tr-fea-assist`（FEA 輔助）| §3.2 + §6.1（模型層）|

### §7.3 從 TRIZ 視角看 §2 五大模型對應的反向錨點

| §2 心智模型 | 反向錨點（如果忽略會怎樣）|
|:-----------|:------------------------|
| 良率驅動 | 解法在 mAP 上贏，但 Escape 沒降 → §3.2 業務層 KPI 失敗 |
| 節拍約束 | 推理太慢，takt time 超限 → 產線拒收 |
| 場域漂移 | 一次訓練永久使用，3 個月後準確率退化 → OQL 惡化 |
| 標記瓶頸 | 解法依賴大量新標記，新機種上線時間爆 → NPI 失敗 |
| 閉環回饋 | 沒設計 retrain 路徑，模型壞了沒人知道 → 系統被現場關掉 |

→ **任何 TRIZ 候選方案在 Step 4 應該對這 5 個反向錨點做檢查**。任一個答「會出事」→ 補丁路徑或回 Step 3 重挖。

---

## §8 速查

**TRIZ 推理時要問：**

1. 此解法影響哪個業務北極星（FPY / NPI / OQL）？
2. 推理延遲是否在 takt time 內？
3. 場域漂移後此解法還有效嗎？
4. 上線需要多少新標記？
5. 閉環回饋設計在哪？

5 問都過 = 領域層綠燈。任一未過 = 回 Step 3 或記為技術債。
