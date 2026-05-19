-- 3-Stage TC Pipeline: add enrichment fields to contradictions
ALTER TABLE contradictions
  ADD COLUMN IF NOT EXISTS linked_kpis text[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS why_selected text,
  ADD COLUMN IF NOT EXISTS priority smallint;

COMMENT ON COLUMN contradictions.linked_kpis IS '3-Stage Pipeline: KPIs linked to this TC';
COMMENT ON COLUMN contradictions.why_selected IS '3-Stage Pipeline: LLM explanation of why this TC was selected';
COMMENT ON COLUMN contradictions.priority IS '3-Stage Pipeline: priority rank (1 = highest)';
