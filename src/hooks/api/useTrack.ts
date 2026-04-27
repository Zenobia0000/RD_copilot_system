/**
 * Track page API hooks
 *
 * Provides hooks for the Track Kanban board (assumptions in Kanban view)
 * and Unknown Factors management.
 *
 * The Track page reads from the same `assumptions` table as the Assumption Ledger,
 * but maps to a different frontend type (TrackAssumption) with Kanban-specific fields.
 *
 * Unknown Factors: Persisted to Supabase `unknown_factors` table.
 */

import { useCallback, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type {
  TrackAssumption,
  VerificationStatus,
  RiskLevel,
  AssumptionSource,
  UnknownFactor,
  Experiment,
  ExperimentStatus,
} from '@/types/track';
import type { Database } from '@/integrations/supabase/types';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

type AssumptionRow = Database['public']['Tables']['assumptions']['Row'];
type AssumptionInsert = Database['public']['Tables']['assumptions']['Insert'];
type AssumptionUpdate = Database['public']['Tables']['assumptions']['Update'];
type ExperimentRow = Database['public']['Tables']['experiments']['Row'];

// ---------------------------------------------------------------------------
// Mappers: DB Row -> Track Frontend Types
// ---------------------------------------------------------------------------

/**
 * Map an assumptions DB row to the Track-specific TrackAssumption type.
 *
 * Key differences from AssumptionLedger's Assumption type:
 * - `verificationStatus` maps from `verification_stage` (Track uses it as Kanban column)
 * - `riskLevel` derived from `worst_severity`
 * - `experimentCount` is 0 by default (enriched separately)
 * - `source` maps from `source_type`
 */
function mapRowToTrackAssumption(row: AssumptionRow, experimentCount: number = 0): TrackAssumption {
  // Map verification_stage to VerificationStatus
  const stageToStatus: Record<string, VerificationStatus> = {
    unplanned: 'unverified',
    planned: 'unverified',
    in_progress: 'verifying',
    completed: 'verified',
    negated: 'negated',
  };

  // Map worst_severity to RiskLevel
  const severityToRisk: Record<string, RiskLevel> = {
    low: 'L',
    medium: 'M',
    high: 'H',
    critical: 'H*',
  };

  // Also accept direct status values (for rows updated via Track)
  const directStatus: Record<string, VerificationStatus> = {
    unverified: 'unverified',
    verifying: 'verifying',
    verified: 'verified',
    negated: 'negated',
  };

  const verificationStatus: VerificationStatus =
    directStatus[row.status] ??
    stageToStatus[row.verification_stage] ??
    'unverified';

  return {
    id: row.id,
    assumptionCode: row.code,
    description: row.content,
    riskLevel: severityToRisk[row.worst_severity ?? ''] ?? null,
    verificationStatus,
    experimentCount,
    source: (row.source_type as AssumptionSource) ?? 'manual',
    linkedContradictionId: null, // TODO: join with contradictions if needed
    aiChallenge: null, // TODO: store in a dedicated column or separate table
    worstConsequence: row.worst_consequence ?? '',
    verificationCost: row.validation_cost ?? '',
    verificationDuration: row.estimated_days ? `${row.estimated_days} days` : '',
    sourceArtifactId: row.source ?? null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function mapExperimentRow(row: ExperimentRow): Experiment {
  return {
    id: row.id,
    name: row.name,
    status: row.status as ExperimentStatus,
    result: row.result ?? null,
    createdAt: row.created_at,
  };
}

// ---------------------------------------------------------------------------
// useTrackAssumptions — SELECT assumptions by project_id (Track/Kanban view)
// ---------------------------------------------------------------------------

export function useTrackAssumptions(projectId: string | undefined) {
  const assumptionsQuery = useSupabaseQuery<AssumptionRow[]>({
    table: 'assumptions',
    queryKey: queryKeys.track.assumptions(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  const expCountQuery = useSupabaseQuery<{ assumption_code: string }[]>({
    table: 'experiments',
    queryKey: [...queryKeys.track.assumptions(projectId), 'exp_counts'],
    select: 'assumption_code',
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq', value: projectId }]
      : [],
    enabled: !!projectId,
  });

  const expCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    if (expCountQuery.data) {
      for (const row of expCountQuery.data) {
        counts[row.assumption_code] = (counts[row.assumption_code] ?? 0) + 1;
      }
    }
    return counts;
  }, [expCountQuery.data]);

  const isLoading = assumptionsQuery.isLoading || expCountQuery.isLoading;

  return {
    ...assumptionsQuery,
    isLoading,
    data: isLoading
      ? []
      : assumptionsQuery.data?.map((row) =>
          mapRowToTrackAssumption(row, expCounts[row.code] ?? 0)
        ) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useUpdateTrackAssumptionStatus — UPDATE verification status (Kanban drag)
// ---------------------------------------------------------------------------

export function useUpdateTrackAssumptionStatus(projectId: string | undefined) {
  const mutation = useSupabaseMutation<
    AssumptionRow,
    AssumptionUpdate & { id: string }
  >({
    table: 'assumptions',
    type: 'update',
    invalidateKeys: [
      queryKeys.track.assumptions(projectId),
      queryKeys.assumptions.byProject(projectId),
    ],
    successMessage: false,
  });

  return {
    ...mutation,
    /** Update verification status by assumption id */
    mutate: (id: string, newStatus: VerificationStatus) => {
      // Map Track VerificationStatus back to DB fields
      const statusToStage: Record<VerificationStatus, string> = {
        unverified: 'unplanned',
        verifying: 'in_progress',
        verified: 'completed',
        negated: 'negated',
      };
      mutation.mutate({
        id,
        status: newStatus,
        verification_stage: statusToStage[newStatus],
        updated_at: new Date().toISOString(),
      });
    },
    mutateAsync: async (id: string, newStatus: VerificationStatus) => {
      const statusToStage: Record<VerificationStatus, string> = {
        unverified: 'unplanned',
        verifying: 'in_progress',
        verified: 'completed',
        negated: 'negated',
      };
      return mutation.mutateAsync({
        id,
        status: newStatus,
        verification_stage: statusToStage[newStatus],
        updated_at: new Date().toISOString(),
      });
    },
  };
}

// ---------------------------------------------------------------------------
// useCreateTrackAssumption — INSERT new assumption (manual add from Kanban)
// ---------------------------------------------------------------------------

export function useCreateTrackAssumption(projectId: string | undefined) {
  return useSupabaseMutation<AssumptionRow, AssumptionInsert>({
    table: 'assumptions',
    type: 'insert',
    invalidateKeys: [
      queryKeys.track.assumptions(projectId),
      queryKeys.assumptions.byProject(projectId),
    ],
    successMessage: '假設已新增',
  });
}

// ---------------------------------------------------------------------------
// useDeleteTrackAssumption — DELETE assumption by id
// ---------------------------------------------------------------------------

export function useDeleteTrackAssumption(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const { error } = await supabase
        .from('assumptions')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.track.assumptions(projectId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.assumptions.byProject(projectId),
      });
      toast.success('假設已刪除');
    },
    onError: (error) => {
      toast.error(`刪除假設失敗：${error.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Unknown Factors — localStorage-based (no DB table yet)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Unknown Factors — Supabase-backed
// ---------------------------------------------------------------------------

interface UnknownFactorRow {
  id: string;
  project_id: string;
  unknown_code: string;
  description: string;
  impact: string;
  status: string;
  note: string | null;
  linked_assumption_id: string | null;
  created_at: string;
  updated_at: string;
}

type UnknownFactorInsert = Omit<UnknownFactorRow, 'id' | 'created_at' | 'updated_at'>;

function mapUnknownFactorRow(r: UnknownFactorRow): UnknownFactor {
  return {
    id: r.id,
    unknownCode: r.unknown_code,
    description: r.description,
    impact: r.impact as UnknownFactor['impact'],
    status: r.status as UnknownFactor['status'],
    note: r.note,
    linkedAssumptionId: r.linked_assumption_id,
    createdAt: r.created_at,
  };
}

export function useUnknownFactors(projectId: string | undefined) {
  const result = useSupabaseQuery<UnknownFactorRow[]>({
    table: 'unknown_factors',
    queryKey: queryKeys.track.unknownFactors(projectId),
    filters: projectId ? [{ column: 'project_id', operator: 'eq', value: projectId }] : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });
  return {
    data: result.data?.map(mapUnknownFactorRow) ?? [],
    isLoading: result.isLoading,
    isError: result.isError,
    refetch: result.refetch,
  };
}

export function useCreateUnknownFactor(projectId: string | undefined) {
  return useSupabaseMutation<UnknownFactorRow, UnknownFactorInsert>({
    table: 'unknown_factors',
    type: 'insert',
    invalidateKeys: [queryKeys.track.unknownFactors(projectId)],
    successMessage: '未知因素已新增',
  });
}

export function useUpdateUnknownFactor(projectId: string | undefined) {
  return useSupabaseMutation<UnknownFactorRow, { id: string; status?: string; note?: string; linked_assumption_id?: string | null }>({
    table: 'unknown_factors',
    type: 'update',
    invalidateKeys: [queryKeys.track.unknownFactors(projectId)],
  });
}

export function useSaveUnknownFactors(_projectId: string | undefined) {
  // Bulk save no longer needed with Supabase — individual mutations handle it.
  // Keep interface for backward compat with Track.tsx onUpdateFactors.
  return { mutate: (_factors: UnknownFactor[]) => {}, isPending: false };
}

// ---------------------------------------------------------------------------
// useConvertUnknownToAssumption — Convert unknown factor to assumption
// ---------------------------------------------------------------------------

export function useConvertUnknownToAssumption(projectId: string | undefined) {
  const queryClient = useQueryClient();

  const insertMutation = useSupabaseMutation<AssumptionRow, AssumptionInsert>({
    table: 'assumptions',
    type: 'insert',
    invalidateKeys: [
      queryKeys.track.assumptions(projectId),
      queryKeys.assumptions.byProject(projectId),
    ],
    successMessage: '已轉化為假設',
  });

  const convert = useCallback(
    async (factor: UnknownFactor, assumptionCount: number) => {
      if (!projectId) return;

      const code = `A-${String(assumptionCount + 1).padStart(3, '0')}`;
      const riskMap: Record<string, string> = {
        high: 'high',
        medium: 'medium',
        low: 'low',
      };

      const insertData: AssumptionInsert = {
        project_id: projectId,
        code,
        content: factor.description,
        source_type: 'unknown_convert',
        worst_severity: riskMap[factor.impact] ?? 'medium',
        status: 'unverified',
        verification_stage: 'unplanned',
      };

      const result = await insertMutation.mutateAsync(insertData);

      // Update the unknown factor in DB to mark as converted
      await supabase
        .from('unknown_factors')
        .update({ status: 'converted', linked_assumption_id: result.id })
        .eq('id', factor.id);
      queryClient.invalidateQueries({ queryKey: queryKeys.track.unknownFactors(projectId) });

      return result;
    },
    [projectId, insertMutation],
  );

  return {
    convert,
    isPending: insertMutation.isPending,
  };
}

// ---------------------------------------------------------------------------
// useTrackExperiments — SELECT experiments by assumption_code
// ---------------------------------------------------------------------------

export function useTrackExperiments(assumptionCode: string | undefined, projectId: string | undefined) {
  const query = useSupabaseQuery<ExperimentRow[]>({
    table: 'experiments',
    queryKey: queryKeys.experiments.byAssumptionCode(projectId, assumptionCode),
    filters: assumptionCode && projectId
      ? [
          { column: 'assumption_code', operator: 'eq', value: assumptionCode },
          { column: 'project_id', operator: 'eq', value: projectId },
        ]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!assumptionCode && !!projectId,
  });

  return {
    ...query,
    data: query.data?.map(mapExperimentRow) ?? [],
  };
}

// ---------------------------------------------------------------------------
// useCreateTrackExperiment and useUpdateTrackExperiment and useDeleteTrackExperiment — CREATE and UPDATE and DELETE experiment by id
// ---------------------------------------------------------------------------

import { useMutation } from '@tanstack/react-query';

export function useCreateTrackExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      projectId: string;
      assumptionCode: string;
      name: string;
      status: ExperimentStatus;
    }) => {
      const { data: { user } } = await supabase.auth.getUser();
      const { data, error } = await supabase
        .from('experiments')
        .insert({
          project_id: params.projectId,
          user_id: user?.id,
          assumption_code: params.assumptionCode,
          name: params.name,
          status: params.status,
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.experiments.byAssumptionCode(variables.projectId, variables.assumptionCode),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.track.assumptions(variables.projectId),
      });
    },
    onError: () => {
      toast.error('新增實驗失敗');
    },
  });
}

export function useUpdateTrackExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      id: string;
      assumptionCode: string;
      projectId?: string;
      status?: ExperimentStatus;
      result?: string | null;
    }) => {
      const updates: Record<string, unknown> = {};
      if (params.status !== undefined) updates.status = params.status;
      if (params.result !== undefined) updates.result = params.result;

      const { data, error } = await supabase
        .from('experiments')
        .update(updates)
        .eq('id', params.id)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.experiments.byAssumptionCode(variables.projectId, variables.assumptionCode),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.track.assumptions(variables.projectId),
      });
    },
    onError: () => {
      toast.error('更新實驗失敗');
    },
  });
}

export function useDeleteTrackExperiment() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { id: string; assumptionCode: string; projectId: string }>({
    mutationFn: async ({ id }) => {
      const { error } = await supabase
        .from('experiments')
        .delete()
        .eq('id', id);

      if (error) throw error;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.experiments.byAssumptionCode(variables.projectId, variables.assumptionCode),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.track.assumptions(variables.projectId),
      });
      toast.success('實驗已刪除');
    },
    onError: (error) => {
      toast.error(`刪除實驗失敗：${error.message}`);
    },
  });
}
