import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { CheckCircle, XCircle, ArrowRight } from "lucide-react";
import type { TrackGateItem } from "@/types/track";

interface TrackGateProps {
  items: TrackGateItem[];
  onNavigateNext: () => void;
}

export function TrackGate({ items, onNavigateNext }: TrackGateProps) {
  const allPassed = items.every((i) => i.passed);

  return (
    <div className="space-y-4 mt-6">
      <Separator />

      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-6 w-1 rounded-full bg-amber-500" />
          <h3 className="text-sm font-semibold">Gate X1 — 假設追蹤完整性檢查</h3>
          <Badge
            className={`text-xs text-white ${allPassed ? 'bg-green-600' : 'bg-red-600'}`}
          >
            {allPassed ? 'Gate X1 Passed' : 'Gate X1 未通過'}
          </Badge>
        </div>

        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.passed ? (
                <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 text-destructive shrink-0" />
              )}
              <span className={item.passed ? '' : 'text-muted-foreground'}>
                {item.label}
              </span>
              <span className="text-xs text-muted-foreground ml-auto">
                {item.current}/{item.target}
              </span>
            </div>
          ))}
        </div>

        {allPassed ? (
          <Button
            onClick={onNavigateNext}
            className="w-full sm:w-auto bg-amber-500 hover:bg-amber-600 text-white"
          >
            前往 Create →
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block">
                <Button disabled className="w-full sm:w-auto opacity-50">
                  前往 Create →
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>請完成上方所有檢查項目</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
