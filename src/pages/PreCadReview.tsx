import { useState, useMemo, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { ArrowLeft, Check, X, AlertTriangle, ClipboardCheck, Loader2, Eye, ShieldCheck, ShieldAlert } from "lucide-react";
import { usePreCadSolutions, usePreCadConvergenceStats } from "@/hooks/api/usePreCadReview";
import { useConstraints } from "@/hooks/api";
import { Solution } from "@/types/solution";
import { ReviewDimension, SolutionReview } from "@/types/preCadReview";
import { ContradictionSeverity } from "@/types/contradiction";
import { SpatialTraceHover } from "@/components/precad/SpatialTraceHover";
import { preCadAnalyze, type PreCadAnalyzeResponse } from "@/lib/api";

// Constraint feasibility — from DB constraints table
const feasibilityStatusConfig = {
  verified: { label: "已驗證", color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200" },
  questionable: { label: "存疑", color: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200" },
  infeasible: { label: "不可行", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
};

const severityBadgeClass: Record<ContradictionSeverity, string> = {
  fatal: "bg-destructive text-destructive-foreground",
  major: "bg-orange-500 text-white",
  minor: "bg-muted text-muted-foreground",
};

const REVIEW_DIMENSIONS: Omit<ReviewDimension, "rating" | "summary">[] = [
  { id: "space", label: "空間約束", description: "方案是否符合現有空間與尺寸限制" },
  { id: "decouple", label: "解耦程度", description: "方案是否與其他子系統充分解耦，可獨立開發驗證" },
  { id: "verifiable", label: "可驗證性", description: "是否存在可在 Pre-CAD 階段驗證的最小實驗" },
  { id: "risk", label: "主要風險", description: "方案的關鍵風險是否已識別且可控" },
  { id: "min-cad", label: "最小 CAD 工作量", description: "進入 CAD 階段所需的工作量是否合理" },
];

const createDefaultDimensions = (): ReviewDimension[] =>
  REVIEW_DIMENSIONS.map((d) => ({ ...d, rating: null, summary: "" }));

const PreCadReview = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // --- API hooks ---
  const { data: candidates = [], isLoading: isLoadingSolutions } = usePreCadSolutions(id);
  const { data: convergenceStats, isLoading: isLoadingStats } = usePreCadConvergenceStats(id);
  const { data: constraints = [], isLoading: isLoadingConstraints } = useConstraints(id);

  const isLoading = isLoadingSolutions || isLoadingStats || isLoadingConstraints;

  // Convergence stats
  const confidenceScore = convergenceStats?.confidenceScore ?? 0;
  const fatalResolved = convergenceStats?.fatalResolved ?? 0;
  const fatalTotal = convergenceStats?.fatalTotal ?? 0;
  const majorResolved = convergenceStats?.majorResolved ?? 0;
  const majorTotal = convergenceStats?.majorTotal ?? 0;
  const minorResolved = convergenceStats?.minorResolved ?? 0;
  const minorTotal = convergenceStats?.minorTotal ?? 0;

  const gatePassed = confidenceScore === 100;

  // Build constraint feasibility from DB constraints
  const constraintFeasibility = useMemo(() => {
    return constraints.map((c: any) => ({
      id: c.id,
      label: `${c.constraintCode ?? c.constraint_code ?? ''} ${c.description}`,
      status: (c.feasibility ?? 'questionable') as 'verified' | 'questionable' | 'infeasible',
    }));
  }, [constraints]);

  const [reviews, setReviews] = useState<Record<string, SolutionReview>>({});

  // Initialize reviews when candidates change
  useMemo(() => {
    if (candidates.length === 0) return;
    setReviews((prev) => {
      const next = { ...prev };
      candidates.forEach((s) => {
        if (!next[s.id]) {
          next[s.id] = { solutionId: s.id, dimensions: createDefaultDimensions(), reviewed: false };
        }
      });
      return next;
    });
  }, [candidates]);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [conclusion, setConclusion] = useState("");
  const [reviewingSolutionId, setReviewingSolutionId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // WBS 10.3: per-solution Pre-CAD AI analysis cache.
  // No Supabase column stores `spatial_trace`; the backend endpoint is
  // stateless, so we call `preCadAnalyze` on demand when the review dialog
  // opens for a candidate and cache the response locally by solution id.
  const [aiAnalysisBySol, setAiAnalysisBySol] = useState<Record<string, PreCadAnalyzeResponse>>({});
  const [aiAnalysisStatus, setAiAnalysisStatus] = useState<Record<string, "idle" | "loading" | "done" | "error">>({});

  useEffect(() => {
    if (!reviewingSolutionId) return;
    const sol = candidates.find((c) => c.id === reviewingSolutionId);
    if (!sol) return;
    if (aiAnalysisStatus[reviewingSolutionId] && aiAnalysisStatus[reviewingSolutionId] !== "idle") return;

    let cancelled = false;
    setAiAnalysisStatus((p) => ({ ...p, [reviewingSolutionId]: "loading" }));
    preCadAnalyze(reviewingSolutionId, {
      project_id: sol.projectId,
      alternative_name: sol.name,
      mechanism: sol.mechanism || sol.description || sol.name,
      constraints: constraints.map((c: any) => c.description).filter(Boolean),
    })
      .then((resp) => {
        if (cancelled) return;
        setAiAnalysisBySol((p) => ({ ...p, [reviewingSolutionId]: resp }));
        setAiAnalysisStatus((p) => ({ ...p, [reviewingSolutionId]: "done" }));
      })
      .catch(() => {
        if (cancelled) return;
        setAiAnalysisStatus((p) => ({ ...p, [reviewingSolutionId]: "error" }));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reviewingSolutionId]);

  const toggleSelected = (sId: string) => {
    setSelectedIds((prev) =>
      prev.includes(sId) ? prev.filter((x) => x !== sId) : [...prev, sId]
    );
  };

  const updateDimension = (solId: string, dimId: string, field: "rating" | "summary", value: string) => {
    setReviews((prev) => ({
      ...prev,
      [solId]: {
        ...prev[solId],
        dimensions: prev[solId].dimensions.map((d) =>
          d.id === dimId ? { ...d, [field]: value } : d
        ),
      },
    }));
  };

  const markReviewed = (solId: string) => {
    const review = reviews[solId];
    const allRated = review.dimensions.every((d) => d.rating !== null);
    if (!allRated) {
      toast.error("請完成所有審查維度的評估");
      return;
    }
    setReviews((prev) => ({
      ...prev,
      [solId]: { ...prev[solId], reviewed: true },
    }));
    setReviewingSolutionId(null);
    toast.success("審查完成");
  };

  const allReviewed = candidates.every((c) => reviews[c.id]?.reviewed);
  const canApprove = selectedIds.length >= 3 && selectedIds.length <= 5 && allReviewed && gatePassed;

  const handleApprove = async () => {
    if (!gatePassed) {
      toast.error("Gate P 門檻未達標：所有 Fatal 和 Major 矛盾必須 100% 收斂");
      return;
    }
    if (!canApprove) {
      if (selectedIds.length < 3) toast.error("請至少選擇 3 條候選方案");
      else if (selectedIds.length > 5) toast.error("最多選擇 5 條候選方案");
      else if (!allReviewed) toast.error("請完成所有方案的審查");
      return;
    }
    setIsSubmitting(true);
    await new Promise((r) => setTimeout(r, 1500));
    setIsSubmitting(false);
    toast.success("Pre-CAD 審查已批准，專案推進至下一階段");
    navigate(`/projects/${id}`);
  };

  const getRatingIcon = (rating: string | null) => {
    if (rating === "pass") return <Check className="h-4 w-4 text-primary" />;
    if (rating === "concern") return <AlertTriangle className="h-4 w-4 text-accent" />;
    if (rating === "fail") return <X className="h-4 w-4 text-destructive" />;
    return null;
  };

  const getReviewStatus = (solId: string) => {
    const r = reviews[solId];
    if (!r) return "pending";
    if (r.reviewed) return "done";
    if (r.dimensions.some((d) => d.rating !== null)) return "partial";
    return "pending";
  };

  const reviewingCandidate = candidates.find((c) => c.id === reviewingSolutionId);

  const scoreColor = confidenceScore >= 100 ? "text-emerald-600" : confidenceScore >= 50 ? "text-amber-600" : "text-destructive";
  const progressColor = confidenceScore >= 100 ? "bg-emerald-500" : confidenceScore >= 50 ? "bg-amber-500" : "bg-destructive";

  /* ---- Loading state ---- */
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">載入審查資料中...</span>
      </div>
    );
  }

  return (
    <div className="page-shell-wide">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/projects/${id}`)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: '"Noto Sans TC", "Helvetica Neue", Arial, sans-serif' }}>
            Pre-CAD 審查
          </h1>
          <p className="text-sm text-muted-foreground">評估候選方案，確認 Gate P 門檻後選擇 3-5 條進入 CAD 階段</p>
        </div>
      </div>

      {/* Section 1: Pre-CAD Confidence Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Confidence Score */}
        <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <CardContent className="p-4 space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Pre-CAD Confidence Score</p>
            <div className={`text-3xl font-bold ${scoreColor}`}>{confidenceScore.toFixed(1)}%</div>
            <div className="relative">
              <Progress value={confidenceScore} className="h-2" />
              <div className={`absolute inset-0 h-2 rounded-full ${progressColor}`} style={{ width: `${Math.min(confidenceScore, 100)}%` }} />
            </div>
            <p className="text-xs text-muted-foreground">
              公式: converged(Fatal+Major) / total(Fatal+Major)
            </p>
          </CardContent>
        </Card>

        {/* Gate P Threshold */}
        <Card className={`rounded-lg ${gatePassed ? "border-emerald-300 dark:border-emerald-700" : "border-destructive/30"}`} style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <CardContent className="p-4 space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Gate P 門檻</p>
            <div className="flex items-center gap-2">
              {gatePassed ? (
                <>
                  <ShieldCheck className="h-6 w-6 text-emerald-600" />
                  <span className="text-lg font-semibold text-emerald-600">達標</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="h-6 w-6 text-destructive" />
                  <span className="text-lg font-semibold text-destructive">未達標</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              要求：Fatal+Major 矛盾 Confidence = 100%
            </p>
            {!gatePassed && (
              <p className="text-xs text-destructive">
                尚有未收斂的 Fatal/Major 矛盾，無法批准審查
              </p>
            )}
          </CardContent>
        </Card>

        {/* Convergence Summary */}
        <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <CardContent className="p-4 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">收斂圖摘要</p>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <Badge className={`text-xs ${severityBadgeClass.fatal}`}>Fatal</Badge>
                <span className={fatalResolved === fatalTotal ? "text-emerald-600" : "text-destructive"}>
                  {fatalResolved}/{fatalTotal} 已解決
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <Badge className={`text-xs ${severityBadgeClass.major}`}>Major</Badge>
                <span className={majorResolved === majorTotal ? "text-emerald-600" : "text-destructive"}>
                  {majorResolved}/{majorTotal} 已解決
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <Badge className={`text-xs ${severityBadgeClass.minor}`}>Minor</Badge>
                <span className="text-muted-foreground">
                  {minorResolved}/{minorTotal} 已解決
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Constraint Feasibility */}
        <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <CardContent className="p-4 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">約束可行性驗證</p>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {constraintFeasibility.length === 0 ? (
                <p className="text-xs text-muted-foreground">尚無約束資料</p>
              ) : (
                constraintFeasibility.map((cf) => (
                  <div key={cf.id} className="flex items-center justify-between gap-2 text-xs">
                    <span className="line-clamp-1 flex-1">{cf.label}</span>
                    <Badge variant="outline" className={`text-xs shrink-0 ${feasibilityStatusConfig[cf.status]?.color ?? ''}`}>
                      {feasibilityStatusConfig[cf.status]?.label ?? cf.status}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Section 2: Candidate list */}
      <div>
        <h2 className="text-lg font-semibold mb-3">候選方案 ({candidates.length})</h2>
        {candidates.length === 0 ? (
          <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
            <CardContent className="py-12 text-center text-muted-foreground">
              <p className="font-medium">沒有候選方案</p>
              <p className="text-sm mt-1">請先在方案探索頁面生成並通過 MUST 快篩。</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {candidates.map((sol) => {
              const status = getReviewStatus(sol.id);
              const isSelected = selectedIds.includes(sol.id);
              return (
                <Card
                  key={sol.id}
                  className={`rounded-lg transition-all ${isSelected ? "ring-2 ring-primary" : ""}`}
                  style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}
                >
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelected(sol.id)}
                        />
                        <h3 className="font-semibold text-sm line-clamp-1">{sol.name}</h3>
                      </div>
                      <Badge
                        variant={status === "done" ? "default" : status === "partial" ? "secondary" : "outline"}
                        className="text-xs shrink-0"
                      >
                        {status === "done" ? "已審查" : status === "partial" ? "審查中" : "待審查"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">{sol.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex gap-1">
                        {sol.mustCriteria.map((m) => (
                          <span key={m.id}>
                            {m.passed === true ? (
                              <Check className="h-3.5 w-3.5 text-primary" />
                            ) : m.passed === false ? (
                              <X className="h-3.5 w-3.5 text-destructive" />
                            ) : (
                              <span className="h-3.5 w-3.5 text-muted-foreground">—</span>
                            )}
                          </span>
                        ))}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setReviewingSolutionId(sol.id)}
                      >
                        <Eye className="mr-1 h-3.5 w-3.5" />
                        {status === "done" ? "查看" : "審查"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Section 4: Conclusion & approval */}
      {candidates.length > 0 && (
        <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <ClipboardCheck className="h-5 w-5" />
              審查結論
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                已選擇 <span className="font-semibold text-foreground">{selectedIds.length}</span> 條方案（需 3-5 條）
              </p>
              {selectedIds.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {selectedIds.map((sId) => {
                    const sol = candidates.find((c) => c.id === sId);
                    return sol ? (
                      <Badge key={sId} variant="secondary" className="text-xs">{sol.name}</Badge>
                    ) : null;
                  })}
                </div>
              )}
            </div>
            <div className="space-y-1.5">
              <Label>審查結論備註（選填）</Label>
              <Textarea
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                placeholder="記錄審查會議的關鍵討論和決策原因..."
                maxLength={500}
                rows={3}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={handleApprove} disabled={!canApprove || isSubmitting}>
                {isSubmitting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                批准審查
              </Button>
              {!gatePassed && (
                <p className="text-xs text-destructive flex items-center gap-1">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Gate P 門檻未達標，無法批准
                </p>
              )}
              {gatePassed && !allReviewed && (
                <p className="text-xs text-muted-foreground">* 需完成所有方案的審查後才能批准</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Review dialog */}
      <Dialog open={!!reviewingSolutionId} onOpenChange={(o) => !o && setReviewingSolutionId(null)}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{reviewingCandidate?.name} — 審查評估</DialogTitle>
          </DialogHeader>
          {reviewingSolutionId && reviews[reviewingSolutionId] && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">{reviewingCandidate?.description}</p>

              <Accordion type="multiple" defaultValue={REVIEW_DIMENSIONS.map((d) => d.id)} className="w-full">
                {reviews[reviewingSolutionId].dimensions.map((dim) => (
                  <AccordionItem key={dim.id} value={dim.id}>
                    <AccordionTrigger className="text-sm">
                      <div className="flex items-center gap-2">
                        {getRatingIcon(dim.rating)}
                        <span>{dim.label}</span>
                        {dim.id === "space" && (() => {
                          // WBS 10.3: wire the hover-card to the real
                          // PreCadAnalyzeResponse fetched on dialog open.
                          const status = aiAnalysisStatus[reviewingSolutionId] ?? "idle";
                          const resp = aiAnalysisBySol[reviewingSolutionId];
                          if (status === "loading") {
                            return (
                              <span className="text-xs text-muted-foreground">空間追蹤計算中…</span>
                            );
                          }
                          if (status === "done" && resp) {
                            return (
                              <SpatialTraceHover
                                trace={resp.spatial_trace ?? null}
                                score={resp.spatial_score ?? 0}
                              />
                            );
                          }
                          if (status === "error") {
                            return (
                              <span className="text-xs text-destructive">AI 分析失敗</span>
                            );
                          }
                          return (
                            <span className="text-xs text-muted-foreground">尚未執行 AI 分析</span>
                          );
                        })()}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-3 pt-2">
                      <p className="text-xs text-muted-foreground">{dim.description}</p>
                      <RadioGroup
                        value={dim.rating || ""}
                        onValueChange={(v) => updateDimension(reviewingSolutionId, dim.id, "rating", v)}
                        className="flex gap-4"
                      >
                        <div className="flex items-center gap-1.5">
                          <RadioGroupItem value="pass" id={`${dim.id}-pass`} />
                          <Label htmlFor={`${dim.id}-pass`} className="text-sm cursor-pointer">通過</Label>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <RadioGroupItem value="concern" id={`${dim.id}-concern`} />
                          <Label htmlFor={`${dim.id}-concern`} className="text-sm cursor-pointer">有疑慮</Label>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <RadioGroupItem value="fail" id={`${dim.id}-fail`} />
                          <Label htmlFor={`${dim.id}-fail`} className="text-sm cursor-pointer">不通過</Label>
                        </div>
                      </RadioGroup>
                      <Textarea
                        value={dim.summary}
                        onChange={(e) => updateDimension(reviewingSolutionId, dim.id, "summary", e.target.value)}
                        placeholder="簡短評估摘要..."
                        maxLength={200}
                        rows={2}
                        className="text-sm"
                      />
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>

              <div className="flex gap-2 pt-2">
                <Button onClick={() => markReviewed(reviewingSolutionId)}>
                  完成審查
                </Button>
                <Button variant="outline" onClick={() => setReviewingSolutionId(null)}>
                  關閉
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PreCadReview;
