/**
 * Shared helpers for engineering spec draft rendering.
 *
 * Extracted from EngineeringSpecDraftPanel to be reused across both
 * flat (EngineeringSpecDraftPanel) and hierarchical (HierarchicalSpecView) views.
 *
 * @see plans/hierarchical-spec-view.md §5 Component Reuse Strategy
 */

import type { DraftValue, DraftCategory } from "@/types/generated/engineeringSpec";
import { DRAFT_CATEGORIES } from "@/types/generated/engineeringSpec";

/** Format a DraftValue's value for display. */
export function fmtValue(v: DraftValue): string {
  if (v.value == null) return "—";
  if (typeof v.value === "number") return String(v.value);
  if (typeof v.value === "string") return v.value;
  // Structured object/array → compact JSON
  try {
    return JSON.stringify(v.value);
  } catch {
    return String(v.value);
  }
}

/** Human-readable field name: snake_case → Title Case. */
export function humanize(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Group specs by category, preserving DRAFT_CATEGORIES order. */
export function groupByCategory(specs: DraftValue[]): Map<DraftCategory, DraftValue[]> {
  const map = new Map<DraftCategory, DraftValue[]>();
  for (const cat of DRAFT_CATEGORIES) {
    const items = specs.filter((s) => s.category === cat.key);
    if (items.length > 0) map.set(cat.key, items);
  }
  // Catch any uncategorized specs (shouldn't happen, but defensive)
  const knownKeys = new Set(DRAFT_CATEGORIES.map((c) => c.key));
  const uncategorized = specs.filter((s) => !knownKeys.has(s.category));
  if (uncategorized.length > 0) {
    const existing = map.get("manufacturing") ?? [];
    map.set("manufacturing", [...existing, ...uncategorized]);
  }
  return map;
}

/** Overall confidence as percentage string. */
export function pctStr(score: number): string {
  return `${Math.round(score * 100)}%`;
}
