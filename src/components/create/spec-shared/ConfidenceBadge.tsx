/**
 * ConfidenceBadge — color-coded badge for DraftValue confidence levels.
 *
 * Extracted from EngineeringSpecDraftPanel for reuse in both flat and
 * hierarchical spec views.
 *
 * @see plans/hierarchical-spec-view.md §5
 */

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DraftConfidence } from "@/types/generated/engineeringSpec";
import { CONFIDENCE_COLORS } from "@/types/generated/engineeringSpec";

export interface ConfidenceBadgeProps {
  confidence: DraftConfidence;
  className?: string;
}

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  const c = CONFIDENCE_COLORS[confidence];
  return (
    <Badge
      variant="outline"
      className={cn("text-[10px] px-1.5 py-0 h-5 font-medium", c.bg, c.text, c.border, className)}
    >
      {c.labelZh}
    </Badge>
  );
}
