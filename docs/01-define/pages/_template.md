---
# === Identity ===
id: P00                              # IA identifier (P01-P18)
file_id: "00"                        # filename ordinal as 2-digit string
page_name: ExamplePage               # CamelCase, matches src/pages/*.tsx
route_path: /example/path            # React Router path
page_type: form                      # auth | list | dashboard | form | wizard | kanban | review | progress | detail | list-detail | utility | error

# === IA & Phase ===
phase: 1                             # null | 1 | 2 | 2.5 | 3
ia_group: phase1-define              # public | portfolio | phase1-define | phase2-diverge | phase3-converge | knowledge | system | dev
gate: D1                             # null | overview | D1 | D2 | X1 | X2 | P | V1 | V2 | V4
protected: true
dev_only: false

# === Source & Status ===
source_component: src/pages/ExamplePage.tsx
spec_version: 1.0
ia_version: 1.2
status: draft                        # draft | stable | deprecated
last_updated: 2026-04-27

# === Cross-links ===
api_resources: []                    # logical resource keys, link into 02-design/E5--api-design-specification.md
modules: []                          # backend modules, link into 02-design/specs/modules/*
depends_on: []                       # upstream P-ids
absorbed_specs: []                   # other spec paths absorbed into this page

# === Optional sections ===
optional_sections: []                # subset of: wireframe, design_principles, conditional_rendering
---

# Page-Level Prompt: ExamplePage 範例頁

> 1-2 句頁面用途陳述。

---

## [PAGE META]

> 結構化欄位（route_path/page_type/etc.）已上移到 frontmatter，本區只保留敘述性欄位。

- **primary_goal**: 主要目標一句話
- **secondary_goal**: 次要目標一句話
- **target_users**: 使用者描述
- **entry_point**: 從哪些頁面/觸發點進入本頁
- **expected_time_on_page**: 預期停留時間區間

---

## [STRUCTURE: SECTIONS]

1. **SectionA**
   - section_type: ...
   - section_purpose: ...
2. **SectionB**
   - section_type: ...
   - section_purpose: ...

---

## [SECTION COMPONENT SPEC]

### Section: SectionA
- **layout**: 描述 layout（grid/flex/etc.）
- **elements**:
  | Element | Type | Required | Description |
  |:--------|:-----|:---------|:------------|
  | ElementA1 | Input | required | ... |
- **states**: default / loading / error / success
- **copy_constraints**: 文案限制

### Section: SectionB
（同上格式）

---

## [INTERACTION & STATE FLOW]

### 主要互動流程
1. ...
2. ...

### RWD 行為差異
| Breakpoint | Layout | 差異 |
|:-----------|:-------|:-----|
| Desktop (≥1024px) | ... | ... |
| Tablet (768-1023px) | ... | ... |
| Mobile (<768px) | ... | ... |

---

## [DATA & API]

- **uses_api**: true / false
- **endpoints**:
  | Action | API Call | Payload |
  |:-------|:---------|:--------|
  | ... | ... | ... |
- **error_cases**:
  - ...

---

## [ACCEPTANCE CRITERIA]

- [ ] 條件 1
- [ ] 條件 2

---

<!--
=== 以下為選填段落（依 frontmatter optional_sections 宣告） ===
新建檔案禁止使用 [CHANGELOG] 段落 — 版本演進改用 frontmatter spec_version + git log。
既有檔案的 [CHANGELOG] 凍結為歷史紀錄，不再追加。
-->

<!-- 以下三段為選填範本，使用時請取消註解並在 frontmatter optional_sections 宣告 -->

<!--
## [WIREFRAME]

> 何時用：頁面結構複雜需 ASCII / Mermaid 線稿輔助理解時。
> frontmatter 須宣告 `optional_sections: [wireframe]`。

```
┌──────────────────────────┐
│  Header                  │
├──────────────────────────┤
│  Body                    │
└──────────────────────────┘
```
-->

<!--
## [DESIGN PRINCIPLES]

> 何時用：頁面有特定設計鐵律需明列時。
> frontmatter 須宣告 `optional_sections: [design_principles]`。

| 原則 | 說明 |
|:-----|:-----|
| 原則 1 | ... |
-->

<!--
## [CONDITIONAL RENDERING]

> 何時用：頁面依資料狀態切換多種渲染模式時（如 06_explore Entry Grading）。
> frontmatter 須宣告 `optional_sections: [conditional_rendering]`。

### 觸發條件
- 條件 A → 模式 1
- 條件 B → 模式 2

### 渲染路由
| 模式 | 渲染策略 | 說明 |
|:-----|:---------|:-----|
| 模式 1 | ... | ... |
-->
