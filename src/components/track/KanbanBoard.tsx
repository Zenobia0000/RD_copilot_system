import { useState, useEffect, useMemo, DragEvent } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { toast } from "sonner";
import { Plus, ChevronDown, ChevronUp, FlaskConical, ClipboardEdit, Trash2, Pencil } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { EvidenceEntryDialog } from "@/components/evidence/EvidenceEntryDialog";
import { socraticGenerate } from "@/lib/api";
import type { TrackAssumption, VerificationStatus, RiskLevel, Experiment, ExperimentStatus } from "@/types/track";
import { VERIFICATION_STATUS_CONFIG, RISK_LEVEL_CONFIG, KANBAN_COLUMNS, EXPERIMENT_STATUS_CONFIG } from "@/types/track";
import { useTrackExperiments, useCreateTrackExperiment, useUpdateTrackExperiment, useDeleteTrackExperiment, useCreateTrackAssumption, useDeleteTrackAssumption } from "@/hooks/api/useTrack";
import { useEvidenceEntries, useDeleteEvidenceEntry, useUpdateEvidenceEntry } from "@/hooks/api/useEvidenceEntries";

interface KanbanBoardProps {
  assumptions: TrackAssumption[];
  onUpdateAssumptions: (assumptions: TrackAssumption[]) => void;
  projectId: string;
  constraints?: string[];
}

export function KanbanBoard({ assumptions, onUpdateAssumptions, projectId, constraints = [] }: KanbanBoardProps) {
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [selectedCard, setSelectedCard] = useState<TrackAssumption | null>(null);
  const [expandedAi, setExpandedAi] = useState<Set<string>>(new Set());
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<VerificationStatus | null>(null);

  // Experiment state
  const [newExpName, setNewExpName] = useState('');
  const [editingExpId, setEditingExpId] = useState<string | null>(null);
  const [editExpResult, setEditExpResult] = useState('');
  const [editExpStatus, setEditExpStatus] = useState<ExperimentStatus>('Plan');

  // New assumption form
  const [newDesc, setNewDesc] = useState('');
  const [newRisk, setNewRisk] = useState<RiskLevel | ''>('');

  // Evidence dialog state
  const [evidenceDialogOpen, setEvidenceDialogOpen] = useState(false);
  const [evidenceDefaultCodes, setEvidenceDefaultCodes] = useState<string[]>([]);

  // Evidence editing state — single nullable object to prevent stale state on card switch
  const [editingEvidence, setEditingEvidence] = useState<{
    id: string; title: string; measuredValue: string; notes: string;
  } | null>(null);

  // Mobile column selector
  const [mobileColumn, setMobileColumn] = useState<VerificationStatus>('unverified');

  // Delete confirmation state
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // DB mutation hooks
  const createAssumption = useCreateTrackAssumption(projectId);
  const deleteAssumption = useDeleteTrackAssumption(projectId);

  // Fetch experiments from Supabase for the selected card
  const selectedAssumptionCode = selectedCard?.assumptionCode;
  const experimentsQuery = useTrackExperiments(selectedAssumptionCode, projectId);
  const deleteExperiment = useDeleteTrackExperiment();
  const createExperiment = useCreateTrackExperiment();
  const updateExperiment = useUpdateTrackExperiment();

  // Fetch evidence entries for this project
  const { data: allEvidence } = useEvidenceEntries(projectId);
  const deleteEvidence = useDeleteEvidenceEntry();
  const updateEvidence = useUpdateEvidenceEntry();

  // Pre-computed evidence count map — O(1) lookup per card instead of O(n×m)
  const evidenceCountByCode = useMemo(() => {
    const map = new Map<string, number>();
    for (const e of allEvidence ?? []) {
      for (const code of e.linkedAssumptionCodes) {
        map.set(code, (map.get(code) ?? 0) + 1);
      }
    }
    return map;
  }, [allEvidence]);

  // Filter evidence linked to the selected assumption
  const selectedEvidence = useMemo(() => {
    if (!selectedCard || !allEvidence) return [];
    return allEvidence.filter((e) =>
      e.linkedAssumptionCodes.includes(selectedCard.assumptionCode)
    );
  }, [selectedCard, allEvidence]);

  // Reset all edit states when switching cards
  useEffect(() => {
    setEditingEvidence(null);
    setEditingExpId(null);
    setEditExpResult('');
    setEditExpStatus('Plan');
  }, [selectedCard?.id]);

  const filteredAssumptions = assumptions.filter((a) => {
    if (riskFilter !== 'all' && a.riskLevel !== riskFilter) return false;
    if (searchQuery && !a.description.includes(searchQuery) && !a.assumptionCode.includes(searchQuery)) return false;
    return true;
  });

  const getColumnAssumptions = (status: VerificationStatus) =>
    filteredAssumptions.filter((a) => a.verificationStatus === status);

  const handleMoveCard = (id: string, newStatus: VerificationStatus) => {
    onUpdateAssumptions(
      assumptions.map((a) =>
        a.id === id ? { ...a, verificationStatus: newStatus, updatedAt: new Date().toISOString() } : a
      )
    );
    toast.success(`假設已移至「${VERIFICATION_STATUS_CONFIG[newStatus].label}」`);
  };

  const handleAddAssumption = () => {
    if (newDesc.trim().length < 10) {
      toast.error('假設描述至少 10 個字元');
      return;
    }
    if (!newRisk) {
      toast.error('請選擇風險等級');
      return;
    }

    const code = `A-${String(assumptions.length + 1).padStart(3, '0')}`;
    const riskToSeverity: Record<RiskLevel, string> = {
      'L': 'low',
      'M': 'medium',
      'H': 'high',
      'H*': 'critical',
    };

    createAssumption.mutate(
      {
        project_id: projectId,
        code,
        content: newDesc.trim(),
        source_type: 'manual',
        worst_severity: riskToSeverity[newRisk],
        status: 'unverified',
        verification_stage: 'unplanned',
      },
      {
        onSuccess: () => {
          setAddModalOpen(false);
          setNewDesc('');
          setNewRisk('');
          toast.success('假設已新增至「未驗證」欄');
        },
      }
    );
  };

  const handleDeleteAssumption = (id: string) => {
    onUpdateAssumptions(assumptions.filter((a) => a.id !== id));
    if (selectedCard?.id === id) {
      setSelectedCard(null);
    }
    deleteAssumption.mutate({ id });
    setDeleteConfirmId(null);
  };

  const handleAiChallenge = async () => {
    setIsAiLoading(true);
    try {
      const unchallenged = assumptions.filter((a) => !a.aiChallenge && a.verificationStatus !== 'negated');
      const result = await socraticGenerate({
        project_id: projectId,
        mission: `針對以下假設生成挑戰性問題：\n${unchallenged.map((a) => `- ${a.description}`).join('\n')}`,
        constraints,
      });
      const challengeMap = new Map<number, string>();
      result.questions.forEach((q, i) => challengeMap.set(i, q.text));
      let challengeIdx = 0;
      const updated = assumptions.map((a) => {
        if (!a.aiChallenge && a.verificationStatus !== 'negated') {
          const challenge = challengeMap.get(challengeIdx) ?? `AI 質疑：「${a.description.slice(0, 20)}...」的依據是否充分？`;
          challengeIdx++;
          return { ...a, aiChallenge: challenge };
        }
        return a;
      });
      onUpdateAssumptions(updated);
      toast.success('AI 已對假設生成挑戰性問題');
    } catch {
      const updated = assumptions.map((a) => {
        if (!a.aiChallenge && a.verificationStatus !== 'negated') {
          return {
            ...a,
            aiChallenge: `AI 質疑：「${a.description.slice(0, 20)}...」的依據是否充分？若外部條件改變，此假設是否仍然成立？`,
          };
        }
        return a;
      });
      onUpdateAssumptions(updated);
      toast.warning('AI 質疑生成失敗，已使用預設問題');
    } finally {
      setIsAiLoading(false);
    }
  };

  const toggleAiExpand = (id: string) => {
    setExpandedAi((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // --- Evidence CRUD handlers ---
  const handleDeleteEvidence = (evidenceId: string) => {
    deleteEvidence.mutate({ id: evidenceId, projectId });
  };

  const handleStartEditEvidence = (ev: typeof selectedEvidence[number]) => {
    setEditingEvidence({
      id: ev.id,
      title: ev.title,
      measuredValue: ev.measuredValue,
      notes: ev.notes,
    });
  };

  const handleSaveEditEvidence = () => {
    if (!editingEvidence || !editingEvidence.title.trim() || !editingEvidence.measuredValue.trim()) {
      toast.error('標題與量測值不可為空');
      return;
    }
    updateEvidence.mutate({
      id: editingEvidence.id,
      projectId,
      title: editingEvidence.title.trim(),
      measuredValue: editingEvidence.measuredValue.trim(),
      notes: editingEvidence.notes.trim(),
    }, {
      onSuccess: () => {
        setEditingEvidence(null);
      },
    });
  };

  const handleCancelEditEvidence = () => {
    setEditingEvidence(null);
  };

  // --- Drag handlers ---
  const handleDragStart = (e: DragEvent, id: string) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverColumn(null);
  };

  const handleColumnDragOver = (e: DragEvent, status: VerificationStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverColumn(status);
  };

  const handleColumnDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleColumnDrop = (e: DragEvent, status: VerificationStatus) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('text/plain');
    if (id) {
      const assumption = assumptions.find((a) => a.id === id);
      if (assumption && assumption.verificationStatus !== status) {
        handleMoveCard(id, status);
      }
    }
    setDraggedId(null);
    setDragOverColumn(null);
  };

  const renderCard = (a: TrackAssumption) => {
    const riskConfig = a.riskLevel ? RISK_LEVEL_CONFIG[a.riskLevel] : null;
    const hasNoRisk = !a.riskLevel;
    const highRiskNoExp = (a.riskLevel === 'H' || a.riskLevel === 'H*') && a.experimentCount === 0;
    const isDragging = draggedId === a.id;

    // O(1) lookup from pre-computed map
    const evidenceCount = evidenceCountByCode.get(a.assumptionCode) ?? 0;

    return (
      <Card
        key={a.id}
        draggable
        onDragStart={(e) => handleDragStart(e, a.id)}
        onDragEnd={handleDragEnd}
        className={`cursor-grab active:cursor-grabbing transition-all hover:shadow-md ${hasNoRisk ? 'border-destructive border-2' : ''} ${isDragging ? 'opacity-40 scale-95' : ''}`}
        onClick={() => setSelectedCard(a)}
      >
        <CardContent className="p-3 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-[10px] font-mono">{a.assumptionCode}</Badge>
            {riskConfig && (
              <Badge className="text-[10px] text-white" style={{ backgroundColor: riskConfig.color }}>
                {riskConfig.label}
              </Badge>
            )}
            {hasNoRisk && (
              <Badge variant="destructive" className="text-[10px]">* 未設定</Badge>
            )}
            {a.source === 'ai_suggest' && (
              <Badge variant="secondary" className="text-[10px]">AI</Badge>
            )}     
            {a.source === 'unknown_convert' && (
              <Badge variant="secondary" className="text-[10px] bg-amber-500/15 text-amber-600">來自 U</Badge>
            )}

            {/* 刪除按鈕 */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeleteConfirmId(a.id);
              }}
              className="ml-auto p-1 rounded hover:bg-destructive/10 transition-colors"
              title="刪除此假設"
            >
              <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
            </button>
          </div>

          <p className="text-sm line-clamp-2">{a.description}</p>

          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={`text-[10px] ${highRiskNoExp ? 'border-destructive text-destructive' : ''}`}
            >
              <FlaskConical className="h-3 w-3 mr-0.5" />
              {a.experimentCount} exps
            </Badge>
            {evidenceCount > 0 && (
              <Badge variant="outline" className="text-[10px] border-green-500 text-green-600">
                <ClipboardEdit className="h-3 w-3 mr-0.5" />
                {evidenceCount} 證據
              </Badge>
            )}
          </div>

          {/* AI challenge sub-card */}
          {a.aiChallenge && (
            <div className="mt-1">
              <button
                className="w-full text-left"
                onClick={(e) => { e.stopPropagation(); toggleAiExpand(a.id); }}
              >
                <div className="bg-muted rounded px-2 py-1.5 text-xs flex items-center gap-1">
                  <Badge variant="secondary" className="text-[9px] shrink-0">AI</Badge>
                  {expandedAi.has(a.id) ? (
                    <ChevronUp className="h-3 w-3 ml-auto shrink-0" />
                  ) : (
                    <ChevronDown className="h-3 w-3 ml-auto shrink-0" />
                  )}
                </div>
              </button>
              {expandedAi.has(a.id) && (
                <div className="bg-muted rounded-b px-2 py-2 text-xs text-muted-foreground -mt-1">
                  {a.aiChallenge}
                </div>
              )}
            </div>
          )}

          {/* Move to column */}
          <div className="pt-1" onClick={(e) => e.stopPropagation()}>
            <Select
              value={a.verificationStatus}
              onValueChange={(v) => handleMoveCard(a.id, v as VerificationStatus)}
            >
              <SelectTrigger className="h-6 text-[10px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {KANBAN_COLUMNS.map((col) => (
                  <SelectItem key={col} value={col} className="text-xs">
                    {VERIFICATION_STATUS_CONFIG[col].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderColumn = (status: VerificationStatus) => {
    const config = VERIFICATION_STATUS_CONFIG[status];
    const cards = getColumnAssumptions(status);
    const isOver = dragOverColumn === status;

    return (
      <div key={status} className="flex-1 min-w-[220px]">
        <div className="rounded-t-lg overflow-hidden">
          <div className="h-1" style={{ backgroundColor: config.color }} />
          <div className="bg-muted/50 px-3 py-2 flex items-center justify-between">
            <span className="text-xs font-semibold">{config.label}</span>
            <Badge variant="secondary" className="text-[10px]">{cards.length}</Badge>
          </div>
        </div>
        <div
          className={`border border-t-0 rounded-b-lg min-h-[200px] p-2 space-y-2 transition-colors ${isOver ? 'bg-primary/5 border-primary/30' : 'bg-background'}`}
          onDragOver={(e) => handleColumnDragOver(e, status)}
          onDragLeave={handleColumnDragLeave}
          onDrop={(e) => handleColumnDrop(e, status)}
        >
          {cards.length === 0 ? (
            <div className={`border-2 border-dashed rounded-lg py-8 text-center transition-colors ${isOver ? 'border-primary/40 bg-primary/5' : ''}`}>
              <p className="text-xs text-muted-foreground">拖拉假設至此</p>
            </div>
          ) : (
            cards.map(renderCard)
          )}
        </div>
      </div>
    );
  };

  if (assumptions.length === 0) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-muted-foreground font-medium">尚無假設</p>
        <p className="text-sm text-muted-foreground">從 Explore 頁面的問答中標記，或點擊 [+ 新增假設] 開始</p>
        <div className="flex gap-3 justify-center">
          <Button onClick={() => setAddModalOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> 新增假設
          </Button>
          <AiButton onClick={handleAiChallenge}>
            識別假設
          </AiButton>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-2 items-center">
        {(['all', 'H*', 'H', 'M', 'L'] as const).map((level) => {
          const isActive = riskFilter === level;
          const config = level === 'all' ? null : RISK_LEVEL_CONFIG[level as RiskLevel];
          return (
            <Button
              key={level}
              variant={isActive ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-7 rounded-full"
              style={isActive && config ? { backgroundColor: config.color } : {}}
              onClick={() => setRiskFilter(level === 'all' ? 'all' : level as RiskLevel)}
            >
              {level === 'all' ? '全部' : config!.label}
            </Button>
          );
        })}

        <Input
          placeholder="搜尋假設..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-7 text-xs w-40 ml-auto"
        />

        <Button size="sm" variant="secondary" onClick={() => setAddModalOpen(true)} className="text-xs h-7">
          <Plus className="h-3 w-3 mr-1" /> 新增假設
        </Button>
        <AiButton size="sm" loading={isAiLoading} onClick={handleAiChallenge} className="text-xs h-7">
          質疑假設
        </AiButton>
      </div>

      {/* Desktop: 4-column Kanban */}
      <div className="hidden lg:flex gap-3">
        {KANBAN_COLUMNS.map(renderColumn)}
      </div>

      {/* Tablet: scrollable */}
      <div className="hidden md:flex lg:hidden gap-3 overflow-x-auto pb-2">
        {KANBAN_COLUMNS.map(renderColumn)}
      </div>

      {/* Mobile: single column with selector */}
      <div className="md:hidden space-y-3">
        <Select value={mobileColumn} onValueChange={(v) => setMobileColumn(v as VerificationStatus)}>
          <SelectTrigger className="h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {KANBAN_COLUMNS.map((col) => (
              <SelectItem key={col} value={col}>
                {VERIFICATION_STATUS_CONFIG[col].label} ({getColumnAssumptions(col).length})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="space-y-2">
          {getColumnAssumptions(mobileColumn).length === 0 ? (
            <div className="border-2 border-dashed rounded-lg py-8 text-center">
              <p className="text-xs text-muted-foreground">此欄位沒有假設</p>
            </div>
          ) : (
            getColumnAssumptions(mobileColumn).map(renderCard)
          )}
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteConfirmId} onOpenChange={(open) => { if (!open) setDeleteConfirmId(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>確認刪除假設</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            刪除後無法復原。確定要刪除假設
            <span className="font-mono font-semibold">
              {" "}{assumptions.find((a) => a.id === deleteConfirmId)?.assumptionCode}
            </span>
            {" "}嗎？
          </p>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteConfirmId(null)}>取消</Button>
            <Button
              variant="destructive"
              disabled={deleteAssumption.isPending}
              onClick={() => {
                if (deleteConfirmId) handleDeleteAssumption(deleteConfirmId);
              }}
            >
              {deleteAssumption.isPending ? '刪除中...' : '確認刪除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add assumption modal */}
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新增假設</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                假設描述 <span className="text-destructive">*</span>
              </label>
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="描述您的設計假設..."
                rows={3}
                maxLength={500}
              />
              <div className="flex justify-between">
                {newDesc.length > 0 && newDesc.length < 10 && (
                  <p className="text-xs text-destructive">至少 10 個字元</p>
                )}
                <span className="text-xs text-muted-foreground ml-auto">{newDesc.length}/500</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                風險等級 <span className="text-destructive">*</span>
              </label>
              <Select value={newRisk} onValueChange={(v) => setNewRisk(v as RiskLevel)}>
                <SelectTrigger><SelectValue placeholder="選擇風險等級" /></SelectTrigger>
                <SelectContent>
                  {(['L', 'M', 'H', 'H*'] as RiskLevel[]).map((r) => (
                    <SelectItem key={r} value={r}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: RISK_LEVEL_CONFIG[r].color }} />
                        {RISK_LEVEL_CONFIG[r].label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddModalOpen(false)}>取消</Button>
            <Button onClick={handleAddAssumption} disabled={createAssumption.isPending}>{createAssumption.isPending ? '建立中...' : '建立'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail panel */}
      <Sheet open={!!selectedCard} onOpenChange={(open) => {
        if (!open) {
          setSelectedCard(null);
          setEditingEvidence(null);
        }
      }}>
        <SheetContent className="w-[400px] sm:w-[420px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>假設詳情</SheetTitle>
          </SheetHeader>
          {selectedCard && (
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="font-mono">{selectedCard.assumptionCode}</Badge>
                {selectedCard.riskLevel && (
                  <Badge className="text-white" style={{ backgroundColor: RISK_LEVEL_CONFIG[selectedCard.riskLevel].color }}>
                    {RISK_LEVEL_CONFIG[selectedCard.riskLevel].label}
                  </Badge>
                )}
                <Badge className="text-white" style={{ backgroundColor: VERIFICATION_STATUS_CONFIG[selectedCard.verificationStatus].color }}>
                  {VERIFICATION_STATUS_CONFIG[selectedCard.verificationStatus].label}
                </Badge>

                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto h-7 text-xs text-destructive hover:text-destructive"
                  onClick={() => setDeleteConfirmId(selectedCard.id)}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1" />
                  刪除
                </Button>
              </div>

              <div>
                <span className="text-xs text-muted-foreground">假設內容</span>
                <p className="text-sm mt-1">{selectedCard.description}</p>
              </div>

              <div>
                <span className="text-xs text-muted-foreground">來源</span>
                <p className="text-sm mt-1">{selectedCard.source === 'explore_tag' ? 'Explore 頁面標記' : selectedCard.source === 'manual' ? '手動新增' : selectedCard.source === 'ai_suggest' ? 'AI 建議' : '未知因素轉化'}</p>
              </div>

              {selectedCard.worstConsequence && (
                <div>
                  <span className="text-xs text-muted-foreground">最壞後果</span>
                  <p className="text-sm mt-1 text-destructive">{selectedCard.worstConsequence}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                {selectedCard.verificationCost && (
                  <div>
                    <span className="text-xs text-muted-foreground">驗證成本</span>
                    <p className="text-sm mt-1">{selectedCard.verificationCost}</p>
                  </div>
                )}
                {selectedCard.verificationDuration && (
                  <div>
                    <span className="text-xs text-muted-foreground">驗證週期</span>
                    <p className="text-sm mt-1">{selectedCard.verificationDuration}</p>
                  </div>
                )}
              </div>
              {selectedCard.sourceArtifactId && (
                <div>
                  <span className="text-xs text-muted-foreground">來源 Artifact</span>
                  <Badge variant="outline" className="text-xs font-mono mt-1">{selectedCard.sourceArtifactId}</Badge>
                </div>
              )}

              {/* Experiments section */}
              <div>
                <span className="text-xs text-muted-foreground">實驗詳情</span>
                {(() => {
                  const exps = experimentsQuery.data ?? [];
                  return (
                    <div className="mt-2 space-y-2">
                      {exps.length === 0 && (
                        <p className="text-sm text-muted-foreground italic">尚無實驗記錄</p>
                      )}
                      {exps.map((exp) => {
                        const statusCfg = EXPERIMENT_STATUS_CONFIG[exp.status] ?? {
                          label: exp.status,
                          color: '#6b7280'
                        };
                        const isEditing = editingExpId === exp.id;
                        return (
                          <div key={exp.id} className="border rounded-lg p-2.5 space-y-2">
                            <div className="flex items-center gap-2">
                              <FlaskConical className="h-3 w-3 text-muted-foreground" />
                              <span className="text-sm font-medium flex-1">{exp.name}</span>
                              <Badge className="text-[10px] text-white" style={{ backgroundColor: statusCfg.color }}>
                                {statusCfg.label}
                              </Badge>
                            </div>
                            {isEditing ? (
                              <div className="space-y-2 pl-5">
                                <Select value={editExpStatus} onValueChange={(v) => setEditExpStatus(v as ExperimentStatus)}>
                                  <SelectTrigger className="h-7 text-xs">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {(['Plan', 'Running', 'Done'] as ExperimentStatus[]).map((s) => (
                                      <SelectItem key={s} value={s} className="text-xs">
                                        {EXPERIMENT_STATUS_CONFIG[s].label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                                <Textarea
                                  value={editExpResult}
                                  onChange={(e) => setEditExpResult(e.target.value)}
                                  placeholder="實驗結果或備註..."
                                  rows={2}
                                  className="text-xs"
                                />
                                <div className="flex gap-1.5">
                                  <Button size="sm" className="h-6 text-[10px]" disabled={updateExperiment.isPending} onClick={() => {
                                      updateExperiment.mutate(
                                        {
                                          id: exp.id,
                                          assumptionCode: selectedCard.assumptionCode,
                                          projectId,
                                          status: editExpStatus,
                                          result: editExpResult.trim() || null,
                                        },
                                        {
                                          onSuccess: () => {
                                            setEditingExpId(null);
                                            toast.success('實驗已更新');
                                          },
                                        }
                                      );
                                    }}>{updateExperiment.isPending ? '儲存中...' : '儲存'}</Button>
                                  <Button size="sm" variant="ghost" className="h-6 text-[10px]" onClick={() => setEditingExpId(null)}>取消</Button>
                                </div>
                              </div>
                            ) : (
                              <>
                                {exp.result && (
                                  <p className="text-xs text-muted-foreground pl-5">{exp.result}</p>
                                )}
                                <div className="flex items-center justify-between pl-5">
                                  <p className="text-[10px] text-muted-foreground/60">
                                    {new Date(exp.createdAt).toLocaleDateString('zh-TW')}
                                  </p>
                                  <div className="flex items-center gap-1">
                                    <Button size="sm" variant="ghost" className="h-5 text-[10px] text-muted-foreground" onClick={() => {
                                      setEditingExpId(exp.id);
                                      setEditExpStatus(exp.status);
                                      setEditExpResult(exp.result || '');
                                    }}>
                                      編輯
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      className="h-5 text-[10px] text-destructive hover:text-destructive"
                                      disabled={deleteExperiment.isPending}
                                      onClick={() => {
                                        deleteExperiment.mutate(
                                          { id: exp.id, assumptionCode: selectedCard.assumptionCode, projectId },
                                        );
                                      }}
                                    >
                                      刪除
                                    </Button>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                        );
                      })}

                      <div className="border border-dashed rounded-lg p-2.5 space-y-2">
                        <div className="flex gap-2">
                          <Input
                            value={newExpName}
                            onChange={(e) => setNewExpName(e.target.value)}
                            placeholder="新增實驗名稱..."
                            className="h-7 text-xs flex-1"
                          />
                          <Button size="sm" className="h-7 text-xs" disabled={newExpName.trim().length < 2 || createExperiment.isPending} onClick={() => {
                              createExperiment.mutate(
                                {
                                  projectId,
                                  assumptionCode: selectedCard.assumptionCode,
                                  name: newExpName.trim(),
                                  status: 'Plan',
                                },
                                {
                                  onSuccess: () => {
                                    setNewExpName('');
                                    toast.success('實驗已新增');
                                  },
                                }
                              );
                            }}>
                            <Plus className="h-3 w-3 mr-0.5" /> 新增
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {selectedCard.aiChallenge && (
                <div className="bg-muted rounded-lg p-3 space-y-1">
                  <Badge variant="secondary" className="text-[10px]">AI 質疑</Badge>
                  <p className="text-sm text-muted-foreground">{selectedCard.aiChallenge}</p>
                </div>
              )}

              {/* ====== Evidence entries section ====== */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-muted-foreground">
                    已登錄證據（{selectedEvidence.length}）
                  </span>
                </div>
                <div className="space-y-2">
                  {selectedEvidence.length === 0 ? (
                    <p className="text-sm text-muted-foreground italic">
                      尚無證據記錄，請點擊下方按鈕登錄
                    </p>
                  ) : (
                    selectedEvidence.map((ev) => {
                      const isEditingThis = editingEvidence?.id === ev.id;

                      if (isEditingThis && editingEvidence) {
                        return (
                          <div key={ev.id} className="border-2 border-primary/30 rounded-lg p-2.5 space-y-2">
                            <div className="space-y-1.5">
                              <Input
                                value={editingEvidence.title}
                                onChange={(e) => setEditingEvidence((prev) => prev ? { ...prev, title: e.target.value } : prev)}
                                placeholder="標題"
                                className="h-7 text-xs"
                              />
                              <Input
                                value={editingEvidence.measuredValue}
                                onChange={(e) => setEditingEvidence((prev) => prev ? { ...prev, measuredValue: e.target.value } : prev)}
                                placeholder="量測值"
                                className="h-7 text-xs"
                              />
                              <Textarea
                                value={editingEvidence.notes}
                                onChange={(e) => setEditingEvidence((prev) => prev ? { ...prev, notes: e.target.value } : prev)}
                                placeholder="備註"
                                rows={2}
                                className="text-xs"
                              />
                            </div>
                            <div className="flex gap-1.5">
                              <Button
                                size="sm"
                                className="h-6 text-[10px]"
                                disabled={updateEvidence.isPending}
                                onClick={handleSaveEditEvidence}
                              >
                                {updateEvidence.isPending ? '儲存中...' : '儲存'}
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 text-[10px]"
                                onClick={handleCancelEditEvidence}
                              >
                                取消
                              </Button>
                            </div>
                          </div>
                        );
                      }

                      return (
                        <div key={ev.id} className="border rounded-lg p-2.5 space-y-1.5">
                          <div className="flex items-center gap-2">
                            <ClipboardEdit className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm font-medium flex-1 truncate">
                              {ev.title}
                            </span>
                            <Badge variant="secondary" className="text-[10px] shrink-0">
                              {ev.evidenceLevel}
                            </Badge>
                          </div>
                          <div className="pl-5 space-y-0.5">
                            <p className="text-xs">
                              <span className="text-muted-foreground">量測值：</span>
                              <span className="font-medium">
                                {ev.measuredValue}
                                {ev.unit ? ` ${ev.unit}` : ''}
                              </span>
                            </p>
                            {ev.method && (
                              <p className="text-xs">
                                <span className="text-muted-foreground">方式：</span>
                                {ev.method}
                              </p>
                            )}
                            {ev.notes && (
                              <p className="text-xs text-muted-foreground italic">
                                {ev.notes}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center justify-between pl-5">
                            <p className="text-[10px] text-muted-foreground/60">
                              {ev.measuredAt
                                ? new Date(ev.measuredAt).toLocaleDateString('zh-TW')
                                : ''}
                            </p>
                            <div className="flex items-center gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-5 w-5 p-0 text-muted-foreground hover:text-foreground"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEditEvidence(ev);
                                }}
                              >
                                <Pencil className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-5 w-5 p-0 text-muted-foreground hover:text-destructive"
                                disabled={deleteEvidence.isPending}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteEvidence(ev.id);
                                }}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Log evidence button */}
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  setEvidenceDefaultCodes([selectedCard.assumptionCode]);
                  setEvidenceDialogOpen(true);
                }}
              >
                <ClipboardEdit className="h-4 w-4 mr-1" />
                登錄證據
              </Button>

              <div>
                <span className="text-xs text-muted-foreground">變更驗證狀態</span>
                <Select
                  value={selectedCard.verificationStatus}
                  onValueChange={(v) => {
                    handleMoveCard(selectedCard.id, v as VerificationStatus);
                    setSelectedCard({ ...selectedCard, verificationStatus: v as VerificationStatus });
                  }}
                >
                  <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {KANBAN_COLUMNS.map((col) => (
                      <SelectItem key={col} value={col}>
                        {VERIFICATION_STATUS_CONFIG[col].label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="text-xs text-muted-foreground">
                建立時間：{new Date(selectedCard.createdAt).toLocaleDateString('zh-TW')}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Evidence Entry Dialog */}
      <EvidenceEntryDialog
        open={evidenceDialogOpen}
        onOpenChange={setEvidenceDialogOpen}
        projectId={projectId}
        defaultAssumptionCodes={evidenceDefaultCodes}
      />
    </div>
  );
}