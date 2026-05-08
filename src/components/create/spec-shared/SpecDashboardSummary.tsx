/**
 * SpecDashboardSummary — Layer 1 行動導向儀表板總覽。
 *
 * 顯示：
 * - 全局統計卡片（規格總數、平均信心、待驗證數）
 * - 各系統的快速狀態列表（信心度色條 + 規格數 + 行動提示）
 *
 * 設計理念：RD 打開後 3 秒內知道「哪裡要先動手」。
 *
 * @see plans/rd-friendly-spec-ux-design.md §Layer 1
 */

import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

import type { SpecTreeNode } from "../hierarchical-spec/buildSpecTree";
import { pctStr } from "./spec-helpers";
import { toSimplifiedLevel } from "./SimplifiedConfidenceIcon";
import type { DraftConfidence } from "@/types/generated/engineeringSpec";
import { CONFIDENCE_SCORES } from "@/types/generated/engineeringSpec";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SpecDashboardSummaryProps {
  specTree: SpecTreeNode[];
  className?: string;
  /** Callback when user clicks a system row to scroll/navigate. */
  onSystemClick?: (systemName: string) => void;
}

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

interface GlobalStats {
  totalSpecs: number;
  verificationCount: number;
  avgConfidence: number;
  systemCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
}

interface SystemSummary {
  name: string;
  totalSpecs: number;
  verificationCount: number;
  avgConfidence: number;
  dominantConfidence: DraftConfidence | null;
  actionHint: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function computeGlobalStats(tree: SpecTreeNode[]): GlobalStats {
  let totalSpecs = 0;
  let verificationCount = 0;
  let weightedConf = 0;
  let highCount = 0;
  let mediumCount = 0;
  let lowCount = 0;

  for (const root of tree) {
    totalSpecs += root.aggregated.totalSpecs;
    verificationCount += root.aggregated.verificationCount;
    weightedConf +=
      root.aggregated.totalSpecs * root.aggregated.avgConfidence;

    // Count specs by simplified level from drafts
    if (root.draft) {
      for (const spec of root.draft.specs) {
        const level = toSimplifiedLevel(spec.confidence);
        if (level === "high") highCount++;
        else if (level === "medium") mediumCount++;
        else lowCount++;
      }
    }
    // Also count from children recursively
    function countChildren(node: SpecTreeNode) {
      for (const child of node.children) {
        if (child.draft) {
          for (const spec of child.draft.specs) {
            const level = toSimplifiedLevel(spec.confidence);
            if (level === "high") highCount++;
            else if (level === "medium") mediumCount++;
            else lowCount++;
          }
        }
        countChildren(child);
      }
    }
    countChildren(root);
  }

  return {
    totalSpecs,
    verificationCount,
    avgConfidence: totalSpecs > 0 ? weightedConf / totalSpecs : 0,
    systemCount: tree.length,
    highCount,
    mediumCount,
    lowCount,
  };
}

function computeSystemSummaries(tree: SpecTreeNode[]): SystemSummary[] {
  return tree.map((node) => {
    // Find dominant confidence by collecting all specs
    const allSpecs: DraftConfidence[] = [];
    function collectSpecs(n: SpecTreeNode) {
      if (n.draft) {
        for (const s of n.draft.specs) {
          allSpecs.push(s.confidence);
        }
      }
      for (const child of n.children) collectSpecs(child);
    }
    collectSpecs(node);

    // Find which confidence level has the most specs
    const confCounts: Record<string, number> = {};
    for (const c of allSpecs) {
      confCounts[c] = (confCounts[c] ?? 0) + 1;
    }
    const dominant = Object.entries(confCounts).sort(
      ([, a], [, b]) => b - a,
    )[0]?.[0] as DraftConfidence | undefined;

    // Action hint
    let actionHint = "";
    if (node.aggregated.verificationCount > 0) {
      actionHint = `${node.aggregated.verificationCount} 項待驗證`;
    } else if (node.aggregated.avgConfidence < 0.5) {
      actionHint = "信心度偏低，建議優先審查";
    } else if (node.aggregated.avgConfidence >= 0.75) {
      actionHint = "狀態良好";
    } else {
      actionHint = "部分估算值需確認";
    }

    return {
      name: node.name,
      totalSpecs: node.aggregated.totalSpecs,
      verificationCount: node.aggregated.verificationCount,
      avgConfidence: node.aggregated.avgConfidence,
      dominantConfidence: dominant ?? null,
      actionHint,
    };
  });
}

// ---------------------------------------------------------------------------
// Stat card sub-component
// ---------------------------------------------------------------------------

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <Card className="flex-1 min-w-[120px]">
      <CardContent className="p-3 flex items-center gap-3">
        <div className={cn("p-2 rounded-lg", color ?? "bg-muted")}>
          {icon}
        </div>
        <div>
          <p className="text-lg font-bold leading-none">{value}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function SpecDashboardSummary({
  specTree,
  className,
  onSystemClick,
}: SpecDashboardSummaryProps) {
  const stats = useMemo(() => computeGlobalStats(specTree), [specTree]);
  const systems = useMemo(
    () => computeSystemSummaries(specTree),
    [specTree],
  );

  if (stats.totalSpecs === 0) return null;

  return (
    <div className={cn("space-y-3", className)}>
      {/* ── Stat cards row ── */}
      <div className="flex flex-wrap gap-2">
        <StatCard
          icon={<BarChart3 className="w-4 h-4 text-blue-600" />}
          label="規格總數"
          value={stats.totalSpecs}
          color="bg-blue-100 dark:bg-blue-950/30"
        />
        <StatCard
          icon={<TrendingUp className="w-4 h-4 text-green-600" />}
          label="平均信心度"
          value={pctStr(stats.avgConfidence)}
          color={
            stats.avgConfidence >= 0.7
              ? "bg-green-100 dark:bg-green-950/30"
              : stats.avgConfidence >= 0.4
                ? "bg-amber-100 dark:bg-amber-950/30"
                : "bg-red-100 dark:bg-red-950/30"
          }
        />
        <StatCard
          icon={
            stats.verificationCount > 0 ? (
              <ShieldAlert className="w-4 h-4 text-red-600" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            )
          }
          label="待驗證項目"
          value={stats.verificationCount}
          color={
            stats.verificationCount > 0
              ? "bg-red-100 dark:bg-red-950/30"
              : "bg-green-100 dark:bg-green-950/30"
          }
        />
      </div>

      {/* ── Confidence distribution bar ── */}
      {stats.totalSpecs > 0 && (
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-muted-foreground shrink-0">信心分布</span>
          <div className="flex-1 flex h-2 rounded-full overflow-hidden bg-muted">
            {stats.highCount > 0 && (
              <div
                className="bg-green-500 h-full"
                style={{
                  width: `${(stats.highCount / stats.totalSpecs) * 100}%`,
                }}
              />
            )}
            {stats.mediumCount > 0 && (
              <div
                className="bg-amber-500 h-full"
                style={{
                  width: `${(stats.mediumCount / stats.totalSpecs) * 100}%`,
                }}
              />
            )}
            {stats.lowCount > 0 && (
              <div
                className="bg-red-500 h-full"
                style={{
                  width: `${(stats.lowCount / stats.totalSpecs) * 100}%`,
                }}
              />
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="flex items-center gap-0.5">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
              {stats.highCount}
            </span>
            <span className="flex items-center gap-0.5">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-500" />
              {stats.mediumCount}
            </span>
            <span className="flex items-center gap-0.5">
              <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
              {stats.lowCount}
            </span>
          </div>
        </div>
      )}

      {/* ── System list with progress ── */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">各系統概況</p>
        {systems.map((sys) => (
          <button
            key={sys.name}
            className="w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-muted/50 transition-colors text-left"
            onClick={() => onSystemClick?.(sys.name)}
          >
            {/* Confidence dot */}
            <span
              className={cn(
                "inline-block w-2 h-2 rounded-full shrink-0",
                sys.avgConfidence >= 0.7
                  ? "bg-green-500"
                  : sys.avgConfidence >= 0.4
                    ? "bg-amber-500"
                    : "bg-red-500",
              )}
            />

            {/* System name */}
            <span className="font-medium min-w-[100px] shrink-0 max-h-[3.5rem] overflow-y-auto">
              {sys.name}
            </span>

            {/* Progress bar */}
            <div className="flex-1 max-w-[120px]">
              <Progress
                value={sys.avgConfidence * 100}
                className="h-1.5"
              />
            </div>

            {/* Confidence % */}
            <span
              className={cn(
                "font-mono w-10 text-right",
                sys.avgConfidence >= 0.7
                  ? "text-green-600"
                  : sys.avgConfidence >= 0.4
                    ? "text-amber-600"
                    : "text-red-600",
              )}
            >
              {pctStr(sys.avgConfidence)}
            </span>

            {/* Spec count */}
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
              {sys.totalSpecs}
            </Badge>

            {/* Verification warning */}
            {sys.verificationCount > 0 && (
              <Badge
                variant="outline"
                className="text-red-600 border-red-300 text-[10px] px-1 py-0 h-4 gap-0.5"
              >
                <AlertTriangle className="w-2.5 h-2.5" />
                {sys.verificationCount}
              </Badge>
            )}

            {/* Action hint */}
            <span className="text-muted-foreground ml-auto max-h-[3rem] overflow-y-auto">
              {sys.actionHint}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
