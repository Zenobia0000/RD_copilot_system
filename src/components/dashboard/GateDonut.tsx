import { cn } from "@/lib/utils";

// SVG layout constants
const DONUT_RADIUS = 36;
const DONUT_VIEWBOX_SIZE = 80;
const DONUT_CENTER = DONUT_VIEWBOX_SIZE / 2; // 40
const DONUT_STROKE_WIDTH = 6;

interface GateDonutProps {
  passed: number;
  total: number;
}

export function GateDonut({ passed, total }: GateDonutProps) {
  const pct = total > 0 ? (passed / total) * 100 : 0;
  const circumference = 2 * Math.PI * DONUT_RADIUS;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex items-center gap-3">
      <div className="relative h-16 w-16 shrink-0">
        <svg viewBox={`0 0 ${DONUT_VIEWBOX_SIZE} ${DONUT_VIEWBOX_SIZE}`} className="h-full w-full -rotate-90">
          <circle cx={DONUT_CENTER} cy={DONUT_CENTER} r={DONUT_RADIUS} fill="none" stroke="hsl(var(--muted))" strokeWidth={DONUT_STROKE_WIDTH} />
          <circle
            cx={DONUT_CENTER} cy={DONUT_CENTER} r={DONUT_RADIUS} fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={DONUT_STROKE_WIDTH}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold">{passed}/{total}</span>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold">Gates Passed</div>
        <div className="text-xs text-muted-foreground">{Math.round(pct)}% 完成</div>
      </div>
    </div>
  );
}
