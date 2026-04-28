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
  Shapes
} from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from "recharts";
import type {
  TrizSolution, Subsystem,
  Alternative, AccordionStepStatus, TrizPath, TrizActionStatus, CreateGateItem,
  SubsystemSource, SubsystemLevel
} from "@/types/create";
import { DEFAULT_MUST_CRITERIA, PRECAD_DIMENSIONS } from "@/types/create";
import type { MustCriterion } from "@/types/create";
import type { InterfaceContractMap } from "@/types/generated/subsystem";
import { EMPTY_INTERFACE_CONTRACT } from "@/types/generated/subsystem";

/**
 * Stage 4 of refactor/subsystem-interface-contracts: convert the manual-form
 * comma-separated "interfaces" text input into an InterfaceContractMap with
 * empty 6-dim placeholders per neighbour. Preserves existing contracts when
 * editing — only adds/removes keys, never overwrites populated fields.
 *
 * This lets the manual subsystem form feed the same data shape the AI path
 * produces, so downstream consumers (InterfaceContractsPanel, Pre-CAD
 * spatial_score) see a uniform structure.
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
import {
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
import { useTrizConsolidationResult, upsertConsolidationResult } from "@/hooks/api/useTrizConsolidationResult";
import { useDirectedTrizSolutions } from "@/hooks/api/useDirectedTrizSolutions";
import type { Contradiction } from "@/types/contradiction";
import type { Json } from "@/integrations/supabase/types";
import { supabase } from "@/integrations/supabase/client";
import { useTrackAssumptions } from "@/hooks/api/useTrack";
import { useBrief, useConstraints, useKpis } from "@/hooks/api/useBrief";
import { trizSolveDirected, trizConsolidate, riskAnalyze, mustEvaluate, validationPassportGenerate, spatialComponentOverride, spatialLearnedComponent, subsystemSpatialOverlay } from "@/lib/api";
import type { DirectedConceptRouteMeta, DirectedAdoptionMode } from "@/types/conceptRoute";
import type { ContradictionDirectionResult, DirectionGroup, DirectionScore, ConsolidationResult } from "@/types/directedTriz";
import { hashContracts, isContractDriftedSinceConfirm } from "@/lib/subsystemHash";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/hooks/api/useQueryConfig";
import type { SpatialEstimate, BBox } from "@/types/generated/subsystem";
import type { MustCriterionResult } from "@/lib/api";
import type { PackageMap } from "@/types/generated/subsystem";
import { useSubsystemSuggestion } from "@/hooks/api/useSubsystemSuggestion";
import { useProject } from "@/hooks/api/useProjects";
// TODO: Replace mockStepKnowledgeRefs with a useKnowledgeRefs hook once a knowledge_refs DB table is created (Sprint 5+)
import { mockStepKnowledgeRefs } from "@/data/mockKnowledgeRefs";
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
import { OzOtPanel } from "@/components/create/OzOtPanel";
import { CciBadge } from "@/components/create/CciBadge";
import { EvidenceCoverageGauge } from "@/components/create/EvidenceCoverageGauge";
import { ConsolidationPanel } from "@/components/create/ConsolidationPanel";
import { DirectionResultCard } from "@/components/create/DirectionResultCard";
import { CompatibilityMatrixView as CompatibilityMatrix } from "@/components/create/CompatibilityMatrix";
import { useConceptRoutes, useCompatibilityPairs } from "@/hooks/api/useConceptRoutes";
// TODO: Replace with API when available — AI-generated adoption state, no dedicated DB table yet
import { mockAdoptionState } from "@/data/mockConceptRoutes";
import type { ConceptRoute, MultiSolutionAdoptionState, CompositionEntry } from "@/types/conceptRoute";

const RADAR_COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--destructive))",
  "hsl(var(--accent))",
  "#10B981",
];

const STEPS = [
  { label: "TRIZ 解矛盾（含跨域去錨定）", shortLabel: "TRIZ", description: "分層 drill-down（L1 含跨域去錨定 / L2 根因 / L3 結構旁路），每條矛盾產出多層級候選方案", zone: "analysis" as const },
  { label: "子系統定義", shortLabel: "子系統", description: "識別受矛盾影響的子系統 (System→Module→Component)，聚焦分析範圍", zone: "analysis" as const },
  { label: "候選方案決策中心", shortLabel: "決策中心", description: "攤平所有來源方案，橫向比較機制、假設、CCI 複雜度、驗證需求與信心等級", zone: "hub" as const },
  { label: "MUST 快篩", shortLabel: "MUST", description: "以必要條件快速淘汰不可行方案（動態 M1-Mn 由 Brief 衍生）", zone: "eval" as const },
  { label: "Pre-CAD 審查", shortLabel: "Pre-CAD", description: "五維審查：MUST/解耦/可驗證性/失效機制/MVP CAD 工作量", zone: "eval" as const },
];

const ZONE_LABELS: Record<string, { badge: string; color: string }> = {
  analysis: { badge: "TRIZ 分析", color: "bg-blue-100 text-blue-700" },
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


export default function Create() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [currentStep, setCurrentStep] = useState(0);
  // activeTrack removed — dual-track (reverse/forward) retired; TRIZ L1 built-in de-anchoring

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
  const trizQuery = useTrizSolutions(id);
  const subsystemsQuery = useSubsystems(id);
  // @deprecated v9: SCAMPER removed — query retained for data compatibility only
  // const scamperQuery = useScamperVariants(id);
  const alternativesQuery = useAlternatives(id);
  const conceptRoutesQuery = useConceptRoutes(id);
  const compatibilityPairsQuery = useCompatibilityPairs(id);
  const trackAssumptionsQuery = useTrackAssumptions(id);
  const contradictionsQuery = useContradictions(id);
  const directedQuery = useDirectedTrizSolutions(id);
  const consolidationQuery = useTrizConsolidationResult(id);

  // ── Phase 1 context ──
  const { data: brief } = useBrief(id);
  const { data: briefConstraints = [] } = useConstraints(id);
  const { data: briefKpis = [] } = useKpis(id);

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

  // ── API Hooks: mutations ──
  const createTrizSolution = useCreateTrizSolution();
  const updateTrizSolution = useUpdateTrizSolution();
  const createSubsystem = useCreateSubsystem();
  const updateSubsystemMut = useUpdateSubsystem();
  const deleteSubsystemMut = useDeleteSubsystem();
  // @deprecated v9: SCAMPER mutations removed
  const createAlternative = useCreateAlternative();
  const updateAlternativeMut = useUpdateAlternative();
  const deleteAlternativeMut = useDeleteAlternative();

  // ── Derived data from queries (with local overrides for optimistic UI) ──
  const [localTrizSolutions, setLocalTrizSolutions] = useState<TrizSolution[]>([]);
  // 9.2.4: Per-contradiction independent loading state
  const [solvingIds, setSolvingIds] = useState<Set<string>>(new Set());

  // v8 directed mode state — keyed by contradiction_id like layeredSolutions
  const [directedResults, setDirectedResults] = useState<Record<string, ContradictionDirectionResult>>({});
  useEffect(() => {
    if (directedQuery.data) {
      setDirectedResults((prev) => ({ ...directedQuery.data, ...prev }));
    }
  }, [directedQuery.data]);

  // ── v8: directed single-contradiction solve helper ───────────────────────
  const solveDirectedSingle = async (c: Contradiction): Promise<[string, ContradictionDirectionResult] | null> => {
    if (!id) return null;
    const cAny = c as unknown as Record<string, unknown>;
    const pickSeverity = (raw: unknown): 'fatal' | 'major' | 'minor' | 'unknown' => {
      const allowed = ['fatal', 'major', 'minor', 'unknown'] as const;
      return (allowed.includes(raw as typeof allowed[number]) ? raw : 'unknown') as typeof allowed[number];
    };
    setSolvingIds(prev => { const next = new Set(prev); next.add(c.id); return next; });
    try {
      const resp = await trizSolveDirected({
        project_id: id,
        contradiction_id: c.id,
        natural_description: c.naturalDescription,
        severity: pickSeverity(cAny.severity),
        improving_param: c.improvingParam ?? undefined,
        worsening_param: c.worseningParam ?? undefined,
      });
      setSolvingIds(prev => { const next = new Set(prev); next.delete(c.id); return next; });
      setDirectedResults(prev => ({ ...prev, [c.id]: resp.result }));
      queryClient.invalidateQueries({ queryKey: queryKeys.directed_triz_solutions.byProject(id) });
      return [c.id, resp.result];
    } catch (err) {
      const desc = (c.naturalDescription || c.engineeringStatement || c.id).slice(0, 60);
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`trizSolveDirected failed for ${c.id}:`, err);
      toast.error(`方向式求解失敗：${desc}`, { description: msg.slice(0, 120) });
      setSolvingIds(prev => { const next = new Set(prev); next.delete(c.id); return next; });
      return null;
    }
  };


  // v8: per-row directed solve (mirrors handleSolveSingle for layered)
  const handleSolveDirectedSingle = async (contradictionId: string) => {
    const contrs = contradictionsQuery.data ?? [];
    const c = contrs.find(x => x.id === contradictionId);
    if (!c) return;
    const result = await solveDirectedSingle(c);
    if (result) {
      toast.success(`已為 "${c.naturalDescription?.slice(0, 30) ?? c.id.slice(0, 8)}" 產出方向式診斷`);
    } else {
      toast.error(`"${c.naturalDescription?.slice(0, 30) ?? c.id.slice(0, 8)}" 方向式求解失敗`);
    }
  };

  const [localSubsystems, setLocalSubsystems] = useState<Subsystem[]>([]);
  // @deprecated v9: SCAMPER local state removed
  const [localAlternatives, setLocalAlternatives] = useState<Alternative[]>([]);

  // Sync query data → local state
  useEffect(() => { setLocalTrizSolutions(trizQuery.data); }, [trizQuery.data]);
  useEffect(() => { setLocalSubsystems(subsystemsQuery.data); }, [subsystemsQuery.data]);
  // @deprecated v9: SCAMPER sync removed
  useEffect(() => { setLocalAlternatives(alternativesQuery.data); }, [alternativesQuery.data]);
  useEffect(() => {if (id) {contradictionsQuery.refetch(); }}, [id]);

  // Use local state as the working data (allows optimistic updates)
  const trizSolutions = localTrizSolutions;
  const subsystems = localSubsystems;
  // @deprecated v9: scamperVariants removed
  const alternatives = localAlternatives;

  const [selectedAltId, setSelectedAltId] = useState<string | null>(null);
  const [comparedAltIds, setComparedAltIds] = useState<Set<string>>(new Set());
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  // Phase B is now manually triggered from the Decision Hub (Step 4),
  // NOT auto-triggered when Phase A converges. This prevents the infinite
  // loop caused by TC/PC/SF solutions from the same contradiction conflicting.

  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [conceptRoutes, setConceptRoutes] = useState<ConceptRoute[]>([]);


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
  const isLoading = trizQuery.isLoading || subsystemsQuery.isLoading || alternativesQuery.isLoading;

  // ── Computed: Multi-Solution Adoption State from DB (fallback to mock) ──
  const adoptionState: MultiSolutionAdoptionState = useMemo(() => {
    const dbRoutes = conceptRoutesQuery.data;
    const dbPairs = compatibilityPairsQuery.data;

    // If DB has data, build state from it; otherwise fall back to mock
    if (dbRoutes && dbRoutes.length > 0 && dbPairs && dbPairs.length > 0) {
      return {
        matrix: {
          // TODO: Build solutions list from convergence loop output or DB query
          solutions: mockAdoptionState.matrix.solutions,
          pairs: dbPairs,
        },
        recommendedRoutes: dbRoutes,
        // TODO: Compute anti-pattern checks from routes + pairs via AI API
        antiPatternChecks: mockAdoptionState.antiPatternChecks,
      };
    }
    return mockAdoptionState;
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


  const getMustValues = (a: Alternative) => MUST_KEYS.map((k) => a.mustScores[k] ?? null);

  const stepStatuses: AccordionStepStatus[] = useMemo(() => {
    // s0: TRIZ convergence — use DB trizSolutions when convergenceLoop hasn't run
    const loopDone = convergenceLoop.state.status === "converged";
    const hasTrizData = trizSolutions.length > 0;
    const s0 = loopDone || hasTrizData ? "complete" : convergenceLoop.state.status !== "idle" ? "in_progress" : "not_started";
    const confirmed = subsystems.filter((s) => s.confirmed).length;
    const s1 = confirmed > 0 ? "complete" : subsystems.length > 0 ? "in_progress" : "not_started";
    // s2: Decision Hub (was s4)
    const s2 = alternatives.length > 0 ? "complete" : "not_started";
    // s3: MUST (was s5)
    const allMustFilled = alternatives.length > 0 && alternatives.every((a) => getMustValues(a).every((v) => v !== null));
    const s3 = allMustFilled ? "complete" : alternatives.some((a) => getMustValues(a).some((v) => v !== null)) ? "in_progress" : "not_started";
    // s4: Pre-CAD (was s6)
    const passedMust = alternatives.filter((a) => !getMustValues(a).includes("fail"));
    const allScored = passedMust.length > 0 && passedMust.every((a) => Object.values(a.preCadScores).every((v) => v !== null));
    const s4 = allScored ? "complete" : passedMust.some((a) => Object.values(a.preCadScores).some((v) => v !== null)) ? "in_progress" : "not_started";
    return [s0, s1, s2, s3, s4];
  }, [convergenceLoop.state.status, trizSolutions, subsystems, alternatives]);

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
      { label: "MUST 快篩已完成", current: stepStatuses[3] === "complete" ? 1 : 0, target: 1, passed: stepStatuses[3] === "complete" },
    ],
    [passedMustAlts, stepStatuses]
  );

  const phaseGate2Items: CreateGateItem[] = useMemo(
    () => [{ label: "≥1 方案 Pre-CAD overall_pass = True", current: preCadPassedAlts.length, target: 1, passed: preCadPassedAlts.length >= 1 }],
    [preCadPassedAlts]
  );


  // ── v8 (directed): batch generation for ALL contradictions ──────────────
  const handleAiGenDirected = async () => {
    if (!id) return;
    const contrs = contradictionsQuery.data ?? [];
    if (contrs.length === 0) {
      toast.warning('尚無矛盾，無法觸發 TRIZ 方向式求解');
      return;
    }
    setAiLoading((p) => ({ ...p, trizGen: true }));
    try {
      const results = await Promise.allSettled(contrs.map(c => solveDirectedSingle(c)));
      const ok = results.filter(r => r.status === 'fulfilled' && r.value !== null).length;
      queryClient.invalidateQueries({ queryKey: queryKeys.directed_triz_solutions.byProject(id) });
      if (ok === 0) {
        toast.error('TRIZ 方向式求解全部失敗');
      } else if (ok < contrs.length) {
        toast.warning(`${ok}/${contrs.length} 條矛盾產出方向式診斷`);
      } else {
        toast.success(`已為 ${ok} 條矛盾產出方向式 (TC/PC/SF → 方向叢集) 診斷`);
      }
    } catch (err) {
      console.error('Directed TRIZ generation failed:', err);
      toast.error('TRIZ 方向式求解失敗');
    } finally {
      setAiLoading((p) => ({ ...p, trizGen: false }));
    }
  };


  // ── v8: directed adoption — build a ConceptRoute from a directed result ──
  const handleDirectedAdopt = (
    result: ContradictionDirectionResult,
    mode: DirectedAdoptionMode,
    direction?: DirectionGroup,
  ) => {
    // Determine which direction to adopt based on mode
    const adoptedDir: DirectionGroup | null =
      mode === 'top1' ? result.top1 :
      mode === 'top2' ? result.top2 :
      direction ?? null;                   // 'custom' requires explicit direction
    if (!adoptedDir) {
      toast.error('找不到可採納的方向');
      return;
    }
    // Find score for the adopted direction
    const adoptedScore: DirectionScore | null =
      result.scored_directions.find(s => s.direction_id === adoptedDir.direction_id) ?? null;

    // Build CompositionEntry[] from the direction's solutions
    const composition: CompositionEntry[] = adoptedDir.solutions.map((sol) => ({
      solutionId: `${result.contradiction_id}::${adoptedDir.direction_id}::${sol.principle_name}`,
      sourcePrinciple: sol.principle_name,
      concrete: sol.suggestion,
      dimension: sol.path,
      adoptionType: 'M1' as const,   // default to M1 (different dimension) — refineable later
    }));

    const directedMeta: DirectedConceptRouteMeta = {
      contradictionId: result.contradiction_id,
      adoptedDirection: adoptedDir,
      adoptedScore: adoptedScore,
      availableDirectionIds: result.all_directions.map(d => d.direction_id),
      adoptionMode: mode,
      adoptionRationale: `${mode === 'top1' ? 'Top-1' : mode === 'top2' ? 'Top-2' : '自選'} 方向：${adoptedDir.direction_name}`,
    };

    const route: ConceptRoute = {
      id: `DR-${result.contradiction_id.slice(0, 8)}-${Date.now().toString(36)}`,
      type: 'directed',
      composition,
      compositionRationale:
        `方向式採納 ${adoptedDir.direction_name}（score=${adoptedScore?.weighted_total?.toFixed(1) ?? '?'}）`,
      antiPatternWarnings: [],
      directed: directedMeta,
      createdAt: new Date().toISOString(),
    };

    setConceptRoutes((prev) => [...prev, route]);
    const modeLabel = mode === 'top1' ? 'Top-1' : mode === 'top2' ? 'Top-2' : '自選';
    toast.success(
      `已採納 ${modeLabel} 方向「${adoptedDir.direction_name}」→ 候選池 ${conceptRoutes.length + 1} 條`,
    );
  };

  // ── v8: cross-contradiction consolidation ─────────────────────────────────
  const handleConsolidate = async () => {
    if (!id) return;
    const resultList = Object.values(directedResults);
    if (resultList.length < 2) {
      toast.warning('至少需要 2 條矛盾的方向式結果才能進行 consolidation');
      return;
    }
    setAiLoading((p) => ({ ...p, consolidate: true }));
    try {
      const resp = await trizConsolidate({ project_id: id, results: resultList });
      await upsertConsolidationResult(id, resp.consolidation);
      queryClient.invalidateQueries({ queryKey: queryKeys.triz_consolidation_results.byProject(id) });
      const statusLabel =
        resp.consolidation.status === 'compatible' ? '✅ 全部相容' :
        resp.consolidation.status === 'resolved_with_swap' ? '⚠️ 已 swap Top2 解決衝突' :
        '❌ 存在衝突';
      toast.success(`跨矛盾整合完成：${statusLabel}`);
    } catch (err) {
      console.error('Consolidation failed:', err);
      const msg = err instanceof Error ? err.message : String(err);
      toast.error('跨矛盾整合失敗', { description: msg.slice(0, 120) });
    } finally {
      setAiLoading((p) => ({ ...p, consolidate: false }));
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
    // contract hash into local session state so downstream steps can detect
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

  // @deprecated v9: SCAMPER handlers removed (toggleScamperAdopt, reconfirmSubsystemContracts, handleGenerateScamperForSubsystem)

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
        toast.warning("尚無已採用的 TRIZ 解法，請先在 TRIZ 分析步驟採用解法，或手動新增方案");
      } else {
        toast.success(`已從 ${adoptedTriz.length} 條 TRIZ 解法整合 ${created} 個候選方案`);
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

  const navigateTo = (step: number) => {
    setCurrentStep(step);
  };
  // Requires at least one RD-confirmed subsystem before entering Decision Hub
  const canProceedFromSubsystem = subsystems.some(s => s.confirmed);

  const goNext = () => {
    if (currentStep === 1 && !canProceedFromSubsystem) {
      toast.error("請至少確認一個子系統後再進入決策中心");
      return;
    }
    setCurrentStep(Math.min(currentStep + 1, 4));
  };
  const goPrev = () => {
    setCurrentStep(Math.max(currentStep - 1, 0));
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
    // Analysis zone (steps 0-1): show TRIZ/Subsystem as tabbed sub-steps
    if (currentStep <= 1) {
      return (
        <div className="space-y-4">
          <div className="flex gap-1 border-b pb-2">
            {[
              { step: 0, label: "① TRIZ 解矛盾（含跨域去錨定）" },
              { step: 1, label: "② 子系統定義" },
            ].map(({ step, label }) => (
              <button
                key={step}
                onClick={() => navigateTo(step)}
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
          {currentStep === 0 && renderTrizConvergence()}
          {currentStep === 1 && renderSubsystem()}
        </div>
      );
    }

    switch (currentStep) {
      case 2: return renderAlternatives();
      case 3: return renderMust();
      case 4: return renderPreCad();
      default: return null;
    }
  };

  // ── Step 0: TRIZ 解矛盾（含跨域去錨定）— 分層 drill-down 診斷 ──
  function renderTrizConvergence() {
    // v8: startPhaseA removed — L1 critic per-card replaces global Phase A scan
    const { state, confirmSeverity, forceContinue, retryBranch } = convergenceLoop;
    const contradictionsList = contradictionsQuery.data ?? [];
    const canStart = !!id && contradictionsList.length > 0;

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

        {/* ── Section 0a: OZ-OT 前置分析 + Evidence Coverage ── */}
        {id && (
          <div className="space-y-3">
            <OzOtPanel
              projectId={id}
              problemDescription={contradictionDescs.join('；')}
              contradictions={contradictionDescs}
            />
            <EvidenceCoverageGauge projectId={id} />
          </div>
        )}

        {/* ── Section A: TRIZ candidate generation (directed) ── */}
          <div className="space-y-3" data-testid="triz-directed-section">
            <div>
              <h3 className="text-sm font-semibold">方向導向 TRIZ 解法（TC / PC / SF 並行 → 方向聚類 → 評分）</h3>
              <p className="text-xs text-muted-foreground">
                每條矛盾同時啟動 TC·PC·SF 三路解法，LLM 將所有解法依實作方向聚類、評分，產出 Top1/Top2 推薦方向。
                跨矛盾整合後執行 consolidate 相容性檢查與衝突報告。
              </p>
            </div>

            {Object.keys(directedResults).length === 0 ? (
              <Card className="border-dashed border-2 border-primary/30">
                <CardContent className="p-6 text-center space-y-3">
                  <div className="mx-auto w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {contradictionsList.length === 0
                      ? '前置條件：需先完成矛盾識別'
                      : `已識別 ${contradictionsList.length} 條矛盾，可產出方向導向解法`}
                  </p>
                  <AiButton loading={!!aiLoading.trizGen} onClick={handleAiGenDirected} disabled={!canStart}>
                    {aiLoading.trizGen ? '方向導向求解中...' : 'AI 產出方向導向解法'}
                  </AiButton>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {topLevelContradictions.map(tc => {
                  const result = directedResults[tc.id];
                  return (
                    <div key={tc.id} className="space-y-2">
                      <p className="text-[11px] font-medium text-muted-foreground truncate" title={tc.engineeringStatement || tc.naturalDescription}>
                        TC: {tc.engineeringStatement || tc.naturalDescription || tc.id.slice(0, 8)}
                      </p>
                      {solvingIds.has(tc.id) && !result && (
                        <Card className="border-dashed border animate-pulse"><CardContent className="p-3 text-xs text-muted-foreground flex items-center gap-2"><Loader2 className="h-3 w-3 animate-spin" />方向導向求解中...</CardContent></Card>
                      )}
                      {!result && !solvingIds.has(tc.id) && (
                        <Button size="sm" variant="outline" className="text-[11px] gap-1" onClick={() => handleSolveDirectedSingle(tc.id)}>
                          <Sparkles className="h-3 w-3" />
                          求解此矛盾（方向導向）
                        </Button>
                      )}
                      {result && (
                        <DirectionResultCard
                          result={result}
                          onAdopt={(mode, direction) => handleDirectedAdopt(result, mode, direction)}
                        />
                      )}
                    </div>
                  );
                })}
                <div className="flex gap-2">
                  <AiButton aiVariant="outline" size="sm" loading={!!aiLoading.trizGen} onClick={handleAiGenDirected} className="text-xs">
                    重新產出方向導向解法
                  </AiButton>
                  {Object.keys(directedResults).length >= 2 && (
                    <AiButton aiVariant="outline" size="sm" loading={!!aiLoading.consolidate} onClick={handleConsolidate} className="text-xs">
                      {aiLoading.consolidate ? '整合中...' : '跨矛盾整合 (Consolidate)'}
                    </AiButton>
                  )}
                </div>
              </div>
            )}
          </div>

        {/* Consolidation panel — shows multi-contradiction direction integration result */}
        {consolidationQuery.data && (
          <ConsolidationPanel consolidation={consolidationQuery.data} />
        )}

        <KnowledgeRefsPanel refs={mockStepKnowledgeRefs[0] ?? []} />
      </div>
    );
  }

  // ── Step 1: 子系統定義 ──
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
              。已確認的子系統將作為候選方案生成的分析範圍。
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

        <KnowledgeRefsPanel refs={mockStepKnowledgeRefs[1] ?? []} />

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

  // ── Step 2: Decision Hub (Alternatives) ──
  function renderAlternatives() {
    // ── Candidate pool: aggregate from all sources ──
    const SOURCE_BADGE: Record<string, { label: string; cls: string }> = {
      triz_tc: { label: 'TRIZ-TC', cls: 'bg-blue-100 text-blue-700' },
      triz_pc: { label: 'TRIZ-PC', cls: 'bg-blue-100 text-blue-700' },
      triz_sf: { label: 'TRIZ-SF', cls: 'bg-blue-100 text-blue-700' },
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
              匯集 TRIZ 所有候選方案。RD 確認後執行交叉檢查。
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


        {/* ── Candidate cards ── */}
        {alternatives.length === 0 ? (
          <div className="text-center py-12 space-y-3 bg-muted/30 rounded-xl border border-dashed">
            <LayoutGrid className="h-8 w-8 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground font-medium">候選池為空</p>
            <p className="text-xs text-muted-foreground">
              點擊「自動匯入候選」從已採用的 TRIZ 解法中自動匯入，或手動新增。
            </p>
          </div>
        ) : (
          <div className="grid gap-3">
            {alternatives.map((alt, i) => {
              const srcBadge = getSourceBadge(alt.source);
              return (
                <Card key={alt.id} className={cn("border-l-[3px] transition-all", "border-l-blue-400")}>
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
                  檢查 {adoptedCount} 個方案之間是否存在跨矛盾衝突或參數干涉。
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

        {/* Compatibility Matrix — from adoption state (concept routes + compatibility pairs) */}
        {adoptionState.matrix.pairs.length > 0 && (
          <CompatibilityMatrix matrix={adoptionState.matrix} />
        )}

        <KnowledgeRefsPanel refs={mockStepKnowledgeRefs[2] ?? []} />
      </div>
    );
  }

  // ── Step 3: MUST 快篩 ──
  function renderMust() {
    if (alternatives.length === 0) {
      return (
        <div className="text-center py-16 space-y-3">
          <p className="text-muted-foreground">請先在「方案整合」中建立方案</p>
          <Button variant="secondary" onClick={() => navigateTo(3)}>
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
        <KnowledgeRefsPanel refs={mockStepKnowledgeRefs[3] ?? []} />
      </div>
    );
  }

  // ── Step 4: Pre-CAD 審查 ──
  function renderPreCad() {
    const eligible = alternatives.filter((a) => !Object.values(a.mustScores).includes("fail") && Object.values(a.mustScores).some((v) => v !== null));
    if (eligible.length === 0) {
      return (
        <div className="text-center py-16 space-y-3">
          <p className="text-muted-foreground">請先在 MUST 快篩中完成評估</p>
          <Button variant="secondary" onClick={() => navigateTo(4)}>
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
        <KnowledgeRefsPanel refs={mockStepKnowledgeRefs[4] ?? []} />
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
              <h3 className="text-sm font-semibold">Gate X2 — 方案創造完整性</h3>
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

        {currentStep === 4 && (
          <Card className="border-2 border-accent/30 bg-accent/5">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center gap-3">
                <Flag className="h-5 w-5 text-accent shrink-0" />
                <h3 className="text-sm font-semibold">Phase Gate X — Diverge 完成</h3>
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
                  通過 Phase Gate X → 進入 CAD 繪製 <ArrowRight className="h-4 w-4 ml-1.5" />
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
          <HelpTooltip text="TRIZ 解矛盾（含跨域去錨定）→ 子系統定義 → 候選方案決策中心 → MUST 快篩 → Pre-CAD 審查。所有方案在決策中心攤平比較後進入統一評估。" className="ml-2 align-middle" />
        </h1>
        <p className="text-sm text-muted-foreground mt-1">系統化分析 · 方案匯流 · 統一評估</p>
      </div>

      <CreateStepper
        steps={STEPS}
        statuses={stepStatuses}
        currentStep={currentStep}
        onStepClick={(step) => navigateTo(step)}
      />

      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className={cn(
            "h-8 w-8 rounded-full flex items-center justify-center text-sm font-semibold",
            "bg-primary text-primary-foreground"
          )}>
            {currentStep + 1}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold flex items-center gap-1">
                {STEPS[currentStep].label}
              </h2>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                ZONE_LABELS[STEPS[currentStep].zone].color
              }`}>
                {ZONE_LABELS[STEPS[currentStep].zone].badge}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {STEPS[currentStep].description}
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
        {currentStep < 4 ? (
          <div className="flex flex-col items-end gap-1">
            <Button
              onClick={goNext}
              disabled={currentStep === 1 && !canProceedFromSubsystem}
            >
              下一步 <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
            {currentStep === 1 && !canProceedFromSubsystem && (
              <span className="text-[10px] text-muted-foreground">
                請至少確認一個子系統後再進入決策中心
              </span>
            )}
          </div>
        ) : (
          <div />
        )}
      </div>
    </div>
  );
}
