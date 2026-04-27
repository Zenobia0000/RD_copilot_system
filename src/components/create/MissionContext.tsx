import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Target, Zap, FlaskConical, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface MissionContextProps {
  problemStatement: string;
  contradictions: { id: string; description: string }[];
  verifiedAssumptions: number;
  totalAssumptions: number;
  highRiskCount: number;
}

export function MissionContext({
  problemStatement,
  contradictions,
  verifiedAssumptions,
  totalAssumptions,
  highRiskCount,
}: MissionContextProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="border-primary/20 bg-primary/[0.03] sticky top-0 z-10 backdrop-blur-sm">
      <CardContent className="p-4">
        {/* Always visible: mission one-liner */}
        <div className="flex items-start gap-3">
          <div className="shrink-0 mt-0.5">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Target className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-muted-foreground tracking-wide uppercase">核心設計使命</p>
            <p className={`text-sm font-medium mt-0.5 leading-relaxed ${!expanded ? "line-clamp-2" : ""}`}>{problemStatement}</p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="shrink-0 p-1.5 rounded-full hover:bg-muted transition-colors text-muted-foreground"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>

        {/* Expandable: details */}
        {expanded && (
          <div className="mt-4 space-y-3">
            <Separator />

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 rounded-lg bg-background">
                <div className="flex items-center justify-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-destructive" />
                  <span className="text-lg font-semibold">{contradictions.length}</span>
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5">待解矛盾</p>
              </div>
              <div className="text-center p-2 rounded-lg bg-background">
                <div className="flex items-center justify-center gap-1.5">
                  <FlaskConical className="h-3.5 w-3.5 text-primary" />
                  <span className="text-lg font-semibold">{verifiedAssumptions}/{totalAssumptions}</span>
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5">已驗證假設</p>
              </div>
              <div className="text-center p-2 rounded-lg bg-background">
                <div className="flex items-center justify-center gap-1.5">
                  <span className="text-lg font-semibold text-destructive">{highRiskCount}</span>
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5">高風險假設</p>
              </div>
            </div>

            {/* Key contradictions */}
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">方案需解決的矛盾</p>
              <div className="space-y-1.5">
                {contradictions.map((c) => (
                  <div key={c.id} className="flex items-start gap-2 text-xs">
                    <Badge variant="outline" className="text-[9px] font-mono shrink-0 mt-0.5">{c.id}</Badge>
                    <span className="text-muted-foreground leading-relaxed">{c.description}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
