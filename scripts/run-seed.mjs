/**
 * CLI seed runner — executes the same logic as seed.ts but from Node.js.
 * Usage: node scripts/run-seed.mjs
 */
import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

// Manual .env parser (no dotenv dependency)
const __dirname = dirname(fileURLToPath(import.meta.url));
const envText = readFileSync(resolve(__dirname, '..', '.env'), 'utf-8');
for (const line of envText.split('\n')) {
  const m = line.match(/^([A-Z_][A-Z0-9_]*)=["']?(.+?)["']?\s*$/);
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
}

const url = process.env.VITE_SUPABASE_URL;
const key = process.env.VITE_SUPABASE_SERVICE_ROLE_KEY;
if (!url || !key) { console.error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_SERVICE_ROLE_KEY'); process.exit(1); }

const db = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });

async function ins(table, data, label) {
  const { error } = await db.from(table).insert(data);
  if (error) throw new Error(`[seed] ${label}: ${error.message}`);
}
async function insRet(table, data, label) {
  const { data: rows, error } = await db.from(table).insert(data).select();
  if (error) throw new Error(`[seed] ${label}: ${error.message}`);
  return rows;
}

// Get first user for created_by
async function getUserId() {
  const { data } = await db.auth.admin.listUsers({ page: 1, perPage: 1 });
  if (data?.users?.[0]) return data.users[0].id;
  return '00000000-0000-0000-0000-000000000000';
}

// ── Clear ──
async function clearAll() {
  const names = [
    'E-Bike 馬達控制器升級', 'E-Bike 電池管理系統 BMS', 'E-Bike 車架結構輕量化',
    '🏆 E-Bike 馬達控制器升級', '🔋 E-Bike 電池管理系統 BMS', '🚲 E-Bike 車架結構輕量化',
  ];
  for (const name of names) {
    await db.from('projects').delete().eq('name', name);
  }
  console.log('[seed] Cleared all showcase data.');
}

// ============================================================================
// PROJECT 1 — 馬達控制器升級 (Phase III COMPLETED)
// ============================================================================
async function seedProject1(uid) {
  const [project] = await insRet('projects', {
    name: 'E-Bike 馬達控制器升級',
    description: '【完整案例】馬達控制器從 Si MOSFET 升級至 GaN 拓撲，達成 95%+ 效率目標。展示從問題定義到決策簽核的完整 TRIZ 流程。',
    status: 'completed', phase: 'Phase III', progress: 100,
    mission: '重新設計馬達控制器，在峰值負載下達到 95%+ 效率，同時降低 30% 散熱量。',
    phase_progress: { '1.1': 'passed', '1.2': 'passed', '1.3': 'passed', '2.1': 'passed', '2.2': 'passed', '2.3': 'passed', '3.1': 'passed', '3.2': 'passed', '3.3': 'passed' },
    quick_stats: { contradictions_count: 3, assumptions_count: 5, alternatives_count: 3, risks_count: 3, experiments_count: 3, evidence_items_count: 5 },
    must_criteria_config: [
      { id: 'M1', label: '效率 ≥ 95%', source: 'KPI: 峰值效率', threshold: '≥ 95%' },
      { id: 'M2', label: '散熱餘裕 ≥ 20%', source: 'KPI: 散熱降幅', threshold: '≥ 20% margin' },
      { id: 'M3', label: 'CISPR 25 Class 5', source: 'C-03: SMT 相容 + EMI 法規', threshold: 'Pass CISPR 25 Class 5' },
      { id: 'M4', label: '成本 ≤ $12', source: 'C-02: BOM ≤ $18 (控制器分攤)', threshold: '≤ $12 USD' },
      { id: 'M5', label: '可製造性 (SMT 相容)', source: 'C-03: 現有 SMT 產線', threshold: '現有產線可生產' },
      { id: 'M6', label: 'ISO 26262 ASIL-B', source: '安全法規', threshold: 'ASIL-B 認證' },
    ],
    gates_passed: 8, gates_total: 8, created_by: uid,
  }, 'project-1');
  const pid = project.id;

  await ins('briefs', {
    project_id: pid,
    mission: '重新設計馬達控制器，在峰值負載下達到 95%+ 效率，同時降低 30% 散熱量。',
    task_definition_5w1h: {
      who: 'Delta Electronics 電力電子事業部', what: '馬達控制器 PCB 與韌體重新設計',
      where: 'E-bike 動力傳動系統整合', when: '2026 Q3 量產目標',
      why: '現行版本在持續爬坡場景超出散熱預算', how: '拓撲最佳化 + GaN MOSFET 評估 + 熱模擬',
    },
  }, 'brief-1');

  await ins('constraints', [
    { project_id: pid, constraint_code: 'C-01', description: '必須符合現有馬達外殼尺寸 (120×80×25mm)', source: '機構團隊', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-02', description: 'BOM 成本不得超過 $18 USD (10k 量級)', source: '產品管理', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-03', description: '優先使用無鉛焊接、相容現有 SMT 產線', source: '製造部', type: 'soft', feasibility: 'verified' },
  ], 'constraints-1');

  const kpis1 = await insRet('kpis', [
    { project_id: pid, kpi_name: '峰值效率', target_value: '95', unit: '%', measurement_method: '48V 輸入額定扭矩 Dyno 測試', current_value: '97.2', current_status: 'on_track' },
    { project_id: pid, kpi_name: '散熱降幅', target_value: '30', unit: '% 降低', measurement_method: '500W 持續負載 IR 熱成像', current_value: '42', current_status: 'on_track' },
    { project_id: pid, kpi_name: '單位 BOM 成本', target_value: '18', unit: 'USD', measurement_method: '10k 量級 BOM rollup', current_value: '11.80', current_status: 'on_track' },
  ], 'kpis-1');
  const kpiIds1 = kpis1.map(k => k.id);

  await ins('socratic_questions', [
    { project_id: pid, category: 'clarification', text: '「峰值負載」的具體操作點為何？', answer: '48V 輸入、15A 連續、25A 突波 30 秒 — 對應爬坡模式。', tagged_as_assumption: false, tagged_as_contradiction: false },
    { project_id: pid, category: 'assumption', text: '現有被動散熱器是否維持不變？', answer: '是，但需要驗證新拓撲的散熱是否足夠。', tagged_as_assumption: true, tagged_as_contradiction: false },
    { project_id: pid, category: 'consequence', text: '切換到 GaN MOSFET 後，Gate driver 的成本與複雜度會如何變化？', answer: 'Gate driver 成本增加約 $1.50，但開關損耗大幅降低。', tagged_as_assumption: false, tagged_as_contradiction: true },
    { project_id: pid, category: 'counter', text: '是否有可能透過拓撲變更在不使用 GaN 的情況下達標？', answer: '評估後效率僅提升 2%，不足以達到 95% 目標。', tagged_as_assumption: false, tagged_as_contradiction: false },
    { project_id: pid, category: 'reframing', text: '如果完全不考慮散熱問題，馬達控制器的瓶頸在哪？', answer: '開關損耗仍為主要瓶頸，佔整體損耗 60%。', tagged_as_assumption: false, tagged_as_contradiction: false },
    { project_id: pid, category: 'origin', text: '散熱預算超標的根本原因是什麼？', answer: '高負載爬坡場景 Rds(on) 損耗佔 70%，Si MOSFET 材料極限。', tagged_as_assumption: false, tagged_as_contradiction: true },
    { project_id: pid, category: 'reframing', text: '「必須用被動散熱」這個結論是否受到過去經驗的偏見影響？', answer: '確實如此，主動散熱（風扇/液冷）在 e-bike 場景並非不可行。', tagged_as_assumption: true, tagged_as_contradiction: false },
  ], 'socratic-1');

  const contradictions = await insRet('contradictions', [
    { project_id: pid, natural_description: '提高開關頻率改善效率，但增加 EMI 排放', improving_param: 21, worsening_param: 31, engineering_statement: 'PWM 頻率從 20kHz 提升至 100kHz，降低導通損失但超過 CISPR 25 Class 5 限制。', type: 'TC', severity: 'fatal', resolved: true },
    { project_id: pid, natural_description: 'GaN MOSFET 降低散熱但超出 BOM 預算', improving_param: 17, worsening_param: 32, engineering_statement: 'GaN FET 降低 Rds(on) 損耗 40%，但 BOM 增加 $3.20。', type: 'TC', severity: 'major', resolved: true },
    { project_id: pid, natural_description: '緊湊 PCB 佈局需求 vs 散熱間距需求', physical_contradiction: '銅面積必須同時大（散熱）又小（空間限制）。', type: 'PC', severity: 'minor', resolved: true },
  ], 'contradictions-1');
  const cids = contradictions.map(c => c.id);

  await ins('assumptions', [
    { project_id: pid, code: 'A-01', content: '被動散熱器足以應對重新設計的控制器', source: '機構團隊口頭確認', source_type: 'manual', worst_consequence: '持續負載下熱節流', worst_severity: 'critical', status: 'validated', verification_stage: 'completed' },
    { project_id: pid, code: 'A-02', content: 'GaN MOSFET 12 個月內達到與 Si 同等成本', source: '供應商藍圖簡報', source_type: 'manual', worst_consequence: 'BOM 超標需回滾設計', worst_severity: 'high', status: 'validated', verification_stage: 'completed' },
    { project_id: pid, code: 'A-03', content: '現有 SMT 產線可處理 0201 被動元件', source: '製造能力清單', source_type: 'manual', worst_consequence: '需外包至專業代工', worst_severity: 'medium', status: 'validated', verification_stage: 'completed' },
    { project_id: pid, code: 'A-04', content: '展頻調變可抑制 EMI 且不犧牲效率', source: '文獻回顧', source_type: 'explore_tag', worst_consequence: '需額外遮蔽或濾波', worst_severity: 'high', status: 'validated', verification_stage: 'completed' },
    { project_id: pid, code: 'A-05', content: '馬達電感變異不影響控制器穩定性', source: '需調查', source_type: 'unknown_convert', worst_consequence: '電流迴路不穩定', worst_severity: 'critical', status: 'validated', verification_stage: 'completed' },
  ], 'assumptions-1');

  const nodes = await insRet('cld_nodes', [
    { project_id: pid, label: '開關頻率', x: 100, y: 200, node_type: 'variable', is_leverage: true },
    { project_id: pid, label: '效率', x: 300, y: 100, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'EMI 排放', x: 300, y: 300, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: '散熱量', x: 500, y: 200, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'BOM 成本', x: 500, y: 400, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'GaN 採用', x: 100, y: 400, node_type: 'variable', is_leverage: true },
    { project_id: pid, label: 'PCB 面積', x: 700, y: 300, node_type: 'variable', is_leverage: false },
  ], 'cld-nodes-1');
  const nids = nodes.map(n => n.id);
  await ins('cld_edges', [
    { project_id: pid, from_node: nids[0], to_node: nids[1], polarity: '+' },
    { project_id: pid, from_node: nids[0], to_node: nids[2], polarity: '+' },
    { project_id: pid, from_node: nids[1], to_node: nids[3], polarity: '-' },
    { project_id: pid, from_node: nids[5], to_node: nids[1], polarity: '+' },
    { project_id: pid, from_node: nids[5], to_node: nids[4], polarity: '+' },
    { project_id: pid, from_node: nids[3], to_node: nids[6], polarity: '+' },
  ], 'cld-edges-1');

  await ins('triz_solutions', [
    { project_id: pid, contradiction_id: cids[0], path: 'TC', principle_number: 28, principle_name: '機械替代', suggestion: '以諧振軟切換拓撲替代固定頻率 PWM，高頻且不增加 EMI。將開關損耗降低 60%，同時 EMI 頻譜分散不超過 CISPR 25 限制。', status: 'adopted' },
    { project_id: pid, contradiction_id: cids[0], path: 'TC', principle_number: 19, principle_name: '週期性動作', suggestion: '使用展頻調變（Spread Spectrum）將 EMI 能量分散到寬頻段。', status: 'adopted' },
    { project_id: pid, contradiction_id: cids[1], path: 'TC', principle_number: 35, principle_name: '參數變更', suggestion: '使用最佳化 Gate drive 的 Si MOSFET（低 Qg 版本），縮小與 GaN 的效率差距。', status: 'rejected' },
    { project_id: pid, contradiction_id: cids[1], path: 'TC', principle_number: 6, principle_name: '萬用性', suggestion: '選用整合 Gate driver 的 GaN 模組，減少分立元件數量抵消成本增加。', status: 'adopted' },
    { project_id: pid, contradiction_id: cids[2], path: 'PC', principle_number: 1, principle_name: '分割', suggestion: '將功率級分離到鋁基板（IMS），訊號走線保留在緊湊 FR4 上。銅面積在 IMS 上最大化，FR4 面積最小化。', status: 'adopted' },
  ], 'triz-1');

  const subsys = await insRet('subsystems', [
    { project_id: pid, name: '功率級', reason: '含 MOSFET、Gate driver、Bus 電容 — 主要熱源與效率瓶頸', related_contradictions: [cids[0], cids[1]], confirmed: true, source: 'rd' },
    { project_id: pid, name: '控制與感測', reason: 'MCU、電流感測器、位置解碼 — 決定控制迴路頻寬與穩定性', related_contradictions: [], confirmed: true, source: 'rd' },
    { project_id: pid, name: '散熱結構', reason: '散熱片、TIM、PCB 銅面 — 熱阻路徑關鍵', related_contradictions: [cids[2]], confirmed: true, source: 'rd' },
  ], 'subsystems-1');

  // @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions
  // await ins('scamper_variants', [...], 'scamper-1');

  const alts = await insRet('alternatives', [
    {
      project_id: pid, name: 'GaN 軟切換 + IMS 分離方案',
      mechanism: 'GaN 諧振軟切換 + IMS 基板功率級分離 + 展頻調變 EMI 抑制。諧振頻率 200kHz，死區時間 50ns，展頻 ±10%。效率 97.2%，EMI 通過 CISPR 25 Class 5。',
      source: 'triz', key_assumption_ids: ['A-01', 'A-02', 'A-04'],
      must_scores: { M1: 'pass', M2: 'pass', M3: 'pass', M4: 'pass', M5: 'pass', M6: 'pass', description: 'GaN 方案：效率 97.2%、散熱降 40%、通過 CISPR 25 Class 5 EMI 認證', assumptions: ['GaN 元件可靠性滿足車規 AEC-Q101', 'IMS 鋁基板供應鏈穩定'], mustCriteria: [{ id: 'M1', label: '效率 ≥ 95%', passed: true }, { id: 'M2', label: '散熱餘裕 ≥ 20%', passed: true }, { id: 'M3', label: 'CISPR 25 Class 5', passed: true }, { id: 'M4', label: '成本 ≤ $12', passed: true }, { id: 'M5', label: '可製造性 (SMT 相容)', passed: true }, { id: 'M6', label: 'ISO 26262 ASIL-B', passed: true }], risks: [{ id: 'R1', description: 'GaN 供應商單一來源風險', severity: 'major', mitigation: '備選 EPC 2nd source 驗證中' }], minValidation: '原型板 thermal cycling 測試 500 次 + EMI 掃描' },
      interface_contract: { envelope: '120×80×25mm (符合現有外殼)', loadPath: 'IMS 鋁基板承載功率級熱負荷', signalPath: 'CAN Bus + SPI (MCU↔Gate driver)', thermalPath: '功率級→IMS→鋁外殼→空氣 (總熱阻 2.1°C/W)', datumTolerance: 'IMS-FR4 連接器同軸度 0.1mm', serviceability: '側蓋可拆 + IMS 模組可獨立更換' },
      pre_cad_scores: { must: 5, decoupling: 5, testability: 4, failureMech: 4, mvpCadEffort: 3 },
      overall_pass: true, cad_status: 'completed',
    },
    {
      project_id: pid, name: '最佳化 Si + 加厚銅面方案',
      mechanism: '低 Qg Si MOSFET (IRF7389) + 4oz 內層銅 PCB + 加大鋁散熱片。透過最佳化 Gate 驅動電路減少開關損耗 15%。效率 93.5%。',
      source: 'triz', key_assumption_ids: ['A-03'],
      must_scores: { M1: 'fail', M2: 'pass', M3: 'pass', M4: 'pass', M5: 'pass', M6: 'pass', description: 'Si 最佳化方案：效率 93.5%、散熱依賴加大面積', assumptions: ['4oz 銅 PCB 內層製程穩定，不影響信號完整性'], mustCriteria: [{ id: 'M1', label: '效率 ≥ 95%', passed: false }, { id: 'M2', label: '散熱餘裕 ≥ 20%', passed: true }, { id: 'M3', label: 'CISPR 25 Class 5', passed: true }, { id: 'M4', label: '成本 ≤ $12', passed: true }, { id: 'M5', label: '可製造性 (SMT 相容)', passed: true }, { id: 'M6', label: 'ISO 26262 ASIL-B', passed: true }], risks: [{ id: 'R2', description: '效率未達 95% 目標', severity: 'fatal', mitigation: '需加入 LLC 諧振輔助' }], minValidation: '效率量測 under full load (48V/15A)' },
      interface_contract: { envelope: '120×80×30mm (高度增加 5mm 容納散熱片)', loadPath: '4oz 銅面直接承載電流路徑', signalPath: 'CAN Bus (標準協議)', thermalPath: '功率級→4oz PCB→散熱片→空氣 (總熱阻 3.5°C/W)', datumTolerance: '散熱片與 PCB 平整度 0.05mm', serviceability: '散熱片螺絲固定可拆換' },
      pre_cad_scores: { must: 4, decoupling: 3, testability: 4, failureMech: 3, mvpCadEffort: 4 },
      overall_pass: false, cad_status: 'completed',
    },
    {
      project_id: pid, name: '傳統 Si + 標準 PCB 基線',
      mechanism: '傳統 Si MOSFET + 標準 2oz PCB + 鋁散熱片。不做任何拓撲變更，作為對照基線方案。效率 89.1%。',
      source: 'manual', key_assumption_ids: [],
      must_scores: { M1: 'fail', M2: 'fail', M3: 'pass', M4: 'fail', M5: 'pass', M6: 'marginal', description: '基線方案作為對照，未做任何優化', mustCriteria: [{ id: 'M1', label: '效率 ≥ 95%', passed: false }, { id: 'M2', label: '散熱餘裕 ≥ 20%', passed: false }, { id: 'M3', label: 'CISPR 25 Class 5', passed: true }, { id: 'M4', label: '成本 ≤ $12', passed: false }, { id: 'M5', label: '可製造性 (SMT 相容)', passed: true }, { id: 'M6', label: 'ISO 26262 ASIL-B', passed: null }], risks: [], minValidation: '無' },
      interface_contract: { envelope: '120×80×25mm', loadPath: '2oz 標準銅面', signalPath: 'CAN Bus', thermalPath: '標準鋁散熱片 (熱阻 5.0°C/W)', datumTolerance: '標準', serviceability: '整體更換' },
      pre_cad_scores: { must: 2, decoupling: 2, testability: 3, failureMech: 2, mvpCadEffort: 5 },
      overall_pass: false, cad_status: 'not_started',
    },
  ], 'alternatives-1');

  await ins('concept_routes', [
    { project_id: pid, route_type: 'composite', composition: [{ solutionId: 'triz-28', sourcePrinciple: '#28 機械替代', concrete: 'GaN 諧振軟切換拓撲 (200kHz)', dimension: '拓撲', adoptionType: 'M2' }, { solutionId: 'triz-1', sourcePrinciple: '#1 分割', concrete: 'IMS 鋁基板功率級分離', dimension: '空間', adoptionType: 'M1' }, { solutionId: 'triz-19', sourcePrinciple: '#19 週期性動作', concrete: '展頻調變 EMI 抑制 (±10%)', dimension: '頻率', adoptionType: 'M2' }], composition_rationale: '結合 TRIZ 原理 #28(軟切換) + #1(空間分離) + #19(展頻)，三者分別作用於拓撲/空間/頻率維度。#28+#19 形成互相強化 (M2)，#1 獨立維度 (M1)。全面解決效率/EMI/散熱三大矛盾。', anti_pattern_warnings: [] },
    { project_id: pid, route_type: 'single', composition: [{ solutionId: 'triz-35', sourcePrinciple: '#35 參數變更', concrete: '低 Qg Si MOSFET + 4oz 銅面 + 加大散熱片', dimension: '參數最佳化', adoptionType: 'M4' }], composition_rationale: '保守方案，不改變拓撲僅最佳化參數。與 GaN 路線物理互斥 (M4)，作為獨立 Route。', anti_pattern_warnings: ['與現有方案差異小，可能陷入路徑依賴'] },
  ], 'concept-routes-1');

  await ins('compatibility_pairs', [
    { project_id: pid, solution_a_id: alts[0].id, solution_b_id: alts[1].id, result: 'exclusive', adoption_type: 'M4', reason: '兩方案核心拓撲互斥（GaN 軟切換 vs Si 硬切換），無法在同一功率級共存。散熱策略可作為 M3 各自採納至不同子系統。' },
  ], 'compat-1');

  await ins('evidence_matrix', [
    { project_id: pid, assumption_code: 'A-01', summary: '被動散熱器足以應對', current_level: 'E3', is_north_star: true },
    { project_id: pid, assumption_code: 'A-02', summary: 'GaN 成本達標', current_level: 'E3', is_north_star: false },
    { project_id: pid, assumption_code: 'A-03', summary: 'SMT 產線相容', current_level: 'E4', is_north_star: false },
    { project_id: pid, assumption_code: 'A-04', summary: '展頻調變 EMI 抑制', current_level: 'E3', is_north_star: true },
    { project_id: pid, assumption_code: 'A-05', summary: '馬達電感穩定性', current_level: 'E2', is_north_star: false },
  ], 'evidence-1');

  await ins('risks', [
    { project_id: pid, description: 'GaN 高溫退磁導致控制失靈', failure_mode: 'MOSFET 熱崩潰', probability: 2, severity: 4, mitigation: '增加 NTC 溫度監控 + 韌體降載保護' },
    { project_id: pid, description: 'IMS 基板供應商集中風險', failure_mode: '供應鏈斷裂', probability: 2, severity: 3, mitigation: '認證第二供應商 + 安全庫存 2 週' },
    { project_id: pid, description: '展頻調變與馬達位置感測干擾', failure_mode: 'EMI 互擾', probability: 3, severity: 3, mitigation: '增加屏蔽層 + EMI 預認證測試' },
  ], 'risks-1');

  await ins('experiments', [
    { project_id: pid, user_id: uid, name: 'GaN 熱循環 1000 次測試', linked_assumptions: ['A-01', 'A-02'], evidence_level: 'E3', method: '溫度循環箱 -40°C ~ 125°C', success_criteria: '0 失效', status: 'Done', result: '通過，0 失效' },
    { project_id: pid, user_id: uid, name: '展頻調變 EMI 掃描', linked_assumptions: ['A-04'], evidence_level: 'E3', method: 'CISPR 25 Class 5 預掃描', success_criteria: '所有頻段低於限制 6dB', status: 'Done', result: '通過，餘量 8dB' },
    { project_id: pid, user_id: uid, name: 'SMT 0201 試產', linked_assumptions: ['A-03'], evidence_level: 'E4', method: '50 片試產 + AOI 檢查', success_criteria: '良率 ≥ 99%', status: 'Done', result: '良率 99.6%' },
  ], 'experiments-1');

  await ins('evidence_entries', [
    { project_id: pid, user_id: uid, title: 'Dyno 效率測試結果', measured_value: '97.2', unit: '%', evidence_level: 'E3', method: '48V Dyno 測試', notes: '實測效率超越目標 2.2%', measured_at: '2026-02-20T10:00:00Z', kpi_id: kpiIds1[0], linked_assumption_codes: ['A-01', 'A-04'], linked_must_ids: ['M1'] },
    { project_id: pid, user_id: uid, title: 'IR 熱成像散熱測試', measured_value: '42', unit: '% 降低', evidence_level: 'E3', method: '500W 持續負載 IR 熱成像', notes: '散熱降幅超過目標 12%', measured_at: '2026-02-22T14:00:00Z', kpi_id: kpiIds1[1], linked_assumption_codes: ['A-01'], linked_must_ids: ['M2'] },
    { project_id: pid, user_id: uid, title: 'BOM 成本核算', measured_value: '11.80', unit: 'USD', evidence_level: 'E3', method: '10k 量級 BOM rollup', notes: '含 GaN 模組，低於 $12 目標', measured_at: '2026-02-25T09:00:00Z', kpi_id: kpiIds1[2], linked_assumption_codes: ['A-02'], linked_must_ids: ['M4'] },
  ], 'evidence-entries-1');

  const [decision] = await insRet('decisions', {
    project_id: pid, selected_alternative_id: alts[0].id, selected_alternative_name: 'GaN 軟切換 + IMS 分離方案',
    rationale: '綜合 WANT 評分最高（加權 287 分），所有 MUST 條件通過，且 EMI、散熱兩大矛盾均已透過 TRIZ 原理解決並以 E3 等級驗證。',
    risk_acceptance: '已識別 3 項風險，均有緩解措施並完成驗證。剩餘風險等級為可接受（中低）。',
    decision_date: '2026-03-01', status: 'signed',
  }, 'decision-1');

  const criteria = await insRet('want_criteria', [
    { project_id: pid, name: '效率餘量', weight: 9, description: '超過 95% 目標的餘量越大越好' },
    { project_id: pid, name: '散熱安全係數', weight: 8, description: '散熱餘裕度' },
    { project_id: pid, name: '成本競爭力', weight: 7, description: 'BOM 成本越低越好' },
    { project_id: pid, name: 'EMI 餘量', weight: 6, description: 'EMI 低於限制的餘量' },
    { project_id: pid, name: '製造難度', weight: 5, description: '越容易量產越好' },
    { project_id: pid, name: '可測試性', weight: 4, description: '易於進行 DVT 驗證' },
    { project_id: pid, name: '驗證可行性', weight: 8, description: '假設能否在時限內驗證' },
  ], 'want-criteria-1');
  const crids = criteria.map(c => c.id);

  const weights = [9,8,7,6,5,4,8];
  const s1 = [9,8,7,9,6,8,9];
  const s2 = [7,7,8,7,8,7,7];
  const wantScores = [];
  crids.forEach((cid, i) => {
    wantScores.push({ project_id: pid, criterion_id: cid, alternative_id: alts[0].id, score: s1[i], evidence: `方案 A: ${s1[i]}/10`, weighted_total: s1[i] * weights[i] });
    wantScores.push({ project_id: pid, criterion_id: cid, alternative_id: alts[1].id, score: s2[i], evidence: `方案 B: ${s2[i]}/10`, weighted_total: s2[i] * weights[i] });
  });
  await ins('want_scores', wantScores, 'want-scores-1');

  await ins('adverse_consequences', [
    { project_id: pid, alternative_id: alts[0].id, description: 'GaN gate driver 複雜度增加維修困難', probability: 'medium', severity: 'low', level: 'M', mitigation: '標準化維修 SOP + 備品庫存' },
    { project_id: pid, alternative_id: alts[0].id, description: 'IMS 基板供應商集中風險', probability: 'low', severity: 'medium', level: 'M', mitigation: '認證第二供應商' },
    { project_id: pid, alternative_id: alts[1].id, description: '加厚銅面增加 PCB 成本 15%', probability: 'high', severity: 'low', level: 'M', mitigation: '與 PCB 廠議價包量' },
  ], 'adverse-consequences-1');

  await ins('signatures', [
    { project_id: pid, decision_id: decision.id, name: '張工程師', role: 'RD 工程師', status: 'signed', signed_at: '2026-03-01T10:00:00Z', note: '' },
    { project_id: pid, decision_id: decision.id, name: '李主管', role: 'RD 主管', status: 'signed', signed_at: '2026-03-01T14:00:00Z', note: '同意此方案，請按計畫執行。' },
    { project_id: pid, decision_id: decision.id, name: '王經理', role: 'PM', status: 'signed', signed_at: '2026-03-02T09:00:00Z', note: '' },
  ], 'signatures-1');

  await ins('action_items', [
    { project_id: pid, decision_id: decision.id, description: '完成 GaN 熱退磁長期驗證（2000 cycles）', assignee: '張工程師', due_date: '2026-03-15' },
    { project_id: pid, decision_id: decision.id, description: '建立 IMS 基板第二供應商認證計畫', assignee: '陳採購', due_date: '2026-03-20' },
    { project_id: pid, decision_id: decision.id, description: 'DVT 計畫書撰寫並送審', assignee: '李主管', due_date: '2026-03-25' },
    { project_id: pid, decision_id: decision.id, description: 'EMC 認證預測試安排', assignee: '林品保', due_date: '2026-04-01' },
  ], 'actions-1');

  await ins('knowledge_entries', [
    { project_id: pid, asset_type: 'design_pattern', title: 'GaN 軟切換拓撲設計指南', content: '此專案驗證了 GaN 諧振軟切換在 E-bike 馬達控制器的可行性。關鍵設計參數：諧振頻率 200kHz、死區時間 50ns、展頻調變 ±10%。效率提升 8% 且 EMI 通過 CISPR 25 Class 5。', reviewed: true },
    { project_id: pid, asset_type: 'lesson_learned', title: 'IMS 基板選型經驗', content: '鋁基板厚度 1.6mm 熱阻 1.0°C/W，優於 FR4 十倍。但需注意 CTE 匹配問題，建議使用柔性連接器與 FR4 板對接。', reviewed: true },
    { project_id: pid, asset_type: 'failure_mode', title: 'GaN MOSFET 串擾問題', content: '上下橋臂同時開啟（shoot-through）在 GaN 中更嚴重，因為 Miller 電容更小但 dV/dt 更高。解法：使用負壓 Gate 偏壓 (-3V) + 獨立 Gate driver 電源。', reviewed: true },
  ], 'knowledge-1');

  console.log(`[seed] Project 1 (Motor Controller) created: ${pid}`);
  return pid;
}

// ============================================================================
// PROJECT 2 — 電池管理系統 BMS (Phase II in progress)
// ============================================================================
async function seedProject2(uid) {
  const [project] = await insRet('projects', {
    name: 'E-Bike 電池管理系統 BMS',
    description: '【進行中案例】鋰電池 BMS 設計，解決均衡充電效率與安全監控的矛盾。展示 Phase I 完成、Phase II 進行中的流程。',
    status: 'in_progress', phase: 'Phase II', progress: 55,
    mission: '設計新一代 48V/20Ah 鋰電池 BMS，實現 ≥98% 均衡效率且滿足 UN38.3 安全認證。',
    phase_progress: { '1.1': 'passed', '1.2': 'passed', '1.3': 'passed', '2.1': 'passed', '2.2': 'in_progress', '2.3': 'not_started', '3.1': 'not_started', '3.2': 'not_started', '3.3': 'not_started' },
    quick_stats: { contradictions_count: 2, assumptions_count: 4, alternatives_count: 2, risks_count: 3, experiments_count: 2, evidence_items_count: 7 },
    must_criteria_config: [
      { id: 'M1', label: '均衡效率 ≥ 95%', source: 'KPI: 均衡效率', threshold: '≥ 95%' },
      { id: 'M2', label: '充放電循環 ≥ 2000', source: '產品壽命需求', threshold: '≥ 2000 cycles' },
      { id: 'M3', label: 'EMI 不干擾 CAN', source: 'C-01: 通訊可靠性', threshold: 'CAN BER < 10^-6' },
      { id: 'M4', label: 'BOM ≤ $8', source: '成本目標 (BMS 分攤)', threshold: '≤ $8 USD' },
      { id: 'M5', label: '可量產性', source: 'C-03: PCB 面積限制', threshold: '60×40mm 內' },
      { id: 'M6', label: 'UN38.3 認證', source: 'C-01: UN38.3', threshold: 'Pass' },
    ],
    gates_passed: 4, gates_total: 8, created_by: uid,
  }, 'project-2');
  const pid = project.id;

  await ins('briefs', { project_id: pid, mission: '設計新一代 48V/20Ah 鋰電池 BMS，實現 ≥98% 均衡效率且滿足 UN38.3 安全認證。', task_definition_5w1h: { who: 'Delta Electronics 儲能事業部', what: 'BMS PCB + 韌體 + 均衡演算法開發', where: '高階 E-bike 電池包整合', when: '2026 Q4 量產', why: '現行被動均衡效率僅 70%，無法支撐長距離騎乘', how: '主動均衡拓撲 + SoC/SoH 估測演算法 + 安全認證規劃' } }, 'brief-2');

  await ins('constraints', [
    { project_id: pid, constraint_code: 'C-01', description: '必須通過 UN38.3 運輸安全認證', source: '法規', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-02', description: '待機功耗 < 50μA（延長擱置壽命）', source: '產品規格', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-03', description: 'BMS PCB 面積 ≤ 60×40mm', source: '電池包結構', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-04', description: '支援 -20°C ~ 60°C 操作溫度範圍', source: '環境測試', type: 'hard', feasibility: 'verified' },
  ], 'constraints-2');

  await ins('kpis', [
    { project_id: pid, kpi_name: '均衡效率', target_value: '98', unit: '%', measurement_method: '20 串均衡測試，SOC 差異 < 1%' },
    { project_id: pid, kpi_name: '待機功耗', target_value: '50', unit: 'μA', measurement_method: '功率分析儀長期監測' },
    { project_id: pid, kpi_name: 'SoC 估測精度', target_value: '3', unit: '% 誤差', measurement_method: '全溫度範圍充放電循環測試' },
    { project_id: pid, kpi_name: 'UN38.3 認證', target_value: 'Pass', unit: '', measurement_method: '第三方認證實驗室' },
  ], 'kpis-2');

  await ins('socratic_questions', [
    { project_id: pid, category: 'clarification', text: '主動均衡拓撲選擇的主要考量因素？', answer: '效率、成本、PCB 面積、EMI。Flyback 型效率最高但面積大。', tagged_as_assumption: false, tagged_as_contradiction: true },
    { project_id: pid, category: 'assumption', text: '低溫環境下的 SoC 估測模型是否足夠準確？', answer: null, tagged_as_assumption: true, tagged_as_contradiction: false },
    { project_id: pid, category: 'consequence', text: '如果採用 Flyback 主動均衡，EMI 會否導致 CAN bus 通訊干擾？', answer: '需要評估，可能需要增加共模電感。', tagged_as_assumption: false, tagged_as_contradiction: true },
    { project_id: pid, category: 'reframing', text: '是否可以從根本上不需要均衡，改用更匹配的電芯分選？', answer: '電芯分選可降低需求但無法消除，長期衰退差異仍需均衡。', tagged_as_assumption: false, tagged_as_contradiction: false },
  ], 'socratic-2');

  const contradictions = await insRet('contradictions', [
    { project_id: pid, natural_description: 'Flyback 主動均衡效率高但 PCB 面積大', improving_param: 21, worsening_param: 7, engineering_statement: 'Flyback 均衡效率 98%+ 但每串需獨立變壓器，PCB 面積增加 40%。', type: 'TC', severity: 'major', resolved: false },
    { project_id: pid, natural_description: '高精度 SoC 估測需要更多感測器但增加成本', improving_param: 29, worsening_param: 32, engineering_statement: '卡爾曼濾波器需要溫度+電壓+電流三重感測，BOM 增加 $2.50。', type: 'TC', severity: 'minor', resolved: true },
  ], 'contradictions-2');
  const cids2 = contradictions.map(c => c.id);

  await ins('assumptions', [
    { project_id: pid, code: 'A-01', content: 'Flyback 變壓器可微型化至 6×6mm 封裝', source: '磁性元件供應商', source_type: 'manual', worst_consequence: 'PCB 面積超標', worst_severity: 'high', status: 'validating', verification_stage: 'in_progress' },
    { project_id: pid, code: 'A-02', content: 'EKF 演算法在 -20°C 下 SoC 精度 < 5%', source: '模擬結果', source_type: 'explore_tag', worst_consequence: '低溫續航預估不準確', worst_severity: 'medium', status: 'pending', verification_stage: 'planned' },
    { project_id: pid, code: 'A-03', content: '均衡 EMI 可透過軟切換抑制至 CAN bus 不受影響', source: '文獻', source_type: 'manual', worst_consequence: 'CAN 通訊錯誤率上升', worst_severity: 'high', status: 'validating', verification_stage: 'in_progress' },
    { project_id: pid, code: 'A-04', content: '待機模式可達 < 50μA 含 RTC 保活', source: '晶片規格書', source_type: 'manual', worst_consequence: '電池擱置壽命不足', worst_severity: 'medium', status: 'validated', verification_stage: 'completed' },
  ], 'assumptions-2');

  const nodes2 = await insRet('cld_nodes', [
    { project_id: pid, label: '均衡效率', x: 100, y: 150, node_type: 'variable', is_leverage: true },
    { project_id: pid, label: '變壓器尺寸', x: 300, y: 100, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'PCB 面積', x: 300, y: 250, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'EMI', x: 500, y: 150, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: 'BOM 成本', x: 500, y: 300, node_type: 'variable', is_leverage: false },
  ], 'cld-nodes-2');
  const nids2 = nodes2.map(n => n.id);
  await ins('cld_edges', [
    { project_id: pid, from_node: nids2[0], to_node: nids2[1], polarity: '+' },
    { project_id: pid, from_node: nids2[1], to_node: nids2[2], polarity: '+' },
    { project_id: pid, from_node: nids2[0], to_node: nids2[3], polarity: '+' },
    { project_id: pid, from_node: nids2[1], to_node: nids2[4], polarity: '+' },
  ], 'cld-edges-2');

  await ins('triz_solutions', [
    { project_id: pid, contradiction_id: cids2[0], path: 'TC', principle_number: 17, principle_name: '另一維度', suggestion: '將變壓器從 PCB 平面移至垂直堆疊（3D 封裝），面積不變但容量提升。使用 PoP 封裝技術。', status: 'pending' },
    { project_id: pid, contradiction_id: cids2[0], path: 'TC', principle_number: 6, principle_name: '萬用性', suggestion: '使用一個共用變壓器 + 多工切換，取代每串獨立變壓器。', status: 'pending' },
    { project_id: pid, contradiction_id: cids2[1], path: 'TC', principle_number: 24, principle_name: '中介物', suggestion: '使用共用 ADC + 多工器替代獨立感測器，降低成本保持精度。', status: 'adopted' },
  ], 'triz-2');

  const subsys2 = await insRet('subsystems', [
    { project_id: pid, name: '均衡電路', reason: '主動均衡拓撲選擇影響效率與面積', related_contradictions: [cids2[0]], confirmed: true, source: 'rd' },
    { project_id: pid, name: 'SoC/SoH 估測', reason: '演算法精度影響續航預估與安全判斷', related_contradictions: [cids2[1]], confirmed: true, source: 'rd' },
    { project_id: pid, name: '安全保護', reason: '過充/過放/短路保護電路', related_contradictions: [], confirmed: true, source: 'rd' },
  ], 'subsystems-2');

  // @deprecated v9: SCAMPER removed — TRIZ 40 principles fully cover SCAMPER actions
  // await ins('scamper_variants', [...], 'scamper-2');

  const alts2 = await insRet('alternatives', [
    {
      project_id: pid, name: 'Flyback 主動均衡 + 3D 堆疊',
      mechanism: '微型 Flyback 變壓器 (6×6mm PoP 封裝) 垂直堆疊 + 軟切換控制，均衡效率 98.2%。每串獨立變壓器但垂直堆疊不增加 PCB 面積。',
      source: 'triz', key_assumption_ids: ['A-01', 'A-03'],
      must_scores: { M1: 'pass', M2: 'pass', M3: 'marginal', M4: 'pass', M5: 'pass', M6: 'pass', description: 'Flyback 3D 堆疊方案：均衡效率 98.2%，面積不增', assumptions: ['Flyback 變壓器可微型化至 6×6mm', '軟切換 EMI 可控'], mustCriteria: [{ id: 'M1', label: '均衡效率 ≥ 95%', passed: true }, { id: 'M2', label: '充放電循環 ≥ 2000', passed: true }, { id: 'M3', label: 'EMI 不干擾 CAN', passed: null }, { id: 'M4', label: 'BOM ≤ $8', passed: true }, { id: 'M5', label: '可量產性', passed: true }, { id: 'M6', label: 'UN38.3 認證', passed: true }], risks: [{ id: 'R1', description: 'PoP 堆疊焊接良率', severity: 'major', mitigation: 'X-ray AOI 全檢' }], minValidation: 'PoP 焊接良率驗證 + EMI 掃描' },
      interface_contract: { envelope: '60×40×12mm (垂直堆疊高度 12mm)', loadPath: 'Flyback 變壓器串間能量傳遞', signalPath: 'I²C 菊鍊 (MCU→均衡 IC×20)', thermalPath: '變壓器→PoP 封裝→PCB 銅面→外殼', datumTolerance: 'PoP 堆疊對位精度 0.1mm', serviceability: '模組化設計可整組更換' },
      pre_cad_scores: { must: 4, decoupling: 4, testability: 3, failureMech: 3, mvpCadEffort: 2 },
      overall_pass: null, cad_status: 'in_progress',
    },
    {
      project_id: pid, name: '電感型均衡 + 標準佈局',
      mechanism: '共用電感切換式均衡，單一電感透過多工器切換均衡各串。效率 95.5%，面積小但均衡速度較慢。',
      source: 'manual', key_assumption_ids: ['A-04'],
      must_scores: { M1: 'pass', M2: 'pass', M3: 'pass', M4: 'pass', M5: 'pass', M6: 'pass', description: '電感型均衡：效率 95.5%，面積小但速度慢', assumptions: ['共用電感切換速度滿足需求'], mustCriteria: [{ id: 'M1', label: '均衡效率 ≥ 95%', passed: true }, { id: 'M2', label: '充放電循環 ≥ 2000', passed: true }, { id: 'M3', label: 'EMI 不干擾 CAN', passed: true }, { id: 'M4', label: 'BOM ≤ $8', passed: true }, { id: 'M5', label: '可量產性', passed: true }, { id: 'M6', label: 'UN38.3 認證', passed: true }], risks: [], minValidation: '均衡速度量測 (20S 全串完成)' },
      interface_contract: { envelope: '60×40×8mm (標準厚度)', loadPath: '共用電感切換均衡', signalPath: 'SPI (MCU→多工器)', thermalPath: '標準 PCB 散熱', datumTolerance: '標準 SMT', serviceability: '整板更換' },
      pre_cad_scores: { must: 4, decoupling: 3, testability: 4, failureMech: 4, mvpCadEffort: 4 },
      overall_pass: null, cad_status: 'not_started',
    },
  ], 'alternatives-2');

  await ins('evidence_matrix', [
    { project_id: pid, assumption_code: 'A-01', summary: 'Flyback 變壓器微型化', current_level: 'E1', is_north_star: true },
    { project_id: pid, assumption_code: 'A-02', summary: 'EKF 低溫精度', current_level: 'E0', is_north_star: false },
    { project_id: pid, assumption_code: 'A-03', summary: '均衡 EMI 抑制', current_level: 'E2', is_north_star: true },
    { project_id: pid, assumption_code: 'A-04', summary: '待機功耗', current_level: 'E3', is_north_star: false },
  ], 'evidence-2');

  await ins('risks', [
    { project_id: pid, description: '微型變壓器飽和導致均衡失效', failure_mode: '磁飽和', probability: 3, severity: 4, mitigation: '增加電流限制回授 + 磁芯材料升級' },
    { project_id: pid, description: 'CAN bus EMI 干擾', failure_mode: '通訊錯誤', probability: 2, severity: 3, mitigation: '增加共模電感 + 軟切換' },
    { project_id: pid, description: '低溫下 SoC 估測偏差過大', failure_mode: '續航誤判', probability: 3, severity: 2, mitigation: '溫度補償查表 + 線上學習' },
  ], 'risks-2');

  await ins('experiments', [
    { project_id: pid, user_id: uid, name: '微型變壓器樣品評估', linked_assumptions: ['A-01'], evidence_level: 'E1', method: '供應商樣品測試', success_criteria: '效率 ≥ 96% 且尺寸 ≤ 6×6mm', status: 'Running', result: '' },
    { project_id: pid, user_id: uid, name: '均衡 EMI 預掃描', linked_assumptions: ['A-03'], evidence_level: 'E2', method: 'CAN bus BER 測試', success_criteria: 'BER < 10^-6', status: 'Done', result: '軟切換後 BER < 10^-8，通過' },
  ], 'experiments-2');

  // Evidence Entries (Gate X1 Track)
  const { data: kpiRows2 } = await db.from('kpis').select('id,kpi_name').eq('project_id', pid);
  const kpiMap2 = {};
  (kpiRows2 || []).forEach(k => { kpiMap2[k.kpi_name] = k.id; });

  await ins('evidence_entries', [
    { project_id: pid, user_id: uid, title: '均衡 EMI 預掃描結果', measured_value: '< 10^-8', unit: 'BER', evidence_level: 'E2', method: 'CAN bus BER 測試 (軟切換模式)', notes: '軟切換後 BER 遠低於 10^-6 門檻', measured_at: '2026-03-05T14:00:00Z', kpi_id: kpiMap2['均衡效率'] || null, linked_assumption_codes: ['A-03'], linked_must_ids: ['M3'] },
    { project_id: pid, user_id: uid, title: '待機功耗量測', measured_value: '38', unit: 'μA', evidence_level: 'E3', method: '功率分析儀 24hr 監測', notes: '含 RTC 保活，低於 50μA 目標', measured_at: '2026-03-08T10:00:00Z', kpi_id: kpiMap2['待機功耗'] || null, linked_assumption_codes: ['A-04'], linked_must_ids: ['M5'] },
    { project_id: pid, user_id: uid, title: '共用 ADC 精度驗證', measured_value: '2.8', unit: '% 誤差', evidence_level: 'E2', method: '全溫度範圍 SoC 估測對比庫倫計數', notes: '25°C 精度 1.5%，-20°C 精度 4.2%（需改善）', measured_at: '2026-03-10T09:00:00Z', kpi_id: kpiMap2['SoC 估測精度'] || null, linked_assumption_codes: ['A-02'], linked_must_ids: ['M1'] },
  ], 'evidence-entries-2');

  // Concept Routes (Gate X2 Create)
  await ins('concept_routes', [
    { project_id: pid, route_type: 'composite', composition: [{ solutionId: 'triz-17', sourcePrinciple: '#17 另一維度', concrete: 'Flyback 變壓器 3D PoP 垂直堆疊', dimension: '空間', adoptionType: 'M1' }, { solutionId: 'triz-24', sourcePrinciple: '#24 中介物', concrete: '共用 ADC + 多工器替代獨立感測器', dimension: '感測', adoptionType: 'M2' }], composition_rationale: '結合 TRIZ #17(3D 堆疊解決面積) + #24(共用 ADC 降成本)，兩者作用於不同維度(空間/感測)，互不衝突(M1+M2)。', anti_pattern_warnings: [] },
    { project_id: pid, route_type: 'single', composition: [{ solutionId: 'triz-6', sourcePrinciple: '#6 萬用性', concrete: '共用變壓器 + 多工切換均衡', dimension: '拓撲', adoptionType: 'M4' }], composition_rationale: '單一共用變壓器方案，與 Flyback 獨立變壓器路線物理互斥(M4)。面積最省但效率略低。', anti_pattern_warnings: ['共用變壓器切換速度可能限制均衡效能'] },
  ], 'concept-routes-2');

  // Compatibility Pairs
  await ins('compatibility_pairs', [
    { project_id: pid, solution_a_id: alts2[0].id, solution_b_id: alts2[1].id, result: 'exclusive', adoption_type: 'M4', reason: '兩方案均衡拓撲互斥：Flyback 獨立變壓器 vs 共用電感切換，無法在同一均衡電路共存。' },
  ], 'compat-2');

  console.log(`[seed] Project 2 (BMS) created: ${pid}`);
  return pid;
}

// ============================================================================
// PROJECT 3 — 車架結構輕量化 (Phase I early stage)
// ============================================================================
async function seedProject3(uid) {
  const [project] = await insRet('projects', {
    name: 'E-Bike 車架結構輕量化',
    description: '【初期案例】碳纖維/鋁合金複合車架設計，探索輕量化與剛性的矛盾。展示 Phase I 定義與探索階段。',
    status: 'in_progress', phase: 'Phase I', progress: 30,
    mission: '將車架重量從 2.8kg 降至 2.0kg 以下，同時維持 ISO 4210 剛性與疲勞測試標準。',
    phase_progress: { '1.1': 'passed', '1.2': 'in_progress', '1.3': 'not_started', '2.1': 'not_started', '2.2': 'not_started', '2.3': 'not_started', '3.1': 'not_started', '3.2': 'not_started', '3.3': 'not_started' },
    quick_stats: { contradictions_count: 2, assumptions_count: 3, alternatives_count: 0, risks_count: 0, experiments_count: 0, evidence_items_count: 0 },
    must_criteria_config: [
      { id: 'M1', label: '車架重量 ≤ 2.0kg', source: 'KPI: 車架重量', threshold: '≤ 2.0 kg' },
      { id: 'M2', label: 'ISO 4210 疲勞測試', source: 'C-01: ISO 4210', threshold: '≥ 100,000 cycles' },
      { id: 'M3', label: '頭管剛性 ≥ 110 N/mm', source: 'C-02: 頭管剛性', threshold: '≥ 110 N/mm' },
      { id: 'M4', label: '成本 ≤ $280', source: 'C-03: 車架成本', threshold: '≤ $280 USD' },
    ],
    gates_passed: 1, gates_total: 8, created_by: uid,
  }, 'project-3');
  const pid = project.id;

  await ins('briefs', { project_id: pid, mission: '將車架重量從 2.8kg 降至 2.0kg 以下，同時維持 ISO 4210 剛性與疲勞測試標準。', task_definition_5w1h: { who: 'Delta Mobility 結構設計部', what: '車架管材選型、幾何最佳化、接合工藝開發', where: '公路型 E-bike', when: '2027 Q1 試產', why: '市場調查顯示重量是消費者購買決策第二大因素', how: '拓撲最佳化 + 碳纖維/鋁合金複合材料評估 + FEA 模擬' } }, 'brief-3');

  await ins('constraints', [
    { project_id: pid, constraint_code: 'C-01', description: '必須通過 ISO 4210 疲勞與衝擊測試', source: '法規/安全', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-02', description: '前三角頭管剛性 ≥ 110 N/mm', source: '操控性能', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-03', description: '車架成本 ≤ $280 USD（不含烤漆）', source: '成本目標', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-04', description: '車架最小壁厚（critical section）須 ≥ 0.8 mm（碳纖維層合板）或 ≥ 1.2 mm（鋁合金 6061-T6），以防止局部挫曲與衝擊穿透失效', source: '結構安全', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-05', description: '任何管件截面之最小壁厚須 ≥ 0.8 mm（碳纖維積層）或 ≥ 1.0 mm（鋁合金 6061/7005 系列），以防止局部挫曲與製程缺陷', source: '製程與強度', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-06', description: '車架幾何公差：頭管中心至五通中心的 stack/reach 偏差須在 ±1.5 mm 內，且左右對稱度偏差 ≤ 1.0 mm', source: '操控與組裝精度', type: 'hard', feasibility: 'questionable' },
    { project_id: pid, constraint_code: 'C-07', description: '車架與前叉介面（頭管內徑）及五通規格須符合市售標準（例如頭管 IS41/IS52 或 EC44/EC56；五通 BSA 68 mm 或 PF30）', source: '介面相容', type: 'hard', feasibility: 'verified' },
    { project_id: pid, constraint_code: 'C-08', description: '五通（BB）殼內徑、螺紋規格或壓入公差須符合目標標準，尺寸偏差 ≤ ±0.05 mm', source: '傳動系統相容', type: 'hard', feasibility: 'questionable' },
  ], 'constraints-3');

  await ins('kpis', [
    { project_id: pid, kpi_name: '車架重量', target_value: '2.0', unit: 'kg', measurement_method: '成車前秤重（不含前叉、座管）' },
    { project_id: pid, kpi_name: '頭管剛性', target_value: '110', unit: 'N/mm', measurement_method: 'MTS 測試機三點彎矩' },
    { project_id: pid, kpi_name: '疲勞壽命', target_value: '100000', unit: 'cycles', measurement_method: 'ISO 4210-6 疲勞測試' },
  ], 'kpis-3');

  await ins('socratic_questions', [
    { project_id: pid, category: 'clarification', text: '「2.0kg 以下」是否包含內部走線與電池座？', answer: '不含，純車架裸重。', tagged_as_assumption: false, tagged_as_contradiction: false },
    { project_id: pid, category: 'assumption', text: '碳纖維管材的接合強度是否足以替代鋁焊接？', answer: null, tagged_as_assumption: true, tagged_as_contradiction: false },
    { project_id: pid, category: 'consequence', text: '如果使用全碳纖維，維修性如何處理？', answer: null, tagged_as_assumption: false, tagged_as_contradiction: true },
    { project_id: pid, category: 'origin', text: '2.0kg 目標的來源是什麼？競品分析結果？', answer: '前三名競品平均 2.1kg，目標設定為低於市場平均。', tagged_as_assumption: false, tagged_as_contradiction: false },
    { project_id: pid, category: 'reframing', text: '「必須全鋁焊接」是經驗偏見嗎？', answer: null, tagged_as_assumption: true, tagged_as_contradiction: false },
  ], 'socratic-3');

  const contradictions3 = await insRet('contradictions', [
    { project_id: pid, natural_description: '減少管壁厚度降低重量但削弱剛性', improving_param: 1, worsening_param: 14, engineering_statement: '管壁從 1.2mm 減薄至 0.8mm 可減重 25%，但頭管剛性下降 30%。', type: 'TC', severity: 'fatal', resolved: false },
    { project_id: pid, natural_description: '碳纖維輕量但成本高且維修性差', improving_param: 1, worsening_param: 32, engineering_statement: '全碳車架可達 1.6kg 但成本 $450+，超出預算 60%。', type: 'TC', severity: 'major', resolved: false },
  ], 'contradictions-3');

  const nodes3 = await insRet('cld_nodes', [
    { project_id: pid, label: '管壁厚度', x: 100, y: 200, node_type: 'variable', is_leverage: true },
    { project_id: pid, label: '車架重量', x: 300, y: 100, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: '頭管剛性', x: 300, y: 300, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: '成本', x: 500, y: 200, node_type: 'variable', is_leverage: false },
    { project_id: pid, label: '碳纖維佔比', x: 100, y: 400, node_type: 'variable', is_leverage: true },
  ], 'cld-nodes-3');
  const nids3 = nodes3.map(n => n.id);
  await ins('cld_edges', [
    { project_id: pid, from_node: nids3[0], to_node: nids3[1], polarity: '+' },
    { project_id: pid, from_node: nids3[0], to_node: nids3[2], polarity: '+' },
    { project_id: pid, from_node: nids3[4], to_node: nids3[1], polarity: '-' },
    { project_id: pid, from_node: nids3[4], to_node: nids3[3], polarity: '+' },
    { project_id: pid, from_node: nids3[4], to_node: nids3[2], polarity: '+' },
  ], 'cld-edges-3');

  // Assumptions (Gate D2 Explore)
  await ins('assumptions', [
    { project_id: pid, code: 'A-01', content: '碳纖維管材的膠合接合強度足以替代鋁焊接，達到 ISO 4210 疲勞標準', source: 'Socratic 提問標記', source_type: 'explore_tag', worst_consequence: '接合處疲勞斷裂', worst_severity: 'critical', status: 'pending', verification_stage: 'planned' },
    { project_id: pid, code: 'A-02', content: '全鋁焊接是唯一可行的接合工藝（可能為經驗偏見）', source: 'Socratic 提問標記', source_type: 'explore_tag', worst_consequence: '忽略更優的複合材料方案', worst_severity: 'high', status: 'pending', verification_stage: 'planned' },
    { project_id: pid, code: 'A-03', content: '管壁減薄至 0.8mm 後局部挫曲風險可透過加肋控制', source: '結構分析推測', source_type: 'manual', worst_consequence: '局部挫曲導致結構失效', worst_severity: 'critical', status: 'pending', verification_stage: 'not_started' },
  ], 'assumptions-3');

  console.log(`[seed] Project 3 (Frame) created: ${pid}`);
  return pid;
}

// ============================================================================
// Main
// ============================================================================
async function main() {
  console.log('[seed] Starting...');
  await clearAll();
  const uid = await getUserId();
  console.log(`[seed] Using user: ${uid}`);

  const ids = [];
  ids.push(await seedProject1(uid));
  ids.push(await seedProject2(uid));
  ids.push(await seedProject3(uid));

  console.log(`\n[seed] ✅ All 3 showcase projects created successfully!`);
  console.log(`  P1 (馬達控制器): ${ids[0]}`);
  console.log(`  P2 (BMS):        ${ids[1]}`);
  console.log(`  P3 (車架):       ${ids[2]}`);
}

main().catch(e => { console.error('[seed] FAILED:', e.message); process.exit(1); });
