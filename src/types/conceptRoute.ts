// Multi-Solution Adoption Strategy types (X2)

/** 5 情境判斷類型 — 對應 TRIZ_Multi_Solution_Adoption_Strategy.md §2 */
export type AdoptionType = 'M1' | 'M2' | 'M3' | 'M4' | 'M5';

export const ADOPTION_TYPE_LABELS: Record<AdoptionType, { zh: string; strategy: string }> = {
  M1: { zh: '不同維度', strategy: '合併採納' },
  M2: { zh: '互相強化', strategy: '合併採納' },
  M3: { zh: '不同子系統', strategy: '各自採納' },
  M4: { zh: '互斥', strategy: '擇一篩選' },
  M5: { zh: '資源有限', strategy: '擇優保留' },
};

export type CompatibilityResult = 'compatible' | 'exclusive' | 'needs_verification';

export interface SolutionCompatibility {
  solutionAId: string;
  solutionBId: string;
  result: CompatibilityResult;
  adoptionType: AdoptionType | null;
  reason: string;
}

export interface CompositionEntry {
  solutionId: string;
  sourcePrinciple: string;
  concrete: string;
  dimension: string;
  adoptionType: AdoptionType;
}

// ---- v7: M6 cross-layer drill-down adoption (TRIZ layered) -----------------
//
// When a ConceptRoute.type === 'layered', it wraps a LayeredTrizSolution with
// the specific layer subset that RD adopted. Same-LTS cross-layer combinations
// are explicitly NOT mutually-exclusive (Phase B's intra-LTS SKIP directive).
// Refs:
//   - docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md v1.1 §2 M6 + §4.2
//   - docs/diagrams/create-ux-spec.md v7 §決策中心 layered 卡片

export type LayeredAdoptionMode = 'recommended' | 'custom' | 'fallback';

/** v7 WP 10.3/10.4: per-layer snapshot embedded in the ConceptRoute so the
 *  Decision Hub can render second/third eyes without re-fetching the LTS. */
/** Per-layer Validation Passport snapshot for the third eye (WBS 10.4). */
export interface LayeredVPSnapshot {
  /** Primary mechanism or principle selected for this layer. */
  mechanism: string;
  /** Key assumptions the layer's solution depends on. */
  keyAssumptions: string[];
  /** Conditions under which this layer's recommendation fails. */
  failConditions: string[];
  /** Evidence level label (E0…E4) — carried from the layer's evidence_level_floor. */
  evidenceLevel: string;
  /** Effort estimate (if available from the LLM). */
  effort?: string;
  /** Gain estimate (if available from the LLM). */
  gain?: string;
}

export interface LayeredLayerSnapshot {
  layer: 'L1' | 'L2' | 'L3';
  depthIndicator: string;                  // "trade-off 改良" / "根因突破" / "功能鏈缺陷修補"
  mechanismSummary: string;                // LLM-written short summary of the layer's mechanism
  suggestionCount: number;
  principleHits: number[];                 // for L1: candidate_principles from matrix
  evidenceLevelFloor: string;              // E0…E4
  effortHint?: string;                     // "low" / "medium" / "med-high" / "high"
  /** Free-text assumption bullets surfaced in the third eye. */
  assumptions: string[];
  /** L2 only — the derived physical parameter and separation type. */
  deepenLink?: {
    derivedParameter: string;
    contradictionStatement: string;
    separationType: string;                // e.g. "time (0.85)"
  };
  /** L3 only — bridge text to L1/L2 and standalone value. */
  bridgeText?: {
    supportsL1: string;
    supportsL2: string;
    standaloneValue: string;
  };
  /** Per-layer Validation Passport snapshot (WBS 10.4). */
  validationPassport?: LayeredVPSnapshot;
}

export interface LayeredConceptRouteMeta {
  /** LayeredTrizSolution.id (LTS-...) — used by Phase B for intra-LTS SKIP. */
  ltsId: string;
  /** Which layers the RD actually adopted. */
  adoptedLayers: ('L1' | 'L2' | 'L3')[];
  /** Which layers exist in the source LTS (some may be skipped upstream). */
  availableLayers: ('L1' | 'L2' | 'L3')[];
  /** e.g. "L2 + L3 組合（突破路線）" */
  recommendedRoute: string;
  /** e.g. "L1 單獨（快速路線）" */
  fallbackRoute: string;
  /** Rationale for the recommended route (from LTS differential_analysis). */
  recommendedRationale?: string;
  /** Adoption mode chosen by RD. */
  adoptionMode: LayeredAdoptionMode;
  /** phase_b_directive values surfaced so Phase B scanners can honour them. */
  phaseBDirective: {
    sameContradictionIntraLayerConflict: 'skip' | 'check';
    crossContradictionConflict: 'skip' | 'check';
  };
  /** Per-layer snapshots (available layers only). Second/third eye consume this. */
  layerSnapshots?: LayeredLayerSnapshot[];
  /** Concise one-sentence differential takeaway shown in the second eye. */
  differentialHighlight?: string;
}

export interface ConceptRoute {
  id: string;
  type: 'single' | 'composite' | 'layered';
  composition: CompositionEntry[];
  compositionRationale: string;
  antiPatternWarnings: string[];
  createdAt?: string;
  /** Populated when type === 'layered' (v7 M6 drill-down). */
  layered?: LayeredConceptRouteMeta;
}

export interface CompatibilityMatrix {
  solutions: { id: string; label: string; dimension: string }[];
  pairs: SolutionCompatibility[];
}

export interface AntiPatternCheck {
  label: string;
  passed: boolean;
  detail: string;
}

export interface MultiSolutionAdoptionState {
  matrix: CompatibilityMatrix;
  recommendedRoutes: ConceptRoute[];
  antiPatternChecks: AntiPatternCheck[];
}
