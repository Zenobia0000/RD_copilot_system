/**
 * CciBadge (WBS 8.6.4)
 *
 * Small badge component that displays CCI (Concept Confidence Index) status:
 * - Evolution (green): strong concept with solid evidence
 * - Weak Evolution (yellow): concept needs more evidence
 * - Patch (red): concept is a workaround, not a true solution
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type CciLevel = 'evolution' | 'weak_evolution' | 'patch';

interface CciBadgeProps {
  level: CciLevel;
  className?: string;
}

const CCI_CONFIG: Record<CciLevel, { label: string; className: string }> = {
  evolution: {
    label: 'Evolution',
    className: 'bg-green-100 text-green-800 border-green-300 hover:bg-green-100',
  },
  weak_evolution: {
    label: 'Weak Evolution',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300 hover:bg-yellow-100',
  },
  patch: {
    label: 'Patch',
    className: 'bg-red-100 text-red-800 border-red-300 hover:bg-red-100',
  },
};

export function CciBadge({ level, className }: CciBadgeProps) {
  const config = CCI_CONFIG[level];

  return (
    <Badge
      variant="outline"
      className={cn('text-[10px] font-semibold', config.className, className)}
    >
      {config.label}
    </Badge>
  );
}
