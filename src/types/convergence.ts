import type { ContradictionSeverity } from './contradiction';
import type { ConvergenceNode, ConvergenceEdge, HealthStatus } from './solution';
import type { TrizPath } from './create';

// ── Convergence Loop States ──

export type ConvergenceStatus = 'idle' | 'exploring' | 'scanning' | 'converged' | 'halted';
export type BranchStatus = 'exploring' | 'converged' | 'halted';

// ── Exploration Data ──

export interface ExplorationSolution {
  id: string;
  path: TrizPath;
  principleNumber: number | null;
  principleName: string;
  suggestion: string;
  score: number; // AI 評分 1-10
  isRecommended: boolean; // AI 推薦採用
}

export interface ScanResultEntry {
  id: string;
  description: string;
  severity: ContradictionSeverity;
  resolved: boolean;
  sourceSolutionId: string;
}

export interface ExplorationRound {
  roundNumber: number;
  solutions: ExplorationSolution[];
  adoptedSolutionId: string | null;
  scanResult: {
    newContradictions: ScanResultEntry[];
    hasNewFatalMajor: boolean;
  };
  timestamp: string;
}

export interface BranchExploration {
  contradictionId: string;
  contradictionLabel: string; // e.g. "速度↑ vs 噪音↑"
  rounds: ExplorationRound[];
  status: BranchStatus;
  depth: number;
}

export interface MinorContradiction {
  id: string;
  description: string;
  sourceBranchId: string;
  sourceRound: number;
}

// ── Main Convergence State ──

export type ConvergencePhase = 'B';  // v8: Phase A retired — L1 critic subsumes

export interface ConvergenceState {
  iteration: number;
  status: ConvergenceStatus;
  phase: ConvergencePhase;
  branches: BranchExploration[];
  graph: {
    nodes: ConvergenceNode[];
    edges: ConvergenceEdge[];
  };
  health: HealthStatus;
  confidence: number; // 0-100
  fatalCount: { resolved: number; total: number };
  majorCount: { resolved: number; total: number };
  minorCount: number;
  riskRegister: MinorContradiction[];
}

// ── Hook Return Type ──

export interface ConvergenceLoopActions {
  state: ConvergenceState;
  startExploration: () => void;
  confirmSeverity: (contradictionId: string, severity: ContradictionSeverity) => void;
  forceHalt: () => void;
  forceContinue: () => void;
  retryBranch: (contradictionId: string) => void;
  addContradiction: (description: string, severity: ContradictionSeverity, sourceBranchId: string) => void;
  markResolved: (contradictionId: string, severity: ContradictionSeverity) => void;
}
