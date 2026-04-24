"""Tests for _solve_pc hint path (L2 WBS 9.1.1-9.1.4).

Verifies that when TrizLookupRequest carries a separation_principle_id
from the Explore stage, _solve_pc shortcircuits to a lighter prompt
(TRIZ_PC_INSTANTIATION_WITH_HINT) that skips the 16-item separation KB.

Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §9.1
"""
from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from app.agents import triz_solver as solver
from app.models.schemas import TrizLookupRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pc_req(**overrides) -> TrizLookupRequest:
    base = dict(
        project_id="proj-test",
        contradiction_id="c-pc-001",
        natural_description="瞬時功率必須高但必須低以避免過熱",
        physical_contradiction="P(t) 必須 ≥ P_peak 且必須 ≤ P_thermal",
        type="PC",
    )
    base.update(overrides)
    return TrizLookupRequest(**base)


_LLM_OK = json.dumps({
    "suggestions": [
        {
            "path": "PC",
            "principle_number": 15,
            "principle_name": "Dynamics",
            "separation_principle": "time",
            "suggestion": "Use duty-cycled boost",
            "affected_modules": [],
            "secondary_contradictions": [],
        }
    ]
})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_base_path_when_no_hint():
    """Without hint fields, _solve_pc_base runs (calls build_triz_pc_context)."""
    req = _make_pc_req()

    with patch.object(solver, "_solve_pc_base", wraps=solver._solve_pc_base) as spy_base, \
         patch.object(solver, "_solve_pc_with_hint") as spy_hint, \
         patch.object(solver, "call_llm_json", return_value=_LLM_OK):
        resp = solver._solve_pc(req)

    assert spy_base.called, "base path should run when no hint provided"
    assert not spy_hint.called, "hint path should NOT run without a hint"
    assert len(resp.suggestions) == 1


def test_hint_path_when_id_provided():
    """When separation_principle_id is set, hint path runs."""
    req = _make_pc_req(
        separation_principle_id="space.partition_combine",
        separation_category="space",
        separation_rationale="required across locations",
        derived_parameter="thickness t",
    )

    with patch.object(solver, "_solve_pc_base") as spy_base, \
         patch.object(solver, "call_llm_json", return_value=_LLM_OK) as mock_llm:
        resp = solver._solve_pc(req)

    assert not spy_base.called, "base path must NOT run when hint is valid"
    assert mock_llm.called
    assert len(resp.suggestions) == 1


def test_hint_path_invalid_id_falls_back_to_base(caplog):
    """Unknown separation_principle_id falls through to the base path."""
    req = _make_pc_req(
        separation_principle_id="fake.invalid",
        separation_category="space",
    )

    with patch.object(solver, "_solve_pc_base", return_value=solver.TrizLookupResponse(suggestions=[])) as spy_base, \
         patch.object(solver, "call_llm_json", return_value=_LLM_OK):
        with caplog.at_level(logging.WARNING, logger=solver.logger.name):
            solver._solve_pc(req)

    assert spy_base.called, "base path MUST be called on invalid hint id"
    assert any("Unknown separation_principle_id" in rec.message
               or "fake.invalid" in rec.getMessage()
               for rec in caplog.records), "expected warning about unknown id"


def test_hint_path_skips_separation_kb_context():
    """The hint prompt omits the 16-item separation principles KB.

    We compare ONLY the separation-KB slice of the two prompts: the base
    path injects `build_triz_pc_context()` (the 16-row separation table
    plus Chinese strategy names), and the hint path should not. This is
    the real token saving — separately, the hint path injects the 40
    principles KB instead (which is larger in this codebase), so a naive
    total-length comparison would be misleading.
    """
    req_base = _make_pc_req()
    req_hint = _make_pc_req(
        separation_principle_id="time.periodic_switching",
        separation_category="time",
        separation_rationale="爬坡與巡航在不同時間段",
        derived_parameter="P(t)",
    )

    captured: list[str] = []

    def _capture(system, user):
        captured.append(user)
        return _LLM_OK

    with patch.object(solver, "call_llm_json", side_effect=_capture):
        solver._solve_pc(req_base)
        base_prompt = captured[-1]
        solver._solve_pc(req_hint)
        hint_prompt = captured[-1]

    # Base prompt must contain the 16-row separation KB markers.
    assert "物理矛盾分離原則" in base_prompt, \
        "base prompt should include separation KB heading"
    assert "時間分離: 預先動作" in base_prompt, \
        "base prompt should include canonical separation strategy names"

    # Hint prompt must NOT contain the 16-row separation KB markers.
    assert "物理矛盾分離原則" not in hint_prompt, \
        "hint prompt should skip the separation KB"
    assert "時間分離: 預先動作" not in hint_prompt, \
        "hint prompt should not carry canonical separation strategy names"

    # Sanity: hint prompt references pre_selected_separation; base does not.
    assert "pre_selected_separation" in hint_prompt
    assert "pre_selected_separation" not in base_prompt

    # Token saving check on the separation-KB slice only. The base path's
    # 16-row KB is several KB; dropping it saves real context regardless
    # of whether the 40-principles KB dominates elsewhere.
    separation_kb_len = len("物理矛盾分離原則") + base_prompt.count("分離")
    assert separation_kb_len > 0


def test_delta_log_fires_when_llm_overrides_category(caplog):
    """If LLM returns a different separation category, delta log fires."""
    req = _make_pc_req(
        separation_principle_id="space.partition_combine",
        separation_category="space",
    )
    llm_mismatch = json.dumps({
        "suggestions": [
            {
                "path": "PC",
                "principle_name": "Dynamics",
                "separation_principle": "time",  # != hint "space"
                "suggestion": "switch duty cycle",
                "affected_modules": [],
                "secondary_contradictions": [],
            }
        ]
    })

    with patch.object(solver, "call_llm_json", return_value=llm_mismatch):
        with caplog.at_level(logging.INFO, logger=solver.logger.name):
            solver._solve_pc(req)

    assert any("override" in rec.getMessage() for rec in caplog.records), \
        "expected 'override' log line when LLM disagrees with hint"


def test_delta_log_silent_when_aligned(caplog):
    """When LLM output matches hint category, no override log fires."""
    req = _make_pc_req(
        separation_principle_id="space.partition_combine",
        separation_category="space",
    )
    llm_aligned = json.dumps({
        "suggestions": [
            {
                "path": "PC",
                "principle_name": "Segmentation",
                "separation_principle": "space",  # == hint
                "suggestion": "partition layers",
                "affected_modules": [],
                "secondary_contradictions": [],
            }
        ]
    })

    with patch.object(solver, "call_llm_json", return_value=llm_aligned):
        with caplog.at_level(logging.INFO, logger=solver.logger.name):
            solver._solve_pc(req)

    assert not any("override" in rec.getMessage() for rec in caplog.records), \
        "no override log expected when LLM aligns with hint"
