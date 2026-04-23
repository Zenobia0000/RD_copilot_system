/**
 * useSubsystemSuggestion — Stage 3 extraction.
 *
 * Owns the end-to-end flow for AI subsystem suggestion:
 *   clear existing AI subsystems → call backend → flatten tree →
 *   insert each node (preserving parent chain) → invalidate query.
 *
 * The page component retains only the button-disabled state and
 * toast feedback (via onSuccess / onError callbacks).
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { scamperSubsystemSuggest } from '@/lib/api';
import type { SuggestedSubsystem, PackageMap, SubsystemLevel } from '@/types/generated/subsystem';
import type { ConsolidationResult } from '@/types/directedTriz';
import { queryKeys } from './useQueryConfig';

const VALID_LEVELS: ReadonlySet<SubsystemLevel> = new Set(['system', 'module', 'component']);

export interface SubsystemSuggestionVariables {
  mission: string;
  contradictions: string[];
  // v9: Brief context + consolidation enrichment
  constraints?: string[];
  kpis?: string[];
  consolidation_result?: ConsolidationResult | null;
}

export interface SubsystemSuggestionResult {
  created: number;
  packageMap?: PackageMap | null;
}

export function useSubsystemSuggestion(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<SubsystemSuggestionResult, Error, SubsystemSuggestionVariables>({
    mutationFn: async ({ mission, contradictions, constraints, kpis, consolidation_result }) => {
      if (!projectId) throw new Error('projectId is required');

      // 1) Clear existing AI-produced subsystems (preserve manual ones).
      const { error: delErr } = await supabase
        .from('subsystems')
        .delete()
        .eq('project_id', projectId)
        .eq('source', 'ai');
      if (delErr) console.warn('Failed to clear subsystems:', delErr.message);

      // 2) Call backend suggestion API.
      const resp = await scamperSubsystemSuggest({
        project_id: projectId,
        mission,
        contradictions,
        existing_subsystems: [],
        constraints,
        kpis,
        consolidation_result: consolidation_result ?? undefined,
      });

      // 3) Flatten tree → sequential inserts preserving parent chain.
      const tree = resp.subsystems ?? [];
      let created = 0;

      const insertTree = async (nodes: SuggestedSubsystem[], parentId: string | null) => {
        for (const node of nodes) {
          // Stage 6: fail-loud on missing level. Silent fallback to "module"
          // was hiding upstream LLM bugs — a node without a level is a
          // contract violation, not a degraded input to patch over.
          if (!node.level || !VALID_LEVELS.has(node.level)) {
            throw new Error(
              `Subsystem "${node.name}" has invalid or missing level (${String(node.level)}). ` +
              `Expected one of: system | module | component.`,
            );
          }

          // Stage 4: no longer write the legacy `interfaces` comma-joined
          // string. interface_contracts is the single source of truth; the
          // `interfaces` column is kept only for read-path fallback until
          // Stage 7 drops it entirely.
          const insertData: Record<string, unknown> = {
            project_id: projectId,
            name: node.name,
            level: node.level,
            reason: node.reason ?? '',
            related_contradictions: node.related_contradictions ?? [],
            confirmed: false,
            source: 'ai',
            parent_id: parentId,
            interface_contracts: node.interface_contracts ?? null,
          };

          const { data, error } = await supabase
            .from('subsystems')
            .insert(insertData)
            .select('id')
            .single();

          // Stage 6: fail loud on insert error. Previously this `continue`d
          // silently, causing the page to report "created N subsystems"
          // with N < expected and no surface signal to RD that data was lost.
          if (error) {
            throw new Error(
              `Failed to insert subsystem "${node.name}": ${error.message}`,
            );
          }
          created++;

          if (node.children?.length && data?.id) {
            await insertTree(node.children, data.id);
          }
        }
      };

      await insertTree(tree, null);

      return { created, packageMap: resp.package_map ?? null };
    },
    onSuccess: () => {
      // 4) Invalidate so the page refetches the new rows.
      queryClient.invalidateQueries({ queryKey: queryKeys.subsystems.all });
    },
  });
}
