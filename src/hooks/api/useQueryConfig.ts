/**
 * Shared React Query configuration
 *
 * Centralizes query key factories and default options
 * to ensure consistent caching and invalidation across the app.
 */

/**
 * Sentinel value used in query keys when an id/projectId is undefined.
 *
 * All queries that accept an optional id also set `enabled: !!id`, so the
 * query never fires with a sentinel key. Using a dedicated sentinel instead
 * of an empty string prevents cache-key collisions between "no id yet" and
 * a hypothetical real empty-string id.
 */
const NONE = '__none__' as const;

/** Resolve an optional id to a cache-safe string. */
const k = (id: string | undefined): string => id ?? NONE;

/**
 * Query key factory — provides type-safe, consistent cache keys.
 *
 * Convention: ['table-name'] for lists, ['table-name', id] for details.
 * Follows the pattern from §7 of WBS_Mock_To_Live_Migration.md.
 *
 * All key functions accept `string | undefined` so callers never need
 * `?? ''` — the factory resolves undefined to a sentinel value internally.
 */
export const queryKeys = {
  // Layer 0: Project backbone
  projects: {
    all: ['projects'] as const,
    detail: (id: string | undefined) => ['projects', k(id)] as const,
    stats: (id: string | undefined) => ['projects', k(id), 'stats'] as const,
  },

  // Layer 1: Step 1 — Problem Definition
  briefs: {
    all: ['briefs'] as const,
    detail: (projectId: string | undefined) => ['briefs', k(projectId)] as const,
  },
  constraints: {
    all: ['constraints'] as const,
    byProject: (projectId: string | undefined) => ['constraints', k(projectId)] as const,
  },
  kpis: {
    all: ['kpis'] as const,
    byProject: (projectId: string | undefined) => ['kpis', k(projectId)] as const,
  },
  socratic_questions: {
    all: ['socratic_questions'] as const,
    byProject: (projectId: string | undefined) => ['socratic_questions', k(projectId)] as const,
  },
  contradictions: {
    all: ['contradictions'] as const,
    byProject: (projectId: string | undefined) => ['contradictions', k(projectId)] as const,
    detail: (id: string | undefined) => ['contradictions', 'detail', k(id)] as const,
  },

  // Layer 2: Step 1.2 — Assumption Management
  assumptions: {
    all: ['assumptions'] as const,
    byProject: (projectId: string | undefined) => ['assumptions', k(projectId)] as const,
    detail: (id: string | undefined) => ['assumptions', 'detail', k(id)] as const,
  },
  cld_nodes: {
    all: ['cld_nodes'] as const,
    byProject: (projectId: string | undefined) => ['cld_nodes', k(projectId)] as const,
  },
  cld_edges: {
    all: ['cld_edges'] as const,
    byProject: (projectId: string | undefined) => ['cld_edges', k(projectId)] as const,
  },

  // Layer 3: Step 2 — Solution Exploration
  anti_anchor_routes: {
    all: ['anti_anchor_routes'] as const,
    byProject: (projectId: string | undefined) => ['anti_anchor_routes', k(projectId)] as const,
  },
  triz_solutions: {
    all: ['triz_solutions'] as const,
    byProject: (projectId: string | undefined) => ['triz_solutions', k(projectId)] as const,
  },
  layered_triz_solutions: {
    all: ['layered_triz_solutions'] as const,
    byProject: (projectId: string | undefined) => ['layered_triz_solutions', k(projectId)] as const,
  },
  directed_triz_solutions: {
    all: ['directed_triz_solutions'] as const,
    byProject: (projectId: string | undefined) => ['directed_triz_solutions', k(projectId)] as const,
  },
  subsystems: {
    all: ['subsystems'] as const,
    byProject: (projectId: string | undefined) => ['subsystems', k(projectId)] as const,
  },
  scamper_variants: {
    all: ['scamper_variants'] as const,
    byProject: (projectId: string | undefined) => ['scamper_variants', k(projectId)] as const,
  },
  alternatives: {
    all: ['alternatives'] as const,
    byProject: (projectId: string | undefined) => ['alternatives', k(projectId)] as const,
    detail: (id: string | undefined) => ['alternatives', 'detail', k(id)] as const,
  },
  concept_routes: {
    all: ['concept_routes'] as const,
    byProject: (projectId: string | undefined) => ['concept_routes', k(projectId)] as const,
  },
  compatibility_pairs: {
    all: ['compatibility_pairs'] as const,
    byProject: (projectId: string | undefined) => ['compatibility_pairs', k(projectId)] as const,
  },

  // Layer 4: Step 3 — Review & Decision
  evidence_matrix: {
    all: ['evidence_matrix'] as const,
    byProject: (projectId: string | undefined) => ['evidence_matrix', k(projectId)] as const,
  },
  risks: {
    all: ['risks'] as const,
    byProject: (projectId: string | undefined) => ['risks', k(projectId)] as const,
  },
  decisions: {
    all: ['decisions'] as const,
    byProject: (projectId: string | undefined) => ['decisions', k(projectId)] as const,
  },
  want_criteria: {
    all: ['want_criteria'] as const,
    byProject: (projectId: string | undefined) => ['want_criteria', k(projectId)] as const,
  },
  want_scores: {
    all: ['want_scores'] as const,
    byProject: (projectId: string | undefined) => ['want_scores', k(projectId)] as const,
  },
  adverse_consequences: {
    all: ['adverse_consequences'] as const,
    byProject: (projectId: string | undefined) => ['adverse_consequences', k(projectId)] as const,
  },
  signatures: {
    all: ['signatures'] as const,
    byProject: (projectId: string | undefined) => ['signatures', k(projectId)] as const,
  },
  action_items: {
    all: ['action_items'] as const,
    byProject: (projectId: string | undefined) => ['action_items', k(projectId)] as const,
  },

  // Layer 5: Knowledge Management
  knowledge_articles: {
    all: ['knowledge_articles'] as const,
    bySlug: (slug: string | undefined) => ['knowledge_articles', k(slug)] as const,
  },
  knowledge_entries: {
    all: ['knowledge_entries'] as const,
    byProject: (projectId: string | undefined) => ['knowledge_entries', k(projectId)] as const,
  },
  constraint_labels: {
    byProject: (projectId: string | undefined) => ['constraint_labels', k(projectId)] as const,
    historyByProject: (projectId: string | undefined) => ['constraint_labels', k(projectId), 'history'] as const,
  },

  // Evidence entries (structured measurement logs)
  evidence_entries: {
    all: ['evidence_entries'] as const,
    byProject: (projectId: string | undefined) => ['evidence_entries', k(projectId)] as const,
    byKpi: (kpiId: string | undefined) => ['evidence_entries', 'kpi', k(kpiId)] as const,
  },

  // Existing tables
  experiments: {
    all: ['experiments'] as const,
    byProject: (projectId: string | undefined) => ['experiments', k(projectId)] as const,
    byAssumptionCode: (projectId: string | undefined, code: string | undefined) =>['experiments', k(projectId), 'assumption', k(code)] as const,  
  },

  // Track page (Kanban view of assumptions + unknown factors)
  track: {
    assumptions: (projectId: string | undefined) => ['track', 'assumptions', k(projectId)] as const,
    unknownFactors: (projectId: string | undefined) => ['track', 'unknown_factors', k(projectId)] as const,
  },
} as const;

/**
 * Default query options applied to all useSupabaseQuery calls.
 *
 * - staleTime: 30 seconds — data is considered fresh for 30s after fetch
 * - retry: 2 — retry failed requests up to 2 times before showing error
 */
export const defaultQueryOptions = {
  staleTime: 30 * 1000, // 30 seconds
  retry: 2,
} as const;
