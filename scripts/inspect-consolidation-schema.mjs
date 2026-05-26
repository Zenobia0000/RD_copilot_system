#!/usr/bin/env node
/**
 * inspect-consolidation-schema.mjs
 * 透過 Supabase Management API 查詢 triz_consolidation_results 的欄位，
 * 並印出查詢結果（不像 run-migration.mjs 只回報 success/error）。
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
const PROJECT_ID = process.env.VITE_SUPABASE_PROJECT_ID;

const url = `https://api.supabase.com/v1/projects/${PROJECT_ID}/database/query`;
const sql = `
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'triz_consolidation_results'
ORDER BY ordinal_position;
`;

const res = await fetch(url, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${ACCESS_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: sql }),
});

if (!res.ok) {
  console.error(`API ${res.status}: ${res.statusText}`);
  console.error(await res.text());
  process.exit(1);
}

const data = await res.json();
console.log("==== columns of triz_consolidation_results ====");
console.log(JSON.stringify(data, null, 2));

// 期望欄位檢核：每次 migration 更新都要在這裡加進來，方便部署時偵測缺欄位。
// migration 020/021: intra_compatibility / was_user_picked
// migration 022:     candidate_pools / exhausted_contradictions / total_rounds
// migration 023:     verdict_lite  （取代舊 verdict_card Q1–Q8）
const EXPECTED_COLUMNS = [
  "status",
  "adopted_directions",
  "conflict_report",
  "integration_advice",
  "intra_compatibility",
  "was_user_picked",
  "candidate_pools",
  "exhausted_contradictions",
  "total_rounds",
  "verdict_lite",
];

// Supabase Management API 回傳的 result 可能是 array 或 {result: [...]}.
const rows = Array.isArray(data?.result)
  ? data.result
  : Array.isArray(data)
    ? data
    : [];
const presentNames = new Set(rows.map((r) => r.column_name));
const missing = EXPECTED_COLUMNS.filter((c) => !presentNames.has(c));

if (missing.length > 0) {
  console.warn("\n⚠️  缺少以下預期欄位 — 請執行對應 migration：");
  for (const m of missing) console.warn(`  - ${m}`);
  console.warn(
    "  執行：node scripts/run-migration.mjs supabase/migrations/<檔名>.sql\n",
  );
  process.exit(2);
} else {
  console.log("\n✅ 所有預期欄位皆存在（含 verdict_lite）。");
}

// 額外提示：若還在的話，verdict_card 是已棄用的舊欄位，未來會 DROP。
if (presentNames.has("verdict_card")) {
  console.log(
    "\nℹ️  注意：DB 仍有舊 `verdict_card` 欄位（Q1–Q8），新版已停用、預計於 migration 024 DROP。",
  );
}
