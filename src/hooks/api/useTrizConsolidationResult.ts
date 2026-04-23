/**
 * React Query hook for `triz_consolidation_results` row (v8, migration 012).
 *
 * Backend `/triz/consolidate` upserts the consolidation outcome into Supabase.
 * For single-contradiction projects the frontend can also upsert directly.
 * This hook rehydrates on mount so page reload keeps the consolidation panel.
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type {
  ConsolidationResult,
  ConsolidationStatus,
  DirectionGroup,
  ConflictReport,
} from '@/types/directedTriz';

interface TrizConsolidationRow {
  id: string;
  project_id: string;
  status: string;
  adopted_directions: unknown;
  conflict_report: unknown | null;
  integration_advice: string;
}

const VALID_STATUSES: ConsolidationStatus[] = ['compatible', 'resolved_with_swap', 'conflict'];

const mapRow = (r: TrizConsolidationRow): ConsolidationResult => ({
  status: (VALID_STATUSES.includes(r.status as ConsolidationStatus)
    ? r.status
    : 'compatible') as ConsolidationStatus,
  adopted_directions: (r.adopted_directions ?? {}) as Record<string, DirectionGroup>,
  conflict_report: (r.conflict_report ?? null) as ConflictReport | null,
  integration_advice: r.integration_advice ?? '',
});

/**
 * Fetch the consolidation result for a project (at most one row per project).
 * Returns `ConsolidationResult | null`.
 */
export function useTrizConsolidationResult(projectId: string | undefined) {
  return useQuery<ConsolidationResult | null, Error>({
    queryKey: queryKeys.triz_consolidation_results.byProject(projectId),
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 012, Supabase types not regenerated yet
      const { data, error } = await (supabase as any)
        .from('triz_consolidation_results')
        .select('*')
        .eq('project_id', projectId!)
        .maybeSingle();
      if (error) throw error;
      if (!data) return null;
      return mapRow(data as TrizConsolidationRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

/**
 * Directly upsert a ConsolidationResult into `triz_consolidation_results`.
 * Used by the frontend for single-contradiction projects that skip the
 * backend `/triz/consolidate` endpoint.
 */
export async function upsertConsolidationResult(
  projectId: string,
  result: ConsolidationResult,
): Promise<void> {
  const tcrId = `TCR-${projectId.slice(0, 8)}`;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { error } = await (supabase as any)
    .from('triz_consolidation_results')
    .upsert(
      {
        id: tcrId,
        project_id: projectId,
        status: result.status,
        adopted_directions: result.adopted_directions,
        conflict_report: result.conflict_report,
        integration_advice: result.integration_advice ?? '',
      },
      { onConflict: 'id' },
    );
  if (error) {
    console.error('upsertConsolidationResult failed:', error);
  }
}
