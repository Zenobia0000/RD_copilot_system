import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  ArrowLeft, CheckCircle, BookOpen, RefreshCw
} from "lucide-react";
import { AiButton } from "@/components/ui/ai-button";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { SectionIntro } from "@/components/ui/section-intro";
import { KnowledgeRefsPanel } from "@/components/create/KnowledgeRefsPanel";
// TODO: Replace with useKnowledgeRefs hook once knowledge_refs DB table is created (Sprint 5+)
import { useKnowledgeEntries, useUpdateKnowledgeEntry } from "@/hooks/api/useKnowledge";

/** 6 asset categories per E2E spec (WBS 4.7.1) */
type KnowledgeAssetType =
  | 'decision'        // 決策記錄
  | 'experiment'      // 實驗結果
  | 'contradiction'   // 矛盾解法
  | 'failure_mode'    // 失效模式
  | 'design_rule'     // 設計規則
  | 'best_practice';  // 最佳實踐

const ASSET_TYPE_CONFIG: Record<KnowledgeAssetType, { label: string; color: string }> = {
  decision: { label: '決策記錄', color: '#3B82F6' },
  experiment: { label: '實驗結果', color: '#10B981' },
  contradiction: { label: '矛盾解法', color: '#F59E0B' },
  failure_mode: { label: '失效模式', color: '#EF4444' },
  design_rule: { label: '設計規則', color: '#8B5CF6' },
  best_practice: { label: '最佳實踐', color: '#EC4899' },
};

interface KnowledgeEntry {
  id: string;
  title: string;
  summary: string;
  source: string;
  assetType: KnowledgeAssetType;
  status: 'pending' | 'written' | 'reviewed';
  createdAt: string;
}

const MOCK_ENTRIES: KnowledgeEntry[] = [
  {
    id: 'ke-001',
    title: '磁力耦合傳動系統設計要點',
    summary: '磁力耦合器透過磁場實現非接觸式扭矩傳遞，關鍵參數包括氣隙距離、磁鐵材質（NdFeB vs SmCo）、溫度退磁特性。設計時需確保最大扭矩 > 1.5× 額定扭矩以防滑脫。高溫環境需選用 SmCo 或做散熱設計。',
    source: '決策記錄 DR-001 + 實驗 Exp-001',
    assetType: 'decision',
    status: 'written',
    createdAt: '2026-02-24T10:00:00Z',
  },
  {
    id: 'ke-002',
    title: '碳纖維蜂巢夾層結構減重方案',
    summary: '蜂巢夾層結構可在減重 35% 的同時維持結構剛度。關鍵假設：蜂巢芯材的剪切模量需 ≥ 50MPa。疲勞壽命需通過 10^6 次循環測試驗證。製造成本約為傳統鋁合金的 2.5 倍。',
    source: '假設 A-003 驗證結果 + TRIZ 分割原理',
    assetType: 'experiment',
    status: 'written',
    createdAt: '2026-02-24T10:30:00Z',
  },
  {
    id: 'ke-003',
    title: 'TRIZ 分割原理在傳動系統的應用模式',
    summary: '分割原理（Principle #1）應用於傳動系統時，可將單一大齒輪分割為多級小齒輪以降低噪音，或將剛性聯軸器分割為柔性元件以吸收振動。本專案中應用於將機械傳動分割為磁力耦合段 + 機械段的混合架構。',
    source: 'TRIZ 求解步驟 + 矛盾 EC-001',
    assetType: 'contradiction',
    status: 'pending',
    createdAt: '2026-02-24T11:00:00Z',
  },
  {
    id: 'ke-004',
    title: '齒輪嚙合噪音致命失效模式',
    summary: '齒輪傳動系統中，齒面磨損導致齒隙增大，引起嚙合衝擊噪音指數增長。當齒隙 > 0.3mm 時噪音可突破 75dB，超過法規限制。建議設定齒隙上限 0.2mm 並設定定期檢測週期。',
    source: 'FMEA 分析 + 文獻回顧',
    assetType: 'failure_mode',
    status: 'written',
    createdAt: '2026-02-24T11:30:00Z',
  },
  {
    id: 'ke-005',
    title: '電動自行車傳動系統散熱設計規則',
    summary: '散熱片面積需 ≥ 50cm²/kW，鰭片間距 ≥ 3mm（自然對流），材質優先選用 Al6063-T5。熱阻目標 ≤ 2°C/W。在密封環境中需額外考慮內部空氣循環路徑。',
    source: '實驗 Exp-001 結論 + 熱仿真結果',
    assetType: 'design_rule',
    status: 'reviewed',
    createdAt: '2026-02-24T12:00:00Z',
  },
  {
    id: 'ke-006',
    title: '磁力耦合器氣隙最佳實踐',
    summary: '氣隙距離建議 1.5-3mm，< 1.5mm 組裝困難且公差敏感，> 3mm 效率快速下降。磁鐵配置推薦 Halbach 陣列以提升 15-20% 磁通密度。端面密封建議採用非接觸式迷宮密封。',
    source: '產業標竿比對 + 專利分析',
    assetType: 'best_practice',
    status: 'pending',
    createdAt: '2026-02-24T12:30:00Z',
  },
];

export default function Feynman() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [localEntries, setLocalEntries] = useState<KnowledgeEntry[]>(MOCK_ENTRIES);

  // Fetch knowledge entries from Supabase
  const { data: liveEntries, isLoading: liveLoading } = useKnowledgeEntries(id);
  const updateEntry = useUpdateKnowledgeEntry();

  // Map live entries to the page's KnowledgeEntry shape
  const livePageEntries: KnowledgeEntry[] = useMemo(() =>
    liveEntries.map((e) => ({
      id: e.id,
      title: e.title,
      summary: e.content,
      source: '',
      assetType: e.assetType as KnowledgeAssetType,
      status: (e.reviewed ? 'reviewed' : 'written') as KnowledgeEntry['status'],
      createdAt: e.createdAt,
    })),
    [liveEntries],
  );

  // Prefer live Supabase data when available; fall back to local mock seed
  const hasLiveData = !liveLoading && livePageEntries.length > 0;
  const entries = hasLiveData ? livePageEntries : localEntries;
  const isLoading = liveLoading;

  const handleGenerate = async () => {
    setIsGenerating(true);
    await new Promise(r => setTimeout(r, 2000));
    const newEntry: KnowledgeEntry = {
      id: `ke-${Date.now()}`,
      title: '電動自行車噪音控制設計準則',
      summary: '噪音源分析：齒輪嚙合 > 馬達電磁 > 風切。控制策略：(1) 嚙合噪音可透過斜齒或磁力耦合消除，(2) 電磁噪音可透過 PWM 頻率調整降低，(3) 殼體隔音需 STC ≥ 25dB。目標 ≤65dB@1m 可達成。',
      source: 'AI 從決策記錄與實驗結果自動生成',
      assetType: 'design_rule',
      status: 'pending',
      createdAt: new Date().toISOString(),
    };
    setLocalEntries(prev => [...prev, newEntry]);
    setIsGenerating(false);
    toast.success('AI 已生成新知識條目');
  };

  const handleMarkReviewed = (entryId: string) => {
    // If using live data, call the update mutation
    if (hasLiveData) {
      updateEntry.mutate({ id: entryId, reviewed: true });
    } else {
      setLocalEntries(prev => prev.map(e => e.id === entryId ? { ...e, status: 'reviewed' as const } : e));
    }
    toast.success('已標記為已審閱');
  };

  const writtenCount = entries.filter(e => e.status === 'written' || e.status === 'reviewed').length;
  const reviewedCount = entries.filter(e => e.status === 'reviewed').length;
  const coveredAssetTypes = new Set(entries.map(e => e.assetType)).size;
  const totalAssetTypes = Object.keys(ASSET_TYPE_CONFIG).length;

  if (isLoading) {
    return (
      <div className="page-shell-narrow py-8">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 w-full" />)}
      </div>
    );
  }

  return (
    <div className="page-shell-narrow">
      {/* Header */}
      <div className="h-1 w-full rounded-full bg-emerald-500" />
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${id}`)} className="text-muted-foreground -ml-2">
          <ArrowLeft className="h-4 w-4 mr-1" /> 返回
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Feynman — 內化與傳達
            <HelpTooltip text="費曼學習法：AI 自動將決策記錄、實驗結果與設計知識轉化為知識庫條目，實現組織學習的自動化。此步驟為全自動（Fully Auto），無需人類介入。" className="ml-2 align-middle" />
          </h1>
          <p className="text-sm text-muted-foreground">Phase 3: Converge &gt; V4（知識回寫自動化）</p>
        </div>
      </div>

      <SectionIntro text="AI 自動將本專案的決策記錄、驗證實驗結果、矛盾解法、失效模式、設計規則、最佳實踐等 6 類資產轉化為可重複使用的知識庫條目。此步驟為全自動，您僅需審閱確認即可。" />

      {/* Stats */}
      <div className="flex flex-wrap gap-3">
        <Badge className="bg-primary text-primary-foreground px-3 py-1">{entries.length} 條目</Badge>
        <Badge variant="secondary" className="px-3 py-1">{writtenCount} 已寫入</Badge>
        <Badge className="bg-green-600 text-white px-3 py-1">{reviewedCount} 已審閱</Badge>
        <Badge variant="outline" className="px-3 py-1">{coveredAssetTypes}/{totalAssetTypes} 類資產</Badge>
      </div>

      {/* Asset type legend */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(ASSET_TYPE_CONFIG) as [KnowledgeAssetType, { label: string; color: string }][]).map(([type, cfg]) => {
          const count = entries.filter(e => e.assetType === type).length;
          return (
            <Badge key={type} variant="outline" className="text-xs gap-1" style={{ borderColor: cfg.color }}>
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: cfg.color }} />
              {cfg.label} ({count})
            </Badge>
          );
        })}
      </div>

      {/* Auto badge */}
      <Card className="border-dashed bg-muted/30">
        <CardContent className="p-3 flex items-center gap-3 text-xs text-muted-foreground">
          <RefreshCw className="h-4 w-4 shrink-0" />
          <div>
            <span className="font-medium text-foreground">自動化等級：Fully Auto</span>
            <span> — AI 自動從決策記錄與實驗結果提取知識，寫入知識庫。Knowledge Agent 執行。</span>
          </div>
        </CardContent>
      </Card>

      {/* Knowledge entries */}
      <div className="space-y-4">
        {entries.map((entry, i) => (
          <Card key={entry.id} className={entry.status === 'reviewed' ? 'border-l-[3px] border-l-green-600' : entry.status === 'written' ? 'border-l-[3px] border-l-primary' : ''}>
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="secondary" className="text-[10px]">AI</Badge>
                <Badge variant="outline" className="text-[10px] font-mono">KE-{String(i + 1).padStart(3, '0')}</Badge>
                <Badge
                  className="text-[10px] text-white"
                  style={{ backgroundColor: ASSET_TYPE_CONFIG[entry.assetType].color }}
                >
                  {ASSET_TYPE_CONFIG[entry.assetType].label}
                </Badge>
                <Badge
                  className={`text-[10px] text-white ${
                    entry.status === 'reviewed' ? 'bg-green-600' : entry.status === 'written' ? 'bg-primary' : 'bg-muted-foreground'
                  }`}
                >
                  {entry.status === 'reviewed' ? '已審閱' : entry.status === 'written' ? '已寫入' : '待處理'}
                </Badge>
              </div>
              <h3 className="text-sm font-semibold">{entry.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{entry.summary}</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground">來源：{entry.source}</span>
                <div className="flex gap-2">
                  {entry.status !== 'reviewed' && (
                    <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => handleMarkReviewed(entry.id)}>
                      <CheckCircle className="h-3 w-3 mr-1" /> 確認審閱
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" className="text-xs h-7" onClick={() => navigate('/knowledge-base')}>
                    <BookOpen className="h-3 w-3 mr-1" /> 查看知識庫
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Generate more */}
      <div className="flex flex-wrap gap-3">
        <AiButton loading={isGenerating} onClick={handleGenerate}>
          生成知識條目
        </AiButton>
      </div>

      {/* Knowledge Enhancement Panel (WBS 3.4.2) */}
      {/* TODO: Replace with useKnowledgeRefs hook (Sprint 5+) */}
      <KnowledgeRefsPanel refs={[]} />

      {/* Gate */}
      <Separator />
      <Card className="border-2 border-emerald-500 bg-emerald-50">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-3">
            <BookOpen className="h-5 w-5 text-emerald-500" />
            <h3 className="text-sm font-semibold">V4 / Gate V4 完成檢查</h3>
            <Badge className={`text-xs text-white ${reviewedCount >= entries.length && entries.length > 0 && coveredAssetTypes >= totalAssetTypes ? 'bg-green-600' : 'bg-red-600'}`}>
              {reviewedCount >= entries.length && entries.length > 0 && coveredAssetTypes >= totalAssetTypes ? '完成' : '待完成'}
            </Badge>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              {entries.length > 0 ? <CheckCircle className="h-4 w-4 text-green-600" /> : <span className="h-4 w-4 rounded-full border-2 border-muted-foreground" />}
              <span>至少 1 條知識條目已生成</span>
            </div>
            <div className="flex items-center gap-2">
              {coveredAssetTypes >= totalAssetTypes ? <CheckCircle className="h-4 w-4 text-green-600" /> : <span className="h-4 w-4 rounded-full border-2 border-muted-foreground" />}
              <span>6 類資產皆已覆蓋 ({coveredAssetTypes}/{totalAssetTypes})</span>
            </div>
            <div className="flex items-center gap-2">
              {reviewedCount >= entries.length && entries.length > 0 ? <CheckCircle className="h-4 w-4 text-green-600" /> : <span className="h-4 w-4 rounded-full border-2 border-muted-foreground" />}
              <span>所有條目已審閱 ({reviewedCount}/{entries.length})</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
