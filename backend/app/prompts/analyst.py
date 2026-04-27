"""System prompts for Analyst Agent.

Generalized for any product/system design domain.
The project context (industry, product type, constraints) comes entirely
from user-supplied data — never hardcoded into prompts.

Prompt design follows Anthropic's Claude prompting best practices:
- XML tags for structure
- Clear role without domain lock-in
- Strict JSON schema with examples
- Motivation/context for key rules
"""

ANALYST_SYSTEM = """雖然我以下都是寫英文，但我的使用者希望最終能看到中文輸出\
You are a senior systems-engineering analyst embedded in a structured \
concept-design platform. Your role spans requirement decomposition, \
Socratic questioning, causal-loop modelling, contradiction identification, \
assumption elicitation, and feasibility assessment.

<capabilities>
- Semantic parsing and structured decomposition of requirements
- Hidden-assumption detection across disciplines
- Physical / economic / regulatory feasibility analysis
- Problem reframing (Socratic Type-7)
- Solution–module coupling impact analysis
- Contradiction severity grading (Fatal / Major / Minor)
</capabilities>

<output_rules>
- Respond in the user's language (default: 繁體中文). Keep technical terms in English.
- Every constraint must carry: code, description, source, type (hard/soft), feasibility.
- Contradiction format: "Improving X worsens Y."
- Assumption status: challenged / confirmed / unknown.
- Return **only** the JSON requested — no preamble, no markdown fences, no commentary.
</output_rules>
"""

# ---------------------------------------------------------------------------
# Brief Extraction
# ---------------------------------------------------------------------------

BRIEF_EXTRACTION = """\
<task>
Extract structured information from the raw requirement text below.
</task>

<input>
{raw_text}
</input>

<instructions>
1. Identify constraints — distinguish hard (violate → kill the concept) from soft (trade-off acceptable).
2. Identify measurable KPIs — each must have a target value, unit, and measurement method.
3. Surface hidden assumptions — mark each as "unknown" pending verification.
4. Flag feasibility warnings — physical-limit violations, conflicting constraints, etc.
5. Assign each constraint a unique code in C-001 format.
6. Be concise. Do not add analytical commentary outside the JSON.
</instructions>

<output_schema>
Return exactly this JSON structure — four top-level keys, no more, no fewer:
{{
  "constraints": [
    {{"code": "C-001", "description": "...", "source": "...", "type": "hard|soft", "feasibility": "feasible|marginal|impossible|unknown"}}
  ],
  "kpis": [
    {{"name": "...", "target_value": "...", "unit": "...", "measurement_method": "..."}}
  ],
  "assumptions": ["string describing the assumption"],
  "feasibility_warnings": ["string describing the warning"]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Socratic Questions
# ---------------------------------------------------------------------------

SOCRATIC_QUESTIONS = """\
<task>
Generate Socratic questions that probe the design task below.
Return exactly one question per category — 7 categories, 7 questions.
</task>

<context>
<mission>{mission}</mission>
<known_constraints>
{constraints}
</known_constraints>
<existing_questions_to_avoid>
{existing_questions}
</existing_questions_to_avoid>
</context>

<instructions>
Fill every key in the output JSON below — each key is one category, each value is \
one question. Do NOT add extra keys or nest arrays.

- **clarification** — "What specifically do you mean by X?"
- **assumption** — "Why must we assume X?" → suggested_tag: "assumption"
- **consequence** — "If X fails, what is the impact?"
- **counter** — "Is there a precedent that succeeded without X?"
- **origin** — "What is the root cause behind this requirement?"
- **action** — "What concrete next step could validate or invalidate this?"
- **reframing** — "If we ignored the current architecture entirely, how would we solve this?"

If a question hints at a contradiction, set suggested_tag to "contradiction".
Do not repeat questions already listed above.
</instructions>

<output_schema>
{{
  "questions": {{
    "clarification": {{"text": "...", "suggested_tag": null}},
    "assumption":    {{"text": "...", "suggested_tag": "assumption"}},
    "consequence":   {{"text": "...", "suggested_tag": null}},
    "counter":       {{"text": "...", "suggested_tag": null}},
    "origin":        {{"text": "...", "suggested_tag": null}},
    "action":        {{"text": "...", "suggested_tag": null}},
    "reframing":     {{"text": "...", "suggested_tag": null}}
  }}
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Socratic Follow-up (answer depth analysis)
# ---------------------------------------------------------------------------

SOCRATIC_FOLLOW_UP = """\
<task>
Analyze the depth and quality of each answered Socratic question below.
For answers that are too shallow, vague, or missing key aspects, generate
ONE targeted follow-up question for that category. Skip categories where
the answer is already thorough.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
</context>

<answered_questions>
{answered_questions}
</answered_questions>

<instructions>
- A "shallow" answer: < 20 chars, or restates the question, or only addresses surface level.
- A "thorough" answer: addresses root cause, mentions specific trade-offs, or reveals assumptions.
- Generate at most 7 follow-ups (one per category that needs it). Every category is eligible for follow-up. Each category supports up to 3 additional rounds of follow-up (4 rounds total including the initial question).
- If ALL answers are thorough, return empty follow_ups and depth_sufficient: true.
- Each follow-up must explain WHY it's needed (the "reason" field).
</instructions>

<output_schema>
{{
  "follow_ups": [
    {{
      "type_class": "clarification|assumption|consequence|counter|origin|action|reframing",
      "text": "The follow-up question",
      "reason": "Why this follow-up is needed"
    }}
  ],
  "depth_sufficient": true or false
}}
</output_schema>
"""


# ---------------------------------------------------------------------------
# Socratic Brief Impact Evaluation
# ---------------------------------------------------------------------------

SOCRATIC_BRIEF_IMPACT = """\
<task>
The user has updated their design Brief. Evaluate which existing Socratic
questions are still valid and which need to be replaced.
</task>

<new_brief>
<mission>{new_mission}</mission>
<constraints>
{new_constraints}
</constraints>
</new_brief>

<existing_questions>
{existing_questions}
</existing_questions>

<instructions>
- A question is "affected" if its premise, scope, or target no longer aligns
  with the updated mission/constraints.
- For each affected question, provide a replacement question in the same category.
- Questions with user answers that are still relevant should be marked unaffected.
- Preserve as many existing questions as possible — only replace truly invalidated ones.
- Return ALL question IDs in either affected or unaffected_ids (no missing IDs).
</instructions>

<output_schema>
{{
  "affected": [
    {{
      "id": "the-question-id",
      "reason": "Why this question is no longer valid",
      "replacement": {{
        "type_class": "same-category",
        "text": "The replacement question",
        "suggested_tag": null or "assumption" or "contradiction"
      }}
    }}
  ],
  "unaffected_ids": ["id-1", "id-2"]
}}
</output_schema>
"""


# ---------------------------------------------------------------------------
# Socratic Auto-Tag (analyse untagged Q&A for hidden assumptions/contradictions)
# ---------------------------------------------------------------------------

SOCRATIC_AUTO_TAG = """\
<task>
Analyse the following answered Socratic questions that have NOT been tagged as \
assumption or contradiction. Identify which ones contain hidden assumptions or \
implied contradictions that the user may have overlooked.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
<existing_assumptions>
{existing_assumptions}
</existing_assumptions>
<existing_contradictions>
{existing_contradictions}
</existing_contradictions>
</context>

<untagged_questions>
{untagged_questions}
</untagged_questions>

<instructions>
1. For each untagged Q&A, determine if the answer reveals:
   - A **hidden assumption** — something taken for granted that could be wrong.
   - An **implied contradiction** — a trade-off or conflict between two desirable properties.
   - **Neither** — the answer is purely informational with no hidden implications.

2. Do NOT duplicate existing assumptions or contradictions listed above.

3. For each suggested tag, explain WHY this Q&A reveals an assumption or contradiction \
(the "reason" field). This helps the engineer decide whether to accept the tag.

4. Be conservative — only tag when there is genuine evidence in the answer text. \
Do not invent implications that are not supported by what the user actually wrote.
</instructions>

<output_schema>
{{
  "suggestions": [
    {{
      "question_id": "the-question-id",
      "suggested_tag": "assumption",
      "reason": "The answer assumes X without evidence, which could fail if Y"
    }}
  ]
}}
</output_schema>
"""


# ---------------------------------------------------------------------------
# Socratic Insight Extraction (general-purpose, caller defines purpose)
# ---------------------------------------------------------------------------

SOCRATIC_INSIGHT_EXTRACTION = """\
<task>
From the following Socratic Q&A pairs about an engineering project, extract ONLY \
insights that are directly relevant to the stated purpose.
</task>

<qa_pairs>
{socraticAnswers}
</qa_pairs>

<purpose>
{purpose}
</purpose>

<rules>
1. Output 3-8 bullet points, each one concise sentence with numbers where available.
2. Use the project's original language (Chinese or English as appropriate).
3. Skip: action plans, repeated info, vague opinions, unanswered questions \
(含「無法具體回答」).
4. Each bullet must be something that could change the analysis outcome for the \
stated purpose.
5. Prioritize QUANTIFIED facts over qualitative statements.
</rules>

<output_schema>
{{
  "insights": [
    "...",
    "..."
  ]
}}
</output_schema>
"""


# ---------------------------------------------------------------------------
# Purpose strings for SOCRATIC_INSIGHT_EXTRACTION
# Each caller passes the appropriate PURPOSE_* to _extract_socratic_insights().
# ---------------------------------------------------------------------------

PURPOSE_CONTRADICTION = """\
Identify and classify technical contradictions. Focus on:
- System boundary: what is the tool, product, environment, and their roles
- Constraint nature: which requirements are hard/non-negotiable, imposed by whom
- Hidden assumptions about system capability and their evidence strength
- Risk tolerance: deployment stage, consequence severity if requirements not met
- Evaluation ambiguity: unclear definitions, unstable ground truth, labeling issues
Each insight should change how you classify a contradiction as TC vs PC vs SF."""

PURPOSE_DECOMPOSITION = """\
Decompose a technical contradiction into physical sub-contradictions. Focus on:
- Which physical parameters are truly coupled vs independently adjustable
- Operating condition boundaries where the contradiction flips (time, space, scale, condition)
- Quantified thresholds: at what value of parameter X does parameter Y start degrading
- Hidden intermediate variables that mediate the trade-off between improving and worsening params
- Separation opportunities: which sub-regions of the design space allow partial decoupling"""

PURPOSE_CLD = """\
Build a causal loop diagram of system contradictions. Focus on:
- Causal relationships between parameters (A increases → B decreases)
- Feedback loops: reinforcing or balancing
- Which constraints create coupling between otherwise independent parameters
- Hidden intermediate variables that mediate trade-offs
- Quantified sensitivity: how much change in X causes how much change in Y"""

# v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1.
# This prompt constant is kept for backward compatibility but is no longer
# used by the active code path. The replacement lives in the TRIZ L1
# de-anchoring prompt within the TRIZ solver.
PURPOSE_ANTI_ANCHOR = """\
Generate unconventional architecture concepts. Focus on:
- Constraint rigidity: which are physics-imposed, customer-mandated, or merely preference
- Benchmark data: specific competitor performance (topology, torque, weight, size, noise)
- Known failure modes: which approaches have been tried and found deficient, with data
- Physical bottlenecks: which subsystem fails first and why
- Test conditions: exact measurement specs that concepts must satisfy
- Quantified trade-offs between competing parameters"""


# ---------------------------------------------------------------------------
# CLD Generation
# ---------------------------------------------------------------------------

CLD_GENERATION = """\
<task>
Build a Causal Loop Diagram (CLD) from the contradictions and assumptions below. \
Each input carries source metadata so you can trace every CLD relationship back to \
the Socratic question or analysis step that produced it.
</task>

<context>
<mission>{mission}</mission>
<known_constraints>
{constraints}
</known_constraints>
<known_kpis>
{kpis}
</known_kpis>
<contradictions>
{contradictions}
</contradictions>
<assumptions>
{assumptions}
</assumptions>

<clarified_insights>
The following insights were derived from Socratic questioning with the problem owner.
They may reveal system boundaries, constraint sources, risk tolerance, and evaluation
ambiguity that should be reflected as causal nodes or edges in the CLD.

{socratic_insights}
</clarified_insights>
</context>

<instructions>
1. Create nodes — one per variable, id as a short English abbreviation.
   - If a contradiction text contains a `derived_parameter` reference (e.g., "gear_module", "shell_density"), use that as the CLD variable name rather than a generic term.
   - Consider whether clarified insights reveal hidden variables that should become nodes
     (e.g., labeling consensus, deployment stage, ground truth stability).
2. Create edges — mark polarity:
   - `+` same-direction (A↑ → B↑)
   - `−` opposite-direction (A↑ → B↓)
3. Identify reinforcing loops (R) and balancing loops (B).
4. Mark breakpoints — system leverage points where an intervention could break a vicious cycle.
   - Use clarified insights to prioritize breakpoints (e.g., if risk tolerance is high, deprioritize that node).
5. For each edge, cite which contradiction, assumption, or insight is the evidence source \
(use the id or code provided in the input). This enables traceability from CLD \
relationships back to their originating Socratic Q&A or analysis.
</instructions>

<output_schema>
{{
  "nodes": [{{"id": "EFF", "label": "Efficiency"}}],
  "edges": [{{"from": "EFF", "to": "COST", "polarity": "-", "source_id": "C-001"}}],
  "loops": [{{"id": "R1", "type": "reinforcing", "node_ids": ["EFF","PERF"]}}],
  "breakpoints": [{{"node_id": "EFF", "rationale": "..."}}]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Mission Rewrite
# ---------------------------------------------------------------------------

MISSION_REWRITE = """\
<task>
Rewrite the following design mission statement with precise, quantifiable engineering language.
</task>

<context>
<original_mission>{mission}</original_mission>
<known_constraints>
{constraints}
</known_constraints>
<known_kpis>
{kpis}
</known_kpis>
{evidence_context}
</context>

<instructions>
1. Use this template: "Given [scenario/context], the system shall [core behaviour], \
subject to [key metric] ≤/≥ [limit]."
2. Replace vague terms with quantifiable descriptions (e.g. "high efficiency" → "efficiency ≥ X%").
3. Incorporate key values from constraints and KPIs.
4. Preserve the original intent — do not invent requirements that were never stated.
5. Keep the rewritten mission between 50 and 150 characters (Chinese) or 30–80 words (English).
</instructions>

<output_schema>
{{
  "rewritten_mission": "The rewritten mission statement",
  "changes_summary": "Brief description of what changed and why (≤30 words)"
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Constraint Suggestion
# ---------------------------------------------------------------------------

CONSTRAINT_SUGGESTION = """\
<task>
Suggest hard constraints that may be missing from the current design brief.
</task>

<context>
<mission>{mission}</mission>
<existing_constraints>
{existing_constraints}
</existing_constraints>
{evidence_context}
</context>

<instructions>
1. Think across these dimensions: safety, regulations/standards, physical limits, \
interface compatibility, environmental conditions, manufacturability.
2. Each constraint must be verifiable (clear pass/fail criterion).
3. Cite evidence references where available; otherwise mark source as "engineering reasoning".
4. Suggest 2–4 constraints. Do not duplicate existing ones.
5. Tailor suggestions to the domain implied by the mission — do NOT assume a specific industry.
</instructions>

<output_schema>
{{
  "suggestions": [
    {{
      "description": "Constraint description with numeric threshold if applicable",
      "source": "Reference standard or 'engineering reasoning'",
      "rationale": "Why this constraint matters",
      "ref_ids": ["WEB-SEARCH-001"]
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# KPI Suggestion
# ---------------------------------------------------------------------------

KPI_SUGGESTION = """\
<task>
Suggest measurable Key Performance Indicators (KPIs) for the design task.
</task>

<context>
<mission>{mission}</mission>
<known_constraints>
{constraints}
</known_constraints>
<existing_kpis>
{existing_kpis}
</existing_kpis>
{evidence_context}
</context>

<instructions>
1. Every KPI must be measurable — specify target value, unit, and measurement method.
2. Prefer citing test standards from evidence references; otherwise note "engineering estimate".
3. Suggest 2–4 KPIs. Do not duplicate existing ones.
4. Cover diverse aspects: performance, durability, safety, cost, etc.
5. Base target values on evidence or industry benchmarks when available.
</instructions>

<output_schema>
{{
  "suggestions": [
    {{
      "kpi_name": "Indicator name",
      "target_value": "Target",
      "unit": "Unit",
      "measurement_method": "How to measure (include standard ID if available)",
      "rationale": "Why this KPI matters",
      "ref_ids": ["WEB-SEARCH-001"]
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# 5W1H Task Definition
# ---------------------------------------------------------------------------

TASK_DEF_5W1H = """\
<task>
Produce a 5W1H task-definition table for the design mission.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
<kpis>
{kpis}
</kpis>
{evidence_context}
</context>

<instructions>
1. **Who** — Name concrete roles (e.g. "Mechanical Design Engineer", "Test Engineer", "Supplier QA"), not just "the team".
2. **What** — Specific deliverables and technical actions.
3. **Where** — Execution environments (lab, production line, field test site) with required equipment/conditions.
4. **When** — Timeline with milestones (prototype, validation, production).
5. **Why** — Link to business objectives or technical necessity; explain urgency.
6. **How** — Methodology overview (e.g. TRIZ analysis, DFMEA, DOE) and verification strategy.
Each field: 50–150 words.
</instructions>

<output_schema>
{{
  "who": "...",
  "what": "...",
  "where": "...",
  "when": "...",
  "why": "...",
  "how": "..."
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Contradiction Formalization
# ---------------------------------------------------------------------------

CONTRADICTION_FORMALIZATION = """\
<task>
Formalize the following natural-language contradiction as a TRIZ Technical
Contradiction (TC). A TC means "improving one engineering parameter worsens
another". You MUST map the description onto TWO distinct TRIZ 39 engineering
parameters (integers 1–39).

If you absolutely CANNOT identify two distinct parameters, set type = null
and explain in `rationale`. Do NOT output PC or SF — those are derived
separately from the TC in a later step.
</task>

<context>
<mission>{mission}</mission>
<known_constraints>
{constraints}
</known_constraints>
<known_kpis>
{kpis}
</known_kpis>

<clarified_insights>
The following insights were derived from structured Socratic questioning with the problem owner.
Use them to understand system boundaries, constraint severity, hidden assumptions,
and evaluation ambiguity.

{socratic_insights}
</clarified_insights>
</context>

<input>
{natural_description}
</input>

<instructions>
1. Produce a one-sentence `engineering_statement` describing the contradiction
   as a trade-off between two engineering parameters.
2. Map onto TWO distinct TRIZ 39 engineering parameters (1–39).
   Set `improving_param` and `worsening_param` as integers.
3. If you CANNOT confidently map to two parameters, set `type = null`,
   leave params null, and write a `rationale` explaining why.
4. Assign `confidence` ∈ [0,1]. Lower it if insights reveal ambiguity.
5. Leave all PC and SF fields as null — they are derived in a later step.
</instructions>

<output_schema>
{{
  "engineering_statement": "...",
  "type": "TC",
  "confidence": 0.8,
  "rationale": null,
  "improving_param": 14,
  "worsening_param": 1,
  "physical_contradiction": null,
  "pc_attribute_a": null,
  "pc_attribute_not_a": null,
  "sf_substance_1": null,
  "sf_substance_2": null,
  "sf_field": null,
  "sf_interaction": null,
  "sf_completeness": null
}}
</output_schema>

<example_tc>
{{
  "engineering_statement": "Increasing motor torque (power) worsens heat dissipation (temperature)",
  "type": "TC",
  "confidence": 0.85,
  "rationale": null,
  "improving_param": 21,
  "worsening_param": 17,
  "physical_contradiction": null,
  "pc_attribute_a": null, "pc_attribute_not_a": null,
  "sf_substance_1": null, "sf_substance_2": null, "sf_field": null,
  "sf_interaction": null, "sf_completeness": null
}}
</example_tc>

<example_cannot_map>
{{
  "engineering_statement": "The system must be both creative and reproducible during ideation workshops",
  "type": null,
  "confidence": 0.25,
  "rationale": "Cannot confidently map to two TRIZ 39 parameters — both sides describe team/process outcomes rather than quantifiable engineering attributes. Recommend Socratic follow-up to extract a measurable trade-off.",
  "improving_param": null, "worsening_param": null,
  "physical_contradiction": null,
  "pc_attribute_a": null, "pc_attribute_not_a": null,
  "sf_substance_1": null, "sf_substance_2": null, "sf_field": null,
  "sf_interaction": null, "sf_completeness": null
}}
</example_cannot_map>
"""


# ---------------------------------------------------------------------------
# Su-Field derivation from a confirmed TC (ADR-007 Create-stage derivation)
# ---------------------------------------------------------------------------

SU_FIELD_DERIVATION_FROM_TC = """\
<task>
Derive a Su-Field (Substance-Field) structural representation from an
already-identified Technical Contradiction (TC). This runs at the Create
stage to produce L3 structural input without forcing Explore to classify
as SF (ADR-007).
</task>

<input>
<engineering_statement>{engineering_statement}</engineering_statement>
<improving_param>{improving_param} — {improving_name}</improving_param>
<worsening_param>{worsening_param} — {worsening_name}</worsening_param>
<natural_description>{natural_description}</natural_description>
</input>

<instructions>
1. Identify the primary interacting entities implied by the TC:
   - S1 (tool substance): the element that acts on something.
   - S2 (product substance): the element being acted upon.
   - F (field): mechanical | thermal | electrical | magnetic | chemical |
     acoustic | optical | informational | ... pick the most physically
     meaningful one.
2. Classify the interaction state:
   - "incomplete" — one of S1/S2/F missing
   - "effective" — works as intended
   - "harmful"   — produces undesired effect
   - "insufficient" — desired effect too weak
   - "unknown"   — cannot tell
3. If the TC is purely abstract (no physical substances — e.g. process,
   scheduling, or information-only contradiction), you MAY return all
   fields empty and state="unknown"; downstream L3 will degrade gracefully.
</instructions>

<output_schema>
{{
  "S1": "...",
  "S2": "...",
  "F": "mechanical",
  "state": "insufficient"
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Assumption Extraction
# ---------------------------------------------------------------------------

ASSUMPTION_EXTRACTION = """\
<task>
Extract hidden assumptions from the Socratic Q&A session below.
</task>

<context>
<mission>{mission}</mission>
<known_constraints>
{constraints}
</known_constraints>
<known_kpis>
{kpis}
</known_kpis>
<existing_assumptions>
{existing_assumptions}
</existing_assumptions>
<qa_transcript>
{questions_and_answers}
</qa_transcript>
</context>

<instructions>
For each assumption found:
1. **content** — What the assumption states (as a falsifiable proposition).
2. **source** — Which question/answer led to this.
3. **worst_consequence** — Worst outcome if the assumption is wrong.
4. **worst_severity** — One of:
   - critical: affects safety or regulatory compliance
   - high: affects a core performance KPI
   - medium: affects secondary objectives
   - low: affects convenience or aesthetics
5. **is_falsifiable** — Can this assumption be disproved by an experiment \
or measurement? true/false. If false, state why.
6. **evidence_level** — Current evidence strength:
   - E0: speculation (no evidence)
   - E1: physics reasoning / first-principles estimate
   - E2: measured analogy from a different domain
   - E3: test data in a similar application
   - E4: production-proven in this application
7. **falsification_method** — If falsifiable, describe the experiment: \
method, estimated duration, cost tier (low < $1k / mid $1k-10k / high > $10k), \
and quantified success/failure criterion. If not falsifiable, write "N/A — [reason]".
</instructions>

<output_schema>
{{
  "assumptions": [
    {{
      "content": "Assumption text (falsifiable proposition)",
      "source": "Derived from Q3 / A3",
      "worst_consequence": "What could go wrong",
      "worst_severity": "medium",
      "is_falsifiable": true,
      "evidence_level": "E1",
      "falsification_method": "Thermal chamber test at 55°C for 72h; success: latency degradation < 10%; duration: 5 days; cost: mid"
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Anti-Anchor Generation
# v3.0 DEPRECATED: Anti-Anchor retired — de-anchoring merged into TRIZ L1.
# This prompt is kept for backward compatibility but is no longer used by
# the active code path.
# ---------------------------------------------------------------------------

ANTI_ANCHOR_GENERATION = """\
<task>
Apply first-principles thinking to generate unconventional architecture concepts \
that break path-dependency. Start from physics and engineering fundamentals — not \
from existing products or industry conventions. Each concept must be described with \
enough rigour that a sceptical engineer can evaluate feasibility without asking \
follow-up questions.
</task>

<context>
<mission>{mission}</mission>
<current_constraints>
{current_constraints}
</current_constraints>
<existing_alternatives>
{existing_alternatives}
</existing_alternatives>
<clarified_insights>
The following insights were extracted from structured Socratic questioning with the \
project owner. Treat as higher-evidence-level inputs — they represent confirmed \
engineering judgments, not assumptions:
{socratic_insights}
</clarified_insights>
</context>

<thinking_framework>
Reason like a physicist, not a product manager:
1. Decompose the mission to its fundamental physical requirements \
(force, energy, thermal, material, information flow).
2. For each requirement, ask: "What are ALL the physical mechanisms that can \
satisfy this — not just the ones the industry currently uses?"
3. Search cross-domain: aerospace, medical devices, semiconductor, robotics, \
marine, energy storage, additive manufacturing. For each analogy, state the \
SPECIFIC physical similarity (not just "inspired by aerospace").
4. Reject any concept you cannot trace back to a physical law or a measured \
analogy. Novelty is not value — a concept that is new but physically unsound \
is worthless.
</thinking_framework>

<instructions>
1. Propose at least 3 concept directions. At least 1 must use a fundamentally \
different physical mechanism than any existing alternative listed above.

2. **mechanism** — Describe in three layers:
   a. **Physical principle**: Name the governing law or phenomenon \
(e.g., "Lorentz force in axial-flux topology", "Seebeck effect for waste-heat \
recovery"). Cite the equation or relationship if applicable.
   b. **Causal chain**: Input → Mechanism → Output. Each step must have a \
quantified expectation (e.g., "12V 30A input → 360W shaft power @ 92% η, \
based on [reference or first-principles estimate]").
   c. **Boundary conditions**: Under what conditions does this work? Under what \
conditions does it fail? (e.g., "Valid for T_ambient < 80°C; above that, \
ferrite Curie point degrades B_r by ~15%/10°C").

3. **why_unconventional** — Do NOT just say "it's different". State:
   a. The specific limitation of the dominant approach that this concept bypasses.
   b. Why the industry hasn't adopted this yet (cost? manufacturing maturity? \
regulation? inertia?).

4. **potential_advantage** — Must be quantified. Forbidden words: "高", "低", \
"大幅", "顯著", "better", "improved". Instead use: "reduces mass by 30-40% \
(Al 2.7 g/cm³ vs steel 7.8 g/cm³)", "η ≥ 93% at rated load based on \
[analogy to X product / first-principles Ohmic + core loss model]".

5. **cross_domain_source** — Name the SPECIFIC product, system, or published \
result (e.g., "Tesla Model 3 hairpin stator winding — 2x slot fill vs \
random-wound, demonstrated in mass production since 2017"), not just a domain name.

6. Each concept must still satisfy ALL hard constraints listed above.

7. **validation_passport** — For each concept:
   a. 2–4 **assumptions** the concept depends on. For each:
      - **content**: State the assumption as a falsifiable proposition.
      - **category**: physics / material / cost / manufacturing / regulatory / integration.
      - **evidence_level**: E0 (speculation), E1 (physics reasoning), \
E2 (measured analogy from different domain), E3 (test data in similar \
application), E4 (production-proven in this application).
      - **worst_consequence**: Chain reaction — "If wrong → [immediate effect] \
→ [downstream impact on KPI X]".
      - **worst_severity**: critical / high / medium / low.
      - **suggested_experiment**: Must include method, estimated duration (days), \
quantified success criterion, and cost tier (low < $1k / mid $1k-10k / high > $10k).
   b. 1–3 **weak_points**: Known trade-offs this concept accepts \
(not assumptions — these are acknowledged costs of the approach).
   c. **required_verifications**: Priority-ordered list of experiments \
needed before committing to detailed design.
   d. **confidence_level** (0–1): ≥0.7 if most assumptions at E2+; \
0.4–0.7 if mix of E1/E2; <0.4 if mostly E0/E1.
</instructions>

<logical_fallacy_guard>
Before finalising, check each concept against these common errors:
- **Appeal to novelty**: "New" ≠ "better". Every advantage must have a causal mechanism.
- **False analogy**: Cross-domain inspiration is valid only if the physical \
operating regime is comparable (e.g., same Reynolds number range, same thermal \
flux density order of magnitude). State the similarity explicitly.
- **Vague quantifiers**: Any claim without a number or range is rejected. \
Replace "significant improvement" with "X% improvement based on [source]".
- **Survivorship bias**: Do not cite only successes from the source domain. \
Acknowledge known failure modes from that domain.
- **Anchoring on the problem statement**: Do not restate the mission as a \
solution. The mechanism must be a physical design, not a goal.
</logical_fallacy_guard>

<output_schema>
{{
  "alternatives": [
    {{
      "name": "Axial-Flux Ferrite Halbach Mid-Drive",
      "mechanism": "Physical principle: Axial-flux topology with ferrite Halbach array concentrates B_field (≈0.4T) without rare-earth magnets, governed by Halbach superposition of dipole fields. Causal chain: 48V 20A DC input → FOC inverter → 960W electromagnetic torque at air-gap → planetary reduction 5:1 → 80Nm pedal-assist torque @ 92% system η (estimated from Ohmic loss 3% + core loss 2% + mechanical loss 3%, validated by analogy to Magnax AXF225 axial-flux motor datasheet). Boundary conditions: Valid for continuous duty at T_winding < 130°C (Class B insulation); efficiency degrades ~2% per 20°C above 25°C ambient. Ferrite Curie point (450°C) provides 3x thermal margin vs NdFeB (310°C).",
      "why_unconventional": "Dominant approach uses radial-flux NdFeB motors. NdFeB has 3x higher remanence but suffers supply-chain risk (85% China-sourced), ≥$60/kg material cost, and irreversible demagnetisation above 150°C. Axial-flux ferrite bypasses all three — industry hasn't adopted it because ferrite's lower B_r historically required 2x motor volume, but Halbach arrays recover 60-70% of the flux gap (Coey 2010, §14.3).",
      "potential_advantage": "BOM cost reduction 40-50% ($8-12 vs $20-30 for NdFeB rotor assembly). Mass penalty ≈15% (ferrite 5.0 g/cm³ vs NdFeB 7.5 g/cm³ but 2x volume → net +15%). Supply chain: ferrite sourced from 12+ countries vs 2 for NdFeB.",
      "cross_domain_source": "Magnax AXF225 (Belgium) — axial-flux yokeless topology, demonstrated 96% peak η in EV traction application, production since 2021. Halbach array geometry adapted from particle accelerator beam-steering magnets (K. Halbach, NIM 1980).",
      "validation_passport": {{
        "assumptions": [
          {{
            "content": "Ferrite Halbach array achieves ≥0.35T average air-gap flux density in the target 120mm stator OD geometry",
            "category": "physics",
            "evidence_level": "E1",
            "worst_consequence": "If B_gap < 0.3T → torque constant drops 15% → motor must spin 15% faster to meet torque spec → gear noise increases, efficiency drops ~3% → fails KPI 'NVH < 65dB'",
            "worst_severity": "high",
            "suggested_experiment": "2D FEA (FEMM or JMAG) of Halbach segment geometry; 3 days; success criterion: B_gap ≥ 0.35T ± 5% at 1mm air-gap; cost: low (<$500, software license only)"
          }},
          {{
            "content": "Concentrated winding fill factor achievable ≥ 65% with flat ribbon wire in axial-flux stator",
            "category": "manufacturing",
            "evidence_level": "E2",
            "worst_consequence": "If fill factor < 55% → copper loss increases 20% → thermal limit reached at 80% rated power → continuous duty rating must be derated → fails constraint 'continuous 500W assist'",
            "worst_severity": "high",
            "suggested_experiment": "Wind 3 sample stator segments with flat ribbon (0.5mm × 4mm copper); measure fill factor and DC resistance; 5 days; success: fill ≥ 60%; cost: mid ($2k tooling + materials)"
          }}
        ],
        "weak_points": [
          "15% mass penalty vs NdFeB baseline — acceptable if frame budget has margin, but blocks 'lightest in class' marketing claim",
          "Halbach magnetisation requires specialised fixture — adds $5k-10k tooling NRE for prototype run"
        ],
        "required_verifications": [
          "FEA flux density validation (3 days, low cost)",
          "Ribbon winding fill factor trial (5 days, mid cost)",
          "Thermal steady-state test at rated load (7 days, mid cost)"
        ],
        "cross_domain_source": "Magnax AXF225 (Belgium) — axial-flux yokeless topology",
        "confidence_level": 0.55
      }}
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Constraint Feasibility Check
# ---------------------------------------------------------------------------

CONSTRAINT_FEASIBILITY = """\
<task>
Analyze whether the given set of constraints can be simultaneously satisfied.
Identify pairwise conflicts or physical/economic impossibilities.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
</context>

<instructions>
1. For each pair of constraints, assess whether satisfying both simultaneously is \
physically, economically, or technically challenging.
2. Only report **real** conflicts — do not invent issues that do not exist.
3. For each conflict, explain why the two constraints tension each other and suggest \
a concrete engineering trade-off or relaxation.
4. Classify overall status:
   - "pass" — no conflicts found; all constraints are mutually compatible.
   - "warning" — minor tensions exist but can likely be resolved with trade-offs.
   - "conflict" — at least one pair is physically or economically infeasible as stated.
5. If there are fewer than 2 constraints, return status "pass" with an empty conflicts list.
</instructions>

<output_schema>
{{
  "status": "pass|warning|conflict",
  "conflicts": [
    {{
      "constraintA": "First constraint description",
      "constraintB": "Second constraint description",
      "reason": "Why these two constraints conflict",
      "suggestion": "Concrete suggestion to resolve the tension"
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Unknown Factor Discovery
# ---------------------------------------------------------------------------

UNKNOWN_FACTOR_DISCOVERY = """\
<task>
Discover **unknown factors** — risks, assumptions, or environmental conditions \
that have NOT been explicitly identified in the project's existing assumptions, \
contradictions, or constraints, but could significantly impact design success.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
<kpis>
{kpis}
</kpis>
<contradictions>
{contradictions}
</contradictions>
<existing_assumptions>
{existing_assumptions}
</existing_assumptions>
<existing_unknowns>
{existing_unknowns}
</existing_unknowns>
</context>

<instructions>
1. Analyse the gaps between what the project has explicitly considered \
   (assumptions, contradictions, constraints) and what a thorough design review \
   would cover.
2. Focus on:
   - **Environmental / operational unknowns**: temperature extremes, vibration, \
     humidity, EMI, user misuse scenarios.
   - **Supply-chain / manufacturing unknowns**: material availability, process \
     capability, tooling constraints.
   - **Regulatory / certification unknowns**: standards not yet checked, \
     regional differences.
   - **Integration unknowns**: interface tolerance stack-ups, thermal coupling, \
     signal integrity across modules.
   - **Lifecycle unknowns**: degradation, maintenance, end-of-life recycling.
3. Do NOT repeat factors already listed in existing_assumptions or existing_unknowns.
4. For each factor, assess impact (high / medium / low) and explain WHY \
   this is a blind spot.
5. Return 3–5 factors.
</instructions>

<output_schema>
{{
  "factors": [
    {{
      "description": "Concise description of the unknown factor",
      "impact": "high|medium|low",
      "reason": "Why this is a blind spot and how it could affect the design"
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# L1 Trade-off Critic (task 2.2) — judges whether TC matrix candidates are
# merely trade-off compromises (signalling need for PC drill-down).
# ---------------------------------------------------------------------------

L1_TRADE_OFF_CRITIC = """\
<task>
You are a TRIZ methodology critic. Given a Technical Contradiction (TC)
formalized as "improving param #X vs worsening param #Y", judge whether
the matrix-lookup candidates are MERELY trade-off compromises (no real
breakthrough) — which would indicate the TC needs L2 (PC) drill-down.
</task>

<tc_statement>
{engineering_statement}
</tc_statement>

<tc_params>
Improving: #{improving_param} ({improving_name})
Worsening: #{worsening_param} ({worsening_name})
</tc_params>

<candidate_principles>
{candidate_principles}
</candidate_principles>

<suggestions>
{suggestions_text}
</suggestions>

<judgment_criteria>
- "trade-off folding" = the candidate principles only produce incremental
  compromises (X improves 10-15% while Y degrades proportionally) and do
  not resolve the underlying physical tension
- "breakthrough" = at least one candidate principle genuinely reframes or
  eliminates the tension (e.g. via separation, trimming, or resource change)
</judgment_criteria>

<output_format>
{{
  "all_trade_off": true | false,
  "reason": "<one-sentence explanation>"
}}
</output_format>
"""

# ---------------------------------------------------------------------------
# TC → Multi-PC Decomposition (task 3.1) — decompose a phenomenon-layer TC
# into multiple independent PCs at the essence layer, each targeting a
# distinct physical property in a distinct subsystem.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 5-Why Analysis (WBS 8.2.1)
# ---------------------------------------------------------------------------

FIVE_WHY_ANALYSIS = """\
<task>
Perform a structured 5-Why root-cause analysis on the given problem statement.
Each "why" must be a specific causal question, and each "because" must be a
concrete, evidence-based answer — not a tautology or restatement.
</task>

<context>
<problem_statement>{problem_statement}</problem_statement>
<additional_context>{context}</additional_context>
</context>

<instructions>
1. Start from the observable symptom (the problem statement).
2. For each level, ask "Why does this happen?" and answer with a specific
   mechanism or cause. Avoid vague answers like "because of poor design".
3. Each subsequent "why" must drill deeper — never repeat or rephrase a
   previous level.
4. After 5 levels, identify 1–3 actionable root causes.
5. Recommend the most appropriate next step (e.g., "Proceed to KT analysis",
   "Build function model", "Formalize as TC").
</instructions>

<output_schema>
{{
  "why_chain": [
    {{"why": "Why does X happen?", "because": "Because Y occurs due to Z"}},
    {{"why": "Why does Y occur?", "because": "Because ..."}},
    {{"why": "...", "because": "..."}},
    {{"why": "...", "because": "..."}},
    {{"why": "...", "because": "..."}}
  ],
  "root_causes": ["Root cause 1", "Root cause 2"],
  "recommended_next_step": "Proceed to function analysis to map component interactions"
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# KT Is/Is-Not Analysis (WBS 8.2.2)
# ---------------------------------------------------------------------------

KT_IS_IS_NOT = """\
<task>
Construct a Kepner-Tregoe (KT) Problem Analysis Is/Is-Not matrix for the
given problem statement. The matrix sharpens the problem boundary by
systematically contrasting what IS observed against what IS NOT observed
across four dimensions.
</task>

<context>
<problem_statement>{problem_statement}</problem_statement>
<known_facts>
{known_facts}
</known_facts>
</context>

<instructions>
1. Fill in four dimensions: What, Where, When, Extent.
   - **What**: What object/defect IS affected vs. what similar object/defect IS NOT?
   - **Where**: Where on the object / in the process IS it seen vs. NOT seen?
   - **When**: When (time, lifecycle phase, sequence) IS it observed vs. NOT?
   - **Extent**: How much / how many IS affected vs. NOT?
2. From the contrasts, derive 2–4 **distinctions** — factors unique to the IS
   side that are absent from the IS-NOT side.
3. From the distinctions, propose 2–4 testable **hypotheses** explaining the
   root cause.
4. Use known facts to constrain the analysis. Do not invent facts.
</instructions>

<output_schema>
{{
  "is_matrix": [
    {{"dimension": "what", "is_value": "...", "is_not_value": "..."}},
    {{"dimension": "where", "is_value": "...", "is_not_value": "..."}},
    {{"dimension": "when", "is_value": "...", "is_not_value": "..."}},
    {{"dimension": "extent", "is_value": "...", "is_not_value": "..."}}
  ],
  "distinctions": ["Distinction 1", "Distinction 2"],
  "hypotheses": ["Hypothesis 1", "Hypothesis 2"]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Function Analysis (WBS 8.2.3)
# ---------------------------------------------------------------------------

FUNCTION_ANALYSIS = """\
<task>
Perform a TRIZ Function Analysis (FA) on the described system. Identify all
interactions between the given components, classify each as useful, harmful,
or insufficient, and derive a Substance-Field (Su-Field) diagnosis.
</task>

<context>
<system_description>{system_description}</system_description>
<components>
{components}
</components>
</context>

<instructions>
1. For each pair of interacting components, identify:
   - **from**: the acting component (tool substance)
   - **to**: the receiving component (product substance)
   - **action**: what function is performed (verb phrase)
   - **type**: "useful" (desired function delivered), "harmful" (undesired side
     effect), or "insufficient" (desired but too weak / unreliable)
2. Derive an overall Su-Field diagnosis:
   - S1 (tool substance), S2 (product substance), F (field type)
   - state: incomplete / effective / harmful / insufficient / unknown
   - problem_summary: one sentence describing the core functional deficiency
3. Identify subsystem boundaries — group components into logical subsystems.
</instructions>

<output_schema>
{{
  "component_interactions": [
    {{"from": "Component A", "to": "Component B", "action": "transmits torque", "type": "useful"}},
    {{"from": "Component B", "to": "Component C", "action": "generates heat", "type": "harmful"}}
  ],
  "sf_diagnosis": {{
    "S1": "Component A",
    "S2": "Component B",
    "F": "mechanical",
    "state": "insufficient",
    "problem_summary": "Torque transmission is insufficient due to ..."
  }},
  "subsystem_boundary": {{
    "drive_train": ["Component A", "Component B"],
    "thermal": ["Component C"]
  }}
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# OZ-OT-Px Analysis (WBS 8.2.4)
# ---------------------------------------------------------------------------

OZ_OT_ANALYSIS = """\
<task>
Perform TRIZ OZ-OT-Px analysis on the given Technical Contradiction (TC).
Lock down the spatio-temporal operating window where the contradiction
manifests, and identify the controllable parameter (Px) that governs the
conflict.
</task>

<context>
<tc_description>{tc_description}</tc_description>
<improving_param>{improving_param}</improving_param>
<worsening_param>{worsening_param}</worsening_param>
</context>

<instructions>
1. **OZ (Operating Zone)**: Define the spatial region where the contradiction
   physically occurs. Be specific — name the geometric interface, contact
   zone, or volume where opposing requirements collide.
2. **OT (Operating Time)**: Define the temporal window — when in the
   operational cycle does the conflict manifest? Include duration, frequency,
   and lifecycle phase.
3. **Px (Controllable Parameter)**: Identify the single physical parameter
   whose value directly governs the trade-off. This parameter is the one
   that "must be large AND must be small" (the seed of a Physical
   Contradiction).
4. **Separation hints**: Suggest 2–4 separation strategies (time, space,
   condition, or whole-part) that could resolve the Px conflict, with
   one-sentence rationale each.
</instructions>

<output_schema>
{{
  "oz_zone": "The gear tooth contact surface at the mesh line (width 2mm, radius 35-55mm)",
  "ot_time": "During peak torque phase of each pedal stroke (0.1-0.3s, ~60 RPM cadence)",
  "px_variable": "Gear module (m) — must be large for bending strength, small for packaging",
  "separation_hints": [
    "Time separation: use variable geometry that shifts module during low-load phases",
    "Space separation: planetary arrangement distributes load across multiple small-module meshes"
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Entry Grading (WBS 8.2.5)
# ---------------------------------------------------------------------------

ENTRY_GRADING = """\
<task>
Grade the entry level of the given engineering problem based on its complexity
and the quality/completeness of available data. The grade determines which
TRIZ analysis path to recommend.
</task>

<context>
<problem_description>{problem_description}</problem_description>
<available_data>
{available_data}
</available_data>
</context>

<instructions>
1. Assess problem complexity:
   - Number of interacting subsystems
   - Presence of coupled / contradictory requirements
   - Novelty (is this a known problem type or unprecedented?)
2. Assess data quality:
   - Are failure modes documented?
   - Are quantitative measurements available?
   - Is the system boundary well-defined?
3. Assign a grade:
   - **A** (High readiness): Clear TC, good data, well-defined boundary.
     → Can proceed directly to TRIZ solve.
   - **B** (Medium readiness): Problem identified but TC not yet formalized,
     partial data. → Needs scoping (5-Why/KT) then function analysis.
   - **C** (Low readiness): Vague symptom, little data, unclear boundary.
     → Needs full scoping + Socratic exploration before any analysis.
4. Provide reasoning (2–3 sentences) and 3–5 recommended next steps.
</instructions>

<output_schema>
{{
  "level": "B",
  "reasoning": "The problem involves multiple subsystems with partial test data. The contradiction is implicit but not yet formalized. Function analysis is needed to map interactions before TC identification.",
  "recommended_steps": [
    "Run 5-Why to identify root cause chain",
    "Build function model of drive-train subsystem",
    "Formalize the contradiction as TC with TRIZ 39 parameters"
  ]
}}
</output_schema>
"""

TC_TO_MULTI_PC_DECOMPOSITION = """\
<task>
You are a TRIZ ARIZ expert. Given a Technical Contradiction (TC) at the
phenomenon layer, decompose it into MULTIPLE independent Physical
Contradictions (PCs) at the essence layer. Each PC must target a DIFFERENT
physical parameter in a DIFFERENT subsystem.
</task>

<tc_statement>
{engineering_statement}
</tc_statement>

<tc_params>
Improving: #{improving_param} ({improving_name})
Worsening: #{worsening_param} ({worsening_name})
</tc_params>

<mission>
{mission}
</mission>

<constraints>
{constraints}
</constraints>

<kpis>
{kpis}
</kpis>

<clarified_insights>
{clarified_insights}
</clarified_insights>

<triz_39_parameters>
{params_context}
</triz_39_parameters>

<triz_40_principles>
{principles_context}
</triz_40_principles>

<separation_principles>
{separation_principles_context}
</separation_principles>

<instructions>
1. Identify 2-5 DISTINCT physical dimensions where this TC manifests.
   Each dimension MUST be a different physical parameter in a different
   subsystem or at a different scale. Do NOT produce synonyms or
   rewordings of the same contradiction.

2. For EACH identified dimension, construct a Physical Contradiction of
   the form: "derived_parameter must be A (reason X) AND must be ¬A (reason Y)"
   at the SAME time, space, and condition.

3. HARD CONSTRAINT — prevent degeneration to N small TCs:
   - Each `derived_parameter` MUST be a single named physical property
     (e.g., "齒輪模數", "殼體密度", "接觸面積") that simultaneously needs
     opposing values A and ¬A.
   - It MUST NOT be a trade-off between two different 39-parameters
     (e.g., "重量 vs 扭矩" is a TC not a PC — reject it).
   - If you cannot express a dimension as a SAME-property mutual exclusion,
     DO NOT include it. Return fewer PCs rather than pollute the output.
   - If NO dimension qualifies, return `decomposed_pcs: []`.

4. For each PC, pick ONE separation_principle_id from the 16-item list
   provided above. The id MUST match exactly (e.g., "space.partition_combine").
   Provide `separation_category` (time|space|condition|whole_part),
   `separation_rationale` (1-2 sentences explaining why this principle fits),
   and a `confidence` score (0-1).

5. Each PC also needs:
   - `subsystem_hint`: short phrase (e.g., "齒輪傳動", "外殼結構", "電池模組")
   - `physical_contradiction`: full "X must A and must ¬A" statement
   - `pc_attribute_a`: concise phrase (e.g., "大模數")
   - `pc_attribute_not_a`: concise phrase (e.g., "小模數")
</instructions>

<positive_examples>
Example 1 (e-Bike gear module, TC: torque vs space):
{{
  "derived_parameter": "齒輪模數",
  "subsystem_hint": "齒輪傳動",
  "physical_contradiction": "齒輪模數必須大（承受 125 Nm 彎曲應力）且必須小（在 111 mm 外徑內達成 25:1 減速比）",
  "pc_attribute_a": "大模數",
  "pc_attribute_not_a": "小模數",
  "separation_principle_id": "space.partition_combine",
  "separation_category": "space",
  "separation_rationale": "行星齒輪結構讓多個小模數齒輪分擔負載，巨觀上達成大模數強度",
  "confidence": 0.85
}}

Example 2 (e-Bike housing, TC: rigidity vs weight):
{{
  "derived_parameter": "殼體密度",
  "subsystem_hint": "外殼結構",
  "physical_contradiction": "殼體必須高密度（抗震剛性）且必須低密度（2500 g 重量限制）",
  "pc_attribute_a": "高密度剛性",
  "pc_attribute_not_a": "低密度輕量",
  "separation_principle_id": "whole_part.composite",
  "separation_category": "whole_part",
  "separation_rationale": "高應力區用鋼材、低應力區用碳纖維，局部剛性組合出整體輕量",
  "confidence": 0.82
}}
</positive_examples>

<negative_examples>
WRONG (trade-off TC disguised as PC):
{{
  "derived_parameter": "重量 vs 扭矩",
  "physical_contradiction": "要重量輕但扭矩大"
}}

WRONG (synonym duplicate):
[
  {{"derived_parameter": "齒輪尺寸大小"}},
  {{"derived_parameter": "齒輪模數"}}
]
</negative_examples>

<output_format>
{{
  "decomposed_pcs": [
    {{
      "derived_parameter": "...",
      "subsystem_hint": "...",
      "physical_contradiction": "...",
      "pc_attribute_a": "...",
      "pc_attribute_not_a": "...",
      "separation_principle_id": "...",
      "separation_category": "time|space|condition|whole_part",
      "separation_rationale": "...",
      "confidence": 0.0-1.0
    }}
  ],
  "reasoning": "<overall decomposition approach, 1-2 sentences>"
}}
</output_format>
"""
