import { useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import {
  ChevronRight,
  Pencil,
  Trash2,
  Layers,
  Box,
  Component as ComponentIcon,
} from "lucide-react";
import type { Subsystem } from "@/types/create";
import type { SpatialEstimate } from "@/types/generated/subsystem";
import { InterfaceContractsPanel } from "./InterfaceContractsPanel";

interface SubsystemHierarchyViewProps {
  subsystems: Subsystem[];
  contradictionMap: Map<string, string>;
  onToggle: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  /** Wave 3 (WBS 7.5) — open RD inline override dialog for a neighbour spatial estimate. */
  onOverrideSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
  /** Wave 3 (WBS 7.6) — open promote-to-learned dialog for a neighbour spatial estimate. */
  onPromoteSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
}

/** 遞迴樹節點：繼承 Subsystem 所有欄位 + 遞迴 children */
type SubsystemTreeNode = Subsystem & {
  children: SubsystemTreeNode[];
};

// Level badge config
const LEVEL_CONFIG = {
  system: {
    label: "System",
    icon: Layers,
    color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
    border: "border-l-indigo-400",
  },
  module: {
    label: "Module",
    icon: Box,
    color: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
    border: "border-l-blue-400",
  },
  component: {
    label: "Component",
    icon: ComponentIcon,
    color: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
    border: "border-l-slate-300",
  },
};

// Source badge config
const SOURCE_CONFIG: Record<string, { label: string; cls: string }> = {
  rd: { label: "RD", cls: "bg-primary/15 text-primary border-primary/30" },
  ai: { label: "AI", cls: "bg-muted border-muted-foreground/30" },
  ai_edited: {
    label: "AI+RD",
    cls: "bg-accent/15 text-accent-foreground border-accent/30",
  },
};

/** Build a tree from flat subsystem list */
function buildTree(subsystems: Subsystem[]): SubsystemTreeNode[] {
  const byId = new Map<string, SubsystemTreeNode>();
  const roots: SubsystemTreeNode[] = [];

  // First pass: create nodes with children array
  for (const ss of subsystems) {
    byId.set(ss.id, { ...ss, children: [] });
  }

  // Second pass: link children to parents
  for (const ss of subsystems) {
    const node = byId.get(ss.id)!;
    if (ss.parentId && byId.has(ss.parentId)) {
      byId.get(ss.parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}

// ── Component List (Level 3) ──
function ComponentList({
  components,
  onOverrideSpatial,
  onPromoteSpatial,
}: {
  components: SubsystemTreeNode[];
  onOverrideSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
  onPromoteSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
}) {
  if (components.length === 0) return null;

  return (
    <Collapsible>
      <CollapsibleTrigger asChild>
        <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors group mt-2">
          <ChevronRight className="h-3 w-3 transition-transform group-data-[state=open]:rotate-90" />
          <ComponentIcon className="h-3 w-3" />
          <span>Components ({components.length})</span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="ml-5 mt-1.5 space-y-1 border-l-2 border-slate-200 dark:border-slate-700 pl-3">
          {components.map((c) => (
            <div key={c.id} className="py-1">
              <div className="flex items-start gap-2 text-xs">
                <span className="w-1 h-1 rounded-full bg-slate-400 mt-1.5 shrink-0" />
                <div className="min-w-0">
                  <span className="font-medium">{c.name}</span>
                  {c.reason && (
                    <span className="text-muted-foreground ml-1.5">
                      — {c.reason}
                    </span>
                  )}
                </div>
              </div>
              {/* Component-level contracts (rare but allowed by the model) */}
              <InterfaceContractsPanel
                contracts={c.interfaceContracts}
                level="component"
                onOverride={(nb, sp) => onOverrideSpatial?.(c.id, nb, sp)}
                onPromote={(nb, sp) => onPromoteSpatial?.(c.id, nb, sp)}
              />
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

// InterfaceContracts panel moved to ./InterfaceContractsPanel.tsx as part of
// Stage 2 of refactor/subsystem-interface-contracts. Rendered at all three
// levels (system / module / component) because the data model allows any
// node to carry contracts with neighbours.

// ── Module Card (Level 2) — this is what gets checkboxed ──
function ModuleCard({
  module,
  components,
  contradictionMap,
  onToggle,
  onEdit,
  onDelete,
  onOverrideSpatial,
  onPromoteSpatial,
}: {
  module: SubsystemTreeNode;
  components: SubsystemTreeNode[];
  contradictionMap: Map<string, string>;
  onToggle: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onOverrideSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
  onPromoteSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
}) {
  const srcCfg = SOURCE_CONFIG[module.source] ?? SOURCE_CONFIG.ai;

  return (
    <div
      className={cn(
        "border rounded-lg p-4 transition-all",
        module.confirmed
          ? "border-blue-300 bg-blue-50/30 dark:bg-blue-950/20 dark:border-blue-700"
          : "border-border hover:border-blue-200"
      )}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        <Checkbox
          checked={module.confirmed}
          onCheckedChange={() => onToggle(module.id)}
          className="mt-0.5"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">{module.name}</span>
            <Badge
              variant="outline"
              className={cn("text-[9px]", LEVEL_CONFIG.module.color)}
            >
              Module
            </Badge>
            <Badge variant="outline" className={cn("text-[9px]", srcCfg.cls)}>
              {srcCfg.label}
            </Badge>
          </div>
          {module.reason && (
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed line-clamp-2">
              {module.reason}
            </p>
          )}

          {/* Contradiction badges */}
          {module.relatedContradictions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {module.relatedContradictions.map((cId) => (
                <Badge
                  key={cId}
                  variant="outline"
                  className="text-[9px] bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-700"
                >
                  ⚡{" "}
                  {(contradictionMap.get(cId) ?? cId).slice(0, 30)}
                  {(contradictionMap.get(cId) ?? "").length > 30
                    ? "…"
                    : ""}
                </Badge>
              ))}
            </div>
          )}

          {/* Components — collapsed */}
          <ComponentList
            components={components}
            onOverrideSpatial={onOverrideSpatial}
            onPromoteSpatial={onPromoteSpatial}
          />

          {/* Interface Contracts — collapsed */}
          <InterfaceContractsPanel
            contracts={module.interfaceContracts}
            level="module"
            onOverride={(nb, sp) => onOverrideSpatial?.(module.id, nb, sp)}
            onPromote={(nb, sp) => onPromoteSpatial?.(module.id, nb, sp)}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            onClick={() => onEdit(module.id)}
            className="p-1.5 rounded hover:bg-muted"
            title="編輯"
          >
            <Pencil className="h-3 w-3 text-muted-foreground" />
          </button>
          <button
            onClick={() => onDelete(module.id)}
            className="p-1.5 rounded hover:bg-destructive/10"
            title="刪除"
          >
            <Trash2 className="h-3 w-3 text-destructive" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── System Card (Level 1) — outermost container, no checkbox ──
function SystemCard({
  system,
  contradictionMap,
  onToggle,
  onEdit,
  onDelete,
  onOverrideSpatial,
  onPromoteSpatial,
}: {
  system: SubsystemTreeNode;
  contradictionMap: Map<string, string>;
  onToggle: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onOverrideSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
  onPromoteSpatial?: (subsystemId: string, neighbour: string, spatial: SpatialEstimate) => void;
}) {
  const [isOpen, setIsOpen] = useState(true);

  // Separate children by level
  const modules = system.children.filter((c) => c.level === "module");
  const directComponents = system.children.filter(
    (c) => c.level === "component"
  );

  return (
    <Card className={cn("border-l-4", LEVEL_CONFIG.system.border)}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <button className="w-full text-left p-4 pb-2 flex items-start gap-3 hover:bg-muted/20 transition-colors group">
            <ChevronRight
              className={cn(
                "h-4 w-4 text-muted-foreground shrink-0 mt-1 transition-transform",
                isOpen && "rotate-90"
              )}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Layers className="h-4 w-4 text-indigo-500 shrink-0" />
                <span className="text-base font-semibold">{system.name}</span>
                <Badge
                  variant="outline"
                  className={cn("text-[9px]", LEVEL_CONFIG.system.color)}
                >
                  System
                </Badge>
                <Badge variant="secondary" className="text-[9px]">
                  {modules.length} modules
                </Badge>
              </div>
              {system.reason && (
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed line-clamp-2">
                  {system.reason}
                </p>
              )}
              {/* System-level contradictions */}
              {system.relatedContradictions.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {system.relatedContradictions.map((cId) => (
                    <Badge
                      key={cId}
                      variant="outline"
                      className="text-[9px] bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-700"
                    >
                      ⚡ {(contradictionMap.get(cId) ?? cId).slice(0, 40)}…
                    </Badge>
                  ))}
                </div>
              )}
              {/* System-level interface contracts (inter-system boundaries) */}
              <InterfaceContractsPanel
                contracts={system.interfaceContracts}
                level="system"
                onOverride={(nb, sp) => onOverrideSpatial?.(system.id, nb, sp)}
                onPromote={(nb, sp) => onPromoteSpatial?.(system.id, nb, sp)}
              />
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 pt-1 space-y-3 ml-7">
            {modules.map((mod) => {
              const modComponents = mod.children.filter(
                (c) => c.level === "component"
              );
              return (
                <ModuleCard
                  key={mod.id}
                  module={mod}
                  components={modComponents}
                  contradictionMap={contradictionMap}
                  onToggle={onToggle}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onOverrideSpatial={onOverrideSpatial}
                  onPromoteSpatial={onPromoteSpatial}
                />
              );
            })}

            {/* Direct components under system (no module parent) */}
            {directComponents.length > 0 && (
              <div className="border rounded-lg p-3 border-dashed bg-muted/10">
                <p className="text-xs text-muted-foreground mb-2">
                  未歸類元件（建議歸入模組）
                </p>
                {directComponents.map((c) => (
                  <div key={c.id} className="py-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                      <span>{c.name}</span>
                      <span className="text-muted-foreground">— {c.reason}</span>
                    </div>
                    {/* Component-level contracts (rare but allowed by the model) */}
                    <InterfaceContractsPanel
                      contracts={c.interfaceContracts}
                      level="component"
                      onOverride={(nb, sp) => onOverrideSpatial?.(c.id, nb, sp)}
                      onPromote={(nb, sp) => onPromoteSpatial?.(c.id, nb, sp)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// ── Main Export ──
export function SubsystemHierarchyView({
  subsystems,
  contradictionMap,
  onToggle,
  onEdit,
  onDelete,
  onOverrideSpatial,
  onPromoteSpatial,
}: SubsystemHierarchyViewProps) {
  const tree = buildTree(subsystems);

  if (tree.length === 0) {
    return (
      <div className="text-center py-12 space-y-3 bg-muted/30 rounded-xl border border-dashed">
        <Layers className="h-8 w-8 text-muted-foreground mx-auto" />
        <p className="text-muted-foreground font-medium">尚無子系統</p>
        <p className="text-xs text-muted-foreground">
          點擊「AI 建議子系統」自動生成，或手動新增
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tree.map((system) => (
        <SystemCard
          key={system.id}
          system={system}
          contradictionMap={contradictionMap}
          onToggle={onToggle}
          onEdit={onEdit}
          onDelete={onDelete}
          onOverrideSpatial={onOverrideSpatial}
          onPromoteSpatial={onPromoteSpatial}
        />
      ))}
    </div>
  );
}
