import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, ArrowRight, Link2, ShieldCheck, AlertTriangle } from 'lucide-react';
import { CompatibilityMatrixView } from './CompatibilityMatrix';
import { ConceptRouteCard } from './ConceptRouteCard';
import type { MultiSolutionAdoptionState, ConceptRoute } from '@/types/conceptRoute';

interface Props {
  adoptionState: MultiSolutionAdoptionState;
  onConfirm: (routes: ConceptRoute[]) => void;
}

export function MultiSolutionAdoptionPanel({ adoptionState, onConfirm }: Props) {
  const { matrix, recommendedRoutes, antiPatternChecks } = adoptionState;
  const solutionCount = matrix.solutions.length;
  const compositeCount = recommendedRoutes.filter((r) => r.type === 'composite').length;
  const singleCount = recommendedRoutes.filter((r) => r.type === 'single').length;

  return (
    <Card className="border-2 border-primary/40 bg-primary/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Link2 className="h-5 w-5 text-primary" />
          多解採納策略 (X2)
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          AI 已分析 {solutionCount} 條採用解法的物理相容性與交互作用，推薦{' '}
          {compositeCount > 0 && <>{compositeCount} 條複合 Route</>}
          {compositeCount > 0 && singleCount > 0 && '、'}
          {singleCount > 0 && <>{singleCount} 條獨立 Route</>}。
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Compatibility Matrix */}
        <CompatibilityMatrixView matrix={matrix} />

        <Separator />

        {/* Recommended Concept Routes */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-primary" />
            AI 推薦 Concept Routes
          </h4>
          {recommendedRoutes.map((route) => (
            <ConceptRouteCard key={route.id} route={route} />
          ))}
        </div>

        <Separator />

        {/* Anti-Pattern Checks */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
            Anti-Pattern 檢查
          </h4>
          {antiPatternChecks.map((check) => (
            <div key={check.label} className="flex items-start gap-2 text-xs">
              {check.passed ? (
                <Badge className="text-[10px] bg-emerald-600 text-white shrink-0">Pass</Badge>
              ) : (
                <Badge variant="destructive" className="text-[10px] shrink-0">Fail</Badge>
              )}
              <div>
                <span className="font-medium">{check.label}</span>
                <span className="text-muted-foreground ml-1">— {check.detail}</span>
              </div>
            </div>
          ))}
          <div className="flex items-start gap-1.5 text-[10px] text-amber-600 dark:text-amber-400 mt-1">
            <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
            <span>提醒：複合 Route 需額外驗證子解法間無負面交互 (Evidence Level E1 以上)</span>
          </div>
        </div>

        <Separator />

        {/* Confirm */}
        <div className="flex items-center gap-3 pt-1">
          <Button
            onClick={() => onConfirm(recommendedRoutes)}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            確認 Concept Routes 並繼續
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
          <p className="text-xs text-muted-foreground">確認後將進入子系統定義步驟</p>
        </div>
      </CardContent>
    </Card>
  );
}
