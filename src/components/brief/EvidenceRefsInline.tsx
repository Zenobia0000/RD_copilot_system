import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight, ExternalLink, BookOpen, FileText, Lightbulb } from "lucide-react";
import { useState } from "react";
import type { EvidenceReference } from "@/lib/api";

interface EvidenceRefsInlineProps {
  references: EvidenceReference[];
  /** If provided, only show refs matching these IDs */
  filterRefIds?: string[];
}

const TYPE_CONFIG = {
  web_search: { label: "Web", icon: ExternalLink, variant: "default" as const },
  uploaded_doc: { label: "文件", icon: FileText, variant: "secondary" as const },
  engineering_reasoning: { label: "推論", icon: Lightbulb, variant: "outline" as const },
};

export function EvidenceRefsInline({ references, filterRefIds }: EvidenceRefsInlineProps) {
  const [open, setOpen] = useState(false);

  const filtered = filterRefIds
    ? references.filter((r) => filterRefIds.includes(r.ref_id))
    : references;

  if (filtered.length === 0) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
        <BookOpen className="h-3 w-3" />
        <span>{filtered.length} 項參考來源</span>
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-1.5">
        {filtered.map((ref) => {
          const config = TYPE_CONFIG[ref.ref_type] || TYPE_CONFIG.engineering_reasoning;
          const Icon = config.icon;
          return (
            <div
              key={ref.ref_id}
              className="flex items-start gap-2 text-xs p-2 rounded-md bg-muted/50 border border-muted"
            >
              <Badge variant={config.variant} className="text-[10px] shrink-0 mt-0.5">
                {config.label}
              </Badge>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[10px] text-muted-foreground">{ref.ref_id}</span>
                  <span className="font-medium truncate">{ref.title}</span>
                </div>
                {ref.snippet && (
                  <p className="text-muted-foreground mt-0.5 line-clamp-2">{ref.snippet}</p>
                )}
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-muted-foreground">{ref.source}</span>
                  {ref.url && (
                    <a
                      href={ref.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-0.5"
                    >
                      <Icon className="h-3 w-3" />
                      開啟
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CollapsibleContent>
    </Collapsible>
  );
}
