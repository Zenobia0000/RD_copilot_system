import { cn } from "@/lib/utils";
import { Check, Zap, Target, LayoutGrid } from "lucide-react";
import type { AccordionStepStatus } from "@/types/create";

export type AnalysisTrack = "reverse" | "forward" | null;

interface CreateStepperProps {
  steps: { label: string; shortLabel: string }[];
  statuses: AccordionStepStatus[];
  currentStep: number;
  activeTrack: AnalysisTrack;
  onStepClick: (step: number, track: AnalysisTrack) => void;
}

function EvalChip({
  label, status, isCurrent, onClick,
}: {
  label: string; status: AccordionStepStatus;
  isCurrent: boolean; onClick: () => void;
}) {
  const isComplete = status === "complete";
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer",
        "hover:bg-accent/50",
        isCurrent && "bg-primary text-primary-foreground",
        isComplete && !isCurrent && "bg-primary/10 text-primary",
        !isCurrent && !isComplete && "text-muted-foreground bg-muted",
      )}
    >
      {isComplete && <Check className="h-3 w-3" />}
      {label}
    </button>
  );
}

export function CreateStepper({ steps, statuses, currentStep, activeTrack, onStepClick }: CreateStepperProps) {
  const HUB = 4;
  const EVAL = [5, 6];

  const isReverseActive = activeTrack === "reverse";
  const isForwardActive = activeTrack === "forward";
  const isHubActive = currentStep === HUB && activeTrack === null;

  const reverseComplete = statuses[0] === "complete";
  // Forward is "complete" when all 3 sub-steps are done
  const forwardComplete = statuses[1] === "complete" && statuses[2] === "complete" && statuses[3] === "complete";
  const forwardHasProgress = statuses[1] !== "not_started";

  return (
    <div className="space-y-3">

      {/* ── Layer 1: Dual Analysis — two symmetric cards ── */}
      <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">雙軌分析</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

        {/* Reverse: Anti-Anchor (single node, creative) */}
        <button
          onClick={() => onStepClick(0, "reverse")}
          className={cn(
            "text-left rounded-lg border-2 p-4 transition-all cursor-pointer",
            "hover:border-amber-300 hover:bg-amber-50/30",
            isReverseActive && "border-amber-400 shadow-sm bg-amber-50/40",
            !isReverseActive && "border-muted",
          )}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <Zap className={cn("h-4 w-4", isReverseActive ? "text-amber-500" : "text-muted-foreground")} />
            <span className="text-xs font-semibold">反向探索</span>
            {reverseComplete && <Check className="h-3.5 w-3.5 text-green-500 ml-auto" />}
          </div>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            Anti-Anchor Sprint — 從約束出發，AI 產出非典型架構概念，每條自帶 Validation Passport
          </p>
        </button>

        {/* Forward: TRIZ E2E (single node, deductive) */}
        <button
          onClick={() => onStepClick(1, "forward")}
          className={cn(
            "text-left rounded-lg border-2 p-4 transition-all cursor-pointer",
            "hover:border-blue-300 hover:bg-blue-50/30",
            isForwardActive && "border-blue-400 shadow-sm bg-blue-50/40",
            !isForwardActive && "border-muted",
          )}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <Target className={cn("h-4 w-4", isForwardActive ? "text-blue-500" : "text-muted-foreground")} />
            <span className="text-xs font-semibold">正向分析</span>
            {forwardComplete && <Check className="h-3.5 w-3.5 text-green-500 ml-auto" />}
            {forwardHasProgress && !forwardComplete && (
              <span className="text-[9px] text-muted-foreground ml-auto">分析中</span>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            TRIZ 解矛盾 → 概念架構包 → 工程規格草案
          </p>
        </button>
      </div>

      {/* ── Layer 2: Decision Hub ── */}
      <div className="flex items-center justify-center py-1">
        <div className="h-px w-8 bg-border" />
        <span className="text-[10px] text-muted-foreground mx-2">▼ 候選池匯流 ▼</span>
        <div className="h-px w-8 bg-border" />
      </div>

      <button
        onClick={() => onStepClick(HUB, null)}
        className={cn(
          "w-full text-left rounded-lg border-2 p-3 transition-all cursor-pointer",
          "hover:border-violet-300 hover:bg-violet-50/30",
          isHubActive && "border-violet-500 bg-violet-50/50 shadow-sm",
          !isHubActive && "border-muted",
        )}
      >
        <div className="flex items-center gap-2">
          <LayoutGrid className={cn("h-4 w-4", isHubActive ? "text-violet-600" : "text-muted-foreground")} />
          <span className="text-xs font-semibold">候選方案決策中心</span>
          {statuses[HUB] === "complete" && <Check className="h-3.5 w-3.5 text-green-500 ml-auto" />}
        </div>
        <p className="text-[10px] text-muted-foreground mt-1">
          攤平所有方案，橫向比較來源、機制、假設、驗證需求與信心等級
        </p>
      </button>

      {/* ── Layer 3: Unified Evaluation ── */}
      <div className="flex items-center justify-center gap-2">
        {EVAL.map((stepIdx) => (
          <EvalChip
            key={stepIdx}
            label={steps[stepIdx].shortLabel}
            status={statuses[stepIdx]}
            isCurrent={currentStep === stepIdx && activeTrack === null}
            onClick={() => onStepClick(stepIdx, null)}
          />
        ))}
      </div>
    </div>
  );
}
