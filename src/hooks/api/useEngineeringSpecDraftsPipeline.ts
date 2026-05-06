/**
 * useEngineeringSpecDraftsPipeline — 3-step split-API pipeline hook.
 *
 * Replaces the single long-running mutation in useGenerateEngineeringSpecDrafts
 * with three sequential HTTP calls, each well within the 300 s Nginx timeout:
 *
 *   Step 1: Structure Expansion    (~90-120 s)  → subsystem tree + package_map
 *   Step 2: AI Spec Generation     (~30-60 s)   → raw drafts
 *   Step 3: Source Strengthening   (~30-60 s)   → enriched drafts
 *
 * Progressive state is exposed so the UI can render partial results as each
 * step completes (e.g. show subsystem tree immediately after step 1).
 *
 * @see plans/split-api-engineering-spec-drafts.md  §3.3
 */

import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./useQueryConfig";
import {
  engSpecStep1Expand,
  engSpecStep2Generate,
  engSpecStep3Strengthen,
  type SubsystemSuggestRequest,
  type EngineeringSpecDraftResponse,
  type EngSpecStep1Response,
  type EngSpecStep2Response,
  type EngSpecStep3Response,
} from "@/lib/api";
import type { GenerateEngineeringSpecVariables } from "./useEngineeringSpecDrafts";

// ── Pipeline phase enum ─────────────────────────────────────────────────────

export type PipelinePhase =
  | "idle"
  | "step1"
  | "step2"
  | "step3"
  | "done"
  | "error";

// ── Pipeline state ──────────────────────────────────────────────────────────

export interface PipelineState {
  /** Current phase of the 3-step pipeline. */
  status: PipelinePhase;
  /** Result from Step 1 (structure expansion). Available after step1 completes. */
  step1Result: EngSpecStep1Response | null;
  /** Result from Step 2 (AI spec generation). Available after step2 completes. */
  step2Result: EngSpecStep2Response | null;
  /** Result from Step 3 (source strengthening). Available after step3 completes. */
  step3Result: EngSpecStep3Response | null;
  /** Error if the pipeline fails at any step. */
  error: Error | null;
  /** Numeric step indicator: 0 = idle, 1-3 = running that step. */
  currentStep: number;
}

const INITIAL_STATE: PipelineState = {
  status: "idle",
  step1Result: null,
  step2Result: null,
  step3Result: null,
  error: null,
  currentStep: 0,
};

// ── Hook ────────────────────────────────────────────────────────────────────

/**
 * 3-step engineering spec drafts pipeline.
 *
 * Usage:
 * ```ts
 * const pipeline = useEngineeringSpecDraftsPipeline(projectId, conceptPack);
 * // Trigger:
 * const result = await pipeline.run({ mission, contradictions, existing_subsystems });
 * // Progressive rendering:
 * if (pipeline.step1Result) renderSubsystemTree(pipeline.step1Result.subsystems);
 * if (pipeline.step2Result) renderDraftPreview(pipeline.step2Result.drafts);
 * ```
 *
 * @param projectId   Current project UUID (may be undefined while loading).
 * @param conceptPack The ConceptArchitecturePack to send. Required to run.
 */
export function useEngineeringSpecDraftsPipeline(
  projectId: string | undefined,
  conceptPack: SubsystemSuggestRequest["concept_pack"],
) {
  const qc = useQueryClient();
  const [pipelineState, setPipelineState] =
    useState<PipelineState>(INITIAL_STATE);

  const run = useCallback(
    async (
      vars: GenerateEngineeringSpecVariables,
    ): Promise<EngineeringSpecDraftResponse> => {
      if (!projectId) throw new Error("projectId is required");
      if (!conceptPack) throw new Error("conceptPack is required");

      // Reset and enter step 1
      setPipelineState({
        ...INITIAL_STATE,
        status: "step1",
        currentStep: 1,
      });

      try {
        // ── Step 1: Structure Expansion ─────────────────────────────────
        const s1 = await engSpecStep1Expand({
          project_id: projectId,
          mission: vars.mission,
          contradictions: vars.contradictions,
          existing_subsystems: vars.existing_subsystems,
          concept_pack: conceptPack,
        });
        setPipelineState((s) => ({
          ...s,
          step1Result: s1,
          status: "step2",
          currentStep: 2,
        }));

        // ── Step 2: AI Spec Generation ──────────────────────────────────
        const s2 = await engSpecStep2Generate({
          project_id: projectId,
          mission: vars.mission,
          subsystems: s1.subsystems,
        });
        setPipelineState((s) => ({
          ...s,
          step2Result: s2,
          status: "step3",
          currentStep: 3,
        }));

        // ── Step 3: Source Strengthening ─────────────────────────────────
        const s3 = await engSpecStep3Strengthen({
          project_id: projectId,
          mission: vars.mission,
          drafts: s2.drafts,
          subsystems: s1.subsystems,
        });
        setPipelineState((s) => ({
          ...s,
          step3Result: s3,
          status: "done",
        }));

        // ── Assemble final response ─────────────────────────────────────
        const final: EngineeringSpecDraftResponse = {
          drafts: s3.drafts,
          subsystem_tree: s1.subsystems,
          package_map: s1.package_map,
        };

        // Invalidate caches so downstream queries refetch
        qc.invalidateQueries({
          queryKey: queryKeys.engineering_spec_drafts.byProject(projectId),
        });
        qc.invalidateQueries({
          queryKey: queryKeys.subsystems.byProject(projectId),
        });

        return final;
      } catch (err) {
        setPipelineState((s) => ({
          ...s,
          status: "error",
          error: err as Error,
        }));
        throw err;
      }
    },
    [projectId, conceptPack, qc],
  );

  /** Reset the pipeline to idle state. */
  const reset = useCallback(() => {
    setPipelineState(INITIAL_STATE);
  }, []);

  /** Whether the pipeline is currently running (any step in progress). */
  const isRunning =
    pipelineState.status === "step1" ||
    pipelineState.status === "step2" ||
    pipelineState.status === "step3";

  return {
    ...pipelineState,
    run,
    reset,
    isRunning,
  };
}
