/**
 * Assumption Management API hooks
 *
 * Provides CRUD hooks for assumptions, CLD nodes/edges, and related data.
 * Maps between snake_case DB columns and camelCase frontend types.
 */

import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type {
  Assumption,
  AssumptionStatus,
  VerificationStage,
  AssumptionFormValues,
  CLDNode,
  CLDEdge,
  LinkedContradiction,
  SocraticFeedback,
  ConvergenceImpact,
} from '@/types/assumption';
import type { Database } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

type AssumptionRow = Database['public']['Tables']['assumptions']['Row'];
type AssumptionInsert = Database['public']['Tables']['assumptions']['Insert'];
type AssumptionUpdate = Database['public']['Tables']['assumptions']['Update'];
type CldNodeRow = Database['public']['Tables']['cld_nodes']['Row'];
type CldEdgeRow = Database['public']['Tables']['cld_edges']['Row'];
type ContradictionRow = Database['public']['Tables']['contradictions']['Row'];

// ---------------------------------------------------------------------------
// Mappers: DB Row <-> Frontend Type
// ---------------------------------------------------------------------------

function mapRowToAssumption(row: AssumptionRow): Assumption {
  return {
    id: row.id,
    code: row.code,
    content: row.content,
    source: row.source ?? '',
    sourceType: (row.source_type as Assumption['sourceType']) ?? 'manual',
    worstConsequence: row.worst_consequence ?? '',
    worstSeverity: (row.worst_severity as Assumption['worstSeverity']) ?? 'medium',
    minValidation: row.min_validation ?? '',
    validationCost: row.validation_cost ?? '',
    validationMethod: row.validation_method ?? undefined,
    estimatedDays: row.estimated_days ?? undefined,
    status: row.status as AssumptionStatus,
    verificationStage: row.verification_stage as VerificationStage,
    impactScope: row.impact_scope ? JSON.parse(row.impact_scope) : [],
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function mapAssumptionToInsert(
  data: AssumptionFormValues & { projectId: string; code: string },
): AssumptionInsert {
  return {
    project_id: data.projectId,
    code: data.code,
    content: data.content,
    source: data.source,
    source_type: 'manual',
    worst_consequence: data.worstConsequence,
    worst_severity: data.worstSeverity,
    min_validation: data.minValidation,
    validation_cost: data.validationCost,
    validation_method: data.validationMethod ?? null,
    estimated_days: data.estimatedDays ?? null,
    status: 'pending',
    verification_stage: 'unplanned',
    impact_scope: JSON.stringify(data.impactScope ?? []),
  };
}

function mapAssumptionToUpdate(
  id: string,
  data: Partial<AssumptionFormValues> & {
    status?: AssumptionStatus;
    verificationStage?: VerificationStage;
  },
): AssumptionUpdate & { id: string } {
  const update: AssumptionUpdate & { id: string } = { id };

  if (data.content !== undefined) update.content = data.content;
  if (data.source !== undefined) update.source = data.source;
  if (data.worstConsequence !== undefined) update.worst_consequence = data.worstConsequence;
  if (data.worstSeverity !== undefined) update.worst_severity = data.worstSeverity;
  if (data.minValidation !== undefined) update.min_validation = data.minValidation;
  if (data.validationCost !== undefined) update.validation_cost = data.validationCost;
  if (data.validationMethod !== undefined) update.validation_method = data.validationMethod ?? null;
  if (data.estimatedDays !== undefined) update.estimated_days = data.estimatedDays ?? null;
  if (data.impactScope !== undefined) update.impact_scope = JSON.stringify(data.impactScope);
  if (data.status !== undefined) update.status = data.status;
  if (data.verificationStage !== undefined) update.verification_stage = data.verificationStage;

  update.updated_at = new Date().toISOString();

  return update;
}

// ---------------------------------------------------------------------------
// CLD Mappers
// ---------------------------------------------------------------------------

function mapRowToCldNode(row: CldNodeRow): CLDNode {
  return {
    id: row.id,
    label: row.label,
    x: row.x,
    y: row.y,
    type: row.node_type as CLDNode['type'],
    assumptionId: row.assumption_id ?? undefined,
    isLeverage: row.is_leverage,
  };
}

function mapRowToCldEdge(row: CldEdgeRow): CLDEdge {
  return {
    id: row.id,
    from: row.from_node,
    to: row.to_node,
    polarity: row.polarity as CLDEdge['polarity'],
  };
}

// ---------------------------------------------------------------------------
// Contradiction Mapper
// ---------------------------------------------------------------------------

function mapRowToLinkedContradiction(row: ContradictionRow): LinkedContradiction {
  return {
    id: row.id,
    description: row.natural_description ?? row.engineering_statement ?? '',
    severity: row.severity as LinkedContradiction['severity'],
    resolved: row.resolved,
  };
}

// ---------------------------------------------------------------------------
// useAssumptions — SELECT all assumptions by project_id
// ---------------------------------------------------------------------------

export function useAssumptions(projectId: string | undefined) {
  const query = useSupabaseQuery<AssumptionRow[]>({
    table: 'assumptions',
    queryKey: queryKeys.assumptions.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapRowToAssumption) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useCreateAssumption — INSERT assumption
// ---------------------------------------------------------------------------

export function useCreateAssumption(projectId: string | undefined) {
  return useSupabaseMutation<
    AssumptionRow,
    AssumptionFormValues & { projectId: string; code: string }
  >({
    table: 'assumptions',
    type: 'insert',
    invalidateKeys: [
      queryKeys.assumptions.byProject(projectId),
      queryKeys.assumptions.all,
    ],
    successMessage: '假設已新增',
    mutationOptions: {
      // Transform camelCase form values to snake_case before sending
      // The useSupabaseMutation sends variables directly, so we intercept here
    },
  });
}

// We need a wrapper that maps before calling mutate
export function useCreateAssumptionMapped(projectId: string | undefined) {
  const mutation = useSupabaseMutation<AssumptionRow, AssumptionInsert>({
    table: 'assumptions',
    type: 'insert',
    invalidateKeys: [
      queryKeys.assumptions.byProject(projectId),
      queryKeys.assumptions.all,
    ],
    successMessage: '假設已新增',
  });

  return {
    ...mutation,
    mutate: (data: AssumptionFormValues & { projectId: string; code: string }) => {
      mutation.mutate(mapAssumptionToInsert(data) as unknown as AssumptionInsert);
    },
    mutateAsync: async (data: AssumptionFormValues & { projectId: string; code: string }) => {
      return mutation.mutateAsync(mapAssumptionToInsert(data) as unknown as AssumptionInsert);
    },
  };
}

// ---------------------------------------------------------------------------
// useUpdateAssumption — UPDATE assumption
// ---------------------------------------------------------------------------

export function useUpdateAssumption(projectId: string | undefined) {
  const mutation = useSupabaseMutation<
    AssumptionRow,
    AssumptionUpdate & { id: string }
  >({
    table: 'assumptions',
    type: 'update',
    invalidateKeys: [
      queryKeys.assumptions.byProject(projectId),
      queryKeys.assumptions.all,
    ],
    successMessage: false,
  });

  return {
    ...mutation,
    /**
     * Update with camelCase partial data.
     * Internally maps to snake_case DB columns.
     */
    mutate: (
      id: string,
      data: Partial<AssumptionFormValues> & {
        status?: AssumptionStatus;
        verificationStage?: VerificationStage;
      },
    ) => {
      mutation.mutate(mapAssumptionToUpdate(id, data));
    },
    mutateAsync: async (
      id: string,
      data: Partial<AssumptionFormValues> & {
        status?: AssumptionStatus;
        verificationStage?: VerificationStage;
      },
    ) => {
      return mutation.mutateAsync(mapAssumptionToUpdate(id, data));
    },
  };
}

// ---------------------------------------------------------------------------
// useDeleteAssumption — DELETE assumption
// ---------------------------------------------------------------------------

export function useDeleteAssumption(projectId: string | undefined) {
  return useSupabaseMutation<unknown, { id: string }>({
    table: 'assumptions',
    type: 'delete',
    invalidateKeys: [
      queryKeys.assumptions.byProject(projectId),
      queryKeys.assumptions.all,
    ],
    successMessage: '假設已刪除',
  });
}

// ---------------------------------------------------------------------------
// useCldNodes — SELECT CLD nodes by project_id
// ---------------------------------------------------------------------------

export function useCldNodes(projectId: string | undefined) {
  const query = useSupabaseQuery<CldNodeRow[]>({
    table: 'cld_nodes',
    queryKey: queryKeys.cld_nodes.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapRowToCldNode) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useCldEdges — SELECT CLD edges by project_id
// ---------------------------------------------------------------------------

export function useCldEdges(projectId: string | undefined) {
  const query = useSupabaseQuery<CldEdgeRow[]>({
    table: 'cld_edges',
    queryKey: queryKeys.cld_edges.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapRowToCldEdge) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useLinkedContradictions — SELECT contradictions by project_id
// ---------------------------------------------------------------------------

export function useLinkedContradictions(projectId: string | undefined) {
  const query = useSupabaseQuery<ContradictionRow[]>({
    table: 'contradictions',
    queryKey: queryKeys.contradictions.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    enabled: !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapRowToLinkedContradiction) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useSocraticFeedback — TODO: No dedicated DB table yet
// ---------------------------------------------------------------------------

/**
 * TODO: Create a `socratic_feedback` table in Supabase with columns:
 * id, assumption_id, type ('causal_inquiry' | 'assumption_challenge'),
 * content, timestamp, created_at
 *
 * For now, returns an empty array.
 */
export function useSocraticFeedback(_assumptionId: string | null) {
  return {
    data: [] as SocraticFeedback[],
    isLoading: false,
    isError: false,
  };
}

// ---------------------------------------------------------------------------
// useConvergenceImpact — TODO: No dedicated DB table yet
// ---------------------------------------------------------------------------

/**
 * TODO: Create a `convergence_impacts` table in Supabase with columns:
 * id, assumption_id, affected_routes, severity, message, created_at
 *
 * For now, returns null.
 */
export function useConvergenceImpact(_assumptionId: string | null) {
  return {
    data: null as ConvergenceImpact | null,
    isLoading: false,
    isError: false,
  };
}
