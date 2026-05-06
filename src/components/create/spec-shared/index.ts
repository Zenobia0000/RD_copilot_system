/**
 * Barrel export for shared engineering spec rendering primitives.
 *
 * @see plans/hierarchical-spec-view.md §5
 */

export { ConfidenceBadge } from "./ConfidenceBadge";
export type { ConfidenceBadgeProps } from "./ConfidenceBadge";

export { SpecRow } from "./SpecRow";
export type { SpecRowProps } from "./SpecRow";

export { CategoryGroup } from "./CategoryGroup";
export type { CategoryGroupProps } from "./CategoryGroup";

export { fmtValue, humanize, groupByCategory, pctStr } from "./spec-helpers";
