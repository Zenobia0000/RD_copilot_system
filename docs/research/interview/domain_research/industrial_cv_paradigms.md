# 工業電腦視覺缺陷檢測：技術範式、比較與選型指南

本文件針對 `domain_fundamentals.md` 中歸納的五大底層觀念（良率驅動、節拍約束、場域漂移、標記成本、閉環回饋），系統性整理當前工業 CV 領域的技術範式、關鍵文獻、技術比較與場域應用。

---

## 一、領域關鍵字 Top 20

依技術影響力、學術引用頻次與產業採用度篩選：

| # | 關鍵字 | 說明 | 選擇依據 |
|:--|:-------|:-----|:---------|
| 1 | **Industrial Anomaly Detection** | 工業異常偵測，領域核心問題 | IAD 論文數 2019→2023 增長 380%（Springer AI Review 2025） |
| 2 | **Unsupervised Anomaly Detection** | 無監督異常偵測，不需缺陷標記 | 解決工業場域標記稀缺的主流範式 |
| 3 | **PatchCore** | 基於 patch-level memory bank 的異常偵測 | MVTec AD 上達 99.1% AUROC，工業界廣泛採用 |
| 4 | **EfficientAD** | 超快速異常偵測模型 | 兼顧速度與精度，適合產線即時推理 |
| 5 | **Few-Shot Defect Detection** | 少樣本缺陷偵測 | 直接對應「小量多樣」痛點 |
| 6 | **Active Learning** | 主動學習標記策略 | 混合採樣策略可減少 90% 標記量（Springer 2025） |
| 7 | **Vision Foundation Model** | 視覺基礎模型（CLIP / DINOv2 / SAM） | Zero-shot 異常偵測的技術基底 |
| 8 | **Zero-Shot Anomaly Detection** | 零樣本異常偵測 | AnomalyCLIP（ICLR 2024）、AnomalyGPT（AAAI 2024） |
| 9 | **YOLO (Object Detection)** | 監督式物件偵測 | YOLOv8/v11 為工業全檢場景最廣泛部署的模型 |
| 10 | **Synthetic Data / Diffusion Augmentation** | 合成資料增強 | Diffusion model 生成品質顯著優於 GAN |
| 11 | **Edge Inference** | 邊緣推理 | 產線節拍約束下的硬性需求 |
| 12 | **Model Compression (Pruning / Quantization / Distillation)** | 模型壓縮三件套 | 結構化剪枝 +40% 推理速度、僅 -2% 精度 |
| 13 | **Knowledge Distillation** | 知識蒸餾 | Student-Teacher 架構在異常偵測中被廣泛使用 |
| 14 | **Domain Adaptation / Transfer Learning** | 領域遷移 | 跨廠區、跨機種模型複用的核心技術 |
| 15 | **Model Drift Detection** | 模型漂移偵測 | Data Drift / Concept Drift / Prediction Drift 三類 |
| 16 | **MLOps for CV** | CV 模型生命週期管理 | 成熟 MLOps 可降低 60% 模型失敗率 |
| 17 | **Human-in-the-Loop (HITL)** | 人機協作標記與決策 | Pre-labeling + 人工複核的工業實踐 |
| 18 | **MVTec AD / MVTec AD 2** | 工業異常偵測基準數據集 | 領域標準 benchmark，2025 推出 AD 2 |
| 19 | **Segment Anything Model (SAM)** | 通用分割基礎模型 | SAM-LAD 等將 SAM 應用於工業邏輯異常偵測 |
| 20 | **Multimodal Defect Detection** | 多模態缺陷偵測（影像+聲學+振動） | 2024 Emerald 發表，結合視覺、聲學、振動信號 |

### 反思問答 1

> **Q: 這 20 個關鍵字是否覆蓋了工業 CV 的核心問題空間？**
> A: 基本覆蓋五大底層觀念對應的技術層。但缺少兩個方向：(1) **3D 點雲缺陷偵測**——在精密組裝場景日益重要；(2) **Continual / Incremental Learning**——持續學習以應對場域漂移。這兩個方向值得後續追蹤，但目前工業落地成熟度仍低於前 20 項。

---

## 二、權威文獻清單

### 2.1 綜合性 Survey（高引用 / 高影響力）

| # | 文獻 | 來源 | 重點 |
|:--|:-----|:-----|:-----|
| S1 | **A survey of deep learning for industrial visual anomaly detection** (2025) | Springer Artificial Intelligence Review | 涵蓋密度估計、記憶庫、流模型、判別式方法；半監督/零樣本框架 |
| S2 | **A systematic survey: role of deep learning-based image anomaly detection in industrial inspection contexts** (2025) | Frontiers in Robotics and AI / PMC | 從手動檢測到自動化系統的演進全景 |
| S3 | **A Comprehensive Survey for Real-World Industrial Defect Detection** (2025) | arXiv 2507.13378 | 2D/3D 模態、closed-set 到 open-set 偵測框架的轉變 |
| S4 | **Using Deep Learning to Detect Defects in Manufacturing: A Comprehensive Survey and Current Challenges** (2020) | PMC (高引用) | 早期奠基性 survey，涵蓋 CNN 各架構在製造缺陷偵測的應用 |
| S5 | **AI-enabled defect detection in industrial products: A comprehensive survey** (2025) | ScienceDirect | 涵蓋 AI 啟用的缺陷偵測全鏈路，含關鍵洞察與未來挑戰 |
| S6 | **A Comprehensive Survey on Machine Learning Driven Material Defect Detection** (2025) | ACM Computing Surveys | ML 驅動的材料缺陷偵測全景 |
| S7 | **Generative AI in industrial machine vision: a review** (2025) | Springer J. Intelligent Manufacturing | GAN/VAE/Diffusion 在工業機器視覺的應用綜述 |

### 2.2 方法論核心論文

| # | 文獻 | 來源 | 核心貢獻 |
|:--|:-----|:-----|:---------|
| M1 | **PatchCore: Towards Total Recall in Industrial Anomaly Detection** (Roth et al., 2022) | CVPR | Patch-level memory bank + coreset subsampling；MVTec AD 99.1% AUROC |
| M2 | **EfficientAD: Accurate Visual Anomaly Detection at Millisecond-Level Latencies** (Batzner et al., 2024) | WACV | Student-Teacher + autoencoder；毫秒級推理 |
| M3 | **AnomalyCLIP: Object-agnostic Prompt Learning for Zero-shot Anomaly Detection** (2024) | ICLR | CLIP-based zero-shot 異常偵測，跨類別泛化 |
| M4 | **AnomalyGPT: Detecting Industrial Anomalies Using Large Vision-Language Models** (2024) | AAAI | LVLMs 應用於工業異常偵測 |
| M5 | **SAM-LAD: Segment Anything Model Meets Zero-Shot Logic Anomaly Detection** (2024) | arXiv | SAM 應用於邏輯異常偵測，plug-and-play 框架 |
| M6 | **VCP-CLIP: Visual Context Prompting for Zero-Shot Anomaly Segmentation** (2024) | ECCV | 視覺上下文提示用於零樣本異常分割 |

### 2.3 工程實踐論文

| # | 文獻 | 來源 | 核心貢獻 |
|:--|:-----|:-----|:---------|
| E1 | **Active learning for industrial defect detection: hybrid sampling strategies** (2025) | Springer IJAMT | 混合採樣（entropy + diversity + random），2400 張標記達 F1=86.7% |
| E2 | **Few-shot learning for defect detection in manufacturing** (2024) | Taylor & Francis IJPR | 影像 + anomaly map 的 few-shot 框架 |
| E3 | **Efficient surface defect detection with minimized labeling effort** (2025) | SAGE ICA | 工業絲印場景的標記效率優化 |
| E4 | **Vision transformers on the edge: model compression and acceleration** (2025) | Neurocomputing | ViT 模型在邊緣設備的壓縮加速策略全景 |
| E5 | **Optimizing PatchCore for One-Shot Industrial Anomaly Detection** (2025) | IEEE ETFA | One-shot 場景下的 PatchCore 優化 |
| E6 | **Latent Diffusion Models for Visual Defect Segmentation in Steel Inspection** (2024) | Sensors | Stable Diffusion + LoRA 生成合成缺陷影像 |

### 2.4 Benchmark 數據集

| 數據集 | 規模 | 特點 | 狀態 |
|:-------|:-----|:-----|:-----|
| **MVTec AD** | 5,354 張 / 15 類 | 工業異常偵測標準 benchmark | SOTA 已飽和（>90% AU-PRO） |
| **MVTec AD 2** (2025) | 8,000+ 張 / 8 類 | 更具挑戰性的新 benchmark | 剛發布，尚未飽和 |
| **VisA** | 10,821 張 / 12 類 | 視覺異常偵測 | 中等難度 |
| **MVTec LOCO-AD** | — | 邏輯約束異常偵測 | 測試結構性/邏輯性異常 |

### 反思問答 2

> **Q: 這些文獻是否有足夠的時效性？是否存在更新的突破？**
> A: 核心 survey 均為 2024-2025 發表，時效性充足。值得追蹤的最新動態：(1) NeurIPS 2025 的 Normal-Abnormal Guided Generalist AD；(2) ICLR 2026 的 MRAD（Memory-Driven Retrieval AD）；(3) AAAI 2026 的 PromptMoE。這些代表 foundation model + anomaly detection 的前沿融合趨勢。
>
> **Q: 文獻之間是否有矛盾結論？**
> A: 主要矛盾在於「監督式 vs. 無監督式」的選擇。Survey S1 強調無監督方法的泛化優勢，而 YOLO 系列實踐論文則展示監督式方法在已知缺陷類別上的精度優勢。結論：**兩者非互斥，而是互補**——監督式處理已知缺陷、無監督式捕捉未知異常，混合部署是工業最佳實踐。

---

## 三、技術範式分類

工業 CV 缺陷偵測的技術範式可分為 **6 大類**：

### 3.1 範式概覽

| 範式 | 代表方法 | 核心思路 | 標記需求 |
|:-----|:---------|:---------|:---------|
| **A. 監督式物件偵測** | YOLO (v8/v11)、Faster R-CNN、DETR | 學習已知缺陷類別的偵測器 | 高：需大量 bbox/mask 標記 |
| **B. 無監督異常偵測（Memory-Bank）** | PatchCore、SPADE | 建立正常樣本記憶庫，偏離即異常 | 極低：僅需正常樣本 |
| **C. 無監督異常偵測（Student-Teacher）** | EfficientAD、STPM、RD | 師生網路差異偵測異常 | 極低：僅需正常樣本 |
| **D. 無監督異常偵測（Reconstruction）** | AutoEncoder、VAE、Flow-based (CFLOW) | 重建失敗 = 異常 | 極低：僅需正常樣本 |
| **E. Zero/Few-Shot（Foundation Model）** | AnomalyCLIP、AnomalyGPT、SAM-LAD、VCP-CLIP | 利用預訓練視覺語言模型做跨類別泛化 | 零/極低：zero-shot 或數張 reference |
| **F. 合成資料增強** | Diffusion Model (SD+LoRA)、GAN (DCGAN)、DefFiller | 生成缺陷影像擴充訓練集 | 輔助手段：減少真實標記需求 |

---

## 四、技術比較表

### 4.1 主要技術特性比較

以工業場域最在意的 8 個維度進行比較：

| 特性維度 | A. 監督式偵測 (YOLO) | B. Memory-Bank (PatchCore) | C. Student-Teacher (EfficientAD) | D. Reconstruction (AE/VAE/Flow) | E. Foundation Model (Zero/Few-Shot) | F. 合成增強 (Diffusion) |
|:---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **已知缺陷偵測精度** | ★★★★★ | ★★★★ | ★★★★ | ★★★ | ★★★ | N/A (輔助) |
| **未知缺陷泛化能力** | ★ | ★★★★ | ★★★★ | ★★★★ | ★★★★★ | ★★★ |
| **標記需求** | 高（數千張 bbox） | 極低（僅正常樣本） | 極低（僅正常樣本） | 極低（僅正常樣本） | 零/極低 | 低（少量真實 + 合成） |
| **推理速度** | ★★★★★ (ms 級) | ★★★ (10-100ms) | ★★★★★ (ms 級) | ★★★ (10-50ms) | ★★ (100ms+) | N/A (離線生成) |
| **部署複雜度** | 低 | 中（需維護 memory bank） | 低 | 低-中 | 高（需大模型推理環境） | 中（需離線生成管線） |
| **邊緣部署適合度** | ★★★★★ | ★★★ | ★★★★★ | ★★★ | ★ | N/A |
| **新產品/新機種適應速度** | 慢（需重新標記+訓練） | 快（收集正常樣本即可） | 快（收集正常樣本即可） | 快 | 最快（零樣本） | 中（需生成+微調） |
| **技術成熟度（工業落地）** | ★★★★★ | ★★★★ | ★★★★ | ★★★ | ★★ | ★★ |
| **抗場域漂移能力** | ★★ (需 retrain) | ★★★ (更新 bank) | ★★★ (更新 teacher) | ★★ (需 retrain) | ★★★★ (泛化性強) | ★★★ (可生成新域) |
| **缺陷定位精度** | ★★★★★ (bbox/mask) | ★★★★ (heatmap) | ★★★★ (heatmap) | ★★★ (粗粒度) | ★★★ (依模型而定) | N/A |

> **★ 評分說明**：★ = 弱 / 不適合，★★★ = 中等，★★★★★ = 極佳

### 4.2 決策矩陣：何時選用哪個範式

| 場景條件 | 推薦範式 | 原因 |
|:---------|:---------|:-----|
| 缺陷類別已知且固定、標記充足 | A. YOLO 監督式 | 精度最高、速度最快、部署最成熟 |
| 缺陷類別未知或樣態多變 | B/C. PatchCore / EfficientAD | 僅需正常樣本，可偵測未見過的異常 |
| 產線節拍極短（<50ms/件） | C. EfficientAD 或 A. YOLO | 毫秒級推理，適合邊緣部署 |
| 新機種頻繁切換 | E. Foundation Model (Zero-Shot) | 無需訓練即可部署，NPI 最快 |
| 缺陷樣本極稀少（<50 張） | E + F. Zero-Shot + Diffusion 合成 | 組合使用：基礎模型做初始偵測，合成資料逐步補強 |
| 需要精確的缺陷分類與定位 | A. YOLO + B. PatchCore 混合 | 監督式做分類定位，無監督式做異常守門 |
| 多廠區統一部署 | B/C + Domain Adaptation | 記憶庫/教師模型支持增量更新，搭配遷移微調 |

### 反思問答 3

> **Q: 單一範式能否解決所有問題？**
> A: 不能。工業場域的最佳實踐是**混合部署（Hybrid Pipeline）**：
> - **第一道防線**：無監督異常偵測（PatchCore / EfficientAD）攔截所有偏離正常的樣本
> - **第二道防線**：監督式偵測（YOLO）對已知缺陷類別做精確分類與定位
> - **輔助層**：Foundation Model 做新機種冷啟動 + Diffusion 做資料增強
>
> 這對應 `domain_fundamentals.md` 中的「良率驅動」——漏檢用無監督守門、誤報用監督式精準分類來降低。

> **Q: Foundation Model (Zero-Shot) 是否能取代傳統方法？**
> A: 短期（2025-2026）不能。原因：(1) 推理延遲仍過高，不適合高節拍產線；(2) 定位精度不如 PatchCore/YOLO；(3) 邊緣部署困難。但中長期（2027+）隨著模型蒸餾與邊緣硬體進步，Foundation Model 可能成為新機種冷啟動的標配。

---

## 五、場域應用表

以工業 CV 的 6 個典型應用場域為橫軸，對各技術特性的在意程度進行評估：

### 5.1 場域定義

| 場域 | 描述 | 典型產業 |
|:-----|:-----|:---------|
| **F1. 高速產線全檢** | 每件產品都檢，節拍 <1 秒 | 電子組裝、PCB、連接器 |
| **F2. 精密零件外觀檢** | 高解析度、微小缺陷 | 半導體、光學元件、航太 |
| **F3. 組裝正確性驗證** | 確認零件是否正確安裝 | 汽車組裝、電子組裝（AICBD 核心） |
| **F4. 多品種小批量** | 頻繁換線、每種產品量少 | 客製化製造、醫療器材 |
| **F5. 連續製程表面檢** | 捲狀/板狀材料連續檢測 | 鋼鐵、紡織、紙業 |
| **F6. 安全合規檢查** | 法規要求的品質記錄 | 食品、藥品、航太 |

### 5.2 各場域對技術特性的在意程度

（5 = 極重要，1 = 不太重要）

| 技術特性 | F1. 高速全檢 | F2. 精密外觀 | F3. 組裝驗證 | F4. 多品種小批量 | F5. 連續製程 | F6. 安全合規 |
|:---------|:---:|:---:|:---:|:---:|:---:|:---:|
| 已知缺陷偵測精度 | 5 | 5 | 4 | 3 | 5 | 5 |
| 未知缺陷泛化能力 | 3 | 4 | 3 | 5 | 3 | 5 |
| 標記需求低 | 3 | 2 | 3 | 5 | 3 | 2 |
| 推理速度 | **5** | 3 | 4 | 3 | **5** | 3 |
| 部署複雜度低 | 4 | 3 | 4 | 4 | 4 | 3 |
| 邊緣部署適合度 | **5** | 3 | 4 | 4 | **5** | 3 |
| 新產品適應速度 | 3 | 2 | 4 | **5** | 2 | 3 |
| 技術成熟度 | 4 | 4 | 4 | 3 | 4 | **5** |
| 抗場域漂移 | 4 | 3 | 4 | 4 | **5** | 3 |
| 缺陷定位精度 | 4 | **5** | 3 | 3 | 4 | 4 |
| 可追溯性/可解釋性 | 3 | 4 | 3 | 3 | 3 | **5** |

### 5.3 場域 × 推薦範式

| 場域 | 主推範式 | 輔助範式 | 關鍵考量 |
|:-----|:---------|:---------|:---------|
| F1. 高速全檢 | A (YOLO) + C (EfficientAD) | F (Diffusion 增強) | 速度是硬約束，必須 ms 級推理 |
| F2. 精密外觀 | B (PatchCore) + A (YOLO) | F (合成增強) | 精度最優先，可容忍較長推理時間 |
| F3. 組裝驗證 | A (YOLO) + B (PatchCore) | E (Foundation Model 冷啟) | **AICBD 核心場域**：已知正確組裝 vs. 錯漏裝 |
| F4. 多品種小批量 | E (Zero-Shot) + B (PatchCore) | F (Diffusion) + Active Learning | 標記成本與換線速度是第一約束 |
| F5. 連續製程 | A (YOLO) + D (Flow-based) | 線上 drift monitoring | 連續影像流，需高吞吐量 + 漂移偵測 |
| F6. 安全合規 | A (YOLO) + 完整 trace | 可解釋性工具 (GradCAM) | 審計追溯是法規要求 |

### 5.4 AICBD 定位分析

AICBD 的核心場域是 **F3（組裝正確性驗證）** 兼顧 **F1（高速全檢）** 與 **F4（多品種小批量）** 特性：

- **組裝直通率** → F3 場域：需同時偵測「錯裝」「漏裝」「反裝」
- **多機種頻繁切換** → F4 特性：新品導入時模型必須快速就緒
- **產線節拍** → F1 約束：推理不能擋線

因此 AICBD 的最佳技術策略為：

```
第一層：EfficientAD / PatchCore（無監督異常守門，僅需正常組裝影像即可上線）
    ↓ 異常樣本累積
第二層：YOLO（監督式精確分類已知缺陷類型）
    ↓ 新機種冷啟動
第三層：Foundation Model (AnomalyCLIP) zero-shot 快速部署
    ↓ 標記不足時
第四層：Diffusion Model 合成缺陷影像增強
    ↓ 持續優化
閉環：Active Learning 選取高價值樣本 → 人工標記 → Retrain
```

### 反思問答 4

> **Q: AICBD 場域的特殊性對技術選型有什麼獨特影響？**
> A: 組裝驗證與表面缺陷偵測有根本差異：
> - **表面缺陷**是像素級異常（刮痕、凹坑、色差）→ 無監督方法表現優異
> - **組裝錯誤**是結構/邏輯級異常（零件缺失、位置錯誤、方向反轉）→ 需要理解「應該長什麼樣」的語義
> - 這意味著 **PatchCore 等純視覺特徵比對方法在組裝驗證場景可能不如物件偵測方法**，因為組裝錯誤不一定在像素特徵上表現為「異常」
> - SAM-LAD 等邏輯異常偵測方法可能在此場景有更大價值

> **Q: 技術選型中最容易犯的錯誤是什麼？**
> A: 三個常見陷阱：
> 1. **追求最新方法而忽略部署約束**：Foundation Model 論文精度很高，但推理延遲可能是產線的 10 倍
> 2. **用 benchmark 精度代替產線精度**：MVTec AD 上 99% AUROC 不代表你的產線也能到 99%，光源、角度、物料差異都會大幅降低
> 3. **忽略漏檢/誤報的不對稱成本**：只看 F1 score 是不夠的，需要分開看 escape rate 和 false call rate

---

## 六、技術選型決策流程

```
Step 1: 確認場域約束
    ├─ 節拍時間 < 100ms? → 必須 edge inference，排除 Foundation Model
    ├─ 缺陷類別已知且穩定? → 優先 YOLO 監督式
    └─ 新機種頻繁 / 缺陷未知? → 優先 PatchCore / EfficientAD

Step 2: 評估標記資源
    ├─ 有專家標記團隊 + 歷史資料? → 監督式 YOLO 為主
    ├─ 僅有正常樣本? → 無監督 (PatchCore / EfficientAD)
    └─ 幾乎無資料? → Zero-Shot (AnomalyCLIP) + Diffusion 合成

Step 3: 設計混合管線
    ├─ 無監督做 「異常守門」（高召回）
    ├─ 監督式做 「精確分類」（低誤報）
    └─ Foundation Model 做 「冷啟動」（新機種快速上線）

Step 4: 建立閉環
    ├─ Active Learning 選取高價值樣本
    ├─ Pre-labeling + 人工複核
    ├─ Drift Detection 觸發 retrain
    └─ A/B testing 驗證新模型
```

---

## 七、關鍵潛在偏誤與局限

| 偏誤/局限 | 說明 | 如何應對 |
|:-----------|:-----|:---------|
| **Benchmark 偏誤** | MVTec AD 影像品質遠優於真實產線；學術 SOTA 不等於產線可用 | 必須在目標產線實測，不依賴 paper 數字 |
| **正常樣本偏誤** | 無監督方法假設訓練集全為正常，但工業數據中常混入未標記的不良品 | 需要資料清洗流程 + outlier filtering |
| **類別不平衡** | 真實產線良率 >99%，不良品極少且分佈長尾 | 不能用 accuracy，必須用 recall / escape rate / false call rate |
| **環境依賴性** | 所有方法都對光源、角度、背景高度敏感 | 標準化取像環境 + 資料增強 + drift monitoring |
| **論文 vs. 工程落差** | 學術論文忽略部署、延遲、維運成本 | 技術選型必須包含 deployment + maintenance 評估 |

### 反思問答 5

> **Q: 本文件最大的不確定性在哪裡？**
> A: 兩個方向：
> 1. **Foundation Model 在工業場域的真實落地效果**——目前大部分是學術驗證，工廠實際部署案例極少，推理成本與延遲仍是瓶頸
> 2. **Diffusion 合成資料的品質上限**——論文報告合成資料可提升偵測性能，但合成缺陷是否能覆蓋真實缺陷的多樣性仍需更多工業驗證
>
> **Q: 這份分析適用於 AICBD 的時效性如何？**
> A: 技術成熟度評估有效期約 12-18 個月（至 2027 中）。Foundation Model 領域進展極快，EfficientAD 等方法的邊緣部署效率也在持續改善。建議每半年回顧一次技術選型決策。

---

## 八、總結：五大底層觀念 × 技術範式映射

| 底層觀念 | 對應技術範式 | 關鍵指標 |
|:---------|:-------------|:---------|
| 良率驅動 | YOLO（低漏檢）+ PatchCore（低誤報）混合 | Escape Rate < 0.1%, False Call Rate < 2% |
| 節拍約束 | EfficientAD / YOLO（ms 級推理）+ Edge Inference | Inference Latency < takt time |
| 場域漂移是常態 | Drift Detection + 記憶庫增量更新 + Retrain Pipeline | Model Drift Score, Cross-Site Variance |
| 標記成本是瓶頸 | 無監督 + Active Learning + Diffusion 合成 + Pre-labeling | Labeling Efficiency, Active Learning Hit Rate |
| 閉環回饋 | MLOps Pipeline + Human Override 回流 + A/B Testing | Human Override Rate, Retrain Frequency |

---

## Sources

- [A survey of deep learning for industrial visual anomaly detection (2025)](https://link.springer.com/article/10.1007/s10462-025-11287-7)
- [A systematic survey: deep learning-based image anomaly detection in industrial inspection (2025)](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1554196/full)
- [A Comprehensive Survey for Real-World Industrial Defect Detection (2025)](https://arxiv.org/abs/2507.13378)
- [AI-enabled defect detection: comprehensive survey (2025)](https://www.sciencedirect.com/science/article/pii/S1474034625009607)
- [Few-shot learning for defect detection in manufacturing (2024)](https://www.tandfonline.com/doi/full/10.1080/00207543.2024.2316279)
- [Active learning for industrial defect detection: hybrid sampling (2025)](https://link.springer.com/article/10.1007/s00170-025-17378-7)
- [Vision transformers on the edge: compression and acceleration (2025)](https://www.sciencedirect.com/science/article/abs/pii/S0925231225010896)
- [Generative AI in industrial machine vision (2025)](https://link.springer.com/article/10.1007/s10845-025-02604-6)
- [MVTec AD 2 Dataset (2025)](https://www.tomomi-research.com/en/archives/3785)
- [Optimizing PatchCore for One-Shot IAD (IEEE ETFA 2025)](https://blog.seavision-group.com/news/anomaly-detection-paper-etfa)
- [awesome-industrial-anomaly-detection (GitHub)](https://github.com/M-3LAB/awesome-industrial-anomaly-detection)
- [SAM-LAD: Zero-Shot Logic Anomaly Detection (2024)](https://arxiv.org/abs/2406.00625)
- [VCP-CLIP: Zero-Shot Anomaly Segmentation (ECCV 2024)](https://dl.acm.org/doi/10.1007/978-3-031-72890-7_18)
- [Latent Diffusion for Steel Defect Segmentation (2024)](https://www.mdpi.com/1424-8220/24/18/6016)
- [Quality Inspection with YOLO11 (Ultralytics)](https://www.ultralytics.com/blog/quality-inspection-in-manufacturing-traditional-vs-deep-learning-methods)
- [Six Challenges of Edge AI in Industrial Vision (2025)](https://www.vision-systems.com/boards-software/article/55307538/six-challenges-of-integrating-edge-ai-into-industrial-vision-systems)
