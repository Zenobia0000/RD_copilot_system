import { useState, useMemo, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  ArrowLeft, ArrowRight, Plus, Loader2, Check,
  CheckCircle, XCircle, Flag, FileDown, FileJson,
  Trophy, Trash2, AlertTriangle, User, CalendarDays, ShieldAlert, TrendingUp
} from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { KnowledgeRefsPanel } from "@/components/create/KnowledgeRefsPanel";
// TODO: Replace with useKnowledgeRefs hook once knowledge_refs DB table is created (Sprint 5+)
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend
} from "recharts";
import type {
  WantCriterion, WantScore, KtDecision, Signature, ActionItem, DecideGateItem, SignatureStatus
} from "@/types/decisionRecord";
import { DEFAULT_WANT_TEMPLATE } from "@/types/decisionRecord";
import type { AdverseConsequence, ACProbability, ACSeverity } from "@/types/decisionRecord";
import { computeACLevel } from "@/types/decisionRecord";
import {
  useDecision,
  useUpsertDecision,
  useWantCriteria,
  useCreateWantCriterion,
  useUpdateWantCriterion,
  useDeleteWantCriterion,
  useWantScores,
  useUpsertWantScore,
  useAdverseConsequences,
  useSignatures,
  useCreateSignature,
  useUpdateSignature,
  useActionItems,
  useCreateActionItem,
  useUpdateActionItem,
  useDeleteActionItem,
  useRisks,
  usePreCadSolutions,
  usePreCadConvergenceStats,
  useAlternatives,
} from "@/hooks/api";

export default function DecisionRecord() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // ── API hooks ──
  const { data: alternativesData, isLoading: altLoading } = useAlternatives(id);
  const { data: preCadSolutions, isLoading: mustLoading } = usePreCadSolutions(id);
  const { data: convergenceStats, isLoading: convergenceLoading } = usePreCadConvergenceStats(id);
  const { data: risksData, isLoading: risksLoading } = useRisks(id);
  const { data: decisionData, isLoading: decisionLoading } = useDecision(id);
  const { data: criteriaData, isLoading: criteriaLoading } = useWantCriteria(id);
  const { data: scoresData, isLoading: scoresLoading } = useWantScores(id);
  const { data: acData, isLoading: acLoading } = useAdverseConsequences(id);
  const { data: signaturesData, isLoading: signaturesLoading } = useSignatures(id);
  const { data: actionItemsData, isLoading: actionItemsLoading } = useActionItems(id, decisionData?.id);

  const upsertDecision = useUpsertDecision();
  const createWantCriterion = useCreateWantCriterion();
  const updateWantCriterionMut = useUpdateWantCriterion();
  const deleteWantCriterionMut = useDeleteWantCriterion();
  const upsertWantScore = useUpsertWantScore();
  const createSignatureMut = useCreateSignature();
  const updateSignatureMut = useUpdateSignature();
  const createActionItemMut = useCreateActionItem();
  const updateActionItemMut = useUpdateActionItem();
  const deleteActionItemMut = useDeleteActionItem();

  // ── Derived data from hooks ──
  const alternatives = useMemo(() =>
    (alternativesData ?? []).map(a => ({ id: a.id, name: a.name })),
    [alternativesData]
  );

  // MUST results: derived from pre-cad solutions (alternatives with mustCriteria)
  const mustResults = useMemo(() => {
    if (!alternativesData) return [];
    return alternativesData.map(alt => {
      const mustCriteria = alt.mustScores ? Object.values(alt.mustScores) : [];
      const allPass = mustCriteria.length > 0 && mustCriteria.every(v => v === 'pass');
      const failedKey = mustCriteria.length > 0
        ? Object.entries(alt.mustScores ?? {}).find(([, v]) => v === 'fail')?.[0]
        : undefined;
      return {
        alternative: alt.name,
        passed: alt.overallPass ?? allPass,
        reason: (alt.overallPass ?? allPass) ? '所有 MUST 條件通過' : `未通過 ${failedKey ?? 'MUST 條件'}`,
      };
    });
  }, [alternativesData]);

  // Risk assessment: from useRisks hook
  const riskAssessment = useMemo(() => {
    if (!risksData) return [];
    return risksData.map(r => {
      const score = r.probability * r.severity;
      const level = score >= 20 ? '重大' : score >= 10 ? '中等' : '低';
      const sevLabel = r.severity >= 4 ? '高' : r.severity >= 2 ? '中' : '低';
      const probLabel = r.probability >= 4 ? '高' : r.probability >= 2 ? '中' : '低';
      return {
        id: r.id,
        description: r.description,
        severity: sevLabel,
        probability: probLabel,
        level,
        mitigation: r.mitigation,
        monitor: r.failureMode || '',
      };
    });
  }, [risksData]);

  // Convergence summary: from usePreCadConvergenceStats
  const convergenceSummary = useMemo(() => {
    if (!convergenceStats) {
      return { confidenceScore: 0, fatal: { resolved: 0, total: 0 }, major: { resolved: 0, total: 0 }, minor: { resolved: 0, total: 0 } };
    }
    return {
      confidenceScore: convergenceStats.confidenceScore,
      fatal: { resolved: convergenceStats.fatalResolved, total: convergenceStats.fatalTotal },
      major: { resolved: convergenceStats.majorResolved, total: convergenceStats.majorTotal },
      minor: { resolved: convergenceStats.minorResolved, total: convergenceStats.minorTotal },
    };
  }, [convergenceStats]);

  // ── Local state synced from hooks ──
  const [criteria, setCriteria] = useState<WantCriterion[]>([]);
  const [scores, setScores] = useState<WantScore[]>([]);
  const [decision, setDecision] = useState<KtDecision>({
    selectedAlternativeId: '',
    selectedAlternativeName: '',
    rationale: '',
    riskAcceptance: '',
    actionItems: [],
    decisionDate: new Date().toISOString().split('T')[0],
    status: 'draft',
  });
  const [decisionId, setDecisionId] = useState<string | undefined>();
  const [signatures, setSignatures] = useState<(Signature & { id?: string; decisionId?: string })[]>([]);
  const [exported, setExported] = useState(false);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [wantExpanded, setWantExpanded] = useState(false);
  const [adverseConsequences, setAdverseConsequences] = useState<AdverseConsequence[]>([]);

  // Sync hook data into local state
  useEffect(() => {
    if (criteriaData) setCriteria(criteriaData);
  }, [criteriaData]);

  useEffect(() => {
    if (scoresData) setScores(scoresData);
  }, [scoresData]);

  useEffect(() => {
    if (decisionData) {
      setDecisionId(decisionData.id);
      setDecision({
        selectedAlternativeId: decisionData.selectedAlternativeId,
        selectedAlternativeName: decisionData.selectedAlternativeName,
        rationale: decisionData.rationale,
        riskAcceptance: decisionData.riskAcceptance,
        actionItems: actionItemsData ?? [],
        decisionDate: decisionData.decisionDate,
        status: decisionData.status,
      });
    }
  }, [decisionData, actionItemsData]);

  useEffect(() => {
    if (signaturesData) setSignatures(signaturesData);
  }, [signaturesData]);

  useEffect(() => {
    if (acData) setAdverseConsequences(acData);
  }, [acData]);

  // Loading state
  const isPageLoading = altLoading || mustLoading || convergenceLoading || risksLoading ||
    decisionLoading || criteriaLoading || scoresLoading || acLoading || signaturesLoading || actionItemsLoading;

  // ── WANT helpers ──
  const calcWeightedTotal = useCallback((altScores: Record<string, number>) => {
    return criteria.reduce((sum, c) => sum + (altScores[c.id] || 0) * c.weight, 0);
  }, [criteria]);

  const rankedScores = useMemo(() => {
    const updated = scores.map(s => ({ ...s, weightedTotal: calcWeightedTotal(s.scores) }));
    return updated.sort((a, b) => b.weightedTotal - a.weightedTotal);
  }, [scores, calcWeightedTotal]);

  const topAlt = rankedScores[0];

  const updateScore = (altId: string, critId: string, value: number) => {
    setScores(prev => prev.map(s =>
      s.alternativeId === altId ? { ...s, scores: { ...s.scores, [critId]: Math.min(10, Math.max(1, value)) } } : s
    ));
  };

  const updateCriterion = (cId: string, field: keyof WantCriterion, value: string | number) => {
    setCriteria(prev => prev.map(c => c.id === cId ? { ...c, [field]: value } : c));
  };

  const addCriterion = () => {
    const newC: WantCriterion = { id: `w-${Date.now()}`, name: '', weight: 5, description: '' };
    setCriteria(prev => [...prev, newC]);
  };

  const removeCriterion = (cId: string) => {
    if (criteria.length <= 3) { toast.error("至少保留 3 項標準"); return; }
    setCriteria(prev => prev.filter(c => c.id !== cId));
  };

  const loadTemplate = () => {
    if (criteria.length > 0 && !confirm("將覆蓋現有條件，確定？")) return;
    const templated = DEFAULT_WANT_TEMPLATE.map((t, i) => ({ ...t, id: `wt-${i}` }));
    setCriteria(templated);
    setScores(prev => prev.map(s => ({
      ...s, scores: Object.fromEntries(templated.map(c => [c.id, s.scores[c.id] || 5]))
    })));
    toast.success("已載入標準模板 W1-W7");
  };

  // ── Decision helpers ──
  const updateDecision = (field: keyof KtDecision, value: string) => {
    setDecision(prev => ({ ...prev, [field]: value }));
  };

  const addAction = () => {
    const newA: ActionItem = { id: `act-${Date.now()}`, description: '', assignee: '', dueDate: '' };
    setDecision(prev => ({ ...prev, actionItems: [...prev.actionItems, newA] }));
  };

  const updateAction = (aId: string, field: keyof ActionItem, value: string) => {
    setDecision(prev => ({
      ...prev,
      actionItems: prev.actionItems.map(a => a.id === aId ? { ...a, [field]: value } : a),
    }));
  };

  const removeAction = (aId: string) => {
    setDecision(prev => ({ ...prev, actionItems: prev.actionItems.filter(a => a.id !== aId) }));
  };

  const confirmDecision = () => {
    if (!decision.selectedAlternativeId) { toast.error("請選擇方案"); return; }
    if (decision.rationale.length < 20) { toast.error("決策理由至少 20 字元"); return; }
    if (decision.actionItems.length === 0) { toast.error("至少 1 項行動計畫"); return; }
    setConfirmModalOpen(true);
  };

  const doConfirm = () => {
    setDecision(prev => ({ ...prev, status: 'confirmed' }));
    setConfirmModalOpen(false);
    toast.success("決策已確認");
  };

  const revertDraft = () => {
    setDecision(prev => ({ ...prev, status: 'draft' }));
    toast.info("已恢復為草稿");
  };

  // ── Export ──
  const handleExport = async (format: 'pdf' | 'json') => {
    setAiLoading(p => ({ ...p, [format]: true }));
    await new Promise(r => setTimeout(r, 1500));
    setAiLoading(p => ({ ...p, [format]: false }));
    setExported(true);
    toast.success(`${format.toUpperCase()} 已匯出`);
  };

  // ── Signature ──
  const addSignature = () => {
    setSignatures(prev => [...prev, { name: '', role: 'RD 工程師', status: 'pending', signedAt: null, note: '' }]);
  };

  const updateSignature = (idx: number, field: keyof Signature, value: string) => {
    setSignatures(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s));
  };

  const signSignature = (idx: number) => {
    setSignatures(prev => prev.map((s, i) =>
      i === idx ? { ...s, status: 'signed' as SignatureStatus, signedAt: new Date().toISOString() } : s
    ));
    toast.success("簽核完成");
  };

  const revertSignature = (idx: number) => {
    setSignatures(prev => prev.map((s, i) =>
      i === idx ? { ...s, status: 'pending' as SignatureStatus, signedAt: null } : s
    ));
  };

  const signedCount = signatures.filter(s => s.status === 'signed').length;

  // ── AI mock ──
  const handleAiAction = async () => {
    setAiLoading(p => ({ ...p, action: true }));
    await new Promise(r => setTimeout(r, 1800));
    const newActions: ActionItem[] = [
      { id: `act-ai-1-${Date.now()}`, description: '完成磁力耦合器熱退磁驗證實驗', assignee: '李工程師', dueDate: '2026-03-15' },
      { id: `act-ai-2-${Date.now()}`, description: '建立碳纖維殼體疲勞測試計畫', assignee: '張工程師', dueDate: '2026-03-20' },
    ];
    setDecision(prev => ({ ...prev, actionItems: [...prev.actionItems, ...newActions] }));
    setAiLoading(p => ({ ...p, action: false }));
    toast.success("AI 已建議 2 項行動");
  };

  // ── Gates ──
  const allScored = scores.every(s => criteria.every(c => s.scores[c.id] && s.scores[c.id] >= 1));

  const hasACAssessment = adverseConsequences.length > 0;
  const gate32Items: DecideGateItem[] = useMemo(() => [
    { label: 'WANT 評分已完成 (含 W7 驗證可行性)', passed: allScored && criteria.length >= 3 },
    { label: '負面後果 (AC) 已評估', passed: hasACAssessment },
    { label: '決策方案已選擇', passed: !!decision.selectedAlternativeId },
    { label: '決策理由已填寫 (≥20 字元)', passed: decision.rationale.length >= 20 },
    { label: '至少 1 項行動計畫', passed: decision.actionItems.length >= 1 },
  ], [allScored, criteria, decision, hasACAssessment]);

  const gate32Passed = gate32Items.every(i => i.passed);

  const phaseGate3Items: DecideGateItem[] = useMemo(() => [
    { label: 'Gate 3.2 已通過', passed: gate32Passed },
    { label: '決策已確認 (Confirmed)', passed: decision.status === 'confirmed' || decision.status === 'signed' },
    { label: '決策報告已匯出', passed: exported },
  ], [gate32Passed, decision.status, exported]);

  const phaseGate3Passed = phaseGate3Items.every(i => i.passed);
  const isLocked = decision.status === 'confirmed' || decision.status === 'signed';

  // Radar chart data
  const radarData = criteria.map(c => {
    const entry: Record<string, string | number> = { criterion: c.name.length > 6 ? c.name.slice(0, 6) : c.name };
    rankedScores.forEach(s => { entry[s.alternativeName] = s.scores[c.id] || 0; });
    return entry;
  });

  // Bar chart data
  const chartData = rankedScores.map((s, i) => ({
    name: s.alternativeName.length > 12 ? s.alternativeName.slice(0, 12) + '...' : s.alternativeName,
    total: s.weightedTotal,
    isTop: i === 0,
  }));

  const statusBadge = (status: string) => {
    if (status === 'confirmed') return <Badge className="bg-primary text-primary-foreground text-xs">已確認</Badge>;
    if (status === 'signed') return <Badge className="bg-accent text-accent-foreground text-xs">已簽核</Badge>;
    return <Badge variant="secondary" className="text-xs">草稿</Badge>;
  };

  if (isPageLoading) {
    return (
      <div className="page-shell-medium flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">載入決策記錄...</span>
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
              決策記錄
              <HelpTooltip text="完整記錄設計決策的過程、依據、結論和後續行動，確保決策可追溯和可解釋。" className="ml-2 align-middle" />
            </h1>
            <p className="text-sm text-muted-foreground">Phase 3: Converge &gt; Decide</p>
          </div>
        </div>
        {statusBadge(decision.status)}
      </div>

      <SectionIntro text="本頁整合 MUST/WANT 分析結果、風險評估與矛盾收斂狀態，記錄決策理由與行動項目，支援簽核與報告匯出。" />

      {/* ═══════════════════════════════════════════
          Section 1: 決策概覽區
          ═══════════════════════════════════════════ */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Flag className="h-4 w-4 text-primary" /> 決策概覽
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Decision statement */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">決策聲明</Label>
            {decision.selectedAlternativeId ? (
              <p className="text-lg font-semibold">
                選定方案：{decision.selectedAlternativeName || '—'}
              </p>
            ) : (
              <p className="text-muted-foreground text-sm italic">尚未選定方案，請在下方 KT 決策分析中完成選擇。</p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Decision maker */}
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground">決策者</p>
                <p className="text-sm font-medium">
                  {signatures.find(s => s.role === 'RD 主管')?.name || '待指定'}
                </p>
              </div>
            </div>
            {/* Decision date */}
            <div className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground">決策日期</p>
                <p className="text-sm font-medium">{decision.decisionDate || '—'}</p>
              </div>
            </div>
            {/* Status */}
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground">狀態</p>
                {statusBadge(decision.status)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ═══════════════════════════════════════════
          Section 2: KT 決策分析結果區
          ═══════════════════════════════════════════ */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Trophy className="h-5 w-5 text-primary" /> KT 決策分析結果
        </h2>

        {/* 2a: MUST 結果表格 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">MUST 結果 — 通過 / 淘汰</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>方案</TableHead>
                  <TableHead className="w-24 text-center">結果</TableHead>
                  <TableHead>原因</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mustResults.map((m, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium text-sm">{m.alternative}</TableCell>
                    <TableCell className="text-center">
                      {m.passed ? (
                        <Badge className="bg-primary/10 text-primary text-xs">通過</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-xs">淘汰</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{m.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* 2b: WANT 結果 (collapsible scoring + chart) */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">WANT 評分結果</CardTitle>
              <div className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={() => setWantExpanded(!wantExpanded)} className="text-xs">
                  {wantExpanded ? '收起評分表' : '展開評分表'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary bar chart always visible */}
            {rankedScores.some(s => s.weightedTotal > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="h-[160px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={120} />
                      <Bar dataKey="total" radius={[0, 4, 4, 0]}>
                        <LabelList dataKey="total" position="right" style={{ fontSize: 11, fontWeight: 600 }} />
                        {chartData.map((d, i) => (
                          <Cell key={i} fill={d.isTop ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground) / 0.3)'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {radarData.length > 0 && (
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="criterion" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis tick={{ fontSize: 9 }} domain={[0, 10]} />
                        {rankedScores.map((s, i) => (
                          <Radar key={s.alternativeId} name={s.alternativeName} dataKey={s.alternativeName}
                            stroke={i === 0 ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))'} fill={i === 0 ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))'} fillOpacity={0.15} />
                        ))}
                        <Legend wrapperStyle={{ fontSize: 10 }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            )}

            {topAlt && topAlt.weightedTotal > 0 && (
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-sm flex items-center gap-2">
                <Trophy className="h-4 w-4 text-primary shrink-0" />
                <span>推薦方案：<span className="font-semibold">{topAlt.alternativeName}</span> (總分: {topAlt.weightedTotal})</span>
              </div>
            )}

            {/* Expandable scoring table */}
            {wantExpanded && (
              <div className="space-y-3 pt-2 border-t">
                <div className="flex gap-3 flex-wrap">
                  <Button size="sm" variant="secondary" onClick={loadTemplate}>載入標準模板 (W1-W6)</Button>
                  <Button size="sm" variant="ghost" onClick={addCriterion}><Plus className="h-3 w-3 mr-1" /> 新增標準</Button>
                </div>

                {criteria.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-2 text-xs text-muted-foreground w-[160px]">條件</th>
                          <th className="text-center py-2 px-2 text-xs text-muted-foreground w-16">權重</th>
                          {alternatives.map(a => (
                            <th key={a.id} className="text-center py-2 px-2 text-xs text-muted-foreground min-w-[100px]">
                              {a.name.length > 10 ? a.name.slice(0, 10) + '...' : a.name}
                            </th>
                          ))}
                          <th className="w-10"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {criteria.map(c => (
                          <tr key={c.id} className="border-b">
                            <td className="py-1.5 px-2">
                              <Input value={c.name} onChange={e => updateCriterion(c.id, 'name', e.target.value)} className="text-xs h-7" maxLength={80} disabled={isLocked} />
                            </td>
                            <td className="py-1.5 px-2 text-center">
                              <Input type="number" min={1} max={10} value={c.weight} onChange={e => updateCriterion(c.id, 'weight', parseInt(e.target.value) || 1)} className="text-xs h-7 w-14 text-center mx-auto" disabled={isLocked} />
                            </td>
                            {alternatives.map(a => {
                              const sc = scores.find(s => s.alternativeId === a.id);
                              const raw = sc?.scores[c.id] || 0;
                              const weighted = raw * c.weight;
                              return (
                                <td key={a.id} className="py-1.5 px-2 text-center">
                                  <div className="flex items-center justify-center gap-1">
                                    <Input type="number" min={1} max={10} value={raw || ''} onChange={e => updateScore(a.id, c.id, parseInt(e.target.value) || 0)} className="text-xs h-7 w-12 text-center" disabled={isLocked} />
                                    <span className="text-[10px] text-muted-foreground">({weighted})</span>
                                  </div>
                                </td>
                              );
                            })}
                            <td className="py-1.5 px-1">
                              {!isLocked && (
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground" onClick={() => removeCriterion(c.id)}>
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                        <tr className="bg-muted/50 font-semibold border-t-2">
                          <td className="py-2 px-2 text-xs">加權總分</td>
                          <td></td>
                          {alternatives.map(a => {
                            const sc = rankedScores.find(s => s.alternativeId === a.id);
                            const isTop = sc?.alternativeId === topAlt?.alternativeId;
                            return (
                              <td key={a.id} className="py-2 px-2 text-center text-sm">
                                {sc?.weightedTotal || 0} {isTop && <span className="text-primary">*</span>}
                              </td>
                            );
                          })}
                          <td></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 2c: 風險評估表格 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-destructive" /> 風險評估
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-20">風險 ID</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead className="w-16 text-center">嚴重度</TableHead>
                    <TableHead className="w-16 text-center">機率</TableHead>
                    <TableHead className="w-16 text-center">等級</TableHead>
                    <TableHead>緩解措施</TableHead>
                    <TableHead>監控指標</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {riskAssessment.map(r => (
                    <TableRow key={r.id}>
                      <TableCell className="font-mono text-xs">{r.id}</TableCell>
                      <TableCell className="text-sm">{r.description}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={r.severity === '高' ? 'destructive' : 'secondary'} className="text-xs">{r.severity}</Badge>
                      </TableCell>
                      <TableCell className="text-center text-xs">{r.probability}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={r.level === '重大' ? 'destructive' : 'outline'} className="text-xs">{r.level}</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{r.mitigation}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{r.monitor}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* 2c-2: Adverse Consequences (AC) — WBS 3.3.3 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" /> 負面後果分析 (AC)
              <HelpTooltip text="KT 決策第三階段：評估各方案的潛在負面後果（Adverse Consequences），識別風險並擬定緩解措施。" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-20">AC ID</TableHead>
                    <TableHead className="w-32">方案</TableHead>
                    <TableHead>負面後果</TableHead>
                    <TableHead className="w-16 text-center">機率</TableHead>
                    <TableHead className="w-16 text-center">嚴重度</TableHead>
                    <TableHead className="w-16 text-center">等級</TableHead>
                    <TableHead>緩解措施</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {adverseConsequences.map(ac => {
                    const altName = alternatives.find(a => a.id === ac.alternativeId)?.name || ac.alternativeId;
                    const levelColor = ac.level === 'H*' || ac.level === 'H' ? 'destructive' : ac.level === 'M' ? 'secondary' : 'outline';
                    return (
                      <TableRow key={ac.id}>
                        <TableCell className="font-mono text-xs">{ac.id}</TableCell>
                        <TableCell className="text-xs">{altName.length > 15 ? altName.slice(0, 15) + '...' : altName}</TableCell>
                        <TableCell className="text-sm">{ac.description}</TableCell>
                        <TableCell className="text-center text-xs">{ac.probability === 'high' ? '高' : ac.probability === 'medium' ? '中' : '低'}</TableCell>
                        <TableCell className="text-center text-xs">{ac.severity === 'high' ? '高' : ac.severity === 'medium' ? '中' : '低'}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant={levelColor as "default" | "secondary" | "outline" | "destructive"} className="text-xs">{ac.level}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{ac.mitigation}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            {adverseConsequences.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">尚無負面後果評估</p>
            )}
          </CardContent>
        </Card>

        {/* 2d: 矛盾收斂摘要 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">矛盾收斂摘要</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="text-center p-3 rounded-lg bg-primary/5">
                <p className="text-2xl font-bold text-primary">{convergenceSummary.confidenceScore}%</p>
                <p className="text-xs text-muted-foreground">Confidence Score</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-destructive/5">
                <p className="text-lg font-semibold">{convergenceSummary.fatal.resolved}/{convergenceSummary.fatal.total}</p>
                <p className="text-xs text-muted-foreground">Fatal 已解決</p>
                <Progress value={(convergenceSummary.fatal.resolved / convergenceSummary.fatal.total) * 100} className="mt-1 h-1.5" />
              </div>
              <div className="text-center p-3 rounded-lg bg-orange-500/5">
                <p className="text-lg font-semibold">{convergenceSummary.major.resolved}/{convergenceSummary.major.total}</p>
                <p className="text-xs text-muted-foreground">Major 已解決</p>
                <Progress value={(convergenceSummary.major.resolved / convergenceSummary.major.total) * 100} className="mt-1 h-1.5" />
              </div>
              <div className="text-center p-3 rounded-lg bg-muted">
                <p className="text-lg font-semibold">{convergenceSummary.minor.resolved}/{convergenceSummary.minor.total}</p>
                <p className="text-xs text-muted-foreground">Minor 已解決</p>
                <Progress value={(convergenceSummary.minor.resolved / convergenceSummary.minor.total) * 100} className="mt-1 h-1.5" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ═══════════════════════════════════════════
          Section 3: 決策結論與行動區
          ═══════════════════════════════════════════ */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">決策結論與行動</h2>

        {/* 3a: 選定方案 + 備援 */}
        <Card className="border-l-4 border-l-primary">
          <CardContent className="p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>主路線（選定方案）*</Label>
                <Select value={decision.selectedAlternativeId} onValueChange={v => {
                  const alt = alternatives.find(a => a.id === v);
                  setDecision(prev => ({ ...prev, selectedAlternativeId: v, selectedAlternativeName: alt?.name || '' }));
                }} disabled={isLocked}>
                  <SelectTrigger><SelectValue placeholder="選擇方案" /></SelectTrigger>
                  <SelectContent>
                    {rankedScores.map((s, i) => (
                      <SelectItem key={s.alternativeId} value={s.alternativeId}>
                        {s.alternativeName} ({s.weightedTotal} 分) {i === 0 ? '*' : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>備援方案</Label>
                <Select disabled={isLocked}>
                  <SelectTrigger><SelectValue placeholder="選擇備援" /></SelectTrigger>
                  <SelectContent>
                    {rankedScores.filter(s => s.alternativeId !== decision.selectedAlternativeId).map(s => (
                      <SelectItem key={s.alternativeId} value={s.alternativeId}>
                        {s.alternativeName} ({s.weightedTotal} 分)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>決策日期 *</Label>
              <Input type="date" value={decision.decisionDate} onChange={e => updateDecision('decisionDate', e.target.value)} disabled={isLocked} className="w-40" />
            </div>

            <div className="space-y-2">
              <Label>選擇理由 * <span className="text-xs text-muted-foreground">(至少 20 字元)</span></Label>
              <Textarea value={decision.rationale} onChange={e => updateDecision('rationale', e.target.value)}
                disabled={isLocked} rows={4} maxLength={2000} placeholder="闡述選擇該方案的理由..." />
              <p className="text-[10px] text-muted-foreground text-right">{decision.rationale.length}/2000</p>
            </div>

            <div className="space-y-2">
              <Label>風險接受聲明</Label>
              <Textarea value={decision.riskAcceptance} onChange={e => updateDecision('riskAcceptance', e.target.value)}
                disabled={isLocked} rows={3} maxLength={1000} placeholder="確認已識別風險及其緩解措施..." />
            </div>
          </CardContent>
        </Card>

        {/* 3b: 行動項目列表 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">行動項目</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {decision.actionItems.length === 0 && (
              <p className="text-sm text-muted-foreground">尚無行動計畫</p>
            )}
            <Accordion type="single" collapsible className="space-y-2">
              {decision.actionItems.map((a, idx) => (
                <AccordionItem key={a.id} value={a.id} className="border rounded-lg px-3">
                  <AccordionTrigger className="text-sm py-2 hover:no-underline">
                    <span className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px]">{idx + 1}</Badge>
                      {a.description || '新行動項目'}
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-2 pb-3">
                    <Input placeholder="行動描述 *" value={a.description} onChange={e => updateAction(a.id, 'description', e.target.value)} disabled={isLocked} className="text-xs h-8" maxLength={100} />
                    <div className="flex gap-2">
                      <Input placeholder="負責人 *" value={a.assignee} onChange={e => updateAction(a.id, 'assignee', e.target.value)} disabled={isLocked} className="text-xs h-8 flex-1" maxLength={50} />
                      <Input type="date" value={a.dueDate} onChange={e => updateAction(a.id, 'dueDate', e.target.value)} disabled={isLocked} className="text-xs h-8 w-36" />
                    </div>
                    {!isLocked && (
                      <Button variant="ghost" size="sm" className="text-xs text-destructive" onClick={() => removeAction(a.id)}>
                        <Trash2 className="h-3 w-3 mr-1" /> 刪除
                      </Button>
                    )}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
            {!isLocked && (
              <div className="flex gap-3">
                <Button size="sm" variant="ghost" onClick={addAction}><Plus className="h-3 w-3 mr-1" /> 新增行動</Button>
                <AiButton size="sm" loading={aiLoading.action} onClick={handleAiAction}>
                  建議行動
                </AiButton>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 3c: 確認決策 */}
        <div className="flex gap-3">
          {!isLocked ? (
            <Button onClick={confirmDecision} className="bg-primary hover:bg-primary/90 text-primary-foreground">
              <Check className="h-4 w-4 mr-1" /> 確認決策
            </Button>
          ) : (
            <Button variant="outline" onClick={revertDraft}>回到草稿</Button>
          )}
        </div>

        {/* 3d: 匯出報告 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">匯出報告</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-3">
              <Tooltip>
                <TooltipTrigger asChild>
                  <span><Button onClick={() => handleExport('pdf')} disabled={!isLocked || aiLoading.pdf}>
                    {aiLoading.pdf ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <FileDown className="h-4 w-4 mr-1" />}
                    匯出 PDF
                  </Button></span>
                </TooltipTrigger>
                {!isLocked && <TooltipContent><p>請先確認決策</p></TooltipContent>}
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span><Button variant="secondary" onClick={() => handleExport('json')} disabled={!isLocked || aiLoading.json}>
                    {aiLoading.json ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <FileJson className="h-4 w-4 mr-1" />}
                    匯出 JSON
                  </Button></span>
                </TooltipTrigger>
                {!isLocked && <TooltipContent><p>請先確認決策</p></TooltipContent>}
              </Tooltip>
            </div>
            {exported && (
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-sm flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-primary" /> 報告已匯出
              </div>
            )}
          </CardContent>
        </Card>

        {/* 3e: 簽核區 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">審查人簽核</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {signatures.length === 0 && (
              <p className="text-sm text-muted-foreground">尚無簽核人</p>
            )}
            {signatures.map((s, idx) => (
              <div key={idx} className="flex flex-col sm:flex-row gap-2 border rounded-lg p-3">
                <div className="flex gap-2 flex-1">
                  <Input placeholder="姓名 *" value={s.name} onChange={e => updateSignature(idx, 'name', e.target.value)}
                    disabled={s.status === 'signed'} className="text-xs h-8 flex-1" maxLength={50} />
                  <Select value={s.role} onValueChange={v => updateSignature(idx, 'role', v)} disabled={s.status === 'signed'}>
                    <SelectTrigger className="text-xs h-8 w-32"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {['RD 工程師', 'RD 主管', 'PM', '品質工程師', '高階主管', '其他'].map(r => (
                        <SelectItem key={r} value={r}>{r}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  {s.status === 'signed' ? (
                    <>
                      <Badge className="bg-primary/10 text-primary text-[10px]"><Check className="h-3 w-3 mr-0.5" /> 已簽核</Badge>
                      <span className="text-[10px] text-muted-foreground">{s.signedAt ? new Date(s.signedAt).toLocaleDateString('zh-TW') : ''}</span>
                      <Button size="sm" variant="ghost" className="text-[10px] h-5 text-muted-foreground" onClick={() => revertSignature(idx)}>撤回</Button>
                    </>
                  ) : (
                    <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => signSignature(idx)}
                      disabled={!s.name || s.name.length < 2}>簽核</Button>
                  )}
                </div>
              </div>
            ))}
            <Button size="sm" variant="ghost" onClick={addSignature}><Plus className="h-3 w-3 mr-1" /> 新增簽核人</Button>
            {signatures.length > 0 && (
              <p className="text-xs text-muted-foreground">{signedCount}/{signatures.length} 已簽核</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Knowledge Enhancement Panel (WBS 3.4.2) */}
      {/* TODO: Replace with useKnowledgeRefs hook (Sprint 5+) */}
      <KnowledgeRefsPanel refs={[]} />

      {/* ═══════════════════════════════════════════
          Gate Checks
          ═══════════════════════════════════════════ */}
      <Separator />
      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-6 w-1 rounded-full bg-primary" />
          <h3 className="text-sm font-semibold">Gate 3.2 — 決策記錄完整性檢查</h3>
          <Badge className={`text-xs text-primary-foreground ${gate32Passed ? 'bg-primary' : 'bg-destructive'}`}>
            {gate32Passed ? 'Gate 3.2 Passed' : 'Gate 3.2 未通過'}
          </Badge>
        </div>
        <div className="space-y-2">
          {gate32Items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.passed ? <CheckCircle className="h-4 w-4 text-primary shrink-0" /> : <XCircle className="h-4 w-4 text-destructive shrink-0" />}
              <span className={item.passed ? '' : 'text-muted-foreground'}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border-2 border-primary bg-primary/5 p-4 space-y-3" style={{ borderStyle: 'double' }}>
        <div className="flex items-center gap-3">
          <Flag className="h-5 w-5 text-primary shrink-0" />
          <h3 className="text-sm font-semibold">Phase Gate 3 — Converge 階段完成檢查</h3>
          <Badge className={`text-xs text-primary-foreground ${phaseGate3Passed ? 'bg-primary' : 'bg-destructive'}`}>
            {phaseGate3Passed ? 'Phase 3 Passed *' : 'Phase 3 未通過'}
          </Badge>
        </div>
        <div className="space-y-2">
          {phaseGate3Items.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.passed ? <CheckCircle className="h-4 w-4 text-primary shrink-0" /> : <XCircle className="h-4 w-4 text-destructive shrink-0" />}
              <span className={item.passed ? '' : 'text-muted-foreground'}>{item.label}</span>
            </div>
          ))}
        </div>
        {phaseGate3Passed ? (
          <Button onClick={() => navigate(`/projects/${id}/feynman`)} className="bg-primary hover:bg-primary/90 text-primary-foreground text-base px-6 py-2">
            Phase Gate 3 通過 → 進入 Feynman 內化 <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block"><Button disabled className="opacity-50">專案完成 → <ArrowRight className="h-4 w-4 ml-1" /></Button></span>
            </TooltipTrigger>
            <TooltipContent><p>請完成所有條件</p></TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Confirm Modal */}
      <Dialog open={confirmModalOpen} onOpenChange={setConfirmModalOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>確認決策</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">確認後決策記錄將鎖定，是否繼續？</p>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmModalOpen(false)}>取消</Button>
            <Button onClick={doConfirm} className="bg-primary hover:bg-primary/90 text-primary-foreground">確認</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
