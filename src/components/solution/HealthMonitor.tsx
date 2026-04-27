import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, ArrowLeft as ArrowLeftIcon } from "lucide-react";
import { HealthStatus } from "@/types/solution";

interface HealthMonitorProps {
  nodeCount: number;
  hasCircular: boolean;
}

const getStatus = (nodeCount: number, hasCircular: boolean): HealthStatus => {
  if (hasCircular) return "circular";
  if (nodeCount > 5) return "critical";
  if (nodeCount >= 4) return "warning";
  return "healthy";
};

const statusConfig: Record<HealthStatus, { color: string; bg: string; label: string; desc: string }> = {
  healthy: { color: "bg-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950", label: "健康", desc: "節點數量正常，可繼續探索。" },
  warning: { color: "bg-amber-500", bg: "bg-amber-50 dark:bg-amber-950", label: "警告", desc: "矛盾節點較多，建議檢視是否可合併或簡化。" },
  critical: { color: "bg-red-500", bg: "bg-red-50 dark:bg-red-950", label: "危險", desc: "節點數超標，建議返回 Step 1 重新定義任務。" },
  circular: { color: "bg-red-500", bg: "bg-red-50 dark:bg-red-950", label: "循環矛盾", desc: "偵測到循環矛盾依賴，需進行架構重構。" },
};

const HealthMonitor = ({ nodeCount, hasCircular }: HealthMonitorProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const status = getStatus(nodeCount, hasCircular);
  const cfg = statusConfig[status];

  return (
    <Card className={`rounded-lg ${cfg.bg}`} style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          Architecture Health Monitor
          <div className={`w-3 h-3 rounded-full ${cfg.color} animate-pulse`} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-sm font-mono">{nodeCount} 節點</Badge>
          <Badge className={`text-xs ${cfg.color} text-white`}>{cfg.label}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{cfg.desc}</p>

        {(status === "critical" || status === "circular") && (
          <div className="flex items-center gap-2 pt-1">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <Button
              variant="destructive"
              size="sm"
              onClick={() => navigate(`/projects/${id}/task-definition`)}
            >
              <ArrowLeftIcon className="mr-1.5 h-3.5 w-3.5" />
              返回任務定義
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default HealthMonitor;
