import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { PreCadScore } from "@/types/project";
import { ShieldCheck } from "lucide-react";

interface PreCadScoreGaugeProps {
  data: PreCadScore;
}

function getScoreColor(score: number) {
  if (score >= 80) return { ring: "hsl(var(--success))", text: "text-success", label: "良好" };
  if (score >= 50) return { ring: "hsl(var(--warning))", text: "text-warning", label: "注意" };
  return { ring: "hsl(var(--destructive))", text: "text-destructive", label: "危險" };
}

export function PreCadScoreGauge({ data }: PreCadScoreGaugeProps) {
  const { score, fatalResolved, fatalTotal, majorResolved, majorTotal } = data;
  const config = getScoreColor(score);
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <ShieldCheck className="h-4 w-4" />
          Pre-CAD Confidence Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          {/* Gauge */}
          <div className="relative h-24 w-24 shrink-0">
            <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
              <circle cx="50" cy="50" r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
              <circle
                cx="50" cy="50" r={radius} fill="none"
                stroke={config.ring}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                className="transition-all duration-700"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={cn("text-2xl font-bold", config.text)}>{score}%</span>
              <span className={cn("text-[10px] font-medium", config.text)}>{config.label}</span>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-destructive" />
              <span className="text-muted-foreground">Fatal 矛盾：</span>
              <span className="font-semibold">{fatalResolved}/{fatalTotal} 已解決</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-warning" />
              <span className="text-muted-foreground">Major 矛盾：</span>
              <span className="font-semibold">{majorResolved}/{majorTotal} 已解決</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Fatal + Major 需 100% 解決方可通過 Gate P
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
