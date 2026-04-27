import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Trash2, Plus } from "lucide-react";
import type { BriefKPI } from "@/types/taskDefinition";

interface KpiListProps {
  kpis: BriefKPI[];
  onChange: (kpis: BriefKPI[]) => void;
  onRemove?: (id: string) => void;
  disabled?: boolean;
}

const MAX_KPIS = 5;

export function KpiList({ kpis, onChange, onRemove, disabled }: KpiListProps) {
  const addKpi = () => {
    if (kpis.length >= MAX_KPIS) return;
    onChange([
      ...kpis,
      { id: `k-${Date.now()}`, kpi_name: "", target_value: "", unit: "", measurement_method: "" },
    ]);
  };

  const removeKpi = (index: number) => {
    if (kpis.length <= 1) return;
    const removed = kpis[index];
    onChange(kpis.filter((_, i) => i !== index));
    if (onRemove) onRemove(removed.id);
  };

  const updateKpi = (index: number, field: keyof BriefKPI, value: string) => {
    const updated = kpis.map((k, i) => (i === index ? { ...k, [field]: value } : k));
    onChange(updated);
  };

  const hasValidData = kpis.some(
    (k) => k.kpi_name.trim() && k.target_value.trim() && k.unit.trim() && k.measurement_method.trim()
  );

  return (
    <div className="space-y-3">
      {kpis.map((kpi, index) => (
        <div key={kpi.id} className="rounded-md border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">KPI {index + 1}</span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={() => removeKpi(index)}
              disabled={kpis.length <= 1 || disabled}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">指標名稱 *</span>
              <Input
                value={kpi.kpi_name}
                onChange={(e) => updateKpi(index, "kpi_name", e.target.value)}
                placeholder="例：傳動效率"
                maxLength={80}
                disabled={disabled}
              />
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">目標值 *</span>
              <Input
                value={kpi.target_value}
                onChange={(e) => updateKpi(index, "target_value", e.target.value)}
                placeholder="例：≥ 85"
                maxLength={50}
                disabled={disabled}
              />
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">單位 *</span>
              <Input
                value={kpi.unit}
                onChange={(e) => updateKpi(index, "unit", e.target.value)}
                placeholder="例：%"
                maxLength={20}
                disabled={disabled}
              />
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">衡量方式 *</span>
              <Input
                value={kpi.measurement_method}
                onChange={(e) => updateKpi(index, "measurement_method", e.target.value)}
                placeholder="例：台架測試"
                maxLength={200}
                disabled={disabled}
              />
            </div>
          </div>
        </div>
      ))}

      {!hasValidData && kpis.length > 0 && (
        <p className="text-xs text-destructive px-1">至少需要 1 項 KPI。</p>
      )}

      {kpis.length < MAX_KPIS && (
        <Button type="button" variant="ghost" size="sm" onClick={addKpi} disabled={disabled}>
          <Plus className="h-4 w-4 mr-1" />
          新增 KPI
        </Button>
      )}
    </div>
  );
}
