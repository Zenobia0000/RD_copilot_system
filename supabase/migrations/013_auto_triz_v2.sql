-- ============================================================================
-- Migration 013: Auto-TRIZ v2 Schema (ADR-008, WBS 8.1.1–8.1.4)
--
-- ADR ref:
--   docs/01-define/adrs/ADR-008-auto-triz-v2-integration.md
--
-- Changes:
--   1. New `function_models` table  (WBS 8.1.1) — FA+SF functional model per
--      project, storing component interactions, Su-Field diagnosis, and
--      subsystem boundary as JSONB.
--   2. New `evidence_claims` table  (WBS 8.1.2) — typed claims with
--      verification status, confidence score, and artifact linking for the
--      evidence-backed reasoning loop.
--   3. New `sim_matrices` table     (WBS 8.1.3) — Solution Interaction Matrix
--      storing cross-contradiction compatibility analysis.
--   4. Extend `contradictions`      (WBS 8.1.4) — add OZ-zone, OT-time, and
--      PX-variable columns for TRIZ v2 separation-principle metadata.
--
-- Rollback:
--   DROP TABLE IF EXISTS sim_matrices CASCADE;
--   DROP TABLE IF EXISTS evidence_claims CASCADE;
--   DROP TABLE IF EXISTS function_models CASCADE;
--   ALTER TABLE contradictions
--     DROP COLUMN IF EXISTS oz_zone,
--     DROP COLUMN IF EXISTS ot_time,
--     DROP COLUMN IF EXISTS px_variable;
-- ============================================================================

BEGIN;

-- ============================================================================
-- 8.1.1  function_models
-- ============================================================================

CREATE TABLE IF NOT EXISTS function_models (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  component_interactions JSONB NOT NULL DEFAULT '[]',
  sf_diagnosis JSONB NOT NULL DEFAULT '{}',
  subsystem_boundary JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_function_models_updated_at
  BEFORE UPDATE ON function_models
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_function_models_project_id
  ON function_models(project_id);

-- ============================================================================
-- 8.1.2  evidence_claims
-- ============================================================================

CREATE TABLE IF NOT EXISTS evidence_claims (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  claim_text TEXT NOT NULL,
  claim_type TEXT NOT NULL CHECK (claim_type IN ('assumption', 'hypothesis', 'result', 'constraint')),
  status TEXT NOT NULL DEFAULT 'unverified' CHECK (status IN ('unverified', 'verified', 'refuted', 'partial')),
  verification_sources JSONB NOT NULL DEFAULT '[]',
  linked_artifact_id UUID,
  linked_artifact_type TEXT,
  confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_evidence_claims_updated_at
  BEFORE UPDATE ON evidence_claims
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_evidence_claims_project_id
  ON evidence_claims(project_id);

CREATE INDEX IF NOT EXISTS idx_evidence_claims_status
  ON evidence_claims(status);

-- ============================================================================
-- 8.1.3  sim_matrices
-- ============================================================================

CREATE TABLE IF NOT EXISTS sim_matrices (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  contradiction_ids UUID[] NOT NULL DEFAULT '{}',
  matrix JSONB NOT NULL DEFAULT '{}',
  optimal_combination JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_sim_matrices_updated_at
  BEFORE UPDATE ON sim_matrices
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_sim_matrices_project_id
  ON sim_matrices(project_id);

-- ============================================================================
-- 8.1.4  contradictions — add separation-principle columns
-- ============================================================================

ALTER TABLE contradictions
  ADD COLUMN IF NOT EXISTS oz_zone TEXT,
  ADD COLUMN IF NOT EXISTS ot_time TEXT,
  ADD COLUMN IF NOT EXISTS px_variable TEXT;

COMMENT ON COLUMN contradictions.oz_zone IS
  'TRIZ v2: Operating Zone — spatial separation dimension';
COMMENT ON COLUMN contradictions.ot_time IS
  'TRIZ v2: Operating Time — temporal separation dimension';
COMMENT ON COLUMN contradictions.px_variable IS
  'TRIZ v2: Parameter X — the controllable variable for separation';

-- ============================================================================
-- RLS policies — project-scoped pattern (matches migration 010 style)
-- ============================================================================

DO $$
DECLARE
  tbl TEXT;
  tables TEXT[] := ARRAY['function_models', 'evidence_claims', 'sim_matrices'];
BEGIN
  FOREACH tbl IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);

    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_select" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_select" ON %I FOR SELECT TO authenticated USING (true)',
      tbl, tbl);

    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_insert" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_insert" ON %I FOR INSERT TO authenticated
       WITH CHECK (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);

    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_update" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_update" ON %I FOR UPDATE TO authenticated
       USING (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))
       WITH CHECK (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);

    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_delete" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_delete" ON %I FOR DELETE TO authenticated
       USING (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);
  END LOOP;
END $$;

COMMIT;
