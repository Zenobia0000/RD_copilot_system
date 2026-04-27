# Page-Level Prompt: Feynman 內化與傳達

> Phase 3 Converge — AI 自動將決策記錄、實驗結果、矛盾解法等 6 類資產轉化為知識庫條目，實現組織學習自動化。此步驟為全自動（Fully Auto），使用者僅需審閱確認。
> **對應步驟**：V4（知識回寫）

---

## [CHANGELOG]

| 版本 | 日期 | 變更摘要 |
|:-----|:-----|:---------|
| v3.0 | 2026-04-27 | D/X/V 編號化：Step 3.3 → V4；Gate 8 → Gate V4；subtitle 對齊 "Phase 3: Converge > V4（知識回寫自動化）"；移除 AA/SCAMPER/strikethrough 噪音；對齊 code 6 種 asset type 與 hook 清單 |

---

## [WIREFRAME]

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase bar (emerald-500)                                          │
│  ← 返回  Feynman — 內化與傳達                                    │
│  Phase 3: Converge > V4（知識回寫自動化）                          │
├──────────────────────────────────────────────────────────────────┤
│  SectionIntro (6 類資產自動轉化說明)                               │
├──────────────────────────────────────────────────────────────────┤
│  Stats: [N 條目] [N 已寫入] [N 已審閱] [N/6 類資產]              │
├──────────────────────────────────────────────────────────────────┤
│  Asset Type Legend                                                 │
│  ● 決策記錄 (N)  ● 實驗結果 (N)  ● 矛盾解法 (N)                 │
│  ● 失效模式 (N)  ● 設計規則 (N)  ● 最佳實踐 (N)                 │
├──────────────────────────────────────────────────────────────────┤
│  自動化等級：Fully Auto — Knowledge Agent 執行                    │
├──────────────────────────────────────────────────────────────────┤
│  Knowledge Entries                                                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ [AI] [KE-001] [決策記錄] [已寫入]                            │ │
│  │ 磁力耦合傳動系統設計要點                                      │ │
│  │ (summary text)                                                │ │
│  │ 來源：...       [確認審閱] [查看知識庫]                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ... more entries ...                                              │
├──────────────────────────────────────────────────────────────────┤
│  [生成知識條目] (AiButton)                                        │
├──────────────────────────────────────────────────────────────────┤
│  KnowledgeRefsPanel                                                │
├──────────────────────────────────────────────────────────────────┤
│  Gate V4 完成檢查                                                  │
│  ☐ 至少 1 條知識條目已生成                                        │
│  ☐ 6 類資產皆已覆蓋                                               │
│  ☐ 所有條目已審閱                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## [DESIGN PRINCIPLES]

| 原則 | 說明 |
|:-----|:-----|
| 全自動 (Fully Auto) | AI 自動從決策記錄與實驗結果提取知識，寫入知識庫 |
| 6 類資產覆蓋 | 決策記錄 / 實驗結果 / 矛盾解法 / 失效模式 / 設計規則 / 最佳實踐 |
| 人類審閱確認 | 使用者僅需審閱 AI 生成的知識條目，不需手動撰寫 |
| 費曼學習法 | 將複雜知識轉化為可理解、可重用的知識庫條目 |

---

## [PAGE META]

- **page_name**: Feynman
- **route_path**: `/projects/:id/feynman`
- **page_type**: detail (knowledge writeback)
- **primary_goal**: AI 自動將專案決策與驗證成果轉化為 6 類知識資產，寫入組織知識庫
- **secondary_goal**: 使用者審閱確認知識條目品質，確保知識正確性
- **target_users**: RD 工程師
- **entry_point**: DecisionRecord 頁 Phase Gate V 通過後導航，或 Dashboard 直接進入
- **expected_time_on_page**: 10 ~ 30 分鐘

---

## [STRUCTURE: SECTIONS]

1. **Header**
   - section_type: navigation + status
   - section_purpose: 返回 Dashboard、頁面標題、subtitle "Phase 3: Converge > V4（知識回寫自動化）"
2. **SectionIntro**
   - section_type: context
   - section_purpose: 說明 6 類資產自動轉化用途
3. **Stats Bar**
   - section_type: summary
   - section_purpose: 條目總數、已寫入、已審閱、資產類型覆蓋率
4. **Asset Type Legend**
   - section_type: legend
   - section_purpose: 6 種資產類型 Badge + 各類計數
5. **Auto Badge**
   - section_type: info
   - section_purpose: 標示自動化等級 Fully Auto
6. **Knowledge Entries**
   - section_type: card-list
   - section_purpose: 知識條目清單，每條含類型、狀態、摘要、來源、操作按鈕
7. **Generate Button**
   - section_type: action
   - section_purpose: AI 生成新知識條目
8. **KnowledgeRefsPanel**
   - section_type: reference
   - section_purpose: 知識參考連結
9. **Gate V4**
   - section_type: gate-check
   - section_purpose: 知識回寫完成檢查

---

## [SECTION COMPONENT SPEC]

### Section: Header
- **layout**: flex items-center gap-3
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | PhaseBar | `<div>` | required | h-1 w-full rounded-full bg-emerald-500 |
  | BackButton | `<Button variant="ghost">` | required | ArrowLeft icon，onClick → `/projects/:id` |
  | Title | `<h1>` | required | "Feynman — 內化與傳達" + HelpTooltip |
  | Subtitle | `<p>` | required | "Phase 3: Converge > V4（知識回寫自動化）" |

### Section: Stats Bar
- **layout**: flex flex-wrap gap-3
- **elements**:
  | Element | Type | Description |
  |:--------|:-----|:------------|
  | TotalBadge | `<Badge>` primary | "{N} 條目" |
  | WrittenBadge | `<Badge>` secondary | "{N} 已寫入" |
  | ReviewedBadge | `<Badge>` green | "{N} 已審閱" |
  | CoverageBadge | `<Badge>` outline | "{N}/6 類資產" |

### Section: Asset Type Legend
- **layout**: flex flex-wrap gap-2
- **asset_types**:
  | Type Key | 標籤 | 顏色 |
  |:---------|:-----|:-----|
  | `decision` | 決策記錄 | `#3B82F6` (blue) |
  | `experiment` | 實驗結果 | `#10B981` (emerald) |
  | `contradiction` | 矛盾解法 | `#F59E0B` (amber) |
  | `failure_mode` | 失效模式 | `#EF4444` (red) |
  | `design_rule` | 設計規則 | `#8B5CF6` (violet) |
  | `best_practice` | 最佳實踐 | `#EC4899` (pink) |

### Section: Knowledge Entries
- **layout**: space-y-4, Card per entry
- **data_source**: `useKnowledgeEntries(id)` (live) with fallback to MOCK_ENTRIES (local)
- **entry_elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | AiBadge | `<Badge>` secondary | always | "AI" 標記 |
  | IdBadge | `<Badge>` outline mono | always | "KE-001" 格式 |
  | TypeBadge | `<Badge>` colored | always | 資產類型（依顏色表） |
  | StatusBadge | `<Badge>` | always | 已審閱 (green) / 已寫入 (primary) / 待處理 (muted) |
  | Title | `<h3>` | always | 知識條目標題 |
  | Summary | `<p>` | always | 知識摘要 |
  | Source | `<span>` | always | 來源說明 |
  | ReviewButton | `<Button>` outline | conditional | "確認審閱"（status !== 'reviewed' 時顯示） |
  | KbButton | `<Button>` ghost | always | "查看知識庫" → `/knowledge-base` |
- **entry_border**: reviewed = border-l-green-600, written = border-l-primary, pending = none

### Section: Generate Button
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | GenerateButton | `<AiButton>` | required | "生成知識條目"，呼叫 handleGenerate（mock: 2000ms delay） |

### Section: Gate V4
- **layout**: Card border-2 border-emerald-500 bg-emerald-50
- **gate_items**:
  | # | 檢查項目 | 判定邏輯 |
  |:--|:---------|:---------|
  | 1 | 至少 1 條知識條目已生成 | `entries.length > 0` |
  | 2 | 6 類資產皆已覆蓋 | `coveredAssetTypes >= 6` |
  | 3 | 所有條目已審閱 | `reviewedCount >= entries.length && entries.length > 0` |
- **pass_display**: Badge "完成" (bg-green-600)
- **fail_display**: Badge "待完成" (bg-red-600)

---

## [HOOKS]

| Hook | 來源 | 用途 |
|:-----|:-----|:-----|
| `useKnowledgeEntries` | `@/hooks/api/useKnowledge` | 載入知識條目（from Supabase） |
| `useUpdateKnowledgeEntry` | `@/hooks/api/useKnowledge` | 更新知識條目（標記已審閱） |

---

## [SHARED COMPONENTS]

| 元件 | 來源 | 用途 |
|:-----|:-----|:-----|
| `AiButton` | `@/components/ui/ai-button` | AI 操作按鈕（生成知識條目） |
| `HelpTooltip` | `@/components/ui/help-tooltip` | 說明提示 |
| `SectionIntro` | `@/components/ui/section-intro` | 區段說明文字 |
| `KnowledgeRefsPanel` | `@/components/create/KnowledgeRefsPanel` | 知識參考面板 |

---

## [TYPES]

| Type | 來源 | 說明 |
|:-----|:-----|:-----|
| `KnowledgeAssetType` | local (Feynman.tsx) | 6 種資產類型 union：`decision \| experiment \| contradiction \| failure_mode \| design_rule \| best_practice` |
| `KnowledgeEntry` | local (Feynman.tsx) | 知識條目（id, title, summary, source, assetType, status, createdAt） |

---

## [NAVIGATION]

| 方向 | 目標 | 觸發 |
|:-----|:-----|:-----|
| 返回 | `/projects/:id` | Header BackButton |
| 查看知識庫 | `/knowledge-base` | Entry "查看知識庫" 按鈕 |
