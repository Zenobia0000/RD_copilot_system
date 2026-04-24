"""Tests for Pre-CAD spatial_trace (WBS 10.2).

The spatial_score field of a PreCadAnalyzeResponse must be deterministic
(validator-sourced) whenever the caller supplies a subsystem tree, regardless
of whether the validator finds spatial data or crashes. The spatial_trace
field carries the raw numbers that back the score so the FE can render a
hover-card explanation.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from app.agents.evaluator import analyze_pre_cad
from app.models.schemas import (
    BBox,
    InterfaceContract,
    PreCadAnalyzeRequest,
    SpatialEstimate,
    SuggestedSubsystem,
)


def _module(name: str, target: str, **spatial_kwargs) -> SuggestedSubsystem:
    bbox_kwargs = {
        k: v
        for k, v in spatial_kwargs.items()
        if k in {"x_mm", "y_mm", "z_mm", "origin_mm", "anchor"}
    }
    rest = {k: v for k, v in spatial_kwargs.items() if k not in bbox_kwargs}
    return SuggestedSubsystem(
        name=name,
        level="module",
        interface_contracts={
            target: InterfaceContract(
                spatial=SpatialEstimate(bbox=BBox(**bbox_kwargs), **rest)
            )
        },
    )


def _fake_llm(spatial_score: int = 5) -> str:
    return json.dumps({
        "spatial_score": spatial_score,
        "cost_score": 4,
        "safety_score": 4,
        "decoupling_score": 4,
        "supply_score": 4,
        "overall_pass": True,
        "analysis": "LLM narrative",
    })


# ---------------------------------------------------------------------------
# spatial_trace populated when subsystems provided
# ---------------------------------------------------------------------------


def test_spatial_trace_populated_from_validator_when_subsystems_provided():
    a = _module("Motor", "Gearbox", x_mm=180, y_mm=140, z_mm=120, mass_g=3900)
    b = _module("Battery", "Frame", x_mm=380, y_mm=75, z_mm=65, mass_g=3100)

    req = PreCadAnalyzeRequest(
        project_id="p1",
        alternative_name="alt",
        mechanism="...",
        constraints=[],
        subsystems=[a, b],
    )

    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm()):
        resp = analyze_pre_cad(req)

    trace = resp.spatial_trace
    assert trace is not None
    assert trace.source == "validator"
    assert trace.module_count == 2
    # Required envelope arithmetic: x serial (180+380), y/z axis max
    assert trace.total_bbox_mm == (560.0, 140.0, 120.0)
    assert trace.total_mass_g == 7000.0
    assert trace.clash_pairs == []  # no origins → no clashes
    assert trace.notes  # validator emits heaviest-module note, etc.


# ---------------------------------------------------------------------------
# spatial_trace source="empty" when no subsystems
# ---------------------------------------------------------------------------


def test_spatial_trace_empty_when_no_subsystems():
    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
    )
    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm(spatial_score=4)):
        resp = analyze_pre_cad(req)

    # No subsystems → legacy LLM score is preserved, but trace is attached
    # with source="empty" so FE can render a neutral "(no spatial trace)".
    assert resp.spatial_score == 4
    assert resp.package_map is None
    trace = resp.spatial_trace
    assert trace is not None
    assert trace.source == "empty"
    assert trace.module_count == 0
    assert trace.clash_pairs == []
    assert trace.total_mass_g == 0.0


# ---------------------------------------------------------------------------
# Empty PackageMap (subsystems without spatial data) → neutral fallback
# ---------------------------------------------------------------------------


def test_spatial_trace_empty_when_subsystems_have_no_spatial_data():
    # Subsystems with no spatial block → discover_package returns empty nodes.
    # Historically the evaluator silently trusted the LLM's guess here; the
    # deterministic contract now forces a neutral 3 + source="empty".
    bare = SuggestedSubsystem(
        name="Power", level="module",
        interface_contracts={"Frame": InterfaceContract()},
    )
    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
        subsystems=[bare],
    )

    # LLM guesses 5 but the validator has no ground truth.
    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm(spatial_score=5)):
        resp = analyze_pre_cad(req)

    assert resp.spatial_score == 3  # neutral fallback, not the LLM's 5
    trace = resp.spatial_trace
    assert trace is not None
    assert trace.source == "empty"
    assert trace.module_count == 0


# ---------------------------------------------------------------------------
# Validator raises → llm_fallback trace + neutral score
# ---------------------------------------------------------------------------


def test_spatial_trace_llm_fallback_when_validator_crashes(monkeypatch):
    a = _module("Motor", "Gearbox", x_mm=180, y_mm=140, z_mm=120, mass_g=3900)

    def _boom(_subsystems):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.spatial_validator.discover_package", _boom)

    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
        subsystems=[a],
    )
    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm(spatial_score=5)):
        resp = analyze_pre_cad(req)

    assert resp.spatial_score == 3  # neutral, LLM's 5 is not trusted
    trace = resp.spatial_trace
    assert trace is not None
    assert trace.source == "llm_fallback"
    assert trace.clash_pairs == []
    assert trace.module_count == 0


# ---------------------------------------------------------------------------
# spatial_score matches validator (not LLM) when subsystems carry spatial data
# ---------------------------------------------------------------------------


def test_spatial_score_matches_validator_not_llm():
    # Validator will score this 1 (clash + envelope overflow + heavy mass):
    a = _module("A", "B", x_mm=400, y_mm=100, z_mm=100, mass_g=4000,
                origin_mm=(0.0, 0.0, 0.0))
    b = _module("C", "D", x_mm=400, y_mm=100, z_mm=100, mass_g=4000,
                origin_mm=(10.0, 0.0, 0.0))
    c = _module("E", "F", x_mm=50, y_mm=50, z_mm=50, mass_g=4500,
                origin_mm=(20.0, 0.0, 0.0))

    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
        subsystems=[a, b, c],
    )
    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm(spatial_score=5)):
        resp = analyze_pre_cad(req)

    assert resp.spatial_score == 1  # validator's answer, not the LLM's 5
    assert resp.spatial_trace is not None
    assert resp.spatial_trace.source == "validator"


# ---------------------------------------------------------------------------
# clash_pairs are deduplicated (A↔B not twice)
# ---------------------------------------------------------------------------


def test_clash_pairs_are_deduplicated():
    # Two modules whose AABBs overlap → PackageMap lists each end of the
    # clash, but the trace must collapse them into a single undirected pair.
    a = _module("Controller", "Battery", x_mm=80, y_mm=60, z_mm=30,
                origin_mm=(50.0, 0.0, 0.0), anchor="downtube")
    b = _module("Sensor", "Wiring", x_mm=40, y_mm=20, z_mm=10,
                origin_mm=(60.0, 10.0, 5.0), anchor="downtube")

    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
        subsystems=[a, b],
    )
    with patch("app.agents.evaluator.call_llm_json", return_value=_fake_llm()):
        resp = analyze_pre_cad(req)

    trace = resp.spatial_trace
    assert trace is not None
    assert len(trace.clash_pairs) == 1
    left, right = trace.clash_pairs[0]
    assert {left, right} == {"Controller → Battery", "Sensor → Wiring"}
