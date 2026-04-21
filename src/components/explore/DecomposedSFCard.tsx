/**
 * DecomposedSFCard — single child SF card for the Plan B hierarchical TC tree.
 *
 * Refs:
 *   - plans/plan-b-hierarchical-tc-tree.md §4.6
 *
 * Renders one row from the contradictions table whose `parentContradictionId`
 * points at a parent TC and whose `type === 'SF'`. Displays Su-Field model
 * fields: S1 (tool substance), S2 (product substance), F (field), interaction
 * status, and completeness assessment.
 *
 * The component is intentionally presentational — all edit/delete actions are
 * delegated via callbacks.
 */

import { type JSX } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { ExploreContradiction } from '@/types/explore';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface DecomposedSFCardProps {
  /** Child SF row (parent_contradiction_id set, type === 'SF'). */
  sf: ExploreContradiction;
  /** Optional callback for edit action. Omit to hide the edit button. */
  onEdit?: (sf: ExploreContradiction) => void;
  /** Optional callback for delete action. Omit to hide the delete button. */
  onDelete?: (sfId: string) => void;
  /** Visual density. Default 'comfortable'. */
  density?: 'compact' | 'comfortable';
}

// ---------------------------------------------------------------------------
// Interaction / Completeness styling
// ---------------------------------------------------------------------------

type InteractionKind = 'useful' | 'harmful' | 'insufficient' | 'missing';
type CompletenessKind = 'complete' | 'incomplete' | 'harmful_complete';

const INTERACTION_LABEL: Record<InteractionKind, string> = {
  useful: '有效',
  harmful: '有害',
  insufficient: '不足',
  missing: '缺失',
};

const INTERACTION_CLASS: Record<InteractionKind, string> = {
  useful:
    'border-green-300 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200',
  harmful:
    'border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200',
  insufficient:
    'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200',
  missing:
    'border-slate-300 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300',
};

const COMPLETENESS_LABEL: Record<CompletenessKind, string> = {
  complete: '完整',
  incomplete: '不完整',
  harmful_complete: '有害完整',
};

const COMPLETENESS_CLASS: Record<CompletenessKind, string> = {
  complete:
    'border-green-300 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200',
  incomplete:
    'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200',
  harmful_complete:
    'border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200',
};

// Bar colour for the left accent
const INTERACTION_BAR: Record<InteractionKind, string> = {
  useful: 'bg-green-500',
  harmful: 'bg-red-500',
  insufficient: 'bg-amber-500',
  missing: 'bg-slate-400',
};

function interactionBarClass(interaction: string | null | undefined): string {
  if (!interaction) return 'bg-indigo-400';
  return INTERACTION_BAR[interaction as InteractionKind] ?? 'bg-indigo-400';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DecomposedSFCard({
  sf,
  onEdit,
  onDelete,
  density = 'comfortable',
}: DecomposedSFCardProps): JSX.Element {
  const isCompact = density === 'compact';

  const interaction = sf.sfInteraction as InteractionKind | null;
  const completeness = sf.sfCompleteness as CompletenessKind | null;

  return (
    <Card
      data-testid="decomposed-sf-card"
      className={cn(
        'relative flex gap-2 overflow-hidden border',
        isCompact ? 'p-2' : 'p-3',
      )}
    >
      {/* Left colour bar */}
      <div
        aria-hidden="true"
        data-testid="sf-interaction-bar"
        className={cn(
          'absolute left-0 top-0 h-full w-1',
          interactionBarClass(sf.sfInteraction),
        )}
      />

      <div className="flex-1 pl-2 space-y-1.5">
        {/* Top row: SF badge + interaction + completeness + actions */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge
              variant="outline"
              className="text-[10px] border-indigo-300 bg-indigo-50 text-indigo-800 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-200"
              data-testid="sf-type-badge"
            >
              Su-Field
            </Badge>
            {interaction && INTERACTION_LABEL[interaction] && (
              <Badge
                variant="outline"
                className={cn('text-[10px]', INTERACTION_CLASS[interaction])}
                data-testid="sf-interaction-badge"
              >
                {INTERACTION_LABEL[interaction]}
              </Badge>
            )}
            {completeness && COMPLETENESS_LABEL[completeness] && (
              <Badge
                variant="outline"
                className={cn('text-[10px]', COMPLETENESS_CLASS[completeness])}
                data-testid="sf-completeness-badge"
              >
                {COMPLETENESS_LABEL[completeness]}
              </Badge>
            )}
          </div>

          {(onEdit || onDelete) && (
            <div className="flex items-center gap-1 shrink-0">
              {onEdit && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  aria-label="編輯"
                  data-testid="sf-edit-btn"
                  onClick={() => onEdit(sf)}
                >
                  <Pencil className="h-3 w-3" />
                </Button>
              )}
              {onDelete && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 text-destructive"
                  aria-label="刪除"
                  data-testid="sf-delete-btn"
                  onClick={() => onDelete(sf.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          )}
        </div>

        {/* S1 → F → S2 model visualization */}
        <div
          className="flex flex-wrap items-center gap-1.5 text-xs"
          data-testid="sf-model-row"
        >
          <span className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[11px]">
            S1: {sf.sfSubstance1 || '?'}
          </span>
          <span aria-hidden="true" className="text-muted-foreground">→</span>
          <span className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[11px]">
            F: {sf.sfField || '?'}
          </span>
          <span aria-hidden="true" className="text-muted-foreground">→</span>
          <span className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[11px]">
            S2: {sf.sfSubstance2 || '?'}
          </span>
        </div>

        {/* Description (if present) */}
        {sf.description && (
          <p
            className="text-[11px] leading-snug text-muted-foreground"
            data-testid="sf-description"
          >
            {sf.description}
          </p>
        )}
      </div>
    </Card>
  );
}

export default DecomposedSFCard;
