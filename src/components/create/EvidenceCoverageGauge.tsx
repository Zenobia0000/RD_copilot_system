/**
 * EvidenceCoverageGauge (WBS 8.6.5)
 *
 * Simple progress bar + percentage display for evidence coverage.
 * - >= 40% coverage: green
 * - < 40% coverage: amber/red
 *
 * Calls useEvidenceCoverage hook to fetch data.
 */

import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { useEvidenceCoverage } from '@/hooks/api/useCreateV2';

interface EvidenceCoverageGaugeProps {
  projectId: string;
  className?: string;
}

export function EvidenceCoverageGauge({ projectId, className }: EvidenceCoverageGaugeProps) {
  const { data, isLoading, isError } = useEvidenceCoverage(projectId);

  if (isLoading) {
    return <Skeleton className={cn('h-8 w-full', className)} />;
  }

  if (isError || !data) {
    return (
      <div className={cn('text-xs text-muted-foreground', className)}>
        證據覆蓋率暫無資料
      </div>
    );
  }

  const pct = Math.round(data.coverage_pct);
  const isHealthy = pct >= 40;

  return (
    <div className={cn('space-y-1.5', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          證據覆蓋率
        </span>
        <span
          className={cn(
            'text-sm font-bold',
            isHealthy ? 'text-green-700' : 'text-amber-700',
          )}
        >
          {pct}%
        </span>
      </div>
      <Progress
        value={pct}
        className={cn(
          'h-2',
          isHealthy ? '[&>div]:bg-green-500' : '[&>div]:bg-amber-500',
        )}
      />
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>{data.covered_claims}/{data.total_claims} claims covered</span>
        {!isHealthy && (
          <span className="text-amber-600 font-medium">需要更多證據</span>
        )}
      </div>
    </div>
  );
}
