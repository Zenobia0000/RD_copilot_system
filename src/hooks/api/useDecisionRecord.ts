/**
 * API hooks for DecisionRecord page (Step 3 — KT Decision)
 *
 * Covers: Decisions, Want Criteria, Want Scores,
 * Adverse Consequences, Signatures, Action Items, and Risks.
 *
 * All hooks use @tanstack/react-query with direct Supabase calls
 * and perform snake_case -> camelCase mapping at the hook layer.
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
  WantCriterion,
  WantScore,
  WantScoreEvidence,
  AdverseConsequence,
  ACProbability,
  ACSeverity,
  ACLevel,
  KtDecision,
  DecisionStatus,
  Signature,
  SignatureStatus,
  ActionItem,
} from '@/types/decisionRecord';
import type { Json } from '@/integrations/supabase/types';

// ---------------------------------------------------------------------------
// Row types (DB snake_case)
// ---------------------------------------------------------------------------

interface DecisionRow {
  id: string;
  project_id: string;
  selected_alternative_id: string | null;
  selected_alternative_name: string | null;
  rationale: string | null;
  risk_acceptance: string | null;
  decision_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface WantCriterionRow {
  id: string;
  project_id: string;
  name: string;
  weight: number;
  description: string | null;
  anchors: string | null;
}

interface WantScoreRow {
  id: string;
  project_id: string;
  criterion_id: string | null;
  alternative_id: string | null;
  score: number;
  evidence: string | null;
  weighted_total: number;
}

interface AdverseConsequenceRow {
  id: string;
  project_id: string;
  alternative_id: string | null;
  description: string;
  probability: string | null;
  severity: string | null;
  level: string | null;
  mitigation: string | null;
  risk_artifact_id: string | null;
}

interface SignatureRow {
  id: string;
  project_id: string;
  decision_id: string | null;
  name: string;
  role: string | null;
  status: string;
  signed_at: string | null;
  note: string | null;
}

interface ActionItemRow {
  id: string;
  project_id: string;
  decision_id: string | null;
  description: string;
  assignee: string | null;
  due_date: string | null;
}


// ---------------------------------------------------------------------------
// Mappers: DB row -> frontend type
// ---------------------------------------------------------------------------

function mapDecision(row: DecisionRow): KtDecision & { id: string } {
  return {
    id: row.id,
    selectedAlternativeId: row.selected_alternative_id ?? '',
    selectedAlternativeName: row.selected_alternative_name ?? '',
    rationale: row.rationale ?? '',
    riskAcceptance: row.risk_acceptance ?? '',
    actionItems: [], // loaded separately via useActionItems
    decisionDate: row.decision_date ?? '',
    status: (row.status as DecisionStatus) || 'draft',
  };
}

function mapWantCriterion(row: WantCriterionRow): WantCriterion {
  let anchors: WantCriterion['anchors'];
  if (row.anchors) {
    try {
      anchors = JSON.parse(row.anchors) as { score10: string; score6: string; score2: string };
    } catch {
      anchors = undefined;
    }
  }
  return {
    id: row.id,
    name: row.name,
    weight: row.weight,
    description: row.description ?? '',
    anchors,
  };
}

function mapAdverseConsequence(row: AdverseConsequenceRow): AdverseConsequence {
  return {
    id: row.id,
    alternativeId: row.alternative_id ?? '',
    description: row.description,
    probability: (row.probability as ACProbability) || 'low',
    severity: (row.severity as ACSeverity) || 'low',
    level: (row.level as ACLevel) || 'L',
    mitigation: row.mitigation ?? '',
    riskArtifactId: row.risk_artifact_id ?? null,
  };
}

function mapSignature(row: SignatureRow): Signature & { id: string; decisionId: string } {
  return {
    id: row.id,
    decisionId: row.decision_id ?? '',
    name: row.name,
    role: row.role ?? 'RD 工程師',
    status: (row.status as SignatureStatus) || 'pending',
    signedAt: row.signed_at ?? null,
    note: row.note ?? '',
  };
}

function mapActionItem(row: ActionItemRow): ActionItem {
  return {
    id: row.id,
    description: row.description,
    assignee: row.assignee ?? '',
    dueDate: row.due_date ?? '',
  };
}

// ---------------------------------------------------------------------------
// Decisions
// ---------------------------------------------------------------------------

/**
 * Fetch the decision record for a project.
 * Returns null if none exists yet.
 */
export function useDecision(projectId: string | undefined) {
  return useQuery<(KtDecision & { id: string }) | null, Error>({
    queryKey: queryKeys.decisions.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('decisions')
        .select('*')
        .eq('project_id', projectId!)
        .order('created_at', { ascending: false })
        .limit(1);
      if (error) throw error;
      if (!data || data.length === 0) return null;
      return mapDecision(data[0] as DecisionRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

/**
 * Upsert a decision: insert if none exists, update if one does.
 */
export function useUpsertDecision() {
  const qc = useQueryClient();
  return useMutation<
    KtDecision & { id: string },
    Error,
    {
      projectId: string;
      decisionId?: string;
      selectedAlternativeId?: string;
      selectedAlternativeName?: string;
      rationale?: string;
      riskAcceptance?: string;
      decisionDate?: string;
      status?: DecisionStatus;
    }
  >({
    mutationFn: async (vars) => {
      const now = new Date().toISOString();
      const row: Record<string, unknown> = {
        project_id: vars.projectId,
        updated_at: now,
      };
      if (vars.selectedAlternativeId !== undefined) row.selected_alternative_id = vars.selectedAlternativeId;
      if (vars.selectedAlternativeName !== undefined) row.selected_alternative_name = vars.selectedAlternativeName;
      if (vars.rationale !== undefined) row.rationale = vars.rationale;
      if (vars.riskAcceptance !== undefined) row.risk_acceptance = vars.riskAcceptance;
      if (vars.decisionDate !== undefined) row.decision_date = vars.decisionDate;
      if (vars.status !== undefined) row.status = vars.status;

      if (vars.decisionId) {
        // Update existing
        const { data, error } = await supabase
          .from('decisions')
          .update(row)
          .eq('id', vars.decisionId)
          .select()
          .single();
        if (error) throw error;
        return mapDecision(data as DecisionRow);
      } else {
        // Insert new
        row.created_at = now;
        const { data, error } = await supabase
          .from('decisions')
          .insert(row)
          .select()
          .single();
        if (error) throw error;
        return mapDecision(data as DecisionRow);
      }
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.decisions.byProject(vars.projectId) });
      toast.success('決策記錄已儲存');
    },
    onError: (err) => {
      toast.error(`儲存決策記錄失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Want Criteria
// ---------------------------------------------------------------------------

export function useWantCriteria(projectId: string | undefined) {
  return useQuery<WantCriterion[], Error>({
    queryKey: queryKeys.want_criteria.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('want_criteria')
        .select('*')
        .eq('project_id', projectId!)
        .order('weight', { ascending: false });
      if (error) throw error;
      return (data as WantCriterionRow[]).map(mapWantCriterion);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

export function useCreateWantCriterion() {
  const qc = useQueryClient();
  return useMutation<
    WantCriterion,
    Error,
    { projectId: string; name: string; weight?: number; description?: string; anchors?: { score10: string; score6: string; score2: string } }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {
        project_id: vars.projectId,
        name: vars.name,
        weight: vars.weight ?? 5,
        description: vars.description ?? '',
        anchors: vars.anchors ? JSON.stringify(vars.anchors) : null,
      };
      const { data, error } = await supabase
        .from('want_criteria')
        .insert(row)
        .select()
        .single();
      if (error) throw error;
      return mapWantCriterion(data as WantCriterionRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.want_criteria.byProject(vars.projectId) });
      toast.success('已新增 WANT 條件');
    },
    onError: (err) => {
      toast.error(`新增 WANT 條件失敗：${err.message}`);
    },
  });
}

export function useUpdateWantCriterion() {
  const qc = useQueryClient();
  return useMutation<
    WantCriterion,
    Error,
    { id: string; projectId: string; name?: string; weight?: number; description?: string; anchors?: { score10: string; score6: string; score2: string } }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {};
      if (vars.name !== undefined) row.name = vars.name;
      if (vars.weight !== undefined) row.weight = vars.weight;
      if (vars.description !== undefined) row.description = vars.description;
      if (vars.anchors !== undefined) row.anchors = JSON.stringify(vars.anchors);

      const { data, error } = await supabase
        .from('want_criteria')
        .update(row)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapWantCriterion(data as WantCriterionRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.want_criteria.byProject(vars.projectId) });
      toast.success('WANT 條件已更新');
    },
    onError: (err) => {
      toast.error(`更新 WANT 條件失敗：${err.message}`);
    },
  });
}

export function useDeleteWantCriterion() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    { id: string; projectId: string }
  >({
    mutationFn: async (vars) => {
      const { error } = await supabase
        .from('want_criteria')
        .delete()
        .eq('id', vars.id);
      if (error) throw error;
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.want_criteria.byProject(vars.projectId) });
      qc.invalidateQueries({ queryKey: queryKeys.want_scores.byProject(vars.projectId) });
      toast.success('已刪除 WANT 條件');
    },
    onError: (err) => {
      toast.error(`刪除 WANT 條件失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Want Scores
// ---------------------------------------------------------------------------

/**
 * Fetch want_scores for a project, grouped by alternative.
 * Joins with alternatives table to get alternative names.
 */
export function useWantScores(projectId: string | undefined) {
  return useQuery<WantScore[], Error>({
    queryKey: queryKeys.want_scores.byProject(projectId),
    queryFn: async () => {
      // Fetch scores
      const { data: scoreRows, error: scoreErr } = await supabase
        .from('want_scores')
        .select('*')
        .eq('project_id', projectId!);
      if (scoreErr) throw scoreErr;

      // Fetch alternatives to get names
      const { data: altRows, error: altErr } = await supabase
        .from('alternatives')
        .select('id, name')
        .eq('project_id', projectId!);
      if (altErr) throw altErr;

      const altMap = new Map<string, string>();
      for (const alt of altRows ?? []) {
        altMap.set(alt.id, alt.name);
      }

      // Group scores by alternative_id
      const grouped = new Map<string, { scores: Record<string, number>; evidence: Record<string, WantScoreEvidence>; weightedTotal: number }>();

      for (const row of (scoreRows as WantScoreRow[]) ?? []) {
        const altId = row.alternative_id ?? '';
        if (!grouped.has(altId)) {
          grouped.set(altId, { scores: {}, evidence: {}, weightedTotal: 0 });
        }
        const group = grouped.get(altId)!;
        const critId = row.criterion_id ?? '';
        group.scores[critId] = row.score;

        // Parse evidence JSON
        let evidenceEntry: WantScoreEvidence = { artifactId: null, evidenceLevel: null };
        if (row.evidence) {
          try {
            evidenceEntry = JSON.parse(row.evidence) as WantScoreEvidence;
          } catch {
            // ignore parse errors
          }
        }
        group.evidence[critId] = evidenceEntry;
        group.weightedTotal = Math.max(group.weightedTotal, row.weighted_total);
      }

      const result: WantScore[] = [];
      for (const [altId, group] of grouped) {
        result.push({
          alternativeId: altId,
          alternativeName: altMap.get(altId) ?? altId,
          scores: group.scores,
          evidence: group.evidence,
          weightedTotal: group.weightedTotal,
        });
      }

      return result;
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

/**
 * Upsert a single want_score for a criterion+alternative pair.
 * Uses Supabase upsert with onConflict matching.
 */
export function useUpsertWantScore() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    {
      projectId: string;
      criterionId: string;
      alternativeId: string;
      score: number;
      evidence?: WantScoreEvidence;
      weightedTotal?: number;
    }
  >({
    mutationFn: async (vars) => {
      const row = {
        project_id: vars.projectId,
        criterion_id: vars.criterionId,
        alternative_id: vars.alternativeId,
        score: vars.score,
        evidence: vars.evidence ? JSON.stringify(vars.evidence) : null,
        weighted_total: vars.weightedTotal ?? 0,
      };

      // TODO: Add DB unique constraint on (project_id, criterion_id, alternative_id) then
      // replace with: supabase.from('want_scores').upsert(row, { onConflict: '...' })
      // Current check-then-act is not fully atomic but handles the common single-user case.
      const { data: existing } = await supabase
        .from('want_scores')
        .select('id')
        .eq('project_id', vars.projectId)
        .eq('criterion_id', vars.criterionId)
        .eq('alternative_id', vars.alternativeId)
        .limit(1)
        .single();

      if (existing) {
        const { error } = await supabase
          .from('want_scores')
          .update(row)
          .eq('id', existing.id);
        if (error) throw error;
      } else {
        const { error } = await supabase
          .from('want_scores')
          .insert(row);
        if (error) throw error;
      }
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.want_scores.byProject(vars.projectId) });
    },
    onError: (err) => {
      toast.error(`儲存評分失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Adverse Consequences
// ---------------------------------------------------------------------------

export function useAdverseConsequences(projectId: string | undefined) {
  return useQuery<AdverseConsequence[], Error>({
    queryKey: queryKeys.adverse_consequences.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('adverse_consequences')
        .select('*')
        .eq('project_id', projectId!)
        .order('id', { ascending: true });
      if (error) throw error;
      return (data as AdverseConsequenceRow[]).map(mapAdverseConsequence);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

export function useCreateAdverseConsequence() {
  const qc = useQueryClient();
  return useMutation<
    AdverseConsequence,
    Error,
    {
      projectId: string;
      alternativeId: string;
      description: string;
      probability?: ACProbability;
      severity?: ACSeverity;
      level?: ACLevel;
      mitigation?: string;
      riskArtifactId?: string | null;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {
        project_id: vars.projectId,
        alternative_id: vars.alternativeId,
        description: vars.description,
        probability: vars.probability ?? 'low',
        severity: vars.severity ?? 'low',
        level: vars.level ?? 'L',
        mitigation: vars.mitigation ?? '',
        risk_artifact_id: vars.riskArtifactId ?? null,
      };
      const { data, error } = await supabase
        .from('adverse_consequences')
        .insert(row)
        .select()
        .single();
      if (error) throw error;
      return mapAdverseConsequence(data as AdverseConsequenceRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.adverse_consequences.byProject(vars.projectId) });
      toast.success('已新增負面後果');
    },
    onError: (err) => {
      toast.error(`新增負面後果失敗：${err.message}`);
    },
  });
}

export function useUpdateAdverseConsequence() {
  const qc = useQueryClient();
  return useMutation<
    AdverseConsequence,
    Error,
    {
      id: string;
      projectId: string;
      alternativeId?: string;
      description?: string;
      probability?: ACProbability;
      severity?: ACSeverity;
      level?: ACLevel;
      mitigation?: string;
      riskArtifactId?: string | null;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {};
      if (vars.alternativeId !== undefined) row.alternative_id = vars.alternativeId;
      if (vars.description !== undefined) row.description = vars.description;
      if (vars.probability !== undefined) row.probability = vars.probability;
      if (vars.severity !== undefined) row.severity = vars.severity;
      if (vars.level !== undefined) row.level = vars.level;
      if (vars.mitigation !== undefined) row.mitigation = vars.mitigation;
      if (vars.riskArtifactId !== undefined) row.risk_artifact_id = vars.riskArtifactId;

      const { data, error } = await supabase
        .from('adverse_consequences')
        .update(row)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapAdverseConsequence(data as AdverseConsequenceRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.adverse_consequences.byProject(vars.projectId) });
      toast.success('負面後果已更新');
    },
    onError: (err) => {
      toast.error(`更新負面後果失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Signatures
// ---------------------------------------------------------------------------

export function useSignatures(projectId: string | undefined) {
  return useQuery<(Signature & { id: string; decisionId: string })[], Error>({
    queryKey: queryKeys.signatures.byProject(projectId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('signatures')
        .select('*')
        .eq('project_id', projectId!)
        .order('id', { ascending: true });
      if (error) throw error;
      return (data as SignatureRow[]).map(mapSignature);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

export function useCreateSignature() {
  const qc = useQueryClient();
  return useMutation<
    Signature & { id: string; decisionId: string },
    Error,
    {
      projectId: string;
      decisionId?: string;
      name: string;
      role?: string;
      status?: SignatureStatus;
      note?: string;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {
        project_id: vars.projectId,
        decision_id: vars.decisionId ?? null,
        name: vars.name,
        role: vars.role ?? 'RD 工程師',
        status: vars.status ?? 'pending',
        note: vars.note ?? '',
      };
      const { data, error } = await supabase
        .from('signatures')
        .insert(row)
        .select()
        .single();
      if (error) throw error;
      return mapSignature(data as SignatureRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.signatures.byProject(vars.projectId) });
      toast.success('已新增簽核人');
    },
    onError: (err) => {
      toast.error(`新增簽核人失敗：${err.message}`);
    },
  });
}

export function useUpdateSignature() {
  const qc = useQueryClient();
  return useMutation<
    Signature & { id: string; decisionId: string },
    Error,
    {
      id: string;
      projectId: string;
      name?: string;
      role?: string;
      status?: SignatureStatus;
      signedAt?: string | null;
      note?: string;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {};
      if (vars.name !== undefined) row.name = vars.name;
      if (vars.role !== undefined) row.role = vars.role;
      if (vars.status !== undefined) row.status = vars.status;
      if (vars.signedAt !== undefined) row.signed_at = vars.signedAt;
      if (vars.note !== undefined) row.note = vars.note;

      const { data, error } = await supabase
        .from('signatures')
        .update(row)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapSignature(data as SignatureRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.signatures.byProject(vars.projectId) });
      toast.success('簽核狀態已更新');
    },
    onError: (err) => {
      toast.error(`更新簽核失敗：${err.message}`);
    },
  });
}

// ---------------------------------------------------------------------------
// Action Items
// ---------------------------------------------------------------------------

export function useActionItems(projectId: string | undefined, decisionId?: string) {
  return useQuery<ActionItem[], Error>({
    queryKey: queryKeys.action_items.byProject(projectId),
    queryFn: async () => {
      let query = supabase
        .from('action_items')
        .select('*')
        .eq('project_id', projectId!);
      if (decisionId) {
        query = query.eq('decision_id', decisionId);
      }
      const { data, error } = await query.order('id', { ascending: true });
      if (error) throw error;
      return (data as ActionItemRow[]).map(mapActionItem);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
  });
}

export function useCreateActionItem() {
  const qc = useQueryClient();
  return useMutation<
    ActionItem,
    Error,
    {
      projectId: string;
      decisionId?: string;
      description: string;
      assignee?: string;
      dueDate?: string;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {
        project_id: vars.projectId,
        decision_id: vars.decisionId ?? null,
        description: vars.description,
        assignee: vars.assignee ?? '',
        due_date: vars.dueDate ?? null,
      };
      const { data, error } = await supabase
        .from('action_items')
        .insert(row)
        .select()
        .single();
      if (error) throw error;
      return mapActionItem(data as ActionItemRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.action_items.byProject(vars.projectId) });
      toast.success('已新增行動項目');
    },
    onError: (err) => {
      toast.error(`新增行動項目失敗：${err.message}`);
    },
  });
}

export function useUpdateActionItem() {
  const qc = useQueryClient();
  return useMutation<
    ActionItem,
    Error,
    {
      id: string;
      projectId: string;
      description?: string;
      assignee?: string;
      dueDate?: string;
    }
  >({
    mutationFn: async (vars) => {
      const row: Record<string, unknown> = {};
      if (vars.description !== undefined) row.description = vars.description;
      if (vars.assignee !== undefined) row.assignee = vars.assignee;
      if (vars.dueDate !== undefined) row.due_date = vars.dueDate;

      const { data, error } = await supabase
        .from('action_items')
        .update(row)
        .eq('id', vars.id)
        .select()
        .single();
      if (error) throw error;
      return mapActionItem(data as ActionItemRow);
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.action_items.byProject(vars.projectId) });
      toast.success('行動項目已更新');
    },
    onError: (err) => {
      toast.error(`更新行動項目失敗：${err.message}`);
    },
  });
}

export function useDeleteActionItem() {
  const qc = useQueryClient();
  return useMutation<
    void,
    Error,
    { id: string; projectId: string }
  >({
    mutationFn: async (vars) => {
      const { error } = await supabase
        .from('action_items')
        .delete()
        .eq('id', vars.id);
      if (error) throw error;
    },
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.action_items.byProject(vars.projectId) });
      toast.success('已刪除行動項目');
    },
    onError: (err) => {
      toast.error(`刪除行動項目失敗：${err.message}`);
    },
  });
}

