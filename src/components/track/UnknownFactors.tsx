import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Plus, ArrowRight, X, Check } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { unknownFactorDiscover } from "@/lib/api";
import { useBrief, useConstraints, useKpis } from "@/hooks/api/useBrief";
import { useContradictions } from "@/hooks/api/useContradictions";
import type { UnknownFactor, ImpactLevel, TrackAssumption } from "@/types/track";
import { IMPACT_CONFIG, UNKNOWN_STATUS_CONFIG } from "@/types/track";

interface UnknownFactorsProps {
  factors: UnknownFactor[];
  assumptions: TrackAssumption[];
  onUpdateFactors: (factors: UnknownFactor[]) => void;
  onConvertToAssumption: (factor: UnknownFactor) => void;
  projectId: string;
}

export function UnknownFactors({ factors, assumptions, onUpdateFactors, onConvertToAssumption, projectId }: UnknownFactorsProps) {
  const [addOpen, setAddOpen] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<{ desc: string; impact: ImpactLevel; reason: string }[]>([]);

  // Fetch project context for AI discovery
  const { data: brief } = useBrief(projectId || undefined);
  const { data: constraints } = useConstraints(projectId || undefined);
  const { data: contradictions } = useContradictions(projectId || undefined);
  const { data: kpis } = useKpis(projectId || undefined);

  // Form state
  const [newDesc, setNewDesc] = useState('');
  const [newImpact, setNewImpact] = useState<ImpactLevel | ''>('');

  const handleAdd = () => {
    if (newDesc.trim().length < 10) {
      toast.error('描述至少 10 個字元');
      return;
    }
    if (!newImpact) {
      toast.error('請選擇影響評估');
      return;
    }
    const code = `U-${String(factors.length + 1).padStart(2, '0')}`;
    const newF: UnknownFactor = {
      id: `uf-${Date.now()}`,
      unknownCode: code,
      description: newDesc,
      impact: newImpact,
      status: 'open',
      note: null,
      linkedAssumptionId: null,
      createdAt: new Date().toISOString(),
    };
    onUpdateFactors([...factors, newF]);
    setAddOpen(false);
    setNewDesc('');
    setNewImpact('');
    toast.success('未知因素已新增');
  };

  const handleDismiss = (id: string) => {
    onUpdateFactors(
      factors.map((f) => (f.id === id ? { ...f, status: 'dismissed' as const } : f))
    );
    toast.success('已標記為排除');
  };

  const handleConvert = (factor: UnknownFactor) => {
    onUpdateFactors(
      factors.map((f) => (f.id === factor.id ? { ...f, status: 'converted' as const } : f))
    );
    onConvertToAssumption(factor);
    toast.success('已轉化為假設，請至假設 Kanban 查看');
  };

  const handleAiDiscover = async () => {
    setIsAiLoading(true);
    try {
      const resp = await unknownFactorDiscover({
        project_id: projectId,
        mission: brief?.mission ?? '',
        constraints: (constraints ?? []).map(c => c.description),
        kpis: (kpis ?? []).map(k => `${k.kpiName}: ${k.targetValue} ${k.unit ?? ''}`),
        contradictions: (contradictions ?? []).map(c => c.naturalDescription ?? c.description ?? ''),
        existing_assumptions: assumptions.map(a => a.content),
        existing_unknowns: factors.map(f => f.description),
      });
      const mapped = (resp.factors ?? []).map(f => ({
        desc: f.description,
        impact: (f.impact || 'medium') as ImpactLevel,
        reason: f.reason || '',
      }));
      setAiSuggestions(mapped);
      toast.success(`AI 已識別 ${mapped.length} 個潛在未知因素`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(`AI 識別失敗：${msg}`);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleAdoptSuggestion = (suggestion: typeof aiSuggestions[0]) => {
    const code = `U-${String(factors.length + 1).padStart(2, '0')}`;
    const newF: UnknownFactor = {
      id: `uf-${Date.now()}`,
      unknownCode: code,
      description: suggestion.desc,
      impact: suggestion.impact,
      status: 'open',
      note: `AI 分析理由：${suggestion.reason}`,
      linkedAssumptionId: null,
      createdAt: new Date().toISOString(),
    };
    onUpdateFactors([...factors, newF]);
    setAiSuggestions((prev) => prev.filter((s) => s.desc !== suggestion.desc));
    toast.success('已採用 AI 建議');
  };

  const handleSkipSuggestion = (desc: string) => {
    setAiSuggestions((prev) => prev.filter((s) => s.desc !== desc));
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">未知集合 U — 追蹤不確定性</h2>
        <Badge variant="secondary" className="text-xs">{factors.filter((f) => f.status === 'open').length} 開放</Badge>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <Button size="sm" variant="secondary" onClick={() => setAddOpen(true)} className="text-xs">
          <Plus className="h-3 w-3 mr-1" /> 新增未知因素
        </Button>
        <AiButton size="sm" loading={isAiLoading} onClick={handleAiDiscover} className="text-xs">
          識別未知
        </AiButton>
      </div>

      {/* AI suggestions */}
      {aiSuggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground font-medium">AI 建議的未知因素</p>
          {aiSuggestions.map((s) => (
            <Card key={s.desc} className="bg-muted/50">
              <CardContent className="p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-[10px]">AI</Badge>
                  <Badge className="text-[10px] text-white" style={{ backgroundColor: IMPACT_CONFIG[s.impact].color }}>
                    影響: {IMPACT_CONFIG[s.impact].label}
                  </Badge>
                </div>
                <p className="text-sm">{s.desc}</p>
                <p className="text-xs text-muted-foreground">{s.reason}</p>
                <div className="flex gap-2">
                  <Button size="sm" className="text-xs h-7" onClick={() => handleAdoptSuggestion(s)}>
                    <Check className="h-3 w-3 mr-1" /> 採用
                  </Button>
                  <Button size="sm" variant="ghost" className="text-xs h-7" onClick={() => handleSkipSuggestion(s.desc)}>
                    跳過
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Factor list */}
      {factors.length === 0 ? (
        <div className="text-center py-16 space-y-3 bg-muted/50 rounded-lg border border-dashed">
          <p className="text-muted-foreground font-medium">尚未記錄未知因素</p>
          <p className="text-sm text-muted-foreground">記錄專案中的不確定性，讓未知變得可追蹤</p>
        </div>
      ) : (
        <div className="space-y-3">
          {factors.map((f) => {
            const isDismissed = f.status === 'dismissed';
            const isConverted = f.status === 'converted';

            return (
              <Card
                key={f.id}
                className={`transition-all ${isConverted ? 'border-l-[3px] border-l-green-600' : ''} ${isDismissed ? 'opacity-50' : ''}`}
              >
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-[10px] font-mono">{f.unknownCode}</Badge>
                    <Badge
                      className="text-[10px] text-white"
                      style={{ backgroundColor: IMPACT_CONFIG[f.impact].color }}
                    >
                      {IMPACT_CONFIG[f.impact].label}
                    </Badge>
                    <Badge
                      className="text-[10px] text-white"
                      style={{ backgroundColor: UNKNOWN_STATUS_CONFIG[f.status].color }}
                    >
                      {UNKNOWN_STATUS_CONFIG[f.status].label}
                    </Badge>
                  </div>

                  <p className={`text-sm ${isDismissed ? 'line-through text-muted-foreground' : ''}`}>
                    {f.description}
                  </p>

                  {f.note && (
                    <p className="text-xs text-muted-foreground">{f.note}</p>
                  )}

                  {f.linkedAssumptionId && (() => {
                    const linked = assumptions.find(a => a.id === f.linkedAssumptionId);
                    return (
                      <Badge variant="outline" className="text-[10px]">
                        關聯假設: {linked ? linked.assumptionCode : f.linkedAssumptionId}
                      </Badge>
                    );
                  })()}

                  {f.status === 'open' && (
                    <div className="flex gap-2 pt-1">
                      <Button
                        size="sm"
                        className="text-xs h-7 bg-amber-500 hover:bg-amber-600 text-white"
                        onClick={() => handleConvert(f)}
                      >
                        <ArrowRight className="h-3 w-3 mr-1" /> 轉為假設
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs h-7 text-destructive"
                        onClick={() => handleDismiss(f.id)}
                      >
                        <X className="h-3 w-3 mr-1" /> 排除
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新增未知因素</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                因素描述 <span className="text-destructive">*</span>
              </label>
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="描述此未知因素..."
                rows={3}
                maxLength={300}
              />
              <div className="flex justify-between">
                {newDesc.length > 0 && newDesc.length < 10 && (
                  <p className="text-xs text-destructive">至少 10 個字元</p>
                )}
                <span className="text-xs text-muted-foreground ml-auto">{newDesc.length}/300</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                影響評估 <span className="text-destructive">*</span>
              </label>
              <Select value={newImpact} onValueChange={(v) => setNewImpact(v as ImpactLevel)}>
                <SelectTrigger><SelectValue placeholder="選擇影響程度" /></SelectTrigger>
                <SelectContent>
                  {(['low', 'medium', 'high'] as ImpactLevel[]).map((i) => (
                    <SelectItem key={i} value={i}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: IMPACT_CONFIG[i].color }} />
                        {IMPACT_CONFIG[i].label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddOpen(false)}>取消</Button>
            <Button onClick={handleAdd}>建立</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
