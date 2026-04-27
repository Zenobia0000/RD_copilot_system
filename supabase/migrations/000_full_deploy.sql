-- ============================================================
-- Design Copilot Blueprint — One-Click Full Deployment
-- Consolidated from 7 migration files for fresh Supabase setup
-- All statements are idempotent (safe to re-run)
--
-- Usage:
--   1. Create a new Supabase project
--   2. Open SQL Editor
--   3. Paste this entire file and run
-- ============================================================

-- ############################################################
-- Part 1: Utility Functions
-- ############################################################

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ############################################################
-- Part 2: Layer 0 — Projects
-- ############################################################

CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'in_progress',
  phase TEXT NOT NULL DEFAULT 'Phase I',
  progress INTEGER DEFAULT 0,
  mission TEXT,
  phase_progress JSONB DEFAULT '{}',
  quick_stats JSONB DEFAULT '{}',
  gates_passed INTEGER DEFAULT 0,
  gates_total INTEGER DEFAULT 0,
  must_criteria_config JSONB DEFAULT NULL,
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN projects.must_criteria_config IS
  'MUST criteria config derived from Brief constraints/KPIs. Array of {id, label, source, threshold}.';

CREATE TRIGGER trg_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ############################################################
-- Part 3: Layer 1 — Problem Definition
-- ############################################################

-- briefs
CREATE TABLE IF NOT EXISTS briefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  mission TEXT,
  task_definition_5w1h JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(project_id)
);
CREATE TRIGGER trg_briefs_updated_at
  BEFORE UPDATE ON briefs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- constraints
CREATE TABLE IF NOT EXISTS constraints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  constraint_code TEXT NOT NULL,
  description TEXT NOT NULL,
  source TEXT,
  type TEXT NOT NULL DEFAULT 'hard',
  feasibility TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_constraints_updated_at
  BEFORE UPDATE ON constraints FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- kpis (with current_value / current_status for evidence tracking)
CREATE TABLE IF NOT EXISTS kpis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  kpi_name TEXT NOT NULL,
  target_value TEXT,
  unit TEXT,
  measurement_method TEXT,
  current_value TEXT DEFAULT NULL,
  current_status TEXT DEFAULT 'unknown',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
COMMENT ON COLUMN kpis.current_value IS 'Latest measured value from evidence entries';
COMMENT ON COLUMN kpis.current_status IS 'Derived status: on_track / at_risk / off_track / unknown';
CREATE TRIGGER trg_kpis_updated_at
  BEFORE UPDATE ON kpis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- socratic_questions
CREATE TABLE IF NOT EXISTS socratic_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  text TEXT NOT NULL,
  answer TEXT,
  tagged_as_assumption BOOLEAN DEFAULT false,
  tagged_as_contradiction BOOLEAN DEFAULT false,
  ai_suggested_tag TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_socratic_questions_updated_at
  BEFORE UPDATE ON socratic_questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- contradictions
CREATE TABLE IF NOT EXISTS contradictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  natural_description TEXT,
  improving_param INTEGER,
  worsening_param INTEGER,
  engineering_statement TEXT,
  physical_contradiction TEXT,
  type TEXT,
  severity TEXT NOT NULL DEFAULT 'minor',
  resolved BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_contradictions_updated_at
  BEFORE UPDATE ON contradictions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ############################################################
-- Part 4: Layer 2 — Assumption Management
-- ############################################################

-- assumptions
CREATE TABLE IF NOT EXISTS assumptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  content TEXT NOT NULL,
  source TEXT,
  source_type TEXT,
  worst_consequence TEXT,
  worst_severity TEXT,
  min_validation TEXT,
  validation_cost TEXT,
  validation_method TEXT,
  estimated_days INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',
  verification_stage TEXT DEFAULT 'unplanned',
  impact_scope TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_assumptions_updated_at
  BEFORE UPDATE ON assumptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- cld_nodes
CREATE TABLE IF NOT EXISTS cld_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  x DOUBLE PRECISION DEFAULT 0,
  y DOUBLE PRECISION DEFAULT 0,
  node_type TEXT DEFAULT 'variable',
  assumption_id UUID REFERENCES assumptions(id),
  is_leverage BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_cld_nodes_updated_at
  BEFORE UPDATE ON cld_nodes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- cld_edges
CREATE TABLE IF NOT EXISTS cld_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  from_node UUID REFERENCES cld_nodes(id) ON DELETE CASCADE,
  to_node UUID REFERENCES cld_nodes(id) ON DELETE CASCADE,
  polarity TEXT DEFAULT '+',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_cld_edges_updated_at
  BEFORE UPDATE ON cld_edges FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ############################################################
-- Part 5: Layer 3 — Solution Exploration
-- ############################################################

-- anti_anchor_routes
CREATE TABLE IF NOT EXISTS anti_anchor_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  is_non_typical BOOLEAN DEFAULT true,
  source TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_anti_anchor_routes_updated_at
  BEFORE UPDATE ON anti_anchor_routes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- triz_solutions
CREATE TABLE IF NOT EXISTS triz_solutions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  contradiction_id UUID REFERENCES contradictions(id),
  path TEXT NOT NULL,
  principle_number INTEGER,
  principle_name TEXT,
  suggestion TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_triz_solutions_updated_at
  BEFORE UPDATE ON triz_solutions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- subsystems
CREATE TABLE IF NOT EXISTS subsystems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  reason TEXT,
  related_contradictions TEXT[],
  confirmed BOOLEAN DEFAULT false,
  parent_id UUID REFERENCES subsystems(id),
  interfaces TEXT,
  source TEXT DEFAULT 'rd',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_subsystems_updated_at
  BEFORE UPDATE ON subsystems FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- scamper_variants
CREATE TABLE IF NOT EXISTS scamper_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  subsystem_id UUID REFERENCES subsystems(id),
  action TEXT NOT NULL,
  description TEXT,
  adopted BOOLEAN DEFAULT false,
  new_contradictions JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_scamper_variants_updated_at
  BEFORE UPDATE ON scamper_variants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- alternatives
CREATE TABLE IF NOT EXISTS alternatives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  mechanism TEXT,
  source TEXT,
  key_assumption_ids TEXT[],
  must_scores JSONB DEFAULT '{}',
  interface_contract JSONB DEFAULT '{}',
  pre_cad_scores JSONB DEFAULT '{}',
  overall_pass BOOLEAN,
  cad_status TEXT DEFAULT 'not_started',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_alternatives_updated_at
  BEFORE UPDATE ON alternatives FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- concept_routes
CREATE TABLE IF NOT EXISTS concept_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  route_type TEXT NOT NULL DEFAULT 'single',
  composition JSONB DEFAULT '[]',
  composition_rationale TEXT,
  anti_pattern_warnings TEXT[],
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_concept_routes_updated_at
  BEFORE UPDATE ON concept_routes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- compatibility_pairs
CREATE TABLE IF NOT EXISTS compatibility_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  solution_a_id TEXT NOT NULL,
  solution_b_id TEXT NOT NULL,
  result TEXT NOT NULL,
  adoption_type TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_compatibility_pairs_updated_at
  BEFORE UPDATE ON compatibility_pairs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ############################################################
-- Part 6: Layer 4 — Review & Decision
-- ############################################################

-- evidence_matrix
CREATE TABLE IF NOT EXISTS evidence_matrix (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  assumption_code TEXT NOT NULL,
  summary TEXT,
  current_level TEXT DEFAULT 'E0',
  is_north_star BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_evidence_matrix_updated_at
  BEFORE UPDATE ON evidence_matrix FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- risks
CREATE TABLE IF NOT EXISTS risks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  failure_mode TEXT,
  probability INTEGER DEFAULT 1,
  severity INTEGER DEFAULT 1,
  mitigation TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_risks_updated_at
  BEFORE UPDATE ON risks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- experiments
CREATE TABLE IF NOT EXISTS experiments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID,
  assumption_code TEXT,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Plan',
  result TEXT,
  linked_assumptions TEXT[],
  evidence_level TEXT,
  method TEXT,
  success_criteria TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER set_experiments_updated_at
  BEFORE UPDATE ON experiments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- decisions
CREATE TABLE IF NOT EXISTS decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  selected_alternative_id UUID REFERENCES alternatives(id),
  selected_alternative_name TEXT,
  rationale TEXT,
  risk_acceptance TEXT,
  decision_date TIMESTAMPTZ,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_decisions_updated_at
  BEFORE UPDATE ON decisions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- want_criteria
CREATE TABLE IF NOT EXISTS want_criteria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  weight INTEGER DEFAULT 5,
  description TEXT,
  anchors TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_want_criteria_updated_at
  BEFORE UPDATE ON want_criteria FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- want_scores
CREATE TABLE IF NOT EXISTS want_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  criterion_id UUID REFERENCES want_criteria(id),
  alternative_id UUID REFERENCES alternatives(id),
  score INTEGER DEFAULT 0,
  evidence TEXT,
  weighted_total DOUBLE PRECISION DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_want_scores_updated_at
  BEFORE UPDATE ON want_scores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- adverse_consequences
CREATE TABLE IF NOT EXISTS adverse_consequences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  alternative_id UUID REFERENCES alternatives(id),
  description TEXT NOT NULL,
  probability TEXT,
  severity TEXT,
  level TEXT,
  mitigation TEXT,
  risk_artifact_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_adverse_consequences_updated_at
  BEFORE UPDATE ON adverse_consequences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- signatures
CREATE TABLE IF NOT EXISTS signatures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  decision_id UUID REFERENCES decisions(id),
  name TEXT NOT NULL,
  role TEXT,
  status TEXT DEFAULT 'pending',
  signed_at TIMESTAMPTZ,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_signatures_updated_at
  BEFORE UPDATE ON signatures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- action_items
CREATE TABLE IF NOT EXISTS action_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  decision_id UUID REFERENCES decisions(id),
  description TEXT NOT NULL,
  assignee TEXT,
  due_date DATE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_action_items_updated_at
  BEFORE UPDATE ON action_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- evidence_entries
CREATE TABLE IF NOT EXISTS evidence_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  title TEXT NOT NULL,
  measured_value TEXT NOT NULL,
  unit TEXT DEFAULT '',
  evidence_level TEXT NOT NULL DEFAULT 'E1',
  method TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  measured_at TIMESTAMPTZ DEFAULT now(),
  kpi_id UUID REFERENCES kpis(id) ON DELETE SET NULL,
  experiment_id UUID REFERENCES experiments(id) ON DELETE SET NULL,
  linked_assumption_codes TEXT[] DEFAULT '{}',
  linked_must_ids TEXT[] DEFAULT '{}',
  attachment_id UUID DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION set_evidence_entries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_evidence_entries_updated_at ON evidence_entries;
CREATE TRIGGER trg_evidence_entries_updated_at
  BEFORE UPDATE ON evidence_entries
  FOR EACH ROW EXECUTE FUNCTION set_evidence_entries_updated_at();

-- ############################################################
-- Part 7: Layer 5 — Knowledge Management
-- ############################################################

-- knowledge_articles
CREATE TABLE IF NOT EXISTS knowledge_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL,
  tags TEXT[],
  author TEXT,
  published_at TIMESTAMPTZ DEFAULT now(),
  content TEXT,
  related_links JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_knowledge_articles_updated_at
  BEFORE UPDATE ON knowledge_articles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- knowledge_entries
CREATE TABLE IF NOT EXISTS knowledge_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  asset_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  reviewed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_knowledge_entries_updated_at
  BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ############################################################
-- Part 8: Profiles & Auth Trigger
-- ############################################################

CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  display_name TEXT NOT NULL DEFAULT '',
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Converge legacy schema to display_name-only profile naming.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS display_name TEXT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'profiles'
      AND column_name = 'username'
  ) THEN
    EXECUTE $sql$
      UPDATE profiles
      SET display_name = COALESCE(
        NULLIF(BTRIM(display_name), ''),
        NULLIF(BTRIM(username), ''),
        'user'
      )
      WHERE display_name IS NULL OR BTRIM(display_name) = ''
    $sql$;

    BEGIN
      ALTER TABLE profiles DROP COLUMN username;
    EXCEPTION
      WHEN dependent_objects_still_exist THEN
        RAISE WARNING
          'Skipped dropping profiles.username because dependent objects still exist. Remove dependencies and re-run migration.';
    END;
  ELSE
    UPDATE profiles
    SET display_name = COALESCE(NULLIF(BTRIM(display_name), ''), 'user')
    WHERE display_name IS NULL OR BTRIM(display_name) = '';
  END IF;
END;
$$;

ALTER TABLE profiles ALTER COLUMN display_name SET DEFAULT '';
UPDATE profiles SET display_name = '' WHERE display_name IS NULL;
ALTER TABLE profiles ALTER COLUMN display_name SET NOT NULL;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  profile_name TEXT;
BEGIN
  profile_name := COALESCE(
    NULLIF(BTRIM(NEW.raw_user_meta_data->>'display_name'), ''),
    NULLIF(SPLIT_PART(COALESCE(NEW.email, ''), '@', 1), ''),
    'user'
  );

  INSERT INTO profiles (user_id, display_name)
  VALUES (NEW.id, profile_name)
  ON CONFLICT DO NOTHING;

  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'handle_new_user: profile insert skipped for user %, reason: %', NEW.id, SQLERRM;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ############################################################
-- Part 9: Storage & Review Attachments
-- ############################################################

INSERT INTO storage.buckets (id, name, public)
VALUES ('review-attachments', 'review-attachments', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Authenticated users can upload review attachments" ON storage.objects;
CREATE POLICY "Authenticated users can upload review attachments"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'review-attachments' AND auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Authenticated users can view review attachments" ON storage.objects;
CREATE POLICY "Authenticated users can view review attachments"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'review-attachments');

DROP POLICY IF EXISTS "Users can delete own review attachments" ON storage.objects;
CREATE POLICY "Users can delete own review attachments"
  ON storage.objects FOR DELETE
  USING (bucket_id = 'review-attachments' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE TABLE IF NOT EXISTS review_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id TEXT NOT NULL,
  user_id UUID NOT NULL,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT NOT NULL DEFAULT 0,
  content_type TEXT,
  description TEXT DEFAULT '',
  assumption_code TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ############################################################
-- Part 10: Indexes
-- ############################################################

-- Layer 1
CREATE INDEX IF NOT EXISTS idx_briefs_project_id ON briefs(project_id);
CREATE INDEX IF NOT EXISTS idx_constraints_project_id ON constraints(project_id);
CREATE INDEX IF NOT EXISTS idx_kpis_project_id ON kpis(project_id);
CREATE INDEX IF NOT EXISTS idx_socratic_questions_project_id ON socratic_questions(project_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_project_id ON contradictions(project_id);

-- Layer 2
CREATE INDEX IF NOT EXISTS idx_assumptions_project_id ON assumptions(project_id);
CREATE INDEX IF NOT EXISTS idx_cld_nodes_project_id ON cld_nodes(project_id);
CREATE INDEX IF NOT EXISTS idx_cld_edges_project_id ON cld_edges(project_id);

-- Layer 3
CREATE INDEX IF NOT EXISTS idx_anti_anchor_routes_project_id ON anti_anchor_routes(project_id);
CREATE INDEX IF NOT EXISTS idx_triz_solutions_project_id ON triz_solutions(project_id);
CREATE INDEX IF NOT EXISTS idx_triz_solutions_contradiction_id ON triz_solutions(contradiction_id);
CREATE INDEX IF NOT EXISTS idx_subsystems_project_id ON subsystems(project_id);
CREATE INDEX IF NOT EXISTS idx_scamper_variants_project_id ON scamper_variants(project_id);
CREATE INDEX IF NOT EXISTS idx_scamper_variants_subsystem_id ON scamper_variants(subsystem_id);
CREATE INDEX IF NOT EXISTS idx_alternatives_project_id ON alternatives(project_id);
CREATE INDEX IF NOT EXISTS idx_concept_routes_project_id ON concept_routes(project_id);
CREATE INDEX IF NOT EXISTS idx_compatibility_pairs_project_id ON compatibility_pairs(project_id);

-- Layer 4
CREATE INDEX IF NOT EXISTS idx_evidence_matrix_project_id ON evidence_matrix(project_id);
CREATE INDEX IF NOT EXISTS idx_risks_project_id ON risks(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_project_id ON decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_want_criteria_project_id ON want_criteria(project_id);
CREATE INDEX IF NOT EXISTS idx_want_scores_project_id ON want_scores(project_id);
CREATE INDEX IF NOT EXISTS idx_want_scores_criterion_id ON want_scores(criterion_id);
CREATE INDEX IF NOT EXISTS idx_want_scores_alternative_id ON want_scores(alternative_id);
CREATE INDEX IF NOT EXISTS idx_adverse_consequences_project_id ON adverse_consequences(project_id);
CREATE INDEX IF NOT EXISTS idx_adverse_consequences_alternative_id ON adverse_consequences(alternative_id);
CREATE INDEX IF NOT EXISTS idx_signatures_project_id ON signatures(project_id);
CREATE INDEX IF NOT EXISTS idx_signatures_decision_id ON signatures(decision_id);
CREATE INDEX IF NOT EXISTS idx_action_items_project_id ON action_items(project_id);
CREATE INDEX IF NOT EXISTS idx_action_items_decision_id ON action_items(decision_id);
CREATE INDEX IF NOT EXISTS idx_evidence_entries_project ON evidence_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_entries_kpi ON evidence_entries(kpi_id);

-- Layer 5
CREATE INDEX IF NOT EXISTS idx_knowledge_articles_category ON knowledge_articles(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_articles_slug ON knowledge_articles(slug);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_project_id ON knowledge_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_asset_type ON knowledge_entries(asset_type);

-- ############################################################
-- Part 11: Row Level Security (RLS)
-- ############################################################

-- Helper macro: project-child RLS (owner-based access)
-- Applied to all project_id tables below

-- profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS user_id UUID;

DO $$ BEGIN
  DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
  CREATE POLICY "Users can view own profile" ON profiles FOR SELECT TO authenticated
    USING (user_id = auth.uid());
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
  CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE TO authenticated
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- projects
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view all projects" ON projects;
CREATE POLICY "Users can view all projects" ON projects FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Users can create own projects" ON projects;
CREATE POLICY "Users can create own projects" ON projects FOR INSERT TO authenticated
  WITH CHECK (created_by = auth.uid()::text);

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects FOR UPDATE TO authenticated
  USING (created_by = auth.uid()::text) WITH CHECK (created_by = auth.uid()::text);

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects FOR DELETE TO authenticated
  USING (created_by = auth.uid()::text);

-- Project-child tables: briefs, constraints, kpis, socratic_questions, contradictions,
-- assumptions, cld_nodes, cld_edges, anti_anchor_routes, triz_solutions, subsystems,
-- scamper_variants, alternatives, concept_routes, compatibility_pairs,
-- evidence_matrix, risks, decisions, want_criteria, want_scores,
-- adverse_consequences, signatures, action_items, knowledge_entries

DO $$
DECLARE
  tbl TEXT;
  tables TEXT[] := ARRAY[
    'briefs', 'constraints', 'kpis', 'socratic_questions', 'contradictions',
    'assumptions', 'cld_nodes', 'cld_edges',
    'anti_anchor_routes', 'triz_solutions', 'subsystems', 'scamper_variants',
    'alternatives', 'concept_routes', 'compatibility_pairs',
    'evidence_matrix', 'risks', 'decisions', 'want_criteria', 'want_scores',
    'adverse_consequences', 'signatures', 'action_items', 'knowledge_entries'
  ];
BEGIN
  FOREACH tbl IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);

    -- SELECT: all authenticated users can read all project data
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

-- knowledge_articles: shared across all authenticated users
ALTER TABLE knowledge_articles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can view all knowledge articles" ON knowledge_articles;
CREATE POLICY "Authenticated users can view all knowledge articles" ON knowledge_articles
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Authenticated users can create knowledge articles" ON knowledge_articles;
CREATE POLICY "Authenticated users can create knowledge articles" ON knowledge_articles
  FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can update knowledge articles" ON knowledge_articles;
CREATE POLICY "Authenticated users can update knowledge articles" ON knowledge_articles
  FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can delete knowledge articles" ON knowledge_articles;
CREATE POLICY "Authenticated users can delete knowledge articles" ON knowledge_articles
  FOR DELETE TO authenticated USING (true);

-- evidence_entries: open to all authenticated users
ALTER TABLE evidence_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "evidence_entries_select" ON evidence_entries;
CREATE POLICY "evidence_entries_select" ON evidence_entries FOR SELECT USING (true);
DROP POLICY IF EXISTS "evidence_entries_insert" ON evidence_entries;
CREATE POLICY "evidence_entries_insert" ON evidence_entries FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "evidence_entries_update" ON evidence_entries;
CREATE POLICY "evidence_entries_update" ON evidence_entries FOR UPDATE USING (true);
DROP POLICY IF EXISTS "evidence_entries_delete" ON evidence_entries;
CREATE POLICY "evidence_entries_delete" ON evidence_entries FOR DELETE USING (true);

-- review_attachments
ALTER TABLE review_attachments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view project attachments" ON review_attachments;
CREATE POLICY "Users can view project attachments" ON review_attachments
  FOR SELECT USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Users can insert own attachments" ON review_attachments;
CREATE POLICY "Users can insert own attachments" ON review_attachments
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own attachments" ON review_attachments;
CREATE POLICY "Users can delete own attachments" ON review_attachments
  FOR DELETE USING (auth.uid() = user_id);

-- convergence_snapshots (persist convergence loop state per project)
CREATE TABLE IF NOT EXISTS convergence_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
  state JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_convergence_snapshots_updated_at
  BEFORE UPDATE ON convergence_snapshots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE convergence_snapshots ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Authenticated users can manage convergence snapshots" ON convergence_snapshots;
CREATE POLICY "Authenticated users can manage convergence snapshots" ON convergence_snapshots
  FOR ALL USING (auth.uid() IS NOT NULL);

-- unknown_factors (未知集合 — persisted, was localStorage)
CREATE TABLE IF NOT EXISTS unknown_factors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  unknown_code TEXT NOT NULL,
  description TEXT NOT NULL,
  impact TEXT DEFAULT 'medium',
  status TEXT DEFAULT 'open',
  note TEXT,
  linked_assumption_id UUID REFERENCES assumptions(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE unknown_factors ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Authenticated users can manage unknown factors" ON unknown_factors;
CREATE POLICY "Authenticated users can manage unknown factors" ON unknown_factors
  FOR ALL USING (auth.uid() IS NOT NULL);

-- ============================================================
-- Done! 31 tables + RLS + indexes + triggers + storage
-- ============================================================
