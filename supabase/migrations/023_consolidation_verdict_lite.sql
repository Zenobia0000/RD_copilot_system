-- VerdictLite — 對照 Brief 任務的精簡審判
--
-- 取代舊 verdict_card (Q1–Q8 工程審判卡) 欄位的新版審判結果。
-- 設計理念見 plans/triz-verdict-card-simplification.md。
--
-- 為什麼需要這個 migration：
--   - 使用者反映 Q1–Q8 結構太複雜、術語太多看不懂
--   - 下游 pipeline (pre-cad / concept architecture / engineering spec drafts)
--     完全沒讀過 verdict_card / Q1–Q8 任何子欄位，是死端點
--   - 新版改用「直接對照 brief 五件事 (mission/constraints/KPIs/SR/socratic/CLD)」
--     的結構，使用者讀起來就是「我 brief 寫的每件事，這方案有沒有達成」
--
-- Schema 形狀（對應 pydantic EngineeringVerdictLite）：
--   {
--     project_id, consolidation_id, overall_verdict, overall_headline, confidence,
--     mission_check: BriefItemCheck | null,
--     constraint_checks: BriefItemCheck[],
--     kpi_checks: BriefItemCheck[],
--     sr_checks: BriefItemCheck[],
--     socratic_checks: BriefItemCheck[],
--     cld_checks: BriefItemCheck[],
--     next_actions: NextAction[]
--   }
--
-- 漸進策略：
--   - Phase 1（本次）：新增 verdict_lite 欄位，舊 verdict_card 暫保留（雙寫期，
--     但 backend 已停寫，所以舊 row 上的 verdict_card 不會被更新）
--   - Phase 2（PR 上線穩定 1 週後）：另開 migration 024 DROP verdict_card 欄位

ALTER TABLE triz_consolidation_results
  ADD COLUMN IF NOT EXISTS verdict_lite JSONB;

COMMENT ON COLUMN triz_consolidation_results.verdict_lite IS
  'EngineeringVerdictLite — 對照 brief 任務的精簡審判 (mission_check / constraint_checks / kpi_checks / sr_checks / socratic_checks / cld_checks / next_actions)。取代舊的 verdict_card Q1–Q8 結構（plans/triz-verdict-card-simplification.md）。';
