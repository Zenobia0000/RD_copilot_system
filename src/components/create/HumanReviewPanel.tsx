import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { CheckCircle, ArrowRight, RefreshCw, Star, ShieldAlert } from 'lucide-react';
import type { BranchExploration, MinorContradiction } from '@/types/convergence';
import type { ContradictionSeverity } from '@/types/contradiction';

const SEVERITY_OPTIONS: { value: ContradictionSeverity; label: string; cls: string }[] = [
  { value: 'fatal', label: 'Fatal', cls: 'bg-red-500 text-white hover:bg-red-600' },
  { value: 'major', label: 'Major', cls: 'bg-orange-500 text-white hover:bg-orange-600' },
  { value: 'minor', label: 'Minor', cls: 'bg-muted text-muted-foreground hover:bg-muted/80' },
];

interface Props {
  branches: BranchExploration[];
  riskRegister: MinorContradiction[];
  onConfirm: () => void;
  onRetry: (contradictionId: string) => void;
  onConfirmSeverity: (id: string, severity: ContradictionSeverity) => void;
}

export function HumanReviewPanel({ branches, riskRegister, onConfirm, onRetry, onConfirmSeverity }: Props) {
  const convergedBranches = branches.filter((b) => b.status === 'converged');

  return (
    <Card className="border-2 border-primary bg-primary/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-primary" />
          AI 探索完成 — 人類審核
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          所有 Fatal/Major 矛盾已收斂。請審核 AI 推薦的採用方案與矛盾分級。
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Recommended solutions per branch */}
        {convergedBranches.map((branch) => {
          const lastRound = branch.rounds[branch.rounds.length - 1];
          const adoptedSolutions = branch.rounds
            .map((r) => {
              const sol = r.solutions.find((s) => s.id === r.adoptedSolutionId);
              return sol ? { round: r.roundNumber, ...sol } : null;
            })
            .filter(Boolean);

          return (
            <div key={branch.contradictionId} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] font-mono">{branch.contradictionId}</Badge>
                  <span className="text-sm font-medium">{branch.contradictionLabel}</span>
                  <Badge className="text-[10px] bg-emerald-600 text-white">
                    {branch.depth} 輪收斂
                  </Badge>
                </div>
                <Button variant="ghost" size="sm" className="text-xs" onClick={() => onRetry(branch.contradictionId)}>
                  <RefreshCw className="h-3 w-3 mr-1" /> 重新探索
                </Button>
              </div>

              <div className="ml-4 space-y-1">
                {adoptedSolutions.map((sol) => sol && (
                  <div key={sol.id} className="flex items-center gap-2 text-xs p-2 rounded-md bg-background border">
                    <Star className="h-3 w-3 text-primary fill-primary shrink-0" />
                    <Badge variant="outline" className="text-[10px]">{sol.path}</Badge>
                    {sol.principleNumber && (
                      <Badge variant="outline" className="text-[10px] font-mono">#{sol.principleNumber}</Badge>
                    )}
                    <span className="font-medium">{sol.principleName}</span>
                    <span className="text-muted-foreground truncate">{sol.suggestion.slice(0, 50)}...</span>
                    <Badge variant="secondary" className="text-[10px] ml-auto shrink-0">
                      R{(sol as { round: number }).round}
                    </Badge>
                  </div>
                ))}
              </div>

              {/* Secondary contradictions with severity confirmation */}
              {branch.rounds.some((r) => r.scanResult.newContradictions.length > 0) && (
                <div className="ml-4 mt-2 space-y-1">
                  <p className="text-[10px] text-muted-foreground font-medium">偵測到的二次矛盾（可調整 AI 分級）:</p>
                  {branch.rounds.flatMap((r) =>
                    r.scanResult.newContradictions.map((nc) => (
                      <div key={nc.id} className="flex items-center gap-2 text-xs p-1.5 rounded-md bg-muted/30 border">
                        <span className="text-muted-foreground truncate flex-1">{nc.description}</span>
                        <div className="flex gap-1 shrink-0">
                          {SEVERITY_OPTIONS.map((opt) => (
                            <Tooltip key={opt.value}>
                              <TooltipTrigger asChild>
                                <button
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-medium transition-all ${
                                    nc.severity === opt.value
                                      ? opt.cls
                                      : 'bg-transparent text-muted-foreground/50 hover:text-muted-foreground'
                                  }`}
                                  onClick={() => onConfirmSeverity(nc.id, opt.value)}
                                >
                                  {opt.label}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent><p className="text-xs">設定為 {opt.label}</p></TooltipContent>
                            </Tooltip>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Risk Register (minor) */}
        {riskRegister.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <ShieldAlert className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Risk Register (Minor — 非阻斷)</span>
              </div>
              {riskRegister.map((r) => (
                <div key={r.id} className="flex items-center gap-2 text-xs text-muted-foreground ml-6">
                  <Badge variant="secondary" className="text-[10px]">Minor</Badge>
                  <span>{r.description}</span>
                  <span className="text-[10px]">← {r.sourceBranchId} R{r.sourceRound}</span>
                </div>
              ))}
            </div>
          </>
        )}

        <Separator />

        {/* Confirm button */}
        <div className="flex items-center gap-3 pt-1">
          <Button onClick={onConfirm} className="bg-primary hover:bg-primary/90 text-primary-foreground">
            <CheckCircle className="h-4 w-4 mr-1" />
            確認分級 → 進入多解採納
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
          <p className="text-xs text-muted-foreground">確認後將進入多解採納策略分析 (X2)</p>
        </div>
      </CardContent>
    </Card>
  );
}
