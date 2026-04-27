-- Migration: Add must_criteria_config to projects table
-- Purpose: Store project-specific MUST criteria derived from Brief constraints/KPIs
-- Format: JSON array of { id, label, source, threshold }
-- Run via Supabase SQL Editor: https://supabase.com/dashboard/project/ybhlybmasoxshzkcaohj/sql

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS must_criteria_config jsonb DEFAULT NULL;

COMMENT ON COLUMN projects.must_criteria_config IS
  'MUST criteria config derived from Brief constraints/KPIs. Array of {id, label, source, threshold}.';
