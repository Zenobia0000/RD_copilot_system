/**
 * Directed TRIZ types — direction-centric flow (v8).
 *
 * Mirrors backend schemas:
 *   DirectionSolution, DirectionGroup, DirectionScore,
 *   ContradictionDirectionResult, ConsolidationResult, etc.
 */

// --- Single solution from TC / PC / SF ---

export interface DirectionSolution {
  path: 'TC' | 'PC' | 'SF';
  principle_number: number | null;
  principle_name: string;
  suggestion: string;
  separation_principle: string;
  affected_modules: string[];
  secondary_contradictions: string[];
}

// --- A cluster of solutions pointing to the same implementation direction ---

export interface DirectionGroup {
  direction_id: string;       // e.g. "DIR-1"
  direction_name: string;     // e.g. "折疊/可變形"
  direction_summary: string;
  solutions: DirectionSolution[];
  tc_count: number;
  pc_count: number;
  sf_count: number;
}

// --- Direction scoring ---

export interface DirectionScore {
  direction_id: string;
  tool_support: number;       // TC + PC + SF vote count
  feasibility: number;        // 0~10
  cost_difficulty: number;    // 0~10
  coverage_score: number;     // 0~10 (Step H coverage audit)
  weighted_total: number;
  score_rationale: string;
}

// --- Brief context snapshot (Step H input, context-aware audit) ---
// Mirrors backend BriefContextSnapshot. All fields optional / default
// empty so partial project data does not break the FE.

export interface BriefConstraint {
  code: string;
  description: string;
  type: string;            // "hard" | "soft"
  feasibility: string;
}

export interface BriefKpi {
  name: string;
  target_value: string;
  unit: string;
  current_value: string;
  current_status: string;  // on_track / at_risk / off_track / unknown
}

export interface SocraticInsight {
  category: string;
  question: string;
  answer: string;
  is_assumption: boolean;
}

export interface CldNodeSummary {
  label: string;
  node_type: string;
  is_leverage: boolean;
}

export interface CldEdgeSummary {
  from_label: string;
  to_label: string;
  polarity: string;        // "+" | "-"
}

export interface CldSummary {
  nodes: CldNodeSummary[];
  edges: CldEdgeSummary[];
  leverage_points: string[];
}

export interface BriefContextSnapshot {
  project_id: string;
  mission: string;
  constraints: BriefConstraint[];
  kpis: BriefKpi[];
  socratic_summary: SocraticInsight[];
  cld_summary: CldSummary;
}

// --- Sub-requirement decomposition (Step H-1, context-aware) ---

// kind = which side of the user's Step-1 contradiction split this SR
// represents. `mission_outcome` is the extra slot for KPI-level goals
// not literally inside the contradiction text.
export type SubRequirementKind =
  | 'desired_improvement'
  | 'undesired_effect'
  | 'boundary_condition'
  | 'mission_outcome';

export interface SubRequirement {
  id: string;
  description: string;
  // priority is kept for back-compat with rows persisted by the
  // pre-context audit; new rows use `kind` instead.
  priority?: 'must' | 'should' | 'nice';
  rationale?: string;
  // v2 (context-aware) additions
  kind?: SubRequirementKind;
  source_ref?: string;     // "mission" | "constraint:C1" | "kpi:K2" | ...
  domain?: string;         // legacy field, kept for back-compat
  why_necessary?: string;  // legacy field, kept for back-compat
}

// --- Coverage audit (Step H-2, context-aware) ---

// 5-state resolution verdict — see architect plan §三.
export type ResolutionStatus =
  | 'directly_resolves'
  | 'partially_resolves'
  | 'conditionally_resolves'
  | 'does_not_resolve'
  | 'unclear';

// Causal layer the direction touches.
export type AddressesLayer = 'root_cause' | 'mechanism' | 'symptom' | 'unclear';

// Per-SR verdict — drives the SR-grouped UI. Backend derives this when
// the LLM omits it (see _parse_coverage_matrix in triz_solver.py).
export type PerSrVerdict =
  | 'directly_solves'
  | 'partially_solves'
  | 'needs_verify'
  | 'violates'
  | 'not_addressed'
  | 'unclear';

export interface CoverageEntry {
  // Legacy shape used `sub_req_id`/`covered`/`note`; backend now emits
  // `sub_requirement_id`/`score`/`rationale`. Both forms are accepted
  // here so old persisted rows still render.
  sub_req_id?: string;
  sub_requirement_id?: string;
  covered?: boolean;
  score?: number;          // 0 / 1 / 2
  note?: string;
  rationale?: string;
  // v3 additions for SR-grouped UI
  verdict?: PerSrVerdict;
  verdict_zh?: string;
}

export interface DirectionCoverageAudit {
  direction_id: string;
  entries?: CoverageEntry[];        // legacy alias
  coverage_matrix?: CoverageEntry[];
  coverage_score: number;
  gap_summary: string;
  // v2 (context-aware) additions — all optional so legacy rows still parse.
  resolution_status?: ResolutionStatus;
  key_assumptions?: string[];
  mission_violations?: string[];
  cld_side_effects?: string[];
  addresses_layer?: AddressesLayer;
  unresolved_gaps?: string[];       // backend may emit this instead of gap_summary
}

// --- Combined direction (Step I) ---

export interface CombinedDirection {
  direction_ids: string[];
  combined_summary: string;
  combined_score: number;
  rationale: string;
  remaining_gaps: string[];
}

// --- Full result for ONE contradiction ---

export interface ContradictionDirectionResult {
  contradiction_id: string;
  natural_description: string;
  severity: 'fatal' | 'major' | 'minor' | 'unknown';
  all_solutions: DirectionSolution[];
  all_directions: DirectionGroup[];
  scored_directions: DirectionScore[];
  top1: DirectionGroup | null;
  top2: DirectionGroup | null;
  top1_score: DirectionScore | null;
  top2_score: DirectionScore | null;
  sub_requirements?: SubRequirement[];
  coverage_audits?: DirectionCoverageAudit[];
  combined_direction?: CombinedDirection | null;
}

// --- Cross-contradiction consolidation ---

// ---- Conflict type enum (matches backend ConflictType literal) ----
export type ConflictType =
  | 'physical_state'
  | 'intervention_clash'
  | 'module_overlap'
  | 'secondary_loop'
  | 'none';

// ---- Structured conflict-resolution suggestion types ----
export type ConflictSuggestionType =
  | 'relax_constraint'
  | 'hybrid'
  | 'rd_manual_choice'
  | 'architectural_reset';

export type ConflictSuggestionCost = 'low' | 'medium' | 'high';

export interface ConflictSuggestion {
  type: ConflictSuggestionType;
  target_contradictions: string[];
  description: string;
  cost: ConflictSuggestionCost;
}

// ---- Updated interfaces ----
export interface CompatibilityResult {
  direction_a: string;
  direction_b: string;
  contradiction_a_id: string;
  contradiction_b_id: string;
  compatible: boolean;
  reason: string;
  conflict_type: ConflictType;        // 新增
}

export interface ConflictReport {
  conflicting_pairs: CompatibilityResult[];
  suggestions: ConflictSuggestion[];   // 從 string[] 升級
}

export type ConsolidationStatus = 'compatible' | 'resolved_with_swap' | 'conflict';

export interface ConsolidationResult {
  status: ConsolidationStatus;
  adopted_directions: Record<string, DirectionGroup>;  // contradiction_id → direction
  conflict_report: ConflictReport | null;
  integration_advice: string;
}

// --- API request / response ---

export interface SolveDirectedRequest {
  project_id: string;
  contradiction_id: string;
  natural_description: string;
  severity?: 'fatal' | 'major' | 'minor' | 'unknown';
  improving_param?: number;
  worsening_param?: number;
  /**
   * Optional override for context-aware coverage audit. When omitted,
   * the backend lazily builds the snapshot from Supabase using
   * `project_id`. Production UI normally leaves this `undefined`;
   * harness / test code may pass a synthetic snapshot directly.
   */
  brief_context?: BriefContextSnapshot;
}

export interface SolveDirectedResponse {
  result: ContradictionDirectionResult;
}

export interface ConsolidateRequest {
  project_id: string;
  results: ContradictionDirectionResult[];
}

export interface ConsolidateResponse {
  consolidation: ConsolidationResult;
}
