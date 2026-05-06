/**
 * Engineering Spec Draft type definitions — DraftValue with full provenance.
 *
 * SINGLE SOURCE OF TRUTH for the engineering spec draft data model.
 * These types are mirrored from `backend/app/models/schemas.py` (DraftValue,
 * EngineeringSpecDraft, EngineeringSpecDraftResponse) and MUST stay in sync.
 *
 * Design principle: every AI-generated value carries source, confidence, and
 * needs_verification — no AI number masquerades as engineering truth.
 *
 * @see plans/concept-pack-to-engineering-specs.md  v3 architecture
 * @see backend/app/models/schemas.py  DraftValue, EngineeringSpecDraft
 */

import type { SuggestedSubsystem, PackageMap } from './subsystem';

// ---------------------------------------------------------------------------
// Confidence & Category enums
// ---------------------------------------------------------------------------

/**
 * Confidence level for a single spec value.
 *   - confirmed: RD verified / datasheet confirmed
 *   - library:   from a reliable reference (learned component DB, standard)
 *   - estimate:  reasonable but unverified
 *   - speculative: LLM guess, must be verified
 */
export type DraftConfidence = 'confirmed' | 'library' | 'estimate' | 'speculative';

/**
 * Spec category for UI grouping and filtering.
 * AI assigns one per DraftValue based on what the spec represents.
 */
export type DraftCategory =
  | 'spatial'
  | 'material'
  | 'thermal'
  | 'electrical'
  | 'mechanical'
  | 'manufacturing';

// ---------------------------------------------------------------------------
// DraftValue — single AI-generated spec with full provenance
// ---------------------------------------------------------------------------

/**
 * A single AI-generated specification value with full provenance triple.
 *
 * Dynamic field design: AI decides `field_name` and `category` per subsystem
 * type, so different subsystems produce different spec fields.
 *
 * Core provenance triple (user requirement):
 *   - `source`:             where this value came from
 *   - `confidence`:         how reliable it is
 *   - `needs_verification`: whether human verification is needed
 */
export interface DraftValue {
  /** AI-decided field name, e.g. 'dimensions', 'thermal_budget', 'gear_ratio'. */
  field_name: string;

  /** Spec category for UI grouping. */
  category: DraftCategory;

  /**
   * Spec value. Can be numeric, string, or structured.
   * Examples: 250.0, 'IP67', { min: 10, max: 25, typical: 18 }
   */
  value: string | number | Record<string, unknown> | unknown[];

  /** Unit, e.g. 'mm', 'kg', 'W', '°C', 'N·m'. Null for dimensionless. */
  unit: string | null;

  /**
   * Origin of this value. Canonical prefixes:
   *   rd_override, learned, web, seed, llm_estimate, datasheet, standard
   */
  source: string;

  /** Confidence level. */
  confidence: DraftConfidence;

  /** Whether human verification is required. Default true for AI outputs. */
  needs_verification: boolean;

  /** Explanation of why this value was chosen. */
  rationale?: string | null;

  /**
   * Alternative options.
   * e.g. [{ value: 'ABS', reason: 'lower cost' }, { value: 'PC', reason: 'higher temp' }]
   */
  alternatives?: Array<Record<string, unknown>> | null;
}

// ---------------------------------------------------------------------------
// EngineeringSpecDraft — per-subsystem dynamic spec collection
// ---------------------------------------------------------------------------

/**
 * Complete engineering spec draft for one subsystem.
 *
 * Uses dynamic `specs: DraftValue[]` instead of fixed fields —
 * AI decides which spec fields to generate based on subsystem role/type.
 */
export interface EngineeringSpecDraft {
  /** Corresponding subsystem code (from ConceptSubsystem.code). */
  subsystem_code: string;

  /**
   * Dynamic spec list. AI produces appropriate fields per subsystem role.
   * E.g. motor → dimensions, mass, max_torque, rated_power, thermal_budget;
   * housing → dimensions, primary_material, waterproof_rating, surface_finish.
   */
  specs: DraftValue[];

  /** Weighted average confidence score (0.0–1.0) across all specs. */
  overall_confidence: number;

  /** Number of specs with needs_verification=true. Shown as red badge in UI. */
  verification_count: number;
}

// ---------------------------------------------------------------------------
// EngineeringSpecDraftResponse — pipeline response wrapper
// ---------------------------------------------------------------------------

/** Response from the engineering spec generation pipeline. */
export interface EngineeringSpecDraftResponse {
  /** One draft per subsystem in the concept pack. */
  drafts: EngineeringSpecDraft[];

  /** Expanded subsystem tree (from structure expansion step). */
  subsystem_tree: SuggestedSubsystem[];

  /** Discovery output. Null when validator finds no spatial data. */
  package_map?: PackageMap | null;
}

// ---------------------------------------------------------------------------
// Split-API step types (mirrors EngSpecStep*Request/Response in schemas.py)
// ---------------------------------------------------------------------------

/** Response from Step 1 — Structure Expansion. */
export interface EngSpecStep1Response {
  /** Expanded 3-level subsystem tree. */
  subsystems: SuggestedSubsystem[];
  /** Discovery output. Null when validator finds no spatial data. */
  package_map: PackageMap | null;
}

/** Response from Step 1a — LLM Structure Expansion only (no spatial/package). */
export interface EngSpecStep1aResponse {
  /** Expanded subsystem tree (spatial estimates are LLM-guesses, not web-resolved). */
  subsystems: SuggestedSubsystem[];
}

/** Request for Step 1b — Spatial Enrichment + Package Map. */
export interface EngSpecStep1bRequest {
  project_id: string;
  /** Subsystem tree from Step 1a (pre-spatial). */
  subsystems: SuggestedSubsystem[];
}

/** Response from Step 1b — subsystems with resolved spatial + package map. */
export interface EngSpecStep1bResponse {
  /** Subsystems with web-resolved spatial estimates. */
  subsystems: SuggestedSubsystem[];
  /** Discovery output. Null when no spatial data found. */
  package_map: PackageMap | null;
}

/** Request for Step 2 — AI Spec Generation. */
export interface EngSpecStep2Request {
  project_id: string;
  mission: string;
  subsystems: SuggestedSubsystem[];
}

/** Response from Step 2 — AI Spec Generation (drafts without strengthening). */
export interface EngSpecStep2Response {
  drafts: EngineeringSpecDraft[];
}

/** Request for Step 3 — Source Strengthening. */
export interface EngSpecStep3Request {
  project_id: string;
  mission: string;
  drafts: EngineeringSpecDraft[];
  /** Subsystem tree for prompt context (needed by strengthening prompt). */
  subsystems: SuggestedSubsystem[];
}

/** Response from Step 3 — Source Strengthening (final drafts). */
export interface EngSpecStep3Response {
  drafts: EngineeringSpecDraft[];
}

// ---------------------------------------------------------------------------
// Confidence score mapping (mirrors _CONFIDENCE_SCORES in schemas.py)
// ---------------------------------------------------------------------------

/** Confidence-to-numeric-score mapping for calculations and sorting. */
export const CONFIDENCE_SCORES: Record<DraftConfidence, number> = {
  confirmed: 1.0,
  library: 0.75,
  estimate: 0.5,
  speculative: 0.25,
} as const;

// ---------------------------------------------------------------------------
// UI helpers — confidence color system
// ---------------------------------------------------------------------------

/** Tailwind color tokens for confidence-based badge rendering. */
export const CONFIDENCE_COLORS: Record<DraftConfidence, {
  bg: string;
  text: string;
  border: string;
  label: string;
  labelZh: string;
}> = {
  confirmed: {
    bg: 'bg-green-100 dark:bg-green-950/30',
    text: 'text-green-700 dark:text-green-400',
    border: 'border-green-300 dark:border-green-700',
    label: 'Confirmed',
    labelZh: '已確認',
  },
  library: {
    bg: 'bg-blue-100 dark:bg-blue-950/30',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-300 dark:border-blue-700',
    label: 'Library',
    labelZh: '參考值',
  },
  estimate: {
    bg: 'bg-amber-100 dark:bg-amber-950/30',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-300 dark:border-amber-700',
    label: 'Estimate',
    labelZh: '估算值',
  },
  speculative: {
    bg: 'bg-red-100 dark:bg-red-950/30',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-300 dark:border-red-700',
    label: 'Speculative',
    labelZh: '推測值',
  },
} as const;

/** Ordered category list for stable UI rendering. */
export const DRAFT_CATEGORIES: ReadonlyArray<{
  key: DraftCategory;
  label: string;
  labelZh: string;
  icon: string;
}> = [
  { key: 'spatial',        label: 'Spatial',        labelZh: '空間尺寸', icon: '📐' },
  { key: 'material',       label: 'Material',       labelZh: '材料',     icon: '🧱' },
  { key: 'thermal',        label: 'Thermal',        labelZh: '熱管理',   icon: '🌡️' },
  { key: 'electrical',     label: 'Electrical',     labelZh: '電氣',     icon: '⚡' },
  { key: 'mechanical',     label: 'Mechanical',     labelZh: '機械',     icon: '⚙️' },
  { key: 'manufacturing',  label: 'Manufacturing',  labelZh: '製造',     icon: '🏭' },
] as const;
