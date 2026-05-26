/**
 * Phase 2 — DecisionCard panel
 *
 * 每條 TRIZ direction 配一張 DecisionCard，給 RD 選購用。
 * 5 欄佈局見 plans/triz-redesign.md §3.1：
 *   1. one_liner (一句話機制)
 *   2. contradiction_face (face badge + 解到哪一面)
 *   3. resolution_status + one_line (對此矛盾的解決度)
 *   4. quick_tags (effort / evidence / affects_modules)
 *   5. combination_hints (跨矛盾整併相容性)
 *
 * 真正的工程審判由整併後的 Brief 任務檢核 提供，不在這層做。
 */

import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Info, Trophy, Medal } from "lucide-react";

import type {
  DecisionCard,
  ResolutionStatus,
  ContradictionFace,
  EffortLevel,
  EvidenceLevel,
} from "@/types/directedTriz";

// ---------- 視覺映射 ----------

const STATUS_STYLE: Record<
  ResolutionStatus,
  { label: string; tone: string; tooltip: string }
> = {
  directly_resolves: {
    label: "直接解",
    tone: "bg-green-100 text-green-800 border-green-300 dark:bg-green-950/40 dark:text-green-200",
    tooltip: "在原脈絡下，這個方向同時推 improving 並抑 worsening。",
  },
  partially_resolves: {
    label: "部分解",
    tone: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-200",
    tooltip: "只解到矛盾的一面（improving 或 worsening 其一），或只到症狀層。",
  },
  conditionally_resolves: {
    label: "條件解",
    tone: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200",
    tooltip: "理論可行，但前提是某些 key_assumptions 成立（需驗證）。",
  },
  does_not_resolve: {
    label: "未解",
    tone: "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200",
    tooltip: "與矛盾的因果鏈關聯很弱，不算解。",
  },
  unclear: {
    label: "不確定",
    tone: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-200",
    tooltip: "資訊不足，未給出明確判斷。",
  },
};

const FACE_LABEL: Record<ContradictionFace, string> = {
  improving_side: "解 improving",
  worsening_side: "解 worsening",
  both: "兩面兼顧",
  side_effect: "處理副作用",
};

const EFFORT_TONE: Record<EffortLevel, string> = {
  low: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-200",
  high: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-200",
};

const EFFORT_LABEL: Record<EffortLevel, string> = {
  low: "低成本",
  medium: "中成本",
  high: "高成本",
};

const EVIDENCE_TONE: Record<EvidenceLevel, string> = {
  E0: "bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200",
  E1: "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200",
  E2: "bg-yellow-100 text-yellow-900 border-yellow-300 dark:bg-yellow-950/40 dark:text-yellow-200",
  E3: "bg-green-100 text-green-900 border-green-300 dark:bg-green-950/40 dark:text-green-200",
  E4: "bg-emerald-200 text-emerald-900 border-emerald-400 dark:bg-emerald-950/50 dark:text-emerald-200",
};

const EVIDENCE_TOOLTIP: Record<EvidenceLevel, string> = {
  E0: "E0 純臆測",
  E1: "E1 物理推理",
  E2: "E2 跨領域類比",
  E3: "E3 同類應用測試",
  E4: "E4 已量產驗證",
};

// ---------- 單張卡 ----------

interface DecisionCardItemProps {
  card: DecisionCard;
  rank?: "top1" | "top2" | "other";
  /** RD 勾選回呼。第二個參數是新狀態（true=勾選 / false=取消）。 */
  onPickChange?: (directionId: string, picked: boolean) => void;
}

export function DecisionCardItem({
  card,
  rank = "other",
  onPickChange,
}: DecisionCardItemProps) {
  const status = STATUS_STYLE[card.resolution_status];
  const face = FACE_LABEL[card.contradiction_face];
  const effortTone = EFFORT_TONE[card.quick_tags.effort];
  const effortLabel = EFFORT_LABEL[card.quick_tags.effort];
  const evidenceTone = EVIDENCE_TONE[card.quick_tags.evidence_level];

  const borderClass =
    rank === "top1"
      ? "border-yellow-400 bg-yellow-50/40 dark:bg-yellow-950/20"
      : rank === "top2"
        ? "border-blue-300 bg-blue-50/30 dark:bg-blue-950/10"
        : card.picked
          ? "border-primary bg-primary/5"
          : "border-muted";

  return (
    <div
      className={cn(
        "border rounded-md p-3 transition-colors flex flex-col gap-2",
        borderClass,
      )}
    >
      {/* 第一行：勾選 + 標題 + rank icon + face badge + status badge */}
      <div className="flex items-start gap-2">
        <Checkbox
          id={`dc-${card.direction_id}`}
          checked={card.picked}
          onCheckedChange={(checked) =>
            onPickChange?.(card.direction_id, checked === true)
          }
          className="mt-0.5"
          aria-label={`勾選方向 ${card.direction_name}`}
        />
        <label
          htmlFor={`dc-${card.direction_id}`}
          className="flex items-center gap-1.5 flex-wrap min-w-0 cursor-pointer flex-1"
        >
          {rank === "top1" && (
            <Trophy className="h-4 w-4 text-yellow-500 shrink-0" />
          )}
          {rank === "top2" && (
            <Medal className="h-4 w-4 text-blue-400 shrink-0" />
          )}
          <span className="text-sm font-semibold">{card.direction_name}</span>
          {card.face_badge && (
            <Badge variant="outline" className="text-[10px]" title={face}>
              {card.face_badge}
            </Badge>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant="outline"
                className={cn("text-[10px] border cursor-help", status.tone)}
              >
                {status.label}
              </Badge>
            </TooltipTrigger>
            <TooltipContent className="max-w-xs text-xs">
              {status.tooltip}
            </TooltipContent>
          </Tooltip>
        </label>
      </div>

      {/* 第 1 欄：one_liner（一句話機制）*/}
      <p className="text-xs text-foreground leading-relaxed">
        {card.one_liner}
      </p>

      {/* 第 3 欄：resolution_one_line（對此矛盾的解決度說明）*/}
      {card.resolution_one_line && (
        <p className="text-[11px] text-muted-foreground italic">
          → {card.resolution_one_line}
        </p>
      )}

      {/* 第 4 欄：quick_tags */}
      <div className="flex items-center gap-1.5 flex-wrap text-[10px]">
        <Badge variant="outline" className={cn("border", effortTone)}>
          {effortLabel}
        </Badge>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="outline"
              className={cn("border cursor-help", evidenceTone)}
            >
              {card.quick_tags.evidence_level}
            </Badge>
          </TooltipTrigger>
          <TooltipContent className="text-xs">
            {EVIDENCE_TOOLTIP[card.quick_tags.evidence_level]}
          </TooltipContent>
        </Tooltip>
        {card.quick_tags.affects_modules.slice(0, 4).map((m) => (
          <Badge
            key={m}
            variant="secondary"
            className="font-normal text-muted-foreground"
          >
            {m}
          </Badge>
        ))}
      </div>

      {/* 第 5 欄：combination_hints */}
      {(card.combination_hints.synergy_with.length > 0 ||
        card.combination_hints.conflict_with.length > 0 ||
        card.combination_hints.best_paired_with.length > 0) && (
        <div className="border-t border-dashed pt-2 space-y-1 text-[11px]">
          {card.combination_hints.best_paired_with.length > 0 && (
            <div>
              <span className="text-muted-foreground">★ 推薦組合：</span>
              <span className="text-foreground">
                {card.combination_hints.best_paired_with.join("； ")}
              </span>
            </div>
          )}
          {card.combination_hints.synergy_with.length > 0 && (
            <div>
              <span className="text-emerald-700 dark:text-emerald-300">
                ▸ 搭配：
              </span>
              <span className="text-foreground">
                {card.combination_hints.synergy_with.join("； ")}
              </span>
            </div>
          )}
          {card.combination_hints.conflict_with.length > 0 && (
            <div>
              <span className="text-rose-700 dark:text-rose-300">
                ✖ 衝突：
              </span>
              <span className="text-foreground">
                {card.combination_hints.conflict_with.join("； ")}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------- 矛盾說明書面板（A0 + A4 整合）----------

import type {
  SubRequirement,
  SubRequirementKind,
  SrWeakWarning,
} from "@/types/directedTriz";

const KIND_LABEL: Record<
  SubRequirementKind,
  { tag: string; tone: string }
> = {
  desired_improvement: {
    tag: "想改善",
    tone: "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200",
  },
  undesired_effect: {
    tag: "想避免",
    tone: "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  },
  boundary_condition: {
    tag: "不可違反",
    tone: "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200",
  },
  mission_outcome: {
    tag: "驗收標準",
    tone: "bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-200",
  },
};

export function ContradictionManifest({
  contradictionDescription,
  subRequirements,
  weakWarnings = [],
}: {
  contradictionDescription: string;
  subRequirements: SubRequirement[];
  weakWarnings?: SrWeakWarning[];
}) {
  if (subRequirements.length === 0 && weakWarnings.length === 0) return null;

  return (
    <div className="border border-dashed rounded-md p-3 bg-muted/30 space-y-2 text-[11px]">
      <div className="flex items-center gap-1.5">
        <span className="font-medium text-foreground/80">
          矛盾說明書（閱讀背景，不是驗收條件 — 真正驗證見整併後 Brief 任務檢核）
        </span>
        <Tooltip>
          <TooltipTrigger asChild>
            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
          </TooltipTrigger>
          <TooltipContent className="max-w-sm text-xs leading-relaxed">
            這份清單描述「這條矛盾在說什麼」，給你在挑方向前先看背景。
            單一方向解掉幾條 SR 不等於矛盾被解；真正驗證是
            RD 勾完方向、按下「跨矛盾整併」之後產出的 Brief 任務檢核。
          </TooltipContent>
        </Tooltip>
      </div>

      {contradictionDescription && (
        <p className="text-muted-foreground italic">
          ⚙ {contradictionDescription}
        </p>
      )}

      {subRequirements.length > 0 && (
        <ol className="space-y-1 list-decimal pl-5">
          {subRequirements.map((sr) => {
            const kind: SubRequirementKind = sr.kind ?? "desired_improvement";
            const k = KIND_LABEL[kind];
            return (
              <li key={sr.id}>
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px] mr-1.5 font-normal border-0",
                    k.tone,
                  )}
                >
                  {k.tag}
                </Badge>
                <span className="text-foreground">{sr.description}</span>
                {sr.source_ref && sr.source_ref !== "contradiction" && (
                  <span className="text-muted-foreground ml-1">
                    （{sr.source_ref}）
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      )}

      {weakWarnings.length > 0 && (
        <div className="border-t border-dashed pt-1.5">
          <span className="text-muted-foreground">
            ⚠️ 弱相關（不列為 SR，但提醒你存在）：
          </span>
          <ul className="space-y-0.5 mt-1 pl-5 list-disc text-muted-foreground">
            {weakWarnings.map((w) => (
              <Tooltip key={w.candidate_id}>
                <TooltipTrigger asChild>
                  <li className="cursor-help">
                    {w.raw_text}{" "}
                    <span className="text-[10px]">（{w.source_ref}）</span>
                  </li>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs text-xs leading-relaxed">
                  {w.why_weak ||
                    "此條目與此矛盾僅弱相關（相關性評分=1），不列為正式 SR，但 RD 可在 Brief 任務檢核 階段重新檢查。"}
                </TooltipContent>
              </Tooltip>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
