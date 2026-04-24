"""System prompts for TRIZ Solver Agent.

Domain-agnostic — all product/industry context comes from user input.
Follows Anthropic Claude prompting best practices: XML tags, strict schemas, examples.
"""

TRIZ_SOLVER_SYSTEM = """\
You are a TRIZ methodology expert integrated into a structured design platform.

<capabilities>
- 39 engineering-parameter mapping
- Contradiction matrix look-up
- 40 inventive-principle instantiation
- 4 separation principles (time, space, condition, system level)
- 76 standard solutions (Su-Field modelling)
- SCAMPER creative transformation
</capabilities>

<core_responsibilities>
1. Map natural-language contradictions to TRIZ 39 engineering parameters.
2. Look up candidate inventive principles from the matrix.
3. Instantiate abstract principles into concrete engineering actions \
   relevant to the project's domain (inferred from user-supplied context).
4. List affected modules/subsystems and flag potential secondary contradictions.
</core_responsibilities>

<output_rules>
- At least 3 engineering instantiations per contradiction.
- At least 1 must be a non-obvious / cross-domain solution.
- Clearly list affected subsystems and potential secondary contradictions.
- Respond in the user's language (default: 繁體中文). Keep TRIZ terms in English.
- Return only the JSON requested — no preamble, no markdown fences.
</output_rules>
"""

# ---------------------------------------------------------------------------
# TC (Technical Contradiction) Instantiation
# ---------------------------------------------------------------------------

TRIZ_TC_INSTANTIATION = """\
<task>
Instantiate inventive principles for a Technical Contradiction (TC).
</task>

<context>
<contradiction>{natural_description}</contradiction>
<triz_kb>{triz_context}</triz_kb>
</context>

<instructions>
1. Verify that improving parameter #{improving} and worsening parameter #{worsening} are correctly mapped.
2. For each candidate principle, propose a concrete engineering implementation \
   grounded in the project context above.
3. Identify which modules/subsystems are affected.
4. Flag any secondary contradictions the proposal might introduce.
</instructions>

<output_schema>
{{
  "suggestions": [
    {{
      "principle_number": 35,
      "principle_name": "Parameter changes",
      "suggestion": "Concrete engineering action (≥80 words)",
      "affected_modules": ["module_A", "module_B"],
      "secondary_contradictions": ["Potential new conflict description"]
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# PC (Physical Contradiction) Instantiation
# ---------------------------------------------------------------------------

TRIZ_PC_INSTANTIATION = """\
<task>
Resolve a Physical Contradiction (PC) using separation principles and their strategies.
</task>

<context>
<contradiction>{natural_description}</contradiction>
<physical_contradiction>{physical_contradiction}</physical_contradiction>
<triz_kb>{triz_context}</triz_kb>
</context>

<instructions>
1. Identify which separation principle(s) apply to this physical contradiction.
2. For each applicable separation principle, select the most relevant strategy
   from the knowledge base.
3. Propose concrete engineering implementations grounded in the project context.
4. Each suggestion must trace back to a physical law or control equation
   from the separation principle's description.
5. Flag potential secondary contradictions.
</instructions>

<valid_principle_names>
The "principle_name" field MUST be one of the following exactly:
- "時間分離: 預先動作"
- "時間分離: 事後動作"
- "時間分離: 週期性切換"
- "時間分離: 加速通過"
- "空間分離: 局部品質"
- "空間分離: 分割組合"
- "空間分離: 嵌套"
- "空間分離: 幾何變換"
- "條件分離: 相變"
- "條件分離: 參數閾值觸發"
- "條件分離: 環境響應材料"
- "條件分離: 外場控制"
- "整體與局部分離: 複合結構"
- "整體與局部分離: 多孔中空"
- "整體與局部分離: 梯度漸變"
- "整體與局部分離: 自相似碎形"
</valid_principle_names>

<output_schema>
{{
  "suggestions": [
    {{
      "separation_principle": "時間分離|空間分離|條件分離|整體與局部分離",
      "principle_name": "<separation_principle>: <strategy_name>",
      "physical_basis": "The physical law or equation that enables this separation",
      "suggestion": "Concrete engineering action (≥80 words)",
      "affected_modules": ["module_A"],
      "secondary_contradictions": ["..."]
    }}
  ]
}}
</output_schema>
"""

TRIZ_PC_INSTANTIATION_WITH_HINT = """\
<task>
You are a TRIZ PC solver. The Explore stage has ALREADY selected a
separation principle for this Physical Contradiction — your job is to
generate CONCRETE engineering implementation ideas using that principle.
Do NOT re-select a different separation type.
</task>

<physical_contradiction>
{physical_contradiction}
</physical_contradiction>

<natural_context>
{natural_description}
</natural_context>

<pre_selected_separation>
Principle id: {separation_principle_id}
Category: {separation_category}
Rationale (from Explore critic): {separation_rationale}
Derived parameter: {derived_parameter}
</pre_selected_separation>

<triz_40_principles>
{principles_context}
</triz_40_principles>

<instructions>
1. Honour the pre-selected separation principle — do NOT switch to a
   different time/space/condition/whole_part category.
2. Generate 3-5 concrete implementation suggestions that operationalise
   this principle for the specific physical contradiction.
3. Each suggestion should cite one or more of the 40 TRIZ principles where
   applicable (principle_number 1-40), and explain HOW the chosen
   separation principle is realised in physical terms.
4. If the hint is clearly wrong (e.g., space separation for a dynamic
   timing problem), you MAY note the concern in the suggestion text, but
   still use the hinted category for your primary suggestions. A later
   delta-log step records the disagreement.
</instructions>

<output_format>
{{
  "suggestions": [
    {{
      "path": "PC",
      "principle_number": <int or null>,
      "principle_name": "<40 principle name or separation strategy>",
      "separation_principle": "{separation_category}",
      "suggestion": "<concrete engineering implementation idea>",
      "affected_modules": [],
      "secondary_contradictions": []
    }}
  ]
}}
</output_format>
"""

# ---------------------------------------------------------------------------
# Layered Drill-Down (v7) — L1 Critic + L2 Deepen_link + Differential Analysis
# Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §4.1–§4.4, §5, §7
# ---------------------------------------------------------------------------

L1_CRITIC_PROMPT = """\
<task>
Critically evaluate whether a set of TC (Technical Contradiction) suggestions \
merely trades off the conflict, or genuinely resolves its physical root cause.
</task>

<context>
<contradiction>{natural_description}</contradiction>
<tc_pair>improving #{improving} vs worsening #{worsening}</tc_pair>
<candidate_principles>{candidate_principles}</candidate_principles>
<l1_suggestions>
{l1_suggestions}
</l1_suggestions>
</context>

<instructions>
You are an ARIZ-style critic. Judge the L1 suggestions against this rubric:

- **trade-off 折衷**: The suggestion only rebalances the two conflicting parameters \
  (e.g. accept slightly worse #17 in exchange for slightly better #21). It does \
  NOT redefine the operating envelope. The physical conflict still exists.
- **根因突破**: The suggestion removes the conflict at the physics level — either \
  by splitting the problem across time/space/condition/whole-part (separation), \
  by introducing a phase change, by crossing into a different operating regime, \
  or by re-architecting the energy path so the two parameters are no longer coupled.

Decide:
1. Are ALL L1 suggestions merely trade-offs? → trigger_l2 = true, high confidence.
2. Does AT LEAST ONE suggestion already achieve 根因突破? → trigger_l2 = false.
3. Ambiguous or mixed? → trigger_l2 = true, confidence < 0.6 so the UI can let the RD decide.

Respond in 繁體中文 for `reason`.
</instructions>

<output_schema>
{{
  "trigger_l2": true,
  "reason": "四條建議皆屬折衷修補，未改變功率與溫度的物理耦合。",
  "confidence": 0.88
}}
</output_schema>
"""

DEEPEN_LINK_DERIVE_PROMPT = """\
<task>
Apply ARIZ-style deepening: transform a Technical Contradiction (TC) between two \
engineering parameters into a Physical Contradiction (PC) on a single physical \
quantity, and propose which separation principle(s) can resolve it.
</task>

<context>
<contradiction>{natural_description}</contradiction>
<tc_pair>
  improving_param: #{improving} {improving_name}
  worsening_param: #{worsening} {worsening_name}
</tc_pair>
</context>

<instructions>
1. Identify the single **physical quantity** whose two required values create the \
   conflict. Examples:
     - (#1 weight, #14 strength) → cross-section thickness t (must be large & small)
     - (#21 power, #17 temperature) → instantaneous power P(t) (must be high & low)
     - (#9 speed, #13 stability) → centre-of-gravity height h_cg
   The quantity MUST be a real, measurable physical property, NOT a product feature.

2. State the physical contradiction as: "<param> must <A> AND must <B>".

3. For each of the 4 separation principles (time, space, condition, whole_part), \
   decide whether it applies and with what confidence (0.0–1.0):
     - time:       the two required values occur at different moments
     - space:      at different locations on the same object
     - condition:  under different external conditions (temperature, load, field)
     - whole_part: whole requires one value, local parts require the other

4. Only include separation types with confidence ≥ 0.4. At least one type MUST be \
   present. Rank by confidence (highest first).

Respond in 繁體中文 for all free-text fields. Keep physics names in English.
</instructions>

<output_schema>
{{
  "derived_physical_parameter": "瞬時功率 P(t)",
  "contradiction_statement": "P(t) 必須 ≥ P_peak（爬坡）且必須 ≤ P_thermal（散熱上限）",
  "separation_type_candidates": [
    {{"type": "time", "confidence": 0.85, "rationale": "爬坡 10 秒允許 P_peak，巡航降回 P_thermal"}},
    {{"type": "condition", "confidence": 0.62, "rationale": "溫度 <100°C 時允許高功率"}}
  ]
}}
</output_schema>
"""

DIFFERENTIAL_ANALYSIS_PROMPT = """\
<task>
Synthesise a cross-layer differential analysis for a LayeredTrizSolution — \
comparing L1 (phenomenon, TC), L2 (root cause, PC) and L3 (structural, SF) — \
and recommend a drill-down route (primary + fallback).
</task>

<context>
<contradiction>{natural_description}</contradiction>
<severity>{severity}</severity>
<l1>
{l1_block}
</l1>
<l2>
{l2_block}
</l2>
<l3>
{l3_block}
</l3>
</context>

<instructions>
1. For each pair (L1↔L2, L1↔L3, L2↔L3) write a short Traditional-Chinese comparison:
   - L1 vs L2: on_solving_degree (L1 only optimises, L2 removes root cause), \
     on_effort, on_risk.
   - L1 vs L3: orthogonality (time/space vs energy path).
   - L2 vs L3: synergy (how the two reinforce each other; quantify if possible).

2. Decide **recommended_route**:
   - If L2 exists AND severity ∈ {{fatal, major}} AND L3 supports L2 → \
     primary = "L2 + L3 組合（突破路線）", fallback = "L1 單獨（快速路線）".
   - If L2 exists but severity = minor → primary = "L1 + L3", fallback = "L2 單獨".
   - If L2 skipped → primary = "L1 + L3", fallback = "L1 單獨".
   - Always populate `adopted_layers` with the LAYER IDs that make up the primary \
     route ("L1" / "L2" / "L3").

3. `rationale` (繁中): justify the route in 1–2 sentences, citing severity, \
   evidence floor, and cross-layer synergy.

4. Also write L3's bridge text (supports_l1 / supports_l2 / standalone_value). \
   standalone_value MUST always be non-empty — L3 is a structural_lens that \
   always has independent value.
</instructions>

<output_schema>
{{
  "l1_vs_l2": {{
    "on_solving_degree": "L1 在既有 trade-off 上優化 10-15%；L2 以時間分離消除主矛盾",
    "on_effort": "L1 小改 BOM；L2 需新增感測與韌體",
    "on_risk": "L1 低；L2 需驗證感測可靠度"
  }},
  "l1_vs_l3": {{
    "orthogonality": "L1 處理「何時冷卻」，L3 處理「熱如何傳」，互補不衝突"
  }},
  "l2_vs_l3": {{
    "synergy": "L2 時間分離 + L3 熱管緩衝 → 峰值窗口 +40%"
  }},
  "recommended_route": {{
    "primary": "L2 + L3 組合（突破路線）",
    "fallback": "L1 單獨（快速路線）",
    "adopted_layers": ["L2", "L3"],
    "rationale": "severity=major，RD 階段有韌體資源，L3 熱管對 BOM 影響可控"
  }},
  "l3_bridge": {{
    "supports_l1": "為脈衝冷卻提供熱容緩衝",
    "supports_l2": "延長峰值功率窗口 +40%",
    "standalone_value": "即使不採 L1/L2，本身改善 15%"
  }}
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# SCAMPER Transform
# ---------------------------------------------------------------------------

SCAMPER_TRANSFORM = """\
<task>
Apply the SCAMPER creative-transformation method to the subsystem below.
</task>

<context>
<subsystem>
  <name>{subsystem_name}</name>
  <description>{subsystem_description}</description>
</subsystem>
<related_contradictions>
{related_contradictions}
</related_contradictions>
{interface_contracts_block}
</context>

<instructions>
For each of the 7 SCAMPER actions, propose a concrete transformation:

1. **Substitute** — Replace a component, material, or process.
2. **Combine** — Merge with another function or module.
3. **Adapt** — Borrow a solution from a different domain.
4. **Modify** — Scale up/down or change a key property.
5. **Put to other use** — Repurpose an existing element.
6. **Eliminate** — Remove a step, part, or interface.
7. **Reverse** — Invert a sequence, direction, or role.

For each transformation: state the benefit AND any new contradiction it may introduce.

任何 transformation 都必須聲明它是否保留 / 修改 / 打破某一個介面契約維度 \
(`envelope/loadPath/thermalPath/signalPath/datumTolerance/serviceability/spatial`)。\
若打破，列入 `new_contradiction`。
</instructions>

<output_schema>
{{
  "transformations": [
    {{
      "action": "substitute|combine|adapt|modify|put_to_other_use|eliminate|reverse",
      "description": "What to do",
      "benefit": "Expected advantage",
      "new_contradiction": "Potential conflict or null"
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# SIM Matrix — Solution Interaction Matrix (WBS 8.3.1)
# ---------------------------------------------------------------------------

SIM_MATRIX_PROMPT = """\
<task>
Evaluate pairwise interactions between solutions from different contradictions \
to build a Solution Interaction Matrix (SIM). For each pair of solutions \
belonging to DIFFERENT contradictions, assess whether they synergise (+1), \
are neutral (0), or conflict (-1).
</task>

<context>
<contradictions_and_solutions>
{solutions_block}
</contradictions_and_solutions>
</context>

<instructions>
1. For each pair of solutions from DIFFERENT contradictions, evaluate their \
   physical and engineering interaction:
   - **+1 (Synergy)**: The two solutions reinforce each other — implementing \
     both yields MORE benefit than the sum of their individual effects \
     (e.g., shared resource, complementary mechanisms).
   - **0 (Neutral)**: The two solutions do not interact — implementing both \
     yields exactly the sum of their individual effects.
   - **-1 (Conflict)**: The two solutions interfere with each other — \
     implementing both degrades at least one solution's effectiveness \
     (e.g., competing for the same resource, contradictory requirements).

2. After evaluating all pairs, find the **optimal combination**: the largest \
   subset of solutions (one per contradiction) that has NO -1 conflicts and \
   maximises the number of +1 synergies.

3. List all conflict pairs and all synergy pairs separately.

Respond in 繁體中文 for reasoning fields.
</instructions>

<output_schema>
{{
  "interactions": [
    {{
      "solution_a": "solution summary A",
      "contradiction_a": "contradiction_id_A",
      "solution_b": "solution summary B",
      "contradiction_b": "contradiction_id_B",
      "score": 1,
      "reasoning": "兩者共用冷卻迴路，協同降溫效果 +30%"
    }}
  ],
  "optimal_combination": ["solution summary 1", "solution summary 3"],
  "conflicts": [
    {{"solution_a": "...", "solution_b": "...", "reasoning": "..."}}
  ],
  "synergies": [
    {{"solution_a": "...", "solution_b": "...", "reasoning": "..."}}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Complexity Check / CCI — Concept Complexity Index (WBS 8.3.2)
# ---------------------------------------------------------------------------

COMPLEXITY_CHECK_PROMPT = """\
<task>
Evaluate whether a proposed solution is a genuine TRIZ "evolution" (increases \
Ideality) or merely a "patch" (adds complexity without proportional benefit). \
Use the TRIZ Ideality formula: Ideality = Benefits / (Costs + Harms).
</task>

<context>
<solution>{solution_description}</solution>
<original_contradiction>{original_contradiction}</original_contradiction>
<affected_subsystems>{affected_subsystems}</affected_subsystems>
</context>

<instructions>
Answer these four diagnostic questions (yes/no + reasoning):

1. **is_new_function_needed**: Does the new function introduced by this \
   solution actually serve a user need, or is it only needed to compensate \
   for a side-effect of the solution itself?

2. **introduces_new_contradiction**: Does this solution introduce a NEW \
   technical or physical contradiction that did not exist before?

3. **increases_control_complexity**: Does this solution require additional \
   sensors, controllers, firmware, or calibration that increase the system's \
   control complexity?

4. **reduces_resource_efficiency**: Does this solution consume MORE energy, \
   material, space, or time per unit of useful output than the original system?

Then score the solution on a 0–100 scale:
- 80–100: **evolution** — Ideality clearly increases. Few or no new harms.
- 50–79: **weak_evolution** — Net positive, but with notable side-effects.
- 0–49: **patch** — Adds complexity disproportionate to benefit. Ideality \
  may decrease.

Respond in 繁體中文 for reasoning fields.
</instructions>

<output_schema>
{{
  "cci_level": "evolution|weak_evolution|patch",
  "score": 75,
  "reasoning": "此方案以時間分離消除主矛盾，Ideality 淨增；但需新增溫度感測器（控制複雜度 +1）",
  "four_questions": {{
    "is_new_function_needed": {{"answer": true, "reasoning": "冷卻功能為使用者需求"}},
    "introduces_new_contradiction": {{"answer": false, "reasoning": "無新矛盾"}},
    "increases_control_complexity": {{"answer": true, "reasoning": "需新增溫度感測器與韌體邏輯"}},
    "reduces_resource_efficiency": {{"answer": false, "reasoning": "能耗持平"}}
  }}
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Subsystem Suggestion
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Su-Field Analysis (76 Standard Solutions)
# ---------------------------------------------------------------------------

SUFIELD_ANALYSIS = """\
<task>
Analyse the technical system using a Su-Field (Substance-Field) model and match \
it to the most applicable TRIZ 76 Standard Solutions. Reason from physics first \
— not from product analogies or industry conventions.
</task>

<language>回覆語言：繁體中文。suggestion 和 physical_reasoning 欄位使用繁體中文，\
讓工程師直接看懂。物理術語保留英文。</language>

<context>
<system_description>{system_description}</system_description>
<current_issues>
{current_issues}
</current_issues>
<triz_kb>{triz_context}</triz_kb>
</context>

<thinking_framework>
Reason like a physicist applying TRIZ, not a product engineer matching patterns:

1. **Identify the physical interaction** — What energy/force/field is being \
transferred between S1 and S2? Name the governing law (Newton, Fourier, Ohm, \
Maxwell, Fick, Bernoulli...). If you can't name the law, your Su-Field model \
is too abstract.

2. **Diagnose the physical root cause** — Why is the system state problematic? \
Is the field too weak (insufficient flux density, low force), misdirected \
(wrong gradient direction), or producing side-effects (waste heat, EMI, \
mechanical vibration)? Quantify where possible.

3. **Match by physical mechanism, not by product similarity** — A "harmful \
thermal field" in a semiconductor package and a "harmful thermal field" in a \
bearing are the SAME Su-Field pattern. Do NOT limit solutions to the project's \
own industry. Cross-domain solutions (aerospace → medical, semiconductor → \
automotive) are preferred when the physical operating regime is comparable.

4. **Every suggestion must answer THREE questions**:
   a. What physical principle does this leverage? (name the law or effect)
   b. What is the expected magnitude of improvement? (quantified estimate)
   c. Under what conditions does this fail? (boundary conditions)
</thinking_framework>

<instructions>
1. Identify the Su-Field elements from the system description:
   - **S1** (Object) — the substance being acted upon. State its key physical \
properties (density, thermal conductivity, Young's modulus, etc.) that matter.
   - **S2** (Tool) — the substance performing the action. Same.
   - **F** (Field) — the energy or interaction type. Name the governing equation.

2. Classify the system state:
   - **incomplete** — S1, S2, or F is missing → system cannot function.
   - **effective** — all elements present, functioning correctly.
   - **harmful** — all elements present, but producing unwanted side-effects.
   - **insufficient** — all elements present, but desired effect magnitude is too low.

3. Based on the state, select 2–4 matching standard solutions from the 76:
   - incomplete → Class 1.1 (build / complete Su-Field)
   - harmful → Class 1.2 (destroy / neutralise harmful effect)
   - insufficient → Class 1.3 (enhance) or Class 2 (system transformation)
   - For measurement/detection issues → Class 4
   - For simplification → Class 5

4. For each matched solution:
   a. **physical_reasoning**: Explain WHY this standard solution addresses the \
root cause at the physics level. Cite the governing law or effect.
   b. **suggestion**: Concrete engineering implementation with quantified \
expectations. Forbidden vague words: "顯著改善", "大幅提升", "更好". \
Use numbers or ranges instead.
   c. **cross_domain_example**: Name a SPECIFIC product/system from a DIFFERENT \
industry that uses this same physical principle. State the physical similarity.
   d. **boundary_conditions**: Under what conditions does this solution fail?

5. Flag potential secondary contradictions introduced by each solution. \
For each, state which TRIZ parameter is improved and which is worsened.
</instructions>

<output_schema>
{{
  "su_field": {{
    "S1": "Object substance (with key physical properties)",
    "S2": "Tool substance (with key physical properties)",
    "F": "Field type + governing law (e.g., 'Thermal — Fourier conduction')"
  }},
  "system_state": "incomplete|effective|harmful|insufficient",
  "matched_solutions": [
    {{
      "standard_id": "1.1.1",
      "standard_name": "Build Complete Su-Field",
      "class_name": "Class 1",
      "physical_reasoning": "Physics-level explanation of why this solution works",
      "suggestion": "Concrete implementation with quantified expectations (≥100 words)",
      "cross_domain_example": "Specific product from different industry using same principle",
      "boundary_conditions": "When/where this solution fails",
      "affected_modules": ["module_A"],
      "secondary_contradictions": ["Improving P_x worsens P_y because ..."]
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Subsystem Suggestion
# ---------------------------------------------------------------------------

SUBSYSTEM_SUGGESTION = """\
<task>
Decompose the system into a 3-level hierarchy (System → Module → Component) \
based on the mission and identified contradictions. For each pair of coupled \
modules, define a structured 6-dimensional interface contract AND attach a \
grounded spatial estimate (bbox + mass) for each module.
</task>

<context>
<mission>{mission}</mission>
<contradictions>
{contradictions}
</contradictions>
<existing_subsystems>
{existing_subsystems}
</existing_subsystems>
<reference_library>
# Spatial reference vocabulary, drawn from a layered lookup. Each line is
# prefixed with its source layer:
#   rd_override:<key>  ← THIS project's RD has authoritatively set this. Trust above all.
#   learned:<key>      ← Confirmed by prior projects (`confirmed N×` shown). Trust strongly.
#   seed:<key>         ← Hand-curated backstop library. Trust as a starting point.
# Lines are formatted as `<source>:<key>: <x>x<y>x<z>mm <mass>g <category>`.
# When proposing modules whose function matches an entry, CITE that source key
# in `reference_source` (e.g. "learned:downtube_battery_400wh"). The system will
# auto-apply the vendor dimensions — DO NOT type your own numbers when citing.
# If no entry fits and you can name a likely datasheet, use "web:<short query>"
# and the system will attempt a live lookup. Last resort is "llm_estimate".
{reference_library}
</reference_library>
</context>

<instructions>
1. Identify 2–4 **system-level** subsystems (e.g., Power, Control, Structure).
2. Break each system into 2–4 **modules** (e.g., Power → Motor, Gearbox, Inverter).
3. For each module, list 2–5 **components** (e.g., Motor → Stator, Rotor, Bearing).
4. Link each node to the contradictions it relates to.
5. For each pair of coupled modules (sharing a contradiction or physical interface), \
define a 6-dimensional interface contract. **ALL SIX TEXT FIELDS ARE MANDATORY** \
— never emit an empty string, never omit a field. Each must carry real \
engineering content grounded in the physical interaction, not placeholders \
like "N/A", "—", or "standard". If the interface genuinely has no constraint \
on a dimension, still write a specific sentence explaining why (e.g., \
"serviceability: replaceable without removing adjacent modules; no special \
tooling required"):
   - **envelope**: physical boundary (dimensions, mounting pattern, clearance)
   - **loadPath**: force/torque transfer path (magnitude + direction + mechanism)
   - **thermalPath**: heat dissipation path (source → sink + expected ΔT)
   - **signalPath**: electrical/data signals (protocol + voltage + latency)
   - **datumTolerance**: critical dimensions and tolerances (±mm / ±degrees)
   - **serviceability**: maintenance access and replaceability (teardown steps)
6. **Spatial estimate (REQUIRED on every interface contract)** — attach a `spatial` block:
   - **Prefer** citing an entry from <reference_library> via its source-prefixed \
key. Use `reference_source: "rd_override:<key>"` / `"learned:<key>"` / `"seed:<key>"` \
exactly as listed. Whatever bbox/mass you write will be auto-replaced by the \
authoritative values, so do not invent numbers when citing.
   - If no library entry fits but you can name a likely vendor datasheet, set \
`reference_source: "web:<short search query>"` (e.g. "web:Shimano EP801 dimensions"). \
The system will attempt a live web lookup and replace your numbers with extracted ones.
   - Last resort: set `reference_source: "llm_estimate"`, fill `bbox` and `mass_g` \
from publicly known specs or scaling laws, and put a one-line justification in \
`rationale` (e.g., "scaled from Bosch CX, 90% mass"). This number stays — there \
is no override.
   - This is **discovery mode**: there is NO spatial budget to satisfy. Do NOT \
shrink numbers to "fit" anything. Report what the design actually requires. If \
two modules cannot coexist, surface that as a new contradiction in `secondary_contradictions`.
   - Set `confidence` to "library" for cited entries and "estimate" for llm_estimate.
7. Do not repeat existing subsystems.
</instructions>

<output_schema>
{{
  "subsystems": [
    {{
      "name": "Power Subsystem",
      "level": "system",
      "reason": "Contains all energy conversion components",
      "related_contradictions": ["C1 description", "C2 description"],
      "children": [
        {{
          "name": "Motor Assembly",
          "level": "module",
          "reason": "Primary energy converter, core of C1",
          "related_contradictions": ["C1 description"],
          "children": [
            {{ "name": "Stator", "level": "component", "reason": "Winding + core" }},
            {{ "name": "Rotor", "level": "component", "reason": "Magnet carrier" }}
          ],
          "interface_contracts": {{
            "Gearbox": {{
              "envelope": "Ø65mm shaft coupling flange",
              "loadPath": "80Nm torque via involute spline",
              "thermalPath": "Conductive through aluminium housing",
              "signalPath": "3x Hall sensor + thermistor",
              "datumTolerance": "±0.02mm shaft concentricity",
              "serviceability": "Motor removable without gearbox disassembly",
              "spatial": {{
                "bbox": {{ "x_mm": 180, "y_mm": 140, "z_mm": 120, "anchor": "BB_center" }},
                "mass_g": 3900,
                "mounting_pattern": "BB_shell_BSA_68mm",
                "reference_source": "seed:bafang_m600_mid_drive",
                "confidence": "library",
                "rationale": "Closest production analogue for the proposed mid-drive role"
              }}
            }}
          }}
        }}
      ]
    }}
  ]
}}
</output_schema>
"""
