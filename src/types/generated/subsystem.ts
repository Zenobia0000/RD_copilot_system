/**
 * Subsystem & Interface Contract type definitions.
 *
 * SINGLE SOURCE OF TRUTH for the subsystem definition + spatial discovery data
 * model. These types are mirrored from `backend/app/models/schemas.py` and
 * MUST stay in sync. To regenerate after changing the Python schema, see
 * `docs/refactoring/codegen.md` (or run `pnpm codegen` once tooling is set up).
 *
 * Hand-maintained for now (Stage 1 of refactor/subsystem-interface-contracts).
 * The intent is that any drift between this file and `schemas.py` is a bug
 * and CI should catch it once codegen is wired up.
 *
 * Naming conventions follow the Python field names verbatim:
 *   - InterfaceContract 6 dimensions: camelCase (loadPath, thermalPath, ...)
 *   - BBox / SpatialEstimate fields:  snake_case (x_mm, mass_g, ...)
 * The mix is intentional: Python field names are the wire contract.
 *
 * @see backend/app/models/schemas.py InterfaceContract
 * @see docs/e2e/Forward_Subsystem_Discovery_Architecture.md §6
 */

// ---------------------------------------------------------------------------
// Spatial primitives
// ---------------------------------------------------------------------------

/** Axis-aligned bounding box in millimeters. */
export interface BBox {
  x_mm: number;
  y_mm: number;
  z_mm: number;
  /** Frame-relative origin offset. Default [0, 0, 0]. */
  origin_mm?: [number, number, number];
  /** Frame-relative anchor name, e.g. "BB_center" / "downtube_top". */
  anchor?: string;
}

/** Per-module structured dimensional estimate (discovery mode). */
export interface SpatialEstimate {
  bbox?: BBox | null;
  mass_g?: number | null;
  /** e.g. "M6x4 @ 50mm PCD" */
  mounting_pattern?: string;
  /**
   * Source layer trace. One of:
   *   "rd_override:<key>" | "learned:<key>" | "web:<query>" |
   *   "seed:<key>" | "llm_estimate"
   * @see Forward_Subsystem_Discovery_Architecture.md §6.2
   */
  reference_source?: string;
  /** "library" | "estimate" | "rd_confirmed" */
  confidence?: 'library' | 'estimate' | 'rd_confirmed';
  /** One-line justification when reference_source is llm_estimate. */
  rationale?: string;
}

// ---------------------------------------------------------------------------
// Interface Contract — 6 dimensions + optional spatial
// ---------------------------------------------------------------------------

/**
 * 6-dimensional interface contract between two coupled modules.
 * Each module declares one of these PER NEIGHBOUR — the map key is the
 * neighbour's name (see InterfaceContractMap below).
 *
 * The 6 textual fields cover the physical channels through which interface
 * breakage can occur: geometric, force, thermal, signal, datum, maintenance.
 * The optional `spatial` block carries machine-readable bbox + mass for
 * downstream validators (Package Map, Pre-CAD spatial_score).
 *
 * @see Forward_Subsystem_Discovery_Architecture.md §6.5
 */
export interface InterfaceContract {
  /** Physical boundary, dimensions, mounting pattern. */
  envelope: string;
  /** Force / torque transfer path. */
  loadPath: string;
  /** Heat dissipation path. */
  thermalPath: string;
  /** Electrical / data signal path. */
  signalPath: string;
  /** Critical dimensions and tolerances. */
  datumTolerance: string;
  /** Maintenance access and replaceability. */
  serviceability: string;
  /** Optional machine-readable spatial estimate. */
  spatial?: SpatialEstimate | null;
}

/** Map of neighbour module name → contract describing the relationship. */
export type InterfaceContractMap = Record<string, InterfaceContract>;

// ---------------------------------------------------------------------------
// Package Map (F2.5 spatial validator output)
// ---------------------------------------------------------------------------

/** A single module flattened into the package map. */
export interface PackageNode {
  name: string;
  spatial: SpatialEstimate;
  /** Names of modules this node clashes with (AABB overlap). */
  clashes: string[];
}

/** The minimum envelope this design REQUIRES (descriptive, not prescriptive). */
export interface RequiredEnvelope {
  total_bbox_mm: [number, number, number];
  total_mass_g: number;
  by_anchor?: Record<string, [number, number, number]>;
}

/**
 * Discovery output. Tells RD what space and mass the design wants.
 * `overlay_*` fields are only populated when an optional what-if overlay
 * is applied via POST /scamper/spatial-overlay.
 */
export interface PackageMap {
  nodes: PackageNode[];
  required: RequiredEnvelope;
  overlay_budget?: Record<string, unknown> | null;
  overlay_violations?: string[];
  /** Inline SVG (pure stdlib renderer). Drop into `dangerouslySetInnerHTML`. */
  svg?: string;
  table_md?: string;
  notes?: string[];
}

// ---------------------------------------------------------------------------
// Suggested Subsystem (LLM output, before persistence)
// ---------------------------------------------------------------------------

/** Hierarchy level. Strict three-level decomposition. */
export type SubsystemLevel = 'system' | 'module' | 'component';

/**
 * One node in the LLM-produced subsystem tree.
 * Returned by POST /scamper/subsystem-suggestions.
 *
 * @see Forward_Subsystem_Discovery_Architecture.md §6.4
 */
export interface SuggestedSubsystem {
  name: string;
  level: SubsystemLevel;
  reason: string;
  /** IDs of contradictions this node relates to (from F1 output). */
  related_contradictions: string[];
  children: SuggestedSubsystem[];
  /** Map keyed by neighbour name. Only present on coupled modules. */
  interface_contracts: InterfaceContractMap;
  /**
   * Original ConceptSubsystem.code (e.g. 'A1').
   * Only system-level nodes carry this; module/component children are null.
   */
  concept_origin_code?: string | null;
  /** KPI IDs propagated from the concept pack. */
  mapped_kpis?: string[];
}

/** Response from POST /scamper/subsystem-suggestions. */
export interface SubsystemSuggestResponse {
  subsystems: SuggestedSubsystem[];
  /** Discovery output. Null when validator finds no spatial data. */
  package_map?: PackageMap | null;
}

// ---------------------------------------------------------------------------
// Compile-time helpers (display-time iteration)
// ---------------------------------------------------------------------------

/** Ordered list of contract dimensions, used for stable UI rendering. */
export const INTERFACE_CONTRACT_DIMS: ReadonlyArray<{
  key: keyof Omit<InterfaceContract, 'spatial'>;
  label: string;
  labelZh: string;
}> = [
  { key: 'envelope',       label: 'Envelope',         labelZh: '包絡尺寸' },
  { key: 'loadPath',       label: 'Load Path',        labelZh: '負載路徑' },
  { key: 'signalPath',     label: 'Signal Path',      labelZh: '信號路徑' },
  { key: 'thermalPath',    label: 'Thermal Path',     labelZh: '熱路徑' },
  { key: 'datumTolerance', label: 'Datum & Tolerance', labelZh: '基準與公差' },
  { key: 'serviceability', label: 'Serviceability',   labelZh: '維修通道' },
] as const;

/** All-empty 6-dim contract, used as a form initial value. */
export const EMPTY_INTERFACE_CONTRACT: InterfaceContract = {
  envelope: '',
  loadPath: '',
  signalPath: '',
  thermalPath: '',
  datumTolerance: '',
  serviceability: '',
};
