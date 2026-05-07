/**
 * SubsystemDatasheet — Layer 2 Datasheet-style table view for a single subsystem.
 *
 * Collects ALL specs from a SpecTreeNode (system-level) and its descendants,
 * groups them by DraftCategory, and renders each category as a proper <table>
 * using SpecRow in tableMode.
 *
 * Features:
 * - Category tab switching (6 categories from DRAFT_CATEGORIES)
 * - Table columns: 規格名稱 | 數值+單位 | 信心度 | 來源 | 狀態 | 詳情
 * - Confidence summary bar in header
 * - CSV export button
 * - Interface contracts section at bottom
 *
 * @see plans/rd-friendly-spec-ux-design.md §Layer 2
 */

import { useMemo, useState, useCallback } from "react";
import { Download } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { DraftValue, DraftCategory } from "@/types/generated/engineeringSpec";
import { DRAFT_CATEGORIES } from "@/types/generated/engineeringSpec";
import type { SpecTreeNode } from "./buildSpecTree";
import { SpecRow } from "../spec-shared/SpecRow";
import {
  SimplifiedConfidenceIcon,
  toSimplifiedLevel,
} from "../spec-shared/SimplifiedConfidenceIcon";
import { fmtValue, humanize } from "../spec-shared/spec-helpers";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SubsystemDatasheetProps {
  /** System-level tree node whose descendants' specs will be displayed. */
  node: SpecTreeNode;
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Recursively collect all DraftValue[] from a node and all descendants. */
function collectAllSpecs(node: SpecTreeNode): DraftValue[] {
  const specs: DraftValue[] = [];
  if (node.draft?.specs) {
    specs.push(...node.draft.specs);
  }
  for (const child of node.children) {
    specs.push(...collectAllSpecs(child));
  }
  return specs;
}

/** Group specs by DraftCategory, preserving DRAFT_CATEGORIES order. */
function groupByCategory(
  specs: DraftValue[],
): Map<DraftCategory, DraftValue[]> {
  const map = new Map<DraftCategory, DraftValue[]>();
  for (const cat of DRAFT_CATEGORIES) {
    map.set(cat.key, []);
  }
  for (const s of specs) {
    const list = map.get(s.category);
    if (list) {
      list.push(s);
    } else {
      // Fallback if category not in DRAFT_CATEGORIES
      map.set(s.category, [s]);
    }
  }
  return map;
}

/** Export specs as CSV string and trigger download. */
function exportCsv(subsystemName: string, specs: DraftValue[]) {
  const esc = (s: string) => {
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const header = "category,field_name,value,unit,confidence,source,needs_verification";
  const rows = specs.map((s) => {
    const val =
      typeof s.value === "object" ? JSON.stringify(s.value) : String(s.value);
    return [
      s.category,
      s.field_name,
      val,
      s.unit ?? "",
      s.confidence,
      s.source,
      s.needs_verification ? "yes" : "no",
    ]
      .map(esc)
      .join(",");
  });

  const csv = [header, ...rows].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${subsystemName.replace(/\s+/g, "_")}_specs.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SubsystemDatasheet({ node, className }: SubsystemDatasheetProps) {
  const allSpecs = useMemo(() => collectAllSpecs(node), [node]);
  const grouped = useMemo(() => groupByCategory(allSpecs), [allSpecs]);

  // Only show categories that have specs
  const activeCats = useMemo(
    () => DRAFT_CATEGORIES.filter((c) => (grouped.get(c.key)?.length ?? 0) > 0),
    [grouped],
  );

  const [activeTab, setActiveTab] = useState<DraftCategory | "__all__">("__all__");

  const handleExport = useCallback(() => {
    exportCsv(node.name, allSpecs);
  }, [node.name, allSpecs]);

  // Confidence distribution for header bar
  const confDist = useMemo(() => {
    let high = 0,
      medium = 0,
      low = 0;
    for (const s of allSpecs) {
      const level = toSimplifiedLevel(s.confidence);
      if (level === "high") high++;
      else if (level === "medium") medium++;
      else low++;
    }
    return { high, medium, low, total: allSpecs.length };
  }, [allSpecs]);

  const verifyCount = useMemo(
    () => allSpecs.filter((s) => s.needs_verification).length,
    [allSpecs],
  );

  if (allSpecs.length === 0) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="p-6 text-center text-sm text-muted-foreground">
          此子系統尚無規格資料
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      {/* ── Header ── */}
      <CardHeader className="pb-2 space-y-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">{node.name}</h3>
            {node.draft?.subsystem_code && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 font-mono">
                {node.draft.subsystem_code}
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={handleExport}
          >
            <Download className="w-3.5 h-3.5" />
            匯出 CSV
          </Button>
        </div>

        {/* Summary row */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span>共 {confDist.total} 項規格</span>
          <span>
            信心度：
            <span className="inline-flex items-center gap-0.5 ml-1">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
              {confDist.high}
            </span>
            <span className="inline-flex items-center gap-0.5 ml-2">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-500" />
              {confDist.medium}
            </span>
            <span className="inline-flex items-center gap-0.5 ml-2">
              <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
              {confDist.low}
            </span>
          </span>
          {verifyCount > 0 && (
            <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4">
              待驗證 {verifyCount}
            </Badge>
          )}
        </div>

        {/* Confidence bar */}
        {confDist.total > 0 && (
          <div className="flex h-1.5 rounded-full overflow-hidden bg-muted">
            {confDist.high > 0 && (
              <div
                className="bg-green-500 transition-all"
                style={{ width: `${(confDist.high / confDist.total) * 100}%` }}
              />
            )}
            {confDist.medium > 0 && (
              <div
                className="bg-amber-500 transition-all"
                style={{ width: `${(confDist.medium / confDist.total) * 100}%` }}
              />
            )}
            {confDist.low > 0 && (
              <div
                className="bg-red-500 transition-all"
                style={{ width: `${(confDist.low / confDist.total) * 100}%` }}
              />
            )}
          </div>
        )}
      </CardHeader>

      {/* ── Category tabs ── */}
      <div className="px-4 border-b">
        <div className="flex gap-0.5 overflow-x-auto -mb-px">
          {/* "All" tab */}
          <button
            onClick={() => setActiveTab("__all__")}
            className={cn(
              "px-3 py-1.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap",
              activeTab === "__all__"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            全部 ({allSpecs.length})
          </button>

          {activeCats.map((cat) => {
            const count = grouped.get(cat.key)?.length ?? 0;
            return (
              <button
                key={cat.key}
                onClick={() => setActiveTab(cat.key)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1",
                  activeTab === cat.key
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                <span>{cat.icon}</span>
                {cat.labelZh}
                <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5 ml-0.5">
                  {count}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Spec tables by category ── */}
      <CardContent className="p-0">
        {activeTab === "__all__" ? (
          // Show all categories sequentially
          <div className="divide-y">
            {activeCats.map((cat) => {
              const specs = grouped.get(cat.key) ?? [];
              if (specs.length === 0) return null;
              return (
                <CategoryTable
                  key={cat.key}
                  categoryKey={cat.key}
                  icon={cat.icon}
                  labelZh={cat.labelZh}
                  specs={specs}
                />
              );
            })}
          </div>
        ) : (
          // Single category
          (() => {
            const catDef = DRAFT_CATEGORIES.find((c) => c.key === activeTab);
            const specs = grouped.get(activeTab) ?? [];
            return (
              <CategoryTable
                categoryKey={activeTab}
                icon={catDef?.icon ?? "📋"}
                labelZh={catDef?.labelZh ?? activeTab}
                specs={specs}
              />
            );
          })()
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// CategoryTable — renders a single category's specs as a <table>
// ---------------------------------------------------------------------------

interface CategoryTableProps {
  categoryKey: DraftCategory;
  icon: string;
  labelZh: string;
  specs: DraftValue[];
}

function CategoryTable({ categoryKey, icon, labelZh, specs }: CategoryTableProps) {
  if (specs.length === 0) return null;

  return (
    <div className="py-2">
      {/* Category header */}
      <div className="px-4 pb-1.5 flex items-center gap-1.5">
        <span className="text-sm">{icon}</span>
        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          {labelZh}
        </span>
        <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5">
          {specs.length}
        </Badge>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-t bg-muted/30">
              <th className="text-left py-1.5 px-2 font-medium text-muted-foreground w-[25%]">
                規格名稱
              </th>
              <th className="text-left py-1.5 px-2 font-medium text-muted-foreground w-[20%]">
                數值
              </th>
              <th className="text-left py-1.5 px-2 font-medium text-muted-foreground w-[15%]">
                信心度
              </th>
              <th className="text-left py-1.5 px-2 font-medium text-muted-foreground w-[15%]">
                來源
              </th>
              <th className="text-center py-1.5 px-2 font-medium text-muted-foreground w-[10%]">
                狀態
              </th>
              <th className="text-center py-1.5 px-2 font-medium text-muted-foreground w-[10%]">
                詳情
              </th>
            </tr>
          </thead>
          <tbody>
            {specs.map((s) => (
              <SpecRow
                key={`${s.field_name}-${s.category}`}
                spec={s}
                tableMode
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
