/**
 * DirectionResultCard — 顯示單一矛盾的方向分析結果 (v8).
 *
 * Shows:
 *   - All directions clustered from TC/PC/SF solutions
 *   - Scored directions with weighted totals
 *   - Top1 (highlighted) + Top2 (secondary)
 *   - Expandable solution details per direction
 *
 * 所有徽章標籤、顏色、Sort / Filter / Severity 文案都從 `directionTerms.ts`
 * 取，跟 DirectionTermsGlossary 共用一份資料源，加新狀態時只要動一個檔。
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
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
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
  BookOpen,
  HelpCircle,
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
  IntraContradictionCompatibility,
} from '@/types/directedTriz';
import { Checkbox } from '@/components/ui/checkbox';
import { ContradictionManifest } from '@/components/create/DecisionCardPanel';
import {
  RESOLUTION_STATUS_TERMS,
  ADDRESSES_LAYER_TERMS,
  VERDICT_TERMS,
  SR_KIND_TERMS,
  SCORE_COLUMN_TERMS,
  SORT_OPTIONS,
  FILTER_OPTIONS,
  SEVERITY_TERMS,
  getSortValue,
  type SortMode,
  type FilterMode,
  type GlossarySectionId,
} from './directionTerms';
import { DirectionTermsGlossary } from './DirectionTermsGlossary';

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
// Tooltip helper for glossary-linked help icons
// ---------------------------------------------------------------------------
function GlossaryHelp({
  description,
  onOpenGlossary,
  sectionId,
  size = 'sm',
}: {
  description: string;
  onOpenGlossary: (section: GlossarySectionId) => void;
  sectionId: GlossarySectionId;
  size?: 'sm' | 'xs';
}) {
  const sizeCls = size === 'xs' ? 'h-3 w-3' : 'h-3.5 w-3.5';
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onOpenGlossary(sectionId);
          }}
          className="text-muted-foreground hover:text-foreground transition-colors cursor-help shrink-0"
          aria-label="開啟名詞說明"
        >
          <HelpCircle className={sizeCls} />
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
        <p>{description}</p>
        <p className="text-[10px] text-muted-foreground mt-1">點擊查看完整說明</p>
      </TooltipContent>
    </Tooltip>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
export interface DirectionResultCardProps {
  result: ContradictionDirectionResult;
  /**
   * Phase 3 (E4)：父元件 (Create.tsx) 可選擇接管 pickedSet 以便在整併按鈕
   * 收集所有矛盾的勾選結果送進 backend.picks。
   * 若未提供 → 元件自行維護內部 state（向後相容）。
   */
  pickedSet?: Set<string>;
  onPickedChange?: (next: Set<string>) => void;
  /**
   * Phase 3 (E5)：當該矛盾完成同矛盾相容性檢查後傳入，顯示警示條。
   */
  intraCompatibility?: IntraContradictionCompatibility | null;
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
  picked,
  onPickChange,
  onOpenGlossary,
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
  /** RD 是否已勾選此方向（為跨矛盾整併準備）。 */
  picked: boolean;
  /** 勾選狀態變更回呼。 */
  onPickChange: (picked: boolean) => void;
  /** 開啟 Glossary 並跳到指定節。 */
  onOpenGlossary: (section: GlossarySectionId) => void;
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
  const statusTerm = RESOLUTION_STATUS_TERMS[statusKey];
  const layerKey = audit?.addresses_layer ?? null;
  const layerTerm = layerKey ? ADDRESSES_LAYER_TERMS[layerKey] : null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn('border', borderClass)}>
        <CardHeader className="p-3 hover:bg-accent/30 transition-colors">
          <div className="flex items-center gap-2">
            {/* Phase 2 (A3): 勾選 checkbox — 不在 CollapsibleTrigger 內，
                免得點 checkbox 同時展開 / 收合 */}
            <Checkbox
              checked={picked}
              onCheckedChange={(c) => onPickChange(c === true)}
              aria-label={`勾選方向 ${direction.direction_name}`}
              className="shrink-0"
            />

            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="flex flex-col items-stretch gap-1 flex-1 min-w-0 text-left cursor-pointer"
              >
                <div className="flex items-center gap-2 flex-wrap min-w-0">
                  {rank === 'top1' && <Trophy className="h-4 w-4 text-yellow-500 shrink-0" />}
                  {rank === 'top2' && <Medal className="h-4 w-4 text-blue-400 shrink-0" />}
                  <CardTitle className="text-sm font-semibold">
                    {direction.direction_name}
                  </CardTitle>

                  {/* Resolution Status badge — wrapped in Tooltip with description. */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge
                        variant="outline"
                        className={cn('text-[10px] border cursor-help', statusTerm.className)}
                      >
                        {statusTerm.label}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                      {statusTerm.description}
                    </TooltipContent>
                  </Tooltip>

                  {/* Addresses Layer badge — newly tooltipped. */}
                  {layerTerm && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge
                          variant="outline"
                          className={cn('text-[10px] border cursor-help', layerTerm.className)}
                        >
                          {layerTerm.label}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                        {layerTerm.description}
                      </TooltipContent>
                    </Tooltip>
                  )}

                  <Badge variant="outline" className="text-[10px]">
                    TC:{direction.tc_count} PC:{direction.pc_count} SF:{direction.sf_count}
                  </Badge>
                  <span className="flex-1" />
                  {score && (
                    <span className="text-xs text-muted-foreground shrink-0">
                      總分 {score.weighted_total.toFixed(1)}
                    </span>
                  )}
                  {open ? <ChevronUp className="h-3 w-3 shrink-0" /> : <ChevronDown className="h-3 w-3 shrink-0" />}
                </div>
                <p className="text-xs text-muted-foreground">
                  {direction.direction_summary}
                </p>
              </button>
            </CollapsibleTrigger>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="p-3 pt-0 space-y-2">
            {/* Score details — each cell wrapped in Tooltip pulling from
                directionTerms.ts so the wording is identical to the
                Glossary's "4 個分數欄位" section.                       */}
            {score && (
              <div className="grid grid-cols-4 gap-2 text-[11px]">
                {SCORE_COLUMN_TERMS.map((col) => {
                  const value =
                    col.key === 'tool_support'
                      ? score.tool_support
                      : col.key === 'feasibility'
                        ? score.feasibility
                        : col.key === 'cost_difficulty'
                          ? score.cost_difficulty
                          : score.coverage_score;
                  const display =
                    col.key === 'tool_support'
                      ? value
                      : (value as number | undefined)?.toFixed?.(1) ?? '—';
                  return (
                    <Tooltip key={col.key}>
                      <TooltipTrigger asChild>
                        <div className="bg-muted/50 rounded p-1.5 text-center cursor-help">
                          <div className="text-muted-foreground">{col.label}</div>
                          <div className="font-bold">{display}</div>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                        <p>{col.description}</p>
                        <button
                          type="button"
                          className="text-[10px] text-primary underline mt-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenGlossary('score_columns');
                          }}
                        >
                          查看 4 個分數欄位的完整說明 →
                        </button>
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
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
                plain-language sentence. */}
            {audit && subRequirements.length > 0 && (
              <div className="space-y-1.5 border-t border-dashed pt-2">
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
                      <div className="flex items-center gap-1 font-medium text-foreground/80">
                        <span>
                          這條矛盾的 {subRequirements.length} 個需求面向（閱讀背景，不是驗收條件）：
                        </span>
                        <GlossaryHelp
                          description="這些 SR 子需求只是「閱讀背景」，幫你看懂矛盾在說什麼；真正驗收要等跨矛盾整併後的 Brief 任務檢核。"
                          onOpenGlossary={onOpenGlossary}
                          sectionId="why_not_verdict"
                          size="xs"
                        />
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
                    const verdictKey: PerSrVerdict =
                      (entry?.verdict as PerSrVerdict | undefined) ??
                      (entry ? 'unclear' : 'not_addressed');
                    const vTerm = VERDICT_TERMS[verdictKey];
                    const verdictSentence =
                      entry?.verdict_zh ||
                      entry?.rationale ||
                      entry?.note ||
                      (entry
                        ? '（這個方向對這條沒給出明確判斷）'
                        : '這個方向沒有觸及這條需求面向。');
                    const kindTerm = sr.kind ? SR_KIND_TERMS[sr.kind] : undefined;
                    const sourceLabel = formatSourceRef(sr.source_ref);

                    return (
                      <div
                        key={sr.id}
                        className="flex items-start gap-2 text-[11px] bg-muted/30 rounded p-2"
                      >
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span
                              className={cn(
                                'inline-block w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 cursor-help',
                                vTerm.dotClass,
                              )}
                              aria-label={vTerm.label}
                            />
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                            <span className={cn('font-medium', vTerm.className)}>
                              {vTerm.icon} {vTerm.label}
                            </span>
                            <span> — {vTerm.description}</span>
                          </TooltipContent>
                        </Tooltip>
                        <div className="flex-1 min-w-0 space-y-1">
                          {/* TOP HALF: the GOAL itself (what must be true). */}
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="font-semibold text-foreground">
                                需求 {idx + 1}
                              </span>
                              {kindTerm && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Badge
                                      variant="outline"
                                      className={cn('text-[9px] px-1 py-0 cursor-help border-0', kindTerm.tone)}
                                    >
                                      {kindTerm.tag}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                                    {kindTerm.description}
                                  </TooltipContent>
                                </Tooltip>
                              )}
                              {sourceLabel && (
                                <span className="text-[9px] text-muted-foreground">
                                  （{sourceLabel}）
                                </span>
                              )}
                              <span className="text-[9px] text-muted-foreground/60 ml-auto">
                                {sr.id}
                              </span>
                            </div>
                            <div className="text-foreground/90">
                              {sr.description}
                            </div>
                          </div>
                          <hr className="border-t border-dashed border-foreground/15 my-1" />
                          {/* BOTTOM HALF: this direction's verdict on the goal. */}
                          <div className={cn('flex items-baseline gap-1 flex-wrap', vTerm.className)}>
                            <span className="font-medium shrink-0">
                              本方案：{vTerm.icon} {vTerm.label}
                            </span>
                            <span className="text-foreground/80">{verdictSentence}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Side-effect warning — direction-level concern. */}
                {audit.cld_side_effects && audit.cld_side_effects.length > 0 && (
                  <div className="text-[11px] bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded p-1.5 space-y-1">
                    <div className="font-medium text-amber-800 dark:text-amber-200">
                      ⚠️ 副作用警示
                    </div>
                    {audit.cld_side_effects.map((effect, i) => {
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
export function DirectionResultCard({
  result,
  pickedSet: pickedSetProp,
  onPickedChange,
  intraCompatibility,
}: DirectionResultCardProps) {
  const [cardOpen, setCardOpen] = useState(true);
  const [sortMode, setSortMode] = useState<SortMode>('tool_support');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');

  // Glossary state — opened on demand by the 📖 button or any inline ? icon.
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [glossarySection, setGlossarySection] = useState<GlossarySectionId | undefined>(undefined);
  const openGlossary = (section: GlossarySectionId) => {
    setGlossarySection(section);
    setGlossaryOpen(true);
  };

  // Phase 2 (A3) → Phase 3 (E4):
  //   - 若父元件 (Create.tsx) 接管 pickedSet，這條 state 不會被讀；
  //   - 否則 fallback 為自管 state 以保持元件可單獨使用。
  const [internalPickedSet, setInternalPickedSet] = useState<Set<string>>(new Set());
  const pickedSet = pickedSetProp ?? internalPickedSet;
  const setPickedSet = (updater: (prev: Set<string>) => Set<string>) => {
    if (onPickedChange) {
      onPickedChange(updater(pickedSet));
    } else {
      setInternalPickedSet(updater);
    }
  };

  const sev = SEVERITY_TERMS[result.severity] ?? SEVERITY_TERMS.unknown;
  const scoreMap = new Map(result.scored_directions.map((s) => [s.direction_id, s]));
  // Coverage audits indexed by direction_id for O(1) lookup in the loop.
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
    return sb - sa; // descending
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

  // Tooltips for the currently-selected sort/filter
  const currentSortDesc = SORT_OPTIONS.find((o) => o.value === sortMode)?.description ?? '';
  const currentFilterDesc = FILTER_OPTIONS.find((o) => o.value === filterMode)?.description ?? '';

  return (
    <>
      <Collapsible open={cardOpen} onOpenChange={setCardOpen}>
        <Card className="border">
          <CardHeader className="p-3 pb-2">
            <div className="flex items-center justify-between gap-2">
              <CollapsibleTrigger asChild>
                <button
                  type="button"
                  className="flex-1 min-w-0 text-left cursor-pointer hover:bg-accent/30 transition-colors rounded -mx-1 px-1 py-0.5"
                >
                  <CardTitle className="text-sm flex items-center gap-2 min-w-0">
                    <Zap className="h-4 w-4 text-primary shrink-0" />
                    <span className="line-clamp-2">
                      {result.natural_description || result.contradiction_id}
                    </span>
                  </CardTitle>
                </button>
              </CollapsibleTrigger>
              <div className="flex items-center gap-1.5 shrink-0">
                {/* Severity badge — tooltipped */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge variant={sev.variant} className="cursor-help">
                      {sev.label}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                    {sev.description}
                  </TooltipContent>
                </Tooltip>

                {/* 📖 名詞說明 button — opens the Glossary sheet. */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-[11px] gap-1"
                      onClick={() => openGlossary('manifest')}
                    >
                      <BookOpen className="h-3.5 w-3.5" />
                      名詞說明
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                    開啟「📖 名詞說明」拉桿，逐節解釋徽章、評語、Sort/Filter 等所有術語。
                  </TooltipContent>
                </Tooltip>

                <CollapsibleTrigger asChild>
                  <button type="button" className="text-muted-foreground hover:text-foreground">
                    {cardOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>
                </CollapsibleTrigger>
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
          <CollapsibleContent>
            <CardContent className="p-3 pt-0 space-y-2">
              {/* Sort + filter selectors — both gain ? icons that open the
                  Glossary directly to the "Sort / Filter 用法" section. */}
              <div className="flex items-center gap-2 flex-wrap">
                <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <div className="flex items-center gap-1">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div>
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
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                      <p className="font-medium mb-0.5">目前排序：</p>
                      <p>{currentSortDesc}</p>
                    </TooltipContent>
                  </Tooltip>
                  <GlossaryHelp
                    description="共 4 種排序方式 — 點擊查看完整說明與適用場景。"
                    onOpenGlossary={openGlossary}
                    sectionId="sort_filter"
                  />
                </div>

                <div className="flex items-center gap-1">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div>
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
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                      <p className="font-medium mb-0.5">目前篩選：</p>
                      <p>{currentFilterDesc}</p>
                    </TooltipContent>
                  </Tooltip>
                  <GlossaryHelp
                    description="共 4 種篩選方式 — 點擊查看完整說明與適用場景。"
                    onOpenGlossary={openGlossary}
                    sectionId="sort_filter"
                  />
                </div>
              </div>

              {/* Phase 1 (A0): 矛盾說明書 — 取代舊「必須全部成立」宣告。 */}
              <ContradictionManifest
                contradictionDescription={result.natural_description}
                subRequirements={subRequirements}
                weakWarnings={result.sr_weak_warnings ?? []}
              />

              {/* Phase 3 (E5): 同矛盾多選相容性警示 — 整併後產出 */}
              {intraCompatibility &&
                intraCompatibility.picked_direction_ids.length >= 2 && (
                  <div
                    className={cn(
                      'rounded-md border text-[11px] p-2 space-y-1',
                      intraCompatibility.has_conflict
                        ? 'border-orange-300 bg-orange-50 dark:bg-orange-950/30 dark:border-orange-700'
                        : 'border-emerald-300 bg-emerald-50 dark:bg-emerald-950/30 dark:border-emerald-700'
                    )}
                  >
                    <div className="font-medium">
                      {intraCompatibility.has_conflict
                        ? `⚠️ 同矛盾勾選衝突：${
                            intraCompatibility.pairwise_results.filter((p) => !p.compatible).length
                          } 對方向有衝突`
                        : `✅ 同矛盾勾選相容：${intraCompatibility.picked_direction_ids.length} 個方向可一起整併`}
                    </div>
                    {intraCompatibility.has_conflict &&
                      intraCompatibility.max_compatible_subsets.length > 0 && (
                        <div>
                          推薦組合：
                          <span className="font-mono ml-1">
                            {intraCompatibility.max_compatible_subsets[0].join(' + ')}
                          </span>
                        </div>
                      )}
                    {intraCompatibility.recommendation && (
                      <div className="text-muted-foreground">{intraCompatibility.recommendation}</div>
                    )}
                  </div>
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
                  picked={pickedSet.has(dir.direction_id)}
                  onPickChange={(picked) => {
                    setPickedSet((prev) => {
                      const next = new Set(prev);
                      if (picked) next.add(dir.direction_id);
                      else next.delete(dir.direction_id);
                      return next;
                    });
                  }}
                  onOpenGlossary={openGlossary}
                />
              ))}
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Glossary Sheet — single instance per card. */}
      <DirectionTermsGlossary
        open={glossaryOpen}
        onOpenChange={setGlossaryOpen}
        defaultSectionId={glossarySection}
      />
    </>
  );
}
