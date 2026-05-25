-- Phase 2: Add DecisionCard + SR weak warning fields to directed_triz_solutions
--
-- 對應 plans/triz-redesign.md §3 (DecisionCard) 與 §2.6 (weak warnings).
--
-- DecisionCard: 每條 direction 1 張選購卡，5 欄結構 + picked 狀態。
-- SrWeakWarning: score=1 的弱相關候選，UI 顯示為 ⚠️ tooltip 而非正式 SR。
--
-- 兩個欄位都 nullable + default empty array → 舊資料相容性 100%.

ALTER TABLE directed_triz_solutions
  ADD COLUMN IF NOT EXISTS decision_cards JSONB DEFAULT '[]'::JSONB,
  ADD COLUMN IF NOT EXISTS sr_weak_warnings JSONB DEFAULT '[]'::JSONB;

COMMENT ON COLUMN directed_triz_solutions.decision_cards IS
  'Phase 2: DecisionCard per direction (5 columns: one_liner / contradiction_face / resolution_status / quick_tags / combination_hints + picked).';

COMMENT ON COLUMN directed_triz_solutions.sr_weak_warnings IS
  'Phase 1 S0c: 弱相關候選 (score=1)，UI 顯示為 ⚠️ tooltip。';
