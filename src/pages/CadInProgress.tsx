import { useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, ArrowRight, PenTool, CheckCircle, Clock, AlertTriangle, Loader2 } from "lucide-react";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { useAlternatives, useUpdateAlternative } from "@/hooks/api";

type CadStatus = "not_started" | "in_progress" | "completed";

interface CadItem {
  altId: string;
  altName: string;
  cadStatus: CadStatus;
  cadNote: string;
}

const CAD_STATUS_CONFIG: Record<CadStatus, { label: string; icon: typeof CheckCircle; variant: "default" | "secondary" | "outline" }> = {
  not_started: { label: "未開始", icon: Clock, variant: "outline" },
  in_progress: { label: "繪製中", icon: PenTool, variant: "secondary" },
  completed: { label: "已完成", icon: CheckCircle, variant: "default" },
};

export default function CadInProgress() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // --- API hooks ---
  const { data: alternatives = [], isLoading } = useAlternatives(id);
  const updateAlternative = useUpdateAlternative();

  // Filter: alternatives that passed MUST (no "fail" in mustScores and at least one non-null)
  // Then map to CadItem using the raw alternative data
  const cadItems: CadItem[] = useMemo(() => {
    const passed = alternatives.filter(
      (a) => !Object.values(a.mustScores).includes("fail") && Object.values(a.mustScores).some((v) => v !== null)
    );
    return passed.map((a, i) => {
      // The Alternative type from useCreate doesn't expose cadStatus,
      // but we can access it as extended property from the raw data
      const rawAny = a as any;
      const cadStatus = (rawAny.cadStatus ?? rawAny.cad_status ?? "not_started") as CadStatus;
      return {
        altId: a.id,
        altName: a.name || `(未命名方案 ${i + 1})`,
        cadStatus,
        cadNote: "",
      };
    });
  }, [alternatives]);

  const completedCount = cadItems.filter((i) => i.cadStatus === "completed").length;
  const progress = cadItems.length > 0 ? Math.round((completedCount / cadItems.length) * 100) : 0;
  const canProceed = completedCount >= 1;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">載入 CAD 階段資料中...</span>
      </div>
    );
  }

  return (
    <div className="page-shell-narrow">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${id}`)} className="text-muted-foreground -ml-2">
          <ArrowLeft className="h-4 w-4 mr-1" /> Dashboard
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          CAD 繪製階段
          <HelpTooltip text="通過 Pre-CAD 審查的方案在此階段由 RD 進行 CAD 建模。完成後進入設計審查。" className="ml-2 align-middle" />
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Phase 2.5 · Pre-CAD → CAD → Design Review</p>
      </div>

      <Card className="bg-muted/30">
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">CAD 完成進度</span>
            <span className="text-sm text-muted-foreground">{completedCount}/{cadItems.length} 方案</span>
          </div>
          <Progress value={progress} className="h-2" />
        </CardContent>
      </Card>

      {cadItems.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-3">
            <AlertTriangle className="h-8 w-8 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground font-medium">沒有通過 Pre-CAD 審查的方案</p>
            <p className="text-sm text-muted-foreground">請先在方案創造頁面完成 MUST 快篩與 Pre-CAD 審查</p>
            <Button variant="secondary" onClick={() => navigate(`/projects/${id}/create`)}>前往方案創造</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {cadItems.map((item) => {
            const config = CAD_STATUS_CONFIG[item.cadStatus];
            const Icon = config.icon;
            return (
              <Card key={item.altId} className={item.cadStatus === "completed" ? "border-l-[3px] border-l-primary" : ""}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold">{item.altName}</h3>
                    <Badge variant={config.variant} className="text-xs gap-1">
                      <Icon className="h-3 w-3" /> {config.label}
                    </Badge>
                  </div>
                  {item.cadNote && (
                    <p className="text-sm text-muted-foreground">{item.cadNote}</p>
                  )}
                  {item.cadStatus === "not_started" && (
                    <p className="text-xs text-muted-foreground italic">等待 RD 開始 CAD 建模</p>
                  )}
                  {/* Status update buttons */}
                  <div className="flex gap-2">
                    {item.cadStatus !== "in_progress" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          updateAlternative.mutate({
                            id: item.altId,
                            cad_status: "in_progress",
                          })
                        }
                      >
                        <PenTool className="h-3 w-3 mr-1" /> 開始繪製
                      </Button>
                    )}
                    {item.cadStatus !== "completed" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          updateAlternative.mutate({
                            id: item.altId,
                            cad_status: "completed",
                          })
                        }
                      >
                        <CheckCircle className="h-3 w-3 mr-1" /> 標記完成
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Card className="border-2 border-primary/30 bg-primary/5">
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center gap-3">
            <PenTool className="h-5 w-5 text-primary shrink-0" />
            <h3 className="text-sm font-semibold">進入設計審查</h3>
            <Badge className={canProceed ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}>
              {canProceed ? "可進入" : "需完成至少 1 方案 CAD"}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            至少 1 個方案完成 CAD 繪製後，即可進入設計審查階段（證據矩陣、風險登錄、最小實驗）。
          </p>
          {canProceed ? (
            <Button onClick={() => navigate(`/projects/${id}/review`)}>
              進入 Design Review <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          ) : (
            <Button disabled className="opacity-50">
              進入 Design Review <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
