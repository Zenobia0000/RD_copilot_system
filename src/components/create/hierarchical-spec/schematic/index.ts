/**
 * Barrel export for the Structural Schematic View sub-module.
 *
 * @see plans/structural-schematic-view.md §7.3
 */

export { StructuralSchematicView } from "./StructuralSchematicView";
export type { StructuralSchematicViewProps } from "./StructuralSchematicView";

export { SchematicCanvas } from "./SchematicCanvas";
export type { SchematicCanvasProps } from "./SchematicCanvas";

export { SchematicToolbar } from "./SchematicToolbar";
export type { SchematicToolbarProps } from "./SchematicToolbar";

export { SchematicDetailPanel } from "./SchematicDetailPanel";
export type { SchematicDetailPanelProps } from "./SchematicDetailPanel";

export { mapToSchematicModel } from "./mapToSchematicModel";
export type { MapToSchematicModelInput } from "./mapToSchematicModel";

export { computeSchematicLayout } from "./schematicLayout";
export type { LayoutResult } from "./schematicLayout";

export type {
  SchematicBlock,
  SchematicRelation,
  SchematicViewModel,
  SchematicFilterState,
  RelationType,
  RiskLevel,
  SchematicBlockLevel,
} from "./types";

export {
  createDefaultFilterState,
  RELATION_TYPE_COLORS,
  RELATION_TYPE_LABELS,
  RISK_LEVEL_COLORS,
} from "./types";
