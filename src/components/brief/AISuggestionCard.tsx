import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Check, X, Loader2, Pencil } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface AISuggestionCardProps {
  title: string;
  /** If content is provided, show it as the AI result (editable). If null/undefined, show loading. */
  content?: string | null;
  /** Hint text explaining what changed (shown below the content). */
  changesSummary?: string;
  /** Whether the AI is currently generating. */
  isLoading?: boolean;
  /** Called with the (potentially edited) content when user clicks "採用". */
  onAdopt: (editedContent: string) => void | Promise<void>;
  onSkip: () => void;
  /** Number of rows for the editable textarea. Defaults to 4. */
  rows?: number;
  /** Disable all action buttons (adopt/edit/skip) while parent is processing. */
  disableActions?: boolean;
  /** Show adopting state on the adopt button. */
  isAdopting?: boolean;
}

export function AISuggestionCard({
  title,
  content,
  changesSummary,
  isLoading,
  onAdopt,
  onSkip,
  rows = 4,
  disableActions = false,
  isAdopting = false,
}: AISuggestionCardProps) {
  const [editedContent, setEditedContent] = useState(content ?? "");
  const [isEditing, setIsEditing] = useState(false);
  const prevContentRef = useRef(content);

  // Sync editedContent when content changes from parent (e.g. AI result arrives)
  useEffect(() => {
    if (content != null && content !== prevContentRef.current && !isEditing) {
      setEditedContent(content);
    }
    prevContentRef.current = content;
  }, [content, isEditing]);

  const handleAdopt = () => {
    if (disableActions || isLoading || isAdopting) return;
    onAdopt(editedContent);
  };

  return (
    <Card className="bg-muted/50 border-dashed border-primary/20">
      <CardContent className="pt-4 pb-3 space-y-3">
        <div className="flex items-center gap-2">
          {isLoading ? (
            <Loader2 className="h-4 w-4 text-primary animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 text-accent" />
          )}
          <span className="text-sm font-medium">{title}</span>
          <Badge variant="secondary" className="text-xs">AI</Badge>
        </div>

        {isLoading ? (
          <div className="flex items-center gap-2 py-4 justify-center text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            AI 正在分析並產出建議...
          </div>
        ) : content != null ? (
          <>
            {isEditing ? (
              <Textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                rows={rows}
                className="text-sm bg-background"
                autoFocus
                disabled={disableActions || isAdopting}
              />
            ) : (
              <div
                className="text-sm leading-relaxed p-2 rounded-md bg-background/50 border border-transparent hover:border-primary/20 cursor-pointer transition-colors group relative prose prose-sm dark:prose-invert max-w-none"
                onClick={() => {
                  if (disableActions || isAdopting) return;
                  setIsEditing(true);
                }}
              >
                <ReactMarkdown>{editedContent}</ReactMarkdown>
                <Pencil className="h-3 w-3 text-muted-foreground absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            )}

            {changesSummary && (
              <p className="text-xs text-muted-foreground italic">
                {changesSummary}
              </p>
            )}

            <div className="flex items-center gap-2">
              <Button size="sm" variant="default" onClick={handleAdopt} disabled={disableActions || isLoading || isAdopting}>
                {isAdopting ? (
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                ) : (
                  <Check className="h-3 w-3 mr-1" />
                )}
                {isAdopting ? "採用中..." : "採用"}
              </Button>
              {isEditing ? (
                <Button size="sm" variant="outline" disabled={disableActions || isAdopting} onClick={() => { setIsEditing(false); setEditedContent(content); }}>
                  還原
                </Button>
              ) : (
                <Button size="sm" variant="outline" disabled={disableActions || isAdopting} onClick={() => setIsEditing(true)}>
                  <Pencil className="h-3 w-3 mr-1" />
                  編輯
                </Button>
              )}
              <Button size="sm" variant="ghost" disabled={disableActions || isAdopting} onClick={onSkip}>
                <X className="h-3 w-3 mr-1" />
                跳過
              </Button>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
