import { useState, useEffect, useMemo, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible";
import { toast } from "sonner";
import {
  ArrowLeft, Check, Plus, Sparkles, Loader2, AlertTriangle,
  ArrowRight, Flag, CheckCircle, XCircle, ChevronLeft, ChevronRight, Pencil, Trash2,
  Shapes, Clock, RefreshCw
} from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from "recharts";
import type {
  AntiAnchorRoute, TrizSolution, Subsystem,
  Alternative, AccordionStepStatus, TrizPath, TrizActionStatus, CreateGateItem,
  SubsystemSource, SubsystemLevel
} from "@/types/create";
import { DEFAULT_MUST_CRITERIA, PRECAD_DIMENSIONS } from "@/types/create";
import type { MustCriterion } from "@/types/create";
import type { InterfaceContractMap } from "@/types/generated/subsystem";
import { EMPTY_INTERFACE_CONTRACT } from "@/types/generated/subsystem";
import { useSocraticQuestions } from "@/hooks/api/useExplore";
/**
 * Stage 4 of refactor/subsystem-interface-contracts: convert the manual-form
 * comma-separated "interfaces" text input into an InterfaceContractMap with
 * empty 6-dim placeholders per neighbour. Preserves existing contracts when
 * editing — only adds/removes keys, never overwrites populated fields.
 *
 * This lets the manual subsystem form feed the same data shape the AI path
 * produces, so downstream consumers (InterfaceContractsPanel, Pre-CAD
 * spatial_score, variant tracking) see a uniform structure.
 */
function neighbourTextToContractMap(
  text: string,
  existing?: InterfaceContractMap | null,
): InterfaceContractMap | null {
  const names = text
    .split(",")
    .map(s => s.trim())
    .filter(Boolean);
  if (names.length === 0) return null;

  const result: InterfaceContractMap = {};
  for (const name of names) {
    result[name] = existing?.[name] ?? { ...EMPTY_INTERFACE_CONTRACT };
  }
  return result;
}
// TODO: Replace with AI-generated anti-anchor warning via API (Sprint 3+)
import {
  useAntiAnchorRoutes,
  useCreateAntiAnchorRoute,
  useUpdateAntiAnchorRoute,
  useDeleteAntiAnchorRoute,
  useTrizSolutions,
  useCreateTrizSolution,
  useUpdateTrizSolution,
  useSubsystems,
  useCreateSubsystem,
  useUpdateSubsystem,
  useDeleteSubsystem,
  useAlternatives,
  useCreateAlternative,
  useUpdateAlternative,
  useDeleteAlternative,
} from "@/hooks/api";
import { useContradictions } from "@/hooks/api/useContradictions";
import { useLayeredTrizSolutions } from "@/hooks/api/useLayeredTrizSolutions";
import { useDirectedTrizSolutions } from "@/hooks/api/useDirectedTrizSolutions";
import { useTrizConsolidationResult, upsertConsolidationResult } from "@/hooks/api/useTrizConsolidationResult";
import type { Contradiction } from "@/types/contradiction";
import type { Json } from "@/integrations/supabase/types";
import { supabase } from "@/integrations/supabase/client";
import { useTrackAssumptions } from "@/hooks/api/useTrack";
import { useBrief, useConstraints, useKpis } from "@/hooks/api/useBrief";
import { antiAnchorGenerate, trizSolveLayered, trizSolveDirected, trizConsolidate, riskAnalyze, mustEvaluate, validationPassportGenerate, subsystemSpatialOverlay, spatialComponentOverride, spatialLearnedComponent } from "@/lib/api";
import type { LayeredTrizSolution, TrizSeverity, AdoptedLayerId } from "@/types/layeredTriz";
import type { ContradictionDirectionResult, ConsolidationResult } from "@/types/directedTriz";
import { LayeredSolutionCard } from "@/components/create/LayeredSolutionCard";
import type { AdoptionMode } from "@/components/create/LayeredSolutionCard";
import { DirectionResultCard } from "@/components/create/DirectionResultCard";
import { ConsolidationPanel } from "@/components/create/ConsolidationPanel";
import type { LayeredConceptRouteMeta, LayeredLayerSnapshot } from "@/types/conceptRoute";
import { hashContracts, isContractDriftedSinceConfirm } from "@/lib/subsystemHash";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/hooks/api/useQueryConfig";
import type { SpatialEstimate, BBox } from "@/types/generated/subsystem";
import type { MustCriterionResult } from "@/lib/api";
import type { PackageMap } from "@/types/generated/subsystem";
import { useSubsystemSuggestion } from "@/hooks/api/useSubsystemSuggestion";
import { useProject } from "@/hooks/api/useProjects";
// TODO: Replace with useKnowledgeRefs hook once knowledge_refs DB table is created (Sprint 5+)
import { MissionContext } from "@/components/create/MissionContext";
import { CreateStepper } from "@/components/create/CreateStepper";
import { KnowledgeRefsPanel } from "@/components/create/KnowledgeRefsPanel";
import { SubsystemHierarchyView } from "@/components/create/SubsystemHierarchyView";
import { PackageMapPanel } from "@/components/create/PackageMapPanel";
import { SpatialOverlayDialog } from "@/components/create/SpatialOverlayDialog";
import type { OverlayPayload, OverlayResult } from "@/components/create/SpatialOverlayDialog";
import { SpatialOverrideDialog } from "@/components/create/SpatialOverrideDialog";
import { PromoteToLearnedDialog } from "@/components/create/PromoteToLearnedDialog";
import { LayoutGrid, List } from "lucide-react";
import ConvergenceGraph from "@/components/solution/ConvergenceGraph";
import { useConvergenceLoop } from "@/hooks/useConvergenceLoop";
import { ConvergenceDashboard } from "@/components/create/ConvergenceDashboard";
// BranchExplorationPanel removed — Phase A has no branch concept, Phase B uses Decision Hub
import { HumanReviewPanel } from "@/components/create/HumanReviewPanel";
import { ArchitectureHaltOverlay } from "@/components/create/ArchitectureHaltOverlay";
import { MultiSolutionAdoptionPanel } from "@/components/create/MultiSolutionAdoptionPanel";
import { useConceptRoutes, useCompatibilityPairs } from "@/hooks/api/useConceptRoutes";
// TODO: Replace with API when available -- AI-generated adoption state, no dedicated DB table yet
import type { ConceptRoute, MultiSolutionAdoptionState } from "@/types/conceptRoute";

const RADAR_COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--destructive))",
  "hsl(var(--accent))",
  "#10B981",
];

const STEPS = [
  { label: "跨域去錨定 (TRIZ L1)", shortLabel: "去錨定", description: "已整合至 TRIZ L1 — 從約束出發產出非典型架構概念", zone: "reverse" as const }, // v3.0: renamed from Anti-Anchor
  { label: "正向分析：TRIZ 解矛盾", shortLabel: "TRIZ", description: "從矛盾出發 → 分層 drill-down 診斷（L1 現象 / L2 根因 / L3 結構）→ 子系統分解", zone: "forward" as const },
  { label: "正向分析：子系統定義", shortLabel: "子系統", description: "識別受矛盾影響的子系統 (System→Module→Component)，聚焦變形範圍", zone: "forward" as const },
  { label: "候選方案決策中心", shortLabel: "決策中心", description: "攤平兩條路徑的所有方案，橫向比較來源、機制、假設、驗證需求與信心等級", zone: "hub" as const },
  { label: "MUST 快篩", shortLabel: "MUST", description: "以必要條件（M1-M6）快速淘汰不可行方案", zone: "eval" as const },
  { label: "Pre-CAD 審查", shortLabel: "Pre-CAD", description: "五維審查：MUST/解耦/可驗證性/失效機制/MVP CAD", zone: "eval" as const },
];

const ZONE_LABELS: Record<string, { badge: string; color: string }> = {
  reverse: { badge: "反向路徑", color: "bg-amber-100 text-amber-700" },
  forward: { badge: "正向路徑", color: "bg-blue-100 text-blue-700" },
  hub: { badge: "決策中心", color: "bg-violet-100 text-violet-700" },
  eval: { badge: "統一評估", color: "bg-green-100 text-green-700" },
};

const MOCK_MISSION = {
  problemStatement: "設計一款中驅電動自行車傳動系統，在 ≤65dB 噪音下達成 25km/h 極速與 15% 坡度爬坡能力",
  contradictions: [
    { id: "EC-001", description: "馬達轉速提升 → 輸出功率增加，但噪音同步惡化" },
    { id: "EC-002", description: "殼體需高結構強度，但重量需控制在目標範圍內" },
  ],
  verifiedAssumptions: 1,
  totalAssumptions: 7,
  highRiskCount: 3,
};

// v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1 flow
// Mock data kept for backward compatibility
const MOCK_AI_ANTIANCHOR: AntiAnchorRoute[] = [
  { id: "aar-ai-001", name: "直驅輪轂方案", description: "完全捨棄傳統中驅+傳動系統，改用輪轂馬達直接驅動後輪，消除傳動效率損失與噪音來源。與競品在物理介面上完全不相容。" },
  { id: "aar-ai-002", name: "磁力耦合無接觸傳動方案", description: "以磁力耦合器取代機械齒輪嚙合，實現非接觸傳動。消除齒輪磨耗噪音，簡化密封設計，但需克服扭矩傳遞效率問題。" },
  { id: "aar-ai-003", name: "液壓靜態傳動方案", description: "以微型液壓泵-馬達迴路替代機械傳動鏈，實現無段變速。運轉噪音極低但系統重量與成本需評估。屬非對標路線。" },
];

export default function Create() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [activeTrack, setActiveTrack] = useState<"reverse" | "forward" | null>("reverse");

  // ── Project data (for must_criteria_config) ──
  const projectQuery = useProject(id);
  const mustCriteria: MustCriterion[] = useMemo(() => {
    const config = projectQuery.data?.must_criteria_config;
    if (config && config.length > 0) return config;
    return DEFAULT_MUST_CRITERIA;
  }, [projectQuery.data]);
  const MUST_KEYS = useMemo(() => mustCriteria.map(c => c.id), [mustCriteria]);

  // AI MUST evaluation results (keyed by altId)
  const [mustAiResults, setMustAiResults] = useState<Record<string, MustCriterionResult[]>>({});

  // ── API Hooks: queries ──
  const antiAnchorQuery = useAntiAnchorRoutes(id);
  const trizQuery = useTrizSolutions(id);
  const subsystemsQuery = useSubsystems(id);
  const alternativesQuery = useAlternatives(id);
  const conceptRoutesQuery = useConceptRoutes(id);
  const compatibilityPairsQuery = useCompatibilityPairs(id);
  const trackAssumptionsQuery = useTrackAssumptions(id);
  const contradictionsQuery = useContradictions(id);
  // v7 persistence: LTS rows upserted by backend `/triz/solve-layered` live in
  // Supabase `layered_triz_solutions`. Hydrate on mount so page reload / tab
  // switch keeps the drill-down results instead of wiping in-memory state.
  const layeredQuery = useLayeredTrizSolutions(id);
  // v8 persistence: directed solutions upserted by backend `/triz/solve-directed`
  // live in Supabase `directed_triz_solutions`. Hydrate on mount so page reload
  // keeps direction analysis results.
  const directedQuery = useDirectedTrizSolutions(id);
  // v8 persistence: consolidation result (migration 012).
  const consolidationQuery = useTrizConsolidationResult(id);

  // ── Phase 1 context ──
  const { data: brief } = useBrief(id);
  const { data: briefConstraints = [] } = useConstraints(id);
  const { data: briefKpis = [] } = useKpis(id);

  // Access Socratic Q&A materials
  const { data: socraticQuestions = [] } = useSocraticQuestions(id);

  const briefMission = brief?.mission || '';
  const constraintStrings = useMemo(
    () => briefConstraints.map((c) => `[${c.constraintCode}] ${c.description} (${c.type})`),
    [briefConstraints],
  );
  const kpiStrings = useMemo(
    () => briefKpis.map((k) => `${k.kpiName}: ${k.targetValue} ${k.unit}`),
    [briefKpis],
  );
  const contradictionDescs = useMemo(
    () => (contradictionsQuery.data || []).map((c) => c.engineeringStatement || c.naturalDescription || '').filter(Boolean),
    [contradictionsQuery.data],
  );
  const socraticQaStrings = useMemo(
    () => socraticQuestions
      .filter((q) => q.answer && q.answer.trim().length > 0)
      .map((q) => `[${q.category}] Q: ${q.text} → A: ${q.answer}`),
    [socraticQuestions],
  );

  // ── API Hooks: mutations ──
  const createAntiAnchorRoute = useCreateAntiAnchorRoute();
  const updateAntiAnchorRoute = useUpdateAntiAnchorRoute();
  const deleteAntiAnchorRouteMut = useDeleteAntiAnchorRoute();
  const createTrizSolution = useCreateTrizSolution();
  const updateTrizSolution = useUpdateTrizSolution();
  const createSubsystem = useCreateSubsystem();
  const updateSubsystemMut = useUpdateSubsystem();
  const deleteSubsystemMut = useDeleteSubsystem();
  const createAlternative = useCreateAlternative();
  const updateAlternativeMut = useUpdateAlternative();
  const deleteAlternativeMut = useDeleteAlternative();

  // ── Derived data from queries (with local overrides for optimistic UI) ──
  const [localRoutes, setLocalRoutes] = useState<AntiAnchorRoute[]>([]);
  const [localTrizSolutions, setLocalTrizSolutions] = useState<TrizSolution[]>([]);
  // v7 (WP 7.2/7.3/8.x/9.5): layered drill-down state. Keyed by contradiction_id
  // so each contradiction maps to exactly one LayeredTrizSolution card. Only
  // v7/v8 layered drill-down state. Keyed by contradiction_id.
  const [layeredSolutions, setLayeredSolutions] = useState<Record<string, LayeredTrizSolution>>({});
  // Hydrate LTS state from Supabase on project load. Local optimistic updates
  // (setLayeredSolutions after a fresh solve) win over server values because
  // React Query refetch lags behind the in-flight POST by one tick — merging
  // `prev` last preserves the just-computed entry until refetch completes.
  useEffect(() => {
    if (layeredQuery.data) {
      setLayeredSolutions((prev) => ({ ...layeredQuery.data, ...prev }));
    }
  }, [layeredQuery.data]);
  // v8: Hydrate directed TRIZ results from DB on mount / refetch.
  // Local optimistic updates (from in-flight solve) win via `...prev` last.
  useEffect(() => {
    if (directedQuery.data && Object.keys(directedQuery.data).length > 0) {
      setDirectedResults((prev) => ({ ...directedQuery.data, ...prev }));
      // Mark DB-loaded results as 'done' in status map (don't overwrite in-flight states)
      setDirectedStatusMap((prev) => {
        const next = { ...prev };
        for (const cid of Object.keys(directedQuery.data!)) {
          if (!next[cid]) next[cid] = 'done';
        }
        return next;
      });
    }
  }, [directedQuery.data]);
  // v8: Hydrate consolidation result from DB on mount / refetch.
  useEffect(() => {
    if (consolidationQuery.data) {
      setConsolidationResult((prev) => prev ?? consolidationQuery.data);
    }
  }, [consolidationQuery.data]);
  // 9.2.4: Per-contradiction independent loading state
  const [solvingIds, setSolvingIds] = useState<Set<string>>(new Set());
  // WP 7.2: per-project quick_mode toggle. Defaults to false.
  const [trizQuickMode, setTrizQuickMode] = useState<boolean>(false);

  // v8: Direction-centric TRIZ solver state
  const [directedResults, setDirectedResults] = useState<Record<string, ContradictionDirectionResult>>({});
  const [consolidationResult, setConsolidationResult] = useState<ConsolidationResult | null>(null);
  const [directedStatusMap, setDirectedStatusMap] = useState<Record<string, 'pending' | 'solving' | 'done' | 'failed'>>({});
  const [directedErrors, setDirectedErrors] = useState<Record<string, string>>({});
  const [directedConsolidating, setDirectedConsolidating] = useState(false);

  // v8: Directed TRIZ — solve only top-level TC contradictions
  // PC and SF are derived internally by the backend from each TC
  const handleDirectedSolveAll = async () => {
    if (!id) return;
    // Only process top-level TC contradictions (no parentContradictionId)
    const contrs = (contradictionsQuery.data ?? []).filter(c => !c.parentContradictionId);
    if (contrs.length === 0) {
      toast.warning("尚未識別任何頂層 TC 矛盾，請先在「深度探索」階段完成矛盾識別");
      return;
    }
    setAiLoading((p) => ({ ...p, directedTriz: true }));
    // Initialize all as pending; clear previous results
    const initStatus: Record<string, 'pending' | 'solving' | 'done' | 'failed'> = {};
    contrs.forEach(c => { initStatus[c.id] = 'pending'; });
    setDirectedStatusMap(initStatus);
    setDirectedErrors({});
    setDirectedResults({});
    setConsolidationResult(null);

    const results: ContradictionDirectionResult[] = [];
    for (const c of contrs) {
      try {
        setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'solving' }));
        const resp = await trizSolveDirected({
          project_id: id,
          contradiction_id: c.id,
          natural_description: c.naturalDescription || c.engineeringStatement || '',
          severity: (c.severity as 'fatal' | 'major' | 'minor' | 'unknown') || 'unknown',
          improving_param: c.improvingParam ?? undefined,
          worsening_param: c.worseningParam ?? undefined,
        });
        setDirectedResults((prev) => ({ ...prev, [c.id]: resp.result }));
        setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'done' }));
        results.push(resp.result);
      } catch (err) {
        console.error(`directed solve failed for ${c.id}:`, err);
        const msg = err instanceof Error ? err.message : String(err);
        setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'failed' }));
        setDirectedErrors((prev) => ({ ...prev, [c.id]: msg.slice(0, 200) }));
      }
    }

    // Auto-consolidate if we have ≥2 results
    if (results.length >= 2) {
      try {
        setDirectedConsolidating(true);
        const consResp = await trizConsolidate({ project_id: id, results });
        setConsolidationResult(consResp.consolidation);
        toast.success(`跨矛盾整併完成：${consResp.consolidation.status === 'compatible' ? '全部相容 ✓' : consResp.consolidation.status === 'resolved_with_swap' ? '替換後相容' : '存在衝突'}`);
      } catch (err) {
        console.error('consolidation failed:', err);
        toast.error('跨矛盾整併失敗');
      } finally {
        setDirectedConsolidating(false);
      }
    } else if (results.length === 1) {
      // Single contradiction: build a local ConsolidationResult so the panel renders
      const singleResult = results[0];
      const singleConsolidation: ConsolidationResult = {
        status: 'compatible',
        adopted_directions: singleResult.top1
          ? { [singleResult.contradiction_id]: singleResult.top1 }
          : {},
        conflict_report: null,
        integration_advice: singleResult.top1
          ? `唯一矛盾「${singleResult.natural_description}」的首選方向：${singleResult.top1.direction_name}。`
          : '',
      };
      setConsolidationResult(singleConsolidation);
      // Persist to DB so page reload also shows the panel
      upsertConsolidationResult(id, singleConsolidation).catch((err) =>
        console.warn('persist single-contradiction consolidation failed:', err),
      );
      toast.success('已為 1 條矛盾產出方向分析');
    } else {
      toast.error('方向求解全部失敗');
    }
    setAiLoading((p) => ({ ...p, directedTriz: false }));
  };

  // v8: Per-contradiction retry for directed TRIZ solving
  const handleDirectedSolveSingle = async (contradictionId: string) => {
    if (!id) return;
    const c = (contradictionsQuery.data ?? []).find(x => x.id === contradictionId);
    if (!c) return;

    setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'solving' }));
    setDirectedErrors((prev) => { const n = { ...prev }; delete n[c.id]; return n; });

    try {
      const resp = await trizSolveDirected({
        project_id: id,
        contradiction_id: c.id,
        natural_description: c.naturalDescription || c.engineeringStatement || '',
        severity: (c.severity as 'fatal' | 'major' | 'minor' | 'unknown') || 'unknown',
        improving_param: c.improvingParam ?? undefined,
        worsening_param: c.worseningParam ?? undefined,
      });

      // Collect all done results for re-consolidation
      let allResults: ContradictionDirectionResult[] = [];
      setDirectedResults((prev) => {
        const next = { ...prev, [c.id]: resp.result };
        allResults = Object.values(next);
        return next;
      });
      setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'done' }));
      toast.success(`${(c.naturalDescription || c.id).slice(0, 30)} 重試成功`);

      // Auto re-consolidate if ≥2 done results
      if (allResults.length >= 2) {
        try {
          setDirectedConsolidating(true);
          setConsolidationResult(null);
          const consResp = await trizConsolidate({ project_id: id, results: allResults });
          setConsolidationResult(consResp.consolidation);
        } catch (err) {
          console.error('re-consolidation failed:', err);
        } finally {
          setDirectedConsolidating(false);
        }
      }
    } catch (err) {
      console.error(`directed solve retry failed for ${c.id}:`, err);
      const msg = err instanceof Error ? err.message : String(err);
      setDirectedStatusMap((prev) => ({ ...prev, [c.id]: 'failed' }));
      setDirectedErrors((prev) => ({ ...prev, [c.id]: msg.slice(0, 200) }));
      toast.error(`${(c.naturalDescription || c.id).slice(0, 30)} 重試失敗`);
    }
  };

  // WBS 7.4: reusable per-contradiction lazy solve helper.
  const solveSingleContradiction = async (c: ExploreContradiction): Promise<[string, LayeredTrizSolution] | null> => {
    if (!id) return null;
    const pickSeverity = (raw: unknown): TrizSeverity => {
      const allowed: TrizSeverity[] = ['fatal', 'major', 'minor', 'unknown'];
      return (allowed.includes(raw as TrizSeverity) ? raw : 'unknown') as TrizSeverity;
    };
    const cType = c.type as 'TC' | 'PC' | 'SF';
    const cAny = c as unknown as Record<string, unknown>;
    const isChildPC = !!c.parentContradictionId;
    const hintFields = isChildPC ? {
      separation_principle_id: c.separationPrincipleId ?? undefined,
      separation_category: c.separationCategory ?? undefined,
      separation_rationale: c.separationRationale ?? undefined,
      derived_parameter: c.derivedParameter ?? undefined,
    } : {};
    const pcDesc = (isChildPC && c.pcAttributeA && c.pcAttributeNotA)
      ? `${c.derivedParameter ?? ''} 必須 ${c.pcAttributeA} 且必須 ${c.pcAttributeNotA}`
      : (cType === 'PC' ? c.physicalContradiction : undefined);
    try {
      setSolvingIds(prev => new Set(prev).add(c.id));
      const resp = await trizSolveLayered({
        project_id: id,
        contradiction_id: c.id,
        natural_description: c.naturalDescription,
        severity: pickSeverity(c.severity ?? cAny.severity),
        // ADR-007: Explore 階段 TC-only；PC/SF 由後端於 solve_triz_layered 入口派生
        improving_param: c.improvingParam ?? undefined,
        worsening_param: c.worseningParam ?? undefined,
        physical_contradiction: pcDesc,
        // sf_* 保留但通常為 null；後端會派生；舊 DB 若有 SF 資料亦可被傳入當 hint
        sf_substance_1: (cAny.sfSubstance1 as string | undefined) ?? undefined,
        sf_substance_2: (cAny.sfSubstance2 as string | undefined) ?? undefined,
        sf_field: (cAny.sfField as string | undefined) ?? undefined,
        quick_mode: trizQuickMode,
        ...hintFields,
      });
      setSolvingIds(prev => { const next = new Set(prev); next.delete(c.id); return next; });
      setLayeredSolutions(prev => ({ ...prev, [c.id]: resp.layered_solution }));
      queryClient.invalidateQueries({ queryKey: queryKeys.layered_triz_solutions.byProject(id) });
      return [c.id, resp.layered_solution];
    } catch (err) {
      const desc = (c.naturalDescription || c.engineeringStatement || c.id).slice(0, 60);
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`trizSolveLayered failed for ${c.id}:`, err);
      toast.error(`求解失敗：${desc}`, { description: msg.slice(0, 120) });
      setSolvingIds(prev => { const next = new Set(prev); next.delete(c.id); return next; });
      return null;
    }
  };

  // WBS 7.4: per-row lazy solve handler.
  const handleSolveSingle = async (contradictionId: string) => {
    const contrs = contradictionsQuery.data ?? [];
    const c = contrs.find(x => x.id === contradictionId);
    if (!c) return;
    const result = await solveSingleContradiction(c);
    if (result) {
      toast.success(`已為 "${c.naturalDescription?.slice(0, 30) ?? c.id.slice(0, 8)}" 產出分層診斷`);
    } else {
      toast.error(`"${c.naturalDescription?.slice(0, 30) ?? c.id.slice(0, 8)}" 求解失敗`);
    }
  };
  const [localSubsystems, setLocalSubsystems] = useState<Subsystem[]>([]);
  const [localAlternatives, setLocalAlternatives] = useState<Alternative[]>([]);

  // Sync query data → local state
  useEffect(() => { setLocalRoutes(antiAnchorQuery.data); }, [antiAnchorQuery.data]);
  useEffect(() => { setLocalTrizSolutions(trizQuery.data); }, [trizQuery.data]);
  useEffect(() => { setLocalSubsystems(subsystemsQuery.data); }, [subsystemsQuery.data]);
  useEffect(() => { setLocalAlternatives(alternativesQuery.data); }, [alternativesQuery.data]);
  // Refetch contradictions on mount AND when returning to this page
  // (staleTime=30s means Explore deletions may not reflect immediately)
  useEffect(() => {
    if (id) {
      contradictionsQuery.refetch();
    }
  }, [id, currentStep]);

  // Use local state as the working data (allows optimistic updates)
  const routes = localRoutes;
  const trizSolutions = localTrizSolutions;
  const subsystems = localSubsystems;
  const alternatives = localAlternatives;

  // Derived: true when DB or optimistic routes exist (no separate state needed)
  const antiAnchorGenerated = routes.length > 0;
  const [selectedAltId, setSelectedAltId] = useState<string | null>(null);
  const [comparedAltIds, setComparedAltIds] = useState<Set<string>>(new Set());
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  // Phase B is now manually triggered from the Decision Hub (X1),
  // NOT auto-triggered when Phase A converges. This prevents the infinite
  // loop caused by TC/PC/SF solutions from the same contradiction conflicting.

  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [conceptRoutes, setConceptRoutes] = useState<ConceptRoute[]>([]);

  // v7 WP 10.6: build `layered_directives` from adopted layered ConceptRoutes.
  // When Phase B runs, the backend scanner uses these to SKIP intra-LTS
  // cross-layer pairs (same lts_id + same contradiction_id) and WARN on cross-
  // LTS redundancy, per `check_phase_b_conflict` in evaluator.py.
  const layeredDirectives = useMemo(() => {
    return conceptRoutes
      .filter((r) => r.layered && r.layered.adoptedLayers.length > 0)
      .map((r) => ({
        alternative_id: r.id,
        lts_id: r.layered!.ltsId,
        adopted_layers: r.layered!.adoptedLayers,
        same_contradiction_intra_layer_conflict:
          r.layered!.phaseBDirective.sameContradictionIntraLayerConflict,
        cross_contradiction_conflict:
          r.layered!.phaseBDirective.crossContradictionConflict,
      }));
  }, [conceptRoutes]);

  const convergenceLoop = useConvergenceLoop({
    projectId: id,
    contradictions: contradictionsQuery.data ?? [],
    alternatives: alternatives.map((a) => ({
      id: a.id,
      name: a.name,
      mechanism: a.mechanism,
      source: a.source,
      resolves_contradiction_ids: a.keyAssumptionIds ?? [],
    })),
    mission: briefMission,
    constraints: constraintStrings,
    kpis: kpiStrings,
    layeredDirectives,
  });
  const [subsystemView, setSubsystemView] = useState<"diagram" | "list">("diagram");
  const [showAddSubsystemForm, setShowAddSubsystemForm] = useState(false);
  const [editingSubsystemId, setEditingSubsystemId] = useState<string | null>(null);
  const [ssFormName, setSsFormName] = useState("");
  const [ssFormReason, setSsFormReason] = useState("");
  const [ssFormContradictions, setSsFormContradictions] = useState<string[]>([]);
  const [ssFormInterfaces, setSsFormInterfaces] = useState("");
  const [ssFormLevel, setSsFormLevel] = useState<SubsystemLevel>("module");
  const [ssFormParentId, setSsFormParentId] = useState<string | null>(null);
  const suggestSubsystems = useSubsystemSuggestion(id);

  // Wave 2: package_map comes back from the subsystem suggestion mutation
  // alongside `subsystems[]`. Only the subsystem tree is persisted to
  // Supabase today, so we stash the ephemeral PackageMap in component state
  // and display it via PackageMapPanel. Cleared whenever a fresh suggestion
  // is requested.
  const [packageMap, setPackageMap] = useState<PackageMap | null>(null);
  const [overlayOpen, setOverlayOpen] = useState(false);

  // Wave 3 (WBS 7.5 / 7.6) — RD inline override + promote-to-learned dialogs.
  // Both are opened from any SpatialBlock action button inside the subsystem
  // hierarchy view; the targets carry just enough context (subsystem id,
  // neighbour name, current spatial estimate) for the dialogs to prefill.
  const [overrideTarget, setOverrideTarget] = useState<{
    subsystemId: string;
    neighbour: string;
    spatial: SpatialEstimate;
  } | null>(null);
  const [promoteTarget, setPromoteTarget] = useState<{
    subsystemId: string;
    neighbour: string;
    spatial: SpatialEstimate;
  } | null>(null);
  const queryClient = useQueryClient();

  // Loading state — true while any query is loading
  const isLoading = antiAnchorQuery.isLoading || trizQuery.isLoading || subsystemsQuery.isLoading || alternativesQuery.isLoading;

  // antiAnchorGenerated is now derived from routes.length — no effect needed

  // ── Computed: Multi-Solution Adoption State from DB ──
  const emptyAdoptionState: MultiSolutionAdoptionState = {
    matrix: { solutions: [], pairs: [] },
    recommendedRoutes: [],
    antiPatternChecks: [],
  };
  const adoptionState: MultiSolutionAdoptionState = useMemo(() => {
    const dbRoutes = conceptRoutesQuery.data;
    const dbPairs = compatibilityPairsQuery.data;

    if (dbRoutes && dbRoutes.length > 0 && dbPairs && dbPairs.length > 0) {
      return {
        matrix: {
          // TODO: Build solutions list from convergence loop output or DB query
          solutions: [],
          pairs: dbPairs,
        },
        recommendedRoutes: dbRoutes,
        // TODO: Compute anti-pattern checks from routes + pairs via AI API
        antiPatternChecks: [],
      };
    }
    return emptyAdoptionState;
  }, [conceptRoutesQuery.data, compatibilityPairsQuery.data]);

  const assumptionMap = useMemo(() => {
    const map = new Map<string, { code: string; description: string }>();
    const assumptions = trackAssumptionsQuery.data ?? [];
    assumptions.forEach((a) => map.set(a.id, { code: a.assumptionCode, description: a.description }));
    return map;
  }, [trackAssumptionsQuery.data]);

  /** Map contradiction ID → short label for display */
  const contradictionMap = useMemo(() => {
    const map = new Map<string, string>();
    (contradictionsQuery.data ?? []).forEach((c) => {
      map.set(c.id, c.engineeringStatement || c.naturalDescription || c.id.slice(0, 8));
    });
    return map;
  }, [contradictionsQuery.data]);

  // ── 9.2.1: Group contradictions by parent for tree-aware solve ──
  const childrenMap = useMemo(() => {
    const map = new Map<string, Contradiction[]>();
    for (const c of contradictionsQuery.data ?? []) {
      if (c.parentContradictionId) {
        const arr = map.get(c.parentContradictionId) ?? [];
        arr.push(c);
        map.set(c.parentContradictionId, arr);
      }
    }
    return map;
  }, [contradictionsQuery.data]);

  const topLevelContradictions = useMemo(
    () => (contradictionsQuery.data ?? []).filter(c => !c.parentContradictionId),
    [contradictionsQuery.data],
  );

  // Group TRIZ solutions by contradiction for display (used in renderTrizConvergence)
  const trizByContradiction = useMemo(() => {
    const map = new Map<string, TrizSolution[]>();
    for (const ts of trizSolutions) {
      const key = ts.contradictionId || '__unlinked';
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(ts);
    }
    return map;
  }, [trizSolutions]);

  // Added: Entries sorted by TC > PC > SF
  const PATH_ORDER = { TC: 0, PC: 1, SF: 2 } as const;

  const sortedTrizEntries = useMemo(() => {
    return Array.from(trizByContradiction.entries()).sort(([, aSols], [, bSols]) => {
      const aPath = aSols[0]?.path ?? 'SF';
      const bPath = bSols[0]?.path ?? 'SF';
      const aOrder = PATH_ORDER[aPath as keyof typeof PATH_ORDER] ?? 99;
      const bOrder = PATH_ORDER[bPath as keyof typeof PATH_ORDER] ?? 99;
      return aOrder - bOrder;
    });
  }, [trizByContradiction]);

  // v7 (WP 10.5): Decision Hub cross-alternative warnings.
  //
  // Legacy v6 flagged "same-contradiction multi-path" as a risk because
  // TC/PC/SF were treated as mutually-exclusive solvers. v7 turns that into a
  // drill-down diagnosis: multiple layers of the SAME `LayeredTrizSolution`
  // (same lts_id) are the INTENDED adoption pattern and must NOT warn — only
  // DIFFERENT LTS ids resolving the same contradiction indicate redundancy.
  // See `backend/app/agents/evaluator.py::check_phase_b_conflict`.
  const crossLtsRedundancyWarnings = useMemo(() => {
    const byContradiction = new Map<string, { alt: Alternative; ltsId: string | null }[]>();
    for (const alt of alternatives) {
      for (const cid of alt.keyAssumptionIds) {
        if (!byContradiction.has(cid)) byContradiction.set(cid, []);
        // Find the ConceptRoute that backs this alternative (if any) so we
        // can read its LTS id. Legacy single/composite routes return null.
        const route = conceptRoutes.find((r) => r.id === alt.id || r.layered?.ltsId === alt.id);
        const ltsId = route?.layered?.ltsId ?? null;
        byContradiction.get(cid)!.push({ alt, ltsId });
      }
    }
    const warnings: { contradictionId: string; alts: Alternative[] }[] = [];
    for (const [cid, entries] of byContradiction.entries()) {
      if (entries.length <= 1) continue;
      // Count distinct non-null LTS ids. Entries sharing one LTS = drill-down → SKIP.
      // Entries with null LTS (legacy) default to legacy behaviour: flag.
      const distinctLtsIds = new Set(entries.map((e) => e.ltsId).filter((x): x is string => x !== null));
      const legacyCount = entries.filter((e) => e.ltsId === null).length;
      const isIntraLtsOnly = distinctLtsIds.size <= 1 && legacyCount === 0;
      if (isIntraLtsOnly) continue; // all same LTS → drill-down, no warning
      warnings.push({ contradictionId: cid, alts: entries.map((e) => e.alt) });
    }
    return warnings;
  }, [alternatives, conceptRoutes]);

  const getMustValues = (a: Alternative) => MUST_KEYS.map((k) => a.mustScores[k] ?? null);

  const stepStatuses: AccordionStepStatus[] = useMemo(() => {
    const s1 = routes.length >= 3 ? "complete" : routes.length > 0 ? "in_progress" : "not_started";
    // s2: TRIZ convergence — use DB trizSolutions when convergenceLoop hasn't run
    const loopDone = convergenceLoop.state.status === "converged";
    const hasTrizData = trizSolutions.length > 0;
    const s2 = loopDone || hasTrizData ? "complete" : convergenceLoop.state.status !== "idle" ? "in_progress" : "not_started";
    const confirmed = subsystems.filter((s) => s.confirmed).length;
    const s3 = confirmed > 0 ? "complete" : subsystems.length > 0 ? "in_progress" : "not_started";
    const s4 = alternatives.length > 0 ? "complete" : "not_started";
    // s5: Only check M1-M6 keys, not the nested bundle fields
    const allMustFilled = alternatives.length > 0 && alternatives.every((a) => getMustValues(a).every((v) => v !== null));
    const s5 = allMustFilled ? "complete" : alternatives.some((a) => getMustValues(a).some((v) => v !== null)) ? "in_progress" : "not_started";
    const passedMust = alternatives.filter((a) => !getMustValues(a).includes("fail"));
    const allScored = passedMust.length > 0 && passedMust.every((a) => Object.values(a.preCadScores).every((v) => v !== null));
    const s6 = allScored ? "complete" : passedMust.some((a) => Object.values(a.preCadScores).some((v) => v !== null)) ? "in_progress" : "not_started";
    return [s1, s2, s3, s4, s5, s6];
  }, [routes, convergenceLoop.state.status, trizSolutions, subsystems, alternatives]);

  const autoSave = useCallback(() => {
    setSaveStatus("saving");
    setTimeout(() => {
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    }, 500);
  }, []);

  const passedMustAlts = alternatives.filter((a) => !Object.values(a.mustScores).includes("fail") && Object.values(a.mustScores).every((v) => v !== null));
  const preCadPassedAlts = alternatives.filter((a) => a.overallPass === true);

  const gate22Items: CreateGateItem[] = useMemo(
    () => [
      { label: "≥2 方案通過 MUST 快篩", current: passedMustAlts.length, target: 2, passed: passedMustAlts.length >= 2 },
      { label: "MUST 快篩已完成", current: stepStatuses[4] === "complete" ? 1 : 0, target: 1, passed: stepStatuses[4] === "complete" },
    ],
    [passedMustAlts, stepStatuses]
  );

  const phaseGate2Items: CreateGateItem[] = useMemo(
    () => [{ label: "≥1 方案 Pre-CAD overall_pass = True", current: preCadPassedAlts.length, target: 1, passed: preCadPassedAlts.length >= 1 }],
    [preCadPassedAlts]
  );

  // Handlers
  // v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1 flow
  const handleAiGenAntiAnchor = async () => {
    if (!id) return;
    setAiLoading((p) => ({ ...p, antiAnchor: true }));
    try {
      // Clear existing routes before regenerating
      for (const r of routes) {
        deleteAntiAnchorRouteMut.mutate({ id: r.id });
      }
      setLocalRoutes([]);

      const result = await antiAnchorGenerate({
        project_id: id,
        mission: briefMission || MOCK_MISSION.problemStatement,
        current_constraints: constraintStrings.length > 0
          ? constraintStrings
          : MOCK_MISSION.contradictions.map((c) => c.description),
        existing_alternatives: [],
        socraticAnswers: socraticQaStrings,
      });
      // Optimistic: build display data from API result immediately
      const optimistic: AntiAnchorRoute[] = result.routes.map((route, i) => ({
        id: `aa-opt-${Date.now()}-${i}`,
        name: route.name,
        mechanism: route.mechanism,
        description: route.description || route.mechanism,
        whyUnconventional: route.why_unconventional,
        potentialAdvantage: route.potential_advantage,
        crossDomainSource: route.cross_domain_source,
        validationPassport: route.validation_passport as unknown as import("@/types/create").ValidationPassport | null,
        createdAt: new Date().toISOString(),
      }));
      setLocalRoutes(optimistic);

      // Persist to DB in background (query invalidation will replace optimistic IDs)
      for (const route of result.routes) {
        createAntiAnchorRoute.mutate({
          project_id: id,
          name: route.name,
          mechanism: route.mechanism,
          description: route.description,
          is_non_typical: route.is_non_typical,
          why_unconventional: route.why_unconventional,
          potential_advantage: route.potential_advantage,
          cross_domain_source: route.cross_domain_source,
          validation_passport: route.validation_passport as unknown as Json,
          source: 'ai',
        });
      }
      toast.success(`AI 已產出 ${result.routes.length} 條非典型架構概念`);
    } catch (err) {
      console.error("Anti-anchor generation failed:", err);
      toast.error("AI 產出失敗，請確認後端服務是否啟動");
    } finally {
      setAiLoading((p) => ({ ...p, antiAnchor: false }));
    }
  };

  // ── TRIZ layered drill-down generation ──
  const handleAiGenTriz = async () => {
    if (!id) return;
    const contrs = contradictionsQuery.data ?? [];
    if (contrs.length === 0) {
      toast.warning("尚未識別任何矛盾，請先在「深度探索」階段完成矛盾識別");
      return;
    }
    // v8 client-side pre-check (non-blocking toast).
    // Backend _run_l1 degrades gracefully when params are missing (status=error, auto-trigger L2).
    const malformedTC = contrs.filter(c => c.type === 'TC' && (!c.improvingParam || !c.worseningParam));
    if (malformedTC.length > 0) {
      toast.warning(`${malformedTC.length} 條 TC 矛盾缺少改善/惡化參數，L1 矩陣查表可能不完整`);
    }

    setAiLoading((p) => ({ ...p, trizGen: true }));

    // Layered drill-down mode: call trizSolveLayered per contradiction.
    // Results stored in `layeredSolutions` keyed by contradiction_id.
    // WBS 7.4: use solveSingleContradiction helper (reused by per-row lazy solve).
    try {
      setLayeredSolutions({});
      // Serialize per-contradiction solves so the backend isn't hit with 3× concurrent
      // multi-step LLM pipelines (L1+critic+L2+L3+differential). Parallel fan-out
      // caused /triz/solve-layered to exceed the 300s request timeout under load.
      const results: Array<[string, LayeredTrizSolution] | null> = [];
      for (const c of contrs) {
        results.push(await solveSingleContradiction(c));
      }
      const ok = results.filter(Boolean).length;
      // Refresh the persisted layered_triz_solutions cache so that subsequent
      // mounts / other tabs see the newly upserted rows without waiting for
      // the default refetch window.
      queryClient.invalidateQueries({ queryKey: queryKeys.layered_triz_solutions.byProject(id) });
      if (ok === 0) {
        toast.error('TRIZ 分層求解全部失敗');
      } else if (ok < contrs.length) {
        toast.warning(`${ok}/${contrs.length} 條矛盾產出分層診斷`);
      } else {
        toast.success(`已為 ${ok} 條矛盾產出分層 drill-down 診斷`);
      }
    } catch (err) {
      console.error('Layered TRIZ generation failed:', err);
      toast.error('TRIZ 分層求解失敗');
    } finally {
      setAiLoading((p) => ({ ...p, trizGen: false }));
    }
  };

  // ── v7 (WP 9.2/9.4/9.5): layered adoption handlers ────────────────────
  // When RD clicks [採納推薦路線] / [自訂組合] / [只採 L1 快速路線] on a
  // LayeredSolutionCard, produce a `type='layered'` ConceptRoute and push it
  // into the local `conceptRoutes` state. Supabase persistence (WP 11.6) is
  // still pending migration apply; for now the route lives in FE memory and
  // flows through the decision hub for Phase B cross-check.
  const handleLayeredAdopt = (
    solution: LayeredTrizSolution,
    mode: AdoptionMode,
    layers: AdoptedLayerId[],
  ) => {
    const availableLayers: AdoptedLayerId[] = ['L1'];
    if (solution.l2_root_cause && solution.l2_root_cause.status === 'ran') availableLayers.push('L2');
    if (solution.l3_structural_check.status === 'ran') availableLayers.push('L3');

    // WP 10.3/10.4: build per-layer snapshots so the decision hub can render
    // second/third eye content without re-fetching the LTS from backend.
    const layerSnapshots: LayeredLayerSnapshot[] = [];
    const l1 = solution.l1_surface;
    layerSnapshots.push({
      layer: 'L1',
      depthIndicator: l1.depth_indicator,
      mechanismSummary: l1.suggestions[0]?.suggestion ?? '(無具體建議)',
      suggestionCount: l1.suggestions.length,
      principleHits: l1.candidate_principles,
      evidenceLevelFloor: l1.evidence_level_floor,
      effortHint: 'low',
      assumptions: l1.critic_reason ? [`critic: ${l1.critic_reason}`] : [],
      validationPassport: {
        mechanism: l1.suggestions[0]?.principle_name ?? '(TC matrix lookup)',
        keyAssumptions: l1.critic_reason ? [l1.critic_reason] : [],
        failConditions: l1.critic_trigger_l2 ? ['trade-off 折衷 — L2 根因未解'] : [],
        evidenceLevel: l1.evidence_level_floor,
        effort: 'low',
        gain: l1.suggestions[0]?.suggestion?.slice(0, 60),
      },
    });
    const l2 = solution.l2_root_cause;
    if (l2 && l2.status === 'ran') {
      const topSep = l2.deepen_link?.separation_type_candidates[0];
      layerSnapshots.push({
        layer: 'L2',
        depthIndicator: l2.depth_indicator,
        mechanismSummary: l2.suggestions[0]?.suggestion ?? '(無 L2 建議)',
        suggestionCount: l2.suggestions.length,
        principleHits: [],
        evidenceLevelFloor: l2.evidence_level_floor,
        effortHint: 'medium-high',
        assumptions: l2.trigger_reason ? [`trigger: ${l2.trigger_reason}`] : [],
        deepenLink: l2.deepen_link
          ? {
              derivedParameter: l2.deepen_link.derived_physical_parameter,
              contradictionStatement: l2.deepen_link.contradiction_statement,
              separationType: topSep
                ? `${topSep.type} (${topSep.confidence.toFixed(2)})`
                : '(未指定)',
            }
          : undefined,
        validationPassport: {
          mechanism: l2.deepen_link
            ? `PC 根因 (${l2.deepen_link.derived_physical_parameter})`
            : l2.suggestions[0]?.principle_name ?? '(L2)',
          keyAssumptions: [
            ...(l2.trigger_reason ? [`trigger: ${l2.trigger_reason}`] : []),
            ...(l2.deepen_link ? [`separation: ${topSep?.type ?? 'unknown'}`] : []),
          ],
          failConditions: l2.deepen_link?.contradiction_statement
            ? [`若 "${l2.deepen_link.contradiction_statement}" 假設不成立`]
            : [],
          evidenceLevel: l2.evidence_level_floor,
          effort: 'medium-high',
          gain: l2.suggestions[0]?.suggestion?.slice(0, 60),
        },
      });
    }
    const l3 = solution.l3_structural_check;
    layerSnapshots.push({
      layer: 'L3',
      depthIndicator: l3.depth_indicator,
      mechanismSummary: l3.suggestions[0]?.suggestion ?? '(無 L3 建議)',
      suggestionCount: l3.suggestions.length,
      principleHits: [],
      evidenceLevelFloor: l3.evidence_level_floor,
      effortHint: 'medium',
      assumptions: l3.matched_standard_solutions.length > 0
        ? [`Su-Field matched: ${l3.matched_standard_solutions.join(', ')}`]
        : [],
      bridgeText: {
        supportsL1: l3.supports_l1,
        supportsL2: l3.supports_l2,
        standaloneValue: l3.standalone_value,
      },
      validationPassport: {
        mechanism: l3.su_field_model.state !== 'unknown'
          ? `Su-Field (${l3.su_field_model.state}): ${l3.su_field_model.S1}/${l3.su_field_model.S2}/${l3.su_field_model.F}`
          : '(SF structural lens)',
        keyAssumptions: l3.matched_standard_solutions.length > 0
          ? [`標準解 ${l3.matched_standard_solutions.join(', ')} 適用`]
          : [],
        failConditions: l3.standalone_value
          ? [`若結構旁路獨立價值不成立: ${l3.standalone_value.slice(0, 60)}`]
          : [],
        evidenceLevel: l3.evidence_level_floor,
        effort: 'medium',
        gain: l3.suggestions[0]?.suggestion?.slice(0, 60),
      },
    });

    // Build the concise differential highlight — first non-empty field wins.
    const diff = solution.differential_analysis;
    const highlight =
      diff.l2_vs_l3.synergy ||
      diff.l1_vs_l2.on_solving_degree ||
      diff.l1_vs_l3.orthogonality ||
      '';

    const layeredMeta: LayeredConceptRouteMeta = {
      ltsId: solution.id,
      adoptedLayers: layers,
      availableLayers,
      recommendedRoute: solution.differential_analysis.recommended_route.primary || '',
      fallbackRoute: solution.differential_analysis.recommended_route.fallback || '',
      recommendedRationale: solution.differential_analysis.recommended_route.rationale || '',
      adoptionMode: mode,
      phaseBDirective: {
        sameContradictionIntraLayerConflict:
          solution.phase_b_directive.same_contradiction_intra_layer_conflict,
        crossContradictionConflict: solution.phase_b_directive.cross_contradiction_conflict,
      },
      layerSnapshots,
      differentialHighlight: highlight,
    };

    // v7 WP 9.3: single-layer auto-downgrade.
    // If the RD picked only ONE layer via custom mode, downgrade type to
    // `single` (or `composite` when L1 contains ≥ 2 adopted principles).
    // We still keep `layered` meta attached so Phase B can trace back to
    // the LTS id for intra-LTS SKIP; that's the critical requirement.
    let routeType: ConceptRoute['type'] = 'layered';
    if (layers.length === 1) {
      const onlyLayer = layers[0];
      if (onlyLayer === 'L1' && solution.l1_surface.suggestions.length >= 2) {
        routeType = 'composite';
      } else {
        routeType = 'single';
      }
    }

    const route: ConceptRoute = {
      id: `CR-${solution.id}-${Date.now().toString(36)}`,
      type: routeType,
      composition: [],
      compositionRationale:
        solution.differential_analysis.recommended_route.rationale ||
        `${routeType === 'layered' ? 'M6 drill-down' : 'layer subset'} 採納 ${layers.join('+')}`,
      antiPatternWarnings: [],
      // Always keep layered meta so cross-LTS WARN + intra-LTS SKIP tracing
      // can work regardless of type downgrade.
      layered: layeredMeta,
      createdAt: new Date().toISOString(),
    };

    setConceptRoutes((prev) => [...prev, route]);
    const modeLabel = routeType === 'layered' ? '分層' : routeType === 'composite' ? '合併' : '單一';
    toast.success(
      `已採納${modeLabel}路線 ${route.id}（${layers.join('+')}）→ 候選池 ${conceptRoutes.length + 1} 條`,
    );
  };

  const handleForceDeepenL2 = async (contradictionId: string) => {
    if (!id) return;
    const contrs = (contradictionsQuery.data ?? []).filter((c) => c.id === contradictionId);
    if (contrs.length === 0) return;
    const c = contrs[0];
    const cAny = c as unknown as Record<string, unknown>;
    try {
      const resp = await trizSolveLayered({
        project_id: id,
        contradiction_id: c.id,
        natural_description: c.naturalDescription,
        severity: (cAny.severity as TrizSeverity) || 'major', // force major to guarantee L2
        improving_param: c.improvingParam,
        worsening_param: c.worseningParam,
        force_l2: true,
      });
      setLayeredSolutions((prev) => ({ ...prev, [c.id]: resp.layered_solution }));
      queryClient.invalidateQueries({ queryKey: queryKeys.layered_triz_solutions.byProject(id) });
      toast.success(`已強制深挖 L2 for ${c.id}`);
    } catch (err) {
      console.error('force_l2 failed:', err);
      toast.error('L2 深挖失敗');
    }
  };

  // TRIZ state transition guard — preserve traceability of human edits
  const TRIZ_VALID_TRANSITIONS: Record<TrizActionStatus, TrizActionStatus[]> = {
    pending:  ['adopted', 'skipped'],
    adopted:  ['skipped'],
    skipped:  ['adopted'],
    edited:   ['adopted', 'skipped'],
  };
  const setTrizStatus = (tsId: string, next: TrizActionStatus) => {
    const ts = localTrizSolutions.find((t) => t.id === tsId);
    if (!ts) return;
    const current = ts.status;
    if (!TRIZ_VALID_TRANSITIONS[current].includes(next)) return;
    setLocalTrizSolutions((prev) => prev.map((t) => (t.id === tsId ? { ...t, status: next } : t)));
    updateTrizSolution.mutate({ id: tsId, status: next });

    // When adopting a TRIZ solution, mark the linked contradiction as resolved
    // in the convergence loop so the loop knows to continue toward convergence.
    if (next === 'adopted' && ts.contradictionId) {
      const contradiction = (contradictionsQuery.data ?? []).find((c) => c.id === ts.contradictionId);
      if (contradiction?.severity) {
        convergenceLoop.markResolved(ts.contradictionId, contradiction.severity);
      }
    }
  };
  const toggleSubsystem = (ssId: string) => {
    const ss = subsystems.find(s => s.id === ssId);
    if (!ss) return;
    const nextConfirmed = !ss.confirmed;
    // WBS 10.1: when RD flips to confirmed, snapshot the current interface
    // contract hash into local session state so drift detection can detect
    // post-confirmation edits. When flipping back to unconfirmed, clear it.
    // The mutation hook does not round-trip this field, so it's purely
    // in-memory — acceptable for Wave 6 per the architecture note.
    const nextHash = nextConfirmed ? hashContracts(ss.interfaceContracts) : '';
    setLocalSubsystems((prev) =>
      prev.map((s) =>
        s.id === ssId
          ? { ...s, confirmed: nextConfirmed, confirmedContractsHash: nextHash }
          : s,
      ),
    );
    updateSubsystemMut.mutate({ id: ssId, confirmed: nextConfirmed });
  };
  const addSubsystem = () => {
    if (!id || !ssFormName.trim()) { toast.error("請輸入子系統名稱"); return; }
    // Stage 4: write interface_contracts (not legacy `interfaces` string).
    // Neighbour names from the text field become empty 6-dim placeholders
    // that RD can fill in-panel later.
    createSubsystem.mutate({
      project_id: id,
      name: ssFormName.trim(),
      reason: ssFormReason.trim(),
      related_contradictions: ssFormContradictions,
      confirmed: true,
      source: "rd",
      interface_contracts: neighbourTextToContractMap(ssFormInterfaces),
      level: ssFormLevel,
      parent_id: ssFormParentId,
    });
    resetSsForm();
    setShowAddSubsystemForm(false);
  };
  const startEditSubsystem = (ssId: string) => {
    const ss = subsystems.find(s => s.id === ssId);
    if (!ss) return;
    setEditingSubsystemId(ssId);
    setSsFormName(ss.name);
    setSsFormReason(ss.reason);
    setSsFormContradictions([...ss.relatedContradictions]);
    setSsFormInterfaces(ss.interfaces?.join(", ") ?? "");
    setSsFormLevel(ss.level);
    setSsFormParentId(ss.parentId);
  };
  const saveEditSubsystem = () => {
    if (!editingSubsystemId || !ssFormName.trim()) return;
    const ss = subsystems.find(s => s.id === editingSubsystemId);
    const newSource = ss?.source === "ai" ? "ai_edited" : ss?.source;
    // Stage 4: compute the new contracts map, preserving any populated
    // 6-dim fields on neighbours that the user kept in the text list.
    const nextContracts = neighbourTextToContractMap(
      ssFormInterfaces,
      ss?.interfaceContracts ?? null,
    );
    // Optimistic local update
    setLocalSubsystems(prev => prev.map(s => {
      if (s.id !== editingSubsystemId) return s;
      return {
        ...s, name: ssFormName.trim(), reason: ssFormReason.trim(),
        relatedContradictions: ssFormContradictions,
        interfaces: nextContracts ? Object.keys(nextContracts) : [],
        interfaceContracts: nextContracts ?? undefined,
        source: (newSource ?? s.source) as SubsystemSource,
        level: ssFormLevel,
        parentId: ssFormParentId,
      };
    }));
    updateSubsystemMut.mutate({
      id: editingSubsystemId,
      name: ssFormName.trim(),
      reason: ssFormReason.trim(),
      related_contradictions: ssFormContradictions,
      interface_contracts: nextContracts,
      source: newSource,
      level: ssFormLevel,
      parent_id: ssFormParentId,
    });
    resetSsForm();
    setEditingSubsystemId(null);
  };
  // v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1 flow
  const deleteAntiAnchorRoute = (routeId: string) => {
    const idx = localRoutes.findIndex(r => r.id === routeId);
    if (idx === -1) return;
    const removed = localRoutes[idx];

    // Immediately delete from DB and optimistic UI
    setLocalRoutes(prev => prev.filter(r => r.id !== routeId));
    deleteAntiAnchorRouteMut.mutate({ id: routeId });

    toast(`已刪除「${removed.name}」`, {
      duration: 5000,
      action: {
        label: "復原",
        onClick: () => {
          // Undo = re-insert the removed item
          createAntiAnchorRoute.mutate({
            project_id: id!,
            name: removed.name,
            description: removed.description || undefined,
            is_non_typical: true,
            source: 'ai',
          });
          setLocalRoutes(prev => {
            const next = [...prev];
            next.splice(Math.min(idx, next.length), 0, removed);
            return next;
          });
        },
      },
    });
  };

  // v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1 flow
  const promoteAntiAnchorToCandidate = (routeId: string) => {
    if (!id) return;
    const route = routes.find(r => r.id === routeId);
    if (!route) return;
    createAlternative.mutate({
      project_id: id,
      name: route.name,
      mechanism: route.mechanism || route.description,
      source: "anti_anchor",
      key_assumption_ids: [],
      must_scores: { M1: null, M2: null, M3: null, M4: null, M5: null, M6: null } as unknown as Json,
      interface_contract: { envelope: '', loadPath: '', signalPath: '', thermalPath: '', datumTolerance: '', serviceability: '' } as unknown as Json,
      pre_cad_scores: { must: null, decoupling: null, testability: null, failureMech: null, mvpCadEffort: null } as unknown as Json,
      overall_pass: null,
    });
    toast.success(`「${route.name}」已晉升為候選方案（X2）`);
  };
  const deleteSubsystem = (ssId: string) => {
    const idx = localSubsystems.findIndex(s => s.id === ssId);
    if (idx === -1) return;
    const removed = localSubsystems[idx];

    setLocalSubsystems(prev => prev.filter(s => s.id !== ssId));
    deleteSubsystemMut.mutate({ id: ssId });

    toast(`已刪除「${removed.name}」`, {
      duration: 5000,
      action: {
        label: "復原",
        onClick: () => {
          createSubsystem.mutate({
            project_id: id!,
            name: removed.name,
            reason: removed.reason || undefined,
            related_contradictions: removed.relatedContradictions,
            confirmed: removed.confirmed,
            source: removed.source || "rd",
            // Stage 4: restore the full contracts map, not the legacy
            // comma-joined string.
            interface_contracts: removed.interfaceContracts ?? null,
          });
          setLocalSubsystems(prev => {
            const next = [...prev];
            next.splice(Math.min(idx, next.length), 0, removed);
            return next;
          });
        },
      },
    });
  };
  const resetSsForm = () => {
    setSsFormName(""); setSsFormReason(""); setSsFormContradictions([]); setSsFormInterfaces("");
    setSsFormLevel("module"); setSsFormParentId(null);
  };

  const aiSuggestSubsystems = () => {
    if (!id) return;
    // Optimistic local clear: preserve manual subsystems, drop AI ones.
    // The query invalidation on success will refetch and replace this.
    setLocalSubsystems(prev => prev.filter(s => s.source !== "ai"));
    suggestSubsystems.mutate(
      { mission: briefMission || "", contradictions: contradictionDescs },
      {
        onSuccess: ({ created, packageMap: pm }) => {
          setPackageMap(pm ?? null);
          toast.success(`AI 建議了 ${created} 個子系統（含層級結構）`);
        },
        onError: (err) => {
          const msg = err instanceof Error ? err.message : String(err);
          toast.error(`AI 子系統建議失敗：${msg}`);
        },
      },
    );
  };

  /**
   * Wave 2: What-if spatial overlay handler for SpatialOverlayDialog.
   *
   * Bridges two shape mismatches between FE and backend:
   *  1. The dialog produces flat arrays (`zones: [{name, bbox_mm, ...}]`,
   *     `module_mass_budgets: [{name, max_mass_g}]`). The backend expects a
   *     nested `overlay` dict keyed by name:
   *       { zones: { name: {x_mm, y_mm, z_mm, anchor} },
   *         mass_budget_g: { name: max_mass_g } }
   *  2. The backend wraps the result in `{package_map: PackageMap}` whereas
   *     the dialog expects the PackageMap fields inline. We unwrap and
   *     coerce nullable `svg` / `overlay_violations` to their non-null
   *     OverlayResult counterparts.
   *
   * Dialog is "stateless relative to main discovery" by contract, so we do
   * NOT update `packageMap` here — the main map keeps showing discovery
   * output, and overlay results live inside the dialog.
   */
  const handleOverlaySubmit = async (payload: OverlayPayload): Promise<OverlayResult> => {
    if (!id) throw new Error("missing project id");
    const zonesDict: Record<string, { x_mm: number; y_mm: number; z_mm: number; anchor: string }> = {};
    for (const z of payload.zones) {
      zonesDict[z.name] = {
        x_mm: z.bbox_mm[0],
        y_mm: z.bbox_mm[1],
        z_mm: z.bbox_mm[2],
        anchor: z.name,
      };
    }
    const massBudget: Record<string, number> = {};
    for (const b of payload.module_mass_budgets) {
      massBudget[b.name] = b.max_mass_g;
    }
    const resp = await subsystemSpatialOverlay({
      project_id: id,
      subsystems: (payload.subsystems ?? []) as unknown[],
      overlay: { zones: zonesDict, mass_budget_g: massBudget },
    });
    const pm = resp.package_map;
    return {
      ...pm,
      overlay_violations: pm.overlay_violations ?? [],
      svg: pm.svg ?? "",
    };
  };

  /**
   * Wave 3 helpers (WBS 7.5 / 7.6) — derive a stable component / learned key
   * from the current node + neighbour, with a sensible canonical fallback.
   *
   * Strategy:
   *   1. If the spatial estimate carries a `reference_source` with one of the
   *      known prefixes (`rd_override:`, `learned:`, `seed:`, `web:`), strip
   *      the prefix and reuse that suffix — this is the same key the layered
   *      resolver already uses, so the override / learned write hits the same
   *      slot the next Suggest call will look up.
   *   2. Otherwise (LLM estimate, or no source) fall back to a normalized
   *      `${owner}__${neighbour}` slug. Both halves are lowercased and
   *      stripped of whitespace / non-alphanum, joined by `__`.
   */
  const deriveSpatialKey = (
    ownerName: string,
    neighbour: string,
    spatial: SpatialEstimate,
  ): string => {
    const src = spatial.reference_source ?? "";
    const KNOWN_PREFIXES = ["rd_override:", "learned:", "seed:", "web:"];
    for (const p of KNOWN_PREFIXES) {
      if (src.startsWith(p)) {
        const tail = src.slice(p.length).trim();
        if (tail) return tail;
      }
    }
    const norm = (s: string) =>
      s
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
    return `${norm(ownerName)}__${norm(neighbour)}`;
  };

  const handleOverrideSubmit = async (payload: {
    component_key: string;
    bbox: BBox;
    mass_g: number;
    category?: string;
    note?: string;
  }) => {
    if (!id) throw new Error("missing project id");
    try {
      await spatialComponentOverride({
        project_id: id,
        component_key: payload.component_key,
        category: payload.category,
        bbox: payload.bbox,
        mass_g: payload.mass_g,
        note: payload.note,
      });
      toast.success(`已寫入 override：${payload.component_key}`);
      // Refetch the subsystem tree so the next Suggest sees rd_confirmed.
      queryClient.invalidateQueries({ queryKey: queryKeys.subsystems.all });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(`寫入 override 失敗：${msg}`);
      throw err;
    }
  };

  const handlePromoteSubmit = async (payload: {
    key: string;
    bbox: BBox;
    mass_g: number;
    category?: string;
    origin?: string;
    origin_project_id?: string;
    source_url?: string;
    source_text?: string;
  }) => {
    try {
      await spatialLearnedComponent({
        key: payload.key,
        // Backend schema treats `category` as required (default "" allowed).
        category: payload.category ?? "",
        bbox: payload.bbox,
        mass_g: payload.mass_g,
        origin: payload.origin,
        origin_project_id: payload.origin_project_id ?? id,
        source_url: payload.source_url,
        source_text: payload.source_text,
      });
      toast.success(`已推升至 learned：${payload.key}`);
      queryClient.invalidateQueries({ queryKey: queryKeys.subsystems.all });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(`推升至 learned 失敗：${msg}`);
      throw err;
    }
  };

  // WBS 10.1: RD re-confirms a subsystem after editing contracts. Refreshes
  // the stored hash to the current contract snapshot.
  const reconfirmSubsystemContracts = (ssId: string) => {
    const ss = subsystems.find((s) => s.id === ssId);
    if (!ss) return;
    const newHash = hashContracts(ss.interfaceContracts);
    setLocalSubsystems((prev) =>
      prev.map((s) =>
        s.id === ssId ? { ...s, confirmedContractsHash: newHash } : s,
      ),
    );
    toast.success('契約已重新確認');
  };

  const cycleMust = (altId: string, mustId: string) => {
    const alt = alternatives.find(a => a.id === altId);
    if (!alt) return;
    const current = alt.mustScores[mustId];
    const next = current === null ? "pass" : current === "pass" ? "fail" : current === "fail" ? "marginal" : null;
    const newMustScores = { ...alt.mustScores, [mustId]: next };
    setLocalAlternatives((prev) =>
      prev.map((a) => a.id !== altId ? a : { ...a, mustScores: newMustScores })
    );
    updateAlternativeMut.mutate({ id: altId, must_scores: newMustScores as unknown as Json });
  };

  /** AI pre-evaluate MUST for a single alternative */
  const handleAiMustEvaluate = async (altId: string) => {
    const alt = alternatives.find(a => a.id === altId);
    if (!alt || !id) return;
    setAiLoading(prev => ({ ...prev, [`must-${altId}`]: true }));
    try {
      const project = projectQuery.data;
      const result = await mustEvaluate({
        project_id: id,
        alternative_name: alt.name,
        mechanism: alt.mechanism,
        must_criteria: mustCriteria.map(c => ({ id: c.id, label: c.label, source: c.source, threshold: c.threshold })),
        constraints: constraintStrings,
        kpis: kpiStrings,
      });
      // Store AI results for display
      setMustAiResults(prev => ({ ...prev, [altId]: result.criteria_results }));
      // Pre-fill MUST scores from AI judgment
      const newMustScores = { ...alt.mustScores };
      result.criteria_results.forEach(cr => {
        if (cr.passed === true) newMustScores[cr.id] = "pass";
        else if (cr.passed === false) newMustScores[cr.id] = "fail";
        // null → leave as-is (RD must decide)
      });
      setLocalAlternatives(prev =>
        prev.map(a => a.id !== altId ? a : { ...a, mustScores: newMustScores })
      );
      updateAlternativeMut.mutate({ id: altId, must_scores: newMustScores as unknown as Json });
      toast.success(`AI 預判完成：${result.summary}`);
    } catch {
      toast.error("AI MUST 評估失敗，請手動評估");
    } finally {
      setAiLoading(prev => ({ ...prev, [`must-${altId}`]: false }));
    }
  };

  /** AI evaluate all alternatives at once */
  const handleAiMustEvaluateAll = async () => {
    for (const alt of alternatives) {
      await handleAiMustEvaluate(alt.id);
    }
  };

  const updatePreCadScore = (altId: string, dim: string, value: number) => {
    const alt = alternatives.find(a => a.id === altId);
    if (!alt) return;
    const newScores = { ...alt.preCadScores, [dim]: value };
    const allFilled = Object.values(newScores).every((v) => v !== null);
    const allPass = allFilled && Object.values(newScores).every((v) => (v as number) >= 3);
    const overallPass = allFilled ? allPass : null;
    setLocalAlternatives((prev) =>
      prev.map((a) => a.id !== altId ? a : { ...a, preCadScores: newScores, overallPass })
    );
    updateAlternativeMut.mutate({ id: altId, pre_cad_scores: newScores as unknown as Json, overall_pass: overallPass });
  };
  const addManualAlternative = () => {
    if (!id) return;
    createAlternative.mutate({
      project_id: id,
      name: "",
      mechanism: "",
      source: "manual",
      key_assumption_ids: [],
      must_scores: { M1: null, M2: null, M3: null, M4: null, M5: null, M6: null } as unknown as Json,
      interface_contract: { envelope: '', loadPath: '', signalPath: '', thermalPath: '', datumTolerance: '', serviceability: '' } as unknown as Json,
      pre_cad_scores: { must: null, decoupling: null, testability: null, failureMech: null, mvpCadEffort: null } as unknown as Json,
      overall_pass: null,
    });
  };
  const deleteAlternative = (altId: string) => {
    const removed = localAlternatives.find(a => a.id === altId);
    if (!removed) return;
    setLocalAlternatives(prev => prev.filter(a => a.id !== altId));
    deleteAlternativeMut.mutate({ id: altId });
    toast(`已刪除「${removed.name || '未命名方案'}」`, {
      duration: 5000,
      action: {
        label: "復原",
        onClick: () => {
          createAlternative.mutate({
            project_id: id!,
            name: removed.name,
            mechanism: removed.mechanism || undefined,
            source: removed.source || undefined,
          });
          setLocalAlternatives(prev => [...prev, removed]);
        },
      },
    });
  };
  const handleAiGenAlts = async () => {
    if (!id) return;
    setAiLoading((p) => ({ ...p, alts: true }));
    try {
      // Collect adopted TRIZ solutions as candidates
      const adoptedTriz = trizSolutions.filter(ts => ts.status === 'adopted' || ts.status === 'edited');

      let created = 0;

      // Create alternatives from adopted TRIZ solutions (with validation passport)
      for (const ts of adoptedTriz) {
        const passport = await validationPassportGenerate({
          project_id: id,
          solution_name: `TRIZ ${ts.principleName} (${ts.path})`,
          mechanism: ts.suggestion,
          source: `triz_${ts.path.toLowerCase()}`,
          constraints: constraintStrings,
          kpis: kpiStrings,
        });
        await createAlternative.mutateAsync({
          project_id: id,
          name: `TRIZ: ${ts.principleName}`,
          mechanism: ts.suggestion,
          source: `triz_${ts.path.toLowerCase()}` as string,
          key_assumption_ids: [],
          must_scores: { M1: null, M2: null, M3: null, M4: null, M5: null, M6: null } as unknown as Json,
          interface_contract: { envelope: '', loadPath: '', signalPath: '', thermalPath: '', datumTolerance: '', serviceability: '' } as unknown as Json,
          pre_cad_scores: { must: null, decoupling: null, testability: null, failureMech: null, mvpCadEffort: null } as unknown as Json,
          overall_pass: null,
        });
        created++;
      }

      if (created === 0) {
        toast.warning("尚無已採用的 TRIZ 解法，請先在 X1-X2 採用解法，或手動新增方案");
      } else {
        toast.success(`已從 ${adoptedTriz.length} 條 TRIZ 整合 ${created} 個候選方案`);
      }
    } catch (err) {
      console.error("AI alternative generation failed:", err);
      toast.error("方案整合失敗");
    } finally {
      setAiLoading((p) => ({ ...p, alts: false }));
    }
  };

  const mustCell = (val: "pass" | "fail" | "marginal" | null) => {
    if (val === "pass") return <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10"><CheckCircle className="h-4 w-4 text-primary" /></span>;
    if (val === "fail") return <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-destructive/10"><XCircle className="h-4 w-4 text-destructive" /></span>;
    if (val === "marginal") return <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-warning/10"><AlertTriangle className="h-4 w-4 text-warning" /></span>;
    return <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-muted text-sm text-muted-foreground">—</span>;
  };

  // Unified step navigation — infers track from step index when not explicit
  const inferTrack = (step: number): "reverse" | "forward" | null => {
    if (step === 0) return "reverse";
    if (step >= 1 && step <= 2) return activeTrack === "reverse" ? "reverse" : "forward";
    return null; // hub, must, pre-cad
  };
  const navigateTo = (step: number, track?: "reverse" | "forward" | null) => {
    setCurrentStep(step);
    setActiveTrack(track !== undefined ? track : inferTrack(step));
  };

  const goNext = () => {
    if (activeTrack === "reverse") {
      // Reverse (step 0) → jump to Decision Hub
      navigateTo(3, null);
    } else if (activeTrack === "forward" && currentStep < 2) {
      // Forward sub-tabs: TRIZ(1) → Subsystem(2)
      navigateTo(currentStep + 1, "forward");
    } else if (activeTrack === "forward" && currentStep === 2) {
      // Last forward sub-tab → Decision Hub
      navigateTo(3, null);
    } else {
      navigateTo(Math.min(currentStep + 1, 5));
    }
  };
  const goPrev = () => {
    if (activeTrack === "forward" && currentStep > 1) {
      // Forward sub-tabs: Subsystem(2) → TRIZ(1)
      navigateTo(currentStep - 1, "forward");
    } else if (currentStep === 3) {
      // Decision Hub → back to whichever track was last active (default forward)
      navigateTo(2, "forward");
    } else {
      navigateTo(Math.max(currentStep - 1, 0));
    }
  };

  if (isLoading) {
    return (
      <div className="page-shell-narrow py-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-12 w-full" />
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)}
      </div>
    );
  }

  const renderStepContent = () => {
    // Forward track: show TRIZ/Subsystem as tabbed sub-steps within one E2E view
    if (activeTrack === "forward" && currentStep >= 1 && currentStep <= 2) {
      return (
        <div className="space-y-4">
          {/* Internal sub-step tabs */}
          <div className="flex gap-1 border-b pb-2">
            {[
              { step: 1, label: "① TRIZ 解矛盾" },
              { step: 2, label: "② 子系統定義" },
            ].map(({ step, label }) => (
              <button
                key={step}
                onClick={() => navigateTo(step, "forward")}
                className={cn(
                  "px-3 py-1.5 text-xs rounded-t-md transition-colors",
                  currentStep === step
                    ? "bg-blue-50 text-blue-700 font-medium border-b-2 border-blue-500"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                {label}
              </button>
            ))}
          </div>
          {/* Sub-step content */}
          {currentStep === 1 && renderTrizConvergence()}
          {currentStep === 2 && renderSubsystem()}
        </div>
      );
    }

    switch (currentStep) {
      case 0: return renderAntiAnchor();
      case 1: return renderTrizConvergence();
      case 2: return renderSubsystem();
      case 3: return renderAlternatives();
      case 4: return renderMust();
      case 5: return renderPreCad();
      default: return null;
    }
  };

  // ── X1: Anti-Anchor (AI Generated) ──
  // v3.0 DEPRECATED: Anti-Anchor section retired — de-anchoring merged into TRIZ L1 flow
  function renderAntiAnchor() {
    return (
      <div className="space-y-6">
        {/* v3.0 DEPRECATED: Anti-Anchor UI retired — de-anchoring merged into TRIZ L1 flow */}
        <Card className="border-amber-300/50 bg-amber-50/30">
          <CardContent className="p-4 text-center text-sm text-muted-foreground">
            Anti-Anchor 功能已整合至 TRIZ L1 跨域去錨定流程。歷史資料仍可檢視，新專案請使用正向分析中的 TRIZ 流程。
          </CardContent>
        </Card>
        {/* v3.0 DEPRECATED: Original AA UI hidden — kept for rollback safety */}
        {false && (
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        <div>
        {/* TODO: Replace with AI-generated anti-anchor warning via API (Sprint 3+) */}

        {/* 🧭 新手閱讀指引 — 第一次看到這頁的人必讀 */}
        <Collapsible defaultOpen={!antiAnchorGenerated}>
          <Card className="border-primary/30 bg-primary/5">
            <CollapsibleTrigger asChild>
              <button className="w-full text-left p-4 flex items-center gap-3 hover:bg-primary/10 transition-colors group">
                <Sparkles className="h-4 w-4 text-primary shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold">報告怎麼看？（新手指引）</p>
                  <p className="text-xs text-muted-foreground mt-0.5">第一次看這頁不知道每個欄位代表什麼？點這裡展開 60 秒讀懂每一區塊</p>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 transition-transform group-data-[state=open]:rotate-90" />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="px-4 pb-4 pt-0 space-y-3 text-xs text-muted-foreground leading-relaxed border-t border-primary/20">
                <div>
                  <p className="font-semibold text-foreground mt-3 mb-1">這頁在做什麼？</p>
                  <p>反向探索（Anti-Anchor）刻意跳過「解矛盾」的正向路徑，直接從物理第一原理逼 AI 想出「與主流競品物理機制不相容」的非典型架構。目的是在你被現有產品綁架之前，先暴露在其他可能的解題方向。每條路線都自帶一張 <strong>Validation Passport</strong>，告訴你「這條路還要驗證什麼才能採用」。</p>
                </div>

                <div>
                  <p className="font-semibold text-foreground mt-2 mb-1">每條「路線」的六個區塊</p>
                  <ul className="space-y-1.5 pl-1">
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">①</span><strong>Physical Principle</strong>：這條路線背後的物理定律（例如 Lorentz 力、Seebeck 效應）。若只看一行，這裡是核心。</li>
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">②</span><strong>Causal Chain</strong>：從輸入到輸出的每一步都帶數字（48V 20A → 960W → 80Nm），用來檢查「帳能不能算得通」。</li>
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">③</span><strong>Boundary Conditions</strong>：在什麼條件下成立？什麼條件下會失效？（例如 T&lt;130°C 以內）</li>
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">④</span><strong>Why Unconventional</strong>：主流為什麼做不到？產業為什麼還沒採用？不是「這很新」，要說出阻礙的原因。</li>
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">⑤</span><strong>Potential Advantage</strong>：量化的好處，禁止「大幅、顯著、better」等模糊詞，必須有數字或區間。</li>
                    <li><span className="font-mono text-[10px] bg-muted px-1 rounded mr-1">⑥</span><strong>Cross-Domain Source</strong>：靈感來自哪個跨領域的具體產品或論文（例如 Tesla Model 3 hairpin 繞組、Magnax AXF225）。</li>
                  </ul>
                </div>

                <div>
                  <p className="font-semibold text-foreground mt-2 mb-1">Validation Passport 是什麼？</p>
                  <p>每條路線「自我揭露」的風險檔案，包含 4 個子區塊：</p>
                  <ul className="space-y-1 pl-1 mt-1">
                    <li>• <strong>Assumptions</strong>：這條路線要成立，哪 2~4 件事必須是真的？每條假設都標一個證據等級 <span className="font-mono bg-muted px-1 rounded">E0–E4</span>（見下）</li>
                    <li>• <strong>Weak Points</strong>：承認的代價（不是錯，是「我知道有這個缺點」）</li>
                    <li>• <strong>Required Verifications</strong>：採用前要做的實驗清單，照優先序排列</li>
                    <li>• <strong>信心 %</strong>：不是 LLM 隨便給的，而是由假設的證據等級分佈自動算：大多 E2+ → ≥70 %；E1/E2 混合 → 40–70 %；大多 E0/E1 → &lt;40 %</li>
                  </ul>
                </div>

                <div>
                  <p className="font-semibold text-foreground mt-2 mb-1">E0 ~ E4 證據等級怎麼讀？</p>
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-1.5">
                    <div className="rounded bg-red-100 dark:bg-red-950/30 px-2 py-1.5 border border-red-200 dark:border-red-900"><span className="font-mono font-bold text-red-900 dark:text-red-200">E0</span><div className="text-[10px] text-red-900/80 dark:text-red-200/80">純臆測</div></div>
                    <div className="rounded bg-amber-100 dark:bg-amber-950/30 px-2 py-1.5 border border-amber-200 dark:border-amber-900"><span className="font-mono font-bold text-amber-900 dark:text-amber-200">E1</span><div className="text-[10px] text-amber-900/80 dark:text-amber-200/80">物理推理</div></div>
                    <div className="rounded bg-yellow-100 dark:bg-yellow-950/30 px-2 py-1.5 border border-yellow-200 dark:border-yellow-900"><span className="font-mono font-bold text-yellow-900 dark:text-yellow-200">E2</span><div className="text-[10px] text-yellow-900/80 dark:text-yellow-200/80">跨領域量測</div></div>
                    <div className="rounded bg-green-100 dark:bg-green-950/30 px-2 py-1.5 border border-green-200 dark:border-green-900"><span className="font-mono font-bold text-green-900 dark:text-green-200">E3</span><div className="text-[10px] text-green-900/80 dark:text-green-200/80">同類應用測試</div></div>
                    <div className="rounded bg-emerald-200 dark:bg-emerald-950/40 px-2 py-1.5 border border-emerald-300 dark:border-emerald-900"><span className="font-mono font-bold text-emerald-900 dark:text-emerald-200">E4</span><div className="text-[10px] text-emerald-900/80 dark:text-emerald-200/80">已量產驗證</div></div>
                  </div>
                  <p className="mt-1.5">實務上 AI 產出的多半是 E1 ~ E2，這代表「值得做實驗驗證」，不代表「已經成立」。看到 E0 就要特別警覺。</p>
                </div>

                <div>
                  <p className="font-semibold text-foreground mt-2 mb-1">看完一條路線後要做什麼？</p>
                  <ul className="space-y-0.5 pl-1">
                    <li>✓ 覺得值得繼續驗證 → 點<strong>「晉升為候選方案」</strong>，路線會進入「候選方案決策中心」與 TRIZ 路徑的候選並列比較</li>
                    <li>✗ 物理不通 / 成本太高 / 不符約束 → 點垃圾桶刪除</li>
                    <li>↻ 全部都不滿意 → 點「重新生成」讓 AI 重試（已存在的路線會作為「避開」提示傳給 LLM）</li>
                  </ul>
                </div>

                <div className="pt-1 text-[10px] text-muted-foreground/70 italic">
                  完整架構說明見 <code>docs/e2e/Reverse_Anti_Anchor_Architecture.md</code>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {!antiAnchorGenerated ? (
          <div className="text-center py-16 space-y-4 bg-muted/30 rounded-xl border border-dashed">
            <Sparkles className="h-10 w-10 text-muted-foreground mx-auto" />
            <div>
              <p className="font-medium">AI 將根據問題描述與矛盾句產出 3 條非典型架構</p>
              <p className="text-sm text-muted-foreground mt-1">至少 1 條必須與競品在物理介面或核心機制上不相容</p>
            </div>
            <AiButton loading={aiLoading.antiAnchor} onClick={handleAiGenAntiAnchor} size="lg">
              生成非典型架構
            </AiButton>
          </div>
        ) : (
          <div className="space-y-3">
            {routes.map((r, i) => {
              const confidence = r.validationPassport ? Math.round((r.validationPassport.confidenceLevel ?? 0) * 100) : null;
              const assumptionCount = r.validationPassport?.assumptions?.length ?? 0;
              return (
              <Collapsible key={r.id}>
                <Card className="overflow-hidden border-l-[3px] border-l-accent">
                  {/* Collapsed header — always visible */}
                  <CollapsibleTrigger asChild>
                    <button className="w-full text-left p-4 flex items-center gap-3 hover:bg-muted/30 transition-colors group">
                      <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 transition-transform group-data-[state=open]:rotate-90" />
                      <Badge variant="outline" className="text-xs font-mono shrink-0">路線 {i + 1}</Badge>
                      <span className="text-sm font-semibold flex-1 truncate">{r.name}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        {confidence !== null && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-[9px] cursor-help">信心 {confidence}%</Badge>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="max-w-xs text-xs leading-relaxed">
                              由假設的證據等級分佈自動推算：大多 E2+ → ≥70%；E1/E2 混合 → 40–70%；大多 E0/E1 → &lt;40%。不是 LLM 自由寫的。
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {assumptionCount > 0 && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-[9px] cursor-help">{assumptionCount} 假設</Badge>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="max-w-xs text-xs leading-relaxed">
                              這條路線要成立必須是真的「可證偽命題」。展開後每條假設都會標 E0–E4 證據等級。
                            </TooltipContent>
                          </Tooltip>
                        )}
                        <span className="badge-ai text-[9px]">AI</span>
                      </div>
                    </button>
                  </CollapsibleTrigger>

                  {/* Expanded detail */}
                  <CollapsibleContent>
                    <CardContent className="px-5 pb-5 pt-0 space-y-4 border-t">
                      {/* Mechanism — structured */}
                      {r.mechanism && (
                        <div className="text-xs space-y-2 bg-muted/40 dark:bg-muted/20 rounded-lg p-3 mt-3">
                          {(() => {
                            const text = r.mechanism;
                            const sections: { label: string; content: string }[] = [];
                            const markers = [
                              { re: /Physical principle:\s*/i, label: "Physical Principle" },
                              { re: /Causal chain:\s*/i, label: "Causal Chain" },
                              { re: /Boundary conditions?:\s*/i, label: "Boundary Conditions" },
                            ];
                            let remaining = text;
                            for (const { re, label } of markers) {
                              const idx = remaining.search(re);
                              if (idx >= 0) {
                                if (idx > 0 && sections.length === 0) {
                                  sections.push({ label: "Overview", content: remaining.slice(0, idx).trim() });
                                }
                                remaining = remaining.slice(idx).replace(re, '');
                                let end = remaining.length;
                                for (const { re: nextRe } of markers) {
                                  const nextIdx = remaining.search(nextRe);
                                  if (nextIdx > 0 && nextIdx < end) end = nextIdx;
                                }
                                sections.push({ label, content: remaining.slice(0, end).trim() });
                                remaining = remaining.slice(end);
                              }
                            }
                            if (sections.length === 0) {
                              sections.push({ label: "Mechanism", content: text });
                            }
                            const labelHints: Record<string, string> = {
                              "Physical Principle": "這條路線背後的物理定律或方程式（例如 Lorentz 力、Maxwell stress、Seebeck 效應）。若只看一行，這裡是核心。",
                              "Causal Chain": "從輸入到輸出的因果鏈，每一步都要帶數字（48V 20A → 960W @92% η → 5:1 → 80Nm）。用來檢查『帳算不算得通』。",
                              "Boundary Conditions": "這條路線在什麼條件下成立、什麼條件下會失效（例如 T_winding<130°C、B_gap>0.35T）。用來判斷風險邊界。",
                              "Overview": "Mechanism 開頭的前言，未被切到三大區塊時的兜底顯示。",
                              "Mechanism": "AI 沒有依規則切出三個區塊，整段合併顯示。這代表結構化失敗，可以考慮重新生成。",
                            };
                            return sections.map((s, si) => (
                              <div key={si}>
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5 flex items-center gap-1">
                                  {s.label}
                                  {labelHints[s.label] && <HelpTooltip text={labelHints[s.label]} />}
                                </p>
                                <p className="text-muted-foreground leading-relaxed">{s.content}</p>
                              </div>
                            ));
                          })()}
                        </div>
                      )}

                      {/* Detail sections — 2-column grid for compact layout */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {r.whyUnconventional && (
                          <div className="text-xs">
                            <p className="font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                              Why Unconventional
                              <HelpTooltip text="主流為什麼做不到？產業為什麼還沒採用？這裡不接受『這很新』，必須說出阻礙原因（成本？量產成熟度？法規？慣性？）。" />
                            </p>
                            <p className="text-muted-foreground leading-relaxed">{r.whyUnconventional}</p>
                          </div>
                        )}
                        {r.potentialAdvantage && (
                          <div className="text-xs">
                            <p className="font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                              Potential Advantage
                              <HelpTooltip text="量化的好處。Prompt 禁止『高、低、大幅、顯著、better、improved』等模糊詞，必須有數字或區間（例如 BOM cost -40~50% 而非「成本大幅下降」）。" />
                            </p>
                            <p className="text-muted-foreground leading-relaxed">{r.potentialAdvantage}</p>
                          </div>
                        )}
                        {r.crossDomainSource && (
                          <div className="text-xs">
                            <p className="font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                              Cross-Domain Source
                              <HelpTooltip text="靈感來自哪個『具體的』跨領域產品或論文（例如 Magnax AXF225、Tesla Model 3 hairpin winding）。不能只說「參考航太」。這是用來檢查 AI 不是在腦補。" />
                            </p>
                            <p className="text-muted-foreground leading-relaxed">{r.crossDomainSource}</p>
                          </div>
                        )}
                      </div>

                      {/* Validation Passport */}
                      {r.validationPassport && (
                        <div className="text-xs space-y-2 border-t pt-3">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-muted-foreground flex items-center gap-1">
                              Validation Passport
                              <HelpTooltip
                                maxWidth="max-w-sm"
                                text="這條路線「自我揭露」的風險檔案：包含 Assumptions（必須為真的前提）、Weak Points（承認的代價）、Required Verifications（採用前要做的實驗）、以及由假設證據等級自動算出的信心 %。Anti-Anchor 是目前唯一一條路徑，其路線天生自帶 Passport。"
                              />
                            </p>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="outline" className="text-[9px] cursor-help">
                                  信心 {Math.round((r.validationPassport.confidenceLevel ?? 0) * 100)}%
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                                Prompt 強制規則：大多 E2+ → ≥70%；E1/E2 混合 → 40–70%；大多 E0/E1 → &lt;40%。LLM 不能自由寫。
                              </TooltipContent>
                            </Tooltip>
                          </div>
                          {(r.validationPassport.assumptions ?? []).length > 0 && (
                            <div>
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1">
                                Assumptions ({(r.validationPassport.assumptions ?? []).length})
                                <HelpTooltip
                                  maxWidth="max-w-sm"
                                  text="要讓這條路線成立必須為真的「可證偽命題」。每條前面的 E0–E4 代表證據等級：E0 純臆測 / E1 物理推理 / E2 跨領域量測 / E3 同類應用測試 / E4 已量產。AI 產出多半是 E1–E2，代表『值得實驗』而非『已成立』。看到 E0 要警覺。"
                                />
                              </p>
                              <ul className="space-y-1">
                                {(r.validationPassport.assumptions ?? []).map((a, ai) => {
                                  const lvl = (a.evidenceLevel ?? '?').toUpperCase();
                                  const lvlTip: Record<string, string> = {
                                    'E0': 'E0 — 純臆測（speculation）。風險最高，必須優先驗證。',
                                    'E1': 'E1 — 第一原理 / 物理推理。有公式支持但未經實測。',
                                    'E2': 'E2 — 跨領域量測類比。別的領域有測過，在本應用尚未。',
                                    'E3': 'E3 — 同類應用已有測試資料。風險較低。',
                                    'E4': 'E4 — 已在本應用量產驗證。幾乎是事實。',
                                  };
                                  return (
                                    <li key={ai} className="flex items-start gap-1.5 text-muted-foreground">
                                      <Tooltip>
                                        <TooltipTrigger asChild>
                                          <span className="text-[9px] font-mono bg-muted rounded px-1 shrink-0 mt-0.5 cursor-help">{lvl}</span>
                                        </TooltipTrigger>
                                        <TooltipContent side="left" className="max-w-xs text-xs leading-relaxed">
                                          {lvlTip[lvl] ?? '未知證據等級'}
                                        </TooltipContent>
                                      </Tooltip>
                                      <span className="leading-relaxed">{a.content}</span>
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}
                          {(r.validationPassport.weakPoints ?? []).length > 0 && (
                            <div>
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1">
                                Weak Points
                                <HelpTooltip text="這條路線「承認的代價」—— 不是錯，是『我知道有這個缺點』。它們不會變成假設被驗證，而是跟著方案一輩子（例如 +15% 重量、NRE 工具費）。" />
                              </p>
                              <ul className="list-disc list-inside space-y-0.5 text-muted-foreground">
                                {(r.validationPassport.weakPoints ?? []).map((wp, wi) => <li key={wi}>{wp}</li>)}
                              </ul>
                            </div>
                          )}
                          {(r.validationPassport.requiredVerifications ?? []).length > 0 && (
                            <div>
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1">
                                Required Verifications
                                <HelpTooltip text="採用前必須做的實驗清單，已按優先序排列。每條實驗的完整細節（方法、天數、成功判據、成本等級）寫在對應的 Assumption 的 suggested_experiment 欄位。" />
                              </p>
                              <ol className="list-decimal list-inside space-y-0.5 text-muted-foreground">
                                {(r.validationPassport.requiredVerifications ?? []).map((rv, ri) => <li key={ri}>{rv}</li>)}
                              </ol>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs gap-1.5"
                          onClick={() => promoteAntiAnchorToCandidate(r.id)}
                        >
                          <ArrowRight className="h-3 w-3" />
                          晉升為候選方案
                        </Button>
                        <button onClick={() => deleteAntiAnchorRoute(r.id)} className="p-1.5 rounded hover:bg-destructive/10" title="刪除此路線">
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </button>
                      </div>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
              );
            })}
            <AiButton aiVariant="outline" size="sm" loading={aiLoading.antiAnchor} onClick={handleAiGenAntiAnchor} className="text-xs">
              重新生成
            </AiButton>
          </div>
        )}

        <Card className="bg-muted/30">
          <CardContent className="p-4 flex items-center gap-3">
            {routes.length >= 3
              ? <><CheckCircle className="h-5 w-5 text-primary shrink-0" /><span className="text-sm">Gate 2.2.1: ≥3 非典型架構已產出，含至少 1 條非對標路線</span></>
              : <><XCircle className="h-5 w-5 text-muted-foreground shrink-0" /><span className="text-sm text-muted-foreground">Gate 2.2.1: 需 AI 產出至少 3 條非典型架構概念</span></>}
          </CardContent>
        </Card>

        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />
        </div>
        )}
      </div>
    );
  }

  // ── X2: TRIZ 解矛盾 — 分層 drill-down 診斷（v8: Phase A retired）──
  function renderTrizConvergence() {
    // v8: startPhaseA removed — L1 critic per-card replaces global Phase A scan
    const { state, confirmSeverity, forceContinue, retryBranch } = convergenceLoop;
    const contradictionsList = contradictionsQuery.data ?? [];
    // v8: 方向導向分析只處理頂層 TC 矛盾，PC/SF 由後端內部從 TC 衍生
    // 條件：無 parent + type 為 TC 或 null（舊資料可能沒設 type）
    const topLevelTCs = contradictionsList.filter(c => !c.parentContradictionId && (!c.type || c.type === 'TC'));
    const canStart = !!id && topLevelTCs.length > 0;

    const PATH_COLORS: Record<string, string> = { TC: 'bg-blue-100 text-blue-700', PC: 'bg-violet-100 text-violet-700', SF: 'bg-teal-100 text-teal-700' };
    const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
      pending: { label: '待評估', cls: 'bg-muted text-muted-foreground' },
      adopted: { label: '已採用', cls: 'bg-primary text-primary-foreground' },
      skipped: { label: '已跳過', cls: 'bg-muted text-muted-foreground line-through' },
      edited: { label: '已修改', cls: 'bg-amber-100 text-amber-700' },
    };

    return (
      <div className="space-y-5">
        {/* Safety valve: architecture halt overlay */}
        {(state.health === 'critical' || state.health === 'circular') && (
          <ArchitectureHaltOverlay
            health={state.health}
            onGoBack={() => navigate(`/projects/${id}/brief`)}
            onForceContinue={forceContinue}
          />
        )}

        {/* ── v8 方向導向分析 (Direction-Centric Flow) ── */}
        <div className="space-y-3" data-testid="triz-directed-section">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold">🎯 方向導向分析（TC → PC → SF → 方向分群 → 評分 → 整併）</h3>
              <p className="text-xs text-muted-foreground">
                對每條矛盾執行 TC/PC/SF 三路求解，合併所有解法後用 LLM 分群為「實現方向」，
                評分選出 Top1/Top2，最後跨矛盾檢查方向相容性。
              </p>
            </div>
          </div>

          {Object.keys(directedStatusMap).length === 0 ? (
            <Card className="border-dashed border-2 border-green-300">
              <CardContent className="p-6 text-center space-y-3">
                <div className="mx-auto w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <Sparkles className="h-5 w-5 text-green-600" />
                </div>
                <p className="text-sm text-muted-foreground">
                  {topLevelTCs.length === 0
                    ? '前置條件：需先在「深度探索」完成矛盾識別'
                    : `已識別 ${topLevelTCs.length} 條頂層 TC 矛盾（共 ${contradictionsList.length} 條含衍生 PC/SF），可執行方向導向分析`}
                </p>
                <AiButton
                  loading={!!aiLoading.directedTriz}
                  onClick={handleDirectedSolveAll}
                  disabled={!canStart}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {aiLoading.directedTriz ? '方向分析中...' : 'AI 方向導向分析（TC+PC+SF → 方向 → 整併）'}
                </AiButton>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {/* Progressive Task List — 四態矛盾清單 */}
              {topLevelTCs.map((c) => {
                const status = directedStatusMap[c.id] || 'pending';
                const result = directedResults[c.id];
                const error = directedErrors[c.id];
                const label = c.naturalDescription || c.engineeringStatement || c.id.slice(0, 12);
                return (
                  <div key={c.id} className="space-y-1">
                    <div className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                      status === 'pending' && "bg-muted/50",
                      status === 'solving' && "bg-blue-50 dark:bg-blue-950/30",
                      status === 'done' && "bg-green-50/50 dark:bg-green-950/20",
                      status === 'failed' && "bg-red-50 dark:bg-red-950/30",
                    )}>
                      {status === 'pending' && <Clock className="h-4 w-4 text-muted-foreground shrink-0" />}
                      {status === 'solving' && <Loader2 className="h-4 w-4 animate-spin text-blue-600 shrink-0" />}
                      {status === 'done' && <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />}
                      {status === 'failed' && <XCircle className="h-4 w-4 text-red-500 shrink-0" />}
                      <span className="flex-1 line-clamp-1">{label}</span>
                      {status === 'failed' && (
                        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1" onClick={() => handleDirectedSolveSingle(c.id)}>
                          <RefreshCw className="h-3 w-3" /> 重試
                        </Button>
                      )}
                    </div>
                    {status === 'done' && result && (
                      <DirectionResultCard result={result} />
                    )}
                    {status === 'failed' && error && (
                      <p className="text-xs text-red-500 px-3 pb-1">{error}</p>
                    )}
                  </div>
                );
              })}

              {/* Consolidation */}
              {directedConsolidating && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-blue-50 dark:bg-blue-950/30 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  跨矛盾方向整併中...
                </div>
              )}
              {consolidationResult && (
                <ConsolidationPanel consolidation={consolidationResult} />
              )}

              <AiButton
                aiVariant="outline"
                size="sm"
                loading={!!aiLoading.directedTriz}
                onClick={handleDirectedSolveAll}
                className="text-xs"
              >
                重新執行方向導向分析
              </AiButton>
            </div>
          )}
        </div>

        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />
      </div>
    );
  }

  // ── X3: Subsystem ──
  function renderSubsystem() {
    const confirmedCount = subsystems.filter(s => s.confirmed).length;
    const rdCount = subsystems.filter(s => s.source === "rd").length;
    const aiCount = subsystems.filter(s => s.source === "ai").length;
    const aiEditedCount = subsystems.filter(s => s.source === "ai_edited").length;

    const renderSsInlineForm = (isEdit: boolean) => (
      <Card className="border-primary/30">
        <CardContent className="p-4 space-y-3">
          <p className="text-sm font-medium">{isEdit ? "編輯子系統" : "新增 RD 定義子系統"}</p>
          <Input placeholder="子系統名稱 *" value={ssFormName} onChange={e => setSsFormName(e.target.value)} />
          <div className="flex gap-2">
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1">層級</p>
              <Select value={ssFormLevel} onValueChange={(v) => setSsFormLevel(v as SubsystemLevel)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system">System (系統)</SelectItem>
                  <SelectItem value="module">Module (模組)</SelectItem>
                  <SelectItem value="component">Component (零件)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1">上層節點</p>
              <Select value={ssFormParentId ?? "__none__"} onValueChange={(v) => setSsFormParentId(v === "__none__" ? null : v)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="無（頂層）" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">無（頂層）</SelectItem>
                  {subsystems
                    .filter(s => s.id !== (isEdit ? editingSubsystemId : undefined))
                    .map(s => (
                      <SelectItem key={s.id} value={s.id}>
                        <span className="text-muted-foreground mr-1">[{s.level === 'system' ? 'S' : s.level === 'module' ? 'M' : 'C'}]</span>
                        {s.name}
                      </SelectItem>
                    ))
                  }
                </SelectContent>
              </Select>
            </div>
          </div>
          <Textarea placeholder="職責 / 原因描述" value={ssFormReason} onChange={e => setSsFormReason(e.target.value)} rows={2} />
          <div>
            <p className="text-xs text-muted-foreground mb-1.5">關聯矛盾</p>
            <div className="flex flex-wrap gap-2">
              {(contradictionsQuery.data || []).map((c, i) => {
                const cId = c.id || `ec-${i + 1}`;
                return (
                  <label key={cId} className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <Checkbox
                      checked={ssFormContradictions.includes(cId)}
                      onCheckedChange={(checked) => {
                        setSsFormContradictions(prev => checked ? [...prev, cId] : prev.filter(x => x !== cId));
                      }}
                    />
                    <span>{(c.engineeringStatement || c.naturalDescription || '').slice(0, 40)}…</span>
                  </label>
                );
              })}
            </div>
          </div>
          <Input placeholder="介面描述（逗號分隔，選填）" value={ssFormInterfaces} onChange={e => setSsFormInterfaces(e.target.value)} />
          <div className="flex gap-2">
            <Button size="sm" onClick={isEdit ? saveEditSubsystem : addSubsystem}>
              {isEdit ? "儲存" : "確認新增"}
            </Button>
            <Button size="sm" variant="outline" onClick={() => { resetSsForm(); setShowAddSubsystemForm(false); setEditingSubsystemId(null); }}>
              取消
            </Button>
          </div>
        </CardContent>
      </Card>
    );

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" className="text-xs gap-1" onClick={() => { resetSsForm(); setShowAddSubsystemForm(true); setEditingSubsystemId(null); }}>
              <Plus className="h-3.5 w-3.5" /> 新增子系統
            </Button>
            <AiButton size="sm" loading={suggestSubsystems.isPending} onClick={aiSuggestSubsystems}>
              建議子系統
            </AiButton>
            <Badge variant="secondary" className="text-xs">{confirmedCount}/{subsystems.length} 已確認</Badge>
          </div>
          <div className="flex items-center border rounded-md overflow-hidden">
            <button onClick={() => setSubsystemView("diagram")} className={`p-1.5 transition-colors ${subsystemView === "diagram" ? "bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground hover:bg-muted"}`} title="區塊圖">
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
            <button onClick={() => setSubsystemView("list")} className={`p-1.5 transition-colors ${subsystemView === "list" ? "bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground hover:bg-muted"}`} title="列表">
              <List className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Add form */}
        {showAddSubsystemForm && !editingSubsystemId && renderSsInlineForm(false)}

        {/* Source statistics summary */}
        <Card className="border-dashed bg-muted/30">
          <CardContent className="p-3 space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-medium">子系統來源統計</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              本專案共 {subsystems.length} 個子系統：
              {rdCount > 0 && <><Badge variant="outline" className="text-[9px] mx-1 bg-primary/15 text-primary border-primary/30">RD {rdCount}</Badge></>}
              {aiCount > 0 && <><Badge variant="outline" className="text-[9px] mx-1 bg-muted border-muted-foreground/30">AI {aiCount}</Badge></>}
              {aiEditedCount > 0 && <><Badge variant="outline" className="text-[9px] mx-1 bg-accent/15 text-accent-foreground border-accent/30">AI+RD {aiEditedCount}</Badge></>}
              。已確認的子系統將作為正向分析的目標範圍。
            </p>
            {rdCount === 0 && (
              <p className="text-xs text-primary mt-1">💡 建議 RD 先定義已知的核心子系統，AI 將補充可能遺漏的部分。</p>
            )}
          </CardContent>
        </Card>

        {/* Edit form (shown above the diagram/list) */}
        {editingSubsystemId && renderSsInlineForm(true)}

        {subsystemView === "diagram" ? (
          <SubsystemHierarchyView
            subsystems={subsystems}
            contradictionMap={contradictionMap}
            onToggle={toggleSubsystem}
            onEdit={startEditSubsystem}
            onDelete={deleteSubsystem}
            onOverrideSpatial={(sid, nb, sp) =>
              setOverrideTarget({ subsystemId: sid, neighbour: nb, spatial: sp })
            }
            onPromoteSpatial={(sid, nb, sp) =>
              setPromoteTarget({ subsystemId: sid, neighbour: nb, spatial: sp })
            }
          />
        ) : (
          subsystems.map((ss) => {
            const srcCfg: Record<string, { label: string; cls: string }> = {
              rd: { label: "RD", cls: "bg-primary/15 text-primary border-primary/30" },
              ai: { label: "AI", cls: "bg-muted border-muted-foreground/30" },
              ai_edited: { label: "AI+RD", cls: "bg-accent/15 text-accent-foreground border-accent/30" },
            };
            const cfg = srcCfg[ss.source] ?? srcCfg.ai;
            return (
              <Card
                key={ss.id}
                className={`transition-all cursor-pointer ${ss.confirmed ? "border-primary/30 bg-primary/[0.03]" : ""}`}
                onClick={() => toggleSubsystem(ss.id)}
              >
                <CardContent className="p-4 flex items-start gap-4">
                  <Checkbox checked={ss.confirmed} onCheckedChange={() => toggleSubsystem(ss.id)} className="mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium">{ss.name}</span>
                      <Badge variant="outline" className={`text-[9px] ${cfg.cls}`}>{cfg.label}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{ss.reason}</p>
                    {ss.relatedContradictions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {ss.relatedContradictions.map((c) => (
                          <Badge key={c} variant="outline" className="text-[10px]">
                            ⚡ {contradictionMap.get(c) ?? c.slice(0, 8)}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={(e) => { e.stopPropagation(); startEditSubsystem(ss.id); }} className="p-1 rounded hover:bg-muted"><Pencil className="h-3 w-3 text-muted-foreground" /></button>
                    {ss.source === "rd" && <button onClick={(e) => { e.stopPropagation(); deleteSubsystem(ss.id); }} className="p-1 rounded hover:bg-destructive/10"><Trash2 className="h-3 w-3 text-destructive" /></button>}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
        {/* Wave 2: Package Map (discovery output) + What-if overlay trigger. */}
        <section className="mt-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Package Map（空間包絡）</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setOverlayOpen(true)}
              className="gap-1"
            >
              <Shapes className="h-3.5 w-3.5" />
              試算車架包絡
            </Button>
          </div>
          <PackageMapPanel packageMap={packageMap} />
        </section>

        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />

        {/* Wave 2: What-if Overlay dialog. Stateless relative to the main
            Package Map — onSubmit does NOT update `packageMap` state. */}
        <SpatialOverlayDialog
          open={overlayOpen}
          onOpenChange={setOverlayOpen}
          subsystems={subsystems}
          onSubmit={handleOverlaySubmit}
        />

        {/* Wave 3 (WBS 7.5) — RD inline override dialog. */}
        {overrideTarget && (() => {
          const owner = subsystems.find((s) => s.id === overrideTarget.subsystemId);
          const ownerName = owner?.name ?? overrideTarget.subsystemId;
          const componentKey = deriveSpatialKey(
            ownerName,
            overrideTarget.neighbour,
            overrideTarget.spatial,
          );
          return (
            <SpatialOverrideDialog
              open={!!overrideTarget}
              onOpenChange={(o) => !o && setOverrideTarget(null)}
              initial={{
                componentKey,
                displayName: `${ownerName} ↔ ${overrideTarget.neighbour}`,
                currentBbox: overrideTarget.spatial.bbox ?? null,
                currentMassG: overrideTarget.spatial.mass_g ?? null,
              }}
              onSubmit={handleOverrideSubmit}
            />
          );
        })()}

        {/* Wave 3 (WBS 7.6) — Promote-to-learned dialog. */}
        {promoteTarget && (() => {
          const owner = subsystems.find((s) => s.id === promoteTarget.subsystemId);
          const ownerName = owner?.name ?? promoteTarget.subsystemId;
          const learnedKey = deriveSpatialKey(
            ownerName,
            promoteTarget.neighbour,
            promoteTarget.spatial,
          );
          return (
            <PromoteToLearnedDialog
              open={!!promoteTarget}
              onOpenChange={(o) => !o && setPromoteTarget(null)}
              initial={{
                key: learnedKey,
                displayName: `${ownerName} ↔ ${promoteTarget.neighbour}`,
                currentBbox: promoteTarget.spatial.bbox ?? null,
                currentMassG: promoteTarget.spatial.mass_g ?? null,
                originProjectId: id,
              }}
              onSubmit={handlePromoteSubmit}
            />
          );
        })()}
      </div>
    );
  }

  // ── X3: Alternatives (Decision Hub) ──
  function renderAlternatives() {
    // ── Candidate pool: aggregate from all sources ──
    const SOURCE_BADGE: Record<string, { label: string; cls: string }> = {
      anti_anchor: { label: '跨域去錨定 (TRIZ L1)', cls: 'bg-amber-100 text-amber-700' }, // v3.0: renamed from Anti-Anchor
      triz_tc: { label: '正向/TRIZ-TC', cls: 'bg-blue-100 text-blue-700' },
      triz_pc: { label: '正向/TRIZ-PC', cls: 'bg-blue-100 text-blue-700' },
      triz_sf: { label: '正向/TRIZ-SF', cls: 'bg-blue-100 text-blue-700' },
      manual: { label: '手動', cls: 'bg-muted text-muted-foreground' },
      ai_integrated: { label: 'AI 整合', cls: 'bg-violet-100 text-violet-700' },
    };
    const getSourceBadge = (src: string) => SOURCE_BADGE[src] || { label: src, cls: 'bg-muted text-muted-foreground' };

    const adoptedCount = alternatives.length;

    return (
      <div className="space-y-5">
        {/* ── Candidate pool header ── */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="text-sm font-semibold">候選方案池</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              匯集跨域去錨定（TRIZ L1）與正向（TRIZ）所有候選。RD 確認後執行 Phase B 交叉檢查。
            </p>
          </div>
          <div className="flex gap-2">
            <AiButton size="sm" loading={!!aiLoading.alts} onClick={handleAiGenAlts}>
              <Sparkles className="h-3.5 w-3.5 mr-1" /> 自動匯入候選
            </AiButton>
            <Button size="sm" variant="secondary" onClick={addManualAlternative}>
              <Plus className="h-3.5 w-3.5 mr-1" /> 手動新增
            </Button>
          </div>
        </div>

        {/* ── v7 (WP 10.5): Cross-LTS redundancy warning ──
            Legacy "same-contradiction multi-path" warning retired. Intra-LTS
            drill-down combinations (e.g. L1+L2+L3 of the same LTS) are now
            the INTENDED pattern and no longer flagged. This block only fires
            when the SAME contradiction is adopted via DIFFERENT LTS ids,
            which indicates redundant work rather than physical incompatibility. */}
        {crossLtsRedundancyWarnings.length > 0 && (
          <Card className="border-amber-300 bg-amber-50/30">
            <CardContent className="p-3 space-y-1.5">
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                <p className="text-xs font-medium text-amber-700">跨 LTS 重複採納提示</p>
              </div>
              {crossLtsRedundancyWarnings.map((w) => (
                <p key={w.contradictionId} className="text-[10px] text-amber-600">
                  矛盾 {contradictionMap.get(w.contradictionId) ?? w.contradictionId.slice(0, 8)} 被 {w.alts.length} 個採納方案同時解決，但它們來自不同的 LayeredTrizSolution — 屬於重複工作而非衝突，建議只保留一條。
                </p>
              ))}
            </CardContent>
          </Card>
        )}

        {/* ── Candidate cards ── */}
        {alternatives.length === 0 ? (
          <div className="text-center py-12 space-y-3 bg-muted/30 rounded-xl border border-dashed">
            <LayoutGrid className="h-8 w-8 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground font-medium">候選池為空</p>
            <p className="text-xs text-muted-foreground">
              點擊「自動匯入候選」從已採用的 TRIZ 解法中自動匯入，<br />
              或從去錨定步驟晉升方案，或手動新增。
            </p>
          </div>
        ) : (
          <div className="grid gap-3">
            {alternatives.map((alt, i) => {
              const srcBadge = getSourceBadge(alt.source);
              const isReverse = alt.source === 'anti_anchor';
              return (
                <Card key={alt.id} className={cn("border-l-[3px] transition-all", isReverse ? "border-l-amber-400" : "border-l-blue-400")}>
                  <CardContent className="p-4 space-y-2">
                    {/* First eye: name + source + badges */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap min-w-0">
                        <Badge variant="outline" className="text-[10px] font-mono shrink-0">#{i + 1}</Badge>
                        <Badge className={cn("text-[10px]", srcBadge.cls)}>{srcBadge.label}</Badge>
                        <span className="text-sm font-medium truncate">{alt.name || "(未命名)"}</span>
                      </div>
                      <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive shrink-0" onClick={() => deleteAlternative(alt.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>

                    {/* Second eye: mechanism */}
                    {alt.source === 'manual' ? (
                      <>
                        <Input
                          className="text-sm font-medium"
                          placeholder="方案名稱 *"
                          value={alt.name}
                          onChange={(e) => setLocalAlternatives((prev) => prev.map((a) => (a.id === alt.id ? { ...a, name: e.target.value } : a)))}
                          onBlur={(e) => updateAlternativeMut.mutate({ id: alt.id, name: e.target.value })}
                        />
                        <Textarea
                          placeholder="機制說明 *"
                          value={alt.mechanism}
                          rows={2}
                          className="text-xs"
                          onChange={(e) => setLocalAlternatives((prev) => prev.map((a) => (a.id === alt.id ? { ...a, mechanism: e.target.value } : a)))}
                          onBlur={(e) => updateAlternativeMut.mutate({ id: alt.id, mechanism: e.target.value })}
                        />
                      </>
                    ) : (
                      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">{alt.mechanism}</p>
                    )}

                    {/* Third eye: assumptions + VP (collapsed) */}
                    {alt.validationPassport && (
                      <details className="text-xs">
                        <summary className="text-muted-foreground cursor-pointer hover:text-foreground">
                          假設 ({alt.validationPassport.assumptions.length}) · 驗證需求 ({alt.validationPassport.requiredVerifications.length}) · 信心 {Math.round(alt.validationPassport.confidenceLevel * 100)}%
                        </summary>
                        <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-muted">
                          {alt.validationPassport.assumptions.map((a, ai) => (
                            <p key={ai} className="text-[10px] text-muted-foreground">
                              <Badge variant="outline" className="text-[8px] mr-1">{a.evidenceLevel}</Badge>
                              {a.content}
                            </p>
                          ))}
                          {alt.validationPassport.weakPoints.length > 0 && (
                            <div className="mt-1">
                              <p className="text-[9px] text-muted-foreground font-medium">弱點：</p>
                              {alt.validationPassport.weakPoints.map((wp, wi) => (
                                <p key={wi} className="text-[10px] text-muted-foreground">- {wp}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      </details>
                    )}

                    {alt.keyAssumptionIds.length > 0 && !alt.validationPassport && (
                      <div className="flex flex-wrap gap-1">
                        {alt.keyAssumptionIds.map((aid) => (
                          <Badge key={aid} variant="outline" className="text-[9px]">
                            {assumptionMap.get(aid)?.code ?? aid.slice(0, 8)}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* ── Phase B: cross-check adopted solutions ── */}
        {adoptedCount > 0 && (
          <Card className="border-violet-300 bg-violet-50/30">
            <CardContent className="p-4 space-y-3">
              <div>
                <p className="text-sm font-semibold">Phase B 收斂掃描 — 方案交叉檢查</p>
                <p className="text-xs text-muted-foreground mt-1">
                  檢查 {adoptedCount} 個方案之間是否存在跨矛盾衝突、參數干涉或跨 LTS 重複採納。
                  （同一 LayeredTrizSolution 的跨層 drill-down 採納會被自動 SKIP，不視為衝突）
                  {convergenceLoop.state.phase === 'B' && convergenceLoop.state.status === 'converged'
                    ? ' ✓ 掃描完成，可進入 MUST 快篩。'
                    : convergenceLoop.state.phase === 'B' && convergenceLoop.state.status === 'exploring'
                    ? ' 掃描進行中...'
                    : ''}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => { convergenceLoop.startPhaseB(); toast.info('Phase B 收斂掃描已啟動'); }}
                  disabled={convergenceLoop.state.status === 'exploring'}
                >
                  {convergenceLoop.state.status === 'exploring'
                    ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> 掃描中...</>
                    : <><Sparkles className="h-3.5 w-3.5 mr-1.5" /> 執行 Phase B 掃描</>}
                </Button>
                {convergenceLoop.state.phase === 'B' && convergenceLoop.state.status === 'converged' && (
                  <Button onClick={() => { toast.success('方案規格已確認'); goNext(); }} className="shrink-0">
                    <Check className="h-4 w-4 mr-1" /> 確認並進入 MUST 快篩
                  </Button>
                )}
              </div>
              {convergenceLoop.state.phase === 'B' && convergenceLoop.state.status !== 'idle' && (
                <ConvergenceDashboard state={convergenceLoop.state} />
              )}
              {convergenceLoop.state.phase === 'B' && convergenceLoop.state.status === 'halted' && (
                <p className="text-xs text-destructive">
                  ⚠ 收斂掃描發現問題（可能有跨方案衝突）。請調整方案後重新掃描。
                </p>
              )}
            </CardContent>
          </Card>
        )}

        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />
      </div>
    );
  }

  // ── X4: MUST ──
  function renderMust() {
    if (alternatives.length === 0) {
      return (
        <div className="text-center py-16 space-y-3">
          <p className="text-muted-foreground">請先在「方案整合」中建立方案</p>
          <Button variant="secondary" onClick={() => navigateTo(3, null)}>
            <ChevronLeft className="h-4 w-4 mr-1" /> 回到方案整合
          </Button>
        </div>
      );
    }

    const anyAiLoading = alternatives.some(a => aiLoading[`must-${a.id}`]);

    /** Get AI reasoning for a criterion */
    const getAiReasoning = (altId: string, criterionId: string): MustCriterionResult | undefined => {
      return mustAiResults[altId]?.find(r => r.id === criterionId);
    };

    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge className="bg-primary/10 text-primary border-0 px-3 py-1">{passedMustAlts.length} 通過</Badge>
          <Badge className="bg-destructive/10 text-destructive border-0 px-3 py-1">{alternatives.filter((a) => Object.values(a.mustScores).includes("fail")).length} 淘汰</Badge>
          <Badge className="bg-muted text-muted-foreground border-0 px-3 py-1">{alternatives.filter((a) => Object.values(a.mustScores).includes("marginal")).length} 待定</Badge>
          <div className="flex-1" />
          <AiButton size="sm" aiVariant="outline" loading={anyAiLoading} onClick={handleAiMustEvaluateAll}>
            全部評估
          </AiButton>
        </div>

        {mustCriteria !== DEFAULT_MUST_CRITERIA && (
          <p className="text-xs text-muted-foreground">MUST 準則已從 Brief 約束/KPI 自動導出（共 {mustCriteria.length} 項）</p>
        )}

        {/* Desktop table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-3 text-xs font-medium text-muted-foreground">方案</th>
                {mustCriteria.map((c) => (
                  <th key={c.id} className="text-center py-3 px-2 text-xs font-medium text-muted-foreground">
                    <Tooltip>
                      <TooltipTrigger asChild><span className="cursor-help">{c.label}</span></TooltipTrigger>
                      <TooltipContent><p className="text-xs">來源: {c.source}{c.threshold ? ` | 閾值: ${c.threshold}` : ""}</p></TooltipContent>
                    </Tooltip>
                  </th>
                ))}
                <th className="text-center py-3 px-2 text-xs font-medium text-muted-foreground">AI</th>
                <th className="text-center py-3 px-3 text-xs font-medium text-muted-foreground">結果</th>
              </tr>
            </thead>
            <tbody>
              {alternatives.map((alt) => {
                const hasFail = Object.values(alt.mustScores).includes("fail");
                return (
                  <tr key={alt.id} className={`border-b transition-colors ${hasFail ? "opacity-50" : "hover:bg-muted/30"}`}>
                    <td className={`py-3 px-3 text-sm max-w-[140px] truncate ${hasFail ? "line-through" : ""}`}>{alt.name || "(未命名)"}</td>
                    {mustCriteria.map((c) => {
                      const aiResult = getAiReasoning(alt.id, c.id);
                      return (
                        <td key={c.id} className="text-center py-3 px-2 cursor-pointer" onClick={() => cycleMust(alt.id, c.id)}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span>{mustCell(alt.mustScores[c.id])}</span>
                            </TooltipTrigger>
                            {aiResult && (
                              <TooltipContent className="max-w-[280px]">
                                <p className="text-xs font-medium mb-1">AI 信心: {Math.round(aiResult.confidence * 100)}%</p>
                                <p className="text-xs">{aiResult.reasoning}</p>
                                {aiResult.evidence_sources.length > 0 && (
                                  <p className="text-xs text-muted-foreground mt-1">依據: {aiResult.evidence_sources.join(", ")}</p>
                                )}
                              </TooltipContent>
                            )}
                          </Tooltip>
                        </td>
                      );
                    })}
                    <td className="text-center py-3 px-2">
                      <AiButton size="sm" aiVariant="ghost" className="h-7 px-2" loading={aiLoading[`must-${alt.id}`]} onClick={() => handleAiMustEvaluate(alt.id)}>
                      </AiButton>
                    </td>
                    <td className="text-center py-3 px-3">
                      {hasFail ? <Badge variant="destructive" className="text-[10px]">淘汰</Badge>
                        : getMustValues(alt).every((v) => v === "pass") ? <Badge className="bg-primary text-primary-foreground text-[10px]">通過</Badge>
                        : <Badge variant="secondary" className="text-[10px]">待定</Badge>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {alternatives.map((alt) => {
            const hasFail = Object.values(alt.mustScores).includes("fail");
            return (
              <Card key={alt.id} className={hasFail ? "opacity-50" : ""}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <p className={`text-sm font-medium ${hasFail ? "line-through" : ""}`}>{alt.name || "(未命名)"}</p>
                    <AiButton size="sm" aiVariant="ghost" className="h-7 px-2" loading={aiLoading[`must-${alt.id}`]} onClick={() => handleAiMustEvaluate(alt.id)}>
                    </AiButton>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {mustCriteria.map((c) => (
                      <div key={c.id} className="text-center cursor-pointer" onClick={() => cycleMust(alt.id, c.id)}>
                        <p className="text-[10px] text-muted-foreground mb-1">{c.id}</p>
                        {mustCell(alt.mustScores[c.id])}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />
      </div>
    );
  }

  // ── X5: Pre-CAD ──
  function renderPreCad() {
    const eligible = alternatives.filter((a) => !Object.values(a.mustScores).includes("fail") && Object.values(a.mustScores).some((v) => v !== null));
    if (eligible.length === 0) {
      return (
        <div className="text-center py-16 space-y-3">
          <p className="text-muted-foreground">請先在 MUST 快篩中完成評估</p>
          <Button variant="secondary" onClick={() => navigateTo(4, null)}>
            <ChevronLeft className="h-4 w-4 mr-1" /> 回到 MUST 快篩
          </Button>
        </div>
      );
    }

    const toggleCompare = (altId: string) => {
      setComparedAltIds((prev) => {
        const next = new Set(prev);
        next.has(altId) ? next.delete(altId) : next.add(altId);
        return next;
      });
    };

    const editingAlt = eligible.find((a) => a.id === selectedAltId) ?? eligible[0];
    const comparedAlts = eligible.filter((a) => comparedAltIds.has(a.id));
    const radarAlts = comparedAlts.length > 0 ? comparedAlts : eligible;

    const radarData = PRECAD_DIMENSIONS.map((d) => {
      const entry: Record<string, any> = { subject: d.label, fullMark: 5 };
      radarAlts.forEach((a) => {
        entry[a.id] = a.preCadScores[d.key as keyof typeof a.preCadScores] ?? 0;
      });
      return entry;
    });

    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">勾選方案加入比較圖，點擊名稱編輯評分</p>
          <div className="space-y-2">
            {eligible.map((a, i) => (
              <div
                key={a.id}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${editingAlt.id === a.id ? "border-primary bg-primary/[0.03]" : "hover:bg-muted/30"}`}
                onClick={() => setSelectedAltId(a.id)}
              >
                <div onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={comparedAltIds.has(a.id)}
                    onCheckedChange={() => toggleCompare(a.id)}
                  />
                </div>
                <div
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: RADAR_COLORS[i % RADAR_COLORS.length] }}
                />
                <span className="text-sm font-medium flex-1 truncate">{a.name || "(未命名)"}</span>
                {a.overallPass === true && <Badge className="bg-primary text-primary-foreground text-[10px]">通過</Badge>}
                {a.overallPass === false && <Badge variant="destructive" className="text-[10px]">不通過</Badge>}
                {a.overallPass === null && <Badge variant="secondary" className="text-[10px]">待評</Badge>}
              </div>
            ))}
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-5">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              <span className="text-sm font-semibold">評分：{editingAlt.name || "(未命名)"}</span>
            </div>
            {PRECAD_DIMENSIONS.map((dim) => {
              const val = editingAlt.preCadScores[dim.key as keyof typeof editingAlt.preCadScores] ?? 1;
              return (
                <div key={dim.key} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{dim.label}</span>
                    <Badge variant={val >= 3 ? "default" : "destructive"} className="text-xs">{val}/5</Badge>
                  </div>
                  <Slider min={1} max={5} step={1} value={[val]} onValueChange={([v]) => updatePreCadScore(editingAlt.id, dim.key, v)} />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>{dim.labels[0]}</span><span>{dim.labels[2]}</span><span>{dim.labels[4]}</span>
                  </div>
                </div>
              );
            })}
            <div className="pt-3">
              {editingAlt.overallPass === true
                ? <Badge className="bg-primary text-primary-foreground px-3 py-1">通過 — 可進入 CAD</Badge>
                : editingAlt.overallPass === false
                ? <Badge variant="destructive" className="px-3 py-1">不通過 — 有維度 &lt; 3</Badge>
                : <Badge variant="secondary" className="px-3 py-1">待完成評分</Badge>}
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-xs text-muted-foreground text-center">
              {comparedAlts.length > 0 ? `比較 ${comparedAlts.length} 個方案` : "全部方案總覽"}
            </p>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid strokeDasharray="3 3" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fontSize: 10 }} />
                {radarAlts.map((a, i) => (
                  <Radar
                    key={a.id}
                    name={a.name || "(未命名)"}
                    dataKey={a.id}
                    stroke={RADAR_COLORS[eligible.indexOf(a) % RADAR_COLORS.length]}
                    fill={RADAR_COLORS[eligible.indexOf(a) % RADAR_COLORS.length]}
                    fillOpacity={0.1}
                  />
                ))}
              </RadarChart>
            </ResponsiveContainer>

            <div className="flex flex-wrap gap-3 justify-center">
              {radarAlts.map((a) => (
                <div key={a.id} className="flex items-center gap-1.5 text-xs">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: RADAR_COLORS[eligible.indexOf(a) % RADAR_COLORS.length] }}
                  />
                  <span className="text-muted-foreground">{a.name || "(未命名)"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* P3: Pre-CAD Gate Confirmation */}
        {preCadPassedAlts.length > 0 && (
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex-1">
                <p className="text-sm font-medium">確認 Pre-CAD 審查結果</p>
                <p className="text-xs text-muted-foreground">
                  {preCadPassedAlts.length} 個方案通過 Pre-CAD 五維審查。確認後進入 CAD 繪製階段。
                </p>
              </div>
              <Button onClick={() => toast.success('Pre-CAD 審查結果已確認')} className="shrink-0">
                <Check className="h-4 w-4 mr-1" /> 確認審查結果
              </Button>
            </CardContent>
          </Card>
        )}
        <KnowledgeRefsPanel refs={[] /* TODO: useKnowledgeRefs (Sprint 5+) */} />
      </div>
    );
  }

  // ── Gate section ──
  function renderGates() {
    if (currentStep < 4) return null;

    return (
      <div className="space-y-4 mt-2">
        <Separator />
        <Card className="border-border">
          <CardContent className="p-5 space-y-3">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold">Gate 2.2 — 方案創造完整性</h3>
              <Badge className={gate22Items.every((i) => i.passed) ? "bg-primary text-primary-foreground" : "bg-destructive text-destructive-foreground"} >
                {gate22Items.every((i) => i.passed) ? "Passed" : "未通過"}
              </Badge>
            </div>
            <div className="space-y-2">
              {gate22Items.map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {item.passed ? <CheckCircle className="h-4 w-4 text-primary shrink-0" /> : <XCircle className="h-4 w-4 text-muted-foreground shrink-0" />}
                  <span className={item.passed ? "" : "text-muted-foreground"}>{item.label}</span>
                  <span className="text-xs text-muted-foreground ml-auto">{item.current}/{item.target}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {currentStep === 5 && (
          <Card className="border-2 border-accent/30 bg-accent/5">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center gap-3">
                <Flag className="h-5 w-5 text-accent shrink-0" />
                <h3 className="text-sm font-semibold">Phase Gate 2 — Diverge 完成</h3>
                <Badge className={phaseGate2Items.every((i) => i.passed) ? "bg-primary text-primary-foreground" : "bg-destructive text-destructive-foreground"}>
                  {phaseGate2Items.every((i) => i.passed) ? "Phase 2 Passed *" : "未通過"}
                </Badge>
              </div>
              <div className="space-y-2">
                {phaseGate2Items.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {item.passed ? <CheckCircle className="h-4 w-4 text-primary shrink-0" /> : <XCircle className="h-4 w-4 text-muted-foreground shrink-0" />}
                    <span className={item.passed ? "" : "text-muted-foreground"}>{item.label}</span>
                    <span className="text-xs text-muted-foreground ml-auto">{item.current}/{item.target}</span>
                  </div>
                ))}
              </div>
              {gate22Items.every((i) => i.passed) && phaseGate2Items.every((i) => i.passed) ? (
                <Button onClick={() => navigate(`/projects/${id}/cad`)} className="w-full sm:w-auto mt-2">
                  通過 Phase Gate 2 → 進入 CAD 繪製 <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              ) : (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="inline-block"><Button disabled className="w-full sm:w-auto opacity-50 mt-2">進入 Review → <ArrowRight className="h-4 w-4 ml-1" /></Button></span>
                  </TooltipTrigger>
                  <TooltipContent><p>請完成所有 Gate 條件</p></TooltipContent>
                </Tooltip>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="page-shell-narrow">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${id}`)} className="text-muted-foreground -ml-2">
          <ArrowLeft className="h-4 w-4 mr-1" /> Dashboard
        </Button>
        {saveStatus !== "idle" && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            {saveStatus === "saving" && "Saving..."}
            {saveStatus === "saved" && <><Check className="h-3 w-3 text-primary" /> Saved</>}
          </span>
        )}
      </div>

      <MissionContext
        problemStatement={briefMission || MOCK_MISSION.problemStatement}
        contradictions={contradictionDescs.length > 0
          ? contradictionDescs.map((d, i) => ({ id: `EC-${String(i + 1).padStart(3, '0')}`, description: d }))
          : MOCK_MISSION.contradictions}
        verifiedAssumptions={MOCK_MISSION.verifiedAssumptions}
        totalAssumptions={MOCK_MISSION.totalAssumptions}
        highRiskCount={MOCK_MISSION.highRiskCount}
      />

      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          方案創造
          <HelpTooltip text="雙軌分析 → 候選方案決策中心 → 統一評估。跨域去錨定（TRIZ L1，原 Anti-Anchor）與正向路徑（TRIZ 解矛盾 → 子系統定義），所有方案在決策中心攤平比較、Phase B 交叉檢查後進入 MUST 快篩。" className="ml-2 align-middle" />
        </h1>
        <p className="text-sm text-muted-foreground mt-1">雙軌分析 · 方案匯流 · 統一評估</p>
      </div>

      <CreateStepper
        steps={STEPS}
        statuses={stepStatuses}
        currentStep={currentStep}
        activeTrack={activeTrack}
        onStepClick={(step, track) => navigateTo(step, track)}
      />

      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className={cn(
            "h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold",
            activeTrack === "reverse" ? "bg-amber-500 text-white" :
            activeTrack === "forward" ? "bg-blue-500 text-white" :
            "bg-primary text-primary-foreground"
          )}>
            {activeTrack === "reverse" ? "⚡" :
             activeTrack === "forward" ? "🎯" :
             currentStep === 3 ? "⬡" : currentStep - 2}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold flex items-center gap-1">
                {activeTrack === "reverse" ? "跨域去錨定 (TRIZ L1)" :
                 activeTrack === "forward" ? "正向分析" :
                 STEPS[currentStep].label}
                {activeTrack === "reverse" && (
                  <HelpTooltip
                    maxWidth="max-w-sm"
                    text="跨域去錨定（原 Anti-Anchor）：已整合至 TRIZ L1 實例化流程。從約束出發產出非典型架構概念，破路徑依賴。歷史資料仍可檢視，新專案請使用正向分析中的 TRIZ 流程。"
                  />
                )}
              </h2>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                activeTrack === "reverse" ? ZONE_LABELS.reverse.color :
                activeTrack === "forward" ? ZONE_LABELS.forward.color :
                ZONE_LABELS[STEPS[currentStep].zone].color
              }`}>
                {activeTrack === "reverse" ? ZONE_LABELS.reverse.badge :
                 activeTrack === "forward" ? ZONE_LABELS.forward.badge :
                 ZONE_LABELS[STEPS[currentStep].zone].badge}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {activeTrack === "reverse" ? "從約束出發，AI 產出非典型架構概念，每條自帶 Validation Passport" :
               activeTrack === "forward" ? "TRIZ 矛盾解 → 子系統分解 — 系統化產出候選方案" :
               STEPS[currentStep].description}
            </p>
          </div>
        </div>
      </div>

      <div className="min-h-[300px]">
        {renderStepContent()}
      </div>

      {renderGates()}

      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={goPrev} disabled={currentStep === 0}>
          <ChevronLeft className="h-4 w-4 mr-1" /> 上一步
        </Button>
        <span className="text-xs text-muted-foreground">
          {ZONE_LABELS[STEPS[currentStep].zone].badge}
        </span>
        {currentStep < 5 ? (
          <div className="flex flex-col items-end gap-1">
            <Button
              onClick={goNext}
            >
              下一步 <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        ) : (
          <div />
        )}
      </div>
    </div>
  );
}
