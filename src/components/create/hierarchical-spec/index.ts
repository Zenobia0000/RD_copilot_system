/**
 * Barrel export for hierarchical engineering spec view components.
 *
 * @see plans/hierarchical-spec-view.md §6 新增檔案清單
 * @see plans/rd-friendly-spec-ux-design.md §8 Wave 1
 */

export { HierarchicalSpecView } from "./HierarchicalSpecView";
export type { HierarchicalSpecViewProps } from "./HierarchicalSpecView";

export { SystemSpecCard } from "./SystemSpecCard";
export type { SystemSpecCardProps } from "./SystemSpecCard";

export { ModuleSpecCard } from "./ModuleSpecCard";
export type { ModuleSpecCardProps } from "./ModuleSpecCard";

export { ComponentSpecList } from "./ComponentSpecList";
export type { ComponentSpecListProps } from "./ComponentSpecList";

export { SubsystemDatasheet } from "./SubsystemDatasheet";
export type { SubsystemDatasheetProps } from "./SubsystemDatasheet";

export { buildSpecTree } from "./buildSpecTree";
export type { SpecTreeNode, AggregatedStats } from "./buildSpecTree";

export { ArchitectureFlowView } from "./ArchitectureFlowView";
export type { ArchitectureFlowViewProps } from "./ArchitectureFlowView";

export { StructuralSchematicView } from "./schematic";
export type { StructuralSchematicViewProps } from "./schematic";

export { generateHierarchyText } from "./generateHierarchyText";
export type { HierarchyTextOptions } from "./generateHierarchyText";
