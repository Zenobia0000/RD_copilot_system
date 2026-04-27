import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { AlertTriangle, ArrowRight, Layers, Box, Network, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ConceptRoute, LayeredLayerSnapshot } from '@/types/conceptRoute';
import { ADOPTION_TYPE_LABELS } from '@/types/conceptRoute';

interface Props {
  route: ConceptRoute;
}

const dimensionColor: Record<string, string> = {
  '空間': 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  '時間': 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  '條件': 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  '材料': 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
};

// v7 M6: layer-id → colour class, mirrors src/types/layeredTriz.ts LAYER_COLOR
const layerIconColor: Record<'L1' | 'L2' | 'L3', string> = {
  L1: 'text-blue-600 dark:text-blue-400',
  L2: 'text-amber-600 dark:text-amber-400',
  L3: 'text-emerald-600 dark:text-emerald-400',
};

/** Render a small L1/L2/L3 adoption badge row for layered ConceptRoutes. */
function LayerAdoptionBadges({
  adopted,
  available,
}: {
  adopted: readonly ('L1' | 'L2' | 'L3')[];
  available: readonly ('L1' | 'L2' | 'L3')[];
}) {
  return (
    <div className="flex items-center gap-0.5" data-testid="layer-adoption-badges">
      {(['L1', 'L2', 'L3'] as const).map((l) => {
        const isAvailable = available.includes(l);
        const isAdopted = adopted.includes(l);
        if (!isAvailable) return null;
        return (
          <span
            key={l}
            className={cn(
              'inline-flex h-4 min-w-[20px] items-center justify-center rounded-full border text-[9px] font-mono font-semibold',
              layerIconColor[l],
              isAdopted
                ? 'bg-background border-current'
                : 'bg-muted/60 border-dashed border-muted-foreground/40 opacity-60',
            )}
            title={`${l} ${isAdopted ? '已採納' : '存在但未採納'}`}
          >
            {isAdopted ? '●' : '○'}
            <span className="ml-0.5">{l}</span>
          </span>
        );
      })}
    </div>
  );
}

// ---- v7 WP 10.3 / 10.4: Layered card 第二眼 / 第三眼 ---------------------
//
// Second eye  = collapsible list of per-layer mechanism summaries + depth
//               indicators + effort hints + differential highlight.
// Third eye   = full assumptions list, deepen_link derivation trace (L2),
//               and L3 bridge text (supports L1/L2 + standalone value).
// Content is read from `LayeredConceptRouteMeta.layerSnapshots`, populated
// at adoption time by `handleLayeredAdopt` in pages/Create.tsx.

const LAYER_COLOR_CLASS: Record<'L1' | 'L2' | 'L3', string> = {
  L1: 'text-blue-700 dark:text-blue-400 border-blue-300',
  L2: 'text-amber-700 dark:text-amber-400 border-amber-300',
  L3: 'text-emerald-700 dark:text-emerald-400 border-emerald-300',
};

function LayerSnapshotRow({ snap }: { snap: LayeredLayerSnapshot }) {
  return (
    <div
      className={cn(
        'rounded-md border p-2 space-y-1 bg-background',
        LAYER_COLOR_CLASS[snap.layer],
      )}
      data-testid={`layer-snapshot-${snap.layer}`}
    >
      <div className="flex items-center gap-1.5 flex-wrap">
        <Badge variant="outline" className={cn('text-[9px] font-mono', LAYER_COLOR_CLASS[snap.layer])}>
          {snap.layer}
        </Badge>
        <span className="text-[10px] text-muted-foreground">{snap.depthIndicator}</span>
        <Badge variant="outline" className="text-[9px]">
          effort: {snap.effortHint ?? '—'}
        </Badge>
        <Badge variant="outline" className="text-[9px]">
          E-floor: {snap.evidenceLevelFloor}
        </Badge>
        {snap.suggestionCount > 0 && (
          <Badge variant="secondary" className="text-[9px]">
            {snap.suggestionCount} suggestion
          </Badge>
        )}
      </div>
      <p className="text-[11px] leading-snug">{snap.mechanismSummary}</p>
      {snap.principleHits.length > 0 && (
        <div className="text-[9px] font-mono text-muted-foreground">
          principles: {snap.principleHits.join(', ')}
        </div>
      )}
    </div>
  );
}

function LayerThirdEyeRow({ snap }: { snap: LayeredLayerSnapshot }) {
  return (
    <div
      className={cn(
        'rounded-md border p-2 space-y-1.5 bg-muted/20',
        LAYER_COLOR_CLASS[snap.layer],
      )}
      data-testid={`layer-third-eye-${snap.layer}`}
    >
      <div className="flex items-center gap-1.5">
        <Badge variant="outline" className={cn('text-[9px] font-mono', LAYER_COLOR_CLASS[snap.layer])}>
          {snap.layer}
        </Badge>
        <span className="text-[9px] uppercase tracking-wide text-muted-foreground">
          assumptions & trace
        </span>
      </div>
      {snap.assumptions.length > 0 && (
        <ul className="text-[10px] space-y-0.5 list-disc list-inside">
          {snap.assumptions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
      {snap.deepenLink && (
        <div className="rounded border border-dashed border-amber-300 p-1.5 space-y-0.5 bg-amber-50/60 dark:bg-amber-950/30">
          <div className="text-[9px] font-semibold text-amber-700 dark:text-amber-400">
            deepen_link
          </div>
          <div className="text-[10px]">
            <span className="font-semibold">physical param:</span>{' '}
            {snap.deepenLink.derivedParameter}
          </div>
          <div className="text-[10px] italic">
            {snap.deepenLink.contradictionStatement}
          </div>
          <div className="text-[9px] text-amber-700 dark:text-amber-400">
            separation: {snap.deepenLink.separationType}
          </div>
        </div>
      )}
      {snap.bridgeText && (
        <div className="rounded border border-dashed border-emerald-300 p-1.5 space-y-0.5 bg-emerald-50/60 dark:bg-emerald-950/30">
          <div className="text-[9px] font-semibold text-emerald-700 dark:text-emerald-400">
            relationship to other layers
          </div>
          {snap.bridgeText.supportsL1 && (
            <div className="text-[10px]">
              <span className="font-semibold">→ L1:</span> {snap.bridgeText.supportsL1}
            </div>
          )}
          {snap.bridgeText.supportsL2 && (
            <div className="text-[10px]">
              <span className="font-semibold">→ L2:</span> {snap.bridgeText.supportsL2}
            </div>
          )}
          {snap.bridgeText.standaloneValue && (
            <div className="text-[10px]">
              <span className="font-semibold">standalone:</span> {snap.bridgeText.standaloneValue}
            </div>
          )}
        </div>
      )}
      {/* WBS 10.4: Validation Passport snapshot */}
      {snap.validationPassport && (
        <div className="rounded border border-dashed border-violet-300 p-1.5 space-y-1 bg-violet-50/60 dark:bg-violet-950/30" data-testid={`layer-vp-${snap.layer}`}>
          <div className="text-[9px] font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wide">
            Validation Passport
          </div>
          <div className="text-[10px]">
            <span className="font-semibold">mechanism:</span> {snap.validationPassport.mechanism}
          </div>
          <div className="text-[10px]">
            <span className="font-semibold">evidence:</span> {snap.validationPassport.evidenceLevel}
            {snap.validationPassport.effort && <> · <span className="font-semibold">effort:</span> {snap.validationPassport.effort}</>}
            {snap.validationPassport.gain && <> · <span className="font-semibold">gain:</span> {snap.validationPassport.gain}</>}
          </div>
          {snap.validationPassport.keyAssumptions.length > 0 && (
            <div className="text-[10px]">
              <span className="font-semibold">assumptions:</span>
              <ul className="list-disc list-inside ml-1">
                {snap.validationPassport.keyAssumptions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
          {snap.validationPassport.failConditions.length > 0 && (
            <div className="text-[10px] text-red-700 dark:text-red-400">
              <span className="font-semibold">fail conditions:</span>
              <ul className="list-disc list-inside ml-1">
                {snap.validationPassport.failConditions.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ConceptRouteCard({ route }: Props) {
  const [secondEyeOpen, setSecondEyeOpen] = useState(false);
  const [thirdEyeOpen, setThirdEyeOpen] = useState(false);
  const isComposite = route.type === 'composite';
  const isLayered = route.type === 'layered';

  return (
    <Card
      className={cn(
        isComposite && 'border-primary/30',
        isLayered && 'border-primary/40 ring-1 ring-primary/10',
      )}
      data-testid={`concept-route-card-${route.type}`}
    >
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2 flex-wrap">
          {isLayered ? (
            <Network className="h-4 w-4 text-primary shrink-0" />
          ) : isComposite ? (
            <Layers className="h-4 w-4 text-primary shrink-0" />
          ) : (
            <Box className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <span className="text-sm font-semibold font-mono">{route.id}</span>
          <Badge
            variant={isLayered || isComposite ? 'default' : 'secondary'}
            className="text-[10px]"
          >
            {isLayered ? 'Layered' : isComposite ? 'Composite' : 'Single'}
          </Badge>
          {isLayered && route.layered && (
            <>
              <LayerAdoptionBadges
                adopted={route.layered.adoptedLayers}
                available={route.layered.availableLayers}
              />
              <Badge variant="outline" className="text-[9px]">
                {route.layered.adoptionMode}
              </Badge>
            </>
          )}
          {isComposite && (
            <Badge variant="outline" className="text-[10px]">
              {route.composition.length} 解合併
            </Badge>
          )}
        </div>

        {/* Layered: recommended route summary (第一眼) */}
        {isLayered && route.layered && (
          <div className="rounded-md border border-primary/20 bg-muted/30 p-2 space-y-1">
            <div className="text-[11px]">
              <span className="font-semibold">推薦路線：</span>
              <span>{route.layered.recommendedRoute || '—'}</span>
            </div>
            {route.layered.fallbackRoute && (
              <div className="text-[10px] text-muted-foreground">
                fallback：{route.layered.fallbackRoute}
              </div>
            )}
            {route.layered.recommendedRationale && (
              <div className="text-[10px] italic text-muted-foreground">
                {route.layered.recommendedRationale}
              </div>
            )}
            <div className="text-[9px] text-muted-foreground italic">
              phase_b_directive: intra-LTS{' '}
              <span className="font-semibold">
                {route.layered.phaseBDirective.sameContradictionIntraLayerConflict}
              </span>{' '}
              · cross-contradiction{' '}
              <span className="font-semibold">
                {route.layered.phaseBDirective.crossContradictionConflict}
              </span>
            </div>
          </div>
        )}

        {/* Layered: 第二眼 — per-layer mechanism summaries */}
        {isLayered && route.layered?.layerSnapshots && route.layered.layerSnapshots.length > 0 && (
          <Collapsible open={secondEyeOpen} onOpenChange={setSecondEyeOpen}>
            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="flex w-full items-center justify-between rounded-md border border-dashed px-2 py-1 text-[10px] text-muted-foreground hover:bg-muted/40"
                data-testid="layered-second-eye-toggle"
              >
                <span>
                  第二眼：每層機制 · {route.layered.layerSnapshots.length} 層
                  {route.layered.differentialHighlight && ' · 差異洞察'}
                </span>
                {secondEyeOpen ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-1.5 space-y-1.5" data-testid="layered-second-eye-content">
              {route.layered.differentialHighlight && (
                <div className="rounded-md bg-primary/5 border border-primary/10 p-1.5 text-[10px] italic">
                  <span className="font-semibold">differential：</span>
                  {route.layered.differentialHighlight}
                </div>
              )}
              {route.layered.layerSnapshots.map((snap) => (
                <LayerSnapshotRow key={snap.layer} snap={snap} />
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Layered: 第三眼 — assumptions + deepen_link + bridge trace */}
        {isLayered && route.layered?.layerSnapshots && route.layered.layerSnapshots.length > 0 && (
          <Collapsible open={thirdEyeOpen} onOpenChange={setThirdEyeOpen}>
            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="flex w-full items-center justify-between rounded-md border border-dashed px-2 py-1 text-[10px] text-muted-foreground hover:bg-muted/40"
                data-testid="layered-third-eye-toggle"
              >
                <span>第三眼：假設 · VP · deepen_link · 結構 bridge</span>
                {thirdEyeOpen ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-1.5 space-y-1.5" data-testid="layered-third-eye-content">
              {route.layered.layerSnapshots.map((snap) => (
                <LayerThirdEyeRow key={snap.layer} snap={snap} />
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Composition chain */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {route.composition.map((entry, idx) => (
            <div key={entry.solutionId} className="flex items-center gap-1.5">
              {idx > 0 && <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />}
              <div className="rounded-lg border bg-background p-2 space-y-1 min-w-[140px]">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-medium">{entry.sourcePrinciple}</span>
                </div>
                <p className="text-[10px] text-muted-foreground leading-snug">
                  {entry.concrete.length > 40 ? entry.concrete.slice(0, 40) + '...' : entry.concrete}
                </p>
                <div className="flex items-center gap-1">
                  <Badge variant="outline" className={`text-[9px] ${dimensionColor[entry.dimension] ?? ''}`}>
                    {entry.dimension}
                  </Badge>
                  <Badge variant="outline" className="text-[9px] font-mono">
                    {entry.adoptionType} {ADOPTION_TYPE_LABELS[entry.adoptionType].zh}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Rationale */}
        <p className="text-xs text-muted-foreground leading-relaxed pl-1 border-l-2 border-muted">
          {route.compositionRationale}
        </p>

        {/* Anti-pattern warnings */}
        {route.antiPatternWarnings.length > 0 && (
          <div className="space-y-1">
            {route.antiPatternWarnings.map((w, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[10px] text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
