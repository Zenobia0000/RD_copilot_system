import type { EvidenceLevel } from './designReview';

export interface EvidenceEntry {
  id: string;
  projectId: string;
  userId: string;
  title: string;
  measuredValue: string;
  unit: string;
  evidenceLevel: EvidenceLevel;
  method: string;
  notes: string;
  measuredAt: string;
  kpiId: string | null;
  experimentId: string | null;
  linkedAssumptionCodes: string[];
  linkedMustIds: string[];
  attachmentId: string | null;
  createdAt: string;
  updatedAt: string;
}

export type KpiStatus = 'on_track' | 'at_risk' | 'off_track' | 'unknown';
