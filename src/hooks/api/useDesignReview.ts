/**
 * API hooks for DesignReview page (V1 — Review & Decision)
 *
 * Covers: Evidence Matrix, Risks, Experiments.
 *
 * All hooks use the generic useSupabaseQuery / useSupabaseMutation
 * helpers and perform snake_case -> camelCase mapping at the hook layer.
 */

import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type {
  EvidenceLevel,
  EvidenceMatrixRow,
  RiskItem,
  Experiment,
  ExperimentStatus,
} from '@/types/designReview';

// ---------------------------------------------------------------------------
// Row types (DB snake_case)
// ---------------------------------------------------------------------------

interface EvidenceMatrixDbRow {
  id: string;
  project_id: string;
  assumption_code: string;
  summary: string;
  current_level: string;
  is_north_star: boolean;
  created_at: string;
  updated_at: string;
}

interface RiskDbRow {
  id: string;
  project_id: string;
  description: string;
  failure_mode: string;
  probability: number;
  severity: number;
  mitigation: string;
  created_at: string;
  updated_at: string;
}

interface ExperimentDbRow {
  id: string;
  project_id: string;
  name: string;
  linked_assumptions: string[];
  evidence_level: string;
  method: string;
  success_criteria: string;
  status: string;
  result: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Mappers: DB row -> frontend type
// ---------------------------------------------------------------------------

function mapEvidenceRow(row: EvidenceMatrixDbRow): EvidenceMatrixRow {
  return {
    assumptionCode: row.assumption_code,
    summary: row.summary,
    currentLevel: row.current_level as EvidenceLevel,
    isNorthStar: row.is_north_star,
    experiments: [], // populated by joining experiments on the page
  };
}

function mapRisk(row: RiskDbRow): RiskItem {
  return {
    id: row.id,
    description: row.description,
    failureMode: row.failure_mode,
    probability: row.probability,
    severity: row.severity,
    mitigation: row.mitigation,
  };
}

function mapExperiment(row: ExperimentDbRow): Experiment {
  return {
    id: row.id,
    name: row.name,
    linkedAssumptions: row.linked_assumptions ?? [],
    evidenceLevel: row.evidence_level as EvidenceLevel,
    method: row.method,
    successCriteria: row.success_criteria,
    status: row.status as ExperimentStatus,
    result: row.result,
  };
}

// ---------------------------------------------------------------------------
// Evidence Matrix
// ---------------------------------------------------------------------------

export function useEvidenceMatrix(projectId: string | undefined) {
  const result = useSupabaseQuery<EvidenceMatrixDbRow[]>({
    table: 'evidence_matrix',
    queryKey: queryKeys.evidence_matrix.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq' as const, value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...result,
    data: result.data?.map(mapEvidenceRow) ?? [],
  };
}

export function useCreateEvidenceRow() {
  return useSupabaseMutation<EvidenceMatrixDbRow, {
    project_id: string;
    assumption_code: string;
    summary: string;
    current_level?: string;
    is_north_star?: boolean;
  }>({
    table: 'evidence_matrix',
    type: 'insert',
    invalidateKeys: [queryKeys.evidence_matrix.all],
    successMessage: '已新增證據列',
  });
}

export function useUpdateEvidenceRow() {
  return useSupabaseMutation<EvidenceMatrixDbRow, {
    id: string;
    current_level?: string;
    is_north_star?: boolean;
    summary?: string;
  }>({
    table: 'evidence_matrix',
    type: 'update',
    invalidateKeys: [queryKeys.evidence_matrix.all],
    successMessage: '證據列已更新',
  });
}

// ---------------------------------------------------------------------------
// Risks
// ---------------------------------------------------------------------------

export function useRisks(projectId: string | undefined) {
  const result = useSupabaseQuery<RiskDbRow[]>({
    table: 'risks',
    queryKey: queryKeys.risks.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq' as const, value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...result,
    data: result.data?.map(mapRisk) ?? [],
  };
}

export function useCreateRisk() {
  return useSupabaseMutation<RiskDbRow, {
    project_id: string;
    description: string;
    failure_mode: string;
    probability: number;
    severity: number;
    mitigation?: string;
  }>({
    table: 'risks',
    type: 'insert',
    invalidateKeys: [queryKeys.risks.all],
    successMessage: '已新增風險',
  });
}

export function useUpdateRisk() {
  return useSupabaseMutation<RiskDbRow, {
    id: string;
    description?: string;
    failure_mode?: string;
    probability?: number;
    severity?: number;
    mitigation?: string;
  }>({
    table: 'risks',
    type: 'update',
    invalidateKeys: [queryKeys.risks.all],
    successMessage: '風險已更新',
  });
}

export function useDeleteRisk() {
  return useSupabaseMutation<RiskDbRow, { id: string }>({
    table: 'risks',
    type: 'delete',
    invalidateKeys: [queryKeys.risks.all],
    successMessage: '風險已刪除',
  });
}

// ---------------------------------------------------------------------------
// Experiments
// ---------------------------------------------------------------------------

export function useExperiments(projectId: string | undefined) {
  const result = useSupabaseQuery<ExperimentDbRow[]>({
    table: 'experiments',
    queryKey: queryKeys.experiments.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq' as const, value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  return {
    ...result,
    data: result.data?.map(mapExperiment) ?? [],
  };
}

export function useCreateExperiment() {
  return useSupabaseMutation<ExperimentDbRow, {
    project_id: string;
    name: string;
    linked_assumptions?: string[];
    evidence_level?: string;
    method?: string;
    success_criteria?: string;
    status?: string;
    result?: string;
  }>({
    table: 'experiments',
    type: 'insert',
    invalidateKeys: [queryKeys.experiments.all],
    successMessage: '已新增實驗',
  });
}

export function useUpdateExperiment() {
  return useSupabaseMutation<ExperimentDbRow, {
    id: string;
    name?: string;
    linked_assumptions?: string[];
    evidence_level?: string;
    method?: string;
    success_criteria?: string;
    status?: string;
    result?: string;
  }>({
    table: 'experiments',
    type: 'update',
    invalidateKeys: [queryKeys.experiments.all],
    successMessage: '實驗已更新',
  });
}
