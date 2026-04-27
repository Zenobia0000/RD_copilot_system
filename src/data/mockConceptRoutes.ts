// Stub — mock data removed in WBS 4.3.4 refactor.
// TODO: Replace with real DB queries once concept_routes + compatibility_pairs are fully wired.
import type { MultiSolutionAdoptionState } from '@/types/conceptRoute';

export const mockAdoptionState: MultiSolutionAdoptionState = {
  matrix: { solutions: [], pairs: [] },
  recommendedRoutes: [],
  antiPatternChecks: [],
};
