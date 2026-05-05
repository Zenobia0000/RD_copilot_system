/**
 * useEngineeringSpecDrafts — React Query hook for the 3-step
 * Concept Architecture Pack → Engineering Spec Drafts pipeline.
 *
 * Pattern mirrors useGenerateConceptArchitecturePack: a useMutation that
 * calls the dedicated backend endpoint and invalidates related query keys
 * on success.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./useQueryConfig";
import {
  scamperEngineeringSpecDrafts,
  type EngineeringSpecDraftResponse,
  type SubsystemSuggestRequest,
} from "@/lib/api";

// ── Variables accepted by the mutation ──────────────────────────────────────

export interface GenerateEngineeringSpecVariables {
  /** The user-facing mission description (already in project state). */
  mission: string;
  /** Contradiction descriptions – optional context for the LLM pipeline. */
  contradictions?: string[];
  /** Existing subsystem names to avoid duplication. */
  existing_subsystems?: string[];
}

// ── Hook ────────────────────────────────────────────────────────────────────

/**
 * Triggers the 3-step engineering spec drafts pipeline:
 *   1. Structure expansion
 *   2. AI spec generation (DraftValue provenance)
 *   3. Source strengthening + verification checklist
 *
 * @param projectId – Current project UUID (may be undefined while loading).
 * @param conceptPack – The ConceptArchitecturePack to send. If undefined the
 *                       mutation will be disabled (cannot fire).
 */
export function useGenerateEngineeringSpecDrafts(
  projectId: string | undefined,
  conceptPack: SubsystemSuggestRequest["concept_pack"],
) {
  const qc = useQueryClient();

  return useMutation<
    EngineeringSpecDraftResponse,
    Error,
    GenerateEngineeringSpecVariables
  >({
    mutationFn: (vars) => {
      if (!projectId) throw new Error("projectId is required");
      if (!conceptPack) throw new Error("conceptPack is required");

      const body: SubsystemSuggestRequest = {
        project_id: projectId,
        mission: vars.mission,
        contradictions: vars.contradictions,
        existing_subsystems: vars.existing_subsystems,
        concept_pack: conceptPack,
      };

      return scamperEngineeringSpecDrafts(body);
    },
    onSuccess: () => {
      // Invalidate both the spec drafts cache and subsystem cache (tree may
      // have been enriched with spec data).
      qc.invalidateQueries({
        queryKey: queryKeys.engineering_spec_drafts.byProject(projectId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.subsystems.byProject(projectId),
      });
    },
  });
}
