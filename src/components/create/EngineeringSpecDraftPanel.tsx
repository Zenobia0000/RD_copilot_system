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
 * @see plans/concept-pack-to-engineering-specs.md
 * @see src/types/generated/engineeringSpec.ts
 */

import { useState } from "react";
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
import { ChevronRight, AlertTriangle, ShieldCheck, Info } from "lucide-react";
import { cn } from "@/lib/utils";

import type {
  EngineeringSpecDraftResponse,
  EngineeringSpecDraft,
  DraftValue,
  DraftCategory,
} from "@/types/generated/engineeringSpec";
import {
  CONFIDENCE_COLORS,
  CONFIDENCE_SCORES,
  DRAFT_CATEGORIES,
} from "@/types/generated/engineeringSpec";

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
// Helpers
// ---------------------------------------------------------------------------

/** Format a DraftValue's value for display. */
function fmtValue(v: DraftValue): string {
  if (v.value == null) return "—";
  if (typeof v.value === "number") return String(v.value);
  if (typeof v.value === "string") return v.value;
  // Structured object/array → compact JSON
  try {
    return JSON.stringify(v.value);
  } catch {
    return String(v.value);
  }
}

/** Human-readable field name: snake_case → Title Case. */
function humanize(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Group specs by category, preserving DRAFT_CATEGORIES order. */
function groupByCategory(specs: DraftValue[]): Map<DraftCategory, DraftValue[]> {
  const map = new Map<DraftCategory, DraftValue[]>();
  for (const cat of DRAFT_CATEGORIES) {
    const items = specs.filter((s) => s.category === cat.key);
    if (items.length > 0) map.set(cat.key, items);
  }
  // Catch any uncategorized specs (shouldn't happen, but defensive)
  const knownKeys = new Set(DRAFT_CATEGORIES.map((c) => c.key));
  const uncategorized = specs.filter((s) => !knownKeys.has(s.category));
  if (uncategorized.length > 0) {
    const existing = map.get("manufacturing") ?? [];
    map.set("manufacturing", [...existing, ...uncategorized]);
  }
  return map;
}

/** Overall confidence as percentage string. */
function pctStr(score: number): string {
  return `${Math.round(score * 100)}%`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Confidence badge with color coding. */
function ConfidenceBadge({ confidence }: { confidence: DraftValue["confidence"] }) {
  const c = CONFIDENCE_COLORS[confidence];
  return (
    <Badge
      variant="outline"
      className={cn("text-[10px] px-1.5 py-0 h-5 font-medium", c.bg, c.text, c.border)}
    >
      {c.labelZh}
    </Badge>
  );
}

/** Single DraftValue row inside a category group. */
function SpecRow({ spec }: { spec: DraftValue }) {
  const [showDetail, setShowDetail] = useState(false);
  const hasAlternatives = spec.alternatives && spec.alternatives.length > 0;

  return (
    <div className="space-y-1">
      {/* Main row */}
      <div className="flex items-center gap-2 text-xs group">
        {/* Field name */}
        <span className="font-medium text-foreground min-w-[120px] shrink-0">
          {humanize(spec.field_name)}
        </span>

        {/* Value + unit */}
        <span className="font-mono text-foreground/80">
          {fmtValue(spec)}
          {spec.unit && (
            <span className="ml-0.5 text-muted-foreground">{spec.unit}</span>
          )}
        </span>

        {/* Confidence badge */}
        <ConfidenceBadge confidence={spec.confidence} />

        {/* Source tag */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5 cursor-default">
              {spec.source}
            </Badge>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs text-xs">
            來源：{spec.source}
          </TooltipContent>
        </Tooltip>

        {/* Needs verification warning */}
        {spec.needs_verification && (
          <Tooltip>
            <TooltipTrigger asChild>
              <AlertTriangle className="w-3.5 h-3.5 text-red-500 shrink-0" />
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">
              需要人工驗證
            </TooltipContent>
          </Tooltip>
        )}

        {/* Detail toggle */}
        {(spec.rationale || hasAlternatives) && (
          <button
            onClick={() => setShowDetail(!showDetail)}
            className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
          </button>
        )}
      </div>

      {/* Detail panel */}
      {showDetail && (
        <div className="ml-[120px] pl-2 border-l-2 border-muted space-y-1 text-[11px] text-muted-foreground">
          {spec.rationale && (
            <p>
              <span className="font-medium text-foreground/70">理由：</span>
              {spec.rationale}
            </p>
          )}
          {hasAlternatives && (
            <div>
              <span className="font-medium text-foreground/70">替代方案：</span>
              <ul className="list-disc list-inside mt-0.5 space-y-0.5">
                {spec.alternatives!.map((alt, i) => (
                  <li key={i}>
                    {Object.entries(alt).map(([k, v]) => (
                      <span key={k} className="mr-2">
                        <span className="font-medium">{k}:</span> {String(v)}
                      </span>
                    ))}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Category group header + spec rows. */
function CategoryGroup({
  categoryKey,
  specs,
}: {
  categoryKey: DraftCategory;
  specs: DraftValue[];
}) {
  const catDef = DRAFT_CATEGORIES.find((c) => c.key === categoryKey);
  const icon = catDef?.icon ?? "📋";
  const label = catDef?.labelZh ?? categoryKey;

  return (
    <div className="space-y-1.5">
      <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
        <span>{icon}</span>
        {label}
        <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 ml-1">
          {specs.length}
        </Badge>
      </p>
      <div className="space-y-1.5 pl-1">
        {specs.map((s) => (
          <SpecRow key={`${s.field_name}-${s.category}`} spec={s} />
        ))}
      </div>
    </div>
  );
}

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
