/**
 * SchematicToolbar — 結構示意圖工具列
 *
 * 提供篩選與搜尋控制，包含：
 *  - 搜尋輸入框
 *  - 關係型別 Checkbox 群組
 *  - 風險篩選 Select
 *  - 層級篩選 Select
 *  - 元件切換 Toggle
 *  - 重置按鈕
 *
 * @see plans/structural-schematic-view.md §6.5
 */

import { useCallback } from "react";
import { Search, RotateCcw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import type { SchematicFilterState, RelationType, RiskLevel, SchematicBlockLevel } from "./types";
import {
  createDefaultFilterState,
  RELATION_TYPE_COLORS,
  RELATION_TYPE_LABELS,
} from "./types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SchematicToolbarProps {
  filter: SchematicFilterState;
  onChange: (next: SchematicFilterState) => void;
  /** Trigger fitView on the canvas */
  onFitView?: () => void;
  /** Total block count for display */
  totalBlocks?: number;
  className?: string;
}

// ---------------------------------------------------------------------------
// Relation types to show as checkboxes (exclude hierarchy — always shown)
// ---------------------------------------------------------------------------

const FILTERABLE_RELATION_TYPES: RelationType[] = [
  "signal",
  "thermal",
  "load",
  "envelope",
  "other",
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SchematicToolbar({
  filter,
  onChange,
  onFitView,
  totalBlocks,
  className,
}: SchematicToolbarProps) {
  // ── Helpers ──
  const update = useCallback(
    (partial: Partial<SchematicFilterState>) => {
      onChange({ ...filter, ...partial });
    },
    [filter, onChange],
  );

  const toggleRelationType = useCallback(
    (type: RelationType) => {
      const next = new Set(filter.relationTypes);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      onChange({ ...filter, relationTypes: next });
    },
    [filter, onChange],
  );

  const handleReset = useCallback(() => {
    onChange(createDefaultFilterState());
    onFitView?.();
  }, [onChange, onFitView]);

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-3 gap-y-2 px-2 py-2 rounded-lg bg-muted/30 border text-xs",
        className,
      )}
    >
      {/* Search */}
      <div className="relative flex-shrink-0">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          type="text"
          placeholder="搜尋區塊…"
          value={filter.searchQuery}
          onChange={(e) => update({ searchQuery: e.target.value })}
          className="h-7 w-[140px] pl-7 text-xs"
        />
      </div>

      {/* Relation type checkboxes */}
      <div className="flex items-center gap-2 border-l border-muted pl-3">
        <span className="text-muted-foreground font-medium">關係：</span>
        {FILTERABLE_RELATION_TYPES.map((type) => (
          <label
            key={type}
            className="flex items-center gap-1 cursor-pointer select-none"
          >
            <Checkbox
              checked={filter.relationTypes.has(type)}
              onCheckedChange={() => toggleRelationType(type)}
              className="h-3.5 w-3.5"
              style={
                filter.relationTypes.has(type)
                  ? {
                      borderColor: RELATION_TYPE_COLORS[type],
                      backgroundColor: RELATION_TYPE_COLORS[type],
                    }
                  : { borderColor: RELATION_TYPE_COLORS[type] }
              }
            />
            <span>{RELATION_TYPE_LABELS[type]}</span>
          </label>
        ))}
      </div>

      {/* Risk filter */}
      <div className="flex items-center gap-1.5 border-l border-muted pl-3">
        <span className="text-muted-foreground font-medium">風險：</span>
        <Select
          value={filter.riskFilter}
          onValueChange={(v) => update({ riskFilter: v as RiskLevel | "all" })}
        >
          <SelectTrigger className="h-7 w-[70px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="high">高</SelectItem>
            <SelectItem value="medium">中</SelectItem>
            <SelectItem value="low">低</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Level filter */}
      <div className="flex items-center gap-1.5 border-l border-muted pl-3">
        <span className="text-muted-foreground font-medium">層級：</span>
        <Select
          value={filter.levelFilter}
          onValueChange={(v) =>
            update({ levelFilter: v as SchematicBlockLevel | "all" })
          }
        >
          <SelectTrigger className="h-7 w-[80px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="system">系統</SelectItem>
            <SelectItem value="module">模組</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Component toggle */}
      <div className="flex items-center gap-1.5 border-l border-muted pl-3">
        <Switch
          id="show-components"
          checked={filter.showComponents}
          onCheckedChange={(checked) =>
            update({ showComponents: Boolean(checked) })
          }
          className="h-4 w-7"
        />
        <Label
          htmlFor="show-components"
          className="text-xs cursor-pointer select-none"
        >
          顯示元件
        </Label>
      </div>

      {/* Total blocks badge */}
      {typeof totalBlocks === "number" && (
        <Badge variant="outline" className="text-[10px] h-5 px-1.5">
          {totalBlocks} 區塊
        </Badge>
      )}

      {/* Reset */}
      <Button
        size="sm"
        variant="ghost"
        className="h-7 px-2 text-xs gap-1 ml-auto"
        onClick={handleReset}
      >
        <RotateCcw className="w-3 h-3" />
        重置
      </Button>
    </div>
  );
}
