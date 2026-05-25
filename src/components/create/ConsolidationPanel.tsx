/**
 * ConsolidationPanel — 顯示跨矛盾方向整併結果 (v8 + PR2-Lite).
 *
 * Three states:
 *   - compatible: all adopted directions are mutually compatible → green
 *   - resolved_with_swap: 演算法 swap 池內方向後相容 → amber
 *   - conflict: 池用盡 / 卡住 → red，顯示「卡點分析」與行動建議
 *
 * Phase 3 / PR2-Lite UI 特性：
 *   1. 採納方向的徽章區分三種情境
 *      a. cid ∈ was_user_picked → 「使用您勾選的方向」（藍色）
 *      b. 採用方向 ≠ Top1 且 cid ∉ was_user_picked → 「Top2 替換」（琥珀色）
 *      c. 其餘 → 不顯示徽章（系統 Top1）
 *   2. PR2-Lite：每條矛盾下展開「候選池」清單，顯示其他 fallback 方向
 *   3. PR1-8 (conflict B 方案)：
 *      - 標題：「您勾選的方向無法全部整併」+「AI 嘗試 N 種組合」
 *      - 卡點分析：exhausted_contradictions 列表 + 提示加勾
 *      - 衝突 pair 結構化呈現（已由 ConflictReport 提供）
 *   4. PR3-1：status badge 旁加 ⓘ tooltip，揭露「LLM 整併 ≠ 物理可行」限制
 */

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  Lightbulb,
  Info,
  ChevronRight,
  ListTree,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ConsolidationResult, ContradictionDirectionResult, DirectionGroup } from '@/types/directedTriz';

export interface ConsolidationPanelProps {
  consolidation: ConsolidationResult;
  /** contradiction ID → human-readable label (engineeringStatement / naturalDescription) */
  contradictionLabels?: Record<string, string>;
  /** Per-contradiction directed results — used to detect Top1→Top2 swap */
  directedResults?: Record<string, ContradictionDirectionResult>;
  /**
   * 2026-05 hardening fallback：使用者在 DecisionCard 勾選的方向（依矛盾分桶）。
   * 即使後端 was_user_picked 因 partial persist 而為空，前端仍能以此反推
   * 「採納方向是不是 RD 勾的」，避免顯示錯誤的「Top2 替換」徽章。
   */
  pickedByContradiction?: Record<string, Set<string>>;
}

const STATUS_CONFIG = {
  compatible: {
    icon: CheckCircle2,
    label: '全部相容',
    color: 'text-green-600',
    bg: 'bg-green-50 dark:bg-green-950/20 border-green-200',
  },
  resolved_with_swap: {
    icon: AlertTriangle,
    label: '替換後相容',
    color: 'text-amber-600',
    bg: 'bg-amber-50 dark:bg-amber-950/20 border-amber-200',
  },
  conflict: {
    icon: XCircle,
    label: '存在衝突',
    color: 'text-red-600',
    bg: 'bg-red-50 dark:bg-red-950/20 border-red-200',
  },
};

/**
 * PR3-1 disclaimer 文字 — 「LLM 整併 ≠ 物理可行」的固定揭露。
 * 抽出為常數讓後續 docs 也能引用同樣措辭。
 */
const LLM_DISCLAIMER =
  '此判斷由 LLM 比對方向摘要、影響模組、次要矛盾的描述層級相容性，' +
  '非物理或 CAD 層級驗證；需於後續 Pre-CAD / MUST 階段實際驗證可行性。';

export function ConsolidationPanel({
  consolidation,
  contradictionLabels,
  directedResults,
  pickedByContradiction,
}: ConsolidationPanelProps) {
  const config = STATUS_CONFIG[consolidation.status];
  const Icon = config.icon;
  const [showCandidatePools, setShowCandidatePools] = useState(false);
  const [showStuckAnalysis, setShowStuckAnalysis] = useState(true);

  /** Resolve a contradiction ID to a human-readable label, falling back to truncated hash. */
  const label = (id: string) => contradictionLabels?.[id] ?? id.slice(0, 12);

  /**
   * Adopted direction was RD's explicit pick (vs system Top1 or system-swapped Top2).
   *
   * 2026-05 hardening：除了優先信任 backend 的 was_user_picked 之外，
   * 增加一道 FE-side fallback — 若 was_user_picked 為空 / undefined（例如 DB
   * partial persist 還沒套 migration），則用使用者在 DecisionCard 上的勾選
   * `pickedByContradiction[cid]` 反推。這樣即使 DB 殘缺，UI 也不會錯把
   * 「RD 勾的方向」誤標成「Top2 替換」。
   */
  const isUserPicked = (cid: string, directionId: string): boolean => {
    // Primary: backend authoritative
    if (consolidation.was_user_picked?.[cid] === directionId) return true;
    // Fallback: FE picked set (defense-in-depth for partial persist / legacy rows)
    const wasUserPickedMap = consolidation.was_user_picked ?? {};
    const backendHasUserPickInfo = Object.keys(wasUserPickedMap).length > 0;
    // 只有當 backend 完全沒提供 was_user_picked 時，才信任 FE picked set；
    // 否則尊重 backend（避免 backend 標 "系統 swap" 被 FE picked 蓋掉）。
    if (!backendHasUserPickInfo) {
      const pickedSet = pickedByContradiction?.[cid];
      if (pickedSet && pickedSet.has(directionId)) return true;
    }
    return false;
  };

  /**
   * Adopted direction was system-swapped from Top1 → Top2 to resolve a cross-contradiction
   * conflict. This is **only** true if RD did **not** explicitly pick this direction —
   * a user pick that happens to not equal Top1 is NOT a swap.
   */
  const isSystemSwap = (cid: string, directionId: string): boolean => {
    if (isUserPicked(cid, directionId)) return false;
    const r = directedResults?.[cid];
    if (!r || !r.top1) return false;
    return r.top1.direction_id !== directionId;
  };

  // PR2-Lite: 候選池 — 過濾出非採納方向作為 fallback 清單
  const candidatePoolsByCid = consolidation.candidate_pools ?? {};
  const totalFallbackCount = Object.entries(candidatePoolsByCid).reduce(
    (sum, [cid, pool]) => {
      const adopted = consolidation.adopted_directions[cid];
      const adoptedId = adopted?.direction_id;
      return sum + pool.filter((d) => d.direction_id !== adoptedId).length;
    },
    0,
  );

  // PR1-8 conflict 卡點分析
  const exhausted = consolidation.exhausted_contradictions ?? [];
  const totalRounds = consolidation.total_rounds ?? 0;
  const isConflict = consolidation.status === 'conflict';
  // 單矛盾情境：backend fast path (consolidate_solutions line 4951) — 跳過跨矛盾比對，
  // 但仍跑 _generate_engineering_verdict_card。前端用這個 flag 切換主標題與說明文案，
  // 讓使用者知道「沒跨矛盾衝突可比 = 正常狀態」，不要誤以為演算法沒做事。
  const adoptedCount = Object.keys(consolidation.adopted_directions).length;
  const isSingleContradiction = adoptedCount === 1;

  return (
    <Card className={cn('border', config.bg)}>
      <CardHeader className="p-4 pb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Icon className={cn('h-5 w-5', config.color)} />
          <CardTitle className="text-sm font-semibold">
            {isSingleContradiction ? '方向整併（單一矛盾）' : '跨矛盾方向整併'}
          </CardTitle>
          <Badge variant="outline" className="text-[10px]">
            {isSingleContradiction ? '無跨矛盾衝突' : config.label}
          </Badge>
          {/* PR3-1：LLM 限制 disclaimer tooltip */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="ml-auto inline-flex items-center text-muted-foreground hover:text-foreground"
                aria-label="整併方法論說明"
              >
                <Info className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="left" className="max-w-xs text-xs leading-relaxed">
              {LLM_DISCLAIMER}
            </TooltipContent>
          </Tooltip>
        </div>

        {/* PR1-8 conflict 標題訊息 */}
        {isConflict && (
          <p className="text-[11px] text-red-700 dark:text-red-300 mt-1">
            您勾選的方向無法全部整併
            {totalRounds > 0 && `（AI 嘗試了 ${totalRounds} 種組合）`}
          </p>
        )}
      </CardHeader>

      <CardContent className="p-4 pt-2 space-y-3">
        {/* PR1-8 卡點分析 — 僅在 conflict 且有 exhausted 時顯示 */}
        {isConflict && exhausted.length > 0 && (
          <Collapsible open={showStuckAnalysis} onOpenChange={setShowStuckAnalysis}>
            <CollapsibleTrigger asChild>
              <button className="w-full flex items-center gap-1.5 text-[11px] font-medium text-amber-700 dark:text-amber-300 hover:underline">
                <ChevronRight
                  className={cn(
                    'h-3 w-3 transition-transform',
                    showStuckAnalysis && 'rotate-90',
                  )}
                />
                <AlertTriangle className="h-3 w-3" />
                卡點分析（為何救不起來）
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-1 rounded border border-amber-300/40 bg-amber-50/50 dark:bg-amber-950/10 p-2 space-y-1.5">
                <p className="text-[11px] text-foreground">
                  以下矛盾的候選池已用盡，AI 無法替換方向：
                </p>
                <ul className="text-[11px] space-y-0.5">
                  {exhausted.map((cid) => (
                    <li key={cid} className="flex items-start gap-1">
                      <span className="text-amber-600 mt-0.5">▸</span>
                      <span>
                        <span className="font-medium">{label(cid)}</span>
                        <span className="text-muted-foreground">
                          {' '}
                          — 建議加勾此矛盾的其他候選方向，提供 AI 替換彈性。
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Adopted directions map */}
        {Object.keys(consolidation.adopted_directions).length > 0 && (
          <div className="space-y-1">
            <div className="text-[11px] font-medium text-muted-foreground">
              採納方向
            </div>
            {Object.entries(consolidation.adopted_directions).map(([cid, dir]) => (
              <div
                key={cid}
                className="flex items-center gap-2 text-[11px] bg-background/80 rounded p-1.5"
              >
                <span className="text-muted-foreground truncate max-w-[220px]" title={cid}>
                  {label(cid)}
                </span>
                <ArrowRight className="h-3 w-3 shrink-0 text-muted-foreground" />
                <span className="font-medium">{dir.direction_name}</span>
                {isUserPicked(cid, dir.direction_id) && (
                  <Badge
                    variant="outline"
                    className="text-[9px] text-blue-600 border-blue-300 bg-blue-50"
                    title="此方向由 RD 在 DecisionCard 直接勾選，不是系統選的 Top1。"
                  >
                    使用您勾選的方向
                  </Badge>
                )}
                {isSystemSwap(cid, dir.direction_id) && (
                  <Badge
                    variant="outline"
                    className="text-[9px] text-amber-600 border-amber-300 bg-amber-50"
                    title="系統為解決跨矛盾衝突，把 Top1 換成 Top2。"
                  >
                    Top2 替換
                  </Badge>
                )}
                <Badge variant="outline" className="text-[9px] ml-auto">
                  TC:{dir.tc_count} PC:{dir.pc_count} SF:{dir.sf_count}
                </Badge>
              </div>
            ))}
          </div>
        )}

        {/* PR2-Lite：候選池摺疊區 — 顯示每條矛盾的其他 fallback 方向 */}
        {totalFallbackCount > 0 && (
          <Collapsible open={showCandidatePools} onOpenChange={setShowCandidatePools}>
            <CollapsibleTrigger asChild>
              <button className="w-full flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground hover:text-foreground">
                <ChevronRight
                  className={cn(
                    'h-3 w-3 transition-transform',
                    showCandidatePools && 'rotate-90',
                  )}
                />
                <ListTree className="h-3 w-3" />
                其他候選方向 ({totalFallbackCount} 個 fallback)
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-1 space-y-2 rounded bg-muted/30 p-2">
                {Object.entries(candidatePoolsByCid).map(([cid, pool]) => {
                  const adopted = consolidation.adopted_directions[cid];
                  const adoptedId = adopted?.direction_id;
                  const fallbacks = pool.filter((d) => d.direction_id !== adoptedId);
                  if (fallbacks.length === 0) return null;
                  return (
                    <div key={cid} className="text-[11px]">
                      <div className="font-medium text-muted-foreground mb-0.5 truncate" title={cid}>
                        {label(cid)}
                      </div>
                      <ul className="ml-2 space-y-0.5">
                        {fallbacks.map((d: DirectionGroup) => (
                          <li
                            key={d.direction_id}
                            className="flex items-center gap-1.5 text-foreground/80"
                          >
                            <span className="text-muted-foreground/60">·</span>
                            <span>{d.direction_name}</span>
                            <span className="text-[9px] text-muted-foreground">
                              (TC:{d.tc_count} PC:{d.pc_count} SF:{d.sf_count})
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
                <p className="text-[10px] text-muted-foreground italic pt-1 border-t border-border/50 mt-1">
                  這些方向是您在 DecisionCard 勾選但未被選為代表的候選，AI 若遇到衝突會優先從這裡換。
                </p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Conflict report */}
        {consolidation.conflict_report &&
          consolidation.conflict_report.conflicting_pairs.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-red-600">無法共存的方向</div>
              {consolidation.conflict_report.conflicting_pairs.map((pair, i) => (
                <div
                  key={i}
                  className="text-[11px] bg-red-50/50 dark:bg-red-950/10 rounded p-2 border border-red-200/50 space-y-1"
                >
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-muted-foreground">📍</span>
                    <span className="text-muted-foreground">[{label(pair.contradiction_a_id)}]</span>
                    <span className="font-medium">「{pair.direction_a}」</span>
                    <XCircle className="h-3 w-3 text-red-500" />
                    <span className="text-muted-foreground">[{label(pair.contradiction_b_id)}]</span>
                    <span className="font-medium">「{pair.direction_b}」</span>
                  </div>
                  {pair.reason && (
                    <div className="text-muted-foreground italic pl-4">
                      原因：{pair.reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

        {/* Suggestions */}
        {consolidation.conflict_report &&
          consolidation.conflict_report.suggestions.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
                <Lightbulb className="h-3 w-3" /> 行動建議
              </div>
              <ul className="text-[11px] text-muted-foreground space-y-0.5 list-disc list-inside">
                {consolidation.conflict_report.suggestions.map((s, i) => (
                  <li key={i}>{s.description}</li>
                ))}
              </ul>
            </div>
          )}

        {/* Integration advice */}
        {consolidation.integration_advice && (
          <div className="text-[11px] bg-muted/40 rounded p-2">
            <div className="font-medium text-muted-foreground mb-0.5">整合建議</div>
            <p className="text-foreground whitespace-pre-wrap">{consolidation.integration_advice}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
