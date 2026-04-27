import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import type { ProjectHistoryItem } from "@/types/project";
import { Calendar, User, ArrowRight, Flag, CheckCircle, Search, ClipboardList } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProjectTimelineProps {
  projectId: string;
  history: ProjectHistoryItem[];
}

const typeConfig: Record<ProjectHistoryItem["type"], { icon: React.ElementType; color: string }> = {
  decision: { icon: Flag, color: "text-accent" },
  milestone: { icon: CheckCircle, color: "text-primary" },
  review: { icon: Search, color: "text-muted-foreground" },
  task: { icon: ClipboardList, color: "text-muted-foreground" },
};

export function ProjectTimeline({ projectId, history }: ProjectTimelineProps) {
  const navigate = useNavigate();

  if (history.length === 0) {
    return (
      <div className="text-center py-10 text-muted-foreground text-sm">
        尚無歷程記錄。
      </div>
    );
  }

  return (
    <div className="relative space-y-0">
      {/* Vertical line */}
      <div className="absolute left-4 top-2 bottom-2 w-px bg-border" />

      {history.map((item, index) => {
        const config = typeConfig[item.type];
        const Icon = config.icon;
        const date = new Date(item.date).toLocaleDateString("zh-TW", {
          month: "2-digit",
          day: "2-digit",
        });

        return (
          <div key={item.id} className="relative flex gap-4 pb-6 last:pb-0">
            {/* Dot */}
            <div className={cn("relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-card", config.color)}>
              <Icon className="h-4 w-4" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-semibold leading-snug">{item.title}</h4>
                <span className="text-xs text-muted-foreground shrink-0">{date}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{item.summary}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <User className="h-3 w-3" />
                  {item.author}
                </span>
                {item.relatedPage && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={() => navigate(`/projects/${projectId}/${item.relatedPage}`)}
                  >
                    查看詳情
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
