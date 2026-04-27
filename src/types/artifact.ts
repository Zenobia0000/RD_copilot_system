// ====================================================================
// E2E Artifact Lifecycle — 6 Core Artifacts + Unified State Machine
// Ref: docs/e2e/RD_Design_Copilot_整合流程.md
// ====================================================================

// --- Artifact State Machine ---
// Draft → Reviewed → Verified → Baselined → Released
export type ArtifactState = 'draft' | 'reviewed' | 'verified' | 'baselined' | 'released';

export const ARTIFACT_STATE_ORDER: ArtifactState[] = ['draft', 'reviewed', 'verified', 'baselined', 'released'];

export const ARTIFACT_STATE_CONFIG: Record<ArtifactState, { label: string; labelZh: string; color: string }> = {
  draft:     { label: 'Draft',     labelZh: '草稿',   color: '#6c757d' },
  reviewed:  { label: 'Reviewed',  labelZh: '已審閱', color: '#3B82F6' },
  verified:  { label: 'Verified',  labelZh: '已驗證', color: '#F59E0B' },
  baselined: { label: 'Baselined', labelZh: '已基線', color: '#8B5CF6' },
  released:  { label: 'Released',  labelZh: '已發行', color: '#10B981' },
};

/** Check if a state transition is valid (only forward transitions allowed) */
export function isValidTransition(from: ArtifactState, to: ArtifactState): boolean {
  const fromIdx = ARTIFACT_STATE_ORDER.indexOf(from);
  const toIdx = ARTIFACT_STATE_ORDER.indexOf(to);
  return toIdx === fromIdx + 1; // only allow single-step forward
}

// --- Artifact Type Registry ---
export type ArtifactType = 'constraint' | 'contradiction' | 'breakpoint' | 'concept_route' | 'evidence' | 'risk';

export const ARTIFACT_TYPE_CONFIG: Record<ArtifactType, { label: string; labelZh: string; prefix: string }> = {
  constraint:    { label: 'Constraint',    labelZh: '約束',     prefix: 'CON' },
  contradiction: { label: 'Contradiction', labelZh: '矛盾',     prefix: 'CTD' },
  breakpoint:    { label: 'Breakpoint',    labelZh: '切入點',   prefix: 'BKP' },
  concept_route: { label: 'Concept Route', labelZh: '概念路線', prefix: 'CRT' },
  evidence:      { label: 'Evidence',      labelZh: '證據',     prefix: 'EVD' },
  risk:          { label: 'Risk',          labelZh: '風險',     prefix: 'RSK' },
};

// --- Base Artifact Interface ---
export interface ArtifactMeta {
  artifactId: string;       // e.g. CON-001, CTD-003
  artifactType: ArtifactType;
  artifactState: ArtifactState;
  createdAt: string;
  updatedAt: string;
  stateHistory: ArtifactStateTransition[];
}

export interface ArtifactStateTransition {
  from: ArtifactState;
  to: ArtifactState;
  triggeredBy: string; // gate ID or user action
  timestamp: string;
}

// --- 6 Core Artifact Interfaces ---

/** 1. Constraint Artifact (D1 → Gate 1) */
export interface ConstraintArtifact extends ArtifactMeta {
  artifactType: 'constraint';
  code: string;           // M1, M2, etc.
  description: string;
  source: string;
  type: 'hard' | 'soft' | 'non_goal';
  feasibility: 'feasible' | 'boundary' | 'impossible' | null;
}

/** 2. Contradiction Artifact (D2–D4 → Gate 2-3) */
export interface ContradictionArtifact extends ArtifactMeta {
  artifactType: 'contradiction';
  type: 'TC' | 'PC' | 'SF';
  description: string;
  engineeringStatement: string;
  improvingParam: number | null;
  worseningParam: number | null;
  physicalContradiction: string | null;
  severity: 'fatal' | 'major' | 'minor';
  resolved: boolean;
}

/** 3. Breakpoint Artifact (D4 → Gate 3) */
export interface BreakpointArtifact extends ArtifactMeta {
  artifactType: 'breakpoint';
  nodeId: string;         // CLD node reference
  label: string;
  reason: string;
  interventionParams: string[];
  linkedContradictionIds: string[];
}

/** 4. Concept Route Artifact (X2 → Gate P) */
export interface ConceptRouteArtifact extends ArtifactMeta {
  artifactType: 'concept_route';
  name: string;
  mechanism: string;
  source: string;
  keyAssumptionIds: string[];
  mustScores: Record<string, 'pass' | 'fail' | 'marginal' | null>;
  interfaceContract: InterfaceContract;
  preCadScores: Record<string, number | null>;
  overallPass: boolean | null;
}

/** Interface Contract — 6 Dimensions (E2E Spec) */
export interface InterfaceContract {
  envelope: string;           // 包絡尺寸
  loadPath: string;           // 負載路徑
  signalPath: string;         // 信號路徑
  thermalPath: string;        // 熱路徑
  datumTolerance: string;     // 基準與公差
  serviceability: string;     // 維修通道
}

export const INTERFACE_CONTRACT_DIMENSIONS: { key: keyof InterfaceContract; label: string; labelZh: string }[] = [
  { key: 'envelope',       label: 'Envelope',         labelZh: '包絡尺寸' },
  { key: 'loadPath',       label: 'Load Path',        labelZh: '負載路徑' },
  { key: 'signalPath',     label: 'Signal Path',      labelZh: '信號路徑' },
  { key: 'thermalPath',    label: 'Thermal Path',     labelZh: '熱路徑' },
  { key: 'datumTolerance', label: 'Datum & Tolerance', labelZh: '基準與公差' },
  { key: 'serviceability', label: 'Serviceability',   labelZh: '維修通道' },
];

export const EMPTY_INTERFACE_CONTRACT: InterfaceContract = {
  envelope: '',
  loadPath: '',
  signalPath: '',
  thermalPath: '',
  datumTolerance: '',
  serviceability: '',
};

/** 5. Evidence Artifact (V1 → Gate C) */
export interface EvidenceArtifact extends ArtifactMeta {
  artifactType: 'evidence';
  linkedAssumptionId: string;
  evidenceLevel: 'E0' | 'E1' | 'E2' | 'E3' | 'E4';
  method: string;
  result: string;
  isNorthStar: boolean;     // North Star KPI evidence
}

/** 6. Risk Artifact (V1 → Gate C → Gate 7) */
export interface RiskArtifact extends ArtifactMeta {
  artifactType: 'risk';
  description: string;
  failureMode: string;
  probability: number;      // 1-5
  severity: number;         // 1-5
  riskLevel: 'L' | 'M' | 'H' | 'H*';
  mitigation: string;
  sourceContradictionId: string | null;
}

// --- Union type for all artifacts ---
export type CoreArtifact =
  | ConstraintArtifact
  | ContradictionArtifact
  | BreakpointArtifact
  | ConceptRouteArtifact
  | EvidenceArtifact
  | RiskArtifact;

// --- Gate-Artifact mapping: which gates transition which artifact types ---
export const GATE_ARTIFACT_TRANSITIONS: Record<string, { types: ArtifactType[]; to: ArtifactState }> = {
  'gate-1':   { types: ['constraint'],                         to: 'reviewed' },
  'gate-2':   { types: ['contradiction'],                      to: 'reviewed' },
  'gate-3':   { types: ['breakpoint', 'contradiction'],        to: 'verified' },
  'gate-4':   { types: ['constraint', 'contradiction'],        to: 'verified' },
  'gate-p':   { types: ['concept_route'],                      to: 'reviewed' },
  'gate-c':   { types: ['evidence', 'risk', 'concept_route'],  to: 'verified' },
  'gate-7':   { types: ['evidence', 'risk', 'concept_route'],  to: 'baselined' },
  'gate-8':   { types: ['constraint', 'contradiction', 'breakpoint', 'concept_route', 'evidence', 'risk'], to: 'released' },
};

// --- Adverse Consequences (KT Decision Step 7) ---
export interface AdverseConsequence {
  id: string;
  alternativeId: string;
  description: string;
  probability: 'high' | 'medium' | 'low';
  severity: 'high' | 'medium' | 'low';
  level: 'L' | 'M' | 'H' | 'H*';
  mitigation: string;
  riskArtifactId: string | null;
}

export function computeACLevel(prob: 'high' | 'medium' | 'low', sev: 'high' | 'medium' | 'low'): 'L' | 'M' | 'H' | 'H*' {
  const pMap = { high: 5, medium: 3, low: 1 };
  const sMap = { high: 5, medium: 3, low: 1 };
  const score = pMap[prob] * sMap[sev];
  if (score >= 20) return 'H*';
  if (score >= 15) return 'H';
  if (score >= 8) return 'M';
  return 'L';
}
