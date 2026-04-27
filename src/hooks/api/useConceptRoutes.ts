/**
 * API hooks for Concept Routes and Compatibility Pairs
 *
 * CRUD operations on `concept_routes` and `compatibility_pairs` tables,
 * mapping snake_case DB columns to camelCase frontend types.
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type {
  ConceptRoute,
  CompositionEntry,
  SolutionCompatibility,
  CompatibilityResult,
  AdoptionType,
} from '@/types/conceptRoute';

// ---------------------------------------------------------------------------
// Row types & mappers — concept_routes
// ---------------------------------------------------------------------------

interface ConceptRouteRow {
  id: string;
  project_id: string;
  route_type: string;
  composition: unknown; // JSONB stored as Json
  composition_rationale: string | null;
  anti_pattern_warnings: string[] | null;
  created_at: string;
}

const mapRouteRow = (r: ConceptRouteRow): ConceptRoute => ({
  id: r.id,
  type: r.route_type as ConceptRoute['type'],
  composition: Array.isArray(r.composition)
    ? (r.composition as CompositionEntry[])
    : [],
  compositionRationale: r.composition_rationale ?? '',
  antiPatternWarnings: r.anti_pattern_warnings ?? [],
  createdAt: r.created_at,
});

// ---------------------------------------------------------------------------
// Row types & mappers — compatibility_pairs
// ---------------------------------------------------------------------------

interface CompatibilityPairRow {
  id: string;
  project_id: string;
  solution_a_id: string;
  solution_b_id: string;
  result: string;
  adoption_type: string | null;
  reason: string | null;
}

const mapPairRow = (r: CompatibilityPairRow): SolutionCompatibility => ({
  solutionAId: r.solution_a_id,
  solutionBId: r.solution_b_id,
  result: r.result as CompatibilityResult,
  adoptionType: (r.adoption_type as AdoptionType) ?? null,
  reason: r.reason ?? '',
});

// ---------------------------------------------------------------------------
// useConceptRoutes — SELECT concept_routes by project
// ---------------------------------------------------------------------------

export function useConceptRoutes(projectId: string | undefined) {
  return useQuery<ConceptRoute[], Error>({
    queryKey: queryKeys.concept_routes.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('concept_routes')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: true });

      if (error) throw error;
      return (data as ConceptRouteRow[]).map(mapRouteRow);
    },
    ...defaultQueryOptions,
    enabled: !!projectId,
  });
}

// ---------------------------------------------------------------------------
// useCreateConceptRoute — INSERT concept_route
// ---------------------------------------------------------------------------

export function useCreateConceptRoute() {
  const queryClient = useQueryClient();

  return useMutation<ConceptRoute, Error, {
    projectId: string;
    routeType: ConceptRoute['type'];
    composition: CompositionEntry[];
    compositionRationale: string;
    antiPatternWarnings: string[];
  }>({
    mutationFn: async (variables) => {
      const { data, error } = await supabase
        .from('concept_routes')
        .insert({
          project_id: variables.projectId,
          route_type: variables.routeType,
          composition: variables.composition as unknown as Record<string, unknown>,
          composition_rationale: variables.compositionRationale,
          anti_pattern_warnings: variables.antiPatternWarnings,
        })
        .select()
        .single();

      if (error) throw error;
      return mapRouteRow(data as ConceptRouteRow);
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.concept_routes.byProject(variables.projectId),
      });
      toast.success('Concept route created');
    },
    onError: (error) => {
      toast.error(`Failed to create concept route: ${error.message}`);
      console.error('[useCreateConceptRoute] insert failed:', error);
    },
  });
}

// ---------------------------------------------------------------------------
// useCompatibilityPairs — SELECT compatibility_pairs by project
// ---------------------------------------------------------------------------

export function useCompatibilityPairs(projectId: string | undefined) {
  return useQuery<SolutionCompatibility[], Error>({
    queryKey: queryKeys.compatibility_pairs.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('compatibility_pairs')
        .select('*')
        .eq('project_id', projectId!);

      if (error) throw error;
      return (data as CompatibilityPairRow[]).map(mapPairRow);
    },
    ...defaultQueryOptions,
    enabled: !!projectId,
  });
}

// ---------------------------------------------------------------------------
// useCreateCompatibilityPairs — INSERT batch (multiple pairs at once)
// ---------------------------------------------------------------------------

export function useCreateCompatibilityPairs() {
  const queryClient = useQueryClient();

  return useMutation<SolutionCompatibility[], Error, {
    projectId: string;
    pairs: Array<{
      solutionAId: string;
      solutionBId: string;
      result: CompatibilityResult;
      adoptionType: AdoptionType | null;
      reason: string;
    }>;
  }>({
    mutationFn: async (variables) => {
      const rows = variables.pairs.map((p) => ({
        project_id: variables.projectId,
        solution_a_id: p.solutionAId,
        solution_b_id: p.solutionBId,
        result: p.result,
        adoption_type: p.adoptionType,
        reason: p.reason,
      }));

      const { data, error } = await supabase
        .from('compatibility_pairs')
        .insert(rows)
        .select();

      if (error) throw error;
      return (data as CompatibilityPairRow[]).map(mapPairRow);
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.compatibility_pairs.byProject(variables.projectId),
      });
      toast.success('Compatibility pairs saved');
    },
    onError: (error) => {
      toast.error(`Failed to save compatibility pairs: ${error.message}`);
      console.error('[useCreateCompatibilityPairs] insert failed:', error);
    },
  });
}
