import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { CheckCircle, XCircle, AlertTriangle, ArrowRight, Flag } from "lucide-react";
import type { GateCheckItem } from "@/types/explore";

interface ExploreGatesProps {
  gate12Items: GateCheckItem[];
  phaseGate1Items: GateCheckItem[];
  onNavigateNext: () => void;
}

function GateIcon({ item }: { item: GateCheckItem }) {
  if (item.passed) return <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />;
  if (item.current > 0 && item.current < item.target) return <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />;
  return <XCircle className="h-4 w-4 text-destructive shrink-0" />;
}

function GateStatusBadge({ items, label }: { items: GateCheckItem[]; label: string }) {
  const allPassed = items.every((i) => i.passed);
  const somePartial = items.some((i) => i.current > 0 && !i.passed);

  if (allPassed) return <Badge className="bg-green-600 text-white text-xs">{label} Passed</Badge>;
  if (somePartial) return <Badge className="bg-amber-500 text-white text-xs">{label} 待完善</Badge>;
  return <Badge variant="destructive" className="text-xs">{label} 未通過</Badge>;
}

export function ExploreGates({ gate12Items, phaseGate1Items, onNavigateNext }: ExploreGatesProps) {
  const gate12Passed = gate12Items.every((i) => i.passed);
  const phaseGate1Passed = phaseGate1Items.every((i) => i.passed);
  const allPassed = gate12Passed && phaseGate1Passed;

  return (
    <div className="space-y-4 mt-6">
      <Separator />

      {/* Gate D2 */}
      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-6 w-1 rounded-full bg-blue-500" />
          <h3 className="text-sm font-semibold">Gate D2 — 問題空間探索完整性</h3>
          <GateStatusBadge items={gate12Items} label="Gate D2" />
        </div>
        <div className="space-y-2">
          {gate12Items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <GateIcon item={item} />
              <span className={item.passed ? '' : 'text-muted-foreground'}>
                {item.label}
              </span>
              <span className="text-xs text-muted-foreground ml-auto">
                {item.current}/{item.target}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase Gate D - milestone style */}
      <div className="rounded-lg border-2 border-blue-500 bg-blue-50 dark:bg-blue-950/40 p-4 space-y-3">
        <div className="flex items-center gap-3">
          <Flag className="h-5 w-5 text-blue-500 shrink-0" />
          <h3 className="text-sm font-semibold">Phase Gate D — Define 階段完成度檢查</h3>
          <GateStatusBadge items={phaseGate1Items} label="Phase Gate D" />
        </div>
        <div className="space-y-2">
          {phaseGate1Items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <GateIcon item={item} />
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
            進入 Phase 2: Diverge →
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block">
                <Button disabled className="w-full sm:w-auto opacity-50">
                  進入 Phase 2: Diverge →
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>請完成 Phase 1 所有 Gate 條件</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
