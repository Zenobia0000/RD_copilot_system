/**
 * Generic Supabase + React Query hooks
 *
 * Provides reusable `useSupabaseQuery` and `useSupabaseMutation` that wrap
 * @tanstack/react-query with Supabase client calls, error toasts, and
 * optimistic update helpers.
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type QueryKey,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { defaultQueryOptions } from '@/hooks/api/useQueryConfig';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Filter operators supported by the query builder */
export interface QueryFilter {
  column: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'ilike' | 'in' | 'is';
  value: unknown;
}

export interface SupabaseQueryOptions<T> {
  /** Supabase table name */
  table: string;
  /** React Query cache key */
  queryKey: QueryKey;
  /** Columns to select (default: '*') */
  select?: string;
  /** Filters to apply */
  filters?: QueryFilter[];
  /** Order by column */
  orderBy?: { column: string; ascending?: boolean };
  /** Limit result count */
  limit?: number;
  /** Whether to select a single row */
  single?: boolean;
  /** Additional react-query options */
  queryOptions?: Omit<UseQueryOptions<T, Error>, 'queryKey' | 'queryFn'>;
  /** Whether the query is enabled */
  enabled?: boolean;
}

export type MutationType = 'insert' | 'update' | 'delete' | 'upsert';

export interface SupabaseMutationOptions<TData, TVariables> {
  /** Supabase table name */
  table: string;
  /** Type of mutation */
  type: MutationType;
  /** Query keys to invalidate on success */
  invalidateKeys?: QueryKey[];
  /** Column(s) used for matching on update/delete (default: 'id') */
  matchColumn?: string;
  /** Column(s) used for conflict resolution on upsert (e.g. 'project_id') */
  onConflict?: string;
  /** Toast message on success (set to false to suppress) */
  successMessage?: string | false;
  /** Toast message on error (set to false to suppress) */
  errorMessage?: string | false;
  /** Enable optimistic updates */
  optimistic?: {
    /** The query key of the list cache to update optimistically */
    queryKey: QueryKey;
    /** Transform the cached data optimistically. Receives current cache and the mutation variables. */
    updater: (oldData: TData[] | undefined, variables: TVariables) => TData[];
  };
  /** Additional react-query mutation options */
  mutationOptions?: Omit<
    UseMutationOptions<TData, Error, TVariables>,
    'mutationFn' | 'onSuccess' | 'onError' | 'onMutate' | 'onSettled'
  >;
}

// ---------------------------------------------------------------------------
// useSupabaseQuery
// ---------------------------------------------------------------------------

/**
 * Generic hook for reading data from a Supabase table.
 *
 * @example
 * ```ts
 * const { data, isLoading } = useSupabaseQuery<Project[]>({
 *   table: 'projects',
 *   queryKey: queryKeys.projects.all,
 *   filters: [{ column: 'status', operator: 'eq', value: 'in_progress' }],
 *   orderBy: { column: 'created_at', ascending: false },
 * });
 * ```
 */
export function useSupabaseQuery<T>(options: SupabaseQueryOptions<T>) {
  const {
    table,
    queryKey,
    select = '*',
    filters = [],
    orderBy,
    limit,
    single = false,
    queryOptions,
    enabled = true,
  } = options;

  return useQuery<T, Error>({
    queryKey,
    queryFn: async (): Promise<T> => {
      let query = supabase.from(table).select(select);

      // Apply filters
      for (const filter of filters) {
        switch (filter.operator) {
          case 'eq':
            query = query.eq(filter.column, filter.value);
            break;
          case 'neq':
            query = query.neq(filter.column, filter.value);
            break;
          case 'gt':
            query = query.gt(filter.column, filter.value);
            break;
          case 'gte':
            query = query.gte(filter.column, filter.value);
            break;
          case 'lt':
            query = query.lt(filter.column, filter.value);
            break;
          case 'lte':
            query = query.lte(filter.column, filter.value);
            break;
          case 'like':
            query = query.like(filter.column, filter.value as string);
            break;
          case 'ilike':
            query = query.ilike(filter.column, filter.value as string);
            break;
          case 'in':
            query = query.in(filter.column, filter.value as unknown[]);
            break;
          case 'is':
            query = query.is(filter.column, filter.value as null);
            break;
        }
      }

      // Order
      if (orderBy) {
        query = query.order(orderBy.column, { ascending: orderBy.ascending ?? true });
      }

      // Limit
      if (limit !== undefined) {
        query = query.limit(limit);
      }

      // Single row
      if (single) {
        const { data, error } = await query.maybeSingle();
        if (error) throw error;
        return data as T;
      }

      const { data, error } = await query;
      if (error) throw error;
      return data as T;
    },
    ...defaultQueryOptions,
    enabled,
    ...queryOptions,
  });
}

// ---------------------------------------------------------------------------
// useSupabaseMutation
// ---------------------------------------------------------------------------

/**
 * Generic hook for insert / update / delete / upsert on a Supabase table.
 *
 * Includes built-in error toast, optional success toast, cache invalidation,
 * and optimistic update support.
 *
 * @example
 * ```ts
 * const createProject = useSupabaseMutation<Project, Partial<Project>>({
 *   table: 'projects',
 *   type: 'insert',
 *   invalidateKeys: [queryKeys.projects.all],
 *   successMessage: 'Project created',
 * });
 *
 * createProject.mutate({ name: 'New Project' });
 * ```
 */
export function useSupabaseMutation<TData = unknown, TVariables = unknown>(
  options: SupabaseMutationOptions<TData, TVariables>,
) {
  const {
    table,
    type,
    invalidateKeys = [],
    matchColumn = 'id',
    onConflict,
    successMessage,
    errorMessage,
    optimistic,
    mutationOptions,
  } = options;

  const queryClient = useQueryClient();

  return useMutation<TData, Error, TVariables>({
    mutationFn: async (variables: TVariables): Promise<TData> => {
      let result: { data: unknown; error: unknown };

      switch (type) {
        case 'insert':
          result = await supabase.from(table).insert(variables as Record<string, unknown>).select().single();
          break;
        case 'update': {
          const { [matchColumn]: matchValue, ...updateData } = variables as Record<string, unknown>;
          result = await supabase
            .from(table)
            .update(updateData)
            .eq(matchColumn, matchValue)
            .select()
            .single();
          break;
        }
        case 'delete': {
          const deleteMatchValue = (variables as Record<string, unknown>)[matchColumn];
          result = await supabase.from(table).delete().eq(matchColumn, deleteMatchValue);
          break;
        }
        case 'upsert':
          result = await supabase.from(table).upsert(
            variables as Record<string, unknown>,
            onConflict ? { onConflict } : undefined,
          ).select().single();
          break;
        default:
          throw new Error(`Unsupported mutation type: ${type}`);
      }

      if (result.error) throw result.error;
      return result.data as TData;
    },

    // Optimistic update: snapshot previous data, apply optimistic updater
    onMutate: optimistic
      ? async (variables: TVariables) => {
          // Cancel outgoing queries so they don't overwrite our optimistic update
          await queryClient.cancelQueries({ queryKey: optimistic.queryKey });

          const previousData = queryClient.getQueryData<TData[]>(optimistic.queryKey);

          queryClient.setQueryData<TData[]>(
            optimistic.queryKey,
            (old) => optimistic.updater(old, variables),
          );

          return { previousData };
        }
      : undefined,

    onSuccess: (_data) => {
      // Invalidate related caches
      for (const key of invalidateKeys) {
        queryClient.invalidateQueries({ queryKey: key });
      }

      if (successMessage !== false && successMessage) {
        toast.success(successMessage);
      }
    },

    onError: (error, _variables, context) => {
      // Rollback optimistic update
      if (optimistic && context && typeof context === 'object' && 'previousData' in context) {
        queryClient.setQueryData(
          optimistic.queryKey,
          (context as { previousData: TData[] }).previousData,
        );
      }

      const message = errorMessage !== false
        ? (errorMessage ?? `Operation failed: ${error.message}`)
        : undefined;

      if (message) {
        toast.error(message);
      }

      console.error(`[useSupabaseMutation] ${table}.${type} failed:`, error);
    },

    onSettled: () => {
      // Always refetch after mutation to ensure consistency
      if (optimistic) {
        queryClient.invalidateQueries({ queryKey: optimistic.queryKey });
      }
    },

    ...mutationOptions,
  });
}
