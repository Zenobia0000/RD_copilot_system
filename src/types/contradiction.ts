export interface TrizParameter {
  id: number;
  name: string;
  nameZh: string;
}

export const CONTRADICTION_SEVERITIES = ['fatal', 'major', 'minor'] as const;
export type ContradictionSeverity = (typeof CONTRADICTION_SEVERITIES)[number];
export const DEFAULT_SEVERITY: ContradictionSeverity = 'minor';

export type ContradictionSourceType = 'socratic' | 'manual' | 'scamper_feedback' | 'convergence';

export interface Contradiction {
  id: string;
  projectId: string;
  naturalDescription: string;
  improvingParam: number | null;
  worseningParam: number | null;
  engineeringStatement: string;
  physicalContradiction: string;
  type: 'TC' | 'PC' | 'SF' | null;
  severity: ContradictionSeverity;
  resolved: boolean;
  sourceQuestionId: string | null;
  sourceType: ContradictionSourceType;
  // Su-Field fields (populated when type === 'SF')
  sfSubstance1: string | null;
  sfSubstance2: string | null;
  sfField: string | null;
  sfInteraction: string | null;  // useful / harmful / insufficient / missing
  sfCompleteness: string | null;  // complete / incomplete / harmful_complete
  // PC Decomposition fields (migration 009) — populated for child PCs under a parent TC
  parentContradictionId: string | null;
  derivedParameter: string | null;
  subsystemHint: string | null;
  separationPrincipleId: string | null;
  separationCategory: 'time' | 'space' | 'condition' | 'whole_part' | null;
  separationRationale: string | null;
  pcAttributeA: string | null;
  pcAttributeNotA: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ContradictionAssumptionLink {
  id: string;
  contradictionId: string;
  assumptionId: string;
  linkType: 'depends_on' | 'challenges' | 'derived_from';
  createdAt: string;
}

export type ContradictionFormData = Omit<Contradiction, 'id' | 'projectId' | 'createdAt' | 'updatedAt'>;
