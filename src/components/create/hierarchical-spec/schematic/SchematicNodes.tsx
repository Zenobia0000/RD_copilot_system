/**
 * SchematicNodes — ReactFlow 自定義節點元件
 *
 * 三種節點類型：
 *  - SystemGroupNode: 虛線外框 system 容器
 *  - ModuleBlockNode: 實線模組區塊
 *  - ComponentChipNode: 小型 component chip
 *
 * @see plans/structural-schematic-view.md §6.4
 */

import { memo } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { SchematicBlock, RiskLevel } from "./types";
import { RISK_LEVEL_COLORS } from "./types";

// ---------------------------------------------------------------------------
// Node data interfaces
// ---------------------------------------------------------------------------

interface SystemNodeData {
  block: SchematicBlock;
  width: number;
  height: number;
  [key: string]: unknown;
}

interface ModuleNodeData {
  block: SchematicBlock;
  width: number;
  height: number;
  [key: string]: unknown;
}

interface ComponentNodeData {
  block: SchematicBlock;
  width: number;
  height: number;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// SystemGroupNode
// ---------------------------------------------------------------------------

/**
 * System-level group node: 虛線外框，標題列含 system name + 模組計數 badge
 */
export const SystemGroupNode = memo(function SystemGroupNode({
  data,
}: NodeProps<Node<SystemNodeData>>) {
  const { block, width, height } = data;

  return (
    <div
      className="rounded-xl border-2 border-dashed border-blue-300/60 bg-blue-50/20 dark:bg-blue-950/10"
      style={{ width, height, position: "relative" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2">
        <span className="text-sm font-semibold text-blue-700 dark:text-blue-400 truncate">
          {block.name}
        </span>
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 shrink-0">
          {block.childCount} 模組
        </Badge>
        <RiskBadge level={block.riskLevel} size="sm" />
      </div>

      {/* Handles for edges */}
      <Handle type="source" position={Position.Right} className="!bg-blue-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Left} className="!bg-blue-400 !w-2 !h-2" />
    </div>
  );
});

// ---------------------------------------------------------------------------
// ModuleBlockNode
// ---------------------------------------------------------------------------

/**
 * Module-level block: 實線外框、顯示 name、bbox 摘要、信心度色條、風險徽章
 */
export const ModuleBlockNode = memo(function ModuleBlockNode({
  data,
}: NodeProps<Node<ModuleNodeData>>) {
  const { block, width, height } = data;
  const confPercent = Math.round(block.avgConfidence * 100);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "rounded-lg border bg-card shadow-sm cursor-pointer transition-all",
            "hover:shadow-md hover:border-primary/50",
            block.riskLevel === "high" && "border-red-400/60",
            block.riskLevel === "medium" && "border-amber-400/60",
            block.riskLevel === "low" && "border-green-400/40",
            block.riskLevel === "none" && "border-border",
          )}
          style={{ width, height, position: "relative" }}
        >
          {/* Confidence bar at top */}
          <div className="absolute top-0 left-0 right-0 h-1 rounded-t-lg overflow-hidden bg-muted">
            <div
              className={cn(
                "h-full transition-all",
                confPercent >= 65 ? "bg-green-500" : confPercent >= 35 ? "bg-amber-500" : "bg-red-500",
              )}
              style={{ width: `${confPercent}%` }}
            />
          </div>

          <div className="p-2.5 pt-3 space-y-1.5">
            {/* Name + risk badge row */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold truncate flex-1">{block.name}</span>
              <RiskBadge level={block.riskLevel} size="xs" />
            </div>

            {/* BBox summary */}
            {block.bboxSummary && (
              <p className="text-[10px] text-muted-foreground font-mono truncate">
                📦 {block.bboxSummary}
              </p>
            )}

            {/* Stats row */}
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <span>{block.specCount} specs</span>
              {block.verificationCount > 0 && (
                <span className="text-green-600">✓{block.verificationCount}</span>
              )}
              {block.childCount > 0 && (
                <span className="text-blue-500">{block.childCount} comp</span>
              )}
            </div>
          </div>

          {/* Handles */}
          <Handle type="source" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />
          <Handle type="target" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
          <Handle type="source" position={Position.Bottom} id="bottom" className="!bg-slate-400 !w-2 !h-2" />
          <Handle type="target" position={Position.Top} id="top" className="!bg-slate-400 !w-2 !h-2" />
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-[260px]">
        <p className="font-semibold">{block.name}</p>
        {block.specTreeNodeRef?.reason && (
          <p className="text-xs text-muted-foreground mt-1">{block.specTreeNodeRef.reason}</p>
        )}
        <p className="text-xs mt-1">
          信心度: {confPercent}% · Specs: {block.specCount}
          {block.massG != null && ` · 質量: ${block.massG}g`}
        </p>
      </TooltipContent>
    </Tooltip>
  );
});

// ---------------------------------------------------------------------------
// ComponentChipNode
// ---------------------------------------------------------------------------

/**
 * Component-level chip: 小型顯示 name + 信心度色點
 */
export const ComponentChipNode = memo(function ComponentChipNode({
  data,
}: NodeProps<Node<ComponentNodeData>>) {
  const { block, width, height } = data;
  const confPercent = Math.round(block.avgConfidence * 100);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "rounded-md border border-dashed bg-muted/30 cursor-pointer",
            "hover:bg-muted/60 hover:border-primary/30 transition-all",
            "flex items-center gap-1.5 px-2 py-1",
          )}
          style={{ width, height }}
        >
          {/* Confidence dot */}
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{
              backgroundColor:
                confPercent >= 65 ? "#22c55e" : confPercent >= 35 ? "#f59e0b" : "#ef4444",
            }}
          />
          <span className="text-[10px] truncate">{block.name}</span>

          {/* Handles */}
          <Handle type="source" position={Position.Right} className="!bg-gray-300 !w-1.5 !h-1.5" />
          <Handle type="target" position={Position.Left} className="!bg-gray-300 !w-1.5 !h-1.5" />
        </div>
      </TooltipTrigger>
      <TooltipContent side="top">
        <p className="text-xs font-semibold">{block.name}</p>
        <p className="text-[10px] text-muted-foreground">
          信心度: {confPercent}% · Specs: {block.specCount}
        </p>
      </TooltipContent>
    </Tooltip>
  );
});

// ---------------------------------------------------------------------------
// Shared: Risk badge
// ---------------------------------------------------------------------------

function RiskBadge({ level, size = "xs" }: { level: RiskLevel; size?: "xs" | "sm" }) {
  if (level === "none") return null;

  const labels: Record<RiskLevel, string> = {
    high: "⚠ 高風險",
    medium: "⚡ 中風險",
    low: "✓ 低風險",
    none: "",
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        "shrink-0 border",
        size === "xs" ? "text-[9px] px-1 py-0 h-3.5" : "text-[10px] px-1.5 py-0 h-4",
      )}
      style={{
        borderColor: RISK_LEVEL_COLORS[level],
        color: RISK_LEVEL_COLORS[level],
      }}
    >
      {labels[level]}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Export node types map for ReactFlow
// ---------------------------------------------------------------------------

export const schematicNodeTypes = {
  schematicSystem: SystemGroupNode,
  schematicModule: ModuleBlockNode,
  schematicComponent: ComponentChipNode,
} as const;
