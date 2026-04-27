import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { LinkedContradiction, SocraticFeedback, ConvergenceImpact } from "@/types/assumption";
import { Link2, AlertTriangle, MessageSquare, ExternalLink, Sparkles } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

interface ContradictionTraceabilityProps {
  assumptionId: string | null;
  assumptionCode?: string;
  isRefuted?: boolean;
  linkedContradictions: LinkedContradiction[];
  socraticFeedback: SocraticFeedback[];
  convergenceImpact?: ConvergenceImpact;
}

const severityConfig: Record<LinkedContradiction["severity"], { label: string; variant: "default" | "secondary" | "destructive" }> = {
  fatal: { label: "Fatal", variant: "destructive" },
  major: { label: "Major", variant: "default" },
  minor: { label: "Minor", variant: "secondary" },
};

export function ContradictionTraceability({
  assumptionId,
  assumptionCode,
  isRefuted,
  linkedContradictions,
  socraticFeedback,
  convergenceImpact,
}: ContradictionTraceabilityProps) {
  const navigate = useNavigate();
  const { id } = useParams();

  if (!assumptionId) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full min-h-[200px] text-sm text-muted-foreground">
          選擇一個假設以查看矛盾追溯
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-full", isRefuted && "border-destructive/50")}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Link2 className="h-4 w-4" />
          矛盾追溯 — {assumptionCode}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Convergence Impact Alert */}
        {isRefuted && convergenceImpact && (
          <div className="rounded-md bg-destructive/10 border border-destructive/30 p-3 space-y-2">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-destructive">收斂圖受影響</p>
                <p className="text-xs text-muted-foreground mt-0.5">{convergenceImpact.message}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="text-xs border-destructive/50 text-destructive"
              onClick={() => navigate(`/projects/${id}/contradiction-identification`)}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              跳轉至矛盾收斂圖
            </Button>
          </div>
        )}

        {/* Linked Contradictions */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">關聯矛盾</h4>
          {linkedContradictions.length === 0 ? (
            <p className="text-xs text-muted-foreground">無關聯矛盾</p>
          ) : (
            <div className="space-y-1.5">
              {linkedContradictions.map((c) => {
                const config = severityConfig[c.severity];
                return (
                  <div
                    key={c.id}
                    className="flex items-center gap-2 rounded-md border p-2 text-xs cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => navigate(`/projects/${id}/contradiction-identification`)}
                  >
                    <Badge variant={config.variant} className="text-[9px] shrink-0">{config.label}</Badge>
                    <span className="flex-1 truncate">{c.description}</span>
                    {c.resolved && <Badge variant="outline" className="text-[9px]">已解決</Badge>}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <Separator />

        {/* Socratic Feedback */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            蘇格拉底回饋
          </h4>
          {socraticFeedback.length === 0 ? (
            <p className="text-xs text-muted-foreground">尚無 AI 回饋</p>
          ) : (
            <div className="space-y-2">
              {socraticFeedback.map((fb) => (
                <div key={fb.id} className="rounded-md bg-muted/40 p-2.5 text-xs space-y-1">
                  <Badge variant="outline" className="text-[9px]">
                    {fb.type === "causal_inquiry" ? "因果追問" : "假設挑戰"}
                  </Badge>
                  <p className="leading-relaxed">{fb.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
