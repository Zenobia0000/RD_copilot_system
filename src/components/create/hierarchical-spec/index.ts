/**
 * Barrel export for hierarchical engineering spec view components.
 *
 * @see plans/hierarchical-spec-view.md §6 新增檔案清單
 */

export { HierarchicalSpecView } from "./HierarchicalSpecView";
export type { HierarchicalSpecViewProps } from "./HierarchicalSpecView";

export { SystemSpecCard } from "./SystemSpecCard";
export type { SystemSpecCardProps } from "./SystemSpecCard";

export { ModuleSpecCard } from "./ModuleSpecCard";
export type { ModuleSpecCardProps } from "./ModuleSpecCard";

export { ComponentSpecList } from "./ComponentSpecList";
export type { ComponentSpecListProps } from "./ComponentSpecList";

export { buildSpecTree } from "./buildSpecTree";
export type { SpecTreeNode, AggregatedStats } from "./buildSpecTree";
