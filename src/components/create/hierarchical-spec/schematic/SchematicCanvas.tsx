/**
 * SchematicCanvas — ReactFlow 畫布元件
 *
 * 負責渲染結構示意圖的 ReactFlow 畫布，包含：
 *  - 自定義節點類型 (system / module / component)
 *  - MiniMap + Controls + Background
 *  - fitView 預設啟用
 *  - 節點點擊回傳 SchematicBlock 給上層
 *
 * @see plans/structural-schematic-view.md §6.3
 */

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  type Node,
  type Edge,
  type EdgeTypes,
  type NodeChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { cn } from "@/lib/utils";
import type { SchematicBlock, SchematicBlockLevel } from "./types";
import { RELATION_TYPE_COLORS } from "./types";
import { schematicNodeTypes } from "./SchematicNodes";
import { SchematicEdge } from "./SchematicEdge";

// ---------------------------------------------------------------------------
// Edge type registration
// ---------------------------------------------------------------------------

const schematicEdgeTypes: EdgeTypes = {
  schematicEdge: SchematicEdge,
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SchematicCanvasProps {
  /** Pre-computed layout nodes from computeSchematicLayout */
  nodes: Node[];
  /** Pre-computed layout edges from computeSchematicLayout */
  edges: Edge[];
  /** Callback when user clicks a block node */
  onBlockClick?: (block: SchematicBlock) => void;
  /** Optional search term to highlight matching nodes */
  searchTerm?: string;
  /** Additional CSS classes */
  className?: string;
}

// ---------------------------------------------------------------------------
// MiniMap color helper
// ---------------------------------------------------------------------------

function minimapNodeColor(node: Node): string {
  const level = (node.data as { block?: SchematicBlock } | undefined)?.block
    ?.level;
  switch (level) {
    case "system":
      return "#3B82F6";
    case "module":
      return "#6366F1";
    case "component":
      return "#9CA3AF";
    default:
      return "#94A3B8";
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SchematicCanvas({
  nodes: layoutNodes,
  edges: layoutEdges,
  onBlockClick,
  searchTerm,
  className,
}: SchematicCanvasProps) {
  // ── Local node state for dragging ──
  const [localNodes, setLocalNodes] = useState<Node[]>(layoutNodes);

  // Sync when layout changes (filter/data change)
  useMemo(() => {
    setLocalNodes(layoutNodes);
  }, [layoutNodes]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setLocalNodes((prev) => applyNodeChanges(changes, prev));
  }, []);

  // ── Search highlight ──
  const highlightedNodes = useMemo(() => {
    if (!searchTerm || searchTerm.trim().length === 0) return localNodes;

    const term = searchTerm.toLowerCase().trim();
    return localNodes.map((node) => {
      const block = (node.data as { block?: SchematicBlock } | undefined)
        ?.block;
      if (!block) return node;

      const isMatch =
        block.name.toLowerCase().includes(term) ||
        block.id.toLowerCase().includes(term);

      return {
        ...node,
        style: {
          ...node.style,
          // Matching nodes get highlighted border, non-matching get dimmed
          opacity: isMatch ? 1 : 0.35,
          transition: "opacity 0.2s ease",
        },
      };
    });
  }, [localNodes, searchTerm]);

  // ── Node click handler ──
  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const block = (node.data as { block?: SchematicBlock } | undefined)
        ?.block;
      if (block && onBlockClick) {
        onBlockClick(block);
      }
    },
    [onBlockClick],
  );

  // ── Dynamic height ──
  const graphHeight = useMemo(() => {
    if (layoutNodes.length === 0) return 400;
    let maxBottom = 0;
    for (const node of layoutNodes) {
      const h =
        typeof node.style?.height === "number"
          ? node.style.height
          : typeof node.measured?.height === "number"
            ? node.measured.height
            : 100;
      maxBottom = Math.max(maxBottom, (node.position?.y ?? 0) + h);
    }
    return Math.max(400, Math.min(900, maxBottom + 100));
  }, [layoutNodes]);

  // ── Empty state ──
  if (layoutNodes.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center py-16 text-muted-foreground text-sm",
          className,
        )}
      >
        尚無結構示意圖資料，請先產生子系統建議
      </div>
    );
  }

  return (
    <div
      className={cn("schematic-canvas w-full", className)}
      style={{ height: graphHeight }}
    >
      <ReactFlow
        nodes={highlightedNodes}
        edges={layoutEdges}
        nodeTypes={schematicNodeTypes}
        edgeTypes={schematicEdgeTypes}
        onNodesChange={onNodesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.15}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          gap={20}
          size={1}
          color="hsl(var(--border) / 0.2)"
        />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={minimapNodeColor}
          maskColor="hsl(var(--background) / 0.7)"
          style={{ height: 80, width: 120 }}
        />
      </ReactFlow>

      {/* Legend */}
      <div className="mt-2 flex gap-3 flex-wrap items-center text-[10px] text-muted-foreground px-1">
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{
              border: "2px dashed #3B82F6",
              background: "rgba(59,130,246,0.04)",
            }}
          />
          系統
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded"
            style={{
              border: "2px solid #6366F1",
              background: "rgba(99,102,241,0.04)",
            }}
          />
          模組
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3 h-3 rounded-full"
            style={{
              border: "1.5px solid #9CA3AF",
              background: "rgba(156,163,175,0.06)",
            }}
          />
          元件
        </span>

        <span className="border-l border-muted pl-2 ml-1 flex items-center gap-1">
          關係：
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-4 border-t-2 border-dashed"
            style={{ borderColor: RELATION_TYPE_COLORS.signal }}
          />
          信號
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-4 border-t-2 border-dashed"
            style={{ borderColor: RELATION_TYPE_COLORS.thermal }}
          />
          熱傳
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-4 border-t-2"
            style={{ borderColor: RELATION_TYPE_COLORS.load }}
          />
          載荷
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-4 border-t-2 border-dashed"
            style={{ borderColor: RELATION_TYPE_COLORS.envelope }}
          />
          包絡
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-4 border-t-2 border-dotted"
            style={{ borderColor: RELATION_TYPE_COLORS.other }}
          />
          其他
        </span>
      </div>
    </div>
  );
}
