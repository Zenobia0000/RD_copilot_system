# RD Design Copilot -- API Reference

> Version 0.1.0 | Base URL: `http://localhost:8000/api/v1`

---

## Authentication

All endpoints (except `GET /api/v1/health`) require a **Bearer token** in the `Authorization` header.
The token is a **Supabase JWT** obtained after user login.

```
Authorization: Bearer <supabase-jwt>
```

---

## Error Response Format

Every error returns a consistent JSON envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "detail": null
  }
}
```

| HTTP Status | Code | Cause |
|-------------|------|-------|
| 400 | `HTTP_400` | Bad request (e.g., invalid gate_id) |
| 401 | `HTTP_401` | Missing or invalid JWT |
| 404 | `HTTP_404` | Resource not found |
| 422 | `VALIDATION_ERROR` | Request body fails Pydantic validation (`detail` contains field-level errors) |
| 500 | `INTERNAL_ERROR` | Unhandled server exception |
| 503 | `RATE_LIMIT` | Anthropic API rate limited |
| 503 | `SERVICE_UNAVAILABLE` | Anthropic API connection error |
| 503 | `AI_SERVICE_ERROR` | Anthropic API returned non-200 |

---

## Health Check

```
GET /api/v1/health
```

No auth required. Returns `{"status": "ok"}`.

---

## 1. Definitions (Brief)

### 1.1 Extract Brief

Extract structured constraints, KPIs, and assumptions from raw text.

```
POST /api/v1/definitions/extract
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | yes | Project UUID |
| `raw_text` | string | no | Raw brief / spec text |
| `file_urls` | string[] | no | Uploaded file URLs |

**Response** `BriefExtractionResponse`

| Field | Type |
|-------|------|
| `constraints` | `ExtractedConstraint[]` (code, description, source, type, feasibility) |
| `kpis` | `ExtractedKpi[]` (name, target_value, unit, measurement_method) |
| `assumptions` | string[] |
| `feasibility_warnings` | string[] |

```bash
curl -X POST http://localhost:8000/api/v1/definitions/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","raw_text":"Design an e-bike motor controller with 95% efficiency..."}'
```

### 1.2 Rewrite Mission

AI rewrites mission statement with precise engineering language.

```
POST /api/v1/definitions/rewrite
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | yes | |
| `mission` | string | yes | Current mission statement |
| `constraints` | string[] | no | Existing constraint descriptions |
| `kpis` | string[] | no | Existing KPI names |

**Response** `BriefRewriteResponse`

| Field | Type |
|-------|------|
| `rewritten_mission` | string |
| `changes_summary` | string |
| `evidence_references` | `EvidenceReference[]` |

```bash
curl -X POST http://localhost:8000/api/v1/definitions/rewrite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Build a motor controller"}'
```

### 1.3 Suggest Constraints

AI suggests missing hard constraints.

```
POST /api/v1/definitions/suggest-constraints
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `existing_constraints` | string[] | no |

**Response** `ConstraintSuggestResponse`

| Field | Type |
|-------|------|
| `suggestions` | `SuggestedConstraint[]` (description, source, rationale, ref_ids) |
| `evidence_references` | `EvidenceReference[]` |

```bash
curl -X POST http://localhost:8000/api/v1/definitions/suggest-constraints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design an e-bike motor controller"}'
```

### 1.4 Suggest KPIs

AI suggests KPIs based on mission and constraints.

```
POST /api/v1/definitions/suggest-kpis
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `constraints` | string[] | no |
| `existing_kpis` | string[] | no |

**Response** `KpiSuggestResponse`

| Field | Type |
|-------|------|
| `suggestions` | `SuggestedKpi[]` (kpi_name, target_value, unit, measurement_method, rationale, ref_ids) |
| `evidence_references` | `EvidenceReference[]` |

```bash
curl -X POST http://localhost:8000/api/v1/definitions/suggest-kpis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design an e-bike motor controller","constraints":["Efficiency >= 95%"]}'
```

### 1.5 Generate 5W1H

AI generates 5W1H task definition from mission context.

```
POST /api/v1/definitions/generate-5w1h
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `constraints` | string[] | no |
| `kpis` | string[] | no |

**Response** `TaskDef5W1HResponse`

| Field | Type |
|-------|------|
| `who` | string |
| `what` | string |
| `where` | string |
| `when` | string |
| `why` | string |
| `how` | string |
| `evidence_references` | `EvidenceReference[]` |

```bash
curl -X POST http://localhost:8000/api/v1/definitions/generate-5w1h \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design an e-bike motor controller"}'
```

---

## 2. Questions (Socratic)

### 2.1 Generate Socratic Questions

Generate Socratic questions across 7 categories to surface assumptions and contradictions.

```
POST /api/v1/questions/generate
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `constraints` | string[] | no |
| `existing_questions` | string[] | no |

**Response** `SocraticResponse`

| Field | Type |
|-------|------|
| `questions` | `SocraticQuestion[]` (category, text, suggested_tag) |

Categories: `clarification`, `assumption`, `consequence`, `counter`, `origin`, `reflection`, `reframing`

```bash
curl -X POST http://localhost:8000/api/v1/questions/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design an e-bike motor controller","constraints":["Max weight 2kg"]}'
```

---

## 3. Contradictions

### 3.1 Formalize Contradiction

Formalize a natural-language contradiction into a TRIZ-compatible sentence.

```
POST /api/v1/contradictions/{cid}/formalize
```

**Path Parameters**

| Param | Description |
|-------|-------------|
| `cid` | Contradiction UUID |

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `contradiction_id` | string | yes |
| `natural_description` | string | yes |

**Response** `ContradictionFormalizeResponse`

| Field | Type |
|-------|------|
| `engineering_statement` | string |
| `improving_param` | int or null |
| `worsening_param` | int or null |
| `physical_contradiction` | string or null |
| `type` | string (`"TC"` or `"PC"`) |
| `confidence` | float (0--1) |

```bash
curl -X POST http://localhost:8000/api/v1/contradictions/abc-123/formalize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","contradiction_id":"abc-123","natural_description":"Higher torque requires larger motor but weight limit is 2kg"}'
```

---

## 4. Causal Loops (CLD)

### 4.1 Generate CLD

Generate a causal loop diagram with breakpoints from contradictions and assumptions.

```
POST /api/v1/causal-loops/generate
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `contradictions` | string[] | yes |
| `assumptions` | string[] | yes |

**Response** `CldGenerationResponse`

| Field | Type |
|-------|------|
| `nodes` | `CldNode[]` (id, label, type) |
| `edges` | `CldEdge[]` (from_node, to_node, polarity) |
| `breakpoints` | string[] (node IDs that are leverage points) |

```bash
curl -X POST http://localhost:8000/api/v1/causal-loops/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","contradictions":["Torque vs Weight"],"assumptions":["Neodymium magnet available"]}'
```

---

## 5. Assumptions

### 5.1 Extract Assumptions

Extract assumptions from Socratic question answers.

```
POST /api/v1/assumptions/extract
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `questions_and_answers` | dict[] | no |
| `mission` | string | no |

**Response** `AssumptionExtractResponse`

| Field | Type |
|-------|------|
| `assumptions` | `ExtractedAssumption[]` (content, source, worst_consequence, worst_severity) |

Severity levels: `critical`, `high`, `medium`, `low`

```bash
curl -X POST http://localhost:8000/api/v1/assumptions/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Motor controller","questions_and_answers":[{"question":"Why 95%?","answer":"Industry standard"}]}'
```

---

## 6. Alternatives (Anti-Anchor)

### 6.1 Anti-Anchor Sprint

Generate 3+ non-typical architecture concepts to break path dependency.

```
POST /api/v1/alternatives/anti-anchor
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `current_constraints` | string[] | yes |
| `existing_alternatives` | string[] | no |

**Response** `AntiAnchorResponse`

| Field | Type |
|-------|------|
| `routes` | `AntiAnchorRoute[]` (name, description, is_non_typical, rationale) |

```bash
curl -X POST http://localhost:8000/api/v1/alternatives/anti-anchor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design motor controller","current_constraints":["Weight <= 2kg"]}'
```

---

## 7. TRIZ

### 7.1 Solve Contradiction

Resolve contradiction via Technical Contradiction (TC) or Physical Contradiction (PC) path.

```
POST /api/v1/triz/solve
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `contradiction_id` | string | yes |
| `natural_description` | string | yes |
| `improving_param` | int | no |
| `worsening_param` | int | no |
| `physical_contradiction` | string | no |
| `type` | string | no (default `"TC"`) |

**Response** `TrizLookupResponse`

| Field | Type |
|-------|------|
| `mapped_improving` | int or null |
| `mapped_worsening` | int or null |
| `candidate_principles` | int[] |
| `suggestions` | `TrizSuggestion[]` (path, principle_number, principle_name, suggestion, affected_modules, secondary_contradictions) |

```bash
curl -X POST http://localhost:8000/api/v1/triz/solve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","contradiction_id":"c-1","natural_description":"Torque vs Weight","type":"TC","improving_param":10,"worsening_param":1}'
```

---

## 8. Subsystems

> **Migration note**: These endpoints were previously under `/scamper/`. The
> old paths (`/scamper/subsystem-suggestions`, `/scamper/spatial-overlay`)
> return HTTP 308 redirects for backward compatibility. The `/scamper/perform`
> and `/scamper/feedback-contradictions` endpoints have been retired — TRIZ 40
> principles cover all SCAMPER actions.

### 8.1 Subsystem Suggestions

AI suggests subsystems suitable for design analysis.

```
POST /api/v1/subsystems/suggest
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `contradictions` | string[] | no |
| `existing_subsystems` | string[] | no |
| `layered_triz_solutions` | `LayeredTrizSolution[]` | no |

**Response** `SubsystemSuggestResponse`

| Field | Type |
|-------|------|
| `subsystems` | `SuggestedSubsystem[]` (name, level, reason, related_contradictions, children, interface_contracts) |
| `package_map` | `PackageMap` or null |

```bash
curl -X POST http://localhost:8000/api/v1/subsystems/suggest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design motor controller"}'
```

### 8.2 Spatial Overlay

Apply a what-if spatial overlay to a subsystem tree.

```
POST /api/v1/subsystems/spatial-overlay
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `subsystems` | `SuggestedSubsystem[]` | no |
| `overlay` | dict | no |

**Response** `SpatialOverlayResponse`

| Field | Type |
|-------|------|
| `package_map` | `PackageMap` |

```bash
curl -X POST http://localhost:8000/api/v1/subsystems/spatial-overlay \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","subsystems":[],"overlay":{"zones":{"downtube":{"x_mm":400}}}}'
```

---

## 9. MUST Evaluation

### 9.1 Evaluate MUST

AI pre-judges Go/No-Go for an alternative against MUST criteria.

```
POST /api/v1/must/evaluate
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `alternative_name` | string | yes |
| `mechanism` | string | yes |
| `must_criteria` | `MustCriterionConfig[]` | yes |
| `constraints` | string[] | no |
| `kpis` | string[] | no |

`MustCriterionConfig`: `{ id, label, source, threshold }`

**Response** `MustEvaluationResponse`

| Field | Type |
|-------|------|
| `criteria_results` | `MustCriterionResult[]` (id, label, passed, confidence, reasoning, evidence_sources) |
| `overall_pass` | bool or null |
| `summary` | string |

```bash
curl -X POST http://localhost:8000/api/v1/must/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","alternative_name":"Design A","mechanism":"BLDC + FOC","must_criteria":[{"id":"M1","label":"Efficiency >= 95%","source":"KPI-1","threshold":"95%"}]}'
```

---

## 10. Pre-CAD Reviews

### 10.1 AI Analyze

AI performs 5D Pre-CAD scoring (Spatial, Cost, Safety, Decoupling, Supply).

```
POST /api/v1/pre-cad-reviews/{rid}/ai-analyze
```

**Path Parameters**

| Param | Description |
|-------|-------------|
| `rid` | Review UUID |

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `alternative_name` | string | yes |
| `mechanism` | string | yes |
| `constraints` | string[] | no |

**Response** `PreCadAnalyzeResponse`

| Field | Type |
|-------|------|
| `spatial_score` | int (1--5) |
| `cost_score` | int (1--5) |
| `safety_score` | int (1--5) |
| `decoupling_score` | int (1--5) |
| `supply_score` | int (1--5) |
| `overall_pass` | bool |
| `analysis` | string |
| `evidence_references` | `EvidenceReference[]` |

```bash
curl -X POST http://localhost:8000/api/v1/pre-cad-reviews/rev-123/ai-analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","alternative_name":"Design A","mechanism":"BLDC + FOC"}'
```

---

## 11. Risks

### 11.1 Analyze Risks

FMEA-style risk identification with probability x severity scoring.

```
POST /api/v1/risks/analyze
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `alternative_name` | string | yes |
| `mechanism` | string | yes |
| `assumptions` | string[] | no |

**Response** `RiskAnalysisResponse`

| Field | Type |
|-------|------|
| `risks` | `RiskSuggestion[]` (description, failure_mode, probability 1--5, severity 1--5, mitigation) |

```bash
curl -X POST http://localhost:8000/api/v1/risks/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","alternative_name":"Design A","mechanism":"BLDC + FOC"}'
```

---

## 12. Actions

### 12.1 Suggest Actions

Generate post-decision action items with assignee roles.

```
POST /api/v1/actions/suggest
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `selected_alternative` | string | yes |
| `rationale` | string | yes |
| `risks` | string[] | no |

**Response** `ActionSuggestResponse`

| Field | Type |
|-------|------|
| `actions` | `ActionSuggestion[]` (description, assignee_role, suggested_due_days) |

```bash
curl -X POST http://localhost:8000/api/v1/actions/suggest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","selected_alternative":"Design A","rationale":"Best efficiency/weight ratio"}'
```

---

## 13. Convergence

### 13.1 Convergence Scan

Detect secondary contradictions and assess architecture health.

```
POST /api/v1/convergence/scan
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `alternatives` | dict[] | yes |
| `contradictions` | dict[] | yes |

**Response** `ConvergenceScanResponse`

| Field | Type |
|-------|------|
| `new_contradictions` | `SecondaryContradiction[]` (description, severity, source_alternative) |
| `convergence_score` | float |
| `architecture_health` | string (`"healthy"`, `"warning"`, `"critical"`) |
| `force_pause` | bool |
| `pause_reason` | string |

```bash
curl -X POST http://localhost:8000/api/v1/convergence/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","alternatives":[{"name":"A","mechanism":"BLDC"}],"contradictions":[{"description":"Torque vs Weight"}]}'
```

---

## 14. WANT

### 14.1 Seed WANT Criteria

AI generates W1--W6 desirable criteria for KT decision matrix.

```
POST /api/v1/want/criteria/seed
```

**Request Body**

| Field | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |
| `mission` | string | yes |
| `constraints` | string[] | no |
| `kpis` | string[] | no |

**Response** `WantSeedResponse`

| Field | Type |
|-------|------|
| `criteria` | `SuggestedWantCriterion[]` (name, description, weight 1--10, anchors) |

```bash
curl -X POST http://localhost:8000/api/v1/want/criteria/seed \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","mission":"Design motor controller","kpis":["Efficiency","Weight"]}'
```

---

## 15. Gates

### 15.1 Check Gate

Verify whether a project passes a specific quality gate.

```
GET /api/v1/gates/{gate_id}/check?project_id={project_id}
```

**Path Parameters**

| Param | Description |
|-------|-------------|
| `gate_id` | One of: `1.1`, `1.2`, `PG1`, `2.1`, `2.2`, `PG2`, `3.2`, `PG3` |

**Query Parameters**

| Param | Type | Required |
|-------|------|----------|
| `project_id` | string | yes |

**Response** `GateCheckResponse`

| Field | Type |
|-------|------|
| `gate_id` | string |
| `passed` | bool |
| `failed_reasons` | string[] |
| `checklist_items` | `GateCheckItem[]` (label, met, detail) |

**Gate Pass Conditions**

| Gate | Condition |
|------|-----------|
| 1.1 | Mission defined + >= 3 KPIs with measurement method |
| 1.2 | >= 10 assumptions + >= 3 high-risk + >= 3 contradictions |
| PG1 | >= 1 CLD + >= 3 breakpoints |
| 2.1 | >= 3 high-risk assumptions with experiments |
| 2.2 | >= 3 alternatives |
| PG2 | >= 1 alternative passed Pre-CAD |
| 3.2 | Decision record signed |
| PG3 | All core artifacts released (manual) |

```bash
curl -X GET "http://localhost:8000/api/v1/gates/1.1/check?project_id=uuid" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 16. Export

### 16.1 Export Project

Export project artifacts to Markdown or JSON format.

```
POST /api/v1/export
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | yes | |
| `format` | string | no | `"markdown"` (default) or `"json"` |
| `sections` | string[] | no | Empty = all sections |

Available sections: `brief`, `constraints`, `kpis`, `assumptions`, `contradictions`, `cld`, `alternatives`, `triz_solutions`, `scamper_variants`, `risks`, `experiments`, `decisions`, `knowledge`

**Response** `ExportResponse`

| Field | Type |
|-------|------|
| `content` | string |
| `format` | string |
| `filename` | string |

```bash
curl -X POST http://localhost:8000/api/v1/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","format":"markdown","sections":["brief","assumptions","risks"]}'
```

---

## 17. Knowledge Writeback

### 17.1 Writeback Knowledge

Auto-assetize project artifacts into the knowledge base (6 asset types).

```
POST /api/v1/knowledge/writeback
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | yes | |
| `asset_types` | string[] | no | Empty = all 6 types |

**Response** `KnowledgeWritebackResponse`

| Field | Type |
|-------|------|
| `written_count` | int |
| `assets` | `WrittenAsset[]` (asset_type, title, id) |

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/writeback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"uuid","asset_types":["constraint","assumption"]}'
```

---

## Common Types

### EvidenceReference

Returned by many AI endpoints as supporting evidence.

| Field | Type | Description |
|-------|------|-------------|
| `ref_id` | string | e.g. `"WEB-SEARCH-001"` |
| `ref_type` | string | `"web_search"`, `"uploaded_doc"`, or `"engineering_reasoning"` |
| `title` | string | |
| `source` | string | Domain, filename, or description |
| `url` | string | Optional URL |
| `snippet` | string | Optional text excerpt |
