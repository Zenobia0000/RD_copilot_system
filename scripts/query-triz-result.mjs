#!/usr/bin/env node
/**
 * query-triz-result.mjs — 抓出指定 project 的 TRIZ 正向分析 input + output。
 *
 * Usage:
 *   node scripts/query-triz-result.mjs <project_id>
 *
 * 透過 Supabase Management API 的 /database/query endpoint 直接跑 SQL。
 * 需要 .env 中：
 *   SUPABASE_ACCESS_TOKEN
 *   VITE_SUPABASE_PROJECT_ID
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
const PROJECT_REF = process.env.VITE_SUPABASE_PROJECT_ID;

if (!ACCESS_TOKEN || !PROJECT_REF) {
  console.error("❌ 缺少 SUPABASE_ACCESS_TOKEN 或 VITE_SUPABASE_PROJECT_ID");
  process.exit(1);
}

const projectId = process.argv[2];
if (!projectId) {
  console.error("Usage: node scripts/query-triz-result.mjs <project_id>");
  process.exit(1);
}

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
  const data = await res.json();
  return data;
}

function header(title) {
  console.log("\n" + "═".repeat(80));
  console.log("  " + title);
  console.log("═".repeat(80));
}

// ── 1. 專案基本資訊 ──
header(`Project ${projectId}`);
{
  const rows = await runSql(
    "project",
    `SELECT id, name, status, created_at FROM projects WHERE id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 2. Brief（mission）─ TaskDefinition 頁產出 ──
header("[INPUT 來源 1] briefs.mission  (TaskDefinition 頁)");
{
  const rows = await runSql(
    "brief",
    `SELECT mission FROM briefs WHERE project_id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 3. Constraints ──
header("[INPUT 來源 2] constraints  (TaskDefinition 頁)");
{
  const rows = await runSql(
    "constraints",
    `SELECT constraint_code, description, type, feasibility
     FROM constraints WHERE project_id = '${projectId}'
     ORDER BY constraint_code`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 4. KPIs ──
header("[INPUT 來源 3] kpis  (TaskDefinition 頁)");
{
  const rows = await runSql(
    "kpis",
    `SELECT kpi_name, target_value, unit, measurement_method
     FROM kpis WHERE project_id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 5. Socratic Q&A（Explore 頁產出）──
header("[INPUT 來源 4] socratic_questions  (Explore 頁)");
{
  const rows = await runSql(
    "socratic",
    `SELECT category, text AS question, answer
     FROM socratic_questions
     WHERE project_id = '${projectId}' AND answer IS NOT NULL AND length(trim(answer)) > 0
     ORDER BY created_at`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 6. CLD nodes / edges（Explore 頁產出）──
header("[INPUT 來源 5a] cld_nodes  (Explore 頁)");
{
  const rows = await runSql(
    "cld_nodes",
    `SELECT id, label FROM cld_nodes WHERE project_id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}
header("[INPUT 來源 5b] cld_edges  (Explore 頁)");
{
  const rows = await runSql(
    "cld_edges",
    `SELECT source, target, feedback_type FROM cld_edges WHERE project_id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 7. Contradictions（Explore 頁產出，TRIZ 的「主餐」）──
header("[INPUT 主體] contradictions  (Explore 頁 — 每條矛盾就是一次 /triz/solve-directed)");
{
  const rows = await runSql(
    "contradictions",
    `SELECT id, type, parent_contradiction_id,
            natural_description, engineering_statement,
            severity, improving_param, worsening_param,
            physical_contradiction
     FROM contradictions
     WHERE project_id = '${projectId}'
     ORDER BY (parent_contradiction_id IS NULL) DESC, id`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 8. directed_triz_solutions（每條矛盾的求解結果，migration 012）──
header("[OUTPUT] directed_triz_solutions  (TRIZ 方向導向分析結果)");
{
  const rows = await runSql(
    "directed",
    `SELECT id, contradiction_id, natural_description, severity,
            jsonb_array_length(all_solutions) AS n_solutions,
            jsonb_array_length(all_directions) AS n_directions,
            jsonb_array_length(scored_directions) AS n_scored,
            top1, top2, top1_score, top2_score,
            jsonb_array_length(COALESCE(sub_requirements,'[]'::jsonb)) AS n_sub_reqs,
            jsonb_array_length(COALESCE(coverage_audits,'[]'::jsonb)) AS n_audits,
            combined_direction,
            updated_at
     FROM directed_triz_solutions
     WHERE project_id = '${projectId}'
     ORDER BY updated_at DESC`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 9. 跨矛盾整併結果 ──
header("[OUTPUT] triz_consolidation_results  (跨矛盾整併)");
{
  const rows = await runSql(
    "consolidation",
    `SELECT status, adopted_directions, conflict_report, integration_advice, updated_at
     FROM triz_consolidation_results
     WHERE project_id = '${projectId}'
     ORDER BY updated_at DESC`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

// ── 10. 完整明細：每條矛盾 → 完整 top1 / top2 / sub_requirements / coverage_audits ──
header("[OUTPUT 明細] 每條矛盾的完整方向結果（all_directions / sub_requirements / coverage_audits）");
{
  const rows = await runSql(
    "directed_full",
    `SELECT contradiction_id,
            natural_description,
            all_directions,
            sub_requirements,
            coverage_audits,
            top1, top2
     FROM directed_triz_solutions
     WHERE project_id = '${projectId}'`,
  );
  console.log(JSON.stringify(rows, null, 2));
}

console.log("\n✅ 完成");
