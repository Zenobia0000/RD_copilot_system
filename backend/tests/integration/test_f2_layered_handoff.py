"""F2 subsystem discovery — layered TRIZ hand-off tests (WP 11.2).

Verifies that `suggest_subsystems` correctly merges `layered_triz_solutions[]`
into its prompt contradiction block, prioritising the adopted drill-down
route from each LTS's `differential_analysis.recommended_route`.

Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §8.1.1
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.agents.triz_solver import (
    _serialize_layered_triz_for_f2_prompt,
    suggest_subsystems,
)
from app.models.schemas import (
    LayeredTrizSolution,
    L1Surface,
    L2RootCause,
    L3StructuralCheck,
    DeepenLink,
    DifferentialAnalysis,
    RecommendedRoute,
    SeparationCandidate,
    SuFieldModel,
    TrizSuggestion,
    SubsystemSuggestRequest,
)


def _make_ebike_lts() -> LayeredTrizSolution:
    return LayeredTrizSolution(
        id="LTS-EBIKE-012",
        project_id="ebike-001",
        contradiction_id="C-EBIKE-012",
        contradiction_natural_description="馬達功率密度提升導致溫升",
        severity="major",
        l1_surface=L1Surface(
            improving_param=21, worsening_param=17,
            candidate_principles=[19, 35, 3, 36],
            suggestions=[
                TrizSuggestion(
                    path="TC", principle_number=19, principle_name="Periodic Action",
                    suggestion="脈衝冷卻 PWM 風扇",
                ),
            ],
            status="ran",
        ),
        l2_root_cause=L2RootCause(
            triggered=True, trigger_reason="severity=major",
            deepen_link=DeepenLink(
                from_tc_pair=(21, 17),
                derived_physical_parameter="瞬時功率 P(t)",
                contradiction_statement="P(t) ≥ P_peak ∧ P(t) ≤ P_thermal",
                separation_type_candidates=[
                    SeparationCandidate(type="time", confidence=0.85, rationale=""),
                ],
            ),
            suggestions=[
                TrizSuggestion(
                    path="PC", principle_name="時間分離: 週期性切換",
                    suggestion="雙模態功率管理器",
                ),
            ],
            status="ran",
        ),
        l3_structural_check=L3StructuralCheck(
            su_field_model=SuFieldModel(S1="定子", S2="外殼", F="熱場", state="insufficient"),
            matched_standard_solutions=["2.2.1"],
            suggestions=[
                TrizSuggestion(
                    path="SuField", principle_name="2.2.1 引入 S3 中介物",
                    suggestion="熱管陣列 S3",
                ),
            ],
            supports_l1="為脈衝冷卻提供熱容緩衝",
            supports_l2="延長峰值窗口 +40%",
            standalone_value="獨立改善 15%",
            status="ran",
        ),
        differential_analysis=DifferentialAnalysis(
            recommended_route=RecommendedRoute(
                primary="L2 + L3 組合（突破路線）",
                fallback="L1 單獨",
                adopted_layers=["L2", "L3"],
                rationale="severity=major + 韌體資源充足",
            ),
        ),
    )


class TestSerializeLayeredTrizForF2Prompt:
    def test_empty_solutions_returns_empty_list(self):
        assert _serialize_layered_triz_for_f2_prompt([]) == []

    def test_single_lts_serialisation_contains_adopted_layers(self):
        lines = _serialize_layered_triz_for_f2_prompt([_make_ebike_lts()])
        assert len(lines) == 1
        line = lines[0]
        # Header with lts id and contradiction id
        assert "LTS-EBIKE-012" in line
        assert "C-EBIKE-012" in line
        # Recommended route + rationale surfaced
        assert "L2 + L3 組合" in line
        assert "severity=major" in line
        # L2 adopted → derived param bleeds through
        assert "瞬時功率 P(t)" in line
        # L3 adopted → Su-Field state surfaces
        assert "Su-Field state=insufficient" in line
        assert "熱管陣列" in line
        # L1 NOT in adopted_layers → should NOT leak L1 mechanism
        assert "脈衝冷卻" not in line

    def test_fallback_to_l1_only(self):
        """When adopted_layers only contains L1, only L1 mechanism surfaces."""
        lts = _make_ebike_lts()
        lts.differential_analysis.recommended_route.adopted_layers = ["L1"]
        lines = _serialize_layered_triz_for_f2_prompt([lts])
        assert len(lines) == 1
        assert "L1: Periodic Action" in lines[0]
        assert "瞬時功率" not in lines[0]
        assert "熱管陣列" not in lines[0]


class TestSuggestSubsystemsLayeredHandoff:
    _LLM_OK = json.dumps({
        "subsystems": [
            {
                "name": "Power Subsystem",
                "level": "system",
                "reason": "energy conversion",
                "related_contradictions": ["C-EBIKE-012"],
                "children": [
                    {
                        "name": "Motor Assembly",
                        "level": "module",
                        "reason": "primary converter",
                        "related_contradictions": ["C-EBIKE-012"],
                        "children": [
                            {"name": "Stator", "level": "component", "reason": "winding"},
                        ],
                        "interface_contracts": {
                            "Controller": {
                                "envelope": "Ø65mm shaft coupling flange",
                                "loadPath": "80Nm torque via spline",
                                "thermalPath": "conductive through Al housing",
                                "signalPath": "3x Hall sensor + thermistor",
                                "datumTolerance": "±0.02mm shaft concentricity",
                                "serviceability": "motor removable without gearbox disassembly",
                                "spatial": {
                                    "bbox": {"x_mm": 180, "y_mm": 140, "z_mm": 120},
                                    "mass_g": 3900,
                                    "mounting_pattern": "BB_shell",
                                    "reference_source": "llm_estimate",
                                    "confidence": "estimate",
                                    "rationale": "test",
                                },
                            },
                        },
                    },
                ],
            },
        ],
    })

    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.default_resolver")
    def test_suggest_subsystems_accepts_layered_triz(
        self, mock_resolver, mock_llm,
    ):
        """When layered_triz_solutions is non-empty, the adopted drill-down
        route should be embedded in the prompt contradiction block."""
        mock_resolver.return_value.summarize_for_prompt.return_value = "(empty)"
        mock_llm.return_value = self._LLM_OK

        req = SubsystemSuggestRequest(
            project_id="ebike-001",
            mission="lightweight commuter e-bike",
            layered_triz_solutions=[_make_ebike_lts()],
        )

        resp = suggest_subsystems(req)
        assert len(resp.subsystems) == 1

        # Verify the prompt sent to the LLM carried the LTS metadata
        called_prompt = mock_llm.call_args[0][1]
        assert "LTS-EBIKE-012" in called_prompt
        assert "adopted drill-down: L2 + L3 組合" in called_prompt
        assert "瞬時功率 P(t)" in called_prompt

    @patch("app.agents.triz_solver.call_llm_json")
    @patch("app.agents.triz_solver.default_resolver")
    def test_suggest_subsystems_backward_compatible_with_flat_contradictions(
        self, mock_resolver, mock_llm,
    ):
        """When `layered_triz_solutions` is empty, the legacy `contradictions`
        list is used as-is (no regression)."""
        mock_resolver.return_value.summarize_for_prompt.return_value = "(empty)"
        mock_llm.return_value = self._LLM_OK

        req = SubsystemSuggestRequest(
            project_id="ebike-001",
            mission="lightweight commuter e-bike",
            contradictions=["Motor weight vs power output"],
            layered_triz_solutions=[],
        )
        resp = suggest_subsystems(req)
        assert len(resp.subsystems) == 1

        called_prompt = mock_llm.call_args[0][1]
        assert "Motor weight vs power output" in called_prompt
        # No LTS id leakage in back-compat mode
        assert "LTS-" not in called_prompt
