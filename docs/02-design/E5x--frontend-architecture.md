# E5x — 前端架構規格 (Frontend Architecture Specification)

---

**文件版本 (Document Version):** `v1.1`
**最後更新 (Last Updated):** `2026-04-23`
**主要作者 (Lead Author):** `Frontend Lead`
**狀態 (Status):** `Active`
**對應 VibeCoding 模板:** `12_frontend_architecture_specification.md`
**上游:** [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) · [`E5--api-design-specification.md`](E5--api-design-specification.md)

> **說明**：本文件為骨架文件；具體 Create 頁 UX 與互動細節已在 [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md) 詳盡記錄。本檔聚焦跨頁面的架構級決策。

---

## 目錄

- [第一部分：前端架構的第一性原理](#第一部分前端架構的第一性原理)
- [第二部分：前端架構的系統化分層](#第二部分前端架構的系統化分層)
- [第三部分：前端設計系統](#第三部分前端設計系統)
- [第四部分：技術選型與架構決策](#第四部分技術選型與架構決策)
- [第五部分：效能與優化策略](#第五部分效能與優化策略)
- [第六部分：可用性與無障礙設計](#第六部分可用性與無障礙設計)
- [第七部分：前端工程化實踐](#第七部分前端工程化實踐)
- [第八部分：前後端協作契約](#第八部分前後端協作契約)
- [第九部分：監控、日誌與安全](#第九部分監控日誌與安全)
- [第十部分：前端開發檢查清單](#第十部分前端開發檢查清單)
- [附錄](#附錄)

---

## 第一部分：前端架構的第一性原理

1. **User-centric**：所有 UI 決策回答「RD 要解什麼問題？」（參 00-discover 痛點 → E3x Scenario 1/2/3）。
2. **Single source of truth**：型別來自 `backend/app/models/schemas.py`（透過 pydantic2ts 同步至 `src/types/generated/`）；手寫 UI 型別在 `src/types/`。
3. **Feature-first organization**：`src/components/{create,explore,review,...}` 按頁面功能切分，避免 MVC 按類型切分。
4. **Progressive disclosure**：複雜流程（TRIZ L1→L2→L3）採分層 drill-down，不一次全展開；Create 頁以 7-step accordion stepper 逐步展開；Explore 頁以 Conditional Stepper 依問題成熟度（Level A/B/C）自動切換引導流/快速通道（ADR-008 §D6）。
5. **Observable state**：所有跨組件狀態走 React Query（server）+ Context（local UI）；避免 prop drilling。

## 第二部分：前端架構的系統化分層

```
┌──────── Pages (src/pages/) ─────────────────────────────────┐
│  18 個路由頁面 — 完整路由樹見                                │
│  E5x--frontend-information-architecture.md §3               │
├──────── Features (src/components/{create,explore,...}/) ─────┤
│  Feature 組件 (90+)：per-page 組件（assumption / brief /   │
│  contradiction / create / dashboard / evidence / explore /  │
│  layouts / precad / projects / review / solution /          │
│  task-definition / track）                                  │
├──────── Hooks (src/hooks/) ──────────────────────────────────┤
│  API hooks (25+): useLayeredTrizSolutions /                 │
│  useDirectedTrizSolutions / useSubsystemSuggestion /        │
│  useConvergenceLoop / useAiOperationGuard / ...             │
├──────── Lib (src/lib/) ─────────────────────────────────────┤
│  api.ts (FastAPI client + ApiError + timeout) /             │
│  utils.ts (cn()) / triz/ / constraintLabeling /             │
│  subsystemHash / webVitals                                  │
├──────── Integrations (src/integrations/) ────────────────────┤
│  Supabase client + auto-generated types                     │
├──────── Types (src/types/ + types/generated/) ───────────────┤
│  手寫 UI 型別 (21 files) + codegen 後端契約                 │
├──────── Config (src/config/) ────────────────────────────────┤
│  featureFlags.ts (runtime toggles) /                        │
│  navigationSteps.ts (phase/step 定義)                       │
├──────── UI primitives (src/components/ui/) ──────────────────┤
│  shadcn/ui (50+) + radix-ui                                │
└──────────────────────────────────────────────────────────────┘
```

**分層規則**：
- 上層可依賴下層，反向禁止。
- `components/ui/` 為葉節點，不可 import feature 或 hook。
- `pages/` 不直接呼叫 API；必須透過 hook。

---

### 2.1 各層實際代碼範例

> 每段代碼取自 `src/` 真實檔案；若該層尚未建立對應實作，以 **TBD** 標註 target + 日期。對應模板：`12_frontend_architecture_specification.md`。

#### (a) 感知層 (Pages) — `src/pages/ProjectDashboard.tsx`

```tsx
// 路由層只組合 feature 組件 + 讀 hooks；不寫資料邏輯
import { PhaseProgressBar } from "@/components/dashboard/PhaseProgressBar";
import { GateDonut } from "@/components/dashboard/GateDonut";
import { NavCards } from "@/components/dashboard/NavCards";
import { PreCadScoreGauge } from "@/components/dashboard/PreCadScoreGauge";
import { ContradictionConvergenceCard } from "@/components/dashboard/ContradictionConvergenceCard";
// ... 高階 layout 由頁面組裝
```

Source: `src/pages/ProjectDashboard.tsx`（import 段 L17–L32）

#### (b) 互動層 (Features / Forms) — `src/components/task-definition/MultiItemInput.tsx` 類型

```tsx
// react-hook-form + zod 範例：TaskDefinition 頁的輸入組件
// 所有 form state 以 react-hook-form 管理，submit handler 呼叫 hook（不直接 fetch）
const onSubmit = form.handleSubmit(async (values) => {
  await extractConstraints.mutateAsync(values); // ← 互動層只呼叫 mutation
});
```

Source: `src/components/task-definition/` + `src/hooks/api/useBrief.ts`（詳見 hook 內 `useSupabaseMutation`）

#### (c) 狀態層 (Client state — Context API)

目前專案 client UI state 以 React `useState` + Context 為主，共 3 個 Context：

| Context | 檔案 | 負責狀態 |
|---|---|---|
| `AuthContext` | `src/contexts/AuthContext.tsx` | `user`, `session`, `isLoading`, `signOut()`；整合 Supabase Auth + `DEV_BYPASS_AUTH` 開發模式 |
| `ArtifactContext` | `src/contexts/ArtifactContext.tsx` | 6 種 artifact 型別的狀態機（Draft → Reviewed → Verified → Baselined → Released）；提供 `addArtifact`, `updateArtifact`, `transitionState`, `applyGateTransition` |
| `ProjectDataContext` | `src/contexts/ProjectDataContext.tsx` | 跨步驟資料共享（questions, contradictions, CLD, assumptions, alternatives） |

**頁面內 UI 狀態**：各頁面以 `useState` 管理局部 UI 狀態（如 Create 頁的 `currentStep`、`activeTrack`；Explore 頁的 `activeTab`）。

**Zustand** 尚未引入（`package.json` 無此依賴）。若未來需精簡跨組件 prop 傳遞，可考慮 per-feature store — `TBD`。

Source: `src/contexts/AuthContext.tsx`, `src/contexts/ArtifactContext.tsx`, `src/contexts/ProjectDataContext.tsx`

#### (d) 通訊層 (API adapter) — `src/hooks/api/useSupabaseQuery.ts`

```ts
// Thin wrapper over React Query + Supabase；所有 feature hook 共用
export function useSupabaseMutation<TData, TVariables>(options) {
  const queryClient = useQueryClient();
  return useMutation<TData, Error, TVariables>({
    mutationFn: async (variables) => {
      // insert / update / delete / upsert 統一入口
      // 錯誤統一 throw，上層由 ErrorBoundary + toast 處理
    },
    onError: (error) => {
      console.error(`[useSupabaseMutation] ${table}.${type} failed:`, error);
      toast.error(errorMessage ?? `Operation failed: ${error.message}`);
    },
  });
}
```

Source: `src/hooks/api/useSupabaseQuery.ts`（L204–L315）

> **Backend API (FastAPI) 路徑**：透過 Vite proxy `/api/v1/*` → `http://localhost:8000`；非 Supabase 的自訂端點 wrapper 位於 `src/hooks/api/useCreate.ts` / `useExplore.ts` 等 per-feature hook。

#### (e) 基礎設施層 (Vite / Build) — `vite.config.ts`

```ts
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "http://localhost:8000";
  const proxyTarget = apiBaseUrl.replace(/\/+$/, "").replace(/\/api\/v1$/i, "");
  return {
    server: {
      host: "::",
      port: 5173,
      strictPort: true,
      hmr: { overlay: false },
      proxy: {
        "/api/v1": { target: proxyTarget || "http://localhost:8000", changeOrigin: true },
      },
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
      dedupe: ["react", "react-dom", "react/jsx-runtime"],
    },
    optimizeDeps: {
      include: ["react", "react-dom", "react/jsx-runtime", "@tanstack/react-query"],
    },
    build: {
      target: "es2020",
      sourcemap: mode !== "production",
      cssCodeSplit: true,
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // vendor-react / vendor-radix / vendor-charts / vendor-query
            // vendor-supabase / vendor-icons / vendor-dates / vendor (其餘)
          },
        },
      },
    },
  };
});
```

Source: `vite.config.ts`（完整檔案 L1–L61）

## 第三部分：前端設計系統

- **UI Kit**：shadcn/ui（手動安裝組件至 `src/components/ui/`，便於客製）。
- **樣式系統**：TailwindCSS 3.x + CSS variables for theme（`src/index.css`）。
- **Theme**：Light / Dark 透過 `ThemeProvider.tsx` 切換。
- **Design tokens**：`tailwind.config.ts` 中的 `theme.extend.colors` 集中管理；對齊 `rd_assistant_design_system/` 視覺規範 — `TBD — <design lead TBD> by 2026-05 TBD`。
- **Iconography**：`lucide-react`（預設）；品牌圖示 TBD。

## 第四部分：技術選型與架構決策

| 決策 | 選擇 | 版本 | 備選 | 理由 | ADR |
|---|---|---|---|---|---|
| Framework | React | 18.3.1 | Vue 3, Svelte | 團隊熟悉、生態系 | TBD |
| Build tool | Vite | 5.4.19 | Next.js, Webpack | SPA 需求，啟動快 | TBD |
| Routing | react-router-dom | 6.30.1 | tanstack router | 成熟、路徑配置集中 | TBD |
| Server state | `@tanstack/react-query` | 5.83.0 | SWR | cache/invalidation 完整 | TBD |
| Client state | React Context API | — | Redux, Zustand | 輕量、原生 React 支援 | TBD |
| Form | react-hook-form + zod | 7.61.1 / 3.25.76 | Formik | 效能 + 型別 | TBD |
| Styling | Tailwind + shadcn/ui | 3.4.17 | CSS Modules, Emotion | utility-first、可客製 | TBD |
| DB Client | Supabase JS | 2.97.0 | — | Auth + RLS + realtime | TBD |
| Graph | @xyflow/react (React Flow) | 12.10.1 | — | 收斂圖 / CLD 視覺化 | TBD |
| Charts | Recharts | 2.15.4 | — | Dashboard 雷達圖、Pre-CAD 六維圖 | TBD |
| Type system | TypeScript strict + codegen | 5.8.3 | — | 與 backend schema 零漂移 | ADR-003 schema codegen |
| Test | Vitest + React Testing Library | 3.2.4 / 16.0.0 | Jest, Cypress | 與 Vite 原生整合 | TBD |

## 第五部分：效能與優化策略

- **Code splitting**：react-router route-level `lazy()` import（`Create`, `Explore`, `PreCadReview`, `Track`, `DesignReview`, `DecisionRecord`, `Feynman`, `KnowledgeBase`, `ConstraintLabelDictionary`, `Settings`, `DevSeed`）；關鍵路徑頁面（`Auth`, `ProjectList`, `ProjectDashboard`, `NotFound`）採 eager import。
- **Manual chunks**（`vite.config.ts`）：`vendor-react` / `vendor-radix` / `vendor-charts` / `vendor-query` / `vendor-supabase` / `vendor-icons` / `vendor-dates` / `vendor`（其餘 node_modules）。
- **React Query**：`staleTime: 30s`、`gcTime: 5min`、4xx 不 retry、5xx retry ≤ 2 次；結合 `invalidateQueries` 精準失效。
- **Memoization**：`React.memo` + `useMemo` 僅對明確瓶頸使用。
- **Bundle budget**：`chunkSizeWarningLimit: 600KB` — `TBD — 正式 budget 定案`。
- **LLM latency 緩解**：Create 正向分析步驟 採 streaming UI（skeleton + 分層逐步顯示）；對應 `specs/triz/E5x--triz-layered-drilldown-optimization.md`。
- **Feature flags**（`src/config/featureFlags.ts`）：`trizLayeredMode` 控制 TRIZ 分層模式啟停（透過 `VITE_TRIZ_LAYERED_MODE` env var，預設 `true`）。

## 第六部分：可用性與無障礙設計

- **WCAG 2.1 AA**：依賴 radix-ui primitive 的 aria 屬性；focus ring 維持預設。
- **鍵盤**：所有 Tab / dialog / command menu 可鍵盤操作。
- **錯誤狀態**：`ErrorBoundary.tsx` 全域包裹；顯示友善 fallback 並 capture 至 observability。
- **i18n**：目前 zh-TW only；英文介面為 `TBD — <pm TBD> by 2026-Q3 TBD`。

## 第七部分：前端工程化實踐

- **Lint / Format**：ESLint + Prettier；pre-commit hook — `TBD — <infra TBD>`。
- **TypeScript strict**：`strict: true`, `noUnusedLocals: true`。
- **Commit**：Conventional Commits（見專案 git log）。
- **Storybook**：`TBD — <fe-lead TBD> by 2026-Q3 TBD`（優先 `components/ui/`）。
- **CI**：`TBD — <infra TBD>`（build, typecheck, vitest, playwright smoke）。

## 第八部分：前後端協作契約

> **前後端共用契約**：所有端點定義、Request/Response schema、錯誤格式、版本策略，以 [`E5--api-design-specification.md`](E5--api-design-specification.md) 為唯一權威來源。Schema 同步機制見 [`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md)。後端開發人員無需閱讀本文件的其他章節。

- **API 契約**：見 [`E5--api-design-specification.md`](E5--api-design-specification.md)。
- **Schema codegen**：Pydantic → TS 一鍵同步，見 [`E6x--schema-codegen-workflow.md`](E6x--schema-codegen-workflow.md)。
- **命名轉換**：前端 camelCase、後端 snake_case；`src/integrations/` 擔任 adapter。參 [`specs/explore/E5x--tc-to-multipc-type-alignment.md`](specs/explore/E5x--tc-to-multipc-type-alignment.md)。
- **錯誤契約**：後端 `{error:{type,code,message,param,request_id}}` → 前端 normalize 成 `ApiError` 物件並 toast。

## 第九部分：監控、日誌與安全

- **Monitoring**：`TBD — <infra TBD>`（預設用 Sentry for FE + Anthropic/OpenAI 使用量）。
- **Logging**：console in dev；prod 送至 observability endpoint `TBD`。
- **Security**：
  - Auth：Supabase Auth session，`Authorization: Bearer <jwt>` 由 `src/integrations/` 自動附加。
  - XSS：依賴 React 預設 escape；任何 `dangerouslySetInnerHTML` 必須 PR review。
  - CSP：部署於 edge — `TBD`。

## 第十部分：前端開發檢查清單

### 架構層

- [ ] 新頁面/組件放對 `src/components/{feature}/`？
- [ ] 型別來自 `src/types/generated/` 還是手寫 `src/types/`（分清邊界）？
- [ ] 有 hook 隔離 API 呼叫？避免組件內直接 fetch？
- [ ] 無障礙：focus / aria / keyboard？
- [ ] Error boundary / loading skeleton / empty state 三態齊備？

### IA / 導航層

- [ ] 每個 Route 有對應 page 元件？
- [ ] 所有 `/projects/:id/*` 受 auth guard？
- [ ] Breadcrumb 可還原層級？
- [ ] 關鍵 state 可由 URL 重建（深連結測試）？
- [ ] 側欄 active 狀態準確？

### 驗收

- [ ] BDD scenario（`E5x--bdd-scenarios.md`）有對應？
- [ ] E7x 手測腳本有覆蓋關鍵路徑？

---

## 附錄

### A. 延伸閱讀（已在其他 spec 覆蓋）
- Create 頁完整 UX → [`specs/ux/E5x--create-ux-spec.md`](specs/ux/E5x--create-ux-spec.md)
- 資訊架構總覽 → [`E5x--frontend-information-architecture.md`](E5x--frontend-information-architecture.md)
- 檔案依賴 → [`specs/E5x--file-dependencies.md`](specs/E5x--file-dependencies.md)
- 類別關係 → [`specs/E5x--class-relationships.md`](specs/E5x--class-relationships.md)
- 專案結構 → [`E5x--project-structure-guide.md`](E5x--project-structure-guide.md)

### B. TBD 清單
- Bundle budget 定案 · Storybook 建置 · i18n 策略 · 完整 design token · monitoring 方案
