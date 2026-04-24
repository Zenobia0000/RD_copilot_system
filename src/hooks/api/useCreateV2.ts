/**
 * API hooks for Create page V2 extensions (WBS 8.6.1)
 *
 * Covers: OZ/OT Analysis (mutation), Evidence Coverage (query).
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ozOtAnalysis,
  evidenceCoverage,
  getApiErrorMessage,
} from '@/lib/api';
import type {
  OzOtAnalysisRequest,
  OzOtAnalysisResponse,
  EvidenceCoverageResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// OZ/OT Analysis — POST /analyst/oz-ot-analysis
// ---------------------------------------------------------------------------

export function useOzOtAnalysis(_projectId?: string) {
  return useMutation<OzOtAnalysisResponse, Error, OzOtAnalysisRequest>({
    mutationFn: (body) => ozOtAnalysis(body),
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'OZ/OT 分析'));
    },
  });
}

// ---------------------------------------------------------------------------
// Evidence Coverage — GET /evidence/coverage/{pid}
// ---------------------------------------------------------------------------

export function useEvidenceCoverage(projectId: string | undefined) {
  return useQuery<EvidenceCoverageResponse, Error>({
    queryKey: ['evidence_coverage', projectId ?? '__none__'],
    queryFn: () => evidenceCoverage(projectId!),
    enabled: !!projectId,
    staleTime: 60_000,
    retry: 1,
  });
}
