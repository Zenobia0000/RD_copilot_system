/**
 * HierarchicalSpecView — top-level container that bridges the 3-level
 * subsystem tree with the ~54 EngineeringSpecDraft items.
 *
 * Features:
 * - Calls `buildSpecTree` to join drafts onto the subsystem hierarchy.
 * - Renders Layer 1 SpecDashboardSummary (collapsible) above hierarchy.
 * - Renders 8 SystemSpecCards (one per root subsystem).
 * - Provides a view toggle: 📊 儀表板 / 🌲 階層視圖 / 📋 扁平視圖.
 *   "Flat" mode falls back to the original EngineeringSpecDraftPanel.
 * - `previewMode` banner when showing Step-2 drafts.
 *
 * Drop-in replacement for EngineeringSpecDraftPanel — accepts the same
 * `data: EngineeringSpecDraftResponse` prop shape.
 *
 * @see plans/hierarchical-spec-view.md §7, §9
 * @see plans/rd-friendly-spec-ux-design.md §8 Wave 1 — Layer 1 dashboard
 */

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  AlertTriangle,
  TreePine,
  List,
  LayoutDashboard,
  Network,
  Info,
  Download,
  Loader2,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUsdaExport } from "@/hooks/api";

import type { EngineeringSpecDraftResponse } from "@/types/generated/engineeringSpec";
import type { ConceptInterface } from "@/types/conceptArchitecture";
import { buildSpecTree } from "./buildSpecTree";
import { generateHierarchyText } from "./generateHierarchyText";
import { SystemSpecCard } from "./SystemSpecCard";
import { EngineeringSpecDraftPanel } from "../EngineeringSpecDraftPanel";
import { pctStr, SpecDashboardSummary } from "../spec-shared";
import { StructuralSchematicView } from "./schematic";

// ---------------------------------------------------------------------------
// Props — intentionally mirrors EngineeringSpecDraftPanelProps for drop-in use
// ---------------------------------------------------------------------------

export interface HierarchicalSpecViewProps {
  /** Pipeline response containing drafts + subsystem_tree. */
  data: EngineeringSpecDraftResponse;
  /** Concept interfaces from the architecture pack — fed to StructuralSchematicView for relation inference. */
  conceptInterfaces?: ConceptInterface[];
  /** Project UUID — required for USDA export endpoint. */
  projectId?: string;
  className?: string;
  /**
   * When true, shows a "Draft" banner — Step-2 results that haven't been
   * strengthened by Step 3 yet.
   */
  previewMode?: boolean;
}

type ViewMode = "dashboard" | "architecture" | "hierarchy" | "flat";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function HierarchicalSpecView({
  data,
  conceptInterfaces,
  projectId,
  className,
  previewMode = false,
}: HierarchicalSpecViewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("dashboard");

  // USDA export mutation
  const usdaExport = useUsdaExport();

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

  // Callback: when user clicks a system in the dashboard, switch to hierarchy
  const handleSystemClick = (_systemName: string) => {
    setViewMode("hierarchy");
  };

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

        {/* USDA Export + View toggle */}
        <div className="flex items-center gap-2">
          {/* USDA export button */}
          {canShowHierarchy && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2.5 text-xs gap-1"
              onClick={() => {
                const text = generateHierarchyText({
                  specTree,
                  conceptInterfaces,
                });
                const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `hierarchy-structure-${Date.now()}.txt`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }, 100);
              }}
            >
              <FileText className="w-3.5 h-3.5" />
              匯出階層文字檔
            </Button>
          )}
          {canShowHierarchy && projectId && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2.5 text-xs gap-1"
              disabled={usdaExport.isPending}
              onClick={() => {
                usdaExport.mutate({
                  project_id: projectId,
                  subsystems: data.subsystem_tree ?? [],
                  drafts: data.drafts ?? [],
                  package_map: data.package_map,
                });
              }}
            >
              {usdaExport.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              匯出 USDA
            </Button>
          )}

          {/* View toggle — 4-way: dashboard / architecture / hierarchy / flat */}
          {canShowHierarchy && (
            <div className="flex rounded-md border overflow-hidden">
            <Button
              size="sm"
              variant={viewMode === "dashboard" ? "default" : "ghost"}
              className="h-7 px-2.5 text-xs rounded-none gap-1"
              onClick={() => setViewMode("dashboard")}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              儀表板
            </Button>
            <Button
              size="sm"
              variant={viewMode === "architecture" ? "default" : "ghost"}
              className="h-7 px-2.5 text-xs rounded-none gap-1"
              onClick={() => setViewMode("architecture")}
            >
              <Network className="w-3.5 h-3.5" />
              結構示意圖
            </Button>
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
      </div>

      {/* Main content: dashboard / hierarchy / flat */}
      {viewMode === "architecture" && canShowHierarchy ? (
        <StructuralSchematicView
          tree={data.subsystem_tree ?? []}
          drafts={data.drafts ?? []}
          packageMap={data.package_map}
          conceptInterfaces={conceptInterfaces}
          onNodeClick={(name) => {
            setViewMode("hierarchy");
          }}
        />
      ) : viewMode === "dashboard" && canShowHierarchy ? (
        <SpecDashboardSummary
          specTree={specTree}
          onSystemClick={handleSystemClick}
        />
      ) : viewMode === "hierarchy" && canShowHierarchy ? (
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
