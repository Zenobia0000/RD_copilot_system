-- PR2-Lite: candidate_pools / exhausted_contradictions / total_rounds
--
-- 對應 plans/triz-redesign.md PR2-Lite 分數損失最小化候選池演算法。
--
-- 背景（語意 3 — 使用者勾的是候選池）：
--   原本 consolidation 用「Top1 + 系統 Top1→Top2 swap」決策，缺乏多選彈性。
--   PR2-Lite 重新定義：
--     • 使用者在 DecisionCard 勾選的 N 個方向 = 該矛盾的「候選池」
--     • 演算法初始用各池首位，衝突時換池內下一名（每輪只換「分數損失最小」者）
--     • 最終 adopted_directions[cid] 仍只是 1 個 DirectionGroup
--     • 但 candidate_pools[cid] 完整保留整個池（含未被採用的 fallback）給前端展開顯示
--     • 池用盡仍無法整合 → 加入 exhausted_contradictions list，前端顯示「卡點分析」
--     • total_rounds 紀錄演算法跑了幾輪，給前端「AI 嘗試 N 種組合」文案
--
-- 三個欄位全部 nullable + default → 舊 row 自動 fallback；前端 hook 兼容 undefined。

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS candidate_pools JSONB DEFAULT '{}'::JSONB;

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS exhausted_contradictions JSONB DEFAULT '[]'::JSONB;

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS total_rounds INTEGER DEFAULT 0;

COMMENT ON COLUMN triz_consolidation_results.candidate_pools IS
  'PR2-Lite: dict[contradiction_id → list[DirectionGroup]]，使用者勾選的整個候選池（依分數降冪）。前端展開區顯示「採納方向 + 其他 fallback」。舊 row 為 {}。';

COMMENT ON COLUMN triz_consolidation_results.exhausted_contradictions IS
  'PR2-Lite: list[contradiction_id]，演算法卡住時候選池已用盡的矛盾 IDs。conflict status 時非空，前端 PR1-8 conflict UI 用於顯示「卡點分析」。';

COMMENT ON COLUMN triz_consolidation_results.total_rounds IS
  'PR2-Lite: 演算法執行的輪次數（含初始 LLM check）。0 = 沒跑演算法（單矛盾 fallback）。前端用於文案「AI 嘗試 N 種組合」。';
