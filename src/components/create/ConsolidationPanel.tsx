/**
 * ConsolidationPanel — 顯示跨矛盾方向整併結果 (v8).
 *
 * Three states:
 *   - compatible: all Top1 directions are compatible → green summary
 *   - resolved_with_swap: some Top1→Top2 swaps resolved conflicts → amber
 *   - conflict: unresolvable conflicts → red with report
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  Lightbulb,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ConsolidationResult } from '@/types/directedTriz';

export interface ConsolidationPanelProps {
  consolidation: ConsolidationResult;
}

const STATUS_CONFIG = {
  compatible: {
    icon: CheckCircle2,
    label: '全部相容',
    color: 'text-green-600',
    bg: 'bg-green-50 dark:bg-green-950/20 border-green-200',
  },
  resolved_with_swap: {
    icon: AlertTriangle,
    label: '替換後相容',
    color: 'text-amber-600',
    bg: 'bg-amber-50 dark:bg-amber-950/20 border-amber-200',
  },
  conflict: {
    icon: XCircle,
    label: '存在衝突',
    color: 'text-red-600',
    bg: 'bg-red-50 dark:bg-red-950/20 border-red-200',
  },
};

export function ConsolidationPanel({ consolidation }: ConsolidationPanelProps) {
  const config = STATUS_CONFIG[consolidation.status];
  const Icon = config.icon;

  return (
    <Card className={cn('border', config.bg)}>
      <CardHeader className="p-4 pb-2">
        <div className="flex items-center gap-2">
          <Icon className={cn('h-5 w-5', config.color)} />
          <CardTitle className="text-sm font-semibold">
            跨矛盾方向整併
          </CardTitle>
          <Badge variant="outline" className="text-[10px]">
            {config.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-2 space-y-3">
        {/* Adopted directions map */}
        {Object.keys(consolidation.adopted_directions).length > 0 && (
          <div className="space-y-1">
            <div className="text-[11px] font-medium text-muted-foreground">
              採納方向
            </div>
            {Object.entries(consolidation.adopted_directions).map(([cid, dir]) => (
              <div
                key={cid}
                className="flex items-center gap-2 text-[11px] bg-background/80 rounded p-1.5"
              >
                <span className="text-muted-foreground font-mono">
                  {cid.slice(0, 12)}
                </span>
                <ArrowRight className="h-3 w-3 text-muted-foreground" />
                <span className="font-medium">{dir.direction_name}</span>
                <Badge variant="outline" className="text-[9px] ml-auto">
                  TC:{dir.tc_count} PC:{dir.pc_count} SF:{dir.sf_count}
                </Badge>
              </div>
            ))}
          </div>
        )}

        {/* Conflict report */}
        {consolidation.conflict_report &&
          consolidation.conflict_report.conflicting_pairs.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-red-600">衝突清單</div>
              {consolidation.conflict_report.conflicting_pairs.map((pair, i) => (
                <div
                  key={i}
                  className="text-[11px] bg-red-50/50 dark:bg-red-950/10 rounded p-2 border border-red-200/50"
                >
                  <div className="font-medium">
                    「{pair.direction_a}」 vs 「{pair.direction_b}」
                  </div>
                  <div className="text-muted-foreground mt-0.5">
                    矛盾 {pair.contradiction_a_id} ↔ {pair.contradiction_b_id}
                  </div>
                  {pair.reason && (
                    <div className="text-muted-foreground mt-0.5 italic">
                      {pair.reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

        {/* Suggestions */}
        {consolidation.conflict_report &&
          consolidation.conflict_report.suggestions.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
                <Lightbulb className="h-3 w-3" /> 建議
              </div>
              <ul className="text-[11px] text-muted-foreground space-y-0.5 list-disc list-inside">
                {consolidation.conflict_report.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

        {/* Integration advice */}
        {consolidation.integration_advice && (
          <div className="text-[11px] bg-muted/40 rounded p-2">
            <div className="font-medium text-muted-foreground mb-0.5">整合建議</div>
            <p className="text-foreground">{consolidation.integration_advice}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
