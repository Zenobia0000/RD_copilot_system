/**
 * useGateSync — batch-check all 8 gates and sync phase_progress back to projects table.
 *
 * On Dashboard mount: calls GET /gates/{id}/check for each gate in parallel,
 * assembles a PhaseProgress object, and writes it back to the projects row
 * if it differs from the current snapshot.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { gateCheck } from '@/lib/api';
import type { PhaseProgress, StepStatus } from '@/types/project';
import { queryKeys } from './useQueryConfig';

/** Backend-registered gate IDs (gate_registry.py). V1 has no backend gate. */
const GATE_IDS = ['D1', 'D2', 'PG-D', 'X1', 'X2', 'PG-X', 'V2', 'PG-V'] as const;

interface GateSyncResult {
  progress: PhaseProgress;
  gatesPassed: number;
}

export function useGateSync(projectId: string | undefined) {
  const queryClient = useQueryClient();

  return useQuery<GateSyncResult, Error>({
    queryKey: ['gate-sync', projectId],
    queryFn: async (): Promise<GateSyncResult> => {
      const id = projectId!;

      // 1) Batch-check all gates in parallel
      const results = await Promise.allSettled(
        GATE_IDS.map((gateId) => gateCheck(gateId, id)),
      );

      // 2) Build a map of gate_id → passed
      const passedMap = new Map<string, boolean>();
      for (let i = 0; i < GATE_IDS.length; i++) {
        const r = results[i];
        passedMap.set(GATE_IDS[i], r.status === 'fulfilled' && r.value.passed);
      }

      // 3) Derive StepStatus for each PhaseProgress key
      function status(gateId: string): StepStatus {
        if (passedMap.get(gateId)) return 'passed';
        // If a prerequisite gate hasn't passed, this gate is not_started
        // Otherwise it's in_progress (has data but doesn't pass yet)
        return 'in_progress';
      }

      // V1 has no backend gate — infer from PG-X (review is accessible after PG-X)
      const v1Status: StepStatus = passedMap.get('PG-X')
        ? (passedMap.get('V2') ? 'passed' : 'in_progress')
        : 'not_started';

      const progress: PhaseProgress = {
        'D1': status('D1'),
        'D2': passedMap.get('D1') ? status('D2') : 'not_started',
        'PG-D': passedMap.get('D2') ? status('PG-D') : 'not_started',
        'X1': passedMap.get('PG-D') ? status('X1') : 'not_started',
        'X2': passedMap.get('X1') ? status('X2') : 'not_started',
        'PG-X': passedMap.get('X2') ? status('PG-X') : 'not_started',
        'V1': v1Status,
        'V2': passedMap.get('PG-X') ? status('V2') : 'not_started',
        'PG-V': passedMap.get('V2') ? status('PG-V') : 'not_started',
      };

      const gatesPassed = Object.values(progress).filter((s) => s === 'passed').length;

      // 4) Write back to projects table (idempotent — skip if unchanged)
      const { data: current } = await supabase
        .from('projects')
        .select('phase_progress, gates_passed')
        .eq('id', id)
        .single();

      const currentProgress = current?.phase_progress as unknown as PhaseProgress | null;
      const changed =
        !currentProgress ||
        JSON.stringify(currentProgress) !== JSON.stringify(progress) ||
        current?.gates_passed !== gatesPassed;

      if (changed) {
        await supabase
          .from('projects')
          .update({
            phase_progress: progress as unknown as Record<string, unknown>,
            gates_passed: gatesPassed,
          })
          .eq('id', id);

        // Invalidate project query so Dashboard picks up the new values
        queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(id) });
      }

      return { progress, gatesPassed };
    },
    enabled: !!projectId,
    staleTime: 60_000,
    retry: 1,
  });
}
