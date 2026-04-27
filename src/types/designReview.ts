import type { ExperimentStatus, RiskLevel } from './shared';
export type { ExperimentStatus, RiskLevel } from './shared';

// Evidence levels E0-E4
export type EvidenceLevel = 'E0' | 'E1' | 'E2' | 'E3' | 'E4';

export const EVIDENCE_LEVELS: { value: EvidenceLevel; label: string; color: string }[] = [
  { value: 'E0', label: '無證據', color: '#dc3545' },
  { value: 'E1', label: '工程估算', color: '#fd7e14' },
  { value: 'E2', label: '仿真', color: '#ffc107' },
  { value: 'E3', label: '原型', color: '#90EE90' },
  { value: 'E4', label: '量產驗證', color: '#28a745' },
];

// Evidence Matrix row (per assumption)
export interface EvidenceMatrixRow {
  assumptionCode: string;
  summary: string;
  currentLevel: EvidenceLevel;
  isNorthStar: boolean; // North Star KPI evidence — Gate C requires >= E2 (WBS H7)
  experiments: { expCode: string; level: EvidenceLevel; status: ExperimentStatus }[];
}

// Risk Register
export interface RiskItem {
  id: string;
  description: string;
  failureMode: string;
  probability: number; // 1-5
  severity: number;    // 1-5
  mitigation: string;
}

export function getRiskScore(r: RiskItem): number {
  return r.probability * r.severity;
}

export function getRiskLevel(score: number): RiskLevel {
  if (score >= 20) return 'H*';
  if (score >= 15) return 'H';
  if (score >= 8) return 'M';
  return 'L';
}

export function getRiskColor(level: RiskLevel): string {
  if (level === 'H*') return '#8B0000';
  if (level === 'H') return '#dc3545';
  if (level === 'M') return '#fd7e14';
  return '#28a745';
}

// Experiment (DesignReview-specific shape — richer than track.Experiment)

export interface Experiment {
  id: string;
  name: string;
  linkedAssumptions: string[]; // assumption codes
  evidenceLevel: EvidenceLevel;
  method: string;
  successCriteria: string;
  status: ExperimentStatus;
  result: string;
}

export const EXP_STATUS_COLOR: Record<ExperimentStatus, string> = {
  Plan: '#3B82F6',
  Running: '#F59E0B',
  Done: '#10B981',
};

// Gate V1
export interface Gate31Item {
  label: string;
  passed: boolean;
}
