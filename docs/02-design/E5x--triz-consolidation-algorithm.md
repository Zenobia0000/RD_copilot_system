# TRIZ 跨矛盾方向整併演算法

> 版本：PR2-Lite (2026-05) — 分數損失最小化候選池演算法
> 對應實作：
> - [`backend/app/agents/triz_solver.py::consolidate_solutions`](../../backend/app/agents/triz_solver.py)
> - [`backend/app/agents/triz_solver.py::_score_loss_optimized_swap`](../../backend/app/agents/triz_solver.py)
> - [`src/components/create/ConsolidationPanel.tsx`](../../src/components/create/ConsolidationPanel.tsx)

---

## 1. 演算法目標

每條矛盾各有一個 RD 在 DecisionCard 勾選的方向集合（候選池），跨矛盾整併要做的是：

> **從各候選池各挑一個方向，組成一組「跨矛盾相容」的最終決策**

這是一個小型組合最佳化問題，搜尋空間 = ∏ |候選池_i|；對 5 矛盾 × 各池 ≤ 6 方向最壞 7776 種組合。直接窮舉 + 每組丟 LLM 顯然不可行（單組 LLM call ≈ 4 秒 → 8 小時）。

---

## 2. 語意 3 — 候選池而非全採納

| 語意 | 使用者勾的方向意義 | 演算法行為 | 為什麼選這個 |
|---|---|---|---|
| 1 | 全部都採納（並列實作） | 跨矛盾要對全部 picks 笛卡兒 LLM 檢查 | LLM 量爆炸 |
| 2 | 合併描述送 LLM | 把多個方向當成一個複合方向 | 整併語意混亂、verdict 無法歸屬 |
| **3** | **候選池**：實際採納一個，其他作 fallback | 演算法挑代表方向，衝突時換池內下一名 | **本系統採用** |

**語意 3 落地的契約**：
- `adopted_directions[cid]: DirectionGroup` — 演算法選定的單一代表方向
- `candidate_pools[cid]: list[DirectionGroup]` — 完整候選池（依分數降冪）
- 前端 `ConsolidationPanel` 在採納方向下方展開 fallback 清單

---

## 3. 分數損失最小化演算法

### 3.1 核心想法

每次只換**一條**矛盾，而且只換「**衝突涉及的、損失分數最少**」那條。

### 3.2 偽碼

```python
def score_loss_optimized_swap(candidate_pools, results_by_cid):
    # 初始：每條矛盾用池首位（最高分）
    pool_idx = {cid: 0 for cid in candidate_pools}
    assignment = {cid: pool[0] for cid, pool in candidate_pools.items()}
    exhausted = set()
    visited = set()
    max_rounds = N + 5  # N = 矛盾數

    for round in range(max_rounds):
        # 1. LLM 跨矛盾相容性檢查（用當前 assignment 的代表方向）
        conflicts = check_compatibility(assignment)
        if not conflicts:
            return success(assignment, exhausted, rounds_run=round+1)

        # 2. 收集衝突涉及的矛盾 IDs
        conflict_cids = {c.a_id for c in conflicts} | {c.b_id for c in conflicts}

        # 3. 計算每個衝突方換到下一名的分數損失
        candidates = []
        for cid in conflict_cids - exhausted:
            next_idx = pool_idx[cid] + 1
            if next_idx >= len(candidate_pools[cid]):
                exhausted.add(cid)  # 此池用盡
                continue
            cur_score = score_of(cid, pool_idx[cid])
            next_score = score_of(cid, next_idx)
            candidates.append((cid, next_idx, cur_score - next_score))

        if not candidates:
            return conflict(assignment, conflicts, exhausted, rounds_run=round+1)

        # 4. 選 loss 最小（同 loss 取 cid 字母序）執行 swap
        chosen_cid, new_idx, _ = min(candidates, key=lambda t: (t[2], t[0]))
        assignment[chosen_cid] = candidate_pools[chosen_cid][new_idx]
        pool_idx[chosen_cid] = new_idx

        # 5. 死循環偵測（理論上單調，但保險）
        sig = frozenset((cid, pool_idx[cid]) for cid in candidate_pools)
        if sig in visited:
            return conflict(...)
        visited.add(sig)

    return conflict(...)  # 超過 max_rounds
```

### 3.3 走一遍範例

5 條矛盾、每池分數：

| 矛盾 | 候選池（DirID:分數） |
|---|---|
| C1 | D1.1:95, D1.2:85 |
| C2 | D2.1:90, D2.2:70 |
| C3 | D3.1:88 |
| C4 | D4.1:82, D4.2:75 |
| C5 | D5.1:80 |

**Round 1**：assignment = (D1.1, D2.1, D3.1, D4.1, D5.1)
- LLM 回報：`C1↔C2 衝突`, `C2↔C4 衝突`
- conflict_cids = {C1, C2, C4}
- 損失：C1→D1.2 損失 10；C2→D2.2 損失 20；C4→D4.2 損失 7
- 選 C4 → swap

**Round 2**：assignment = (D1.1, D2.1, D3.1, **D4.2**, D5.1)
- LLM 回報：`C1↔C2 衝突`
- conflict_cids = {C1, C2}
- 損失：C1→D1.2 損失 10；C2→D2.2 損失 20
- 選 C1 → swap

**Round 3**：assignment = (**D1.2**, D2.1, D3.1, D4.2, D5.1)
- LLM 回報：無衝突
- **成功**，總損失 = 7 + 10 = 17

對照「固定順序 greedy」會先換 C1 → C2 → C4，累積損失 10+20+7=37。

### 3.4 複雜度

- **LLM 呼叫次數**：≤ max_rounds = N + 5（一輪一次跨矛盾相容性檢查）
- **時間**：5 矛盾最壞 10 次 LLM × 4 秒 ≈ 40 秒
- **最佳性**：local optimal（非全域最佳）。極端情境（兩個高損失 swap 各能單獨解但合起來不能解）可能漏組合，但實務上很少見。

---

## 4. 終止條件

| 條件 | Status | 解釋 |
|---|---|---|
| 無衝突且首輪通過 | `compatible` | 各池首位天然相容 |
| 無衝突但發生過 swap | `resolved_with_swap` | 至少一條被換到池內非首位 |
| 衝突方池全用盡 | `conflict` | exhausted_contradictions 非空 |
| Cycle 偵測觸發 | `conflict` | 同一 assignment 重複出現 |
| 超過 max_rounds | `conflict` | 安全 fallback |

---

## 5. 重要限制聲明（LLM-only）

### 5.1 整併「相容」≠ 物理可行

整併使用的 LLM 比對只看：
- direction_name / direction_summary（文字摘要）
- affected_modules（影響的子系統名稱）
- secondary_contradictions（次要矛盾文字描述）
- TC / PC / SF 工具支持數量

**LLM 看不到**：
- ❌ 物理量綱、能量平衡、阻抗匹配等量化資訊
- ❌ CAD 干涉、組裝順序、製造公差
- ❌ 熱/結構 simulation 結果
- ❌ KPI 真實達成度

### 5.2 因此整併結果只是「描述層級的粗篩」

| 能抓到 | 抓不到 |
|---|---|
| ✅「兩方向都要動 PCB 結構」這類模組重疊 | ❌ 兩方向阻抗匹配是否衝突 |
| ✅ 描述明顯互斥（「全密封 vs 開放散熱」） | ❌ 物理量綱、能量平衡不一致 |
| ✅ 同次要矛盾文字描述衝突 | ❌ 製造公差、組裝順序衝突 |

### 5.3 後續驗證必要

整併 status=`compatible` 並**不**代表「真的能一起做」，必須在後續階段實證：
1. **Pre-CAD 審查**：MUST 快篩 + 五維審查（解耦/可驗證性/失效機制/MVP CAD effort）
2. **Concept Architecture Pack**：介面契約、子系統分解的物理層級對齊
3. **Engineering Spec Drafts**：尺寸、材料、規格的數值驗證
4. **試作 / 試模**：實機驗證

前端 UI 已透過：
- `ConsolidationPanel` ⓘ tooltip
- `VerdictCardPanel` disclaimer

明確揭露此限制。

---

## 6. 卡住怎麼辦 (status=conflict)

前端 `ConsolidationPanel` 在 conflict 時呈現：

1. **標題**：「您勾選的方向無法全部整併（AI 嘗試了 N 種組合）」
2. **卡點分析（可摺疊）**：列出 `exhausted_contradictions`，告知「以下矛盾的候選池已用盡」
3. **衝突清單**：以 `📍 [矛盾 A] 方向 X ✗ [矛盾 B] 方向 Y / 原因 …` 結構呈現
4. **行動建議**：來自 LLM 的 `suggestions`

使用者的可選行動：
- **加勾**：在 exhausted 矛盾的 DecisionCard 加勾其他方向，提供 AI 更多 swap 彈性
- **取消勾**：取消衝突方的某個方向，讓另一邊有機會被選
- **改 brief / 重做方向分析**：上游矛盾本身的方向產出不夠多元

---

## 7. 與舊 (Phase 3) 演算法的差異

| Phase 3 (舊) | PR2-Lite (現在) |
|---|---|
| 衝突時 swap 為 Top2（固定的次選） | 衝突時 swap 為「池內下一名」（可多次） |
| swap 策略：所有 conflict cids 一次全 swap | swap 策略：每輪只換 1 條（loss 最小者） |
| 池只有 [Top1, Top2] 兩個 | 池由 RD 勾選決定，可達 6 個 |
| `adopted_directions` 只記 Top1 換 Top2 | 同左但池資訊保留在 `candidate_pools` |
| 沒有 exhausted / rounds 紀錄 | 完整紀錄供 UI 卡點分析 |

---

## 7.5. DB 持久化與失敗回報（2026-05 hardening）

### 7.5.1 背景：靜默 fallback 導致的 bug

舊版 [`_persist_consolidation_result`](../../backend/app/agents/triz_solver.py:4032) 用
寬鬆的 `except Exception` 把**任何** DB upsert 錯誤都當成「migration 未套用」處理：

```python
try:
    sb.table("triz_consolidation_results").upsert(full_payload).execute()
except Exception:                       # 寬鬆過頭！
    # pop 掉 verdict_card / was_user_picked / candidate_pools / ...
    # 再用 legacy 欄位重試
```

實際發生的 bug（2026-05 使用者回報）：

- 線上 Supabase 缺 migration 022 的三個欄位 (`candidate_pools` / `exhausted_contradictions` / `total_rounds`)。
- 每次整併都拋 `column ... does not exist` → fallback 觸發。
- 但 fallback 順手把 **migration 020/021 的 `verdict_card` / `was_user_picked`** 也 pop 掉。
- DB 寫進去的是「只有舊欄位」的半殘 row。
- 使用者第一次跑 OK（看的是 in-memory response）。
- 重整後 React Query `refetchOnMount: 'always'` 從 DB hydrate → 撈到半殘 row →
  - `was_user_picked = {}` → UI 誤把 RD 勾選的方向標成「Top2 替換」徽章
  - `verdict_card = null` 或更舊的殘值 → Q1–Q8 工程審判顯示錯誤

### 7.5.2 修復原則：**fail loud, not silent**

新版改用顯式錯誤判別 + 回傳結構化結果：

```python
def _persist_consolidation_result(...) -> PersistenceOutcome:
    try:
        sb.table(...).upsert(full_payload).execute()
        return PersistenceOutcome(status="ok", columns_written=[...])
    except Exception as exc:
        if _looks_like_missing_column_error(exc):
            # 只在錯誤訊息明確帶 column / 42703 / PGRST204 / schema cache 才 fallback
            try:
                sb.table(...).upsert(legacy_payload).execute()
                return PersistenceOutcome(status="partial", reason="...")
            except Exception as legacy_exc:
                return PersistenceOutcome(status="failed", reason=str(legacy_exc))
        else:
            # 非 schema 錯誤直接 failed，絕不 pop Phase 3 欄位
            return PersistenceOutcome(status="failed", reason=str(exc))
```

### 7.5.3 PersistenceOutcome 三種狀態

| status | 觸發條件 | DB 結果 | FE 行為 |
|---|---|---|---|
| `ok` | 完整 payload upsert 成功 | 所有欄位寫入 | `setQueryData` 寫 cache + 綠色成功 toast |
| `partial` | 第一次拋 column-missing → legacy fallback 成功 | 只有舊欄位寫入；Phase 3 欄位不存在 | **不**寫 cache + 黃色警告 toast，提示工程師執行 migration |
| `failed` | 非 schema 錯誤（network/RLS/JSON），或 legacy fallback 也失敗 | 完全沒寫 / 殘缺 | **不**寫 cache + 紅色錯誤 toast 請使用者重試 |

### 7.5.4 為什麼 partial / failed 都不能寫 cache？

`useTrizConsolidationResult` hook 設 `refetchOnMount: 'always'`，重整時會從 DB 取得真實狀態。
若 FE 把樂觀的 in-memory snapshot 寫進 cache，下次 mount 雖然 `refetch` 會校正，但 race 中
DB-wins useEffect 會把 cache 的舊值塞進 state；當 DB 上其實是殘缺 row、cache 是完整 snapshot，
就會出現使用者看到的「重整後資料突然變不對」現象。

正確做法：partial / failed 時讓 cache 維持空白，refetch 直接拿 DB 真實狀態（即使是殘缺的），
與 UI 顯示一致；同時透過 toast 提示使用者「DB 寫入有問題，請重試」。

### 7.5.5 FE 防禦補強：`isUserPicked` fallback

即使 DB `was_user_picked = {}`（partial persist 後），
[`ConsolidationPanel`](../../src/components/create/ConsolidationPanel.tsx:91) 仍能正確判別「使用您勾選的方向」徽章：

1. **Primary**：信任 backend 的 `consolidation.was_user_picked[cid]`
2. **Fallback**：若 backend 完全沒提供 was_user_picked（空 dict），改用 FE 端的 `pickedByContradiction[cid]` set 反推。

這條 fallback 是 defense-in-depth：在 partial persist / 舊 row / 還沒套 migration 020-022 的情境下，
仍然能在 UI 上做出正確判斷，不會錯把 RD 勾選的方向標成「Top2 替換」。

### 7.5.6 Migration 檢核

部署時應跑 [`scripts/inspect-consolidation-schema.mjs`](../../scripts/inspect-consolidation-schema.mjs) 驗證
`triz_consolidation_results` 表上有以下欄位：

```
status, adopted_directions, conflict_report, integration_advice,
intra_compatibility, verdict_card, was_user_picked,           ← migration 020/021
candidate_pools, exhausted_contradictions, total_rounds       ← migration 022
```

若缺任一欄位，整併會走 `partial` fallback，但所有 Phase 3 / PR2-Lite 功能都會降級。

---

## 8. 測試

關鍵 case 涵蓋於 [`backend/tests/integration/test_consolidate_phase3.py`](../../backend/tests/integration/test_consolidate_phase3.py)：

- **(a) 全相容**：各池首位天然相容 → status=compatible, rounds=1
- **(b) 一輪解決**：首位衝突，換 loss 最小者後 OK → status=resolved_with_swap
- **(c) 多輪解決**：累計 swap 多次後 OK
- **(d) 池用盡**：所有衝突方池只有 1 個方向 → status=conflict + exhausted 列出全部
