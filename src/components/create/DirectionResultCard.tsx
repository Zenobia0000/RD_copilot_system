/**
 * DirectionResultCard — 顯示單一矛盾的方向分析結果 (v8).
 *
 * Shows:
 *   - All directions clustered from TC/PC/SF solutions
 *   - Scored directions with weighted totals
 *   - Top1 (highlighted) + Top2 (secondary)
 *   - Expandable solution details per direction
 */

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ChevronDown,
  ChevronUp,
  Trophy,
  Medal,
  Target,
  Zap,
  Wrench,
  FlaskConical,
  ArrowUpDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  ContradictionDirectionResult,
  DirectionGroup,
  DirectionScore,
  DirectionSolution,
} from '@/types/directedTriz';

// ---------------------------------------------------------------------------
// Severity badge config
// ---------------------------------------------------------------------------
const SEVERITY_BADGE: Record<string, { label: string; variant: 'destructive' | 'default' | 'secondary' | 'outline' }> = {
  fatal: { label: '致命', variant: 'destructive' },
  major: { label: '主要', variant: 'default' },
  minor: { label: '次要', variant: 'secondary' },
  unknown: { label: '未知', variant: 'outline' },
};

// ---------------------------------------------------------------------------
// Sort mode config
// ---------------------------------------------------------------------------
type SortMode = 'weighted_total' | 'feasibility' | 'cost_difficulty' | 'tool_support';

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'weighted_total', label: '加權總分' },
  { value: 'feasibility', label: '可行性優先' },
  { value: 'cost_difficulty', label: '成本難度優先' },
  { value: 'tool_support', label: '工具共識優先' },
];

/** Return the score value for a given sort mode. cost_difficulty is ascending (lower = better). */
function getSortValue(score: DirectionScore | undefined, mode: SortMode): number {
  if (!score) return mode === 'cost_difficulty' ? Infinity : -Infinity;
  switch (mode) {
    case 'weighted_total': return score.weighted_total;
    case 'feasibility': return score.feasibility;
    case 'cost_difficulty': return -score.cost_difficulty; // negate so ascending sort = lower cost first
    case 'tool_support': return score.tool_support;
  }
}

// Path icon helper
function PathIcon({ path }: { path: string }) {
  switch (path) {
    case 'TC': return <Target className="h-3 w-3 text-blue-500" />;
    case 'PC': return <Wrench className="h-3 w-3 text-amber-500" />;
    case 'SF': return <FlaskConical className="h-3 w-3 text-green-500" />;
    default: return <Zap className="h-3 w-3 text-muted-foreground" />;
  }
}

// ---------------------------------------------------------------------------
// Sub-component: expandable solution item
// ---------------------------------------------------------------------------
const SUGGESTION_TRUNCATE_LEN = 120;

function SolutionItem({ sol }: { sol: DirectionSolution }) {
  const long = sol.suggestion.length > SUGGESTION_TRUNCATE_LEN;
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="flex gap-1.5 items-start text-[11px] bg-muted/30 rounded p-1.5">
      <PathIcon path={sol.path} />
      <div className="flex-1 min-w-0">
        <span className="font-medium">
          {sol.principle_name || `#${sol.principle_number}`}
        </span>
        <p className={cn(
          "text-muted-foreground whitespace-pre-wrap",
          !expanded && long && "line-clamp-2",
        )}>
          {sol.suggestion}
        </p>
        {long && (
          <button
            type="button"
            className="text-primary/70 hover:text-primary text-[10px] mt-0.5 cursor-pointer"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? '收合 ▲' : '展開全文 ▼'}
          </button>
        )}
        {sol.affected_modules.length > 0 && (
          <div className="flex gap-1 mt-0.5 flex-wrap">
            {sol.affected_modules.map((m) => (
              <Badge key={m} variant="outline" className="text-[9px] px-1 py-0">
                {m}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
export interface DirectionResultCardProps {
  result: ContradictionDirectionResult;
}

// ---------------------------------------------------------------------------
// Sub-component: Direction block
// ---------------------------------------------------------------------------
function DirectionBlock({
  direction,
  score,
  rank,
}: {
  direction: DirectionGroup;
  score?: DirectionScore;
  rank: 'top1' | 'top2' | 'other';
}) {
  const [open, setOpen] = useState(rank === 'top1');

  const borderClass = rank === 'top1'
    ? 'border-yellow-400 bg-yellow-50/50 dark:bg-yellow-950/20'
    : rank === 'top2'
      ? 'border-blue-300 bg-blue-50/30 dark:bg-blue-950/10'
      : 'border-muted';

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn('border', borderClass)}>
        <CollapsibleTrigger asChild>
          <CardHeader className="p-3 cursor-pointer hover:bg-accent/30 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {rank === 'top1' && <Trophy className="h-4 w-4 text-yellow-500" />}
                {rank === 'top2' && <Medal className="h-4 w-4 text-blue-400" />}
                <CardTitle className="text-sm font-semibold">
                  {direction.direction_name}
                </CardTitle>
                <Badge variant="outline" className="text-[10px]">
                  TC:{direction.tc_count} PC:{direction.pc_count} SF:{direction.sf_count}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                {score && (
                  <span className="text-xs text-muted-foreground">
                    總分 {score.weighted_total.toFixed(1)}
                  </span>
                )}
                {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {direction.direction_summary}
            </p>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="p-3 pt-0 space-y-2">
            {/* Score details */}
            {score && (
              <div className="grid grid-cols-4 gap-2 text-[11px]">
                <div className="bg-muted/50 rounded p-1.5 text-center">
                  <div className="text-muted-foreground">工具支持</div>
                  <div className="font-bold">{score.tool_support}</div>
                </div>
                <div className="bg-muted/50 rounded p-1.5 text-center">
                  <div className="text-muted-foreground">可行性</div>
                  <div className="font-bold">{score.feasibility.toFixed(1)}</div>
                </div>
                <div className="bg-muted/50 rounded p-1.5 text-center">
                  <div className="text-muted-foreground">成本難度</div>
                  <div className="font-bold">{score.cost_difficulty.toFixed(1)}</div>
                </div>
                <div className="bg-muted/50 rounded p-1.5 text-center">
                  <div className="text-muted-foreground">覆蓋率</div>
                  <div className="font-bold">{score.coverage_score?.toFixed(1) ?? '—'}</div>
                </div>
              </div>
            )}
            {score?.score_rationale && (
              <p className="text-[11px] text-muted-foreground italic">
                {score.score_rationale}
              </p>
            )}

            {/* Solutions list */}
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-muted-foreground">
                解法清單（{direction.solutions.length}）
              </div>
              {direction.solutions.map((sol, i) => (
                <SolutionItem key={i} sol={sol} />
              ))}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function DirectionResultCard({ result }: DirectionResultCardProps) {
  const [cardOpen, setCardOpen] = useState(true);
  const [sortMode, setSortMode] = useState<SortMode>('weighted_total');
  const sev = SEVERITY_BADGE[result.severity] ?? SEVERITY_BADGE.unknown;
  const scoreMap = new Map(result.scored_directions.map((s) => [s.direction_id, s]));

  // Determine rank for each direction (system recommendation — stays constant)
  const top1Id = result.top1?.direction_id;
  const top2Id = result.top2?.direction_id;
  const getRank = (d: DirectionGroup): 'top1' | 'top2' | 'other' => {
    if (d.direction_id === top1Id) return 'top1';
    if (d.direction_id === top2Id) return 'top2';
    return 'other';
  };

  // Sort: when default mode, keep top1 first → top2 second → rest by score desc.
  // Otherwise sort purely by chosen metric (top1/top2 badges still shown but order follows metric).
  const sorted = [...result.all_directions].sort((a, b) => {
    if (sortMode === 'weighted_total') {
      const ra = getRank(a);
      const rb = getRank(b);
      const order = { top1: 0, top2: 1, other: 2 };
      if (order[ra] !== order[rb]) return order[ra] - order[rb];
    }
    const sa = getSortValue(scoreMap.get(a.direction_id), sortMode);
    const sb = getSortValue(scoreMap.get(b.direction_id), sortMode);
    return sb - sa; // descending (getSortValue already negates cost_difficulty)
  });

  return (
    <Collapsible open={cardOpen} onOpenChange={setCardOpen}>
      <Card className="border">
        <CollapsibleTrigger asChild>
          <CardHeader className="p-3 pb-2 cursor-pointer hover:bg-accent/30 transition-colors">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-sm flex items-center gap-2 min-w-0">
                <Zap className="h-4 w-4 text-primary shrink-0" />
                <span className="line-clamp-2">
                  {result.natural_description || result.contradiction_id}
                </span>
              </CardTitle>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={sev.variant}>{sev.label}</Badge>
                {cardOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </div>
            </div>
            <div className="flex gap-3 text-[11px] text-muted-foreground mt-1">
              <span>解法 {result.all_solutions.length} 條</span>
              <span>方向 {result.all_directions.length} 個</span>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="p-3 pt-0 space-y-2">
            {/* Sort mode selector */}
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              <Select value={sortMode} onValueChange={(v) => setSortMode(v as SortMode)}>
                <SelectTrigger className="h-7 w-[160px] text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SORT_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-[11px]">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {sorted.map((dir) => (
              <DirectionBlock
                key={dir.direction_id}
                direction={dir}
                score={scoreMap.get(dir.direction_id)}
                rank={getRank(dir)}
              />
            ))}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
