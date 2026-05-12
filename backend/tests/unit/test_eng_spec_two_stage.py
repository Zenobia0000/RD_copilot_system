"""Tests for the two-stage per-module engineering spec generation pipeline.

Covers:
  - _extract_modules()          — tree walking for module-level nodes
  - _parse_field_plan()         — Stage 2a JSON parsing
  - _field_plan_to_dict()       — round-trip serialisation
  - _parse_and_validate_drafts()— draft parsing with malformed-skip
  - _generate_module_specs()    — two-stage flow + fallback
  - _generate_system_level_specs() — system-level single call
  - eng_spec_step2_generate()   — full orchestrator with parallel execution

Ref: plans/eng-spec-quality-gap.md §9
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.models.schemas import (
    SuggestedSubsystem,
    EngineeringSpecDraft,
    DraftValue,
    EngSpecStep2Request,
    EngSpecStep2Response,
    EngSpecStep2ModuleRequest,
    EngSpecStep2ModuleResponse,
    EngSpecStep2SystemRequest,
    EngSpecStep2SystemResponse,
)
from app.agents.triz_solver import (
    _extract_modules,
    _parse_field_plan,
    _field_plan_to_dict,
    _parse_and_validate_drafts,
    _generate_module_specs,
    _generate_system_level_specs,
    eng_spec_step2_generate,
    eng_spec_step2_generate_module,
    eng_spec_step2_generate_system,
    PlannedField,
    ComponentFieldPlan,
    ModuleFieldPlan,
)


# ---------------------------------------------------------------------------
# Fixtures — reusable tree structures
# ---------------------------------------------------------------------------

def _make_component(name: str) -> SuggestedSubsystem:
    """Create a component-level node."""
    return SuggestedSubsystem(name=name, level="component", reason="test")


def _make_module(name: str, children: list[SuggestedSubsystem] | None = None) -> SuggestedSubsystem:
    """Create a module-level node with optional children."""
    return SuggestedSubsystem(
        name=name,
        level="module",
        reason="test",
        children=children or [],
    )


def _make_system(name: str, children: list[SuggestedSubsystem] | None = None) -> SuggestedSubsystem:
    """Create a system-level node with optional children."""
    return SuggestedSubsystem(
        name=name,
        level="system",
        reason="test",
        children=children or [],
    )


def _build_three_level_tree() -> list[SuggestedSubsystem]:
    """Build a canonical 3-level tree: 1 system → 2 modules → 3 components."""
    return [
        _make_system("Motor System", children=[
            _make_module("Stator Module", children=[
                _make_component("Lamination Stack"),
                _make_component("Winding"),
            ]),
            _make_module("Rotor Module", children=[
                _make_component("Permanent Magnet"),
            ]),
        ]),
    ]


# ---------------------------------------------------------------------------
# LLM response fixtures (JSON strings)
# ---------------------------------------------------------------------------

_FIELD_PLAN_RESPONSE = json.dumps({
    "module_name": "Stator Module",
    "components": [
        {
            "subsystem_code": "CS-STATOR-LAMINATION",
            "component_type_hint": "lamination_stack",
            "fields": [
                {
                    "field_name": "stack_height",
                    "category": "spatial",
                    "why": "Determines magnetic path length",
                    "expected_unit": "mm",
                },
                {
                    "field_name": "material_grade",
                    "category": "material",
                    "why": "Core loss depends on silicon steel grade",
                },
            ],
        },
        {
            "subsystem_code": "CS-STATOR-WINDING",
            "component_type_hint": "winding",
            "fields": [
                {
                    "field_name": "wire_gauge",
                    "category": "electrical",
                    "why": "Current capacity constraint",
                    "expected_unit": "AWG",
                },
            ],
        },
    ],
})

_VALUE_FILLING_RESPONSE = json.dumps({
    "drafts": [
        {
            "subsystem_code": "CS-STATOR-LAMINATION",
            "specs": [
                {
                    "field_name": "stack_height",
                    "category": "spatial",
                    "value": 25.0,
                    "unit": "mm",
                    "source": "llm_estimate",
                    "confidence": "estimate",
                    "needs_verification": True,
                    "rationale": "Typical for 60mm OD stator",
                },
                {
                    "field_name": "material_grade",
                    "category": "material",
                    "value": "35CS300",
                    "unit": None,
                    "source": "datasheet",
                    "confidence": "library",
                    "needs_verification": False,
                    "rationale": "Common automotive grade",
                },
            ],
        },
        {
            "subsystem_code": "CS-STATOR-WINDING",
            "specs": [
                {
                    "field_name": "wire_gauge",
                    "category": "electrical",
                    "value": 18,
                    "unit": "AWG",
                    "source": "llm_estimate",
                    "confidence": "speculative",
                    "needs_verification": True,
                    "rationale": "Rough estimate for 5A max",
                },
            ],
        },
    ],
})

_LEGACY_FALLBACK_RESPONSE = json.dumps({
    "drafts": [
        {
            "subsystem_code": "CS-FALLBACK",
            "specs": [
                {
                    "field_name": "mass",
                    "category": "mechanical",
                    "value": 1.5,
                    "unit": "kg",
                    "source": "llm_estimate",
                    "confidence": "speculative",
                    "needs_verification": True,
                },
            ],
        },
    ],
})

_SYSTEM_LEVEL_RESPONSE = json.dumps({
    "drafts": [
        {
            "subsystem_code": "SYS-MOTOR",
            "specs": [
                {
                    "field_name": "total_mass",
                    "category": "mechanical",
                    "value": 5.0,
                    "unit": "kg",
                    "source": "llm_estimate",
                    "confidence": "estimate",
                    "needs_verification": True,
                },
            ],
        },
    ],
})


# ═══════════════════════════════════════════════════════════════════════════
# Test: _extract_modules
# ═══════════════════════════════════════════════════════════════════════════

class TestExtractModules:
    """Test tree-walking extraction of module-level nodes."""

    def test_extracts_modules_from_three_level_tree(self):
        tree = _build_three_level_tree()
        modules = _extract_modules(tree)
        assert len(modules) == 2
        names = {m.name for m in modules}
        assert names == {"Stator Module", "Rotor Module"}

    def test_module_retains_children(self):
        tree = _build_three_level_tree()
        modules = _extract_modules(tree)
        stator = next(m for m in modules if m.name == "Stator Module")
        assert len(stator.children) == 2
        assert stator.children[0].level == "component"

    def test_no_modules_returns_empty(self):
        """A tree with only system and components (no module layer) returns empty."""
        tree = [
            _make_system("Flat System", children=[
                _make_component("Bare Component"),
            ]),
        ]
        assert _extract_modules(tree) == []

    def test_flat_module_list(self):
        """Top-level modules (no system wrapper) are still found."""
        tree = [
            _make_module("Module A"),
            _make_module("Module B"),
        ]
        modules = _extract_modules(tree)
        assert len(modules) == 2

    def test_empty_tree(self):
        assert _extract_modules([]) == []

    def test_deeply_nested_modules(self):
        """Module nested under another module (unusual but defensively handled)."""
        inner_mod = _make_module("Inner Module")
        outer_mod = _make_module("Outer Module", children=[inner_mod])
        tree = [_make_system("System", children=[outer_mod])]
        modules = _extract_modules(tree)
        # Both modules should be collected
        assert len(modules) == 2
        names = {m.name for m in modules}
        assert names == {"Outer Module", "Inner Module"}


# ═══════════════════════════════════════════════════════════════════════════
# Test: _parse_field_plan
# ═══════════════════════════════════════════════════════════════════════════

class TestParseFieldPlan:
    """Test Stage 2a JSON parsing into ModuleFieldPlan."""

    def test_valid_json_parses_correctly(self):
        plan = _parse_field_plan(_FIELD_PLAN_RESPONSE)
        assert isinstance(plan, ModuleFieldPlan)
        assert plan.module_name == "Stator Module"
        assert len(plan.components) == 2

    def test_component_fields_populated(self):
        plan = _parse_field_plan(_FIELD_PLAN_RESPONSE)
        lamination = plan.components[0]
        assert lamination.subsystem_code == "CS-STATOR-LAMINATION"
        assert lamination.component_type_hint == "lamination_stack"
        assert len(lamination.fields) == 2
        assert lamination.fields[0].field_name == "stack_height"
        assert lamination.fields[0].category == "spatial"
        assert lamination.fields[0].expected_unit == "mm"
        assert lamination.fields[0].why == "Determines magnetic path length"

    def test_missing_optional_expected_unit(self):
        plan = _parse_field_plan(_FIELD_PLAN_RESPONSE)
        material_field = plan.components[0].fields[1]
        assert material_field.expected_unit is None

    def test_defaults_for_missing_keys(self):
        """LLM may omit keys — defaults should be applied."""
        raw = json.dumps({
            "components": [
                {
                    "fields": [{}],
                },
            ],
        })
        plan = _parse_field_plan(raw)
        assert plan.module_name == "unknown"
        assert plan.components[0].subsystem_code == ""
        assert plan.components[0].component_type_hint == "generic"
        field = plan.components[0].fields[0]
        assert field.field_name == "unknown"
        assert field.category == "spatial"
        assert field.why == ""
        assert field.expected_unit is None

    def test_empty_components_list(self):
        raw = json.dumps({"module_name": "Empty Module", "components": []})
        plan = _parse_field_plan(raw)
        assert plan.module_name == "Empty Module"
        assert plan.components == []

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_field_plan("not valid json")


# ═══════════════════════════════════════════════════════════════════════════
# Test: _field_plan_to_dict (round-trip)
# ═══════════════════════════════════════════════════════════════════════════

class TestFieldPlanToDict:
    """Test ModuleFieldPlan → dict serialisation."""

    def test_round_trip(self):
        """Parse JSON → ModuleFieldPlan → dict → compare with original data."""
        plan = _parse_field_plan(_FIELD_PLAN_RESPONSE)
        result = _field_plan_to_dict(plan)
        assert result["module_name"] == "Stator Module"
        assert len(result["components"]) == 2
        # Verify first component fields
        comp0 = result["components"][0]
        assert comp0["subsystem_code"] == "CS-STATOR-LAMINATION"
        assert len(comp0["fields"]) == 2
        assert comp0["fields"][0]["field_name"] == "stack_height"
        assert comp0["fields"][0]["expected_unit"] == "mm"

    def test_empty_plan(self):
        plan = ModuleFieldPlan(module_name="Empty", components=[])
        result = _field_plan_to_dict(plan)
        assert result == {"module_name": "Empty", "components": []}

    def test_serialisable_to_json(self):
        """Result must be JSON-serialisable (no dataclass objects)."""
        plan = _parse_field_plan(_FIELD_PLAN_RESPONSE)
        result = _field_plan_to_dict(plan)
        serialised = json.dumps(result)
        assert isinstance(serialised, str)
        roundtrip = json.loads(serialised)
        assert roundtrip["module_name"] == "Stator Module"


# ═══════════════════════════════════════════════════════════════════════════
# Test: _parse_and_validate_drafts
# ═══════════════════════════════════════════════════════════════════════════

class TestParseAndValidateDrafts:
    """Test draft parsing with validation and malformed-skip."""

    def test_valid_drafts_parsed(self):
        drafts = _parse_and_validate_drafts(_VALUE_FILLING_RESPONSE)
        assert len(drafts) == 2
        assert all(isinstance(d, EngineeringSpecDraft) for d in drafts)

    def test_recompute_stats_called(self):
        """After parsing, overall_confidence and verification_count are computed."""
        drafts = _parse_and_validate_drafts(_VALUE_FILLING_RESPONSE)
        lamination = next(d for d in drafts if d.subsystem_code == "CS-STATOR-LAMINATION")
        # 2 specs: estimate(0.5) + library(0.75) → avg = 0.625
        assert lamination.overall_confidence == pytest.approx(0.625, abs=0.001)
        # 1 needs_verification (stack_height), material_grade has needs_verification=False
        assert lamination.verification_count == 1

    def test_malformed_draft_skipped(self):
        """A draft with invalid data is skipped, but valid ones still pass."""
        raw = json.dumps({
            "drafts": [
                {
                    "subsystem_code": "GOOD",
                    "specs": [{
                        "field_name": "x",
                        "category": "spatial",
                        "value": 1.0,
                        "source": "llm_estimate",
                        "confidence": "estimate",
                        "needs_verification": True,
                    }],
                },
                {
                    # Missing required field 'subsystem_code'
                    "specs": [{
                        "field_name": "y",
                        "category": "INVALID_CATEGORY",  # bad enum
                        "value": 2.0,
                    }],
                },
            ],
        })
        drafts = _parse_and_validate_drafts(raw)
        assert len(drafts) == 1
        assert drafts[0].subsystem_code == "GOOD"

    def test_empty_drafts_key(self):
        raw = json.dumps({"drafts": []})
        assert _parse_and_validate_drafts(raw) == []

    def test_missing_drafts_key(self):
        raw = json.dumps({"something_else": 123})
        assert _parse_and_validate_drafts(raw) == []

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_and_validate_drafts("{bad json")


# ═══════════════════════════════════════════════════════════════════════════
# Test: _generate_module_specs (two-stage + fallback)
# ═══════════════════════════════════════════════════════════════════════════

class TestGenerateModuleSpecs:
    """Test two-stage (2a+2b) generation for a single module."""

    @patch("app.agents.triz_solver.call_llm_json")
    def test_two_stage_happy_path(self, mock_llm):
        """Stage 2a returns field plan, Stage 2b returns drafts."""
        mock_llm.side_effect = [_FIELD_PLAN_RESPONSE, _VALUE_FILLING_RESPONSE]
        module = _make_module("Stator Module", children=[
            _make_component("Lamination Stack"),
            _make_component("Winding"),
        ])
        drafts = _generate_module_specs(
            module=module,
            mission="Design a brushless DC motor",
            library_summary="No library data",
            project_id="test-project",
        )
        assert len(drafts) == 2
        assert mock_llm.call_count == 2
        # First call: Stage 2a (field planning)
        first_call_prompt = mock_llm.call_args_list[0][0][1]
        assert "Stator Module" in first_call_prompt or "stator" in first_call_prompt.lower()

    @patch("app.agents.triz_solver.call_llm_json")
    def test_fallback_on_stage2a_failure(self, mock_llm):
        """When Stage 2a raises, fallback to legacy single-call."""
        mock_llm.side_effect = [
            Exception("LLM timeout"),        # Stage 2a fails
            _LEGACY_FALLBACK_RESPONSE,        # Fallback call
        ]
        module = _make_module("Broken Module", children=[
            _make_component("Part A"),
        ])
        drafts = _generate_module_specs(
            module=module,
            mission="Test fallback",
            library_summary="",
            project_id="test",
        )
        assert len(drafts) == 1
        assert drafts[0].subsystem_code == "CS-FALLBACK"
        # 2 calls: failed 2a + fallback
        assert mock_llm.call_count == 2

    @patch("app.agents.triz_solver.call_llm_json")
    def test_fallback_on_stage2b_failure(self, mock_llm):
        """When Stage 2a succeeds but Stage 2b raises, fallback to legacy."""
        mock_llm.side_effect = [
            _FIELD_PLAN_RESPONSE,             # Stage 2a succeeds
            ValueError("Bad LLM output"),     # Stage 2b fails
            _LEGACY_FALLBACK_RESPONSE,        # Fallback call
        ]
        module = _make_module("Half Broken", children=[
            _make_component("Part B"),
        ])
        drafts = _generate_module_specs(
            module=module,
            mission="Test partial fallback",
            library_summary="",
            project_id="test",
        )
        assert len(drafts) == 1
        assert drafts[0].subsystem_code == "CS-FALLBACK"
        # 3 calls: 2a + failed 2b + fallback
        assert mock_llm.call_count == 3

    @patch("app.agents.triz_solver.call_llm_json")
    def test_draft_recompute_stats_applied(self, mock_llm):
        """Drafts returned have recompute_stats already called."""
        mock_llm.side_effect = [_FIELD_PLAN_RESPONSE, _VALUE_FILLING_RESPONSE]
        module = _make_module("Stats Check", children=[_make_component("C")])
        drafts = _generate_module_specs(
            module=module,
            mission="Test stats",
            library_summary="",
            project_id="test",
        )
        for d in drafts:
            # Stats should have been computed (not default 0.0)
            if d.specs:
                assert d.overall_confidence > 0


# ═══════════════════════════════════════════════════════════════════════════
# Test: _generate_system_level_specs
# ═══════════════════════════════════════════════════════════════════════════

class TestGenerateSystemLevelSpecs:
    """Test system-level spec generation (legacy single call)."""

    @patch("app.agents.triz_solver.call_llm_json", return_value=_SYSTEM_LEVEL_RESPONSE)
    def test_system_level_returns_drafts(self, mock_llm):
        systems = [_make_system("Motor System")]
        drafts = _generate_system_level_specs(
            systems=systems,
            mission="Build a motor",
            library_summary="lib data",
            project_id="proj-1",
        )
        assert len(drafts) == 1
        assert drafts[0].subsystem_code == "SYS-MOTOR"
        assert mock_llm.call_count == 1

    @patch("app.agents.triz_solver.call_llm_json", return_value=_SYSTEM_LEVEL_RESPONSE)
    def test_children_stripped_from_prompt(self, mock_llm):
        """System nodes passed to LLM should have children=[] to keep prompt concise."""
        system_with_children = _make_system("System", children=[
            _make_module("Mod A", children=[_make_component("C1")]),
        ])
        _generate_system_level_specs(
            systems=[system_with_children],
            mission="test",
            library_summary="",
            project_id="p",
        )
        prompt_arg = mock_llm.call_args[0][1]
        # The prompt should contain a tree with empty children
        assert '"children": []' in prompt_arg

    def test_empty_systems_returns_empty(self):
        """No system nodes → empty list, no LLM call."""
        result = _generate_system_level_specs(
            systems=[],
            mission="test",
            library_summary="",
            project_id="p",
        )
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# Test: eng_spec_step2_generate (full orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class TestEngSpecStep2Generate:
    """Test the full Step 2 orchestrator with parallel module processing."""

    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_orchestrator_happy_path(self, mock_resolver, mock_mod_specs, mock_sys_specs):
        """Modules + system nodes both produce drafts that are aggregated."""
        # Setup resolver mock
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = "test library"
        mock_resolver.return_value = resolver_instance

        # Module specs return 2 drafts
        mock_mod_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="C1", specs=[]),
            EngineeringSpecDraft(subsystem_code="C2", specs=[]),
        ]
        # System specs return 1 draft
        mock_sys_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="SYS-1", specs=[]),
        ]

        tree = _build_three_level_tree()
        req = EngSpecStep2Request(
            project_id="test-proj",
            mission="Design a motor",
            subsystems=tree,
        )
        resp = eng_spec_step2_generate(req)

        assert isinstance(resp, EngSpecStep2Response)
        # 2 modules × 2 drafts each + 1 system draft = 5
        # But mock returns same 2 for each module call, so 2 calls × 2 = 4 + 1 = 5
        assert len(resp.drafts) == 5

        # _generate_module_specs should be called once per module
        assert mock_mod_specs.call_count == 2
        # _generate_system_level_specs called once with [system_node]
        mock_sys_specs.assert_called_once()

    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_module_failure_does_not_crash_pipeline(
        self, mock_resolver, mock_mod_specs, mock_sys_specs,
    ):
        """If _generate_module_specs raises for one module, others still contribute."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Module exploded")
            return [EngineeringSpecDraft(subsystem_code="OK", specs=[])]

        mock_mod_specs.side_effect = side_effect
        mock_sys_specs.return_value = []

        tree = _build_three_level_tree()  # 2 modules
        req = EngSpecStep2Request(
            project_id="p",
            mission="m",
            subsystems=tree,
        )
        resp = eng_spec_step2_generate(req)
        # One module failed, one succeeded → 1 draft
        assert len(resp.drafts) == 1

    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_no_modules_still_generates_system_specs(
        self, mock_resolver, mock_mod_specs, mock_sys_specs,
    ):
        """Tree with only system nodes (no modules) still produces system-level specs."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        mock_sys_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="SYS-ONLY", specs=[]),
        ]

        # Tree with a system node that has no module children
        tree = [_make_system("Solo System", children=[_make_component("Direct Child")])]
        req = EngSpecStep2Request(
            project_id="p",
            mission="m",
            subsystems=tree,
        )
        resp = eng_spec_step2_generate(req)
        assert len(resp.drafts) == 1
        assert resp.drafts[0].subsystem_code == "SYS-ONLY"
        # No modules → _generate_module_specs never called
        mock_mod_specs.assert_not_called()

    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_resolver_called_without_web(
        self, mock_resolver, mock_mod_specs, mock_sys_specs,
    ):
        """Resolver should be created with include_web=False for speed."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        mock_mod_specs.return_value = []
        mock_sys_specs.return_value = []

        req = EngSpecStep2Request(
            project_id="p",
            mission="m",
            subsystems=[_make_module("M")],
        )
        eng_spec_step2_generate(req)
        mock_resolver.assert_called_once_with(include_web=False)

    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_empty_tree_returns_empty_response(
        self, mock_resolver, mock_mod_specs, mock_sys_specs,
    ):
        """An empty subsystem tree should return an empty drafts list."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        mock_sys_specs.return_value = []

        req = EngSpecStep2Request(
            project_id="p",
            mission="m",
            subsystems=[],
        )
        resp = eng_spec_step2_generate(req)
        assert resp.drafts == []
        mock_mod_specs.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# Test: eng_spec_step2_generate_module (incremental per-module endpoint)
# ═══════════════════════════════════════════════════════════════════════════

class TestEngSpecStep2GenerateModule:
    """Test the incremental per-module Step 2 endpoint."""

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_happy_path_returns_drafts(self, mock_resolver, mock_mod_specs, mock_emit):
        """Single module call produces drafts and returns correct module_name."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = "test library"
        mock_resolver.return_value = resolver_instance

        mock_mod_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="C1", specs=[]),
            EngineeringSpecDraft(subsystem_code="C2", specs=[]),
        ]

        module = _make_module("Drive Module", children=[_make_component("Motor")])
        tree = _build_three_level_tree()
        req = EngSpecStep2ModuleRequest(
            project_id="proj-1",
            mission="Design a motor",
            subsystems=tree,
            module_name="Drive Module",
            module_node=module,
        )
        resp = eng_spec_step2_generate_module(req)

        assert isinstance(resp, EngSpecStep2ModuleResponse)
        assert resp.module_name == "Drive Module"
        assert len(resp.drafts) == 2
        mock_mod_specs.assert_called_once()

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_resolver_called_without_web(self, mock_resolver, mock_mod_specs, mock_emit):
        """Resolver should be created with include_web=False."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance
        mock_mod_specs.return_value = []

        module = _make_module("M1")
        req = EngSpecStep2ModuleRequest(
            project_id="p",
            mission="m",
            subsystems=[module],
            module_name="M1",
            module_node=module,
        )
        eng_spec_step2_generate_module(req)
        mock_resolver.assert_called_once_with(include_web=False)

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_metric_emitted_with_draft_count(self, mock_resolver, mock_mod_specs, mock_emit):
        """emit_counter should be called with correct module name and draft count."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        mock_mod_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="C1", specs=[]),
        ]

        module = _make_module("Sensor Module")
        req = EngSpecStep2ModuleRequest(
            project_id="proj-2",
            mission="m",
            subsystems=[module],
            module_name="Sensor Module",
            module_node=module,
        )
        eng_spec_step2_generate_module(req)

        mock_emit.assert_called_once_with(
            "eng_spec.step2_module_done",
            value=1,
            project_id="proj-2",
            module="Sensor Module",
            draft_count=1,
        )

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_passes_library_summary_to_generate(self, mock_resolver, mock_mod_specs, mock_emit):
        """The library summary from resolver.summarize_for_prompt() should be forwarded."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = "enriched library context"
        mock_resolver.return_value = resolver_instance
        mock_mod_specs.return_value = []

        module = _make_module("M1", children=[_make_component("C1")])
        tree = [_make_system("S1", children=[module])]
        req = EngSpecStep2ModuleRequest(
            project_id="p",
            mission="Design something",
            subsystems=tree,
            module_name="M1",
            module_node=module,
        )
        eng_spec_step2_generate_module(req)

        call_kwargs = mock_mod_specs.call_args[1]
        assert call_kwargs["library_summary"] == "enriched library context"
        assert call_kwargs["module"] == module
        assert call_kwargs["mission"] == "Design something"
        assert call_kwargs["project_id"] == "p"

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_module_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_module_specs_error_propagates(self, mock_resolver, mock_mod_specs, mock_emit):
        """Unlike the orchestrator, per-module endpoint should let errors propagate."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance
        mock_mod_specs.side_effect = RuntimeError("LLM timeout")

        module = _make_module("Broken")
        req = EngSpecStep2ModuleRequest(
            project_id="p",
            mission="m",
            subsystems=[module],
            module_name="Broken",
            module_node=module,
        )
        with pytest.raises(RuntimeError, match="LLM timeout"):
            eng_spec_step2_generate_module(req)


# ═══════════════════════════════════════════════════════════════════════════
# Test: eng_spec_step2_generate_system (incremental system-level endpoint)
# ═══════════════════════════════════════════════════════════════════════════

class TestEngSpecStep2GenerateSystem:
    """Test the incremental system-level Step 2 endpoint."""

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_happy_path_returns_drafts(self, mock_resolver, mock_sys_specs, mock_emit):
        """System-level call produces drafts correctly."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = "test library"
        mock_resolver.return_value = resolver_instance

        mock_sys_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="SYS-1", specs=[]),
        ]

        tree = _build_three_level_tree()
        req = EngSpecStep2SystemRequest(
            project_id="proj-3",
            mission="Design a motor",
            subsystems=tree,
        )
        resp = eng_spec_step2_generate_system(req)

        assert isinstance(resp, EngSpecStep2SystemResponse)
        assert len(resp.drafts) == 1
        assert resp.drafts[0].subsystem_code == "SYS-1"

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_resolver_called_without_web(self, mock_resolver, mock_sys_specs, mock_emit):
        """Resolver should be created with include_web=False."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance
        mock_sys_specs.return_value = []

        req = EngSpecStep2SystemRequest(
            project_id="p",
            mission="m",
            subsystems=[],
        )
        eng_spec_step2_generate_system(req)
        mock_resolver.assert_called_once_with(include_web=False)

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_metric_emitted_with_draft_count(self, mock_resolver, mock_sys_specs, mock_emit):
        """emit_counter should emit step2_system_done with correct count."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance

        mock_sys_specs.return_value = [
            EngineeringSpecDraft(subsystem_code="SYS-A", specs=[]),
            EngineeringSpecDraft(subsystem_code="SYS-B", specs=[]),
        ]

        req = EngSpecStep2SystemRequest(
            project_id="proj-4",
            mission="m",
            subsystems=_build_three_level_tree(),
        )
        eng_spec_step2_generate_system(req)

        mock_emit.assert_called_once_with(
            "eng_spec.step2_system_done",
            value=1,
            project_id="proj-4",
            draft_count=2,
        )

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_empty_subsystems_returns_empty(self, mock_resolver, mock_sys_specs, mock_emit):
        """An empty subsystems list should still work and return empty drafts."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = ""
        mock_resolver.return_value = resolver_instance
        mock_sys_specs.return_value = []

        req = EngSpecStep2SystemRequest(
            project_id="p",
            mission="m",
            subsystems=[],
        )
        resp = eng_spec_step2_generate_system(req)
        assert resp.drafts == []

    @patch("app.agents.triz_solver.emit_counter")
    @patch("app.agents.triz_solver._generate_system_level_specs")
    @patch("app.agents.triz_solver.default_resolver")
    def test_passes_correct_args_to_generate(self, mock_resolver, mock_sys_specs, mock_emit):
        """Verify all arguments are correctly forwarded to _generate_system_level_specs."""
        resolver_instance = MagicMock()
        resolver_instance.summarize_for_prompt.return_value = "lib context"
        mock_resolver.return_value = resolver_instance
        mock_sys_specs.return_value = []

        tree = _build_three_level_tree()
        req = EngSpecStep2SystemRequest(
            project_id="proj-5",
            mission="Build a robot",
            subsystems=tree,
        )
        eng_spec_step2_generate_system(req)

        call_kwargs = mock_sys_specs.call_args[1]
        assert call_kwargs["systems"] == tree
        assert call_kwargs["mission"] == "Build a robot"
        assert call_kwargs["library_summary"] == "lib context"
        assert call_kwargs["project_id"] == "proj-5"


# ═══════════════════════════════════════════════════════════════════════════
# Test: dataclass construction
# ═══════════════════════════════════════════════════════════════════════════

class TestDataclasses:
    """Smoke tests for internal dataclasses."""

    def test_planned_field_defaults(self):
        f = PlannedField(field_name="x", category="spatial", why="reason")
        assert f.expected_unit is None

    def test_component_field_plan_defaults(self):
        c = ComponentFieldPlan(subsystem_code="C-1", component_type_hint="motor")
        assert c.fields == []

    def test_module_field_plan_defaults(self):
        m = ModuleFieldPlan(module_name="Mod")
        assert m.components == []

    def test_field_plan_full_construction(self):
        f = PlannedField(field_name="mass", category="mechanical", why="weight budget", expected_unit="kg")
        c = ComponentFieldPlan(subsystem_code="C-1", component_type_hint="housing", fields=[f])
        m = ModuleFieldPlan(module_name="Shell Module", components=[c])
        assert m.module_name == "Shell Module"
        assert len(m.components) == 1
        assert m.components[0].fields[0].expected_unit == "kg"
