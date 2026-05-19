-- ============================================================================
-- Migration 014: Add missing JSONB columns to directed_triz_solutions
--
-- The backend model ContradictionDirectionResult includes sub_requirements,
-- coverage_audits, and combined_direction (Steps H/I of the directed solver),
-- but migration 011 omitted these columns. This caused _persist_directed_solution
-- to silently fail on every upsert, meaning results were never saved to DB.
--
-- Rollback:
--   ALTER TABLE directed_triz_solutions
--     DROP COLUMN IF EXISTS sub_requirements,
--     DROP COLUMN IF EXISTS coverage_audits,
--     DROP COLUMN IF EXISTS combined_direction;
-- ============================================================================

BEGIN;

ALTER TABLE directed_triz_solutions
  ADD COLUMN IF NOT EXISTS sub_requirements   JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS coverage_audits    JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS combined_direction JSONB;

COMMENT ON COLUMN directed_triz_solutions.sub_requirements IS
  'Step H-1: Physical sub-requirements decomposed from the contradiction. SubRequirement[]';
COMMENT ON COLUMN directed_triz_solutions.coverage_audits IS
  'Step H-2: Coverage audit per direction against sub-requirements. DirectionCoverageAudit[]';
COMMENT ON COLUMN directed_triz_solutions.combined_direction IS
  'Step I: Combined direction composed when best coverage < threshold. CombinedDirection | null';

COMMIT;
