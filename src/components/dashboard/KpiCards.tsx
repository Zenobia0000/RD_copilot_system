import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CriticalKPI } from "@/types/project";
import { TrendingUp, AlertTriangle, XCircle, HelpCircle, ClipboardEdit } from "lucide-react";

interface KpiCardsProps {
  kpis: CriticalKPI[];
  onLogEvidence?: (kpiId: string) => void;
}

const statusConfig: Record<CriticalKPI["status"], { label: string; variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ElementType }> = {
  on_track: { label: "正常", variant: "default", icon: TrendingUp },
  at_risk: { label: "風險中", variant: "secondary", icon: AlertTriangle },
  off_track: { label: "偏離", variant: "destructive", icon: XCircle },
  unknown: { label: "待測試", variant: "outline", icon: HelpCircle },
};

export function KpiCards({ kpis, onLogEvidence }: KpiCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {kpis.map((kpi) => {
        const config = statusConfig[kpi.status];
        const Icon = config.icon;
        return (
          <Card key={kpi.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {kpi.name}
                </CardTitle>
                <Badge variant={config.variant} className="text-xs">
                  <Icon className="h-3 w-3 mr-1" />
                  {config.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpi.current}</div>
              <div className="flex items-center justify-between mt-1">
                <p className="text-xs text-muted-foreground">目標：{kpi.target}</p>
                {onLogEvidence && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                    onClick={() => onLogEvidence(kpi.id)}
                  >
                    <ClipboardEdit className="h-3 w-3 mr-1" />
                    登錄證據
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
