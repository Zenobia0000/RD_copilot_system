-- ============================================================================
-- Migration 015: Concept Architecture Packs
--
-- Stores LLM-generated concept-level subsystem architecture packs.
-- Agent refs:
--   backend/app/agents/concept_architecture.py
--     _persist_concept_architecture_pack()  → upsert on project_id
--     fetch_latest_pack()                   → select by project_id
--
-- Changes:
--   1. Create concept_architecture_packs table
--   2. UNIQUE on project_id (required by PostgREST upsert on_conflict)
--   3. updated_at trigger (project convention)
--   4. RLS policies (project-scoped, same pattern as all other tables)
--
-- Rollback:
--   DROP TABLE IF EXISTS concept_architecture_packs CASCADE;
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1.  concept_architecture_packs table
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS concept_architecture_packs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    uuid NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
  pack_json     jsonb NOT NULL DEFAULT '{}'::jsonb,
  template_id   text NOT NULL DEFAULT 'generic',
  applied       boolean NOT NULL DEFAULT false,
  source_badges jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cap_project
  ON concept_architecture_packs(project_id);

-- ----------------------------------------------------------------------------
-- 2.  updated_at trigger
-- ----------------------------------------------------------------------------

CREATE TRIGGER trg_concept_architecture_packs_updated_at
  BEFORE UPDATE ON concept_architecture_packs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 3.  Comments
-- ----------------------------------------------------------------------------

COMMENT ON TABLE concept_architecture_packs
  IS 'Concept Architecture Pack — LLM-generated concept-level subsystem architecture';
COMMENT ON COLUMN concept_architecture_packs.pack_json
  IS 'Full ConceptArchitecturePack JSON: subsystems, interfaces, rationale';
COMMENT ON COLUMN concept_architecture_packs.template_id
  IS 'Template used: generic | ebike_mid_drive';
COMMENT ON COLUMN concept_architecture_packs.applied
  IS 'Whether this pack has been applied to subsystem definition';
COMMENT ON COLUMN concept_architecture_packs.source_badges
  IS 'dict[str,bool] badges indicating which upstream artifacts were available';

-- ----------------------------------------------------------------------------
-- 4.  RLS policies — follow existing project-scoped pattern
-- ----------------------------------------------------------------------------

ALTER TABLE concept_architecture_packs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cap_select ON concept_architecture_packs;
CREATE POLICY cap_select ON concept_architecture_packs
  FOR SELECT USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS cap_insert ON concept_architecture_packs;
CREATE POLICY cap_insert ON concept_architecture_packs
  FOR INSERT WITH CHECK (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS cap_update ON concept_architecture_packs;
CREATE POLICY cap_update ON concept_architecture_packs
  FOR UPDATE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS cap_delete ON concept_architecture_packs;
CREATE POLICY cap_delete ON concept_architecture_packs
  FOR DELETE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

COMMIT;
