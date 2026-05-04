/**
 * React Query hooks for `concept_architecture_packs` (migration 015).
 *
 * - useConceptArchitecturePack(projectId)  — useQuery  (read latest pack)
 * - useGenerateConceptArchitecturePack(projectId) — useMutation (POST generate)
 *
 * Pattern follows useTrizConsolidationResult.ts: direct Supabase read + API mutation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import { generateConceptArchitecturePack } from '@/lib/api';
import type {
  ConceptSubsystem,
  ConceptInterface,
  ConceptArchitecturePack,
  ConceptArchitecturePackResponse,
  UpstreamArtifactSummary,
} from '@/types/conceptArchitecture';

/* ------------------------------------------------------------------ */
/*  Row type returned by Supabase (snake_case JSON columns)           */
/* ------------------------------------------------------------------ */

interface ConceptArchitecturePackRow {
  id: string;
  project_id: string;
  template_id: string;
  subsystems: unknown;
  interfaces: unknown;
  architecture_rationale: string;
  coverage_summary: string;
  source_badges: unknown;
  created_at: string;
}

/* ------------------------------------------------------------------ */
/*  Row → domain type mapper                                          */
/* ------------------------------------------------------------------ */

const mapRow = (r: ConceptArchitecturePackRow): ConceptArchitecturePackResponse => ({
  pack: {
    subsystems: (r.subsystems ?? []) as ConceptSubsystem[],
    interfaces: (r.interfaces ?? []) as ConceptInterface[],
    architecture_rationale: r.architecture_rationale ?? '',
    template_id: r.template_id ?? 'generic',
    coverage_summary: r.coverage_summary ?? '',
  },
  source_badges: (r.source_badges ?? {}) as Record<string, boolean>,
});

/* ------------------------------------------------------------------ */
/*  useQuery — read latest pack from Supabase                         */
/* ------------------------------------------------------------------ */

/**
 * Fetch the latest concept architecture pack for a project.
 * Returns `ConceptArchitecturePackResponse | null`.
 */
export function useConceptArchitecturePack(projectId: string | undefined) {
  return useQuery<ConceptArchitecturePackResponse | null, Error>({
    queryKey: queryKeys.concept_architecture_packs.byProject(projectId),
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 015, Supabase types not regenerated yet
      const { data, error } = await (supabase as any)
        .from('concept_architecture_packs')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle();
      if (error) throw error;
      if (!data) return null;
      return mapRow(data as ConceptArchitecturePackRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

/* ------------------------------------------------------------------ */
/*  useMutation — trigger generation via POST API                     */
/* ------------------------------------------------------------------ */

export interface GeneratePackVariables {
  upstream: UpstreamArtifactSummary;
  templateId?: string;
}

/**
 * Trigger concept architecture pack generation.
 * On success, invalidates the useQuery cache so the UI picks up the new pack.
 */
export function useGenerateConceptArchitecturePack(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation<ConceptArchitecturePackResponse, Error, GeneratePackVariables>({
    mutationFn: (vars) =>
      generateConceptArchitecturePack({
        project_id: projectId!,
        template_id: vars.templateId ?? 'generic',
        upstream: vars.upstream,
      }),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: queryKeys.concept_architecture_packs.byProject(projectId),
      });
    },
  });
}
