/**
 * API hooks for Create page (Step 2 — Solution Exploration)
 *
 * Covers: TRIZ Solutions, Subsystems, and Alternatives.
 *
 * All hooks use the generic useSupabaseQuery / useSupabaseMutation
 * helpers and perform snake_case → camelCase mapping at the hook layer.
 */

import { useMemo } from 'react';
import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type {
  TrizSolution,
  TrizPath,
  TrizActionStatus,
  Subsystem,
  SubsystemSource,
  SubsystemLevel,
  ScamperVariant,
  ScamperAction,
  ScamperNewContradiction,
  Alternative,
  AlternativeSource,
  InterfaceContract,
  ValidationPassport,
} from '@/types/create';
import type { InterfaceContractMap } from '@/types/generated/subsystem';
import type { Json } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// Row types (DB snake_case)
// ---------------------------------------------------------------------------

interface TrizSolutionRow {
  id: string;
  project_id: string;
  contradiction_id: string | null;
  path: string;
  principle_number: number | null;
  principle_name: string | null;
  suggestion: string | null;
  status: string;
  created_at: string;
}

interface SubsystemRow {
  id: string;
  project_id: string;
  name: string;
  level: string | null;
  reason: string | null;
  related_contradictions: string[] | null;
  confirmed: boolean;
  parent_id: string | null;
  interfaces: string | null;
  interface_contracts: Record<string, unknown> | null;
  source: string;
  created_at: string;
}

/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
interface ScamperVariantRow {
  id: string;
  project_id: string;
  subsystem_id: string | null;
  action: string;
  description: string | null;
  adopted: boolean;
  new_contradictions: Json | null;
  created_at: string;
}

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
  validation_passport: Json | null;
  cad_status: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Mappers: DB row → frontend type
// ---------------------------------------------------------------------------

function mapValidationPassport(raw: Record<string, unknown> | null): ValidationPassport | null {
  if (!raw) return null;
  return {
    assumptions: (Array.isArray(raw.assumptions) ? raw.assumptions : []).map((a: Record<string, unknown>) => ({
      content: (a.content as string) ?? '',
      category: (a.category as string) ?? '',
      evidenceLevel: (a.evidence_level ?? a.evidenceLevel ?? 'E0') as string,
      worstConsequence: (a.worst_consequence ?? a.worstConsequence ?? '') as string,
      worstSeverity: (a.worst_severity ?? a.worstSeverity ?? 'medium') as string,
      suggestedExperiment: (a.suggested_experiment ?? a.suggestedExperiment ?? '') as string,
    })),
    weakPoints: Array.isArray(raw.weak_points ?? raw.weakPoints) ? (raw.weak_points ?? raw.weakPoints) as string[] : [],
    requiredVerifications: Array.isArray(raw.required_verifications ?? raw.requiredVerifications) ? (raw.required_verifications ?? raw.requiredVerifications) as string[] : [],
    crossDomainSource: (raw.cross_domain_source ?? raw.crossDomainSource ?? '') as string,
    confidenceLevel: Number(raw.confidence_level ?? raw.confidenceLevel ?? 0),
  };
}

function mapTrizSolution(row: TrizSolutionRow): TrizSolution {
  return {
    id: row.id,
    contradictionId: row.contradiction_id ?? '',
    path: row.path as TrizPath,
    principleNumber: row.principle_number,
    principleName: row.principle_name ?? '',
    suggestion: row.suggestion ?? '',
    status: row.status as TrizActionStatus,
    createdAt: row.created_at,
  };
}

function mapSubsystem(row: SubsystemRow): Subsystem {
  // Stage 6: if level is missing on the DB row this is a data corruption
  // signal — log loudly so developers see it in the console, but keep the
  // row visible (falling back to "module") so one bad row does not take
  // down the entire subsystems list. Insert-path validation in
  // useSubsystemSuggestion.ts is the fail-loud enforcement layer.
  const level = (row.level as SubsystemLevel) ?? 'module';
  if (!row.level) {
    console.error(
      `[mapSubsystem] subsystem ${row.id} (${row.name}) has no level in DB; ` +
        `defaulting to "module". This indicates an insert-path bug — please report.`,
    );
  }
  // Stage 4: derive `interfaces` list from interface_contracts keys rather
  // than the legacy comma-joined `interfaces` column. Migration 008 already
  // upgraded historical rows so the contracts map is the authoritative
  // source. The legacy column is kept until Stage 7 for rollback safety.
  const interfaceContracts = (row.interface_contracts as InterfaceContractMap) ?? undefined;
  const interfaces = interfaceContracts
    ? Object.keys(interfaceContracts)
    : row.interfaces
      ? row.interfaces.split(',').map(s => s.trim()).filter(Boolean)
      : [];
  return {
    id: row.id,
    name: row.name,
    level,
    reason: row.reason ?? '',
    relatedContradictions: row.related_contradictions ?? [],
    confirmed: row.confirmed,
    parentId: row.parent_id,
    interfaces,
    interfaceContracts,
    source: row.source as SubsystemSource,
    createdAt: row.created_at,
  };
}

/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
function mapScamperVariant(row: ScamperVariantRow): ScamperVariant {
  return {
    id: row.id,
    subsystemId: row.subsystem_id ?? '',
    action: row.action as ScamperAction,
    description: row.description ?? '',
    adopted: row.adopted,
    newContradictions: (row.new_contradictions as ScamperNewContradiction[] | null) ?? undefined,
    createdAt: row.created_at,
  };
}

function mapAlternative(row: AlternativeRow): Alternative {
  const defaultMust: Record<string, 'pass' | 'fail' | 'marginal' | null> = {
    M1: null, M2: null, M3: null, M4: null, M5: null, M6: null,
  };
  const defaultPreCad = {
    must: null as number | null,
    decoupling: null as number | null,
    testability: null as number | null,
    failureMech: null as number | null,
    mvpCadEffort: null as number | null,
  };
  const defaultContract: InterfaceContract = {
    envelope: '', loadPath: '', signalPath: '', thermalPath: '', datumTolerance: '', serviceability: '',
  };

  return {
    id: row.id,
    name: row.name,
    mechanism: row.mechanism ?? '',
    source: (row.source ?? 'manual') as AlternativeSource,
    keyAssumptionIds: row.key_assumption_ids ?? [],
    mustScores: row.must_scores ? { ...defaultMust, ...(row.must_scores as Record<string, 'pass' | 'fail' | 'marginal' | null>) } : defaultMust,
    interfaceContract: row.interface_contract ? { ...defaultContract, ...(row.interface_contract as Partial<InterfaceContract>) } : defaultContract,
    preCadScores: row.pre_cad_scores ? { ...defaultPreCad, ...(row.pre_cad_scores as Partial<typeof defaultPreCad>) } : defaultPreCad,
    overallPass: row.overall_pass,
    validationPassport: (row.validation_passport as ValidationPassport | null) ?? null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

// ---------------------------------------------------------------------------
// TRIZ Solutions
// ---------------------------------------------------------------------------

export function useTrizSolutions(projectId: string | undefined) {
  const result = useSupabaseQuery<TrizSolutionRow[]>({
    table: 'triz_solutions',
    queryKey: queryKeys.triz_solutions.byProject(projectId),
    filters: projectId ? [{ column: 'project_id', operator: 'eq', value: projectId }] : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  const data = useMemo(() => result.data?.map(mapTrizSolution) ?? [], [result.data]);
  return { ...result, data };
}

export function useCreateTrizSolution() {
  return useSupabaseMutation<TrizSolutionRow, {
    project_id: string;
    contradiction_id?: string;
    path: string;
    principle_number?: number | null;
    principle_name?: string;
    suggestion?: string;
    status?: string;
  }>({
    table: 'triz_solutions',
    type: 'insert',
    invalidateKeys: [queryKeys.triz_solutions.all],
    successMessage: '已新增 TRIZ 解法',
  });
}

export function useUpdateTrizSolution() {
  return useSupabaseMutation<TrizSolutionRow, {
    id: string;
    status?: string;
    suggestion?: string;
    principle_name?: string;
  }>({
    table: 'triz_solutions',
    type: 'update',
    invalidateKeys: [queryKeys.triz_solutions.all],
    successMessage: 'TRIZ 解法已更新',
  });
}

// ---------------------------------------------------------------------------
// Subsystems
// ---------------------------------------------------------------------------

export function useSubsystems(projectId: string | undefined) {
  const result = useSupabaseQuery<SubsystemRow[]>({
    table: 'subsystems',
    queryKey: queryKeys.subsystems.byProject(projectId),
    filters: projectId ? [{ column: 'project_id', operator: 'eq', value: projectId }] : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  const data = useMemo(() => result.data?.map(mapSubsystem) ?? [], [result.data]);
  return { ...result, data };
}

// Stage 4: mutation payloads now carry `interface_contracts` (JSONB) directly
// instead of the legacy `interfaces` comma-joined string. The DB column
// `subsystems.interfaces` still exists (to be dropped in Stage 7) but writes
// no longer target it — migration 008 upgrades historical rows from
// `interfaces` → `interface_contracts` with empty 6-dim placeholders.
export function useCreateSubsystem() {
  return useSupabaseMutation<SubsystemRow, {
    project_id: string;
    name: string;
    reason?: string;
    related_contradictions?: string[];
    confirmed?: boolean;
    parent_id?: string | null;
    interface_contracts?: InterfaceContractMap | null;
    source?: string;
    level?: string;
  }>({
    table: 'subsystems',
    type: 'insert',
    invalidateKeys: [queryKeys.subsystems.all],
    successMessage: '已新增子系統',
  });
}

export function useUpdateSubsystem() {
  return useSupabaseMutation<SubsystemRow, {
    id: string;
    name?: string;
    reason?: string;
    related_contradictions?: string[];
    confirmed?: boolean;
    parent_id?: string | null;
    interface_contracts?: InterfaceContractMap | null;
    source?: string;
    level?: string;
  }>({
    table: 'subsystems',
    type: 'update',
    invalidateKeys: [queryKeys.subsystems.all],
    successMessage: '子系統已更新',
  });
}

export function useDeleteSubsystem() {
  return useSupabaseMutation<unknown, { id: string }>({
    table: 'subsystems',
    type: 'delete',
    invalidateKeys: [queryKeys.subsystems.all],
    successMessage: '已刪除子系統',
  });
}

// ---------------------------------------------------------------------------
// SCAMPER Variants
// @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions
// ---------------------------------------------------------------------------

/** @deprecated v9: SCAMPER removed */
export function useScamperVariants(projectId: string | undefined) {
  const result = useSupabaseQuery<ScamperVariantRow[]>({
    table: 'scamper_variants',
    queryKey: queryKeys.scamper_variants.byProject(projectId),
    filters: projectId ? [{ column: 'project_id', operator: 'eq', value: projectId }] : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  const data = useMemo(() => result.data?.map(mapScamperVariant) ?? [], [result.data]);
  return { ...result, data };
}

/** @deprecated v9: SCAMPER removed */
export function useCreateScamperVariant() {
  return useSupabaseMutation<ScamperVariantRow, {
    project_id: string;
    subsystem_id?: string;
    action: string;
    description?: string;
    adopted?: boolean;
    new_contradictions?: Json;
  }>({
    table: 'scamper_variants',
    type: 'insert',
    invalidateKeys: [queryKeys.scamper_variants.all],
    successMessage: '已新增 SCAMPER 變形',
  });
}

/** @deprecated v9: SCAMPER removed */
export function useUpdateScamperVariant() {
  return useSupabaseMutation<ScamperVariantRow, {
    id: string;
    adopted?: boolean;
    description?: string;
    new_contradictions?: Json;
  }>({
    table: 'scamper_variants',
    type: 'update',
    invalidateKeys: [queryKeys.scamper_variants.all],
    successMessage: 'SCAMPER 變形已更新',
  });
}

// ---------------------------------------------------------------------------
// Alternatives
// ---------------------------------------------------------------------------

export function useAlternatives(projectId: string | undefined) {
  const result = useSupabaseQuery<AlternativeRow[]>({
    table: 'alternatives',
    queryKey: queryKeys.alternatives.byProject(projectId),
    filters: projectId ? [{ column: 'project_id', operator: 'eq', value: projectId }] : [],
    orderBy: { column: 'created_at', ascending: true },
    enabled: !!projectId,
  });

  const data = useMemo(() => result.data?.map(mapAlternative) ?? [], [result.data]);
  return { ...result, data };
}

export function useCreateAlternative() {
  return useSupabaseMutation<AlternativeRow, {
    project_id: string;
    name: string;
    mechanism?: string;
    source?: string;
    key_assumption_ids?: string[];
    must_scores?: Json;
    interface_contract?: Json;
    pre_cad_scores?: Json;
    overall_pass?: boolean | null;
    cad_status?: string;
  }>({
    table: 'alternatives',
    type: 'insert',
    invalidateKeys: [queryKeys.alternatives.all],
    successMessage: '已新增方案',
  });
}

export function useUpdateAlternative() {
  return useSupabaseMutation<AlternativeRow, {
    id: string;
    name?: string;
    mechanism?: string;
    source?: string;
    key_assumption_ids?: string[];
    must_scores?: Json;
    interface_contract?: Json;
    pre_cad_scores?: Json;
    overall_pass?: boolean | null;
    cad_status?: string;
  }>({
    table: 'alternatives',
    type: 'update',
    invalidateKeys: [queryKeys.alternatives.all],
    successMessage: '方案已更新',
  });
}

export function useDeleteAlternative() {
  return useSupabaseMutation<unknown, { id: string }>({
    table: 'alternatives',
    type: 'delete',
    invalidateKeys: [queryKeys.alternatives.all],
  });
}
