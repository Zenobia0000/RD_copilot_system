import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Globe, ExternalLink } from "lucide-react";
import type { KnowledgeRef } from "@/types/knowledge";

interface KnowledgeRefsPanelProps {
  refs: KnowledgeRef[];
}

const RELEVANCE_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  High: "default",
  Medium: "secondary",
  Low: "outline",
};

export function KnowledgeRefsPanel({ refs }: KnowledgeRefsPanelProps) {
  if (!refs || refs.length === 0) return null;

  return (
    <div className="space-y-3 mt-6">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <BookOpen className="h-3.5 w-3.5" />
        <span className="font-medium">知識參考資料</span>
        <Badge variant="outline" className="text-[9px]">{refs.length} 筆</Badge>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {refs.map((ref) => (
          <Card key={ref.id} className="bg-muted/30 border-dashed">
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                {ref.type === "rag" ? (
                  <Badge variant="secondary" className="text-[9px] gap-1">
                    <BookOpen className="h-2.5 w-2.5" /> RAG
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-[9px] gap-1">
                    <Globe className="h-2.5 w-2.5" /> Web
                  </Badge>
                )}
                <Badge variant="outline" className="text-[9px] font-mono">{ref.id}</Badge>
                <Badge variant={RELEVANCE_VARIANT[ref.relevance]} className="text-[9px] ml-auto">
                  {ref.relevance}
                </Badge>
              </div>
              <p className="text-xs font-medium leading-snug">{ref.title}</p>
              <p className="text-[11px] text-muted-foreground leading-relaxed">{ref.summary}</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground">{ref.source}</span>
                {ref.url ? (
                  <a
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-primary flex items-center gap-0.5 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="h-2.5 w-2.5" /> 來源
                  </a>
                ) : ref.type === "rag" ? (
                  <a
                    href="/knowledge-base"
                    className="text-[10px] text-primary flex items-center gap-0.5 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <BookOpen className="h-2.5 w-2.5" /> 知識庫
                  </a>
                ) : (
                  <span className="text-[10px] text-muted-foreground/60 italic">無外部連結</span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
