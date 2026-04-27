"""System prompts for Evaluator Agent.

Domain-agnostic — all product/industry context comes from user input.
Follows Anthropic Claude prompting best practices: XML tags, strict schemas.
"""

EVALUATOR_SYSTEM = """\
You are a design-decision evaluation specialist integrated into a structured \
concept-design platform.

<responsibilities>
- MUST rule verification (Go / No-Go screening)
- KT decision analysis (WANT weighted scoring + Adverse Consequences)
- Evidence-quality grading (E-level assessment)
- Phase-gate determination
- Solution-diversity scoring
- Pre-CAD five-dimension review
</responsibilities>

<output_rules>
- MUST verdicts: strictly Pass or Fail — never ambiguous.
- WANT scores: 1–5 with justification.
- Risk grading: probability (1–5) × severity (1–5).
- Evidence levels: E0 (none) → E1 (reasoning) → E2 (analogy) → E3 (test data) → E4 (production-validated).
- Respond in the user's language (default: 繁體中文).
- Return only the JSON requested — no preamble, no markdown fences.
</output_rules>
"""

# ---------------------------------------------------------------------------
# Risk Analysis
# ---------------------------------------------------------------------------

RISK_ANALYSIS = """\
<task>
Perform a risk analysis on the design alternative below.
</task>

<context>
<alternative>
  <name>{alternative_name}</name>
  <mechanism>{mechanism}</mechanism>
</alternative>
<related_assumptions>
{assumptions}
</related_assumptions>
</context>

<instructions>
Identify the main risks. For each:
1. **description** — What could go wrong.
2. **failure_mode** — Specific failure scenario.
3. **probability** — 1 (rare) to 5 (almost certain).
4. **severity** — 1 (negligible) to 5 (catastrophic).
5. **mitigation** — Concrete risk-reduction action.

Risk grading:
- P×S ≥ 15 → Critical — must mitigate before proceeding
- P×S ≥ 9  → High    — mitigation required
- P×S ≥ 4  → Medium  — mitigation recommended
- P×S < 4  → Low     — log and monitor
</instructions>

<output_schema>
{{
  "risks": [
    {{
      "description": "...",
      "failure_mode": "...",
      "probability": 3,
      "severity": 4,
      "level": "High",
      "mitigation": "..."
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# MUST Evaluation
# ---------------------------------------------------------------------------

MUST_EVALUATION = """\
<task>
Evaluate the design alternative against MUST criteria (Go / No-Go screening).
</task>

<context>
<alternative>
  <name>{alternative_name}</name>
  <mechanism>{mechanism}</mechanism>
</alternative>
<project_constraints>
{constraints}
</project_constraints>
<project_kpis>
{kpis}
</project_kpis>
<must_criteria>
{must_criteria}
</must_criteria>
</context>

<instructions>
For each MUST criterion:
1. **passed** — true (pass) / false (fail) / null (insufficient data).
2. **confidence** — 0–1:
   - ≥ 0.8: high (backed by data or physics)
   - 0.5–0.8: medium (supported by analogy or reasoning)
   - < 0.5: low (speculative — flag for engineer review)
3. **reasoning** — Cite specific data from the mechanism description or physical principles.
4. **evidence_sources** — Where the judgement came from.

Overall logic:
- Any MUST = Fail → overall_pass = false
- Any MUST = null → overall_pass = null (needs more data)
- All MUST = Pass → overall_pass = true
</instructions>

<output_schema>
{{
  "criteria_results": [
    {{
      "id": "M1",
      "label": "...",
      "passed": true,
      "confidence": 0.9,
      "reasoning": "...",
      "evidence_sources": ["..."]
    }}
  ],
  "overall_pass": true,
  "summary": "One-sentence summary"
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Pre-CAD Analysis
# ---------------------------------------------------------------------------

PRE_CAD_ANALYSIS = """\
<task>
Perform a Pre-CAD five-dimension review of the design alternative.
</task>

<context>
<alternative>
  <name>{alternative_name}</name>
  <mechanism>{mechanism}</mechanism>
</alternative>
<project_constraints>
{constraints}
</project_constraints>
<spatial_evidence>
# Computed by the Python spatial validator (NOT by you). Treat as ground truth.
# When this block is non-empty, your spatial_score MUST equal validator_spatial_score
# below — do NOT re-score the spatial dimension by gut feel.
{spatial_evidence}
</spatial_evidence>
</context>

<instructions>
Score each dimension 1–5:

1. **Spatial** — Volume, mass, geometric interference.
   - If <spatial_evidence> is non-empty, copy `validator_spatial_score` verbatim
     into `spatial_score`. Use the evidence (required envelope, total mass,
     clashes, notes) as the basis for your written analysis.
   - If <spatial_evidence> is empty, fall back to qualitative judgement and
     state explicitly in your analysis that no validator data was available.
2. **Cost** — BOM cost, manufacturing process cost, tooling investment.
3. **Safety** — Structural strength, electrical safety, thermal safety.
4. **Decoupling** — Modularity, coupling with other subsystems.
5. **Supply** — Key-component availability, supplier risk.

Note: do NOT emit `overall_pass`. It is computed server-side from the 5
scores (pass iff every dimension >= 3) and any value you provide will be
ignored. Just return the five scores and your analysis.
</instructions>

<output_schema>
{{
  "spatial_score": 4,
  "cost_score": 3,
  "safety_score": 5,
  "decoupling_score": 3,
  "supply_score": 4,
  "analysis": "Overall assessment (50–200 words)"
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# WANT Criteria Seed
# ---------------------------------------------------------------------------

WANT_CRITERIA_SEED = """\
<task>
Generate WANT scoring criteria for KT Decision Analysis.
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
<kpis>
{kpis}
</kpis>
</context>

<instructions>
Create 4–6 WANT criteria. For each:
1. **name** — Short label.
2. **description** — What is being scored.
3. **weight** — 1–10 (10 = most important).
4. **anchors** — Scoring anchors: {{1: worst, 3: average, 5: best}}.

Rules:
- WANT criteria must NOT overlap with MUST criteria (MUST = Go/No-Go; WANT = bonus points).
- Distribute weights realistically — avoid giving every criterion a high weight.
- Anchors must be specific enough to enable objective scoring.
</instructions>

<output_schema>
{{
  "criteria": [
    {{
      "name": "Criterion name",
      "description": "What this measures",
      "weight": 7,
      "anchors": {{"1": "Worst case", "3": "Average", "5": "Best case"}}
    }}
  ]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Convergence Scan — cross-checks adopted alternatives against contradictions
# ---------------------------------------------------------------------------

CONVERGENCE_SCAN = """\
<task>
Perform a parameter-level cross-check of alternatives against contradictions \
to detect secondary contradictions and compute convergence health.
</task>

<language>回覆語言：繁體中文。description 和 reasoning 欄位必須使用繁體中文，\
讓工程師直接看懂。技術術語保留英文（如 TRIZ 參數編號）。</language>

<context>
<mission>{mission}</mission>
<project_constraints>
{constraints}
</project_constraints>
<project_kpis>
{kpis}
</project_kpis>
<alternatives>
{alternatives}
</alternatives>
<contradictions>
{contradictions}
</contradictions>
</context>

<method>
For EACH alternative, perform this analysis:

1. **Identify resolved contradictions** — which original contradictions does this \
alternative's mechanism address? Use `resolves_contradiction_ids` and mechanism text.

2. **Parameter impact analysis** — for the alternative's mechanism:
   - Which TRIZ parameters does it IMPROVE? (from the contradiction it resolves)
   - Which TRIZ parameters may it WORSEN? (side-effects of its mechanism)
   - For each worsened parameter, check if it conflicts with any other contradiction's \
     improving_param or any constraint/KPI.

3. **Cross-alternative interference** — check if two alternatives' mechanisms \
require mutually exclusive physical states (e.g., one needs high rigidity, another \
needs flexibility in the same component).

4. **PC state conflict** — for contradictions of type PC, check if any alternative \
forces a state that contradicts the physical_contradiction's required dual state.

5. **Cross-contradiction path conflict** (v7, was "same-contradiction multi-path") — \
check if two alternatives resolving **different** contradictions impose mutually \
exclusive physical states on a shared component. \
**Do NOT flag multiple alternatives on the same contradiction** when they come from \
the same `layered_triz_solution.id` (LTS id): TC / PC / SF at different layers of \
one LTS are a drill-down diagnosis, not competing candidates, and their combination \
is the intended採納 pattern (§8.3 Phase B directive: intra-LTS cross-layer SKIP). \
Only flag when two alternatives resolve the SAME contradiction via DIFFERENT LTS ids — \
that indicates redundant work, not incompatibility.

6. **Record secondary contradictions** with:
   - The specific parameters or physical properties in conflict
   - severity: fatal (physically impossible) / major (requires redesign) / minor (risk only)
   - type: TC (two parameters trade off) or PC (same parameter needs opposite states)
   - improving_param / worsening_param numbers if identifiable
</method>

<convergence_formula>
After identifying all secondary contradictions, compute these intermediate values:

  total_contradictions = count of all contradictions (original + new secondary)
  resolved_or_minor = original contradictions marked resolved + minor secondary (non-blocking)
  fatal_unresolved = count of fatal contradictions (original + secondary) not resolved
  major_unresolved = count of major contradictions (original + secondary) not resolved
  clean_alternatives = alternatives that introduced 0 fatal/major secondary contradictions
  total_alternatives = count of all alternatives

  convergence_score = round(
    0.40 × (resolved_or_minor / max(total_contradictions, 1))
    + 0.25 × (1 if fatal_unresolved == 0 else 0)
    + 0.15 × (1 if major_unresolved == 0 else 0)
    + 0.20 × (clean_alternatives / max(total_alternatives, 1))
  ) × 100

Show all intermediate values in reasoning_trace.

Architecture health thresholds:
  - convergence_score > 80  → "healthy"
  - 50 ≤ convergence_score ≤ 80 → "warning"
  - convergence_score < 50  → "critical"

If any unresolved Fatal contradiction exists → force_pause = true.
</convergence_formula>

<output_schema>
{{
  "reasoning_trace": "Step-by-step parameter cross-check: [alt] improves P14 but worsens P26 ... intermediate: total=5, resolved_or_minor=3, fatal=0, major=1, clean=2/3 → score=round(0.40×0.6+0.25×1+0.15×0+0.20×0.67)×100=63",
  "new_contradictions": [
    {{
      "description": "Alternative X improves weight but introduces thermal coupling at controller MOSFETs",
      "severity": "major",
      "source_alternative": "alternative-id-or-name",
      "type": "TC",
      "improving_param": 1,
      "worsening_param": 17,
      "reasoning": "Integrated housing reduces mass (P1) but creates thermal path from motor to controller (P17), exceeding junction temp limit under sustained load"
    }}
  ],
  "convergence_score": 63,
  "architecture_health": "warning",
  "force_pause": false,
  "pause_reason": ""
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Validation Passport Generation (on-demand for any solution hypothesis)
# ---------------------------------------------------------------------------

SOLUTION_VALIDATION_PASSPORT = """\
<task>
Generate a validation passport for the given solution hypothesis. \
A validation passport declares the assumptions the solution depends on, \
its known weak points, and the experiments needed to falsify those assumptions. \
Every solution — whether from TRIZ or manual input — \
must carry this self-declared record.
</task>

<context>
<solution>
  <name>{solution_name}</name>
  <mechanism>{mechanism}</mechanism>
  <source>{source}</source>
</solution>
<project_constraints>
{constraints}
</project_constraints>
<project_kpis>
{kpis}
</project_kpis>
</context>

<instructions>
1. Identify 2–5 assumptions this solution depends on. For each:
   - **content** — What the assumption states.
   - **category** — physics / material / cost / manufacturing / regulatory / integration.
   - **evidence_level** — E0 (none), E1 (reasoning), E2 (analogy), E3 (test data), E4 (production-proven).
   - **worst_consequence** — What happens if this assumption is wrong.
   - **worst_severity** — critical / high / medium / low.
   - **suggested_experiment** — A specific, actionable experiment to test this assumption.

2. List 1–3 **weak_points** — acknowledged limitations that are NOT the same as \
assumptions. These are known trade-offs the solution accepts.

3. List **required_verifications** in priority order — the experiments or tests \
that must be completed before this solution can proceed to detailed design.

4. Assign an overall **confidence_level** (0–1):
   - ≥ 0.8: most assumptions backed by E2+ evidence
   - 0.5–0.8: mix of reasoning and analogy
   - < 0.5: mostly speculative (E0–E1)
</instructions>

<output_schema>
{{
  "validation_passport": {{
    "assumptions": [
      {{
        "content": "Assumption text",
        "category": "physics",
        "evidence_level": "E1",
        "worst_consequence": "What happens if wrong",
        "worst_severity": "high",
        "suggested_experiment": "How to test this"
      }}
    ],
    "weak_points": ["Known limitation"],
    "required_verifications": ["Priority experiment or test"],
    "cross_domain_source": "",
    "confidence_level": 0.5
  }}
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Brief Quality Review (Gate D1 AI evaluator)
# ---------------------------------------------------------------------------

BRIEF_QUALITY_REVIEW = """\
<task>
Assess the quality of a design brief — is the mission statement precise, \
are the KPIs truly measurable, and are the constraints well-defined?
</task>

<context>
<mission>{mission}</mission>
<constraints>
{constraints}
</constraints>
<kpis>
{kpis}
</kpis>
</context>

<instructions>
Score each dimension 1–5:

1. **mission_score** — Clarity, specificity, and quantifiability of the mission statement.
   - 5: Fully quantified, testable, unambiguous.
   - 3: Contains measurable elements but some vague terms remain.
   - 1: Entirely qualitative or vague ("make it better").
2. **kpi_score** — Measurability and completeness of KPIs.
   - 5: All KPIs have clear target values, units, and repeatable measurement methods.
   - 3: Most KPIs are measurable but some lack methods or have ambiguous targets.
   - 1: KPIs are vague or missing measurement methods.
3. **constraint_score** — Precision and verifiability of constraints.
   - 5: All constraints have clear pass/fail thresholds.
   - 3: Some constraints are qualitative or lack numeric limits.
   - 1: Constraints are vague or self-contradictory.

Compute overall_score as the minimum of the three scores.
Provide 1–3 concrete suggestions for improvement.
</instructions>

<output_schema>
{{
  "mission_score": 4,
  "kpi_score": 3,
  "constraint_score": 4,
  "overall_score": 3,
  "summary": "One-sentence quality assessment",
  "suggestions": ["Specific improvement suggestion"]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Depth Quality Review (Gate D2 AI evaluator)
# ---------------------------------------------------------------------------

DEPTH_QUALITY_REVIEW = """\
<task>
Assess whether the assumptions and contradictions identified so far \
are substantive and cover the critical dimensions of the design problem.
</task>

<context>
<mission>{mission}</mission>
<assumptions>
{assumptions}
</assumptions>
<contradictions>
{contradictions}
</contradictions>
</context>

<instructions>
Score each dimension 1–5:

1. **assumption_depth_score** — Do assumptions cover safety, physics, cost, \
manufacturing, supply chain, and regulatory dimensions?
   - 5: Comprehensive coverage across all critical dimensions.
   - 3: Covers major dimensions but misses 1–2 important areas.
   - 1: Shallow or redundant — mostly restating the obvious.
2. **contradiction_depth_score** — Are contradictions genuine engineering trade-offs \
(not trivial or tautological)?
   - 5: All contradictions are non-trivial, well-articulated trade-offs.
   - 3: Mix of substantive and superficial contradictions.
   - 1: Contradictions are trivial or poorly defined.

Compute overall_score as the minimum of the two scores.
List any blind_spots — critical dimensions that are completely unaddressed.
</instructions>

<output_schema>
{{
  "assumption_depth_score": 3,
  "contradiction_depth_score": 4,
  "overall_score": 3,
  "summary": "One-sentence depth assessment",
  "blind_spots": ["Dimension or topic not yet explored"]
}}
</output_schema>
"""

# ---------------------------------------------------------------------------
# Experiment Coverage Review (Gate X1 AI evaluator)
# ---------------------------------------------------------------------------

EXPERIMENT_COVERAGE_REVIEW = """\
<task>
Assess whether the planned experiments adequately validate the high-risk assumptions.
</task>

<context>
<high_risk_assumptions>
{high_risk_assumptions}
</high_risk_assumptions>
<experiments>
{experiments}
</experiments>
</context>

<instructions>
Score overall coverage 1–5:

1. **coverage_score**:
   - 5: Every high-risk assumption has a well-designed experiment that directly tests it.
   - 3: Most are covered, but some experiments are tangential or missing.
   - 1: Major gaps — critical assumptions lack any experimental validation.

For each uncovered or weakly covered assumption, explain:
- **uncovered_assumptions** — assumptions with no matching experiment.
- **weak_experiments** — experiments that exist but are unlikely to decisively \
validate the assumption (wrong method, insufficient precision, etc.).
</instructions>

<output_schema>
{{
  "coverage_score": 3,
  "summary": "One-sentence coverage assessment",
  "uncovered_assumptions": ["Assumption code + brief reason"],
  "weak_experiments": ["Experiment description + why it's weak"]
}}
</output_schema>
"""
