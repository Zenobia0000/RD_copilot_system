/**
 * React Query hook for `directed_triz_solutions` rows (v8).
 *
 * Backend `/triz/solve-directed` upserts each result into Supabase
 * (see backend/app/agents/triz_solver.py::_persist_directed_solution).
 * The UI reads the full set on mount so that page reload / tab switch
 * no longer drops in-memory state.
 *
 * Row structure mirrors migration 011
 * (supabase/migrations/011_triz_directed_solutions.sql).
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type {
  ContradictionDirectionResult,
  DirectionSolution,
  DirectionGroup,
  DirectionScore,
  SubRequirement,
  DirectionCoverageAudit,
  CombinedDirection,
} from '@/types/directedTriz';

interface DirectedTrizSolutionRow {
  id: string;
  project_id: string;
  contradiction_id: string;
  natural_description: string | null;
  severity: string;
  all_solutions: unknown;
  all_directions: unknown;
  scored_directions: unknown;
  top1: unknown | null;
  top2: unknown | null;
  top1_score: unknown | null;
  top2_score: unknown | null;
  sub_requirements: unknown;
  coverage_audits: unknown;
  combined_direction: unknown | null;
}

type Severity = 'fatal' | 'major' | 'minor' | 'unknown';

const VALID_SEVERITIES: Severity[] = ['fatal', 'major', 'minor', 'unknown'];

const mapRow = (r: DirectedTrizSolutionRow): ContradictionDirectionResult => ({
  contradiction_id: r.contradiction_id,
  natural_description: r.natural_description ?? '',
  severity: (VALID_SEVERITIES.includes(r.severity as Severity)
    ? r.severity
    : 'unknown') as Severity,
  all_solutions: (r.all_solutions ?? []) as DirectionSolution[],
  all_directions: (r.all_directions ?? []) as DirectionGroup[],
  scored_directions: (r.scored_directions ?? []) as DirectionScore[],
  top1: (r.top1 ?? null) as DirectionGroup | null,
  top2: (r.top2 ?? null) as DirectionGroup | null,
  top1_score: (r.top1_score ?? null) as DirectionScore | null,
  top2_score: (r.top2_score ?? null) as DirectionScore | null,
  sub_requirements: (r.sub_requirements ?? []) as SubRequirement[],
  coverage_audits: (r.coverage_audits ?? []) as DirectionCoverageAudit[],
  combined_direction: (r.combined_direction ?? null) as CombinedDirection | null,
});

/**
 * Fetch all directed TRIZ solutions for a project, keyed by contradiction_id.
 *
 * Returns `Record<string, ContradictionDirectionResult>` — same shape as
 * the in-memory `directedResults` state in Create.tsx.
 */
export function useDirectedTrizSolutions(projectId: string | undefined) {
  return useQuery<Record<string, ContradictionDirectionResult>, Error>({
    queryKey: queryKeys.directed_triz_solutions.byProject(projectId),
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 011, Supabase types not regenerated yet
      const { data, error } = await (supabase as any)
        .from('directed_triz_solutions')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: true });
      if (error) throw error;
      const byContradiction: Record<string, ContradictionDirectionResult> = {};
      for (const row of (data as DirectedTrizSolutionRow[]) ?? []) {
        byContradiction[row.contradiction_id] = mapRow(row);
      }
      return byContradiction;
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}
