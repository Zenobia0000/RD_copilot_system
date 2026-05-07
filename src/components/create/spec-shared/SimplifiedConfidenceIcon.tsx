/**
 * SimplifiedConfidenceIcon — 3-level surface confidence indicator
 * with hover tooltip revealing the full 4-level detail.
 *
 * Mapping (DraftConfidence → SimplifiedLevel):
 *   🟢 high   = confirmed | library   (score ≥ 0.75)
 *   🟡 medium = estimate              (score = 0.5)
 *   🔴 low    = speculative           (score = 0.25)
 *
 * @see plans/rd-friendly-spec-ux-design.md §4
 */

import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { DraftConfidence } from "@/types/generated/engineeringSpec";
import { CONFIDENCE_COLORS } from "@/types/generated/engineeringSpec";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SimplifiedLevel = "high" | "medium" | "low";

export interface SimplifiedConfidenceIconProps {
  confidence: DraftConfidence;
  /** Show the simplified label text next to the dot. Default: false. */
  showLabel?: boolean;
  className?: string;
}

// ---------------------------------------------------------------------------
// Mapping helpers
// ---------------------------------------------------------------------------

const LEVEL_MAP: Record<DraftConfidence, SimplifiedLevel> = {
  confirmed: "high",
  library: "high",
  estimate: "medium",
  speculative: "low",
};

const LEVEL_CONFIG: Record<
  SimplifiedLevel,
  { dot: string; label: string; labelZh: string }
> = {
  high: {
    dot: "bg-green-500",
    label: "High",
    labelZh: "可信",
  },
  medium: {
    dot: "bg-amber-500",
    label: "Medium",
    labelZh: "需確認",
  },
  low: {
    dot: "bg-red-500",
    label: "Low",
    labelZh: "待驗證",
  },
};

/** Map DraftConfidence → SimplifiedLevel. */
export function toSimplifiedLevel(c: DraftConfidence): SimplifiedLevel {
  return LEVEL_MAP[c];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SimplifiedConfidenceIcon({
  confidence,
  showLabel = false,
  className,
}: SimplifiedConfidenceIconProps) {
  const level = LEVEL_MAP[confidence];
  const config = LEVEL_CONFIG[level];
  const detail = CONFIDENCE_COLORS[confidence];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            "inline-flex items-center gap-1 cursor-default",
            className,
          )}
        >
          <span
            className={cn(
              "inline-block w-2 h-2 rounded-full shrink-0",
              config.dot,
            )}
          />
          {showLabel && (
            <span className="text-[10px] text-muted-foreground font-medium">
              {config.labelZh}
            </span>
          )}
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs space-y-0.5 max-w-[200px]">
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "inline-block w-2 h-2 rounded-full",
              config.dot,
            )}
          />
          <span className="font-medium">{config.labelZh}</span>
          <span className="text-muted-foreground">({config.label})</span>
        </div>
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <span
            className={cn(
              "inline-block w-1.5 h-1.5 rounded-full",
              detail.bg.split(" ")[0] === "bg-green-100"
                ? "bg-green-500"
                : detail.bg.split(" ")[0] === "bg-blue-100"
                  ? "bg-blue-500"
                  : detail.bg.split(" ")[0] === "bg-amber-100"
                    ? "bg-amber-500"
                    : "bg-red-500",
            )}
          />
          <span>
            詳細：{detail.labelZh}（{detail.label}）
          </span>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
