# Page-Level Prompt: Feynman 費曼學習 / 知識內化

> AI 自動將專案中的決策記錄、實驗結果、矛盾解法等 6 類知識資產轉化為可重複使用的知識庫條目，實現組織學習的自動化。

---

## [PAGE META]

- **page_name**: Feynman
- **route_path**: `/projects/:id/feynman`
- **page_type**: phase-step (Phase 3 — Converge > Step 3.3)
- **primary_goal**: 自動化知識回寫，將專案決策與實驗成果轉化為知識庫條目
- **secondary_goal**: 讓使用者審閱並確認 AI 生成的知識條目，確保品質
- **target_users**: RD 工程師、專案負責人
- **entry_point**: 專案 Dashboard 的 Step 3.3 卡片、或上一步驟完成後自動導向
- **expected_time_on_page**: 3 ~ 10 分鐘

---

## [STRUCTURE: SECTIONS]

1. **Header**
  - section_type: navigation + branding
  - section_purpose: 顯示返回按鈕、頁面標題、階段描述與 HelpTooltip
2. **SectionIntro**
  - section_type: guidance
  - section_purpose: 說明此步驟的功能與使用者僅需審閱確認
3. **StatsBadges**
  - section_type: summary
  - section_purpose: 顯示條目數、已寫入數、已審閱數、資產類型覆蓋率
4. **AssetTypeLegend**
  - section_type: legend
  - section_purpose: 顯示 6 類資產類型及各自條目數量（帶色彩標示）
5. **AutoBadge**
  - section_type: info
  - section_purpose: 標示此步驟的自動化等級為 Fully Auto
6. **KnowledgeEntriesList**
  - section_type: content-list
  - section_purpose: 列出所有知識條目卡片，支援審閱與導航操作
7. **GenerateButton**
  - section_type: action
  - section_purpose: 觸發 AI 生成新知識條目
8. **KnowledgeRefsPanel**
  - section_type: enhancement
  - section_purpose: 知識增強面板，顯示相關知識參考（WBS 3.4.2）
9. **GateCheck**
  - section_type: gate
  - section_purpose: Gate 8 完成檢查，顯示三項通過條件與整體狀態

---

## [SECTION COMPONENT SPEC]

### Section: Header

- **layout**: 頂部 emerald-500 色條 (h-1 rounded-full) + flex items-center gap-3
- **elements**:

  | Element     | Type               | Required | Description                                                           |
  | ----------- | ------------------ | -------- | --------------------------------------------------------------------- |
  | ColorBar    | `<div>`            | required | h-1 w-full rounded-full bg-emerald-500，頂部色條                           |
  | BackButton  | Button (ghost, sm) | required | ArrowLeft icon + "返回"，導航至 `/projects/:id`                             |
  | Title       | `<h1>`             | required | "Feynman — 內化與傳達"，text-2xl font-bold tracking-tight                   |
  | HelpTooltip | HelpTooltip        | required | 說明費曼學習法與 Fully Auto 自動化等級                                             |
  | PhaseLabel  | `<p>`              | required | "Phase 3: Converge > Step 3.3（知識回寫自動化）"，text-sm text-muted-foreground |

- **states**: 無特殊狀態
- **copy_constraints**: 標題固定，Phase 描述需與 WBS 一致

### Section: SectionIntro

- **layout**: SectionIntro 元件
- **elements**:

  | Element   | Type         | Required | Description      |
  | --------- | ------------ | -------- | ---------------- |
  | IntroText | SectionIntro | required | 說明 6 類資產的自動化轉化流程 |

- **states**: 無
- **copy_constraints**: 需列出 6 類資產名稱：決策記錄、驗證實驗結果、矛盾解法、失效模式、設計規則、最佳實踐

### Section: StatsBadges

- **layout**: flex flex-wrap gap-3
- **elements**:

  | Element       | Type              | Required | Description                               |
  | ------------- | ----------------- | -------- | ----------------------------------------- |
  | EntryCount    | Badge (primary)   | required | "{n} 條目"，總條目數                             |
  | WrittenCount  | Badge (secondary) | required | "{n} 已寫入"，status 為 written 或 reviewed 的數量 |
  | ReviewedCount | Badge (green-600) | required | "{n} 已審閱"，status 為 reviewed 的數量           |
  | AssetCoverage | Badge (outline)   | required | "{n}/{6} 類資產"，已覆蓋的資產類型數                   |

- **states**: 數值動態計算，隨條目狀態變更即時更新
- **copy_constraints**: 無

### Section: AssetTypeLegend

- **layout**: flex flex-wrap gap-2
- **elements**:

  | Element    | Type               | Required | Description              |
  | ---------- | ------------------ | -------- | ------------------------ |
  | AssetBadge | Badge (outline) x6 | required | 每類資產一個，含色彩圓點 + 中文標籤 + 計數 |

- **asset_types**:

  | Type          | Label | Color   |
  | ------------- | ----- | ------- |
  | decision      | 決策記錄  | #3B82F6 |
  | experiment    | 實驗結果  | #10B981 |
  | contradiction | 矛盾解法  | #F59E0B |
  | failure_mode  | 失效模式  | #EF4444 |
  | design_rule   | 設計規則  | #8B5CF6 |
  | best_practice | 最佳實踐  | #EC4899 |

- **states**: 計數動態計算
- **copy_constraints**: 無

### Section: AutoBadge

- **layout**: Card (border-dashed bg-muted/30) > CardContent (p-3 flex items-center gap-3)
- **elements**:

  | Element     | Type      | Required | Description                                    |
  | ----------- | --------- | -------- | ---------------------------------------------- |
  | Icon        | RefreshCw | required | h-4 w-4 shrink-0                               |
  | LevelLabel  | `<span>`  | required | "自動化等級：Fully Auto"，font-medium text-foreground |
  | Description | `<span>`  | required | 說明 AI 自動提取知識並寫入知識庫，由 Knowledge Agent 執行        |

- **states**: 無
- **copy_constraints**: 無

### Section: KnowledgeEntriesList

- **layout**: space-y-4，每張條目為 Card > CardContent (p-4 space-y-3)
- **elements**:

  | Element      | Type                 | Required | Description                                                    |
  | ------------ | -------------------- | -------- | -------------------------------------------------------------- |
  | AIBadge      | Badge (secondary)    | required | "AI"，text-[10px]，標示條目為 AI 生成                                   |
  | IdBadge      | Badge (outline)      | required | "KE-{序號}"，font-mono text-[10px]                                |
  | TypeBadge    | Badge                | required | 資產類型標籤，背景色對應 ASSET_TYPE_CONFIG                                 |
  | StatusBadge  | Badge                | required | "已審閱" (green-600) / "已寫入" (primary) / "待處理" (muted-foreground) |
  | Title        | `<h3>`               | required | text-sm font-semibold                                          |
  | Summary      | `<p>`                | required | text-sm text-muted-foreground leading-relaxed                  |
  | Source       | `<span>`             | required | "來源：{source}"，text-[10px] text-muted-foreground                |
  | ReviewButton | Button (outline, sm) | optional | 僅非 reviewed 狀態顯示，CheckCircle icon + "確認審閱"                     |
  | ViewKBButton | Button (ghost, sm)   | required | BookOpen icon + "查看知識庫"，導航至 `/knowledge-base`                  |

- **states**:
  - reviewed: Card 左邊框 3px green-600
  - written: Card 左邊框 3px primary
  - pending: 無左邊框特殊樣式
- **copy_constraints**: 無

### Section: GenerateButton

- **layout**: flex flex-wrap gap-3
- **elements**:

  | Element     | Type     | Required | Description                     |
  | ----------- | -------- | -------- | ------------------------------- |
  | GenerateBtn | AiButton | required | "生成知識條目"，loading={isGenerating} |

- **states**:
  - default: 可點擊
  - loading: isGenerating=true，顯示載入動畫，模擬 2 秒延遲後新增條目
- **copy_constraints**: 無

### Section: KnowledgeRefsPanel

- **layout**: KnowledgeRefsPanel 元件
- **elements**:

  | Element   | Type               | Required | Description                                 |
  | --------- | ------------------ | -------- | ------------------------------------------- |
  | RefsPanel | KnowledgeRefsPanel | required | refs={mockPageKnowledgeRefs.feynman}，知識增強面板 |

- **states**: 無
- **copy_constraints**: 無

### Section: GateCheck

- **layout**: Separator + Card (border-2 border-emerald-500 bg-emerald-50) > CardContent (p-4 space-y-3)
- **elements**:

  | Element     | Type                 | Required | Description                        |
  | ----------- | -------------------- | -------- | ---------------------------------- |
  | GateIcon    | BookOpen             | required | h-5 w-5 text-emerald-500           |
  | GateTitle   | `<h3>`               | required | "Step 3.3 / Gate 8 完成檢查"           |
  | StatusBadge | Badge                | required | "完成" (green-600) 或 "待完成" (red-600) |
  | Criteria1   | CheckCircle / Circle | required | "至少 1 條知識條目已生成"                    |
  | Criteria2   | CheckCircle / Circle | required | "6 類資產皆已覆蓋 ({n}/{6})"              |
  | Criteria3   | CheckCircle / Circle | required | "所有條目已審閱 ({n}/{total})"            |

- **states**:
  - 完成: 三項條件皆滿足，Badge 為 green-600
  - 待完成: 任一條件未滿足，Badge 為 red-600
  - 每個條件獨立顯示 CheckCircle (green) 或空心圓
- **copy_constraints**: 無

---

## [INTERACTION & STATE FLOW]

### 主要互動流程

1. 使用者從專案 Dashboard 進入 `/projects/:id/feynman`
2. 頁面載入時呼叫 `useKnowledgeEntries(id)` 從 Supabase 取得知識條目
3. 若 Supabase 有資料 → 使用 livePageEntries；否則 → 使用 MOCK_ENTRIES 作為初始種子
4. 使用者瀏覽各條目卡片，檢視 AI 生成的知識摘要
5. 對尚未審閱的條目點擊「確認審閱」→ 呼叫 `useUpdateKnowledgeEntry` 或更新 localEntries → toast.success "已標記為已審閱"
6. 點擊「生成知識條目」→ isGenerating=true → 模擬 2 秒 → 新增一筆 pending 條目 → toast.success "AI 已生成新知識條目"
7. 點擊「查看知識庫」→ 導航至 `/knowledge-base`
8. Gate 8 檢查即時更新：三項條件全部達成時顯示「完成」

### RWD 行為差異


| Breakpoint            | Layout               | 差異                                |
| --------------------- | -------------------- | --------------------------------- |
| Desktop (>= 1024px)   | page-shell-narrow，單欄 | Stats badges 單行排列                 |
| Tablet (768 ~ 1023px) | 同 Desktop            | badges 可能換行                       |
| Mobile (< 768px)      | 同 Desktop            | badges 與 legend 自動換行，flex-wrap 適應 |


---

## [DATA & API]

- **uses_api**: true
- **endpoints**:

  | Action | API Call                         | Payload / Params                                                            |
  | ------ | -------------------------------- | --------------------------------------------------------------------------- |
  | 取得知識條目 | `useKnowledgeEntries(projectId)` | 從 Supabase 查詢，回傳 `{ id, title, content, assetType, reviewed, createdAt }[]` |
  | 更新知識條目 | `useUpdateKnowledgeEntry()`      | `{ id: string, reviewed: boolean }`                                         |

- **fallback**: 若 Supabase 無資料或載入中，使用 MOCK_ENTRIES（6 筆種子資料）
- **error_cases**:
  - Supabase 查詢失敗 → 自動降級至 MOCK_ENTRIES
  - 更新條目失敗 → updateEntry mutation 的 onError 處理
  - 網路異常 → Skeleton 載入狀態持續顯示

---

## [ACCEPTANCE CRITERIA]

- 頁面頂部顯示 emerald 色條與「返回」按鈕，點擊可回到專案 Dashboard
- 標題 "Feynman — 內化與傳達" 旁有 HelpTooltip 說明費曼學習法
- SectionIntro 顯示 6 類資產的自動化說明
- Stats badges 正確顯示條目數、已寫入數、已審閱數、資產覆蓋率
- Asset type legend 顯示 6 種資產類型，各自帶對應顏色與計數
- Fully Auto badge 正確顯示自動化等級說明
- 知識條目卡片顯示 AI badge、編號、類型 badge、狀態 badge
- reviewed 條目左邊框為 green-600，written 為 primary，pending 無特殊邊框
- 非 reviewed 條目顯示「確認審閱」按鈕，點擊後呼叫 API 並 toast 成功
- 每張卡片的「查看知識庫」按鈕可導航至 `/knowledge-base`
- 「生成知識條目」按鈕點擊後顯示載入動畫，2 秒後新增條目並 toast
- KnowledgeRefsPanel 正確渲染知識增強面板
- Gate 8 三項條件即時計算並以 CheckCircle 或空心圓顯示
- Gate 8 整體狀態在三項皆滿足時顯示「完成」綠色 badge，否則顯示「待完成」紅色 badge
- 載入中顯示 Skeleton 佔位符（標題 + 3 張卡片）
- Supabase 無資料時自動降級至 MOCK_ENTRIES

