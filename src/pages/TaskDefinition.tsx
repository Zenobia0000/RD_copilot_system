import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ConstraintsTable } from "@/components/brief/ConstraintsTable";
import { KpiList } from "@/components/brief/KpiList";
import { AITaskDefinitionCard } from "@/components/brief/AITaskDefinitionCard";
import { GateChecklist } from "@/components/brief/GateChecklist";
import { AISuggestionCard } from "@/components/brief/AISuggestionCard";
import { EvidenceRefsInline } from "@/components/brief/EvidenceRefsInline";
import { FileUploadZone } from "@/components/task-definition/FileUploadZone";
import { AIExtractionResults } from "@/components/task-definition/AIExtractionResults";
import { FeasibilityValidation } from "@/components/task-definition/FeasibilityValidation";
import { MultiItemInput } from "@/components/task-definition/MultiItemInput";
import { ArrowLeft, AlertCircle, RefreshCw, Check } from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { cn } from "@/lib/utils";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { useTaskDefinitionForm } from "@/hooks/useTaskDefinitionForm";

export default function TaskDefinition() {
  const { id } = useParams<{ id: string }>();

  const form = useTaskDefinitionForm(id);

  if (form.isLoading) {
    return (
      <div className="page-shell-narrow">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-24 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (form.loadError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center mx-auto max-w-md">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-lg font-semibold">載入失敗</h2>
        <p className="text-sm text-muted-foreground mt-1 mb-4">無法取得任務定義資料。</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          重試
        </Button>
      </div>
    );
  }

  return (
    <div className="page-shell-narrow">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => form.navigate(`/projects/${id}`)} className="text-muted-foreground -ml-2">
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回 Dashboard
          </Button>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void form.runBackendHealthCheck(true)}
              className="h-7 px-2 text-xs"
            >
              <RefreshCw className={cn("h-3 w-3 mr-1", form.backendStatus === "checking" && "animate-spin")} />
              後端檢查
            </Button>
            <Badge variant={form.backendStatus === "ok" ? "default" : form.backendStatus === "down" ? "destructive" : "secondary"} className="text-[10px]">
              {form.backendStatus === "ok" ? "Backend 正常" : form.backendStatus === "down" ? "Backend 異常" : "Backend 檢查中"}
            </Badge>
            {form.saveStatus !== "idle" && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                {form.saveStatus === "saving" && "Saving..."}
                {form.saveStatus === "saved" && (
                  <><Check className="h-3 w-3 text-success" /> Saved</>
                )}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 rounded-full bg-phase-1" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              任務定義
              <HelpTooltip text="任務定義是設計流程的起點。上傳素材讓 AI 自動提取約束，定義 Mission、硬約束和 KPI，並通過約束可行性驗證 (Gate D1)。" className="ml-2 align-middle" />
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              D1 · 結構化定義 Mission、約束與 KPI，支援 AI 自動提取
            </p>
          </div>
        </div>
      </div>

      <SectionIntro text="上傳專案相關素材，AI 將自動提取約束與假設。接著定義核心使命、硬約束、軟目標與 KPI，通過約束可行性驗證後進入下一階段。" />

      {form.backendStatus === "down" && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="py-3 text-sm text-destructive flex items-center justify-between gap-3">
            <span>{form.backendStatusMessage}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void form.runBackendHealthCheck(true)}
              className="h-7"
            >
              重新檢查
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Section 1: 多模態素材上傳 */}
      <FileUploadZone
        files={form.uploadedFiles}
        onFilesChange={form.setUploadedFiles}
        onExtract={form.handleExtract}
        isExtracting={form.isExtracting}
      />

      {/* Section 2: AI 提取結果 */}
      <AIExtractionResults
        items={form.extractedItems}
        onItemsChange={form.setExtractedItems}
        onAcceptAll={form.handleAcceptAllExtracted}
        visible={form.showExtraction}
      />

      {/* Section 3: Mission */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            核心使命 (Mission Statement) <span className="text-destructive">*</span>
          </CardTitle>
          <p className="text-xs text-muted-foreground italic">
            模板：在 [情境] 下，系統必須 [行為]，且 [指標] 不得超標
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={form.mission}
            onChange={(e) => form.setMission(e.target.value)}
            placeholder="在 [情境] 下，系統必須 [行為]，且 [指標] 不得超標"
            rows={4}
            className={cn(
              "min-h-[100px]",
              form.missionReady && "border-l-[3px] border-l-success"
            )}
          />
          <div className="flex justify-between items-center text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              {!form.missionReady && form.mission.trim().length > 0 && (
                <span className="text-destructive">Mission 需至少 10 個字元</span>
              )}
              {form.missionReady && !form.showMissionSuggestion && (
                <AiButton
                  size="sm"
                  loading={form.isMissionRewriting}
                  onClick={form.handleMissionRewrite}
                  className="text-xs h-7"
                >
                  改寫 Mission
                </AiButton>
              )}
            </div>
            <span>{form.mission.length}字</span>
          </div>
          {form.showMissionSuggestion && (
            <>
              <AISuggestionCard
                title="改寫建議"
                content={form.missionSuggestion}
                changesSummary={form.missionChangesSummary}
                isLoading={form.isMissionRewriting}
                onAdopt={form.handleAdoptMissionSuggestion}
                onSkip={form.handleDismissMissionSuggestion}
                rows={4}
              />
              {form.missionEvidenceRefs.length > 0 && (
                <EvidenceRefsInline references={form.missionEvidenceRefs} />
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Section 4: Hard Constraints */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              硬約束 (Hard Constraints) <span className="text-destructive">*</span>
            </CardTitle>
            <AiButton
              size="sm"
              loading={form.isConstraintSuggesting}
              onClick={form.handleConstraintSuggest}
              disabled={form.isConstraintSuggesting || form.activeConstraintActionIndex !== null}
            >
              建議約束
            </AiButton>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <ConstraintsTable constraints={form.constraints} onChange={form.setConstraints} onRemove={form.removeConstraint} />
          {form.showConstraintSuggestions && (
            <div className="space-y-2 mt-3">
              {form.isConstraintSuggesting && (
                <AISuggestionCard
                  title="分析中..."
                  isLoading
                  onAdopt={() => {}}
                  onSkip={form.handleDismissConstraintSuggesting}
                  disableActions={form.activeConstraintActionIndex !== null}
                />
              )}
              {form.constraintSuggestionList.map((s, i) => (
                <AISuggestionCard
                  key={i}
                  title={`建議約束 #${i + 1}`}
                  content={`約束描述: ${s.description}\n來源依據: ${s.source}`}
                  changesSummary={s.rationale}
                  isAdopting={form.activeConstraintActionIndex === i}
                  disableActions={form.activeConstraintActionIndex !== null && form.activeConstraintActionIndex !== i}
                  onAdopt={async () => form.handleAdoptConstraintAtIndex(i, s)}
                  onSkip={() => form.handleSkipConstraintAtIndex(i)}
                  rows={2}
                />
              ))}
              {!form.isConstraintSuggesting && form.constraintEvidenceRefs.length > 0 && (
                <EvidenceRefsInline references={form.constraintEvidenceRefs} />
              )}
              {!form.isConstraintSuggesting && form.constraintSuggestionList.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-2">AI 未產出額外建議</p>
              )}
              {!form.isConstraintSuggesting && (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={form.activeConstraintActionIndex !== null}
                  onClick={form.handleCloseConstraintSuggestions}
                  className="text-xs"
                >
                  關閉建議
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Section 5: Soft Objectives */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">軟目標 (Soft Objectives)</CardTitle>
          <p className="text-xs text-muted-foreground">可權衡的目標，如效能提升、重量輕量化</p>
        </CardHeader>
        <CardContent>
          <MultiItemInput
            items={form.softObjectives}
            onChange={form.setSoftObjectives}
            placeholder="輸入軟目標，按 Enter 新增"
          />
        </CardContent>
      </Card>

      {/* Section 6: Non-Goals */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">非目標 (Non-Goals)</CardTitle>
          <p className="text-xs text-muted-foreground">明確定義本版專案不追求的範圍，避免範圍蔓延</p>
        </CardHeader>
        <CardContent>
          <MultiItemInput
            items={form.nonGoals}
            onChange={form.setNonGoals}
            placeholder="輸入非目標，按 Enter 新增"
          />
        </CardContent>
      </Card>

      {/* Section 7: KPIs */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              關鍵績效指標 (Critical KPIs) <span className="text-destructive">*</span>
            </CardTitle>
            <AiButton
              size="sm"
              loading={form.isKpiSuggesting}
              onClick={form.handleKpiSuggest}
              disabled={form.isKpiSuggesting || form.activeKpiActionIndex !== null}
            >
              建議 KPI
            </AiButton>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <KpiList kpis={form.kpis} onChange={form.setKpis} onRemove={form.removeKpi} />
          {form.showKpiSuggestions && (
            <div className="space-y-2 mt-3">
              {form.isKpiSuggesting && (
                <AISuggestionCard
                  title="分析中..."
                  isLoading
                  onAdopt={() => {}}
                  onSkip={form.handleDismissKpiSuggesting}
                  disableActions={form.activeKpiActionIndex !== null}
                />
              )}
              {form.kpiSuggestionList.map((s, i) => (
                <AISuggestionCard
                  key={i}
                  title={`建議 KPI: ${s.kpi_name}`}
                  content={`目標值: ${s.target_value} ${s.unit}\n衡量方式: ${s.measurement_method}`}
                  changesSummary={s.rationale}
                  isAdopting={form.activeKpiActionIndex === i}
                  disableActions={form.activeKpiActionIndex !== null && form.activeKpiActionIndex !== i}
                  onAdopt={async () => form.handleAdoptKpiAtIndex(i, s)}
                  onSkip={() => form.handleSkipKpiAtIndex(i)}
                  rows={2}
                />
              ))}
              {!form.isKpiSuggesting && form.kpiEvidenceRefs.length > 0 && (
                <EvidenceRefsInline references={form.kpiEvidenceRefs} />
              )}
              {!form.isKpiSuggesting && form.kpiSuggestionList.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-2">AI 未產出額外建議</p>
              )}
              {!form.isKpiSuggesting && (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={form.activeKpiActionIndex !== null}
                  onClick={form.handleCloseKpiSuggestions}
                  className="text-xs"
                >
                  關閉建議
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Section 8: AI 5W1H */}
      <AITaskDefinitionCard
        data={form.taskDef5W1H}
        missionReady={form.missionReady}
        onRegenerate={form.handleRegenerate5W1H}
      />

      {/* Section 9: 約束可行性驗證 (Gate D1) */}
      <FeasibilityValidation
        status={form.feasibilityStatus}
        conflicts={form.feasibilityConflicts.map((c, i) => ({ id: `fc-${i}`, ...c }))}
        stale={form.isFeasibilityStale}
        onCheck={form.handleFeasibilityCheck}
        onOverride={form.handleFeasibilityOverride}
      />

      {/* Section 10: Gate D1 Checklist — sole exit point */}
      <GateChecklist
        items={form.gateItems}
        onNavigateNext={form.handleSubmit}
        isSubmitting={form.isSubmitting}
      />

      <div className="flex gap-3 pb-8">
        <Button variant="ghost" size="sm" onClick={() => form.navigate(`/projects/${id}`)} className="text-muted-foreground">
          ← 返回 Dashboard
        </Button>
      </div>
    </div>
  );
}
