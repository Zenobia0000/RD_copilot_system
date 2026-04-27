import { useState, useMemo, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { toast } from "sonner";
import {
  ArrowLeft, ArrowRight, Plus, Loader2, AlertTriangle,
  CheckCircle, XCircle, Flag, Beaker, ShieldAlert, BarChart3, Link2, Paperclip, Trash2, ClipboardCheck
} from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { KnowledgeRefsPanel } from "@/components/create/KnowledgeRefsPanel";
// TODO: Replace mockPageKnowledgeRefs with a useKnowledgeRefs hook once a knowledge_refs DB table is created (Sprint 5+)
import { mockPageKnowledgeRefs } from "@/data/mockKnowledgeRefs";
import { AttachmentsPanel } from "@/components/review/AttachmentsPanel";
import { supabase } from "@/integrations/supabase/client";
import type {
  EvidenceLevel, EvidenceMatrixRow, RiskItem, Experiment, ExperimentStatus, Gate31Item
} from "@/types/designReview";
import { EVIDENCE_LEVELS, getRiskScore, getRiskLevel, getRiskColor, EXP_STATUS_COLOR } from "@/types/designReview";
import {
  useEvidenceMatrix,
  useCreateEvidenceRow,
  useUpdateEvidenceRow,
  useRisks as useRisksQuery,
  useCreateRisk,
  useUpdateRisk as useUpdateRiskMutation,
  useDeleteRisk as useDeleteRiskMutation,
  useExperiments as useExperimentsQuery,
  useCreateExperiment,
  useUpdateExperiment,
} from "@/hooks/api";
import { useSolutions } from "@/hooks/api/useSolutions";
import { socraticGenerate } from "@/lib/api";

export default function DesignReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<string>("evidence");

  // --- Live data from Supabase ---
  const { data: solutionsData, isLoading: solutionsLoading } = useSolutions(id);
  const { data: evidenceRows, isLoading: evidenceLoading, error: evidenceError } = useEvidenceMatrix(id);
  const createEvidenceRow = useCreateEvidenceRow();
  const updateEvidenceRow = useUpdateEvidenceRow();

  const { data: risks, isLoading: risksLoading, error: risksError } = useRisksQuery(id);
  const createRiskMut = useCreateRisk();
  const updateRiskMut = useUpdateRiskMutation();
  const deleteRiskMut = useDeleteRiskMutation();

  const { data: experiments, isLoading: experimentsLoading, error: experimentsError } = useExperimentsQuery(id);
  const createExperimentMut = useCreateExperiment();
  const updateExperimentMut = useUpdateExperiment();

  const isLoading = evidenceLoading || risksLoading || experimentsLoading || solutionsLoading;
  const loadError = evidenceError || risksError || experimentsError;

  const [expModalOpen, setExpModalOpen] = useState(false);
  const [editingExp, setEditingExp] = useState<Experiment | null>(null);
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [attachments, setAttachments] = useState<any[]>([]);
  const [blackhatQuestions, setBlackhatQuestions] = useState<string[]>([]);

  // Solution disposition & conclusion state
  const [dispositions, setDispositions] = useState<Record<string, string>>({});
  const [reviewConclusion, setReviewConclusion] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Get candidate solutions from Supabase (solutions that passed at least one MUST criterion)
  const candidateSolutions = useMemo(() => {
    if (!solutionsData) return [];
    return solutionsData.filter(
      (s) => s.projectId === id && s.mustCriteria?.some((m) => m.passed === true)
    );
  }, [id, solutionsData]);

  const handleAiBlackhat = async () => {
    setAiLoading(p => ({ ...p, blackhat: true }));
    try {
      const solutionNames = candidateSolutions.map((s) => s.name).join(', ');
      const result = await socraticGenerate({
        project_id: id || "",
        mission: `設計審查黑帽質疑：針對方案 [${solutionNames}] 提出最嚴厲的技術質疑`,
        constraints: candidateSolutions.map((s) => s.mechanism || s.name),
      });
      const questions = result.questions.map((q) => q.text);
      setBlackhatQuestions(questions.length > 0 ? questions : [
        '磁力耦合器在高溫環境下（>80°C）是否存在退磁風險？目前的驗證是否涵蓋極端工況？',
        '傳動效率目標是否考慮了磨合期效率衰減？長期效率數據如何驗證？',
      ]);
      toast.success(`AI 已生成 ${questions.length} 項黑帽質疑`);
    } catch {
      setBlackhatQuestions([
        '磁力耦合器在高溫環境下（>80°C）是否存在退磁風險？目前的驗證是否涵蓋極端工況？',
        '碳纖維蜂巢殼體的疲勞壽命數據是否基於實際測試？靜態 FEA 是否足以代表動態負載？',
        '傳動效率 92% 的目標是否考慮了磨合期效率衰減？長期效率數據如何驗證？',
      ]);
      toast.warning('AI 黑帽質疑失敗，已使用預設問題');
    } finally {
      setAiLoading(p => ({ ...p, blackhat: false }));
    }
  };

  // Fetch attachments from DB
  const fetchAttachments = useCallback(async () => {
    if (!id) return;
    const { data, error } = await supabase
      .from("review_attachments")
      .select("*")
      .eq("project_id", id)
      .order("created_at", { ascending: false });
    if (!error && data) setAttachments(data);
  }, [id]);

  useEffect(() => { fetchAttachments(); }, [fetchAttachments]);

  // --- Evidence Matrix helpers ---
  const gapCount = useMemo(() => evidenceRows.filter(r => r.currentLevel === 'E0' || r.currentLevel === 'E1').length, [evidenceRows]);
  const hasGap = gapCount > 0;

  const levelIndex = (l: EvidenceLevel) => EVIDENCE_LEVELS.findIndex(e => e.value === l);

  // --- Risk helpers ---
  const addRisk = () => {
    if (!id) return;
    createRiskMut.mutate({
      project_id: id,
      description: '',
      failure_mode: '',
      probability: 1,
      severity: 1,
      mitigation: '',
    });
  };

  // Field name mapping: camelCase frontend -> snake_case DB
  const riskFieldMap: Record<string, string> = {
    failureMode: 'failure_mode',
    description: 'description',
    probability: 'probability',
    severity: 'severity',
    mitigation: 'mitigation',
  };

  const updateRisk = (rId: string, field: keyof RiskItem, value: string | number) => {
    const dbField = riskFieldMap[field] ?? field;
    updateRiskMut.mutate({ id: rId, [dbField]: value });
  };

  const deleteRisk = (rId: string) => {
    deleteRiskMut.mutate({ id: rId });
  };

  const highRisksWithoutMitigation = useMemo(() =>
    risks.filter(r => {
      const level = getRiskLevel(getRiskScore(r));
      return (level === 'H' || level === 'H*') && !r.mitigation.trim();
    }).length
  , [risks]);

  // --- Experiment helpers ---
  const openNewExp = () => {
    setEditingExp({
      id: '', // will be generated by DB
      name: '', linkedAssumptions: [], evidenceLevel: 'E1',
      method: '', successCriteria: '', status: 'Plan', result: '',
    });
    setExpModalOpen(true);
  };

  const saveExp = () => {
    if (!editingExp || !id) return;
    if (!editingExp.name || editingExp.name.length < 3) { toast.error("實驗名稱至少 3 字元"); return; }
    if (editingExp.status === 'Done' && editingExp.result.length < 10) { toast.error("已完成實驗需填寫結果 (≥10 字元)"); return; }

    const isNew = !editingExp.id || !experiments.find(e => e.id === editingExp.id);
    if (isNew) {
      createExperimentMut.mutate({
        project_id: id,
        name: editingExp.name,
        linked_assumptions: editingExp.linkedAssumptions,
        evidence_level: editingExp.evidenceLevel,
        method: editingExp.method,
        success_criteria: editingExp.successCriteria,
        status: editingExp.status,
        result: editingExp.result,
      });
    } else {
      updateExperimentMut.mutate({
        id: editingExp.id,
        name: editingExp.name,
        linked_assumptions: editingExp.linkedAssumptions,
        evidence_level: editingExp.evidenceLevel,
        method: editingExp.method,
        success_criteria: editingExp.successCriteria,
        status: editingExp.status,
        result: editingExp.result,
      });
      // If experiment is Done, update linked evidence rows
      if (editingExp.status === 'Done') {
        evidenceRows.forEach(row => {
          if (editingExp.linkedAssumptions.includes(row.assumptionCode)) {
            const newLevel = levelIndex(editingExp.evidenceLevel) > levelIndex(row.currentLevel) ? editingExp.evidenceLevel : row.currentLevel;
            if (newLevel !== row.currentLevel) {
              // Find the evidence row's DB id by assumption_code — use the update hook
              // Note: We need the DB id; evidence rows from the query don't expose id directly.
              // For now, update via the evidence_matrix query refetch triggered by experiments invalidation.
            }
          }
        });
      }
    }
    setExpModalOpen(false);
    setEditingExp(null);
  };

  const deleteExperiment = (expId: string) => {
    // Use update to mark deleted or just remove — experiments table has no soft delete,
    // so we rely on the mutation pattern. For now, update status or use a dedicated delete.
    // Since useDeleteExperiment is not defined, we log a toast for now.
    toast.info("實驗刪除功能將在後續版本支援");
  };

  // --- Gate V1 — with North Star KPI + MUST revalidation (WBS 4.3/H7/H8) ---
  const northStarKPIs = evidenceRows.filter(r => r.isNorthStar === true);
  const northStarAllE2Plus = northStarKPIs.length > 0 && northStarKPIs.every(r => {
    const lvl = r.currentLevel;
    return lvl === 'E2' || lvl === 'E3' || lvl === 'E4';
  });
  const allEvidenceAboveE0 = evidenceRows.length > 0 && evidenceRows.every(r => r.currentLevel !== 'E0');

  const gate31Items: Gate31Item[] = useMemo(() => [
    { label: '證據矩陣已建立 (≥1 假設有實驗)', passed: evidenceRows.some(r => r.experiments.length > 0) || experiments.length > 0 },
    { label: '所有 H*/H 風險有 mitigation', passed: highRisksWithoutMitigation === 0 },
    { label: 'North Star KPI 皆達 ≥ E2 證據等級', passed: northStarAllE2Plus },
    { label: 'MUST 已以 E2+ 證據重新驗證（無 E0）', passed: allEvidenceAboveE0 },
  ], [evidenceRows, experiments, highRisksWithoutMitigation, northStarAllE2Plus, allEvidenceAboveE0]);

  const gate31Passed = gate31Items.every(i => i.passed);

  // --- AI mock actions ---
  const handleAiRisk = async () => {
    if (!id) return;
    setAiLoading(p => ({ ...p, risk: true }));
    await new Promise(r => setTimeout(r, 1800));
    createRiskMut.mutate({
      project_id: id,
      description: '磁力耦合器軸向間隙變化導致效率波動',
      failure_mode: '效率降至 <85%，低於設計目標',
      probability: 3, severity: 4, mitigation: '',
    });
    setAiLoading(p => ({ ...p, risk: false }));
    toast.success("AI 已識別 1 項潛在風險");
  };

  const handleAiExp = async () => {
    if (!id) return;
    setAiLoading(p => ({ ...p, exp: true }));
    await new Promise(r => setTimeout(r, 1800));
    const gapAssumptions = evidenceRows.filter(r => r.currentLevel === 'E0' || r.currentLevel === 'E1');
    if (gapAssumptions.length === 0) {
      toast.info("無證據缺口，不需要新增實驗");
      setAiLoading(p => ({ ...p, exp: false }));
      return;
    }
    const target = gapAssumptions[0];
    createExperimentMut.mutate({
      project_id: id,
      name: `驗證 ${target.summary.slice(0, 20)}`,
      linked_assumptions: [target.assumptionCode],
      evidence_level: 'E2',
      method: 'FEA 仿真分析',
      success_criteria: '指標達成設計目標',
      status: 'Plan',
      result: '',
    });
    setAiLoading(p => ({ ...p, exp: false }));
    toast.success("AI 已建議 1 項實驗");
  };

  // P x S matrix renderer
  const renderPSMatrix = () => {
    const grid: Record<string, string[]> = {};
    risks.forEach(r => {
      const key = `${r.probability}-${r.severity}`;
      if (!grid[key]) grid[key] = [];
      grid[key].push(r.id);
    });

    return (
      <div className="overflow-x-auto">
        <table className="border-collapse text-xs">
          <thead>
            <tr>
              <th className="p-1 text-muted-foreground">P＼S</th>
              {[1,2,3,4,5].map(s => <th key={s} className="p-1 w-12 text-center text-muted-foreground">{s}</th>)}
            </tr>
          </thead>
          <tbody>
            {[5,4,3,2,1].map(p => (
              <tr key={p}>
                <td className="p-1 font-medium text-muted-foreground text-center">{p}</td>
                {[1,2,3,4,5].map(s => {
                  const score = p * s;
                  const level = getRiskLevel(score);
                  const color = getRiskColor(level);
                  const ids = grid[`${p}-${s}`] || [];
                  return (
                    <td key={s} className="p-0.5">
                      <div className="w-12 h-10 rounded flex items-center justify-center text-[10px] font-medium text-white"
                        style={{ backgroundColor: color, opacity: ids.length > 0 ? 1 : 0.25 }}>
                        {ids.length > 0 ? ids.join(', ') : ''}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Data source info banner
  const renderDataSourceBanner = () => (
    <Card className="bg-muted/30 border-dashed">
      <CardContent className="p-3 flex items-center gap-3 text-xs text-muted-foreground">
        <Link2 className="h-4 w-4 shrink-0" />
        <div>
          <span className="font-medium text-foreground">資料來源：</span>
          <span> 證據矩陣（{evidenceRows.length} 項假設），風險登錄（{risks.length} 項），實驗（{experiments.length} 項）。</span>
          <Button variant="link" size="sm" className="text-xs h-auto p-0 ml-2" onClick={() => navigate(`/projects/${id}/track`)}>
            前往 Track →
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  // --- Loading / Error states ---
  if (isLoading) {
    return (
      <div className="page-shell-medium flex items-center justify-center py-24 gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="text-muted-foreground">載入設計審查資料中...</span>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="page-shell-medium flex flex-col items-center justify-center py-24 gap-3">
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-destructive">載入失敗：{loadError.message}</p>
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>重新載入</Button>
      </div>
    );
  }

  return (
    <div className="page-shell-medium">
      {/* Phase header */}
      <div className="h-1 w-full rounded-full bg-primary" />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${id}`)} className="text-muted-foreground -ml-2">
            <ArrowLeft className="h-4 w-4 mr-1" /> 返回
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Review — 設計審查
              <HelpTooltip text="此階段審查 CAD 完成後的設計方案。證據矩陣來自 Track 假設追蹤，風險登錄從高風險假設衍生，最小實驗驗證關鍵假設。" className="ml-2 align-middle" />
            </h1>
            <p className="text-sm text-muted-foreground">Phase 3: Converge &gt; V1（CAD 完成後）</p>
          </div>
        </div>
      </div>

      {/* Purpose intro */}
      <SectionIntro text="RD 完成 CAD 建模後，在此審查設計證據。證據矩陣連結自 Track 假設、風險從高風險假設衍生、實驗從 Track 同步。" />

      {/* Section 1: Candidate Solutions List */}
      <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-sm font-semibold">審查方案列表</h3>
            <Badge variant="outline" className="text-xs">{candidateSolutions.length} 方案</Badge>
          </div>
          {candidateSolutions.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">沒有審查方案，請先完成 Pre-CAD 審查。</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {candidateSolutions.map((sol: any) => (
                <div key={sol.id} className="rounded-lg border p-3 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium line-clamp-1">{sol.name}</p>
                    <div className="flex gap-1 shrink-0">
                      {sol.mustCriteria?.map((m: any) => (
                        <span key={m.id}>
                          {m.passed === true ? <CheckCircle className="h-3 w-3 text-primary" /> : m.passed === false ? <XCircle className="h-3 w-3 text-destructive" /> : <span className="text-muted-foreground text-xs">—</span>}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{sol.description}</p>
                  <div className="space-y-1">
                    <Label className="text-xs">方案去向</Label>
                    <Select
                      value={dispositions[sol.id] || ""}
                      onValueChange={(v) => setDispositions((prev) => ({ ...prev, [sol.id]: v }))}
                    >
                      <SelectTrigger className="h-7 text-xs">
                        <SelectValue placeholder="選擇去向" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="approve">批准</SelectItem>
                        <SelectItem value="revise">修訂</SelectItem>
                        <SelectItem value="eliminate">淘汰</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Black Hat Questioning (P1) */}
      <Card className="border-destructive/20 bg-destructive/5">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-destructive" />
            <span className="text-sm font-semibold">AI 黑帽質疑</span>
            <Badge variant="secondary" className="text-[10px]">AI</Badge>
            <HelpTooltip text="AI 自動從設計方案中找出潛在弱點與盲點，模擬黑帽思維進行質疑。" />
          </div>
          {aiLoading.blackhat ? (
            <div className="flex items-center gap-2 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">AI 正在分析設計弱點...</span>
            </div>
          ) : blackhatQuestions.length > 0 ? (
            <div className="space-y-2">
              {blackhatQuestions.map((q, i) => (
                <div key={i} className="flex items-start gap-2 p-2 rounded-md border bg-background">
                  <span className="text-destructive text-xs font-bold mt-0.5">Q{i + 1}</span>
                  <p className="text-sm flex-1">{q}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">尚未生成質疑，請點擊下方按鈕。</p>
          )}
          <AiButton size="sm" aiVariant="outline" loading={aiLoading.blackhat} onClick={handleAiBlackhat}>
            黑帽質疑
          </AiButton>
        </CardContent>
      </Card>

      {/* AI Evidence Gap Detection (P1) */}
      {hasGap && (
        <Card className="border-accent/20 bg-accent/5">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-accent" />
              <span className="text-sm font-semibold">AI 證據缺口分析</span>
              <Badge variant="secondary" className="text-[10px]">AI</Badge>
            </div>
            <div className="space-y-1.5">
              {evidenceRows.filter(r => r.currentLevel === 'E0' || r.currentLevel === 'E1').map(r => (
                <div key={r.assumptionCode} className="flex items-center gap-2 text-xs p-1.5 rounded bg-background border">
                  <Badge variant="outline" className="text-[10px]">{r.assumptionCode}</Badge>
                  <span className="text-muted-foreground flex-1 truncate">{r.summary}</span>
                  <Badge className="text-[10px] bg-accent text-accent-foreground">{r.currentLevel}</Badge>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              建議：為上述 {gapCount} 項假設規劃最小實驗，提升證據等級至 E2 以上。
            </p>
            <Button size="sm" variant="outline" onClick={() => setActiveTab('experiment')}>
              <Beaker className="h-3 w-3 mr-1" /> 前往規劃實驗
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Data source banner */}
      {renderDataSourceBanner()}

      {/* 4 Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full grid grid-cols-4">
          <TabsTrigger value="evidence" className="text-xs sm:text-sm">
            <BarChart3 className="h-3.5 w-3.5 mr-1 hidden sm:inline-block" /> 證據矩陣
          </TabsTrigger>
          <TabsTrigger value="risk" className="text-xs sm:text-sm">
            <ShieldAlert className="h-3.5 w-3.5 mr-1 hidden sm:inline-block" /> 風險登錄
          </TabsTrigger>
          <TabsTrigger value="experiment" className="text-xs sm:text-sm">
            <Beaker className="h-3.5 w-3.5 mr-1 hidden sm:inline-block" /> 最小實驗
            {hasGap && <AlertTriangle className="h-3 w-3 ml-1 text-amber-500" />}
          </TabsTrigger>
          <TabsTrigger value="attachments" className="text-xs sm:text-sm">
            <Paperclip className="h-3.5 w-3.5 mr-1 hidden sm:inline-block" /> 附件
            {attachments.length > 0 && <Badge variant="secondary" className="text-[9px] ml-1">{attachments.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Evidence Matrix */}
        <TabsContent value="evidence" className="space-y-4 mt-4">
          {evidenceRows.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-muted-foreground">
              <p>尚無數據，請先在 Track 頁建立假設</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => navigate(`/projects/${id}/track`)}>前往 Track</Button>
            </CardContent></Card>
          ) : (
            <>
              {/* Evidence source badges */}
              <div className="flex flex-wrap gap-2">
                {evidenceRows.slice(0, 4).map((row) => (
                  <Badge key={row.assumptionCode} variant="outline" className="text-[10px] gap-1">
                    {row.assumptionCode}
                    {row.isNorthStar && <Flag className="h-2.5 w-2.5 text-primary" />}
                  </Badge>
                ))}
                {evidenceRows.length > 4 && (
                  <Badge variant="outline" className="text-[10px]">+{evidenceRows.length - 4} 更多</Badge>
                )}
              </div>

              {/* Desktop heatmap table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground w-[200px]">假設</th>
                      {EVIDENCE_LEVELS.map(l => (
                        <th key={l.value} className="text-center py-2 px-2 text-xs font-medium text-muted-foreground w-16">{l.value}<br/><span className="text-[10px]">{l.label}</span></th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceRows.map(row => {
                      return (
                        <tr key={row.assumptionCode} className="border-b hover:bg-muted/30">
                          <td className="py-2 px-3">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="text-xs">
                                  <span className="font-medium">{row.assumptionCode}</span>
                                  {row.isNorthStar && (
                                    <Badge variant="outline" className="text-[8px] ml-1 py-0 border-primary text-primary">
                                      NS
                                    </Badge>
                                  )}
                                  {" "}{row.summary.length > 30 ? row.summary.slice(0, 30) + '...' : row.summary}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent><p className="max-w-xs text-xs">{row.summary}</p></TooltipContent>
                            </Tooltip>
                          </td>
                          {EVIDENCE_LEVELS.map((l) => {
                            const isCurrent = l.value === row.currentLevel;
                            const hasExp = row.experiments.some(e => e.level === l.value);
                            return (
                              <td key={l.value} className="text-center py-2 px-2">
                                {isCurrent ? (
                                  <div className="w-6 h-6 rounded-full mx-auto" style={{ backgroundColor: l.color }}
                                    title={`${l.value} ${l.label}`} />
                                ) : hasExp ? (
                                  <div className="w-3 h-3 rounded-full mx-auto border-2" style={{ borderColor: l.color }} />
                                ) : null}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3">
                {evidenceRows.map(row => {
                  const li = levelIndex(row.currentLevel);
                  return (
                    <Card key={row.assumptionCode}>
                      <CardContent className="p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">{row.assumptionCode}</span>
                          <Badge style={{ backgroundColor: EVIDENCE_LEVELS[li]?.color, color: '#fff' }} className="text-[10px]">{row.currentLevel}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{row.summary}</p>
                        <div className="flex gap-0.5">
                          {EVIDENCE_LEVELS.map((l, i) => (
                            <div key={l.value} className="flex-1 h-2 rounded-sm" style={{ backgroundColor: i <= li ? l.color : 'hsl(var(--muted))' }} />
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {/* Gap summary */}
              <div className={`rounded-lg p-3 text-sm flex items-center gap-2 ${hasGap ? 'bg-accent/10 border border-accent/30' : 'bg-primary/10 border border-primary/30'}`}>
                {hasGap ? (
                  <><AlertTriangle className="h-4 w-4 text-accent shrink-0" /><span>{gapCount} 項假設仍處於 E0/E1，存在證據缺口</span></>
                ) : (
                  <><CheckCircle className="h-4 w-4 text-primary shrink-0" /><span>所有假設已有充足證據</span></>
                )}
              </div>
            </>
          )}
        </TabsContent>

        {/* Tab 2: Risk Register */}
        <TabsContent value="risk" className="space-y-4 mt-4">
          {/* Source note */}
          <p className="text-xs text-muted-foreground">
            風險來源：Track 假設中風險等級為 H/H* 的假設自動帶入，可手動新增或 AI 識別。
          </p>

          {/* P x S matrix */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="shrink-0">
              <p className="text-xs font-medium text-muted-foreground mb-2">P × S 風險矩陣</p>
              {renderPSMatrix()}
            </div>

            {/* Risk table (desktop) */}
            <div className="flex-1 hidden md:block overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 text-xs text-muted-foreground">ID</th>
                    <th className="text-left py-2 px-2 text-xs text-muted-foreground">描述 *</th>
                    <th className="text-left py-2 px-2 text-xs text-muted-foreground">失效模式 *</th>
                    <th className="text-center py-2 px-2 text-xs text-muted-foreground">P *</th>
                    <th className="text-center py-2 px-2 text-xs text-muted-foreground">S *</th>
                    <th className="text-center py-2 px-2 text-xs text-muted-foreground">RPN</th>
                    <th className="text-left py-2 px-2 text-xs text-muted-foreground">緩解措施</th>
                    <th className="text-center py-2 px-2 text-xs text-muted-foreground w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {risks.map(r => {
                    const score = getRiskScore(r);
                    const level = getRiskLevel(score);
                    const color = getRiskColor(level);
                    const needsMitigation = (level === 'H' || level === 'H*') && !r.mitigation.trim();
                    return (
                      <tr key={r.id} className={`border-b ${needsMitigation ? 'bg-destructive/5' : ''}`}>
                        <td className="py-1.5 px-2 text-xs font-medium">{r.id}</td>
                        <td className="py-1.5 px-2"><Input value={r.description} onChange={e => updateRisk(r.id, 'description', e.target.value)} className="text-xs h-7" /></td>
                        <td className="py-1.5 px-2"><Input value={r.failureMode} onChange={e => updateRisk(r.id, 'failureMode', e.target.value)} className="text-xs h-7" /></td>
                        <td className="py-1.5 px-2">
                          <Select value={String(r.probability)} onValueChange={v => updateRisk(r.id, 'probability', parseInt(v))}>
                            <SelectTrigger className="text-xs h-7 w-14"><SelectValue /></SelectTrigger>
                            <SelectContent>{[1,2,3,4,5].map(n => <SelectItem key={n} value={String(n)}>{n}</SelectItem>)}</SelectContent>
                          </Select>
                        </td>
                        <td className="py-1.5 px-2">
                          <Select value={String(r.severity)} onValueChange={v => updateRisk(r.id, 'severity', parseInt(v))}>
                            <SelectTrigger className="text-xs h-7 w-14"><SelectValue /></SelectTrigger>
                            <SelectContent>{[1,2,3,4,5].map(n => <SelectItem key={n} value={String(n)}>{n}</SelectItem>)}</SelectContent>
                          </Select>
                        </td>
                        <td className="py-1.5 px-2 text-center">
                          <Badge style={{ backgroundColor: color, color: '#fff' }} className="text-[10px]">{score} ({level})</Badge>
                        </td>
                        <td className="py-1.5 px-2"><Input value={r.mitigation} onChange={e => updateRisk(r.id, 'mitigation', e.target.value)} className="text-xs h-7" placeholder={needsMitigation ? '⚠ 需填寫' : ''} /></td>
                        <td className="py-1.5 px-2 text-center">
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => deleteRisk(r.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile risk cards */}
          <div className="md:hidden space-y-3">
            {risks.map(r => {
              const score = getRiskScore(r);
              const level = getRiskLevel(score);
              const color = getRiskColor(level);
              const needsMitigation = (level === 'H' || level === 'H*') && !r.mitigation.trim();
              return (
                <Card key={r.id} className={needsMitigation ? 'border-destructive/40' : ''}>
                  <CardContent className="p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{r.id}</span>
                      <Badge style={{ backgroundColor: color, color: '#fff' }} className="text-[10px]">{score} ({level})</Badge>
                    </div>
                    <Input value={r.description} onChange={e => updateRisk(r.id, 'description', e.target.value)} className="text-xs h-7" placeholder="風險描述 *" />
                    <Input value={r.failureMode} onChange={e => updateRisk(r.id, 'failureMode', e.target.value)} className="text-xs h-7" placeholder="失效模式 *" />
                    <div className="flex gap-2">
                      <Select value={String(r.probability)} onValueChange={v => updateRisk(r.id, 'probability', parseInt(v))}>
                        <SelectTrigger className="text-xs h-7 flex-1"><SelectValue placeholder="P" /></SelectTrigger>
                        <SelectContent>{[1,2,3,4,5].map(n => <SelectItem key={n} value={String(n)}>P={n}</SelectItem>)}</SelectContent>
                      </Select>
                      <Select value={String(r.severity)} onValueChange={v => updateRisk(r.id, 'severity', parseInt(v))}>
                        <SelectTrigger className="text-xs h-7 flex-1"><SelectValue placeholder="S" /></SelectTrigger>
                        <SelectContent>{[1,2,3,4,5].map(n => <SelectItem key={n} value={String(n)}>S={n}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <Input value={r.mitigation} onChange={e => updateRisk(r.id, 'mitigation', e.target.value)} className="text-xs h-7" placeholder={needsMitigation ? '⚠ 緩解措施 (必要)' : '緩解措施'} />
                    <Button variant="ghost" size="sm" className="text-xs h-6 text-destructive" onClick={() => deleteRisk(r.id)}>
                      <Trash2 className="h-3 w-3 mr-1" /> 刪除
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {risks.length === 0 && (
            <Card><CardContent className="py-8 text-center text-muted-foreground text-sm">
              尚無風險，建議使用 AI 識別潛在風險
            </CardContent></Card>
          )}

          <div className="flex gap-3">
            <Button size="sm" variant="secondary" onClick={addRisk}><Plus className="h-3 w-3 mr-1" /> 新增風險</Button>
            <AiButton size="sm" loading={aiLoading.risk} onClick={handleAiRisk}>
              識別風險
            </AiButton>
          </div>
        </TabsContent>

        {/* Tab 3: Minimum Experiments */}
        <TabsContent value="experiment" className="space-y-4 mt-4">
          {/* Source note */}
          <p className="text-xs text-muted-foreground">
            實驗資料來源：Track 假設追蹤中已建立的實驗自動同步至此，可在此新增額外實驗。
          </p>

          {experiments.length === 0 ? (
            <Card><CardContent className="py-8 text-center text-muted-foreground text-sm">
              尚無實驗，查看證據矩陣確認缺口後規劃實驗
            </CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {experiments.map(exp => (
                <Card key={exp.id} className={`${exp.status === 'Done' ? 'border-l-[3px] border-l-primary' : ''}`}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">{exp.id}</span>
                      <div className="flex gap-1.5">
                        <Badge style={{ backgroundColor: EVIDENCE_LEVELS.find(l => l.value === exp.evidenceLevel)?.color, color: '#fff' }} className="text-[10px]">{exp.evidenceLevel}</Badge>
                        <Badge style={{ backgroundColor: EXP_STATUS_COLOR[exp.status], color: '#fff' }} className="text-[10px]">{exp.status === 'Plan' ? '計畫' : exp.status === 'Running' ? '執行中' : '已完成'}</Badge>
                      </div>
                    </div>
                    <p className="text-sm font-medium">{exp.name}</p>
                    {exp.linkedAssumptions.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {exp.linkedAssumptions.map(a => <Badge key={a} variant="outline" className="text-[10px]">{a}</Badge>)}
                      </div>
                    )}
                    {exp.method && <p className="text-xs text-muted-foreground">方法: {exp.method}</p>}
                    {exp.successCriteria && <p className="text-xs text-muted-foreground">成功標準: {exp.successCriteria}</p>}
                    {exp.status === 'Done' && exp.result && (
                      <p className="text-xs bg-primary/5 p-2 rounded">結果: {exp.result}</p>
                    )}
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" className="text-xs h-6" onClick={() => { setEditingExp({...exp}); setExpModalOpen(true); }}>
                        編輯
                      </Button>
                      <Button variant="ghost" size="sm" className="text-xs h-6 text-destructive" onClick={() => deleteExperiment(exp.id)}>
                        <Trash2 className="h-3 w-3 mr-1" /> 刪除
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <Button size="sm" variant="secondary" onClick={openNewExp}><Plus className="h-3 w-3 mr-1" /> 新增實驗</Button>
            <AiButton size="sm" loading={aiLoading.exp} onClick={handleAiExp}>
              建議實驗
            </AiButton>
          </div>
        </TabsContent>

        {/* Tab 4: Attachments */}
        <TabsContent value="attachments" className="space-y-4 mt-4">
          <p className="text-xs text-muted-foreground">
            上傳 CAD 圖檔、仿真報告、測試數據等文件作為設計審查的佐證附件。每份文件可加上概略描述。
          </p>
          <AttachmentsPanel
            projectId={id ?? ""}
            attachments={attachments}
            onRefresh={fetchAttachments}
          />
        </TabsContent>
      </Tabs>

      {/* Conclusion & Decision Section */}
      <Card className="rounded-lg" style={{ boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold">審查結論與決策</h3>
          </div>

          {/* Disposition summary */}
          {candidateSolutions.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground">方案去向摘要：</p>
              <div className="flex flex-wrap gap-1.5">
                {candidateSolutions.map((sol: any) => {
                  const d = dispositions[sol.id];
                  return (
                    <Badge
                      key={sol.id}
                      variant={d === "approve" ? "default" : d === "eliminate" ? "destructive" : "secondary"}
                      className="text-xs"
                    >
                      {sol.name?.slice(0, 15)}: {d === "approve" ? "批准" : d === "revise" ? "修訂" : d === "eliminate" ? "淘汰" : "未決定"}
                    </Badge>
                  );
                })}
              </div>
              {candidateSolutions.some((s: any) => !dispositions[s.id]) && (
                <p className="text-xs text-destructive">⚠ 尚有方案未選擇去向</p>
              )}
            </div>
          )}

          <div className="space-y-1.5">
            <Label className="text-sm">審查結論備註（選填）</Label>
            <Textarea
              value={reviewConclusion}
              onChange={(e) => setReviewConclusion(e.target.value)}
              placeholder="記錄審查會議的關鍵討論和決策原因..."
              maxLength={500}
              rows={3}
            />
          </div>

          <Button
            onClick={async () => {
              const allDecided = candidateSolutions.every((s: any) => dispositions[s.id]);
              if (!allDecided) {
                toast.error("請為所有方案選擇去向");
                return;
              }
              if (!gate31Passed) {
                toast.error("Gate V1 未通過，無法批准審查");
                return;
              }
              setIsSubmitting(true);
              await new Promise((r) => setTimeout(r, 1500));
              setIsSubmitting(false);
              toast.success("設計審查已批准，專案推進至下一階段");
              navigate(`/projects/${id}`);
            }}
            disabled={isSubmitting || !gate31Passed || candidateSolutions.some((s: any) => !dispositions[s.id])}
          >
            {isSubmitting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
            批准審查
          </Button>
        </CardContent>
      </Card>

      {/* Knowledge Enhancement Panel (WBS 3.4.2) */}
      <KnowledgeRefsPanel refs={mockPageKnowledgeRefs.review ?? []} />

      {/* Gate V1 */}
      <Separator />
      <Card className="border-2 border-primary/30 bg-primary/5">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Flag className="h-5 w-5 text-primary shrink-0" />
            <h3 className="text-sm font-semibold">Gate V1 — 設計審查完整性檢查</h3>
            <Badge className={gate31Passed ? "bg-primary text-primary-foreground" : "bg-destructive text-destructive-foreground"}>
              {gate31Passed ? 'Gate V1 Passed' : 'Gate V1 未通過'}
            </Badge>
          </div>
          <div className="space-y-2">
            {gate31Items.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {item.passed ? <CheckCircle className="h-4 w-4 text-primary shrink-0" /> : <XCircle className="h-4 w-4 text-destructive shrink-0" />}
                <span className={item.passed ? '' : 'text-muted-foreground'}>{item.label}</span>
              </div>
            ))}
          </div>
          {gate31Passed ? (
            <Button onClick={() => navigate(`/projects/${id}/decide`)}>
              通過 → 進入 Decide <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-block"><Button disabled className="opacity-50">進入 Decide → <ArrowRight className="h-4 w-4 ml-1" /></Button></span>
              </TooltipTrigger>
              <TooltipContent><p>請完成上方所有檢查項目</p></TooltipContent>
            </Tooltip>
          )}
        </CardContent>
      </Card>

      {/* Experiment Modal */}
      <Dialog open={expModalOpen} onOpenChange={o => { if (!o) { setExpModalOpen(false); setEditingExp(null); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>{editingExp?.id ? `${editingExp.id} — 編輯實驗` : '新增實驗'}</DialogTitle></DialogHeader>
          {editingExp && (
            <div className="space-y-3">
              <div className="space-y-1"><Label>實驗名稱 *</Label><Input value={editingExp.name} onChange={e => setEditingExp({...editingExp, name: e.target.value})} maxLength={100} /></div>
              <div className="space-y-1"><Label>關聯假設 *</Label><Input value={editingExp.linkedAssumptions.join(', ')} onChange={e => setEditingExp({...editingExp, linkedAssumptions: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} placeholder="A-001, A-002" /></div>
              <div className="space-y-1"><Label>目標證據等級</Label>
                <Select value={editingExp.evidenceLevel} onValueChange={v => setEditingExp({...editingExp, evidenceLevel: v as EvidenceLevel})}>
                  <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                  <SelectContent>{EVIDENCE_LEVELS.map(l => <SelectItem key={l.value} value={l.value}>{l.value} {l.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label>實驗方法</Label><Textarea value={editingExp.method} onChange={e => setEditingExp({...editingExp, method: e.target.value})} rows={2} maxLength={500} /></div>
              <div className="space-y-1"><Label>成功標準</Label><Input value={editingExp.successCriteria} onChange={e => setEditingExp({...editingExp, successCriteria: e.target.value})} maxLength={200} /></div>
              <div className="space-y-1"><Label>狀態</Label>
                <Select value={editingExp.status} onValueChange={v => setEditingExp({...editingExp, status: v as ExperimentStatus})}>
                  <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Plan">Plan</SelectItem>
                    <SelectItem value="Running">Running</SelectItem>
                    <SelectItem value="Done">Done</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {editingExp.status === 'Done' && (
                <div className="space-y-1"><Label>實驗結果 *</Label><Textarea value={editingExp.result} onChange={e => setEditingExp({...editingExp, result: e.target.value})} rows={3} maxLength={500} /></div>
              )}
              <div className="flex gap-2 pt-2">
                <Button onClick={saveExp}>儲存</Button>
                <Button variant="outline" onClick={() => { setExpModalOpen(false); setEditingExp(null); }}>取消</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
