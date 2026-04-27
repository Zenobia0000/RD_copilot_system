/**
 * Project API hooks
 *
 * Provides CRUD operations and stats for projects using Supabase + React Query.
 */

import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys } from '@/hooks/api/useQueryConfig';
import { useSupabaseMutation } from '@/hooks/api/useSupabaseQuery';
import { toast } from 'sonner';
import type { Project, ProjectStatus, PhaseProgress, QuickStats, MustCriterionConfig } from '@/types/project';
import type { Database } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ProjectRow = Database['public']['Tables']['projects']['Row'];
type ProjectInsert = Database['public']['Tables']['projects']['Insert'];

// ---------------------------------------------------------------------------
// Row <-> Frontend mapping
// ---------------------------------------------------------------------------

const DEFAULT_PHASE_PROGRESS: PhaseProgress = {
  'D1': 'not_started', 'D2': 'not_started', 'PG-D': 'not_started',
  'X1': 'not_started', 'X2': 'not_started', 'PG-X': 'not_started',
  'V1': 'not_started', 'V2': 'not_started', 'PG-V': 'not_started',
};

const DEFAULT_QUICK_STATS: QuickStats = {
  contradictions_count: 0,
  assumptions_count: 0,
  alternatives_count: 0,
  risks_count: 0,
  experiments_count: 0,
  evidence_items_count: 0,
};

function mapRowToProject(row: ProjectRow): Project {
  return {
    id: row.id,
    name: row.name,
    description: row.description ?? '',
    status: row.status as ProjectStatus,
    progress: row.progress,
    createdBy: row.created_by ?? '',
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    phase: row.phase,
    mission: row.mission ?? undefined,
    phase_progress: (row.phase_progress as unknown as PhaseProgress) ?? DEFAULT_PHASE_PROGRESS,
    quick_stats: (row.quick_stats as unknown as QuickStats) ?? DEFAULT_QUICK_STATS,
    gates_passed: row.gates_passed,
    gates_total: row.gates_total,
    must_criteria_config: (row.must_criteria_config as unknown as MustCriterionConfig[]) ?? undefined,
  };
}

// ---------------------------------------------------------------------------
// useProjects — SELECT all projects
// ---------------------------------------------------------------------------

export function useProjects() {
  return useQuery<Project[], Error>({
    queryKey: queryKeys.projects.all,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .order('updated_at', { ascending: false });

      if (error) throw error;
      return (data as ProjectRow[]).map(mapRowToProject);
    },
    staleTime: 30_000,
    retry: 2,
  });
}

// ---------------------------------------------------------------------------
// useProject — SELECT single project by id
// ---------------------------------------------------------------------------

export function useProject(id: string | undefined) {
  return useQuery<Project, Error>({
    queryKey: queryKeys.projects.detail(id),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('id', id!)
        .single();

      if (error) throw error;
      return mapRowToProject(data as ProjectRow);
    },
    enabled: !!id,
    staleTime: 30_000,
    retry: 2,
  });
}

// ---------------------------------------------------------------------------
// useCreateProject — INSERT mutation
// ---------------------------------------------------------------------------

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation<Project, Error, { name: string; description: string }>({
    mutationFn: async (variables) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('使用者未登入');

      const insertData: ProjectInsert = {
        name: variables.name,
        description: variables.description,
        status: 'in_progress',
        phase: 'Phase I',
        progress: 0,
        phase_progress: DEFAULT_PHASE_PROGRESS as unknown as Database['public']['Tables']['projects']['Insert']['phase_progress'],
        quick_stats: DEFAULT_QUICK_STATS as unknown as Database['public']['Tables']['projects']['Insert']['quick_stats'],
        gates_passed: 0,
        gates_total: 8,
        created_by: user.id,
      };

      const { data, error } = await supabase
        .from('projects')
        .insert(insertData)
        .select()
        .single();

      if (error) throw error;
      return mapRowToProject(data as ProjectRow);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
      toast.success('專案建立成功');
    },
    onError: (error) => {
      toast.error(`建立專案失敗：${error.message}`);
      console.error('[useCreateProject] failed:', error);
    },
  });
}

// ---------------------------------------------------------------------------
// useUpdateProject — UPDATE mutation
// ---------------------------------------------------------------------------

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation<Project, Error, Partial<ProjectRow> & { id: string }>({
    mutationFn: async ({ id, ...updateData }) => {
      const { data, error } = await supabase
        .from('projects')
        .update(updateData)
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;
      return mapRowToProject(data as ProjectRow);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(data.id) });
      toast.success('專案更新成功');
    },
    onError: (error) => {
      toast.error(`更新專案失敗：${error.message}`);
      console.error('[useUpdateProject] failed:', error);
    },
  });
}

// ---------------------------------------------------------------------------
// useDeleteProject — DELETE mutation
// ---------------------------------------------------------------------------

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const { error } = await supabase
        .from('projects')
        .delete()
        .eq('id', id);

      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
      toast.success('專案已刪除');
    },
    onError: (error) => {
      toast.error(`刪除專案失敗：${error.message}`);
      console.error('[useDeleteProject] failed:', error);
    },
  });
}

// ---------------------------------------------------------------------------
// useProjectStats — count queries for QuickStats
// ---------------------------------------------------------------------------

export function useProjectStats(projectId: string | undefined) {
  return useQuery<QuickStats, Error>({
    queryKey: queryKeys.projects.stats(projectId),
    queryFn: async () => {
      const id = projectId!;

      const [
        contradictions,
        assumptions,
        alternatives,
        risks,
        experiments,
        evidenceItems,
      ] = await Promise.all([
        supabase.from('contradictions').select('id', { count: 'exact', head: true }).eq('project_id', id),
        supabase.from('assumptions').select('id', { count: 'exact', head: true }).eq('project_id', id),
        supabase.from('alternatives').select('id', { count: 'exact', head: true }).eq('project_id', id),
        supabase.from('risks').select('id', { count: 'exact', head: true }).eq('project_id', id),
        supabase.from('experiments').select('id', { count: 'exact', head: true }).eq('project_id', id),
        supabase.from('evidence_matrix').select('id', { count: 'exact', head: true }).eq('project_id', id),
      ]);

      // Check for errors
      const results = [contradictions, assumptions, alternatives, risks, experiments, evidenceItems];
      for (const r of results) {
        if (r.error) throw r.error;
      }

      return {
        contradictions_count: contradictions.count ?? 0,
        assumptions_count: assumptions.count ?? 0,
        alternatives_count: alternatives.count ?? 0,
        risks_count: risks.count ?? 0,
        experiments_count: experiments.count ?? 0,
        evidence_items_count: evidenceItems.count ?? 0,
      };
    },
    enabled: !!projectId,
    staleTime: 30_000,
    retry: 2,
  });
}
