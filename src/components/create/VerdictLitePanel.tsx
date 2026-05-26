/**
 * VerdictLitePanel — 對照 Brief 任務的精簡審判面板（v0.5 / v3 — CLD 健檢徽章版）
 *
 * 取代舊 VerdictCardPanel (Q1–Q8 工程審判)。設計理念見
 * plans/triz-verdict-card-simplification.md §14–§20。
 *
 * v0.5 (v3) 結構性精簡：
 *   - 移除 solved / gaps 兩區分組 → 改為「Brief 達成檢核」單一區，
 *     mission → constraint → kpi 按 brief 順序排，status icon 在每行最右
 *   - 移除 sub_requirement / socratic_concern / cld_side_effect 三 kind 渲染
 *     （schema 已移除，UI 也跟著拿掉）
 *   - 新增 <ExploreHealthSection /> 子元件：摺疊式徽章顯示
 *     contradiction_coverage / cld_warning（DOT_COLOR map: green/yellow/red）
 *   - <NextActionsSection /> 過濾只渲染 blocking=true 的條目
 *     （非 blocking 存在 DB 但不顯示給 RD）
 *
 * v2 (v0.4) 沿用：
 *   - 所有 emoji 加 Tooltip 解釋
 *   - 「⛔ blocking」徽章 → 「🔴 必做」+ tooltip
 *   - DIR-X bug 修復：找不到方向名稱時 fallback 純 id
 */

import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Target,
  CheckCircle2,
  ClipboardList,
  Activity,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  BriefItemCheck,
  CheckStatus,
  ConsolidationResult,
  ContradictionDirectionResult,
  DirectionGroup,
  EngineeringVerdictLite,
  ExploreHealthSummary,
  NextAction,
} from '@/types/directedTriz';

interface VerdictLitePanelProps {
  card: EngineeringVerdictLite;
  /**
   * 整併結果（含 adopted_directions + candidate_pools）。
   * Panel 會自動 flatten 成 direction_id → DirectionGroup 的 lookup map。
   *
   * 注意：`adopted_directions` 的 key 是「矛盾 ID」(C-1)，
   * 不是「方向 ID」(DIR-1)，所以必須在 Panel 內 rebuild。
   */
  consolidation?: ConsolidationResult | null;
  /**
   * 全部矛盾的方向探索結果 (contradiction_id → ContradictionDirectionResult)。
   * Panel 會從 `all_directions` 取得所有方向（包含未被勾選的）。
   * 這層 fallback 用於：LLM 在 contributing_directions 引用了使用者勾過、
   * 但最終沒被採用的方向 ID。
   */
  directedResults?: Record<string, ContradictionDirectionResult>;
}

// 對應 overall_verdict 的視覺風格 + hover tooltip
const OVERALL_VERDICT: Record<
  EngineeringVerdictLite['overall_verdict'],
  {
    label: string;
    variant: 'default' | 'secondary' | 'destructive' | 'outline';
    tint: string;
    tooltip: string;
  }
> = {
  adopt: {
    label: '✅ 可採用',
    variant: 'default',
    tint: 'text-green-700 dark:text-green-300',
    tooltip: 'AI 認為這組方向可以直接採用，brief 任務大致都已覆蓋。',
  },
  adopt_with_conditions: {
    label: '🟡 可採用（有條件）',
    variant: 'secondary',
    tint: 'text-yellow-700 dark:text-yellow-300',
    tooltip: '可採用，但要先處理幾件未解 / 風險項目（看下方清單）。',
  },
  needs_revision: {
    label: '⚠️ 要先調整',
    variant: 'outline',
    tint: 'text-orange-700 dark:text-orange-300',
    tooltip: '還沒到能採用的程度；要不要再加勾方向、或修改 brief。',
  },
  reject: {
    label: '🛑 不建議採用',
    variant: 'destructive',
    tint: 'text-red-700 dark:text-red-300',
    tooltip: '整組方向不建議採用，brief 任務有重大項目無法達成。',
  },
};

// status → 顯示用 badge + hover tooltip
const STATUS_BADGE: Record<
  CheckStatus,
  { icon: string; label: string; tint: string; tooltip: string }
> = {
  met: {
    icon: '✅',
    label: '達成',
    tint: 'text-green-700 dark:text-green-300',
    tooltip: '達成 — 此 brief 項目已被勾選方向直接處理。',
  },
  partial: {
    icon: '🟡',
    label: '部分',
    tint: 'text-yellow-700 dark:text-yellow-300',
    tooltip: '部分達成 — 有處理但未完整，需後續驗證或加方向。',
  },
  at_risk: {
    icon: '⚠️',
    label: '有風險',
    tint: 'text-orange-700 dark:text-orange-300',
    tooltip: '有風險 — 可能會撞到硬限制（如成本超預算、外徑超限）。',
  },
  unmet: {
    icon: '🛑',
    label: '未達成',
    tint: 'text-red-700 dark:text-red-300',
    tooltip: '未達成 — 目前勾選的方向沒有處理到這個 brief 項目。',
  },
  not_relevant: {
    icon: '⚫',
    label: '無關',
    tint: 'text-muted-foreground',
    tooltip: '與此方案無關 — 檢查過了但確認沒影響到這個 brief 項目。',
  },
};

// item_kind → RD 友善中文標籤 + tooltip
// v0.5 (v3): 從 6 種降為 3 種（mission / constraint / kpi）。
// 舊 sub_requirement / socratic_concern / cld_side_effect 已從 schema 移除。
const KIND_LABEL: Record<
  BriefItemCheck['item_kind'],
  { label: string; tooltip: string }
> = {
  mission: {
    label: '主任務',
    tooltip: 'Brief 中寫的主任務 (mission) — 整個產品要達成的核心目標。',
  },
  constraint: {
    label: '規格',
    tooltip: 'Brief 中寫的硬規格 / 限制 — 必須守住的紅線（不能超過）。',
  },
  kpi: {
    label: 'KPI',
    tooltip: 'Brief 中寫的 KPI — 必須達到的關鍵績效數字目標。',
  },
};

const EFFORT_LABEL: Record<
  NonNullable<NextAction['effort_hint']>,
  { label: string; tooltip: string }
> = {
  small: { label: '輕量 (<4h)', tooltip: '預估工時 4 小時以內' },
  medium: { label: '中等 (4-24h)', tooltip: '預估工時 4-24 小時' },
  large: { label: '重 (>24h)', tooltip: '預估工時超過 24 小時' },
  unknown: { label: '工時未知', tooltip: 'AI 未估工時，請 RD 自行評估' },
};

// v0.5 (v3): Explore 健檢徽章顏色點。
// green = 健康 / yellow = 有警示 / red = 有阻擋
const DOT_COLOR = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
} as const;

/**
 * 把 direction_id list 展開成「方向名稱 (DIR-X)」格式給 RD 閱讀。
 * 查不到 direction_name 時 fallback 回純 id（不額外標警告，因為大量誤報會嚇到使用者）。
 */
function formatDirections(
  ids: string[],
  directionsById: Map<string, DirectionGroup>,
): string {
  if (directionsById.size === 0) return ids.join('、');
  return ids
    .map((id) => {
      const dir = directionsById.get(id);
      if (dir && dir.direction_name) {
        return `${dir.direction_name}（${id}）`;
      }
      // 找不到對應名稱 — 直接 fallback 純 id，不嚇使用者
      return id;
    })
    .join('、 ');
}

function ItemRow({
  item,
  directionsById,
}: {
  item: BriefItemCheck;
  directionsById: Map<string, DirectionGroup>;
}) {
  const badge = STATUS_BADGE[item.status] ?? STATUS_BADGE.not_relevant;
  const kind = KIND_LABEL[item.item_kind] ?? {
    label: item.item_kind,
    tooltip: '',
  };
  // 若 LLM 已把 item_id 嵌進 item_label（例「C-01 產品最大徑向…」），
  // 就不再單獨顯示 item_id（避免重複）。判定：item_label 開頭就是 item_id。
  const labelHasId =
    item.item_id !== '' && item.item_label.startsWith(item.item_id);
  return (
    <div className="border-l-2 pl-2 py-1 text-[12px]">
      <div className="flex items-baseline gap-2 flex-wrap">
        {/* item_kind 標籤 + tooltip */}
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-muted-foreground text-[10px] cursor-help underline decoration-dotted">
              [{kind.label}]
            </span>
          </TooltipTrigger>
          <TooltipContent className="text-[11px] max-w-[260px]">
            {kind.tooltip}
          </TooltipContent>
        </Tooltip>

        {item.item_id && !labelHasId && (
          <span className="font-mono text-[10px] text-muted-foreground/80">
            {item.item_id}
          </span>
        )}
        <span className="font-medium flex-1 min-w-0">
          {item.item_label || '(未命名)'}
        </span>

        {/* status emoji + tooltip 移到行尾，讓 RD 一眼掃到哪行有問題 */}
        <Tooltip>
          <TooltipTrigger asChild>
            <span className={cn('cursor-help text-sm', badge.tint)}>
              {badge.icon}
            </span>
          </TooltipTrigger>
          <TooltipContent className="text-[11px] max-w-[260px]">
            <strong>{badge.label}</strong>：{badge.tooltip}
          </TooltipContent>
        </Tooltip>
      </div>
      {item.rationale && (
        <div className="text-muted-foreground mt-0.5">{item.rationale}</div>
      )}
      {item.quantitative_estimate && (
        <div className="font-mono text-[10px] mt-0.5">
          量化估計：{item.quantitative_estimate}
        </div>
      )}
      {item.contributing_directions.length > 0 && (
        <div className="text-[10px] text-muted-foreground/80 mt-0.5">
          相關方向：{formatDirections(item.contributing_directions, directionsById)}
        </div>
      )}
    </div>
  );
}

/**
 * v0.5 (v3) 新增子元件：單行健檢徽章 + 摺疊細節。
 *
 * 視覺：左邊一個顏色圓點（DOT_COLOR）+ label + 描述 + 右邊展開箭頭。
 * 點開後展開 details 清單。details 為空時不顯示展開箭頭。
 */
function HealthBadgeRow({
  dot,
  label,
  value,
  tooltip,
  details,
  open,
  onToggle,
}: {
  dot: string;
  label: string;
  value: string;
  tooltip: string;
  details: string[];
  open: boolean;
  onToggle: () => void;
}) {
  const expandable = details.length > 0;
  return (
    <div className="border rounded-sm px-2 py-1 text-[12px]">
      <button
        type="button"
        onClick={expandable ? onToggle : undefined}
        className={cn(
          'w-full flex items-center gap-2 text-left',
          expandable && 'cursor-pointer hover:opacity-80',
          !expandable && 'cursor-default',
        )}
      >
        <span className={cn('inline-block h-2 w-2 rounded-full shrink-0', dot)} />
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="font-medium cursor-help underline decoration-dotted">
              {label}
            </span>
          </TooltipTrigger>
          <TooltipContent className="text-[11px] max-w-[280px]">
            {tooltip}
          </TooltipContent>
        </Tooltip>
        <span className="text-muted-foreground flex-1">{value}</span>
        {expandable &&
          (open ? (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          ))}
      </button>
      {expandable && open && (
        <ul className="mt-1 pl-4 space-y-0.5 text-[11px] text-muted-foreground list-disc">
          {details.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * v0.5 (v3) 新增子元件：Explore 階段健檢區。
 *
 * 兩個徽章：
 *   1. 矛盾覆蓋率 — 一定渲染（總有一個值，至少是「（本專案無矛盾）」）
 *   2. CLD 副作用警示 — cld_warning 為 null 時不渲染
 */
function ExploreHealthSection({ health }: { health: ExploreHealthSummary }) {
  const [coverageOpen, setCoverageOpen] = useState(false);
  const [cldOpen, setCldOpen] = useState(false);

  const coverage = health.contradiction_coverage;
  const cld = health.cld_warning;

  return (
    <section>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-1 text-xs font-medium text-purple-700 dark:text-purple-300 mb-1 cursor-help">
            <Activity className="h-3.5 w-3.5" />
            <span>Explore 階段健檢</span>
          </div>
        </TooltipTrigger>
        <TooltipContent className="text-[11px] max-w-[280px]">
          檢視 Explore 階段挖出來的矛盾有沒有被勾選方向涵蓋，
          以及勾選方向動到的 CLD 節點會不會撞到 brief 紅線。
          平時摺疊，點徽章可展開細節。
        </TooltipContent>
      </Tooltip>
      <div className="grid grid-cols-1 gap-1.5">
        <HealthBadgeRow
          dot={DOT_COLOR[coverage.level]}
          label="矛盾覆蓋率"
          value={coverage.label}
          tooltip="Explore 階段挖出來的矛盾，目前的整併方向解到幾條。覆蓋率越高代表這組方向越完整。"
          details={coverage.details ?? []}
          open={coverageOpen}
          onToggle={() => setCoverageOpen((o) => !o)}
        />
        {cld && (
          <HealthBadgeRow
            dot={DOT_COLOR[cld.level]}
            label="CLD 副作用警示"
            value={`動 ${cld.nodes_touched} 節點 / ${cld.side_effects.length} 條風險鏈`}
            tooltip="勾選方向沿著 brief 的 CLD（因果輪迴圖）走 1-2 hop，會不會撞到其他 brief 條目。"
            details={cld.side_effects.map(
              (c) =>
                `${c.chain}（來源：${c.source_direction_id}，撞到：${c.related_brief_item_id}${
                  c.severity ? `，嚴重度：${c.severity}` : ''
                }）`,
            )}
            open={cldOpen}
            onToggle={() => setCldOpen((o) => !o)}
          />
        )}
      </div>
    </section>
  );
}

export function VerdictLitePanel({
  card,
  consolidation,
  directedResults,
}: VerdictLitePanelProps) {
  // ⚠ 關鍵：adopted_directions 的 key 是「矛盾 ID」(C-1, C-2)，不是「方向 ID」(DIR-1)。
  // 所以要把 Record 的 values 全部拉出來、用 direction_id 重組成新的 lookup map。
  // 同時把 candidate_pools 與所有 directedResults.all_directions 也合進去，
  // 確保 LLM 引用任何「曾被考慮過的方向」都能查到名稱。
  const directionsById = new Map<string, DirectionGroup>();
  const addDirection = (d: DirectionGroup | undefined | null) => {
    if (!d) return;
    if (!d.direction_id) return;
    // 已存在就不覆寫（保留 adopted 為首選）
    if (!directionsById.has(d.direction_id)) {
      directionsById.set(d.direction_id, d);
    }
  };
  // 優先：consolidation.adopted_directions（每條矛盾被選中的代表方向）
  if (consolidation?.adopted_directions) {
    for (const d of Object.values(consolidation.adopted_directions)) {
      addDirection(d);
    }
  }
  // 次優：candidate_pools（每條矛盾的完整候選池，含未採用的）
  if (consolidation?.candidate_pools) {
    for (const pool of Object.values(consolidation.candidate_pools)) {
      for (const d of pool) addDirection(d);
    }
  }
  // Fallback：全部 directedResults.all_directions（所有方向探索的結果）
  if (directedResults) {
    for (const r of Object.values(directedResults)) {
      for (const d of r.all_directions ?? []) addDirection(d);
      // top1 / top2 也可能不在 all_directions 裡（防衛）
      if (r.top1) addDirection(r.top1);
      if (r.top2) addDirection(r.top2);
    }
  }

  // 建一個 brief item_id → item_label 的 map，讓 next_actions.related_item_ids
  // 在 UI 上能展開成完整描述（如「C-01 產品最大徑向尺寸 ≤ 111mm」）。
  // v0.5 (v3): 移除 sr_checks / socratic_checks / cld_checks 三個 list 的 addCheck。
  const briefItemLabelById = new Map<string, string>();
  const addCheck = (c: BriefItemCheck | null | undefined) => {
    if (!c) return;
    if (c.item_id && c.item_label) briefItemLabelById.set(c.item_id, c.item_label);
  };
  addCheck(card.mission_check);
  for (const c of card.constraint_checks) addCheck(c);
  for (const c of card.kpi_checks) addCheck(c);

  /**
   * 把 next_action.related_item_ids 展開成完整描述。
   * 例：["C-01", "K2"] → ["C-01 產品最大徑向尺寸 ≤ 111mm", "K2 馬達效率 ≥ 85%"]
   * 若找不到，回 fallback 純 id。
   */
  const formatRelatedItems = (ids: string[]): string =>
    ids.map((id) => briefItemLabelById.get(id) ?? id).join('、 ');

  const meta = OVERALL_VERDICT[card.overall_verdict] ?? OVERALL_VERDICT.needs_revision;

  // v0.5 (v3) 單區排序：brief 條目按 mission → constraints → KPIs 順序排，
  // 不再分 solved / gaps 兩區（status icon 在每行最右，眼睛掃一次就知道哪行有問題）。
  const allBriefChecks: BriefItemCheck[] = [
    ...(card.mission_check ? [card.mission_check] : []),
    ...card.constraint_checks,
    ...card.kpi_checks,
  ];

  // v0.5 (v3) next_actions 過濾：只渲染 blocking=true 的條目
  // （非 blocking 的存在 DB 但不顯示給 RD）
  const blockingActions = card.next_actions.filter((a) => a.blocking === true);

  return (
    <TooltipProvider delayDuration={150}>
      <Card className="border-primary/40">
        <CardHeader className="p-3 pb-2">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <CardTitle className="text-sm flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              你勾的這組方向 → 能完成 brief 任務嗎？
            </CardTitle>
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant={meta.variant} className="cursor-help">
                    {meta.label}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent className="text-[11px] max-w-[280px]">
                  {meta.tooltip}
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-[11px] text-muted-foreground cursor-help underline decoration-dotted">
                    信心 {(card.confidence * 100).toFixed(0)}%
                  </span>
                </TooltipTrigger>
                <TooltipContent className="text-[11px] max-w-[260px]">
                  AI 對自己這次判斷的信心程度（0-100%）。
                  低於 60% 建議多看幾遍、或加勾更多方向再跑一次整併。
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
          {/* 限制揭露：LLM 推論，非實驗 / CAD 驗證 */}
          <p className="text-[10px] text-muted-foreground/80 italic mt-1 leading-relaxed">
            ⓘ 此判斷由 AI 基於 brief 任務 + 勾選方向推論產出，
            <strong>非實驗、模擬或 CAD 驗證</strong>。
          </p>
          {card.overall_headline && (
            <div className={cn('text-[12px] mt-1', meta.tint)}>
              {card.overall_headline}
            </div>
          )}
        </CardHeader>
        <CardContent className="p-2 space-y-3">
          {/* ② Brief 達成檢核（單區排序，按 brief 順序） */}
          <section>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 text-xs font-medium text-green-700 dark:text-green-300 mb-1 cursor-help">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Brief 達成檢核（{allBriefChecks.length}）</span>
                </div>
              </TooltipTrigger>
              <TooltipContent className="text-[11px] max-w-[260px]">
                Brief 中寫的主任務 / 規格 / KPI 一覽，按 brief 文件順序排列。
                每行最右的 emoji 就是達成狀態：✅ 達成 / 🟡 部分 / ⚠️ 有風險 /
                🛑 未達成 / ⚫ 無關。
              </TooltipContent>
            </Tooltip>
            {allBriefChecks.length === 0 ? (
              <div className="text-[11px] italic text-muted-foreground pl-4">
                （brief 沒有列出任何 mission / 規格 / KPI；建議回 brief 階段補上）
              </div>
            ) : (
              <div className="space-y-1">
                {allBriefChecks.map((item, i) => (
                  <ItemRow
                    key={`brief-${item.item_kind}-${item.item_id}-${i}`}
                    item={item}
                    directionsById={directionsById}
                  />
                ))}
              </div>
            )}
          </section>

          {/* ③ Explore 階段健檢徽章（v0.5 / v3 新增） */}
          {card.explore_health && (
            <ExploreHealthSection health={card.explore_health} />
          )}

          {/* ④ 採用前必做的事（v0.5 / v3：只顯示 blocking=true） */}
          <section>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 text-xs font-medium text-blue-700 dark:text-blue-300 mb-1 cursor-help">
                  <ClipboardList className="h-3.5 w-3.5" />
                  <span>採用前必做的事（{blockingActions.length}）</span>
                </div>
              </TooltipTrigger>
              <TooltipContent className="text-[11px] max-w-[260px]">
                AI 建議「不做不能進下一階段」(CAD / 試模 / 量產) 的行動。
                標 🔴 必做的優先處理；非必做項目存在但不在此顯示。
              </TooltipContent>
            </Tooltip>
            {blockingActions.length === 0 ? (
              <div className="text-[11px] italic text-muted-foreground pl-4">
                （AI 未列出任何必做的下一步；如有疑慮請人工複查）
              </div>
            ) : (
              <ol className="list-decimal pl-5 space-y-1 text-[12px]">
                {blockingActions.map((a, i) => {
                  const effort = a.effort_hint
                    ? EFFORT_LABEL[a.effort_hint] ?? null
                    : null;
                  return (
                    <li key={i} className="space-y-0.5">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge
                              variant="destructive"
                              className="text-[10px] cursor-help"
                            >
                              🔴 必做
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent className="text-[11px] max-w-[260px]">
                            這件事不做，方案不能進到下一階段
                            （CAD / 試模 / 量產）。
                          </TooltipContent>
                        </Tooltip>
                        <span className="font-medium">{a.action}</span>
                        {effort && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-[10px] text-muted-foreground cursor-help">
                                [{effort.label}]
                              </span>
                            </TooltipTrigger>
                            <TooltipContent className="text-[11px] max-w-[200px]">
                              {effort.tooltip}
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                      {a.why && (
                        <div className="text-[11px] text-muted-foreground pl-1">
                          原因：{a.why}
                        </div>
                      )}
                      {a.related_item_ids && a.related_item_ids.length > 0 && (
                        <div className="text-[10px] text-muted-foreground/80 pl-1">
                          相關：{formatRelatedItems(a.related_item_ids)}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}
