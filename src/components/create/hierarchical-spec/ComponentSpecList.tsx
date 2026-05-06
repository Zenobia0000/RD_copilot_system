/**
 * ComponentSpecList — renders component-level specs as inline compact badges.
 *
 * Component level is the leaf of the 3-level hierarchy. Shows a compact row
 * with key spec values (field: value unit) as small badges, plus a confidence
 * indicator. Expandable to full SpecRow detail on click.
 *
 * @see plans/hierarchical-spec-view.md §6 ComponentSpecList
 */

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { ChevronRight, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

import type { SpecTreeNode } from "./buildSpecTree";
import { ConfidenceBadge, CategoryGroup, groupByCategory, pctStr } from "../spec-shared";

export interface ComponentSpecListProps {
  node: SpecTreeNode;
}

/**
 * Inline component-level spec display.
 *
 * Default: compact single-line with key spec badges.
 * Expanded: full CategoryGroup breakdown.
 */
export function ComponentSpecList({ node }: ComponentSpecListProps) {
  const [expanded, setExpanded] = useState(false);
  const { draft, aggregated } = node;

  if (!draft || draft.specs.length === 0) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground py-1 pl-2">
        <span className="font-medium">{node.name}</span>
        <span className="italic">無規格資料</span>
      </div>
    );
  }

  const grouped = groupByCategory(draft.specs);

  // Pick up to 3 key specs for the compact view
  const keySpecs = draft.specs.slice(0, 3);

  return (
    <div className="space-y-1">
      {/* Compact row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs w-full text-left hover:bg-muted/30 rounded px-2 py-1.5 transition-colors group"
      >
        <ChevronRight
          className={cn(
            "w-3 h-3 text-muted-foreground transition-transform shrink-0",
            expanded && "rotate-90",
          )}
        />

        {/* Component name */}
        <span className="font-medium text-foreground min-w-[100px] shrink-0">
          {node.name}
        </span>

        {/* Key spec badges (compact) */}
        <div className="flex items-center gap-1 flex-wrap">
          {keySpecs.map((s) => (
            <Badge
              key={s.field_name}
              variant="secondary"
              className="text-[10px] px-1.5 py-0 h-4 font-mono"
            >
              {s.field_name.replace(/_/g, " ")}:{" "}
              {typeof s.value === "number"
                ? s.value
                : typeof s.value === "string"
                  ? s.value
                  : "…"}
              {s.unit ? ` ${s.unit}` : ""}
            </Badge>
          ))}
          {draft.specs.length > 3 && (
            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">
              +{draft.specs.length - 3}
            </Badge>
          )}
        </div>

        {/* Confidence */}
        <span className="ml-auto flex items-center gap-1 shrink-0">
          <span
            className={cn(
              "text-[10px] font-mono font-medium",
              aggregated.avgConfidence >= 0.7
                ? "text-green-600"
                : aggregated.avgConfidence >= 0.4
                  ? "text-amber-600"
                  : "text-red-600",
            )}
          >
            {pctStr(aggregated.avgConfidence)}
          </span>
          {aggregated.verificationCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertTriangle className="w-3 h-3 text-red-500" />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {aggregated.verificationCount} 項待驗證
              </TooltipContent>
            </Tooltip>
          )}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="pl-7 pr-2 pb-2 space-y-3 border-l-2 border-muted ml-3">
          {/* Reason */}
          {node.reason && (
            <p className="text-[11px] text-muted-foreground italic">
              {node.reason}
            </p>
          )}
          {Array.from(grouped.entries()).map(([catKey, specs]) => (
            <CategoryGroup key={catKey} categoryKey={catKey} specs={specs} compact />
          ))}
        </div>
      )}
    </div>
  );
}
