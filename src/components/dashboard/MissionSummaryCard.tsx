import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Target, Lock, Star } from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  CONSTRAINT_LABEL_CLASSIFIER_VERSION,
  classifyHardConstraints,
  normalizeConstraintKey,
  splitConstraintItems,
} from "@/lib/constraintLabeling";
import {
  buildConstraintLabelHistoryPayload,
  CONSTRAINT_LABEL_ASSET_TYPE,
  CONSTRAINT_LABEL_HISTORY_ASSET_TYPE,
  HARD_CONSTRAINT_LABEL_TITLE,
  buildConstraintLabelPayload,
  type ConstraintLabelActionType,
  useCreateConstraintLabelHistory,
  useConstraintLabelMap,
  useCreateConstraintLabelMap,
  useUpdateConstraintLabelMap,
} from "@/hooks/api/useKnowledge";
import { useAuth } from "@/contexts/AuthContext";

interface MissionSummaryCardProps {
  projectId?: string;
  projectOwnerId?: string;
  mission?: string;
  hardConstraints?: string | string[];
  softObjectives?: string | string[];
}

export function MissionSummaryCard({
  projectId,
  projectOwnerId,
  mission,
  hardConstraints,
  softObjectives,
}: MissionSummaryCardProps) {
  const hardConstraintItems = splitConstraintItems(hardConstraints);
  const softObjectiveItems = splitConstraintItems(softObjectives);
  const { user } = useAuth();
  const [constraintLabelMap, setConstraintLabelMap] = useState<Record<string, string>>({});
  const [initialized, setInitialized] = useState(false);

  const {
    entryId,
    labelMap: dbLabelMap,
    isLoading: isLabelMapLoading,
  } = useConstraintLabelMap(projectId);
  const createLabelMap = useCreateConstraintLabelMap(projectId);
  const updateLabelMap = useUpdateConstraintLabelMap(projectId);
  const createHistory = useCreateConstraintLabelHistory(projectId);
  const isProjectOwner = !!user && !!projectOwnerId && user.id === projectOwnerId;
  const isAdmin = user?.app_metadata?.role === "admin";
  const canManageLabels = Boolean(isProjectOwner || isAdmin);

  useEffect(() => {
    if (!projectId) {
      setInitialized(true);
      return;
    }
    if (isLabelMapLoading) return;

    if (!isSameLabelMap(constraintLabelMap, dbLabelMap)) {
      setConstraintLabelMap(dbLabelMap);
    }
    setInitialized(true);
  }, [projectId, isLabelMapLoading, dbLabelMap, constraintLabelMap]);

  const hardConstraintClassifyResult = useMemo(
    () => classifyHardConstraints(hardConstraintItems, constraintLabelMap),
    [hardConstraintItems, constraintLabelMap],
  );

  const isSameLabelMap = (a: Record<string, string>, b: Record<string, string>) => {
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every((key) => a[key] === b[key]);
  };

  const persistLabelMap = (
    nextMap: Record<string, string>,
    options?: {
      action?: ConstraintLabelActionType;
      note?: string;
      actor?: {
        id: string;
        email: string;
        displayName: string;
      };
      previousMap?: Record<string, string>;
      classifierVersion?: string;
    },
  ) => {
    if (!projectId) return;
    const classifierVersion = options?.classifierVersion ?? CONSTRAINT_LABEL_CLASSIFIER_VERSION;
    const serialized = JSON.stringify(buildConstraintLabelPayload(nextMap, classifierVersion));

    if (entryId) {
      if (updateLabelMap.isPending) return;
      updateLabelMap.mutate({ id: entryId, content: serialized, reviewed: true });
    } else {
      if (createLabelMap.isPending) return;
      createLabelMap.mutate({
        project_id: projectId,
        asset_type: CONSTRAINT_LABEL_ASSET_TYPE,
        title: HARD_CONSTRAINT_LABEL_TITLE,
        content: serialized,
        reviewed: true,
      });
    }

    if (options?.action && !createHistory.isPending) {
      const historyPayload = buildConstraintLabelHistoryPayload({
        action: options.action,
        source: "dashboard",
        actor: options.actor ?? {
          id: user?.id ?? "unknown",
          email: user?.email ?? "unknown",
          displayName: (user?.user_metadata?.display_name as string) ?? (user?.email ?? "unknown"),
        },
        before: options.previousMap ?? constraintLabelMap,
        after: nextMap,
        classifierVersion,
        note: options.note,
      });
      createHistory.mutate({
        project_id: projectId,
        asset_type: CONSTRAINT_LABEL_HISTORY_ASSET_TYPE,
        title: HARD_CONSTRAINT_LABEL_TITLE,
        content: JSON.stringify(historyPayload),
        reviewed: true,
      });
    }
  };

  useEffect(() => {
    if (!initialized || !canManageLabels) return;

    const { hasUpdates, nextLabelMap } = hardConstraintClassifyResult;
    if (!hasUpdates) return;

    // Avoid same value setState → redundant re-render
    if (isSameLabelMap(constraintLabelMap, nextLabelMap)) return;

    setConstraintLabelMap(nextLabelMap);
    persistLabelMap(nextLabelMap, {
      action: "auto_classify_sync",
      actor: {
        id: user?.id ?? "unknown",
        email: user?.email ?? "unknown",
        displayName: (user?.user_metadata?.display_name as string) ?? (user?.email ?? "unknown"),
      },
      previousMap: constraintLabelMap,
    });
  }, [
    initialized,
    canManageLabels,
    hardConstraintClassifyResult.hasUpdates,
    hardConstraintClassifyResult.nextLabelMap,
    constraintLabelMap,
    user?.id,
    user?.email,
    user?.user_metadata?.display_name,
  ]);

  const hardConstraintGroups = hardConstraintClassifyResult.groups;
  if (!mission && hardConstraintItems.length === 0 && softObjectiveItems.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">任務摘要</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {mission && (
          <div className="flex gap-2">
            <Target className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-0.5">Mission</div>
              <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{mission}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
        {hardConstraintItems.length > 0 && (
          <div className="flex gap-2">
            <Lock className="h-4 w-4 mt-0.5 shrink-0 text-destructive" />
            <div>
              <div className="mb-1 flex items-center gap-2">
                <div className="text-xs font-medium text-muted-foreground">Hard Constraints</div>
                {projectId && (
                  <Button asChild size="sm" variant="ghost" className="h-5 px-1.5 text-[11px]">
                    <Link to={`/projects/${projectId}/constraint-labels`}>管理標籤字典</Link>
                  </Button>
                )}
              </div>
              <div className="space-y-2">
                {hardConstraintGroups.map((group) => (
                  <div key={group.label} className="space-y-1">
                    <p className="text-xs font-medium text-foreground/80">{group.label}</p>
                    <ul className="list-disc pl-5 space-y-1 text-sm leading-relaxed">
                      {group.items.map((item, index) => {
                        const itemKey = normalizeConstraintKey(item);
                        const currentLabel = hardConstraintClassifyResult.itemLabels[itemKey] ?? group.label;
                        return (
                          <li key={`${group.label}-${item}-${index}`}>
                            <div className="flex flex-wrap items-center gap-2">
                              <span>{item}</span>
                              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                {currentLabel}
                              </span>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {softObjectiveItems.length > 0 && (
          <div className="flex gap-2">
            <Star className="h-4 w-4 mt-0.5 shrink-0 text-warning" />
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-0.5">Soft Objectives</div>
              <ul className="list-disc pl-5 space-y-1 text-sm leading-relaxed">
                {softObjectiveItems.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
