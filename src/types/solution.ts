import { ContradictionSeverity } from "./contradiction";

export interface MustCriteria {
  id: string;
  label: string;
  passed: boolean | null; // null = not evaluated
}

export interface SolutionRisk {
  id: string;
  description: string;
  severity: "low" | "medium" | "high";
  mitigation: string;
}

export interface SecondaryContradiction {
  id: string;
  description: string;
  severity: ContradictionSeverity;
  resolved: boolean;
}

export interface Solution {
  id: string;
  projectId: string;
  name: string;
  description: string;
  mechanism: string;
  assumptions: string[];
  risks: SolutionRisk[];
  minValidation: string;
  mustCriteria: MustCriteria[];
  relatedContradictionIds: string[];
  secondaryContradictions: SecondaryContradiction[];
  contradictionSeverity: ContradictionSeverity;
  createdAt: string;
  updatedAt: string;
}

// DAG types for convergence graph
export interface ConvergenceNode {
  id: string;
  label: string;
  type: "contradiction" | "solution";
  severity?: ContradictionSeverity;
  resolved?: boolean;
  x: number;
  y: number;
}

export interface ConvergenceEdge {
  from: string;
  to: string;
}

export type HealthStatus = "healthy" | "warning" | "critical" | "circular";
