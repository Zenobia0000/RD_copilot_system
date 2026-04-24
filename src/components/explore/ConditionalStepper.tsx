/**
 * ConditionalStepper (WBS 8.5.3)
 *
 * Renders different exploration flows based on entry grading level:
 * - Level A: 5-step stepper (Problem Scoping -> Function Analysis -> Socratic -> Contradiction -> CLD)
 * - Level B: delegates to existing 3-tab layout
 *
 * This component is designed to be embedded within Explore.tsx as an
 * optional enhancement — it does NOT replace the existing tabs.
 */

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { ProblemScopingStep } from './ProblemScopingStep';
import { FunctionAnalysisStep } from './FunctionAnalysisStep';

interface ConditionalStepperProps {
  level: 'A' | 'B';
  projectId: string;
  /** When level=B, render this content (the existing 3-tab layout) */
  levelBContent?: React.ReactNode;
}

interface StepConfig {
  key: string;
  label: string;
  description: string;
}

const LEVEL_A_STEPS: StepConfig[] = [
  { key: 'scoping', label: 'Problem Scoping', description: '5Why + KT Is/Is Not' },
  { key: 'function', label: 'Function Analysis', description: '組件交互 + SF 診斷' },
  { key: 'socratic', label: 'Socratic Q&A', description: '蘇格拉底式深度問答' },
  { key: 'contradiction', label: 'Contradiction', description: '矛盾識別與分類' },
  { key: 'cld', label: 'CLD', description: '因果迴路圖' },
];

export function ConditionalStepper({ level, projectId, levelBContent }: ConditionalStepperProps) {
  const [currentStep, setCurrentStep] = useState(0);

  // Level B: just render the existing content
  if (level === 'B') {
    return <>{levelBContent}</>;
  }

  // Level A: 5-step stepper
  const steps = LEVEL_A_STEPS;
  const step = steps[currentStep];

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-1">
        {steps.map((s, i) => (
          <div key={s.key} className="flex items-center">
            <button
              onClick={() => setCurrentStep(i)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
                i === currentStep
                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                  : i < currentStep
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-muted text-muted-foreground',
              )}
            >
              {i < currentStep ? (
                <Check className="h-3 w-3" />
              ) : (
                <span className="w-4 text-center">{i + 1}</span>
              )}
              <span className="hidden sm:inline">{s.label}</span>
            </button>
            {i < steps.length - 1 && (
              <div className={cn(
                'w-6 h-px mx-1',
                i < currentStep ? 'bg-green-300' : 'bg-border',
              )} />
            )}
          </div>
        ))}
      </div>

      {/* Step content */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">{step.label}</CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">{step.description}</p>
            </div>
            <Badge variant="outline" className="text-xs">
              Step {currentStep + 1}/{steps.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {step.key === 'scoping' && (
            <ProblemScopingStep projectId={projectId} />
          )}
          {step.key === 'function' && (
            <FunctionAnalysisStep projectId={projectId} />
          )}
          {step.key === 'socratic' && (
            <div className="text-sm text-muted-foreground py-8 text-center">
              切換至上方「蘇格拉底問答」tab 使用完整功能
            </div>
          )}
          {step.key === 'contradiction' && (
            <div className="text-sm text-muted-foreground py-8 text-center">
              切換至上方「矛盾識別」tab 使用完整功能
            </div>
          )}
          {step.key === 'cld' && (
            <div className="text-sm text-muted-foreground py-8 text-center">
              切換至上方「因果迴路圖」tab 使用完整功能
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          上一步
        </Button>
        <Button
          size="sm"
          onClick={() => setCurrentStep((s) => Math.min(steps.length - 1, s + 1))}
          disabled={currentStep === steps.length - 1}
        >
          下一步
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}
