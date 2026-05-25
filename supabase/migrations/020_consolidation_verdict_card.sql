-- Phase 3: Intra-contradiction compatibility + EngineeringVerdictCard storage
--
-- 對應 plans/triz-redesign.md Phase 3 §A (同矛盾相容性) 與 §4 (Q1–Q8 工程審判卡)。
--
-- intra_compatibility: list[IntraContradictionCompatibility]
--   每條矛盾若 RD 勾選多個方向，就有一筆 pairwise + max_compatible_subsets 報告。
--
-- verdict_card: EngineeringVerdictCard（Q1–Q8 八節）
--   整併方案產出後立即跑 LLM 產出，前端展開「跨矛盾整併」按鈕後顯示。
--
-- 兩個欄位都 nullable + default empty → 舊資料相容性 100%.

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS intra_compatibility JSONB DEFAULT '[]'::JSONB,
  ADD COLUMN IF NOT EXISTS verdict_card JSONB;

COMMENT ON COLUMN triz_consolidation_results.intra_compatibility IS
  'Phase 3 §A: list[IntraContradictionCompatibility] — 每條矛盾多選方向的兩兩相容性 + max independent subsets.';

COMMENT ON COLUMN triz_consolidation_results.verdict_card IS
  'Phase 3 §4: EngineeringVerdictCard — 整併方案的 Q1–Q8 工程審判結果 (mechanism_trace / feasibility_matrix / cld side-effects / coverage / verification / duty_cycle / boundary_collapse + final_verdict).';
