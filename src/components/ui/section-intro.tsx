import { Info } from "lucide-react";

interface SectionIntroProps {
  text: string;
  className?: string;
}

export function SectionIntro({ text, className = "" }: SectionIntroProps) {
  return (
    <div className={`flex items-start gap-2 rounded-lg bg-muted/50 border border-border/50 px-3 py-2.5 ${className}`}>
      <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
      <p className="text-xs text-muted-foreground leading-relaxed">{text}</p>
    </div>
  );
}
