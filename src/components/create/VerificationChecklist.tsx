/**
 * VerificationChecklist — filters needs_verification DraftValues,
 * groups by top-level system → module/component sub-codes,
 * provides checkbox tracking + CSV export.
 *
 * Wave 2C: Cards are grouped by root system code (e.g. A1, B1).
 * Expanding a system card reveals module/component sub-groups inside.
 *
 * @see plans/concept-pack-to-engineering-specs.md
 * @see src/types/generated/engineeringSpec.ts
 */

import { useState, useMemo, useCallback } from "react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  ChevronRight,
  ClipboardCheck,
  Download,
  CheckCheck,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";

import type {
  EngineeringSpecDraftResponse,
  DraftValue,
  DraftCategory,
} from "@/types/generated/engineeringSpec";
import {
  CONFIDENCE_COLORS,
  DRAFT_CATEGORIES,
} from "@/types/generated/engineeringSpec";
import type { SuggestedSubsystem } from "@/types/generated/subsystem";
import { Progress } from "@/components/ui/progress";

// ---------------------------------------------------------------------------
// Code → Name mapping (subsystem_tree walk)
// ---------------------------------------------------------------------------

/**
 * 遞迴走訪 subsystem_tree，建立 code → name 對照表。
 * 系統節點使用 concept_origin_code；模組/元件子節點使用位置碼
 * (parentCode.1, parentCode.2, ...) 以匹配 EngineeringSpecDraft.subsystem_code。
 */
function buildCodeToNameMap(tree: SuggestedSubsystem[]): Map<string, string> {
  const map = new Map<string, string>();
  function walk(nodes: SuggestedSubsystem[], parentCode: string | null) {
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      const code =
        node.concept_origin_code ??
        (parentCode ? `${parentCode}.${i + 1}` : null);
      if (code) {
        map.set(code, node.name);
      }
      // Also register name → name so that name-based subsystem_codes can resolve
      map.set(node.name, node.name);
      if (node.children?.length) walk(node.children, code ?? null);
    }
  }
  walk(tree, null);
  return map;
}

/**
 * 走訪 subsystem_tree，建立 (concept_origin_code | name) → 根系統 code 的映射。
 * 由於 module/component 層級的 draft.subsystem_code 使用 **name**（非點記法），
 * 故需要以 name 做為查詢 key，才能正確歸屬到其所屬的頂層系統。
 */
function buildCodeToRootMap(tree: SuggestedSubsystem[]): Map<string, string> {
  const map = new Map<string, string>();
  function walk(nodes: SuggestedSubsystem[], rootCode: string | null) {
    for (const node of nodes) {
      // When we encounter a system-level node, use its code as the new root
      const currentRoot =
        node.level === "system" && node.concept_origin_code
          ? node.concept_origin_code
          : rootCode;
      // Register concept_origin_code → root (for system-level drafts)
      if (node.concept_origin_code && currentRoot) {
        map.set(node.concept_origin_code, currentRoot);
      }
      // Register name → root (for module/component-level drafts whose
      // subsystem_code is the node name rather than dot-notation)
      if (currentRoot) {
        map.set(node.name, currentRoot);
      }
      if (node.children?.length) walk(node.children, currentRoot);
    }
  }
  walk(tree, null);
  return map;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface VerificationChecklistProps {
  /** Pipeline response containing all subsystem drafts. */
  data: EngineeringSpecDraftResponse;
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers (reuse patterns from EngineeringSpecDraftPanel)
// ---------------------------------------------------------------------------

/** Format a DraftValue's value for display. */
function fmtValue(v: DraftValue): string {
  if (v.value == null) return "—";
  if (typeof v.value === "number") return String(v.value);
  if (typeof v.value === "string") return v.value;
  try {
    return JSON.stringify(v.value);
  } catch {
    return String(v.value);
  }
}

/** Human-readable field name: snake_case → Title Case. */
function humanize(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Suggest a verification method based on field_name + source.
 * Provides reasonable default suggestions; not a fixed mapping —
 * real verification guidance would come from domain experts.
 */
function suggestVerificationMethod(field: string, source: string): string {
  const fl = field.toLowerCase();
  const sl = source.toLowerCase();

  // Source-specific overrides
  if (sl.includes("datasheet")) return "核對原廠 Datasheet";
  if (sl.includes("standard")) return "查閱對應規範文件";
  if (sl.includes("learned")) return "對照已驗證元件資料庫";

  // Field-based suggestions
  if (fl.includes("mass") || fl.includes("weight"))
    return "秤重實測或 CAD 計算";
  if (fl.includes("dimension") || fl.includes("length") || fl.includes("width") || fl.includes("height") || fl.includes("diameter"))
    return "CAD 模型量測或實物量測";
  if (fl.includes("torque"))
    return "查閱馬達 Datasheet 或扭矩測試";
  if (fl.includes("gear") || fl.includes("ratio"))
    return "確認齒輪箱規格";
  if (fl.includes("thermal") || fl.includes("temperature") || fl.includes("heat"))
    return "熱模擬或實測";
  if (fl.includes("power") || fl.includes("watt"))
    return "電氣量測或 Datasheet 確認";
  if (fl.includes("voltage") || fl.includes("current"))
    return "電氣量測或 Datasheet 確認";
  if (fl.includes("material"))
    return "確認材料規格書或測試報告";
  if (fl.includes("waterproof") || fl.includes("ip"))
    return "查閱防護等級測試報告";
  if (fl.includes("surface") || fl.includes("finish"))
    return "確認製造工藝規格";
  if (fl.includes("tolerance") || fl.includes("clearance"))
    return "CAD 公差分析";
  if (fl.includes("cost") || fl.includes("price"))
    return "供應商報價或 BOM 確認";

  // Generic fallback
  if (sl.includes("llm") || sl.includes("estimate"))
    return "需工程團隊驗證";
  return "需人工確認";
}

/** Get category display info. */
function getCategoryInfo(cat: DraftCategory) {
  return DRAFT_CATEGORIES.find((c) => c.key === cat) ?? {
    key: cat,
    label: cat,
    labelZh: cat,
    icon: "📋",
  };
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface VerifiableItem {
  subsystemCode: string;
  /** Human-readable subsystem name resolved from subsystem_tree. */
  subsystemName: string;
  spec: DraftValue;
  suggestedMethod: string;
}

// ---------------------------------------------------------------------------
// CSV Export
// ---------------------------------------------------------------------------

function exportToCsv(items: VerifiableItem[], verifiedSet: Set<string>) {
  const BOM = "\uFEFF"; // UTF-8 BOM for Excel compatibility
  const headers = [
    "子系統",
    "子系統代碼",
    "欄位名稱",
    "值",
    "單位",
    "來源",
    "信心等級",
    "建議驗證方法",
    "已驗證",
  ];

  const escCsv = (s: string) => {
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const rows = items.map((item) => {
    const key = `${item.subsystemCode}::${item.spec.field_name}`;
    return [
      item.subsystemName,
      item.subsystemCode,
      humanize(item.spec.field_name),
      fmtValue(item.spec),
      item.spec.unit ?? "",
      item.spec.source,
      CONFIDENCE_COLORS[item.spec.confidence].labelZh,
      item.suggestedMethod,
      verifiedSet.has(key) ? "✓" : "",
    ]
      .map(escCsv)
      .join(",");
  });

  const csv = BOM + [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `verification-checklist-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Confidence badge (same visual style as EngineeringSpecDraftPanel). */
function ConfidenceBadge({ confidence }: { confidence: DraftValue["confidence"] }) {
  const c = CONFIDENCE_COLORS[confidence];
  return (
    <Badge
      variant="outline"
      className={cn("text-[10px] px-1.5 py-0 h-5 font-medium", c.bg, c.text, c.border)}
    >
      {c.labelZh}
    </Badge>
  );
}

/** Single verification item row. */
function VerificationRow({
  item,
  checked,
  onToggle,
}: {
  item: VerifiableItem;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <label
      className={cn(
        "flex items-start gap-3 p-2.5 rounded-md cursor-pointer transition-colors",
        "hover:bg-muted/40",
        checked && "opacity-60 bg-green-50/50 dark:bg-green-950/20"
      )}
    >
      <Checkbox
        checked={checked}
        onCheckedChange={onToggle}
        className="mt-0.5 shrink-0"
      />
      <div className="flex-1 min-w-0 space-y-1">
        {/* Field name + value */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn("text-sm font-medium", checked && "line-through")}>
            {humanize(item.spec.field_name)}
          </span>
          <span className="text-sm text-muted-foreground">
            ({fmtValue(item.spec)}{item.spec.unit ? ` ${item.spec.unit}` : ""})
          </span>
          <ConfidenceBadge confidence={item.spec.confidence} />
        </div>
        {/* Source + suggested verification method */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span>來源: <span className="font-medium">{item.spec.source}</span></span>
          <span className="text-muted-foreground/50">|</span>
          <span>建議: <span className="font-medium">{item.suggestedMethod}</span></span>
        </div>
      </div>
    </label>
  );
}

/** Category group within a subsystem section. */
function CategoryGroup({
  category,
  items,
  verifiedSet,
  onToggle,
}: {
  category: DraftCategory;
  items: VerifiableItem[];
  verifiedSet: Set<string>;
  onToggle: (key: string) => void;
}) {
  const info = getCategoryInfo(category);
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 px-2">
        <span>{info.icon}</span>
        <span>{info.labelZh}</span>
        <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4 ml-1">
          {items.length}
        </Badge>
      </p>
      <div className="space-y-0.5">
        {items.map((item) => {
          const key = `${item.subsystemCode}::${item.spec.field_name}`;
          return (
            <VerificationRow
              key={key}
              item={item}
              checked={verifiedSet.has(key)}
              onToggle={() => onToggle(key)}
            />
          );
        })}
      </div>
    </div>
  );
}

/**
 * 模組/元件子群組 — 系統卡片展開後的第二層摺疊區段。
 * 顯示單一 subsystem_code（模組或元件）下的驗證項目。
 */
function ModuleSubGroup({
  subCode,
  subName,
  items,
  verifiedSet,
  onToggle,
}: {
  subCode: string;
  subName: string;
  items: VerifiableItem[];
  verifiedSet: Set<string>;
  onToggle: (key: string) => void;
}) {
  const verifiedCount = items.filter(
    (i) => verifiedSet.has(`${i.subsystemCode}::${i.spec.field_name}`)
  ).length;
  const total = items.length;

  const byCategory = useMemo(() => {
    const map = new Map<DraftCategory, VerifiableItem[]>();
    for (const cat of DRAFT_CATEGORIES) {
      const catItems = items.filter((i) => i.spec.category === cat.key);
      if (catItems.length > 0) map.set(cat.key, catItems);
    }
    return map;
  }, [items]);

  return (
    <Collapsible defaultOpen>
      <div className="rounded-md border bg-muted/20">
        <CollapsibleTrigger className="w-full px-3 py-2 flex items-center gap-2 hover:bg-muted/40 transition-colors text-left">
          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground transition-transform [[data-state=open]>*>&]:rotate-90" />
          <span className="text-xs font-semibold">{subName}</span>
          <span className="text-[10px] text-muted-foreground font-mono">{subCode}</span>
          {verifiedCount === total ? (
            <Badge
              variant="outline"
              className="text-[10px] px-1 py-0 h-4 bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-green-300 dark:border-green-700"
            >
              <CheckCheck className="w-2.5 h-2.5 mr-0.5" />
              完成
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="text-[10px] px-1 py-0 h-4 bg-orange-100 dark:bg-orange-950/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-700"
            >
              {total - verifiedCount} 待驗證
            </Badge>
          )}
          <span className="text-[10px] text-muted-foreground ml-auto">
            {verifiedCount}/{total}
          </span>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-3 pb-3 pt-1 space-y-2 border-t">
            {Array.from(byCategory.entries()).map(([cat, catItems]) => (
              <CategoryGroup
                key={cat}
                category={cat}
                items={catItems}
                verifiedSet={verifiedSet}
                onToggle={onToggle}
              />
            ))}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

/**
 * 頂層系統卡片 — 聚合某根系統代碼（如 A1）下所有子系統/模組/元件的驗證進度。
 * 預設折疊（defaultOpen=false）；展開後按 subsystem_code 分群顯示 ModuleSubGroup。
 * 若該系統只有一個 sub-code（即自身），則直接展示 CategoryGroup，避免多餘層級。
 */
function SystemSection({
  systemCode,
  systemName,
  subGroups,
  codeToName,
  verifiedSet,
  onToggle,
}: {
  systemCode: string;
  systemName: string;
  /** Map<subsystem_code, items[]> — 此根系統下所有子代碼的驗證項目。 */
  subGroups: Map<string, VerifiableItem[]>;
  codeToName: Map<string, string>;
  verifiedSet: Set<string>;
  onToggle: (key: string) => void;
}) {
  // Aggregate all items across sub-groups for progress calculation
  const allSystemItems = useMemo(() => {
    const items: VerifiableItem[] = [];
    for (const list of subGroups.values()) items.push(...list);
    return items;
  }, [subGroups]);

  const verifiedCount = allSystemItems.filter(
    (i) => verifiedSet.has(`${i.subsystemCode}::${i.spec.field_name}`)
  ).length;
  const pendingCount = allSystemItems.length - verifiedCount;
  const progressPct =
    allSystemItems.length > 0
      ? (verifiedCount / allSystemItems.length) * 100
      : 100;

  // Dynamic border color: all verified → green, else orange
  const borderColor =
    pendingCount === 0 ? "border-l-green-500/70" : "border-l-orange-400/60";

  // If all items belong to the system code itself (no child modules), render categories directly
  const subCodes = Array.from(subGroups.keys());
  const isSingleLevel = subCodes.length === 1 && subCodes[0] === systemCode;

  // Category grouping for single-level fallback
  const directCategories = useMemo(() => {
    if (!isSingleLevel) return null;
    const map = new Map<DraftCategory, VerifiableItem[]>();
    for (const cat of DRAFT_CATEGORIES) {
      const catItems = allSystemItems.filter(
        (i) => i.spec.category === cat.key
      );
      if (catItems.length > 0) map.set(cat.key, catItems);
    }
    return map;
  }, [allSystemItems, isSingleLevel]);

  return (
    <Collapsible defaultOpen={false}>
      <Card className={cn("border-l-4", borderColor)}>
        <CollapsibleTrigger asChild>
          <CardContent className="p-4 cursor-pointer hover:bg-muted/30 transition-colors">
            <div className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-muted-foreground transition-transform [[data-state=open]>*>&]:rotate-90" />
              <span className="text-sm font-semibold">{systemName}</span>
              <span className="text-xs text-muted-foreground font-mono">
                {systemCode}
              </span>
              {pendingCount > 0 ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1.5 py-0 h-5 bg-orange-100 dark:bg-orange-950/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-700"
                    >
                      <AlertTriangle className="w-3 h-3 mr-0.5" />
                      {pendingCount} 項待驗證
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    {pendingCount} 項規格待人工驗證
                  </TooltipContent>
                </Tooltip>
              ) : (
                <Badge
                  variant="outline"
                  className="text-[10px] px-1.5 py-0 h-5 bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-green-300 dark:border-green-700"
                >
                  <CheckCheck className="w-3 h-3 mr-0.5" />
                  已全部驗證
                </Badge>
              )}
              <span className="text-xs text-muted-foreground ml-auto">
                {verifiedCount}/{allSystemItems.length}
              </span>
            </div>
            {/* Progress bar */}
            <div className="mt-2 flex items-center gap-2">
              <Progress value={progressPct} className="h-1.5 flex-1" />
              <span className="text-[10px] text-muted-foreground font-mono w-8 text-right">
                {Math.round(progressPct)}%
              </span>
            </div>
          </CardContent>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="px-4 pb-4 pt-0 border-t space-y-2">
            {directCategories
              ? /* Single-level: render category groups directly */
                Array.from(directCategories.entries()).map(
                  ([cat, catItems]) => (
                    <CategoryGroup
                      key={cat}
                      category={cat}
                      items={catItems}
                      verifiedSet={verifiedSet}
                      onToggle={onToggle}
                    />
                  )
                )
              : /* Multi-level: render ModuleSubGroup per sub-code */
                Array.from(subGroups.entries()).map(
                  ([subCode, subItems]) => (
                    <ModuleSubGroup
                      key={subCode}
                      subCode={subCode}
                      subName={codeToName.get(subCode) ?? subCode}
                      items={subItems}
                      verifiedSet={verifiedSet}
                      onToggle={onToggle}
                    />
                  )
                )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

/** Empty state when no items require verification. */
function EmptyState() {
  return (
    <div className="text-center py-6 text-muted-foreground">
      <CheckCheck className="w-8 h-8 mx-auto mb-2 text-green-500" />
      <p className="text-sm font-medium">所有規格值已確認</p>
      <p className="text-xs">沒有需要驗證的項目</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function VerificationChecklist({
  data,
  className,
}: VerificationChecklistProps) {
  // Build code → name lookup from subsystem_tree
  const codeToName = useMemo(
    () => buildCodeToNameMap(data.subsystem_tree ?? []),
    [data.subsystem_tree],
  );

  // Build subsystem_code → root system code lookup from subsystem_tree
  const codeToRoot = useMemo(
    () => buildCodeToRootMap(data.subsystem_tree ?? []),
    [data.subsystem_tree],
  );

  // Build flat list of all verifiable items
  const allItems = useMemo(() => {
    const items: VerifiableItem[] = [];
    for (const draft of data.drafts) {
      for (const spec of draft.specs) {
        if (spec.needs_verification) {
          items.push({
            subsystemCode: draft.subsystem_code,
            subsystemName:
              codeToName.get(draft.subsystem_code) ?? draft.subsystem_code,
            spec,
            suggestedMethod: suggestVerificationMethod(spec.field_name, spec.source),
          });
        }
      }
    }
    return items;
  }, [data.drafts, codeToName]);

  // Group by root system code → sub-code → items (two-level Map)
  // Uses codeToRoot to resolve name-based subsystem_codes to their root system
  const bySystem = useMemo(() => {
    const map = new Map<string, Map<string, VerifiableItem[]>>();
    for (const item of allItems) {
      const root = codeToRoot.get(item.subsystemCode) ?? item.subsystemCode;
      if (!map.has(root)) map.set(root, new Map());
      const inner = map.get(root)!;
      const list = inner.get(item.subsystemCode) ?? [];
      list.push(item);
      inner.set(item.subsystemCode, list);
    }
    return map;
  }, [allItems, codeToRoot]);

  // Verified state: Set of "subsystemCode::field_name" keys
  const [verifiedSet, setVerifiedSet] = useState<Set<string>>(new Set());

  const toggleVerified = useCallback((key: string) => {
    setVerifiedSet((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const markAllVerified = useCallback(() => {
    setVerifiedSet(
      new Set(allItems.map((i) => `${i.subsystemCode}::${i.spec.field_name}`))
    );
  }, [allItems]);

  const totalPending = allItems.length - verifiedSet.size;

  if (allItems.length === 0) {
    return (
      <Card className={cn("border-green-400/30", className)}>
        <CardContent className="p-4">
          <EmptyState />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("border-orange-400/30", className)}>
      {/* Header */}
      <CardContent className="p-4 pb-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-orange-500" />
            <h3 className="text-sm font-semibold">驗證清單</h3>
            {totalPending > 0 ? (
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 h-5 bg-orange-100 dark:bg-orange-950/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-700"
              >
                {totalPending} 項待驗證
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 h-5 bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-green-300 dark:border-green-700"
              >
                <CheckCheck className="w-3 h-3 mr-0.5" />
                全部已驗證
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7"
              onClick={() => exportToCsv(allItems, verifiedSet)}
            >
              <Download className="w-3.5 h-3.5 mr-1" />
              匯出驗證清單
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7"
              onClick={markAllVerified}
              disabled={totalPending === 0}
            >
              <CheckCheck className="w-3.5 h-3.5 mr-1" />
              全部標記已驗證
            </Button>
          </div>
        </div>
      </CardContent>

      {/* System-level sections (one card per root system code) */}
      <CardContent className="px-4 pb-4 pt-0 space-y-2">
        {Array.from(bySystem.entries()).map(([rootCode, subGroups]) => (
          <SystemSection
            key={rootCode}
            systemCode={rootCode}
            systemName={codeToName.get(rootCode) ?? rootCode}
            subGroups={subGroups}
            codeToName={codeToName}
            verifiedSet={verifiedSet}
            onToggle={toggleVerified}
          />
        ))}
      </CardContent>
    </Card>
  );
}
