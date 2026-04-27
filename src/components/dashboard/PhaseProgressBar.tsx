import type { PhaseProgress, StepStatus } from "@/types/project";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface PhaseProgressBarProps {
  progress: PhaseProgress;
}

interface StepDef {
  key: keyof PhaseProgress;
  label: string;
  phase: 1 | 2 | 3;
}

const STEPS: StepDef[] = [
  { key: "D1", label: "Brief", phase: 1 },
  { key: "D2", label: "Explore", phase: 1 },
  { key: "PG-D", label: "矛盾確認", phase: 1 },
  { key: "X1", label: "Track", phase: 2 },
  { key: "X2", label: "Create", phase: 2 },
  { key: "PG-X", label: "Pre-CAD", phase: 2 },
  { key: "V1", label: "Review", phase: 3 },
  { key: "V2", label: "Decide", phase: 3 },
  { key: "PG-V", label: "Feynman", phase: 3 },
];

const PHASE_LABELS: Record<number, string> = {
  1: "Phase 1: Define",
  2: "Phase 2: Diverge",
  3: "Phase 3: Converge",
};

const phaseLineColor: Record<number, string> = {
  1: "bg-phase-1",
  2: "bg-phase-2",
  3: "bg-phase-3",
};

const phaseTextColor: Record<number, string> = {
  1: "text-phase-1",
  2: "text-phase-2",
  3: "text-phase-3",
};

const statusLabels: Record<StepStatus, string> = {
  passed: "已通過",
  in_progress: "進行中",
  not_started: "未開始",
};

export function PhaseProgressBar({ progress }: PhaseProgressBarProps) {
  // Group steps by phase
  const phases = [1, 2, 3] as const;

  return (
    <div className="space-y-2">
      {/* Phase labels */}
      <div className="flex gap-0">
        {phases.map((p) => {
          const stepsInPhase = STEPS.filter((s) => s.phase === p);
          return (
            <div key={p} className="flex-1 text-center">
              <span className={cn("text-xs font-semibold", phaseTextColor[p])}>
                {PHASE_LABELS[p]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress line with step dots */}
      <div className="flex items-center gap-0">
        {STEPS.map((step, i) => {
          const status = progress[step.key];
          const prevStatus = i > 0 ? progress[STEPS[i - 1].key] : "not_started";
          const prevPhase = i > 0 ? STEPS[i - 1].phase : step.phase;
          const showPhaseDivider = i > 0 && step.phase !== prevPhase;
          // Line is colored if either end is passed or in_progress
          const lineActive = prevStatus === "passed" || status === "passed" || status === "in_progress";

          return (
            <div key={step.key} className="flex items-center flex-1">
              {/* Connector line (not for first) */}
              {i > 0 && (
                <div className={cn(
                  "flex-1 h-0.5",
                  showPhaseDivider && !lineActive ? "bg-border" :
                  !lineActive ? "bg-border" : phaseLineColor[step.phase]
                )} />
              )}

              {/* Step dot */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex flex-col items-center gap-1">
                    <div className={cn(
                      "h-5 w-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold transition-all",
                      status === "passed" && cn(phaseLineColor[step.phase], "border-transparent text-background"),
                      status === "in_progress" && cn("border-current animate-pulse bg-background", phaseTextColor[step.phase]),
                      status === "not_started" && "border-muted-foreground/30 bg-background text-muted-foreground/50",
                    )}>
                      {status === "passed" ? "·" : ""}
                    </div>
                    <span className={cn(
                      "text-[10px] leading-none",
                      status === "not_started" ? "text-muted-foreground/50" : phaseTextColor[step.phase]
                    )}>
                      {step.label}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Step {step.label}: {statusLabels[status]}</p>
                </TooltipContent>
              </Tooltip>
            </div>
          );
        })}
      </div>
    </div>
  );
}
