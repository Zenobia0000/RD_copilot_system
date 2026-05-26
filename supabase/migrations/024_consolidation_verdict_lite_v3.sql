-- 024_consolidation_verdict_lite_v3.sql
-- =============================================================================
-- v0.5 (v3) 結構性精簡：sr_checks / socratic_checks / cld_checks 移除，
-- 新增 explore_health (contradiction_coverage + cld_warning) 健檢徽章。
--
-- 重要：verdict_lite 是 JSONB schemaless，**不需要任何 schema migration**。
--   - 舊 row 含 sr_checks / socratic_checks / cld_checks 仍能被 Pydantic v2
--     讀取（預設 ignore unknown fields），不會報錯
--   - 新 row 寫入 explore_health 物件，舊欄位寫 null 或省略
--   - DB 端不需要 ALTER / DROP；本 migration 只是把 COMMENT 同步更新，
--     供未來 schema 探查使用
--
-- 完整規格見 plans/triz-verdict-card-simplification.md §17.3。
-- =============================================================================

COMMENT ON COLUMN triz_consolidation_results.verdict_lite IS
  'EngineeringVerdictLite v0.5 (v3) — Brief 達成檢核 (mission_check / constraint_checks / kpi_checks) + Explore 階段健檢 (explore_health.contradiction_coverage / explore_health.cld_warning) + next_actions (UI 僅渲染 blocking=true)。v0.4 的 sr_checks / socratic_checks / cld_checks 已移除（內部產物、歷史紀錄不外露給 RD）。JSONB schemaless 無需 schema migration，舊資料 Pydantic v2 會 ignore unknown fields。';
