-- ============================================================================
-- Migration 011: Cleanup legacy top-level PC/SF contradictions (ADR-007)
--
-- ADR ref:
--   docs/01-define/adrs/ADR-007-tc-only-explore-pc-sf-derivation-in-create.md
--
-- Context:
--   Explore stage is now TC-only. Historical rows where Explore formalized a
--   contradiction as type='PC' or type='SF' at the top level (i.e. without a
--   parent TC) no longer have a valid UI surface in Explore and cannot feed
--   the layered drill-down (L1/L2/L3) because they lack improving/worsening
--   params. Child PCs produced by Create-stage decompose_tc_to_pcs keep their
--   parent_contradiction_id set and are NOT affected by this migration.
--
-- Changes:
--   1. Delete top-level (parent IS NULL) contradictions with type IN ('PC','SF').
--      Any dependent rows via ON DELETE CASCADE (evidence refs, layered
--      solutions keyed on contradiction_id) will drop with them. Constraints
--      without CASCADE would have blocked the delete, surfacing the issue.
--   2. Report deleted count via NOTICE for operator visibility.
--
-- Rollback:
--   No rollback — deleted rows are not recoverable without a DB restore.
--   If production data is affected, take a backup via
--     pg_dump --table=contradictions ...
--   BEFORE applying.
-- ============================================================================

BEGIN;

DO $$
DECLARE
  deleted_count INTEGER;
BEGIN
  WITH purged AS (
    DELETE FROM contradictions
    WHERE parent_contradiction_id IS NULL
      AND type IN ('PC', 'SF')
    RETURNING id
  )
  SELECT COUNT(*) INTO deleted_count FROM purged;

  RAISE NOTICE 'ADR-007 cleanup: removed % legacy top-level PC/SF contradictions', deleted_count;
END $$;

COMMIT;
