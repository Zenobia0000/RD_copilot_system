/**
 * API hooks for Solutions (SolutionExplorer page)
 *
 * The `Solution` frontend type is backed by the `alternatives` table.
 * Complex nested fields (mustCriteria, risks, secondaryContradictions)
 * are stored in JSON columns (`must_scores` for mustCriteria + risks + secondaryContradictions bundle).
 *
 * The convergence graph is built client-side from `contradictions` + `alternatives`.
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
  Solution,
  MustCriteria,
  SolutionRisk,
  SecondaryContradiction,
  ConvergenceNode,
  ConvergenceEdge,
} from '@/types/solution';
import type { ContradictionSeverity } from '@/types/contradiction';
import type { Json } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// Row type & mapper
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

/**
 * We store extra Solution fields inside `must_scores` JSON as an extended bundle:
 * {
 *   description?: string,
 *   assumptions?: string[],
 *   risks?: SolutionRisk[],
 *   minValidation?: string,
 *   mustCriteria?: MustCriteria[],
 *   relatedContradictionIds?: string[],
 *   secondaryContradictions?: SecondaryContradiction[],
 *   contradictionSeverity?: ContradictionSeverity,
 * }
 */
interface SolutionBundle {
  description?: string;
  assumptions?: string[];
  risks?: SolutionRisk[];
  minValidation?: string;
  mustCriteria?: MustCriteria[];
  relatedContradictionIds?: string[];
  secondaryContradictions?: SecondaryContradiction[];
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
    risks: bundle.risks ?? [],
    minValidation: bundle.minValidation ?? '',
    mustCriteria: bundle.mustCriteria ?? [],
    relatedContradictionIds: bundle.relatedContradictionIds ?? [],
    secondaryContradictions: bundle.secondaryContradictions ?? [],
    contradictionSeverity: bundle.contradictionSeverity ?? 'minor',
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

function solutionToRow(
  sol: Partial<Solution> & { projectId: string; name: string },
): Record<string, unknown> {
  const bundle: SolutionBundle = {
    description: sol.description,
    assumptions: sol.assumptions,
    risks: sol.risks,
    minValidation: sol.minValidation,
    mustCriteria: sol.mustCriteria,
    relatedContradictionIds: sol.relatedContradictionIds,
    secondaryContradictions: sol.secondaryContradictions,
    contradictionSeverity: sol.contradictionSeverity,
  };
  const now = new Date().toISOString();
  return {
    project_id: sol.projectId,
    name: sol.name,
    mechanism: sol.mechanism ?? sol.description ?? '',
    must_scores: bundle as unknown as Json,
    updated_at: now,
  };
}

// ---------------------------------------------------------------------------
// useSolutions — list solutions for a project
// ---------------------------------------------------------------------------

export function useSolutions(projectId: string | undefined) {
  return useQuery<Solution[], Error>({
    queryKey: queryKeys.alternatives.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('alternatives')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: true });
      if (error) throw error;
      return (data as AlternativeRow[]).map(mapRowToSolution);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

// ---------------------------------------------------------------------------
// useCreateSolution
// ---------------------------------------------------------------------------

export function useCreateSolution() {
  const qc = useQueryClient();
  return useMutation<
    Solution,
    Error,
    Partial<Solution> & { projectId: string; name: string }
  >({
    mutationFn: async (vars) => {
      const row = solutionToRow(vars);
      row.created_at = new Date().toISOString();
      const { data, error } = await supabase
        .from('alternatives')
        .insert(row)
        .select()
        .single();
      if (error) throw error;
      return mapRowToSolution(data as AlternativeRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.alternatives.byProject(vars.projectId) });
      toast.success('方案已建立');
    },
    onError: (err) => {
      toast.error(`建立方案失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// useUpdateSolution — update MUST criteria, risks, secondary contradictions, etc.
// ---------------------------------------------------------------------------

export function useUpdateSolution() {
  const qc = useQueryClient();
  return useMutation<
    Solution,
    Error,
    { id: string; projectId: string } & Partial<Solution>
  >({
    mutationFn: async (vars) => {
      // First fetch current row to merge bundle
      const { data: current, error: fetchErr } = await supabase
        .from('alternatives')
        .select('*')
        .eq('id', vars.id)
        .single();
      if (fetchErr) throw fetchErr;

      const existing = mapRowToSolution(current as AlternativeRow);
      const merged: Solution = { ...existing, ...vars, updatedAt: new Date().toISOString() };
      const row = solutionToRow(merged);

      const { data, error } = await supabase
        .from('alternatives')
        .update(row)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapRowToSolution(data as AlternativeRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.alternatives.byProject(vars.projectId) });
      toast.success('方案已更新');
    },
    onError: (err) => {
      toast.error(`更新方案失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// useConvergenceGraph — build DAG from contradictions + solutions
// ---------------------------------------------------------------------------

interface ContradictionRow {
  id: string;
  project_id: string;
  severity: string;
  resolved: boolean;
  engineering_statement: string | null;
  improving_param: number | null;
  worsening_param: number | null;
}

export function useConvergenceGraph(projectId: string | undefined) {
  return useQuery<{ nodes: ConvergenceNode[]; edges: ConvergenceEdge[] }, Error>({
    queryKey: [...queryKeys.alternatives.byProject(projectId), 'convergence'],
    queryFn: async () => {
      // Fetch contradictions
      const { data: contRows, error: contErr } = await supabase
        .from('contradictions')
        .select('id, project_id, severity, resolved, engineering_statement, improving_param, worsening_param')
        .eq('project_id', projectId!);
      if (contErr) throw contErr;

      // Fetch alternatives (solutions)
      const { data: altRows, error: altErr } = await supabase
        .from('alternatives')
        .select('*')
        .eq('project_id', projectId!);
      if (altErr) throw altErr;

      const contradictions = contRows as ContradictionRow[];
      const solutions = (altRows as AlternativeRow[]).map(mapRowToSolution);

      const nodes: ConvergenceNode[] = [];
      const edges: ConvergenceEdge[] = [];

      // Layout: contradictions on the left, solutions in the middle, secondary contradictions on the right
      const SPACING_X = 200;
      const SPACING_Y = 100;

      // Add contradiction nodes
      contradictions.forEach((c, i) => {
        const label = c.engineering_statement
          ? c.engineering_statement.slice(0, 30)
          : `矛盾 ${i + 1}`;
        nodes.push({
          id: c.id,
          label,
          type: 'contradiction',
          severity: c.severity as ContradictionSeverity,
          resolved: c.resolved,
          x: 50,
          y: 50 + i * SPACING_Y,
        });
      });

      // Add solution nodes + edges from related contradictions + secondary contradiction nodes
      let solY = 50;
      solutions.forEach((sol) => {
        nodes.push({
          id: sol.id,
          label: sol.name.slice(0, 20),
          type: 'solution',
          x: 50 + SPACING_X,
          y: solY,
        });

        // Edges: contradiction -> solution
        sol.relatedContradictionIds.forEach((cId) => {
          edges.push({ from: cId, to: sol.id });
        });

        // Secondary contradiction nodes
        sol.secondaryContradictions.forEach((sc, scIdx) => {
          nodes.push({
            id: sc.id,
            label: sc.description.slice(0, 20),
            type: 'contradiction',
            severity: sc.severity,
            resolved: sc.resolved,
            x: 50 + SPACING_X * 2,
            y: solY + scIdx * (SPACING_Y * 0.6),
          });
          edges.push({ from: sol.id, to: sc.id });
        });

        solY += Math.max(1, sol.secondaryContradictions.length) * SPACING_Y;
      });

      return { nodes, edges };
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}
