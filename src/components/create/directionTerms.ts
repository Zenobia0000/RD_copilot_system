/**
 * directionTerms.ts — Single source of truth for the colour/label/description
 * of every "term" that appears on the Create page's 「解矛盾」 section
 * (DirectionResultCard + DecisionCardPanel + the new DirectionTermsGlossary).
 *
 * Why centralise:
 *   - Resolution Status (5), Addresses Layer (4), Per-SR Verdict (6),
 *     SR Kind (4), Sort (4), Filter (4), Severity (4), Score columns (4)
 *     all live here. The Card uses them for Badges/Tooltips; the Glossary
 *     uses them for the long-form explanation panel.
 *   - When backend adds a new state (e.g. a 6th ResolutionStatus), one
 *     file flips the whole UI + docs into sync.
 *
 * Keep ZERO React imports here — this file is pure data so it can be
 * imported by tests, the Glossary, and the Card alike.
 */

import type {
  ResolutionStatus,
  AddressesLayer,
  PerSrVerdict,
  SubRequirementKind,
} from '@/types/directedTriz';

// ---------------------------------------------------------------------------
// Common shape for every "term entry"
// ---------------------------------------------------------------------------

export interface TermEntry {
  /** Short label shown on the badge / chip. */
  label: string;
  /** Tailwind class string for the badge background + text + border. */
  className?: string;
  /** Just the dot colour (for per-SR rows that use a tiny dot indicator). */
  dotClass?: string;
  /** One-line plain-language meaning — shown in tooltips. */
  description: string;
  /** Concrete RD-friendly example — shown only in the Glossary, not tooltip. */
  example?: string;
}

// ---------------------------------------------------------------------------
// Glossary section identifier
// ---------------------------------------------------------------------------
// Used by the in-place "?" buttons next to Sort / Filter so they can open
// the Glossary sheet pre-scrolled to the relevant section.
export type GlossarySectionId =
  | 'manifest'
  | 'resolution_status'
  | 'addresses_layer'
  | 'per_sr_verdict'
  | 'score_columns'
  | 'sort_filter'
  | 'severity'
  | 'why_not_verdict';

// ---------------------------------------------------------------------------
// 1) Resolution Status — 方向級的整體審判 (5 種)
// ---------------------------------------------------------------------------
export const RESOLUTION_STATUS_TERMS: Record<ResolutionStatus, TermEntry> = {
  directly_resolves: {
    label: '✓ 直接解決',
    className: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-950 dark:text-green-200',
    description: '同時改善目標、抑制副作用，未明顯違反邊界 — 這個方向已經解掉矛盾。',
    example: '例：吸震結構 + 阻尼層同時降低諧波振動（想改善）並未犧牲扭矩（想避免），是「直接解決」。',
  },
  partially_resolves: {
    label: '◐ 部分解決',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-950 dark:text-yellow-200',
    description: '只解到矛盾其中一面，或只壓掉症狀沒處理根因。',
    example: '例：只加阻尼貼片降低振動表象，但齒輪嚙合誤差（真正根因）沒動 → 「部分解決」。',
  },
  conditionally_resolves: {
    label: '⚠ 條件成立',
    className: 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-950 dark:text-orange-200',
    description: '理論上可行，但依賴尚未證明的關鍵假設 — 假設不成立就不算解。',
    example: '例：firmware 演算法消除 backlash —「如果」chirp 訊號能在 5 ms 內辨識諧波，就成立；要先做 bench 驗證。',
  },
  does_not_resolve: {
    label: '✗ 未解到',
    className: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-200',
    description: '與矛盾關聯弱，或違反 mission / KPI / 邊界條件。',
    example: '例：改成液冷可降熱（想改善），但重量超過 mission 規定的 1.2 kg 上限（不可違反）→ 違反邊界，「未解到」。',
  },
  unclear: {
    label: '? 資訊不足',
    className: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300',
    description: '資料不足，AI 無法可靠判定 — 通常代表問題描述太抽象或方向太籠統。',
    example: '例：方向描述「優化控制邏輯」太空泛，又沒給對哪一條訊號做什麼 → 標 「資訊不足」 提醒 RD 補資料。',
  },
};

// ---------------------------------------------------------------------------
// 2) Addresses Layer — 解到哪一層因果 (4 種)
// ---------------------------------------------------------------------------
export const ADDRESSES_LAYER_TERMS: Record<AddressesLayer, TermEntry> = {
  root_cause: {
    label: '解根因',
    className: 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200',
    description: '動到「導致矛盾發生」的最底層原因。',
    example: '例：根因是「諧波減速齒對嚙合誤差」，重新設計柔輪齒形使誤差<0.005° → 解根因。',
  },
  mechanism: {
    label: '解機制',
    className: 'bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-950 dark:text-sky-200',
    description: '動到「中間傳遞機制」（如熱傳路徑、力學鏈、訊號路徑）。',
    example: '例：根因動不到，但在嚙合誤差 → 傳到輸出軸的力學鏈上加阻尼層阻擋傳遞 → 解機制。',
  },
  symptom: {
    label: '解症狀',
    className: 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-200',
    description: '只壓掉「表面現象」，根因與機制仍存在。',
    example: '例：在外殼貼吸音棉降低聽到的噪音，齒輪誤差跟力學傳遞鏈都沒動 → 解症狀。',
  },
  unclear: {
    label: '層級不明',
    className: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300',
    description: '資訊不足，無法判斷這個方向動到哪一層因果。',
  },
};

// 設計哲學：解根因 > 解機制 > 解症狀（越底層越值得投資）。
export const ADDRESSES_LAYER_PHILOSOPHY =
  '設計哲學：解根因 > 解機制 > 解症狀。越底層越值得投資，但成本通常也越高。RD 要在「徹底度」與「實作成本」之間取捨。';

// ---------------------------------------------------------------------------
// 3) Per-SR Verdict — 方向對「單條子需求」的評語 (6 種)
// ---------------------------------------------------------------------------
export interface VerdictTermEntry extends TermEntry {
  icon: string;
}

export const VERDICT_TERMS: Record<PerSrVerdict, VerdictTermEntry> = {
  directly_solves: {
    icon: '✓',
    label: '直接解',
    className: 'text-green-700 dark:text-green-300',
    dotClass: 'bg-green-500',
    description: '這條 SR 被這個方向直接解掉。',
  },
  partially_solves: {
    icon: '◐',
    label: '部分支撐',
    className: 'text-yellow-700 dark:text-yellow-300',
    dotClass: 'bg-yellow-500',
    description: '只間接支撐，不算解掉 — 需要其他方向補位。',
  },
  needs_verify: {
    icon: '⚠',
    label: '要驗證',
    className: 'text-orange-700 dark:text-orange-300',
    dotClass: 'bg-orange-500',
    description: '理論上會解，但需要 bench / sim 才能確認。',
  },
  violates: {
    icon: '✗',
    label: '違反',
    className: 'text-red-700 dark:text-red-300',
    dotClass: 'bg-red-500',
    description: '這個方向違反這條 SR — 強烈淘汰訊號。',
  },
  not_addressed: {
    icon: '·',
    label: '未觸及',
    className: 'text-muted-foreground',
    dotClass: 'bg-gray-400',
    description: '這個方向沒有處理這條 SR。',
  },
  unclear: {
    icon: '?',
    label: '不清楚',
    className: 'text-muted-foreground',
    dotClass: 'bg-gray-400',
    description: '方向有提到這條，但 AI 沒給明確判斷。',
  },
};

// ---------------------------------------------------------------------------
// 4) SR Kind — 子需求類別 (4 種)
// ---------------------------------------------------------------------------
export interface SrKindTermEntry extends TermEntry {
  tag: string;
  /** Tailwind class for the small inline tag (DecisionCardPanel.ContradictionManifest). */
  tone: string;
}

export const SR_KIND_TERMS: Record<SubRequirementKind, SrKindTermEntry> = {
  desired_improvement: {
    tag: '想改善',
    label: '想改善',
    tone: 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200',
    description: '矛盾想要「更多 / 更好」的那一面。',
    example: '例：「希望伺服馬達輸出扭矩提升 30%」← 想改善。',
  },
  undesired_effect: {
    tag: '想避免',
    label: '想避免',
    tone: 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200',
    description: '矛盾想要「擋住別變更糟」的那一面。',
    example: '例：「但體積與重量不能增加」← 想避免。',
  },
  boundary_condition: {
    tag: '不可違反',
    label: '不可違反',
    tone: 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200',
    description: '硬限制 — 一旦違反整個方案就無效。',
    example: '例：「外殼最大直徑 ≤ 95 mm」← 不可違反。',
  },
  mission_outcome: {
    tag: '驗收標準',
    label: '驗收標準',
    tone: 'bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-200',
    description: 'KPI / Mission 等級的最終承諾。',
    example: '例：「Backlash < 0.02° 且雜訊 < 55 dB」← 驗收標準。',
  },
};

// ---------------------------------------------------------------------------
// 5) Score Columns — 4 個分數欄位 (DirectionBlock 內部)
// ---------------------------------------------------------------------------
export interface ScoreColumnTerm {
  key: 'tool_support' | 'feasibility' | 'cost_difficulty' | 'coverage';
  label: string;
  description: string;
  example?: string;
}

export const SCORE_COLUMN_TERMS: ScoreColumnTerm[] = [
  {
    key: 'tool_support',
    label: '工具支持',
    description:
      'TC + PC + SF 三條 TRIZ 路徑各有多少工具產出此方向，分數越高代表越多獨立路徑同意。',
    example: '例：TC 投 2 票 + PC 投 1 票 + SF 投 1 票 → tool_support=4；高於只有 1 個工具同意的方向。',
  },
  {
    key: 'feasibility',
    label: '技術成熟度',
    description:
      '跨領域 / 同類應用是否已有實例支持，分數越高代表技術越成熟、越值得相信。',
    example: '例：「PCM 相變材料散熱」已有量產手機案例 → feasibility 高；「常溫超導磁懸浮」尚未量產 → feasibility 低。',
  },
  {
    key: 'cost_difficulty',
    label: '實施容易度',
    description:
      '實施所需成本與複雜度 — 分數越高代表越便宜、越容易（不是越貴！）。',
    example: '例：firmware-only 改演算法 → cost_difficulty=9 高分；要重新開模改結構 → cost_difficulty=4。',
  },
  {
    key: 'coverage',
    label: '解掉矛盾的程度',
    description: '此方向「單獨採用」對矛盾本身 + 相關 SR 的涵蓋率，分數越高代表越能獨立解掉這個矛盾。',
    example: '例：覆蓋 5 條 SR 中的 4 條且無違反 → coverage 高；只覆蓋 1 條 → coverage 低。',
  },
];

// ---------------------------------------------------------------------------
// 6) Sort options (4 種) — 排序選單
// ---------------------------------------------------------------------------
export type SortMode = 'tool_support' | 'feasibility' | 'cost_difficulty' | 'coverage';

export interface SortOptionTerm {
  value: SortMode;
  label: string;
  description: string;
}

export const SORT_OPTIONS: SortOptionTerm[] = [
  {
    value: 'tool_support',
    label: '工具支持優先',
    description: '優先顯示「越多 TRIZ 工具同意」的方向，適合想看「最多獨立路徑指向同一答案」的場景。',
  },
  {
    value: 'feasibility',
    label: '技術成熟度優先',
    description: '優先顯示「已有實例驗證」的方向，適合風險規避、追求穩妥落地。',
  },
  {
    value: 'cost_difficulty',
    label: '實施容易度優先',
    description: '優先顯示「最便宜、最容易做」的方向（高分=容易），適合預算/時程吃緊的迭代。',
  },
  {
    value: 'coverage',
    label: '解掉矛盾的程度優先',
    description: '優先顯示「對 SR 覆蓋率最高」的方向，適合想找「單一方向就能搞定大半」的場景。',
  },
];

// ---------------------------------------------------------------------------
// 7) Filter options (4 種) — 篩選選單
// ---------------------------------------------------------------------------
export type FilterMode =
  | 'all'
  | 'directly_only'
  | 'hide_does_not'
  | 'with_assumptions';

export interface FilterOptionTerm {
  value: FilterMode;
  label: string;
  description: string;
}

export const FILTER_OPTIONS: FilterOptionTerm[] = [
  { value: 'all', label: '全部', description: '顯示所有方向，不過濾。' },
  {
    value: 'directly_only',
    label: '只看直接解決',
    description: '只顯示 Resolution Status = 「直接解決」的方向，最快收斂候選池。',
  },
  {
    value: 'hide_does_not',
    label: '藏掉未解到',
    description: '藏掉 Resolution Status = 「未解到」的方向，其他全留（含「資訊不足」）。',
  },
  {
    value: 'with_assumptions',
    label: '只看條件解 (依賴假設)',
    description:
      '只顯示 Resolution Status = 「條件成立」的方向 — 適合 RD 想集中盤點「哪些方向必須先驗證假設」。',
  },
];

// ---------------------------------------------------------------------------
// 8) Severity (4 種) — 矛盾嚴重度
// ---------------------------------------------------------------------------
export type SeverityKey = 'fatal' | 'major' | 'minor' | 'unknown';

export interface SeverityTerm extends TermEntry {
  variant: 'destructive' | 'default' | 'secondary' | 'outline';
}

export const SEVERITY_TERMS: Record<SeverityKey, SeverityTerm> = {
  fatal: {
    label: '致命',
    variant: 'destructive',
    description: '架構層級的根本性衝突，必須完全解決才能繼續。未收斂則 Confidence 無法達 100%。',
  },
  major: {
    label: '主要',
    variant: 'default',
    description: '影響核心功能的重大矛盾，必須解決。與 Fatal 共同計入 Confidence 公式分母。',
  },
  minor: {
    label: '次要',
    variant: 'secondary',
    description: '次要矛盾，不阻斷收斂流程。自動記入 Risk Register，供後續設計階段追蹤處理。',
  },
  unknown: {
    label: '未知',
    variant: 'outline',
    description: '矛盾嚴重度尚未評估或 AI 沒給明確判定。',
  },
};

// ---------------------------------------------------------------------------
// 9) Glossary section metadata — used by the Glossary sheet for nav + by
//    the in-place "?" buttons so they can jump to the right section.
// ---------------------------------------------------------------------------
export interface GlossarySectionMeta {
  id: GlossarySectionId;
  title: string;
  /** Short subtitle shown under the title — 用一句話解釋本節說什麼。 */
  blurb: string;
  /** UI 對應位置 — 幫 RD 對照畫面。 */
  uiAnchor: string;
}

export const GLOSSARY_SECTIONS: GlossarySectionMeta[] = [
  {
    id: 'manifest',
    title: '矛盾說明書 + 子需求 (SR)',
    blurb: '挑方向前的「閱讀背景」— 不是驗收條件。',
    uiAnchor: '對應每張方向卡頂端那段虛線框「矛盾說明書」。',
  },
  {
    id: 'resolution_status',
    title: '方向整體判定（5 種狀態）',
    blurb: 'AI 給這個方向「整體有沒有解掉矛盾」的審判。',
    uiAnchor: '對應方向卡標題列的彩色徽章：直接解決 / 部分解決 / 條件成立 / 未解到 / 資訊不足。',
  },
  {
    id: 'addresses_layer',
    title: '解到哪一層因果（4 種）',
    blurb: '這個方向動的是「根因 / 機制 / 症狀」哪一層？',
    uiAnchor: '對應方向卡標題列的「解根因 / 解機制 / 解症狀」徽章（在 5 色徽章旁邊）。',
  },
  {
    id: 'per_sr_verdict',
    title: '方向對單條 SR 的評語（6 種）',
    blurb: '方向展開後，對每條子需求的逐條短評。',
    uiAnchor: '展開方向後，每條 SR 列前面的小圓點 + 「本方案：直接解 / 要驗證...」那行。',
  },
  {
    id: 'score_columns',
    title: '4 個分數欄位是什麼意思',
    blurb: '工具支持、技術成熟度、實施容易度、解掉矛盾的程度。',
    uiAnchor: '展開方向後，最上方那一排 4 個分數格。',
  },
  {
    id: 'sort_filter',
    title: 'Sort / Filter 用法',
    blurb: '4 種排序 × 4 種篩選的差別與使用情境。',
    uiAnchor: '對應方向卡頂端的「排序」與「篩選」下拉。',
  },
  {
    id: 'severity',
    title: '矛盾嚴重度（4 種）',
    blurb: '致命 / 主要 / 次要 / 未知。',
    uiAnchor: '對應方向卡標題右上角的嚴重度徽章。',
  },
  {
    id: 'why_not_verdict',
    title: '為什麼這裡不是「驗收」',
    blurb: '單一方向解掉幾條 SR ≠ 矛盾被解。真正驗收在「跨矛盾整併」後的 Brief 任務檢核。',
    uiAnchor: '對應頁面下方「跨矛盾整併」按鈕產出的 Brief 任務檢核 (VerdictLite)。',
  },
];

// ---------------------------------------------------------------------------
// Helper — given a SortMode/FilterMode, fetch its description.
// ---------------------------------------------------------------------------
export function getSortDescription(mode: SortMode): string {
  return SORT_OPTIONS.find((o) => o.value === mode)?.description ?? '';
}

export function getFilterDescription(mode: FilterMode): string {
  return FILTER_OPTIONS.find((o) => o.value === mode)?.description ?? '';
}

// ---------------------------------------------------------------------------
// Helper — get the sort value from a DirectionScore object. Centralised
// here so the Glossary can show "this column drives this sort" without
// duplicating logic.
// ---------------------------------------------------------------------------
import type { DirectionScore } from '@/types/directedTriz';

export function getSortValue(score: DirectionScore | undefined, mode: SortMode): number {
  if (!score) return -Infinity;
  switch (mode) {
    case 'tool_support':
      return score.tool_support;
    case 'feasibility':
      return score.feasibility;
    case 'cost_difficulty':
      return score.cost_difficulty;
    case 'coverage':
      return score.coverage_score;
  }
}
