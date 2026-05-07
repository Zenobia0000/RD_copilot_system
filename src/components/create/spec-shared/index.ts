/**
 * Barrel export for shared engineering spec rendering primitives.
 *
 * @see plans/hierarchical-spec-view.md §5
 * @see plans/rd-friendly-spec-ux-design.md §8 Wave 1
 */

export { ConfidenceBadge } from "./ConfidenceBadge";
export type { ConfidenceBadgeProps } from "./ConfidenceBadge";

export { SpecRow } from "./SpecRow";
export type { SpecRowProps } from "./SpecRow";

export { CategoryGroup } from "./CategoryGroup";
export type { CategoryGroupProps } from "./CategoryGroup";

export {
  SimplifiedConfidenceIcon,
  toSimplifiedLevel,
} from "./SimplifiedConfidenceIcon";
export type {
  SimplifiedConfidenceIconProps,
  SimplifiedLevel,
} from "./SimplifiedConfidenceIcon";

export { SpecDashboardSummary } from "./SpecDashboardSummary";
export type { SpecDashboardSummaryProps } from "./SpecDashboardSummary";

export { fmtValue, humanize, groupByCategory, pctStr } from "./spec-helpers";
