import { Card, CardContent } from "@/components/ui/card";
import type { QuickStats } from "@/types/project";
import { GitBranch, FileQuestion, Lightbulb, ShieldAlert, FlaskConical, FileCheck } from "lucide-react";

interface QuickStatsGridProps {
  stats: QuickStats;
}

const STAT_DEFS: {
  key: keyof QuickStats;
  label: string;
  icon: React.ElementType;
}[] = [
  { key: "contradictions_count", label: "矛盾數", icon: GitBranch },
  { key: "assumptions_count", label: "假設數", icon: FileQuestion },
  { key: "alternatives_count", label: "方案數", icon: Lightbulb },
  { key: "risks_count", label: "風險數", icon: ShieldAlert },
  { key: "experiments_count", label: "實驗數", icon: FlaskConical },
  { key: "evidence_items_count", label: "證據數", icon: FileCheck },
];

function formatNumber(n: number | undefined | null) {
  if (n == null) return "0";
  if (n > 9999) return "9999+";
  return n.toLocaleString();
}

export function QuickStatsGrid({ stats }: QuickStatsGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {STAT_DEFS.map(({ key, label, icon: Icon }) => (
        <Card key={key} className="text-center">
          <CardContent className="pt-4 pb-3 px-3">
            <Icon className="h-5 w-5 mx-auto text-muted-foreground mb-1" />
            <div className="text-2xl font-bold">{formatNumber(stats[key])}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
