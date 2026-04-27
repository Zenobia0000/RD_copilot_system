import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { Project, PhaseProgress } from "@/types/project";
import { PROJECT_STATUS_LABELS } from "@/types/project";
import { Calendar, Trash2, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: Project;
  onDelete: (project: Project) => void;
  isDeleting?: boolean;
}

const statusVariantMap: Record<string, "default" | "secondary" | "outline"> = {
  in_progress: "default",
  completed: "secondary",
  archived: "outline",
};

/** Phase color band segments */
const PHASE_STEPS: { phase: 1 | 2 | 3; keys: (keyof PhaseProgress)[] }[] = [
  { phase: 1, keys: ["D1", "D2", "PG-D"] },
  { phase: 2, keys: ["X1", "X2", "PG-X"] },
  { phase: 3, keys: ["V1", "V2", "PG-V"] },
];

const phaseColors: Record<number, string> = {
  1: "bg-phase-1",
  2: "bg-phase-2",
  3: "bg-phase-3",
};

const phaseColorsMuted: Record<number, string> = {
  1: "bg-phase-1/20",
  2: "bg-phase-2/20",
  3: "bg-phase-3/20",
};

function getPhaseSegmentFill(keys: (keyof PhaseProgress)[], progress: PhaseProgress): number {
  const passed = keys.filter((k) => progress[k] === "passed").length;
  return Math.round((passed / keys.length) * 100);
}

export function ProjectCard({ project, onDelete, isDeleting = false }: ProjectCardProps) {
  const navigate = useNavigate();

  const formattedDate = new Date(project.updatedAt).toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return (
    <Card
      className="cursor-pointer transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5 overflow-hidden group rounded-xl"
      onClick={() => navigate(`/projects/${project.id}`)}
    >
      {/* Phase color band top */}
      <div className="flex h-1">
        {PHASE_STEPS.map(({ phase, keys }) => {
          const fill = getPhaseSegmentFill(keys, project.phase_progress);
          return (
            <div key={phase} className={cn("flex-1 relative", phaseColorsMuted[phase])}>
              <div
                className={cn("absolute inset-y-0 left-0", phaseColors[phase])}
                style={{ width: `${fill}%` }}
              />
            </div>
          );
        })}
      </div>

      <CardHeader className="pb-1.5">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-[15px] font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors">
            {project.name}
          </CardTitle>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              aria-label={`刪除專案 ${project.name}`}
              className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(project);
              }}
              disabled={isDeleting}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            <Badge variant={statusVariantMap[project.status]} className="text-xs">
              {PROJECT_STATUS_LABELS[project.status]}
            </Badge>
          </div>
        </div>
        <CardDescription className="line-clamp-2 text-[13px] mt-1.5 min-h-[2.5rem]">
          {project.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 pt-1">
        {/* Progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground">進度</span>
            <span className="font-medium">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-1.5" />
        </div>

        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {project.createdBy}
          </span>
          <Badge variant="outline" className="text-[11px] font-normal">
            {project.gates_passed}/{project.gates_total} Gates
          </Badge>
        </div>
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <Badge variant="secondary" className="font-normal text-[11px]">{project.phase}</Badge>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formattedDate}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}