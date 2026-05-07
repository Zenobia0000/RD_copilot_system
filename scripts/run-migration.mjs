#!/usr/bin/env node
/**
 * run-migration.mjs — 透過 Supabase Management API 執行 .sql migration 檔案
 *
 * Usage:
 *   node scripts/run-migration.mjs supabase/migrations/016_engineering_spec_draft_packs.sql
 *
 * 需要 .env 中包含：
 *   SUPABASE_ACCESS_TOKEN   — Supabase dashboard 個人 access token
 *   VITE_SUPABASE_PROJECT_ID — 專案 ref (e.g. ybhlybmasoxshzkcaohj)
 */

import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

// ── 讀取 .env ──────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));
const envText = readFileSync(resolve(__dirname, "..", ".env"), "utf-8");
for (const line of envText.split("\n")) {
  const m = line.match(/^([A-Z_][A-Z0-9_]*)=["']?(.+?)["']?\s*$/);
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
}

const ACCESS_TOKEN = process.env.SUPABASE_ACCESS_TOKEN;
const PROJECT_ID = process.env.VITE_SUPABASE_PROJECT_ID;

if (!ACCESS_TOKEN) {
  console.error("❌ 缺少 SUPABASE_ACCESS_TOKEN（請檢查 .env）");
  process.exit(1);
}
if (!PROJECT_ID) {
  console.error("❌ 缺少 VITE_SUPABASE_PROJECT_ID（請檢查 .env）");
  process.exit(1);
}

// ── 讀取 SQL 檔案 ──────────────────────────────────────────
const sqlPath = process.argv[2];
if (!sqlPath) {
  console.error("Usage: node scripts/run-migration.mjs <path-to-sql-file>");
  process.exit(1);
}

const fullPath = resolve(sqlPath);
let sql;
try {
  sql = readFileSync(fullPath, "utf-8");
} catch (err) {
  console.error(`❌ 無法讀取檔案: ${fullPath}`);
  console.error(err.message);
  process.exit(1);
}

console.log(`📄 SQL 檔案: ${fullPath}`);
console.log(`📦 專案 ID:  ${PROJECT_ID}`);
console.log(`📏 SQL 長度: ${sql.length} chars`);
console.log("⏳ 正在執行 migration...\n");

// ── 呼叫 Supabase Management API ──────────────────────────
const url = `https://api.supabase.com/v1/projects/${PROJECT_ID}/database/query`;

const res = await fetch(url, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${ACCESS_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: sql }),
});

if (!res.ok) {
  const text = await res.text();
  console.error(`❌ API 回應 ${res.status}: ${res.statusText}`);
  console.error(text);
  process.exit(1);
}

const data = await res.json();

// Management API 回傳陣列，每個元素對應一個 SQL statement 的結果
if (Array.isArray(data)) {
  const hasError = data.some((d) => d.error);
  if (hasError) {
    console.error("❌ Migration 執行有錯誤:");
    for (const d of data) {
      if (d.error) console.error("  →", d.error);
    }
    process.exit(1);
  }
  console.log(`✅ Migration 成功！共執行 ${data.length} 個 statement(s)。`);
} else {
  // 單一結果或其他格式
  if (data.error) {
    console.error("❌ Migration 執行錯誤:", data.error);
    process.exit(1);
  }
  console.log("✅ Migration 成功！");
  console.log(JSON.stringify(data, null, 2));
}
