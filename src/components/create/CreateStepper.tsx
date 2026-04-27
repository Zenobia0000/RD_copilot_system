import { cn } from "@/lib/utils";
import { Check, Target, LayoutGrid } from "lucide-react";
import type { AccordionStepStatus } from "@/types/create";

interface CreateStepperProps {
  steps: { label: string; shortLabel: string }[];
  statuses: AccordionStepStatus[];
  currentStep: number;
  onStepClick: (step: number) => void;
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

export function CreateStepper({ steps, statuses, currentStep, onStepClick }: CreateStepperProps) {
  const HUB = 2;
  const EVAL = [3, 4];

  const isAnalysisActive = currentStep <= 1;
  const isHubActive = currentStep === HUB;
  const analysisComplete = statuses[0] === "complete" && statuses[1] === "complete";
  const analysisHasProgress = statuses[0] !== "not_started";

  return (
    <div className="space-y-3">

      {/* ── Layer 1: TRIZ Analysis (single entry — de-anchoring built into L1) ── */}
      <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">TRIZ 分析</p>
      <button
        onClick={() => onStepClick(0)}
        className={cn(
          "w-full text-left rounded-lg border-2 p-4 transition-all cursor-pointer",
          "hover:border-blue-300 hover:bg-blue-50/30",
          isAnalysisActive && "border-blue-400 shadow-sm bg-blue-50/40",
          !isAnalysisActive && "border-muted",
        )}
      >
        <div className="flex items-center gap-2 mb-1.5">
          <Target className={cn("h-4 w-4", isAnalysisActive ? "text-blue-500" : "text-muted-foreground")} />
          <span className="text-xs font-semibold">TRIZ 解矛盾 + 子系統定義</span>
          {analysisComplete && <Check className="h-3.5 w-3.5 text-green-500 ml-auto" />}
          {analysisHasProgress && !analysisComplete && (
            <span className="text-[9px] text-muted-foreground ml-auto">分析中</span>
          )}
        </div>
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          從矛盾出發，L1 內建跨域去錨定 → L2 根因分離 → L3 結構旁路，再定義子系統與介面契約
        </p>
      </button>

      {/* ── Layer 2: Decision Hub ── */}
      <div className="flex items-center justify-center py-1">
        <div className="h-px w-8 bg-border" />
        <span className="text-[10px] text-muted-foreground mx-2">▼ 候選池匯流 ▼</span>
        <div className="h-px w-8 bg-border" />
      </div>

      <button
        onClick={() => onStepClick(HUB)}
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
            isCurrent={currentStep === stepIdx}
            onClick={() => onStepClick(stepIdx)}
          />
        ))}
      </div>
    </div>
  );
}
