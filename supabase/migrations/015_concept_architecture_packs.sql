BEGIN;

CREATE TABLE IF NOT EXISTS concept_architecture_packs (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  pack_json   jsonb NOT NULL DEFAULT '{}'::jsonb,
  template_id text NOT NULL DEFAULT 'generic',
  applied     boolean NOT NULL DEFAULT false,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cap_project
  ON concept_architecture_packs(project_id);

COMMENT ON TABLE concept_architecture_packs
  IS 'Concept Architecture Pack — LLM-generated concept-level subsystem architecture';
COMMENT ON COLUMN concept_architecture_packs.pack_json
  IS 'Full ConceptArchitecturePack JSON (subsystems, interfaces, rationale)';
COMMENT ON COLUMN concept_architecture_packs.template_id
  IS 'Template used: generic | ebike_mid_drive';
COMMENT ON COLUMN concept_architecture_packs.applied
  IS 'Whether this pack has been applied to subsystem definition';

COMMIT;
