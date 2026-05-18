import { memo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Check, Pencil, Trash2, Undo2, Lightbulb } from "lucide-react";
import { trizParameters } from "@/data/trizParameters";
import type { ExploreContradiction } from "@/types/explore";

export function getParamLabel(paramId: number | null | undefined): string {
  if (!paramId) return "—";
  const p = trizParameters.find((t) => t.id === paramId);
  return p ? `#${p.id} ${p.nameZh}` : "—";
}

interface Props {
  contradiction: ExploreContradiction;
  onConfirm: (id: string) => void;
  onStartEdit: (c: ExploreContradiction) => void;
  onRequestDelete: (id: string) => void;
  onRequestRevert: (id: string) => void;
}

function ContradictionDisplayCardImpl({
  contradiction: c,
  onConfirm,
  onStartEdit,
  onRequestDelete,
  onRequestRevert,
}: Props) {
  const isConfirmed = c.status === "confirmed";
  const severity = c.severity ?? "minor";
  const severityColor = severity === "fatal" ? "#DC2626" : severity === "major" ? "#F97316" : "#6B7280";
  const severityLabel = severity === "fatal" ? "致命" : severity === "major" ? "重要" : "輕微";

  return (
    <Card className={`transition-colors ${isConfirmed ? "border-l-[3px] border-l-green-600" : ""}`}>
      <CardContent className="p-4 space-y-3">
        {/* Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge
            className="text-xs text-white"
            style={{ backgroundColor: c.type === "TC" ? "#3B82F6" : c.type === "SF" ? "#10B981" : "#F59E0B" }}
          >
            {c.type}
          </Badge>
          {c.type === "TC" && c.priority != null && (
            <Badge className="text-[10px] text-white bg-indigo-600">#{c.priority}</Badge>
          )}
          <Badge
            className="text-[10px] text-white"
            style={{ backgroundColor: severityColor }}
            title="矛盾嚴重度：fatal/major 會自動觸發 TRIZ L2 深挖；minor 在 quick_mode 下跳過 L2"
          >
            {severityLabel}
          </Badge>
          {c.source === "ai" && !isConfirmed && (
            <Badge variant="secondary" className="text-[10px]">AI</Badge>
          )}
          {isConfirmed && (
            <Badge className="bg-green-600 text-white text-[10px]">已確認</Badge>
          )}
        </div>

        {/* Statement */}
        <p className="text-sm">{c.description}</p>

        {/* Type-specific parameters */}
        {c.type === "TC" ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <div className="bg-muted rounded px-2 py-1 text-xs">
                <span className="text-muted-foreground">改善: </span>
                <span className="font-medium">{getParamLabel(c.improvingParam)}</span>
              </div>
              <span className="text-muted-foreground text-xs self-center">→</span>
              <div className="bg-muted rounded px-2 py-1 text-xs">
                <span className="text-muted-foreground">惡化: </span>
                <span className="font-medium">{getParamLabel(c.worseningParam)}</span>
              </div>
            </div>
            {/* 3-Stage Pipeline: Linked KPIs */}
            {c.linkedKpis && c.linkedKpis.length > 0 && (
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-muted-foreground text-[10px]">🔗 KPIs:</span>
                {c.linkedKpis.map((kpi, i) => (
                  <Badge key={i} variant="outline" className="text-[10px] font-normal">{kpi}</Badge>
                ))}
              </div>
            )}
            {/* 3-Stage Pipeline: Why Selected */}
            {c.whySelected && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-1 text-[11px] text-muted-foreground cursor-help">
                      <Lightbulb className="h-3 w-3 text-amber-500 shrink-0" />
                      <span className="truncate max-w-[300px]">{c.whySelected}</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-sm whitespace-pre-wrap">
                    <p className="text-xs">{c.whySelected}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        ) : c.type === "SF" ? (
          c.sfSubstance1 ? (
            <div className="flex flex-wrap gap-2">
              <div className="bg-muted rounded px-2 py-1 text-xs">
                <span className="text-muted-foreground">S1: </span>
                <span className="font-medium">{c.sfSubstance1}</span>
              </div>
              <span className="text-muted-foreground text-xs self-center">⟶</span>
              <div className="bg-muted rounded px-2 py-1 text-xs">
                <span className="text-muted-foreground">F: </span>
                <span className="font-medium">{c.sfField || "—"}</span>
              </div>
              <span className="text-muted-foreground text-xs self-center">⟶</span>
              <div className="bg-muted rounded px-2 py-1 text-xs">
                <span className="text-muted-foreground">S2: </span>
                <span className="font-medium">{c.sfSubstance2 || "—"}</span>
              </div>
              {c.sfInteraction && (
                <Badge variant="outline" className="text-[10px]">{c.sfInteraction}</Badge>
              )}
              {c.sfCompleteness && (
                <Badge variant="outline" className="text-[10px]">{c.sfCompleteness}</Badge>
              )}
            </div>
          ) : (
            <div className="bg-muted rounded px-2 py-1 text-xs text-muted-foreground">
              Su-Field 模型細節待補充 — 點擊上方「識別 SF」自動填入，或手動編輯 S1/F/S2
            </div>
          )
        ) : c.pcAttributeA && c.pcAttributeNotA ? (
          <div className="flex flex-wrap gap-2">
            <div className="bg-muted rounded px-2 py-1 text-xs">
              <span className="text-muted-foreground">需要: </span>
              <span className="font-medium">{c.pcAttributeA}</span>
            </div>
            <span className="text-muted-foreground text-xs self-center">⟷</span>
            <div className="bg-muted rounded px-2 py-1 text-xs">
              <span className="text-muted-foreground">同時需要: </span>
              <span className="font-medium">{c.pcAttributeNotA}</span>
            </div>
          </div>
        ) : c.pcAttributeA ? (
          <div className="bg-muted rounded p-2 text-xs">
            <span className="text-muted-foreground">物理矛盾: </span>
            <span className="font-medium">{c.pcAttributeA}</span>
          </div>
        ) : (
          <div className="bg-muted rounded px-2 py-1 text-xs text-muted-foreground">
            物理矛盾細節待補充 — 點擊上方「識別 PC」自動填入，或手動編輯
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          {!isConfirmed ? (
            <>
              <Button size="sm" onClick={() => onConfirm(c.id)}>
                <Check className="h-3 w-3 mr-1" /> 確認 *
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onStartEdit(c)}>
                <Pencil className="h-3 w-3 mr-1" /> 編輯
              </Button>
              <Button size="sm" variant="ghost" className="text-destructive" onClick={() => onRequestDelete(c.id)}>
                <Trash2 className="h-3 w-3 mr-1" /> 刪除
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="outline" onClick={() => onRequestRevert(c.id)}>
                <Undo2 className="h-3 w-3 mr-1" /> 撤回確認
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onStartEdit(c)}>
                <Pencil className="h-3 w-3 mr-1" /> 編輯
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export const ContradictionDisplayCard = memo(ContradictionDisplayCardImpl);
