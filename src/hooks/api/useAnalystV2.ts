/**
 * API hooks for Auto-TRIZ v2 Analyst endpoints (WBS 8.5.1)
 *
 * Covers: Entry Grading, 5Why, KT Analysis, Function Analysis.
 * All hooks wrap the POST /analyst/* endpoints via useMutation.
 */

import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  entryGrading,
  fiveWhyAnalysis,
  ktAnalysis,
  functionAnalysis,
  getApiErrorMessage,
} from '@/lib/api';
import type {
  EntryGradingRequest,
  EntryGradingResponse,
  FiveWhyRequest,
  FiveWhyResponse,
  KtAnalysisRequest,
  KtIsIsNotResponse,
  FunctionAnalysisRequest,
  FunctionAnalysisResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Entry Grading — POST /analyst/entry-grading
// ---------------------------------------------------------------------------

export function useEntryGrading(_projectId?: string) {
  return useMutation<EntryGradingResponse, Error, EntryGradingRequest>({
    mutationFn: (body) => entryGrading(body),
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Entry Grading'));
    },
  });
}

// ---------------------------------------------------------------------------
// 5Why — POST /analyst/five-why
// ---------------------------------------------------------------------------

export function useFiveWhy(_projectId?: string) {
  return useMutation<FiveWhyResponse, Error, FiveWhyRequest>({
    mutationFn: (body) => fiveWhyAnalysis(body),
    onError: (err) => {
      toast.error(getApiErrorMessage(err, '5Why 分析'));
    },
  });
}

// ---------------------------------------------------------------------------
// KT Analysis — POST /analyst/kt-analysis
// ---------------------------------------------------------------------------

export function useKtAnalysis(_projectId?: string) {
  return useMutation<KtIsIsNotResponse, Error, KtAnalysisRequest>({
    mutationFn: (body) => ktAnalysis(body),
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'KT 分析'));
    },
  });
}

// ---------------------------------------------------------------------------
// Function Analysis — POST /analyst/function-analysis
// ---------------------------------------------------------------------------

export function useFunctionAnalysis(_projectId?: string) {
  return useMutation<FunctionAnalysisResponse, Error, FunctionAnalysisRequest>({
    mutationFn: (body) => functionAnalysis(body),
    onError: (err) => {
      toast.error(getApiErrorMessage(err, '功能分析'));
    },
  });
}
