/**
 * API client for communicating with the FastAPI backend.
 *
 * All AI-powered features (TRIZ, Socratic, CLD, Anti-Anchor, Risk, etc.)
 * go through this client instead of using mock data + setTimeout.
 */

import type { ZodType } from "zod";
import type { InterfaceContractMap } from "@/types/generated/subsystem";
import type {
  SolveTrizLayeredRequest,
  SolveTrizLayeredResponse,
} from "@/types/layeredTriz";

const API_PREFIX = "/api/v1";
const ENV_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();

function normalizeApiBaseUrl(rawBaseUrl?: string): string {
  if (!rawBaseUrl) return API_PREFIX;
  const baseUrl = rawBaseUrl.replace(/\/+$/, "");
  if (/\/api\/v1$/i.test(baseUrl)) return baseUrl;
  return `${baseUrl}${API_PREFIX}`;
}

// In dev, prefer Vite same-origin proxy to avoid "localhost" resolving to the user's browser machine.
const BASE_URL = import.meta.env.DEV ? API_PREFIX : normalizeApiBaseUrl(ENV_BASE_URL);
const REQUEST_TIMEOUT_MS = 90000;

// ─── Evidence Reference (shared across AI responses) ────────────────────────

export interface EvidenceReference {
  ref_id: string;
  ref_type: "web_search" | "uploaded_doc" | "engineering_reasoning";
  title: string;
  source: string;
  url?: string;
  snippet?: string;
}

class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super(`API error ${status}: ${typeof body === "string" ? body : JSON.stringify(body)}`);
    this.status = status;
    this.body = body;
  }
}

class ApiNetworkError extends Error {
  kind: "network" | "timeout";

  constructor(kind: "network" | "timeout", message: string) {
    super(message);
    this.kind = kind;
  }
}

const DEV_BYPASS = import.meta.env.VITE_DEV_BYPASS_AUTH === "true";

async function getAuthToken(): Promise<string | null> {
  if (DEV_BYPASS) return "dev-bypass-token";
  const { supabase } = await import("@/integrations/supabase/client");
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit, timeoutMs = REQUEST_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiNetworkError("timeout", `Request timeout after ${timeoutMs}ms`);
    }
    if (err instanceof TypeError) {
      throw new ApiNetworkError("network", err.message);
    }
    throw err;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

// ─── Runtime response validation ─────────────────────────────────────────────

interface RequestOptions<T> {
  /** Optional Zod schema — when provided, response is parsed & validated. */
  schema?: ZodType<T>;
  /** Override default timeout (ms). Use for long-running AI calls. */
  timeoutMs?: number;
}

const IS_DEV = import.meta.env.DEV;

/**
 * Safely parse a Response body as JSON.
 * Falls back to a descriptive ApiError when the body is not valid JSON.
 */
async function safeParseJson(res: Response, path: string): Promise<unknown> {
  const text = await res.text();
  if (!text) {
    // Empty 2xx body — return null so callers can handle
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new ApiError(
      res.status,
      `Expected JSON from ${path} but received non-JSON body: ${text.slice(0, 200)}`,
    );
  }
}

/**
 * Dev-only sanity check: warn when the parsed value doesn't look like a plain
 * object (the shape returned by 100 % of our backend endpoints).
 */
function devAssertObject(value: unknown, path: string): void {
  if (!IS_DEV) return;
  if (value === null || value === undefined) {
    console.warn(`[api] ${path}: response body is ${String(value)}`);
    return;
  }
  if (typeof value !== "object" || Array.isArray(value)) {
    console.warn(
      `[api] ${path}: expected plain object, got ${Array.isArray(value) ? "array" : typeof value}`,
    );
  }
}

/**
 * If a Zod schema was supplied, validate the response and return the parsed
 * (and potentially transformed) value.  On failure, log a dev warning and
 * return the raw data so the app keeps working.
 */
function validateWithSchema<T>(data: unknown, schema: ZodType<T> | undefined, path: string): T {
  if (!schema) return data as T;
  const result = schema.safeParse(data);
  if (result.success) return result.data;
  if (IS_DEV) {
    console.warn(`[api] ${path}: Zod validation failed`, result.error.format());
  }
  // Graceful degradation: return raw data so the UI isn't blocked.
  return data as T;
}

async function request<T>(path: string, body: unknown, opts?: RequestOptions<T>): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = await getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  }, opts?.timeoutMs);
  if (!res.ok) {
    // Try JSON first (FastAPI error detail), fall back to raw text.
    const errorBody = await safeParseJsonError(res);
    throw new ApiError(res.status, errorBody);
  }
  const data = await safeParseJson(res, path);
  devAssertObject(data, path);
  return validateWithSchema(data, opts?.schema, path);
}

/**
 * Extract error payload from a non-ok response.
 * FastAPI returns `{ "detail": "..." }` for most errors — surface that string
 * when available so ApiError messages are human-readable.
 */
async function safeParseJsonError(res: Response): Promise<unknown> {
  const text = await res.text().catch(() => "unknown error");
  try {
    const json = JSON.parse(text);
    // FastAPI convention: { detail: string | object }
    if (json && typeof json === "object" && "detail" in json) {
      return json.detail;
    }
    return json;
  } catch {
    return text;
  }
}

// ─── Brief ──────────────────────────────────────────────────────────────────

export interface BriefExtractRequest {
  project_id: string;
  raw_text: string;
  file_urls?: string[];
}

export interface ExtractedConstraint {
  code: string;
  description: string;
  source: string;
  type: string;
  feasibility: string;
}

export interface ExtractedKpi {
  name: string;
  target_value: string;
  unit: string;
  measurement_method: string;
}

export interface BriefExtractResponse {
  constraints: ExtractedConstraint[];
  kpis: ExtractedKpi[];
  assumptions: string[];
  feasibility_warnings: string[];
}

export function briefExtract(body: BriefExtractRequest) {
  return request<BriefExtractResponse>("/definitions/extract", body);
}

// ─── Brief Rewrite ──────────────────────────────────────────────────────────

export interface BriefRewriteRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  kpis?: string[];
}

export interface BriefRewriteResponse {
  rewritten_mission: string;
  changes_summary: string;
  evidence_references?: EvidenceReference[];
}

export function briefRewrite(body: BriefRewriteRequest) {
  return request<BriefRewriteResponse>("/definitions/rewrite", body);
}

// ─── Constraint Feasibility Check ────────────────────────────────────────────

export interface ConstraintFeasibilityRequest {
  project_id: string;
  mission: string;
  constraints: string[];
}

export interface FeasibilityConflictResult {
  constraintA: string;
  constraintB: string;
  reason: string;
  suggestion: string;
}

export interface ConstraintFeasibilityResponse {
  status: "pass" | "warning" | "conflict";
  conflicts: FeasibilityConflictResult[];
}

export function constraintFeasibilityCheck(body: ConstraintFeasibilityRequest) {
  return request<ConstraintFeasibilityResponse>("/definitions/check-feasibility", body);
}

// ─── Constraint Suggestions ─────────────────────────────────────────────────

export interface ConstraintSuggestRequest {
  project_id: string;
  mission: string;
  existing_constraints?: string[];
}

export interface SuggestedConstraint {
  description: string;
  source: string;
  rationale: string;
  ref_ids?: string[];
}

export interface ConstraintSuggestResponse {
  suggestions: SuggestedConstraint[];
  evidence_references?: EvidenceReference[];
}

export function constraintSuggest(body: ConstraintSuggestRequest) {
  return request<ConstraintSuggestResponse>("/definitions/suggest-constraints", body);
}

// ─── KPI Suggestions ────────────────────────────────────────────────────────

export interface KpiSuggestRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  existing_kpis?: string[];
}

export interface SuggestedKpi {
  kpi_name: string;
  target_value: string;
  unit: string;
  measurement_method: string;
  rationale: string;
  ref_ids?: string[];
}

export interface KpiSuggestResponse {
  suggestions: SuggestedKpi[];
  evidence_references?: EvidenceReference[];
}

export function kpiSuggest(body: KpiSuggestRequest) {
  return request<KpiSuggestResponse>("/definitions/suggest-kpis", body);
}

// ─── 5W1H Task Definition ──────────────────────────────────────────────────

export interface TaskDef5W1HRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  kpis?: string[];
}

export interface TaskDef5W1HResponse {
  who: string;
  what: string;
  where: string;
  when: string;
  why: string;
  how: string;
  evidence_references?: EvidenceReference[];
}

export function briefGenerate5W1H(body: TaskDef5W1HRequest) {
  return request<TaskDef5W1HResponse>("/definitions/generate-5w1h", body);
}

// ─── Socratic ───────────────────────────────────────────────────────────────

export interface SocraticGenerateRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  existing_questions?: string[];
}

export interface SocraticQuestionResult {
  category: string;
  text: string;
  suggested_tag: string | null;
}

export interface SocraticGenerateResponse {
  questions: SocraticQuestionResult[];
}

export function socraticGenerate(body: SocraticGenerateRequest) {
  return request<SocraticGenerateResponse>("/questions/generate", body);
}

// ─── Socratic Follow-up & Brief Impact ─────────────────────────────────────

export interface SocraticFollowUpRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  answered_questions: { id?: string; category: string; question: string; answer: string }[];
}

export interface FollowUpItem {
  category: string;
  text: string;
  reason: string;
}

export interface SocraticFollowUpResponse {
  follow_ups: FollowUpItem[];
  depth_sufficient: boolean;
}

export function socraticFollowUp(body: SocraticFollowUpRequest) {
  return request<SocraticFollowUpResponse>("/questions/follow-up", body);
}

export interface SocraticBriefImpactRequest {
  project_id: string;
  new_mission: string;
  new_constraints?: string[];
  existing_questions: { id: string; category: string; text: string; answer?: string }[];
}

export interface AffectedQuestionItem {
  id: string;
  reason: string;
  replacement: { category: string; text: string; suggested_tag?: string | null };
}

export interface SocraticBriefImpactResponse {
  affected: AffectedQuestionItem[];
  unaffected_ids: string[];
}

export function socraticBriefImpact(body: SocraticBriefImpactRequest) {
  return request<SocraticBriefImpactResponse>("/questions/brief-impact", body);
}

// ─── Socratic Auto-Tag ──────────────────────────────────────────────────────

export interface UntaggedQuestionItem {
  id: string;
  category: string;
  text: string;
  answer: string;
}

export interface SocraticAutoTagRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  existing_assumptions?: string[];
  existing_contradictions?: string[];
  untagged_questions: UntaggedQuestionItem[];
}

export interface AutoTagSuggestionResult {
  question_id: string;
  suggested_tag: string;
  reason: string;
}

export interface SocraticAutoTagResponse {
  suggestions: AutoTagSuggestionResult[];
}

export function socraticAutoTag(body: SocraticAutoTagRequest) {
  return request<SocraticAutoTagResponse>("/questions/auto-tag", body);
}

// ─── CLD ────────────────────────────────────────────────────────────────────

export interface CldGenerateRequest {
  project_id: string;
  contradictions: string[];
  assumptions: string[];
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  socraticAnswers?: string[];
}

export interface CldNode {
  id: string;
  label: string;
  type: string;
}

export interface CldEdge {
  from_node: string;
  to_node: string;
  polarity: string;
  source_id: string;
}

export interface CldLoop {
  id: string;
  type: string;
  node_ids: string[];
}

export interface CldBreakpoint {
  node_id: string;
  rationale: string;
}

export interface CldGenerateResponse {
  nodes: CldNode[];
  edges: CldEdge[];
  loops: CldLoop[];
  breakpoints: CldBreakpoint[];
}

export function cldGenerate(body: CldGenerateRequest) {
  return request<CldGenerateResponse>("/causal-loops/generate", body);
}

// ─── Anti-Anchor ────────────────────────────────────────────────────────────

export interface AntiAnchorGenerateRequest {
  project_id: string;
  mission: string;
  current_constraints: string[];
  existing_alternatives?: string[];
  socraticAnswers?: string[];
}

export interface AntiAnchorRouteResult {
  name: string;
  mechanism: string;
  description: string;
  is_non_typical: boolean;
  rationale: string;
  why_unconventional: string;
  potential_advantage: string;
  cross_domain_source: string;
  validation_passport: Record<string, unknown> | null;
}

export interface AntiAnchorGenerateResponse {
  routes: AntiAnchorRouteResult[];
}

export function antiAnchorGenerate(body: AntiAnchorGenerateRequest) {
  return request<AntiAnchorGenerateResponse>("/alternatives/anti-anchor", body, { timeoutMs: 300_000 });
}

// ─── TRIZ ───────────────────────────────────────────────────────────────────

export interface TrizSolveRequest {
  project_id: string;
  contradiction_id: string;
  natural_description: string;
  improving_param?: number | null;
  worsening_param?: number | null;
  physical_contradiction?: string | null;
  // Su-Field fields (used when type === "SF")
  sf_substance_1?: string | null;
  sf_substance_2?: string | null;
  sf_field?: string | null;
  type?: "TC" | "PC" | "SF";
  // Hint fields for child PC solve (Phase 9.1 / 9.2)
  separation_principle_id?: string | null;
  separation_category?: string | null;
  separation_rationale?: string | null;
  derived_parameter?: string | null;
}

export interface TrizSuggestionResult {
  path: string;
  principle_number: number | null;
  principle_name: string;
  suggestion: string;
  affected_modules: string[];
  secondary_contradictions: string[];
}

export interface TrizSolveResponse {
  mapped_improving: number | null;
  mapped_worsening: number | null;
  candidate_principles: number[];
  suggestions: TrizSuggestionResult[];
}

export function trizSolve(body: TrizSolveRequest) {
  return request<TrizSolveResponse>("/triz/solve", body, { timeoutMs: 300_000 });
}

// ─── TRIZ Layered Drill-Down (v7) ───────────────────────────────────────────
// POST /triz/solve-layered returns a LayeredTrizSolution — see
//   docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §5 and
//   src/types/layeredTriz.ts
//
// The legacy /triz/solve above is kept as the primitive API; use this newer
// endpoint whenever the `triz_layered_mode` feature flag is enabled.

export function trizSolveLayered(body: SolveTrizLayeredRequest) {
  return request<SolveTrizLayeredResponse>("/triz/solve-layered", body, {
    timeoutMs: 480_000,
  });
}

// ─── TRIZ Directed (v8) — Direction-centric flow ────────────────────────────
// POST /triz/solve-directed  — single contradiction direction solver
// POST /triz/consolidate     — cross-contradiction consolidation

import type {
  SolveDirectedRequest,
  SolveDirectedResponse,
  ConsolidateRequest,
  ConsolidateResponse,
} from "@/types/directedTriz";

export type { SolveDirectedRequest, SolveDirectedResponse, ConsolidateRequest, ConsolidateResponse };
export type {
  ContradictionDirectionResult,
  DirectionGroup,
  DirectionScore,
  DirectionSolution,
  ConsolidationResult,
  ConflictReport,
  CompatibilityResult,
} from "@/types/directedTriz";

export function trizSolveDirected(body: SolveDirectedRequest) {
  return request<SolveDirectedResponse>("/triz/solve-directed", body, {
    timeoutMs: 480_000,
  });
}

export function trizConsolidate(body: ConsolidateRequest) {
  return request<ConsolidateResponse>("/triz/consolidate", body, {
    timeoutMs: 600_000,
  });
}

// ─── Su-Field (76 Standard Solutions) ───────────────────────────────────────

export interface SuFieldRequest {
  project_id: string;
  system_description: string;
  current_issues: string[];
}

export interface MatchedStandardSolution {
  standard_id: string;
  standard_name: string;
  class_name: string;
  suggestion: string;
  affected_modules: string[];
  secondary_contradictions: string[];
}

export interface SuFieldResponse {
  su_field: { S1: string; S2: string; F: string };
  system_state: string;
  matched_solutions: MatchedStandardSolution[];
}

export function suFieldAnalyze(body: SuFieldRequest) {
  return request<SuFieldResponse>("/triz/sufield", body, { timeoutMs: 300_000 });
}

// ─── SCAMPER ────────────────────────────────────────────────────────────────

export interface ScamperTransformRequest {
  project_id: string;
  subsystem_name: string;
  subsystem_description: string;
  related_contradictions?: string[];
  /** RD-confirmed 6-dim interface contracts keyed by neighbour name.
   *  Optional so existing legacy call sites compile unchanged. When set,
   *  the backend prompt tells the LLM to respect the contract boundaries
   *  and to declare preserve/modify/break per dimension. (WBS 10.1) */
  interface_contracts?: InterfaceContractMap;
  /** Stable djb2 fingerprint of the contract snapshot at RD-confirm time.
   *  Used by the FE to detect drift and block SCAMPER generation until
   *  RD re-confirms the subsystem. */
  contracts_hash?: string;
}

export interface ScamperVariantResult {
  action: string;
  description: string;
  potential_benefits: string;
  new_contradictions: string[];
}

export interface ScamperTransformResponse {
  variants: ScamperVariantResult[];
}

export function scamperTransform(body: ScamperTransformRequest) {
  return request<ScamperTransformResponse>("/scamper/perform", body);
}

// ─── Risk ───────────────────────────────────────────────────────────────────

export interface RiskAnalyzeRequest {
  project_id: string;
  alternative_name: string;
  mechanism: string;
  assumptions?: string[];
}

export interface RiskSuggestionResult {
  description: string;
  failure_mode: string;
  probability: number;
  severity: number;
  mitigation: string;
}

export interface RiskAnalyzeResponse {
  risks: RiskSuggestionResult[];
}

export function riskAnalyze(body: RiskAnalyzeRequest) {
  return request<RiskAnalyzeResponse>("/risks/analyze", body);
}

// ─── Action ─────────────────────────────────────────────────────────────────

export interface ActionSuggestRequest {
  project_id: string;
  selected_alternative: string;
  rationale: string;
  risks?: string[];
}

export interface ActionSuggestionResult {
  description: string;
  assignee_role: string;
  suggested_due_days: number;
}

export interface ActionSuggestResponse {
  actions: ActionSuggestionResult[];
}

export function actionSuggest(body: ActionSuggestRequest) {
  return request<ActionSuggestResponse>("/actions/suggest", body);
}

// ─── Convergence ────────────────────────────────────────────────────────────

export interface ConvergenceAlternativeInput {
  id: string;
  name: string;
  mechanism: string;
  source: string;
  resolves_contradiction_ids: string[];
}

export interface ConvergenceContradictionInput {
  id: string;
  natural_description: string;
  severity: string;
  resolved: boolean;
  type: string | null;  // "TC" | "PC" | "SF"
  improving_param: number | null;
  worsening_param: number | null;
  engineering_statement: string;
  physical_contradiction: string;
  // Su-Field fields (populated when type === "SF")
  sf_substance_1?: string;
  sf_substance_2?: string;
  sf_field?: string;
}

/** v7 WP 10.6: phase_b_directive carried per-alternative so the backend
 *  scanner can honour intra-LTS SKIP without re-reading the LTS from DB. */
export interface LayeredAlternativeDirective {
  alternative_id: string;
  lts_id: string;
  adopted_layers: ("L1" | "L2" | "L3")[];
  same_contradiction_intra_layer_conflict: "skip" | "check";
  cross_contradiction_conflict: "skip" | "check";
}

export interface ConvergenceScanRequest {
  project_id: string;
  alternatives?: ConvergenceAlternativeInput[];  // optional — empty for Phase A
  contradictions: ConvergenceContradictionInput[];
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  phase?: "B";  // v8: always "B" — Phase A retired (L1 critic subsumes)
  /** v7 WP 10.6: when non-empty, Phase B scanner applies the SKIP rules
   *  described in TRIZ_Layered_DrillDown_Optimization.md §8.3. Back-compat
   *  default is an empty array (legacy flat mode). */
  layered_directives?: LayeredAlternativeDirective[];
}

export interface SecondaryContradictionResult {
  description: string;
  severity: string;
  source_alternative: string;
  type: string;
  improving_param: number | null;
  worsening_param: number | null;
  reasoning: string;
  is_confirmatory?: boolean;  // true = same causal chain as existing, doesn't count as new
}

export interface ConvergenceScanResponse {
  new_contradictions: SecondaryContradictionResult[];
  convergence_score: number;  // 0-100
  architecture_health: string;
  force_pause: boolean;
  pause_reason: string;
  reasoning_trace: string;
  phase: "B";  // v8: always "B"
}

export function convergenceScan(body: ConvergenceScanRequest) {
  return request<ConvergenceScanResponse>("/convergence/scan", body, { timeoutMs: 300_000 });
}

// ─── Validation Passport ─────────────────────────────────────────────────────

export interface ValidationPassportRequest {
  project_id: string;
  solution_name: string;
  mechanism: string;
  source?: string;
  constraints?: string[];
  kpis?: string[];
}

export interface ValidationPassportAssumptionResult {
  content: string;
  category: string;
  evidence_level: string;
  worst_consequence: string;
  worst_severity: string;
  suggested_experiment: string;
}

export interface ValidationPassportResult {
  assumptions: ValidationPassportAssumptionResult[];
  weak_points: string[];
  required_verifications: string[];
  cross_domain_source: string;
  confidence_level: number;
}

export interface ValidationPassportResponse {
  validation_passport: ValidationPassportResult;
}

export function validationPassportGenerate(body: ValidationPassportRequest) {
  return request<ValidationPassportResponse>("/alternatives/validation-passport", body);
}

// ─── MUST Evaluation ────────────────────────────────────────────────────────

export interface MustCriterionConfig {
  id: string;
  label: string;
  source: string;
  threshold?: string;
}

export interface MustEvaluateRequest {
  project_id: string;
  alternative_name: string;
  mechanism: string;
  must_criteria: MustCriterionConfig[];
  constraints?: string[];
  kpis?: string[];
}

export interface MustCriterionResult {
  id: string;
  label: string;
  passed: boolean | null;
  confidence: number;
  reasoning: string;
  evidence_sources: string[];
}

export interface MustEvaluateResponse {
  criteria_results: MustCriterionResult[];
  overall_pass: boolean | null;
  summary: string;
}

export function mustEvaluate(body: MustEvaluateRequest) {
  return request<MustEvaluateResponse>("/must/evaluate", body);
}

// ─── Contradiction Formalization ────────────────────────────────────────────

export interface ContradictionFormalizeRequest {
  project_id: string;
  contradiction_id: string;
  natural_description: string;
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  socraticAnswers?: string[];
}

export interface ContradictionFormalizeResponse {
  engineering_statement: string;
  improving_param: number | null;
  worsening_param: number | null;
  physical_contradiction: string | null;
  pc_attribute_a: string | null;
  pc_attribute_not_a: string | null;
  // Su-Field fields (populated when type === "SF")
  sf_substance_1: string | null;
  sf_substance_2: string | null;
  sf_field: string | null;
  sf_interaction: string | null;
  sf_completeness: string | null;
  // ADR-007: Explore 強制 TC-only；若 LLM 無法映射到 39 參數，後端回 type=null + rationale
  type: "TC" | "PC" | "SF" | null;
  confidence: number;
  // ADR-007: 當 type=null 時，後端附帶說明以驅動追問/細化 UX
  rationale?: string | null;
}

export function contradictionFormalize(body: ContradictionFormalizeRequest) {
  return request<ContradictionFormalizeResponse>(`/contradictions/${body.contradiction_id}/formalize`, body);
}

// ─── Multi-TC Identification (one-shot identify multiple TCs) ──────────────

export interface MultiTcIdentifyRequest {
  project_id: string;
  mission: string;
  constraints: string[];
  kpis: string[];
  socraticAnswers: string[];
  existing_descriptions: string[];
}

export interface IdentifiedTC {
  engineering_statement: string;
  type: "TC" | null;
  confidence: number;
  rationale: string | null;
  improving_param: number | null;
  worsening_param: number | null;
}

export interface MultiTcIdentifyResponse {
  items: IdentifiedTC[];
}

export function contradictionIdentifyMulti(
  body: MultiTcIdentifyRequest,
): Promise<MultiTcIdentifyResponse> {
  return request("/contradictions/identify-multi", body);
}

// ─── Contradiction PC Decomposition (L2 WBS 5.1) ───────────────────────────

export interface DecomposedPCPayload {
  derived_parameter: string;
  subsystem_hint: string;
  physical_contradiction: string;
  pc_attribute_a: string;
  pc_attribute_not_a: string;
  separation_principle_id: string;
  separation_category: 'time' | 'space' | 'condition' | 'whole_part';
  separation_rationale: string;
  confidence: number;
}

export interface ContradictionDecomposeRequest {
  project_id: string;
  parent_contradiction_id: string;
  engineering_statement: string;
  improving_param?: number | null;
  worsening_param?: number | null;
  severity?: string;
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  socraticAnswers?: string[];
  candidate_principles?: number[];
  rd_manual?: boolean;
}

export interface ContradictionDecomposeResponse {
  triggered: boolean;
  trigger_reason: string;
  decomposed_pcs: DecomposedPCPayload[];
  reasoning: string;
}

export function contradictionDecompose(
  cid: string,
  body: ContradictionDecomposeRequest,
) {
  return request<ContradictionDecomposeResponse>(`/contradictions/${cid}/decompose`, body);
}

// ─── Contradiction SF Derivation (Plan B hierarchical tree) ────────────────

export interface ContradictionDeriveSFRequest {
  project_id: string;
  contradiction_id: string;
  engineering_statement: string;
  improving_param: number;
  worsening_param: number;
  natural_description?: string;
}

export interface ContradictionDeriveSFResponse {
  derived: boolean;
  sf_substance_1?: string | null;
  sf_substance_2?: string | null;
  sf_field?: string | null;
  sf_interaction?: string | null;
  sf_completeness?: string | null;
}

export function contradictionDeriveSF(
  cid: string,
  body: ContradictionDeriveSFRequest,
) {
  return request<ContradictionDeriveSFResponse>(`/contradictions/${cid}/derive-sf`, body);
}

// ─── Assumption Extraction ─────────────────────────────────────────────────

export interface AssumptionExtractRequest {
  project_id: string;
  questions_and_answers?: Record<string, unknown>[];
  mission?: string;
  constraints?: string[];
  kpis?: string[];
  existing_assumptions?: string[];
}

export interface ExtractedAssumption {
  content: string;
  source: string;
  worst_consequence: string;
  worst_severity: string;
}

export interface AssumptionExtractResponse {
  assumptions: ExtractedAssumption[];
}

export function assumptionExtract(body: AssumptionExtractRequest) {
  return request<AssumptionExtractResponse>("/assumptions/extract", body);
}

// ─── SCAMPER Subsystem Suggestions ─────────────────────────────────────────

export interface SubsystemSuggestRequest {
  project_id: string;
  mission: string;
  contradictions?: string[];
  existing_subsystems?: string[];
  concept_pack?: ConceptArchitecturePack;
}

// Subsystem suggestion types are imported from the single source of truth
// (mirrored from backend Pydantic schemas). Wire format is camelCase only —
// the previous dual-casing `SuggestedInterfaceContract` was a band-aid for
// the now-removed AliasChoices hack in InterfaceContract.
// See Stage 1 of refactor/subsystem-interface-contracts.
export type {
  SuggestedSubsystem,
  SubsystemSuggestResponse,
  InterfaceContract as SuggestedInterfaceContract,
  InterfaceContractMap,
  PackageMap,
  PackageNode,
  RequiredEnvelope,
  SpatialEstimate,
  BBox,
} from '@/types/generated/subsystem';

export function scamperSubsystemSuggest(body: SubsystemSuggestRequest) {
  return request<SubsystemSuggestResponse>("/scamper/subsystem-suggestions", body, { timeoutMs: 300_000 });
}

// ─── Spatial Overlay / Override / Learned ──────────────────────────────────
//
// Matches the backend contracts in:
//   - backend/app/routers/scamper.py    → POST /scamper/spatial-overlay
//   - backend/app/routers/spatial.py    → POST /spatial/component-overrides
//                                       → POST /spatial/learned-components
// The request/response shapes below mirror the Pydantic models in
// backend/app/models/schemas.py (SpatialOverlayRequest, ComponentOverrideRequest,
// LearnedComponentPromoteRequest, and their *Response counterparts).
//
// NOTE: the backend overlay endpoint takes a nested `overlay` dict
// (`{zones: {name: {x_mm, ...}}, mass_budget_g: {key: cap}}`), NOT the flat
// arrays the SpatialOverlayDialog produces. Callers (see Create.tsx
// handleOverlaySubmit) are responsible for translating between the dialog
// payload and this request shape.
//
// `PackageMap` and `BBox` are both re-exported from the SCAMPER block above
// (`export type { ..., PackageMap, BBox, ... }`) so they're already in scope
// within this file.

export interface SpatialOverlayRequest {
  project_id: string;
  subsystems: unknown[];
  overlay: {
    zones?: Record<string, { x_mm: number; y_mm: number; z_mm: number; anchor?: string }>;
    mass_budget_g?: Record<string, number>;
  };
}

export interface SpatialOverlayResponse {
  package_map: PackageMap;
}

export function scamperSpatialOverlay(body: SpatialOverlayRequest) {
  return request<SpatialOverlayResponse>("/scamper/spatial-overlay", body, { timeoutMs: 60_000 });
}

export interface SpatialComponentOverrideRequest {
  project_id: string;
  component_key: string;
  category?: string;
  bbox: BBox;
  mass_g?: number;
  note?: string;
}

export interface SpatialComponentOverrideResponse {
  saved: boolean;
  component_key: string;
}

export function spatialComponentOverride(body: SpatialComponentOverrideRequest) {
  return request<SpatialComponentOverrideResponse>("/spatial/component-overrides", body);
}

export interface SpatialLearnedComponentRequest {
  key: string;
  category: string;
  bbox: BBox;
  mass_g?: number;
  origin?: string;
  origin_project_id?: string;
  source_url?: string;
  source_text?: string;
}

export interface SpatialLearnedComponentResponse {
  saved: boolean;
  key: string;
  confirmed_count: number;
}

export function spatialLearnedComponent(body: SpatialLearnedComponentRequest) {
  return request<SpatialLearnedComponentResponse>("/spatial/learned-components", body);
}

// ─── SCAMPER Feedback Contradictions ───────────────────────────────────────

export interface ScamperFeedbackRequest {
  project_id: string;
  new_contradictions: Record<string, unknown>[];
}

export interface ScamperFeedbackResponse {
  created_count: number;
  deduplicated_count: number;
  contradiction_ids: string[];
}

export function scamperFeedbackContradictions(body: ScamperFeedbackRequest) {
  return request<ScamperFeedbackResponse>("/scamper/feedback-contradictions", body);
}

// ─── Pre-CAD AI Analysis ───────────────────────────────────────────────────

export interface PreCadAnalyzeRequest {
  project_id: string;
  alternative_name: string;
  mechanism: string;
  constraints?: string[];
}

/**
 * Deterministic trace of why `spatial_score` has its value.
 * Produced from the spatial validator's PackageMap on the backend, never
 * from the LLM. See backend/app/models/schemas.py::SpatialTrace.
 */
export interface SpatialTrace {
  total_mass_g: number;
  total_bbox_mm: [number, number, number];
  clash_pairs: [string, string][];
  module_count: number;
  notes: string[];
  source: "validator" | "llm_fallback" | "empty";
}

export interface PreCadAnalyzeResponse {
  spatial_score: number;
  cost_score: number;
  safety_score: number;
  decoupling_score: number;
  supply_score: number;
  overall_pass: boolean;
  analysis: string;
  evidence_references?: EvidenceReference[];
  /** Optional deterministic trace of the spatial_score. */
  spatial_trace?: SpatialTrace | null;
}

export function preCadAnalyze(rid: string, body: PreCadAnalyzeRequest) {
  return request<PreCadAnalyzeResponse>(`/pre-cad-reviews/${rid}/ai-analyze`, body);
}

// ─── WANT Criteria Seed ────────────────────────────────────────────────────

export interface WantSeedRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  kpis?: string[];
}

export interface SuggestedWantCriterion {
  name: string;
  description: string;
  weight: number;
  anchors: Record<string, string>;
}

export interface WantSeedResponse {
  criteria: SuggestedWantCriterion[];
}

export function wantCriteriaSeed(body: WantSeedRequest) {
  return request<WantSeedResponse>("/want/criteria/seed", body);
}

// ─── Gate Check ────────────────────────────────────────────────────────────

export interface GateCheckItem {
  label: string;
  met: boolean;
  detail?: string;
}

export interface GateCheckResponse {
  gate_id: string;
  passed: boolean;
  failed_reasons: string[];
  checklist_items: GateCheckItem[];
}

async function requestGet<T>(path: string, opts?: RequestOptions<T>): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = await getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, {
    method: "GET",
    headers,
  });
  if (!res.ok) {
    const errorBody = await safeParseJsonError(res);
    throw new ApiError(res.status, errorBody);
  }
  const data = await safeParseJson(res, path);
  devAssertObject(data, path);
  return validateWithSchema(data, opts?.schema, path);
}

export function gateCheck(gateId: string, projectId: string) {
  return requestGet<GateCheckResponse>(`/gates/${gateId}/check?project_id=${encodeURIComponent(projectId)}`);
}

export interface BackendHealthCheckResult {
  ok: boolean;
  message: string;
}

export async function checkBackendHealth(): Promise<BackendHealthCheckResult> {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/health`, { method: "GET" });
    if (!res.ok) {
      const detail = await safeParseJsonError(res);
      const suffix = typeof detail === "string" ? `: ${detail}` : "";
      return { ok: false, message: `Health check 回應異常（HTTP ${res.status}）${suffix}` };
    }
    // Validate the response body is actually parseable JSON
    const data = await safeParseJson(res, "/health");
    if (data && typeof data === "object" && "status" in data) {
      return { ok: true, message: "後端連線正常" };
    }
    return { ok: true, message: "後端連線正常（回應格式非預期，但連線成功）" };
  } catch (err) {
    return { ok: false, message: getApiErrorMessage(err, "後端連線檢查") };
  }
}

export function getApiErrorMessage(error: unknown, actionLabel = "操作"): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return `${actionLabel}失敗：未授權（請重新登入或檢查 DEV_BYPASS）`;
    if (error.status === 403) return `${actionLabel}失敗：權限不足`;
    if (error.status === 404) return `${actionLabel}失敗：API 路徑不存在`;
    if (error.status >= 500) return `${actionLabel}失敗：後端服務異常（HTTP ${error.status}）`;
    return `${actionLabel}失敗：請求錯誤（HTTP ${error.status}）`;
  }
  if (error instanceof ApiNetworkError) {
    if (error.kind === "timeout") return `${actionLabel}失敗：請求逾時，請稍後重試`;
    return `${actionLabel}失敗：網路連線異常（無法連上後端）`;
  }
  if (error instanceof Error) {
    return `${actionLabel}失敗：${error.message}`;
  }
  return `${actionLabel}失敗：未知錯誤`;
}

// ─── Unknown Factor Discovery ─────────────────────────────────────────────

export interface UnknownFactorDiscoverRequest {
  project_id: string;
  mission: string;
  constraints?: string[];
  kpis?: string[];
  contradictions?: string[];
  existing_assumptions?: string[];
  existing_unknowns?: string[];
}

export interface DiscoveredUnknownFactor {
  description: string;
  impact: string;
  reason: string;
}

export interface UnknownFactorDiscoverResponse {
  factors: DiscoveredUnknownFactor[];
}

export function unknownFactorDiscover(body: UnknownFactorDiscoverRequest) {
  return request<UnknownFactorDiscoverResponse>("/unknown-factors/discover", body, { timeoutMs: 300_000 });
}

// ─── Analyst V2 (Auto-TRIZ v2 Layer 2) ─────────────────────────────────────

export interface EntryGradingRequest {
  project_id: string;
  problem_description: string;
}

export interface EntryGradingResponse {
  level: "A" | "B" | "C";
  reasoning: string;
}

export function entryGrading(body: EntryGradingRequest) {
  return request<EntryGradingResponse>("/analyst/entry-grading", body);
}

export interface FiveWhyRequest {
  project_id: string;
  problem_description: string;
  context?: string;
}

export interface FiveWhyPair {
  why: string;
  because: string;
}

export interface FiveWhyResponse {
  chain: FiveWhyPair[];
  root_cause: string;
}

export function fiveWhyAnalysis(body: FiveWhyRequest) {
  return request<FiveWhyResponse>("/analyst/five-why", body);
}

export interface KtAnalysisRequest {
  project_id: string;
  problem_description: string;
  context?: string;
}

export interface KtIsIsNotRow {
  dimension: string;
  is: string;
  is_not: string;
}

export interface KtIsIsNotResponse {
  rows: KtIsIsNotRow[];
  summary: string;
}

export function ktAnalysis(body: KtAnalysisRequest) {
  return request<KtIsIsNotResponse>("/analyst/kt-analysis", body);
}

export interface FunctionAnalysisRequest {
  project_id: string;
  problem_description: string;
  context?: string;
}

export interface FunctionComponent {
  name: string;
  role: string;
  interactions: string[];
}

export interface SfDiagnosis {
  substance_1: string;
  substance_2: string;
  field: string;
  diagnosis: string;
}

export interface FunctionAnalysisResponse {
  components: FunctionComponent[];
  sf_diagnosis: SfDiagnosis;
  summary: string;
}

export function functionAnalysis(body: FunctionAnalysisRequest) {
  return request<FunctionAnalysisResponse>("/analyst/function-analysis", body);
}

// ─── OZ/OT Analysis (Create V2) ────────────────────────────────────────────

export interface OzOtAnalysisRequest {
  project_id: string;
  problem_description: string;
  contradictions?: string[];
}

export interface OzOtAnalysisResponse {
  operating_zone: string;
  operating_time: string;
  controllable_params: string[];
  summary: string;
}

export function ozOtAnalysis(body: OzOtAnalysisRequest) {
  return request<OzOtAnalysisResponse>("/analyst/oz-ot-analysis", body);
}

// ─── Evidence Coverage (GET) ────────────────────────────────────────────────

export interface EvidenceCoverageResponse {
  project_id: string;
  coverage_pct: number;
  total_claims: number;
  covered_claims: number;
}

export function evidenceCoverage(projectId: string) {
  return requestGet<EvidenceCoverageResponse>(`/evidence/coverage/${encodeURIComponent(projectId)}`);
}

// ─── Concept Architecture Pack ──────────────────────────────────────────────

import type {
  UpstreamArtifactSummary,
  ConceptArchitecturePackResponse,
  ConceptArchitecturePack,
} from "@/types/conceptArchitecture";

export interface GenerateConceptArchitecturePackRequest {
  project_id: string;
  template_id?: string;
  upstream: UpstreamArtifactSummary;
}

export function generateConceptArchitecturePack(
  body: GenerateConceptArchitecturePackRequest
) {
  return request<ConceptArchitecturePackResponse>(
    "/concept-architecture/generate-pack",
    body,
    { timeoutMs: 120_000 }
  );
}

export function getLatestConceptArchitecturePack(projectId: string) {
  return requestGet<ConceptArchitecturePackResponse | null>(
    `/concept-architecture/latest-pack/${encodeURIComponent(projectId)}`
  );
}

// ─── Engineering Spec Drafts ────────────────────────────────────────────────

export type {
  EngineeringSpecDraftResponse,
  EngineeringSpecDraft,
  DraftValue,
  EngSpecStep1Response,
  EngSpecStep1aResponse,
  EngSpecStep1bRequest,
  EngSpecStep1bResponse,
  EngSpecStep2Request,
  EngSpecStep2Response,
  EngSpecStep3Request,
  EngSpecStep3Response,
} from "@/types/generated/engineeringSpec";

import type {
  EngineeringSpecDraftResponse,
  EngSpecStep1Response,
  EngSpecStep1aResponse,
  EngSpecStep1bRequest,
  EngSpecStep1bResponse,
  EngSpecStep2Response,
  EngSpecStep3Response,
} from "@/types/generated/engineeringSpec";

import type {
  EngSpecStep2Request,
  EngSpecStep3Request,
} from "@/types/generated/engineeringSpec";

export function scamperEngineeringSpecDrafts(body: SubsystemSuggestRequest) {
  return request<EngineeringSpecDraftResponse>(
    "/scamper/engineering-spec-drafts",
    body,
    { timeoutMs: 300_000 }
  );
}

// ── Split Engineering-Spec Pipeline ──────────────────────────────────────

/** Step 1: Expand concept architecture → 3-level subsystem hierarchy. */
export function engSpecStep1Expand(body: SubsystemSuggestRequest) {
  return request<EngSpecStep1Response>(
    "/scamper/engineering-spec-drafts/step1-expand",
    body,
    { timeoutMs: 180_000 },  // 3 min — spatial resolution can be slow
  );
}

/** Step 1a: LLM Structure Expansion only (≤150 s). */
export function engSpecStep1aExpand(body: SubsystemSuggestRequest) {
  return request<EngSpecStep1aResponse>(
    "/scamper/engineering-spec-drafts/step1a-expand",
    body,
    { timeoutMs: 300_000 },  // 5 min — LLM expansion (60-90s) + optional retry (60-90s) + buffer
  );
}

/** Step 1b: Spatial Enrichment + Package Map (≤80 s). */
export function engSpecStep1bEnrich(body: EngSpecStep1bRequest) {
  return request<EngSpecStep1bResponse>(
    "/scamper/engineering-spec-drafts/step1b-enrich",
    body,
    { timeoutMs: 120_000 },  // 2 min — web spatial + package discovery
  );
}

/** Step 2: Generate per-subsystem engineering spec drafts. */
export function engSpecStep2Generate(body: EngSpecStep2Request) {
  return request<EngSpecStep2Response>(
    "/scamper/engineering-spec-drafts/step2-generate",
    body,
    { timeoutMs: 120_000 },  // 2 min
  );
}

/** Step 3: Strengthen sources & upgrade confidence levels. */
export function engSpecStep3Strengthen(body: EngSpecStep3Request) {
  return request<EngSpecStep3Response>(
    "/scamper/engineering-spec-drafts/step3-strengthen",
    body,
    { timeoutMs: 120_000 },  // 2 min
  );
}

export { ApiError, ApiNetworkError, type RequestOptions };
