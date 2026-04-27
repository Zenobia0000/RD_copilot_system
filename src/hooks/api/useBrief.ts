/**
 * API hooks for Brief, Constraints, and KPIs tables.
 *
 * Provides CRUD operations backed by Supabase + React Query,
 * with snake_case (DB) → camelCase (frontend) mapping handled at this layer.
 */

import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type { Tables, TablesInsert, TablesUpdate } from '@/integrations/supabase/types';
import type { TaskDefinition5W1H } from '@/types/taskDefinition';

// ---------------------------------------------------------------------------
// DB row types (snake_case)
// ---------------------------------------------------------------------------
export type BriefRow = Tables<'briefs'>;
export type ConstraintRow = Tables<'constraints'>;
export type KpiRow = Tables<'kpis'>;

// ---------------------------------------------------------------------------
// Frontend mapped types (kept compatible with existing UI types)
// ---------------------------------------------------------------------------
export interface BriefFrontend {
  id: string;
  projectId: string;
  mission: string;
  taskDefinition5w1h: TaskDefinition5W1H | null;
  createdAt: string;
  updatedAt: string;
}

export interface ConstraintFrontend {
  id: string;
  projectId: string;
  constraintCode: string;
  description: string;
  source: string;
  type: string;
  feasibility: string | null;
  createdAt: string;
}

export interface KpiFrontend {
  id: string;
  projectId: string;
  kpiName: string;
  targetValue: string;
  unit: string;
  measurementMethod: string;
  currentValue: string | null;
  currentStatus: string;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Mappers: DB → Frontend
// ---------------------------------------------------------------------------
function mapBrief(row: BriefRow): BriefFrontend {
  return {
    id: row.id,
    projectId: row.project_id,
    mission: row.mission ?? '',
    taskDefinition5w1h: row.task_definition_5w1h as TaskDefinition5W1H | null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function mapConstraint(row: ConstraintRow): ConstraintFrontend {
  return {
    id: row.id,
    projectId: row.project_id,
    constraintCode: row.constraint_code,
    description: row.description,
    source: row.source ?? '',
    type: row.type,
    feasibility: row.feasibility,
    createdAt: row.created_at,
  };
}

function mapKpi(row: KpiRow): KpiFrontend {
  return {
    id: row.id,
    projectId: row.project_id,
    kpiName: row.kpi_name,
    targetValue: row.target_value ?? '',
    unit: row.unit ?? '',
    measurementMethod: row.measurement_method ?? '',
    currentValue: row.current_value ?? null,
    currentStatus: row.current_status ?? 'unknown',
    createdAt: row.created_at,
  };
}

// ---------------------------------------------------------------------------
// Brief hooks
// ---------------------------------------------------------------------------

/** Fetch a single brief by project_id. Returns null when not found. */
export function useBrief(projectId: string | undefined) {
  const query = useSupabaseQuery<BriefRow>({
    table: 'briefs',
    queryKey: queryKeys.briefs.detail(projectId),
    filters: [{ column: 'project_id', operator: 'eq', value: projectId }],
    single: true,
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data ? mapBrief(query.data) : undefined,
  };
}

/** Upsert a brief (briefs table has UNIQUE(project_id)). */
export function useUpsertBrief() {
  return useSupabaseMutation<BriefRow, TablesInsert<'briefs'>>({
    table: 'briefs',
    type: 'upsert',
    onConflict: 'project_id',
    invalidateKeys: [queryKeys.briefs.all],
    successMessage: 'Brief 已儲存',
  });
}

// ---------------------------------------------------------------------------
// Constraint hooks
// ---------------------------------------------------------------------------

/** Fetch all constraints for a project. */
export function useConstraints(projectId: string | undefined) {
  const query = useSupabaseQuery<ConstraintRow[]>({
    table: 'constraints',
    queryKey: queryKeys.constraints.byProject(projectId),
    filters: [{ column: 'project_id', operator: 'eq', value: projectId }],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapConstraint),
  };
}

/** Insert a new constraint. */
export function useCreateConstraint() {
  return useSupabaseMutation<ConstraintRow, TablesInsert<'constraints'>>({
    table: 'constraints',
    type: 'insert',
    invalidateKeys: [queryKeys.constraints.all],
    successMessage: '約束已新增',
  });
}

/** Update an existing constraint. */
export function useUpdateConstraint() {
  return useSupabaseMutation<ConstraintRow, TablesUpdate<'constraints'> & { id: string }>({
    table: 'constraints',
    type: 'update',
    invalidateKeys: [queryKeys.constraints.all],
    successMessage: '約束已更新',
  });
}

/** Delete a constraint by id. */
export function useDeleteConstraint() {
  return useSupabaseMutation<ConstraintRow, { id: string }>({
    table: 'constraints',
    type: 'delete',
    invalidateKeys: [queryKeys.constraints.all],
    successMessage: '約束已刪除',
  });
}

// ---------------------------------------------------------------------------
// KPI hooks
// ---------------------------------------------------------------------------

/** Fetch all KPIs for a project. */
export function useKpis(projectId: string | undefined) {
  const query = useSupabaseQuery<KpiRow[]>({
    table: 'kpis',
    queryKey: queryKeys.kpis.byProject(projectId),
    filters: [{ column: 'project_id', operator: 'eq', value: projectId }],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapKpi),
  };
}

/** Insert a new KPI. */
export function useCreateKpi() {
  return useSupabaseMutation<KpiRow, TablesInsert<'kpis'>>({
    table: 'kpis',
    type: 'insert',
    invalidateKeys: [queryKeys.kpis.all],
    successMessage: 'KPI 已新增',
  });
}

/** Update an existing KPI. */
export function useUpdateKpi() {
  return useSupabaseMutation<KpiRow, TablesUpdate<'kpis'> & { id: string }>({
    table: 'kpis',
    type: 'update',
    invalidateKeys: [queryKeys.kpis.all],
    successMessage: 'KPI 已更新',
  });
}

/** Delete a KPI by id. */
export function useDeleteKpi() {
  return useSupabaseMutation<KpiRow, { id: string }>({
    table: 'kpis',
    type: 'delete',
    invalidateKeys: [queryKeys.kpis.all],
    successMessage: 'KPI 已刪除',
  });
}
