/**
 * useEngineeringSpecDraftsPipeline — 4-step split-API pipeline hook.
 *
 * Replaces the single long-running mutation in useGenerateEngineeringSpecDrafts
 * with four sequential HTTP calls, each well within the 180 s frontend timeout:
 *
 *   Step 1a: LLM Structure Expansion   (~60-150 s) → subsystem tree (pre-spatial)
 *   Step 1b: Spatial Enrichment         (~20-80 s)  → subsystems + package_map
 *   Step 2:  AI Spec Generation         (~30-60 s)  → raw drafts
 *   Step 3:  Source Strengthening       (~30-60 s)  → enriched drafts
 *
 * Progressive state is exposed so the UI can render partial results as each
 * step completes (e.g. show subsystem tree immediately after step 1a).
 *
 * @see plans/fix-step1-timeout-split.md
 */

import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./useQueryConfig";
import {
  engSpecStep1aExpand,
  engSpecStep1bEnrich,
  engSpecStep2Generate,
  engSpecStep3Strengthen,
  type SubsystemSuggestRequest,
  type EngineeringSpecDraftResponse,
  type EngSpecStep1aResponse,
  type EngSpecStep1bResponse,
  type EngSpecStep2Response,
  type EngSpecStep3Response,
} from "@/lib/api";
import type { GenerateEngineeringSpecVariables } from "./useEngineeringSpecDrafts";

// ── Pipeline phase enum ─────────────────────────────────────────────────────

export type PipelinePhase =
  | "idle"
  | "step1a"
  | "step1b"
  | "step2"
  | "step3"
  | "done"
  | "error";

// ── Pipeline state ──────────────────────────────────────────────────────────

export interface PipelineState {
  /** Current phase of the 4-step pipeline. */
  status: PipelinePhase;
  /** Result from Step 1a (LLM structure expansion). Available after step1a completes. */
  step1aResult: EngSpecStep1aResponse | null;
  /** Result from Step 1b (spatial enrichment + package map). Available after step1b completes. */
  step1bResult: EngSpecStep1bResponse | null;
  /**
   * Assembled Step 1 result — same shape as the old EngSpecStep1Response.
   * Available after step1b completes. Used by downstream UI that expects
   * `step1Result.subsystems` and `step1Result.package_map`.
   */
  step1Result: { subsystems: EngSpecStep1bResponse["subsystems"]; package_map: EngSpecStep1bResponse["package_map"] } | null;
  /** Result from Step 2 (AI spec generation). Available after step2 completes. */
  step2Result: EngSpecStep2Response | null;
  /** Result from Step 3 (source strengthening). Available after step3 completes. */
  step3Result: EngSpecStep3Response | null;
  /** Error if the pipeline fails at any step. */
  error: Error | null;
  /** Which pipeline phase was active when the error occurred. */
  failedStep: PipelinePhase | null;
  /** Numeric step indicator: 0 = idle, 1-4 = running that step. */
  currentStep: number;
}

const INITIAL_STATE: PipelineState = {
  status: "idle",
  step1aResult: null,
  step1bResult: null,
  step1Result: null,
  step2Result: null,
  step3Result: null,
  error: null,
  failedStep: null,
  currentStep: 0,
};

// ── Hook ────────────────────────────────────────────────────────────────────

/**
 * 4-step engineering spec drafts pipeline.
 *
 * Usage:
 * ```ts
 * const pipeline = useEngineeringSpecDraftsPipeline(projectId, conceptPack);
 * // Trigger:
 * const result = await pipeline.run({ mission, contradictions, existing_subsystems });
 * // Progressive rendering:
 * if (pipeline.step1aResult) renderSubsystemTree(pipeline.step1aResult.subsystems);
 * if (pipeline.step1bResult) renderPackageMap(pipeline.step1bResult.package_map);
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

      // Reset and enter step 1a
      setPipelineState({
        ...INITIAL_STATE,
        status: "step1a",
        currentStep: 1,
      });

      try {
        // ── Step 1a: LLM Structure Expansion ──────────────────────────────
        const s1a = await engSpecStep1aExpand({
          project_id: projectId,
          mission: vars.mission,
          contradictions: vars.contradictions,
          existing_subsystems: vars.existing_subsystems,
          concept_pack: conceptPack,
        });
        setPipelineState((s) => ({
          ...s,
          step1aResult: s1a,
          status: "step1b",
          currentStep: 2,
        }));

        // ── Step 1b: Spatial Enrichment + Package Map ─────────────────────
        const s1b = await engSpecStep1bEnrich({
          project_id: projectId,
          subsystems: s1a.subsystems,
        });
        const assembledStep1 = {
          subsystems: s1b.subsystems,
          package_map: s1b.package_map,
        };
        setPipelineState((s) => ({
          ...s,
          step1bResult: s1b,
          step1Result: assembledStep1,
          status: "step2",
          currentStep: 3,
        }));

        // ── Step 2: AI Spec Generation ────────────────────────────────────
        const s2 = await engSpecStep2Generate({
          project_id: projectId,
          mission: vars.mission,
          subsystems: s1b.subsystems,
        });
        setPipelineState((s) => ({
          ...s,
          step2Result: s2,
          status: "step3",
          currentStep: 4,
        }));

        // ── Step 3: Source Strengthening ───────────────────────────────────
        const s3 = await engSpecStep3Strengthen({
          project_id: projectId,
          mission: vars.mission,
          drafts: s2.drafts,
          subsystems: s1b.subsystems,
        });
        setPipelineState((s) => ({
          ...s,
          step3Result: s3,
          status: "done",
        }));

        // ── Assemble final response ───────────────────────────────────────
        const final: EngineeringSpecDraftResponse = {
          drafts: s3.drafts,
          subsystem_tree: s1b.subsystems,
          package_map: s1b.package_map,
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
          failedStep: s.status as PipelinePhase,
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
    pipelineState.status === "step1a" ||
    pipelineState.status === "step1b" ||
    pipelineState.status === "step2" ||
    pipelineState.status === "step3";

  return {
    ...pipelineState,
    run,
    reset,
    isRunning,
  };
}
