# Subsystem 持久化策略（WBS 2.4）

> **對齊**：`Subsystem_Interface_Development_WBS.md` §2.4、`Forward_Subsystem_Discovery_Architecture.md` §7.1
> **目的**：凍結「誰寫 `subsystems` 表」，避免 FE 與後端雙寫競態。

---

## 決策摘要


| 寫入情境                              | 寫入方                                 | 觸發                                                                                              | 備註                                      |
| --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------- |
| AI 建議產出                           | **前端（useSubsystemSuggestion hook）** | UC1 `POST /subsystems/suggest` 回傳 → FE 收到完整樹 → clear 舊 AI rows → batch insert 新 rows *(v9: 原 `/scamper/subsystem-suggestions`)* | 後端**不**直接寫 Supabase；只回傳 JSON 讓 FE 決定持久化 |
| RD 手動新增                           | **前端**                              | `createSubsystem()` mutation                                                                    | 單筆 insert                               |
| RD 編輯六維                           | **前端**                              | `updateSubsystem()` mutation（`RDEdited` 狀態）                                                     | 逐節點 patch                               |
| RD 勾選「已確認」                        | **前端**                              | checkbox → `updateSubsystem({confirmed: true})`                                                 | 不觸發後端副作用                                |
| RD 刪除                             | **前端**                              | `deleteSubsystem()` mutation                                                                    | 單筆 delete                               |
| 空間覆寫（project_component_overrides） | **後端**                              | `POST /spatial/component-overrides`                                                             | **不同表**，不與 subsystems 表競寫               |
| 空間推升 learned（learned_components）  | **後端**                              | `POST /spatial/learned-components`                                                              | **不同表**，後端獨占寫入                          |


## 為什麼這樣分

1. **後端無狀態**：`suggest_subsystems` 是 stateless RPC — LLM 呼叫 + 型別檢查後回傳，不持久化。這讓 UC1 可以重試、可以 local-mock、可以被 Wave 4 契約測試以 stub LLM 的方式完整覆蓋而無需真正 Supabase。
2. **FE 擁有 cache**：React Query 是 subsystems 樹的權威 cache；若後端也寫，就會有「剛寫完但 hook 還沒 invalidate」的短暫不一致。
3. **Override / learned 是獨立表**：這兩者**不是** subsystems，而是 spatial resolver 的輔助儲存，後端獨占寫入不會與 FE 衝突。

## 例外與警示

- ❌ **不得**在後端任何 router（`/subsystems/`*）內直接 `supabase.table("subsystems").upsert(...)` *(v9: 原 `/scamper/`)*
- ❌ **不得**在 FE 以 raw SQL 或 service role key 寫 `project_component_overrides` / `learned_components`
- ⚠️ 若日後需要 **後端接管** subsystems 寫入（例如要加寫入時的 server-side 驗證），必須：
  1. 移除所有 FE 的 direct write mutation
  2. 改為 `POST /subsystems/sync` 端點
  3. 更新本文件、`Three_Tier_Tree_Review_Checklist.md`、`test_subsystem_contract.py`
  4. 同步變更時機在 PR description 明確標註「改動 WBS 2.4」

## 測試依據

- **Contract test**（`backend/tests/test_subsystem_contract.py::TestSubsystemSuggestionsContract`）：`TestClient` round-trip 不涉及 Supabase，證明後端 handler 不寫表。
- **Integration test**（`backend/tests/test_subsystem_integration.py::TestOverrideHitsL1OnNextLookup`）：明確測試 override 寫入到 `project_component_overrides`，與 subsystems 表無關。

---

**修訂紀錄**

- 2026-04-09 v1.0：首版，凍結 FE 寫 subsystems / 後端寫 override+learned 的分工。

