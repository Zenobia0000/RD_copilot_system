import { useNavigate, useParams } from "react-router-dom";
import { cn } from "@/lib/utils";
import type { ProjectStage } from "@/types/project";
import {
  ClipboardList, FileQuestion, GitBranch, Lightbulb,
  FileCheck, Search, FileSignature, CheckCircle, Circle, Loader2,
} from "lucide-react";

interface StageNavigationProps {
  stages: ProjectStage[];
}

const iconMap: Record<string, React.ElementType> = {
  ClipboardList, FileQuestion, GitBranch, Lightbulb,
  FileCheck, Search, FileSignature,
};

const statusIconMap: Record<ProjectStage["status"], React.ElementType> = {
  completed: CheckCircle,
  in_progress: Loader2,
  not_started: Circle,
};

const statusStyles: Record<ProjectStage["status"], string> = {
  completed: "text-primary",
  in_progress: "text-accent",
  not_started: "text-muted-foreground",
};

export function StageNavigation({ stages }: StageNavigationProps) {
  const navigate = useNavigate();
  const { id } = useParams();

  // Group stages by phase
  const phases = stages.reduce<Record<string, ProjectStage[]>>((acc, stage) => {
    if (!acc[stage.phase]) acc[stage.phase] = [];
    acc[stage.phase].push(stage);
    return acc;
  }, {});

  return (
    <nav className="space-y-4">
      {Object.entries(phases).map(([phase, phaseStages]) => (
        <div key={phase}>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
            {phase}
          </h4>
          <ul className="space-y-1">
            {phaseStages.map((stage) => {
              const StageIcon = iconMap[stage.icon] || ClipboardList;
              const StatusIcon = statusIconMap[stage.status];
              return (
                <li key={stage.id}>
                  <button
                    onClick={() => navigate(`/projects/${id}/${stage.path}`)}
                    className={cn(
                      "flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm font-medium transition-colors text-left",
                      "hover:bg-muted",
                      stage.status === "in_progress" && "bg-muted"
                    )}
                  >
                    <StageIcon className={cn("h-4 w-4 shrink-0", statusStyles[stage.status])} />
                    <span className="flex-1 truncate">{stage.label}</span>
                    <StatusIcon className={cn("h-3.5 w-3.5 shrink-0", statusStyles[stage.status])} />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}
