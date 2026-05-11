/**
 * schematicLayout — Rule-based 佈局演算法
 *
 * 將 SchematicViewModel + SchematicFilterState 轉換為帶座標的
 * ReactFlow Node[] 與 Edge[]。
 *
 * 佈局規則 (see plans/structural-schematic-view.md §5)：
 *  1. System 節點作為 group 容器
 *  2. BBox 影響大小（對數縮放）
 *  3. 高 centrality 的 system 居中
 *  4. 模組在 system 內按網格排列
 *  5. Component 展開時垂直堆疊
 */

import type { Node, Edge, MarkerType } from "@xyflow/react";
import type {
  SchematicViewModel,
  SchematicFilterState,
  SchematicBlock,
  SchematicRelation,
  RelationType,
} from "./types";
import { RELATION_TYPE_COLORS } from "./types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MODULE_BASE_W = 180;
const MODULE_BASE_H = 80;
const MODULE_MAX_W = 300;
const MODULE_MAX_H = 140;
const MODULE_GAP = 24;

const COMPONENT_W = 160;
const COMPONENT_H = 44;
const COMPONENT_GAP = 8;

const SYSTEM_PADDING_X = 32;
const SYSTEM_PADDING_Y = 56; // top padding includes header
const SYSTEM_BOTTOM_PAD = 24;
const SYSTEM_GAP = 60;

const BBOX_SCALE_FACTOR = 12;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface LayoutResult {
  nodes: Node[];
  edges: Edge[];
}

/**
 * 根據 view model 和篩選狀態計算 ReactFlow 節點與邊的座標位置。
 */
export function computeSchematicLayout(
  model: SchematicViewModel,
  filter: SchematicFilterState,
): LayoutResult {
  // Step 1: filter blocks & relations
  const visibleBlocks = filterBlocks(model.blocks, filter);
  const visibleRelations = filterRelations(model.relations, filter, visibleBlocks);

  // Step 2: group by system
  const systemGroups = groupBySystem(visibleBlocks);

  // Step 3: compute centrality for system ordering
  const centralityMap = computeSystemCentrality(visibleRelations, systemGroups);

  // Step 4: sort systems by centrality (descending)
  const sortedSystems = [...systemGroups.entries()].sort(
    ([a], [b]) => (centralityMap.get(b) ?? 0) - (centralityMap.get(a) ?? 0),
  );

  // Step 5: layout each system → compute positions
  const nodes: Node[] = [];
  const systemPositions = new Map<string, { x: number; y: number; w: number; h: number }>();

  let cursorX = 0;

  for (const [systemId, members] of sortedSystems) {
    const systemBlock = members.find((b) => b.level === "system");
    const moduleBlocks = members.filter((b) => b.level === "module");
    const componentBlocks = members.filter((b) => b.level === "component");

    // Layout modules within system
    const { moduleNodes, componentNodes, innerW, innerH } = layoutModulesInSystem(
      systemId,
      moduleBlocks,
      componentBlocks,
      filter.showComponents,
    );

    const systemW = innerW + SYSTEM_PADDING_X * 2;
    const systemH = innerH + SYSTEM_PADDING_Y + SYSTEM_BOTTOM_PAD;

    // System group node
    nodes.push({
      id: systemId,
      type: "schematicSystem",
      position: { x: cursorX, y: 0 },
      data: {
        block: systemBlock ?? {
          id: systemId,
          name: systemId,
          level: "system" as const,
          parentId: null,
          bboxSummary: null,
          massG: null,
          avgConfidence: 0,
          riskLevel: "none" as const,
          specCount: 0,
          verificationCount: 0,
          childCount: moduleBlocks.length,
          specTreeNodeRef: null,
        },
        width: systemW,
        height: systemH,
      },
      style: { width: systemW, height: systemH },
    });

    // Add module/component nodes offset within system
    for (const mn of moduleNodes) {
      nodes.push({
        ...mn,
        position: {
          x: mn.position.x + SYSTEM_PADDING_X,
          y: mn.position.y + SYSTEM_PADDING_Y,
        },
        parentId: systemId,
        extent: "parent" as const,
      });
    }

    for (const cn of componentNodes) {
      nodes.push({
        ...cn,
        parentId: systemId,
        extent: "parent" as const,
      });
    }

    systemPositions.set(systemId, {
      x: cursorX,
      y: 0,
      w: systemW,
      h: systemH,
    });

    cursorX += systemW + SYSTEM_GAP;
  }

  // Step 6: build edges
  const edges = buildEdges(visibleRelations);

  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// Internal: filter
// ---------------------------------------------------------------------------

function filterBlocks(
  blocks: SchematicBlock[],
  filter: SchematicFilterState,
): SchematicBlock[] {
  return blocks.filter((b) => {
    // Level filter
    if (!filter.showComponents && b.level === "component") return false;
    if (filter.levelFilter !== "all" && b.level !== filter.levelFilter) {
      // Always keep system blocks if we're filtering for module/component
      if (b.level !== "system") return false;
    }

    // Risk filter
    if (filter.riskFilter !== "all" && b.riskLevel !== filter.riskFilter) {
      // Always keep system blocks for grouping
      if (b.level !== "system") return false;
    }

    // Search filter
    if (filter.searchQuery.trim()) {
      const q = filter.searchQuery.toLowerCase();
      if (!b.name.toLowerCase().includes(q)) return false;
    }

    return true;
  });
}

function filterRelations(
  relations: SchematicRelation[],
  filter: SchematicFilterState,
  visibleBlocks: SchematicBlock[],
): SchematicRelation[] {
  const visibleIds = new Set(visibleBlocks.map((b) => b.id));

  return relations.filter((r) => {
    // Both endpoints must be visible
    if (!visibleIds.has(r.sourceId) || !visibleIds.has(r.targetId)) return false;

    // At least one relation type must match the filter
    const hasMatchingType = r.types.some((t) => filter.relationTypes.has(t));
    if (!hasMatchingType) return false;

    return true;
  });
}

// ---------------------------------------------------------------------------
// Internal: grouping
// ---------------------------------------------------------------------------

interface SystemGroup {
  systemBlock: SchematicBlock | null;
  modules: SchematicBlock[];
  components: SchematicBlock[];
}

function groupBySystem(
  blocks: SchematicBlock[],
): Map<string, SchematicBlock[]> {
  const map = new Map<string, SchematicBlock[]>();

  // First pass: add system blocks
  for (const b of blocks) {
    if (b.level === "system") {
      if (!map.has(b.id)) map.set(b.id, []);
      map.get(b.id)!.push(b);
    }
  }

  // Second pass: add module/component blocks to parent system
  for (const b of blocks) {
    if (b.level === "module" && b.parentId) {
      if (!map.has(b.parentId)) map.set(b.parentId, []);
      map.get(b.parentId)!.push(b);
    }
  }

  // Third pass: add components to their module's system
  for (const b of blocks) {
    if (b.level === "component" && b.parentId) {
      // Find the module's parent system
      const moduleBlock = blocks.find((m) => m.id === b.parentId && m.level === "module");
      const systemId = moduleBlock?.parentId;
      if (systemId && map.has(systemId)) {
        map.get(systemId)!.push(b);
      }
    }
  }

  return map;
}

// ---------------------------------------------------------------------------
// Internal: centrality
// ---------------------------------------------------------------------------

function computeSystemCentrality(
  relations: SchematicRelation[],
  systemGroups: Map<string, SchematicBlock[]>,
): Map<string, number> {
  // Build block → system mapping
  const blockToSystem = new Map<string, string>();
  for (const [systemId, members] of systemGroups) {
    for (const m of members) {
      blockToSystem.set(m.id, systemId);
    }
  }

  const centralityMap = new Map<string, number>();
  for (const key of systemGroups.keys()) {
    centralityMap.set(key, 0);
  }

  for (const r of relations) {
    const sysA = blockToSystem.get(r.sourceId);
    const sysB = blockToSystem.get(r.targetId);
    if (sysA && sysB && sysA !== sysB) {
      centralityMap.set(sysA, (centralityMap.get(sysA) ?? 0) + 1);
      centralityMap.set(sysB, (centralityMap.get(sysB) ?? 0) + 1);
    }
  }

  return centralityMap;
}

// ---------------------------------------------------------------------------
// Internal: module layout within a system
// ---------------------------------------------------------------------------

interface ModuleLayoutResult {
  moduleNodes: Node[];
  componentNodes: Node[];
  innerW: number;
  innerH: number;
}

function layoutModulesInSystem(
  systemId: string,
  moduleBlocks: SchematicBlock[],
  componentBlocks: SchematicBlock[],
  showComponents: boolean,
): ModuleLayoutResult {
  if (moduleBlocks.length === 0) {
    return { moduleNodes: [], componentNodes: [], innerW: MODULE_BASE_W, innerH: MODULE_BASE_H };
  }

  const cols = Math.ceil(Math.sqrt(moduleBlocks.length));
  const moduleNodes: Node[] = [];
  const componentNodes: Node[] = [];

  // Compute each module's size (BBox-influenced)
  const moduleSizes = moduleBlocks.map((b) => computeModuleSize(b));

  // Compute row heights and column widths
  const rows = Math.ceil(moduleBlocks.length / cols);
  const rowHeights: number[] = [];
  const colWidths: number[] = [];

  for (let c = 0; c < cols; c++) {
    colWidths[c] = MODULE_BASE_W;
  }
  for (let r = 0; r < rows; r++) {
    rowHeights[r] = MODULE_BASE_H;
  }

  // First pass: determine sizes per cell
  for (let i = 0; i < moduleBlocks.length; i++) {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const size = moduleSizes[i];

    // If showing components, add space for them
    let extraH = 0;
    if (showComponents) {
      const children = componentBlocks.filter((c) => c.parentId === moduleBlocks[i].id);
      extraH = children.length * (COMPONENT_H + COMPONENT_GAP);
    }

    colWidths[col] = Math.max(colWidths[col], size.w);
    rowHeights[row] = Math.max(rowHeights[row], size.h + extraH);
  }

  // Second pass: compute positions
  const rowYOffsets: number[] = [0];
  for (let r = 1; r < rows; r++) {
    rowYOffsets[r] = rowYOffsets[r - 1] + rowHeights[r - 1] + MODULE_GAP;
  }
  const colXOffsets: number[] = [0];
  for (let c = 1; c < cols; c++) {
    colXOffsets[c] = colXOffsets[c - 1] + colWidths[c - 1] + MODULE_GAP;
  }

  for (let i = 0; i < moduleBlocks.length; i++) {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const size = moduleSizes[i];
    const block = moduleBlocks[i];

    const x = colXOffsets[col];
    const y = rowYOffsets[row];

    moduleNodes.push({
      id: block.id,
      type: "schematicModule",
      position: { x, y },
      data: {
        block,
        width: size.w,
        height: size.h,
      },
      style: { width: size.w, height: size.h },
    });

    // Add component children below the module
    if (showComponents) {
      const children = componentBlocks.filter((c) => c.parentId === block.id);
      let compY = y + size.h + COMPONENT_GAP;

      for (const child of children) {
        componentNodes.push({
          id: child.id,
          type: "schematicComponent",
          position: {
            x: x + SYSTEM_PADDING_X + (size.w - COMPONENT_W) / 2,
            y: compY + SYSTEM_PADDING_Y,
          },
          data: {
            block: child,
            width: COMPONENT_W,
            height: COMPONENT_H,
          },
          style: { width: COMPONENT_W, height: COMPONENT_H },
        });
        compY += COMPONENT_H + COMPONENT_GAP;
      }
    }
  }

  // Compute total inner dimensions
  const lastCol = cols - 1;
  const lastRow = rows - 1;
  const innerW = (colXOffsets[lastCol] ?? 0) + (colWidths[lastCol] ?? MODULE_BASE_W);
  const innerH = (rowYOffsets[lastRow] ?? 0) + (rowHeights[lastRow] ?? MODULE_BASE_H);

  return { moduleNodes, componentNodes, innerW, innerH };
}

/**
 * 基於 BBox volume 計算模組節點的視覺大小。
 * base_size + log(bbox_volume) * scale_factor
 */
function computeModuleSize(block: SchematicBlock): { w: number; h: number } {
  let w = MODULE_BASE_W;
  let h = MODULE_BASE_H;

  if (block.bboxSummary) {
    const volume = parseBboxVolume(block.bboxSummary);
    if (volume > 0) {
      const logScale = Math.log10(volume + 1) * BBOX_SCALE_FACTOR;
      w = Math.min(MODULE_MAX_W, MODULE_BASE_W + logScale);
      h = Math.min(MODULE_MAX_H, MODULE_BASE_H + logScale * 0.6);
    }
  }

  return { w: Math.round(w), h: Math.round(h) };
}

/**
 * 從 "120×80×40 mm" 格式字串解析 bbox volume。
 */
function parseBboxVolume(summary: string): number {
  const match = summary.match(/([\d.]+)\s*[×x]\s*([\d.]+)\s*[×x]\s*([\d.]+)/i);
  if (!match) return 0;
  return parseFloat(match[1]) * parseFloat(match[2]) * parseFloat(match[3]);
}

// ---------------------------------------------------------------------------
// Internal: edge building — bezier curves with parallel-edge offset
// ---------------------------------------------------------------------------

/** Spacing (px) between parallel edges connecting the same source-target pair */
const PARALLEL_EDGE_GAP = 16;

/**
 * Build ReactFlow Edge array from SchematicRelation[].
 *
 * Key improvements over the previous `smoothstep` approach:
 *  1. Uses custom `"schematicEdge"` type (bezier) so paths are always curved.
 *  2. Groups edges that share the same (source, target) pair (regardless of
 *     direction) and assigns perpendicular pixel offsets so they do NOT overlap.
 *  3. Adds `markerEnd` arrow for direction clarity.
 */
function buildEdges(relations: SchematicRelation[]): Edge[] {
  // ── Step 1: Group edges by normalised source–target pair ──
  // Normalise the key so (A→B) and (B→A) share the same group.
  const pairGroups = new Map<string, SchematicRelation[]>();
  for (const r of relations) {
    const key = [r.sourceId, r.targetId].sort().join("||");
    const group = pairGroups.get(key);
    if (group) {
      group.push(r);
    } else {
      pairGroups.set(key, [r]);
    }
  }

  // ── Step 2: Assign offset index within each group ──
  const offsetMap = new Map<string, number>();
  for (const [, group] of pairGroups) {
    const count = group.length;
    group.forEach((r, idx) => {
      // Centre the group: offsets are symmetric around 0
      // e.g. 3 edges → offsets: -1, 0, +1  (times PARALLEL_EDGE_GAP)
      const centred = idx - (count - 1) / 2;
      offsetMap.set(r.id, centred * PARALLEL_EDGE_GAP);
    });
  }

  // ── Step 3: Build edge objects ──
  return relations.map((r) => {
    const primaryType = r.types[0] ?? "other";
    const color = RELATION_TYPE_COLORS[primaryType];
    const offset = offsetMap.get(r.id) ?? 0;

    return {
      id: r.id,
      source: r.sourceId,
      target: r.targetId,
      type: "schematicEdge",
      animated: r.criticality === "high",
      label: r.label,
      markerEnd: {
        type: "arrowclosed" as MarkerType,
        color,
        width: 14,
        height: 14,
      },
      style: {
        stroke: color,
        strokeWidth: r.criticality === "high" ? 2.5 : r.criticality === "medium" ? 1.8 : 1.2,
        strokeDasharray: r.criticality === "low" ? "6 3" : undefined,
      },
      data: { relation: r, offset },
      labelStyle: {
        fontSize: 10,
        fill: "#64748b",
      },
      labelBgStyle: {
        fill: "#f8fafc",
        fillOpacity: 0.85,
      },
    };
  });
}
