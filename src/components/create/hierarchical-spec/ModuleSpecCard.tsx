/**
 * ModuleSpecCard — renders a module-level node inside a SystemSpecCard.
 *
 * Shows:
 * - Module header with aggregated stats (spec count, confidence, verification)
 * - InterfaceContractsPanel (reused from existing component)
 * - Spec categories via CategoryGroup
 * - Component children via ComponentSpecList
 *
 * Default: collapsed. Expands on click to reveal full detail.
 *
 * @see plans/hierarchical-spec-view.md §3 元件架構
 */

import { useState } from "react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { ChevronRight, AlertTriangle, Box, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

import type { SpecTreeNode } from "./buildSpecTree";
import { ComponentSpecList } from "./ComponentSpecList";
import { GenerateUsdaButton } from "./GenerateUsdaButton";
import { InterfaceContractsPanel } from "../InterfaceContractsPanel";
import { CategoryGroup, ConfidenceBadge, groupByCategory, pctStr } from "../spec-shared";

export interface ModuleSpecCardProps {
  node: SpecTreeNode;
  /** When true, starts in expanded state. */
  defaultOpen?: boolean;
}

/**
 * Module-level spec card with collapsible detail.
 */
export function ModuleSpecCard({ node, defaultOpen = false }: ModuleSpecCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const { draft, aggregated, children } = node;

  const grouped = draft ? groupByCategory(draft.specs) : new Map();
  const hasSpecs = draft && draft.specs.length > 0;
  const hasChildren = children.length > 0;
  const hasContracts =
    node.interface_contracts && Object.keys(node.interface_contracts).length > 0;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      {/* Module header trigger */}
      <CollapsibleTrigger asChild>
        <button
          className={cn(
            "flex items-center gap-2 w-full text-left px-3 py-2 rounded-md",
            "hover:bg-muted/50 transition-colors group",
            "border border-transparent",
            open && "bg-muted/30 border-border",
          )}
        >
          <ChevronRight
            className={cn(
              "w-4 h-4 text-muted-foreground transition-transform shrink-0",
              open && "rotate-90",
            )}
          />

          <Box className="w-4 h-4 text-blue-500 shrink-0" />

          {/* Module name */}
          <span className="font-medium text-sm">{node.name}</span>

          {/* Stats badges */}
          <div className="flex items-center gap-1.5 ml-auto">
            {/* Spec count */}
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
              {aggregated.totalSpecs} specs
            </Badge>

            {/* Confidence */}
            <span
              className={cn(
                "text-[11px] font-mono font-medium",
                aggregated.avgConfidence >= 0.7
                  ? "text-green-600"
                  : aggregated.avgConfidence >= 0.4
                    ? "text-amber-600"
                    : "text-red-600",
              )}
            >
              {pctStr(aggregated.avgConfidence)}
            </span>

            {/* Verification count */}
            {aggregated.verificationCount > 0 && (
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 h-4 text-red-600 border-red-300"
              >
                <AlertTriangle className="w-3 h-3 mr-0.5" />
                {aggregated.verificationCount}
              </Badge>
            )}

            {/* Children indicator */}
            {hasChildren && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                <Layers className="w-3 h-3 mr-0.5" />
                {children.length}
              </Badge>
            )}

            {/* Generate USDA via LLM */}
            <GenerateUsdaButton node={node} />
          </div>
        </button>
      </CollapsibleTrigger>

      {/* Expanded content */}
      <CollapsibleContent>
        <div className="ml-5 pl-4 border-l-2 border-muted space-y-3 py-2">
          {/* Reason / rationale */}
          {node.reason && (
            <p className="text-xs text-muted-foreground italic">{node.reason}</p>
          )}

          {/* Related contradictions */}
          {node.related_contradictions.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-[10px] text-muted-foreground">矛盾關聯:</span>
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

          {/* Interface contracts — reuse existing panel */}
          {hasContracts && (
            <InterfaceContractsPanel
              contracts={node.interface_contracts}
              level="module"
            />
          )}

          {/* Own specs via CategoryGroup */}
          {hasSpecs && (
            <div className="space-y-2">
              <span className="text-xs font-medium text-muted-foreground">
                模組規格 ({draft!.specs.length})
              </span>
              {Array.from(grouped.entries()).map(([catKey, specs]) => (
                <CategoryGroup key={catKey} categoryKey={catKey} specs={specs} />
              ))}
            </div>
          )}

          {/* Component children */}
          {hasChildren && (
            <div className="space-y-0.5">
              <span className="text-xs font-medium text-muted-foreground">
                元件 ({children.length})
              </span>
              {children.map((child) => (
                <ComponentSpecList key={child.name} node={child} />
              ))}
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
