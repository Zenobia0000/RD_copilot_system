import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Assumption, VerificationStage } from "@/types/assumption";
import { VERIFICATION_STAGE_LABELS, SEVERITY_LABELS } from "@/types/assumption";
import { ArrowRight, Clock, AlertTriangle } from "lucide-react";

interface VerificationKanbanProps {
  assumptions: Assumption[];
  onMoveStage: (id: string, newStage: VerificationStage) => void;
  onSelect: (assumption: Assumption) => void;
}

const COLUMNS: VerificationStage[] = ["unplanned", "planned", "in_progress", "completed", "refuted"];

const columnStyles: Record<VerificationStage, string> = {
  unplanned: "border-t-muted-foreground",
  planned: "border-t-info",
  in_progress: "border-t-warning",
  completed: "border-t-success",
  refuted: "border-t-destructive",
};

const severityColor: Record<Assumption["worstSeverity"], string> = {
  critical: "bg-destructive/10 text-destructive",
  high: "bg-warning/10 text-warning",
  medium: "bg-info/10 text-info",
  low: "bg-muted text-muted-foreground",
};

const nextStage: Record<VerificationStage, VerificationStage | null> = {
  unplanned: "planned",
  planned: "in_progress",
  in_progress: "completed",
  completed: null,
  refuted: null,
};

export function VerificationKanban({ assumptions, onMoveStage, onSelect }: VerificationKanbanProps) {
  // Sort by severity within each column
  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">驗證規劃看板</CardTitle>
        <p className="text-xs text-muted-foreground">依「最壞後果」嚴重度自動排序優先級</p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {COLUMNS.map((stage) => {
            const items = assumptions
              .filter((a) => a.verificationStage === stage)
              .sort((a, b) => severityOrder[a.worstSeverity] - severityOrder[b.worstSeverity]);

            return (
              <div key={stage} className={cn("rounded-lg border border-t-[3px] p-2 min-h-[200px]", columnStyles[stage])}>
                <div className="flex items-center justify-between mb-2 px-1">
                  <span className="text-xs font-semibold">{VERIFICATION_STAGE_LABELS[stage]}</span>
                  <Badge variant="outline" className="text-[10px]">{items.length}</Badge>
                </div>
                <div className="space-y-2">
                  {items.map((asm) => (
                    <div
                      key={asm.id}
                      className="rounded-md border bg-card p-2 text-xs space-y-1.5 cursor-pointer hover:shadow-card-hover transition-shadow"
                      onClick={() => onSelect(asm)}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-mono text-muted-foreground">{asm.code}</span>
                        <Badge variant="outline" className={cn("text-[9px]", severityColor[asm.worstSeverity])}>
                          {SEVERITY_LABELS[asm.worstSeverity]}
                        </Badge>
                      </div>
                      <p className="line-clamp-2 leading-snug">{asm.content}</p>
                      {asm.estimatedDays && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{asm.estimatedDays} 天</span>
                        </div>
                      )}
                      {nextStage[stage] && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-5 px-1.5 text-[10px] w-full justify-center"
                          onClick={(e) => {
                            e.stopPropagation();
                            onMoveStage(asm.id, nextStage[stage]!);
                          }}
                        >
                          移至 {VERIFICATION_STAGE_LABELS[nextStage[stage]!]}
                          <ArrowRight className="h-3 w-3 ml-0.5" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
