import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Sparkles, Check, X, Edit2, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ExtractedItem {
  id: string;
  type: "constraint" | "assumption" | "data";
  content: string;
  source: string; // source file name
  accepted: boolean;
  editing: boolean;
}

interface AIExtractionResultsProps {
  items: ExtractedItem[];
  onItemsChange: (items: ExtractedItem[]) => void;
  onAcceptAll: () => void;
  visible: boolean;
}

const typeLabels: Record<ExtractedItem["type"], { label: string; color: string }> = {
  constraint: { label: "約束", color: "bg-primary/10 text-primary" },
  assumption: { label: "假設", color: "bg-warning/10 text-warning" },
  data: { label: "數據", color: "bg-info/10 text-info" },
};

export function AIExtractionResults({ items, onItemsChange, onAcceptAll, visible }: AIExtractionResultsProps) {
  const [reviewMode, setReviewMode] = useState(false);

  if (!visible || items.length === 0) return null;

  const acceptedCount = items.filter((i) => i.accepted).length;

  const toggleAccept = (id: string) => {
    onItemsChange(items.map((i) => i.id === id ? { ...i, accepted: !i.accepted } : i));
  };

  const toggleEdit = (id: string) => {
    onItemsChange(items.map((i) => i.id === id ? { ...i, editing: !i.editing } : i));
  };

  const updateContent = (id: string, content: string) => {
    onItemsChange(items.map((i) => i.id === id ? { ...i, content } : i));
  };

  const removeItem = (id: string) => {
    onItemsChange(items.filter((i) => i.id !== id));
  };

  return (
    <Card className="border-dashed border-accent/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" />
            <CardTitle className="text-base">AI 提取結果</CardTitle>
            <Badge variant="secondary" className="text-xs">{acceptedCount}/{items.length} 已接受</Badge>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setReviewMode(!reviewMode)}>
              {reviewMode ? "退出審查" : "逐條審查"}
            </Button>
            <Button size="sm" onClick={onAcceptAll}>
              <Check className="h-3 w-3 mr-1" />
              全部接受
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((item) => {
          const typeConf = typeLabels[item.type];
          return (
            <div
              key={item.id}
              className={cn(
                "flex items-start gap-3 rounded-md border p-3 transition-colors",
                item.accepted && "bg-muted/40 border-primary/30"
              )}
            >
              <Badge variant="outline" className={cn("text-[10px] shrink-0 mt-0.5", typeConf.color)}>
                {typeConf.label}
              </Badge>
              <div className="flex-1 min-w-0 space-y-1">
                {item.editing ? (
                  <Input
                    value={item.content}
                    onChange={(e) => updateContent(item.id, e.target.value)}
                    onBlur={() => toggleEdit(item.id)}
                    autoFocus
                    className="text-sm"
                  />
                ) : (
                  <p className="text-sm">{item.content}</p>
                )}
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  來源：{item.source}
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button onClick={() => toggleEdit(item.id)} className="text-muted-foreground hover:text-foreground p-1">
                  <Edit2 className="h-3.5 w-3.5" />
                </button>
                <button onClick={() => toggleAccept(item.id)} className={cn("p-1", item.accepted ? "text-primary" : "text-muted-foreground hover:text-primary")}>
                  <Check className="h-3.5 w-3.5" />
                </button>
                <button onClick={() => removeItem(item.id)} className="text-muted-foreground hover:text-destructive p-1">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
