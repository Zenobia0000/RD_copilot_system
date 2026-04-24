"""Tests for the Spatial Validator (Discovery mode) and reference library
override in the TRIZ solver agent.

These tests cover the parts of the spatial-grounding feature that RD relies
on as ground truth: arithmetic, library lookup, clash detection, overlay
violation reporting, and the deterministic pre-CAD spatial score.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.agents.evaluator import (
    _format_spatial_evidence,
    _spatial_score_from_validator,
    analyze_pre_cad,
)
from app.agents.triz_solver import _override_with_reference_library, suggest_subsystems
from app.models.schemas import (
    BBox,
    InterfaceContract,
    PreCadAnalyzeRequest,
    SpatialEstimate,
    SubsystemSuggestRequest,
    SuggestedSubsystem,
)
from app.services import reference_library
from app.services.spatial_validator import apply_overlay, discover_package


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# discover_package: arithmetic and notes
# ---------------------------------------------------------------------------


def test_discover_package_sums_extents_and_mass():
    a = _module("Motor", "Gearbox", x_mm=180, y_mm=140, z_mm=120, mass_g=3900)
    b = _module("Battery", "Frame", x_mm=380, y_mm=75, z_mm=65, mass_g=3100)

    pkg = discover_package([a, b])

    # Required envelope: x is the serial sum, y/z are the per-axis maxima.
    assert pkg.required.total_bbox_mm == (560.0, 140.0, 120.0)
    assert pkg.required.total_mass_g == 7000.0
    assert len(pkg.nodes) == 2
    assert all(not n.clashes for n in pkg.nodes)
    assert any("Heaviest" in note for note in pkg.notes)
    # SVG and table fallbacks must be populated
    assert pkg.svg.startswith("<svg")
    assert "Motor → Gearbox" in pkg.table_md


def test_discover_package_empty_when_no_spatial_data():
    bare = SuggestedSubsystem(
        name="Power", level="module",
        interface_contracts={"Frame": InterfaceContract()},
    )
    pkg = discover_package([bare])
    assert pkg.nodes == []
    assert pkg.required.total_bbox_mm == (0.0, 0.0, 0.0)
    assert "empty" in pkg.notes[0].lower()


# ---------------------------------------------------------------------------
# discover_package: clash detection
# ---------------------------------------------------------------------------


def test_discover_package_detects_clash_when_origins_overlap():
    a = _module(
        "Motor", "Gearbox",
        x_mm=200, y_mm=100, z_mm=100,
        origin_mm=(0.0, 0.0, 0.0), anchor="BB",  # origin (0,0,0) → no clash test
    )
    # Bypass: explicitly use a non-zero origin so the clash test fires
    b = _module(
        "Controller", "Battery",
        x_mm=80, y_mm=60, z_mm=30,
        origin_mm=(50.0, 0.0, 0.0), anchor="downtube",
    )
    c = _module(
        "Sensor", "Wiring",
        x_mm=40, y_mm=20, z_mm=10,
        origin_mm=(60.0, 10.0, 5.0), anchor="downtube",
    )
    # b and c overlap; a has no origin so it doesn't participate
    pkg = discover_package([a, b, c])
    clashes_for_b = next(n.clashes for n in pkg.nodes if n.name == "Controller → Battery")
    clashes_for_c = next(n.clashes for n in pkg.nodes if n.name == "Sensor → Wiring")
    assert "Sensor → Wiring" in clashes_for_b
    assert "Controller → Battery" in clashes_for_c
    # Module a (no origin) is unaffected
    a_node = next(n for n in pkg.nodes if n.name == "Motor → Gearbox")
    assert a_node.clashes == []


# ---------------------------------------------------------------------------
# Reference library override
# ---------------------------------------------------------------------------


def test_reference_library_override_replaces_llm_numbers():
    """LLM cites a library key but writes wrong dimensions — the post-processor
    must overwrite with the real vendor data."""
    llm_node = SuggestedSubsystem(
        name="Motor",
        level="module",
        interface_contracts={
            "Gearbox": InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=999, y_mm=999, z_mm=999),  # garbage
                    mass_g=99999,
                    reference_source="ref_lib:bafang_m600_mid_drive",
                    confidence="estimate",
                )
            )
        },
    )
    _override_with_reference_library([llm_node])
    spatial = llm_node.interface_contracts["Gearbox"].spatial
    assert spatial.bbox.x_mm == 180
    assert spatial.bbox.y_mm == 140
    assert spatial.bbox.z_mm == 120
    assert spatial.mass_g == 3900
    assert spatial.confidence == "library"
    assert spatial.rationale  # citation copied from library entry


def test_reference_library_unknown_key_downgrades_confidence():
    llm_node = SuggestedSubsystem(
        name="Mystery",
        level="module",
        interface_contracts={
            "Frame": InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=10, y_mm=10, z_mm=10),
                    reference_source="ref_lib:does_not_exist",
                    confidence="library",
                )
            )
        },
    )
    _override_with_reference_library([llm_node])
    spatial = llm_node.interface_contracts["Frame"].spatial
    assert spatial.confidence == "estimate"
    # Original numbers preserved (not overwritten)
    assert spatial.bbox.x_mm == 10


def test_reference_library_summarize_for_prompt_lists_real_keys():
    summary = reference_library.summarize_for_prompt()
    assert "bafang_m600_mid_drive" in summary
    assert "180x140x120mm" in summary


# ---------------------------------------------------------------------------
# Overlay (what-if) violations
# ---------------------------------------------------------------------------


def test_apply_overlay_flags_zone_overflow_and_mass_excess():
    a = _module("Motor", "Gearbox", x_mm=180, y_mm=140, z_mm=120, mass_g=3900, anchor="downtube")
    b = _module("Battery", "Frame", x_mm=380, y_mm=75, z_mm=65, mass_g=3100, anchor="downtube")
    pkg = discover_package([a, b])

    overlay = {
        "zones": {"downtube": {"x_mm": 400}},
        "mass_budget_g": {"Battery": 2500},
    }
    overlaid = apply_overlay(pkg, overlay)

    # 180 + 380 = 560 > 400
    assert any("downtube" in v and "exceeds" in v for v in overlaid.overlay_violations)
    # Battery mass 3100 > 2500
    assert any("Battery" in v for v in overlaid.overlay_violations)
    # Discovery itself is unmodified
    assert pkg.overlay_violations == []


def test_apply_overlay_passes_when_within_budget():
    a = _module("Motor", "Gearbox", x_mm=180, y_mm=100, z_mm=100, mass_g=2000, anchor="BB")
    pkg = discover_package([a])
    overlaid = apply_overlay(pkg, {"zones": {"BB": {"x_mm": 250}}})
    assert overlaid.overlay_violations == []


# ---------------------------------------------------------------------------
# Pre-CAD deterministic spatial score
# ---------------------------------------------------------------------------


def test_spatial_score_perfect_when_clean():
    a = _module("Motor", "Gearbox", x_mm=150, y_mm=100, z_mm=100, mass_g=2500)
    pkg = discover_package([a])
    assert _spatial_score_from_validator(pkg) == 5


def test_spatial_score_penalizes_heavy_modules():
    # Single 6kg module — exceeds 5kg single-module rule (-1)
    a = _module("Battery", "Pack", x_mm=300, y_mm=80, z_mm=80, mass_g=6000)
    pkg = discover_package([a])
    assert _spatial_score_from_validator(pkg) == 4


def test_spatial_score_penalizes_clashes_and_overflow():
    a = _module("A", "B", x_mm=400, y_mm=100, z_mm=100, mass_g=4000,
                origin_mm=(0.0, 0.0, 0.0))
    # Force clash by giving both nodes overlapping non-zero origins
    b = _module("C", "D", x_mm=400, y_mm=100, z_mm=100, mass_g=4000,
                origin_mm=(10.0, 0.0, 0.0))
    c = _module("E", "F", x_mm=50, y_mm=50, z_mm=50, mass_g=4500,
                origin_mm=(20.0, 0.0, 0.0))
    pkg = discover_package([a, b, c])
    score = _spatial_score_from_validator(pkg)
    # 5 - 2 (clash cap) - 1 (total mass 12.5kg > 12kg) - 1 (envelope x=850 > 700) = 1
    assert score == 1


def test_spatial_score_returns_zero_signal_when_no_evidence():
    pkg = discover_package([])
    assert _spatial_score_from_validator(pkg) == 0
    evidence = _format_spatial_evidence(pkg)
    assert "empty" in evidence.lower()


# ---------------------------------------------------------------------------
# analyze_pre_cad: validator overrides LLM spatial_score
# ---------------------------------------------------------------------------


def test_analyze_pre_cad_overrides_llm_spatial_score_when_subsystems_provided():
    fake_llm_response = json.dumps({
        "spatial_score": 5,           # LLM is wrong; clash exists
        "cost_score": 4,
        "safety_score": 4,
        "decoupling_score": 4,
        "supply_score": 4,
        "overall_pass": True,
        "analysis": "LLM narrative",
    })

    # Build a tree with a clash so the validator scores < 5
    a = _module("A", "B", x_mm=400, y_mm=100, z_mm=100, mass_g=2000,
                origin_mm=(10.0, 0.0, 0.0))
    b = _module("C", "D", x_mm=400, y_mm=100, z_mm=100, mass_g=2000,
                origin_mm=(20.0, 0.0, 0.0))

    req = PreCadAnalyzeRequest(
        project_id="p1",
        alternative_name="alt",
        mechanism="...",
        constraints=[],
        subsystems=[a, b],
    )

    with patch("app.agents.evaluator.call_llm_json", return_value=fake_llm_response):
        resp = analyze_pre_cad(req)

    # Validator detected: clash + envelope_x=800>700 → 5 - 2 - 1 = 2
    assert resp.spatial_score == 2
    assert resp.package_map is not None
    # overall_pass recomputed: spatial=2 → fail
    assert resp.overall_pass is False
    assert resp.analysis == "LLM narrative"


def test_analyze_pre_cad_keeps_llm_score_when_no_subsystems():
    fake_llm_response = json.dumps({
        "spatial_score": 4,
        "cost_score": 4,
        "safety_score": 4,
        "decoupling_score": 4,
        "supply_score": 4,
        "overall_pass": True,
        "analysis": "no subsystems given",
    })
    req = PreCadAnalyzeRequest(
        project_id="p1", alternative_name="alt", mechanism="...", constraints=[],
    )
    with patch("app.agents.evaluator.call_llm_json", return_value=fake_llm_response):
        resp = analyze_pre_cad(req)
    assert resp.spatial_score == 4
    assert resp.package_map is None


# ---------------------------------------------------------------------------
# suggest_subsystems integration: prompt receives reference library
# ---------------------------------------------------------------------------


def test_suggest_subsystems_injects_reference_library_into_prompt():
    """The prompt formatting must include the library summary so the LLM has
    a grounded vocabulary. We capture the rendered prompt by stubbing the LLM."""
    captured = {}

    def fake_llm(system, prompt, **kwargs):
        captured["prompt"] = prompt
        return json.dumps({"subsystems": []})

    req = SubsystemSuggestRequest(
        project_id="p1",
        mission="lightweight commuter e-bike",
        contradictions=["weight vs range"],
        existing_subsystems=[],
    )
    with patch("app.agents.triz_solver.call_llm_json", side_effect=fake_llm):
        resp = suggest_subsystems(req)

    # New layered resolver prefixes seed entries with `seed:` in the prompt
    assert "seed:bafang_m600_mid_drive" in captured["prompt"]
    assert "180x140x120mm" in captured["prompt"]
    # Empty subsystems → package_map is still computed (empty) so FE doesn't crash
    assert resp.package_map is not None
    assert resp.package_map.nodes == []


# ---------------------------------------------------------------------------
# Layered resolver: priority ordering and individual backends
# ---------------------------------------------------------------------------


def test_layered_resolver_first_hit_wins():
    """The resolver should consult backends in order and stop at the first
    non-None result, even if later backends would also have matched."""
    from app.services.spatial_lookup import LookupQuery, SpatialResolver

    class FakeBackend:
        def __init__(self, name, hit):
            self.name = name
            self._hit = hit
            self.calls = 0

        def lookup(self, query):
            self.calls += 1
            return self._hit

        def summarize(self, project_id=""):
            return []

    a_estimate = SpatialEstimate(
        bbox=BBox(x_mm=10, y_mm=10, z_mm=10),
        reference_source="rd_override:battery",
        confidence="rd_confirmed",
    )
    b_estimate = SpatialEstimate(
        bbox=BBox(x_mm=20, y_mm=20, z_mm=20),
        reference_source="learned:battery",
        confidence="library",
    )

    a = FakeBackend("rd_override", a_estimate)
    b = FakeBackend("learned", b_estimate)
    resolver = SpatialResolver(backends=[a, b])

    result = resolver.lookup(LookupQuery(key="battery", project_id="p1"))
    assert result.reference_source == "rd_override:battery"
    assert a.calls == 1
    assert b.calls == 0  # short-circuited — never reached


def test_layered_resolver_falls_through_to_seed():
    from app.services.spatial_lookup import LookupQuery, SeedJsonBackend, SpatialResolver

    class NullBackend:
        name = "null"
        def lookup(self, q): return None
        def summarize(self, project_id=""): return []

    resolver = SpatialResolver(backends=[NullBackend(), NullBackend(), SeedJsonBackend()])
    result = resolver.lookup(LookupQuery(key="bafang_m600_mid_drive"))
    assert result is not None
    assert result.reference_source == "seed:bafang_m600_mid_drive"
    assert result.bbox.x_mm == 180


def test_resolver_returns_none_when_nothing_matches():
    from app.services.spatial_lookup import LookupQuery, SeedJsonBackend, SpatialResolver

    resolver = SpatialResolver(backends=[SeedJsonBackend()])
    assert resolver.lookup(LookupQuery(key="nonexistent_part")) is None


def test_seed_backend_category_fallback():
    """When key is unknown but a category is given, the seed backend should
    return the first entry in that category."""
    from app.services.spatial_lookup import LookupQuery, SeedJsonBackend

    backend = SeedJsonBackend()
    result = backend.lookup(LookupQuery(category="brake"))
    assert result is not None
    assert result.reference_source.startswith("seed:")


# ---------------------------------------------------------------------------
# Web search backend: regex extraction
# ---------------------------------------------------------------------------


def test_extract_dims_handles_common_formats():
    from app.services.spatial_lookup import _extract_dims_from_text

    bbox, mass = _extract_dims_from_text("Dimensions: 180 x 140 x 120 mm. Weight: 3.9 kg.")
    assert bbox == (180.0, 140.0, 120.0)
    assert mass == 3900.0

    bbox, mass = _extract_dims_from_text("Bosch CX 145×145×110mm 2.9kg")
    assert bbox == (145.0, 145.0, 110.0)
    assert mass == 2900.0

    bbox, mass = _extract_dims_from_text("compact unit: 95 mm x 55 mm x 40 mm, 280 g")
    assert bbox == (95.0, 55.0, 40.0)
    assert mass == 280.0


def test_extract_dims_returns_none_when_no_dims():
    from app.services.spatial_lookup import _extract_dims_from_text

    bbox, mass = _extract_dims_from_text("Lorem ipsum no useful data here.")
    assert bbox is None
    assert mass is None


def test_web_backend_constructs_estimate_from_extracted_text():
    """Patch the web search to return a synthetic snippet and verify the
    backend builds a correct SpatialEstimate from it."""
    from app.services.spatial_lookup import LookupQuery, WebSearchBackend
    from app.services.web_search import SearchResponse, SearchResult

    fake_response = SearchResponse(
        query="x",
        provider="tavily",
        results=[
            SearchResult(
                title="Bafang M620 datasheet",
                url="https://example.com/m620.pdf",
                snippet="Bafang Ultra M620 mid drive 200 x 165 x 140 mm 5.5 kg",
                source="example.com",
                relevance_score=0.9,
            )
        ],
    )

    async def fake_search(query, **kwargs):
        return fake_response

    backend = WebSearchBackend()
    with patch("app.services.web_search.search_web", side_effect=fake_search):
        result = backend.lookup(LookupQuery(description="Bafang M620 dimensions"))

    assert result is not None
    assert result.bbox.x_mm == 200
    assert result.bbox.z_mm == 140
    assert result.mass_g == 5500
    assert result.reference_source.startswith("web:https://example.com")


def test_web_backend_returns_none_when_no_dims_in_results():
    from app.services.spatial_lookup import LookupQuery, WebSearchBackend
    from app.services.web_search import SearchResponse, SearchResult

    fake_response = SearchResponse(
        query="x",
        provider="tavily",
        results=[SearchResult(title="x", url="https://x", snippet="no dims here")],
    )

    async def fake_search(query, **kwargs):
        return fake_response

    backend = WebSearchBackend()
    with patch("app.services.web_search.search_web", side_effect=fake_search):
        assert backend.lookup(LookupQuery(description="something")) is None


# ---------------------------------------------------------------------------
# Resolver wired into triz_solver agent: priority demonstration
# ---------------------------------------------------------------------------


def test_agent_resolver_prefers_rd_override_over_seed():
    """End-to-end-ish: stub the resolver with an rd_override hit and verify
    the agent's spatial post-processing replaces the LLM's seed citation
    with the override values."""
    from app.agents.triz_solver import _resolve_spatial_via_layers
    from app.services.spatial_lookup import SpatialResolver

    # LLM proposed a seed entry for the motor
    motor = SuggestedSubsystem(
        name="Motor",
        level="module",
        interface_contracts={
            "Gearbox": InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=180, y_mm=140, z_mm=120),
                    mass_g=3900,
                    reference_source="seed:bafang_m600_mid_drive",
                    confidence="library",
                )
            )
        },
    )

    # Project has an RD override that says "no, our motor is custom 200x150x130 / 4.2kg"
    rd_override_estimate = SpatialEstimate(
        bbox=BBox(x_mm=200, y_mm=150, z_mm=130),
        mass_g=4200,
        reference_source="rd_override:bafang_m600_mid_drive",
        confidence="rd_confirmed",
        rationale="custom-tuned for project P1",
    )

    class StubResolver(SpatialResolver):
        def lookup(self, query):
            return rd_override_estimate

    _resolve_spatial_via_layers([motor], project_id="p1", resolver=StubResolver())
    result = motor.interface_contracts["Gearbox"].spatial
    assert result.bbox.x_mm == 200
    assert result.mass_g == 4200
    assert result.reference_source.startswith("rd_override:")
    assert result.confidence == "rd_confirmed"


def test_agent_keeps_llm_estimate_when_no_layer_resolves():
    """If `reference_source == 'llm_estimate'`, the resolver chain MUST be
    skipped — the LLM number is the documented last-resort fallback."""
    from app.agents.triz_solver import _resolve_spatial_via_layers
    from app.services.spatial_lookup import SpatialResolver

    node = SuggestedSubsystem(
        name="Mystery",
        level="module",
        interface_contracts={
            "Frame": InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=77, y_mm=77, z_mm=77),
                    mass_g=999,
                    reference_source="llm_estimate",
                    confidence="estimate",
                    rationale="best guess",
                )
            )
        },
    )

    class TrackingResolver(SpatialResolver):
        def __init__(self):
            super().__init__(backends=[])
            self.called = False
        def lookup(self, query):
            self.called = True
            return None

    tracker = TrackingResolver()
    _resolve_spatial_via_layers([node], project_id="p1", resolver=tracker)

    spatial = node.interface_contracts["Frame"].spatial
    assert tracker.called is False  # llm_estimate must short-circuit
    assert spatial.bbox.x_mm == 77
    assert spatial.mass_g == 999


def test_agent_downgrades_unknown_layer_citation():
    """When the LLM cites a layer key that no backend recognises, the entry
    is kept but `confidence` is downgraded to 'estimate' so RD knows the
    number is not vendor-grade."""
    from app.agents.triz_solver import _resolve_spatial_via_layers
    from app.services.spatial_lookup import SpatialResolver

    node = SuggestedSubsystem(
        name="Mystery",
        level="module",
        interface_contracts={
            "Frame": InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=10, y_mm=10, z_mm=10),
                    reference_source="learned:does_not_exist",
                    confidence="library",
                )
            )
        },
    )

    class EmptyResolver(SpatialResolver):
        def lookup(self, query):
            return None

    _resolve_spatial_via_layers([node], project_id="p1", resolver=EmptyResolver())
    spatial = node.interface_contracts["Frame"].spatial
    assert spatial.confidence == "estimate"
    assert spatial.bbox.x_mm == 10  # numbers preserved (not overwritten)
