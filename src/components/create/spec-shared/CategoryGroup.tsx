/**
 * CategoryGroup — renders a group of DraftValues under a single category header.
 *
 * Displays the category icon + label + count badge, followed by SpecRow list.
 *
 * Extracted from EngineeringSpecDraftPanel for reuse.
 *
 * @see plans/hierarchical-spec-view.md §5
 */

import { Badge } from "@/components/ui/badge";
import type { DraftValue, DraftCategory } from "@/types/generated/engineeringSpec";
import { DRAFT_CATEGORIES } from "@/types/generated/engineeringSpec";
import { SpecRow } from "./SpecRow";

export interface CategoryGroupProps {
  categoryKey: DraftCategory;
  specs: DraftValue[];
  /** Compact mode for inline display (e.g. component level). */
  compact?: boolean;
}

export function CategoryGroup({ categoryKey, specs, compact = false }: CategoryGroupProps) {
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
          <SpecRow key={`${s.field_name}-${s.category}`} spec={s} compact={compact} />
        ))}
      </div>
    </div>
  );
}
