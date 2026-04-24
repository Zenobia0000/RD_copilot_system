/**
 * FunctionAnalysisStep (WBS 8.5.5) — Level A Step 1
 *
 * Contains:
 * - Component interaction list/cards
 * - SF diagnosis summary
 * - Calls useFunctionAnalysis hook
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { useFunctionAnalysis } from '@/hooks/api/useAnalystV2';
import type { FunctionAnalysisResponse } from '@/lib/api';

interface FunctionAnalysisStepProps {
  projectId: string;
}

export function FunctionAnalysisStep({ projectId }: FunctionAnalysisStepProps) {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<FunctionAnalysisResponse | null>(null);

  const analysis = useFunctionAnalysis(projectId);

  const handleRun = () => {
    if (!description.trim()) return;
    analysis.mutate(
      { project_id: projectId, problem_description: description.trim() },
      { onSuccess: (data) => setResult(data) },
    );
  };

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="space-y-3">
        <Textarea
          placeholder="描述系統或子系統的功能（例如：散熱模組負責將熱量從 CPU 傳導至散熱片）..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          disabled={analysis.isPending}
        />
        <Button
          onClick={handleRun}
          disabled={!description.trim() || analysis.isPending}
          size="sm"
        >
          {analysis.isPending ? (
            <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 mr-1.5" />
          )}
          執行功能分析
        </Button>
      </div>

      {result && (
        <>
          {/* Component Interaction Cards */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">組件交互圖</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {result.components.map((comp, i) => (
                  <div
                    key={i}
                    className="rounded-lg border p-3 space-y-2"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">{comp.name}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{comp.role}</p>
                    {comp.interactions.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">交互：</p>
                        {comp.interactions.map((inter, j) => (
                          <div key={j} className="flex items-center gap-1.5 text-xs">
                            <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                            <span>{inter}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* SF Diagnosis Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Su-Field 診斷摘要</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">S1 (物質1)</p>
                  <p className="text-sm font-medium">{result.sf_diagnosis.substance_1}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">S2 (物質2)</p>
                  <p className="text-sm font-medium">{result.sf_diagnosis.substance_2}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">F (場)</p>
                  <p className="text-sm font-medium">{result.sf_diagnosis.field}</p>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                <p className="text-xs font-medium text-blue-800 mb-1">診斷</p>
                <p className="text-sm text-blue-900">{result.sf_diagnosis.diagnosis}</p>
              </div>
              {result.summary && (
                <p className="text-xs text-muted-foreground mt-3">{result.summary}</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
