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
