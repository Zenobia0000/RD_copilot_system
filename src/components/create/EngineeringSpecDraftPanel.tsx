/**
 * EngineeringSpecDraftPanel — renders AI-generated engineering spec drafts
 * with full provenance (source, confidence, needs_verification) per DraftValue.
 *
 * Design principle: every AI-generated value carries source, confidence, and
 * needs_verification — no AI number masquerades as engineering truth.
 *
 * Layout:
 *   • Top-level: one Collapsible card per subsystem
 *   • Inside each subsystem: specs grouped by DRAFT_CATEGORIES order
 *   • Each DraftValue: name + value + unit, confidence badge, source tag,
 *     needs_verification warning, rationale toggle, alternatives list
 *
 * Shared primitives (ConfidenceBadge, SpecRow, CategoryGroup, helpers) are
 * extracted to spec-shared/ for reuse in HierarchicalSpecView.
 *
 * @see plans/hierarchical-spec-view.md §5 Component Reuse Strategy
 * @see plans/concept-pack-to-engineering-specs.md
 * @see src/types/generated/engineeringSpec.ts
 */

import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { ChevronRight, AlertTriangle, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

import type {
  EngineeringSpecDraftResponse,
  EngineeringSpecDraft,
} from "@/types/generated/engineeringSpec";

// Import shared primitives from spec-shared/
import { CategoryGroup, groupByCategory, pctStr } from "./spec-shared";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface EngineeringSpecDraftPanelProps {
  /** Pipeline response containing all subsystem drafts. */
  data: EngineeringSpecDraftResponse;
  className?: string;
  /**
   * When true, the panel is showing Step-2 drafts that have NOT yet been
   * strengthened by Step 3 (source strengthening). A subtle "Draft" banner
   * is rendered so users know confidence/sources may still be upgraded.
   */
  previewMode?: boolean;
}

// ---------------------------------------------------------------------------
// Sub-components (panel-specific; shared ones live in spec-shared/)
// ---------------------------------------------------------------------------

/** Single subsystem collapsible card. */
function SubsystemDraftCard({ draft }: { draft: EngineeringSpecDraft }) {
  const grouped = groupByCategory(draft.specs);
  const confColor = draft.overall_confidence >= 0.7
    ? "text-green-600"
    : draft.overall_confidence >= 0.4
      ? "text-amber-600"
      : "text-red-600";

  return (
    <Collapsible>
      <Card className="border-l-[3px] border-l-amber-400/60">
        <CollapsibleTrigger asChild>
          <CardContent className="p-3 cursor-pointer hover:bg-muted/30 transition-colors">
            <div className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-muted-foreground transition-transform [[data-state=open]>&]:rotate-90" />

              {/* Subsystem code */}
              <span className="text-sm font-semibold">{draft.subsystem_code}</span>

              {/* Spec count */}
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
                {draft.specs.length} 項規格
              </Badge>

              {/* Overall confidence */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className={cn("text-xs font-mono font-medium ml-auto", confColor)}>
                    <ShieldCheck className="w-3.5 h-3.5 inline-block mr-0.5 -mt-0.5" />
                    {pctStr(draft.overall_confidence)}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  加權平均信心度：{pctStr(draft.overall_confidence)}
                </TooltipContent>
              </Tooltip>

              {/* Verification count badge */}
              {draft.verification_count > 0 && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1.5 py-0 h-5 border-red-300 text-red-600 bg-red-50 dark:bg-red-950/20"
                    >
                      <AlertTriangle className="w-3 h-3 mr-0.5" />
                      {draft.verification_count} 待驗證
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    {draft.verification_count} 項規格需要人工驗證
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="px-4 pb-4 pt-0 border-t space-y-4">
            {Array.from(grouped.entries()).map(([catKey, specs]) => (
              <CategoryGroup key={catKey} categoryKey={catKey} specs={specs} />
            ))}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

/** Empty state when no drafts are available. */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-muted-foreground text-xs gap-2">
      <ShieldCheck className="w-8 h-8 opacity-30" />
      <p>尚無工程規格草案</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * EngineeringSpecDraftPanel — top-level panel rendering the full pipeline output.
 *
 * Shows a summary header with total draft count + average confidence,
 * followed by one collapsible card per subsystem.
 */
export function EngineeringSpecDraftPanel({
  data,
  className,
  previewMode = false,
}: EngineeringSpecDraftPanelProps) {
  const { drafts } = data;
  const isEmpty = drafts.length === 0;

  // Aggregate stats
  const totalSpecs = drafts.reduce((sum, d) => sum + d.specs.length, 0);
  const totalVerify = drafts.reduce((sum, d) => sum + d.verification_count, 0);
  const avgConf =
    drafts.length > 0
      ? drafts.reduce((sum, d) => sum + d.overall_confidence, 0) / drafts.length
      : 0;

  return (
    <Card className={cn("border-amber-400/30", previewMode && "border-dashed", className)}>
      {/* Preview mode banner */}
      {previewMode && (
        <CardContent className="px-4 pt-3 pb-0">
          <Badge variant="outline" className="text-[10px] px-2 py-0.5 border-amber-400 text-amber-600 bg-amber-50 dark:bg-amber-950/20">
            ⏳ 草案預覽 — 來源強化進行中，信心度可能會提升
          </Badge>
        </CardContent>
      )}
      {/* Header */}
      <CardContent className="p-4 pb-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
          <span>📋</span>
          {previewMode ? "工程規格草案（預覽）" : "工程規格草案"}
          {!isEmpty && (
            <>
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5 ml-1">
                {drafts.length} 子系統 · {totalSpecs} 項規格
              </Badge>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-[10px] px-1.5 py-0 h-5",
                      avgConf >= 0.7
                        ? "border-green-300 text-green-600"
                        : avgConf >= 0.4
                          ? "border-amber-300 text-amber-600"
                          : "border-red-300 text-red-600",
                    )}
                  >
                    信心度 {pctStr(avgConf)}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  所有子系統的平均信心度
                </TooltipContent>
              </Tooltip>
              {totalVerify > 0 && (
                <Badge
                  variant="outline"
                  className="text-[10px] px-1.5 py-0 h-5 border-red-300 text-red-600 bg-red-50 dark:bg-red-950/20"
                >
                  <AlertTriangle className="w-3 h-3 mr-0.5" />
                  {totalVerify} 待驗證
                </Badge>
              )}
            </>
          )}
        </div>
      </CardContent>

      {/* Body */}
      <CardContent className="px-4 pb-4 pt-0 space-y-2">
        {isEmpty ? (
          <EmptyState />
        ) : (
          drafts.map((draft) => (
            <SubsystemDraftCard key={draft.subsystem_code} draft={draft} />
          ))
        )}
      </CardContent>
    </Card>
  );
}
