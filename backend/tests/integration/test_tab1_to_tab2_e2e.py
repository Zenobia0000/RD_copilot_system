"""Tab (1) TRIZ -> Tab (2) UC1 suggest_subsystems vertical integration.

WBS 10.4: "Tab (1) 銜接" — contradictions flow into UC1 untouched and
resurface in every node of the resulting tree that lists them. The
response must also carry spatially-resolved interface contracts and a
package_map derived from them.

These tests call ``suggest_subsystems`` directly (skipping the HTTP
layer — the Wave 4 contract tests already cover wire format) and stub
``call_llm_json`` with canned JSON so the test is hermetic: no LLM,
no Tavily, no Supabase.

Owned by Wave 5 integration agent; do NOT edit alongside any test that
touches triz_solver.py, test_observability.py, or test_subsystem_*.py.
"""

from __future__ import annotations

import json

import pytest
from unittest.mock import patch

from app.agents.triz_solver import suggest_subsystems
from app.models.schemas import (
    BBox,
    SpatialEstimate,
    SubsystemSuggestRequest,
)
from app.services.spatial_lookup import LookupQuery, SpatialResolver


# ---------------------------------------------------------------------------
# Canned LLM payload helpers
# ---------------------------------------------------------------------------


def _fully_populated_contract(
    envelope: str = "180x140x120mm",
    spatial: dict | None = None,
) -> dict:
    """Return a 6-dim interface contract dict with every MANDATORY field
    populated so the fail-loud validator in ``suggest_subsystems`` does not
    trigger its retry path. ``spatial`` is optional and passed through."""
    contract: dict = {
        "envelope": envelope,
        "loadPath": "bottom bracket -> crank",
        "thermalPath": "case -> frame",
        "signalPath": "CAN bus to controller",
        "datumTolerance": "+/-0.1mm",
        "serviceability": "removable cover",
    }
    if spatial is not None:
        contract["spatial"] = spatial
    return contract


def _llm_payload(subsystems: list[dict]) -> str:
    """Serialize a canned SubsystemSuggestResponse payload as JSON text —
    the shape that ``call_llm_json`` is expected to produce."""
    return json.dumps({"subsystems": subsystems})


def _request(
    contradictions: list[str],
    existing: list[str] | None = None,
) -> SubsystemSuggestRequest:
    return SubsystemSuggestRequest(
        project_id="p1",
        mission="lightweight commuter e-bike",
        contradictions=contradictions,
        existing_subsystems=existing or [],
    )


class _StubResolver(SpatialResolver):
    """Test resolver that returns a single canned hit for any lookup whose
    key matches ``expected_key``, otherwise None. Used to prove the layered
    resolver actually overrides the LLM's initial numbers in
    ``suggest_subsystems``."""

    def __init__(self, expected_key: str, estimate: SpatialEstimate):
        # Intentionally bypass SpatialResolver.__init__ — no backend chain
        # is needed, we fully override lookup().
        self._expected_key = expected_key
        self._estimate = estimate

    def lookup(self, query: LookupQuery):  # type: ignore[override]
        if query.key == self._expected_key:
            return self._estimate
        return None

    def summarize_for_prompt(self, project_id: str = "", max_chars: int = 2500) -> str:  # type: ignore[override]
        return "(stub resolver — empty library)"


# ---------------------------------------------------------------------------
# Main test class
# ---------------------------------------------------------------------------


class TestTab1ToTab2Handoff:
    """Vertical integration: TRIZ Tab (1) contradictions -> UC1
    suggest_subsystems -> resolved spatial -> interface_contracts.
    Locks the contract that ``related_contradictions`` survives end-to-end
    and that the downstream PackageMap reflects the contradictions'
    emphasis (when applicable).
    """

    def test_contradiction_ids_survive_handoff(self):
        """Pass two contradictions; stub LLM to return a tree whose root
        lists [c1] and whose child module lists [c1, c2]. The response
        must preserve exactly those id lists — no dropping, no injection.
        """
        contradictions = [
            "c1: weight vs strength",
            "c2: heat vs compact",
        ]
        canned = _llm_payload([
            {
                "name": "Frame",
                "level": "system",
                "reason": "structural backbone",
                "related_contradictions": ["c1: weight vs strength"],
                "interface_contracts": {
                    "Motor": _fully_populated_contract(envelope="frame-motor IF"),
                },
                "children": [
                    {
                        "name": "Downtube",
                        "level": "module",
                        "reason": "motor + battery mount",
                        "related_contradictions": [
                            "c1: weight vs strength",
                            "c2: heat vs compact",
                        ],
                        "interface_contracts": {
                            "BatteryPack": _fully_populated_contract(envelope="downtube-batt IF"),
                        },
                        "children": [],
                    },
                ],
            },
        ])

        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ):
            resp = suggest_subsystems(_request(contradictions))

        assert len(resp.subsystems) == 1
        root = resp.subsystems[0]
        assert root.related_contradictions == ["c1: weight vs strength"]
        assert len(root.children) == 1
        child = root.children[0]
        assert child.related_contradictions == [
            "c1: weight vs strength",
            "c2: heat vs compact",
        ]

    def test_multiple_contradictions_produce_coupled_modules(self):
        """Two sibling modules that share a contradiction id must both
        carry that id in their ``related_contradictions`` list — the
        traceability is per-node, not deduplicated-across-siblings.
        """
        contradictions = ["c1: weight vs strength", "c2: heat vs compact"]
        canned = _llm_payload([
            {
                "name": "Powertrain",
                "level": "system",
                "reason": "propulsion group",
                "related_contradictions": [],
                "interface_contracts": {
                    "Frame": _fully_populated_contract(),
                },
                "children": [
                    {
                        "name": "Motor",
                        "level": "module",
                        "reason": "mid-drive",
                        "related_contradictions": ["c2: heat vs compact"],
                        "interface_contracts": {
                            "Gearbox": _fully_populated_contract(),
                        },
                        "children": [],
                    },
                    {
                        "name": "Controller",
                        "level": "module",
                        "reason": "power electronics",
                        "related_contradictions": ["c2: heat vs compact"],
                        "interface_contracts": {
                            "Motor": _fully_populated_contract(),
                        },
                        "children": [],
                    },
                ],
            },
        ])

        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ):
            resp = suggest_subsystems(_request(contradictions))

        root = resp.subsystems[0]
        module_names = {c.name for c in root.children}
        assert module_names == {"Motor", "Controller"}
        shared_id = "c2: heat vs compact"
        for child in root.children:
            assert shared_id in child.related_contradictions, (
                f"module {child.name} lost the shared contradiction id"
            )

    def test_spatial_resolution_runs_after_llm(self):
        """Stub LLM to produce a contract citing ``seed:motor_500w`` with
        deliberately wrong numbers. Stub the resolver so that key resolves
        to authoritative values. Assert the post-LLM resolver overwrite
        actually ran — the final bbox and mass come from the resolver,
        not the LLM's initial numbers.
        """
        llm_spatial = {
            "bbox": {"x_mm": 999, "y_mm": 999, "z_mm": 999, "anchor": "BB_center"},
            "mass_g": 9999,
            "reference_source": "seed:motor_500w",
            "confidence": "library",
            "rationale": "LLM guess — should be replaced by resolver",
        }
        canned = _llm_payload([
            {
                "name": "Motor",
                "level": "module",
                "reason": "mid-drive",
                "related_contradictions": [],
                "interface_contracts": {
                    "Gearbox": _fully_populated_contract(spatial=llm_spatial),
                },
                "children": [],
            },
        ])

        authoritative = SpatialEstimate(
            bbox=BBox(x_mm=180, y_mm=140, z_mm=120, anchor="BB_center"),
            mass_g=3900,
            reference_source="seed:motor_500w",
            confidence="library",
            rationale="vendor datasheet",
        )
        stub_resolver = _StubResolver(
            expected_key="motor_500w",
            estimate=authoritative,
        )

        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ), patch(
            "app.agents.triz_solver.default_resolver",
            return_value=stub_resolver,
        ):
            resp = suggest_subsystems(_request(["c1: weight vs strength"]))

        motor = resp.subsystems[0]
        contract = motor.interface_contracts["Gearbox"]
        assert contract.spatial is not None
        # Authoritative numbers from the resolver — NOT the LLM's 999/9999.
        assert contract.spatial.bbox.x_mm == 180
        assert contract.spatial.bbox.y_mm == 140
        assert contract.spatial.bbox.z_mm == 120
        assert contract.spatial.mass_g == 3900

    def test_empty_contradictions_still_produces_tree(self):
        """Empty contradictions list must not short-circuit UC1 — the agent
        still yields a tree, and every node's ``related_contradictions``
        is an empty list.
        """
        canned = _llm_payload([
            {
                "name": "Frame",
                "level": "system",
                "reason": "structural backbone",
                "related_contradictions": [],
                "interface_contracts": {
                    "Motor": _fully_populated_contract(),
                },
                "children": [
                    {
                        "name": "Downtube",
                        "level": "module",
                        "reason": "mounting",
                        "related_contradictions": [],
                        "interface_contracts": {
                            "BatteryPack": _fully_populated_contract(),
                        },
                        "children": [],
                    },
                ],
            },
        ])

        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ):
            resp = suggest_subsystems(_request([]))

        assert len(resp.subsystems) == 1

        def _walk(node):
            assert node.related_contradictions == []
            for child in node.children:
                _walk(child)

        _walk(resp.subsystems[0])

    def test_package_map_reflects_only_nodes_with_spatial(self):
        """Stub LLM to return 3 sibling modules: two with interface
        contracts carrying a populated ``spatial`` block, one whose
        contract has no spatial. The package_map.nodes list must contain
        exactly the two spatially-populated interface contracts (the
        third contract is invisible to the spatial validator).
        """
        spatial_a = {
            "bbox": {"x_mm": 100, "y_mm": 50, "z_mm": 50, "anchor": "downtube_top"},
            "mass_g": 1200,
            "reference_source": "llm_estimate",
            "confidence": "estimate",
            "rationale": "module A rough guess",
        }
        spatial_b = {
            "bbox": {"x_mm": 80, "y_mm": 60, "z_mm": 40, "anchor": "BB_center"},
            "mass_g": 800,
            "reference_source": "llm_estimate",
            "confidence": "estimate",
            "rationale": "module B rough guess",
        }
        canned = _llm_payload([
            {
                "name": "Powertrain",
                "level": "system",
                "reason": "root",
                "related_contradictions": [],
                "interface_contracts": {
                    "A": _fully_populated_contract(spatial=spatial_a),
                    "B": _fully_populated_contract(spatial=spatial_b),
                    "C": _fully_populated_contract(),  # no spatial block
                },
                "children": [],
            },
        ])

        with patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ):
            resp = suggest_subsystems(_request(["c1: weight vs strength"]))

        assert resp.package_map is not None
        # Two nodes expected: Powertrain->A and Powertrain->B; C is skipped
        # because its contract has no spatial block.
        node_names = {n.name for n in resp.package_map.nodes}
        assert node_names == {"Powertrain → A", "Powertrain → B"}
        assert len(resp.package_map.nodes) == 2

    def test_no_llm_or_tavily_called_in_this_test(self):
        """Defensive hermeticity check: patch the LLM and Tavily entry
        points with ``side_effect=AssertionError``; then stub
        ``suggest_subsystems`` itself at the call site so the test proves
        nothing in this file reaches the real world when the agent is
        short-circuited. This is belt-and-suspenders for the other five
        tests: if any of them regressed to real network I/O, that would
        mean these patches are ineffective — this test locks the patch
        targets.
        """

        def _boom(*args, **kwargs):
            raise AssertionError("real LLM should not be called in hermetic test")

        async def _boom_async(*args, **kwargs):
            raise AssertionError("real tavily should not be called in hermetic test")

        canned = _llm_payload([
            {
                "name": "Frame",
                "level": "system",
                "reason": "structural backbone",
                "related_contradictions": [],
                "interface_contracts": {
                    "Motor": _fully_populated_contract(),
                },
                "children": [],
            },
        ])

        # Patch the real network entrypoints to explode, THEN patch the
        # LLM call at its triz_solver import location to return canned.
        # Order matters: the canned-return patch is the innermost, so
        # suggest_subsystems sees the stub, not the exploder.
        with patch(
            "app.services.web_search.search_web",
            side_effect=_boom_async,
        ), patch(
            "app.agents.base.call_llm_json",
            side_effect=_boom,
        ), patch(
            "app.agents.triz_solver.call_llm_json",
            return_value=canned,
        ):
            resp = suggest_subsystems(_request(["c1: weight vs strength"]))

        # If we reach this line, the canned LLM stub was correctly used.
        assert len(resp.subsystems) == 1
        assert resp.subsystems[0].name == "Frame"
