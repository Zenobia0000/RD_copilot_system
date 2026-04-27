import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ShieldCheck, AlertTriangle, XCircle, CheckCircle, Loader2, Sparkles } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { cn } from "@/lib/utils";

export interface FeasibilityConflict {
  id: string;
  constraintA: string;
  constraintB: string;
  reason: string;
  suggestion: string;
}

export type FeasibilityStatus = "idle" | "checking" | "pass" | "warning" | "conflict";

interface FeasibilityValidationProps {
  status: FeasibilityStatus;
  conflicts: FeasibilityConflict[];
  stale?: boolean;
  onCheck: () => void;
  onOverride: (reason: string) => void;
}

const statusConfig: Record<Exclude<FeasibilityStatus, "idle" | "checking">, {
  icon: React.ElementType;
  label: string;
  variant: "default" | "secondary" | "destructive";
  color: string;
}> = {
  pass: { icon: CheckCircle, label: "通過", variant: "default", color: "text-success" },
  warning: { icon: AlertTriangle, label: "警告", variant: "secondary", color: "text-warning" },
  conflict: { icon: XCircle, label: "衝突", variant: "destructive", color: "text-destructive" },
};

export function FeasibilityValidation({ status, conflicts, stale = false, onCheck, onOverride }: FeasibilityValidationProps) {
  const [overrideReason, setOverrideReason] = useState("");
  const [showOverride, setShowOverride] = useState(false);

  return (
    <Card className={cn(
      status === "conflict" && "border-destructive/50",
      status === "warning" && "border-warning/50",
      status === "pass" && "border-success/50"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            約束可行性驗證 (Gate 1)
          </CardTitle>
          {status !== "idle" && status !== "checking" && (
            <Badge variant={statusConfig[status].variant}>
              {statusConfig[status].label}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {status === "idle" && (
          <div className="flex items-center gap-3 py-2">
            <ShieldCheck className="h-5 w-5 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">尚未驗證。AI 將檢查約束之間是否存在物理衝突。</p>
            </div>
            <AiButton size="sm" onClick={onCheck}>
              驗證可行性
            </AiButton>
          </div>
        )}

        {status === "checking" && (
          <div className="flex items-center gap-3 py-4 justify-center text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">AI 正在驗證約束組合的物理可行性...</span>
          </div>
        )}

        {status === "pass" && (
          <div className="space-y-2">
            <div className="flex items-center gap-3 py-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <p className="text-sm flex-1">所有約束組合通過物理可行性驗證，可進入下一步。</p>
              <AiButton aiVariant="outline" size="sm" onClick={onCheck} className="shrink-0 text-xs">
                驗證可行性
              </AiButton>
            </div>
            {stale && (
              <div className="flex items-center gap-2 rounded-md border border-warning/50 bg-warning/5 dark:bg-warning/10 px-3 py-2">
                <AlertTriangle className="h-4 w-4 text-warning shrink-0" />
                <p className="text-sm text-warning flex-1">約束或 Mission 已變更，驗證結果可能過期。</p>
                <AiButton size="sm" aiVariant="outline" onClick={onCheck} className="shrink-0 text-xs border-warning/50 text-warning">
                  驗證可行性
                </AiButton>
              </div>
            )}
          </div>
        )}

        {(status === "warning" || status === "conflict") && (
          <div className="space-y-3">
            {/* Stale banner */}
            {stale && (
              <div className="flex items-center gap-2 rounded-md border border-warning/50 bg-warning/5 dark:bg-warning/10 px-3 py-2">
                <AlertTriangle className="h-4 w-4 text-warning shrink-0" />
                <p className="text-sm text-warning flex-1">約束或 Mission 已變更，驗證結果可能過期。</p>
                <AiButton size="sm" aiVariant="outline" onClick={onCheck} className="shrink-0 text-xs">
                  驗證可行性
                </AiButton>
              </div>
            )}

            {conflicts.map((c) => (
              <div key={c.id} className="rounded-md border p-3 space-y-2">
                <div className="flex items-start gap-2">
                  <AlertTriangle className={cn("h-4 w-4 mt-0.5 shrink-0", status === "conflict" ? "text-destructive" : "text-warning")} />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      <span className="text-muted-foreground">約束衝突：</span>
                      {c.constraintA} ↔ {c.constraintB}
                    </p>
                    <p className="text-sm text-muted-foreground">{c.reason}</p>
                    <div className="flex items-start gap-1.5 mt-1">
                      <Sparkles className="h-3.5 w-3.5 text-accent mt-0.5 shrink-0" />
                      <p className="text-sm text-accent">{c.suggestion}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Re-check button */}
            <AiButton aiVariant="outline" size="sm" onClick={onCheck}>
              驗證可行性
            </AiButton>

            {status === "conflict" && !showOverride && (
              <Button variant="outline" size="sm" onClick={() => setShowOverride(true)} className="text-warning border-warning/50">
                <AlertTriangle className="h-3 w-3 mr-1" />
                我了解風險，選擇覆寫
              </Button>
            )}

            {showOverride && (
              <div className="space-y-2 rounded-md border border-warning/50 p-3">
                <p className="text-sm font-medium text-warning">覆寫確認</p>
                <Textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="請填寫覆寫原因，說明為何接受此風險..."
                  rows={2}
                  className="text-sm"
                />
                <div className="flex gap-2">
                  <Button size="sm" variant="destructive" disabled={overrideReason.trim().length < 5} onClick={() => onOverride(overrideReason)}>
                    確認覆寫
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowOverride(false)}>取消</Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
