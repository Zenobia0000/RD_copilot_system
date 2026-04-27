-- Migration: Create evidence_entries table
-- Purpose: Structured measurement logging from RD experiments
-- Run via Supabase SQL Editor

CREATE TABLE IF NOT EXISTS evidence_entries (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id       uuid NOT NULL,

  -- What was measured
  title         text NOT NULL,
  measured_value text NOT NULL,
  unit          text DEFAULT '',
  evidence_level text NOT NULL DEFAULT 'E1',
  method        text DEFAULT '',
  notes         text DEFAULT '',
  measured_at   timestamptz DEFAULT now(),

  -- Links
  kpi_id        uuid REFERENCES kpis(id) ON DELETE SET NULL,
  experiment_id uuid REFERENCES experiments(id) ON DELETE SET NULL,
  linked_assumption_codes text[] DEFAULT '{}',
  linked_must_ids text[] DEFAULT '{}',
  attachment_id uuid DEFAULT NULL,

  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_entries_project ON evidence_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_entries_kpi ON evidence_entries(kpi_id);

-- Updated at trigger
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

-- RLS
ALTER TABLE evidence_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "evidence_entries_select" ON evidence_entries
  FOR SELECT USING (true);

CREATE POLICY "evidence_entries_insert" ON evidence_entries
  FOR INSERT WITH CHECK (true);

CREATE POLICY "evidence_entries_update" ON evidence_entries
  FOR UPDATE USING (true);

CREATE POLICY "evidence_entries_delete" ON evidence_entries
  FOR DELETE USING (true);
