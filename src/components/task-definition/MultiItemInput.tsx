import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, X } from "lucide-react";
import { useState } from "react";

interface MultiItemInputProps {
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  errors?: string[];
}

export function MultiItemInput({ items, onChange, placeholder, errors }: MultiItemInputProps) {
  const [draft, setDraft] = useState("");

  const addItem = () => {
    const trimmed = draft.trim();
    if (trimmed) {
      onChange([...items, trimmed]);
      setDraft("");
    }
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addItem();
    }
  };

  return (
    <div className="space-y-2">
      {/* Existing items */}
      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {items.map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-1.5 rounded-md border bg-card px-3 py-1.5 text-sm"
            >
              <span className="max-w-[300px] truncate">{item}</span>
              <button
                type="button"
                onClick={() => removeItem(index)}
                className="text-muted-foreground hover:text-destructive transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          maxLength={200}
          className="flex-1"
        />
        <Button type="button" variant="outline" size="icon" onClick={addItem} disabled={!draft.trim()}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Errors */}
      {errors && errors.length > 0 && (
        <div className="space-y-0.5">
          {errors.map((err, i) => (
            <p key={i} className="text-xs text-destructive">{err}</p>
          ))}
        </div>
      )}
    </div>
  );
}
