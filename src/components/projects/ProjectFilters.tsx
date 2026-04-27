import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Search } from "lucide-react";

interface ProjectFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  phaseFilter: string;
  onPhaseFilterChange: (value: string) => void;
  creatorFilter: string;
  onCreatorFilterChange: (value: string) => void;
  creators: string[];
  onCreateProject: () => void;
}

export function ProjectFilters({
  search,
  onSearchChange,
  phaseFilter,
  onPhaseFilterChange,
  creatorFilter,
  onCreatorFilterChange,
  creators,
  onCreateProject,
}: ProjectFiltersProps) {
  return (
    <div className="rounded-xl border bg-card p-3 md:p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-1 flex-col gap-2.5 sm:flex-row sm:items-center">
          <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜尋專案名稱或描述..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9"
            maxLength={50}
          />
        </div>
        <Select value={phaseFilter} onValueChange={onPhaseFilterChange}>
          <SelectTrigger className="w-full sm:w-[168px]">
            <SelectValue placeholder="所有階段" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部階段</SelectItem>
            <SelectItem value="Phase I">Phase 1</SelectItem>
            <SelectItem value="Phase II">Phase 2</SelectItem>
            <SelectItem value="Phase III">Phase 3</SelectItem>
            <SelectItem value="completed">已完成</SelectItem>
          </SelectContent>
        </Select>
        <Select value={creatorFilter} onValueChange={onCreatorFilterChange}>
          <SelectTrigger className="w-full sm:w-[168px]">
            <SelectValue placeholder="所有創建者" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有創建者</SelectItem>
            {creators.filter(Boolean).map((c) => (
              <SelectItem key={c} value={c}>{c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        </div>
        <Button onClick={onCreateProject} className="shrink-0 min-w-[120px]">
          <Plus className="h-4 w-4" />
          新增專案
        </Button>
      </div>
    </div>
  );
}