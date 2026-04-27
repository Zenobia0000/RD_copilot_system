import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Trash2, Plus } from "lucide-react";
import type { BriefConstraint } from "@/types/taskDefinition";

interface ConstraintsTableProps {
  constraints: BriefConstraint[];
  onChange: (constraints: BriefConstraint[]) => void;
  onRemove?: (id: string) => void;
  disabled?: boolean;
}

export function ConstraintsTable({ constraints, onChange, onRemove, disabled }: ConstraintsTableProps) {
  const addRow = () => {
    const code = `M${constraints.length + 1}`;
    onChange([
      ...constraints,
      { id: `c-${Date.now()}`, constraint_code: code, description: "", source: "" },
    ]);
  };

  const removeRow = (index: number) => {
    if (constraints.length <= 1) return;
    const removed = constraints[index];
    const updated = constraints.filter((_, i) => i !== index).map((c, i) => ({
      ...c,
      constraint_code: `M${i + 1}`,
    }));
    onChange(updated);
    if (onRemove) onRemove(removed.id);
  };

  const updateRow = (index: number, field: "description" | "source", value: string) => {
    const updated = constraints.map((c, i) =>
      i === index ? { ...c, [field]: value } : c
    );
    onChange(updated);
  };

  const hasValidData = constraints.some((c) => c.description.trim().length > 0);

  return (
    <div className="space-y-3">
      {/* Table header - hidden on mobile */}
      <div className="hidden sm:grid sm:grid-cols-[60px_1fr_1fr_40px] gap-2 text-xs font-medium text-muted-foreground px-1">
        <span>代碼</span>
        <span>約束描述 *</span>
        <span>來源依據</span>
        <span></span>
      </div>

      {/* Rows */}
      {constraints.map((c, index) => (
        <div
          key={c.id}
          className="grid grid-cols-1 sm:grid-cols-[60px_1fr_1fr_40px] gap-2 items-start rounded-md border p-3 sm:p-2 sm:border-0 sm:rounded-none"
        >
          {/* Code - readonly */}
          <div className="flex items-center gap-2 sm:block">
            <span className="text-xs text-muted-foreground sm:hidden">代碼：</span>
            <span className="text-sm font-mono text-muted-foreground bg-muted rounded px-2 py-1">
              {c.constraint_code}
            </span>
          </div>

          {/* Description */}
          <div>
            <span className="text-xs text-muted-foreground sm:hidden">約束描述 *</span>
            <Input
              value={c.description}
              onChange={(e) => updateRow(index, "description", e.target.value)}
              placeholder="例：成本 ≤ $500"
              maxLength={200}
              disabled={disabled}
              className={!c.description.trim() ? "" : "border-l-[3px] border-l-[hsl(var(--success))]"}
            />
          </div>

          {/* Source */}
          <div>
            <span className="text-xs text-muted-foreground sm:hidden">來源依據</span>
            <Input
              value={c.source}
              onChange={(e) => updateRow(index, "source", e.target.value)}
              placeholder="例：規格書 v2.1"
              maxLength={200}
              disabled={disabled}
            />
          </div>

          {/* Delete */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
            onClick={() => removeRow(index)}
            disabled={constraints.length <= 1 || disabled}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}

      {!hasValidData && constraints.length > 0 && (
        <p className="text-xs text-destructive px-1">至少需要 1 項硬約束。</p>
      )}

      <Button type="button" variant="ghost" size="sm" onClick={addRow} disabled={disabled}>
        <Plus className="h-4 w-4 mr-1" />
        新增約束
      </Button>
    </div>
  );
}
