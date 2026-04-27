import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2 } from "lucide-react";
import type { TaskDefinitionKPI } from "@/types/taskDefinition";

interface KpiInputListProps {
  kpis: TaskDefinitionKPI[];
  onChange: (kpis: TaskDefinitionKPI[]) => void;
  errors?: Record<string, string[]>; // index-based errors
}

export function KpiInputList({ kpis, onChange, errors }: KpiInputListProps) {
  const addKpi = () => {
    onChange([
      ...kpis,
      { id: `kpi-${Date.now()}`, name: "", target: "", method: "" },
    ]);
  };

  const removeKpi = (index: number) => {
    onChange(kpis.filter((_, i) => i !== index));
  };

  const updateKpi = (index: number, field: keyof TaskDefinitionKPI, value: string) => {
    const updated = kpis.map((kpi, i) =>
      i === index ? { ...kpi, [field]: value } : kpi
    );
    onChange(updated);
  };

  return (
    <div className="space-y-3">
      {kpis.map((kpi, index) => {
        const kpiErrors = errors?.[String(index)];
        return (
          <div
            key={kpi.id}
            className="rounded-md border p-4 space-y-3 bg-card"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                指標 {index + 1}
              </span>
              {kpis.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive"
                  onClick={() => removeKpi(index)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="text-xs">名稱</Label>
                <Input
                  placeholder="例：傳動效率"
                  value={kpi.name}
                  onChange={(e) => updateKpi(index, "name", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">目標值</Label>
                <Input
                  placeholder="例：≥ 85%"
                  value={kpi.target}
                  onChange={(e) => updateKpi(index, "target", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">衡量方式</Label>
                <Input
                  placeholder="例：實驗室台架測試"
                  value={kpi.method}
                  onChange={(e) => updateKpi(index, "method", e.target.value)}
                />
              </div>
            </div>
            {kpiErrors && (
              <p className="text-xs text-destructive">{kpiErrors.join("、")}</p>
            )}
          </div>
        );
      })}

      <Button type="button" variant="outline" size="sm" onClick={addKpi}>
        <Plus className="h-4 w-4 mr-1" />
        新增指標
      </Button>
    </div>
  );
}
