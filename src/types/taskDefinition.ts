import { z } from "zod";

// Constraint with auto-generated code
export interface BriefConstraint {
  id: string;
  constraint_code: string; // M1, M2, ...
  description: string;
  source: string;
}

// KPI with 4 columns
export interface BriefKPI {
  id: string;
  kpi_name: string;
  target_value: string;
  unit: string;
  measurement_method: string;
}

// 5W1H AI task definition
export interface TaskDefinition5W1H {
  who: string;
  what: string;
  where: string;
  when: string;
  why: string;
  how: string;
}

// Gate checklist item
export interface GateCheckItem {
  label: string;
  passed: boolean;
}

// Full Brief data
export interface BriefData {
  mission: string;
  constraints: BriefConstraint[];
  kpis: BriefKPI[];
  task_definition_5w1h: TaskDefinition5W1H | null;
}

// Validation schema
export const briefValidationSchema = z.object({
  mission: z
    .string()
    .trim()
    .min(10, "Mission 為必填項，且需至少 10 個字元。"),
  constraints: z
    .array(
      z.object({
        id: z.string(),
        constraint_code: z.string(),
        description: z.string().trim().min(2, "約束描述至少 2 個字元。").max(200),
        source: z.string().max(200).optional(),
      })
    )
    .min(1, "至少需要 1 項硬約束。"),
  kpis: z
    .array(
      z.object({
        id: z.string(),
        kpi_name: z.string().trim().min(2, "指標名稱至少 2 個字元。").max(80),
        target_value: z.string().trim().min(1, "目標值為必填。").max(50),
        unit: z.string().trim().min(1, "單位為必填。").max(20),
        measurement_method: z.string().trim().min(2, "衡量方式至少 2 個字元。").max(200),
      })
    )
    .min(1, "至少需要 1 項 KPI。"),
});

// Legacy support types (kept for backward compatibility)
export interface TaskDefinitionKPI {
  id: string;
  name: string;
  target: string;
  method: string;
}

export interface TaskDefinitionData {
  mission: string;
  hardConstraints: string[];
  softObjectives: string[];
  nonGoals: string[];
  criticalKPIs: TaskDefinitionKPI[];
}

export const taskDefinitionSchema = z.object({
  mission: z.string().trim().min(10),
  hardConstraints: z.array(z.string().trim().min(5).max(200)),
  softObjectives: z.array(z.string().trim().min(5).max(200)),
  nonGoals: z.array(z.string().trim().min(5).max(200)),
  criticalKPIs: z.array(
    z.object({
      id: z.string(),
      name: z.string().trim().min(3),
      target: z.string().trim().min(1),
      method: z.string().trim().min(1),
    })
  ).min(1),
});

export type TaskDefinitionFormValues = z.infer<typeof taskDefinitionSchema>;
