/**
 * DecomposedChildrenList — container for child PCs + SFs under a parent TC.
 *
 * Refs:
 *   - plans/plan-b-hierarchical-tc-tree.md §4.5
 *   - docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §6.3
 *
 * Renders a collapsible, indented list of `DecomposedPCCard`s (sorted by
 * separation category) and `DecomposedSFCard`s under a parent TC. This is a
 * pure presentational container — no data fetching.
 */

import { useState, type JSX } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ExploreContradiction } from '@/types/explore';
import type { SeparationCategory } from '@/lib/triz/separationPrinciples';
import { DecomposedPCCard } from './DecomposedPCCard';
import { DecomposedSFCard } from './DecomposedSFCard';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface DecomposedChildrenListProps {
  /** All child rows (PC + SF, already filtered by parent_contradiction_id). */
  children: ExploreContradiction[];
  /** Parent TC id, for reference / empty-state labeling. */
  parentId: string;
  onEditPC?: (pc: ExploreContradiction) => void;
  onDeletePC?: (pcId: string) => void;
  onEditSF?: (sf: ExploreContradiction) => void;
  onDeleteSF?: (sfId: string) => void;
  /** Whether the list is expanded by default. Default true. */
  defaultExpanded?: boolean;
  /** When true, show a yellow banner indicating parent TC has changed. */
  stale?: boolean;
  /** Callback to re-run PC decomposition for this parent. */
  onReDecompose?: () => void;
}

// ---------------------------------------------------------------------------
// Sorting
// ---------------------------------------------------------------------------

const CATEGORY_ORDER: Record<SeparationCategory, number> = {
  time: 0,
  space: 1,
  condition: 2,
  whole_part: 3,
};

function categoryRank(cat: SeparationCategory | null | undefined): number {
  if (!cat) return 99;
  return CATEGORY_ORDER[cat] ?? 99;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DecomposedChildrenList({
  children,
  parentId,
  onEditPC,
  onDeletePC,
  onEditSF,
  onDeleteSF,
  defaultExpanded = true,
  stale,
  onReDecompose,
}: DecomposedChildrenListProps): JSX.Element | null {
  const [pcExpanded, setPcExpanded] = useState(defaultExpanded);

  // Separate PC and SF children
  const pcChildren = children.filter((c) => c.type === 'PC');
  const sfChildren = children.filter((c) => c.type === 'SF');

  if (pcChildren.length === 0 && sfChildren.length === 0) {
    return null;
  }

  const sortedPCs = [...pcChildren].sort((a, b) => {
    const ra = categoryRank(a.separationCategory);
    const rb = categoryRank(b.separationCategory);
    if (ra !== rb) return ra - rb;
    // stable-ish secondary sort by derivedParameter for determinism
    return (a.derivedParameter ?? '').localeCompare(b.derivedParameter ?? '');
  });

  return (
    <div
      data-testid="decomposed-children-list"
      data-parent-id={parentId}
      className="pl-8 border-l-2 border-dashed border-muted ml-2 space-y-2"
    >
      {stale && (
        <div className="flex items-center gap-2 px-3 py-2 mb-2 rounded-md bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 text-xs">
          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
          <span>父矛盾參數已更新，建議重新深挖</span>
          {onReDecompose && (
            <button
              onClick={onReDecompose}
              className="ml-auto text-xs font-medium text-amber-600 dark:text-amber-400 hover:underline"
            >
              重新深挖
            </button>
          )}
        </div>
      )}

      {/* ── PC section ── */}
      {sortedPCs.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setPcExpanded((v) => !v)}
            className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
            aria-expanded={pcExpanded}
            data-testid="decomposed-pc-toggle"
          >
            {pcExpanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
            <span>已深挖 {sortedPCs.length} 個物理矛盾</span>
          </button>
          <div className={cn('space-y-2', !pcExpanded && 'hidden')}>
            {sortedPCs.map((child) => (
              <DecomposedPCCard
                key={child.id}
                pc={child}
                onEdit={onEditPC}
                onDelete={onDeletePC}
              />
            ))}
          </div>
        </>
      )}

      {/* ── SF section ── */}
      {sfChildren.length > 0 && (
        <>
          <div
            className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground"
            data-testid="decomposed-sf-label"
          >
            <span>衍生 {sfChildren.length} 個 Su-Field 問題</span>
          </div>
          <div className="space-y-2">
            {sfChildren.map((child) => (
              <DecomposedSFCard
                key={child.id}
                sf={child}
                onEdit={onEditSF}
                onDelete={onDeleteSF}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default DecomposedChildrenList;
