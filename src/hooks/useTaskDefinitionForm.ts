import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  briefExtract, type BriefExtractResponse,
  briefRewrite,
  constraintSuggest, type SuggestedConstraint,
  constraintFeasibilityCheck, type FeasibilityConflictResult,
  kpiSuggest, type SuggestedKpi,
  briefGenerate5W1H,
  checkBackendHealth,
  getApiErrorMessage,
  type EvidenceReference,
} from "@/lib/api";
import {
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
} from "@/hooks/api/useBrief";
import { supabase } from "@/integrations/supabase/client";
import type { TablesInsert } from "@/integrations/supabase/types";
import type { BriefConstraint, BriefKPI, TaskDefinition5W1H, GateCheckItem } from "@/types/taskDefinition";
import type { UploadedFile } from "@/components/task-definition/FileUploadZone";
import type { ExtractedItem } from "@/components/task-definition/AIExtractionResults";
import type { FeasibilityStatus } from "@/components/task-definition/FeasibilityValidation";
import { toast } from "sonner";

// ── Internal helper types ────────────────────────────────────────────

interface ConstraintCodePattern {
  prefix: string;
  separator: string;
  width: number;
  nextNumber: number;
}

// ── Hook ─────────────────────────────────────────────────────────────

export function useTaskDefinitionForm(projectId: string | undefined) {
  const navigate = useNavigate();

  // ── Supabase queries ──────────────────────────────────────────────
  const briefQuery = useBrief(projectId);
  const constraintsQuery = useConstraints(projectId);
  const kpisQuery = useKpis(projectId);

  // ── Supabase mutations ────────────────────────────────────────────
  const upsertBrief = useUpsertBrief();
  const createConstraint = useCreateConstraint();
  const updateConstraint = useUpdateConstraint();
  const deleteConstraint = useDeleteConstraint();
  const createKpi = useCreateKpi();
  const updateKpi = useUpdateKpi();
  const deleteKpi = useDeleteKpi();

  // Aggregate loading / error states
  const isLoading = briefQuery.isLoading || constraintsQuery.isLoading || kpisQuery.isLoading;
  const loadError = briefQuery.isError || constraintsQuery.isError || kpisQuery.isError;

  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [mission, setMission] = useState("");
  const [constraints, setConstraints] = useState<BriefConstraint[]>([
    { id: "c-new", constraint_code: "C-01", description: "", source: "" },
  ]);
  const [kpis, setKpis] = useState<BriefKPI[]>([
    { id: "k-new", kpi_name: "", target_value: "", unit: "", measurement_method: "" },
  ]);
  const [softObjectives, setSoftObjectives] = useState<string[]>([]);
  const [nonGoals, setNonGoals] = useState<string[]>([]);
  const [taskDef5W1H, setTaskDef5W1H] = useState<TaskDefinition5W1H | null>(null);

  // Track whether we've seeded form state from server data
  const [seeded, setSeeded] = useState(false);

  // Upload & extraction state
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedItems, setExtractedItems] = useState<ExtractedItem[]>([]);
  const [showExtraction, setShowExtraction] = useState(false);

  // Feasibility state
  const [feasibilityStatus, setFeasibilityStatus] = useState<FeasibilityStatus>("idle");
  const [feasibilityConflicts, setFeasibilityConflicts] = useState<FeasibilityConflictResult[]>([]);

  // AI suggestion state
  const [showMissionSuggestion, setShowMissionSuggestion] = useState(false);
  const [missionSuggestion, setMissionSuggestion] = useState<string | null>(null);
  const [missionChangesSummary, setMissionChangesSummary] = useState("");
  const [isMissionRewriting, setIsMissionRewriting] = useState(false);
  const [showConstraintSuggestions, setShowConstraintSuggestions] = useState(false);
  const [constraintSuggestionList, setConstraintSuggestionList] = useState<SuggestedConstraint[]>([]);
  const [isConstraintSuggesting, setIsConstraintSuggesting] = useState(false);
  const [activeConstraintActionIndex, setActiveConstraintActionIndex] = useState<number | null>(null);
  const [showKpiSuggestions, setShowKpiSuggestions] = useState(false);
  const [kpiSuggestionList, setKpiSuggestionList] = useState<SuggestedKpi[]>([]);
  const [isKpiSuggesting, setIsKpiSuggesting] = useState(false);
  const [activeKpiActionIndex, setActiveKpiActionIndex] = useState<number | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "down">("checking");
  const [backendStatusMessage, setBackendStatusMessage] = useState("檢查後端連線中...");

  // Evidence references from AI responses
  const [missionEvidenceRefs, setMissionEvidenceRefs] = useState<EvidenceReference[]>([]);
  const [constraintEvidenceRefs, setConstraintEvidenceRefs] = useState<EvidenceReference[]>([]);
  const [kpiEvidenceRefs, setKpiEvidenceRefs] = useState<EvidenceReference[]>([]);

  // 5W1H generation state
  const [is5W1HGenerating, setIs5W1HGenerating] = useState(false);

  // ── Seed form state from server data once loaded ──────────────────
  useEffect(() => {
    if (seeded || isLoading) return;

    if (briefQuery.data) {
      setMission(briefQuery.data.mission);
      setTaskDef5W1H(briefQuery.data.taskDefinition5w1h);

      // Restore persisted feasibility data from the 5W1H JSON blob
      const raw = briefQuery.data.taskDefinition5w1h as Record<string, unknown> | null;
      if (raw?.feasibility_status && typeof raw.feasibility_status === 'string') {
        setFeasibilityStatus(raw.feasibility_status as FeasibilityStatus);
      }
      if (raw?.feasibility_conflicts && Array.isArray(raw.feasibility_conflicts)) {
        setFeasibilityConflicts(raw.feasibility_conflicts as FeasibilityConflictResult[]);
      }
    }

    if (constraintsQuery.data && constraintsQuery.data.length > 0) {
      setConstraints(
        constraintsQuery.data.map((c) => ({
          id: c.id,
          constraint_code: c.constraintCode,
          description: c.description,
          source: c.source,
        }))
      );
    }

    if (kpisQuery.data && kpisQuery.data.length > 0) {
      setKpis(
        kpisQuery.data.map((k) => ({
          id: k.id,
          kpi_name: k.kpiName,
          target_value: k.targetValue,
          unit: k.unit,
          measurement_method: k.measurementMethod,
        }))
      );
    }

    setSeeded(true);
  }, [isLoading, seeded, briefQuery.data, constraintsQuery.data, kpisQuery.data]);

  // ── Backend health check ──────────────────────────────────────────
  const runBackendHealthCheck = async (showFailureToast = false) => {
    setBackendStatus("checking");
    setBackendStatusMessage("檢查後端連線中...");
    const result = await checkBackendHealth();
    if (result.ok) {
      setBackendStatus("ok");
      setBackendStatusMessage(result.message);
      return;
    }
    setBackendStatus("down");
    setBackendStatusMessage(result.message);
    if (showFailureToast) {
      toast.error(result.message);
    }
  };

  // Check backend reachability on page load
  useEffect(() => {
    void runBackendHealthCheck();
  }, []);

  // ── Constraint code helpers ───────────────────────────────────────

  const inferConstraintCodePattern = (items: BriefConstraint[]): ConstraintCodePattern => {
    const parsed = items
      .map((c) => c.constraint_code.trim())
      .filter(Boolean)
      .map((code) => {
        const m = code.match(/^([A-Za-z]+)([-_]?)(\d+)$/);
        if (!m) return null;
        return {
          prefix: m[1],
          separator: m[2],
          number: Number(m[3]),
          width: m[3].length,
        };
      })
      .filter((v): v is { prefix: string; separator: string; number: number; width: number } => v !== null);

    if (parsed.length === 0) {
      return { prefix: "C", separator: "-", width: 2, nextNumber: 1 };
    }

    const base = parsed[0];
    const maxNumber = Math.max(
      ...parsed
        .filter((p) => p.prefix === base.prefix && p.separator === base.separator)
        .map((p) => p.number),
    );

    return {
      prefix: base.prefix,
      separator: base.separator,
      width: base.width,
      nextNumber: maxNumber + 1,
    };
  };

  const buildNextConstraintCodes = (count: number): string[] => {
    const pattern = inferConstraintCodePattern(constraints.filter((c) => c.description.trim()));
    return Array.from({ length: count }, (_, idx) => {
      const n = pattern.nextNumber + idx;
      return `${pattern.prefix}${pattern.separator}${String(n).padStart(pattern.width, "0")}`;
    });
  };

  // ── AI handlers ───────────────────────────────────────────────────

  const handleMissionRewrite = async () => {
    if (!projectId || mission.trim().length < 10) {
      toast.error("Mission 需至少 10 個字元才能改寫");
      return;
    }
    setShowMissionSuggestion(true);
    setMissionSuggestion(null);
    setIsMissionRewriting(true);
    try {
      const res = await briefRewrite({
        project_id: projectId,
        mission,
        constraints: constraints.filter(c => c.description.trim()).map(c => c.description),
        kpis: kpis.filter(k => k.kpi_name.trim()).map(k => `${k.kpi_name}: ${k.target_value} ${k.unit}`),
      });
      setMissionSuggestion(res.rewritten_mission);
      setMissionChangesSummary(res.changes_summary);
      setMissionEvidenceRefs(res.evidence_references ?? []);
    } catch (err) {
      console.error("Mission rewrite failed:", err);
      toast.error(getApiErrorMessage(err, "AI 改寫"));
      setShowMissionSuggestion(false);
    } finally {
      setIsMissionRewriting(false);
    }
  };

  const handleConstraintSuggest = async () => {
    if (!projectId) return;
    if (mission.trim().length < 10) {
      toast.error("請先填寫 Mission（至少 10 字）再使用 AI 建議約束");
      return;
    }
    if (isConstraintSuggesting) return;
    setShowConstraintSuggestions(true);
    setConstraintSuggestionList([]);
    setIsConstraintSuggesting(true);
    try {
      const res = await constraintSuggest({
        project_id: projectId,
        mission,
        existing_constraints: constraints.filter(c => c.description.trim()).map(c => c.description),
      });
      setConstraintSuggestionList(res.suggestions);
      setConstraintEvidenceRefs(res.evidence_references ?? []);
      if (res.suggestions.length === 0) {
        toast.info("AI 未產出約束建議，請補充更具體的 Mission 或上下文");
      } else {
        toast.success(`AI 已產生 ${res.suggestions.length} 項約束建議`);
      }
    } catch (err) {
      console.error("Constraint suggestion failed:", err);
      toast.error(getApiErrorMessage(err, "AI 約束建議"));
      setShowConstraintSuggestions(false);
    } finally {
      setIsConstraintSuggesting(false);
    }
  };

  const handleKpiSuggest = async () => {
    if (!projectId) return;
    if (mission.trim().length < 10) {
      toast.error("請先填寫 Mission（至少 10 字）再使用 AI 建議 KPI");
      return;
    }
    if (isKpiSuggesting) return;
    setShowKpiSuggestions(true);
    setKpiSuggestionList([]);
    setIsKpiSuggesting(true);
    try {
      const res = await kpiSuggest({
        project_id: projectId,
        mission,
        constraints: constraints.filter(c => c.description.trim()).map(c => c.description),
        existing_kpis: kpis.filter(k => k.kpi_name.trim()).map(k => `${k.kpi_name}: ${k.target_value} ${k.unit}`),
      });
      setKpiSuggestionList(res.suggestions);
      setKpiEvidenceRefs(res.evidence_references ?? []);
      if (res.suggestions.length === 0) {
        toast.info("AI 未產出 KPI 建議，請補充更具體的 Mission 或約束");
      } else {
        toast.success(`AI 已產生 ${res.suggestions.length} 項 KPI 建議`);
      }
    } catch (err) {
      console.error("KPI suggestion failed:", err);
      toast.error(getApiErrorMessage(err, "AI KPI 建議"));
      setShowKpiSuggestions(false);
    } finally {
      setIsKpiSuggesting(false);
    }
  };

  // ── 5W1H generation ───────────────────────────────────────────────

  const generate5W1H = async () => {
    if (!projectId || mission.trim().length < 10) return;
    setIs5W1HGenerating(true);
    try {
      const res = await briefGenerate5W1H({
        project_id: projectId,
        mission,
        constraints: constraints.filter(c => c.description.trim()).map(c => c.description),
        kpis: kpis.filter(k => k.kpi_name.trim()).map(k => `${k.kpi_name}: ${k.target_value} ${k.unit}`),
      });
      setTaskDef5W1H(res);
    } catch (err) {
      console.error("5W1H generation failed:", err);
      toast.error(getApiErrorMessage(err, "AI 5W1H 產生"));
    } finally {
      setIs5W1HGenerating(false);
    }
  };

  // Auto-trigger 5W1H when mission is ready and no data exists
  useEffect(() => {
    if (mission.trim().length >= 10 && !taskDef5W1H && !is5W1HGenerating && projectId) {
      const timer = setTimeout(() => generate5W1H(), 1000);
      return () => clearTimeout(timer);
    }
  }, [mission, taskDef5W1H, projectId]);

  // ── Auto-save: debounce upsert brief mission to Supabase ─────────
  useEffect(() => {
    if (isLoading || !seeded || !projectId) return;
    const timer = setTimeout(() => {
      setSaveStatus("saving");
      upsertBrief.mutate(
        {
          project_id: projectId,
          mission,
          task_definition_5w1h: taskDef5W1H as unknown as TablesInsert<"briefs">["task_definition_5w1h"],
        },
        {
          onSuccess: () => {
            setSaveStatus("saved");
            setTimeout(() => setSaveStatus("idle"), 2000);
          },
          onError: () => {
            setSaveStatus("idle");
          },
        }
      );
    }, 3000);
    return () => clearTimeout(timer);
  }, [mission, taskDef5W1H]);

  // ── Auto-save: debounce constraints to Supabase ─────────────────
  useEffect(() => {
    if (isLoading || !seeded || !projectId) return;
    const timer = setTimeout(() => {
      for (const c of constraints) {
        if (c.id.startsWith("c-") || c.description.trim().length < 2) continue;
        const db = constraintsQuery.data?.find((d) => d.id === c.id);
        if (db && (db.description !== c.description || db.source !== c.source)) {
          updateConstraint.mutate({
            id: c.id,
            constraint_code: c.constraint_code,
            description: c.description,
            source: c.source || undefined,
          });
        }
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [constraints, seeded, isLoading, projectId]);

  // ── Auto-save: debounce KPIs to Supabase ───────────────────────
  useEffect(() => {
    if (isLoading || !seeded || !projectId) return;
    const timer = setTimeout(() => {
      for (const k of kpis) {
        if (k.id.startsWith("k-") || !k.kpi_name.trim()) continue;
        const db = kpisQuery.data?.find((d) => d.id === k.id);
        if (db && (db.kpiName !== k.kpi_name || db.targetValue !== k.target_value || db.unit !== k.unit || db.measurementMethod !== k.measurement_method)) {
          updateKpi.mutate({
            id: k.id,
            kpi_name: k.kpi_name,
            target_value: k.target_value,
            unit: k.unit,
            measurement_method: k.measurement_method,
          });
        }
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [kpis, seeded, isLoading, projectId]);

  // ── Gate D1 check ────────────────────────────────────────────────
  const missionReady = mission.trim().length >= 10;
  const hasConstraint = constraints.some((c) => c.description.trim().length >= 2);
  const hasKpi = kpis.some(
    (k) => k.kpi_name.trim() && k.target_value.trim() && k.unit.trim() && k.measurement_method.trim()
  );

  // ── Detect content change → mark feasibility as stale ─────────────
  const feasibilitySnapshotRef = useRef<string>("");
  const [isFeasibilityStale, setIsFeasibilityStale] = useState(false);

  const gateItems: GateCheckItem[] = useMemo(() => [
    { label: "Mission 已填寫 (≥ 10 字元)", passed: missionReady },
    { label: "至少 1 項硬約束", passed: hasConstraint },
    { label: "至少 1 項 KPI", passed: hasKpi },
    { label: "約束可行性驗證通過", passed: (feasibilityStatus === "pass" || feasibilityStatus === "warning") && !isFeasibilityStale },
  ], [missionReady, hasConstraint, hasKpi, feasibilityStatus, isFeasibilityStale]);

  useEffect(() => {
    if (feasibilityStatus === "idle" || feasibilityStatus === "checking") return;
    const currentSnapshot = `${mission}||${constraints.map((c) => c.description).join(",")}||${kpis.map((k) => `${k.kpi_name}:${k.target_value}`).join(",")}`;
    if (feasibilitySnapshotRef.current && feasibilitySnapshotRef.current !== currentSnapshot) {
      setIsFeasibilityStale(true);
    }
  }, [mission, constraints, kpis, feasibilityStatus]);

  // ── Extraction handlers ───────────────────────────────────────────

  const handleExtract = async () => {
    if (!projectId) return;
    setIsExtracting(true);
    try {
      const result: BriefExtractResponse = await briefExtract({
        project_id: projectId,
        raw_text: mission,
        file_urls: [],
      });
      const items: ExtractedItem[] = [
        ...result.constraints.map((c, i) => ({
          id: `ext-c-${i}`,
          type: "constraint" as const,
          content: c.description,
          source: c.source,
          accepted: false,
          editing: false,
        })),
        ...result.kpis.map((k, i) => ({
          id: `ext-k-${i}`,
          type: "data" as const,
          content: `${k.name}: ${k.target_value} ${k.unit}`,
          source: k.measurement_method || "AI extracted",
          accepted: false,
          editing: false,
        })),
        ...result.assumptions.map((a, i) => ({
          id: `ext-a-${i}`,
          type: "assumption" as const,
          content: a,
          source: "AI extracted",
          accepted: false,
          editing: false,
        })),
      ];
      setExtractedItems(items);
      setShowExtraction(true);
      toast.success(`AI 提取完成，共提取 ${items.length} 條項目`);
      if (result.feasibility_warnings.length > 0) {
        toast.warning(`可行性警告：${result.feasibility_warnings[0]}`);
      }
    } catch (err) {
      console.error("Brief extraction failed:", err);
      toast.error(getApiErrorMessage(err, "AI 提取"));
    } finally {
      setIsExtracting(false);
    }
  };

  const handleAcceptAllExtracted = () => {
    const accepted = extractedItems.map((i) => ({ ...i, accepted: true }));
    setExtractedItems(accepted);

    const newConstraintItems = accepted.filter((i) => i.type === "constraint");

    if (newConstraintItems.length > 0 && projectId) {
      const newCodes = buildNextConstraintCodes(newConstraintItems.length);
      newConstraintItems.forEach((item, idx) => {
        const code = newCodes[idx];
        createConstraint.mutate({
          project_id: projectId,
          constraint_code: code,
          description: item.content,
          source: item.source,
        });
      });

      const newConstraints = newConstraintItems.map((i, idx) => ({
        id: `c-ext-${idx}`,
        constraint_code: newCodes[idx],
        description: i.content,
        source: i.source,
      }));
      setConstraints((prev) => [...prev.filter((c) => c.description.trim()), ...newConstraints]);
    }
    toast.success("已接受所有提取結果並填入表單");
  };

  // ── Feasibility handlers ──────────────────────────────────────────

  const persistFeasibility = async (status: FeasibilityStatus, conflicts: FeasibilityConflictResult[]) => {
    if (!projectId) return;
    const blob = { ...(taskDef5W1H ?? {}), feasibility_status: status, feasibility_conflicts: conflicts };
    await supabase
      .from('briefs')
      .update({ task_definition_5w1h: blob as unknown as TablesInsert<"briefs">["task_definition_5w1h"], updated_at: new Date().toISOString() })
      .eq('project_id', projectId);
  };

  const handleFeasibilityCheck = async () => {
    if (!projectId) return;
    const descriptions = constraints.map((c) => c.description).filter((d) => d.trim().length >= 2);
    // Take snapshot of current content for staleness detection
    const snapshot = `${mission}||${constraints.map((c) => c.description).join(",")}||${kpis.map((k) => `${k.kpi_name}:${k.target_value}`).join(",")}`;
    if (descriptions.length < 2) {
      setFeasibilityStatus("pass");
      setFeasibilityConflicts([]);
      setIsFeasibilityStale(false);
      feasibilitySnapshotRef.current = snapshot;
      await persistFeasibility("pass", []);
      return;
    }
    setFeasibilityStatus("checking");
    try {
      const result = await constraintFeasibilityCheck({
        project_id: projectId,
        mission,
        constraints: descriptions,
      });
      setFeasibilityConflicts(result.conflicts);
      setFeasibilityStatus(result.status as FeasibilityStatus);
      setIsFeasibilityStale(false);
      feasibilitySnapshotRef.current = snapshot;
      await persistFeasibility(result.status as FeasibilityStatus, result.conflicts);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "約束可行性驗證"));
      setFeasibilityStatus("idle");
    }
  };

  const handleFeasibilityOverride = async (reason: string) => {
    setFeasibilityStatus("warning");
    const conflictsWithOverride = feasibilityConflicts.map((c) => ({ ...c, overrideReason: reason }));
    await persistFeasibility("warning", conflictsWithOverride);
    toast.info("已記錄覆寫原因，可繼續進行");
  };

  // ── Remove constraint / KPI (instant DB delete + local state) ────
  const removeConstraint = (id: string) => {
    setConstraints((prev) => prev.filter((c) => c.id !== id));
    if (!id.startsWith("c-") && projectId) {
      deleteConstraint.mutate({ id });
    }
  };

  const removeKpi = (id: string) => {
    setKpis((prev) => prev.filter((k) => k.id !== id));
    if (!id.startsWith("k-") && projectId) {
      deleteKpi.mutate({ id });
    }
  };

  // ── Adopt AI suggestions ──────────────────────────────────────────

  const handleAdoptMissionSuggestion = (editedContent: string) => {
    setMission(editedContent);
    setShowMissionSuggestion(false);
    setMissionSuggestion(null);
    toast.success("已採用 AI 改寫的 Mission");
  };

  const handleAdoptConstraintSuggestion = (desc: string, source: string) => {
    const code = buildNextConstraintCodes(1)[0];
    const tempId = `c-ai-${Date.now()}`;
    setConstraints([...constraints, { id: tempId, constraint_code: code, description: desc, source }]);
    if (projectId) {
      createConstraint.mutate({ project_id: projectId, constraint_code: code, description: desc, source });
    }
    toast.success("已新增 AI 建議約束");
  };

  const handleAdoptKpiSuggestion = (kpi: SuggestedKpi) => {
    const tempId = `k-ai-${Date.now()}`;
    const newKpi = {
      id: tempId,
      kpi_name: kpi.kpi_name,
      target_value: kpi.target_value,
      unit: kpi.unit,
      measurement_method: kpi.measurement_method,
    };
    setKpis([...kpis, newKpi]);
    if (projectId) {
      createKpi.mutate({
        project_id: projectId,
        kpi_name: kpi.kpi_name,
        target_value: kpi.target_value,
        unit: kpi.unit,
        measurement_method: kpi.measurement_method,
      });
    }
    toast.success("已新增 AI 建議 KPI");
  };

  // ── Submit ────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    if (!missionReady || !hasConstraint || !hasKpi) {
      toast.error("請完成所有必填項目");
      return;
    }

    if (feasibilityStatus !== "pass" && feasibilityStatus !== "warning") {
      toast.error("請先完成約束可行性驗證");
      return;
    }

    if (!projectId) return;
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      // 1) Upsert brief
      const briefBlob = {
        ...(taskDef5W1H ?? {}),
        feasibility_status: feasibilityStatus,
        feasibility_conflicts: feasibilityConflicts,
      };
      await upsertBrief.mutateAsync({
        project_id: projectId,
        mission,
        task_definition_5w1h: briefBlob as unknown as TablesInsert<"briefs">["task_definition_5w1h"],
      });

      // 2) Sync constraints
      const validConstraints = constraints.filter((c) => c.description.trim().length >= 2);
      const existingDbConstraints = constraintsQuery.data ?? [];

      const validConstraintIds = new Set(validConstraints.map((c) => c.id));
      const constraintsToDelete = existingDbConstraints.filter((db) => !validConstraintIds.has(db.id));

      for (const d of constraintsToDelete) {
        await deleteConstraint.mutateAsync({ id: d.id });
      }

      for (const c of validConstraints) {
        if (c.id.startsWith("c-")) {
          await createConstraint.mutateAsync({
            project_id: projectId,
            constraint_code: c.constraint_code,
            description: c.description,
            source: c.source || undefined,
          });
        } else {
          await updateConstraint.mutateAsync({
            id: c.id,
            constraint_code: c.constraint_code,
            description: c.description,
            source: c.source || undefined,
          });
        }
      }

      // 3) Sync KPIs
      const validKpis = kpis.filter(
        (k) => k.kpi_name.trim() && k.target_value.trim() && k.unit.trim() && k.measurement_method.trim()
      );
      const existingDbKpis = kpisQuery.data ?? [];

      const validKpiIds = new Set(validKpis.map((k) => k.id));
      const kpisToDelete = existingDbKpis.filter((db) => !validKpiIds.has(db.id));

      for (const d of kpisToDelete) {
        await deleteKpi.mutateAsync({ id: d.id });
      }

      for (const k of validKpis) {
        if (k.id.startsWith("k-")) {
          await createKpi.mutateAsync({
            project_id: projectId,
            kpi_name: k.kpi_name,
            target_value: k.target_value,
            unit: k.unit,
            measurement_method: k.measurement_method,
          });
        } else {
          await updateKpi.mutateAsync({
            id: k.id,
            kpi_name: k.kpi_name,
            target_value: k.target_value,
            unit: k.unit,
            measurement_method: k.measurement_method,
          });
        }
      }

      toast.success("任務定義已保存");
      navigate(`/projects/${projectId}/explore`);
    } catch (err) {
      console.error("handleSubmit failed:", err);
      toast.error("保存失敗，請重試");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Constraint suggestion card handlers (for JSX callbacks) ───────

  const handleAdoptConstraintAtIndex = (index: number, suggestion: SuggestedConstraint) => {
    if (activeConstraintActionIndex !== null) return;
    setActiveConstraintActionIndex(index);
    try {
      handleAdoptConstraintSuggestion(suggestion.description, suggestion.source);
      setConstraintSuggestionList((prev) => {
        const next = prev.filter((_, idx) => idx !== index);
        if (next.length === 0) {
          setShowConstraintSuggestions(false);
        }
        return next;
      });
    } finally {
      setActiveConstraintActionIndex(null);
    }
  };

  const handleSkipConstraintAtIndex = (index: number) => {
    if (activeConstraintActionIndex !== null) return;
    setConstraintSuggestionList(prev => prev.filter((_, idx) => idx !== index));
  };

  const handleCloseConstraintSuggestions = () => {
    setShowConstraintSuggestions(false);
    setConstraintSuggestionList([]);
  };

  // ── KPI suggestion card handlers (for JSX callbacks) ──────────────

  const handleAdoptKpiAtIndex = (index: number, suggestion: SuggestedKpi) => {
    if (activeKpiActionIndex !== null) return;
    setActiveKpiActionIndex(index);
    try {
      handleAdoptKpiSuggestion(suggestion);
      setKpiSuggestionList((prev) => {
        const next = prev.filter((_, idx) => idx !== index);
        if (next.length === 0) {
          setShowKpiSuggestions(false);
        }
        return next;
      });
    } finally {
      setActiveKpiActionIndex(null);
    }
  };

  const handleSkipKpiAtIndex = (index: number) => {
    if (activeKpiActionIndex !== null) return;
    setKpiSuggestionList(prev => prev.filter((_, idx) => idx !== index));
  };

  const handleCloseKpiSuggestions = () => {
    setShowKpiSuggestions(false);
    setKpiSuggestionList([]);
  };

  // ── Mission suggestion dismiss ────────────────────────────────────

  const handleDismissMissionSuggestion = () => {
    setShowMissionSuggestion(false);
    setMissionSuggestion(null);
  };

  // ── Dismiss constraint suggesting loading card ────────────────────

  const handleDismissConstraintSuggesting = () => {
    setShowConstraintSuggestions(false);
    setIsConstraintSuggesting(false);
  };

  const handleDismissKpiSuggesting = () => {
    setShowKpiSuggestions(false);
    setIsKpiSuggesting(false);
  };

  // ── 5W1H regenerate ───────────────────────────────────────────────

  const handleRegenerate5W1H = () => {
    setTaskDef5W1H(null);
    generate5W1H();
  };

  return {
    // Loading / error
    isLoading,
    loadError,

    // Save / submit status
    saveStatus,
    isSubmitting,

    // Form state
    mission,
    setMission,
    constraints,
    setConstraints,
    removeConstraint,
    kpis,
    setKpis,
    removeKpi,
    softObjectives,
    setSoftObjectives,
    nonGoals,
    setNonGoals,
    taskDef5W1H,

    // Upload & extraction
    uploadedFiles,
    setUploadedFiles,
    isExtracting,
    extractedItems,
    setExtractedItems,
    showExtraction,
    handleExtract,
    handleAcceptAllExtracted,

    // Feasibility
    feasibilityStatus,
    feasibilityConflicts,
    isFeasibilityStale,
    handleFeasibilityCheck,
    handleFeasibilityOverride,

    // Mission AI
    showMissionSuggestion,
    missionSuggestion,
    missionChangesSummary,
    isMissionRewriting,
    missionEvidenceRefs,
    handleMissionRewrite,
    handleAdoptMissionSuggestion,
    handleDismissMissionSuggestion,

    // Constraint AI
    showConstraintSuggestions,
    constraintSuggestionList,
    isConstraintSuggesting,
    activeConstraintActionIndex,
    constraintEvidenceRefs,
    handleConstraintSuggest,
    handleAdoptConstraintAtIndex,
    handleSkipConstraintAtIndex,
    handleCloseConstraintSuggestions,
    handleDismissConstraintSuggesting,

    // KPI AI
    showKpiSuggestions,
    kpiSuggestionList,
    isKpiSuggesting,
    activeKpiActionIndex,
    kpiEvidenceRefs,
    handleKpiSuggest,
    handleAdoptKpiAtIndex,
    handleSkipKpiAtIndex,
    handleCloseKpiSuggestions,
    handleDismissKpiSuggesting,

    // 5W1H
    handleRegenerate5W1H,

    // Backend status
    backendStatus,
    backendStatusMessage,
    runBackendHealthCheck,

    // Gate
    missionReady,
    gateItems,

    // Submit
    handleSubmit,

    // Navigation
    navigate,
  };
}
