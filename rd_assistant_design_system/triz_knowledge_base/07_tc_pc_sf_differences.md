# TC / PC / SF 差異對照（矛盾形態 × 知識檔 × Prompt）

> **用途**：與 `06_tc_pc_sf_flows.md`（流程與區塊圖）互補；本檔以**表格化差異**說明三徑在**問題定義、判定準則、KB 注入、後端 Prompt 共用性**上的不同。  
> **實作對照**：`backend/app/agents/triz_solver.py`、`backend/app/prompts/triz_solver.py`、`backend/app/tools/triz_kb.py`、`backend/app/models/schemas.py`（`TrizLookupRequest`）。

---

## 1. 矛盾形態差異（何時用哪一徑）

| 維度 | **TC** 技術矛盾 | **PC** 物理矛盾 | **SF** Su-Field |
|------|-----------------|-----------------|------------------|
| **核心句式** | 改善參數 **#i** → 惡化參數 **#j**（兩個 **不同**的 39 參數） | **同一**物件／介面上的**同一屬性 P** 需同時為 **A** 與 **¬A**（互斥） | **S1–S2–F** 不完整、有害、或效應不足 |
| **TRIZ 結構** | (i, j) ∈ 39×39，查矩陣 | 分離維度：時間／空間／條件／整體–局部 | 物質–場模型 + 76 標準解 |
| **典型誤判** | 把「同一屬性兩頭拉」硬塞成兩參數 TC | 把「i vs j 取捨」當成 PC（其實是 TC） | 未建 Function Model 就無法穩定填 S1/S2/F |

### 1.1 PC 的「同一參數 A / ¬A」判定要點

1. **同一性**：矛盾是否落在**單一可命名屬性** P（如厚度、剛度、通透度），而非兩個不同工程參數的取捨。  
2. **互斥性**：在**未**引入時間／空間／條件／尺度分離前，A 與 ¬A **不能同時成立**。  
3. **與 TC 分流**：若能乾淨對應到「改善 #i、惡化 #j」且意義完整 → 優先 **TC**；若剩餘核心是「P 既要又要互斥」→ **PC**。  

理論表述見 `04_separation_principles.md`（物理矛盾與解耦維度）。

---

## 2. 知識檔（靜態 KB）差異

| 知識檔 | TC | PC | SF |
|--------|:--:|:--:|:--:|
| `01_39_parameters.md` | 常用（映射與驗證） | 選用（屬性語言可對照參數，非必須） | 選用 |
| `02_contradiction_matrix.md` | **必用**（查表） | 不用 | 不用 |
| `03_40_principles.md` | **必用**（矩陣候選原理切片／具體化） | **必用**（分離後對應原理；可全量或依分離類子集） | 選用 |
| `04_separation_principles.md` | 不用 | **必用** | 不用 |
| `05_76_standard_solutions.md` | 不用 | 不用 | **必用** |

---

## 3. 後端 Prompt 組合：何者共用、何者分離

| 層級 | TC | PC | SF | 是否共用 |
|------|----|----|-----|----------|
| **System** | `TRIZ_SOLVER_SYSTEM` | 同左 | Su-Field 另有分析模板 | TC 與 PC **共用**同一 System；SF 使用不同 task 模板鏈 |
| **User 任務模板** | `TRIZ_TC_INSTANTIATION` | `TRIZ_PC_INSTANTIATION` | `SUFIELD_ANALYSIS`（等） | **不共用** |
| **`triz_context` 組裝** | `build_triz_tc_context`：01 + 矩陣結果 + **候選** 03 切片 | `build_triz_pc_context`：04 + 03（全或子集） | `build_sufield_context`（05 等） | **不共用** |
| **規則引擎步驟** | `lookup_matrix(improving, worsening)` | 無矩陣查表 | 狀態分類 + 標準解匹配邏輯 | 路徑不同 |

**結論**：**TC 與 PC 共用 System prompt**；**User 模板與 KB 拼裝分離**；**40 原理（03）在 TC、PC 兩徑都會進上下文，但 TC 與矩陣候選綁定，PC 與分離策略／可選子集綁定**。

---

## 4. API 槽位差異（`TrizLookupRequest` 對齊）

| 欄位 | TC | PC | SF |
|------|:--:|:--:|:--:|
| `type` | `TC` | `PC` | `SF` |
| `natural_description` |  |  |  |
| `improving_param`, `worsening_param` | 必填（1–39） | 不用 | 不用 |
| `physical_contradiction` | 不用 | 建議必填（A vs ¬A 句式） | 不用 |
| `sf_substance_1`, `sf_substance_2`, `sf_field` | 不用 | 不用 | 與模型一致時必填 |

---

## 5. 輸出語意差異（摘要）

|  | TC | PC | SF |
|--|----|----|-----|
| 主軸 | `candidate_principles` + 具體化 `suggestions`，`path=TC` | `suggestions` 帶 `separation_principle`，`path=PC` | `su_field`、`system_state`、`matched_solutions` |
| 與 40 原理 | 矩陣推薦編號為主 | 模板要求分離後對應到原理 | 標準解編號（76）為主 |

---

## 6. 與其他檔案關係

| 檔案 | 角色 |
|------|------|
| `06_tc_pc_sf_flows.md` | 流程步驟 + Mermaid 區塊圖（含 Prompt Ingress/Compose/Parse） |
| **本檔 `07_tc_pc_sf_differences.md`** | 差異矩陣與判定／共用性速查 |
| `README.md` | 檔案索引與注入策略 |

---

*文件版本：與 repo 內 AutoTRIZ Step 5a 路由一致；若 `schemas.py` 或 `triz_solver` 欄位變更，請同步更新 §4、§5。*
