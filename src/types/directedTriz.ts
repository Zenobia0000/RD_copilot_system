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
