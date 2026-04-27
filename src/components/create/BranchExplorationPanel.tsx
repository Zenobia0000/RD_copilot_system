import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { CheckCircle, Loader2, AlertTriangle, Star, GitBranch } from 'lucide-react';
import type { BranchExploration, ExplorationRound, ExplorationSolution } from '@/types/convergence';

interface Props {
  branches: BranchExploration[];
}

const severityBadge = (severity: string) => {
  switch (severity) {
    case 'fatal': return <Badge variant="destructive" className="text-[10px]">Fatal</Badge>;
    case 'major': return <Badge className="text-[10px] bg-orange-500 text-white">Major</Badge>;
    case 'minor': return <Badge variant="secondary" className="text-[10px]">Minor</Badge>;
    default: return null;
  }
};

const pathBadge = (path: string) => {
  const colors: Record<string, string> = {
    TC: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    PC: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    SF: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  };
  return <Badge variant="outline" className={`text-[10px] ${colors[path] ?? ''}`}>{path}</Badge>;
};

function SolutionRow({ sol }: { sol: ExplorationSolution }) {
  return (
    <div className={`flex items-start gap-2 py-1.5 px-2 rounded-md text-xs ${sol.isRecommended ? 'bg-primary/5 border border-primary/20' : ''}`}>
      <div className="flex items-center gap-1 shrink-0 pt-0.5">
        {pathBadge(sol.path)}
        {sol.principleNumber && (
          <Badge variant="outline" className="text-[10px] font-mono">#{sol.principleNumber}</Badge>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <span className="font-medium">{sol.principleName}</span>
        <span className="text-muted-foreground ml-1">{sol.suggestion.length > 60 ? sol.suggestion.slice(0, 60) + '...' : sol.suggestion}</span>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <span className="text-[10px] text-muted-foreground tabular-nums">{sol.score.toFixed(1)}</span>
        {sol.isRecommended && <Star className="h-3 w-3 text-primary fill-primary" />}
      </div>
    </div>
  );
}

function RoundSection({ round }: { round: ExplorationRound }) {
  const adopted = round.solutions.find((s) => s.id === round.adoptedSolutionId);
  const hasNew = round.scanResult.hasNewFatalMajor;
  const newConts = round.scanResult.newContradictions;

  return (
    <div className="ml-4 border-l-2 border-muted pl-3 pb-3 space-y-2">
      <div className="flex items-center gap-2 text-xs">
        <Badge variant="outline" className="text-[10px] font-mono">Round {round.roundNumber}</Badge>
        {adopted && (
          <span className="text-muted-foreground">
            AI 採用: <span className="font-medium text-foreground">{adopted.principleName}</span>
          </span>
        )}
      </div>

      {/* Solutions explored */}
      <div className="space-y-1">
        {round.solutions.map((sol) => (
          <SolutionRow key={sol.id} sol={sol} />
        ))}
      </div>

      {/* Scan result */}
      {newConts.length > 0 ? (
        <div className={`rounded-md p-2 text-xs ${hasNew ? 'bg-destructive/5 border border-destructive/20' : 'bg-muted/50'}`}>
          <p className="font-medium flex items-center gap-1 mb-1">
            <AlertTriangle className="h-3 w-3 text-destructive" />
            掃描發現 {newConts.length} 個二次矛盾
          </p>
          {newConts.map((c) => (
            <div key={c.id} className="flex items-center gap-1.5 text-[10px] text-muted-foreground mt-0.5">
              {severityBadge(c.severity)}
              <span>{c.description}</span>
              {c.resolved && <CheckCircle className="h-3 w-3 text-emerald-500 shrink-0" />}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-md p-2 text-xs bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800">
          <p className="font-medium text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            掃描完成：無新矛盾，已收斂
          </p>
        </div>
      )}
    </div>
  );
}

export function BranchExplorationPanel({ branches }: Props) {
  if (branches.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <GitBranch className="h-4 w-4" />
          分支探索歷程
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" defaultValue={branches.map((b) => b.contradictionId)}>
          {branches.map((branch) => (
            <AccordionItem key={branch.contradictionId} value={branch.contradictionId}>
              <AccordionTrigger className="py-2 hover:no-underline">
                <div className="flex items-center gap-2 text-sm">
                  {branch.status === 'converged' ? (
                    <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
                  ) : branch.status === 'halted' ? (
                    <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
                  ) : (
                    <Loader2 className="h-4 w-4 text-primary animate-spin shrink-0" />
                  )}
                  <span className="font-medium">{branch.contradictionLabel}</span>
                  <Badge variant="outline" className="text-[10px] font-mono">{branch.contradictionId}</Badge>
                  <Badge
                    className={`text-[10px] text-white ${
                      branch.status === 'converged' ? 'bg-emerald-600' :
                      branch.status === 'halted' ? 'bg-red-600' : 'bg-primary'
                    }`}
                  >
                    {branch.status === 'converged' ? '已收斂' : branch.status === 'halted' ? '已停止' : '探索中'}
                  </Badge>
                  <Badge variant="secondary" className="text-[10px]">深度: {branch.depth}</Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-1 pt-1">
                  {branch.rounds.map((round) => (
                    <RoundSection key={round.roundNumber} round={round} />
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
