#!/usr/bin/env node
/**
 * cleanup-orphan-dts.mjs — 刪除孤兒 directed_triz_solutions row。
 *
 * 場景：UI 允許 RD 在識別 contradiction 後跑 /triz/solve-directed，把 DTS 寫進 DB；
 * 之後若 RD 把這條 contradiction 刪了（或它被替換掉），contradictions 表的 row 沒了，
 * 但 directed_triz_solutions row 還在 → 變成孤兒，整併會把它撈進來跨矛盾比對。
 *
 * 此 script 用 Supabase Management API 直接跑 SQL，刪除所有「contradiction_id 已不在
 * contradictions 表中」的 directed_triz_solutions row。
 *
 * Usage:
 *   node scripts/cleanup-orphan-dts.mjs                # 全 project 一次清
 *   node scripts/cleanup-orphan-dts.mjs <project_id>   # 只清指定 project
 *   node scripts/cleanup-orphan-dts.mjs --dry-run      # 只列出不刪
 *
 * 需要 .env 中：
 *   SUPABASE_ACCESS_TOKEN
 *   VITE_SUPABASE_PROJECT_ID
 *
 * Backend 也會在 consolidate_solutions 啟動時做 lazy GC（_gc_orphan_directed_solutions），
 * 這個 script 是「一次性把全 DB 髒資料清乾淨」的工具。
 */

import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const envText = readFileSync(resolve(__dirname, "..", ".env"), "utf-8");
for (const line of envText.split("\n")) {
  const m = line.match(/^([A-Z_][A-Z0-9_]*)=["']?(.+?)["']?\s*$/);
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
}

const ACCESS_TOKEN = process.env.SUPABASE_ACCESS_TOKEN;
const PROJECT_REF = process.env.VITE_SUPABASE_PROJECT_ID;

if (!ACCESS_TOKEN || !PROJECT_REF) {
  console.error("❌ 缺少 SUPABASE_ACCESS_TOKEN 或 VITE_SUPABASE_PROJECT_ID");
  process.exit(1);
}

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const projectId = args.find((a) => !a.startsWith("--"));

const url = `https://api.supabase.com/v1/projects/${PROJECT_REF}/database/query`;

async function runSql(label, sql) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${ACCESS_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: sql }),
  });
  if (!res.ok) {
    const txt = await res.text();
    console.error(`❌ [${label}] HTTP ${res.status}: ${txt}`);
    return null;
  }
  return res.json();
}

// 1. 列出孤兒
// 注意：contradictions.id 是 uuid、directed_triz_solutions.contradiction_id 是 text，
// JOIN 時要 cast 成同型別。
const whereProject = projectId ? `AND dts.project_id = '${projectId}'` : "";
const previewSql = `
  SELECT dts.id, dts.project_id, dts.contradiction_id, dts.natural_description, dts.updated_at
  FROM directed_triz_solutions dts
  LEFT JOIN contradictions c ON c.id::text = dts.contradiction_id
  WHERE c.id IS NULL ${whereProject}
  ORDER BY dts.updated_at DESC
`;

console.log("═".repeat(80));
console.log("  孤兒 directed_triz_solutions" + (projectId ? ` (project=${projectId})` : ""));
console.log("═".repeat(80));

const preview = await runSql("preview", previewSql);
if (!preview) process.exit(1);

const orphans = preview ?? [];
console.log(`找到 ${orphans.length} 條孤兒。`);
if (orphans.length === 0) {
  console.log("✅ 沒有孤兒可清。");
  process.exit(0);
}
console.log(JSON.stringify(orphans, null, 2));

if (dryRun) {
  console.log("\n⚠️ --dry-run 模式，不刪。");
  process.exit(0);
}

// 2. 執行刪除
const deleteSql = `
  DELETE FROM directed_triz_solutions
  WHERE id IN (
    SELECT dts.id
    FROM directed_triz_solutions dts
    LEFT JOIN contradictions c ON c.id::text = dts.contradiction_id
    WHERE c.id IS NULL ${whereProject}
  )
  RETURNING id
`;

console.log("\n執行刪除...");
const deleted = await runSql("delete", deleteSql);
console.log(`✅ 已刪除 ${deleted?.length ?? 0} 條孤兒。`);
