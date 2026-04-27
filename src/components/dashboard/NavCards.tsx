import { useNavigate, useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  ClipboardList, Compass, ListChecks, Wand2, Search, Gavel, Lock,
} from "lucide-react";
import type { NavCardDef } from "@/types/project";

const iconMap: Record<string, React.ElementType> = {
  ClipboardList, Compass, ListChecks, Wand2, Search, Gavel,
};

const phaseTopColor: Record<string, string> = {
  "Phase 1": "bg-phase-1",
  "Phase 2": "bg-phase-2",
  "Phase 3": "bg-phase-3",
};

interface NavCardsProps {
  cards: NavCardDef[];
}

export function NavCards({ cards }: NavCardsProps) {
  const navigate = useNavigate();
  const { id } = useParams();

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((card) => {
        const Icon = iconMap[card.icon] || ClipboardList;
        const completionText = `${card.completedSteps}/${card.subSteps} done`;

        const content = (
          <Card
            key={card.id}
            className={cn(
              "overflow-hidden transition-all relative",
              card.locked
                ? "opacity-50 cursor-not-allowed"
                : "cursor-pointer hover:shadow-card-hover hover:-translate-y-0.5"
            )}
            onClick={() => {
              if (!card.locked) navigate(`/projects/${id}/${card.route}`);
            }}
          >
            {/* Phase color band */}
            <div className={cn("h-1", phaseTopColor[card.phase])} />
            <CardContent className="pt-4 pb-3 px-3 text-center space-y-2">
              <div className="relative">
                <Icon className="h-6 w-6 mx-auto text-foreground" />
                {card.locked && (
                  <Lock className="h-3 w-3 absolute -top-1 -right-1 text-muted-foreground" />
                )}
              </div>
              <div>
                <div className="text-sm font-semibold">{card.enName}</div>
                <div className="text-xs text-muted-foreground">{card.zhName}</div>
              </div>
              <Badge variant="outline" className="text-[10px] font-normal">
                {completionText}
              </Badge>
            </CardContent>
          </Card>
        );

        if (card.locked && card.lockReason) {
          return (
            <Tooltip key={card.id}>
              <TooltipTrigger asChild>{content}</TooltipTrigger>
              <TooltipContent><p>{card.lockReason}</p></TooltipContent>
            </Tooltip>
          );
        }

        return <div key={card.id}>{content}</div>;
      })}
    </div>
  );
}
