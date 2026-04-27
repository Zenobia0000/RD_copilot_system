import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, GitMerge, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useConstraints } from "@/hooks/api/useBrief";
import { useAuth } from "@/contexts/AuthContext";
import { useProject } from "@/hooks/api/useProjects";
import {
  buildConstraintLabelHistoryPayload,
  buildConstraintLabelPayload,
  CONSTRAINT_LABEL_ASSET_TYPE,
  CONSTRAINT_LABEL_HISTORY_ASSET_TYPE,
  HARD_CONSTRAINT_LABEL_TITLE,
  type ConstraintLabelActionType,
  useConstraintLabelHistory,
  useCreateConstraintLabelHistory,
  useConstraintLabelMap,
  useCreateConstraintLabelMap,
  useUpdateConstraintLabelMap,
} from "@/hooks/api/useKnowledge";
import {
  classifyHardConstraints,
  CONSTRAINT_LABEL_CLASSIFIER_VERSION,
  getConstraintLabelSuggestions,
  splitConstraintItems,
} from "@/lib/constraintLabeling";

export default function ConstraintLabelDictionary() {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: project } = useProject(projectId);

  const { data: constraints, isLoading: constraintsLoading } = useConstraints(projectId);
  const {
    entryId,
    labelMap: dbLabelMap,
    classifierVersion,
    schemaVersion,
    isLegacyPayload,
    isLoading: labelMapLoading,
  } = useConstraintLabelMap(projectId);
  const { items: historyItems } = useConstraintLabelHistory(projectId, 30);
  const createLabelMap = useCreateConstraintLabelMap(projectId);
  const updateLabelMap = useUpdateConstraintLabelMap(projectId);
  const createHistory = useCreateConstraintLabelHistory(projectId);

  const [localLabelMap, setLocalLabelMap] = useState<Record<string, string>>({});
  const [initialized, setInitialized] = useState(false);
  const [mergeFromLabel, setMergeFromLabel] = useState("");
  const [mergeToLabel, setMergeToLabel] = useState("");
  const [previewHistoryId, setPreviewHistoryId] = useState<string | null>(null);
  const isProjectOwner = !!user && !!project?.createdBy && user.id === project.createdBy;
  const isAdmin = user?.app_metadata?.role === "admin";
  const canManageLabels = Boolean(isProjectOwner || isAdmin);

  useEffect(() => {
    if (!projectId) {
      setInitialized(true);
      return;
    }
    if (labelMapLoading) return;
    setLocalLabelMap(dbLabelMap);
    setInitialized(true);
  }, [projectId, labelMapLoading, dbLabelMap]);

  const hardConstraintItems = useMemo(
    () => splitConstraintItems((constraints ?? []).filter((c) => c.type === "hard").map((c) => c.description)),
    [constraints],
  );

  const classifyResult = useMemo(
    () => classifyHardConstraints(hardConstraintItems, localLabelMap),
    [hardConstraintItems, localLabelMap],
  );

  const labelOptions = useMemo(
    () => getConstraintLabelSuggestions(classifyResult.nextLabelMap),
    [classifyResult.nextLabelMap],
  );

  const persistLabelMap = (
    nextMap: Record<string, string>,
    options?: {
      action?: ConstraintLabelActionType;
      note?: string;
      previousMap?: Record<string, string>;
      classifierVersion?: string;
    },
  ) => {
    if (!projectId) return;
    const targetClassifierVersion = options?.classifierVersion ?? CONSTRAINT_LABEL_CLASSIFIER_VERSION;
    const payload = buildConstraintLabelPayload(nextMap, targetClassifierVersion);
    const content = JSON.stringify(payload);

    if (entryId) {
      if (updateLabelMap.isPending) return;
      updateLabelMap.mutate({ id: entryId, content, reviewed: true });
      return;
    }

    if (createLabelMap.isPending) return;
    createLabelMap.mutate({
      project_id: projectId,
      asset_type: CONSTRAINT_LABEL_ASSET_TYPE,
      title: HARD_CONSTRAINT_LABEL_TITLE,
      content,
      reviewed: true,
    });

    if (options?.action && !createHistory.isPending) {
      const historyPayload = buildConstraintLabelHistoryPayload({
        action: options.action,
        source: "dictionary",
        actor: {
          id: user?.id ?? "unknown",
          email: user?.email ?? "unknown",
          displayName: (user?.user_metadata?.display_name as string) ?? (user?.email ?? "unknown"),
        },
        before: options.previousMap ?? localLabelMap,
        after: nextMap,
        classifierVersion: targetClassifierVersion,
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
    if (!initialized || !classifyResult.hasUpdates || !canManageLabels) return;
    setLocalLabelMap(classifyResult.nextLabelMap);
    persistLabelMap(classifyResult.nextLabelMap, {
      action: "auto_classify_sync",
      previousMap: localLabelMap,
      classifierVersion: classifierVersion || CONSTRAINT_LABEL_CLASSIFIER_VERSION,
    });
  }, [initialized, classifyResult, classifierVersion, canManageLabels, localLabelMap]);

  const handleMergeLabels = () => {
    if (!canManageLabels) {
      toast.error("你沒有權限修改標籤字典");
      return;
    }
    if (!mergeFromLabel || !mergeToLabel) {
      toast.error("請先選擇來源標籤與目標標籤");
      return;
    }
    if (mergeFromLabel === mergeToLabel) {
      toast.error("來源與目標標籤不能相同");
      return;
    }

    const nextMap: Record<string, string> = {};
    for (const [key, value] of Object.entries(localLabelMap)) {
      nextMap[key] = value === mergeFromLabel ? mergeToLabel : value;
    }

    setLocalLabelMap(nextMap);
    persistLabelMap(nextMap, {
      action: "merge_labels",
      previousMap: localLabelMap,
      note: `${mergeFromLabel} -> ${mergeToLabel}`,
    });
    setMergeFromLabel("");
    setMergeToLabel("");
    toast.success(`已將「${mergeFromLabel}」合併至「${mergeToLabel}」`);
  };

  const handleUpgradeVersion = () => {
    if (!canManageLabels) {
      toast.error("你沒有權限升級映射版本");
      return;
    }
    persistLabelMap(localLabelMap, {
      action: "upgrade_classifier_version",
      previousMap: localLabelMap,
      classifierVersion: CONSTRAINT_LABEL_CLASSIFIER_VERSION,
    });
    toast.success("已升級映射版本至目前分類器版本");
  };

  const handleRollback = (targetMap: Record<string, string>, note: string) => {
    if (!canManageLabels) {
      toast.error("你沒有權限回滾");
      return;
    }
    setLocalLabelMap(targetMap);
    persistLabelMap(targetMap, {
      action: "rollback",
      previousMap: localLabelMap,
      note,
    });
    toast.success("已回滾到指定版本");
  };

  const actionLabels: Record<ConstraintLabelActionType, string> = {
    auto_classify_sync: "自動分類同步",
    manual_override: "手動改標籤",
    merge_labels: "合併標籤",
    upgrade_classifier_version: "升級分類器版本",
    rollback: "回滾",
  };

  const previewItem = historyItems.find((item) => item.id === previewHistoryId);
  const previewDiff = useMemo(() => {
    if (!previewItem) return [];
    const before = previewItem.payload.before;
    const after = previewItem.payload.after;
    const keys = Array.from(new Set([...Object.keys(before), ...Object.keys(after)]));
    return keys
      .filter((key) => before[key] !== after[key])
      .map((key) => ({ key, from: before[key] ?? "-", to: after[key] ?? "-" }));
  }, [previewItem]);

  if (constraintsLoading || labelMapLoading) {
    return (
      <div className="page-shell-wide space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="page-shell-wide space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${projectId}`)}>
            <ArrowLeft className="mr-1 h-4 w-4" />
            回 Dashboard
          </Button>
          <h1 className="text-xl font-semibold">標籤字典</h1>
        </div>
        {!canManageLabels && (
          <Badge variant="outline">唯讀模式（僅專案擁有者或 Admin 可編輯）</Badge>
        )}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">映射版本</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2 text-sm">
          <Badge variant="outline">Schema v{schemaVersion}</Badge>
          <Badge variant="outline">Classifier {classifierVersion}</Badge>
          {isLegacyPayload && canManageLabels && (
            <Button size="sm" variant="outline" onClick={handleUpgradeVersion}>
              升級至 {CONSTRAINT_LABEL_CLASSIFIER_VERSION}
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">合併重複標籤</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2">
          <Select value={mergeFromLabel} onValueChange={setMergeFromLabel}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="來源標籤" />
            </SelectTrigger>
            <SelectContent>
              {labelOptions.map((label) => (
                <SelectItem key={`from-${label}`} value={label}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground">→</span>
          <Select value={mergeToLabel} onValueChange={setMergeToLabel}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="目標標籤" />
            </SelectTrigger>
            <SelectContent>
              {labelOptions.map((label) => (
                <SelectItem key={`to-${label}`} value={label}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleMergeLabels} disabled={!canManageLabels}>
            <GitMerge className="mr-1 h-4 w-4" />
            合併
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">目前標籤分佈</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {classifyResult.groups.length === 0 ? (
            <p className="text-sm text-muted-foreground">目前沒有 Hard Constraints。</p>
          ) : (
            classifyResult.groups.map((group) => (
              <div key={group.label} className="rounded border p-3">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{group.label}</p>
                  <Badge variant="secondary">{group.items.length}</Badge>
                </div>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {group.items.slice(0, 6).map((item, index) => (
                    <li key={`${group.label}-${index}`}>{item}</li>
                  ))}
                  {group.items.length > 6 && <li>... 還有 {group.items.length - 6} 項</li>}
                </ul>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">操作歷史（可一鍵回滾）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {historyItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">目前尚無操作歷史。</p>
          ) : (
            historyItems.map((history) => (
              <div key={history.id} className="flex flex-wrap items-center justify-between gap-2 rounded border p-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{actionLabels[history.payload.action]}</Badge>
                    <Badge variant="secondary">{history.payload.source}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(history.createdAt).toLocaleString("zh-TW")}
                    {history.payload.note ? ` · ${history.payload.note}` : ""}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    by {history.payload.actor.displayName} ({history.payload.actor.email})
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setPreviewHistoryId((prev) => (prev === history.id ? null : history.id))}
                  >
                    {previewHistoryId === history.id ? "收合差異" : "預覽差異"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canManageLabels}
                    onClick={() => handleRollback(history.payload.after, `rollback to ${history.id}`)}
                  >
                    <RotateCcw className="mr-1 h-3.5 w-3.5" />
                    回滾到此版本
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {previewItem && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">回滾差異預覽</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="text-muted-foreground">
              共 {previewDiff.length} 個 key 會改變（顯示前 20 筆）
            </p>
            <div className="space-y-1">
              {previewDiff.slice(0, 20).map((row) => (
                <div key={row.key} className="rounded border p-2">
                  <p className="font-mono text-xs text-muted-foreground">{row.key}</p>
                  <p className="text-xs">from: {row.from}</p>
                  <p className="text-xs">to: {row.to}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
