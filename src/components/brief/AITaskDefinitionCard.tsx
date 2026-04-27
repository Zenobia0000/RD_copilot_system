import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight, Pencil, RefreshCw, Save, X } from "lucide-react";
import type { TaskDefinition5W1H } from "@/types/taskDefinition";

interface AITaskDefinitionCardProps {
  data: TaskDefinition5W1H | null;
  missionReady: boolean;
  onRegenerate: () => void;
}

const LABELS: Record<keyof TaskDefinition5W1H, string> = {
  who: "Who (誰負責)",
  what: "What (做什麼)",
  where: "Where (在哪裡)",
  when: "When (時間軸)",
  why: "Why (為什麼)",
  how: "How (怎麼做)",
};

export function AITaskDefinitionCard({ data, missionReady, onRegenerate }: AITaskDefinitionCardProps) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<TaskDefinition5W1H | null>(null);
  const [loading, setLoading] = useState(false);

  // Reset loading when new data arrives
  if (data && loading) {
    setLoading(false);
  }

  const handleEdit = () => {
    if (data) {
      setEditData({ ...data });
      setEditing(true);
    }
  };

  const handleSaveEdit = () => {
    setEditing(false);
    setEditData(null);
  };

  const handleRegenerate = () => {
    setLoading(true);
    onRegenerate();
  };

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className="bg-muted/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">任務定義表</CardTitle>
                <Badge variant="secondary" className="text-xs">AI</Badge>
              </div>
              {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            {!missionReady ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                請先完成 Mission 填寫，AI 將自動生成任務定義表。
              </p>
            ) : loading ? (
              <div className="space-y-3 py-2">
                <p className="text-sm text-muted-foreground">AI 正在分析...</p>
                {Object.keys(LABELS).map((k) => (
                  <Skeleton key={k} className="h-8 w-full" />
                ))}
              </div>
            ) : data ? (
              <>
                <div className="space-y-2">
                  {(Object.keys(LABELS) as (keyof TaskDefinition5W1H)[]).map((key) => (
                    <div key={key} className="grid grid-cols-[120px_1fr] gap-2 items-start">
                      <span className="text-xs font-medium text-muted-foreground pt-2">{LABELS[key]}</span>
                      {editing ? (
                        <Textarea
                          value={editData?.[key] ?? ""}
                          onChange={(e) =>
                            setEditData((prev) => prev ? { ...prev, [key]: e.target.value } : prev)
                          }
                          rows={2}
                          className="bg-background"
                        />
                      ) : (
                        <p className="text-sm py-2 px-3 rounded bg-muted">{data[key]}</p>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-2">
                  {editing ? (
                    <>
                      <Button size="sm" onClick={handleSaveEdit}>
                        <Save className="h-3 w-3 mr-1" />
                        儲存
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditData(null); }}>
                        <X className="h-3 w-3 mr-1" />
                        取消
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button size="sm" variant="ghost" onClick={handleEdit}>
                        <Pencil className="h-3 w-3 mr-1" />
                        編輯
                      </Button>
                      <Button size="sm" variant="ghost" onClick={handleRegenerate}>
                        <RefreshCw className="h-3 w-3 mr-1" />
                        重新生成
                      </Button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground py-4 text-center">
                AI 任務定義表尚未生成。
              </p>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
