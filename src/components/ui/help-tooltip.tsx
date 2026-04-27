import { HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface HelpTooltipProps {
  text: string;
  className?: string;
  side?: "top" | "bottom" | "left" | "right";
  maxWidth?: string;
}

export function HelpTooltip({ text, className = "", side = "top", maxWidth = "max-w-xs" }: HelpTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className={`inline-flex items-center justify-center rounded-full text-muted-foreground/60 hover:text-muted-foreground transition-colors focus:outline-none ${className}`}
          aria-label="說明"
        >
          <HelpCircle className="h-3.5 w-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent side={side} className={`${maxWidth} text-xs leading-relaxed`}>
        <p>{text}</p>
      </TooltipContent>
    </Tooltip>
  );
}
