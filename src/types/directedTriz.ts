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

// --- Phase 1 (S0c) — SR weak warnings (score=1 候選) ---

export interface SrWeakWarning {
  candidate_id: number;
  kind: SubRequirement['kind'];
  source_ref: string;
  raw_text: string;
  relevance_score: number;
  why_weak: string;
}

// --- Phase 2 — DecisionCard per direction (給 RD 選購用) ---

export type ContradictionFace = 'improving_side' | 'worsening_side' | 'both' | 'side_effect';
export type EffortLevel = 'low' | 'medium' | 'high';
export type EvidenceLevel = 'E0' | 'E1' | 'E2' | 'E3' | 'E4';

export interface DecisionCardQuickTags {
  effort: EffortLevel;
  evidence_level: EvidenceLevel;
  affects_modules: string[];
}

export interface DecisionCardCombinationHints {
  synergy_with: string[];
  conflict_with: string[];
  best_paired_with: string[];
}

export interface DecisionCard {
  direction_id: string;
  direction_name: string;
  one_liner: string;
  contradiction_face: ContradictionFace;
  face_badge: string;
  resolution_status: ResolutionStatus;
  resolution_one_line: string;
  quick_tags: DecisionCardQuickTags;
  combination_hints: DecisionCardCombinationHints;
  picked: boolean;
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
  sr_weak_warnings?: SrWeakWarning[];     // Phase 1 S0c
  coverage_audits?: DirectionCoverageAudit[];
  combined_direction?: CombinedDirection | null;
  decision_cards?: DecisionCard[];        // Phase 2
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
  adopted_directions: Record<string, DirectionGroup>;  // contradiction_id → direction (代表方向)
  conflict_report: ConflictReport | null;
  integration_advice: string;
  /**
   * Phase 3 bugfix：contradiction_id → direction_id，由 RD 「直接勾選」的方向。
   * 與 status=resolved_with_swap 的「系統把 Top1 swap 成 Top2」**互斥**：
   *  - 若 cid 在 was_user_picked 內，UI 應顯示「使用您勾選的方向」徽章。
   *  - 否則若採用方向不是 Top1，才是「Top2 替換」。
   * 為了向後相容，rows 沒這欄位時視為 {} (前端必須處理 undefined)。
   */
  was_user_picked?: Record<string, string>;
  /**
   * Phase 3：整併方案的 Q1–Q8 工程審判卡。Backend 失敗時為 null；
   * 舊資料 row 沒此欄位時為 undefined。
   */
  verdict_card?: EngineeringVerdictCard | null;
  /**
   * Phase 3：同矛盾多選相容性報告（依 contradiction_id 索引）。
   * 為了向後相容，rows 沒此欄位時為 undefined。
   */
  intra_compatibility?: IntraContradictionCompatibility[];
  /**
   * PR2-Lite：contradiction_id → 完整候選池（依分數降冪）。
   * adopted_directions[cid] 是代表方向（首選），candidate_pools[cid] 是含 fallback 的整池。
   * 前端 ConsolidationPanel 可摺疊顯示「其他候選方向」。
   * 舊資料 row 沒此欄位時為 undefined。
   */
  candidate_pools?: Record<string, DirectionGroup[]>;
  /**
   * PR2-Lite：演算法卡住、池已用盡的 contradiction_id list。
   * 僅在 status='conflict' 才有值；前端 conflict UI「卡點分析」區用此標出哪些
   * 矛盾無法再 swap，建議使用者於該矛盾加勾其他方向。
   */
  exhausted_contradictions?: string[];
  /**
   * PR2-Lite：演算法執行的輪次數（含初始 LLM check）。
   * 0 = 沒跑演算法（單矛盾 fallback）；用於 UI 文案「AI 嘗試 N 種組合」。
   */
  total_rounds?: number;
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

// ---------------------------------------------------------------------------
// Phase 3 — Picked selections + intra-contradiction compatibility
// ---------------------------------------------------------------------------

export interface PickedSelection {
  contradiction_id: string;
  picked_direction_ids: string[];   // ≤6 (backend 422 if exceeded)
}

export interface IntraContradictionCompatibility {
  contradiction_id: string;
  picked_direction_ids: string[];
  pairwise_results: CompatibilityResult[];
  max_compatible_subsets: string[][];   // 排序：最大優先
  has_conflict: boolean;
  recommendation: string;
}

// ---------------------------------------------------------------------------
// Phase 3 — EngineeringVerdictCard Q1–Q8
// ---------------------------------------------------------------------------

export interface ContradictionFacePerPicked {
  contradiction_id: string;
  picked_direction_id: string;
  picked_direction_name: string;
  improving_side: 'yes' | 'partial' | 'no';
  worsening_side: 'yes' | 'partial' | 'no';
  introduces_new_side_effect: string[];
}

export interface MechanismTrace {
  technology_mix: Array<'control' | 'structure' | 'material' | 'topology'>;
  delta_chain: string[];
  assumptions: string[];
  evidence_level: 'E0' | 'E1' | 'E2' | 'E3' | 'E4';
}

export interface FeasibilityVerdict {
  axis: string;
  source_ref: string;
  verdict:
    | 'pass'
    | 'marginal_pass'
    | 'bottleneck'
    | 'not_addressed'
    | 'not_affected'
    | 'fail';
  rationale: string;
  quantitative_estimate: string;
}

export interface FeasibilityMatrix {
  axes: FeasibilityVerdict[];
  overall_verdict: 'pass' | 'marginal' | 'fail';
  bottleneck_axes: string[];
}

export interface CldSideEffect {
  cld_path: string[];
  polarity_chain: Array<'positive' | 'negative'>;
  direction_impact: string;
  risk_level: 'low' | 'medium' | 'high';
}

export interface SideEffectsViaCld {
  paths: CldSideEffect[];
  socratic_warnings: string[];
}

export interface CoverageCompleteness {
  resolves_fully: string[];
  resolves_partial: string[];
  resolves_conditional: string[];
  does_not_address: string[];
  open_questions: string[];
}

export interface VerificationStep {
  phase:
    | 'simulation'
    | 'bench'
    | 'thermal_soak'
    | 'prototype'
    | 'pilot'
    | 'field';
  test_description: string;
  expected_outcome: string;
  effort_hours: number;
  blocking: boolean;
}

export interface VerificationPlan {
  steps: VerificationStep[];
  socratic_action_links: string[];
}

export interface DutyCycleVerdict {
  peak: 'addressed' | 'marginal' | 'not_addressed';
  continuous: 'addressed' | 'marginal' | 'not_addressed';
  startup: 'addressed' | 'marginal' | 'not_addressed';
  steady_state: 'addressed' | 'marginal' | 'not_addressed';
  cycle_specific_notes: string;
}

export interface BoundaryCollapse {
  condition: string;
  failure_mode: string;
  severity: 'mild' | 'moderate' | 'catastrophic';
}

export interface EngineeringVerdictCard {
  project_id: string;
  consolidation_id: string;
  contradiction_face_per_picked: ContradictionFacePerPicked[];
  mechanism_trace: MechanismTrace;
  feasibility_matrix: FeasibilityMatrix;
  side_effects_via_cld: SideEffectsViaCld;
  coverage_completeness: CoverageCompleteness;
  verification_plan: VerificationPlan;
  duty_cycle_verdict: DutyCycleVerdict;
  boundary_collapse: BoundaryCollapse[];
  final_verdict: 'adopt' | 'adopt_with_conditions' | 'needs_revision' | 'reject';
  final_rationale: string;
  confidence: number;
}

export interface ConsolidateRequest {
  project_id: string;
  results: ContradictionDirectionResult[];
  /** Phase 3：若提供，後端會尊重每條矛盾的勾選方向並對同矛盾多選做相容性檢查 */
  picks?: PickedSelection[];
}

/**
 * 2026-05 hardening：後端寫 DB 結果的回報。
 *  - "ok"      → 完整 payload (含 verdict_card / was_user_picked / ...) 寫成功
 *  - "partial" → 偵測到 migration 未套用，退回 legacy schema；重整後會丟 Phase 3 資料
 *  - "failed"  → 寫入完全失敗；FE 應顯示錯誤、勿把回傳寫進 React Query cache
 */
export interface PersistenceOutcome {
  status: 'ok' | 'partial' | 'failed';
  reason?: string | null;
  columns_written: string[];
}

export interface ConsolidateResponse {
  consolidation: ConsolidationResult;
  /** Phase 3：同矛盾多選相容性報告 (與 request.picks 同順序) */
  intra_compatibility?: IntraContradictionCompatibility[];
  /** Phase 3：整併方案的 Q1–Q8 工程審判卡，LLM 失敗時為 null */
  verdict_card?: EngineeringVerdictCard | null;
  /**
   * 2026-05 hardening：DB persist 狀態。後端保證一定回傳；
   * 舊版後端的 response 沒此欄位時前端視為 status='ok' 兼容（見 handleConsolidateOnly）。
   */
  persistence?: PersistenceOutcome;
}
