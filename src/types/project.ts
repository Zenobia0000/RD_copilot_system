export type ProjectStatus = "in_progress" | "completed" | "archived";

export type StepStatus = "passed" | "in_progress" | "not_started";

export interface PhaseProgress {
  "D1": StepStatus;
  "D2": StepStatus;
  "PG-D": StepStatus;
  "X1": StepStatus;
  "X2": StepStatus;
  "PG-X": StepStatus;
  "V1": StepStatus;
  "V2": StepStatus;
  "PG-V": StepStatus;
}

export interface QuickStats {
  contradictions_count: number;
  assumptions_count: number;
  alternatives_count: number;
  risks_count: number;
  experiments_count: number;
  evidence_items_count: number;
}

/** MUST criterion config derived from Brief constraints/KPIs */
export interface MustCriterionConfig {
  id: string;
  label: string;
  source: string;
  threshold?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  progress: number; // 0-100
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  phase: string; // e.g. "Phase I", "Phase II", "Phase III"
  mission?: string;
  hardConstraints?: string;
  softObjectives?: string;
  criticalKPIs?: CriticalKPI[];
  phase_progress: PhaseProgress;
  quick_stats: QuickStats;
  gates_passed: number;
  gates_total: number;
  must_criteria_config?: MustCriterionConfig[];
}

export interface CriticalKPI {
  id: string;
  name: string;
  target: string;
  current: string;
  status: "on_track" | "at_risk" | "off_track" | "unknown";
}

export interface ProjectHistoryItem {
  id: string;
  date: string;
  title: string;
  summary: string;
  author: string;
  type: "decision" | "milestone" | "review" | "task";
  relatedPage?: string; // route path
}

export interface ProjectStage {
  id: string;
  label: string;
  path: string;
  phase: string;
  status: "completed" | "in_progress" | "not_started";
  icon: string; // lucide icon name
}

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  in_progress: "進行中",
  completed: "已完成",
  archived: "已封存",
};

// 6+1 navigation card definition
export interface NavCardDef {
  id: string;
  enName: string;
  zhName: string;
  phase: "Phase 1" | "Phase 2" | "Phase 3";
  icon: string;
  route: string; // relative to /projects/:id/
  subSteps: number; // total sub-steps
  completedSteps: number;
  requiredGate?: string; // gate that must be passed to unlock
  locked: boolean;
  lockReason?: string;
}

// Dashboard gauge / convergence card types
export interface PreCadScore {
  score: number; // 0-100
  fatalResolved: number;
  fatalTotal: number;
  majorResolved: number;
  majorTotal: number;
}

export interface ContradictionConvergence {
  totalNodes: number;
  fatalCount: number;
  majorCount: number;
  minorCount: number;
  hasCircularDependency: boolean;
  healthWarning: boolean; // true if nodes > 5 or circular
}
