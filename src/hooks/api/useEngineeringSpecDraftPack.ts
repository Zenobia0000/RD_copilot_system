/**
 * React Query hook for `engineering_spec_draft_packs` (migration 016).
 *
 * - useEngineeringSpecDraftPack(projectId)  — useQuery  (read latest pack)
 *
 * Pattern follows useConceptArchitecturePack.ts: direct Supabase read.
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type { EngineeringSpecDraftResponse } from '@/types/generated/engineeringSpec';

/* ------------------------------------------------------------------ */
/*  Row type returned by Supabase (snake_case JSON columns)           */
/* ------------------------------------------------------------------ */

interface EngineeringSpecDraftPackRow {
  id: string;
  project_id: string;
  drafts_json: unknown;
  pipeline_version: string | null;
  step_count: number | null;
  created_at: string;
  updated_at: string;
}

/* ------------------------------------------------------------------ */
/*  Row → domain type mapper                                          */
/* ------------------------------------------------------------------ */

const mapRow = (r: EngineeringSpecDraftPackRow): EngineeringSpecDraftResponse => {
  const dj = (r.drafts_json ?? {}) as Record<string, unknown>;
  return {
    drafts: (dj.drafts ?? []) as EngineeringSpecDraftResponse['drafts'],
    subsystem_tree: (dj.subsystem_tree ?? []) as EngineeringSpecDraftResponse['subsystem_tree'],
    package_map: (dj.package_map ?? null) as EngineeringSpecDraftResponse['package_map'],
  };
};

/* ------------------------------------------------------------------ */
/*  useQuery — read latest pack from Supabase                         */
/* ------------------------------------------------------------------ */

/**
 * Fetch the latest engineering spec draft pack for a project.
 * Returns `EngineeringSpecDraftResponse | null`.
 */
export function useEngineeringSpecDraftPack(projectId: string | undefined) {
  return useQuery<EngineeringSpecDraftResponse | null, Error>({
    queryKey: queryKeys.engineering_spec_drafts.byProject(projectId),
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 016, Supabase types not regenerated yet
      const { data, error } = await (supabase as any)
        .from('engineering_spec_draft_packs')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle();
      if (error) throw error;
      if (!data) return null;
      return mapRow(data as EngineeringSpecDraftPackRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}
