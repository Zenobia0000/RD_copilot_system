# WBS：Mock Data → Live API 遷移開發計畫

**目標**：將所有 16 個 mock data 檔案替換為 Supabase 即時 API，實現完整的 CRUD 資料流。

**最後更新**：2026-04-07
**整體進度**：~75% 完成（Sprint 0–3 已落地，Sprint 4 知識管理大致完成但 7 個 mock 檔尚有殘留 import）

### 進度速覽

| Sprint | 狀態 | 備註 |
|--------|------|------|
| Sprint 0 基礎建設 | ✅ 完成 | 31 表 + RLS + types + react-query 結構 |
| Sprint 1 專案 + Step 1 | ✅ 完成 | Projects/Brief/Constraints/KPIs/Socratic/Contradictions/Assumptions/CLD 全部 live |
| Sprint 2 Step 2 解方探索 | ✅ 完成 | Anti-Anchor/TRIZ(含 Su-Field)/Subsystems/SCAMPER/Alternatives/ConceptRoutes/CompatPairs/Solutions/PreCAD 全部 live；Track 假設新增/刪除已寫入 DB |
| Sprint 3 Step 3 審查決策 | ✅ 完成 | Evidence Matrix / Risks / Experiments / Decision / WANT / AC / Signatures / Actions / Export 全部 live |
| Sprint 4 知識 + 收尾 | 🟡 進行中 | Feynman/KnowledgeArticles hooks live；7 個 mock 檔仍存在於 `src/data/`（含部分 import）|

---

## §1 現況盤點

### 1.1 頁面 × Mock Data × API 對照表

| # | 頁面 | 路由 | 設計階段 | Mock 檔案 | 現有 API | 需新建 API |
|---|------|------|---------|-----------|---------|-----------|
| 1 | ProjectList | `/projects` | — | mockProjects | 無 | CRUD projects |
| 2 | ProjectDashboard | `/projects/:id` | — | mockProjects, mockDashboard, mockNavCards | 無 | R project detail, R dashboard stats |
| 3 | TaskDefinition | `/projects/:id/brief` | Step 1.1 | mockTaskDefinition, mockExtraction | 無 | CRUD brief/constraints/KPIs, AI extraction |
| 4 | Explore | `/projects/:id/explore` | Step 1.2–1.3 | mockExplore | 無 | CRUD socratic Q&A, contradictions, CLD |
| 5 | AssumptionLedger | `/projects/:id/assumptions` | Step 1.2 | mockAssumptions | 無 | CRUD assumptions, CLD, linked contradictions |
| 6 | ContradictionID | `/projects/:id/contradictions` | Step 1.3 | mockContradictions, trizParameters | 無 | CRUD contradictions |
| 7 | Track | `/projects/:id/track` | Step 2.1 | mockTrack | 無 | CRUD track assumptions, unknown factors, experiments |
| 8 | Create | `/projects/:id/create` | Step 2.2–2.3 | mockCreate, mockConceptRoutes, mockConvergence, mockKnowledgeRefs | 無 | CRUD anti-anchor, TRIZ solutions, subsystems, SCAMPER, alternatives, concept routes |
| 9 | SolutionExplorer | `/projects/:id/solutions` | Step 2.4 | mockSolutions, mockContradictions | 無 | CRUD solutions, convergence graph |
| 10 | PreCadReview | `/projects/:id/pre-cad` | Step 2.5 | mockSolutions | 無 | CRUD pre-cad reviews |
| 11 | CadInProgress | `/projects/:id/cad` | Step 2.5b | mockCreate (alternatives) | 無 | RU CAD status |
| 12 | DesignReview | `/projects/:id/review` | Step 3.1 | mockDesignReview, mockSolutions, mockTrack | 部分 (attachments) | CRUD evidence matrix, risks, experiments |
| 13 | DecisionRecord | `/projects/:id/decide` | Step 3.2 | mockDecisionRecord | 無 | CRUD decision, WANT scores, signatures, action items |
| 14 | Feynman | `/projects/:id/feynman` | Step 3.3 | 內建 mock entries | 無 | CRUD knowledge entries |
| 15 | KnowledgeBase | `/knowledge-base` | — | mockKnowledge | 無 | CRUD knowledge articles |
| 16 | Settings | `/settings` | — | — | 已有 (profiles) | — |
| 17 | Auth | `/auth` | — | — | 已有 (auth) | — |

### 1.2 現有 Supabase 資源（2026-04-07 更新）

| 資源 | 狀態 |
|------|------|
| Auth (signIn/signUp/reset) | ✅ 已實作 |
| profiles 表 | ✅ 已實作 |
| **31 張業務資料表** | ✅ 已部署（migrations 000–004）|
| RLS Policies | ✅ 全表覆蓋 |
| types.ts (auto-gen) | ✅ 同步 |
| react-query 封裝 | ✅ `src/hooks/api/` 完整結構 |
| Storage（review attachments）| ✅ 已實作 |

---

## §2 資料庫 Schema 規劃

### 2.1 核心資料表（共 20 張）

依據 `src/types/` 中的型別定義，規劃以下 Supabase 表：

#### Layer 0：專案骨幹

```sql
-- 1. projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'in_progress', -- in_progress | completed | archived
  phase TEXT NOT NULL DEFAULT 'Phase I',
  progress INTEGER DEFAULT 0,
  mission TEXT,
  phase_progress JSONB DEFAULT '{}',
  quick_stats JSONB DEFAULT '{}',
  gates_passed INTEGER DEFAULT 0,
  gates_total INTEGER DEFAULT 0,
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### Layer 1：Step 1 — 問題界定

```sql
-- 2. briefs (TaskDefinition)
CREATE TABLE briefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  mission TEXT,
  task_definition_5w1h JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(project_id)
);

-- 3. constraints
CREATE TABLE constraints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  constraint_code TEXT NOT NULL,
  description TEXT NOT NULL,
  source TEXT,
  type TEXT NOT NULL DEFAULT 'hard', -- hard | soft | non_goal
  feasibility TEXT, -- pass | warning | fail
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. kpis
CREATE TABLE kpis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  kpi_name TEXT NOT NULL,
  target_value TEXT,
  unit TEXT,
  measurement_method TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. socratic_questions
CREATE TABLE socratic_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  category TEXT NOT NULL, -- clarification | assumption | consequence | counter | origin | action | reframing
  text TEXT NOT NULL,
  answer TEXT,
  tagged_as_assumption BOOLEAN DEFAULT false,
  tagged_as_contradiction BOOLEAN DEFAULT false,
  ai_suggested_tag TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. contradictions
CREATE TABLE contradictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  natural_description TEXT,
  improving_param INTEGER,
  worsening_param INTEGER,
  engineering_statement TEXT,
  physical_contradiction TEXT,
  type TEXT, -- TC | PC | SF
  severity TEXT NOT NULL DEFAULT 'minor', -- fatal | major | minor
  resolved BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### Layer 2：Step 1.2 — 假設管理

```sql
-- 7. assumptions
CREATE TABLE assumptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  content TEXT NOT NULL,
  source TEXT,
  source_type TEXT, -- explore_tag | manual | ai_suggest | unknown_convert
  worst_consequence TEXT,
  worst_severity TEXT, -- critical | high | medium | low
  min_validation TEXT,
  validation_cost TEXT,
  validation_method TEXT,
  estimated_days INTEGER,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | validating | validated | refuted
  verification_stage TEXT DEFAULT 'unplanned', -- unplanned | planned | in_progress | completed | refuted
  impact_scope TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 8. causal_loop_diagrams
CREATE TABLE cld_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  x DOUBLE PRECISION DEFAULT 0,
  y DOUBLE PRECISION DEFAULT 0,
  node_type TEXT DEFAULT 'variable', -- assumption | variable
  assumption_id UUID REFERENCES assumptions(id),
  is_leverage BOOLEAN DEFAULT false
);

CREATE TABLE cld_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  from_node UUID REFERENCES cld_nodes(id) ON DELETE CASCADE,
  to_node UUID REFERENCES cld_nodes(id) ON DELETE CASCADE,
  polarity TEXT DEFAULT '+' -- + | -
);
```

#### Layer 3：Step 2 — 解方探索

```sql
-- 9. anti_anchor_routes
CREATE TABLE anti_anchor_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  is_non_typical BOOLEAN DEFAULT true,
  source TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 10. triz_solutions
CREATE TABLE triz_solutions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  contradiction_id UUID REFERENCES contradictions(id),
  path TEXT NOT NULL, -- TC | PC | SF
  principle_number INTEGER,
  principle_name TEXT,
  suggestion TEXT,
  status TEXT DEFAULT 'pending', -- adopted | edited | skipped | pending
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 11. subsystems
CREATE TABLE subsystems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  reason TEXT,
  related_contradictions TEXT[], -- contradiction IDs
  confirmed BOOLEAN DEFAULT false,
  parent_id UUID REFERENCES subsystems(id),
  interfaces TEXT,
  source TEXT DEFAULT 'rd', -- rd | ai | ai_edited
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 12. scamper_variants
CREATE TABLE scamper_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  subsystem_id UUID REFERENCES subsystems(id),
  action TEXT NOT NULL, -- S | C | A | M | P | E | R
  description TEXT,
  adopted BOOLEAN DEFAULT false,
  new_contradictions JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 13. alternatives (Concept Routes 前身)
CREATE TABLE alternatives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  mechanism TEXT,
  source TEXT, -- triz_tc | triz_pc | triz_sf | scamper | manual | ai_integrated
  key_assumption_ids TEXT[],
  must_scores JSONB DEFAULT '{}',
  interface_contract JSONB DEFAULT '{}',
  pre_cad_scores JSONB DEFAULT '{}',
  overall_pass BOOLEAN,
  cad_status TEXT DEFAULT 'not_started', -- not_started | in_progress | completed
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 14. concept_routes (多解採納)
CREATE TABLE concept_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  route_type TEXT NOT NULL DEFAULT 'single', -- single | composite
  composition JSONB DEFAULT '[]',
  composition_rationale TEXT,
  anti_pattern_warnings TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 15. compatibility_pairs (相容性矩陣)
CREATE TABLE compatibility_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  solution_a_id TEXT NOT NULL,
  solution_b_id TEXT NOT NULL,
  result TEXT NOT NULL, -- compatible | exclusive | needs_verification
  adoption_type TEXT, -- M1 | M2 | M3 | M4 | M5
  reason TEXT
);
```

#### Layer 4：Step 3 — 審查與決策

```sql
-- 16. evidence_matrix
CREATE TABLE evidence_matrix (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  assumption_code TEXT NOT NULL,
  summary TEXT,
  current_level TEXT DEFAULT 'E0', -- E0 | E1 | E2 | E3 | E4
  is_north_star BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 17. risks
CREATE TABLE risks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  failure_mode TEXT,
  probability INTEGER DEFAULT 1, -- 1-5
  severity INTEGER DEFAULT 1, -- 1-5
  mitigation TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- experiments 表已存在，需擴展欄位
-- ALTER TABLE experiments ADD COLUMN linked_assumptions TEXT[];
-- ALTER TABLE experiments ADD COLUMN evidence_level TEXT;
-- ALTER TABLE experiments ADD COLUMN method TEXT;
-- ALTER TABLE experiments ADD COLUMN success_criteria TEXT;

-- 18. decisions
CREATE TABLE decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  selected_alternative_id UUID REFERENCES alternatives(id),
  selected_alternative_name TEXT,
  rationale TEXT,
  risk_acceptance TEXT,
  decision_date TIMESTAMPTZ,
  status TEXT DEFAULT 'draft', -- draft | confirmed | signed
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 19. want_criteria
CREATE TABLE want_criteria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  weight INTEGER DEFAULT 5, -- 1-10
  description TEXT,
  anchors TEXT
);

-- 20. want_scores
CREATE TABLE want_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  criterion_id UUID REFERENCES want_criteria(id),
  alternative_id UUID REFERENCES alternatives(id),
  score INTEGER DEFAULT 0,
  evidence TEXT,
  weighted_total DOUBLE PRECISION DEFAULT 0
);

-- 21. adverse_consequences
CREATE TABLE adverse_consequences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  alternative_id UUID REFERENCES alternatives(id),
  description TEXT NOT NULL,
  probability TEXT, -- high | medium | low
  severity TEXT, -- high | medium | low
  level TEXT, -- L | M | H | H*
  mitigation TEXT,
  risk_artifact_id UUID
);

-- 22. signatures
CREATE TABLE signatures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  decision_id UUID REFERENCES decisions(id),
  name TEXT NOT NULL,
  role TEXT,
  status TEXT DEFAULT 'pending', -- pending | signed | rejected
  signed_at TIMESTAMPTZ,
  note TEXT
);

-- 23. action_items
CREATE TABLE action_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  decision_id UUID REFERENCES decisions(id),
  description TEXT NOT NULL,
  assignee TEXT,
  due_date DATE
);
```

#### Layer 5：知識管理

```sql
-- 24. knowledge_articles
CREATE TABLE knowledge_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL, -- playbook | case-study | template | convergence-pattern
  tags TEXT[],
  author TEXT,
  published_at TIMESTAMPTZ DEFAULT now(),
  content TEXT,
  related_links JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 25. knowledge_entries (Feynman 產出)
CREATE TABLE knowledge_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  asset_type TEXT NOT NULL, -- decision_record | experiment_result | contradiction_resolution | failure_mode | design_rule | best_practice
  title TEXT NOT NULL,
  content TEXT,
  reviewed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 2.2 表格統計

| 層級 | 表數 | 說明 |
|------|------|------|
| Layer 0 專案骨幹 | 1 | projects |
| Layer 1 問題界定 | 5 | briefs, constraints, kpis, socratic_questions, contradictions |
| Layer 2 假設管理 | 3 | assumptions, cld_nodes, cld_edges |
| Layer 3 解方探索 | 7 | anti_anchor_routes, triz_solutions, subsystems, scamper_variants, alternatives, concept_routes, compatibility_pairs |
| Layer 4 審查決策 | 8 | evidence_matrix, risks, decisions, want_criteria, want_scores, adverse_consequences, signatures, action_items |
| Layer 5 知識管理 | 2 | knowledge_articles, knowledge_entries |
| 已存在 | 3 | profiles, experiments (需擴展), review_attachments |
| **合計** | **29** | 新建 26 + 既有 3 |

---

## §3 API 層規劃

### 3.1 API Hooks 清單（依頁面分組）

每個 hook 使用 `@tanstack/react-query` 的 `useQuery` / `useMutation` 封裝 Supabase 呼叫。

#### 專案管理

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useProjects()` | SELECT all | projects | ProjectList |
| `useProject(id)` | SELECT by id | projects + briefs + stats | ProjectDashboard |
| `useCreateProject()` | INSERT | projects | ProjectList |
| `useUpdateProject()` | UPDATE | projects | ProjectDashboard |
| `useDeleteProject()` | DELETE | projects | ProjectList |
| `useProjectStats(id)` | SELECT aggregated | multiple tables | ProjectDashboard |

#### Step 1：問題界定

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useBrief(projectId)` | SELECT | briefs | TaskDefinition |
| `useUpsertBrief()` | UPSERT | briefs | TaskDefinition |
| `useConstraints(projectId)` | SELECT | constraints | TaskDefinition |
| `useMutateConstraint()` | INSERT/UPDATE/DELETE | constraints | TaskDefinition |
| `useKpis(projectId)` | SELECT | kpis | TaskDefinition |
| `useMutateKpi()` | INSERT/UPDATE/DELETE | kpis | TaskDefinition |
| `useSocraticQuestions(projectId)` | SELECT | socratic_questions | Explore |
| `useMutateSocraticQuestion()` | UPDATE (answer) | socratic_questions | Explore |
| `useContradictions(projectId)` | SELECT | contradictions | Explore, ContradictionID, SolutionExplorer |
| `useMutateContradiction()` | INSERT/UPDATE/DELETE | contradictions | ContradictionID |

#### Step 1.2：假設管理

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useAssumptions(projectId)` | SELECT | assumptions | AssumptionLedger, Track |
| `useMutateAssumption()` | INSERT/UPDATE/DELETE | assumptions | AssumptionLedger, Track |
| `useCldNodes(projectId)` | SELECT | cld_nodes | AssumptionLedger, Explore |
| `useMutateCldNode()` | INSERT/UPDATE/DELETE | cld_nodes | AssumptionLedger |
| `useCldEdges(projectId)` | SELECT | cld_edges | AssumptionLedger, Explore |
| `useMutateCldEdge()` | INSERT/UPDATE/DELETE | cld_edges | AssumptionLedger |

#### Step 2：解方探索

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useAntiAnchorRoutes(projectId)` | SELECT | anti_anchor_routes | Create |
| `useMutateAntiAnchorRoute()` | INSERT/UPDATE/DELETE | anti_anchor_routes | Create |
| `useTrizSolutions(projectId)` | SELECT | triz_solutions | Create |
| `useMutateTrizSolution()` | INSERT/UPDATE | triz_solutions | Create |
| `useSubsystems(projectId)` | SELECT | subsystems | Create |
| `useMutateSubsystem()` | INSERT/UPDATE/DELETE | subsystems | Create |
| `useScamperVariants(projectId)` | SELECT | scamper_variants | Create |
| `useMutateScamperVariant()` | INSERT/UPDATE | scamper_variants | Create |
| `useAlternatives(projectId)` | SELECT | alternatives | Create, PreCadReview, CadInProgress |
| `useMutateAlternative()` | INSERT/UPDATE | alternatives | Create |
| `useConceptRoutes(projectId)` | SELECT | concept_routes | Create |
| `useMutateConceptRoute()` | INSERT | concept_routes | Create |
| `useCompatibilityPairs(projectId)` | SELECT | compatibility_pairs | Create |
| `useSolutions(projectId)` | SELECT | (derived from triz_solutions + alternatives) | SolutionExplorer |

#### Step 3：審查與決策

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useEvidenceMatrix(projectId)` | SELECT | evidence_matrix | DesignReview |
| `useMutateEvidenceRow()` | INSERT/UPDATE | evidence_matrix | DesignReview |
| `useRisks(projectId)` | SELECT | risks | DesignReview |
| `useMutateRisk()` | INSERT/UPDATE/DELETE | risks | DesignReview |
| `useExperiments(projectId)` | SELECT | experiments | DesignReview, Track |
| `useMutateExperiment()` | INSERT/UPDATE | experiments | DesignReview |
| `useDecision(projectId)` | SELECT | decisions | DecisionRecord |
| `useMutateDecision()` | INSERT/UPDATE | decisions | DecisionRecord |
| `useWantCriteria(projectId)` | SELECT | want_criteria | DecisionRecord |
| `useMutateWantCriterion()` | INSERT/UPDATE/DELETE | want_criteria | DecisionRecord |
| `useWantScores(projectId)` | SELECT | want_scores | DecisionRecord |
| `useMutateWantScore()` | UPDATE | want_scores | DecisionRecord |
| `useAdverseConsequences(projectId)` | SELECT | adverse_consequences | DecisionRecord |
| `useMutateAC()` | INSERT/UPDATE/DELETE | adverse_consequences | DecisionRecord |
| `useSignatures(projectId)` | SELECT | signatures | DecisionRecord |
| `useMutateSignature()` | UPDATE | signatures | DecisionRecord |
| `useActionItems(projectId)` | SELECT | action_items | DecisionRecord |
| `useMutateActionItem()` | INSERT/UPDATE/DELETE | action_items | DecisionRecord |

#### 知識管理

| Hook | 方法 | 對應表 | 使用頁面 |
|------|------|--------|---------|
| `useKnowledgeArticles()` | SELECT | knowledge_articles | KnowledgeBase |
| `useKnowledgeArticle(slug)` | SELECT by slug | knowledge_articles | KnowledgeBase |
| `useKnowledgeEntries(projectId)` | SELECT | knowledge_entries | Feynman |
| `useMutateKnowledgeEntry()` | INSERT/UPDATE | knowledge_entries | Feynman |

### 3.2 API 統計

| 類別 | Query Hooks | Mutation Hooks | 合計 |
|------|-------------|----------------|------|
| 專案管理 | 3 | 3 | 6 |
| Step 1 問題界定 | 5 | 5 | 10 |
| Step 1.2 假設管理 | 3 | 3 | 6 |
| Step 2 解方探索 | 7 | 7 | 14 |
| Step 3 審查決策 | 9 | 9 | 18 |
| 知識管理 | 3 | 2 | 5 |
| **合計** | **30** | **29** | **59** |

---

## §4 完整功能清單

### 4.1 依設計階段分組

#### Phase I — 問題定義與假設

| 功能 | 頁面 | Gate | 描述 |
|------|------|------|------|
| F01 專案 CRUD | ProjectList | — | 建立/檢視/篩選/封存專案 |
| F02 專案儀表板 | ProjectDashboard | — | Phase 進度、KPI、歷程、導航卡 |
| F03 任務定義 | TaskDefinition | Gate 1.1 | Mission、Hard/Soft/Non-goal 約束、KPI 定義 |
| F04 文件萃取 | TaskDefinition | Gate 1.1 | 多模態上傳 → AI 萃取約束/KPI |
| F05 可行性檢查 | TaskDefinition | Gate 1.1 | 約束間衝突偵測 |
| F06 5W1H 產生 | TaskDefinition | Gate 1.1 | AI 產生 Who/What/Where/When/Why/How |
| F07 蘇格拉底問答 | Explore | Gate 1.2 | 7 類提問 + 回答 + 假設/矛盾標記 |
| F08 矛盾辨識 | Explore, ContradictionID | Gate 1.3 | 39 參數選擇、自然語言→工程陳述、TC/PC 分類 |
| F09 因果迴路圖 | Explore | Phase Gate 1 | CLD 節點/邊/斷裂點視覺化 |
| F10 假設台帳 | AssumptionLedger | — | CRUD 假設、狀態管理、嚴重度、驗證方法 |
| F11 CLD 關聯 | AssumptionLedger | — | 假設 ↔ CLD 節點 ↔ 矛盾 連結 |
| F12 蘇格拉底回饋 | AssumptionLedger | — | AI 對假設的質疑與建議 |

#### Phase II — 解方探索與收斂

| 功能 | 頁面 | Gate | 描述 |
|------|------|------|------|
| F13 假設看板 | Track | Gate 2.1 | Kanban（unverified→validating→validated/refuted） |
| F14 未知因素管理 | Track | Gate 2.1 | U-set 收集、轉換為假設 |
| F15 Anti-Anchor Sprint | Create | Gate 2.2 | 非典型架構概念產生 |
| F16 TRIZ 解方 | Create | Gate 2.2 | TC/PC/SF 三路徑解方、原理具體化 |
| F17 子系統拆解 | Create | Gate 2.2 | 系統→子系統分解、介面定義 |
| F18 SCAMPER 變體 | Create | Gate 2.2 | 7 種操作手法產出變體 + 新矛盾偵測 |
| F19 方案管理 | Create | Gate 2.3 | Alternative CRUD、MUST 評分、Pre-CAD 評分 |
| F20 介面契約 | Create | Gate 2.3 | 6 維度介面定義（包絡/載荷/訊號/熱/基準/維護） |
| F21 TRIZ 收斂迴圈 | Create | — | AI 自動探索 → 分支 → 收斂 → Human Review |
| F22 多解採納策略 | Create | Step 5a-X | N×N 相容性矩陣、M1-M5 判斷、複合 Route |
| F23 解方探索器 | SolutionExplorer | — | 解方詳情、收斂圖、MUST checklist、二次矛盾掃描 |
| F24 Pre-CAD 審查 | PreCadReview | Gate P | 5 維度審查、信心分數、方案篩選 |
| F25 CAD 進度追蹤 | CadInProgress | — | CAD 狀態管理（not_started→in_progress→completed） |

#### Phase III — 設計審查與決策

| 功能 | 頁面 | Gate | 描述 |
|------|------|------|------|
| F26 證據矩陣 | DesignReview | Gate 3.1 | E0-E4 證據等級追蹤、North Star 標記 |
| F27 風險登錄 | DesignReview | Gate 3.1 | FMEA-like 風險管理（機率×嚴重度） |
| F28 實驗管理 | DesignReview | Gate 3.1 | 實驗 CRUD、狀態追蹤、證據連結 |
| F29 附件管理 | DesignReview | Gate 3.1 | 檔案上傳/下載（已有 Supabase Storage） |
| F30 KT 決策分析 | DecisionRecord | Gate 3.2 | MUST 結果 + WANT 評分 + 雷達圖 |
| F31 WANT 管理 | DecisionRecord | Gate 3.2 | 準則 CRUD、權重、模板載入 |
| F32 不良後果分析 | DecisionRecord | Gate 3.2 | AC 評估（機率×嚴重度→等級） |
| F33 決策確認 | DecisionRecord | Gate 3.2 | 主方案/備案選擇、理由、行動項目 |
| F34 簽核流程 | DecisionRecord | Phase Gate 3 | 多角色簽核（pending→signed→rejected） |
| F35 匯出 | DecisionRecord | — | PDF/JSON 匯出 |

#### 知識內化

| 功能 | 頁面 | Gate | 描述 |
|------|------|------|------|
| F36 Feynman 知識產出 | Feynman | Gate 8 | 6 類知識資產自動產生 + 人工審核 |
| F37 知識庫 | KnowledgeBase | — | 文章瀏覽、分類篩選、全文搜尋 |

**功能總計：37 個**

---

## §5 WBS 開發工作分解

### Sprint 0：基礎建設 ✅ 完成

| WBS | 工作項目 | 狀態 | 產出 |
|-----|---------|------|------|
| 0.1 | Supabase Schema 建立 | ✅ | 31 張表（migrations 000–004）|
| 0.2 | RLS (Row Level Security) 策略 | ✅ | 每張表的 RLS policy |
| 0.3 | Supabase types 自動產生 | ✅ | `src/integrations/supabase/types.ts` 同步 |
| 0.4 | API 基礎架構 | ✅ | `src/hooks/api/` + react-query QueryClient |
| 0.5 | Error/Loading 統一元件 | ✅ | `<QueryBoundary>` / `<ErrorFallback>` |
| 0.6 | Seed data 腳本 | ✅ | DevSeed.tsx + seed migration |

### Sprint 1：專案骨幹 + Step 1 ✅ 完成

| WBS | 工作項目 | 功能 | 狀態 | Mock 檔案 |
|-----|---------|------|------|-----------|
| 1.1 | Projects API + 頁面接入 | F01, F02 | ✅ | mockProjects ✅ 移除 / mockDashboard ✅ 移除 / mockNavCards 🟡 仍存在但未使用 |
| 1.2 | Brief/Constraints/KPIs API | F03–F06 | ✅ | mockTaskDefinition ✅ 移除 / mockExtraction ✅ 移除 |
| 1.3 | Socratic + Contradictions API | F07–F09 | ✅ | mockExplore 🟡 仍 import / mockContradictions ✅ 移除 / trizParameters 保留 |
| 1.4 | Assumptions + CLD API | F10–F12 | ✅ | mockAssumptions ✅ 移除 |

### Sprint 2：Step 2 解方探索 ✅ 完成

| WBS | 工作項目 | 功能 | 狀態 | Mock 檔案 |
|-----|---------|------|------|-----------|
| 2.1 | Track API（假設看板 + 未知因素 + 實驗）| F13, F14 | ✅ | mockTrack 🟡 仍 import；`unknown_factors` 表已建立、`useTrackAssumptions/useCreate/useDelete/useUnknownFactors/useTrackExperiments` 完整 |
| 2.2 | Anti-Anchor + TRIZ + Subsystem API | F15–F17 | ✅ | mockCreate 🟡 仍 import；TRIZ 已支援 TC/PC/SF 三路徑（含 `/triz/sufield`）|
| 2.3 | SCAMPER + Alternatives API | F18–F20 | ✅ | mockCreate（同上）；含 SCAMPER feedback-contradictions 閉環 |
| 2.4 | Convergence Loop + Multi-Solution API | F21, F22 | ✅ | mockConvergence ✅ 移除 / mockConceptRoutes 🟡 仍存在 |
| 2.5 | Solution Explorer API | F23 | ✅ | mockSolutions ✅ 移除 |
| 2.6 | Pre-CAD + CAD Status API | F24, F25 | ✅ | `usePreCadSolutions` / `usePreCadConvergenceStats` 已 live |

### Sprint 3：Step 3 審查決策 ✅ 完成

| WBS | 工作項目 | 功能 | 狀態 | Mock 檔案 |
|-----|---------|------|------|-----------|
| 3.1 | Evidence Matrix API | F26 | ✅ | mockDesignReview ✅ 移除 |
| 3.2 | Risks + Experiments API | F27, F28 | ✅ | 同上（experiments 表已擴展 linked_assumptions/evidence_level/method/success_criteria）|
| 3.3 | Decision + WANT Scoring API | F30, F31 | ✅ | mockDecisionRecord ✅ 移除 |
| 3.4 | AC + Signatures + Actions API | F32–F34 | ✅ | 同上 |
| 3.5 | Export API | F35 | ✅ | `POST /api/v1/export` 已實作 |

### Sprint 4：知識管理 + 收尾 🟡 進行中

| WBS | 工作項目 | 功能 | 狀態 | 備註 |
|-----|---------|------|------|------|
| 4.1 | Feynman Knowledge Entries API | F36 | ✅ | `useKnowledgeEntries` live |
| 4.2 | Knowledge Base API | F37 | ✅ Hook live | `useKnowledgeArticles` 完成；KnowledgeBase.tsx 仍 import `mockKnowledge` 作為 fallback |
| 4.3 | Knowledge Refs 遷移 | — | 🟡 | `mockKnowledgeRefs` 仍被 KnowledgeBase 使用 |
| 4.4 | Mock 檔案清除 | — | 🟡 | 仍剩 7 個 mock 檔（見 §6）|
| 4.5 | 整合測試 + E2E 驗證 | — | 🔲 | 待 4.4 完成 |

### 工期總覽（實績）

| Sprint | 狀態 | 工作項目數 | Mock 檔案清除 |
|--------|------|-----------|-------------|
| Sprint 0 基礎建設 | ✅ | 6 | 0 |
| Sprint 1 專案 + Step 1 | ✅ | 4 | 6 |
| Sprint 2 Step 2 | ✅ | 6 | 2 |
| Sprint 3 Step 3 | ✅ | 5 | 2 |
| Sprint 4 知識 + 收尾 | 🟡 | 5 | 0（pending） |
| **合計** | **~85%** | **26** | **10 / 17** |

---

## §6 Mock 檔案 → 清除狀態（2026-04-07）

| Mock 檔案 | 規劃 Sprint | 替換的 API Hooks | 清除狀態 |
|-----------|------------|-----------------|----------|
| `mockProjects.ts` | Sprint 1 | useProjects, useProject | ✅ 已移除 |
| `mockDashboard.ts` | Sprint 1 | useProjectStats | ✅ 已移除 |
| `mockNavCards.ts` | Sprint 1 | useProject (derived) | 🟡 檔案存在但無頁面 import |
| `mockTaskDefinition.ts` | Sprint 1 | useBrief, useConstraints, useKpis | ✅ 已移除 |
| `mockExtraction.ts` | Sprint 1 | AI extraction endpoint | ✅ 已移除 |
| `mockExplore.ts` | Sprint 1 | useSocraticQuestions, useCldNodes/Edges | 🟡 仍被 Explore.tsx import（fallback）|
| `mockContradictions.ts` | Sprint 1 | useContradictions | ✅ 已移除 |
| `mockAssumptions.ts` | Sprint 1 | useAssumptions, useCldNodes/Edges | ✅ 已移除 |
| `mockTrack.ts` | Sprint 2 | useTrackAssumptions, useUnknownFactors, useTrackExperiments | 🟡 仍被 Track.tsx import |
| `mockCreate.ts` | Sprint 2 | useAntiAnchorRoutes/useTrizSolutions/useSubsystems/useScamperVariants/useAlternatives | 🟡 仍被 Create.tsx import |
| `mockConvergence.ts` | Sprint 2 | useContradictionScan / convergence stats | ✅ 已移除 |
| `mockConceptRoutes.ts` | Sprint 2 | useConceptRoutes, useCompatibilityPairs | 🟡 檔案存在 |
| `mockSolutions.ts` | Sprint 2 | useSolutions | ✅ 已移除 |
| `mockDesignReview.ts` | Sprint 3 | useEvidenceMatrix, useRisks, useExperiments, useEvidenceEntries | ✅ 已移除 |
| `mockDecisionRecord.ts` | Sprint 3 | useDecision, useWantCriteria, useWantScores, useSignatures, useActionItems, useAdverseConsequences | ✅ 已移除 |
| `mockKnowledge.ts` | Sprint 4 | useKnowledgeArticles | 🟡 仍被 KnowledgeBase.tsx import |
| `mockKnowledgeRefs.ts` | Sprint 4 | (各頁 KnowledgeRefsPanel) | 🟡 仍被 KnowledgeBase.tsx import |
| `trizParameters.ts` | **保留** | 靜態知識，不需遷移至 DB | ⏸ 永久保留 |

**清除統計**：9 ✅ 已移除 / 7 🟡 殘留 / 1 ⏸ 永久保留 = 共 17 個

> `trizParameters.ts` 為 TRIZ 39 工程參數靜態資料，屬於知識庫常數，保留於前端。

### Sprint 4 收尾待辦清單

1. **Explore.tsx**：移除 `mockExplore` import，全面改用 `useSocraticQuestions` / `useExploreContradictions` / `useCldNodes` / `useCldEdges`。
2. **Track.tsx**：移除 `mockTrack` import；目前 hooks 已 live，僅型別/輔助常數仍依賴 mock 檔。
3. **Create.tsx**：移除 `mockCreate` import；解方探索全 hook 已 live，Create 頁仍以 mock 為視覺 fallback。
4. **KnowledgeBase.tsx**：移除 `mockKnowledge` / `mockKnowledgeRefs`，全面切換至 `useKnowledgeArticles` / `useKnowledgeEntries`。
5. **mockNavCards.ts / mockConceptRoutes.ts**：確認無頁面依賴後直接刪檔。
6. **整合 E2E 驗證**：完成上述清除後執行 Playwright / 走查 Gate 1.1 → Phase Gate 3 全流程。

---

## §7 開發原則

1. **漸進替換**：每個 Sprint 完成後，該範圍的 mock import 全部移除，確保不回退。
2. **型別優先**：先更新 `src/integrations/supabase/types.ts`（自動產生），再寫 hooks。
3. **Query Key 規範**：`['table-name', projectId]` 格式統一，確保 cache invalidation 正確。
4. **Optimistic Updates**：CRUD 操作使用 React Query 的 optimistic update 提升 UX。
5. **RLS 優先**：所有表必須有 Row Level Security，確保多租戶安全。
6. **Loading/Error 統一**：所有頁面使用統一的 `<QueryBoundary>` 包裹。
7. **測試策略**：每個 API hook 搭配 Vitest mock 測試，頁面層級用 Testing Library 驗證。
