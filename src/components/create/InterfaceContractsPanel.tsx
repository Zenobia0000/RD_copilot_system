import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { ChevronRight, Link2, Pencil, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  InterfaceContract,
  InterfaceContractMap,
  SpatialEstimate,
} from "@/types/generated/subsystem";
import { INTERFACE_CONTRACT_DIMS } from "@/types/generated/subsystem";

/**
 * InterfaceContractsPanel — display-layer primitive for the 6-dim + spatial
 * interface contract map of a single subsystem tree node.
 *
 * Renders at ANY level (system / module / component) because the underlying
 * data model places contracts on any node that has neighbours — polymorphism
 * belongs at the data layer, not hardcoded to "module".
 *
 * @see Forward_Subsystem_Discovery_Architecture.md §6.5
 * @see docs/diagrams/create-ux-spec.md Tab ② 區塊 A
 */
interface InterfaceContractsPanelProps {
  contracts?: InterfaceContractMap | null;
  /** Optional hint for panel sizing — system level cards tend to need a wider grid. */
  level?: "system" | "module" | "component";
  /** Wave 3 (WBS 7.5) — RD inline override on a per-neighbour spatial estimate. */
  onOverride?: (neighbour: string, spatial: SpatialEstimate) => void;
  /** Wave 3 (WBS 7.6) — promote estimate to org-wide learned components. */
  onPromote?: (neighbour: string, spatial: SpatialEstimate) => void;
}

export function InterfaceContractsPanel({
  contracts,
  level = "module",
  onOverride,
  onPromote,
}: InterfaceContractsPanelProps) {
  if (!contracts || Object.keys(contracts).length === 0) return null;

  const entries: ReadonlyArray<readonly [string, InterfaceContract]> =
    Object.entries(contracts);

  return (
    <Collapsible>
      <CollapsibleTrigger asChild>
        <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors group mt-2">
          <ChevronRight className="h-3 w-3 transition-transform group-data-[state=open]:rotate-90" />
          <Link2 className="h-3 w-3" />
          <span>關聯 ({entries.length})</span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className={cn("mt-2 space-y-3", level === "system" ? "ml-6" : "ml-5")}>
          {entries.map(([target, contract]) => (
            <ContractCard
              key={target}
              target={target}
              contract={contract}
              level={level}
              onOverride={onOverride}
              onPromote={onPromote}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

// ---------------------------------------------------------------------------
// Single contract card (one neighbour ↔ current node)
// ---------------------------------------------------------------------------

function ContractCard({
  target,
  contract,
  level,
  onOverride,
  onPromote,
}: {
  target: string;
  contract: InterfaceContract;
  level: "system" | "module" | "component";
  onOverride?: (neighbour: string, spatial: SpatialEstimate) => void;
  onPromote?: (neighbour: string, spatial: SpatialEstimate) => void;
}) {
  const populated = INTERFACE_CONTRACT_DIMS.filter(
    (d) => contract[d.key] && contract[d.key].trim() !== "",
  );
  const hasSpatial = !!contract.spatial;
  const isEmpty = populated.length === 0 && !hasSpatial;

  return (
    <div className="text-xs border rounded-lg p-3 bg-muted/20 space-y-1.5">
      <p className="font-medium text-foreground">↔ {target}</p>

      {isEmpty ? (
        <p className="text-[10px] text-muted-foreground italic">
          （此介面尚未填寫任何維度，請重新執行 Suggest Subsystems 或手動編輯）
        </p>
      ) : (
        <>
          {populated.length > 0 && (
            <div
              className={cn(
                "grid gap-1.5",
                level === "system"
                  ? "grid-cols-1 md:grid-cols-3"
                  : "grid-cols-1 sm:grid-cols-2",
              )}
            >
              {populated.map((d) => (
                <div key={d.key}>
                  <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                    {d.labelZh}
                  </span>
                  <p className="text-muted-foreground leading-relaxed max-h-[3.5rem] overflow-y-auto">
                    {contract[d.key]}
                  </p>
                </div>
              ))}
            </div>
          )}

          {hasSpatial && (
            <SpatialBlock
              spatial={contract.spatial!}
              targetNeighbour={target}
              onOverride={onOverride}
              onPromote={onPromote}
            />
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Spatial sub-block (bbox + mass + confidence badge + reference trace)
// ---------------------------------------------------------------------------

/**
 * Confidence colour system — mirrors docs/diagrams/create-ux-spec.md v6
 * §Spatial Confidence 視覺對應. Colours deliberately match the dark-theme-
 * safe palette used in Mermaid diagrams across the architecture docs.
 */
const CONFIDENCE_STYLE: Record<
  NonNullable<SpatialEstimate["confidence"]>,
  { label: string; cls: string }
> = {
  rd_confirmed: {
    label: "RD 簽核",
    cls: "bg-emerald-900 text-white border-emerald-950 dark:bg-emerald-800",
  },
  library: {
    label: "Library",
    cls: "bg-emerald-100 text-emerald-900 border-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  },
  estimate: {
    label: "Estimate",
    cls: "bg-amber-100 text-amber-900 border-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  },
};

function SpatialBlock({
  spatial,
  targetNeighbour,
  onOverride,
  onPromote,
}: {
  spatial: SpatialEstimate;
  targetNeighbour?: string;
  onOverride?: (neighbour: string, spatial: SpatialEstimate) => void;
  onPromote?: (neighbour: string, spatial: SpatialEstimate) => void;
}) {
  const bbox = spatial.bbox;
  const bboxText = bbox
    ? `${fmt(bbox.x_mm)}×${fmt(bbox.y_mm)}×${fmt(bbox.z_mm)} mm`
    : "—";
  const massText = spatial.mass_g != null ? `${fmt(spatial.mass_g)} g` : "—";
  const confidence = spatial.confidence ?? "estimate";
  const source = spatial.reference_source ?? "";
  // llm_estimate gets its own red style (it's the weakest signal, RD should override)
  const isLlmEstimate = source === "llm_estimate" || (!source && confidence === "estimate");
  const confCls = isLlmEstimate
    ? "bg-red-100 text-red-900 border-red-800 dark:bg-red-900/40 dark:text-red-200"
    : CONFIDENCE_STYLE[confidence]?.cls ?? CONFIDENCE_STYLE.estimate.cls;
  const confLabel = isLlmEstimate
    ? "LLM 估計"
    : CONFIDENCE_STYLE[confidence]?.label ?? confidence;

  // Wave 3 visibility rules (WBS 7.5 / 7.6):
  //  - "我來給數字" — show whenever the value is not yet RD-confirmed (i.e.
  //    LLM estimate, library, web/seed estimate). RD override always wins.
  //  - "推升至 learned" — only when there's already a non-LLM grounded
  //    estimate (web/seed/etc.) AND it's not already learned. We hide if the
  //    source begins with `learned:` (already in the L2 table) or starts
  //    with `llm_estimate` (no real grounding to promote).
  const canOverride =
    !!onOverride && targetNeighbour != null && (isLlmEstimate || confidence !== "rd_confirmed");
  const canPromote =
    !!onPromote &&
    targetNeighbour != null &&
    confidence === "estimate" &&
    !source.startsWith("llm_estimate") &&
    !source.startsWith("learned:");

  return (
    <div
      className="mt-2 pt-2 border-t border-dashed border-border/60 space-y-1.5"
      title={source ? `reference_source: ${source}` : undefined}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px]">
        <span className="font-mono text-muted-foreground">📐 {bboxText}</span>
        <span className="font-mono text-muted-foreground">⚖ {massText}</span>
        <span
          className={cn(
            "px-1.5 py-0.5 rounded border font-semibold",
            confCls,
          )}
        >
          {confLabel}
        </span>
        {source && !isLlmEstimate && (
          <span className="text-muted-foreground break-all">
            src: {source}
          </span>
        )}
        {spatial.mounting_pattern && (
          <span className="text-muted-foreground">
            · mount: {spatial.mounting_pattern}
          </span>
        )}
      </div>

      {(canOverride || canPromote) && (
        <div className="flex flex-wrap items-center gap-1">
          {canOverride && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-6 px-2 text-[10px] gap-1"
              onClick={() => onOverride?.(targetNeighbour!, spatial)}
            >
              <Pencil className="h-3 w-3" />
              我來給數字
            </Button>
          )}
          {canPromote && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-6 px-2 text-[10px] gap-1"
              onClick={() => onPromote?.(targetNeighbour!, spatial)}
            >
              <TrendingUp className="h-3 w-3" />
              推升至 learned
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

function fmt(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}
