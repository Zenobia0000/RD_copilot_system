import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { CheckCircle, XCircle, ArrowRight, Loader2 } from "lucide-react";
import type { GateCheckItem } from "@/types/taskDefinition";

interface GateChecklistProps {
  items: GateCheckItem[];
  onNavigateNext: () => void;
  isSubmitting?: boolean;
}

export function GateChecklist({ items, onNavigateNext, isSubmitting = false }: GateChecklistProps) {
  const allPassed = items.every((i) => i.passed);

  return (
    <div className="space-y-4">
      <Separator />
      <div className="rounded-lg border p-4 space-y-4">
        {/* Phase 1 blue top band */}
        <div className="flex items-center gap-3">
          <div className="h-6 w-1 rounded-full bg-phase-1" />
          <h3 className="text-sm font-semibold">Gate D1 — 任務定義完整性檢查</h3>
          <Badge
            variant={allPassed ? "default" : "destructive"}
            className="ml-auto text-xs"
          >
            {allPassed ? "Gate D1 Passed" : "Gate D1 未通過"}
          </Badge>
        </div>

        {/* Checklist */}
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.passed ? (
                <CheckCircle className="h-4 w-4 text-[hsl(var(--success))] shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 text-destructive shrink-0" />
              )}
              <span className={item.passed ? "" : "text-muted-foreground"}>
                {item.label}
              </span>
            </div>
          ))}
        </div>

        {/* Navigate button */}
        {allPassed ? (
          <Button onClick={onNavigateNext} disabled={isSubmitting} className="w-full sm:w-auto">
            {isSubmitting ? (
              <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> 儲存中...</>
            ) : (
              <>通過 → 進入 Explore <ArrowRight className="h-4 w-4 ml-1" /></>
            )}
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block">
                <Button disabled className="w-full sm:w-auto">
                  通過 → 進入 Explore
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>請完成上方所有必填項目</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
