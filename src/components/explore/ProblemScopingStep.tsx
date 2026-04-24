/**
 * ProblemScopingStep (WBS 8.5.4) — Level A Step 0
 *
 * Contains:
 * - 5Why chain display (why -> because pairs)
 * - KT Is/Is Not matrix table
 * - Calls useFiveWhy + useKtAnalysis hooks
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Loader2, ArrowDown, Sparkles } from 'lucide-react';
import { useFiveWhy, useKtAnalysis } from '@/hooks/api/useAnalystV2';
import type { FiveWhyResponse, KtIsIsNotResponse } from '@/lib/api';

interface ProblemScopingStepProps {
  projectId: string;
}

export function ProblemScopingStep({ projectId }: ProblemScopingStepProps) {
  const [description, setDescription] = useState('');
  const [fiveWhyResult, setFiveWhyResult] = useState<FiveWhyResponse | null>(null);
  const [ktResult, setKtResult] = useState<KtIsIsNotResponse | null>(null);

  const fiveWhy = useFiveWhy(projectId);
  const ktAnalysis = useKtAnalysis(projectId);

  const handleRunAll = () => {
    if (!description.trim()) return;
    const body = { project_id: projectId, problem_description: description.trim() };

    fiveWhy.mutate(body, {
      onSuccess: (data) => setFiveWhyResult(data),
    });

    ktAnalysis.mutate(body, {
      onSuccess: (data) => setKtResult(data),
    });
  };

  const isRunning = fiveWhy.isPending || ktAnalysis.isPending;

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="space-y-3">
        <Textarea
          placeholder="描述問題現象（例如：產品在高溫環境下出現翹曲變形）..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          disabled={isRunning}
        />
        <Button
          onClick={handleRunAll}
          disabled={!description.trim() || isRunning}
          size="sm"
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 mr-1.5" />
          )}
          執行 5Why + KT 分析
        </Button>
      </div>

      {/* 5Why Chain */}
      {fiveWhyResult && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">5Why 鏈式分析</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {fiveWhyResult.chain.map((pair, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <Badge variant="outline" className="text-xs shrink-0">
                      Why {i + 1}
                    </Badge>
                    {i < fiveWhyResult.chain.length - 1 && (
                      <ArrowDown className="h-4 w-4 text-muted-foreground mt-1" />
                    )}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">{pair.why}</p>
                    <p className="text-sm text-muted-foreground">
                      → {pair.because}
                    </p>
                  </div>
                </div>
              ))}
              {fiveWhyResult.root_cause && (
                <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
                  <p className="text-xs font-medium text-amber-800 mb-1">根本原因</p>
                  <p className="text-sm text-amber-900">{fiveWhyResult.root_cause}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* KT Is/Is Not Matrix */}
      {ktResult && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">KT Is / Is Not 矩陣</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[140px]">維度</TableHead>
                  <TableHead>Is (是)</TableHead>
                  <TableHead>Is Not (不是)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ktResult.rows.map((row, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium text-sm">{row.dimension}</TableCell>
                    <TableCell className="text-sm">{row.is}</TableCell>
                    <TableCell className="text-sm">{row.is_not}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {ktResult.summary && (
              <p className="text-xs text-muted-foreground mt-3">{ktResult.summary}</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
