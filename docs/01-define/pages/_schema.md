# Page Spec Frontmatter Schema

> 本檔定義 `docs/01-define/pages/*.md` 每份 page spec 必備的 YAML frontmatter 結構。
> **規範對象**：18 份 IA page spec（`01_auth.md` … `18_not_found.md`）。
> **SSOT 原則**：結構化 metadata 一律寫在 frontmatter，**不**在 `[PAGE META]` 區塊重複。`INDEX.md` 由 frontmatter 聚合產出。

---

## 1. 完整欄位定義

```yaml
---
# === Identity ===
id: P05                              # IA identifier，對應 MAPPING §2 的 P01-P18
file_id: "05"                        # 檔名前綴 ordinal（兩位字串，與 NN_ 前綴一致）
page_name: TaskDefinition            # CamelCase，對應 src/pages/*.tsx 元件名
route_path: /projects/:id/brief      # React Router 路徑
page_type: form                      # 見 §2.1 enum

# === IA & Phase ===
phase: 1                             # 見 §2.2 enum
ia_group: phase1-define              # 見 §2.3 enum
gate: D1                             # 見 §2.4 enum (本頁退出條件對應的 gate code)
protected: true                      # ProtectedRoute 包覆 → true；Public route → false
dev_only: false                      # DEV-only 路由（目前只有 17_dev_seed=true）

# === Source & Status ===
source_component: src/pages/TaskDefinition.tsx  # 對應 React 元件路徑
spec_version: 1.3                    # 本檔規格版本（沿用既有 CHANGELOG 表的最新版號；無 CHANGELOG 者填 1.0）
ia_version: 1.2                      # 本 spec 對齊的 IA 版本（從 MAPPING.md 讀）
status: stable                       # 見 §2.5 enum
last_updated: 2026-04-27             # ISO date，最後修訂日

# === Cross-links ===
api_resources: [brief]               # 邏輯資源 key 陣列，連向 docs/02-design/E5--api-design-specification.md §2
modules: [analyst]                   # 後端模組陣列，連向 docs/02-design/specs/modules/*
depends_on: [P03]                    # 上游頁面 P-id 陣列（如本頁需先完成 P03 才能進）；無則 []
absorbed_specs: []                   # 該頁吸收的其他 spec 路徑陣列（目前僅 08_create 有值）

# === Optional sections this file uses ===
optional_sections: []                # 見 §2.6 enum；本檔實際使用的選填段落（驅動 template 檢查）
---
```

---

## 2. Enum 定義

### 2.1 `page_type`

| 值 | 說明 | 對應檔 |
|:---|:-----|:-------|
| `auth` | 認證頁（登入/註冊/重設） | 01, 02 |
| `list` | 清單頁 | 03 |
| `dashboard` | 儀表板 | 04 |
| `form` | 表單頁 | 05, 12, 16 |
| `wizard` | 多步驟精靈 | 06, 08 |
| `kanban` | 看板 | 07 |
| `review` | 審查頁 | 09, 11 |
| `progress` | 進度監控 | 10 |
| `detail` | 詳情頁 | 13 |
| `list-detail` | 清單+詳情雙模式 | 14 |
| `utility` | 輔助工具 | 15, 17 |
| `error` | 錯誤頁 | 18 |

### 2.2 `phase`

| 值 | 說明 |
|:---|:-----|
| `null` | 不屬於 RD 流程 phase（auth/system/error 等） |
| `1` | Phase 1 Define |
| `2` | Phase 2 Diverge |
| `2.5` | Phase 2.5 CAD bridge（10_cad_in_progress 專用） |
| `3` | Phase 3 Converge |

### 2.3 `ia_group`

| 值 | 說明 | 對應 MAPPING §2 |
|:---|:-----|:-----------------|
| `public` | 公開路由（未登入可訪） | §2.1 |
| `portfolio` | 專案管理入口 | §2.2 |
| `phase1-define` | Phase 1 Define | §2.3 |
| `phase2-diverge` | Phase 2 Diverge | §2.4 |
| `phase3-converge` | Phase 3 Converge（含 CAD bridge） | §2.5 |
| `knowledge` | 知識與輔助工具 | §2.6 |
| `system` | 系統設定與錯誤頁 | §2.7（含 18_not_found） |
| `dev` | 僅開發環境 | §2.7（17_dev_seed） |

### 2.4 `gate`

| 值 | 說明 | 對應檔 |
|:---|:-----|:-------|
| `null` | 本頁無 gate | auth/portfolio/utility/system/error |
| `overview` | Dashboard 總覽（非實際 gate，標記 monitoring 角色） | 04 |
| `D1` | Phase 1 Define Gate 1 | 05 |
| `D2` | Phase 1 Define Gate 2 | 06 |
| `X1` | Phase 2 Diverge Gate 1 | 07 |
| `X2` | Phase 2 Diverge Gate 2 | 08 |
| `P` | Pre-CAD Gate | 09 |
| `V1` | Phase 3 Converge Gate 1 | 11 |
| `V2` | Phase 3 Converge Gate 2 | 12 |
| `V4` | Phase 3 Converge Gate 4 | 13 |

> 註：D/X/V 編碼為內部 gate code，IA 上的 P 編號（P01-P18）與 gate 是不同維度，分別放在 `id` 與 `gate` 欄位。

### 2.5 `status`

| 值 | 說明 |
|:---|:-----|
| `draft` | 設計中，可能尚未實作 |
| `stable` | 規格穩定，已或將實作 |
| `deprecated` | 規格廢棄，僅保留歷史 |

### 2.6 `optional_sections`

宣告本檔實際使用的選填段落。可填值：

| 值 | 對應段落 | 何時使用 |
|:---|:---------|:---------|
| `wireframe` | `[WIREFRAME]` | 需要 ASCII / Mermaid 線稿者（08 用） |
| `design_principles` | `[DESIGN PRINCIPLES]` | 需要表列設計原則者（08 用） |
| `conditional_rendering` | `[CONDITIONAL RENDERING]` | 同頁面有多模式渲染（06 Entry Grading 用） |
| `changelog` | `[CHANGELOG]` | **僅既有檔案保留歷史用**；新建檔案禁止填此值 |

---

## 3. 從現有 PAGE META + MAPPING.md 推 frontmatter 對應表

| Frontmatter 欄位 | 來源 | 推導規則 |
|:-----------------|:-----|:---------|
| `id` | `MAPPING.md §2`「IA #」欄 | 直取 |
| `file_id` | 檔名前綴 | `01_auth.md` → `"01"` |
| `page_name` | `[PAGE META] page_name` | 直取 |
| `route_path` | `[PAGE META] route_path` | 直取 |
| `page_type` | `MAPPING.md §3`「頁面類型」欄 | 對齊 §2.1 enum；不一致時以 §2.1 為準 |
| `phase` | `MAPPING.md §2`「Phase」欄 | `1/2/2.5/3` 數字直取；`—` → `null` |
| `ia_group` | 依 `MAPPING.md §2` 子節（§2.1-§2.7）對應 §2.3 enum |
| `gate` | `MAPPING.md §3`「Gate 覆蓋」欄 | 對齊 §2.4 enum；無 → `null` |
| `protected` | `MAPPING.md §1`「受保護路由」 | 14 頁 protected:true，3 頁 false（auth/reset/notfound），1 頁 dev-only（DEV 環境視為 dev） |
| `dev_only` | 同上 | 僅 17_dev_seed 為 true |
| `source_component` | `MAPPING.md §2`「Source」欄 | 直取 |
| `spec_version` | 既有 `[CHANGELOG]` 表最後一列「版本」欄 | 無 CHANGELOG 表者填 `1.0` |
| `ia_version` | `MAPPING.md` 標頭「對應 IA 版本」 | 目前所有 spec 統一填 `1.2` |
| `status` | 預設 `stable` | 全 18 份目前皆為 stable |
| `last_updated` | 既有 CHANGELOG 最後一列日期 / 檔案頂部「最後更新」 | 無則填 spec 最後 git mtime |
| `api_resources` | spec `[DATA & API]` 區塊 | 抽 endpoint 資源名（如 `/projects/:id/brief` → `brief`） |
| `modules` | spec `[DATA & API]` 區塊 | 抽前端 hook 涉及的後端模組（如 `useBrief` → `analyst`） |
| `depends_on` | `[PAGE META] entry_point` 描述 | 解析「從 X 頁進入」對應的 P-id |
| `absorbed_specs` | 檔內註明「合併自...」字樣 | 目前僅 08_create 一筆 |
| `optional_sections` | 該檔實際存在的選填段落 | 掃 `## [WIREFRAME]` 等標題 |

---

## 4. 驗證規則（人工 review 用）

對任一 page spec 檔，下列條件需同時成立：

1. 第一行為 `---`，frontmatter 區塊在第二行起。
2. 必填欄位齊全：`id`, `file_id`, `page_name`, `route_path`, `page_type`, `phase`, `ia_group`, `gate`, `protected`, `dev_only`, `source_component`, `spec_version`, `ia_version`, `status`, `last_updated`, `api_resources`, `modules`, `depends_on`, `absorbed_specs`, `optional_sections`。
3. 所有 enum 欄位的值落在 §2 列舉內。
4. `id` 與 `file_id` 一致（如 `id: P05` 對應 `file_id: "05"`）。
5. `page_type` 值與 `MAPPING.md §3` 該列的「頁面類型」一致（容許微調，但需在本檔 §2.1 enum 內）。
6. `optional_sections` 所列每個值都對應檔內存在的段落標題；反之，檔內出現的選填段落都列在此欄位中。
7. `[PAGE META]` 區塊**不再包含**結構化欄位（`route_path` / `page_type` / `target_users` 等）；只保留敘述性欄位（`primary_goal` / `secondary_goal` / `entry_point` / `expected_time_on_page`）。

---

## 5. 與其他 SSOT 的關係

| Frontmatter 欄位 | SSOT 位置 | 本欄位角色 |
|:-----------------|:----------|:-----------|
| `id`, `route_path` | `MAPPING.md` / `02-design/E5x--frontend-information-architecture.md` | 鏡像（讓本檔可獨立被機器讀） |
| `api_resources` | `02-design/E5--api-design-specification.md` | 反向索引 |
| `source_component` | `src/pages/*.tsx` 實際存在 | 鏡像（git mv 時需同步） |
| `spec_version` | git history + 本檔 frontmatter | **取代** 過往 `[CHANGELOG]` 區塊的 SSOT 角色 |

