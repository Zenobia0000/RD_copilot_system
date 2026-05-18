// Socratic Q&A types
export type QuestionCategory = 'clarification' | 'assumption' | 'consequence' | 'counter' | 'origin' | 'action' | 'reframing';

export interface SocraticQuestion {
  id: string;
  category: QuestionCategory;
  text: string;
  answer: string | null;
  taggedAsAssumption: boolean;
  aiSuggestedTag: 'assumption' | null; // AI auto-detected tag
  aiTagConfirmed: boolean; // user confirmed
  aiTagDismissed: boolean; // user dismissed the suggestion
  createdAt?: string;
  replacedAt?: string; // set when this question was replaced due to Brief change
}

export const CATEGORY_CONFIG: Record<QuestionCategory, { label: string; labelZh: string; color: string }> = {
  clarification: { label: 'Clarification', labelZh: '澄清', color: '#3B82F6' },
  assumption: { label: 'Assumption', labelZh: '假設', color: '#8B5CF6' },
  consequence: { label: 'Consequence', labelZh: '後果', color: '#EC4899' },
  counter: { label: 'Counter', labelZh: '對立', color: '#F59E0B' },
  origin: { label: 'Origin', labelZh: '本源', color: '#10B981' },
  action: { label: 'Action', labelZh: '行動', color: '#6366F1' },
  reframing: { label: 'Reframing', labelZh: '重構', color: '#EF4444' },
};

// Contradiction types (enhanced from existing)
export type ContradictionType = 'TC' | 'PC' | 'SF';
export type ContradictionStatus = 'draft' | 'confirmed' | 'rejected';

// Mirror of contradictions.severity — feeds TRIZ L2 trigger rule
// (`severity ∈ {fatal, major}` → auto-deepen; `minor` + quick_mode → skip).
// Keep in sync with ContradictionSeverity in types/contradiction.ts.
export type ExploreContradictionSeverity = 'fatal' | 'major' | 'minor';

export interface ExploreContradiction {
  id: string;
  projectId: string;
  type: ContradictionType;
  /** RD-annotated severity. Drives TRIZ L2 auto-trigger (fatal/major → deepen). */
  severity?: ExploreContradictionSeverity;
  improvingParam: number | null;
  worseningParam: number | null;
  pcAttributeA: string | null;
  pcAttributeNotA: string | null;
  // Su-Field fields (populated when type === 'SF')
  sfSubstance1: string | null;
  sfSubstance2: string | null;
  sfField: string | null;
  sfInteraction: string | null;  // useful / harmful / insufficient / missing
  sfCompleteness: string | null;  // complete / incomplete / harmful_complete
  description: string;
  engineeringStatement: string | null;
  status: ContradictionStatus;
  source: 'ai' | 'manual';
  createdAt: string;
  updatedAt: string;
  // Added by L2 WBS 4.4 (PC Decomposition — mirrors migration 009 columns)
  parentContradictionId?: string | null;
  derivedParameter?: string | null;
  subsystemHint?: string | null;
  separationPrincipleId?: string | null;
  separationCategory?: 'time' | 'space' | 'condition' | 'whole_part' | null;
  separationRationale?: string | null;
  // 3-Stage TC Pipeline fields
  linkedKpis?: string[];
  whySelected?: string | null;
  priority?: number | null;
}

// CLD types
export interface CausalNode {
  id: string;
  label: string;
  position: { x: number; y: number };
  isBreakpoint: boolean;
  breakpointReason: string | null;
  relatedContradictions: string[];
}

export interface CausalEdge {
  id: string;
  source: string;
  target: string;
  feedbackType: 'positive' | 'negative';
}

export interface CausalLoop {
  id: string;
  nodes: CausalNode[];
  edges: CausalEdge[];
}

// Gate check types
export interface GateCheckItem {
  label: string;
  current: number;
  target: number;
  passed: boolean;
}

export interface GateCheckResult {
  gateId: string;
  passed: boolean;
  checklist: GateCheckItem[];
}
