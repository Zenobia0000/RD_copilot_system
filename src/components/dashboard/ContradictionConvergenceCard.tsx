import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ContradictionConvergence } from "@/types/project";
import { GitBranch, AlertTriangle } from "lucide-react";

interface ContradictionConvergenceCardProps {
  data: ContradictionConvergence;
}

export function ContradictionConvergenceCard({ data }: ContradictionConvergenceCardProps) {
  const { totalNodes, fatalCount, majorCount, minorCount, hasCircularDependency, healthWarning } = data;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            矛盾收斂狀態
          </CardTitle>
          {healthWarning && (
            <Badge variant="destructive" className="text-xs">
              <AlertTriangle className="h-3 w-3 mr-1" />
              架構警告
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Node count */}
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{totalNodes}</span>
            <span className="text-sm text-muted-foreground">個矛盾節點</span>
          </div>

          {/* Severity bars */}
          <div className="space-y-2">
            <SeverityRow label="Fatal" count={fatalCount} total={totalNodes} className="bg-destructive" />
            <SeverityRow label="Major" count={majorCount} total={totalNodes} className="bg-warning" />
            <SeverityRow label="Minor" count={minorCount} total={totalNodes} className="bg-muted-foreground" />
          </div>

          {/* Warnings */}
          <div className="space-y-1 text-xs text-muted-foreground">
            {totalNodes > 5 && (
              <p className="flex items-center gap-1 text-warning">
                <AlertTriangle className="h-3 w-3" />
                節點數超過 5，建議進行架構簡化
              </p>
            )}
            {hasCircularDependency && (
              <p className="flex items-center gap-1 text-destructive">
                <AlertTriangle className="h-3 w-3" />
                偵測到循環依賴，請優先處理
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SeverityRow({ label, count, total, className }: { label: string; count: number; total: number; className: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs w-10 text-muted-foreground">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
        <div className={cn(className, "h-full rounded-full transition-all")} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium w-4 text-right">{count}</span>
    </div>
  );
}

