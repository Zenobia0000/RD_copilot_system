/**
 * HierarchicalSpecView — top-level container that bridges the 3-level
 * subsystem tree with the ~54 EngineeringSpecDraft items.
 *
 * Features:
 * - Calls `buildSpecTree` to join drafts onto the subsystem hierarchy.
 * - Renders 8 SystemSpecCards (one per root subsystem).
 * - Provides a view toggle: 🌲 階層視圖 / 📋 扁平視圖.
 *   "Flat" mode falls back to the original EngineeringSpecDraftPanel.
 * - `previewMode` banner when showing Step-2 drafts.
 *
 * Drop-in replacement for EngineeringSpecDraftPanel — accepts the same
 * `data: EngineeringSpecDraftResponse` prop shape.
 *
 * @see plans/hierarchical-spec-view.md §7, §9
 */

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  AlertTriangle,
  TreePine,
  List,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";

import type { EngineeringSpecDraftResponse } from "@/types/generated/engineeringSpec";
import { buildSpecTree } from "./buildSpecTree";
import { SystemSpecCard } from "./SystemSpecCard";
import { EngineeringSpecDraftPanel } from "../EngineeringSpecDraftPanel";
import { pctStr } from "../spec-shared";

// ---------------------------------------------------------------------------
// Props — intentionally mirrors EngineeringSpecDraftPanelProps for drop-in use
// ---------------------------------------------------------------------------

export interface HierarchicalSpecViewProps {
  /** Pipeline response containing drafts + subsystem_tree. */
  data: EngineeringSpecDraftResponse;
  className?: string;
  /**
   * When true, shows a "Draft" banner — Step-2 results that haven't been
   * strengthened by Step 3 yet.
   */
  previewMode?: boolean;
}

type ViewMode = "hierarchy" | "flat";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function HierarchicalSpecView({
  data,
  className,
  previewMode = false,
}: HierarchicalSpecViewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("hierarchy");

  // Build the merged tree — memoised on data identity
  const specTree = useMemo(
    () => buildSpecTree(data.subsystem_tree ?? [], data.drafts ?? []),
    [data.subsystem_tree, data.drafts],
  );

  // Global aggregate for the summary bar
  const globalStats = useMemo(() => {
    let totalSpecs = 0;
    let verificationCount = 0;
    let weightedConf = 0;

    for (const root of specTree) {
      totalSpecs += root.aggregated.totalSpecs;
      verificationCount += root.aggregated.verificationCount;
      weightedConf +=
        root.aggregated.totalSpecs * root.aggregated.avgConfidence;
    }

    return {
      totalSpecs,
      verificationCount,
      avgConfidence: totalSpecs > 0 ? weightedConf / totalSpecs : 0,
      systemCount: specTree.length,
    };
  }, [specTree]);

  // Guard: no tree data → fall back to flat view automatically
  const canShowHierarchy =
    specTree.length > 0 && (data.subsystem_tree ?? []).length > 0;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Preview mode banner */}
      {previewMode && (
        <div className="flex items-center gap-2 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
          <Info className="w-4 h-4 shrink-0" />
          <span>
            Step 2 草稿 — 信心度與來源尚未經 Step 3 強化，可能會有所變動。
          </span>
        </div>
      )}

      {/* Top bar: summary + view toggle */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        {/* Global summary */}
        <div className="flex items-center gap-3 text-xs">
          <Badge variant="secondary" className="gap-1">
            <BarChart3 className="w-3 h-3" />
            {globalStats.totalSpecs} 規格項
          </Badge>
          <Badge variant="secondary" className="gap-1">
            {globalStats.systemCount} 系統
          </Badge>
          <span
            className={cn(
              "font-mono font-medium",
              globalStats.avgConfidence >= 0.7
                ? "text-green-600"
                : globalStats.avgConfidence >= 0.4
                  ? "text-amber-600"
                  : "text-red-600",
            )}
          >
            平均信心 {pctStr(globalStats.avgConfidence)}
          </span>
          {globalStats.verificationCount > 0 && (
            <Badge
              variant="outline"
              className="text-red-600 border-red-300 gap-1"
            >
              <AlertTriangle className="w-3 h-3" />
              {globalStats.verificationCount} 待驗證
            </Badge>
          )}
        </div>

        {/* View toggle */}
        {canShowHierarchy && (
          <div className="flex rounded-md border overflow-hidden">
            <Button
              size="sm"
              variant={viewMode === "hierarchy" ? "default" : "ghost"}
              className="h-7 px-2.5 text-xs rounded-none gap-1"
              onClick={() => setViewMode("hierarchy")}
            >
              <TreePine className="w-3.5 h-3.5" />
              階層視圖
            </Button>
            <Button
              size="sm"
              variant={viewMode === "flat" ? "default" : "ghost"}
              className="h-7 px-2.5 text-xs rounded-none gap-1"
              onClick={() => setViewMode("flat")}
            >
              <List className="w-3.5 h-3.5" />
              扁平視圖
            </Button>
          </div>
        )}
      </div>

      {/* Main content: hierarchy or flat */}
      {viewMode === "hierarchy" && canShowHierarchy ? (
        <div className="space-y-3">
          {specTree.map((rootNode) => (
            <SystemSpecCard key={rootNode.name} node={rootNode} />
          ))}
        </div>
      ) : (
        <EngineeringSpecDraftPanel
          data={data}
          previewMode={previewMode}
        />
      )}
    </div>
  );
}
