import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Grid3X3 } from 'lucide-react';
import type { CompatibilityMatrix as MatrixType, CompatibilityResult, AdoptionType } from '@/types/conceptRoute';
import { ADOPTION_TYPE_LABELS } from '@/types/conceptRoute';

interface Props {
  matrix: MatrixType;
}

const resultStyle: Record<CompatibilityResult, { icon: string; bg: string; text: string }> = {
  compatible:        { icon: 'O', bg: 'bg-emerald-50 dark:bg-emerald-950/40',  text: 'text-emerald-700 dark:text-emerald-300' },
  exclusive:         { icon: 'X', bg: 'bg-red-50 dark:bg-red-950/40',          text: 'text-red-700 dark:text-red-300' },
  needs_verification:{ icon: '?', bg: 'bg-amber-50 dark:bg-amber-950/40',     text: 'text-amber-700 dark:text-amber-300' },
};

function CellContent({ result, adoptionType, reason }: { result: CompatibilityResult; adoptionType: AdoptionType | null; reason: string }) {
  const style = resultStyle[result];
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={`flex flex-col items-center justify-center gap-0.5 p-1.5 rounded-md cursor-help ${style.bg}`}>
          <span className="text-sm">{style.icon}</span>
          {adoptionType && (
            <span className={`text-[10px] font-mono font-medium ${style.text}`}>
              {adoptionType}
            </span>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <div className="space-y-1">
          {adoptionType && (
            <p className="text-xs font-medium">
              {adoptionType} — {ADOPTION_TYPE_LABELS[adoptionType].zh} ({ADOPTION_TYPE_LABELS[adoptionType].strategy})
            </p>
          )}
          <p className="text-xs text-muted-foreground">{reason}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}

export function CompatibilityMatrixView({ matrix }: Props) {
  const { solutions, pairs } = matrix;
  const n = solutions.length;

  const getPair = (aId: string, bId: string) =>
    pairs.find(
      (p) =>
        (p.solutionAId === aId && p.solutionBId === bId) ||
        (p.solutionAId === bId && p.solutionBId === aId)
    );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Grid3X3 className="h-4 w-4" />
          物理相容性矩陣
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="p-1.5 text-left" />
                {solutions.map((s) => (
                  <th key={s.id} className="p-1.5 text-center min-w-[80px]">
                    <div className="font-medium">{s.label}</div>
                    <Badge variant="outline" className="text-[9px] mt-0.5">{s.dimension}</Badge>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {solutions.map((rowSol, rowIdx) => (
                <tr key={rowSol.id}>
                  <td className="p-1.5 font-medium whitespace-nowrap">
                    <div>{rowSol.label}</div>
                    <Badge variant="outline" className="text-[9px] mt-0.5">{rowSol.dimension}</Badge>
                  </td>
                  {solutions.map((colSol, colIdx) => {
                    if (colIdx <= rowIdx) {
                      return (
                        <td key={colSol.id} className="p-1.5 text-center">
                          {colIdx === rowIdx ? (
                            <span className="text-muted-foreground">—</span>
                          ) : null}
                        </td>
                      );
                    }
                    const pair = getPair(rowSol.id, colSol.id);
                    if (!pair) return <td key={colSol.id} className="p-1.5" />;
                    return (
                      <td key={colSol.id} className="p-1.5">
                        <CellContent
                          result={pair.result}
                          adoptionType={pair.adoptionType}
                          reason={pair.reason}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t text-[10px] text-muted-foreground">
          <span>O 可合併</span>
          <span>X 互斥</span>
          <span>? 待確認</span>
          <span className="ml-auto">Hover 查看詳情</span>
        </div>
      </CardContent>
    </Card>
  );
}
