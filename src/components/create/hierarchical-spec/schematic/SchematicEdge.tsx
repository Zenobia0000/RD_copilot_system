/**
 * SchematicEdge — 自訂貝茲曲線邊元件
 *
 * 解決原本 smoothstep 在同 Y 水平時退化成直線、
 * 以及多條平行邊完全重疊的問題。
 *
 * 功能：
 *  - 貝茲曲線路徑（永遠呈現弧度，不會退化直線）
 *  - 平行邊偏移（相同源-目標對的多條邊沿垂直方向分散）
 *  - 方向箭頭 (markerEnd)
 *  - 動畫閃爍 (criticality=high 時由 ReactFlow animated 處理)
 */

import {
  BaseEdge,
  getBezierPath,
  type EdgeProps,
  type Edge,
} from "@xyflow/react";
import type { SchematicRelation } from "./types";

// ---------------------------------------------------------------------------
// Edge data interface
// ---------------------------------------------------------------------------

export interface SchematicEdgeData {
  relation: SchematicRelation;
  /** Perpendicular pixel offset for parallel edge separation */
  offset: number;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SchematicEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  data,
  label,
  labelStyle,
  labelBgStyle,
  markerEnd,
}: EdgeProps<Edge<SchematicEdgeData>>) {
  const offset = data?.offset ?? 0;

  // ── Perpendicular offset for parallel edge separation ──
  // Calculate perpendicular direction to the straight line between source → target
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  // Perpendicular unit vector (rotate 90° counter-clockwise)
  const px = -dy / len;
  const py = dx / len;

  // Shift both endpoints perpendicular to the connection line
  const osx = sourceX + px * offset;
  const osy = sourceY + py * offset;
  const otx = targetX + px * offset;
  const oty = targetY + py * offset;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: osx,
    sourceY: osy,
    targetX: otx,
    targetY: oty,
    sourcePosition,
    targetPosition,
    curvature: 0.3,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={style}
      markerEnd={markerEnd}
      label={label}
      labelStyle={labelStyle}
      labelBgStyle={labelBgStyle}
      labelX={labelX}
      labelY={labelY}
      labelShowBg={!!label}
      labelBgPadding={[4, 2]}
      labelBgBorderRadius={3}
    />
  );
}
