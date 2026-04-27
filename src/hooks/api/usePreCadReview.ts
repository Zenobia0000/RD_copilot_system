/**
 * API hooks for Pre-CAD Review page
 *
 * - usePreCadSolutions: fetch alternatives that have at least one MUST passed (as Solution type)
 * - usePreCadConvergenceStats: compute convergence stats from contradictions for Gate P
 * - useUpdatePreCadReview: update pre_cad_scores on an alternative
 *
 * For raw Alternative hooks (useAlternatives, useUpdateAlternative), use './useCreate'.
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type { Solution, ConvergenceNode } from '@/types/solution';
import type { ContradictionSeverity } from '@/types/contradiction';
import type { Json } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// Shared row type & mapper (Solution view of alternatives table)
// ---------------------------------------------------------------------------

interface AlternativeRow {
  id: string;
  project_id: string;
  name: string;
  mechanism: string | null;
  source: string | null;
  key_assumption_ids: string[] | null;
  must_scores: Json | null;
  interface_contract: Json | null;
  pre_cad_scores: Json | null;
  overall_pass: boolean | null;
  cad_status: string;
  created_at: string;
  updated_at: string;
}

interface SolutionBundle {
  description?: string;
  assumptions?: string[];
  risks?: Array<{ id: string; description: string; severity: string; mitigation: string }>;
  minValidation?: string;
  mustCriteria?: Array<{ id: string; label: string; passed: boolean | null }>;
  relatedContradictionIds?: string[];
  secondaryContradictions?: Array<{ id: string; description: string; severity: ContradictionSeverity; resolved: boolean }>;
  contradictionSeverity?: ContradictionSeverity;
}

function parseSolutionBundle(json: Json | null): SolutionBundle {
  if (!json || typeof json !== 'object' || Array.isArray(json)) return {};
  return json as unknown as SolutionBundle;
}

function mapRowToSolution(r: AlternativeRow): Solution {
  const bundle = parseSolutionBundle(r.must_scores);
  return {
    id: r.id,
    projectId: r.project_id,
    name: r.name,
    description: bundle.description ?? r.mechanism ?? '',
    mechanism: r.mechanism ?? '',
    assumptions: bundle.assumptions ?? (r.key_assumption_ids ?? []),
    risks: (bundle.risks ?? []) as Solution['risks'],
    minValidation: bundle.minValidation ?? '',
    mustCriteria: (bundle.mustCriteria ?? []) as Solution['mustCriteria'],
    relatedContradictionIds: bundle.relatedContradictionIds ?? [],
    secondaryContradictions: (bundle.secondaryContradictions ?? []) as Solution['secondaryContradictions'],
    contradictionSeverity: bundle.contradictionSeverity ?? 'minor',
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

// ---------------------------------------------------------------------------
// usePreCadSolutions — alternatives with at least one MUST passed (as Solution[])
// ---------------------------------------------------------------------------

export function usePreCadSolutions(projectId: string | undefined) {
  return useQuery<Solution[], Error>({
    queryKey: [...queryKeys.alternatives.byProject(projectId), 'pre-cad'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('alternatives')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: true });
      if (error) throw error;

      const allSolutions = (data as AlternativeRow[]).map(mapRowToSolution);
      // Filter: at least one mustCriteria passed
      return allSolutions.filter(
        (s) => s.mustCriteria.some((m) => m.passed === true)
      );
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

// ---------------------------------------------------------------------------
// usePreCadConvergenceStats — contradiction convergence for Gate P
// ---------------------------------------------------------------------------

interface ConvergenceStats {
  confidenceScore: number;
  fatalResolved: number;
  fatalTotal: number;
  majorResolved: number;
  majorTotal: number;
  minorResolved: number;
  minorTotal: number;
  contradictionNodes: ConvergenceNode[];
}

export function usePreCadConvergenceStats(projectId: string | undefined) {
  return useQuery<ConvergenceStats, Error>({
    queryKey: [...queryKeys.contradictions.byProject(projectId), 'convergence-stats'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('contradictions')
        .select('id, severity, resolved, engineering_statement')
        .eq('project_id', projectId!);
      if (error) throw error;

      const rows = data as Array<{
        id: string;
        severity: string;
        resolved: boolean;
        engineering_statement: string | null;
      }>;

      const contradictionNodes: ConvergenceNode[] = rows.map((r, i) => ({
        id: r.id,
        label: r.engineering_statement?.slice(0, 30) ?? `矛盾 ${i + 1}`,
        type: 'contradiction' as const,
        severity: r.severity as ContradictionSeverity,
        resolved: r.resolved,
        x: 50,
        y: 50 + i * 80,
      }));

      const fatal = rows.filter((r) => r.severity === 'fatal');
      const major = rows.filter((r) => r.severity === 'major');
      const minor = rows.filter((r) => r.severity === 'minor');

      const fatalR = fatal.filter((r) => r.resolved).length;
      const majorR = major.filter((r) => r.resolved).length;
      const totalFM = fatal.length + major.length;
      const resolvedFM = fatalR + majorR;
      const score = totalFM > 0 ? (resolvedFM / totalFM) * 100 : 100;

      return {
        confidenceScore: Math.round(score * 10) / 10,
        fatalResolved: fatalR,
        fatalTotal: fatal.length,
        majorResolved: majorR,
        majorTotal: major.length,
        minorResolved: minor.filter((r) => r.resolved).length,
        minorTotal: minor.length,
        contradictionNodes,
      };
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

// ---------------------------------------------------------------------------
// useUpdatePreCadReview — update pre_cad_scores on an alternative
// ---------------------------------------------------------------------------

export function useUpdatePreCadReview() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    {
      id: string;
      projectId: string;
      preCadScores?: Record<string, number | null>;
      overallPass?: boolean | null;
    }
  >({
    mutationFn: async (vars) => {
      const updateData: Record<string, unknown> = {
        updated_at: new Date().toISOString(),
      };
      if (vars.preCadScores !== undefined) updateData.pre_cad_scores = vars.preCadScores;
      if (vars.overallPass !== undefined) updateData.overall_pass = vars.overallPass;

      const { error } = await supabase
        .from('alternatives')
        .update(updateData)
        .eq('id', vars.id);
      if (error) throw error;
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.alternatives.byProject(vars.projectId) });
      toast.success('審查分數已更新');
    },
    onError: (err) => {
      toast.error(`更新審查分數失敗：${err.message}`);
    },
  });
}
