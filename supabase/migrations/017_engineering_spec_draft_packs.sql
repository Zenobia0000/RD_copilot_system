-- 016_engineering_spec_draft_packs.sql
-- Engineering Spec Draft Packs — persist step2/step3/legacy pipeline results
-- so the Create page can rehydrate on refresh.

-- 1. Table
CREATE TABLE IF NOT EXISTS engineering_spec_draft_packs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      uuid NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
  drafts_json     jsonb NOT NULL DEFAULT '{}'::jsonb,
  pipeline_version text NOT NULL DEFAULT 'v2',
  step_count      integer NOT NULL DEFAULT 0,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- 2. Index
CREATE INDEX IF NOT EXISTS idx_esdp_project
  ON engineering_spec_draft_packs(project_id);

-- 3. Auto-update trigger
CREATE TRIGGER set_esdp_updated_at
  BEFORE UPDATE ON engineering_spec_draft_packs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. Comments
COMMENT ON TABLE  engineering_spec_draft_packs IS 'Singleton per project: stores the full EngineeringSpecDraftResponse JSON for rehydration.';
COMMENT ON COLUMN engineering_spec_draft_packs.drafts_json IS 'Full EngineeringSpecDraftResponse as JSON (drafts, subsystem_tree, package_map).';
COMMENT ON COLUMN engineering_spec_draft_packs.pipeline_version IS 'v1=legacy one-shot, v2=4-step pipeline.';
COMMENT ON COLUMN engineering_spec_draft_packs.step_count IS 'Number of drafts in this pack.';

-- 5. RLS
ALTER TABLE engineering_spec_draft_packs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS esdp_select ON engineering_spec_draft_packs;
CREATE POLICY esdp_select ON engineering_spec_draft_packs
  FOR SELECT USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS esdp_insert ON engineering_spec_draft_packs;
CREATE POLICY esdp_insert ON engineering_spec_draft_packs
  FOR INSERT WITH CHECK (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS esdp_update ON engineering_spec_draft_packs;
CREATE POLICY esdp_update ON engineering_spec_draft_packs
  FOR UPDATE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );

DROP POLICY IF EXISTS esdp_delete ON engineering_spec_draft_packs;
CREATE POLICY esdp_delete ON engineering_spec_draft_packs
  FOR DELETE USING (
    project_id IN (SELECT id FROM projects WHERE auth.uid() IS NOT NULL)
  );
