/**
 * API Hooks barrel file
 *
 * Re-exports all API hooks for convenient imports.
 * Usage: import { useProjects, queryKeys } from '@/hooks/api';
 */

// Shared configuration & utilities
export { queryKeys, defaultQueryOptions } from './useQueryConfig';
export { useSupabaseQuery, useSupabaseMutation } from './useSupabaseQuery';

// Seed utilities (dev only)
export { seedDemoProject, clearDemoData, seedShowcaseProjects, clearAllShowcaseData } from './seed';

// --- Sprint 1: Projects + Step 1 ---
export { useProjects, useProject, useCreateProject, useUpdateProject, useDeleteProject, useProjectStats } from './useProjects';
export {
  useBrief,
  useUpsertBrief,
  useConstraints,
  useCreateConstraint,
  useUpdateConstraint,
  useDeleteConstraint,
  useKpis,
  useCreateKpi,
  useUpdateKpi,
  useDeleteKpi,
} from './useBrief';
// Explore page hooks (Socratic Q&A, Explore Contradictions)
export {
  useSocraticQuestions,
  useCreateSocraticQuestion,
  useUpdateSocraticQuestion,
  useDeleteSocraticQuestion,
  useExploreContradictions,
  useMutateCldNode,
  useMutateCldEdge,
} from './useExplore';

// Contradiction Identification page hooks
export {
  useContradictions,
  useCreateContradiction,
  useUpdateContradiction,
  useDeleteContradiction,
} from './useContradictions';

// TRIZ Layered Drill-Down persistence (migration 010)
export { useLayeredTrizSolutions } from './useLayeredTrizSolutions';

// TRIZ Directed Solutions persistence (migration 011)
export { useDirectedTrizSolutions } from './useDirectedTrizSolutions';

// TRIZ Consolidation Result persistence (migration 012)
export { useTrizConsolidationResult, upsertConsolidationResult } from './useTrizConsolidationResult';

// --- Sprint 1.2: Assumptions + CLD ---
export {
  useAssumptions,
  useCreateAssumptionMapped,
  useUpdateAssumption,
  useDeleteAssumption,
  useCldNodes,
  useCldEdges,
  useLinkedContradictions,
  useSocraticFeedback,
  useConvergenceImpact,
} from './useAssumptions';

// --- Track page (Kanban + Unknown Factors) ---
export {
  useTrackAssumptions,
  useUpdateTrackAssumptionStatus,
  useCreateTrackAssumption,
  useDeleteTrackAssumption,
  useUnknownFactors,
  useCreateUnknownFactor,
  useUpdateUnknownFactor,
  useSaveUnknownFactors,
  useConvertUnknownToAssumption,
  useTrackExperiments,
} from './useTrack';

// --- Sprint 2: Step 2 Solution Exploration ---
export {
  useAntiAnchorRoutes,
  useCreateAntiAnchorRoute,
  useUpdateAntiAnchorRoute,
  useDeleteAntiAnchorRoute,
  useTrizSolutions,
  useCreateTrizSolution,
  useUpdateTrizSolution,
  useSubsystems,
  useCreateSubsystem,
  useUpdateSubsystem,
  useDeleteSubsystem,
  useAlternatives,
  useCreateAlternative,
  useUpdateAlternative,
  useDeleteAlternative,
} from './useCreate';
export {
  useConceptRoutes,
  useCreateConceptRoute,
  useCompatibilityPairs,
  useCreateCompatibilityPairs,
} from './useConceptRoutes';

// Solution Explorer page hooks (Solution-level view of alternatives)
export { useSolutions, useCreateSolution, useUpdateSolution, useConvergenceGraph } from './useSolutions';

// Pre-CAD Review page hooks
export { usePreCadSolutions, usePreCadConvergenceStats, useUpdatePreCadReview } from './usePreCadReview';

// --- Sprint 3: Step 3 Review & Decision ---
export {
  useEvidenceMatrix,
  useCreateEvidenceRow,
  useUpdateEvidenceRow,
  useRisks,
  useCreateRisk,
  useUpdateRisk,
  useDeleteRisk,
  useExperiments,
  useCreateExperiment,
  useUpdateExperiment,
} from './useDesignReview';
// Sprint 3.2: Decision Record hooks
export {
  useDecision,
  useUpsertDecision,
  useWantCriteria,
  useCreateWantCriterion,
  useUpdateWantCriterion,
  useDeleteWantCriterion,
  useWantScores,
  useUpsertWantScore,
  useAdverseConsequences,
  useCreateAdverseConsequence,
  useUpdateAdverseConsequence,
  useSignatures,
  useCreateSignature,
  useUpdateSignature,
  useActionItems,
  useCreateActionItem,
  useUpdateActionItem,
  useDeleteActionItem,
} from './useDecisionRecord';

// --- Auto-TRIZ v2: Analyst hooks (WBS 8.5) ---
export {
  useEntryGrading,
  useFiveWhy,
  useKtAnalysis,
  useFunctionAnalysis,
} from './useAnalystV2';

// --- Auto-TRIZ v2: Create V2 hooks (WBS 8.6) ---
export {
  useOzOtAnalysis,
  useEvidenceCoverage,
} from './useCreateV2';

// --- Evidence Entries (structured measurement logs) ---
export {
  useEvidenceEntries,
  useEvidenceEntriesByKpi,
  useCreateEvidenceEntry,
  useDeleteEvidenceEntry,
} from './useEvidenceEntries';
export type { CreateEvidenceEntryInput } from './useEvidenceEntries';

// --- Sprint 4: Knowledge Management ---
export {
  useKnowledgeArticles,
  useKnowledgeArticle,
  useCreateKnowledgeArticle,
  useUpdateKnowledgeArticle,
  useKnowledgeEntries,
  useCreateKnowledgeEntry,
  useUpdateKnowledgeEntry,
} from './useKnowledge';
export type { KnowledgeEntry } from './useKnowledge';
