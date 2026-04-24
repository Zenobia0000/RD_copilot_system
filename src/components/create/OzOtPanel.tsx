/**
 * OzOtPanel (WBS 8.6.2)
 *
 * Accordion section displayed before TRIZ solving in Create Step 1.
 * Shows Operating Zone (OZ), Operating Time (OT), and controllable
 * parameters (Px) from the oz-ot-analysis API.
 */

import { useState } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, Sparkles, MapPin, Clock, Sliders } from 'lucide-react';
import { useOzOtAnalysis } from '@/hooks/api/useCreateV2';
import type { OzOtAnalysisResponse } from '@/lib/api';

interface OzOtPanelProps {
  projectId: string;
  /** Pre-fill problem description from upstream context */
  problemDescription?: string;
  contradictions?: string[];
}

export function OzOtPanel({ projectId, problemDescription, contradictions }: OzOtPanelProps) {
  const [description, setDescription] = useState(problemDescription ?? '');
  const [result, setResult] = useState<OzOtAnalysisResponse | null>(null);

  const analysis = useOzOtAnalysis(projectId);

  const handleAnalyze = () => {
    if (!description.trim()) return;
    analysis.mutate(
      {
        project_id: projectId,
        problem_description: description.trim(),
        contradictions,
      },
      { onSuccess: (data) => setResult(data) },
    );
  };

  return (
    <Accordion type="single" collapsible defaultValue="">
      <AccordionItem value="oz-ot" className="border rounded-lg">
        <AccordionTrigger className="px-4 py-3 text-sm font-medium hover:no-underline">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            OZ/OT 分析（操作區域 / 操作時間）
            {result && (
              <Badge variant="secondary" className="text-[10px]">已完成</Badge>
            )}
          </div>
        </AccordionTrigger>
        <AccordionContent className="px-4 pb-4">
          <div className="space-y-4">
            {/* Input */}
            {!result && (
              <div className="space-y-3">
                <Textarea
                  placeholder="描述問題或系統以進行 OZ/OT 分析..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  disabled={analysis.isPending}
                />
                <Button
                  onClick={handleAnalyze}
                  disabled={!description.trim() || analysis.isPending}
                  size="sm"
                  variant="outline"
                >
                  {analysis.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4 mr-1.5" />
                  )}
                  分析 OZ/OT
                </Button>
              </div>
            )}

            {/* Result */}
            {result && (
              <div className="grid gap-3 sm:grid-cols-2">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="h-4 w-4 text-blue-600" />
                      <p className="text-xs font-medium text-muted-foreground">OZ 操作區域</p>
                    </div>
                    <p className="text-sm">{result.operating_zone}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="h-4 w-4 text-amber-600" />
                      <p className="text-xs font-medium text-muted-foreground">OT 操作時間</p>
                    </div>
                    <p className="text-sm">{result.operating_time}</p>
                  </CardContent>
                </Card>

                <Card className="sm:col-span-2">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Sliders className="h-4 w-4 text-green-600" />
                      <p className="text-xs font-medium text-muted-foreground">Px 可控參數</p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {result.controllable_params.map((p, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
                          {p}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {result.summary && (
                  <p className="text-xs text-muted-foreground sm:col-span-2">
                    {result.summary}
                  </p>
                )}

                <div className="sm:col-span-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setResult(null)}
                    className="text-xs"
                  >
                    重新分析
                  </Button>
                </div>
              </div>
            )}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
