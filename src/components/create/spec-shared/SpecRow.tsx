/**
 * SpecRow — renders a single DraftValue with full provenance display.
 *
 * Shows: field name, value + unit, confidence badge, source tag,
 * needs_verification warning, and expandable rationale/alternatives detail.
 *
 * Extracted from EngineeringSpecDraftPanel for reuse.
 *
 * @see plans/hierarchical-spec-view.md §5
 */

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { AlertTriangle, Info } from "lucide-react";

import type { DraftValue } from "@/types/generated/engineeringSpec";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { fmtValue, humanize } from "./spec-helpers";

export interface SpecRowProps {
  spec: DraftValue;
  /** Compact mode hides detail toggle and shortens field name display. */
  compact?: boolean;
  /** Render as <tr> table cells instead of flex div. */
  tableMode?: boolean;
}

export function SpecRow({ spec, compact = false, tableMode = false }: SpecRowProps) {
  const [showDetail, setShowDetail] = useState(false);
  const hasAlternatives = spec.alternatives && spec.alternatives.length > 0;

  // ── Table mode: render as <tr> ──
  if (tableMode) {
    return (
      <>
        <tr className="border-b hover:bg-muted/30 text-xs group">
          {/* Field name */}
          <td className="py-1.5 px-2 font-medium text-foreground whitespace-nowrap">
            {humanize(spec.field_name)}
          </td>

          {/* Value + unit */}
          <td className="py-1.5 px-2 font-mono text-foreground/80 whitespace-nowrap">
            {fmtValue(spec)}
            {spec.unit && (
              <span className="ml-0.5 text-muted-foreground">{spec.unit}</span>
            )}
          </td>

          {/* Confidence */}
          <td className="py-1.5 px-2">
            <ConfidenceBadge confidence={spec.confidence} />
          </td>

          {/* Source */}
          <td className="py-1.5 px-2">
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
          </td>

          {/* Status */}
          <td className="py-1.5 px-2 text-center">
            {spec.needs_verification ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <AlertTriangle className="w-3.5 h-3.5 text-red-500 inline-block" />
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  需要人工驗證
                </TooltipContent>
              </Tooltip>
            ) : (
              <span className="text-green-500">✓</span>
            )}
          </td>

          {/* Detail toggle */}
          <td className="py-1.5 px-2 text-center">
            {(spec.rationale || hasAlternatives) && (
              <button
                onClick={() => setShowDetail(!showDetail)}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Info className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
              </button>
            )}
          </td>
        </tr>

        {/* Detail row (spans full width) */}
        {showDetail && (
          <tr className="bg-muted/20">
            <td colSpan={6} className="px-4 py-2 text-[11px] text-muted-foreground">
              {spec.rationale && (
                <p>
                  <span className="font-medium text-foreground/70">理由：</span>
                  {spec.rationale}
                </p>
              )}
              {hasAlternatives && (
                <div className="mt-1">
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
            </td>
          </tr>
        )}
      </>
    );
  }

  // ── Default flex mode ──
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
        {!compact && (spec.rationale || hasAlternatives) && (
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
