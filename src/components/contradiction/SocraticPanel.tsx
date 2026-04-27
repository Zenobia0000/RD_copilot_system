import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp, MessageCircleQuestion } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { socraticGenerate } from "@/lib/api";

interface SocraticQuestion {
  type: string;
  typeLabel: string;
  question: string;
}

const questionTypes = [
  { key: "clarification", label: "澄清", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  { key: "assumption", label: "假設挑戰", color: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200" },
  { key: "evidence", label: "證據追問", color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200" },
  { key: "perspective", label: "觀點轉換", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200" },
  { key: "causal", label: "因果追問", color: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200" },
  { key: "consequence", label: "後果探索", color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200" },
  { key: "reframing", label: "重構", color: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200" },
];

const mockSocraticQuestions: SocraticQuestion[] = [
  { type: "clarification", typeLabel: "澄清", question: "你所說的「效能」具體指的是哪個量化指標？是功率、吞吐量、還是響應時間？" },
  { type: "assumption", typeLabel: "假設挑戰", question: "你假設增加轉速必然導致噪音增加，但是否存在某種轉速範圍內噪音不會顯著增加的情況？" },
  { type: "evidence", typeLabel: "證據追問", question: "目前有哪些測試數據支持「轉速提高 → 噪音惡化」的關聯？這個關聯是線性的嗎？" },
  { type: "perspective", typeLabel: "觀點轉換", question: "如果從使用者的角度來看，噪音是否真的是不可接受的？在什麼使用情境下噪音可以被容忍？" },
  { type: "causal", typeLabel: "因果追問", question: "噪音增加的根本原因是什麼？是機械振動、空氣動力學效應、還是結構共振？" },
  { type: "consequence", typeLabel: "後果探索", question: "如果我們接受較高的噪音水平，對產品市場定位和用戶滿意度會有什麼具體影響？" },
  { type: "reframing", typeLabel: "重構", question: "是否可以重新定義問題：不是「如何在高轉速下降低噪音」，而是「如何在不提高轉速的情況下達到同等效能」？" },
];

interface SocraticPanelProps {
  description: string;
  projectId?: string;
  mission?: string;
  constraints?: string[];
  existingQuestions?: string[];
}

const SocraticPanel = ({ description, projectId, mission, constraints, existingQuestions }: SocraticPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [questions, setQuestions] = useState<SocraticQuestion[]>([]);

  const handleGenerate = async () => {
    if (!description || description.length < 10) return;
    setIsLoading(true);
    try {
      const combinedMission = mission
        ? `${mission}\n\n目前分析的矛盾描述：${description}`
        : description;
      const result = await socraticGenerate({
        project_id: projectId || "",
        mission: combinedMission,
        constraints: constraints || [],
        existing_questions: existingQuestions || [],
      });
      const mapped: SocraticQuestion[] = result.questions.map((q, i) => ({
        type: q.category,
        typeLabel: questionTypes.find((t) => t.key === q.category)?.label ?? q.category,
        question: q.text,
      }));
      setQuestions(mapped.length > 0 ? mapped : mockSocraticQuestions);
    } catch {
      setQuestions(mockSocraticQuestions);
    } finally {
      setIsLoading(false);
    }
  };

  const getTypeStyle = (type: string) => {
    return questionTypes.find((t) => t.key === type)?.color ?? "";
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="outline" size="sm" className="w-full justify-between">
          <span className="flex items-center gap-1.5">
            <MessageCircleQuestion className="h-4 w-4" />
            七類蘇格拉底提問輔助
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-3 space-y-3">
        <div className="flex flex-wrap gap-1.5 mb-2">
          {questionTypes.map((t) => (
            <Badge key={t.key} variant="outline" className={`text-xs ${t.color}`}>
              {t.label}
            </Badge>
          ))}
        </div>

        <AiButton
          size="sm"
          loading={isLoading}
          onClick={handleGenerate}
          disabled={isLoading || !description || description.length < 10}
        >
          生成引導問題
        </AiButton>

        {questions.length > 0 && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {questions.map((q, i) => (
              <Card key={i} className="rounded-lg">
                <CardContent className="p-3 flex gap-2 items-start">
                  <Badge variant="outline" className={`text-xs shrink-0 ${getTypeStyle(q.type)}`}>
                    {q.typeLabel}
                  </Badge>
                  <p className="text-sm text-muted-foreground">{q.question}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {questions.length === 0 && !isLoading && (
          <p className="text-xs text-muted-foreground">輸入矛盾描述後，點擊「生成引導問題」以獲得 AI 輔助。</p>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
};

export default SocraticPanel;
