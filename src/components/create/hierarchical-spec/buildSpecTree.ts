/**
 * buildSpecTree — joins EngineeringSpecDraft[] onto SuggestedSubsystem[]
 * tree, producing a SpecTreeNode[] with bottom-up aggregated statistics.
 *
 * Join key: draft.subsystem_code ↔ node.concept_origin_code (preferred)
 *           or draft.subsystem_code ↔ node.name (fallback)
 *
 * @see plans/hierarchical-spec-view.md §buildSpecTree helper
 */

import type { SuggestedSubsystem } from "@/types/generated/subsystem";
import type { EngineeringSpecDraft } from "@/types/generated/engineeringSpec";

// ---------------------------------------------------------------------------
// SpecTreeNode — tree node enriched with matched draft + aggregated stats
// ---------------------------------------------------------------------------

/** Aggregated statistics from this node + all descendants. */
export interface AggregatedStats {
  totalSpecs: number;
  verificationCount: number;
  avgConfidence: number;
}

/**
 * A subsystem tree node with its matched draft and descendant-aggregated stats.
 *
 * Extends the shape of SuggestedSubsystem but replaces `children` with
 * typed SpecTreeNode[] for recursive rendering.
 */
export interface SpecTreeNode {
  /** Original subsystem fields. */
  name: string;
  level: SuggestedSubsystem["level"];
  reason: string;
  related_contradictions: string[];
  interface_contracts: SuggestedSubsystem["interface_contracts"];

  /** Original ConceptSubsystem.code, if present (system-level only). */
  concept_origin_code?: string | null;
  /** KPI IDs from concept pack. */
  mapped_kpis?: string[];

  /** Matched draft for this node (null if no draft exists). */
  draft: EngineeringSpecDraft | null;

  /** Aggregated stats from this node + all descendants. */
  aggregated: AggregatedStats;

  /** Recursive children with specs attached. */
  children: SpecTreeNode[];
}

// ---------------------------------------------------------------------------
// Builder
// ---------------------------------------------------------------------------

/**
 * Build the spec tree by joining drafts onto the subsystem hierarchy.
 *
 * Algorithm:
 * 1. Index drafts by subsystem_code into a Map for O(1) lookup.
 * 2. Recursively walk the SuggestedSubsystem tree.
 * 3. At each node, attach the matching draft (if any).
 * 4. Bottom-up aggregate: totalSpecs, verificationCount, avgConfidence.
 */
export function buildSpecTree(
  tree: SuggestedSubsystem[],
  drafts: EngineeringSpecDraft[],
): SpecTreeNode[] {
  // Step 1: index drafts by subsystem_code
  const draftMap = new Map<string, EngineeringSpecDraft>();
  for (const d of drafts) {
    draftMap.set(d.subsystem_code, d);
  }

  // Step 2-4: recursive build with bottom-up aggregation
  function buildNode(sub: SuggestedSubsystem): SpecTreeNode {
    // Recurse into children first (bottom-up)
    const childNodes = (sub.children ?? []).map(buildNode);

    // Find matching draft — prefer concept_origin_code, fallback to name
    const draft =
      (sub.concept_origin_code ? draftMap.get(sub.concept_origin_code) : undefined) ??
      draftMap.get(sub.name) ??
      null;

    // This node's own stats
    const ownSpecs = draft?.specs.length ?? 0;
    const ownVerify = draft?.verification_count ?? 0;
    const ownConf = draft?.overall_confidence ?? 0;

    // Aggregate from children
    const childTotalSpecs = childNodes.reduce((s, c) => s + c.aggregated.totalSpecs, 0);
    const childVerify = childNodes.reduce((s, c) => s + c.aggregated.verificationCount, 0);

    const totalSpecs = ownSpecs + childTotalSpecs;
    const verificationCount = ownVerify + childVerify;

    // Weighted average confidence:
    // - own contribution weighted by ownSpecs
    // - each child contributes its avgConfidence weighted by its totalSpecs
    let avgConfidence = 0;
    if (totalSpecs > 0) {
      const ownWeight = ownSpecs * ownConf;
      const childWeight = childNodes.reduce(
        (s, c) => s + c.aggregated.totalSpecs * c.aggregated.avgConfidence,
        0,
      );
      avgConfidence = (ownWeight + childWeight) / totalSpecs;
    }

    return {
      name: sub.name,
      level: sub.level,
      reason: sub.reason,
      related_contradictions: sub.related_contradictions,
      interface_contracts: sub.interface_contracts,
      concept_origin_code: sub.concept_origin_code ?? null,
      mapped_kpis: sub.mapped_kpis ?? [],
      draft,
      aggregated: { totalSpecs, verificationCount, avgConfidence },
      children: childNodes,
    };
  }

  return tree.map(buildNode);
}
