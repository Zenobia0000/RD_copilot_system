/**
 * SystemSpecCard — top-level card for a system node in the hierarchy.
 *
 * Shows:
 * - System name + aggregated stats bar (total specs, avg confidence gauge,
 *   verification count badge)
 * - Collapsible body with ModuleSpecCard children
 * - Default: expanded (per interaction behaviour table in the plan)
 *
 * @see plans/hierarchical-spec-view.md §3 元件架構, §8 互動行為
 */

import { useState } from "react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  ChevronDown,
  AlertTriangle,
  Server,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

import type { SpecTreeNode } from "./buildSpecTree";
import { ModuleSpecCard } from "./ModuleSpecCard";
import { pctStr } from "../spec-shared";

export interface SystemSpecCardProps {
  node: SpecTreeNode;
  /** When true, starts in collapsed state. Default is expanded. */
  defaultOpen?: boolean;
}

/** Colour helper based on confidence value 0-1. */
function confColor(v: number): string {
  if (v >= 0.7) return "text-green-600";
  if (v >= 0.4) return "text-amber-600";
  return "text-red-600";
}

function confBg(v: number): string {
  if (v >= 0.7) return "bg-green-500";
  if (v >= 0.4) return "bg-amber-500";
  return "bg-red-500";
}

/**
 * System-level card — the outermost accordion for each of the ~8 root
 * subsystem nodes.
 */
export function SystemSpecCard({ node, defaultOpen = true }: SystemSpecCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const { aggregated, children } = node;

  const confPct = Math.round(aggregated.avgConfidence * 100);
  const allVerified = aggregated.verificationCount === 0;

  return (
    <Card className="overflow-hidden">
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader
            className={cn(
              "cursor-pointer select-none py-3 px-4",
              "hover:bg-muted/30 transition-colors",
            )}
          >
            <div className="flex items-center gap-3 w-full">
              {/* Icon */}
              <Server className="w-5 h-5 text-indigo-500 shrink-0" />

              {/* System name */}
              <div className="flex flex-col min-w-0">
                <span className="font-semibold text-sm max-h-[3.5rem] overflow-y-auto">
                  {node.name}
                </span>
                {node.reason && (
                  <span className="text-[11px] text-muted-foreground max-h-[3rem] overflow-y-auto block">
                    {node.reason}
                  </span>
                )}
              </div>

              {/* Aggregated stats bar (right aligned) */}
              <div className="flex items-center gap-3 ml-auto shrink-0">
                {/* Total spec count */}
                <div className="flex items-center gap-1">
                  <BarChart3 className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-xs font-mono">
                    {aggregated.totalSpecs}
                  </span>
                  <span className="text-[10px] text-muted-foreground">specs</span>
                </div>

                {/* Confidence gauge */}
                <div className="flex items-center gap-1.5 min-w-[80px]">
                  <Progress
                    value={confPct}
                    className="h-1.5 w-14"
                    // The progress bar indicator colour
                    style={
                      {
                        "--progress-foreground": confBg(aggregated.avgConfidence),
                      } as React.CSSProperties
                    }
                  />
                  <span
                    className={cn(
                      "text-xs font-mono font-medium",
                      confColor(aggregated.avgConfidence),
                    )}
                  >
                    {pctStr(aggregated.avgConfidence)}
                  </span>
                </div>

                {/* Verification status */}
                {allVerified ? (
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1.5 py-0 h-5 text-green-600 border-green-300"
                  >
                    <CheckCircle2 className="w-3 h-3 mr-0.5" />
                    已驗證
                  </Badge>
                ) : (
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1.5 py-0 h-5 text-red-600 border-red-300"
                  >
                    <AlertTriangle className="w-3 h-3 mr-0.5" />
                    {aggregated.verificationCount} 待驗證
                  </Badge>
                )}

                {/* Module count */}
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
                  {children.length} 模組
                </Badge>

                {/* Collapse chevron */}
                <ChevronDown
                  className={cn(
                    "w-4 h-4 text-muted-foreground transition-transform",
                    !open && "-rotate-90",
                  )}
                />
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 pb-3 px-4 space-y-1">
            {/* Related contradictions */}
            {node.related_contradictions.length > 0 && (
              <div className="flex items-center gap-1 flex-wrap mb-2">
                <span className="text-[10px] text-muted-foreground">
                  矛盾關聯:
                </span>
                {node.related_contradictions.map((c) => (
                  <Badge
                    key={c}
                    variant="outline"
                    className="text-[10px] px-1.5 py-0 h-4"
                  >
                    {c}
                  </Badge>
                ))}
              </div>
            )}

            {/* Module children */}
            {children.length > 0 ? (
              <div className="space-y-1">
                {children.map((child) => (
                  <ModuleSpecCard key={child.name} node={child} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic py-2">
                此系統無子模組
              </p>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
