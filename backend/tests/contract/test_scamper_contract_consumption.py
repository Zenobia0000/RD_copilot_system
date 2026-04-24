"""WBS 10.1 — F3 SCAMPER contract consumption tests.

Covers:
- ScamperRequest accepts (and omits) interface_contracts / contracts_hash
  without breaking backward-compat for legacy callers.
- scamper_transform renders the 6-dim contract block into the LLM prompt,
  including neighbour names and spatial summaries when present.
- The fallback line shows up when no contracts were provided.
- The `scamper.contracts_provided` metrics counter fires on every call.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from app.agents.triz_solver import (
    _format_contracts_for_scamper_prompt,
    scamper_transform,
)
from app.models.schemas import (
    BBox,
    InterfaceContract,
    ScamperRequest,
    SpatialEstimate,
)


# ---------------------------------------------------------------------------
# Schema round-trip
# ---------------------------------------------------------------------------

def test_scamper_request_legacy_shape_still_validates():
    """Existing callers that don't send contracts must still work."""
    req = ScamperRequest.model_validate({
        "project_id": "p1",
        "subsystem_name": "Battery Pack",
        "subsystem_description": "48V storage",
        "related_contradictions": ["weight vs capacity"],
    })
    assert req.interface_contracts == {}
    assert req.contracts_hash == ""


def test_scamper_request_accepts_camelcase_contracts():
    """6-dim contracts are wire-format camelCase. Snake_case must not leak in."""
    req = ScamperRequest.model_validate({
        "project_id": "p1",
        "subsystem_name": "BMS",
        "subsystem_description": "battery management",
        "related_contradictions": [],
        "interface_contracts": {
            "Battery Pack": {
                "envelope": "PCB 80x60x10 mm",
                "loadPath": "none",
                "thermalPath": "conductive to case",
                "signalPath": "CAN bus",
                "datumTolerance": "+/- 0.2 mm",
                "serviceability": "bolt-on",
            },
        },
        "contracts_hash": "deadbeef",
    })
    assert req.contracts_hash == "deadbeef"
    assert "Battery Pack" in req.interface_contracts
    contract = req.interface_contracts["Battery Pack"]
    assert isinstance(contract, InterfaceContract)
    assert contract.envelope == "PCB 80x60x10 mm"


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------

def test_format_contracts_empty_fallback_line():
    block = _format_contracts_for_scamper_prompt({})
    assert "<interface_contracts>" in block
    assert "未提供結構化契約" in block
    assert "</interface_contracts>" in block


def test_format_contracts_renders_all_six_dims_per_neighbour():
    contracts = {
        "Motor Controller": InterfaceContract(
            envelope="case 120x80x40",
            loadPath="mount bracket M6x4",
            thermalPath="aluminium heatsink",
            signalPath="CAN + PWM",
            datumTolerance="+/- 0.1 mm",
            serviceability="service door access",
        ),
        "Frame": InterfaceContract(
            envelope="downtube mount",
            loadPath="4x M6 bolts",
            thermalPath="-",
            signalPath="-",
            datumTolerance="+/- 0.5 mm",
            serviceability="3 min removal",
        ),
    }
    block = _format_contracts_for_scamper_prompt(contracts)
    # Both neighbours present
    assert "Motor Controller" in block
    assert "Frame" in block
    # All 6 dim labels present (at least once per neighbour — so twice total)
    for dim in ("envelope", "loadPath", "thermalPath", "signalPath",
                "datumTolerance", "serviceability"):
        assert block.count(dim) >= 2
    # Spot-check a value text
    assert "case 120x80x40" in block
    assert "CAN + PWM" in block


def test_format_contracts_includes_spatial_when_present():
    contracts = {
        "Battery Pack": InterfaceContract(
            envelope="box",
            loadPath="x",
            thermalPath="x",
            signalPath="x",
            datumTolerance="x",
            serviceability="x",
            spatial=SpatialEstimate(
                bbox=BBox(x_mm=200, y_mm=120, z_mm=60),
                mass_g=4500,
            ),
        ),
    }
    block = _format_contracts_for_scamper_prompt(contracts)
    assert "200" in block and "120" in block and "60" in block
    assert "4500" in block
    assert "spatial:" in block


# ---------------------------------------------------------------------------
# scamper_transform end-to-end with stubbed LLM
# ---------------------------------------------------------------------------

_STUB_LLM_JSON = json.dumps({
    "transformations": [
        {
            "action": "substitute",
            "description": "Replace aluminium with carbon",
            "benefit": "lighter",
            "new_contradiction": "cost up",
        },
    ],
})


def test_scamper_transform_injects_contracts_into_prompt(caplog):
    caplog.set_level(logging.INFO, logger="metrics")
    captured = {}

    def fake_call_llm_json(system, prompt):
        captured["prompt"] = prompt
        return _STUB_LLM_JSON

    req = ScamperRequest(
        project_id="pX",
        subsystem_name="Drive Unit",
        subsystem_description="motor + gearbox",
        related_contradictions=["torque vs weight"],
        interface_contracts={
            "Frame": InterfaceContract(
                envelope="downtube bracket",
                loadPath="4xM8",
                thermalPath="air",
                signalPath="-",
                datumTolerance="+/- 0.3 mm",
                serviceability="5 min",
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=140, y_mm=90, z_mm=70),
                    mass_g=3200,
                ),
            ),
            "BMS": InterfaceContract(
                envelope="pcb 80x60",
                loadPath="none",
                thermalPath="conductive",
                signalPath="CAN",
                datumTolerance="+/- 0.2",
                serviceability="bolt on",
            ),
        },
        contracts_hash="abc123",
    )

    with patch("app.agents.triz_solver.call_llm_json", side_effect=fake_call_llm_json):
        resp = scamper_transform(req)

    assert len(resp.variants) == 1
    prompt = captured["prompt"]
    # Neighbours included
    assert "Frame" in prompt
    assert "BMS" in prompt
    # Spatial summary for the one neighbour that has it
    assert "140" in prompt and "3200" in prompt
    # Subsystem + contradiction still present (regression guard)
    assert "Drive Unit" in prompt
    assert "torque vs weight" in prompt
    # Metrics counter emitted
    assert any("scamper.contracts_provided" in rec.getMessage() for rec in caplog.records)


def test_scamper_transform_hash_missing_counter(caplog):
    caplog.set_level(logging.INFO, logger="metrics")

    def fake_call_llm_json(system, prompt):
        return _STUB_LLM_JSON

    req = ScamperRequest(
        project_id="pY",
        subsystem_name="X",
        subsystem_description="d",
        related_contradictions=[],
        interface_contracts={
            "N": InterfaceContract(
                envelope="e", loadPath="l", thermalPath="t",
                signalPath="s", datumTolerance="dt", serviceability="sv",
            ),
        },
        contracts_hash="",
    )
    with patch("app.agents.triz_solver.call_llm_json", side_effect=fake_call_llm_json):
        scamper_transform(req)

    assert any("scamper.hash_missing" in rec.getMessage() for rec in caplog.records)


def test_scamper_transform_empty_contracts_still_works(caplog):
    caplog.set_level(logging.INFO, logger="metrics")
    captured = {}

    def fake_call_llm_json(system, prompt):
        captured["prompt"] = prompt
        return _STUB_LLM_JSON

    req = ScamperRequest(
        project_id="pZ",
        subsystem_name="Widget",
        subsystem_description="thing",
        related_contradictions=["a"],
    )
    with patch("app.agents.triz_solver.call_llm_json", side_effect=fake_call_llm_json):
        resp = scamper_transform(req)

    assert len(resp.variants) == 1
    assert "未提供結構化契約" in captured["prompt"]
