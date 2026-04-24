/**
 * EntryGradingModal (WBS 8.5.2)
 *
 * A dialog that collects a problem description, calls the entry-grading API,
 * and displays the resulting level (A/B/C) with reasoning.
 *
 * - Level A: triggers the 5-step ConditionalStepper
 * - Level B: keeps the original 3-tab Explore layout
 * - Level C: informational only
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles } from 'lucide-react';
import { useEntryGrading } from '@/hooks/api/useAnalystV2';
import type { EntryGradingResponse } from '@/lib/api';

interface EntryGradingModalProps {
  projectId: string;
  onGraded?: (result: EntryGradingResponse) => void;
  children?: React.ReactNode;
}

const LEVEL_STYLES: Record<string, { bg: string; label: string; description: string }> = {
  A: {
    bg: 'bg-red-100 text-red-800 border-red-300',
    label: 'Level A - 複雜問題',
    description: '建議使用完整 5-step 流程（Problem Scoping → Function Analysis → Socratic → Contradiction → CLD）',
  },
  B: {
    bg: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    label: 'Level B - 一般問題',
    description: '使用標準 3-tab 探索流程即可',
  },
  C: {
    bg: 'bg-green-100 text-green-800 border-green-300',
    label: 'Level C - 簡單問題',
    description: '問題較為直接，可直接進入解題階段',
  },
};

export function EntryGradingModal({ projectId, onGraded, children }: EntryGradingModalProps) {
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<EntryGradingResponse | null>(null);

  const grading = useEntryGrading(projectId);

  const handleSubmit = () => {
    if (!description.trim()) return;
    grading.mutate(
      { project_id: projectId, problem_description: description.trim() },
      {
        onSuccess: (data) => {
          setResult(data);
          onGraded?.(data);
        },
      },
    );
  };

  const handleClose = () => {
    setOpen(false);
    // Reset state after close animation
    setTimeout(() => {
      setResult(null);
      setDescription('');
    }, 200);
  };

  const style = result ? LEVEL_STYLES[result.level] : null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children ?? (
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4 mr-1.5" />
            問題分級
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>問題入口分級 (Entry Grading)</DialogTitle>
          <DialogDescription>
            輸入問題描述，AI 將評估問題複雜度並建議適合的探索流程。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <Textarea
            placeholder="描述您遇到的技術問題或設計挑戰..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            disabled={grading.isPending}
          />

          {result && style && (
            <div className={`rounded-lg border p-4 ${style.bg}`}>
              <div className="flex items-center gap-2 mb-2">
                <Badge className={style.bg}>{style.label}</Badge>
              </div>
              <p className="text-sm mb-2">{style.description}</p>
              <div className="mt-3 pt-3 border-t border-current/10">
                <p className="text-xs font-medium mb-1">AI 推理：</p>
                <p className="text-xs opacity-80">{result.reasoning}</p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {result ? (
            <Button onClick={handleClose}>確認</Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!description.trim() || grading.isPending}
            >
              {grading.isPending && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
              分析問題
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
