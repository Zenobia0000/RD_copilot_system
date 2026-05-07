/**
 * ArchitectureFlowView — interactive system architecture diagram using
 * ReactFlow group nodes (parentId), showing the 3-level subsystem topology
 * as a **nested block diagram**: systems visually contain modules, modules
 * visually contain components. Interface contracts render as cross-module
 * dashed edges.
 *
 * Node types:
 *   - systemGroup  (system level)  — large container, thick blue border
 *   - moduleGroup  (module level)  — medium container, slate border
 *   - component    (component)     — small leaf card, dashed border
 *
 * Edge types:
 *   - interface — dashed animated smoothstep, cross-module contract + tooltip
 *
 * Layout: custom bottom-up sizing + top-down positioning (replaces dagre).
 *
 * @see plans/nested-block-diagram-architecture.md
 */

import { useMemo, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeChange,
  type NodeProps,
  applyNodeChanges,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { cn } from "@/lib/utils";
import type {
  SuggestedSubsystem,
  SubsystemLevel,
  InterfaceContract,
} from "@/types/generated/subsystem";
import { INTERFACE_CONTRACT_DIMS } from "@/types/generated/subsystem";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ArchitectureFlowViewProps {
  tree: SuggestedSubsystem[];
  onNodeClick?: (subsystemName: string) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Node data shape
// ---------------------------------------------------------------------------

interface FlowNodeData {
  label: string;
  code: string;
  level: SubsystemLevel;
  childCount: number;
  contractCount: number;
  /** Total component count across all modules (system-level summary). */
  totalComponentCount?: number;
  /** Callback injected at render-time to notify hover on module nodes. */
  onHoverModule?: (moduleId: string | null) => void;
  /** The module node's own ID (set during node data patching). */
  moduleId?: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const LAYOUT = {
  // Component leaf
  COMP_W: 140,
  COMP_H: 36,
  COMP_GAP: 8,

  // Module container padding
  MOD_PADDING_TOP: 36,
  MOD_PADDING_X: 12,
  MOD_PADDING_BOTTOM: 12,
  MOD_GAP: 16, // gap between modules inside a system

  // System container padding
  SYS_PADDING_TOP: 44,
  SYS_PADDING_X: 16,
  SYS_PADDING_BOTTOM: 20,
  SYS_GAP: 32, // horizontal gap between systems
  SYS_ROW_GAP: 32, // vertical gap between system rows

  // Grid limits
  MODULES_PER_ROW: 3, // max modules per row inside a system
  SYSTEMS_PER_ROW: 2, // max systems per row on the canvas
};

// ---------------------------------------------------------------------------
// CSS — dark-mode-aware overrides for ReactFlow chrome
// ---------------------------------------------------------------------------

const flowStyles = `
  .architecture-flow .react-flow {
    background: hsl(var(--muted) / 0.15) !important;
    border-radius: 8px;
  }
  .dark .architecture-flow .react-flow {
    background: hsl(var(--card)) !important;
  }
  .architecture-flow .react-flow__controls-button {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    color: hsl(var(--foreground));
  }
  .architecture-flow .react-flow__controls-button svg {
    fill: hsl(var(--foreground));
  }
  .architecture-flow .react-flow__minimap {
    border: 1px solid hsl(var(--border));
    border-radius: 4px;
  }
  .dark .architecture-flow .react-flow__minimap {
    background: hsl(var(--card));
  }
  .dark .architecture-flow .react-flow__node {
    color: #E5E7EB;
  }
`;

// ---------------------------------------------------------------------------
// Custom Node components — group containers + leaf
// ---------------------------------------------------------------------------

/** System-level group container — thick blue border, title bar at top. */
function SystemGroupNode({ data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        borderRadius: 12,
        border: "3px solid #3B82F6",
        background: "rgba(59, 130, 246, 0.04)",
        position: "relative",
      }}
    >
      {/* Invisible handles for potential system-level edges */}
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />

      {/* Title bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: LAYOUT.SYS_PADDING_TOP - 4,
          padding: "8px 14px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(59, 130, 246, 0.15)",
          borderRadius: "12px 12px 0 0",
          background: "rgba(59, 130, 246, 0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>{data.label}</span>
          {data.code && (
            <span style={{ fontSize: 10, opacity: 0.5, fontWeight: 500 }}>
              {data.code}
            </span>
          )}
        </div>
        <div style={{ fontSize: 9, opacity: 0.5 }}>
          {data.childCount > 0 && `${data.childCount} 模組`}
          {data.childCount > 0 &&
            (data.totalComponentCount ?? 0) > 0 &&
            " · "}
          {(data.totalComponentCount ?? 0) > 0 &&
            `${data.totalComponentCount} 元件`}
          {(data.childCount > 0 || (data.totalComponentCount ?? 0) > 0) &&
            data.contractCount > 0 &&
            " · "}
          {data.contractCount > 0 && `${data.contractCount} 關聯`}
        </div>
      </div>
    </div>
  );
}

/** Module-level group container — slate border, title bar, holds components. */
function ModuleGroupNode({ data, id }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        borderRadius: 8,
        border: "2px solid #64748B",
        background: "rgba(100, 116, 139, 0.04)",
        position: "relative",
      }}
      onMouseEnter={() => data.onHoverModule?.(id)}
      onMouseLeave={() => data.onHoverModule?.(null)}
    >
      {/* Handles for interface-contract edges */}
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ opacity: 0 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left-target"
        style={{ opacity: 0 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right-source"
        style={{ opacity: 0 }}
      />

      {/* Title bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: LAYOUT.MOD_PADDING_TOP - 4,
          padding: "6px 10px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(100, 116, 139, 0.15)",
          borderRadius: "8px 8px 0 0",
          background: "rgba(100, 116, 139, 0.06)",
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600 }}>{data.label}</span>
        {data.contractCount > 0 && (
          <span
            style={{
              fontSize: 9,
              display: "inline-flex",
              alignItems: "center",
              gap: 3,
              color: "#6366F1",
              opacity: 0.8,
            }}
          >
            🔗 {data.contractCount} 關聯
          </span>
        )}
      </div>
    </div>
  );
}

/** Component leaf node — small dashed-border card (non-container). */
function ComponentFlowNode({ data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        width: LAYOUT.COMP_W,
        height: LAYOUT.COMP_H,
        borderRadius: 6,
        border: "1.5px dashed #9CA3AF",
        background: "rgba(156, 163, 175, 0.05)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 11,
        fontWeight: 500,
        cursor: "pointer",
      }}
    >
      {data.label}
    </div>
  );
}

const nodeTypes = {
  systemGroup: SystemGroupNode,
  moduleGroup: ModuleGroupNode,
  component: ComponentFlowNode,
};

// ---------------------------------------------------------------------------
// Contract helpers (preserved from original implementation)
// ---------------------------------------------------------------------------

function nodeId(node: SuggestedSubsystem): string {
  return node.concept_origin_code ?? node.name;
}

/** Build a label summarising which of the 6 contract dims are filled. */
function contractSummaryLabel(contract: InterfaceContract): string {
  const filled = INTERFACE_CONTRACT_DIMS.filter(
    (d) => contract[d.key]?.trim(),
  ).length;
  return `${filled}/6 維`;
}

/** Map contract completeness (filled dims out of 6) to a colour. */
function completenessColor(contract: InterfaceContract): string {
  const filled = INTERFACE_CONTRACT_DIMS.filter(
    (d) => contract[d.key]?.trim(),
  ).length;
  if (filled >= 5) return "#22C55E"; // green  — 完整
  if (filled >= 3) return "#EAB308"; // yellow — 部分
  return "#EF4444";                  // red    — 薄弱
}

/** Build tooltip text for an interface contract edge. */
function contractTooltip(
  sourceName: string,
  targetName: string,
  contract: InterfaceContract,
): string {
  const lines = [`${sourceName} ↔ ${targetName}`];
  for (const dim of INTERFACE_CONTRACT_DIMS) {
    const val = contract[dim.key]?.trim();
    lines.push(`${val ? "✅" : "❌"} ${dim.labelZh}`);
  }
  if (contract.spatial) {
    lines.push("📐 spatial: defined");
  }
  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Nested layout algorithm — bottom-up sizing, top-down positioning
// ---------------------------------------------------------------------------

interface SizeInfo {
  w: number;
  h: number;
}

interface ModuleLayoutInfo {
  id: string;
  size: SizeInfo;
}

interface SystemLayoutInfo {
  id: string;
  size: SizeInfo;
  modules: ModuleLayoutInfo[];
  /** Max height of each row of modules inside this system. */
  moduleRowMaxHeights: number[];
}

/** Compute module container size from its children count. */
function computeModuleSize(compCount: number): SizeInfo {
  if (compCount === 0) {
    return {
      w: LAYOUT.COMP_W + LAYOUT.MOD_PADDING_X * 2,
      h: LAYOUT.MOD_PADDING_TOP + LAYOUT.MOD_PADDING_BOTTOM + 24,
    };
  }
  return {
    w: LAYOUT.COMP_W + LAYOUT.MOD_PADDING_X * 2,
    h:
      LAYOUT.MOD_PADDING_TOP +
      compCount * LAYOUT.COMP_H +
      Math.max(0, compCount - 1) * LAYOUT.COMP_GAP +
      LAYOUT.MOD_PADDING_BOTTOM,
  };
}

/** Compute system container size from its module layouts. */
function computeSystemSize(modules: ModuleLayoutInfo[]): {
  size: SizeInfo;
  moduleRowMaxHeights: number[];
} {
  if (modules.length === 0) {
    return {
      size: {
        w: 200,
        h: LAYOUT.SYS_PADDING_TOP + LAYOUT.SYS_PADDING_BOTTOM + 40,
      },
      moduleRowMaxHeights: [],
    };
  }

  const modulesPerRow = Math.min(LAYOUT.MODULES_PER_ROW, modules.length);
  const rows = Math.ceil(modules.length / modulesPerRow);
  const maxModW = Math.max(...modules.map((m) => m.size.w));

  // Max height per row
  const moduleRowMaxHeights: number[] = [];
  for (let r = 0; r < rows; r++) {
    const rowModules = modules.slice(
      r * modulesPerRow,
      (r + 1) * modulesPerRow,
    );
    moduleRowMaxHeights.push(Math.max(...rowModules.map((m) => m.size.h)));
  }

  const totalW =
    modulesPerRow * maxModW +
    Math.max(0, modulesPerRow - 1) * LAYOUT.MOD_GAP +
    LAYOUT.SYS_PADDING_X * 2;

  const totalH =
    LAYOUT.SYS_PADDING_TOP +
    moduleRowMaxHeights.reduce((a, b) => a + b, 0) +
    Math.max(0, rows - 1) * LAYOUT.MOD_GAP +
    LAYOUT.SYS_PADDING_BOTTOM;

  return { size: { w: totalW, h: totalH }, moduleRowMaxHeights };
}

// ---------------------------------------------------------------------------
// Build flow elements — nested nodes + interface-contract edges
// ---------------------------------------------------------------------------

interface FlowElements {
  nodes: Node<FlowNodeData>[];
  edges: Edge[];
}

function buildNestedFlowElements(tree: SuggestedSubsystem[]): FlowElements {
  // Separate arrays — parents MUST precede children in final array
  const systemNodes: Node<FlowNodeData>[] = [];
  const moduleNodes: Node<FlowNodeData>[] = [];
  const componentNodes: Node<FlowNodeData>[] = [];
  const edges: Edge[] = [];
  const interfaceEdgeSet = new Set<string>();

  // ── name → id lookup for resolving interface_contracts neighbours ──
  const nameToId = new Map<string, string>();
  function registerNames(subtree: SuggestedSubsystem[]) {
    for (const s of subtree) {
      nameToId.set(s.name, nodeId(s));
      if (s.children?.length) registerNames(s.children);
    }
  }
  registerNames(tree);

  // ── Phase 1: bottom-up sizing + node creation ──
  const systemLayouts: SystemLayoutInfo[] = [];

  for (const system of tree) {
    const sysId = nodeId(system);
    const modules = system.children ?? [];
    const moduleLayouts: ModuleLayoutInfo[] = [];
    let systemContractCount = 0;
    let totalComponentCount = 0;

    for (const mod of modules) {
      const modId = nodeId(mod);
      const components = mod.children ?? [];
      totalComponentCount += components.length;
      const modSize = computeModuleSize(components.length);
      moduleLayouts.push({ id: modId, size: modSize });

      const modContractKeys = Object.keys(mod.interface_contracts ?? {});
      systemContractCount += modContractKeys.length;

      // ── Component leaf nodes ──
      for (let ci = 0; ci < components.length; ci++) {
        const comp = components[ci];
        componentNodes.push({
          id: nodeId(comp),
          type: "component",
          parentId: modId,
          extent: "parent",
          position: {
            x: LAYOUT.MOD_PADDING_X,
            y:
              LAYOUT.MOD_PADDING_TOP +
              ci * (LAYOUT.COMP_H + LAYOUT.COMP_GAP),
          },
          data: {
            label: comp.name,
            code: comp.concept_origin_code ?? "",
            level: "component",
            childCount: 0,
            contractCount: 0,
          },
        });
      }

      // ── Module group node (position set in Phase 2) ──
      moduleNodes.push({
        id: modId,
        type: "moduleGroup",
        parentId: sysId,
        extent: "parent",
        position: { x: 0, y: 0 },
        style: { width: modSize.w, height: modSize.h },
        data: {
          label: mod.name,
          code: mod.concept_origin_code ?? "",
          level: "module",
          childCount: components.length,
          contractCount: modContractKeys.length,
        },
      });

      // ── Interface contract edges (module ↔ module) ──
      if (mod.interface_contracts) {
        for (const [neighbourName, contract] of Object.entries(
          mod.interface_contracts,
        )) {
          const targetId = nameToId.get(neighbourName);
          if (!targetId) continue;

          const canonKey = [modId, targetId].sort().join("↔");
          if (interfaceEdgeSet.has(canonKey)) continue;
          interfaceEdgeSet.add(canonKey);

          const edgeColor = completenessColor(contract);
          edges.push({
            id: `i-${modId}-${targetId}`,
            source: modId,
            target: targetId,
            hidden: true,
            animated: true,
            type: "smoothstep",
            style: {
              stroke: edgeColor,
              strokeWidth: 1.5,
              strokeDasharray: "6 3",
            },
            label: contractSummaryLabel(contract),
            labelStyle: { fontSize: 9, fill: edgeColor, fontWeight: 600 },
            labelBgStyle: {
              fill: "rgba(255,255,255,0.85)",
              stroke: edgeColor,
              strokeWidth: 0.5,
              borderRadius: 3,
            },
            data: {
              tooltip: contractTooltip(mod.name, neighbourName, contract),
              sourceModuleId: modId,
              targetModuleId: targetId,
            },
          });
        }
      }
    }

    // System-level contracts (if any)
    if (system.interface_contracts) {
      systemContractCount += Object.keys(system.interface_contracts).length;

      for (const [neighbourName, contract] of Object.entries(
        system.interface_contracts,
      )) {
        const targetId = nameToId.get(neighbourName);
        if (!targetId) continue;

        const canonKey = [sysId, targetId].sort().join("↔");
        if (interfaceEdgeSet.has(canonKey)) continue;
        interfaceEdgeSet.add(canonKey);

        const sysEdgeColor = completenessColor(contract);
        edges.push({
          id: `i-${sysId}-${targetId}`,
          source: sysId,
          target: targetId,
          hidden: true,
          animated: true,
          type: "smoothstep",
          style: {
            stroke: sysEdgeColor,
            strokeWidth: 1.5,
            strokeDasharray: "6 3",
          },
          label: contractSummaryLabel(contract),
          labelStyle: { fontSize: 9, fill: sysEdgeColor, fontWeight: 600 },
          labelBgStyle: {
            fill: "rgba(255,255,255,0.85)",
            stroke: sysEdgeColor,
            strokeWidth: 0.5,
            borderRadius: 3,
          },
          data: {
            tooltip: contractTooltip(system.name, neighbourName, contract),
            sourceModuleId: sysId,
            targetModuleId: targetId,
          },
        });
      }
    }

    // ── Compute system container size ──
    const { size: sysSize, moduleRowMaxHeights } =
      computeSystemSize(moduleLayouts);
    systemLayouts.push({
      id: sysId,
      size: sysSize,
      modules: moduleLayouts,
      moduleRowMaxHeights,
    });

    // ── System group node (position set in Phase 2) ──
    systemNodes.push({
      id: sysId,
      type: "systemGroup",
      position: { x: 0, y: 0 },
      style: { width: sysSize.w, height: sysSize.h },
      data: {
        label: system.name,
        code: system.concept_origin_code ?? "",
        level: "system",
        childCount: modules.length,
        contractCount: systemContractCount,
        totalComponentCount,
      },
    });
  }

  // ── Phase 2: top-down positioning ──

  // Position systems in a grid (left → right, wrapping)
  const systemsPerRow = Math.min(
    LAYOUT.SYSTEMS_PER_ROW,
    systemLayouts.length || 1,
  );
  let cursorX = 0;
  let cursorY = 0;
  let rowMaxH = 0;

  for (let si = 0; si < systemLayouts.length; si++) {
    const sysLayout = systemLayouts[si];

    // Wrap to next row
    if (si > 0 && si % systemsPerRow === 0) {
      cursorX = 0;
      cursorY += rowMaxH + LAYOUT.SYS_ROW_GAP;
      rowMaxH = 0;
    }

    // Set system position
    const sysNode = systemNodes.find((n) => n.id === sysLayout.id);
    if (sysNode) {
      sysNode.position = { x: cursorX, y: cursorY };
    }

    // Position modules within system (grid layout)
    const modulesPerRow = Math.min(
      LAYOUT.MODULES_PER_ROW,
      sysLayout.modules.length || 1,
    );
    const maxModW =
      sysLayout.modules.length > 0
        ? Math.max(...sysLayout.modules.map((m) => m.size.w))
        : 0;

    for (let mi = 0; mi < sysLayout.modules.length; mi++) {
      const modLayout = sysLayout.modules[mi];
      const col = mi % modulesPerRow;
      const row = Math.floor(mi / modulesPerRow);

      // Compute y from cumulative row heights
      let yOffset = LAYOUT.SYS_PADDING_TOP;
      for (let r = 0; r < row; r++) {
        yOffset += sysLayout.moduleRowMaxHeights[r] + LAYOUT.MOD_GAP;
      }

      const modNode = moduleNodes.find((n) => n.id === modLayout.id);
      if (modNode) {
        modNode.position = {
          x: LAYOUT.SYS_PADDING_X + col * (maxModW + LAYOUT.MOD_GAP),
          y: yOffset,
        };
      }
    }

    cursorX += sysLayout.size.w + LAYOUT.SYS_GAP;
    rowMaxH = Math.max(rowMaxH, sysLayout.size.h);
  }

  // Merge in correct order: parents before children
  const nodes = [...systemNodes, ...moduleNodes, ...componentNodes];
  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// MiniMap color helper
// ---------------------------------------------------------------------------

function minimapNodeColor(node: Node): string {
  const level = (node.data as FlowNodeData | undefined)?.level;
  switch (level) {
    case "system":
      return "#3B82F6";
    case "module":
      return "#64748B";
    case "component":
      return "#9CA3AF";
    default:
      return "#6366F1";
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ArchitectureFlowView({
  tree,
  onNodeClick,
  className,
}: ArchitectureFlowViewProps) {
  // Build nested layout
  const { initialNodes, flowEdges } = useMemo(() => {
    const { nodes, edges } = buildNestedFlowElements(tree);
    return { initialNodes: nodes, flowEdges: edges };
  }, [tree]);

  // ── Edge visibility state ──
  const [hoveredModuleId, setHoveredModuleId] = useState<string | null>(null);
  const [showAllEdges, setShowAllEdges] = useState(false);

  // Inject onHoverModule callback into moduleGroup nodes (pure build fn can't access state)
  const patchedNodes = useMemo(() => {
    return initialNodes.map((node) => {
      if (node.type === "moduleGroup") {
        return {
          ...node,
          data: {
            ...node.data,
            onHoverModule: setHoveredModuleId,
            moduleId: node.id,
          },
        };
      }
      return node;
    });
  }, [initialNodes]);

  // Compute visible edges based on hover / toggle state
  const visibleEdges = useMemo(() => {
    if (showAllEdges) {
      return flowEdges.map((e) => ({ ...e, hidden: false }));
    }
    if (!hoveredModuleId) {
      return flowEdges; // all hidden by default from build
    }
    return flowEdges.map((e) => ({
      ...e,
      hidden:
        e.source !== hoveredModuleId && e.target !== hoveredModuleId,
    }));
  }, [flowEdges, hoveredModuleId, showAllEdges]);

  const [localNodes, setLocalNodes] = useState<Node[]>(patchedNodes);

  // Sync when tree changes
  useMemo(() => {
    setLocalNodes(patchedNodes);
  }, [patchedNodes]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setLocalNodes((prev) => applyNodeChanges(changes, prev));
  }, []);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const data = node.data as FlowNodeData;
      onNodeClick?.(data.label);
    },
    [onNodeClick],
  );

  // Dynamic height: find bottom-most system node
  const graphHeight = useMemo(() => {
    if (initialNodes.length === 0) return 300;
    let maxBottom = 0;
    for (const node of initialNodes) {
      if (node.type === "systemGroup") {
        const h = (node.style?.height as number) ?? 200;
        maxBottom = Math.max(maxBottom, (node.position?.y ?? 0) + h);
      }
    }
    return Math.max(400, Math.min(800, maxBottom + 80));
  }, [initialNodes]);

  if (tree.length === 0) {
    return (
      <div
        className={cn(
          "text-center py-8 text-muted-foreground text-sm",
          className,
        )}
      >
        尚無子系統架構資料
      </div>
    );
  }

  return (
    <div className={cn("architecture-flow", className)}>
      <style>{flowStyles}</style>
      <div style={{ height: graphHeight }} className="rounded-lg border">
        <ReactFlow
          nodes={localNodes}
          edges={visibleEdges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} size={1} color="hsl(var(--border) / 0.25)" />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={minimapNodeColor}
            maskColor="hsl(var(--background) / 0.7)"
            style={{ height: 80, width: 120 }}
          />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="mt-2 flex gap-4 flex-wrap items-center text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{
              border: "3px solid #3B82F6",
              background: "rgba(59,130,246,0.04)",
            }}
          />
          系統（容器）
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{
              border: "2px solid #64748B",
              background: "rgba(100,116,139,0.04)",
            }}
          />
          模組（容器）
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{
              border: "1.5px dashed #9CA3AF",
              background: "rgba(156,163,175,0.05)",
            }}
          />
          元件
        </span>

        {/* Completeness colour legend */}
        <span className="flex items-center gap-1 ml-2 pl-2 border-l border-muted">
          模組關聯：
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 border-t-2 border-dashed" style={{ borderColor: "#22C55E" }} />
          完整 5-6/6
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 border-t-2 border-dashed" style={{ borderColor: "#EAB308" }} />
          部分 3-4/6
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 border-t-2 border-dashed" style={{ borderColor: "#EF4444" }} />
          薄弱 0-2/6
        </span>

        {/* Toggle button */}
        <button
          type="button"
          onClick={() => setShowAllEdges((prev) => !prev)}
          className="text-[10px] px-2 py-0.5 rounded border hover:bg-muted transition ml-auto"
        >
          {showAllEdges ? "隱藏關聯" : "顯示全部關聯"}
        </button>
      </div>
    </div>
  );
}
