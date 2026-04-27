/**
 * EvidenceEntryDialog — Reusable dialog for logging structured measurement evidence.
 *
 * Entry points:
 * - Dashboard KPI card → defaultKpiId
 * - Track Kanban assumption detail → defaultAssumptionCodes
 * - DesignReview evidence matrix → defaultAssumptionCodes
 */

import { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useKpis } from '@/hooks/api/useBrief';
import { useTrackAssumptions } from '@/hooks/api/useTrack';
import { useCreateEvidenceEntry } from '@/hooks/api/useEvidenceEntries';
import { useProject } from '@/hooks/api/useProjects';
import type { EvidenceLevel } from '@/types/designReview';
import { Save, Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EvidenceEntryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  defaultKpiId?: string | null;
  defaultAssumptionCodes?: string[];
  defaultExperimentId?: string | null;
}

const EVIDENCE_LEVELS: { value: EvidenceLevel; label: string }[] = [
  { value: 'E1', label: 'E1 — 估算' },
  { value: 'E2', label: 'E2 — 模擬' },
  { value: 'E3', label: 'E3 — 原型實測' },
  { value: 'E4', label: 'E4 — 量產驗證' },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function EvidenceEntryDialog({
  open,
  onOpenChange,
  projectId,
  defaultKpiId = null,
  defaultAssumptionCodes = [],
  defaultExperimentId = null,
}: EvidenceEntryDialogProps) {
  // Form state
  const [title, setTitle] = useState('');
  const [measuredValue, setMeasuredValue] = useState('');
  const [unit, setUnit] = useState('');
  const [evidenceLevel, setEvidenceLevel] = useState<EvidenceLevel>('E1');
  const [method, setMethod] = useState('');
  const [notes, setNotes] = useState('');
  const [measuredAt, setMeasuredAt] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [selectedKpiId, setSelectedKpiId] = useState<string>(defaultKpiId ?? '');
  const [selectedAssumptionCodes, setSelectedAssumptionCodes] = useState<string[]>(defaultAssumptionCodes);
  const [selectedMustIds, setSelectedMustIds] = useState<string[]>([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>(defaultExperimentId ?? '');

  // Data sources
  const { data: kpis } = useKpis(projectId);
  const { data: assumptions } = useTrackAssumptions(projectId);
  const { data: project } = useProject(projectId);
  const mustCriteria = project?.must_criteria_config ?? [];

  const createEntry = useCreateEvidenceEntry();

  // Reset form when dialog closes
  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      setTitle('');
      setMeasuredValue('');
      setUnit('');
      setEvidenceLevel('E1');
      setMethod('');
      setNotes('');
      setMeasuredAt(new Date().toISOString().slice(0, 10));
      setSelectedKpiId(defaultKpiId ?? '');
      setSelectedAssumptionCodes(defaultAssumptionCodes);
      setSelectedMustIds([]);
      setSelectedExperimentId(defaultExperimentId ?? '');
    }
    onOpenChange(isOpen);
  };

  // Auto-fill unit from selected KPI
  const selectedKpi = useMemo(
    () => kpis?.find((k) => k.id === selectedKpiId),
    [kpis, selectedKpiId],
  );

  const handleKpiChange = (kpiId: string) => {
    const resolved = kpiId === "__none__" ? "" : kpiId;
    setSelectedKpiId(resolved);
    const kpi = kpis?.find((k) => k.id === resolved);
    if (kpi?.unit) setUnit(kpi.unit);
  };

  const toggleAssumption = (code: string) => {
    setSelectedAssumptionCodes((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  };

  const toggleMust = (id: string) => {
    setSelectedMustIds((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id],
    );
  };

  const canSubmit = title.trim() && measuredValue.trim();

  const handleSubmit = () => {
    if (!canSubmit) return;

    createEntry.mutate(
      {
        projectId,
        title: title.trim(),
        measuredValue: measuredValue.trim(),
        unit: unit.trim(),
        evidenceLevel,
        method: method.trim(),
        notes: notes.trim(),
        measuredAt: new Date(measuredAt).toISOString(),
        kpiId: selectedKpiId || null,
        experimentId: selectedExperimentId || null,
        linkedAssumptionCodes: selectedAssumptionCodes,
        linkedMustIds: selectedMustIds,
      },
      {
        onSuccess: () => {
          handleOpenChange(false);
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>登錄證據</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Title */}
          <div className="space-y-1.5">
            <Label htmlFor="ev-title">標題 *</Label>
            <Input
              id="ev-title"
              placeholder="例：GaN 效率測試結果"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Measured value + Unit */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="ev-value">量測值 *</Label>
              <Input
                id="ev-value"
                placeholder="97.2"
                value={measuredValue}
                onChange={(e) => setMeasuredValue(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ev-unit">單位</Label>
              <Input
                id="ev-unit"
                placeholder="%"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
              />
            </div>
          </div>

          {/* Evidence Level + Method */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>證據等級</Label>
              <Select value={evidenceLevel} onValueChange={(v) => setEvidenceLevel(v as EvidenceLevel)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EVIDENCE_LEVELS.map((l) => (
                    <SelectItem key={l.value} value={l.value}>
                      {l.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ev-method">量測方式</Label>
              <Input
                id="ev-method"
                placeholder="48V Dyno 測試"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              />
            </div>
          </div>

          {/* Measured date */}
          <div className="space-y-1.5">
            <Label htmlFor="ev-date">量測日期</Label>
            <Input
              id="ev-date"
              type="date"
              value={measuredAt}
              onChange={(e) => setMeasuredAt(e.target.value)}
            />
          </div>

          {/* Divider: Links */}
          <div className="border-t pt-3">
            <p className="text-sm font-medium text-muted-foreground mb-3">關聯項目</p>

            {/* KPI select */}
            {kpis && kpis.length > 0 && (
              <div className="space-y-1.5 mb-3">
                <Label>KPI</Label>
                <Select value={selectedKpiId || "__none__"} onValueChange={handleKpiChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="選擇 KPI（選填）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">不關聯</SelectItem>
                    {kpis.map((k) => (
                      <SelectItem key={k.id} value={k.id}>
                        {k.kpiName} ({k.targetValue} {k.unit})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Assumption multi-select */}
            {assumptions && assumptions.length > 0 && (
              <div className="space-y-1.5 mb-3">
                <Label>關聯假設</Label>
                <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
                  {assumptions.map((a) => (
                    <label
                      key={a.assumptionCode}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 rounded px-1 py-0.5"
                    >
                      <Checkbox
                        checked={selectedAssumptionCodes.includes(a.assumptionCode)}
                        onCheckedChange={() => toggleAssumption(a.assumptionCode)}
                      />
                      <span className="font-mono text-xs text-muted-foreground">{a.assumptionCode}</span>
                      <span className="truncate">{a.description}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* MUST multi-select */}
            {mustCriteria.length > 0 && (
              <div className="space-y-1.5 mb-3">
                <Label>MUST 準則</Label>
                <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
                  {mustCriteria.map((m) => (
                    <label
                      key={m.id}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 rounded px-1 py-0.5"
                    >
                      <Checkbox
                        checked={selectedMustIds.includes(m.id)}
                        onCheckedChange={() => toggleMust(m.id)}
                      />
                      <span className="font-mono text-xs text-muted-foreground">{m.id}</span>
                      <span className="truncate">{m.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label htmlFor="ev-notes">備註</Label>
            <Textarea
              id="ev-notes"
              placeholder="實測效率超越目標 2.2%"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit || createEntry.isPending}>
            {createEntry.isPending ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-1" />
            )}
            登錄
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
