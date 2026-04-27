"""E2E scenario test: eBike mid-drive motor design through Phase 1 -> Phase 2 -> Phase 3.

Simulates a realistic design project for a high-efficiency mid-drive motor for urban eBike,
flowing through all stages of the copilot pipeline with data passing between steps.

All external services (LLM calls and Supabase) are mocked.
"""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared constants — realistic eBike mid-drive motor project
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-ebike-mid-drive-001"
MISSION = "Design a high-efficiency mid-drive motor for urban eBike"

# ---------------------------------------------------------------------------
# LLM mock responses — realistic eBike data
# ---------------------------------------------------------------------------

_BRIEF_EXTRACT_RESPONSE = json.dumps({
    "constraints": [
        {
            "code": "C1",
            "description": "Peak efficiency >= 95%",
            "source": "customer_spec",
            "type": "hard",
            "feasibility": "challenging",
        },
        {
            "code": "C2",
            "description": "Thermal rise <= 35C above ambient at rated load",
            "source": "safety_standard",
            "type": "hard",
            "feasibility": "feasible",
        },
        {
            "code": "C3",
            "description": "BOM cost <= $12 per unit",
            "source": "business_target",
            "type": "hard",
            "feasibility": "challenging",
        },
    ],
    "kpis": [
        {
            "name": "Peak Efficiency",
            "target_value": "95",
            "unit": "%",
            "measurement_method": "dynamometer at rated torque",
        },
        {
            "name": "Thermal Drop",
            "target_value": "35",
            "unit": "degC",
            "measurement_method": "thermocouple on stator winding",
        },
        {
            "name": "BOM Cost",
            "target_value": "12",
            "unit": "USD",
            "measurement_method": "supplier quotation aggregation",
        },
    ],
    "assumptions": [
        "Ambient temperature range is 0-40C",
        "Battery voltage is 36V nominal (42V max)",
        "Cadence sensor provides reliable pedal input",
    ],
    "feasibility_warnings": [
        "95% peak efficiency at $12 BOM is aggressive — may require novel winding topology",
        "Thermal drop target constrains housing material choices",
    ],
})

_SOCRATIC_RESPONSE = json.dumps({
    "questions": [
        {
            "category": "assumption",
            "text": "What if the rider operates in sustained hill-climb mode exceeding rated torque for >10 minutes?",
            "suggested_tag": "assumption",
        },
        {
            "category": "contradiction",
            "text": "How do you achieve 95% efficiency while keeping BOM under $12 — high-grade magnets needed for efficiency raise cost?",
            "suggested_tag": "contradiction",
        },
        {
            "category": "clarification",
            "text": "Is the 95% efficiency target at the motor shaft or including controller losses?",
            "suggested_tag": None,
        },
        {
            "category": "consequence",
            "text": "What happens to thermal performance if potting compound is eliminated to save cost?",
            "suggested_tag": "contradiction",
        },
    ],
})

_CONTRADICTION_FORMALIZE_TC_RESPONSE = json.dumps({
    "engineering_statement": "Improving motor efficiency (param #31: Harmful factors acting on object) worsens weight (param #1: Weight of moving object) due to larger magnet volume required",
    "improving_param": 31,
    "worsening_param": 1,
    "physical_contradiction": None,
    "type": "TC",
    "confidence": 0.85,
})

_CONTRADICTION_FORMALIZE_PC_RESPONSE = json.dumps({
    "engineering_statement": "The motor housing must simultaneously have high thermal conductivity (to dissipate heat) and low thermal conductivity (to insulate electronics)",
    "improving_param": None,
    "worsening_param": None,
    "physical_contradiction": "Housing must be thermally conductive and thermally insulating simultaneously",
    "type": "PC",
    "confidence": 0.80,
})

_TRIZ_TC_RESPONSE = json.dumps({
    "suggestions": [
        {
            "path": "TC",
            "principle_number": 35,
            "principle_name": "Parameter changes",
            "suggestion": "Change winding geometry from round to flat ribbon wire to increase copper fill factor by 15%, improving efficiency without proportional weight increase",
            "affected_modules": ["stator", "winding"],
            "secondary_contradictions": ["Flat ribbon wire may increase manufacturing complexity"],
        },
        {
            "path": "TC",
            "principle_number": 28,
            "principle_name": "Mechanics substitution",
            "suggestion": "Replace mechanical commutation with optimized FOC algorithm to extract more torque per ampere, reducing copper mass needed",
            "affected_modules": ["controller", "firmware"],
            "secondary_contradictions": ["Higher computing cost for advanced FOC"],
        },
    ],
})

_SCAMPER_RESPONSE = json.dumps({
    "variants": [
        {
            "action": "Substitute",
            "description": "Substitute NdFeB magnets with ferrite + Halbach arrangement to reduce cost while maintaining flux density",
            "potential_benefits": "60% magnet cost reduction, eliminates rare-earth supply risk",
            "new_contradictions": ["Ferrite has lower remanence, requiring larger magnet volume"],
        },
        {
            "action": "Combine",
            "description": "Combine motor housing with heatsink — use die-cast aluminum housing with integrated cooling fins",
            "potential_benefits": "Eliminates separate heatsink, reduces assembly steps",
            "new_contradictions": ["Die-cast aluminum may have porosity affecting thermal conductivity"],
        },
        {
            "action": "Adapt",
            "description": "Adapt automotive-grade concentrated winding from EV traction motors to mid-drive eBike scale",
            "potential_benefits": "Shorter end-turns reduce copper loss by 10%",
            "new_contradictions": ["Concentrated winding increases torque ripple"],
        },
        {
            "action": "Modify",
            "description": "Modify stator tooth geometry with tapered tips to optimize flux distribution",
            "potential_benefits": "2% efficiency improvement at partial load",
            "new_contradictions": [],
        },
        {
            "action": "Put to other use",
            "description": "Use motor back-EMF for battery regenerative braking, recovering 5-8% energy on descents",
            "potential_benefits": "Extended range without additional hardware",
            "new_contradictions": ["Regenerative braking adds controller complexity"],
        },
        {
            "action": "Eliminate",
            "description": "Eliminate position sensor by implementing sensorless FOC startup algorithm",
            "potential_benefits": "Saves $0.80 per unit, improves reliability",
            "new_contradictions": ["Sensorless startup may have poor low-speed performance"],
        },
        {
            "action": "Reverse",
            "description": "Reverse rotor-stator arrangement — outer rotor design for higher torque density",
            "potential_benefits": "30% higher torque density, simplified assembly",
            "new_contradictions": ["Outer rotor complicates thermal management of inner stator"],
        },
    ],
})

_SCAMPER_FEEDBACK_EXISTING = [
    {"id": "c-existing-1", "natural_description": "Ferrite has lower remanence requiring larger magnet volume"},
]

_MUST_EVAL_RESPONSE = json.dumps({
    "criteria_results": [
        {
            "id": "M1",
            "label": "Peak efficiency >= 95%",
            "passed": True,
            "confidence": 0.82,
            "reasoning": "Flat ribbon winding + optimized FOC is projected to achieve 95.3% peak efficiency based on FEA simulation benchmarks",
            "evidence_sources": ["motor_FEA_benchmark", "winding_fill_study"],
        },
        {
            "id": "M2",
            "label": "Thermal rise <= 35C",
            "passed": True,
            "confidence": 0.75,
            "reasoning": "Integrated aluminum housing heatsink with 12 fins provides estimated 30C rise at rated load",
            "evidence_sources": ["thermal_CFD_estimate"],
        },
        {
            "id": "M3",
            "label": "BOM cost <= $12",
            "passed": True,
            "confidence": 0.68,
            "reasoning": "Ferrite magnets + sensorless design saves $2.50 vs baseline; estimated BOM $11.40",
            "evidence_sources": ["supplier_quote_Q3", "BOM_calculator"],
        },
    ],
    "overall_pass": True,
    "summary": "Alternative passes all MUST criteria. Cost confidence is lowest — recommend supplier quote validation before gate.",
})

_PRE_CAD_RESPONSE = json.dumps({
    "spatial_score": 4,
    "cost_score": 3,
    "safety_score": 4,
    "decoupling_score": 3,
    "supply_score": 4,
    "overall_pass": True,
    "analysis": "Mid-drive axial-flux design fits within standard BB shell envelope (68mm). Cost score limited by die-cast tooling investment. Decoupling score reduced due to thermal coupling between motor and controller in integrated housing. Supply chain favorable with ferrite magnets.",
    "evidence_references": [],
})

_RISK_ANALYSIS_RESPONSE = json.dumps({
    "risks": [
        {
            "description": "Flat ribbon winding manufacturing yield",
            "failure_mode": "Insulation breakdown between ribbon layers causing inter-turn short circuit",
            "probability": 3,
            "severity": 4,
            "mitigation": "Implement automated winding machine with real-time insulation resistance monitoring",
        },
        {
            "description": "Ferrite magnet demagnetization at high temperature",
            "failure_mode": "Permanent loss of magnetic flux above 150C, reducing motor output by >20%",
            "probability": 2,
            "severity": 5,
            "mitigation": "Add thermal fuse cutoff at 130C stator temperature; use high-Hci ferrite grade",
        },
        {
            "description": "Sensorless FOC startup failure under load",
            "failure_mode": "Motor fails to start when rider is on incline with weight on pedals",
            "probability": 3,
            "severity": 3,
            "mitigation": "Implement pulse injection sensorless algorithm with hill-start assist logic",
        },
    ],
})

_CONVERGENCE_SCAN_RESPONSE = json.dumps({
    "reasoning_trace": "Alt 'Axial-Flux Ferrite Mid-Drive' improves P1(weight) but worsens P17(temperature) due to integrated housing. intermediate: total=2, resolved_or_minor=0, fatal=0, major=1, clean=0/1 → score=round(0.40*0+0.25*1+0.15*0+0.20*0)*100=25",
    "new_contradictions": [
        {
            "description": "Integrated housing thermal coupling creates hotspot at controller MOSFETs when motor runs at sustained high load",
            "severity": "major",
            "source_alternative": "Axial-Flux Ferrite Mid-Drive",
            "type": "TC",
            "improving_param": 1,
            "worsening_param": 17,
            "reasoning": "Integrated die-cast housing reduces mass (P1) but creates thermal path from motor windings to controller MOSFETs (P17), exceeding Tj limit under sustained hill-climb load",
        },
    ],
    "convergence_score": 0.25,
    "architecture_health": "critical",
    "force_pause": False,
    "pause_reason": "",
})

_KNOWLEDGE_SYNTHESIS_RESPONSE = json.dumps({
    "title": "Axial-Flux Ferrite Mid-Drive Design Pattern",
    "content": "Ferrite Halbach array in axial-flux topology achieves 95%+ efficiency at sub-$12 BOM. Key enablers: flat ribbon concentrated winding for high fill factor, integrated die-cast aluminum housing as heatsink. Critical watch: thermal coupling between motor and controller in integrated housing.",
})


# ---------------------------------------------------------------------------
# Supabase mock helpers (reused from test_gates.py pattern)
# ---------------------------------------------------------------------------

def _sb_response(data=None, count=None):
    return SimpleNamespace(data=data, count=count)


def _make_chain(final_response):
    m = MagicMock()
    m.execute.return_value = final_response
    m.maybe_single.return_value = m
    m.eq.return_value = m
    m.gte.return_value = m
    m.select.return_value = m
    m.insert.return_value = m
    return m


def _build_sb_mock(table_map: dict[str, MagicMock]) -> MagicMock:
    sb = MagicMock()
    sb.table.side_effect = lambda name: table_map.get(name, _make_chain(_sb_response(data=[], count=0)))
    return sb


def _mock_scamper_feedback_supabase(existing_rows=None):
    """Build Supabase mock for SCAMPER feedback endpoint."""
    if existing_rows is None:
        existing_rows = []

    client = MagicMock()

    select_result = MagicMock()
    select_result.data = existing_rows

    select_chain = MagicMock()
    select_chain.eq.return_value = MagicMock(execute=MagicMock(return_value=select_result))

    def make_insert_result(rows):
        result = MagicMock()
        result.data = [
            {**row, "id": row.get("id", str(uuid.uuid4()))} for row in rows
        ]
        return result

    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(
        side_effect=lambda: make_insert_result(insert_chain._last_rows)
    )

    def capture_insert(rows):
        insert_chain._last_rows = rows
        return insert_chain

    table_mock = MagicMock()
    table_mock.select.return_value = select_chain
    table_mock.insert.side_effect = capture_insert

    client.table.return_value = table_mock
    return client


def _make_knowledge_supabase(table_data: dict):
    """Create Supabase mock for knowledge writeback."""

    def table_router(name: str):
        chain = MagicMock()

        def select_fn(*args, **kwargs):
            eq_mock = MagicMock()
            eq_mock.eq = lambda col, val: eq_mock
            eq_mock.gte = lambda col, val: eq_mock

            def execute_fn():
                resp = MagicMock()
                resp.data = table_data.get(name, [])
                return resp

            eq_mock.execute = execute_fn
            return eq_mock

        chain.select = select_fn

        def insert_fn(rows):
            insert_mock = MagicMock()

            def exec_insert():
                resp = MagicMock()
                inserted = []
                for r in (rows if isinstance(rows, list) else [rows]):
                    row = dict(r)
                    row["id"] = row.get("id", str(uuid.uuid4()))
                    inserted.append(row)
                resp.data = inserted
                return resp

            insert_mock.execute = exec_insert
            return insert_mock

        chain.insert = insert_fn
        return chain

    sb = MagicMock()
    sb.table = table_router
    return sb


def _make_export_supabase():
    """Create Supabase mock for the export endpoint."""
    def table_router(name: str):
        chain = MagicMock()

        def select_fn(*args, **kwargs):
            eq_mock = MagicMock()
            eq_mock.eq = lambda col, val: eq_mock

            def maybe_single_fn():
                ms_mock = MagicMock()
                def execute_fn():
                    if name == "projects":
                        return _sb_response(data={"name": "eBike-MidDrive-v1"})
                    return _sb_response(data=[])
                ms_mock.execute = execute_fn
                return ms_mock
            eq_mock.maybe_single = maybe_single_fn

            def execute_fn():
                return _sb_response(data=[
                    {"mission": MISSION, "task_definition_5w1h": {"who": "Delta eBike team"}},
                ] if name == "briefs" else [])
            eq_mock.execute = execute_fn

            return eq_mock

        chain.select = select_fn
        return chain

    sb = MagicMock()
    sb.table = table_router
    return sb


# ===========================================================================
# E2E Scenario Test
# ===========================================================================

class TestEbikeE2EScenario:
    """Full Phase 1 -> Phase 2 -> Phase 3 pipeline for eBike mid-drive motor design."""

    # -----------------------------------------------------------------------
    # Phase 1: Define
    # -----------------------------------------------------------------------

    @patch("app.agents.analyst.call_llm_json")
    def test_step01_extract_brief(self, mock_llm, client):
        """Phase 1, Step 1: Extract structured brief from raw eBike requirements."""
        mock_llm.return_value = _BRIEF_EXTRACT_RESPONSE

        resp = client.post("/api/v1/definitions/extract", json={
            "project_id": PROJECT_ID,
            "raw_text": (
                "Design a high-efficiency mid-drive motor for urban eBike. "
                "Peak efficiency must be at least 95%. "
                "Thermal rise must not exceed 35C above ambient at rated load. "
                "BOM cost target is $12 per unit. "
                "Motor must fit standard bottom bracket shell (68mm). "
                "Battery voltage: 36V nominal."
            ),
        })

        assert resp.status_code == 200
        brief = resp.json()

        # Verify structure
        assert len(brief["constraints"]) == 3
        assert len(brief["kpis"]) == 3
        assert len(brief["assumptions"]) >= 2
        assert len(brief["feasibility_warnings"]) >= 1

        # Verify eBike-specific content
        constraint_descs = [c["description"] for c in brief["constraints"]]
        assert any("95%" in d for d in constraint_descs)
        assert any("35" in d for d in constraint_descs)
        assert any("$12" in d for d in constraint_descs)

        kpi_names = [k["name"] for k in brief["kpis"]]
        assert "Peak Efficiency" in kpi_names
        assert "Thermal Drop" in kpi_names
        assert "BOM Cost" in kpi_names

        # Store for downstream steps
        self.__class__._brief = brief

    @patch("app.agents.analyst.call_llm_json")
    def test_step02_socratic_questions(self, mock_llm, client):
        """Phase 1, Step 2: Generate Socratic questions from extracted brief."""
        mock_llm.return_value = _SOCRATIC_RESPONSE
        brief = getattr(self.__class__, "_brief", json.loads(_BRIEF_EXTRACT_RESPONSE))

        resp = client.post("/api/v1/questions/generate", json={
            "project_id": PROJECT_ID,
            "mission": MISSION,
            "constraints": [c["description"] for c in brief["constraints"]],
            "existing_questions": [],
        })

        assert resp.status_code == 200
        socratic = resp.json()

        assert len(socratic["questions"]) == 4
        categories = {q["category"] for q in socratic["questions"]}
        assert "assumption" in categories
        assert "contradiction" in categories
        assert "clarification" in categories

        # Verify at least one question tagged as contradiction
        contradiction_qs = [q for q in socratic["questions"] if q.get("suggested_tag") == "contradiction"]
        assert len(contradiction_qs) >= 1

        self.__class__._socratic = socratic

    @patch("app.agents.analyst.call_llm_json")
    def test_step03a_identify_contradiction_tc(self, mock_llm, client):
        """Phase 1, Step 3a: Formalize TC contradiction — efficiency vs weight."""
        mock_llm.return_value = _CONTRADICTION_FORMALIZE_TC_RESPONSE

        resp = client.post("/api/v1/contradictions/c-tc-eff-weight/formalize", json={
            "project_id": PROJECT_ID,
            "contradiction_id": "c-tc-eff-weight",
            "natural_description": "Improving motor efficiency requires larger/better magnets which increases weight and cost",
        })

        assert resp.status_code == 200
        tc = resp.json()

        assert tc["type"] == "TC"
        assert tc["improving_param"] == 31
        assert tc["worsening_param"] == 1
        assert tc["confidence"] >= 0.5
        assert "efficiency" in tc["engineering_statement"].lower() or "weight" in tc["engineering_statement"].lower()

        self.__class__._tc_contradiction = tc

    @patch("app.agents.analyst.call_llm_json")
    def test_step03b_identify_contradiction_pc(self, mock_llm, client):
        """Phase 1, Step 3b (ADR-007): LLM-emitted PC now coerced to type=null + rationale.

        Explore stage is TC-only; when LLM cannot map to 39 params (or returns a legacy
        PC/SF classification), formalize_contradiction returns type=null with rationale
        so UI can drive Socratic refinement. PC/SF derivation moves to Create stage.
        """
        mock_llm.return_value = _CONTRADICTION_FORMALIZE_PC_RESPONSE

        resp = client.post("/api/v1/contradictions/c-pc-thermal-cost/formalize", json={
            "project_id": PROJECT_ID,
            "contradiction_id": "c-pc-thermal-cost",
            "natural_description": "Motor housing must have high thermal conductivity to dissipate heat but low thermal conductivity to protect electronics",
        })

        assert resp.status_code == 200
        payload = resp.json()

        assert payload["type"] is None, "ADR-007: non-TC LLM output must be coerced to null"
        assert payload.get("rationale"), "ADR-007: rationale must explain why mapping failed"
        assert payload.get("physical_contradiction") in (None, ""), \
            "ADR-007: PC field no longer emitted from Explore"

        self.__class__._pc_contradiction = payload

    # -----------------------------------------------------------------------
    # Phase 2: Diverge
    # -----------------------------------------------------------------------

    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[35, 28, 1])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<triz_tc_context>")
    def test_step05_triz_solve_tc(self, mock_tc_ctx, mock_matrix, mock_llm, client):
        """Phase 2, Step 5: TRIZ TC solve for efficiency vs weight."""
        mock_llm.return_value = _TRIZ_TC_RESPONSE
        tc = getattr(self.__class__, "_tc_contradiction", json.loads(_CONTRADICTION_FORMALIZE_TC_RESPONSE))

        resp = client.post("/api/v1/triz/solve", json={
            "project_id": PROJECT_ID,
            "contradiction_id": "c-tc-eff-weight",
            "natural_description": "Improving motor efficiency worsens weight",
            "improving_param": tc["improving_param"],
            "worsening_param": tc["worsening_param"],
            "type": "TC",
        })

        assert resp.status_code == 200
        triz = resp.json()

        assert triz["candidate_principles"] == [35, 28, 1]
        assert len(triz["suggestions"]) >= 1
        assert triz["suggestions"][0]["path"] == "TC"
        assert len(triz["suggestions"][0]["affected_modules"]) >= 1

        # Verify secondary contradictions are flagged
        all_secondary = []
        for s in triz["suggestions"]:
            all_secondary.extend(s.get("secondary_contradictions", []))
        assert len(all_secondary) >= 1

        self.__class__._triz_result = triz

    @patch("app.agents.triz_solver.call_llm_json")
    def test_step06_scamper(self, mock_llm, client):
        """Phase 2, Step 6: SCAMPER 7-action variations on stator subsystem."""
        mock_llm.return_value = _SCAMPER_RESPONSE
        triz = getattr(self.__class__, "_triz_result", json.loads(_TRIZ_TC_RESPONSE))
        affected_module = triz.get("suggestions", json.loads(_TRIZ_TC_RESPONSE)["suggestions"])[0]["affected_modules"][0]

        resp = client.post("/api/v1/scamper/perform", json={
            "project_id": PROJECT_ID,
            "subsystem_name": affected_module,
            "subsystem_description": "Mid-drive motor stator assembly with concentrated windings and ferrite magnets",
            "related_contradictions": [
                "Efficiency vs weight",
                "Power density vs thermal management",
            ],
        })

        assert resp.status_code == 200
        scamper = resp.json()

        assert len(scamper["variants"]) == 7
        actions = {v["action"] for v in scamper["variants"]}
        expected_actions = {"Substitute", "Combine", "Adapt", "Modify", "Put to other use", "Eliminate", "Reverse"}
        assert actions == expected_actions

        # Collect new contradictions for feedback step
        new_contradictions_from_scamper = []
        for v in scamper["variants"]:
            for nc in v.get("new_contradictions", []):
                new_contradictions_from_scamper.append(nc)
        assert len(new_contradictions_from_scamper) >= 3

        self.__class__._scamper = scamper

    def test_step07_scamper_feedback_contradictions(self, client):
        """Phase 2, Step 7: Feed SCAMPER-generated contradictions back."""
        scamper = getattr(self.__class__, "_scamper", json.loads(_SCAMPER_RESPONSE))
        new_contradictions = []
        for v in scamper["variants"]:
            for nc in v.get("new_contradictions", []):
                new_contradictions.append({
                    "description": nc,
                    "severity": "major",
                })

        sb_mock = _mock_scamper_feedback_supabase(existing_rows=_SCAMPER_FEEDBACK_EXISTING)

        with patch("app.agents.scamper_feedback.get_supabase", return_value=sb_mock):
            resp = client.post("/api/v1/scamper/feedback-contradictions", json={
                "project_id": PROJECT_ID,
                "new_contradictions": new_contradictions,
            })

        assert resp.status_code == 200
        feedback = resp.json()

        assert isinstance(feedback["created_count"], int)
        assert isinstance(feedback["deduplicated_count"], int)
        # At least some should be created (not all deduplicated)
        assert feedback["created_count"] + feedback["deduplicated_count"] == len(new_contradictions)
        assert feedback["created_count"] >= 1
        # The ferrite one should be deduplicated against existing
        assert feedback["deduplicated_count"] >= 1

        self.__class__._feedback = feedback

    @patch("app.agents.evaluator.call_llm_json")
    def test_step08_must_evaluate(self, mock_llm, client):
        """Phase 2, Step 8: MUST screening of the proposed alternative."""
        mock_llm.return_value = _MUST_EVAL_RESPONSE
        brief = getattr(self.__class__, "_brief", json.loads(_BRIEF_EXTRACT_RESPONSE))

        resp = client.post("/api/v1/must/evaluate", json={
            "project_id": PROJECT_ID,
            "alternative_name": "Axial-Flux Ferrite Mid-Drive",
            "mechanism": "Axial-flux topology with ferrite Halbach array, flat ribbon concentrated winding, integrated aluminum housing heatsink, sensorless FOC",
            "must_criteria": [
                {
                    "id": "M1",
                    "label": "Peak efficiency >= 95%",
                    "source": "C1",
                    "threshold": "95%",
                },
                {
                    "id": "M2",
                    "label": "Thermal rise <= 35C",
                    "source": "C2",
                    "threshold": "35 degC",
                },
                {
                    "id": "M3",
                    "label": "BOM cost <= $12",
                    "source": "C3",
                    "threshold": "$12",
                },
            ],
            "constraints": [c["description"] for c in brief["constraints"]],
            "kpis": [f"{k['name']} >= {k['target_value']} {k['unit']}" for k in brief["kpis"]],
        })

        assert resp.status_code == 200
        must = resp.json()

        assert must["overall_pass"] is True
        assert len(must["criteria_results"]) == 3
        for cr in must["criteria_results"]:
            assert cr["passed"] is True
            assert 0 <= cr["confidence"] <= 1
            assert cr["reasoning"]

        # Verify cost criterion has lowest confidence (realistic concern)
        cost_cr = next(cr for cr in must["criteria_results"] if cr["id"] == "M3")
        eff_cr = next(cr for cr in must["criteria_results"] if cr["id"] == "M1")
        assert cost_cr["confidence"] < eff_cr["confidence"]

        self.__class__._must = must

    @patch("app.agents.evaluator.call_llm_json")
    def test_step09_pre_cad_review(self, mock_llm, client):
        """Phase 2, Step 9: Pre-CAD review with AI 5D scoring."""
        mock_llm.return_value = _PRE_CAD_RESPONSE
        brief = getattr(self.__class__, "_brief", json.loads(_BRIEF_EXTRACT_RESPONSE))

        resp = client.post("/api/v1/pre-cad-reviews/review-001/ai-analyze", json={
            "project_id": PROJECT_ID,
            "alternative_name": "Axial-Flux Ferrite Mid-Drive",
            "mechanism": "Axial-flux topology with ferrite Halbach array, flat ribbon concentrated winding, integrated aluminum housing heatsink",
            "constraints": [c["description"] for c in brief["constraints"]],
        })

        assert resp.status_code == 200
        precad = resp.json()

        # All 5D scores present and in valid range
        for dim in ["spatial_score", "cost_score", "safety_score", "decoupling_score", "supply_score"]:
            assert dim in precad
            assert 1 <= precad[dim] <= 5

        assert precad["overall_pass"] is True
        assert precad["analysis"]
        assert "thermal" in precad["analysis"].lower() or "cost" in precad["analysis"].lower()

        self.__class__._precad = precad

    # -----------------------------------------------------------------------
    # Phase 3: Converge
    # -----------------------------------------------------------------------

    @patch("app.agents.evaluator.call_llm_json")
    def test_step10_risk_register(self, mock_llm, client):
        """Phase 3, Step 10: Register risks for the selected alternative."""
        mock_llm.return_value = _RISK_ANALYSIS_RESPONSE

        resp = client.post("/api/v1/risks/analyze", json={
            "project_id": PROJECT_ID,
            "alternative_name": "Axial-Flux Ferrite Mid-Drive",
            "mechanism": "Axial-flux topology with ferrite Halbach array, flat ribbon concentrated winding, sensorless FOC",
            "assumptions": [
                "Ambient temperature range is 0-40C",
                "Battery voltage is 36V nominal (42V max)",
                "Flat ribbon winding can achieve >60% copper fill factor",
            ],
        })

        assert resp.status_code == 200
        risk = resp.json()

        assert len(risk["risks"]) == 3
        for r in risk["risks"]:
            assert 1 <= r["probability"] <= 5
            assert 1 <= r["severity"] <= 5
            assert r["mitigation"]
            assert r["failure_mode"]

        # Highest risk severity should be the demagnetization risk
        max_severity_risk = max(risk["risks"], key=lambda r: r["severity"])
        assert max_severity_risk["severity"] == 5
        assert "demag" in max_severity_risk["failure_mode"].lower() or "flux" in max_severity_risk["failure_mode"].lower()

        self.__class__._risks = risk

    @patch("app.agents.evaluator.call_llm_json")
    def test_step11_convergence_scan(self, mock_llm, client):
        """Phase 3, Step 11: Convergence scan for secondary contradictions."""
        mock_llm.return_value = _CONVERGENCE_SCAN_RESPONSE

        resp = client.post("/api/v1/convergence/scan", json={
            "project_id": PROJECT_ID,
            "alternatives": [
                {
                    "id": "alt-001",
                    "name": "Axial-Flux Ferrite Mid-Drive",
                    "mechanism": "Axial-flux with ferrite Halbach, ribbon winding, integrated housing",
                    "source": "triz_tc",
                    "resolves_contradiction_ids": ["ctr-001"],
                },
            ],
            "contradictions": [
                {
                    "id": "ctr-001",
                    "natural_description": "Efficiency vs weight (TC)",
                    "type": "TC",
                    "severity": "major",
                    "resolved": True,
                    "improving_param": 14,
                    "worsening_param": 1,
                    "engineering_statement": "Improving efficiency worsens weight",
                },
                {
                    "id": "ctr-002",
                    "natural_description": "Housing thermal conductivity vs insulation (PC)",
                    "type": "PC",
                    "severity": "major",
                    "resolved": False,
                    "physical_contradiction": "Housing must be thermally conductive for cooling yet electrically insulating for safety",
                },
            ],
        })

        assert resp.status_code == 200
        conv = resp.json()

        assert isinstance(conv["convergence_score"], (int, float))
        assert 0 <= conv["convergence_score"] <= 100
        assert conv["architecture_health"] in ("healthy", "warning", "critical")
        assert isinstance(conv["force_pause"], bool)

        # There should be at least one new secondary contradiction found
        assert len(conv["new_contradictions"]) >= 1
        for nc in conv["new_contradictions"]:
            assert nc["severity"] in ("fatal", "major", "minor")
            assert nc["source_alternative"]

        self.__class__._convergence = conv

    @patch("app.routers.gates.get_supabase")
    def test_step12a_gate_1_1_check(self, mock_sb, client):
        """Phase 3, Gate D1 check — mission + KPIs."""
        briefs_chain = _make_chain(_sb_response(data={"mission": MISSION}))
        kpis_chain = _make_chain(_sb_response(data=[
            {"id": "kpi-1", "measurement_method": "dynamometer at rated torque"},
            {"id": "kpi-2", "measurement_method": "thermocouple on stator winding"},
            {"id": "kpi-3", "measurement_method": "supplier quotation aggregation"},
        ]))
        sb = _build_sb_mock({"briefs": briefs_chain, "kpis": kpis_chain})
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D1/check", params={"project_id": PROJECT_ID})

        assert resp.status_code == 200
        gate = resp.json()

        assert gate["gate_id"] == "D1"
        assert gate["passed"] is True
        assert len(gate["failed_reasons"]) == 0
        assert len(gate["checklist_items"]) == 3
        assert all(item["met"] for item in gate["checklist_items"])

    @patch("app.routers.gates.get_supabase")
    def test_step12b_gate_1_2_check(self, mock_sb, client):
        """Phase 3, Gate D2 check — assumptions + contradictions."""
        assumptions_data = [
            {"id": f"a{i}", "worst_severity": "critical" if i < 4 else "high" if i < 7 else "medium"}
            for i in range(12)
        ]
        assumptions_chain = _make_chain(_sb_response(data=assumptions_data))
        contradictions_chain = _make_chain(_sb_response(data=[], count=5))
        sb = _build_sb_mock({
            "assumptions": assumptions_chain,
            "contradictions": contradictions_chain,
        })
        mock_sb.return_value = sb

        resp = client.get("/api/v1/gates/D2/check", params={"project_id": PROJECT_ID})

        assert resp.status_code == 200
        gate = resp.json()

        assert gate["gate_id"] == "D2"
        assert gate["passed"] is True
        assert len(gate["failed_reasons"]) == 0
        assert len(gate["checklist_items"]) == 3

    @patch("app.agents.knowledge_wb.call_llm_json")
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_step13_knowledge_writeback(self, mock_get_sb, mock_llm, client):
        """Phase 3, Step 13: Knowledge writeback — assetize design artifacts."""
        mock_llm.return_value = _KNOWLEDGE_SYNTHESIS_RESPONSE

        table_data = {
            "alternatives": [
                {"id": "alt-1", "project_id": PROJECT_ID, "name": "Axial-Flux Ferrite Mid-Drive",
                 "mechanism": "Axial-flux with ferrite Halbach", "selected": True},
            ],
            "triz_solutions": [
                {"id": "triz-1", "project_id": PROJECT_ID, "principle_name": "Parameter changes",
                 "suggestion": "Flat ribbon winding"},
            ],
            "risks": [
                {"id": "risk-1", "project_id": PROJECT_ID, "description": "Winding yield",
                 "severity": 4, "mitigation": "Automated winding machine"},
            ],
            "experiments": [
                {"id": "exp-1", "project_id": PROJECT_ID, "name": "Ribbon winding test",
                 "result": "Passed", "evidence_level": "E3"},
            ],
            "adverse_consequences": [
                {"id": "ac-1", "project_id": PROJECT_ID, "description": "Demagnetization at high temp"},
            ],
            "contradictions": [
                {"id": "con-1", "project_id": PROJECT_ID, "description": "Efficiency vs weight",
                 "resolved": True, "triz_principles": "Parameter changes"},
            ],
            "must_criteria": [
                {"id": "m-1", "project_id": PROJECT_ID, "label": "Efficiency >= 95%",
                 "threshold": "95%", "passed": True},
            ],
            "knowledge_entries": [],
        }
        sb = _make_knowledge_supabase(table_data)
        mock_get_sb.return_value = sb

        resp = client.post("/api/v1/knowledge/writeback", json={
            "project_id": PROJECT_ID,
            "asset_types": ["design_pattern", "lesson_learned"],
        })

        assert resp.status_code == 200
        kb = resp.json()

        assert kb["written_count"] == 2
        assert len(kb["assets"]) == 2

        asset_types = {a["asset_type"] for a in kb["assets"]}
        assert "design_pattern" in asset_types
        assert "lesson_learned" in asset_types

        for asset in kb["assets"]:
            assert asset["title"]
            assert asset["id"]

    @patch("app.routers.exports.get_supabase")
    def test_step14_export_project(self, mock_sb, client):
        """Phase 3, Step 14: Export project artifacts to Markdown."""
        sb = _make_export_supabase()
        mock_sb.return_value = sb

        resp = client.post("/api/v1/export", json={
            "project_id": PROJECT_ID,
            "format": "markdown",
            "sections": ["brief", "constraints", "kpis"],
        })

        assert resp.status_code == 200
        export = resp.json()

        assert export["format"] == "markdown"
        assert export["filename"].endswith(".md")
        assert "eBike-MidDrive-v1" in export["filename"]
        assert export["content"]
        assert "Design Report" in export["content"]

    # -----------------------------------------------------------------------
    # Full pipeline chaining verification
    # -----------------------------------------------------------------------

    @patch("app.agents.evaluator.call_llm_json")
    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.lookup_matrix", return_value=[35, 28, 1])
    @patch("app.agents.triz_solver.build_triz_tc_context", return_value="<ctx>")
    @patch("app.agents.analyst.call_llm_json")
    def test_full_pipeline_data_flows(self, mock_analyst_llm, mock_tc_ctx, mock_matrix,
                                      mock_triz_llm, mock_eval_llm, client):
        """Verify end-to-end data flow: brief -> socratic -> TRIZ -> SCAMPER -> MUST.

        Each step uses output from the previous step as input.
        """
        # Step 1: Extract brief
        mock_analyst_llm.return_value = _BRIEF_EXTRACT_RESPONSE
        r1 = client.post("/api/v1/definitions/extract", json={
            "project_id": PROJECT_ID,
            "raw_text": "Design a high-efficiency mid-drive motor for urban eBike.",
        })
        assert r1.status_code == 200
        brief = r1.json()

        # Step 2: Socratic questions — uses constraints from brief
        mock_analyst_llm.return_value = _SOCRATIC_RESPONSE
        r2 = client.post("/api/v1/questions/generate", json={
            "project_id": PROJECT_ID,
            "mission": MISSION,
            "constraints": [c["description"] for c in brief["constraints"]],
            "existing_questions": [],
        })
        assert r2.status_code == 200
        socratic = r2.json()
        assert len(socratic["questions"]) >= 1

        # Step 3: TRIZ solve — uses formalized contradiction params
        mock_triz_llm.return_value = _TRIZ_TC_RESPONSE
        r3 = client.post("/api/v1/triz/solve", json={
            "project_id": PROJECT_ID,
            "contradiction_id": "c-tc-001",
            "natural_description": "Efficiency vs weight",
            "improving_param": 31,
            "worsening_param": 1,
            "type": "TC",
        })
        assert r3.status_code == 200
        triz = r3.json()

        # Step 4: SCAMPER — uses affected_modules from TRIZ
        mock_triz_llm.return_value = _SCAMPER_RESPONSE
        affected = triz["suggestions"][0]["affected_modules"][0]
        secondary = triz["suggestions"][0].get("secondary_contradictions", [])
        r4 = client.post("/api/v1/scamper/perform", json={
            "project_id": PROJECT_ID,
            "subsystem_name": affected,
            "subsystem_description": f"{affected} assembly for mid-drive motor",
            "related_contradictions": secondary,
        })
        assert r4.status_code == 200
        scamper = r4.json()
        assert len(scamper["variants"]) >= 1

        # Step 5: MUST evaluate — uses constraints/KPIs from brief
        mock_eval_llm.return_value = _MUST_EVAL_RESPONSE
        r5 = client.post("/api/v1/must/evaluate", json={
            "project_id": PROJECT_ID,
            "alternative_name": "Axial-Flux Ferrite Mid-Drive",
            "mechanism": "Based on TRIZ + SCAMPER outputs",
            "must_criteria": [
                {"id": "M1", "label": brief["constraints"][0]["description"],
                 "source": "C1", "threshold": brief["kpis"][0]["target_value"] + brief["kpis"][0]["unit"]},
            ],
            "constraints": [c["description"] for c in brief["constraints"]],
            "kpis": [f"{k['name']} {k['target_value']}{k['unit']}" for k in brief["kpis"]],
        })
        assert r5.status_code == 200
        must = r5.json()
        assert must["overall_pass"] is True
