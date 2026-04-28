# 行為驅動情境 (BDD) 指南與規格 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**主要作者**：技術負責人 + 產品經理（草稿由 AI Agent 整合產出）
**狀態**：`Active`
**模板來源**：`VibeCoding_Workflow_Templates/03_behavior_driven_development_guide.md`

---

## 目錄

- [Ⅰ. BDD 核心原則](#ⅰ-bdd-核心原則)
- [Ⅱ. Gherkin 語法速查](#ⅱ-gherkin-語法速查)
- [Ⅲ. 7 個核心 Feature](#ⅲ-7-個核心-feature)
  - [Feature 1: 早期問題定義](#feature-1)
  - [Feature 2: Phase Gate 退出檢查](#feature-2)
  - [Feature 3: TRIZ 三路徑求解](#feature-3)
  - [Feature 4: Pre-CAD 五維審查](#feature-4)
  - [Feature 5: AI 黑帽質疑](#feature-5)
  - [Feature 6: KT 決策記錄](#feature-6)
  - [Feature 7: 知識資產自動產出](#feature-7)
- [Ⅳ. 最佳實踐](#ⅳ-最佳實踐)
- [Ⅴ. 與 PRD User Story 對應表](#ⅴ-與-prd-user-story-對應表)

---

**目的**：將 [`02_prd.md`](./02_prd.md) §3 的 user stories 翻譯為可執行的 Gherkin 情境，作為 QA 驗收與 TDD 開發的雙重起點。

---

## Ⅰ. BDD 核心原則

1. **從對話開始**：BDD 不是寫測試，而是 PM/Engineer/QA 對需求達成共識。
2. **由外而內**：從用戶與系統的互動（外部行為）出發，再深入內部實現。
3. **Ubiquitous Language**：本專案的 BDD 用詞需與 PRD、TRIZ skill 規格、頁面 spec 一致：
   - `矛盾 (Contradiction)`、`假設 (Assumption)`、`Gate (D1/D2/X1/X2/P/V1/V2/V4)`、`Phase (I/II/III)`、`OZ-OT-Px`、`CCI`、`TR (TR1-TR10)`
4. **TRIZ-aware**：所有涉及 TRIZ 的 scenarios 應引用 `docs/_harness/auto_triz_strategy.md` 與 `.claude/skills/triz-*` 的契約。

---

## Ⅱ. Gherkin 語法速查

| 關鍵字 | 用途 | 對應 |
|:-------|:-----|:-----|
| `Feature` | 高層次功能（≈ 1 個 Epic） | PRD Epic |
| `Scenario` | 一個具體場景 | PRD User Story |
| `Background` | 共用前置條件 | 多 Scenario 共享 Given |
| `Given` | 前置狀態 | Arrange |
| `When` | 觸發動作 | Act |
| `Then` | 預期結果 | Assert |
| `And / But` | 串接多步驟 | — |
| `Scenario Outline + Examples` | 同情境多組資料 | 邊界值測試 |
| `@tag` | 分類標記 | `@happy-path`, `@sad-path`, `@triz`, `@gate` |

---

## Ⅲ. 7 個核心 Feature

### Feature 1
**檔名**：`features/define_problem.feature`
**對應 PRD**：US-101, US-102
**對應頁面**：P05 TaskDefinition, P06 Explore

```gherkin
# Feature: 早期問題定義
# 目的: RD 能在 30 秒內把多模態素材轉為結構化 Brief，並透過七類蘇格拉底提問識別矛盾與假設。
# 對應 PRD: 02_prd.md#epic-1

Feature: 早期問題定義（Phase I — Define）

  Background:
    Given 我是登入的機構 RD「alice@delta.com」
    And 我已建立專案「ebike-drive-unit-v2」
    And 我位於 "/projects/ebike-drive-unit-v2/brief" 頁面

  @happy-path @smoke-test @triz-step-0
  Scenario: 上傳 PDF 後 AI 自動萃取約束並預填 Brief
    Given 我有一份「需求規格書.pdf」（含尺寸、扭矩、成本上限）
    When 我將檔案拖放至「上傳區」
    Then 我應該看到上傳進度條
    And 上傳完成後系統應該觸發 AI 萃取
    And 我應該在 30 秒內看到 Brief 表單已預填
    And 預填欄位應該包含「硬約束」、「軟目標」、「KPI」
    And 每個欄位應該有「來源連結」回到原始 PDF 的位置

  @sad-path
  Scenario: 上傳不支援的檔案格式
    When 我嘗試上傳「.zip」格式檔案
    Then 我應該看到錯誤訊息「不支援此檔案格式」
    And 我應該看到支援格式提示「PDF / DOCX / XLSX / JPG / PNG / STEP」

  @happy-path @triz-step-1 @socratic
  Scenario: 七類蘇格拉底提問引導識別矛盾
    Given Brief 已完成且 Gate D1 已通過
    When 我點擊「進入 Explore」
    Then 我應該看到 7 類問題分組（boundary / function / resource / time / environment / human / counter）
    And 每類問題應該有 AI 預生成的 ≥ 2 條問題
    When 我回答問題「軸向長度限制是否必須 ≤ 92mm？」為「是，這是強制約束」
    And 我點擊「標記為矛盾」
    Then 系統應該將該回答自動 formalize 為矛盾記錄
    And 矛盾應該包含「improving_param」與「worsening_param」

  @edge-case
  Scenario Outline: 上傳檔案大小邊界
    When 我上傳「<filename>」（大小 <size>）
    Then 我應該看到「<expected>」

    Examples:
      | filename       | size  | expected                          |
      | small.pdf      | 2MB   | 上傳成功                          |
      | medium.pdf     | 19MB  | 上傳成功                          |
      | huge.pdf       | 21MB  | 錯誤：檔案超過 20MB 限制          |
      | empty.pdf      | 0KB   | 錯誤：檔案為空                    |
```

---

### Feature 2
**檔名**：`features/phase_gate_check.feature`
**對應 PRD**：US-103
**對應頁面**：所有 Gate 頁（Explore D2, Track X1, Create X2, PreCAD P, Review V1, Decide V2, Feynman V4）

```gherkin
# Feature: Phase Gate 退出檢查
# 目的: 確保每個 Phase 的退出條件全部滿足才能授權進入下一階段。
# 對應 PRD: 02_prd.md US-103

Feature: Phase Gate 退出檢查

  Background:
    Given 我是 RD 主管「bob@delta.com」（具有 Gate 簽核權限）

  @happy-path @gate
  Scenario: Gate D2 全部條件滿足，授權進入 Phase II
    Given 專案「ebike-drive-unit-v2」位於 Phase I Explore 階段
    And 累計回答數 = 12（≥ 10 ✓）
    And 7 類問題皆有回答（✓）
    And 矛盾全部分類為 TC/PC/SF（✓）
    And 已建立 ≥ 1 個因果迴路圖（✓）
    And 已標記 ≥ 3 個斷路點（✓）
    When 我打開 ExploreGates 面板
    Then 我應該看到「Gate D2: 5/5 條件達成」
    And 「下一步」按鈕應該為可點擊
    When 我點擊「通過 → 進入 Track」
    Then 我應該被導向 "/projects/.../track"
    And 系統應記錄 Gate D2 通過時間與簽核人

  @sad-path @gate
  Scenario: Gate 條件未滿足時阻擋通過
    Given 累計回答數 = 7（< 10 ✗）
    When 我打開 ExploreGates 面板
    Then 「下一步」按鈕應該為 disabled
    And 我應該看到「未達成 1 項：累計回答數需 ≥ 10（目前 7）」

  @edge-case @gate
  Scenario: 零矛盾專案的 Gate D2 通過規則
    Given 專案無任何識別矛盾
    And 用戶已選「確認此專案無矛盾」
    Then Gate D2 矛盾相關條件應該視為通過
    And 我可正常通過 Gate D2

  @gate @override
  Scenario: RD 主管覆寫 Gate 判定（含理由）
    Given 系統判定 Gate 未通過（4/5 條件達成）
    When 我點擊「主管覆寫」
    And 我輸入覆寫理由「該未達條件不適用本專案類型」
    Then 系統應該記錄覆寫事件、人員、時間、理由
    And Gate 應該顯示為「已覆寫通過」狀態
```

---

### Feature 3
**檔名**：`features/triz_solve.feature`
**對應 PRD**：US-201, US-202
**對應頁面**：P08 Create

```gherkin
# Feature: TRIZ 三路徑求解（含 L1 跨域去錨定）
# 目的: 對識別出的 TC 在 60 秒內產出分層解法卡，並在 Decision Hub 提供 CCI/Evidence 標記。
# 對應 PRD: 02_prd.md US-201, US-202

Feature: TRIZ 三路徑求解

  Background:
    Given 我是機構 RD
    And 專案「ebike-drive-unit-v2」已 formalize 5 個 TC
    And 我位於 "/projects/.../create" 頁面 Step 1（X2）

  @happy-path @triz-step-2 @triz-step-3
  Scenario: 對單一 TC 觸發 TRIZ 三路徑求解
    Given 我選擇「TC1: torque density vs. volume」
    When 我點擊「求解」按鈕
    Then 系統應該觸發 OZ-OT 分析（locks Px variable）
    And 我應該在 60 秒內看到分層解法卡片：
      | Layer | Description |
      | L1    | 具體解（含跨域去錨定）|
      | L2    | 根因解 |
      | L3    | 結構旁路 |
    And 每層應該包含 F/S/OZ/OT/Solution 五元組
    And 每層應該標記「信心等級」（HIGH/MEDIUM/LOW）

  @happy-path @sim-matrix
  Scenario: 多 TC 求解後產出 SIM 矩陣
    Given ≥ 2 個 TC 已求解
    When 我點擊「執行 SIM 評估」
    Then 系統應該產出 +1/0/-1 交互矩陣
    And 矩陣應該標記出 conflict pairs
    And 對 -1 衝突項應該顯示「建議回流處理」提示

  @happy-path @decision-hub
  Scenario: Decision Hub 攤平所有候選方案
    Given 所有 TC 已求解
    When 我進入 Step 3（X4 候選方案決策中心）
    Then 我應該看到 Evidence Coverage Gauge（< 40% 顯示橘色警告）
    And 每張方案卡應該顯示 CCI Badge（Evolution / Weak Evolution / Patch）
    And CCI 為「Patch」的方案 hover 時應該提示「建議記錄技術債」

  @sad-path
  Scenario: TRIZ 求解失敗的降級處理
    Given AI 服務暫時無法回應
    When 我點擊「求解」
    Then 我應該看到 toast「AI 暫時無法生成，請稍後重試」
    And 系統不應該阻擋我手動編輯解法
```

---

### Feature 4
**檔名**：`features/precad_review.feature`
**對應 PRD**：US-203
**對應頁面**：P09 PreCadReview

```gherkin
# Feature: Pre-CAD 五維審查（Gate P）
# 目的: 確認候選方案在進入 CAD 前 Fatal+Major 矛盾 100% 解決，五維評分通過門檻。
# 對應 PRD: 02_prd.md US-203

Feature: Pre-CAD 五維審查

  Background:
    Given 我是 RD 主管
    And 專案位於 "/projects/.../pre-cad" 頁面
    And 候選方案集合已通過 MUST 快篩

  @happy-path @gate-p
  Scenario: 五維評分通過 Gate P 門檻
    Given 候選方案 A 評分如下：
      | Dimension          | Score |
      | 空間約束           | 4/5   |
      | 解耦程度           | 5/5   |
      | 可驗證性           | 4/5   |
      | 主要風險           | 3/5   |
      | 最小 CAD 工作量    | 4/5   |
    And Fatal 矛盾解決率 = 100%
    And Major 矛盾解決率 = 95%（≥ 90% ✓）
    When 我點擊「批准進入 CAD 階段」
    Then 系統應該產生 Validation Passport
    And 我應該被提示「下一步：通知 RD 進行 CAD 建模」

  @sad-path @gate-p
  Scenario: Fatal 矛盾未 100% 解決阻擋通過
    Given 候選方案 B 的 Fatal 矛盾解決率 = 80%
    When 我嘗試批准
    Then 系統應該阻擋「Gate P 強制要求 Fatal 100% 解決」
    And 系統應該顯示未解決的 Fatal 矛盾清單
```

---

### Feature 5
**檔名**：`features/ai_devil_advocate.feature`
**對應 PRD**：US-301
**對應頁面**：P11 DesignReview

```gherkin
# Feature: AI 黑帽質疑（Devil's Advocate）
# 目的: CAD 完成後，AI 主動扮演挑戰者角色，補齊證據缺口。
# 對應 PRD: 02_prd.md US-301

Feature: AI 黑帽質疑

  Background:
    Given 我是機構 RD
    And 候選方案 A 已通過 Gate P 並完成 CAD
    And 我位於 "/projects/.../review" 頁面（V1）

  @happy-path @ai
  Scenario: 觸發黑帽質疑產出 ≥ 3 條問題
    When 我點擊「黑帽質疑」按鈕
    Then 系統應該觸發 socraticGenerate
    And 我應該在 30 秒內看到 ≥ 3 條質疑問題
    And 每條質疑應該含「假設挑戰」+「驗證建議」
    Examples:
      | Q                                      | Verification Suggestion |
      | 此設計在極端高溫下是否仍可靠？           | T-102 高溫運轉測試      |
      | 若供應商 A 缺料，B/C 替代方案的成本影響？| 採購備援方案調研        |

  @happy-path @evidence-gap
  Scenario: AI 偵測證據缺口並建議最小實驗
    Given 風險登錄含「軸承壽命」項目（信心等級 LOW）
    When 我打開「Evidence Gap Detection」面板
    Then 系統應該偵測到 LOW 信心項目
    And 系統應該建議「最小實驗：T-102 加速壽命測試」
    And 建議應該連結至測試規範（如 IEC 60068）
```

---

### Feature 6
**檔名**：`features/kt_decision_record.feature`
**對應 PRD**：US-302
**對應頁面**：P12 DecisionRecord

```gherkin
# Feature: KT 決策記錄
# 目的: 完整記錄設計決策（MUST/WANT/AC），確保可追溯、可解釋、可簽核。
# 對應 PRD: 02_prd.md US-302

Feature: KT 決策記錄

  Background:
    Given 我是專案 PM
    And 專案位於 "/projects/.../decide" 頁面（V2）

  @happy-path @kt
  Scenario: 完成 KT 四階段填寫
    Given 候選方案 A、B、C 已通過 V1
    When 我完成 MUST 篩選（A、B 通過）
    And 我完成 WANT 評分（A: 85, B: 78）
    And 我完成 AC 評估（A 負面後果可接受、B 中度風險）
    And 我選擇「主路線：A」「備援：B」
    And 我輸入「選擇理由」與「風險接受聲明」
    Then 我應該能點擊「確認決策」
    And 表單應該變為「已確認」狀態並鎖定（isLocked=true）

  @happy-path @signoff
  Scenario: 多人簽核流程
    Given 決策已確認
    When RD 主管簽核
    And PM 簽核
    And 品質工程簽核
    Then 每位簽核人應該記錄「姓名、角色、簽核時間」
    And 全部簽核完成後狀態應該為「已簽核」
    And 我應該能匯出 PDF 報告

  @sad-path @lock
  Scenario: 嘗試修改已鎖定的決策
    Given 決策狀態 = 已鎖定
    When 我嘗試編輯任一欄位
    Then 表單應該保持唯讀
    And 我應該看到「請先點擊『回到草稿』解鎖」
```

---

### Feature 7
**檔名**：`features/knowledge_writeback.feature`
**對應 PRD**：US-303
**對應頁面**：P13 Feynman

```gherkin
# Feature: 知識資產自動產出（Feynman）
# 目的: AI 自動將決策、實驗、矛盾解法轉化為 6 類知識資產，組織學習自動化。
# 對應 PRD: 02_prd.md US-303

Feature: 知識資產自動產出

  Background:
    Given 我是機構 RD
    And 專案已完成 V2（決策記錄已簽核）
    And 我位於 "/projects/.../feynman" 頁面（V4）

  @happy-path @knowledge
  Scenario: Knowledge Agent 全自動產出 6 類資產
    When 我點擊「生成知識條目」
    Then 系統應該觸發 Knowledge Agent
    And 我應該看到產出條目分為 6 類：
      | Asset Type | Source                |
      | 決策記錄   | DecisionRecord 簽核版 |
      | 實驗結果   | T-102 測試報告        |
      | 矛盾解法   | TC1-TC5 採用方案      |
      | 失效模式   | Risk Register 高風險  |
      | 設計規則   | Pre-CAD 五維分析      |
      | 最佳實踐   | RD 標記為「值得參考」 |
    And 每條目應該標記「待審閱」狀態

  @happy-path @review
  Scenario: RD 審閱確認知識條目
    Given 6 類條目已生成
    When 我點擊條目「KE-001 磁力耦合傳動系統設計要點」
    And 我審閱後點擊「確認審閱」
    Then 條目狀態應該變為「已寫入知識庫」
    And 條目應該出現在 KnowledgeBase 頁面

  @gate-v4
  Scenario: Gate V4 完整性檢查
    Given 已生成 ≥ 1 條知識條目
    And 6 類資產皆已覆蓋
    And 所有條目已審閱
    Then Gate V4 應該標記為通過
    And 「結束專案」按鈕應該變為可點擊
```

---

## Ⅳ. 最佳實踐

1. **一個 Scenario 只測一件事**：保持每個場景的專注性。
2. **使用陳述式而非命令式**：
   - ✅ `Then I should be redirected to "/track"`
   - ❌ `Then the system redirects me to "/track"`
3. **避免 UI 細節**：BDD 關注「行為」，不關注顏色/元素 ID。
   - ✅ `When I confirm the contradiction`
   - ❌ `When I click the green button with id="btn-confirm"`
4. **TRIZ 術語要對齊**：使用 `auto_triz_strategy.md` 與 skill 規格的詞彙（TC/PC/SF、OZ-OT-Px、CCI、Evidence Coverage…）。
5. **Tag 規範**：
   - `@happy-path` / `@sad-path` / `@edge-case`
   - `@triz-step-N`（標記對應 TRIZ 步驟）
   - `@gate-{D1/D2/X1/X2/P/V1/V2/V4}`
   - `@smoke-test`（CI/CD 必跑）
   - `@ai`（涉及 LLM 服務）

**LLM Prompting Guide**：
> 請根據以下的 BDD 情境，使用 Clean Architecture 和 TDD 方法，為我生成對應的 Controller、Use Case、Entity 以及一個初步的、會失敗的單元測試。情境如下：[貼上 Gherkin Scenario 文本]

---

## Ⅴ. 與 PRD User Story 對應表

| PRD Story ID | BDD Feature | Scenario 數 | 主要 Tag |
|:-------------|:------------|:------------|:---------|
| US-101 | Feature 1 | 4 | @triz-step-0, @happy-path |
| US-102 | Feature 1 | 1 | @triz-step-1, @socratic |
| US-103 | Feature 2 | 4 | @gate, @override |
| US-201 | Feature 3 | 2 | @triz-step-2, @triz-step-3 |
| US-202 | Feature 3 | 1 | @decision-hub |
| US-203 | Feature 4 | 2 | @gate-p |
| US-301 | Feature 5 | 2 | @ai, @evidence-gap |
| US-302 | Feature 6 | 3 | @kt, @signoff, @lock |
| US-303 | Feature 7 | 3 | @knowledge, @review, @gate-v4 |

---

## 文件溯源

- 模板：`VibeCoding_Workflow_Templates/03_behavior_driven_development_guide.md`
- PRD：[`02_prd.md`](./02_prd.md)
- 既有頁面規格：`docs/01-define/pages/INDEX.md` § 18 頁
- TRIZ 策略：`docs/_harness/auto_triz_strategy.md`
- Skill 規格：`.claude/skills/triz-*` / `.claude/skills/tr-*`
