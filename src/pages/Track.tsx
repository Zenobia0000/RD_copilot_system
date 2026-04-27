import { useState, useMemo, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { KanbanBoard } from "@/components/track/KanbanBoard";
import { UnknownFactors } from "@/components/track/UnknownFactors";
import { TrackGate } from "@/components/track/TrackGate";
import {
  useTrackAssumptions,
  useUpdateTrackAssumptionStatus,
  useUnknownFactors,
  useCreateUnknownFactor,
  useUpdateUnknownFactor,
  useConvertUnknownToAssumption,
} from "@/hooks/api/useTrack";
import { useConstraints } from "@/hooks/api/useBrief";
import type { TrackAssumption, UnknownFactor, TrackGateItem } from "@/types/track";
import { ArrowLeft, Check } from "lucide-react";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { KnowledgeRefsPanel } from "@/components/create/KnowledgeRefsPanel";
// TODO: Replace mockPageKnowledgeRefs with a useKnowledgeRefs hook once a knowledge_refs DB table is created (Sprint 5+)
import { mockPageKnowledgeRefs } from "@/data/mockKnowledgeRefs";

type TabKey = 'kanban' | 'unknown';

export default function Track() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const hashTab = location.hash.replace('#', '') as TabKey;
  const initialTab: TabKey = ['kanban', 'unknown'].includes(hashTab) ? hashTab : 'kanban';

  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  // --- API hooks ---
  const {
    data: assumptions,
    isLoading: isAssumptionsLoading,
  } = useTrackAssumptions(id);
  const updateStatus = useUpdateTrackAssumptionStatus(id);
  const { data: briefConstraints = [] } = useConstraints(id);
  const trackConstraintStrings = useMemo(
    () => briefConstraints.map((c) => `[${c.constraintCode}] ${c.description} (${c.type})`),
    [briefConstraints],
  );

  const {
    data: factors,
    isLoading: isFactorsLoading,
    refetch: refetchFactors,
  } = useUnknownFactors(id);
  const createFactor = useCreateUnknownFactor(id);
  const updateFactor = useUpdateUnknownFactor(id);
  const convertMutation = useConvertUnknownToAssumption(id);

  const isLoading = isAssumptionsLoading || isFactorsLoading;

  // Local state mirrors for optimistic Kanban drag and factor updates
  const [localAssumptions, setLocalAssumptions] = useState<TrackAssumption[] | null>(null);
  const [localFactors, setLocalFactors] = useState<UnknownFactor[] | null>(null);

  // Use local overrides when available, otherwise API data
  const displayAssumptions = localAssumptions ?? assumptions;
  const displayFactors = localFactors ?? factors;

  // Sync local state when API data changes
  // (reset local overrides so fresh data shows)
  const assumptionsKey = JSON.stringify(assumptions.map((a) => `${a.id}:${a.verificationStatus}`));
  useMemo(() => { setLocalAssumptions(null); }, [assumptionsKey]);

  const factorsKey = JSON.stringify(factors.map((f) => `${f.id}:${f.status}`));
  useMemo(() => { setLocalFactors(null); }, [factorsKey]);

  const handleTabChange = useCallback((tab: string) => {
    const t = tab as TabKey;
    setActiveTab(t);
    window.history.replaceState(null, '', `#${t}`);
    setSaveStatus('saving');
    setTimeout(() => {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }, 500);
  }, []);

  // Kanban drag: optimistically update local state + fire mutation
  const handleUpdateAssumptions = useCallback((updated: TrackAssumption[]) => {
    setLocalAssumptions(updated);

    // Detect which assumption changed status
    const current = displayAssumptions;
    for (const u of updated) {
      const prev = current.find((a) => a.id === u.id);
      if (prev && prev.verificationStatus !== u.verificationStatus) {
        updateStatus.mutate(u.id, u.verificationStatus);
      }
    }
  }, [displayAssumptions, updateStatus]);

  // Unknown factors: detect new/changed items and persist to DB
  const handleUpdateFactors = useCallback((updated: UnknownFactor[]) => {
    setLocalFactors(updated);
    const currentIds = new Set(factors.map((f) => f.id));
    for (const f of updated) {
      if (!currentIds.has(f.id)) {
        // New factor → insert to DB
        createFactor.mutate({
          project_id: id!,
          unknown_code: f.unknownCode,
          description: f.description,
          impact: f.impact,
          status: f.status,
          note: f.note ?? null,
          linked_assumption_id: f.linkedAssumptionId ?? null,
        });
      } else {
        // Existing factor → check if changed
        const orig = factors.find((o) => o.id === f.id);
        if (orig && (orig.status !== f.status || orig.note !== f.note)) {
          updateFactor.mutate({ id: f.id, status: f.status, note: f.note ?? undefined });
        }
      }
    }
  }, [factors, id, createFactor, updateFactor]);

  const handleConvertToAssumption = useCallback(async (factor: UnknownFactor) => {
    await convertMutation.convert(factor, displayAssumptions.length);
    refetchFactors();
  }, [convertMutation, displayAssumptions.length, refetchFactors]);

  // Gate X1 checks
  const totalAssumptions = displayAssumptions.length;
  const beyondUnverified = displayAssumptions.filter((a) => a.verificationStatus !== 'unverified').length;
  const highRiskAssumptions = displayAssumptions.filter((a) => a.riskLevel === 'H' || a.riskLevel === 'H*');
  const highRiskWithExp = highRiskAssumptions.filter((a) => a.experimentCount > 0).length;

  const gateItems: TrackGateItem[] = useMemo(() => [
    // { label: '至少 5 個假設已建立', current: totalAssumptions, target: 5, passed: totalAssumptions >= 5 },
    { label: '至少 1 個假設處於「驗證中」或以上', current: beyondUnverified, target: 1, passed: beyondUnverified >= 1 },
    // { label: '所有高風險 (H*/H) 假設皆有實驗計畫', current: highRiskWithExp, target: Math.max(highRiskAssumptions.length, 1), passed: highRiskAssumptions.length > 0 && highRiskWithExp === highRiskAssumptions.length },
  ], [totalAssumptions, beyondUnverified, highRiskWithExp, highRiskAssumptions.length]);

  const openFactors = displayFactors.filter((f) => f.status === 'open').length;

  if (isLoading) {
    return (
      <div className="page-shell-wide">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-full" />
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64 flex-1" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell-wide">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}
            className="text-muted-foreground -ml-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回 Dashboard
          </Button>
          {saveStatus !== 'idle' && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              {saveStatus === 'saving' && 'Saving...'}
              {saveStatus === 'saved' && (
                <>
                  <Check className="h-3 w-3 text-green-600" />
                  Saved
                </>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 rounded-full bg-amber-500" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Track — 假設追蹤
              <HelpTooltip text="此階段管理所有設計假設，透過 Kanban 看板追蹤驗證進度。高風險假設必須有實驗計畫，通過 Gate X1 後進入方案創造。" className="ml-2 align-middle" />
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              X1 · 假設 Kanban + 未知集合 U
            </p>
          </div>
        </div>
      </div>

      {/* Purpose intro */}
      <SectionIntro text="將設計假設拖曳到對應的驗證階段（未驗證 → 驗證中 → 已驗證/已推翻）。「未知集合 U」收集尚未歸類的不確定因素，可一鍵轉為假設進行追蹤。" />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="w-full grid grid-cols-2 h-11">
          <TabsTrigger
            value="kanban"
            className="text-xs sm:text-sm data-[state=active]:border-b-[3px] data-[state=active]:border-b-amber-500 rounded-none"
          >
            假設 Kanban
            <Badge variant="secondary" className="text-[10px] ml-1.5 hidden sm:inline-flex">
              {displayAssumptions.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger
            value="unknown"
            className="text-xs sm:text-sm data-[state=active]:border-b-[3px] data-[state=active]:border-b-amber-500 rounded-none"
          >
            未知集合 U
            <Badge variant="secondary" className="text-[10px] ml-1.5 hidden sm:inline-flex">
              {openFactors}
            </Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="kanban" className="mt-5">
          <KanbanBoard
            assumptions={displayAssumptions}
            onUpdateAssumptions={handleUpdateAssumptions}
            projectId={id || ''}
            constraints={trackConstraintStrings}
          />
        </TabsContent>

        <TabsContent value="unknown" className="mt-5">
          <UnknownFactors
            factors={displayFactors}
            assumptions={displayAssumptions}
            onUpdateFactors={handleUpdateFactors}
            onConvertToAssumption={handleConvertToAssumption}
            projectId={id || ''}
          />
        </TabsContent>
      </Tabs>

      {/* Knowledge Enhancement Panel (WBS 3.4.2) */}
      <KnowledgeRefsPanel refs={mockPageKnowledgeRefs.track ?? []} />

      {/* Gate */}
      <TrackGate
        items={gateItems}
        onNavigateNext={() => navigate(`/projects/${id}/create`)}
      />
    </div>
  );
}
