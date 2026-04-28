# .triz-state.json Schema

> SSOT for TRIZ session state. Only skills may write this file.

## Top-Level Fields

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `session_id` | string | triz-router | all skills | ✓ | Unique ID: `YYYY-MM-DD-{topic}` |
| `created_at` | ISO 8601 | triz-router | all | ✓ | Session creation timestamp |
| `current_step` | enum | each step skill | triz-router, hook | ✓ | `step0`\|`step1`\|`step2`\|`step3`\|`step4`\|`step5` |
| `path` | enum | triz-router, triz-contradict | all | ✓ | `tc-main`\|`sf-only`\|`multi-tc`\|`multi-tc-bottleneck`\|`multi-tc-sim` |
| `problem_description` | string | triz-router | all | ✓ | User's problem statement |
| `report_file` | string | triz-router | all | ✓ | Path to session markdown report |
| `specs` | object | triz-router | all | — | Domain-specific specifications (free-form) |
| `preliminary_tcs` | array\<TC_brief\> | triz-router | triz-model, triz-contradict | — | Initial TC hypotheses from routing |
| `spiral_iteration` | integer | triz-verify | triz-router | — | Spiral ascent counter (0 = first pass). Added when Step 4 detects new TC |

## step0

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-scoping | all | ✓ | |
| `routing` | enum | triz-scoping | triz-router | ✓ | `step1`\|`step2`\|`sf-only`\|`ceca` |
| `root_causes` | array\<string\> | triz-scoping | triz-model | — | From 5Why/CECA |
| `tc_hypothesis` | array\<string\> | triz-scoping | triz-model | — | Initial TC guesses |
| `ceca_nodes` | array\<object\> | triz-scoping | triz-model | — | CECA causal chain nodes |
| `ceca_key_nodes` | array\<string\> | triz-scoping | triz-model | — | CECA convergence nodes |
| `note` | string | triz-scoping | — | — | |

## step1

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-model | all | ✓ | |
| `fa_components` | array\<FA_entry\> | triz-model | triz-contradict | ✓ | Functional analysis: source, function, target, type |
| `sf_diagnosis` | array\<SF_entry\> | triz-model | triz-contradict | ✓ | S1, F, S2, status, linked TC |
| `improve_worsen_nl` | object | triz-model | triz-contradict | ✓ | `{TC_id: {improve: str, worsen: str}}` |
| `routing` | enum | triz-model | triz-router | ✓ | `tc-main`\|`sf-only` |

### FA_entry

```json
{"source": "str", "function": "str", "target": "str", "type": "useful|harmful|insufficient|excessive|missing"}
```

### SF_entry

```json
{"id": "SF1", "s1": "str", "f": "str", "s2": "str", "status": "harmful|insufficient|missing|excessive", "tc": "TC1,TC2"}
```

## step2

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-contradict | all | ✓ | |
| `multi_tc_path` | enum | triz-contradict | self | — | `bottleneck`\|`sim-iterate` |
| `bottleneck_tc` | string | triz-contradict | self | — | TC id if bottleneck path |
| `tcs` | array\<TC_full\> | triz-contradict | triz-verify | ✓ | Full TC definitions |

### TC_full

```json
{
  "id": "TC1",
  "p_improve": {"id": 10, "name": "Force"},
  "p_worsen": {"id": 7, "name": "Volume of moving object"},
  "matrix_principles": [15, 9, 12, 37],
  "selected_principles": [12, 15, 37],
  "bottleneck": true,
  "note": "optional"
}
```

## step3

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-contradict | all | ✓ | |
| `refinement_round` | integer | triz-contradict | self | — | 0 = first pass; increments on re-entry from Step 4 patch |
| `solutions` | object | triz-contradict / triz-analyst (via supervisor merge) | triz-verify, triz-wi | ✓ | `{TC_id: Solution_entry}` |
| `sim` | SIM_result | triz-contradict | triz-verify | — | Only for multi-TC |
| `sim_iteration_count` | integer | triz-contradict | self | — | SIM iteration counter (max 2) |
| `sim_minus1_history` | array\<integer\> | triz-contradict | self | — | -1 count per SIM round (must be monotonically decreasing) |

### Solution_entry

```json
{
  "pc": "str — PC statement (Px must be A and not-A)",
  "separation": "str — separation type + strategy",
  "oz": "str — operation zone",
  "ot": "str — operation time",
  "sf_class": ["1.3.2 (desc)", "2.2.5 (desc)"],
  "solution": "str — concrete solution description"
}
```

### SIM_result

```json
{
  "conflicts": 0,
  "synergies": 2,
  "synergy_pairs": [{"pair": "TC1-TC3", "score": 1, "reason": "str"}],
  "neutral_pairs": ["TC1-TC4"],
  "verdict": "str"
}
```

## step4

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-verify | all | ✓ | |
| `px_separation_verified` | boolean | triz-verify | triz-wi | ✓ | |
| `px_results` | object | triz-verify | triz-wi | ✓ | `{TC_id: "Pass/Fail — detail"}` |
| `verdict` | enum | triz-verify | triz-router, triz-wi | ✓ | `evolution`\|`weak-evolution`\|`patch`\|`strong-patch` |
| `complexity_scores` | CCI_scores | triz-verify | triz-wi | ✓ | |
| `cci_verdict` | string | triz-verify | all | ✓ | Human-readable CCI label |
| `evidence_registry` | Evidence_registry | triz-verify | triz-wi | ✓ | |
| `new_tc_detected` | boolean | triz-verify | triz-router | ✓ | If true, spiral_iteration incremented |
| `new_tc_description` | string | triz-verify | triz-router | — | Only if new_tc_detected=true |
| `observation_items` | array\<string\> | triz-verify | triz-wi, tr-gate | ✓ | Items to watch in TR phase |

### CCI_scores

```json
{
  "structural": 0.25,
  "energy": 0.50,
  "cognitive": 0.75,
  "evolution_aligned": 0.00,
  "cci": 0.35
}
```

### Evidence_registry

```json
{
  "total_claims": 11,
  "high_confidence": 6,
  "medium_confidence": 4,
  "low_confidence": 1,
  "coverage_pct": 91,
  "evolution_sustained": true,
  "corrections": ["str"]
}
```

## step5

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `completed` | boolean | triz-wi | all | ✓ | |
| `subsystems_identified` | array\<string\> | triz-wi | tr-router | ✓ | |
| `wi_files` | array\<string\> | triz-wi | tr-gate, tr-fea-assist | ✓ | Filenames in output_dir |
| `icd_files` | array\<string\> | triz-wi | tr-gate | ✓ | |
| `mc_files` | array\<string\> | triz-wi | tr-fea-assist | ✓ | |
| `framework_files` | array\<string\> | triz-wi | tr-gate | ✓ | |
| `total_files` | integer | triz-wi | all | ✓ | |
| `output_dir` | string | triz-wi | all | ✓ | Should be `docs/engineering/` |

---

# .tr-state.json Schema

> SSOT for TR gate engineering execution. Only TR skills may write.

## Top-Level Fields

| Field | Type | Writer | Reader | Required | Description |
|:------|:-----|:-------|:-------|:--------:|:------------|
| `project_id` | string | triz-wi (bootstrap) | all TR skills | ✓ | |
| `triz_session_ref` | string | triz-wi (bootstrap) | tr-router | ✓ | Points to `.triz-state.json` session_id |
| `triz_state_hash` | string | triz-wi (bootstrap), tr-router (refresh) | tr-router | — | SHA-256 of .triz-state.json for staleness check |
| `created_at` | ISO 8601 | triz-wi | all | ✓ | |
| `subsystem_tr` | object | tr-gate | all TR skills | ✓ | `{subsystem: SubsystemTR}` |
| `wi_status` | object | tr-gate, tr-fea-assist | all TR skills | ✓ | `{WI-nn: WI_status}` |
| `gate_reviews` | array\<GateReview\> | tr-gate | all TR skills | ✓ | |
| `v_tests` | object | tr-test-report | tr-gate | ✓ | `{Vn: V_test}` |
| `risk_status` | object | tr-gate | all TR skills | ✓ | `{R-nnn: "open"\|"mitigated"\|"closed"}` |

### SubsystemTR

```json
{
  "current": "TR0",
  "target": "TR1",
  "blockers": ["str"],
  "responsible_wi": ["WI-01"]
}
```

### WI_status

```json
{
  "status": "not_started|in_progress|completed",
  "steps_completed": ["str"],
  "deliverables": {}
}
```

### GateReview

```json
{
  "gate": "TR1",
  "date": "2026-MM-DD",
  "verdict": "GO|CONDITIONAL|NO-GO",
  "report_file": "docs/engineering/gate_reviews/TR1_review_YYYY-MM-DD.md",
  "conditions": ["str"]
}
```

### V_test

```json
{
  "status": "not_tested|pass|fail|conditional",
  "result": null,
  "phase": "A|B|C|D",
  "subsystem": "motor|gearbox|thermal|system"
}
```
