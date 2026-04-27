import { z } from "zod";

export type AssumptionStatus = "pending" | "validating" | "validated" | "refuted";

export type VerificationStage = "unplanned" | "planned" | "in_progress" | "completed" | "refuted";

export interface Assumption {
  id: string;
  code: string; // A-001, A-002, etc.
  content: string;
  source: string;
  sourceType: "manual" | "ai_extracted"; // AI 提取標記
  worstConsequence: string;
  worstSeverity: "critical" | "high" | "medium" | "low"; // for auto-sort
  minValidation: string;
  validationCost: string;
  validationMethod?: string;
  estimatedDays?: number;
  status: AssumptionStatus;
  verificationStage: VerificationStage;
  impactScope: string[]; // related contradiction/module IDs
  createdAt: string;
  updatedAt: string;
}

export const ASSUMPTION_STATUS_LABELS: Record<AssumptionStatus, string> = {
  pending: "待驗證",
  validating: "驗證中",
  validated: "已驗證",
  refuted: "已推翻",
};

export const VERIFICATION_STAGE_LABELS: Record<VerificationStage, string> = {
  unplanned: "待規劃",
  planned: "待驗證",
  in_progress: "驗證中",
  completed: "已完成",
  refuted: "已推翻",
};

export const VERIFICATION_METHODS = [
  "仿真分析",
  "原型測試",
  "專家審查",
  "文獻引用",
  "實測驗證",
  "其他",
];

export const SEVERITY_LABELS: Record<Assumption["worstSeverity"], string> = {
  critical: "致命",
  high: "高",
  medium: "中",
  low: "低",
};

// CLD types
export interface CLDNode {
  id: string;
  label: string;
  x: number;
  y: number;
  type: "assumption" | "variable";
  assumptionId?: string;
  isLeverage?: boolean; // AI-identified leverage point
}

export interface CLDEdge {
  id: string;
  from: string;
  to: string;
  polarity: "+" | "-"; // positive or negative feedback
}

export interface CLDLoop {
  id: string;
  type: "R" | "B"; // Reinforcing or Balancing
  nodeIds: string[];
  label: string;
}

// Contradiction traceability
export interface LinkedContradiction {
  id: string;
  description: string;
  severity: "fatal" | "major" | "minor";
  resolved: boolean;
}

export interface SocraticFeedback {
  id: string;
  type: "causal_inquiry" | "assumption_challenge";
  content: string;
  timestamp: string;
}

export interface ConvergenceImpact {
  affectedRoutes: number;
  severity: "high" | "medium" | "low";
  message: string;
}

export const assumptionSchema = z.object({
  content: z.string().trim().min(10, "假設內容為必填項，且需至少 10 個字元。").max(300, "假設內容不可超過 300 個字元。"),
  source: z.string().trim().min(1, "依據來源為必填項。"),
  worstConsequence: z.string().trim().min(1, "最壞後果為必填項。"),
  worstSeverity: z.enum(["critical", "high", "medium", "low"]),
  minValidation: z.string().trim().min(1, "最小驗證方法為必填項。"),
  validationCost: z.string().trim().min(1, "驗證成本/週期為必填項。"),
  validationMethod: z.string().optional(),
  estimatedDays: z.number().optional(),
  impactScope: z.array(z.string()).optional(),
});

export type AssumptionFormValues = z.infer<typeof assumptionSchema>;
