/**
 * DirectionTermsGlossary — 「📖 名詞說明」拉桿 (Sheet)
 *
 * RD 點開後從右側滑出，逐節解釋 Create 頁「解矛盾」區的所有徽章、
 * 顏色、評語、排序、篩選術語。所有顏色 / 標籤 / 文字都來自單一資料源
 * `directionTerms.ts`，所以這份說明永遠跟卡片畫面一致。
 *
 * 設計目標：
 *   - 第一次進 Create 頁的 RD 想完整搞懂概念 → 點 1 個按鈕看完整 7 節。
 *   - 老手只想「快速確認單一徽章意思」→ 走就地 Tooltip 不用打開這裡。
 *   - 跨節有錨點：Sort/Filter 旁的 ? icon 可指定 `defaultSectionId` 預先展開該節。
 *
 * 開關狀態以 localStorage 保留 (`directionGlossary.lastSection` /
 * `directionGlossary.hasOpened`)，第一次自動引導展開，之後尊重 RD 偏好。
 */

import { useEffect, useMemo, useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  GLOSSARY_SECTIONS,
  RESOLUTION_STATUS_TERMS,
  ADDRESSES_LAYER_TERMS,
  ADDRESSES_LAYER_PHILOSOPHY,
  VERDICT_TERMS,
  SR_KIND_TERMS,
  SCORE_COLUMN_TERMS,
  SORT_OPTIONS,
  FILTER_OPTIONS,
  SEVERITY_TERMS,
  type GlossarySectionId,
} from './directionTerms';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
export interface DirectionTermsGlossaryProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** 預設展開哪一節（給就地 ? icon 用）；不傳則展開第一節。 */
  defaultSectionId?: GlossarySectionId;
}

// ---------------------------------------------------------------------------
// Small inline pieces — keep visual parity with DirectionResultCard
// ---------------------------------------------------------------------------
function StaticBadge({
  label,
  className,
}: {
  label: string;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn('text-[10px] border', className)}
    >
      {label}
    </Badge>
  );
}

function UiAnchorBox({ children }: { children: string }) {
  return (
    <div className="text-[11px] mt-2 px-2 py-1.5 rounded bg-muted/50 border border-dashed">
      <span className="text-muted-foreground">📍 對應 UI 位置：</span>
      <span className="text-foreground/90">{children}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section bodies — one per GlossarySectionId
// ---------------------------------------------------------------------------

function ManifestSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        每張方向卡頂端那段虛線框就是「矛盾說明書」 — 它把矛盾拆成 4 種
        類別的<strong>子需求 (Sub-Requirement, SR)</strong>，讓你在挑方向
        前先把背景讀過一次。注意：<strong>它不是驗收條件</strong>，真正
        驗收要等「跨矛盾整併」後的 VerdictCard。
      </p>
      <div className="space-y-1.5 mt-2">
        {Object.entries(SR_KIND_TERMS).map(([key, term]) => (
          <div key={key} className="flex items-start gap-2">
            <Badge
              variant="outline"
              className={cn('text-[10px] mt-0.5 border-0 shrink-0', term.tone)}
            >
              {term.tag}
            </Badge>
            <div className="flex-1 min-w-0">
              <div className="text-foreground/90">{term.description}</div>
              {term.example && (
                <div className="text-[11px] text-muted-foreground italic mt-0.5">
                  {term.example}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <UiAnchorBox>
        對應每張方向卡頂端那段虛線框「矛盾說明書」內的 SR 清單。
      </UiAnchorBox>
    </div>
  );
}

function ResolutionStatusSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        AI 對「這個方向有沒有解掉矛盾」的整體審判，共 <strong>5 種狀態</strong>。
      </p>
      <div className="space-y-2 mt-2">
        {Object.entries(RESOLUTION_STATUS_TERMS).map(([key, term]) => (
          <div key={key} className="space-y-1">
            <StaticBadge label={term.label} className={term.className} />
            <div className="text-foreground/90">{term.description}</div>
            {term.example && (
              <div className="text-[11px] text-muted-foreground italic">
                {term.example}
              </div>
            )}
          </div>
        ))}
      </div>
      <UiAnchorBox>
        對應方向卡標題列上的 5 色徽章（綠 / 黃 / 橘 / 紅 / 灰）。
      </UiAnchorBox>
    </div>
  );
}

function AddressesLayerSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        AI 額外判斷這個方向動到的是<strong>哪一層因果</strong>，共{' '}
        <strong>4 種</strong>。設計理念：解根因 &gt; 解機制 &gt; 解症狀。
      </p>
      <div className="space-y-2 mt-2">
        {Object.entries(ADDRESSES_LAYER_TERMS).map(([key, term]) => (
          <div key={key} className="space-y-1">
            <StaticBadge label={term.label} className={term.className} />
            <div className="text-foreground/90">{term.description}</div>
            {term.example && (
              <div className="text-[11px] text-muted-foreground italic">
                {term.example}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="text-[11px] mt-2 px-2 py-1.5 rounded bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
        💡 {ADDRESSES_LAYER_PHILOSOPHY}
      </div>
      <UiAnchorBox>
        對應方向卡標題列上、5 色徽章旁邊那個「解根因 / 解機制 / 解症狀」徽章。
      </UiAnchorBox>
    </div>
  );
}

function PerSrVerdictSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        展開方向後，每條 SR 都會有一個逐條短評，共 <strong>6 種</strong>。
      </p>
      <div className="space-y-1.5 mt-2">
        {Object.entries(VERDICT_TERMS).map(([key, term]) => (
          <div key={key} className="flex items-start gap-2">
            <span
              className={cn(
                'inline-block w-1.5 h-1.5 rounded-full mt-1.5 shrink-0',
                term.dotClass,
              )}
            />
            <div className="flex-1 min-w-0">
              <span className={cn('font-medium', term.className)}>
                {term.icon} {term.label}
              </span>
              <span className="text-foreground/80 ml-1.5">— {term.description}</span>
            </div>
          </div>
        ))}
      </div>
      <UiAnchorBox>
        對應展開方向後，每條 SR 列前面的小圓點 + 「本方案：...」那行。
      </UiAnchorBox>
    </div>
  );
}

function ScoreColumnsSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        展開方向後最上面有 4 個分數格，每個欄位的意義如下：
      </p>
      <div className="space-y-2 mt-2">
        {SCORE_COLUMN_TERMS.map((term) => (
          <div key={term.key} className="space-y-0.5">
            <div className="font-medium text-foreground">{term.label}</div>
            <div className="text-foreground/90">{term.description}</div>
            {term.example && (
              <div className="text-[11px] text-muted-foreground italic">
                {term.example}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="text-[11px] mt-2 px-2 py-1.5 rounded bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
        ⚠️ 注意：<strong>「實施容易度」是分數越高越容易</strong>，不是越貴！
        firmware-only 改演算法會拿到接近 9~10 的高分。
      </div>
      <UiAnchorBox>
        對應展開方向後最上方那一排 4 個彩色分數格。
      </UiAnchorBox>
    </div>
  );
}

function SortFilterSection() {
  return (
    <div className="space-y-3 text-[12px]">
      <div>
        <div className="font-medium text-foreground mb-1.5">
          排序（Sort）— 4 種
        </div>
        <div className="space-y-1.5">
          {SORT_OPTIONS.map((opt) => (
            <div key={opt.value}>
              <span className="font-medium">{opt.label}</span>
              <span className="text-foreground/80"> — {opt.description}</span>
            </div>
          ))}
        </div>
      </div>
      <Separator />
      <div>
        <div className="font-medium text-foreground mb-1.5">
          篩選（Filter）— 4 種
        </div>
        <div className="space-y-1.5">
          {FILTER_OPTIONS.map((opt) => (
            <div key={opt.value}>
              <span className="font-medium">{opt.label}</span>
              <span className="text-foreground/80"> — {opt.description}</span>
            </div>
          ))}
        </div>
      </div>
      <UiAnchorBox>
        對應方向卡頂端那兩個下拉（排序 / 篩選）。
      </UiAnchorBox>
    </div>
  );
}

function SeveritySection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        AI 評估「這條矛盾有多嚴重 / 多致命」，共 <strong>4 種</strong>。
      </p>
      <div className="space-y-2 mt-2">
        {Object.entries(SEVERITY_TERMS).map(([key, term]) => (
          <div key={key} className="space-y-0.5">
            <Badge variant={term.variant} className="text-[10px]">
              {term.label}
            </Badge>
            <div className="text-foreground/90">{term.description}</div>
          </div>
        ))}
      </div>
      <UiAnchorBox>
        對應方向卡標題右上角的嚴重度徽章。
      </UiAnchorBox>
    </div>
  );
}

function WhyNotVerdictSection() {
  return (
    <div className="space-y-2 text-[12px]">
      <p className="text-foreground/90">
        <strong>單一方向解掉幾條 SR，並不等於「整個矛盾被解了」。</strong>
        本頁的所有評語都是「給 RD 挑方向用的閱讀背景」。
      </p>
      <div className="text-foreground/90">
        真正驗收要等 RD 勾完方向後、按下「跨矛盾整併」產出的
        <strong> EngineeringVerdictCard (Q1–Q8) </strong>
        — 它會檢查 8 個工程維度：矛盾兩面的覆蓋、機制溯源、可行性矩陣、
        CLD 副作用、覆蓋完整度、驗證計畫、duty cycle、邊界塌陷。
      </div>
      <div className="text-[11px] mt-2 px-2 py-1.5 rounded bg-muted/50 border border-dashed">
        🎯 設計哲學：方向 ≠ 解；方向是「值得花力氣往這個方向想」的提示，
        真正解一定要做完整併 + VerdictCard。
      </div>
      <UiAnchorBox>
        對應頁面下方「跨矛盾整併」按鈕產出的 EngineeringVerdictCard 區塊。
      </UiAnchorBox>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section renderer
// ---------------------------------------------------------------------------
function renderSectionBody(id: GlossarySectionId): JSX.Element {
  switch (id) {
    case 'manifest':
      return <ManifestSection />;
    case 'resolution_status':
      return <ResolutionStatusSection />;
    case 'addresses_layer':
      return <AddressesLayerSection />;
    case 'per_sr_verdict':
      return <PerSrVerdictSection />;
    case 'score_columns':
      return <ScoreColumnsSection />;
    case 'sort_filter':
      return <SortFilterSection />;
    case 'severity':
      return <SeveritySection />;
    case 'why_not_verdict':
      return <WhyNotVerdictSection />;
  }
}

// ---------------------------------------------------------------------------
// localStorage key for remembering the last opened section
// ---------------------------------------------------------------------------
const LAST_SECTION_KEY = 'directionGlossary.lastSection';

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function DirectionTermsGlossary({
  open,
  onOpenChange,
  defaultSectionId,
}: DirectionTermsGlossaryProps) {
  // Choose which section is expanded:
  //   1) explicit prop wins
  //   2) else last-used (from localStorage)
  //   3) else first section
  const initialSection = useMemo<GlossarySectionId>(() => {
    if (defaultSectionId) return defaultSectionId;
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem(LAST_SECTION_KEY) as
        | GlossarySectionId
        | null;
      if (saved && GLOSSARY_SECTIONS.some((s) => s.id === saved)) {
        return saved;
      }
    }
    return GLOSSARY_SECTIONS[0].id;
  }, [defaultSectionId]);

  const [expanded, setExpanded] = useState<string>(initialSection);

  // Re-sync when caller changes defaultSectionId while open.
  useEffect(() => {
    if (open && defaultSectionId) {
      setExpanded(defaultSectionId);
    }
  }, [open, defaultSectionId]);

  // Persist user's last-opened section.
  useEffect(() => {
    if (typeof window !== 'undefined' && expanded) {
      window.localStorage.setItem(LAST_SECTION_KEY, expanded);
    }
  }, [expanded]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md overflow-y-auto"
      >
        <SheetHeader className="pb-2">
          <SheetTitle className="text-base">📖 名詞說明</SheetTitle>
          <SheetDescription className="text-xs leading-relaxed">
            這頁的每個徽章、顏色、欄位代表什麼？以下 8 節對應「解矛盾」區
            的所有術語。可保持開著，邊看邊對照方向卡。
          </SheetDescription>
        </SheetHeader>

        <Accordion
          type="single"
          collapsible
          value={expanded}
          onValueChange={(v) => setExpanded(v)}
          className="mt-2"
        >
          {GLOSSARY_SECTIONS.map((section) => (
            <AccordionItem key={section.id} value={section.id}>
              <AccordionTrigger className="text-sm text-left">
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{section.title}</div>
                  <div className="text-[11px] text-muted-foreground font-normal mt-0.5">
                    {section.blurb}
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                {renderSectionBody(section.id)}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </SheetContent>
    </Sheet>
  );
}
