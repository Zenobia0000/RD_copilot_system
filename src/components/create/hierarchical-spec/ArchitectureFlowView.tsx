/**
 * ArchitectureFlowView — interactive system architecture diagram using
 * ReactFlow + dagre, showing the 3-level subsystem topology and interface
 * contracts between coupled modules.
 *
 * Node types:
 *   - SystemFlowNode  (system level)  — large card, thick border, blue accent
 *   - ModuleFlowNode  (module level)  — medium card, thin border, slate accent
 *   - ComponentFlowNode (component)   — small card, dashed border, gray accent
 *
 * Edge types:
 *   - hierarchy — solid gray arrow, parent → child
 *   - interface — dashed animated line, cross-system contract + tooltip
 *
 * @see plans/wave2-verification-checklist-and-architecture-diagram.md §2
 * @see src/components/solution/ConvergenceGraph.tsx (dagre pattern reference)
 */

import { useMemo, useState, useCallback, type CSSProperties } from "react";
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
  MarkerType,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Dagre from "@dagrejs/dagre";
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
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NODE_SIZES: Record<SubsystemLevel, { w: number; h: number }> = {
  system: { w: 220, h: 70 },
  module: { w: 180, h: 56 },
  component: { w: 150, h: 44 },
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
// Custom Node components
// ---------------------------------------------------------------------------

const nodeBaseStyle: CSSProperties = {
  fontFamily: "inherit",
  cursor: "pointer",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
  padding: "8px 12px",
  boxSizing: "border-box",
};

function SystemFlowNode({ data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        ...nodeBaseStyle,
        width: NODE_SIZES.system.w,
        minHeight: NODE_SIZES.system.h,
        borderRadius: 10,
        border: "3px solid #3B82F6",
        background: "rgba(59, 130, 246, 0.08)",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.3 }}>
        {data.label}
      </div>
      {data.code && (
        <div style={{ fontSize: 10, opacity: 0.6, marginTop: 2 }}>
          {data.code}
        </div>
      )}
      <div style={{ fontSize: 9, opacity: 0.5, marginTop: 2 }}>
        {data.childCount > 0 && `${data.childCount} 子模組`}
        {data.childCount > 0 && data.contractCount > 0 && " · "}
        {data.contractCount > 0 && `${data.contractCount} 介面`}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

function ModuleFlowNode({ data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        ...nodeBaseStyle,
        width: NODE_SIZES.module.w,
        minHeight: NODE_SIZES.module.h,
        borderRadius: 8,
        border: "2px solid #64748B",
        background: "rgba(100, 116, 139, 0.06)",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.3 }}>
        {data.label}
      </div>
      {data.contractCount > 0 && (
        <div style={{ fontSize: 9, opacity: 0.5, marginTop: 2 }}>
          {data.contractCount} 介面合約
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

function ComponentFlowNode({ data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div
      style={{
        ...nodeBaseStyle,
        width: NODE_SIZES.component.w,
        minHeight: NODE_SIZES.component.h,
        borderRadius: 6,
        border: "1.5px dashed #9CA3AF",
        background: "rgba(156, 163, 175, 0.05)",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div style={{ fontSize: 11, fontWeight: 500, lineHeight: 1.3 }}>
        {data.label}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = {
  system: SystemFlowNode,
  module: ModuleFlowNode,
  component: ComponentFlowNode,
};

// ---------------------------------------------------------------------------
// Build flow elements from subsystem tree
// ---------------------------------------------------------------------------

interface FlowElements {
  nodes: Node<FlowNodeData>[];
  edges: Edge[];
}

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

function buildFlowElements(tree: SuggestedSubsystem[]): FlowElements {
  const nodes: Node<FlowNodeData>[] = [];
  const edges: Edge[] = [];
  // Track which interface edges we already created (avoid duplicates A→B and B→A)
  const interfaceEdgeSet = new Set<string>();

  // Build a name → id lookup for resolving interface_contracts neighbours
  const nameToId = new Map<string, string>();
  function registerNames(subtree: SuggestedSubsystem[]) {
    for (const s of subtree) {
      nameToId.set(s.name, nodeId(s));
      if (s.children?.length) registerNames(s.children);
    }
  }
  registerNames(tree);

  function walk(
    subtree: SuggestedSubsystem[],
    parentId: string | null,
  ) {
    for (const s of subtree) {
      const id = nodeId(s);
      const contractKeys = Object.keys(s.interface_contracts ?? {});

      nodes.push({
        id,
        type: s.level,
        position: { x: 0, y: 0 }, // dagre will reposition
        data: {
          label: s.name,
          code: s.concept_origin_code ?? "",
          level: s.level,
          childCount: s.children?.length ?? 0,
          contractCount: contractKeys.length,
        },
      });

      // Hierarchy edge: parent → child
      if (parentId) {
        edges.push({
          id: `h-${parentId}-${id}`,
          source: parentId,
          target: id,
          type: "default",
          style: { stroke: "#9CA3AF", strokeWidth: 1.5 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: "#9CA3AF",
            width: 12,
            height: 12,
          },
        });
      }

      // Interface contract edges (dashed, animated)
      if (s.interface_contracts) {
        for (const [neighbourName, contract] of Object.entries(
          s.interface_contracts,
        )) {
          const targetId = nameToId.get(neighbourName);
          if (!targetId) continue;

          // Deduplicate: canonical key is sorted pair
          const canonKey = [id, targetId].sort().join("↔");
          if (interfaceEdgeSet.has(canonKey)) continue;
          interfaceEdgeSet.add(canonKey);

          edges.push({
            id: `i-${id}-${targetId}`,
            source: id,
            target: targetId,
            animated: true,
            style: {
              stroke: "#6366F1",
              strokeWidth: 1.5,
              strokeDasharray: "6 3",
            },
            label: contractSummaryLabel(contract),
            labelStyle: { fontSize: 9, fill: "#6366F1", fontWeight: 600 },
            labelBgStyle: {
              fill: "rgba(255,255,255,0.85)",
              stroke: "#6366F1",
              strokeWidth: 0.5,
              borderRadius: 3,
            },
            // Store tooltip data in edge data for potential use
            data: {
              tooltip: contractTooltip(s.name, neighbourName, contract),
            },
          });
        }
      }

      // Recurse children
      if (s.children?.length) {
        walk(s.children, id);
      }
    }
  }

  walk(tree, null);
  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// Dagre layout
// ---------------------------------------------------------------------------

function layoutWithDagre(nodes: Node[], edges: Edge[]): Node[] {
  if (nodes.length === 0) return nodes;

  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 40, ranksep: 60 });

  for (const node of nodes) {
    const level = (node.data as FlowNodeData).level ?? "module";
    const size = NODE_SIZES[level] ?? NODE_SIZES.module;
    g.setNode(node.id, { width: size.w, height: size.h });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  Dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    const level = (node.data as FlowNodeData).level ?? "module";
    const size = NODE_SIZES[level] ?? NODE_SIZES.module;
    return {
      ...node,
      position: { x: pos.x - size.w / 2, y: pos.y - size.h / 2 },
    };
  });
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
  // Build + layout flow elements
  const { initialNodes, flowEdges } = useMemo(() => {
    const { nodes: rawNodes, edges } = buildFlowElements(tree);
    const positioned = layoutWithDagre(rawNodes, edges);
    return { initialNodes: positioned, flowEdges: edges };
  }, [tree]);

  const [localNodes, setLocalNodes] = useState<Node[]>(initialNodes);

  // Sync when tree changes
  useMemo(() => {
    setLocalNodes(initialNodes);
  }, [initialNodes]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setLocalNodes((prev) => applyNodeChanges(changes, prev));
    },
    [],
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const data = node.data as FlowNodeData;
      onNodeClick?.(data.label);
    },
    [onNodeClick],
  );

  // Dynamic height based on node count
  const graphHeight = Math.max(300, Math.min(600, localNodes.length * 60 + 120));

  if (tree.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground text-sm", className)}>
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
          edges={flowEdges}
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
      <div className="mt-2 flex gap-4 flex-wrap text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{ border: "2px solid #3B82F6", background: "rgba(59,130,246,0.08)" }}
          />
          系統
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{ border: "1.5px solid #64748B", background: "rgba(100,116,139,0.06)" }}
          />
          模組
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{ border: "1.5px dashed #9CA3AF", background: "rgba(156,163,175,0.05)" }}
          />
          元件
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 border-t border-gray-400" />
          階層
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 border-t border-dashed border-indigo-500" />
          介面合約
        </span>
      </div>
    </div>
  );
}
