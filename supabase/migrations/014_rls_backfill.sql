-- ============================================================================
-- Migration 014: RLS backfill for 4 tables missing Row Level Security
-- ============================================================================
-- Context: Audit found 4 tables created without ENABLE ROW LEVEL SECURITY.
--   - experiments (000), project_spatial_overlay (006),
--     project_component_overrides (007) → Pattern 1: project-child
--   - learned_components (007) → Pattern 3: backend-curated
--     (SELECT for authenticated; INSERT/UPDATE/DELETE blocked for frontend,
--      write only via service-role which bypasses RLS)
--
-- See E4--erd.md §5.5 for pattern definitions.
-- ============================================================================

-- ============================================================================
-- Pattern 1: project-child (same as migration 000 batch)
-- ============================================================================

DO $$
DECLARE
  tbl TEXT;
  tables TEXT[] := ARRAY[
    'experiments',
    'project_spatial_overlay',
    'project_component_overrides'
  ];
BEGIN
  FOREACH tbl IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);

    -- SELECT: all authenticated users can read
    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_select" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_select" ON %I FOR SELECT TO authenticated USING (true)',
      tbl, tbl);

    -- INSERT: only project owner
    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_insert" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_insert" ON %I FOR INSERT TO authenticated
       WITH CHECK (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);

    -- UPDATE: only project owner
    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_update" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_update" ON %I FOR UPDATE TO authenticated
       USING (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))
       WITH CHECK (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);

    -- DELETE: only project owner
    EXECUTE format('DROP POLICY IF EXISTS "rls_%s_delete" ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE POLICY "rls_%s_delete" ON %I FOR DELETE TO authenticated
       USING (project_id IN (SELECT id FROM projects WHERE created_by = auth.uid()::text))',
      tbl, tbl);
  END LOOP;
END $$;

-- ============================================================================
-- Pattern 3: backend-curated — learned_components
-- ============================================================================
-- Rationale: learned_components is a global shared knowledge base (not project-scoped).
-- origin_project FK uses ON DELETE SET NULL — the component outlives any single project.
-- Frontend can read all entries; writes are restricted to service-role (backend API)
-- to maintain data quality (layered resolver: L1 overrides → L2 learned → L3 web → L4 seed → L5 llm).

ALTER TABLE learned_components ENABLE ROW LEVEL SECURITY;

-- SELECT: all authenticated users can read the global component library
DROP POLICY IF EXISTS "rls_learned_components_select" ON learned_components;
CREATE POLICY "rls_learned_components_select"
  ON learned_components FOR SELECT TO authenticated
  USING (true);

-- INSERT: blocked for frontend — service-role (backend) bypasses RLS
DROP POLICY IF EXISTS "rls_learned_components_insert" ON learned_components;
CREATE POLICY "rls_learned_components_insert"
  ON learned_components FOR INSERT TO authenticated
  WITH CHECK (false);

-- UPDATE: blocked for frontend
DROP POLICY IF EXISTS "rls_learned_components_update" ON learned_components;
CREATE POLICY "rls_learned_components_update"
  ON learned_components FOR UPDATE TO authenticated
  USING (false);

-- DELETE: blocked for frontend
DROP POLICY IF EXISTS "rls_learned_components_delete" ON learned_components;
CREATE POLICY "rls_learned_components_delete"
  ON learned_components FOR DELETE TO authenticated
  USING (false);
