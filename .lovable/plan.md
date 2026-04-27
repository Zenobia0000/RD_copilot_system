

## 子系統定義：RD + AI 混合模式

### 問題
目前子系統定義完全由 AI 建議，RD 只能勾選確認，等同剝奪了工程師的設計定義權。實際產品開發中，資深 RD 往往在專案初期就對系統架構有明確想法。

### 設計理念

將子系統來源分為三類，以不同 Badge 標示：

| 來源 | Badge | 說明 |
|------|-------|------|
| RD 手動定義 | `RD` (藍色) | 工程師自行新增的子系統 |
| AI 建議 | `AI` (灰色) | AI 根據矛盾分析自動建議 |
| RD 編輯過的 AI 建議 | `AI+RD` (紫色) | AI 建議經 RD 修改名稱/原因/介面後 |

### UI 變更

#### 1. 頂部新增「手動新增子系統」入口

在 AI 摘要卡片上方加一個按鈕列：
- 「+ 新增子系統」按鈕 -- 點擊後展開一個內嵌表單（非 Modal），包含：
  - 名稱（Input，必填）
  - 原因/職責描述（Textarea）
  - 關聯矛盾（多選 Checkbox，從 MOCK_MISSION.contradictions 列出）
  - 介面描述（可選，逗號分隔或 tag input）
  - 「確認新增」/「取消」按鈕
- 新增的子系統自動標記 `source: "rd"`、`confirmed: true`

#### 2. 每個子系統卡片/方塊支援編輯

- Block Diagram 與 List 兩種視圖的每個子系統方塊，右上角加一個「編輯」小圖標按鈕（Pencil icon）
- 點擊後該方塊就地展開為可編輯狀態（inline edit），可修改名稱、原因、關聯矛盾、介面
- 儲存後，若原本是 AI 建議 (`source: "ai"`)，自動變成 `source: "ai_edited"`
- RD 自己新增的 (`source: "rd"`) 編輯後仍保持 `source: "rd"`

#### 3. AI 摘要卡片調整

原本的 AI 摘要改為顯示混合來源統計：
- 「本專案共 N 個子系統：M 個 RD 定義、K 個 AI 建議、J 個 AI+RD 混合」
- 若 RD 尚未新增任何子系統，顯示引導提示：「建議 RD 先定義已知的核心子系統，AI 將補充可能遺漏的部分」

#### 4. Block Diagram 視覺區分

在 `SubsystemBlockDiagram` 中，根據 `source` 顯示不同視覺風格：
- RD 定義：左邊框加藍色色條（`border-l-4 border-l-blue-500`）
- AI 建議：左邊框加灰色色條
- AI+RD：左邊框加紫色色條

### 技術細節

#### 型別擴充 (`src/types/create.ts`)

```typescript
export type SubsystemSource = 'rd' | 'ai' | 'ai_edited';

export interface Subsystem {
  id: string;
  name: string;
  reason: string;
  relatedContradictions: string[];
  confirmed: boolean;
  parentId?: string | null;
  interfaces?: string[];
  source: SubsystemSource;  // 新增
}
```

#### Mock 資料更新 (`src/data/mockCreate.ts`)

現有子系統加上 `source: "ai"`。

#### SubsystemBlockDiagram 修改 (`src/components/create/SubsystemBlockDiagram.tsx`)

- Props 新增 `onEdit?: (id: string) => void`
- 每個方塊內加來源 Badge（RD/AI/AI+RD）及編輯按鈕
- 根據 `source` 設定左邊框顏色

#### Create.tsx 修改 (`src/pages/Create.tsx`)

- `renderSubsystem()` 頂部加「+ 新增子系統」按鈕與內嵌表單
- 新增 `addSubsystem(data)` 函式，生成 `source: "rd"` 的子系統
- 新增 `editSubsystem(id, data)` 函式，若原 source 為 ai 則改為 ai_edited
- 新增 `deleteSubsystem(id)` 函式（僅允許刪除 RD 定義的）
- 新增 `editingSubsystemId` state 控制 inline 編輯
- 新增 `showAddForm` state 控制新增表單展開
- AI 摘要卡片改為顯示來源統計

### 檔案變更清單

| 檔案 | 動作 |
|------|------|
| `src/types/create.ts` | 新增 `SubsystemSource` 型別，`Subsystem` 加 `source` 欄位 |
| `src/data/mockCreate.ts` | 現有子系統加 `source: "ai"` |
| `src/components/create/SubsystemBlockDiagram.tsx` | 加來源 Badge、編輯按鈕、左邊框色條 |
| `src/pages/Create.tsx` | 加新增表單、inline 編輯、來源統計、刪除功能 |

