import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Plus, AlertTriangle, Undo2 } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { trizParameters } from "@/data/trizParameters";
import { supabase } from "@/integrations/supabase/client";
import { queryKeys } from "@/hooks/api/useQueryConfig";
import { contradictionFormalize, contradictionDecompose, contradictionDeriveSF, contradictionIdentifyMulti } from "@/lib/api";
import type { ContradictionFormalizeResponse, IdentifiedTC } from "@/lib/api";
import { DEFAULT_SEVERITY } from "@/types/contradiction";
import type { ExploreContradiction, ContradictionType } from "@/types/explore";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { useAiOperationGuard } from "@/hooks/useAiOperationGuard";
import { DecomposedChildrenList } from "./DecomposedChildrenList";
import { ContradictionDisplayCard } from "./ContradictionDisplayCard";

interface ContradictionTabProps {
  contradictions: ExploreContradiction[];
  onUpdateContradictions: (contradictions: ExploreContradiction[]) => void;
  hasAnswers: boolean;
  projectId: string;
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  socraticAnswers?: string[];
}

export function ContradictionTab({ contradictions, onUpdateContradictions, hasAnswers, projectId, mission, constraints, kpis, socraticAnswers }: ContradictionTabProps) {
  const qc = useQueryClient();
  const [aiLoadingType, setAiLoadingType] = useState<ContradictionType | null>(null);
  const { runGuarded, isMountedRef } = useAiOperationGuard();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ExploreContradiction>>({});
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [addingType, setAddingType] = useState<ContradictionType | null>(null);
  const [revertConfirmId, setRevertConfirmId] = useState<string | null>(null);
  const [staleParentIds, setStaleParentIds] = useState<Set<string>>(new Set());
  const pendingEditIdRef = useRef<string | null>(null);

  const invalidate = () => qc.invalidateQueries({ queryKey: queryKeys.contradictions.byProject(projectId) });

  // 6.1 — Group contradictions into parent TCs + child PCs
  const childrenMap = useMemo(() => {
    const map = new Map<string, ExploreContradiction[]>();
    for (const c of contradictions) {
      if (c.parentContradictionId) {
        const arr = map.get(c.parentContradictionId) ?? [];
        arr.push(c);
        map.set(c.parentContradictionId, arr);
      }
    }
    return map;
  }, [contradictions]);

  // Top-level: only contradictions without a parent
  const topLevelContradictions = useMemo(
    () => contradictions.filter(c => !c.parentContradictionId),
    [contradictions]
  );

  // TC / PC / SF 分類列表
  //   · tcList = 正式 TC + 尚未細化 (type=null) 的草稿
  const tcList = useMemo(
    () => topLevelContradictions.filter((c) => c.type === 'TC' || c.type == null),
    [topLevelContradictions]
  );
  const confirmedCount = useMemo(
    () => contradictions.filter((c) => c.status === 'confirmed').length,
    [contradictions]
  );

  // ── CRUD handlers ─────────────────────────────────────────────────────

  const handleConfirm = useCallback(async (id: string) => {
    const { error } = await supabase
      .from('contradictions')
      .update({ resolved: true, updated_at: new Date().toISOString() })
      .eq('id', id);
    if (error) { toast.error(`確認失敗：${error.message}`); return; }
    invalidate();
    toast.success('矛盾已確認');
  }, [invalidate]);

  const handleRevertToDraft = useCallback(async (id: string) => {
    const { error } = await supabase
      .from('contradictions')
      .update({ resolved: false, updated_at: new Date().toISOString() })
      .eq('id', id);
    if (error) { toast.error(`撤回失敗：${error.message}`); return; }
    setRevertConfirmId(null);
    invalidate();
    toast.info('已恢復為草稿狀態');
  }, [invalidate]);

  const handleStartEdit = useCallback((c: ExploreContradiction) => {
    setEditingId(c.id);
    setEditForm({ ...c });
  }, []);

  const handleRequestDelete = useCallback((id: string) => {
    setDeleteConfirmId(id);
  }, []);

  const handleRequestRevert = useCallback((id: string) => {
    setRevertConfirmId(id);
  }, []);

  const handleSaveEdit = async () => {
    if (!editingId) return;

    // ✅ 驗證必填欄位，防止空描述被儲存
    const desc = editForm.description?.trim();
    if (!desc) {
      toast.error('請填寫矛盾描述');
      return;
    }

    if (editForm.type === 'TC') {
      if (!editForm.improvingParam || !editForm.worseningParam) {
        toast.error('技術矛盾需要選擇改善參數和惡化參數');
        return;
      }
    } else if (editForm.type === 'PC') {
      if (!editForm.pcAttributeA?.trim() || !editForm.pcAttributeNotA?.trim()) {
        toast.error('物理矛盾需要填寫屬性 A 和非 A');
        return;
      }
    } else if (editForm.type === 'SF') {
      if (!editForm.sfSubstance1?.trim() || !editForm.sfSubstance2?.trim() || !editForm.sfField?.trim()) {
        toast.error('Su-Field 問題需要填寫 S1、S2 和 Field');
        return;
      }
    }

    const updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    };
    if (editForm.description !== undefined) {
      updateData.natural_description = editForm.description;
      updateData.engineering_statement = editForm.description;
    }
    if (editForm.improvingParam !== undefined) updateData.improving_param = editForm.improvingParam;
    if (editForm.worseningParam !== undefined) updateData.worsening_param = editForm.worseningParam;
    if (editForm.type !== undefined) updateData.type = editForm.type;
    if (editForm.pcAttributeA !== undefined || editForm.pcAttributeNotA !== undefined) {
      updateData.physical_contradiction = `${editForm.pcAttributeA ?? ''} | ${editForm.pcAttributeNotA ?? ''}`;
    }
    if (editForm.sfSubstance1 !== undefined) updateData.sf_substance_1 = editForm.sfSubstance1;
    if (editForm.sfSubstance2 !== undefined) updateData.sf_substance_2 = editForm.sfSubstance2;
    if (editForm.sfField !== undefined) updateData.sf_field = editForm.sfField;
    if (editForm.sfInteraction !== undefined) updateData.sf_interaction = editForm.sfInteraction;
    if (editForm.sfCompleteness !== undefined) updateData.sf_completeness = editForm.sfCompleteness;
    if (editForm.severity !== undefined) updateData.severity = editForm.severity;

    const { error } = await supabase
      .from('contradictions')
      .update(updateData)
      .eq('id', editingId);
    if (error) {
      toast.error(`更新失敗：${error.message}`);
      return;
    }

    // 7.1 — Mark children as stale if parent TC params changed
    const savedId = editingId;
    const original = contradictions.find(c => c.id === savedId);
    if (original && childrenMap.has(savedId) && (
      editForm.improvingParam !== original.improvingParam ||
      editForm.worseningParam !== original.worseningParam ||
      editForm.engineeringStatement !== original.engineeringStatement
    )) {
      setStaleParentIds(prev => new Set(prev).add(savedId));
    }

    setEditingId(null);
    setEditForm({});
    invalidate();
    toast.success('矛盾已更新');
  };

  const handleDelete = async (id: string) => {
    // Delete dependent triz_solutions first to avoid FK constraint violation
    const { error: trizErr } = await supabase
      .from('triz_solutions')
      .delete()
      .eq('contradiction_id', id);
    if (trizErr) { toast.error(`刪除關聯 TRIZ 解法失敗：${trizErr.message}`); return; }

    // Drop the layered drill-down row (migration 010). The column is TEXT-typed
    // contradiction_id (FK-by-name) with no DB-level cascade, so clean it
    // manually to avoid orphan rows the UI would still hydrate on next mount.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 010, Supabase types not regenerated yet
    const { error: ltsErr } = await (supabase as any)
      .from('layered_triz_solutions')
      .delete()
      .eq('contradiction_id', id);
    if (ltsErr) { toast.error(`刪除分層解法失敗：${ltsErr.message}`); return; }

    const { error } = await supabase
      .from('contradictions')
      .delete()
      .eq('id', id);
    if (error) { toast.error(`刪除失敗：${error.message}`); return; }
    setDeleteConfirmId(null);
    invalidate();
    qc.invalidateQueries({ queryKey: queryKeys.layered_triz_solutions.byProject(projectId) });
    toast.success('矛盾及關聯 TRIZ 解法已刪除');
  };

  // 6.4 — Edit handler for child PC (reuses existing inline edit UX)
  const handleEditChildPC = useCallback((pc: ExploreContradiction) => {
    handleStartEdit(pc);
  }, []);

  // 6.4 — Delete handler for child PC (reuses existing confirmation dialog)
  const handleDeleteChildPC = useCallback((pcId: string) => {
    setDeleteConfirmId(pcId);
  }, []);

  // 7.2 — Re-decompose: delete old children, re-run decomposition, clear stale flag
  const handleReDecompose = useCallback(async (parentTc: ExploreContradiction) => {
    // 1. Delete existing children
    const existingChildren = childrenMap.get(parentTc.id) ?? [];
    for (const child of existingChildren) {
      await supabase.from('contradictions').delete().eq('id', child.id);
    }
    // 2. Re-run decomposition with force=true to skip dedup
    const fakeResult: ContradictionFormalizeResponse = {
      type: 'TC',
      engineering_statement: parentTc.engineeringStatement ?? '',
      improving_param: parentTc.improvingParam ?? null,
      worsening_param: parentTc.worseningParam ?? null,
      physical_contradiction: null,
      pc_attribute_a: null,
      pc_attribute_not_a: null,
      sf_substance_1: null,
      sf_substance_2: null,
      sf_field: null,
      sf_interaction: null,
      sf_completeness: null,
      confidence: 1,
    };
    await Promise.all([
      maybeAutoDecomposeTC(parentTc.id, fakeResult, true),
      maybeAutoDeriveChildSF(parentTc.id, fakeResult),
    ]);
    // 3. Clear stale flag
    setStaleParentIds(prev => {
      const next = new Set(prev);
      next.delete(parentTc.id);
      return next;
    });
    invalidate();
  }, [childrenMap, invalidate]);

  // 手動新增矛盾 — 使用 addingType 決定類型 (TC/PC/SF)
  const handleAddManual = async () => {
    const typeToAdd = 'TC'; // Plan B: only TC at top level
    const now = new Date().toISOString();
    const { data, error } = await supabase
      .from('contradictions')
      .insert({
        project_id: projectId,
        type: typeToAdd,
        natural_description: '',
        severity: DEFAULT_SEVERITY,
        created_at: now,
        updated_at: now,
      })
      .select()
      .single();
    if (error) {
      toast.error(`新增失敗：${error.message}`);
      return;
    }
    setAddingType(null);

    // ✅ 記住待編輯的 ID，等資料刷新後再自動進入編輯模式
    pendingEditIdRef.current = data.id;
    await qc.invalidateQueries({
      queryKey: queryKeys.contradictions.byProject(projectId),
    });
  };

  // ✅ 資料刷新後，自動對剛新增的項目進入編輯模式
  useEffect(() => {
    if (!pendingEditIdRef.current) return;
    const target = contradictions.find((c) => c.id === pendingEditIdRef.current);
    if (target) {
      handleStartEdit(target);
      pendingEditIdRef.current = null;
    }
  }, [contradictions]);

  // ── Auto PC decomposition (L2 WBS 5.2-5.5) ───────────────────────────
  // After a formalize call returns type === 'TC', auto-trigger the backend
  // /contradictions/{cid}/decompose endpoint and batch-insert any child PCs
  // into Supabase. Entire flow is silent on failure so it never disrupts
  // the outer AI re-identify flow.

  const maybeAutoDecomposeTC = async (
    parentRowId: string,
    formalizeResponse: ContradictionFormalizeResponse,
    force = false, // 7.2: skip dedup when re-decomposing
  ): Promise<number> => {
    try {
      if (formalizeResponse.type !== 'TC') return 0;
      if (!formalizeResponse.engineering_statement) {
        console.warn('[pc-decompose] missing engineering_statement, skipping');
        return 0;
      }

      // 5.5 — Dedup guard: skip if parent already has children (unless force)
      if (!force) {
        const existingChildren = contradictions.filter(
          (c) => c.parentContradictionId === parentRowId,
        );
        if (existingChildren.length > 0) {
          console.debug('[pc-decompose] parent has children, skipping');
          return 0;
        }
      }

      // 5.2 — Auto call backend /decompose
      const decomposeResponse = await contradictionDecompose(parentRowId, {
        project_id: projectId,
        parent_contradiction_id: parentRowId,
        engineering_statement: formalizeResponse.engineering_statement,
        improving_param: formalizeResponse.improving_param,
        worsening_param: formalizeResponse.worsening_param,
        mission: mission ?? '',
        constraints: constraints ?? [],
        kpis: kpis ?? [],
        socraticAnswers: socraticAnswers ?? [],
      });

      if (!decomposeResponse.triggered || decomposeResponse.decomposed_pcs.length === 0) {
        console.warn('[pc-decompose] critic not triggered:', decomposeResponse.trigger_reason);
        return 0;
      }

      // 5.3 — Batch insert children
      const childRows = decomposeResponse.decomposed_pcs.map((pc) => ({
        project_id: projectId,
        parent_contradiction_id: parentRowId,
        type: 'PC',
        natural_description: pc.physical_contradiction,
        physical_contradiction: pc.physical_contradiction,
        pc_attribute_a: pc.pc_attribute_a,
        pc_attribute_not_a: pc.pc_attribute_not_a,
        derived_parameter: pc.derived_parameter,
        subsystem_hint: pc.subsystem_hint,
        separation_principle_id: pc.separation_principle_id,
        separation_category: pc.separation_category,
        separation_rationale: pc.separation_rationale,
        severity: 'minor',
        resolved: false,
      }));
      const { error: insertErr } = await supabase.from('contradictions').insert(childRows);
      if (insertErr) throw insertErr;

      return decomposeResponse.decomposed_pcs.length;
    } catch (err) {
      console.warn('[pc-decompose] auto-decompose failed:', err);
      return 0;
    }
  };

  // ── Auto SF derivation (Plan B hierarchical tree) ──────────────────────
  // After a formalize call returns type === 'TC', auto-trigger the backend
  // /contradictions/{cid}/derive-sf endpoint and insert a child SF row.
  // Runs in parallel with maybeAutoDecomposeTC. Silent on failure.

  const maybeAutoDeriveChildSF = async (
    parentRowId: string,
    formalizeResponse: ContradictionFormalizeResponse,
  ): Promise<void> => {
    try {
      if (formalizeResponse.type !== 'TC') return;
      if (!formalizeResponse.engineering_statement) return;
      if (!formalizeResponse.improving_param || !formalizeResponse.worsening_param) return;

      const sfResp = await contradictionDeriveSF(parentRowId, {
        project_id: projectId,
        contradiction_id: parentRowId,
        engineering_statement: formalizeResponse.engineering_statement,
        improving_param: formalizeResponse.improving_param,
        worsening_param: formalizeResponse.worsening_param,
      });

      if (!sfResp.derived) return;

      const now = new Date().toISOString();
      await supabase.from('contradictions').insert({
        project_id: projectId,
        parent_contradiction_id: parentRowId,
        type: 'SF',
        natural_description: `Su-Field: ${sfResp.sf_substance_1 ?? ''} ↔ ${sfResp.sf_substance_2 ?? ''} via ${sfResp.sf_field ?? ''}`,
        sf_substance_1: sfResp.sf_substance_1 ?? null,
        sf_substance_2: sfResp.sf_substance_2 ?? null,
        sf_field: sfResp.sf_field ?? null,
        sf_interaction: sfResp.sf_interaction ?? null,
        sf_completeness: sfResp.sf_completeness ?? null,
        severity: 'minor',
        resolved: false,
        created_at: now,
        updated_at: now,
      });
    } catch (err) {
      console.warn('[sf-derive] auto-derive SF failed:', err);
    }
  };

  // ── AI 識別矛盾 (TC-only, Plan B) ─────────────────────────────────────

  const handleAiReidentify = () => {
    setAiLoadingType('TC'); // reuse as generic loading indicator
    runGuarded(async () => {
    try {
      // 待形式化目標：所有 top-level row 中，缺少類型特定關鍵欄位的項目
      const targets = topLevelContradictions.filter((c) => {
        if (!c.description) return false;
        if (c.type == null) return true;
        if (c.type === 'TC') return !c.improvingParam && !c.worseningParam;
        return false; // Plan B: only TC at top level
      });

      if (targets.length > 0) {
        // Parallelize per-target formalize + update + decompose. Each target
        // is independent; failures are isolated via Promise.allSettled so one
        // LLM error doesn't cancel siblings.
        const processOne = async (c: ExploreContradiction): Promise<number> => {
          const result = await contradictionFormalize({
            project_id: projectId,
            contradiction_id: c.id,
            natural_description: c.description,
            mission, constraints, kpis, socraticAnswers,
          });
          if (result.type === null) {
            const desc = (c.description || c.id).slice(0, 40);
            toast.warning(`無法形式化「${desc}」`, {
              description: (result.rationale ?? '請細化描述或多答幾題 Socratic 後重試').slice(0, 160),
            });
            return 0;
          }
          await supabase
            .from('contradictions')
            .update({
              type: 'TC',
              improving_param: result.improving_param,
              worsening_param: result.worsening_param,
              engineering_statement: result.engineering_statement,
              updated_at: new Date().toISOString(),
            })
            .eq('id', c.id);
          // Parallel: decompose TC → child PCs + derive child SF
          const [pcCount] = await Promise.all([
            maybeAutoDecomposeTC(c.id, result),
            maybeAutoDeriveChildSF(c.id, result),
          ]);
          return pcCount;
        };
        const results = await Promise.allSettled(targets.map(processOne));
        const count = results.filter((r) => r.status === 'fulfilled').length;
        const totalDecomposed = results.reduce(
          (sum, r) => sum + (r.status === 'fulfilled' ? r.value : 0),
          0,
        );
        invalidate();
        toast.success(`AI 已形式化 ${count} 個技術矛盾 (TC)`);
        if (totalDecomposed > 0) {
          toast.success(`已自動深挖出 ${totalDecomposed} 個子矛盾 (PC + SF)`);
        }
      } else {
        // Path B: 無待形式化目標 → 一次辨識多個 TC (Multi-TC)
        const existingDescs = topLevelContradictions
          .filter(c => c.type === 'TC' && c.description)
          .map(c => c.description!);

        const multiResult = await contradictionIdentifyMulti({
          project_id: projectId,
          mission: mission || '',
          constraints: constraints || [],
          kpis: kpis || [],
          socraticAnswers: socraticAnswers || [],
          existing_descriptions: existingDescs,
        });

        const validTcs = multiResult.items.filter(tc => tc.type === 'TC');
        if (validTcs.length === 0) {
          toast.warning('AI 無法辨識任何技術矛盾', {
            description: '請提供更具體的工程描述或先答 Socratic 題目後重試',
          });
          invalidate();
          return;
        }

        // 對每個有效 TC：插入 draft → 更新 → 自動分解
        const processOneTc = async (tc: IdentifiedTC): Promise<number> => {
          const now = new Date().toISOString();
          const { data: draft, error: insertErr } = await supabase
            .from('contradictions')
            .insert({
              project_id: projectId,
              type: 'TC',
              natural_description: tc.engineering_statement,
              engineering_statement: tc.engineering_statement,
              improving_param: tc.improving_param,
              worsening_param: tc.worsening_param,
              severity: DEFAULT_SEVERITY,
              // 3-Stage Pipeline new fields
              linked_kpis: tc.linked_kpis ?? [],
              why_selected: tc.why_selected ?? null,
              priority: tc.priority ?? null,
              created_at: now,
              updated_at: now,
            })
            .select()
            .single();
          if (insertErr) throw insertErr;

          // Parallel: decompose TC → child PCs + derive child SF
          const [pcCount] = await Promise.all([
            maybeAutoDecomposeTC(draft.id, {
              engineering_statement: tc.engineering_statement,
              improving_param: tc.improving_param,
              worsening_param: tc.worsening_param,
            } as ContradictionFormalizeResponse),
            maybeAutoDeriveChildSF(draft.id, {
              engineering_statement: tc.engineering_statement,
              improving_param: tc.improving_param,
              worsening_param: tc.worsening_param,
            } as ContradictionFormalizeResponse),
          ]);
          return pcCount;
        };

        const results = await Promise.allSettled(validTcs.map(processOneTc));
        const successCount = results.filter(r => r.status === 'fulfilled').length;
        const totalDecomposed = results.reduce(
          (sum, r) => sum + (r.status === 'fulfilled' ? (r as PromiseFulfilledResult<number>).value : 0),
          0,
        );

        invalidate();
        toast.success(`AI 已識別 ${successCount} 個技術矛盾 (TC)`);
        if (totalDecomposed > 0) {
          toast.success(`已自動深挖出 ${totalDecomposed} 個子矛盾 (PC + SF)`);
        }
      }
    } catch (err) {
      console.error('AI re-identify failed:', err);
      toast.error('AI 識別失敗，請稍後重試');
    } finally {
      if (isMountedRef.current) setAiLoadingType(null);
    }
    }, '矛盾 AI 識別');
  };

  // ── Render a single contradiction card ────────────────────────────────

  const renderCard = (c: ExploreContradiction) => {
    const isEditing = editingId === c.id;

    if (!isEditing) {
      return (
        <ContradictionDisplayCard
          contradiction={c}
          onConfirm={handleConfirm}
          onStartEdit={handleStartEdit}
          onRequestDelete={handleRequestDelete}
          onRequestRevert={handleRequestRevert}
        />
      );
    }

    // Edit mode — kept inline (only one card is editing at a time)
    return (
      <Card key={c.id} className="transition-colors">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge
              className="text-xs text-white"
              style={{ backgroundColor: c.type === 'TC' ? '#3B82F6' : c.type === 'SF' ? '#10B981' : '#F59E0B' }}
            >
              {c.type}
            </Badge>
            {c.source === 'ai' && (
              <Badge variant="secondary" className="text-[10px]">AI</Badge>
            )}
          </div>
          {/* Edit form */}
          <div className="space-y-3">
              {editForm.type === 'TC' ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground">改善參數 *</span>
                    <Select
                      value={editForm.improvingParam?.toString() ?? ''}
                      onValueChange={(v) => setEditForm((f) => ({ ...f, improvingParam: Number(v) }))}
                    >
                      <SelectTrigger><SelectValue placeholder="選擇" /></SelectTrigger>
                      <SelectContent>
                        {trizParameters.map((p) => (
                          <SelectItem key={p.id} value={p.id.toString()}>
                            #{p.id} {p.nameZh}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground">惡化參數 *</span>
                    <Select
                      value={editForm.worseningParam?.toString() ?? ''}
                      onValueChange={(v) => setEditForm((f) => ({ ...f, worseningParam: Number(v) }))}
                    >
                      <SelectTrigger><SelectValue placeholder="選擇" /></SelectTrigger>
                      <SelectContent>
                        {trizParameters.map((p) => (
                          <SelectItem key={p.id} value={p.id.toString()}>
                            #{p.id} {p.nameZh}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ) : editForm.type === 'SF' ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground">S1 工具物質 *</span>
                      <Input
                        value={editForm.sfSubstance1 ?? ''}
                        onChange={(e) => setEditForm((f) => ({ ...f, sfSubstance1: e.target.value }))}
                        placeholder="例：軸承"
                        maxLength={100}
                      />
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground">S2 產品物質 *</span>
                      <Input
                        value={editForm.sfSubstance2 ?? ''}
                        onChange={(e) => setEditForm((f) => ({ ...f, sfSubstance2: e.target.value }))}
                        placeholder="例：轉子"
                        maxLength={100}
                      />
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground">場 (Field) *</span>
                      <Input
                        value={editForm.sfField ?? ''}
                        onChange={(e) => setEditForm((f) => ({ ...f, sfField: e.target.value }))}
                        placeholder="例：機械場"
                        maxLength={100}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground">交互作用</span>
                      <Select
                        value={editForm.sfInteraction ?? ''}
                        onValueChange={(v) => setEditForm((f) => ({ ...f, sfInteraction: v }))}
                      >
                        <SelectTrigger><SelectValue placeholder="選擇" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="useful">有用 (useful)</SelectItem>
                          <SelectItem value="harmful">有害 (harmful)</SelectItem>
                          <SelectItem value="insufficient">不足 (insufficient)</SelectItem>
                          <SelectItem value="missing">缺失 (missing)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xs text-muted-foreground">Su-Field 完整性</span>
                      <Select
                        value={editForm.sfCompleteness ?? ''}
                        onValueChange={(v) => setEditForm((f) => ({ ...f, sfCompleteness: v }))}
                      >
                        <SelectTrigger><SelectValue placeholder="選擇" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="complete">完整 (complete)</SelectItem>
                          <SelectItem value="incomplete">不完整 (incomplete)</SelectItem>
                          <SelectItem value="harmful_complete">有害完整 (harmful)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground">需要的屬性 A *</span>
                    <Input
                      value={editForm.pcAttributeA ?? ''}
                      onChange={(e) => setEditForm((f) => ({ ...f, pcAttributeA: e.target.value }))}
                      placeholder="例：高轉速"
                      maxLength={100}
                    />
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground">同時需要非 A *</span>
                    <Input
                      value={editForm.pcAttributeNotA ?? ''}
                      onChange={(e) => setEditForm((f) => ({ ...f, pcAttributeNotA: e.target.value }))}
                      placeholder="例：低轉速"
                      maxLength={100}
                    />
                  </div>
                </div>
              )}
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">矛盾描述 *</span>
                <Textarea
                  value={editForm.description ?? ''}
                  onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  maxLength={500}
                />
              </div>
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">
                  嚴重度{' '}
                  <span className="text-[10px]">（fatal/major 會自動深挖 TRIZ L2；minor 在 quick_mode 下跳過 L2）</span>
                </span>
                <Select
                  value={editForm.severity ?? 'minor'}
                  onValueChange={(v) => setEditForm((f) => ({ ...f, severity: v as 'fatal' | 'major' | 'minor' }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fatal">致命 (fatal) — 必須解，阻斷主流程</SelectItem>
                    <SelectItem value="major">重要 (major) — 影響關鍵 KPI</SelectItem>
                    <SelectItem value="minor">輕微 (minor) — 次要影響</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSaveEdit}>儲存</Button>
                <Button size="sm" variant="ghost" onClick={() => { setEditingId(null); setEditForm({}); }}>取消</Button>
              </div>
            </div>
        </CardContent>
      </Card>
    );
  };

  // ── Render TC section ─────────────────────────────────────────────────

  const renderTcSection = () => {
    const list = tcList;
    const color = '#3B82F6';
    const help = 'TC（技術矛盾）：改善參數 A 會惡化參數 B → 矛盾矩陣 → 40 原理。AI 會自動衍生子 PC（物理矛盾）與 SF（Su-Field 問題）。';
    const confirmed = list.filter((c) => c.status === 'confirmed').length;

    return (
      <div className="space-y-4">
        {/* Section header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-5 w-1 rounded-full" style={{ backgroundColor: color }} />
            <h3 className="text-base font-semibold">技術矛盾 (TC)</h3>
            <HelpTooltip text={help} />
            <Badge className="text-white text-[10px]" style={{ backgroundColor: color }}>{list.length}</Badge>
            {confirmed > 0 && (
              <Badge className="bg-green-600 text-white text-[10px]">已確認 {confirmed}</Badge>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={() => setAddingType('TC')}>
            <Plus className="h-3.5 w-3.5 mr-1" /> 手動新增 TC
          </Button>
        </div>

        {/* Cards */}
        {list.length > 0 ? (
          <div className="space-y-3">
            {list.map((c) => (
              <div key={c.id}>
                {renderCard(c)}
                {/* null-type 草稿：formalize 未細化，標示「需細化」 */}
                {c.type == null && (
                  <div className="mt-1 ml-2 text-[11px] text-amber-600">
                    ⚠ 尚未形式化為 TC — 請細化描述或答 Socratic 後點「識別 TC」
                  </div>
                )}
                {/* 6.1 — Nested child PCs (from TC→multi-PC decomposition, Create 階段產物) */}
                <DecomposedChildrenList
                  children={childrenMap.get(c.id) ?? []}
                  parentId={c.id}
                  onEditPC={handleEditChildPC}
                  onDeletePC={handleDeleteChildPC}
                  stale={staleParentIds.has(c.id)}
                  onReDecompose={() => handleReDecompose(c)}
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-muted/30 rounded-lg border border-dashed">
            <p className="text-sm text-muted-foreground">
              尚無技術矛盾 — 點擊上方「AI 識別矛盾」或手動新增
            </p>
          </div>
        )}
      </div>
    );
  };


  // ── Empty state ───────────────────────────────────────────────────────

  if (contradictions.length === 0 && !hasAnswers) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-muted-foreground font-medium">尚無矛盾</p>
        <p className="text-sm text-muted-foreground">請先完成蘇格拉底問答，AI 將自動識別技術矛盾 (TC)，並衍生子 PC 與 SF</p>
        <Button variant="ghost" onClick={() => setAddingType('TC')}>
          <Plus className="h-4 w-4 mr-1" /> 手動新增 TC
        </Button>
      </div>
    );
  }

  // ── Main render ───────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Purpose intro */}
      <SectionIntro text="Explore 階段識別技術矛盾 (TC)。AI 會自動衍生子物理矛盾 (PC) 與 Su-Field 問題 (SF)，以階層樹狀結構呈現。確認後將用於 TRIZ 分層解法。" />

      {/* Summary stats + global AI button */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge className="bg-blue-500 text-white text-xs">TC: {tcList.length}</Badge>
        <Badge variant="secondary" className="text-xs">總計: {contradictions.length}</Badge>
        <Badge className="bg-green-600 text-white text-xs">已確認: {confirmedCount}</Badge>
        <div className="ml-auto">
          <AiButton size="sm" loading={!!aiLoadingType} onClick={() => handleAiReidentify()}>
            AI 識別 TC
          </AiButton>
        </div>
      </div>

      {/* TC Section (hierarchical tree: TC → child PCs + child SF) */}
      {renderTcSection()}

      {/* Add new dialog — type-aware */}
      <Dialog open={!!addingType} onOpenChange={() => setAddingType(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新增技術矛盾 (TC)</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            TC（技術矛盾）：改善一個參數會導致另一個參數惡化。建立後可編輯改善 / 惡化參數。子 PC 和 SF 將由 AI 自動衍生。
          </p>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddingType(null)}>取消</Button>
            <Button onClick={() => handleAddManual()}>建立</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revert confirmation */}
      <Dialog open={!!revertConfirmId} onOpenChange={() => setRevertConfirmId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Undo2 className="h-5 w-5 text-muted-foreground" />
              確定要撤回確認？
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">此矛盾將恢復為草稿狀態，您可以重新編輯後再次確認。</p>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRevertConfirmId(null)}>取消</Button>
            <Button variant="outline" onClick={() => revertConfirmId && handleRevertToDraft(revertConfirmId)}>撤回確認</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={!!deleteConfirmId} onOpenChange={() => setDeleteConfirmId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              確定刪除此矛盾？
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">此操作不可復原。</p>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteConfirmId(null)}>取消</Button>
            <Button variant="destructive" onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}>刪除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
