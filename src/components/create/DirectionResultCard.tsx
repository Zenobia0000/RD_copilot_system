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
  DirectionCoverageAudit,
  ResolutionStatus,
  SubRequirement,
  CoverageEntry,
  PerSrVerdict,
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
// Resolution status badge config (context-aware coverage audit, 方案 A)
// ---------------------------------------------------------------------------
// 5-state semantic verdict for whether a direction truly resolves the
// contradiction in its original problem context. See:
//   backend/app/agents/triz_solver.py::RESOLUTION_STATUS_MULTIPLIER
//   backend/app/prompts/triz_solver.py::RESOLUTION_COVERAGE_AUDIT_PROMPT
//
// Colour mapping mirrors the architect plan (directly=green / partially=yellow
// / conditionally=orange / does_not=red / unclear=gray). All Tailwind
// classes here are static strings so the JIT picks them up correctly.
const RESOLUTION_STATUS_BADGE: Record<
  ResolutionStatus,
  { label: string; className: string; tooltip: string }
> = {
  directly_resolves: {
    label: '✓ 直接解決',
    className: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-950 dark:text-green-200',
    tooltip: '同時改善目標、抑制副作用，未明顯違反邊界',
  },
  partially_resolves: {
    label: '◐ 部分解決',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-950 dark:text-yellow-200',
    tooltip: '只解到一面，或只處理症狀而非根因',
  },
  conditionally_resolves: {
    label: '⚠ 條件成立',
    className: 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-950 dark:text-orange-200',
    tooltip: '理論上可行，但依賴尚未證明的關鍵假設',
  },
  does_not_resolve: {
    label: '✗ 未解到',
    className: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-200',
    tooltip: '與矛盾關聯弱，或違反 mission/KPI/邊界',
  },
  unclear: {
    label: '? 資訊不足',
    className: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300',
    tooltip: '資訊不足，無法可靠判定',
  },
};

const ADDRESSES_LAYER_LABEL: Record<string, string> = {
  root_cause: '解根因',
  mechanism: '解機制',
  symptom: '解症狀',
  unclear: '層級不明',
};

// ---------------------------------------------------------------------------
// Per-SR verdict UI config (SR-grouped audit, RD-friendly rewrite)
// ---------------------------------------------------------------------------
// Each entry tells the SR row what icon / colour / one-liner to show
// when this direction's stance on THIS specific SR is X. Keeps the row
// scannable for a non-systems-thinker RD: see icon + 1 sentence.
const VERDICT_BADGE: Record<
  PerSrVerdict,
  { icon: string; label: string; className: string; dotClass: string }
> = {
  directly_solves: {
    icon: '✓',
    label: '直接解',
    className: 'text-green-700 dark:text-green-300',
    dotClass: 'bg-green-500',
  },
  partially_solves: {
    icon: '◐',
    label: '部分支撐',
    className: 'text-yellow-700 dark:text-yellow-300',
    dotClass: 'bg-yellow-500',
  },
  needs_verify: {
    icon: '⚠',
    label: '要驗證',
    className: 'text-orange-700 dark:text-orange-300',
    dotClass: 'bg-orange-500',
  },
  violates: {
    icon: '✗',
    label: '違反',
    className: 'text-red-700 dark:text-red-300',
    dotClass: 'bg-red-500',
  },
  not_addressed: {
    icon: '·',
    label: '未觸及',
    className: 'text-muted-foreground',
    dotClass: 'bg-gray-400',
  },
  unclear: {
    icon: '?',
    label: '不清楚',
    className: 'text-muted-foreground',
    dotClass: 'bg-gray-400',
  },
};

// SR kind labels — the LLM tags every "達成目標" with one of 4 kinds.
// Labels intentionally avoid the word 「目標」 inside the tag because
// the wrapping section is already called 「達成目標」; using the same
// word again would clash visually and conceptually.
const SR_KIND_TAG: Record<string, { tag: string; tagDescription: string }> = {
  desired_improvement: { tag: '想改善', tagDescription: '矛盾想要更多更好的東西' },
  undesired_effect: { tag: '想避免', tagDescription: '矛盾想要擋住別變更糟的東西' },
  boundary_condition: { tag: '不可違反', tagDescription: '硬限制 / 一旦違反整個方案就無效' },
  mission_outcome: { tag: '驗收標準', tagDescription: 'KPI 等級的最終承諾' },
};

/** Pull the sub_requirement_id out of an entry regardless of legacy/new shape. */
function entrySrId(e: CoverageEntry): string {
  return (e.sub_requirement_id ?? e.sub_req_id ?? '').trim();
}

/**
 * Pretty-print the source_ref so RD knows where this SR came from.
 * "constraint:C2" → "約束 C2"; "kpi:K1" → "KPI K1"; etc.
 */
function formatSourceRef(ref?: string): string {
  if (!ref) return '';
  const r = ref.trim();
  if (!r) return '';
  if (r === 'mission') return '來自 mission';
  if (r === 'contradiction') return '矛盾本身';
  if (r === 'socratic') return '來自蘇格拉底問答';
  if (r === 'cld') return '來自 CLD';
  if (r.startsWith('constraint:')) return `約束 ${r.slice('constraint:'.length)}`;
  if (r.startsWith('kpi:')) return `KPI ${r.slice('kpi:'.length)}`;
  return r;
}

// ---------------------------------------------------------------------------
// Filter mode config — RD-facing shortcuts for the 5-state verdict
// ---------------------------------------------------------------------------
type FilterMode =
  | 'all'
  | 'directly_only'
  | 'hide_does_not'
  | 'with_assumptions';

const FILTER_OPTIONS: { value: FilterMode; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'directly_only', label: '只看直接解決' },
  { value: 'hide_does_not', label: '藏掉未解到' },
  { value: 'with_assumptions', label: '只看條件解 (依賴假設)' },
];

// ---------------------------------------------------------------------------
// Sort mode config
// ---------------------------------------------------------------------------
type SortMode = 'tool_support' | 'feasibility' | 'cost_difficulty' | 'coverage';

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'tool_support', label: '工具共識優先' },
  { value: 'feasibility', label: '可行性優先' },
  { value: 'cost_difficulty', label: '成本難度優先' },
  { value: 'coverage', label: '覆蓋率優先' },
];

/** Return the score value for a given sort mode. cost_difficulty is ascending (lower = better). */
function getSortValue(score: DirectionScore | undefined, mode: SortMode): number {
  if (!score) return mode === 'cost_difficulty' ? Infinity : -Infinity;
  switch (mode) {
    case 'tool_support': return score.tool_support;
    case 'feasibility': return score.feasibility;
    case 'cost_difficulty': return -score.cost_difficulty; // negate so ascending sort = lower cost first
    case 'coverage': return score.coverage_score;
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
  audit,
  subRequirements,
  rank,
}: {
  direction: DirectionGroup;
  score?: DirectionScore;
  audit?: DirectionCoverageAudit;
  /**
   * Full sub-requirement list from this contradiction (NOT a slice).
   * The SR-grouped view iterates this so every SR row appears in the
   * same order across every direction — even if a direction did not
   * audit some SRs (they show up as "未觸及"). This is what makes the
   * UI scannable side-by-side.
   */
  subRequirements: SubRequirement[];
  rank: 'top1' | 'top2' | 'other';
}) {
  const [open, setOpen] = useState(rank === 'top1');

  const borderClass = rank === 'top1'
    ? 'border-yellow-400 bg-yellow-50/50 dark:bg-yellow-950/20'
    : rank === 'top2'
      ? 'border-blue-300 bg-blue-50/30 dark:bg-blue-950/10'
      : 'border-muted';

  // Resolution status fallback to 'unclear' so legacy rows without
  // context-aware audit still render a deterministic badge.
  const statusKey: ResolutionStatus = audit?.resolution_status ?? 'unclear';
  const statusConfig = RESOLUTION_STATUS_BADGE[statusKey];
  const layerLabel = audit?.addresses_layer
    ? ADDRESSES_LAYER_LABEL[audit.addresses_layer] ?? audit.addresses_layer
    : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn('border', borderClass)}>
        <CollapsibleTrigger asChild>
          <CardHeader className="p-3 cursor-pointer hover:bg-accent/30 transition-colors">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 flex-wrap min-w-0">
                {rank === 'top1' && <Trophy className="h-4 w-4 text-yellow-500 shrink-0" />}
                {rank === 'top2' && <Medal className="h-4 w-4 text-blue-400 shrink-0" />}
                <CardTitle className="text-sm font-semibold">
                  {direction.direction_name}
                </CardTitle>
                {/* 5-state resolution status badge (context-aware audit) */}
                <Badge
                  variant="outline"
                  className={cn('text-[10px] border', statusConfig.className)}
                  title={statusConfig.tooltip}
                >
                  {statusConfig.label}
                </Badge>
                {layerLabel && (
                  <Badge variant="outline" className="text-[10px]">
                    {layerLabel}
                  </Badge>
                )}
                <Badge variant="outline" className="text-[10px]">
                  TC:{direction.tc_count} PC:{direction.pc_count} SF:{direction.sf_count}
                </Badge>
              </div>
              <div className="flex items-center gap-2 shrink-0">
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

            {/* SR-grouped audit (context-aware, RD-friendly rewrite).
                Every SR gets one row. The row shows what THIS direction
                does for THAT SR using a 5-state verdict + a single
                plain-language sentence. Replaces the old 3-section
                layout (依賴假設 / 違反 / 未涵蓋) that forced RD to
                cross-reference. */}
            {audit && subRequirements.length > 0 && (
              <div className="space-y-1.5 border-t border-dashed pt-2">
                {/* Direction-level 局勢彙總 — single-glance count of how
                    many "達成目標" this direction handles vs leaves to
                    verification vs ignores. Computed inline so it
                    stays in sync with the rows below without a useMemo
                    dance (subRequirements is short).                  */}
                {(() => {
                  const entries = audit.coverage_matrix ?? audit.entries ?? [];
                  const counts: Record<PerSrVerdict, number> = {
                    directly_solves: 0,
                    partially_solves: 0,
                    needs_verify: 0,
                    violates: 0,
                    not_addressed: 0,
                    unclear: 0,
                  };
                  for (const sr of subRequirements) {
                    const entry = entries.find((e) => entrySrId(e) === sr.id);
                    const v: PerSrVerdict =
                      (entry?.verdict as PerSrVerdict | undefined) ??
                      (entry ? 'unclear' : 'not_addressed');
                    counts[v] += 1;
                  }
                  const parts: string[] = [];
                  if (counts.directly_solves) parts.push(`✓ ${counts.directly_solves} 條已解`);
                  if (counts.needs_verify) parts.push(`⚠ ${counts.needs_verify} 條要驗證`);
                  if (counts.partially_solves) parts.push(`◐ ${counts.partially_solves} 條間接支撐`);
                  if (counts.violates) parts.push(`✗ ${counts.violates} 條違反`);
                  if (counts.not_addressed) parts.push(`· ${counts.not_addressed} 條未觸及`);
                  if (counts.unclear) parts.push(`? ${counts.unclear} 條不清楚`);
                  return (
                    <div className="text-[11px] bg-muted/40 rounded p-2 space-y-0.5">
                      <div className="font-medium text-foreground/80">
                        這個矛盾要算解掉，下面 {subRequirements.length} 個達成目標必須全部成立：
                      </div>
                      <div className="text-foreground/90">
                        本方向局勢：{parts.join('　')}
                      </div>
                      {audit.gap_summary && (
                        <div className="text-muted-foreground italic">
                          脈絡判斷：{audit.gap_summary}
                        </div>
                      )}
                    </div>
                  );
                })()}

                <div className="space-y-2">
                  {subRequirements.map((sr, idx) => {
                    const entry = (audit.coverage_matrix ?? audit.entries ?? []).find(
                      (e) => entrySrId(e) === sr.id,
                    );
                    // No entry for this SR → treat as not_addressed so
                    // the row is still visible (a missing entry is
                    // itself information: the direction ignored this SR).
                    const verdictKey: PerSrVerdict =
                      (entry?.verdict as PerSrVerdict | undefined) ??
                      (entry ? 'unclear' : 'not_addressed');
                    const vb = VERDICT_BADGE[verdictKey];
                    const verdictSentence =
                      entry?.verdict_zh ||
                      entry?.rationale ||
                      entry?.note ||
                      (entry
                        ? '（這個方向對這條沒給出明確判斷）'
                        : '這個方向沒有觸及這條達成目標。');
                    const kindTag = sr.kind ? SR_KIND_TAG[sr.kind] : undefined;
                    const sourceLabel = formatSourceRef(sr.source_ref);

                    return (
                      <div
                        key={sr.id}
                        className="flex items-start gap-2 text-[11px] bg-muted/30 rounded p-2"
                      >
                        <span
                          className={cn('inline-block w-1.5 h-1.5 rounded-full mt-1.5 shrink-0', vb.dotClass)}
                          aria-hidden
                        />
                        <div className="flex-1 min-w-0 space-y-1">
                          {/* TOP HALF: the GOAL itself (what must be true). */}
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="font-semibold text-foreground">
                                達成目標 {idx + 1}
                              </span>
                              {kindTag && (
                                <Badge
                                  variant="outline"
                                  className="text-[9px] px-1 py-0"
                                  title={kindTag.tagDescription}
                                >
                                  {kindTag.tag}
                                </Badge>
                              )}
                              {sourceLabel && (
                                <span className="text-[9px] text-muted-foreground">
                                  （{sourceLabel}）
                                </span>
                              )}
                              {/* Internal id kept for cross-talk/searches
                                  but visually weak so first-time readers
                                  do not get distracted by SR-x codes. */}
                              <span className="text-[9px] text-muted-foreground/60 ml-auto">
                                {sr.id}
                              </span>
                            </div>
                            <div className="text-foreground/90">
                              {sr.description}
                            </div>
                          </div>
                          {/* Divider — visually separates the GOAL (题目)
                              from this direction's RESULT (this方案的成績). */}
                          <hr className="border-t border-dashed border-foreground/15 my-1" />
                          {/* BOTTOM HALF: this direction's verdict on the goal. */}
                          <div className={cn('flex items-baseline gap-1', vb.className)}>
                            <span className="font-medium shrink-0">
                              本方案：{vb.icon} {vb.label}
                            </span>
                            <span className="text-foreground/80">{verdictSentence}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Side-effect warning — separate block because it is a
                    direction-level concern, not per-SR. */}
                {audit.cld_side_effects && audit.cld_side_effects.length > 0 && (
                  <div className="text-[11px] bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded p-1.5 space-y-1">
                    <div className="font-medium text-amber-800 dark:text-amber-200">
                      ⚠️ 副作用警示
                    </div>
                    {audit.cld_side_effects.map((effect, i) => {
                      // The prompt asks the LLM to emit two parts:
                      //   "<白話結果>. (技術註腳: <CLD 路徑>)"
                      // Split on the literal "(技術註腳" tag so the
                      // technical detail lives in a smaller, italic
                      // tail — RD reads the plain-language sentence
                      // first, only digs into the trace when needed.
                      const noteMarker = '(技術註腳';
                      const idx = effect.indexOf(noteMarker);
                      const plain = idx >= 0 ? effect.slice(0, idx).trim() : effect;
                      const note = idx >= 0
                        ? effect.slice(idx).replace(/^\(|\)$/g, '').trim()
                        : '';
                      return (
                        <div key={i} className="space-y-0.5">
                          <p className="text-foreground/90">{plain}</p>
                          {note && (
                            <p className="text-[10px] text-muted-foreground italic">
                              {note}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
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
  const [sortMode, setSortMode] = useState<SortMode>('tool_support');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const sev = SEVERITY_BADGE[result.severity] ?? SEVERITY_BADGE.unknown;
  const scoreMap = new Map(result.scored_directions.map((s) => [s.direction_id, s]));
  // Coverage audits indexed by direction_id for O(1) lookup in the loop.
  // Legacy rows without audits silently fall through to `undefined` so
  // DirectionBlock uses the 'unclear' fallback rather than crashing.
  const auditMap = new Map(
    (result.coverage_audits ?? []).map((a) => [a.direction_id, a]),
  );
  // SR list for this contradiction. Passed to every DirectionBlock so
  // every direction renders the same SR rows in the same order — the
  // RD can scan multiple directions vertically and compare verdicts.
  const subRequirements: SubRequirement[] = result.sub_requirements ?? [];

  // Determine rank for each direction (system recommendation — stays constant)
  const top1Id = result.top1?.direction_id;
  const top2Id = result.top2?.direction_id;
  const getRank = (d: DirectionGroup): 'top1' | 'top2' | 'other' => {
    if (d.direction_id === top1Id) return 'top1';
    if (d.direction_id === top2Id) return 'top2';
    return 'other';
  };

  // Apply context-aware filter (5-state verdict) BEFORE sort.
  const filtered = result.all_directions.filter((d) => {
    if (filterMode === 'all') return true;
    const status = auditMap.get(d.direction_id)?.resolution_status ?? 'unclear';
    switch (filterMode) {
      case 'directly_only':
        return status === 'directly_resolves';
      case 'hide_does_not':
        // Hide does_not_resolve; keep unclear visible (RD may still inspect).
        return status !== 'does_not_resolve';
      case 'with_assumptions':
        return status === 'conditionally_resolves';
      default:
        return true;
    }
  });

  // Sort purely by chosen metric (top1/top2 badges still shown but order follows metric).
  const sorted = [...filtered].sort((a, b) => {
    const sa = getSortValue(scoreMap.get(a.direction_id), sortMode);
    const sb = getSortValue(scoreMap.get(b.direction_id), sortMode);
    return sb - sa; // descending (getSortValue already negates cost_difficulty)
  });

  // Count by status for the header chip — gives RD instant signal of
  // how many of the candidates actually resolve in context.
  const statusCounts = result.all_directions.reduce<Record<ResolutionStatus, number>>(
    (acc, d) => {
      const s = auditMap.get(d.direction_id)?.resolution_status ?? 'unclear';
      acc[s] = (acc[s] ?? 0) + 1;
      return acc;
    },
    {
      directly_resolves: 0,
      partially_resolves: 0,
      conditionally_resolves: 0,
      does_not_resolve: 0,
      unclear: 0,
    },
  );

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
            <div className="flex gap-3 text-[11px] text-muted-foreground mt-1 flex-wrap">
              <span>解法 {result.all_solutions.length} 條</span>
              <span>方向 {result.all_directions.length} 個</span>
              {statusCounts.directly_resolves > 0 && (
                <span className="text-green-700 dark:text-green-300">
                  ✓ 直接解 {statusCounts.directly_resolves}
                </span>
              )}
              {statusCounts.conditionally_resolves > 0 && (
                <span className="text-orange-700 dark:text-orange-300">
                  ⚠ 條件解 {statusCounts.conditionally_resolves}
                </span>
              )}
              {statusCounts.does_not_resolve > 0 && (
                <span className="text-red-700 dark:text-red-300">
                  ✗ 未解到 {statusCounts.does_not_resolve}
                </span>
              )}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="p-3 pt-0 space-y-2">
            {/* Sort + filter selectors */}
            <div className="flex items-center gap-2 flex-wrap">
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
              <Select value={filterMode} onValueChange={(v) => setFilterMode(v as FilterMode)}>
                <SelectTrigger className="h-7 w-[180px] text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FILTER_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-[11px]">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sub-requirement overview (context-aware audit, 方案 A).
                Shows EVERY SR for the contradiction once, up-front, so
                the RD knows what "SR-3" means before scanning per-
                direction verdicts below. Collapsed by default to keep
                the card density manageable. */}
            {subRequirements.length > 0 && (
              <details className="text-[11px] border border-dashed rounded p-2">
                <summary className="cursor-pointer font-medium text-muted-foreground">
                  這個矛盾要算解掉，下面 {subRequirements.length} 個達成目標必須全部成立（點開看）
                </summary>
                <ol className="space-y-1 mt-2 list-decimal pl-5">
                  {subRequirements.map((sr) => {
                    const kindTag = sr.kind ? SR_KIND_TAG[sr.kind] : undefined;
                    const sourceLabel = formatSourceRef(sr.source_ref);
                    return (
                      <li key={sr.id} className="flex items-start gap-1.5 flex-wrap">
                        {kindTag && (
                          <Badge variant="outline" className="text-[9px] px-1 py-0 shrink-0" title={kindTag.tagDescription}>
                            {kindTag.tag}
                          </Badge>
                        )}
                        <span className="text-foreground/90 flex-1 min-w-[200px]">{sr.description}</span>
                        {sourceLabel && (
                          <span className="text-[10px] text-muted-foreground shrink-0">
                            （{sourceLabel}）
                          </span>
                        )}
                        <span className="text-[9px] text-muted-foreground/60 shrink-0">
                          {sr.id}
                        </span>
                      </li>
                    );
                  })}
                </ol>
                <p className="text-[10px] text-muted-foreground mt-2 leading-snug">
                  標籤說明：
                  「<b>想改善</b>」=矛盾想要更多更好的東西；
                  「<b>想避免</b>」=矛盾想要擋住別變更糟的東西；
                  「<b>不可違反</b>」=硬限制，一旦違反整個方案就無效；
                  「<b>驗收標準</b>」=KPI 等級的最終承諾。
                </p>
              </details>
            )}

            {sorted.length === 0 && (
              <div className="text-[11px] text-muted-foreground italic p-3 text-center">
                目前篩選條件沒有符合的方向
              </div>
            )}

            {sorted.map((dir) => (
              <DirectionBlock
                key={dir.direction_id}
                direction={dir}
                score={scoreMap.get(dir.direction_id)}
                audit={auditMap.get(dir.direction_id)}
                subRequirements={subRequirements}
                rank={getRank(dir)}
              />
            ))}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
