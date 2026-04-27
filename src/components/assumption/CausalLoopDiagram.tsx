import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { CLDNode, CLDEdge, CLDLoop } from "@/types/assumption";
import { Download, ZoomIn, ZoomOut, Star } from "lucide-react";

interface CausalLoopDiagramProps {
  nodes: CLDNode[];
  edges: CLDEdge[];
  loops: CLDLoop[];
  selectedAssumptionId?: string | null;
  onNodeClick: (assumptionId: string | undefined) => void;
}

export function CausalLoopDiagram({ nodes, edges, loops, selectedAssumptionId, onNodeClick }: CausalLoopDiagramProps) {
  const [scale, setScale] = useState(1);

  const svgWidth = 620;
  const svgHeight = 320;

  // Find highlighted nodes based on selected assumption
  const highlightedNodeIds = useMemo(() => {
    if (!selectedAssumptionId) return new Set<string>();
    const directNode = nodes.find((n) => n.assumptionId === selectedAssumptionId);
    if (!directNode) return new Set<string>();
    const ids = new Set<string>([directNode.id]);
    // Add connected nodes
    edges.forEach((e) => {
      if (e.from === directNode.id) ids.add(e.to);
      if (e.to === directNode.id) ids.add(e.from);
    });
    return ids;
  }, [selectedAssumptionId, nodes, edges]);

  if (nodes.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">因果迴路圖 (CLD)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48 text-sm text-muted-foreground border-2 border-dashed rounded-lg">
            新增假設以開始建模
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-base">因果迴路圖 (CLD)</CardTitle>
          <div className="flex items-center gap-1">
            {/* Loop badges */}
            {loops.map((loop) => (
              <Badge key={loop.id} variant={loop.type === "R" ? "destructive" : "secondary"} className="text-[10px]">
                {loop.type === "R" ? "增強迴路" : "平衡迴路"} {loop.label}
              </Badge>
            ))}
            <div className="flex gap-1 ml-2">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setScale((s) => Math.min(s + 0.2, 2))}>
                <ZoomIn className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setScale((s) => Math.max(s - 0.2, 0.5))}>
                <ZoomOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto rounded-lg border bg-muted/20" style={{ maxHeight: 380 }}>
          <svg
            width={svgWidth * scale}
            height={svgHeight * scale}
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full"
          >
            <defs>
              <marker id="arrow-pos" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                <path d="M0,0 L8,3 L0,6" fill="hsl(var(--primary))" />
              </marker>
              <marker id="arrow-neg" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                <path d="M0,0 L8,3 L0,6" fill="hsl(var(--destructive))" />
              </marker>
            </defs>

            {/* Edges */}
            {edges.map((edge) => {
              const fromNode = nodes.find((n) => n.id === edge.from);
              const toNode = nodes.find((n) => n.id === edge.to);
              if (!fromNode || !toNode) return null;

              const isHighlighted = highlightedNodeIds.has(edge.from) && highlightedNodeIds.has(edge.to);
              const midX = (fromNode.x + toNode.x) / 2;
              const midY = (fromNode.y + toNode.y) / 2 - 15;

              return (
                <g key={edge.id}>
                  <line
                    x1={fromNode.x} y1={fromNode.y}
                    x2={toNode.x} y2={toNode.y}
                    stroke={edge.polarity === "+" ? "hsl(var(--primary))" : "hsl(var(--destructive))"}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeOpacity={isHighlighted || !selectedAssumptionId ? 1 : 0.3}
                    markerEnd={edge.polarity === "+" ? "url(#arrow-pos)" : "url(#arrow-neg)"}
                  />
                  <text x={midX} y={midY} textAnchor="middle" fontSize="12" fontWeight="bold"
                    fill={edge.polarity === "+" ? "hsl(var(--primary))" : "hsl(var(--destructive))"}
                    opacity={isHighlighted || !selectedAssumptionId ? 1 : 0.3}
                  >
                    {edge.polarity}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {nodes.map((node) => {
              const isSelected = node.assumptionId === selectedAssumptionId;
              const isHighlighted = highlightedNodeIds.has(node.id);
              const dimmed = selectedAssumptionId && !isHighlighted;

              return (
                <g
                  key={node.id}
                  className="cursor-pointer"
                  onClick={() => onNodeClick(node.assumptionId)}
                  opacity={dimmed ? 0.3 : 1}
                >
                  <rect
                    x={node.x - 48} y={node.y - 18}
                    width={96} height={36} rx={6}
                    fill={isSelected ? "hsl(var(--primary))" : node.type === "assumption" ? "hsl(var(--card))" : "hsl(var(--muted))"}
                    stroke={isSelected ? "hsl(var(--primary))" : node.isLeverage ? "hsl(var(--accent))" : "hsl(var(--border))"}
                    strokeWidth={isSelected ? 2 : node.isLeverage ? 2 : 1}
                  />
                  <text
                    x={node.x} y={node.y + 4}
                    textAnchor="middle" fontSize="11"
                    fill={isSelected ? "hsl(var(--primary-foreground))" : "hsl(var(--foreground))"}
                    fontWeight={isSelected ? 600 : 400}
                  >
                    {node.label.length > 8 ? node.label.slice(0, 8) + "…" : node.label}
                  </text>
                  {node.isLeverage && (
                    <circle cx={node.x + 40} cy={node.y - 12} r={6} fill="hsl(var(--accent))" />
                  )}
                </g>
              );
            })}
          </svg>
        </div>
        <div className="flex items-center gap-4 mt-2 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1"><span className="inline-block w-3 h-0.5 bg-primary" /> + 正反饋</span>
          <span className="flex items-center gap-1"><span className="inline-block w-3 h-0.5 bg-destructive" /> − 負反饋</span>
          <span className="flex items-center gap-1"><Star className="h-3 w-3 text-accent" /> 槓桿點</span>
        </div>
      </CardContent>
    </Card>
  );
}
