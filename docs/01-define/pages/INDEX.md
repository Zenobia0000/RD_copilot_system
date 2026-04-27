# Page Spec Index

> **本檔由各 page spec 的 frontmatter 聚合產出**。frontmatter 為 SSOT；本檔為導覽輔助，需與 frontmatter 同步。
> 修改 page spec 時：直接改該檔的 frontmatter；變更 IA 群組/編號等結構性異動時再回頭同步本檔。
>
> **格式規範**：見 [`_schema.md`](./_schema.md)。**新建 spec**：複製 [`_template.md`](./_template.md)。

---

## 1. 快速總覽

| 指標 | 數量 |
|:-----|:-----|
| Page spec 檔數 | 18 |
| 受保護路由 (`protected: true`) | 14 |
| 公開路由 (`protected: false`, `dev_only: false`) | 3（P01 / P02 / P18） |
| DEV-only 路由 (`dev_only: true`) | 1（P17） |
| 含 Gate 的頁 (`gate != null`) | 9（P04 overview + 8 個 D/X/V/P） |

---

## 2. Forward Mapping — IA → Spec

| id | route_path | page_name | page_type | phase | gate | spec | source |
|:---|:-----------|:----------|:----------|:------|:-----|:-----|:-------|
| P01 | `/auth` | Auth | auth | — | — | [`01_auth.md`](./01_auth.md) | `src/pages/Auth.tsx` |
| P02 | `/reset-password` | ResetPassword | auth | — | — | [`02_reset_password.md`](./02_reset_password.md) | `src/pages/ResetPassword.tsx` |
| P03 | `/projects` | ProjectList | list | — | — | [`03_project_list.md`](./03_project_list.md) | `src/pages/ProjectList.tsx` |
| P04 | `/projects/:id` | ProjectDashboard | dashboard | — | overview | [`04_project_dashboard.md`](./04_project_dashboard.md) | `src/pages/ProjectDashboard.tsx` |
| P05 | `/projects/:id/brief` | TaskDefinition | form | 1 | D1 | [`05_task_definition.md`](./05_task_definition.md) | `src/pages/TaskDefinition.tsx` |
| P06 | `/projects/:id/explore` | Explore | wizard | 1 | D2 | [`06_explore.md`](./06_explore.md) | `src/pages/Explore.tsx` |
| P07 | `/projects/:id/track` | Track | kanban | 2 | X1 | [`07_track.md`](./07_track.md) | `src/pages/Track.tsx` |
| P08 | `/projects/:id/create` | Create | wizard | 2 | X2 | [`08_create.md`](./08_create.md) | `src/pages/Create.tsx` |
| P09 | `/projects/:id/pre-cad` | PreCadReview | review | 2 | P | [`09_pre_cad_review.md`](./09_pre_cad_review.md) | `src/pages/PreCadReview.tsx` |
| P10 | `/projects/:id/cad` | CadInProgress | progress | 2.5 | — | [`10_cad_in_progress.md`](./10_cad_in_progress.md) | `src/pages/CadInProgress.tsx` |
| P11 | `/projects/:id/review` | DesignReview | review | 3 | V1 | [`11_design_review.md`](./11_design_review.md) | `src/pages/DesignReview.tsx` |
| P12 | `/projects/:id/decide` | DecisionRecord | form | 3 | V2 | [`12_decision_record.md`](./12_decision_record.md) | `src/pages/DecisionRecord.tsx` |
| P13 | `/projects/:id/feynman` | Feynman | detail | 3 | V4 | [`13_feynman.md`](./13_feynman.md) | `src/pages/Feynman.tsx` |
| P14 | `/knowledge-base`, `/knowledge-base/:slug` | KnowledgeBase | list-detail | — | — | [`14_knowledge_base.md`](./14_knowledge_base.md) | `src/pages/KnowledgeBase.tsx` |
| P15 | `/projects/:id/constraint-labels` | ConstraintLabelDictionary | utility | — | — | [`15_constraint_label_dictionary.md`](./15_constraint_label_dictionary.md) | `src/pages/ConstraintLabelDictionary.tsx` |
| P16 | `/settings` | Settings | form | — | — | [`16_settings.md`](./16_settings.md) | `src/pages/Settings.tsx` |
| P17 | `/dev/seed` | DevSeed | utility | — | — | [`17_dev_seed.md`](./17_dev_seed.md) | `src/pages/DevSeed.tsx` |
| P18 | `*` | NotFound | error | — | — | [`18_not_found.md`](./18_not_found.md) | `src/pages/NotFound.tsx` |

---

## 3. IA Group 分群視圖

### 3.1 `public` — 公開路由
| id | spec | route |
|:---|:-----|:------|
| P01 | `01_auth.md` | `/auth` |
| P02 | `02_reset_password.md` | `/reset-password` |

### 3.2 `portfolio` — 專案管理
| id | spec | route |
|:---|:-----|:------|
| P03 | `03_project_list.md` | `/projects` |
| P04 | `04_project_dashboard.md` | `/projects/:id` |

### 3.3 `phase1-define` — Phase 1 Define
| id | gate | spec |
|:---|:-----|:-----|
| P05 | D1 | `05_task_definition.md` |
| P06 | D2 | `06_explore.md` |

### 3.4 `phase2-diverge` — Phase 2 Diverge
| id | gate | spec |
|:---|:-----|:-----|
| P07 | X1 | `07_track.md` |
| P08 | X2 | `08_create.md` |
| P09 | P | `09_pre_cad_review.md` |

### 3.5 `phase3-converge` — Phase 3 Converge（含 CAD bridge）
| id | phase | gate | spec |
|:---|:------|:-----|:-----|
| P10 | 2.5 | — | `10_cad_in_progress.md` |
| P11 | 3 | V1 | `11_design_review.md` |
| P12 | 3 | V2 | `12_decision_record.md` |
| P13 | 3 | V4 | `13_feynman.md` |

### 3.6 `knowledge` — 知識與輔助工具
| id | spec |
|:---|:-----|
| P14 | `14_knowledge_base.md` |
| P15 | `15_constraint_label_dictionary.md` |

### 3.7 `system` — 系統設定與錯誤頁
| id | spec |
|:---|:-----|
| P16 | `16_settings.md` |
| P18 | `18_not_found.md` |

### 3.8 `dev` — 僅開發環境
| id | spec |
|:---|:-----|
| P17 | `17_dev_seed.md` |

---

## 4. Gate 覆蓋對照

| gate | 對應頁 | spec |
|:-----|:-------|:-----|
| `overview` | P04 ProjectDashboard | `04_project_dashboard.md` |
| `D1` | P05 TaskDefinition | `05_task_definition.md` |
| `D2` | P06 Explore | `06_explore.md` |
| `X1` | P07 Track | `07_track.md` |
| `X2` | P08 Create | `08_create.md` |
| `P` | P09 PreCadReview | `09_pre_cad_review.md` |
| `V1` | P11 DesignReview | `11_design_review.md` |
| `V2` | P12 DecisionRecord | `12_decision_record.md` |
| `V4` | P13 Feynman | `13_feynman.md` |

---

## 5. 依賴 DAG（`depends_on` 聚合）

```
P01 Auth ─┬─► P03 ProjectList ─► P04 Dashboard ─┬─► P05 Brief ─► P06 Explore ─► P07 Track ─► P08 Create
          │                                      │                                              │
          └─► P02 ResetPassword                   ├─► P15 ConstraintLabelDictionary             ▼
                                                  │                                       P09 PreCadReview
                                                  │                                              │
                                                  │                                              ▼
                                                  │                                       P10 CadInProgress
                                                  │                                              │
                                                  │                                              ▼
                                                  │                                       P11 DesignReview
                                                  │                                              │
                                                  │                                              ▼
                                                  │                                       P12 DecisionRecord
                                                  │                                              │
                                                  │                                              ▼
                                                  │                                       P13 Feynman
                                                  │
                                                  └─ P14 KnowledgeBase / P16 Settings / P17 DevSeed / P18 NotFound（無前置）
```

---

## 6. 關鍵互動路徑

> 跨頁 scenario 敘事與序列圖（待重建）。本節僅列 page-level 路徑骨架。

| Journey | 涉及 Spec |
|:--------|:----------|
| Forward TRIZ 解矛盾 | P01 → P03 → P04 → P08 |
| TRIZ 跨域去錨定具體化 | P04 → P08 → P07 |
| Pre-CAD Gate | P04 → P09 → P12 |
| 完整 8-Gate Happy Path | P01 → P03 → … → P13 |
| 知識庫查詢 | P14 |

---

## 7. 維護指引

- **新增頁面**：複製 [`_template.md`](./_template.md) → 改檔名為 `NN_<page_name>.md` → 填 frontmatter → 在本檔 §2 與對應 §3.x 群組新增列。
- **修改 IA group / phase / gate**：改 frontmatter 後同步本檔 §2、§3、§4。
- **改 route_path / page_name**：改 frontmatter + spec 內文 + `src/pages/*.tsx` + 本檔 §2。
- **取代舊 MAPPING.md**：本檔取代 `MAPPING.md` v3.x 的所有對照表功能；`MAPPING.md` 縮為指向本檔的 stub 以維持外部連結相容性。
