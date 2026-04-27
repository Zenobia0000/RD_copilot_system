-- Migration: Add current_value and current_status to kpis table
-- Purpose: Track actual measurement values and derived KPI status
-- Run via Supabase SQL Editor

ALTER TABLE kpis
  ADD COLUMN IF NOT EXISTS current_value text DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS current_status text DEFAULT 'unknown';

COMMENT ON COLUMN kpis.current_value IS 'Latest measured value from evidence entries';
COMMENT ON COLUMN kpis.current_status IS 'Derived status: on_track / at_risk / off_track / unknown';
