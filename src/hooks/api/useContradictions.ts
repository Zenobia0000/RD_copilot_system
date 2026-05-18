/**
 * API hooks for the Contradiction Identification page
 *
 * CRUD operations on the `contradictions` table, mapping
 * snake_case DB columns to the camelCase `Contradiction` frontend type.
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import { CONTRADICTION_SEVERITIES, DEFAULT_SEVERITY } from '@/types/contradiction';
import type { Contradiction, ContradictionSeverity } from '@/types/contradiction';

// ---------------------------------------------------------------------------
// Row type & mapper
// ---------------------------------------------------------------------------

interface ContradictionRow {
  id: string;
  project_id: string;
  natural_description: string | null;
  improving_param: number | null;
  worsening_param: number | null;
  engineering_statement: string | null;
  physical_contradiction: string | null;
  type: string | null;
  severity: string;
  resolved: boolean;
  source_question_id: string | null;
  source_type: string | null;
  // Su-Field fields (populated when type === 'SF')
  sf_substance_1: string | null;
  sf_substance_2: string | null;
  sf_field: string | null;
  sf_interaction: string | null;
  sf_completeness: string | null;
  // PC decomposition columns (migration 009)
  parent_contradiction_id: string | null;
  derived_parameter: string | null;
  subsystem_hint: string | null;
  separation_principle_id: string | null;
  separation_category: string | null;
  separation_rationale: string | null;
  pc_attribute_a: string | null;
  pc_attribute_not_a: string | null;
  // 3-Stage TC Pipeline fields
  linked_kpis: string[] | null;
  why_selected: string | null;
  priority: number | null;
  created_at: string;
  updated_at: string;
}

const validSeverities: ReadonlySet<string> = new Set(CONTRADICTION_SEVERITIES);

const mapRow = (r: ContradictionRow): Contradiction => ({
  id: r.id,
  projectId: r.project_id,
  naturalDescription: r.natural_description ?? '',
  improvingParam: r.improving_param,
  worseningParam: r.worsening_param,
  engineeringStatement: r.engineering_statement ?? '',
  physicalContradiction: r.physical_contradiction ?? '',
  type: (r.type === 'TC' || r.type === 'PC' || r.type === 'SF' ? r.type : null) as 'TC' | 'PC' | 'SF' | null,
  severity: (validSeverities.has(r.severity) ? r.severity : DEFAULT_SEVERITY) as ContradictionSeverity,
  resolved: (r as any).resolved ?? false,
  sourceQuestionId: r.source_question_id ?? null,
  sourceType: (r.source_type ?? 'manual') as Contradiction['sourceType'],
  sfSubstance1: r.sf_substance_1 ?? null,
  sfSubstance2: r.sf_substance_2 ?? null,
  sfField: r.sf_field ?? null,
  sfInteraction: r.sf_interaction ?? null,
  sfCompleteness: r.sf_completeness ?? null,
  parentContradictionId: r.parent_contradiction_id ?? null,
  derivedParameter: r.derived_parameter ?? null,
  subsystemHint: r.subsystem_hint ?? null,
  separationPrincipleId: r.separation_principle_id ?? null,
  separationCategory: (r.separation_category as Contradiction['separationCategory']) ?? null,
  separationRationale: r.separation_rationale ?? null,
  pcAttributeA: r.pc_attribute_a ?? null,
  pcAttributeNotA: r.pc_attribute_not_a ?? null,
  linkedKpis: r.linked_kpis ?? [],
  whySelected: r.why_selected ?? null,
  priority: r.priority ?? null,
  createdAt: r.created_at,
  updatedAt: r.updated_at,
});

// ---------------------------------------------------------------------------
// Query hook
// ---------------------------------------------------------------------------

export function useContradictions(projectId: string | undefined) {
  return useQuery<Contradiction[], Error>({
    queryKey: queryKeys.contradictions.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('contradictions')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: true });
      if (error) throw error;
      return (data as ContradictionRow[]).map(mapRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

export function useCreateContradiction() {
  const qc = useQueryClient();
  return useMutation<
    Contradiction,
    Error,
    {
      projectId: string;
      naturalDescription: string;
      improvingParam: number | null;
      worseningParam: number | null;
      engineeringStatement: string;
      physicalContradiction?: string;
      severity: ContradictionSeverity;
    }
  >({
    mutationFn: async (vars) => {
      const now = new Date().toISOString();
      const { data, error } = await supabase
        .from('contradictions')
        .insert({
          project_id: vars.projectId,
          natural_description: vars.naturalDescription,
          improving_param: vars.improvingParam,
          worsening_param: vars.worseningParam,
          engineering_statement: vars.engineeringStatement,
          physical_contradiction: vars.physicalContradiction ?? '',
          severity: vars.severity,
          created_at: now,
          updated_at: now,
        })
        .select()
        .single();
      if (error) throw error;
      return mapRow(data as ContradictionRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.contradictions.byProject(vars.projectId) });
      toast.success('矛盾已新增');
    },
    onError: (err) => {
      toast.error(`新增矛盾失敗：${err.message}`);
    },
  });
}

export function useUpdateContradiction() {
  const qc = useQueryClient();
  return useMutation<
    Contradiction,
    Error,
    {
      id: string;
      projectId: string;
      naturalDescription?: string;
      improvingParam?: number | null;
      worseningParam?: number | null;
      engineeringStatement?: string;
      physicalContradiction?: string;
      severity?: ContradictionSeverity;
    }
  >({
    mutationFn: async (vars) => {
      const updateData: Record<string, unknown> = { updated_at: new Date().toISOString() };
      if (vars.naturalDescription !== undefined) updateData.natural_description = vars.naturalDescription;
      if (vars.improvingParam !== undefined) updateData.improving_param = vars.improvingParam;
      if (vars.worseningParam !== undefined) updateData.worsening_param = vars.worseningParam;
      if (vars.engineeringStatement !== undefined) updateData.engineering_statement = vars.engineeringStatement;
      if (vars.physicalContradiction !== undefined) updateData.physical_contradiction = vars.physicalContradiction;
      if (vars.severity !== undefined) updateData.severity = vars.severity;

      const { data, error } = await supabase
        .from('contradictions')
        .update(updateData)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapRow(data as ContradictionRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.contradictions.byProject(vars.projectId) });
      toast.success('矛盾已更新');
    },
    onError: (err) => {
      toast.error(`更新矛盾失敗：${err.message}`);
    },
  });
}

export function useDeleteContradiction() {
  const qc = useQueryClient();
  return useMutation<void, Error, { id: string; projectId: string }>({
    mutationFn: async (vars) => {
      // Delete dependent triz_solutions first to avoid FK constraint violation
      const { error: trizErr } = await supabase
        .from('triz_solutions')
        .delete()
        .eq('contradiction_id', vars.id);
      if (trizErr) throw trizErr;

      // Drop the matching layered drill-down row (migration 010). Its
      // contradiction_id is a TEXT FK-by-name without DB-level cascade.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 010, Supabase types not regenerated yet
      const { error: ltsErr } = await (supabase as any)
        .from('layered_triz_solutions')
        .delete()
        .eq('contradiction_id', vars.id);
      if (ltsErr) throw ltsErr;

      const { error } = await supabase
        .from('contradictions')
        .delete()
        .eq('id', vars.id);
      if (error) throw error;
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.contradictions.byProject(vars.projectId) });
      qc.invalidateQueries({ queryKey: queryKeys.triz_solutions.all });
      qc.invalidateQueries({ queryKey: queryKeys.layered_triz_solutions.byProject(vars.projectId) });
      toast.success('矛盾及關聯 TRIZ 解法已刪除');
    },
    onError: (err) => {
      toast.error(`刪除矛盾失敗：${err.message}`);
    },
  });
}
