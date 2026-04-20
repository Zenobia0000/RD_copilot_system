-- ============================================================================
-- Migration 011: Directed TRIZ Solutions (v8)
--
-- Adds `directed_triz_solutions` table storing the direction-centric
-- ContradictionDirectionResult per contradiction. Complements (does NOT
-- replace) the legacy `layered_triz_solutions` table from migration 010.
--
-- Rollback:
--   DROP TABLE IF EXISTS directed_triz_solutions CASCADE;
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS directed_triz_solutions (
  id TEXT PRIMARY KEY,                              -- e.g. "DTS-EBIKE-012"
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  contradiction_id TEXT NOT NULL,
  natural_description TEXT,
  severity TEXT NOT NULL DEFAULT 'unknown'
    CHECK (severity IN ('fatal', 'major', 'minor', 'unknown')),

  all_solutions JSONB NOT NULL DEFAULT '[]'::jsonb,       -- DirectionSolution[]
  all_directions JSONB NOT NULL DEFAULT '[]'::jsonb,      -- DirectionGroup[]
  scored_directions JSONB NOT NULL DEFAULT '[]'::jsonb,   -- DirectionScore[]
  top1 JSONB,                                              -- DirectionGroup | null
  top2 JSONB,                                              -- DirectionGroup | null
  top1_score JSONB,                                        -- DirectionScore | null
  top2_score JSONB,                                        -- DirectionScore | null

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_directed_triz_solutions_updated_at
  BEFORE UPDATE ON directed_triz_solutions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_directed_triz_solutions_project_id
  ON directed_triz_solutions(project_id);
CREATE INDEX IF NOT EXISTS idx_directed_triz_solutions_contradiction_id
  ON directed_triz_solutions(contradiction_id);

COMMENT ON TABLE directed_triz_solutions IS
  'v8: Direction-centric TRIZ solver output. One row per contradiction. '
  'Stores merged TC+PC+SF solutions, clustered directions, scores, and '
  'Top1/Top2 picks. Consumed by the cross-contradiction consolidation '
  'endpoint and the Create page UI.';

-- RLS policies
ALTER TABLE directed_triz_solutions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS directed_triz_solutions_select ON directed_triz_solutions;
CREATE POLICY directed_triz_solutions_select ON directed_triz_solutions
  FOR SELECT USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS directed_triz_solutions_insert ON directed_triz_solutions;
CREATE POLICY directed_triz_solutions_insert ON directed_triz_solutions
  FOR INSERT WITH CHECK (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS directed_triz_solutions_update ON directed_triz_solutions;
CREATE POLICY directed_triz_solutions_update ON directed_triz_solutions
  FOR UPDATE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS directed_triz_solutions_delete ON directed_triz_solutions;
CREATE POLICY directed_triz_solutions_delete ON directed_triz_solutions
  FOR DELETE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

COMMIT;
