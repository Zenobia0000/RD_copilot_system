/**
 * StructuralSchematicView — 結構示意圖主容器
 *
 * 整合 SchematicToolbar + SchematicCanvas + SchematicDetailPanel，
 * 使用 ResizablePanelGroup 實現左右分割佈局。
 *
 * 資料流:
 *  1. props (tree, drafts, packageMap, conceptInterfaces) → mapToSchematicModel → SchematicViewModel
 *  2. SchematicViewModel + SchematicFilterState → computeSchematicLayout → LayoutResult { nodes, edges }
 *  3. nodes/edges 餵入 SchematicCanvas (ReactFlow)
 *  4. 點擊節點 → 右側 SchematicDetailPanel 展開
 *
 * @see plans/structural-schematic-view.md §6.2
 */

import { useCallback, useMemo, useState, useRef } from "react";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

import type { SuggestedSubsystem } from "@/types/generated/subsystem";
import type { PackageMap } from "@/types/generated/subsystem";
import type { EngineeringSpecDraft } from "@/types/generated/engineeringSpec";
import type { ConceptInterface } from "@/types/conceptArchitecture";

import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

import type { SchematicBlock, SchematicFilterState } from "./types";
import { createDefaultFilterState } from "./types";
import { mapToSchematicModel } from "./mapToSchematicModel";
import type { MapToSchematicModelInput } from "./mapToSchematicModel";
import { computeSchematicLayout } from "./schematicLayout";
import { SchematicCanvas } from "./SchematicCanvas";
import { SchematicToolbar } from "./SchematicToolbar";
import { SchematicDetailPanel } from "./SchematicDetailPanel";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface StructuralSchematicViewProps {
  tree: SuggestedSubsystem[];
  drafts: EngineeringSpecDraft[];
  packageMap?: PackageMap | null;
  conceptInterfaces?: ConceptInterface[];
  onNodeClick?: (name: string) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function StructuralSchematicView({
  tree,
  drafts,
  packageMap,
  conceptInterfaces,
  onNodeClick,
  className,
}: StructuralSchematicViewProps) {
  // -- State -----------------------------------------------------------------
  const [filter, setFilter] = useState<SchematicFilterState>(
    createDefaultFilterState,
  );
  const [selectedBlock, setSelectedBlock] = useState<SchematicBlock | null>(
    null,
  );

  // Panel ref to imperatively resize right panel
  const rightPanelRef = useRef<import("react-resizable-panels").ImperativePanelHandle | null>(null);

  // -- Memoised view model ---------------------------------------------------
  const viewModel = useMemo(() => {
    const input: MapToSchematicModelInput = {
      tree,
      drafts,
      packageMap: packageMap ?? undefined,
      conceptInterfaces,
    };
    return mapToSchematicModel(input);
  }, [tree, drafts, packageMap, conceptInterfaces]);

  // -- Memoised layout -------------------------------------------------------
  const layout = useMemo(
    () => computeSchematicLayout(viewModel, filter),
    [viewModel, filter],
  );

  // -- Connected relations for selected block --------------------------------
  const selectedRelations = useMemo(() => {
    if (!selectedBlock) return [];
    return viewModel.relations.filter(
      (r) =>
        r.sourceId === selectedBlock.id || r.targetId === selectedBlock.id,
    );
  }, [selectedBlock, viewModel.relations]);

  // -- Handlers --------------------------------------------------------------
  const handleBlockClick = useCallback(
    (block: SchematicBlock) => {
      setSelectedBlock(block);
      // Expand right panel
      rightPanelRef.current?.resize(35);
      // Notify parent if needed
      onNodeClick?.(block.name);
    },
    [onNodeClick],
  );

  const handleCloseDetail = useCallback(() => {
    setSelectedBlock(null);
    // Collapse right panel
    rightPanelRef.current?.collapse();
  }, []);

  const handleFilterChange = useCallback((next: SchematicFilterState) => {
    setFilter(next);
  }, []);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div className={cn("space-y-2", className)}>
      {/* LLM disclaimer banner */}
      <div className="flex items-center gap-2 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span>
          以下結構示意圖由 LLM 推估產生，尺寸、空間佈局及介面關係僅供
          <strong>概念理解</strong>之用，不代表實際 CAD 設計。
        </span>
      </div>

      {/* Main split layout */}
      <ResizablePanelGroup
        direction="horizontal"
        className="rounded-lg border min-h-[500px]"
      >
        {/* Left panel: toolbar + canvas */}
        <ResizablePanel defaultSize={100} minSize={50}>
          <div className="flex flex-col h-full">
            <SchematicToolbar
              filter={filter}
              onChange={handleFilterChange}
              totalBlocks={viewModel.globalStats.totalBlocks}
              className="border-b"
            />
            <div className="flex-1 min-h-0">
              <SchematicCanvas
                nodes={layout.nodes}
                edges={layout.edges}
                onBlockClick={handleBlockClick}
                searchTerm={filter.searchQuery}
              />
            </div>
          </div>
        </ResizablePanel>

        {/* Resize handle — only visible when detail is open */}
        <ResizableHandle withHandle />

        {/* Right panel: detail (collapsed by default) */}
        <ResizablePanel
          ref={rightPanelRef}
          defaultSize={0}
          minSize={0}
          maxSize={50}
          collapsible
          collapsedSize={0}
        >
          {selectedBlock && (
            <SchematicDetailPanel
              block={selectedBlock}
              relations={selectedRelations}
              onClose={handleCloseDetail}
              className="h-full"
            />
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
