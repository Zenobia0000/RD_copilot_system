import { Boxes, AlertTriangle, StickyNote } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PackageMap, PackageNode } from "@/types/generated/subsystem";

/**
 * PackageMapPanel — Tab ② 區塊 B display-layer primitive.
 *
 * Renders the F2.5 spatial validator output (Package Map) for the currently
 * selected design: inline top/side SVG, clash warnings, required envelope
 * totals and optional discovery notes.
 *
 * Visual language (per create-ux-spec "Discovery vs Overlay"):
 * this is the DISCOVERY surface, so fills/badges use NEUTRAL slate/gray.
 * Red/orange/green are reserved for the overlay compare view. Clash
 * indicators may use a red border/banner only.
 *
 * @see docs/diagrams/create-ux-spec.md Tab ② 區塊 B
 * @see docs/e2e/module/Forward_Subsystem_Discovery_Architecture.md §3.3 / §5
 */
interface PackageMapPanelProps {
  packageMap?: PackageMap | null;
  className?: string;
}

export function PackageMapPanel({ packageMap, className }: PackageMapPanelProps) {
  const isEmpty =
    !packageMap || !packageMap.nodes || packageMap.nodes.length === 0;

  return (
    <Card
      className={cn(
        "border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-900/20",
        className,
      )}
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
          <Boxes className="h-4 w-4" />
          <span>Package Map · 空間封殼預估</span>
          {!isEmpty && (
            <Badge
              variant="outline"
              className="ml-auto text-[10px] border-slate-300 text-slate-600 dark:border-slate-700 dark:text-slate-300"
            >
              {packageMap!.nodes.length} nodes
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {isEmpty ? (
          <EmptyState />
        ) : (
          <>
            <ClashStrip nodes={packageMap!.nodes} />
            <TotalsReadout required={packageMap!.required} />
            <SvgViewport svg={packageMap!.svg} />
            <NotesList notes={packageMap!.notes} />
            <p className="text-[10px] text-muted-foreground/60 text-right select-none">
              {COORD_HINT}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

/** Global coordinate convention shared with backend prompts & USDA export. */
const COORD_HINT =
  "座標系：右手定則 X=右, Y=上, Z=前 · 原點=產品幾何中心 · 單位 mm";

function EmptyState() {
  return (
    <p className="text-xs italic text-muted-foreground py-4 text-center">
      尚無空間資料（validator 未產出 Package Map）— 不影響子系統確認
    </p>
  );
}

// ---------------------------------------------------------------------------
// Inline SVG viewport (XY top view + XZ side view from backend stdlib renderer)
// ---------------------------------------------------------------------------

function SvgViewport({ svg }: { svg?: string }) {
  if (!svg || svg.trim() === "") {
    return (
      <div className="rounded-md border border-dashed border-slate-300 dark:border-slate-700 bg-slate-100/50 dark:bg-slate-800/30 py-6 text-center text-[11px] text-muted-foreground">
        （此 Package Map 尚未附帶 SVG 視圖）
      </div>
    );
  }

  return (
    <div
      className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/50 overflow-auto max-h-[360px] p-2 [&_svg]:max-w-full [&_svg]:h-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

// ---------------------------------------------------------------------------
// Clash strip — red banner listing every clashing pair (deduped)
// ---------------------------------------------------------------------------

function ClashStrip({ nodes }: { nodes: PackageNode[] }) {
  // Collect unordered pairs so "motor_mount ↔ battery_bay" is only shown once.
  const pairs = new Set<string>();
  for (const n of nodes) {
    for (const other of n.clashes ?? []) {
      const [a, b] = [n.name, other].sort();
      pairs.add(`${a} ↔ ${b}`);
    }
  }
  if (pairs.size === 0) return null;

  return (
    <div className="rounded-md border border-red-400 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-2.5 text-xs">
      <div className="flex items-center gap-1.5 font-semibold text-red-800 dark:text-red-200">
        <AlertTriangle className="h-3.5 w-3.5" />
        <span>空間衝突 · {pairs.size} 對</span>
      </div>
      <ul className="mt-1 ml-5 list-disc space-y-0.5 text-red-700 dark:text-red-300">
        {[...pairs].map((p) => (
          <li key={p} className="font-mono text-[11px]">
            {p}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Totals readout — required envelope + total mass
// ---------------------------------------------------------------------------

function TotalsReadout({
  required,
}: {
  required: PackageMap["required"];
}) {
  const [w, h, d] = required.total_bbox_mm;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-slate-700 dark:text-slate-300">
      <span>
        <span className="text-muted-foreground">質量 · </span>
        {formatGrams(required.total_mass_g)} g
      </span>
      <span className="text-slate-300 dark:text-slate-700">|</span>
      <span>
        <span className="text-muted-foreground">最小封殼 · </span>
        {fmtMm(w)}×{fmtMm(h)}×{fmtMm(d)} mm
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Notes list — discovery-time hints from the validator
// ---------------------------------------------------------------------------

function NotesList({ notes }: { notes?: string[] }) {
  if (!notes || notes.length === 0) return null;
  return (
    <div className="pt-1 border-t border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mt-2">
        <StickyNote className="h-3 w-3" />
        <span>Notes</span>
      </div>
      <ul className="mt-1 ml-4 list-disc space-y-0.5 text-[11px] text-muted-foreground">
        {notes.map((n, i) => (
          <li key={i}>{n}</li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatGrams(g: number): string {
  return g.toLocaleString("en-US");
}

function fmtMm(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}
