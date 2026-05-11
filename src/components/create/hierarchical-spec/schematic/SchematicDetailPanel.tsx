/**
 * SchematicDetailPanel — 結構示意圖右側詳情面板
 *
 * 當使用者點擊某個區塊節點時，此面板展開顯示：
 *  - 所有連接的 InterfaceContract 摘要
 *  - 該節點對應的 SubsystemDatasheet 完整規格
 *  - 關閉按鈕回到摺疊狀態
 *
 * @see plans/structural-schematic-view.md §6.6
 */

import { useMemo } from "react";
import { X, Link2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import type { SchematicBlock, SchematicRelation } from "./types";
import { RELATION_TYPE_LABELS, RELATION_TYPE_COLORS, RISK_LEVEL_COLORS } from "./types";
import { SubsystemDatasheet } from "../SubsystemDatasheet";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SchematicDetailPanelProps {
  /** Currently selected block */
  block: SchematicBlock;
  /** All relations in the current model */
  relations: SchematicRelation[];
  /** Close callback */
  onClose: () => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function riskLabel(level: string): string {
  switch (level) {
    case "high":
      return "高風險";
    case "medium":
      return "中風險";
    case "low":
      return "低風險";
    default:
      return "無";
  }
}

function criticalityLabel(c: string): string {
  switch (c) {
    case "high":
      return "高";
    case "medium":
      return "中";
    case "low":
      return "低";
    default:
      return c;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SchematicDetailPanel({
  block,
  relations,
  onClose,
  className,
}: SchematicDetailPanelProps) {
  // Find relations connected to this block
  const connectedRelations = useMemo(() => {
    return relations.filter(
      (r) => r.sourceId === block.id || r.targetId === block.id,
    );
  }, [relations, block.id]);

  return (
    <ScrollArea className={cn("h-full", className)}>
      <div className="space-y-4 p-3">
        {/* Header with close button */}
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <h3 className="font-semibold text-sm truncate">{block.name}</h3>
            <div className="flex items-center gap-1.5 flex-wrap">
              <Badge variant="outline" className="text-[10px] h-5">
                {block.level === "system"
                  ? "系統"
                  : block.level === "module"
                    ? "模組"
                    : "元件"}
              </Badge>
              <Badge
                variant="outline"
                className="text-[10px] h-5"
                style={{
                  borderColor: RISK_LEVEL_COLORS[block.riskLevel],
                  color: RISK_LEVEL_COLORS[block.riskLevel],
                }}
              >
                {riskLabel(block.riskLevel)}
              </Badge>
              <Badge variant="outline" className="text-[10px] h-5">
                {block.specCount} 規格
              </Badge>
              {block.verificationCount > 0 && (
                <Badge
                  variant="outline"
                  className="text-[10px] h-5 text-red-600 border-red-300"
                >
                  {block.verificationCount} 待驗證
                </Badge>
              )}
            </div>
          </div>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6 shrink-0"
            onClick={onClose}
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          {block.bboxSummary && (
            <div className="bg-muted/30 rounded px-2 py-1.5">
              <span className="text-muted-foreground">包絡：</span>
              <span className="font-mono">{block.bboxSummary}</span>
            </div>
          )}
          {block.massG != null && (
            <div className="bg-muted/30 rounded px-2 py-1.5">
              <span className="text-muted-foreground">質量：</span>
              <span className="font-mono">{block.massG}g</span>
            </div>
          )}
          <div className="bg-muted/30 rounded px-2 py-1.5">
            <span className="text-muted-foreground">信心度：</span>
            <span className="font-mono">
              {(block.avgConfidence * 100).toFixed(0)}%
            </span>
          </div>
          {block.childCount > 0 && (
            <div className="bg-muted/30 rounded px-2 py-1.5">
              <span className="text-muted-foreground">子元件：</span>
              <span className="font-mono">{block.childCount}</span>
            </div>
          )}
        </div>

        {/* Connected relations / interface contracts */}
        {connectedRelations.length > 0 && (
          <Card className="border-dashed">
            <CardHeader className="pb-2 px-3 pt-3">
              <CardTitle className="text-xs font-medium flex items-center gap-1.5">
                <Link2 className="w-3.5 h-3.5" />
                連接關係 ({connectedRelations.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {connectedRelations.map((rel) => {
                const peer =
                  rel.sourceId === block.id ? rel.targetId : rel.sourceId;
                return (
                  <div
                    key={rel.id}
                    className="flex items-start gap-2 text-[11px] rounded bg-muted/20 px-2 py-1.5"
                  >
                    <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <div className="flex items-center gap-1 flex-wrap">
                        <span className="font-medium truncate">{peer}</span>
                        {rel.isCrossModule && (
                          <Badge
                            variant="outline"
                            className="text-[9px] h-4 px-1"
                          >
                            跨模組
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1 flex-wrap">
                        {rel.types.map((t) => (
                          <span
                            key={t}
                            className="inline-flex items-center gap-0.5"
                          >
                            <span
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: RELATION_TYPE_COLORS[t],
                              }}
                            />
                            <span className="text-muted-foreground">
                              {RELATION_TYPE_LABELS[t]}
                            </span>
                          </span>
                        ))}
                        <span className="text-muted-foreground">
                          · 嚴重度: {criticalityLabel(rel.criticality)}
                        </span>
                      </div>
                      {rel.label && (
                        <p className="text-muted-foreground leading-tight">
                          {rel.label}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* SubsystemDatasheet — full spec rendering */}
        <SubsystemDatasheet node={block.specTreeNodeRef} />
      </div>
    </ScrollArea>
  );
}
