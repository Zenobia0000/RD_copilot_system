import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useProject, useProjectStats } from "@/hooks/api/useProjects";
import { useBrief, useConstraints, useKpis } from "@/hooks/api/useBrief";
import { useContradictions } from "@/hooks/api/useContradictions";
import {
  useAntiAnchorRoutes,
  useTrizSolutions,
  useSubsystems,
  useAlternatives,
} from "@/hooks/api";
import { useConceptRoutes } from "@/hooks/api/useConceptRoutes";
import { useTrackAssumptions } from "@/hooks/api/useTrack";
import { getNavCards } from "@/lib/navCards";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PhaseProgressBar } from "@/components/dashboard/PhaseProgressBar";
import { QuickStatsGrid } from "@/components/dashboard/QuickStatsGrid";
import { GateDonut } from "@/components/dashboard/GateDonut";
import { NavCards } from "@/components/dashboard/NavCards";
import { ProjectTimeline } from "@/components/dashboard/ProjectTimeline";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { MissionSummaryCard } from "@/components/dashboard/MissionSummaryCard";
import { PreCadScoreGauge } from "@/components/dashboard/PreCadScoreGauge";
import { ContradictionConvergenceCard } from "@/components/dashboard/ContradictionConvergenceCard";
import { PROJECT_STATUS_LABELS } from "@/types/project";
import type { CriticalKPI, ProjectHistoryItem, PreCadScore, ContradictionConvergence } from "@/types/project";
import { EvidenceEntryDialog } from "@/components/evidence/EvidenceEntryDialog";
import { ArrowLeft, AlertCircle, Calendar, User, RefreshCw } from "lucide-react";

export default function ProjectDashboard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Invalidate all cached queries for this project on mount so dashboard always shows fresh data
  useEffect(() => {
    if (id) {
      queryClient.invalidateQueries({ queryKey: ['projects', id] });
      queryClient.invalidateQueries({ queryKey: ['briefs', id] });
      queryClient.invalidateQueries({ queryKey: ['constraints', id] });
      queryClient.invalidateQueries({ queryKey: ['kpis', id] });
      queryClient.invalidateQueries({ queryKey: ['contradictions', id] });
      queryClient.invalidateQueries({ queryKey: ['assumptions', id] });
      queryClient.invalidateQueries({ queryKey: ['track', 'assumptions', id] });
    }
  }, [id, queryClient]);

  const { data: project, isLoading, isError, refetch } = useProject(id);
  const { data: liveStats } = useProjectStats(id);
  const { data: brief } = useBrief(id);
  const { data: constraints } = useConstraints(id);
  const { data: kpis } = useKpis(id);
  const { data: contradictions } = useContradictions(id);

  // Phase 2 data sources for timeline
  const antiAnchorRoutes = useAntiAnchorRoutes(id);
  const trizSolutions = useTrizSolutions(id);
  const subsystemsQuery = useSubsystems(id);
  const alternativesQuery = useAlternatives(id);
  const conceptRoutesQuery = useConceptRoutes(id);
  const trackAssumptionsQuery = useTrackAssumptions(id);

  // Evidence entry dialog state
  const [evidenceDialogOpen, setEvidenceDialogOpen] = useState(false);
  const [evidenceDefaultKpiId, setEvidenceDefaultKpiId] = useState<string | null>(null);

  const handleLogEvidence = (kpiId: string) => {
    setEvidenceDefaultKpiId(kpiId);
    setEvidenceDialogOpen(true);
  };

  // Derive KPI cards from DB — use real current_value + current_status
  const criticalKPIs: CriticalKPI[] = useMemo(() =>
    (kpis ?? []).map((k) => ({
      id: k.id,
      name: k.kpiName,
      target: `${k.targetValue} ${k.unit}`.trim(),
      current: k.currentValue
        ? `${k.currentValue} ${k.unit}`.trim()
        : '待測試',
      status: (k.currentStatus as CriticalKPI['status']) || 'unknown',
    })),
    [kpis],
  );

  // Derive convergence from real contradictions
  const convergence: ContradictionConvergence | undefined = useMemo(() => {
    if (!contradictions || contradictions.length === 0) return undefined;
    const fatalCount = contradictions.filter((c) => c.severity === 'fatal').length;
    const majorCount = contradictions.filter((c) => c.severity === 'major').length;
    const minorCount = contradictions.filter((c) => c.severity === 'minor').length;
    return {
      totalNodes: contradictions.length,
      fatalCount,
      majorCount,
      minorCount,
      hasCircularDependency: false,
      healthWarning: contradictions.length > 5 || fatalCount > 0,
    };
  }, [contradictions]);

  // Derive pre-CAD score from contradictions resolved status
  const preCadScore: PreCadScore | undefined = useMemo(() => {
    if (!contradictions || contradictions.length === 0) return undefined;
    const fatal = contradictions.filter((c) => c.severity === 'fatal');
    const major = contradictions.filter((c) => c.severity === 'major');
    const fatalResolved = fatal.filter((c) => c.resolved).length;
    const majorResolved = major.filter((c) => c.resolved).length;
    const total = fatal.length + major.length;
    const resolved = fatalResolved + majorResolved;
    const score = total > 0 ? Math.round((resolved / total) * 100) : 100;
    return { score, fatalResolved, fatalTotal: fatal.length, majorResolved, majorTotal: major.length };
  }, [contradictions]);

  // Build timeline from real project events (Phase 1 + Phase 2)
  const history: ProjectHistoryItem[] = useMemo(() => {
    if (!project) return [];
    const items: ProjectHistoryItem[] = [];
    const author = project.createdBy;

    // --- Phase 1: Task Definition ---
    items.push({
      id: 'h-created',
      date: project.createdAt,
      title: '專案建立',
      summary: `專案「${project.name}」正式建立。`,
      author,
      type: 'milestone',
    });
    if (brief) {
      items.push({
        id: 'h-brief',
        date: brief.updatedAt ?? brief.createdAt,
        title: '任務定義確認',
        summary: `Mission: ${brief.mission.slice(0, 60)}${brief.mission.length > 60 ? '...' : ''}`,
        author,
        type: 'milestone',
        relatedPage: 'brief',
      });
    }
    if (contradictions && contradictions.length > 0) {
      items.push({
        id: 'h-contradictions',
        date: contradictions[contradictions.length - 1].createdAt,
        title: `矛盾分析：已識別 ${contradictions.length} 項`,
        summary: `包含 ${contradictions.filter(c => c.severity === 'fatal').length} 項致命、${contradictions.filter(c => c.severity === 'major').length} 項重大矛盾。`,
        author,
        type: 'task',
        relatedPage: 'explore',
      });
    }
    if (kpis && kpis.length > 0) {
      items.push({
        id: 'h-kpis',
        date: kpis[kpis.length - 1].createdAt,
        title: `KPI 設定：${kpis.length} 項指標`,
        summary: kpis.map(k => k.kpiName).join('、'),
        author,
        type: 'task',
        relatedPage: 'brief',
      });
    }
    if (constraints && constraints.length > 0) {
      const hard = constraints.filter(c => c.type === 'hard').length;
      const soft = constraints.filter(c => c.type === 'soft').length;
      items.push({
        id: 'h-constraints',
        date: constraints[constraints.length - 1].createdAt,
        title: `約束條件定義：${hard} 硬約束、${soft} 軟約束`,
        summary: constraints.slice(0, 3).map(c => c.description).join('；'),
        author,
        type: 'task',
        relatedPage: 'brief',
      });
    }

    // --- Phase 2: Solution Creation ---
    const aaRoutes = antiAnchorRoutes.data ?? [];
    if (aaRoutes.length > 0) {
      const latestDate = aaRoutes.reduce((d, r) => r.createdAt && r.createdAt > d ? r.createdAt : d, aaRoutes[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-antianchor',
        date: latestDate,
        title: `Anti-Anchor：${aaRoutes.length} 條非典型架構`,
        summary: aaRoutes.map(r => r.name).join('、'),
        author,
        type: 'task',
        relatedPage: 'create',
      });
    }

    const triz = trizSolutions.data ?? [];
    if (triz.length > 0) {
      const adopted = triz.filter(t => t.status === 'adopted');
      const latestDate = triz.reduce((d, t) => t.createdAt && t.createdAt > d ? t.createdAt : d, triz[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-triz',
        date: latestDate,
        title: `TRIZ 解矛盾：${triz.length} 條解法`,
        summary: `已採用 ${adopted.length} 條（TC ${triz.filter(t => t.path === 'TC').length} / PC ${triz.filter(t => t.path === 'PC').length} / SF ${triz.filter(t => t.path === 'SF').length}）`,
        author,
        type: 'task',
        relatedPage: 'create',
      });
    }

    const subs = subsystemsQuery.data ?? [];
    if (subs.length > 0) {
      const confirmed = subs.filter(s => s.confirmed).length;
      const latestDate = subs.reduce((d, s) => s.createdAt && s.createdAt > d ? s.createdAt : d, subs[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-subsystems',
        date: latestDate,
        title: `子系統定義：${subs.length} 個（${confirmed} 已確認）`,
        summary: subs.map(s => s.name).join('、'),
        author,
        type: 'task',
        relatedPage: 'create',
      });
    }

    const alts = alternativesQuery.data ?? [];
    if (alts.length > 0) {
      const passed = alts.filter(a => a.overallPass === true).length;
      const latestDate = alts.reduce((d, a) => a.createdAt && a.createdAt > d ? a.createdAt : d, alts[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-alternatives',
        date: latestDate,
        title: `方案整合：${alts.length} 個概念方案`,
        summary: alts.map(a => a.name || '(未命名)').join('、'),
        author,
        type: 'task',
        relatedPage: 'create',
      });
      // MUST screening result
      const mustDone = alts.filter(a => Object.values(a.mustScores).every(v => v !== null));
      const mustPassed = alts.filter(a => !Object.values(a.mustScores).includes('fail') && Object.values(a.mustScores).every(v => v !== null));
      if (mustDone.length > 0) {
        items.push({
          id: 'h-must',
          date: latestDate,
          title: `MUST 快篩完成：${mustPassed.length}/${mustDone.length} 通過`,
          summary: mustPassed.map(a => a.name).join('、') || '無方案通過',
          author,
          type: 'review',
          relatedPage: 'create',
        });
      }
      // Pre-CAD result
      if (passed > 0) {
        items.push({
          id: 'h-precad',
          date: alts.find(a => a.overallPass === true)?.updatedAt ?? latestDate,
          title: `Pre-CAD 審查：${passed} 個方案通過`,
          summary: alts.filter(a => a.overallPass === true).map(a => a.name).join('、'),
          author,
          type: 'milestone',
          relatedPage: 'create',
        });
      }
    }

    const cRoutes = conceptRoutesQuery.data ?? [];
    if (cRoutes.length > 0) {
      const compositeCount = cRoutes.filter(r => r.type === 'composite').length;
      const singleCount = cRoutes.filter(r => r.type === 'single').length;
      const latestDate = cRoutes.reduce((d, r) => r.createdAt && r.createdAt > d ? r.createdAt : d, cRoutes[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-conceptroutes',
        date: latestDate,
        title: `Concept Routes 確認：${cRoutes.length} 條`,
        summary: `${compositeCount} composite、${singleCount} single`,
        author,
        type: 'decision',
        relatedPage: 'create',
      });
    }

    const assumptions = trackAssumptionsQuery.data ?? [];
    if (assumptions.length > 0) {
      const verified = assumptions.filter(a => a.verificationStatus === 'verified').length;
      const negated = assumptions.filter(a => a.verificationStatus === 'negated').length;
      const latestDate = assumptions.reduce((d, a) => a.createdAt && a.createdAt > d ? a.createdAt : d, assumptions[0].createdAt ?? project.createdAt);
      items.push({
        id: 'h-assumptions',
        date: latestDate,
        title: `假設追蹤：${assumptions.length} 項假設`,
        summary: `已驗證 ${verified}、已否定 ${negated}、待驗證 ${assumptions.length - verified - negated}`,
        author,
        type: 'task',
        relatedPage: 'assumption-ledger',
      });
    }

    // Sort newest first
    items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return items;
  }, [project, brief, contradictions, kpis, constraints, antiAnchorRoutes.data, trizSolutions.data, subsystemsQuery.data, alternativesQuery.data, conceptRoutesQuery.data, trackAssumptionsQuery.data]);

  // Loading state
  if (isLoading) {
    return (
      <div className="page-shell-wide">
        <div className="space-y-3">
          <Skeleton className="h-8 w-32" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-6 w-16" />
          </div>
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-20 w-full rounded-lg" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !project) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center mx-auto max-w-md">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-lg font-semibold">
          {isError ? "載入失敗" : "專案不存在"}
        </h2>
        <p className="text-sm text-muted-foreground mt-1 mb-4">
          {isError
            ? "無法載入專案資料，請稍後再試。"
            : "找不到指定的專案，請確認 URL 是否正確。"}
        </p>
        <div className="flex gap-2">
          {isError && (
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              重試
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate("/projects")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回專案列表
          </Button>
        </div>
      </div>
    );
  }

  // Use live stats from DB if available, otherwise fall back to project.quick_stats
  const quickStats = liveStats ?? project.quick_stats;

  const navCards = getNavCards(project.phase_progress);
  const createdDate = new Date(project.createdAt).toLocaleDateString("zh-TW");
  const isZeroData = Object.values(quickStats).every((v) => v === 0);

  return (
    <div className="page-shell-wide">
      {/* Header */}
      <div className="space-y-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/projects")} className="text-muted-foreground -ml-2">
          <ArrowLeft className="h-4 w-4 mr-1" />
          返回專案列表
        </Button>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
              <Badge variant={project.status === "completed" ? "secondary" : "default"}>
                {PROJECT_STATUS_LABELS[project.status]}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1"><User className="h-3 w-3" />{project.createdBy}</span>
              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{createdDate}</span>
            </div>
          </div>
          <GateDonut passed={project.gates_passed} total={project.gates_total} />
        </div>
      </div>

      {/* Phase Progress Bar */}
      <Card>
        <CardContent className="pt-5 pb-4">
          <PhaseProgressBar progress={project.phase_progress} />
        </CardContent>
      </Card>

      {/* Mission Summary + KPIs */}
      {(brief || project.mission) && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold">專案概覽</h2>
          <MissionSummaryCard
            projectId={id}
            projectOwnerId={project.createdBy}
            mission={brief?.mission ?? project.mission ?? ''}
            hardConstraints={
              constraints?.filter(c => c.type === 'hard').map(c => c.description)
              ?? project.hardConstraints
            }
            softObjectives={
              constraints?.filter(c => c.type === 'soft').map(c => c.description)
              ?? project.softObjectives
            }
          />
          {criticalKPIs.length > 0 && (
            <KpiCards kpis={criticalKPIs} onLogEvidence={handleLogEvidence} />
          )}
        </div>
      )}

      {/* Pre-CAD Score + Contradiction Convergence */}
      {(preCadScore || convergence) && (
        <div className="grid gap-4 md:grid-cols-2">
          {preCadScore && <PreCadScoreGauge data={preCadScore} />}
          {convergence && <ContradictionConvergenceCard data={convergence} />}
        </div>
      )}

      {/* Quick Stats */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold">Quick Stats</h2>
        {isZeroData ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-sm text-muted-foreground">從 Brief 開始你的設計旅程</p>
              <Button className="mt-3" size="sm" onClick={() => navigate(`/projects/${id}/brief`)}>
                開始 Brief
              </Button>
            </CardContent>
          </Card>
        ) : (
          <QuickStatsGrid stats={quickStats} />
        )}
      </div>

      {/* 6+1 Navigation Cards */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold">功能導航</h2>
        <NavCards cards={navCards} />
      </div>

      {/* Timeline */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">專案歷程</CardTitle>
          </CardHeader>
          <CardContent>
            <ProjectTimeline projectId={project.id} history={history} />
          </CardContent>
        </Card>
      )}

      {/* Evidence Entry Dialog */}
      {id && (
        <EvidenceEntryDialog
          open={evidenceDialogOpen}
          onOpenChange={setEvidenceDialogOpen}
          projectId={id}
          defaultKpiId={evidenceDefaultKpiId}
        />
      )}
    </div>
  );
}
