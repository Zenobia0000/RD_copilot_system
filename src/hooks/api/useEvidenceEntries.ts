/**
 * Evidence Entries API hooks
 *
 * CRUD operations for structured measurement logs + auto-propagation logic
 * that updates KPI status, evidence_matrix level, and assumption verification_stage.
 */

import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys } from './useQueryConfig';
import { toast } from 'sonner';
import type { EvidenceEntry } from '@/types/evidenceEntry';
import type { Database } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// DB row types
// ---------------------------------------------------------------------------

type EvidenceEntryRow = Database['public']['Tables']['evidence_entries']['Row'];
type EvidenceEntryInsert = Database['public']['Tables']['evidence_entries']['Insert'];

// ---------------------------------------------------------------------------
// Row <-> Frontend mapping
// ---------------------------------------------------------------------------

function mapRow(row: EvidenceEntryRow): EvidenceEntry {
  return {
    id: row.id,
    projectId: row.project_id,
    userId: row.user_id,
    title: row.title,
    measuredValue: row.measured_value,
    unit: row.unit ?? '',
    evidenceLevel: row.evidence_level as EvidenceEntry['evidenceLevel'],
    method: row.method ?? '',
    notes: row.notes ?? '',
    measuredAt: row.measured_at ?? '',
    kpiId: row.kpi_id,
    experimentId: row.experiment_id,
    linkedAssumptionCodes: row.linked_assumption_codes ?? [],
    linkedMustIds: row.linked_must_ids ?? [],
    attachmentId: row.attachment_id,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

// ---------------------------------------------------------------------------
// KPI status derivation
// ---------------------------------------------------------------------------

function deriveKpiStatus(
  measuredValue: string,
  targetValue: string,
): 'on_track' | 'at_risk' | 'off_track' | 'unknown' {
  const measured = parseFloat(measuredValue);
  const target = parseFloat(targetValue);

  if (isNaN(measured) || isNaN(target) || target === 0) {
    return measuredValue.trim() === targetValue.trim() ? 'on_track' : 'unknown';
  }

  const ratio = measured / target;

  if (ratio >= 1.0) return 'on_track';
  if (ratio >= 0.9) return 'at_risk';
  return 'off_track';
}

// ---------------------------------------------------------------------------
// Evidence level ranking
// ---------------------------------------------------------------------------

const EVIDENCE_LEVEL_RANK: Record<string, number> = {
  E0: 0, E1: 1, E2: 2, E3: 3, E4: 4,
};

// ---------------------------------------------------------------------------
// Auto-propagation after evidence entry save
// ---------------------------------------------------------------------------

async function propagateEvidence(entry: EvidenceEntryRow) {
  const promises: Promise<unknown>[] = [];

  if (entry.kpi_id) {
    const propagateKpi = async () => {
      const { data: kpi } = await supabase
        .from('kpis')
        .select('target_value')
        .eq('id', entry.kpi_id!)
        .single();

      if (kpi) {
        const status = deriveKpiStatus(entry.measured_value, kpi.target_value ?? '');
        await supabase
          .from('kpis')
          .update({
            current_value: entry.measured_value,
            current_status: status,
          })
          .eq('id', entry.kpi_id!);
      }
    };
    promises.push(propagateKpi());
  }

  if (entry.linked_assumption_codes.length > 0) {
    const propagateMatrix = async () => {
      for (const code of entry.linked_assumption_codes) {
        const { data: entries } = await supabase
          .from('evidence_entries')
          .select('evidence_level')
          .contains('linked_assumption_codes', [code])
          .eq('project_id', entry.project_id);

        if (entries && entries.length > 0) {
          const maxLevel = entries.reduce((max, e) => {
            const rank = EVIDENCE_LEVEL_RANK[e.evidence_level] ?? 0;
            return rank > (EVIDENCE_LEVEL_RANK[max] ?? 0) ? e.evidence_level : max;
          }, 'E0');

          await supabase
            .from('evidence_matrix')
            .update({ current_level: maxLevel })
            .eq('project_id', entry.project_id)
            .eq('assumption_code', code);

          if ((EVIDENCE_LEVEL_RANK[maxLevel] ?? 0) >= 3) {
            await supabase
              .from('assumptions')
              .update({ verification_stage: 'completed' })
              .eq('project_id', entry.project_id)
              .eq('assumption_code', code);
          }
        }
      }
    };
    promises.push(propagateMatrix());
  }

  await Promise.all(promises);
}

// ---------------------------------------------------------------------------
// Propagation result type — carries a flag so onSuccess can decide which toast
// ---------------------------------------------------------------------------

type WithPropagationFlag<T> = T & { _propagationFailed?: boolean };

// ---------------------------------------------------------------------------
// useEvidenceEntries — SELECT by project
// ---------------------------------------------------------------------------

export function useEvidenceEntries(projectId: string | undefined) {
  return useQuery<EvidenceEntry[], Error>({
    queryKey: queryKeys.evidence_entries.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('evidence_entries')
        .select('*')
        .eq('project_id', projectId!)
        .order('measured_at', { ascending: false });

      if (error) throw error;
      return (data as EvidenceEntryRow[]).map(mapRow);
    },
    enabled: !!projectId,
    staleTime: 30_000,
    retry: 2,
  });
}

// ---------------------------------------------------------------------------
// useEvidenceEntriesByKpi — SELECT by kpi_id
// ---------------------------------------------------------------------------

export function useEvidenceEntriesByKpi(kpiId: string | undefined) {
  return useQuery<EvidenceEntry[], Error>({
    queryKey: queryKeys.evidence_entries.byKpi(kpiId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('evidence_entries')
        .select('*')
        .eq('kpi_id', kpiId!)
        .order('measured_at', { ascending: false });

      if (error) throw error;
      return (data as EvidenceEntryRow[]).map(mapRow);
    },
    enabled: !!kpiId,
    staleTime: 30_000,
    retry: 2,
  });
}

// ---------------------------------------------------------------------------
// useCreateEvidenceEntry — INSERT + auto-propagation
// ---------------------------------------------------------------------------

export interface CreateEvidenceEntryInput {
  projectId: string;
  title: string;
  measuredValue: string;
  unit?: string;
  evidenceLevel: string;
  method?: string;
  notes?: string;
  measuredAt?: string;
  kpiId?: string | null;
  experimentId?: string | null;
  linkedAssumptionCodes?: string[];
  linkedMustIds?: string[];
}

export function useCreateEvidenceEntry() {
  const queryClient = useQueryClient();

  return useMutation<WithPropagationFlag<EvidenceEntry>, Error, CreateEvidenceEntryInput>({
    mutationFn: async (input) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('使用者未登入');

      const insertData: EvidenceEntryInsert = {
        project_id: input.projectId,
        user_id: user.id,
        title: input.title,
        measured_value: input.measuredValue,
        unit: input.unit ?? '',
        evidence_level: input.evidenceLevel,
        method: input.method ?? '',
        notes: input.notes ?? '',
        measured_at: input.measuredAt ?? new Date().toISOString(),
        kpi_id: input.kpiId ?? null,
        experiment_id: input.experimentId ?? null,
        linked_assumption_codes: input.linkedAssumptionCodes ?? [],
        linked_must_ids: input.linkedMustIds ?? [],
      };

      const { data, error } = await supabase
        .from('evidence_entries')
        .insert(insertData)
        .select()
        .single();

      if (error) throw error;

      let propagationFailed = false;
      try {
        await propagateEvidence(data as EvidenceEntryRow);
      } catch (propagationError) {
        console.error(
          '[useCreateEvidenceEntry] propagation failed (entry saved, related data may be stale):',
          propagationError,
        );
        propagationFailed = true;
      }

      return { ...mapRow(data as EvidenceEntryRow), _propagationFailed: propagationFailed };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_entries.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.kpis.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_matrix.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.track.assumptions(data.projectId) });
      if (data.kpiId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.evidence_entries.byKpi(data.kpiId) });
      }
      if (data._propagationFailed) {
        toast.warning('證據已儲存，但相關 KPI / 矩陣同步失敗，請手動重新整理');
      } else {
        toast.success('證據已登錄');
      }
    },
    onError: (error) => {
      toast.error(`登錄證據失敗：${error.message}`);
      console.error('[useCreateEvidenceEntry] failed:', error);
    },
  });
}

// ---------------------------------------------------------------------------
// useDeleteEvidenceEntry — DELETE
// ---------------------------------------------------------------------------

export function useDeleteEvidenceEntry() {
  const queryClient = useQueryClient();

  return useMutation<{ projectId: string }, Error, { id: string; projectId: string }>({
    mutationFn: async ({ id, projectId }) => {
      const { error } = await supabase
        .from('evidence_entries')
        .delete()
        .eq('id', id)
        .eq('project_id', projectId);

      if (error) throw error;
      return { projectId };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_entries.byProject(variables.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.kpis.byProject(variables.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_matrix.byProject(variables.projectId) });
      toast.success('證據已刪除');
    },
    onError: (error) => {
      toast.error(`刪除證據失敗：${error.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// useUpdateEvidenceEntry — UPDATE + auto-propagation
// ---------------------------------------------------------------------------

export interface UpdateEvidenceEntryInput {
  id: string;
  projectId: string;
  title?: string;
  measuredValue?: string;
  unit?: string;
  evidenceLevel?: string;
  method?: string;
  notes?: string;
  measuredAt?: string;
  kpiId?: string | null;
  experimentId?: string | null;
  linkedAssumptionCodes?: string[];
  linkedMustIds?: string[];
}

export function useUpdateEvidenceEntry() {
  const queryClient = useQueryClient();

  return useMutation<WithPropagationFlag<EvidenceEntry>, Error, UpdateEvidenceEntryInput>({
    mutationFn: async (input) => {
      const updateData: Record<string, unknown> = {};
      if (input.title !== undefined) updateData.title = input.title;
      if (input.measuredValue !== undefined) updateData.measured_value = input.measuredValue;
      if (input.unit !== undefined) updateData.unit = input.unit;
      if (input.evidenceLevel !== undefined) updateData.evidence_level = input.evidenceLevel;
      if (input.method !== undefined) updateData.method = input.method;
      if (input.notes !== undefined) updateData.notes = input.notes;
      if (input.measuredAt !== undefined) updateData.measured_at = input.measuredAt;
      if (input.kpiId !== undefined) updateData.kpi_id = input.kpiId;
      if (input.experimentId !== undefined) updateData.experiment_id = input.experimentId;
      if (input.linkedAssumptionCodes !== undefined) updateData.linked_assumption_codes = input.linkedAssumptionCodes;
      if (input.linkedMustIds !== undefined) updateData.linked_must_ids = input.linkedMustIds;

      const { data, error } = await supabase
        .from('evidence_entries')
        .update(updateData)
        .eq('id', input.id)
        .eq('project_id', input.projectId)
        .select()
        .single();

      if (error) throw error;

      let propagationFailed = false;
      try {
        await propagateEvidence(data as EvidenceEntryRow);
      } catch (propagationError) {
        console.error('[useUpdateEvidenceEntry] propagation failed:', propagationError);
        propagationFailed = true;
      }

      return { ...mapRow(data as EvidenceEntryRow), _propagationFailed: propagationFailed };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_entries.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.kpis.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.evidence_matrix.byProject(data.projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.track.assumptions(data.projectId) });
      if (data.kpiId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.evidence_entries.byKpi(data.kpiId) });
      }
      if (data._propagationFailed) {
        toast.warning('證據已更新，但相關 KPI / 矩陣同步失敗');
      } else {
        toast.success('證據已更新');
      }
    },
    onError: (error) => {
      toast.error(`更新證據失敗：${error.message}`);
    },
  });
}