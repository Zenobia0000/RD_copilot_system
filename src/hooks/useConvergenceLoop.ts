/**
 * useConvergenceLoop — AI autonomous contradiction convergence loop
 *
 * Implements the E2E spec's Fully Auto TRIZ convergence using the real
 * /convergence/scan API endpoint:
 *   - AI explores each contradiction branch in parallel (TC/PC/SF)
 *   - Each round: call convergenceScan → process secondary contradictions
 *   - Fatal/Major → auto-trigger next round (no iteration limit)
 *   - Minor → risk register (non-blocking)
 *   - Converged when convergence_score >= 80 or no new fatal/major
 *   - Halted when architecture_health is critical/circular or force_pause
 *
 * Accepts real Contradiction[] from Supabase (via useContradictions) and
 * calls the backend API for each convergence scan round.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import type { ContradictionSeverity } from '@/types/contradiction';
import type { Contradiction } from '@/types/contradiction';
import { supabase } from '@/integrations/supabase/client';
import type { HealthStatus, ConvergenceNode, ConvergenceEdge } from '@/types/solution';
import type {
  ConvergenceState,
  ConvergenceLoopActions,
  BranchExploration,
  MinorContradiction,
} from '@/types/convergence';
import {
  convergenceScan,
  getApiErrorMessage,
} from '@/lib/api';
import { evaluateConvergence, recalcConfidenceOnAdd, resolveContradiction } from './convergenceLogic';
import type {
  ConvergenceAlternativeInput,
  ConvergenceScanResponse,
  SecondaryContradictionResult,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Hook configuration
// ---------------------------------------------------------------------------

export interface UseConvergenceLoopOptions {
  /** Current project ID (from route params). Required for API calls. */
  projectId: string | undefined;
  /** Real contradictions from Supabase via useContradictions(). */
  contradictions: Contradiction[];
  /** Alternatives to evaluate (passed through to convergenceScan). */
  alternatives?: ConvergenceAlternativeInput[];
  /** Phase 1 context for richer AI reasoning. */
  mission?: string;
  constraints?: string[];
  kpis?: string[];
}

// ---------------------------------------------------------------------------
// Delay between convergence rounds (visual pacing)
// ---------------------------------------------------------------------------
const STEP_DELAY_MS = 1500;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mapArchitectureHealth(health: string): HealthStatus {
  switch (health) {
    case 'critical': return 'critical';
    case 'circular': return 'circular';
    case 'warning': return 'warning';
    case 'healthy': return 'healthy';
    default: return 'healthy';
  }
}

function mapSeverity(s: string): ContradictionSeverity {
  if (s === 'fatal' || s === 'major' || s === 'minor') return s;
  return 'minor';
}

let nodeIdCounter = 0;
function nextNodeId(prefix: string): string {
  nodeIdCounter += 1;
  return `${prefix}-${nodeIdCounter}`;
}

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const initialState: ConvergenceState = {
  iteration: 0,
  status: 'idle',
  phase: 'B',  // v8: Phase A retired — always Phase B
  branches: [],
  graph: { nodes: [], edges: [] },
  health: 'healthy',
  confidence: 0,
  fatalCount: { resolved: 0, total: 0 },
  majorCount: { resolved: 0, total: 0 },
  minorCount: 0,
  riskRegister: [],
};

// ---------------------------------------------------------------------------
// DB persistence helpers (convergence_snapshots table)
// ---------------------------------------------------------------------------

async function persistState(projectId: string, state: ConvergenceState) {
  await supabase
    .from('convergence_snapshots')
    .upsert(
      { project_id: projectId, state: state as unknown as Record<string, unknown> },
      { onConflict: 'project_id' },
    );
}

async function restoreState(projectId: string): Promise<ConvergenceState | null> {
  const { data } = await supabase
    .from('convergence_snapshots')
    .select('state')
    .eq('project_id', projectId)
    .maybeSingle();
  if (!data?.state) return null;
  return data.state as unknown as ConvergenceState;
}

// ---------------------------------------------------------------------------
// Hook implementation
// ---------------------------------------------------------------------------

export function useConvergenceLoop(options: UseConvergenceLoopOptions): ConvergenceLoopActions {
  const {
    projectId,
    contradictions,
    alternatives = [],
    mission,
    constraints,
    kpis,
  } = options;

  const [state, _setStateRaw] = useState<ConvergenceState>(initialState);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef(false);
  const generationRef = useRef(0);

  // Wrapper: update state + persist to DB (supports direct value or updater fn)
  const setState = useCallback((action: ConvergenceState | ((prev: ConvergenceState) => ConvergenceState)) => {
    _setStateRaw((prev) => {
      const next = typeof action === 'function' ? action(prev) : action;
      if (projectId && next.status !== 'idle') {
        persistState(projectId, next);
      }
      return next;
    });
  }, [projectId]);

  // Restore from DB on mount
  useEffect(() => {
    if (!projectId) return;
    restoreState(projectId).then((saved) => {
      if (saved && saved.status !== 'idle') {
        // 'exploring' in DB means the loop was interrupted (page reload / crash).
        // Timers aren't persisted, so restore as 'halted' to let user re-trigger.
        if (saved.status === 'exploring') {
          _setStateRaw({ ...saved, status: 'halted' });
        } else {
          _setStateRaw(saved);
        }
      }
    });
  }, [projectId]);

  // Phase A = contradiction-only, Phase B = full cross-check with alternatives
  const phaseRef = useRef<'A' | 'B'>('A');

  // ------------------------------------------------------------------
  // Graph builder: adds nodes/edges from a scan response to the graph
  // ------------------------------------------------------------------
  const appendToGraph = useCallback(
    (
      prevNodes: ConvergenceNode[],
      prevEdges: ConvergenceEdge[],
      _fallbackSourceId: string, // kept for backward compat, prefer per-item source
      newContradictions: SecondaryContradictionResult[],
    ): { nodes: ConvergenceNode[]; edges: ConvergenceEdge[] } => {
      const nodes = [...prevNodes];
      const edges = [...prevEdges];
      const maxX = nodes.length > 0 ? Math.max(...nodes.map((n) => n.x)) : 0;
      const nodeIdSet = new Set(nodes.map((n) => n.id));

      for (const nc of newContradictions) {
        const nid = nextNodeId('sc');
        const severity = mapSeverity(nc.severity);
        nodes.push({
          id: nid,
          label: nc.description,
          type: 'contradiction',
          severity,
          resolved: severity === 'minor',
          x: maxX + 160,
          y: 20 + nodes.filter((n) => n.type === 'contradiction').length * 60,
        });
        // Use per-item source_alternative for correct parent edge.
        // Fall back to _fallbackSourceId only if source not found in graph.
        const parentId = nc.source_alternative && nodeIdSet.has(nc.source_alternative)
          ? nc.source_alternative
          : _fallbackSourceId;
        edges.push({ from: parentId, to: nid });
      }

      return { nodes, edges };
    },
    [],
  );

  // ------------------------------------------------------------------
  // Build initial graph from contradictions list
  // ------------------------------------------------------------------
  const buildInitialGraph = useCallback(
    (contrs: Contradiction[]): { nodes: ConvergenceNode[]; edges: ConvergenceEdge[] } => {
      const nodes: ConvergenceNode[] = [];
      const edges: ConvergenceEdge[] = [];
      contrs.forEach((c, i) => {
        nodes.push({
          id: c.id,
          label: c.naturalDescription,
          type: 'contradiction',
          severity: c.severity,
          resolved: c.resolved ?? false,
          x: 20,
          y: 20 + i * 80,
        });
      });
      return { nodes, edges };
    },
    [],
  );

  // ------------------------------------------------------------------
  // Run a single convergence scan round via the API
  // ------------------------------------------------------------------
  const runScanRound = useCallback(
    async (
      iteration: number,
      branches: BranchExploration[],
      graph: { nodes: ConvergenceNode[]; edges: ConvergenceEdge[] },
      riskRegister: MinorContradiction[],
      fatalCount: { resolved: number; total: number },
      majorCount: { resolved: number; total: number },
      minorCount: number,
    ) => {
      const myGeneration = generationRef.current;
      if (abortRef.current || !projectId) return;

      // Call the real API
      let scanResult: ConvergenceScanResponse;
      try {
        scanResult = await convergenceScan({
          project_id: projectId,
          alternatives: alternatives,  // v8: always Phase B, no empty-list branch
          contradictions: contradictions.map((c) => ({
            id: c.id,
            natural_description: c.naturalDescription,
            severity: c.severity,
            resolved: c.resolved ?? false,
            type: c.type ?? null,
            improving_param: c.improvingParam,
            worsening_param: c.worseningParam,
            engineering_statement: c.engineeringStatement,
            physical_contradiction: c.physicalContradiction,
            sf_substance_1: (c as Record<string, unknown>).sfSubstance1 as string ?? '',
            sf_substance_2: (c as Record<string, unknown>).sfSubstance2 as string ?? '',
            sf_field: (c as Record<string, unknown>).sfField as string ?? '',
          })),
          mission,
          constraints,
          kpis,
          phase: phaseRef.current,
        });
      } catch (err) {
        // On API error, halt the loop
        const msg = getApiErrorMessage(err, '收斂掃描');
        setState((prev) => ({
          ...prev,
          status: 'halted',
          health: 'critical',
        }));
        console.error('[useConvergenceLoop] scan failed:', msg);
        return;
      }

      // Discard stale results if a new exploration was started while we were awaiting
      if (abortRef.current || myGeneration !== generationRef.current) return;

      // Process new contradictions from the scan — skip confirmatory (semantic duplicates)
      const genuineNew = scanResult.new_contradictions.filter((c) => !c.is_confirmatory);
      const newFatal = genuineNew.filter((c) => c.severity === 'fatal');
      const newMajor = genuineNew.filter((c) => c.severity === 'major');
      const newMinor = genuineNew.filter(
        (c) => c.severity !== 'fatal' && c.severity !== 'major',
      );

      // Add minor contradictions to risk register
      const updatedRisk = [...riskRegister];
      for (const nc of newMinor) {
        updatedRisk.push({
          id: nextNodeId('risk'),
          description: nc.description,
          sourceBranchId: nc.source_alternative,
          sourceRound: iteration,
        });
      }

      // Update graph: use the first contradiction node as source if available
      const sourceNodeId = graph.nodes.length > 0 ? graph.nodes[graph.nodes.length - 1].id : 'root';
      const updatedGraph = appendToGraph(
        graph.nodes,
        graph.edges,
        sourceNodeId,
        scanResult.new_contradictions,
      );

      // Use pure logic module for convergence evaluation
      const convergenceResult = evaluateConvergence({
        iteration,
        confidence: scanResult.convergence_score,
        fatalCount,
        majorCount,
        scan: {
          newFatal: newFatal.length,
          newMajor: newMajor.length,
          newMinor: newMinor.length,
          noNewContradictions: scanResult.new_contradictions.length === 0,
        },
        forcePause: scanResult.force_pause,
        architectureHealth: scanResult.architecture_health,
      });

      const { fatalCount: updatedFatal, majorCount: updatedMajor } = convergenceResult;
      const updatedMinorCount = minorCount + newMinor.length;
      const health = mapArchitectureHealth(scanResult.architecture_health);

      // Update branches status — per-branch tracking using source_alternative
      const branchesWithNewBlocking = new Set<string>();
      for (const nc of [...newFatal, ...newMajor]) {
        // source_alternative may reference a contradiction ID that belongs to a branch
        const srcId = nc.source_alternative;
        const branch = branches.find((b) => b.contradictionId === srcId);
        if (branch) branchesWithNewBlocking.add(branch.contradictionId);
      }
      const nextStatus = convergenceResult.status;

      // Update branches: match final loop status (converged/halted/exploring)
      const updatedBranches = branches.map((b) => ({
        ...b,
        status: (
          branchesWithNewBlocking.has(b.contradictionId)
            ? 'exploring'
            : nextStatus === 'exploring' ? b.status : nextStatus
        ) as BranchExploration['status'],
        depth: iteration,
      }));

      // Confidence: use API score, but floor to 100 if truly converged (all resolved + no new)
      const displayConfidence = nextStatus === 'converged'
        ? Math.max(scanResult.convergence_score, 100)
        : scanResult.convergence_score;

      setState({
        iteration,
        status: nextStatus,
        phase: phaseRef.current,
        branches: updatedBranches,
        graph: updatedGraph,
        health,
        confidence: displayConfidence,
        fatalCount: updatedFatal,
        majorCount: updatedMajor,
        minorCount: updatedMinorCount,
        riskRegister: updatedRisk,
      });

      // If not converged and not halted, schedule the next round
      if (nextStatus === 'exploring') {
        timerRef.current = setTimeout(() => {
          runScanRound(
            iteration + 1,
            updatedBranches,
            updatedGraph,
            updatedRisk,
            updatedFatal,
            updatedMajor,
            updatedMinorCount,
          );
        }, STEP_DELAY_MS);
      }
    },
    [projectId, alternatives, contradictions, mission, constraints, kpis, appendToGraph],
  );

  // ------------------------------------------------------------------
  // Internal: shared bootstrap logic for starting a scan
  // ------------------------------------------------------------------
  const _bootstrap = useCallback((phase: 'A' | 'B') => {
    abortRef.current = true;
    if (timerRef.current) clearTimeout(timerRef.current);
    generationRef.current += 1;
    abortRef.current = false;

    if (!projectId || contradictions.length === 0) {
      setState({ ...initialState });
      return null;
    }

    phaseRef.current = phase;
    nodeIdCounter = 0;

    const initialBranches: BranchExploration[] = contradictions.map((c) => ({
      contradictionId: c.id,
      contradictionLabel: c.naturalDescription,
      rounds: [],
      status: 'exploring' as const,
      depth: 0,
    }));

    const initialGraph = buildInitialGraph(contradictions);

    const initialFatal = {
      total: contradictions.filter((c) => c.severity === 'fatal').length,
      resolved: contradictions.filter((c) => c.severity === 'fatal' && c.resolved).length,
    };
    const initialMajor = {
      total: contradictions.filter((c) => c.severity === 'major').length,
      resolved: contradictions.filter((c) => c.severity === 'major' && c.resolved).length,
    };

    setState({
      ...initialState,
      status: 'exploring',
      phase,
      branches: initialBranches,
      graph: initialGraph,
      fatalCount: initialFatal,
      majorCount: initialMajor,
    });

    timerRef.current = setTimeout(() => {
      runScanRound(1, initialBranches, initialGraph, [], initialFatal, initialMajor, 0);
    }, STEP_DELAY_MS);

    return { initialBranches, initialGraph, initialFatal, initialMajor };
  }, [projectId, contradictions, buildInitialGraph, runScanRound]);

  // v8: startPhaseA removed — L1 critic subsumes Phase A's role.
  // Only Phase B (cross-check with adopted alternatives) remains.

  // ------------------------------------------------------------------
  // startPhaseB — full cross-check with adopted alternatives
  // Used by Decision Hub: after RD selects which solutions to adopt.
  // ------------------------------------------------------------------
  const startPhaseB = useCallback(() => {
    _bootstrap('B');
  }, [_bootstrap]);

  // ------------------------------------------------------------------
  // startExploration — always Phase B (v8: Phase A retired)
  // ------------------------------------------------------------------
  const startExploration = useCallback(() => {
    _bootstrap('B');
  }, [_bootstrap]);

  // ------------------------------------------------------------------
  // confirmSeverity — override a node's severity in the graph
  // ------------------------------------------------------------------
  const confirmSeverity = useCallback((contradictionId: string, severity: ContradictionSeverity) => {
    setState((prev) => {
      const updatedNodes = prev.graph.nodes.map((n) =>
        n.id === contradictionId && n.type === 'contradiction' ? { ...n, severity } : n,
      );
      return { ...prev, graph: { ...prev.graph, nodes: updatedNodes } };
    });
  }, []);

  // ------------------------------------------------------------------
  // forceHalt — immediately stop the loop
  // ------------------------------------------------------------------
  const forceHalt = useCallback(() => {
    abortRef.current = true;
    if (timerRef.current) clearTimeout(timerRef.current);
    setState((prev) => ({ ...prev, status: 'halted' }));
  }, []);

  // ------------------------------------------------------------------
  // forceContinue — resume after a halt
  // ------------------------------------------------------------------
  const forceContinue = useCallback(() => {
    abortRef.current = false;
    setState((prev) => {
      const newState = { ...prev, status: 'exploring' as const, health: 'warning' as HealthStatus };

      // Schedule the next scan round
      timerRef.current = setTimeout(() => {
        runScanRound(
          prev.iteration + 1,
          prev.branches,
          prev.graph,
          prev.riskRegister,
          prev.fatalCount,
          prev.majorCount,
          prev.minorCount,
        );
      }, STEP_DELAY_MS);

      return newState;
    });
  }, [runScanRound]);

  // ------------------------------------------------------------------
  // retryBranch — re-run exploration for a specific branch
  // ------------------------------------------------------------------
  const retryBranch = useCallback((contradictionId: string) => {
    abortRef.current = false;
    setState((prev) => {
      const updatedBranches = prev.branches.map((b) =>
        b.contradictionId === contradictionId ? { ...b, status: 'exploring' as const } : b,
      );
      const newState = { ...prev, status: 'exploring' as const, branches: updatedBranches };

      timerRef.current = setTimeout(() => {
        runScanRound(
          prev.iteration + 1,
          updatedBranches,
          prev.graph,
          prev.riskRegister,
          prev.fatalCount,
          prev.majorCount,
          prev.minorCount,
        );
      }, STEP_DELAY_MS);

      return newState;
    });
  }, [runScanRound]);

  // ------------------------------------------------------------------
  // addContradiction — manually add a contradiction to the loop
  // ------------------------------------------------------------------
  const addContradiction = useCallback((description: string, severity: ContradictionSeverity, sourceBranchId: string) => {
    const newId = `sc-ext-${Date.now()}`;
    const isFatalMajor = severity === 'fatal' || severity === 'major';

    setState((prev) => {
      const newNode: ConvergenceNode = {
        id: newId,
        label: description,
        type: 'contradiction',
        severity,
        resolved: false,
        x: Math.max(...prev.graph.nodes.map((n) => n.x), 0) + 160,
        y: 180,
      };
      const updatedFatal = severity === 'fatal'
        ? { ...prev.fatalCount, total: prev.fatalCount.total + 1 }
        : prev.fatalCount;
      const updatedMajor = severity === 'major'
        ? { ...prev.majorCount, total: prev.majorCount.total + 1 }
        : prev.majorCount;
      const updatedMinor = severity === 'minor' ? prev.minorCount + 1 : prev.minorCount;
      // Connect to source branch if it exists in the graph
      const sourceExists = prev.graph.nodes.some((n) => n.id === sourceBranchId);
      const updatedGraph = {
        nodes: [...prev.graph.nodes, newNode],
        edges: sourceExists
          ? [...prev.graph.edges, { from: sourceBranchId, to: newId }]
          : prev.graph.edges,
      };

      // Auto re-scan: schedule next round when fatal/major injected
      if (isFatalMajor) {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
          runScanRound(
            prev.iteration + 1,
            prev.branches,
            updatedGraph,
            prev.riskRegister,
            updatedFatal,
            updatedMajor,
            updatedMinor,
          );
        }, STEP_DELAY_MS);
      }

      return {
        ...prev,
        status: isFatalMajor ? 'exploring' : prev.status,
        graph: updatedGraph,
        fatalCount: updatedFatal,
        majorCount: updatedMajor,
        minorCount: updatedMinor,
        // Provisional local estimate until next API scan replaces it
        confidence: isFatalMajor
          ? recalcConfidenceOnAdd(prev.fatalCount, prev.majorCount, severity)
          : prev.confidence,
      };
    });
  }, [runScanRound]);

  // ------------------------------------------------------------------
  // markResolved — called when a TRIZ solution is adopted for a contradiction
  // ------------------------------------------------------------------
  const markResolved = useCallback((contradictionId: string, severity: ContradictionSeverity) => {
    setState((prev) => {
      const { fatalCount, majorCount, confidence } = resolveContradiction(
        prev.fatalCount,
        prev.majorCount,
        severity,
      );

      // Also mark the graph node as resolved
      const updatedNodes = prev.graph.nodes.map((n) =>
        n.id === contradictionId ? { ...n, resolved: true } : n,
      );

      return {
        ...prev,
        fatalCount,
        majorCount,
        confidence,
        graph: { ...prev.graph, nodes: updatedNodes },
      };
    });
  }, []);

  return {
    state,
    startExploration,
    // startPhaseA removed in v8
    startPhaseB,
    confirmSeverity,
    forceHalt,
    forceContinue,
    retryBranch,
    addContradiction,
    markResolved,
  };
}
