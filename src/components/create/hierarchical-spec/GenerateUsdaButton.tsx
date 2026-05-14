/**
 * GenerateUsdaButton — per-node "Generate USDA" button for the
 * hierarchical spec view.
 *
 * Assembles context from a SpecTreeNode (recursively for system / module)
 * and calls the LLM-based USDA endpoint via useNodeUsdaExport.
 *
 * @see plans/per-node-usda-llm-generation.md §7.1 GenerateUsdaButton
 */

import { useCallback } from "react";
import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { toast } from "sonner";

import { useNodeUsdaExport } from "@/hooks/api/useNodeUsdaExport";
import type { NodeUsdaLlmRequest } from "@/lib/api";
import type { SpecTreeNode } from "./buildSpecTree";

// ---------------------------------------------------------------------------
// Context assembly helpers
// ---------------------------------------------------------------------------

/** Build specs_summary entries from a single node's draft. */
function nodeSpecsSummary(node: SpecTreeNode): Array<Record<string, unknown>> {
  if (!node.draft) return [];
  return node.draft.specs.map((s) => ({
    field_name: s.field_name,
    category: s.category,
    value: s.value,
    unit: s.unit ?? null,
    source: s.source,
    confidence: s.confidence,
  }));
}

/** Flatten interface_contracts to Record<string, Record<string, unknown>>. */
function flattenContracts(
  contracts: SpecTreeNode["interface_contracts"],
): Record<string, Record<string, unknown>> {
  if (!contracts || typeof contracts !== "object") return {};
  const result: Record<string, Record<string, unknown>> = {};
  for (const [key, val] of Object.entries(contracts)) {
    result[key] = (val && typeof val === "object" ? val : {}) as Record<string, unknown>;
  }
  return result;
}

/** Collect all specs from this node + all descendants recursively. */
function collectDescendantSpecs(node: SpecTreeNode): Array<Record<string, unknown>> {
  const own = nodeSpecsSummary(node);
  const childSpecs = node.children.flatMap(collectDescendantSpecs);
  return [...own, ...childSpecs];
}

/** Collect all interface_contracts from this node + all descendants. */
function collectDescendantContracts(
  node: SpecTreeNode,
): Record<string, Record<string, unknown>> {
  let merged = flattenContracts(node.interface_contracts);
  for (const child of node.children) {
    merged = { ...merged, ...collectDescendantContracts(child) };
  }
  return merged;
}

/** Collect all descendant names recursively. */
function collectDescendantNames(node: SpecTreeNode): string[] {
  return node.children.flatMap((c) => [c.name, ...collectDescendantNames(c)]);
}

/**
 * Assemble the NodeUsdaLlmRequest payload from a SpecTreeNode.
 *
 * - **component**: own specs only, no children.
 * - **module**: own specs + children specs, children_names = direct children.
 * - **system**: all descendant specs, children_names = all descendants.
 */
export function collectNodeContext(node: SpecTreeNode): NodeUsdaLlmRequest {
  const level = node.level as "system" | "module" | "component";

  switch (level) {
    case "component":
      return {
        node_name: node.name,
        node_level: "component",
        node_description: node.reason || "",
        specs_summary: nodeSpecsSummary(node),
        interface_contracts: flattenContracts(node.interface_contracts),
        children_names: [],
      };

    case "module":
      return {
        node_name: node.name,
        node_level: "module",
        node_description: node.reason || "",
        specs_summary: collectDescendantSpecs(node),
        interface_contracts: collectDescendantContracts(node),
        children_names: node.children.map((c) => c.name),
      };

    case "system":
    default:
      return {
        node_name: node.name,
        node_level: "system",
        node_description: node.reason || "",
        specs_summary: collectDescendantSpecs(node),
        interface_contracts: collectDescendantContracts(node),
        children_names: collectDescendantNames(node),
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface GenerateUsdaButtonProps {
  node: SpecTreeNode;
  /** Visual size variant. Default "icon" shows only icon; "sm" shows text. */
  variant?: "icon" | "sm";
}

/**
 * Renders a small download button that triggers LLM-based USDA generation
 * for the given SpecTreeNode.
 */
export function GenerateUsdaButton({
  node,
  variant = "icon",
}: GenerateUsdaButtonProps) {
  const { mutate, isPending } = useNodeUsdaExport();

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Prevent triggering parent collapsible toggle
      e.stopPropagation();

      const payload = collectNodeContext(node);
      mutate(payload, {
        onError: (err) => {
          toast.error(`USDA 生成失敗: ${err.message}`);
        },
      });
    },
    [node, mutate],
  );

  const label = `生成 ${node.name} USDA`;

  if (variant === "sm") {
    return (
      <Button
        size="sm"
        variant="ghost"
        className="h-6 px-2 text-[10px] gap-1"
        disabled={isPending}
        onClick={handleClick}
      >
        {isPending ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : (
          <Download className="w-3 h-3" />
        )}
        USDA
      </Button>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          size="icon"
          variant="ghost"
          className="h-5 w-5"
          disabled={isPending}
          onClick={handleClick}
        >
          {isPending ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Download className="w-3 h-3" />
          )}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs">
        {label}
      </TooltipContent>
    </Tooltip>
  );
}
