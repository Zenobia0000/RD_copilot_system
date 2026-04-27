// Create page types

export type AccordionStepStatus = 'complete' | 'in_progress' | 'not_started';

export interface CreateStepProgress {
  triz: AccordionStepStatus;
  subsystem: AccordionStepStatus;
  alternatives: AccordionStepStatus;
  must: AccordionStepStatus;
  preCad: AccordionStepStatus;
}

// Validation Passport — self-declared validation record for any solution hypothesis
export type EvidenceLevel = 'E0' | 'E1' | 'E2' | 'E3' | 'E4';
export type AssumptionSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface ValidationPassportAssumption {
  content: string;
  category: string; // physics / material / cost / manufacturing / regulatory / integration
  evidenceLevel: EvidenceLevel;
  worstConsequence: string;
  worstSeverity: AssumptionSeverity;
  suggestedExperiment: string;
}

export interface ValidationPassport {
  assumptions: ValidationPassportAssumption[];
  weakPoints: string[];
  requiredVerifications: string[];
  crossDomainSource: string;
  confidenceLevel: number; // 0-1
}

// TRIZ solutions
export type TrizPath = 'TC' | 'PC' | 'SF';
export type TrizActionStatus = 'adopted' | 'edited' | 'skipped' | 'pending';

export interface TrizSolution {
  id: string;
  contradictionId: string;
  path: TrizPath;
  principleNumber: number | null;
  principleName: string;
  suggestion: string;
  status: TrizActionStatus;
  createdAt?: string;
}

// Subsystem
export type SubsystemSource = 'rd' | 'ai' | 'ai_edited';
// SubsystemLevel and InterfaceContract types are now imported from the
// generated single source of truth (mirrored from backend Pydantic schemas).
// This eliminates the previous duplicate definitions in this file.
import type { InterfaceContractMap, SubsystemLevel as GenSubsystemLevel } from '@/types/generated/subsystem';
export type SubsystemLevel = GenSubsystemLevel;

export interface Subsystem {
  id: string;
  name: string;
  level: SubsystemLevel;
  reason: string;
  relatedContradictions: string[];
  confirmed: boolean;
  parentId?: string | null;
  interfaces?: string[];
  interfaceContracts?: InterfaceContractMap;
  source: SubsystemSource;
  createdAt?: string;
  /**
   * Snapshot hash of `interfaceContracts` captured at the moment RD confirmed
   * the subsystem. Local-session state only (not persisted to Supabase in
   * Wave 6 — see WBS 10.1). Used by the SCAMPER page to detect contract
   * drift after confirmation and force re-confirm before regenerating.
   */
  confirmedContractsHash?: string;
}

// SCAMPER
/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
export type ScamperAction = 'S' | 'C' | 'A' | 'M' | 'P' | 'E' | 'R';
/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
export const SCAMPER_LABELS: Record<ScamperAction, { en: string; zh: string }> = {
  S: { en: 'Substitute', zh: '替代' },
  C: { en: 'Combine', zh: '結合' },
  A: { en: 'Adapt', zh: '適應' },
  M: { en: 'Modify', zh: '修改' },
  P: { en: 'Put to other use', zh: '其他用途' },
  E: { en: 'Eliminate', zh: '消除' },
  R: { en: 'Rearrange', zh: '重排' },
};

/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
export interface ScamperNewContradiction {
  id: string;
  description: string;
  severity: 'fatal' | 'major' | 'minor';
  fedBack: boolean;  // 是否已回饋至收斂圖
}

/** @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions */
export interface ScamperVariant {
  id: string;
  subsystemId: string;
  action: ScamperAction;
  description: string;
  adopted: boolean;
  newContradictions?: ScamperNewContradiction[];
  createdAt?: string;
}

// Interface Contract — 6 Dimensions (E2E Spec)
// Single source of truth lives in `@/types/generated/subsystem`. Re-exported
// here for backwards compatibility with existing alternative-flow imports.
// Stage 1 of refactor/subsystem-interface-contracts: was 3 duplicate
// definitions, now 1.
export type { InterfaceContract } from '@/types/generated/subsystem';
export {
  INTERFACE_CONTRACT_DIMS,
  EMPTY_INTERFACE_CONTRACT,
} from '@/types/generated/subsystem';

// Alternative (concept route)
export type AlternativeSource = 'triz_tc' | 'triz_pc' | 'triz_sf' | 'scamper' | 'manual' | 'ai_integrated';

export interface Alternative {
  id: string;
  name: string;
  mechanism: string;
  source: AlternativeSource;
  keyAssumptionIds: string[];
  mustScores: Record<string, 'pass' | 'fail' | 'marginal' | null>; // M1-M6
  interfaceContract: InterfaceContract; // 6-dim interface contract (E2E H4)
  preCadScores: {
    must: number | null;
    decoupling: number | null;
    testability: number | null;
    failureMech: number | null;
    mvpCadEffort: number | null;
  };
  overallPass: boolean | null;
  validationPassport: ValidationPassport | null;
  createdAt?: string;
  updatedAt?: string;
}

/** Dynamic MUST criteria — derived from Brief constraints/KPIs per project. */
export interface MustCriterion {
  id: string;        // "M1", "M2", ...
  label: string;     // e.g. "效率 ≥ 95%"
  source: string;    // which constraint/KPI
  threshold?: string;
}

/**
 * Fallback MUST criteria for projects without must_criteria_config.
 * New projects should derive MUST from Brief constraints/KPIs.
 */
export const DEFAULT_MUST_CRITERIA: MustCriterion[] = [
  { id: 'M1', label: 'M1 空間', source: '通用' },
  { id: 'M2', label: 'M2 成本', source: '通用' },
  { id: 'M3', label: 'M3 安全餘裕', source: '通用' },
  { id: 'M4', label: 'M4 解耦', source: '通用' },
  { id: 'M5', label: 'M5 供應', source: '通用' },
  { id: 'M6', label: 'M6 製造路徑', source: '通用' },
];

/** @deprecated Use DEFAULT_MUST_CRITERIA for backward compat */
export const MUST_CRITERIA = DEFAULT_MUST_CRITERIA;

export const PRECAD_DIMENSIONS = [
  { key: 'must', label: 'MUST 硬限制', labels: ['不滿足', '', '勉強', '', '全數通過'] },
  { key: 'decoupling', label: '解耦程度', labels: ['高耦合', '', '適度', '', '完全解耦'] },
  { key: 'testability', label: '可驗證性', labels: ['無法驗證', '', '4週內', '', '1週內'] },
  { key: 'failureMech', label: '失效機制風險', labels: ['致命風險', '', '有緩解', '', '風險極低'] },
  { key: 'mvpCadEffort', label: 'MVP CAD 工作量', labels: ['極高', '', '中等', '', '極低'] },
] as const;

// Gate
export interface CreateGateItem {
  label: string;
  current: number;
  target: number;
  passed: boolean;
}
