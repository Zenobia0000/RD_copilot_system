/**
 * VerdictCardPanel — Phase 3 §E3 EngineeringVerdictCard Q1–Q8 顯示
 *
 * 設計理念見 plans/triz-redesign.md §4：整併方案做完之後，
 * 後端跑 `_generate_engineering_verdict_card` 產出八節 (Q1–Q8) 完整工程審判。
 * 前端用 collapsible 區塊 + 一個固定的 final_verdict 標頭呈現。
 */

import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, Gavel } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { EngineeringVerdictCard } from '@/types/directedTriz';

interface VerdictCardPanelProps {
  card: EngineeringVerdictCard;
}

const FINAL_VERDICT_LABEL: Record<
  EngineeringVerdictCard['final_verdict'],
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; tint: string }
> = {
  adopt: { label: '✅ 採用', variant: 'default', tint: 'text-green-700 dark:text-green-300' },
  adopt_with_conditions: {
    label: '🟡 附條件採用',
    variant: 'secondary',
    tint: 'text-yellow-700 dark:text-yellow-300',
  },
  needs_revision: {
    label: '⚠️ 需修訂',
    variant: 'outline',
    tint: 'text-orange-700 dark:text-orange-300',
  },
  reject: { label: '🛑 拒絕', variant: 'destructive', tint: 'text-red-700 dark:text-red-300' },
};

const FEASIBILITY_VERDICT_LABEL: Record<string, string> = {
  pass: '✅ 通過',
  marginal_pass: '🟢 邊界通過',
  bottleneck: '🟡 瓶頸',
  not_addressed: '⚪ 未處理',
  not_affected: '⚫ 不影響',
  fail: '🛑 失敗',
};

const DUTY_CYCLE_LABEL: Record<string, string> = {
  addressed: '✅ 已處理',
  marginal: '🟡 邊界',
  not_addressed: '⚪ 未處理',
};

const SEVERITY_LABEL: Record<string, { label: string; tint: string }> = {
  mild: { label: '輕微', tint: 'text-yellow-700 dark:text-yellow-300' },
  moderate: { label: '中等', tint: 'text-orange-700 dark:text-orange-300' },
  catastrophic: { label: '災難', tint: 'text-red-700 dark:text-red-300' },
};

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="w-full flex items-center justify-between p-2 text-left text-xs font-medium hover:bg-accent/40 rounded"
        >
          <span>{title}</span>
          {open ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="px-2 pb-2 text-[11px] space-y-1">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function VerdictCardPanel({ card }: VerdictCardPanelProps) {
  const verdictMeta = FINAL_VERDICT_LABEL[card.final_verdict] ?? FINAL_VERDICT_LABEL.needs_revision;

  return (
    <Card className="border-primary/40">
      <CardHeader className="p-3 pb-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-sm flex items-center gap-2">
            <Gavel className="h-4 w-4 text-primary" />
            EngineeringVerdictCard — Q1–Q8 工程審判
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={verdictMeta.variant}>{verdictMeta.label}</Badge>
            <span className="text-[11px] text-muted-foreground">
              信心 {(card.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        {/* PR3-2 disclaimer：LLM 工程審判的限制揭露 */}
        <p className="text-[10px] text-muted-foreground/80 italic mt-1 leading-relaxed">
          ⓘ 此審判由 LLM 基於採納方向 + brief context 推理產出，
          **非實驗、模擬或 CAD 驗證**；Q1–Q8 結論需在後續 Pre-CAD / 試作階段以實證確認。
        </p>
        {card.final_rationale && (
          <div className={cn('text-[11px] mt-1', verdictMeta.tint)}>
            {card.final_rationale}
          </div>
        )}
      </CardHeader>
      <CardContent className="p-2 space-y-1">
        {/* Q1: contradiction_face_per_picked */}
        <Section title="Q1 每條被勾方向解的是哪一面" defaultOpen>
          {card.contradiction_face_per_picked.length === 0 && (
            <div className="italic text-muted-foreground">(無資料)</div>
          )}
          {card.contradiction_face_per_picked.map((f, i) => (
            <div key={`${f.picked_direction_id}-${i}`} className="border-l-2 pl-2">
              <div>
                <span className="font-mono text-[10px] mr-1">
                  {f.picked_direction_id}
                </span>
                {f.picked_direction_name}
              </div>
              <div className="text-muted-foreground">
                improving: {f.improving_side} / worsening: {f.worsening_side}
              </div>
              {f.introduces_new_side_effect.length > 0 && (
                <div className="text-orange-700 dark:text-orange-300">
                  新副作用：{f.introduces_new_side_effect.join('；')}
                </div>
              )}
            </div>
          ))}
        </Section>

        {/* Q2: mechanism_trace */}
        <Section title="Q2 機制因果鏈">
          <div>
            技術組合：
            <span className="font-mono">
              {card.mechanism_trace.technology_mix.join(' + ') || '(無)'}
            </span>
            <span className="ml-2">證據等級 {card.mechanism_trace.evidence_level}</span>
          </div>
          {card.mechanism_trace.delta_chain.length > 0 && (
            <ol className="list-decimal pl-4 space-y-0.5">
              {card.mechanism_trace.delta_chain.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          )}
          {card.mechanism_trace.assumptions.length > 0 && (
            <div className="text-muted-foreground">
              假設：{card.mechanism_trace.assumptions.join('；')}
            </div>
          )}
        </Section>

        {/* Q3: feasibility_matrix */}
        <Section title="Q3 可行性矩陣">
          <div>
            整體判定：
            <Badge
              variant={
                card.feasibility_matrix.overall_verdict === 'pass'
                  ? 'default'
                  : card.feasibility_matrix.overall_verdict === 'fail'
                    ? 'destructive'
                    : 'secondary'
              }
            >
              {card.feasibility_matrix.overall_verdict}
            </Badge>
            {card.feasibility_matrix.bottleneck_axes.length > 0 && (
              <span className="ml-2 text-orange-700 dark:text-orange-300">
                瓶頸：{card.feasibility_matrix.bottleneck_axes.join('；')}
              </span>
            )}
          </div>
          {card.feasibility_matrix.axes.map((a, i) => (
            <div key={`${a.axis}-${i}`} className="border-l-2 pl-2">
              <div className="font-medium">
                {a.axis}
                <span className="ml-2">
                  {FEASIBILITY_VERDICT_LABEL[a.verdict] ?? a.verdict}
                </span>
              </div>
              <div className="text-muted-foreground">{a.rationale}</div>
              {a.quantitative_estimate && (
                <div className="font-mono text-[10px]">
                  量化估計：{a.quantitative_estimate}
                </div>
              )}
            </div>
          ))}
        </Section>

        {/* Q4: side_effects_via_cld */}
        <Section title="Q4 CLD 副作用鏈">
          {card.side_effects_via_cld.paths.length === 0 && (
            <div className="italic text-muted-foreground">(CLD 未提供或無相關路徑)</div>
          )}
          {card.side_effects_via_cld.paths.map((p, i) => (
            <div key={i} className="border-l-2 pl-2">
              <div className="font-mono text-[10px]">
                {p.cld_path.join(' → ')}
              </div>
              <div className="text-muted-foreground">
                極性：{p.polarity_chain.join(', ')}
                <span className="ml-2">風險：{p.risk_level}</span>
              </div>
              <div>{p.direction_impact}</div>
            </div>
          ))}
          {card.side_effects_via_cld.socratic_warnings.length > 0 && (
            <div className="text-orange-700 dark:text-orange-300">
              {card.side_effects_via_cld.socratic_warnings.map((w, i) => (
                <div key={i}>{w}</div>
              ))}
            </div>
          )}
        </Section>

        {/* Q5: coverage_completeness */}
        <Section title="Q5 SR 涵蓋率">
          {[
            ['完全解', card.coverage_completeness.resolves_fully],
            ['部分解', card.coverage_completeness.resolves_partial],
            ['條件解', card.coverage_completeness.resolves_conditional],
            ['未處理', card.coverage_completeness.does_not_address],
          ].map(([label, ids]) => (
            <div key={label as string}>
              <span className="font-medium">{label}：</span>
              <span className="font-mono">
                {(ids as string[]).length === 0 ? '(無)' : (ids as string[]).join(', ')}
              </span>
            </div>
          ))}
          {card.coverage_completeness.open_questions.length > 0 && (
            <div className="text-muted-foreground">
              開放問題：
              <ul className="list-disc pl-4">
                {card.coverage_completeness.open_questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        {/* Q6: verification_plan */}
        <Section title="Q6 驗證計畫">
          {card.verification_plan.steps.map((s, i) => (
            <div key={i} className="border-l-2 pl-2">
              <div className="font-medium">
                [{s.phase}] {s.test_description}
                {s.blocking && (
                  <Badge variant="destructive" className="ml-2 text-[10px]">
                    blocking
                  </Badge>
                )}
              </div>
              <div className="text-muted-foreground">
                預期：{s.expected_outcome} · 估時 {s.effort_hours}h
              </div>
            </div>
          ))}
          {card.verification_plan.socratic_action_links.length > 0 && (
            <div className="text-muted-foreground">
              {card.verification_plan.socratic_action_links.map((l, i) => (
                <div key={i}>{l}</div>
              ))}
            </div>
          )}
        </Section>

        {/* Q7: duty_cycle_verdict */}
        <Section title="Q7 工況覆蓋 (peak/continuous/startup/steady_state)">
          <div className="grid grid-cols-2 gap-1">
            {(['peak', 'continuous', 'startup', 'steady_state'] as const).map((k) => (
              <div key={k} className="flex justify-between">
                <span>{k}</span>
                <span>
                  {DUTY_CYCLE_LABEL[card.duty_cycle_verdict[k]] ??
                    card.duty_cycle_verdict[k]}
                </span>
              </div>
            ))}
          </div>
          {card.duty_cycle_verdict.cycle_specific_notes && (
            <div className="text-muted-foreground">
              {card.duty_cycle_verdict.cycle_specific_notes}
            </div>
          )}
        </Section>

        {/* Q8: boundary_collapse */}
        <Section title={`Q8 失效條件 (${card.boundary_collapse.length})`}>
          {card.boundary_collapse.map((b, i) => {
            const sev = SEVERITY_LABEL[b.severity] ?? SEVERITY_LABEL.moderate;
            return (
              <div key={i} className="border-l-2 pl-2">
                <div className="font-medium">
                  {b.condition}
                  <span className={cn('ml-2 text-[10px]', sev.tint)}>
                    [{sev.label}]
                  </span>
                </div>
                <div className="text-muted-foreground">{b.failure_mode}</div>
              </div>
            );
          })}
        </Section>
      </CardContent>
    </Card>
  );
}
