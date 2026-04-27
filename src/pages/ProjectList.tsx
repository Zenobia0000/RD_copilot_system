import { useState, useMemo } from "react";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { ProjectFilters } from "@/components/projects/ProjectFilters";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useDeleteProject, useProjects } from "@/hooks/api/useProjects";
import type { Project } from "@/types/project";
import { FolderOpen, AlertCircle, RefreshCw, FolderKanban, PlayCircle, CheckCircle2, Archive, AlertTriangle } from "lucide-react";

export default function ProjectList() {
  const [search, setSearch] = useState("");
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [creatorFilter, setCreatorFilter] = useState("all");
  const [createOpen, setCreateOpen] = useState(false);
  const [projectPendingDelete, setProjectPendingDelete] = useState<Project | null>(null);

  const { data: projects = [], isLoading, isError, refetch } = useProjects();
  const deleteProject = useDeleteProject();

  const handleConfirmDelete = async () => {
    if (!projectPendingDelete) return;
    try {
      await deleteProject.mutateAsync({ id: projectPendingDelete.id });
      setProjectPendingDelete(null);
    } catch {
      // toast is handled in useDeleteProject
    }
  };

  // Extract unique creators for filter
  const creators = useMemo(() => {
    const set = new Set(projects.map((p) => p.createdBy));
    return Array.from(set).sort();
  }, [projects]);

  // Stats
  const stats = useMemo(() => ({
    total: projects.length,
    inProgress: projects.filter((p) => p.status === "in_progress").length,
    completed: projects.filter((p) => p.status === "completed").length,
    archived: projects.filter((p) => p.status === "archived").length,
  }), [projects]);

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const q = search.toLowerCase();
      const matchesSearch =
        !search ||
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q);
      const matchesPhase =
        phaseFilter === "all" ||
        (phaseFilter === "completed" ? p.status === "completed" : p.phase === phaseFilter);
      const matchesCreator =
        creatorFilter === "all" || p.createdBy === creatorFilter;
      return matchesSearch && matchesPhase && matchesCreator;
    });
  }, [projects, search, phaseFilter, creatorFilter]);

  const statCards = [
    { label: "全部專案", value: stats.total, icon: FolderKanban, color: "text-primary" },
    { label: "進行中", value: stats.inProgress, icon: PlayCircle, color: "text-phase-2" },
    { label: "已完成", value: stats.completed, icon: CheckCircle2, color: "text-success" },
    { label: "已封存", value: stats.archived, icon: Archive, color: "text-muted-foreground" },
  ];

  return (
    <div className="page-shell-list">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-h2 tracking-tight">專案列表</h1>
        <p className="text-sm text-muted-foreground">
          管理您的概念設計專案，追蹤進度與決策。
        </p>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {statCards.map((s) => (
          <Card key={s.label} className="overflow-hidden rounded-xl border">
            <CardContent className="flex items-center gap-3 p-3.5">
              <div className={`rounded-md bg-muted p-2 ${s.color}`}>
                <s.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xl font-semibold leading-none">{s.value}</p>
                <p className="text-[11px] text-muted-foreground mt-1">{s.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <ProjectFilters
        search={search}
        onSearchChange={setSearch}
        phaseFilter={phaseFilter}
        onPhaseFilterChange={setPhaseFilter}
        creatorFilter={creatorFilter}
        onCreatorFilterChange={setCreatorFilter}
        creators={creators}
        onCreateProject={() => setCreateOpen(true)}
      />

      {/* Results count */}
      {!isLoading && !isError && filteredProjects.length > 0 && (
        <p className="text-[11px] text-muted-foreground">
          顯示 {filteredProjects.length} 個專案
          {(search || phaseFilter !== "all" || creatorFilter !== "all") && (
            <span>（共 {projects.length} 個）</span>
          )}
        </p>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-3 rounded-lg border p-6">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-2 w-full" />
              <div className="flex justify-between">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-lg font-semibold">載入失敗</h2>
          <p className="text-sm text-muted-foreground mt-1 mb-4">
            無法取得專案列表，請稍後再試。
          </p>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            重試
          </Button>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <FolderOpen className="h-12 w-12 text-muted-foreground mb-4" />
          <h2 className="text-lg font-semibold">
            {search || phaseFilter !== "all" || creatorFilter !== "all"
              ? "找不到符合條件的專案"
              : "尚無專案"}
          </h2>
          <p className="text-sm text-muted-foreground mt-1 mb-4">
            {search || phaseFilter !== "all" || creatorFilter !== "all"
              ? "嘗試調整搜尋或篩選條件。"
              : "建立你的第一個專案，開始概念設計旅程。"}
          </p>
          {!search && phaseFilter === "all" && creatorFilter === "all" && (
            <Button onClick={() => setCreateOpen(true)}>新增專案</Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={setProjectPendingDelete}
              isDeleting={deleteProject.isPending && projectPendingDelete?.id === project.id}
            />
          ))}
        </div>
      )}

      <CreateProjectModal open={createOpen} onOpenChange={setCreateOpen} />

      <AlertDialog open={!!projectPendingDelete} onOpenChange={(open) => !open && setProjectPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>確認刪除專案？</AlertDialogTitle>
            <AlertDialogDescription>
              專案「{projectPendingDelete?.name ?? ""}」將被永久刪除，且無法復原。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">高風險操作</p>
              <p>刪除後將移除該專案及其關聯資料，請再次確認。</p>
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteProject.isPending}>取消</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={handleConfirmDelete}
              disabled={deleteProject.isPending}
            >
              {deleteProject.isPending ? "刪除中..." : "確認刪除"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
