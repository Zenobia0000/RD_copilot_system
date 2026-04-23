-- ============================================================================
-- Migration 012: TRIZ Consolidation Results (v8)
--
-- Adds `triz_consolidation_results` table storing the cross-contradiction
-- consolidation outcome (ConsolidationResult) per project. Each project has
-- at most ONE active consolidation result (latest run wins).
--
-- Rollback:
--   DROP TABLE IF EXISTS triz_consolidation_results CASCADE;
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS triz_consolidation_results (
  id TEXT PRIMARY KEY,                              -- e.g. "TCR-<project_id_prefix>"
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'compatible'
    CHECK (status IN ('compatible', 'resolved_with_swap', 'conflict')),

  adopted_directions JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Record<string, DirectionGroup>
  conflict_report JSONB,                                   -- ConflictReport | null
  integration_advice TEXT NOT NULL DEFAULT '',

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT uq_triz_consolidation_project UNIQUE (project_id)
);

CREATE TRIGGER trg_triz_consolidation_results_updated_at
  BEFORE UPDATE ON triz_consolidation_results
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_triz_consolidation_results_project_id
  ON triz_consolidation_results(project_id);

COMMENT ON TABLE triz_consolidation_results IS
  'v8: Cross-contradiction consolidation output. One row per project. '
  'Stores adopted directions, conflict report, and integration advice. '
  'Consumed by the Create page UI for subsystem suggestion handoff.';

-- RLS policies
ALTER TABLE triz_consolidation_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS triz_consolidation_results_select ON triz_consolidation_results;
CREATE POLICY triz_consolidation_results_select ON triz_consolidation_results
  FOR SELECT USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS triz_consolidation_results_insert ON triz_consolidation_results;
CREATE POLICY triz_consolidation_results_insert ON triz_consolidation_results
  FOR INSERT WITH CHECK (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS triz_consolidation_results_update ON triz_consolidation_results;
CREATE POLICY triz_consolidation_results_update ON triz_consolidation_results
  FOR UPDATE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS triz_consolidation_results_delete ON triz_consolidation_results;
CREATE POLICY triz_consolidation_results_delete ON triz_consolidation_results
  FOR DELETE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

COMMIT;
