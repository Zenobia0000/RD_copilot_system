# ADR-001：前端技術棧

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, ARCH, FE
**決策日期 (Date)**：2026-04-28
**諮詢 (Consulted)**：FE 團隊
**知會 (Informed)**：All

---

## Context & Problem Statement

需要選擇前端技術棧支援 18 頁 IA、AI 互動、即時表單、複雜資料表格與圖表。

**驅動因素**：
- 既有 design-system-specs 已圍繞 React + Tailwind 撰寫
- 需支援 LCP < 2.5s / INP < 200ms
- 開發速度優先（MVP Q3）
- 團隊熟悉 React 生態

**約束**：
- 必須支援 SSR/SSG 選項（v2 SEO 考量）
- TypeScript first
- 需有大量現成元件庫可整合（Tailwind + Headless UI）

---

## Considered Options

| Option | Pros | Cons | Cost |
|:-------|:-----|:-----|:-----|
| **React 18 + Tailwind + Zustand + React Query** | 生態最成熟、團隊熟悉、design-system 已對齊 | bundle size 較大 | Low |
| Vue 3 + Pinia + Tailwind | 學習曲線低、模板清晰 | 團隊不熟、design-system 需改寫 | High |
| Svelte + SvelteKit | 體積小、效能好 | 生態相對新、第三方元件少 | Med |
| Next.js（含 SSR） | SEO 友好、官方推薦 | MVP 不需 SSR、複雜度增加 | Med |

---

## Decision Outcome

**選擇**：React 18 + Tailwind CSS + Zustand + React Query + React Hook Form + Framer Motion + Recharts + React Table

**理由**：
1. design-system-specs 已實作對應規範
2. 團隊熟悉度高，開發速度最快
3. v1 MVP 不需 SSR，CSR 即可滿足
4. 各層級狀態（全局/伺服器/表單/URL）職責分離乾淨

**權衡**：
- 接受 bundle size 較 Svelte 大（用 code splitting 緩解）
- 接受未來若要 SSR 需遷移至 Next.js（保持元件 SSR-friendly）

---

## Consequences

### Positive
- 開發速度快、招聘容易
- 設計系統 + 元件庫無縫整合
- 大量第三方學習材料

### Risks
- bundle size：用 Vite + tree-shaking + lazy load 控制
- 過度依賴狀態管理庫的學習曲線：建立內部 cookbook

### Re-evaluation Triggers
- v2 若需 SSR/SEO 強需求 → 評估遷移 Next.js
- TRIZ skill UI 出現極端效能瓶頸 → 評估 Solid/Qwik

---

## Implementation Plan

詳見 [`05_architecture.md §4.1`](../05_architecture.md) + [`08_project_structure.md`](../08_project_structure.md)。

---

## References

- design-system-specs：`rd_assistant_design_system/design-system-specs/`
- universal_template `01_GLOBAL_SYSTEM_PROMPT [TECH & CONSTRAINT LAYER]`
