import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { Loader2, Check, X, Lightbulb, Trash2, AlertTriangle } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import type { SocraticQuestion, QuestionCategory } from "@/types/explore";
import { CATEGORY_CONFIG } from "@/types/explore";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { socraticGenerate, socraticFollowUp } from "@/lib/api";

const QUESTION_CAP = 28; // 7 categories × 4 rounds max (including follow-ups)

interface SocraticTabProps {
  questions: SocraticQuestion[];
  onUpdateQuestions: (questions: SocraticQuestion[]) => void;
  onDeleteQuestion?: (questionId: string) => void;
  isBriefStale?: boolean;
  briefUpdatedAt?: string;
  projectId: string;
  mission?: string;
  constraints?: string[];
}

const CATEGORY_FILTERS: (QuestionCategory | 'all')[] = ['all', 'clarification', 'assumption', 'consequence', 'counter', 'origin', 'action', 'reframing'];

const AI_TAG_LABELS = {
  assumption: { label: '假設', color: '#8B5CF6', description: 'AI 偵測到此回答包含未驗證的假設，建議納入假設追蹤。' },
};

export function SocraticTab({ questions, onUpdateQuestions, onDeleteQuestion, isBriefStale = false, briefUpdatedAt, projectId, mission = '', constraints = [] }: SocraticTabProps) {
  const [categoryFilter, setCategoryFilter] = useState<QuestionCategory | 'all'>('all');
  const [isGenerating, setIsGenerating] = useState(false);
  const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({});

  const answeredCount = questions.filter((q) => q.answer && q.answer.trim().length >= 5).length;
  const totalCount = questions.length;
  const answeredCategories = new Set(
    questions.filter((q) => q.answer && q.answer.trim().length >= 5).map((q) => q.category)
  ).size;

  const filteredQuestions =
    categoryFilter === 'all' ? questions : questions.filter((q) => q.category === categoryFilter);

  const handleAnswer = (qId: string, value: string) => {
    setLocalAnswers((prev) => ({ ...prev, [qId]: value }));
  };
  // 離開輸入框時 → 才通知父元件存資料庫
  const handleAnswerBlur = (qId: string) => {
    const localValue = localAnswers[qId];
    if (localValue === undefined) return;
    // 跟資料庫的值一樣就不存
    const original = questions.find((q) => q.id === qId);
    if (original && original.answer === localValue) return;
    onUpdateQuestions(
      questions.map((q) => (q.id === qId ? { ...q, answer: localValue } : q))
    );
  };

  const handleConfirmTag = (qId: string) => {
    onUpdateQuestions(
      questions.map((q) => {
        if (q.id !== qId || !q.aiSuggestedTag) return q;
        return {
          ...q,
          aiTagConfirmed: true,
          taggedAsAssumption: true,
        };
      })
    );
    toast.success('已確認為假設，已同步至假設追蹤');
  };

  const handleRevertTag = (qId: string) => {
    onUpdateQuestions(
      questions.map((q) => {
        if (q.id !== qId) return q;
        return {
          ...q,
          aiTagConfirmed: false,
          taggedAsAssumption: false,
        };
      })
    );
    toast.info('已撤回假設標記，假設追蹤中的對應項目已移除');
  };

  const handleDismissTag = (qId: string) => {
    onUpdateQuestions(
      questions.map((q) => (q.id === qId ? {
        ...q,
        aiTagDismissed: true,
        aiTagConfirmed: false,
        taggedAsAssumption: false,
      } : q))
    );
    toast.info('已忽略 AI 建議');
  };

  const handleRestoreTag = (qId: string) => {
    onUpdateQuestions(
      questions.map((q) => (q.id === qId ? { ...q, aiTagDismissed: false } : q))
    );
    toast.success('已恢復 AI 建議');
  };

  const handleGenerateInitial = async () => {
    setIsGenerating(true);
    try {
      const result = await socraticGenerate({
        project_id: projectId,
        mission,
        constraints,
        existing_questions: questions.map((q) => q.text),
      });
      const newQuestions: SocraticQuestion[] = result.questions.map((q, i) => ({
        id: `q-${Date.now()}-${i}`,
        category: q.category as QuestionCategory,
        text: q.text,
        answer: null,
        taggedAsAssumption: false,
        aiSuggestedTag: q.suggested_tag as 'assumption' | 'contradiction' | null,
        aiTagConfirmed: false,
        aiTagDismissed: false,
      }));
      // Initial generation: backend returns exactly 7 (dict keyed by category)
      // Deduplicate against existing questions by category
      const seen = new Set(questions.map((q) => q.category));
      const deduped = newQuestions.filter((q) => !seen.has(q.category));
      onUpdateQuestions([...questions, ...deduped].slice(0, QUESTION_CAP));
      toast.success(`AI 已生成 ${deduped.length} 個問題`);
    } catch (err) {
      console.error("Socratic generation failed:", err);
      toast.error("AI 生成問題失敗，請確認後端服務是否啟動");
    } finally {
      setIsGenerating(false);
    }
  };

  // Brief impact: delete all old questions and fully regenerate from new brief
  const handleBriefImpact = async () => {
    setIsGenerating(true);
    try {
      // Delete all existing questions from DB
      if (onDeleteQuestion) {
        for (const q of questions) {
          onDeleteQuestion(q.id);
        }
      }

      // Clear locally cached answers
      setLocalAnswers({});

      // Regenerate from scratch with no existing questions
      const result = await socraticGenerate({
        project_id: projectId,
        mission,
        constraints,
        existing_questions: [],
      });

      const newQuestions: SocraticQuestion[] = result.questions.map((q, i) => ({
        id: `q-${Date.now()}-${i}`,
        category: q.category as QuestionCategory,
        text: q.text,
        answer: null,
        taggedAsAssumption: false,
        aiSuggestedTag: q.suggested_tag as 'assumption' | 'contradiction' | null,
        aiTagConfirmed: false,
        aiTagDismissed: false,
      }));

      // Full replacement — no old questions kept
      onUpdateQuestions(newQuestions);
      toast.success(`已重新生成 ${newQuestions.length} 個問題`);
    } catch (err) {
      console.error("Brief impact regeneration failed:", err);
      toast.error("AI 重新生成問題失敗，請確認後端服務是否啟動");
    } finally {
      setIsGenerating(false);
    }
  };

  if (questions.length === 0) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-muted-foreground font-medium">尚無問題</p>
        <p className="text-sm text-muted-foreground">請確認 Brief 已完成，AI 將自動生成問題</p>
        <AiButton loading={isGenerating} onClick={handleGenerateInitial}>
          生成問題
        </AiButton>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Purpose intro */}
      <SectionIntro text="AI 會根據您的 Brief 自動生成 7 類蘇格拉底式問題（含重構），引導您深入思考設計背後的假設與盲點。回答後 AI 會自動偵測是否包含假設或矛盾，並以建議標籤提示您確認。" />

      {/* Brief stale warning — full regeneration */}
      {isBriefStale && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/30 px-4 py-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium">Brief 已更新</p>
            <p className="text-xs text-muted-foreground">Brief 內容已變更，現有問題可能不再適用。點擊將清空所有問題並根據新 Brief 重新生成。</p>
          </div>
          <AiButton size="sm" loading={isGenerating} onClick={handleBriefImpact}>
            重新生成問題
          </AiButton>
        </div>
      )}

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">蘇格拉底問答 — AI 引導式問題探索</h2>
          <Badge className="bg-blue-500 text-white text-xs">
            已回答 {answeredCount}/{totalCount}
          </Badge>
        </div>
        <Progress value={(answeredCategories / 7) * 100} className="h-2" />
        <p className="text-xs text-muted-foreground">{answeredCategories}/7 類別已回答</p>
      </div>

      {/* Category filter pills */}
      <div className="flex flex-wrap gap-2">
        {CATEGORY_FILTERS.map((cat) => {
          const isActive = categoryFilter === cat;
          const config = cat === 'all' ? null : CATEGORY_CONFIG[cat];
          return (
            <Button
              key={cat}
              variant={isActive ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-7 rounded-full"
              style={isActive && config ? { backgroundColor: config.color } : {}}
              onClick={() => setCategoryFilter(cat)}
            >
              {cat === 'all' ? '全部' : config!.labelZh}
            </Button>
          );
        })}
      </div>

      {/* Question cards */}
      <div className="space-y-4">
        {filteredQuestions.map((q) => {
          const config = CATEGORY_CONFIG[q.category] ?? { label: q.category, labelZh: q.category, color: '#6B7280' };
          const isAnswered = q.answer && q.answer.trim().length >= 5;
          const hasPendingSuggestion = q.aiSuggestedTag && !q.aiTagConfirmed && !q.aiTagDismissed;
          const hasConfirmedTag = q.aiSuggestedTag && q.aiTagConfirmed;
          const hasDismissedTag = q.aiSuggestedTag && q.aiTagDismissed && !q.aiTagConfirmed;
          const tagConfig = q.aiSuggestedTag ? AI_TAG_LABELS[q.aiSuggestedTag] : null;
          const isReplaced = !!q.replacedAt;

          return (
            <Card
              key={q.id}
              className={`transition-colors ${
                isReplaced
                  ? 'border-l-[3px] border-l-amber-400 bg-amber-50/30 dark:bg-amber-950/10'
                  : isAnswered
                    ? 'border-l-[3px] border-l-green-600'
                    : ''
              }`}
            >
              <CardContent className="p-4 space-y-3">
                {/* Replaced banner */}
                {isReplaced && (
                  <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span>此題因 Brief 更新已被替換，請重新回答</span>
                  </div>
                )}

                {/* AI question area */}
                <div className="bg-muted rounded-md p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="secondary" className="text-[10px]">AI</Badge>
                      <Badge
                        className="text-[10px] text-white"
                        style={{ backgroundColor: config.color }}
                      >
                        {config.labelZh}
                      </Badge>
                      {isReplaced && (
                        <Badge className="text-[10px] bg-amber-400 text-amber-950">已替換</Badge>
                      )}
                    </div>
                    {onDeleteQuestion && (
                      <button
                        onClick={() => onDeleteQuestion(q.id)}
                        className="p-1 rounded hover:bg-destructive/10"
                        title="刪除此問題"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </button>
                    )}
                  </div>
                  <p className="text-sm">{q.text}</p>
                </div>

                {/* User answer */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-destructive">*</span>
                    <span className="text-xs text-muted-foreground">您的回答</span>
                  </div>
                  <Textarea
                    value={localAnswers[q.id] ?? q.answer ?? ''}
                    onChange={(e) => handleAnswer(q.id, e.target.value)}
                    onBlur={() => handleAnswerBlur(q.id)}
                    placeholder="請在此輸入您的回答..."
                    rows={2}
                    maxLength={1000}
                    className="min-h-[60px] bg-background"
                  />
                  {(() => {
                    const val = (localAnswers[q.id] ?? q.answer ?? '').trim();
                    return val.length > 0 && val.length < 5 ? (
                      <p className="text-xs text-destructive">回答至少需要 5 個字元</p>
                    ) : null;
                  })()}
                </div>

                {/* AI auto-detected tag — pending confirmation */}
                {hasPendingSuggestion && tagConfig && (
                  <div
                    className="flex items-center gap-3 rounded-lg border px-3 py-2.5 animate-in fade-in slide-in-from-top-1"
                    style={{ borderColor: `${tagConfig.color}40`, backgroundColor: `${tagConfig.color}08` }}
                  >
                    <Lightbulb className="h-4 w-4 shrink-0" style={{ color: tagConfig.color }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Badge className="text-[10px] text-white" style={{ backgroundColor: tagConfig.color }}>
                          AI 建議
                        </Badge>
                        <span className="text-xs font-medium">可能是{tagConfig.label}</span>
                        <HelpTooltip text={tagConfig.description} />
                      </div>
                    </div>
                    <div className="flex gap-1.5 shrink-0">
                      <Button
                        size="sm"
                        className="h-7 text-xs text-white"
                        style={{ backgroundColor: tagConfig.color }}
                        onClick={() => handleConfirmTag(q.id)}
                      >
                        <Check className="h-3 w-3 mr-1" /> 確認
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-xs"
                        onClick={() => handleDismissTag(q.id)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Confirmed tag badge */}
                {hasConfirmedTag && tagConfig && (
                  <div className="flex items-center gap-2">
                    <Badge className="text-[10px] text-white" style={{ backgroundColor: tagConfig.color }}>
                      已標記為假設
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">
                      已自動同步至假設追蹤
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-6 text-[10px] text-muted-foreground hover:text-destructive ml-auto"
                      onClick={() => handleRevertTag(q.id)}
                    >
                      撤回假設
                    </Button>
                  </div>
                )}

                {/* Dismissed tag — recoverable */}
                {hasDismissedTag && tagConfig && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-muted-foreground">AI 曾建議標記為{tagConfig.label}，已忽略</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-6 text-[10px] text-muted-foreground hover:text-foreground"
                      onClick={() => handleRestoreTag(q.id)}
                    >
                      恢復建議
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Batch confirm bar — triggers tagging + depth analysis + follow-up */}
      {answeredCount > 0 && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <div className="flex-1">
              <p className="text-sm font-medium">本輪回答確認</p>
              <p className="text-xs text-muted-foreground">
                已回答 {answeredCount} 題，{answeredCategories}/7 類別覆蓋。確認後 AI 分析標記 + 評估深度，必要時追問。
              </p>
            </div>
            <Button
              disabled={isGenerating}
              onClick={async () => {
                setIsGenerating(true);
                toast.success(`已確認 ${answeredCount} 題回答，AI 正在分析...`);

                // Step 1: Heuristic tagging
                const tagByHeuristic = (q: SocraticQuestion): 'assumption' | null => {
                  const a = q.answer ?? '';
                  const isAssumption = q.category === 'assumption'
                    || a.includes('假設') || a.includes('基於') || a.includes('認為')
                    || a.includes('預期') || a.includes('如果');
                  if (isAssumption) return 'assumption';
                  return null;
                };

                let tagged = questions.map((q) => {
                  if (q.answer && q.answer.trim().length >= 5 && !q.aiSuggestedTag && !q.aiTagDismissed) {
                    const tag = tagByHeuristic(q);
                    if (tag) return { ...q, aiSuggestedTag: tag };
                  }
                  return q;
                });
                onUpdateQuestions(tagged);

                // Step 2: AI depth analysis + follow-up (if under cap)
                try {
                  const answeredQs = tagged
                    .filter((q) => q.answer && q.answer.trim().length >= 5)
                    .map((q) => ({ id: q.id, category: q.category, question: q.text, answer: q.answer! }));

                  const result = await socraticFollowUp({
                    project_id: projectId,
                    mission,
                    constraints,
                    answered_questions: answeredQs,
                  });

                  if (result.depth_sufficient) {
                    toast.success('AI 判定回答深度充分，探索完成！');
                  } else if (result.follow_ups.length > 0 && questions.length < QUESTION_CAP) {
                    const slots = QUESTION_CAP - questions.length;
                    const followUps: SocraticQuestion[] = result.follow_ups.slice(0, slots).map((f, i) => ({
                      id: `fu-${Date.now()}-${i}`,
                      category: f.category as QuestionCategory,
                      text: f.text,
                      answer: null,
                      taggedAsAssumption: false,
                      aiSuggestedTag: null,
                      aiTagConfirmed: false,
                      aiTagDismissed: false,
                    }));
                    onUpdateQuestions([...tagged, ...followUps]);
                    toast.info(`AI 追問 ${followUps.length} 題（深度不足的類別）`);
                  } else {
                    toast.info('AI 分析完成，請檢查標記建議');
                  }
                } catch {
                  toast.info('標記完成（深度分析離線，已跳過追問）');
                }
                setIsGenerating(false);
              }}
              className="shrink-0"
            >
              {isGenerating ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
              確認本輪回答
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Question cap indicator */}
      <p className="text-xs text-muted-foreground text-center">
        {questions.length}/{QUESTION_CAP} 題
        {questions.length >= QUESTION_CAP && ' — 已達上限'}
      </p>
    </div>
  );
}
