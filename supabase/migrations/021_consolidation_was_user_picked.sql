-- Phase 3 bugfix: was_user_picked column on triz_consolidation_results
--
-- 對應 plans/triz-redesign.md Phase 3 bugfix (Bug 2)。
--
-- 背景：consolidate_solutions 之前用 status="resolved_with_swap" 同時表達兩種事情：
--   1. 系統自動把 Top1 swap 成 Top2 來解 conflict（真正的 swap）
--   2. RD 在 DecisionCard 直接勾選的方向「剛好不是 Top1」（user pick）
--
-- 這是錯的：user pick ≠ system swap，UI 文案會誤導 RD「系統幫你替換了」。
-- bugfix 拆開：
--   - status = "resolved_with_swap" 嚴格代表「系統做了 swap」。
--   - was_user_picked dict[cid → direction_id] 記錄「RD 勾的方向」。
-- 前端 UI 用 was_user_picked 顯示「使用您勾選的方向」徽章 (藍色)；用「採用方向 ≠ Top1
-- 且 cid ∉ was_user_picked」判斷「Top2 替換」徽章 (琥珀色)。
--
-- 此欄位 nullable + default empty → 舊資料 row 自動 fallback 成空 dict，
-- TypeScript hook 把 undefined 視為「沒有 user pick」。

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS was_user_picked JSONB DEFAULT '{}'::JSONB;

COMMENT ON COLUMN triz_consolidation_results.was_user_picked IS
  'Phase 3 bugfix (Bug 2): dict[contradiction_id → direction_id]，RD 在 DecisionCard 直接勾選的方向。與 status=resolved_with_swap (系統 swap) 互斥；UI 用此區分「使用您勾選的方向」vs「Top2 替換」徽章。';
