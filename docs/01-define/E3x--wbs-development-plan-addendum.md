# E3x WBS Development Plan — Addendum (Workstreams D–H)

> **文件版本**：v1.0
> **最後更新**：2026-04-15
> **狀態**：Active
> **主文檔**：[`E3x--wbs-development-plan.md`](E3x--wbs-development-plan.md)
> **模板對應**：VibeCoding 16 (WBS Development Plan)

---

## 用途 (Purpose)

主 WBS (`E3x--wbs-development-plan.md`) 整併了 **WS-A / WS-B / WS-C** 三條 workstream（API 對齊、E2E 差距修正、Mock→Live 遷移）。

本 Addendum 追蹤另外五條 **功能導向** 的 workstream，原分散於 `docs/02-design/specs/` 中，於 2026-04-15 重構時移入 `docs/01-define/wbs-workstreams/`，以統一「工作分解結構 = DEFINE 階段產出」的 5D 框架分類。

---

## Workstream 索引

| Workstream | 主題 | 檔案 | 狀態 | 完成度 |
|-----------|------|------|------|--------|
| **WS-D** | TRIZ 分層 Drill-Down 開發（Create Tab ①） | [`wbs-workstreams/WS-D--triz-layered-drilldown-development.md`](wbs-workstreams/WS-D--triz-layered-drilldown-development.md) | Active | ~88.6 % (62/70) |
| **WS-E** | 子系統介面開發（Create Tab ②） | [`wbs-workstreams/WS-E--subsystem-interface-development.md`](wbs-workstreams/WS-E--subsystem-interface-development.md) | Active | Draft · 部分進行中 |
| **WS-F** | Explore TC→多 PC 分解 | [`wbs-workstreams/WS-F--tc-to-multipc-decomposition.md`](wbs-workstreams/WS-F--tc-to-multipc-decomposition.md) | Active | 見檔案內 dashboard |
| **WS-G** | Explore L3 Su-Field 平行旁路 | [`wbs-workstreams/WS-G--l3-sf-parallel-check.md`](wbs-workstreams/WS-G--l3-sf-parallel-check.md) | Skeleton | 待排程 |
| **WS-H** | Playwright E2E 補測 | [`wbs-workstreams/WS-H--playwright-e2e-followup.md`](wbs-workstreams/WS-H--playwright-e2e-followup.md) | Skeleton | 待排程 |
| **Module 8.0** | Auto-TRIZ v2 Integration | 主 WBS [`E3x--wbs-development-plan.md`](E3x--wbs-development-plan.md) §Module 8.0 | Done | 100% (25/25) |

---

## 與主 WBS 的關係

- **主 WBS (A/B/C)**：以 **release 軸** 切分（API / E2E / Mock 三大遷移），面向整體里程碑 M1–M6。
- **Addendum (D–H)**：以 **功能模組軸** 切分（Tab ① TRIZ / Tab ② Subsystem / Explore / QA），面向具體 spec 實作。

兩者互補：D–H 的工作項在完成時會回饋至 A/B/C 的里程碑驗收（特別是 M4 Mock 清零與 Playwright 覆蓋）。

---

## 變更管控

Addendum 內 workstream 的範疇調整 → 在對應檔案頂部版本號記錄；跨 workstream 的架構決策 → 開新 ADR 於 `docs/01-define/adrs/`。

---

**最後更新**：2026-04-15（5D 重構，自 `docs/02-design/specs/` 搬入）
