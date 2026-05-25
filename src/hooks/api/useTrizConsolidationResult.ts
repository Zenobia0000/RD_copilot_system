/**
 * React Query hook for `triz_consolidation_results` row (v8, migration 012).
 *
 * Backend `/triz/consolidate` upserts the consolidation outcome into Supabase.
 * Whenever possible **backend is the single writer** — see Bug fix (2026-05)
 * below. The FE-side `upsertConsolidationResult` helper is kept as a defensive
 * fallback path (e.g. legacy projects, dev seed) but uses a safe
 * "select-then-merge" strategy so it cannot accidentally null-out columns
 * that backend just wrote.
 *
 * Phase 3 bugfix (migration 020)：
 *   多讀 `verdict_card` 與 `intra_compatibility` 兩欄並回傳；舊 row 沒這兩欄
 *   也不會 crash（undefined fallback）。
 *
 * Bug fix (2026-05)：refetchOnMount: 'always'
 *   舊版預設只有 staleTime=30s。整併剛跑完 setQueryData 後 30 秒內重整，
 *   雖然 cache 已是新值（OK），但若使用者切走 > 30s 後回來，cache 已 stale，
 *   會延遲一個 frame 後 refetch。把 refetchOnMount 改為 'always' 確保
 *   每次掛載都 refetch DB，畫面跟 DB 保證同步，避免 hydration race。
 *
 * Bug fix (2026-05)：upsertConsolidationResult 改 select-merge
 *   Supabase JS upsert 預設 `defaultToNull: true`，payload 缺欄位會把該欄位
 *   **改回 NULL**。舊版 FE upsert 缺 verdict_card → 蓋掉 backend 剛寫好的
 *   verdict_card。新版先 select 整 row、merge 新欄位、再 upsert，避免
 *   無意覆寫任何 backend-managed 欄位。
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { queryKeys, defaultQueryOptions } from '@/hooks/api/useQueryConfig';
import type {
  ConsolidationResult,
  ConsolidationStatus,
  DirectionGroup,
  ConflictReport,
  EngineeringVerdictCard,
  IntraContradictionCompatibility,
} from '@/types/directedTriz';

interface TrizConsolidationRow {
  id: string;
  project_id: string;
  status: string;
  adopted_directions: unknown;
  conflict_report: unknown | null;
  integration_advice: string;
  // Phase 3 (migration 020) — 可能為 undefined（舊 row）或 null（從未填過）
  verdict_card?: unknown | null;
  intra_compatibility?: unknown;
  was_user_picked?: unknown;
  // PR2-Lite (migration 022) — 可能為 undefined（舊 row）或 default 空容器
  candidate_pools?: unknown;
  exhausted_contradictions?: unknown;
  total_rounds?: number | null;
}

const VALID_STATUSES: ConsolidationStatus[] = ['compatible', 'resolved_with_swap', 'conflict'];

const mapRow = (r: TrizConsolidationRow): ConsolidationResult => ({
  status: (VALID_STATUSES.includes(r.status as ConsolidationStatus)
    ? r.status
    : 'compatible') as ConsolidationStatus,
  adopted_directions: (r.adopted_directions ?? {}) as Record<string, DirectionGroup>,
  conflict_report: (r.conflict_report ?? null) as ConflictReport | null,
  integration_advice: r.integration_advice ?? '',
  // Phase 3 bugfix — 讀 verdict_card / intra_compatibility / was_user_picked
  verdict_card: (r.verdict_card ?? null) as EngineeringVerdictCard | null,
  intra_compatibility: Array.isArray(r.intra_compatibility)
    ? (r.intra_compatibility as IntraContradictionCompatibility[])
    : undefined,
  was_user_picked:
    r.was_user_picked && typeof r.was_user_picked === 'object'
      ? (r.was_user_picked as Record<string, string>)
      : undefined,
  // PR2-Lite — candidate_pools / exhausted_contradictions / total_rounds
  candidate_pools:
    r.candidate_pools && typeof r.candidate_pools === 'object' && !Array.isArray(r.candidate_pools)
      ? (r.candidate_pools as Record<string, DirectionGroup[]>)
      : undefined,
  exhausted_contradictions: Array.isArray(r.exhausted_contradictions)
    ? (r.exhausted_contradictions as string[])
    : undefined,
  total_rounds:
    typeof r.total_rounds === 'number' ? r.total_rounds : undefined,
});

/**
 * Fetch the consolidation result for a project (at most one row per project).
 * Returns `ConsolidationResult | null`.
 *
 * `refetchOnMount: 'always'` — 確保每次頁面 mount/重整都從 DB 拿最新值。
 * 與整併成功後 `setQueryData` 配合：cache 立即有新值（畫面瞬間更新），
 * 接著背景 refetch 校正成 DB 真實值（防止任何 race / 多 tab 衝突）。
 */
export function useTrizConsolidationResult(projectId: string | undefined) {
  return useQuery<ConsolidationResult | null, Error>({
    queryKey: queryKeys.triz_consolidation_results.byProject(projectId),
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- table added in migration 012, Supabase types not regenerated yet
      const { data, error } = await (supabase as any)
        .from('triz_consolidation_results')
        .select('*')
        .eq('project_id', projectId!)
        .maybeSingle();
      if (error) throw error;
      if (!data) return null;
      return mapRow(data as TrizConsolidationRow);
    },
    enabled: !!projectId,
    ...defaultQueryOptions,
    // 整併重整 bug 修復：強制每次 mount 重抓，避免 stale cache。
    refetchOnMount: 'always',
  });
}

/**
 * Directly upsert a ConsolidationResult into `triz_consolidation_results`.
 *
 * **Use sparingly** — backend `/triz/consolidate` already persists the full
 * row including `verdict_card` / `intra_compatibility`. This helper exists
 * only for legacy / dev-seed paths.
 *
 * Bug fix (2026-05): 改成 select-then-merge 模式。
 *   原本直接 upsert(payload, on_conflict='id') 會踩到 Supabase JS
 *   `defaultToNull: true` 的陷阱：payload 缺的欄位 → DB 該欄位被改回 NULL。
 *   現在做法：
 *     1. 先 select 既有 row（如存在），拿到完整欄位
 *     2. 用呼叫端提供的 result 物件「淺合併」進去
 *     3. 再 upsert 整個 merged payload
 *   這樣即使呼叫端 result 沒帶 verdict_card，DB 上已有的 verdict_card 也會
 *   一起被寫回，永遠不會弄丟欄位。
 */
export async function upsertConsolidationResult(
  projectId: string,
  result: ConsolidationResult,
): Promise<void> {
  const tcrId = `TCR-${projectId.slice(0, 8)}`;

  // Step 1: fetch existing row (if any) so we can merge instead of overwrite.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { data: existing, error: selErr } = await (supabase as any)
    .from('triz_consolidation_results')
    .select('*')
    .eq('id', tcrId)
    .maybeSingle();
  if (selErr) {
    console.warn('upsertConsolidationResult: select existing row failed:', selErr);
    // continue — we'll still try the upsert with whatever the caller supplied
  }

  // Step 2: build merged payload. Start from existing row (or empty), then
  // overlay caller-supplied fields. Caller can pass `undefined` to mean
  // "don't touch", or an explicit value to update.
  const merged: Record<string, unknown> = {
    ...(existing ?? {}),
    id: tcrId,
    project_id: projectId,
    status: result.status,
    adopted_directions: result.adopted_directions,
    conflict_report: result.conflict_report,
    integration_advice: result.integration_advice ?? '',
  };
  if (result.verdict_card !== undefined) merged.verdict_card = result.verdict_card;
  if (result.intra_compatibility !== undefined) merged.intra_compatibility = result.intra_compatibility;
  if (result.was_user_picked !== undefined) merged.was_user_picked = result.was_user_picked;
  if (result.candidate_pools !== undefined) merged.candidate_pools = result.candidate_pools;
  if (result.exhausted_contradictions !== undefined)
    merged.exhausted_contradictions = result.exhausted_contradictions;
  if (result.total_rounds !== undefined) merged.total_rounds = result.total_rounds;

  // Step 3: upsert the merged payload.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { error } = await (supabase as any)
    .from('triz_consolidation_results')
    .upsert(merged, { onConflict: 'id' });
  if (error) {
    console.error('upsertConsolidationResult failed:', error);
  }
}
