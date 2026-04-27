/**
 * API hooks for Knowledge Management (Layer 5)
 *
 * Covers: knowledge_articles (KnowledgeBase page), knowledge_entries (Feynman page).
 *
 * All hooks use the generic useSupabaseQuery / useSupabaseMutation
 * helpers and perform snake_case -> camelCase mapping at the hook layer.
 */

import { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';
import { queryKeys } from './useQueryConfig';
import type { KnowledgeArticle } from '@/types/knowledge';
import {
  CONSTRAINT_LABEL_CLASSIFIER_VERSION,
  CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
} from '@/lib/constraintLabeling';

// ---------------------------------------------------------------------------
// Row types (DB snake_case)
// ---------------------------------------------------------------------------

interface KnowledgeArticleDbRow {
  id: string;
  slug: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  author: string;
  published_at: string;
  content: string;
  related_links: { label: string; url: string }[];
  created_at: string;
  updated_at: string;
}

interface KnowledgeEntryDbRow {
  id: string;
  project_id: string;
  asset_type: string;
  title: string;
  content: string;
  reviewed: boolean;
  created_at: string;
  updated_at: string;
}

export const CONSTRAINT_LABEL_ASSET_TYPE = 'constraint_label_map';
export const CONSTRAINT_LABEL_HISTORY_ASSET_TYPE = 'constraint_label_history';
export const HARD_CONSTRAINT_LABEL_TITLE = 'hard_constraints';

export interface ConstraintLabelMapPayload {
  schemaVersion: number;
  classifierVersion: string;
  labels: Record<string, string>;
  updatedAt: string;
}

export type ConstraintLabelActionType =
  | 'auto_classify_sync'
  | 'manual_override'
  | 'merge_labels'
  | 'upgrade_classifier_version'
  | 'rollback';

export interface ConstraintLabelHistoryPayload {
  schemaVersion: number;
  classifierVersion: string;
  action: ConstraintLabelActionType;
  source: 'dashboard' | 'dictionary';
  actor: {
    id: string;
    email: string;
    displayName: string;
  };
  before: Record<string, string>;
  after: Record<string, string>;
  note?: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Frontend types for knowledge_entries
// ---------------------------------------------------------------------------

export interface KnowledgeEntry {
  id: string;
  projectId: string;
  assetType: string;
  title: string;
  content: string;
  reviewed: boolean;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Mappers: DB row -> frontend type
// ---------------------------------------------------------------------------

function mapArticle(row: KnowledgeArticleDbRow): KnowledgeArticle {
  return {
    id: row.id,
    slug: row.slug,
    title: row.title,
    description: row.description ?? '',
    category: row.category as KnowledgeArticle['category'],
    tags: row.tags ?? [],
    author: row.author ?? '',
    publishedAt: row.published_at ?? '',
    content: row.content ?? '',
    relatedLinks: row.related_links ?? [],
  };
}

function mapEntry(row: KnowledgeEntryDbRow): KnowledgeEntry {
  return {
    id: row.id,
    projectId: row.project_id,
    assetType: row.asset_type,
    title: row.title,
    content: row.content ?? '',
    reviewed: row.reviewed,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

// ---------------------------------------------------------------------------
// Knowledge Articles (KnowledgeBase page)
// ---------------------------------------------------------------------------

/** List all knowledge articles (not project-scoped) */
export function useKnowledgeArticles() {
  const result = useSupabaseQuery<KnowledgeArticleDbRow[]>({
    table: 'knowledge_articles',
    queryKey: queryKeys.knowledge_articles.all,
    orderBy: { column: 'published_at', ascending: false },
  });

  return {
    ...result,
    data: result.data?.map(mapArticle) ?? [],
  };
}

/** Fetch a single knowledge article by slug */
export function useKnowledgeArticle(slug: string | undefined) {
  const result = useSupabaseQuery<KnowledgeArticleDbRow>({
    table: 'knowledge_articles',
    queryKey: queryKeys.knowledge_articles.bySlug(slug),
    filters: slug
      ? [{ column: 'slug', operator: 'eq' as const, value: slug }]
      : [],
    single: true,
    enabled: !!slug,
  });

  return {
    ...result,
    data: result.data ? mapArticle(result.data) : undefined,
  };
}

/** Create a new knowledge article */
export function useCreateKnowledgeArticle() {
  return useSupabaseMutation<KnowledgeArticleDbRow, {
    slug: string;
    title: string;
    description?: string;
    category: string;
    tags?: string[];
    author?: string;
    content?: string;
    related_links?: { label: string; url: string }[];
  }>({
    table: 'knowledge_articles',
    type: 'insert',
    invalidateKeys: [queryKeys.knowledge_articles.all],
    successMessage: '已新增知識文章',
  });
}

/** Update an existing knowledge article */
export function useUpdateKnowledgeArticle() {
  return useSupabaseMutation<KnowledgeArticleDbRow, {
    id: string;
    slug?: string;
    title?: string;
    description?: string;
    category?: string;
    tags?: string[];
    author?: string;
    content?: string;
    related_links?: { label: string; url: string }[];
  }>({
    table: 'knowledge_articles',
    type: 'update',
    invalidateKeys: [queryKeys.knowledge_articles.all],
    successMessage: '知識文章已更新',
  });
}

// ---------------------------------------------------------------------------
// Knowledge Entries (Feynman page)
// ---------------------------------------------------------------------------

/** List knowledge entries for a project */
export function useKnowledgeEntries(projectId: string | undefined) {
  const result = useSupabaseQuery<KnowledgeEntryDbRow[]>({
    table: 'knowledge_entries',
    queryKey: queryKeys.knowledge_entries.byProject(projectId),
    filters: projectId
      ? [{ column: 'project_id', operator: 'eq' as const, value: projectId }]
      : [],
    orderBy: { column: 'created_at', ascending: false },
    enabled: !!projectId,
  });

  return {
    ...result,
    data: result.data?.map(mapEntry) ?? [],
  };
}

/** Create a new knowledge entry */
export function useCreateKnowledgeEntry() {
  return useSupabaseMutation<KnowledgeEntryDbRow, {
    project_id: string;
    asset_type: string;
    title: string;
    content?: string;
    reviewed?: boolean;
  }>({
    table: 'knowledge_entries',
    type: 'insert',
    invalidateKeys: [queryKeys.knowledge_entries.all],
    successMessage: '已新增知識條目',
  });
}

/** Update a knowledge entry (e.g. mark as reviewed) */
export function useUpdateKnowledgeEntry() {
  return useSupabaseMutation<KnowledgeEntryDbRow, {
    id: string;
    title?: string;
    content?: string;
    reviewed?: boolean;
    asset_type?: string;
  }>({
    table: 'knowledge_entries',
    type: 'update',
    invalidateKeys: [queryKeys.knowledge_entries.all],
    successMessage: '知識條目已更新',
  });
}

export function useConstraintLabelMap(projectId: string | undefined) {
  const result = useSupabaseQuery<KnowledgeEntryDbRow[]>({
    table: 'knowledge_entries',
    queryKey: queryKeys.constraint_labels.byProject(projectId),
    filters: projectId
      ? [
          { column: 'project_id', operator: 'eq' as const, value: projectId },
          { column: 'asset_type', operator: 'eq' as const, value: CONSTRAINT_LABEL_ASSET_TYPE },
          { column: 'title', operator: 'eq' as const, value: HARD_CONSTRAINT_LABEL_TITLE },
        ]
      : [],
    orderBy: { column: 'created_at', ascending: false },
    limit: 1,
    enabled: !!projectId,
  });

  const entry = result.data?.[0];
  let payload: ConstraintLabelMapPayload = {
    schemaVersion: CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
    classifierVersion: CONSTRAINT_LABEL_CLASSIFIER_VERSION,
    labels: {},
    updatedAt: new Date(0).toISOString(),
  };

  if (entry?.content) {
    try {
      const parsed = JSON.parse(entry.content);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        const maybePayload = parsed as Partial<ConstraintLabelMapPayload>;
        if (maybePayload.labels && typeof maybePayload.labels === 'object' && !Array.isArray(maybePayload.labels)) {
          payload = {
            schemaVersion: maybePayload.schemaVersion ?? CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
            classifierVersion: maybePayload.classifierVersion ?? CONSTRAINT_LABEL_CLASSIFIER_VERSION,
            labels: maybePayload.labels,
            updatedAt: maybePayload.updatedAt ?? entry.updated_at,
          };
        } else {
          // Backward compatibility: legacy content was plain Record<string, string>.
          payload = {
            schemaVersion: CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
            classifierVersion: CONSTRAINT_LABEL_CLASSIFIER_VERSION,
            labels: parsed as Record<string, string>,
            updatedAt: entry.updated_at,
          };
        }
      }
    } catch {
      payload = {
        schemaVersion: CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
        classifierVersion: CONSTRAINT_LABEL_CLASSIFIER_VERSION,
        labels: {},
        updatedAt: entry.updated_at,
      };
    }
  }

  return {
    ...result,
    entryId: entry?.id,
    payload,
    labelMap: payload.labels,
    classifierVersion: payload.classifierVersion,
    schemaVersion: payload.schemaVersion,
    isLegacyPayload: payload.classifierVersion !== CONSTRAINT_LABEL_CLASSIFIER_VERSION
      || payload.schemaVersion !== CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
  };
}

export function buildConstraintLabelPayload(
  labels: Record<string, string>,
  classifierVersion = CONSTRAINT_LABEL_CLASSIFIER_VERSION,
): ConstraintLabelMapPayload {
  return {
    schemaVersion: CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
    classifierVersion,
    labels,
    updatedAt: new Date().toISOString(),
  };
}

export function buildConstraintLabelHistoryPayload(params: {
  action: ConstraintLabelActionType;
  source: 'dashboard' | 'dictionary';
  actor: {
    id: string;
    email: string;
    displayName: string;
  };
  before: Record<string, string>;
  after: Record<string, string>;
  classifierVersion?: string;
  note?: string;
}): ConstraintLabelHistoryPayload {
  return {
    schemaVersion: CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
    classifierVersion: params.classifierVersion ?? CONSTRAINT_LABEL_CLASSIFIER_VERSION,
    action: params.action,
    source: params.source,
    actor: params.actor,
    before: params.before,
    after: params.after,
    note: params.note,
    updatedAt: new Date().toISOString(),
  };
}

export function useCreateConstraintLabelMap(projectId: string | undefined) {
  return useSupabaseMutation<KnowledgeEntryDbRow, {
    project_id: string;
    asset_type: string;
    title: string;
    content: string;
    reviewed?: boolean;
  }>({
    table: 'knowledge_entries',
    type: 'insert',
    invalidateKeys: projectId
      ? [queryKeys.constraint_labels.byProject(projectId), queryKeys.knowledge_entries.byProject(projectId)]
      : [queryKeys.knowledge_entries.all],
    successMessage: false,
    errorMessage: false,
  });
}

export function useUpdateConstraintLabelMap(projectId: string | undefined) {
  return useSupabaseMutation<KnowledgeEntryDbRow, {
    id: string;
    content: string;
    reviewed?: boolean;
  }>({
    table: 'knowledge_entries',
    type: 'update',
    invalidateKeys: projectId
      ? [queryKeys.constraint_labels.byProject(projectId), queryKeys.knowledge_entries.byProject(projectId)]
      : [queryKeys.knowledge_entries.all],
    successMessage: false,
    errorMessage: false,
  });
}

export interface ConstraintLabelHistoryItem {
  id: string;
  projectId: string;
  createdAt: string;
  payload: ConstraintLabelHistoryPayload;
}

export function useConstraintLabelHistory(projectId: string | undefined, limit = 20) {
  const result = useSupabaseQuery<KnowledgeEntryDbRow[]>({
    table: 'knowledge_entries',
    queryKey: [...queryKeys.constraint_labels.historyByProject(projectId), limit],
    filters: projectId
      ? [
          { column: 'project_id', operator: 'eq' as const, value: projectId },
          { column: 'asset_type', operator: 'eq' as const, value: CONSTRAINT_LABEL_HISTORY_ASSET_TYPE },
          { column: 'title', operator: 'eq' as const, value: HARD_CONSTRAINT_LABEL_TITLE },
        ]
      : [],
    orderBy: { column: 'created_at', ascending: false },
    limit,
    enabled: !!projectId,
  });

  const items: ConstraintLabelHistoryItem[] = (result.data ?? [])
    .map((row) => {
      try {
        const parsed = JSON.parse(row.content) as Partial<ConstraintLabelHistoryPayload>;
        if (!parsed || typeof parsed !== 'object') return null;
        if (!parsed.before || !parsed.after || !parsed.action || !parsed.source) return null;
        return {
          id: row.id,
          projectId: row.project_id,
          createdAt: row.created_at,
          payload: {
            schemaVersion: parsed.schemaVersion ?? CONSTRAINT_LABEL_PAYLOAD_SCHEMA_VERSION,
            classifierVersion: parsed.classifierVersion ?? CONSTRAINT_LABEL_CLASSIFIER_VERSION,
            action: parsed.action,
            source: parsed.source,
            actor: parsed.actor ?? {
              id: 'unknown',
              email: 'unknown',
              displayName: 'unknown',
            },
            before: parsed.before,
            after: parsed.after,
            note: parsed.note,
            updatedAt: parsed.updatedAt ?? row.created_at,
          } as ConstraintLabelHistoryPayload,
        };
      } catch {
        return null;
      }
    })
    .filter((item): item is ConstraintLabelHistoryItem => !!item);

  return {
    ...result,
    items,
  };
}

export function useCreateConstraintLabelHistory(projectId: string | undefined) {
  return useSupabaseMutation<KnowledgeEntryDbRow, {
    project_id: string;
    asset_type: string;
    title: string;
    content: string;
    reviewed?: boolean;
  }>({
    table: 'knowledge_entries',
    type: 'insert',
    invalidateKeys: projectId
      ? [queryKeys.constraint_labels.historyByProject(projectId)]
      : [queryKeys.knowledge_entries.all],
    successMessage: false,
    errorMessage: false,
  });
}
