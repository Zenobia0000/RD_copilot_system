"""Tests for the USDA Serializer — verifying correct USD ASCII output.

Covers:
  - Name sanitization
  - Layer header / defaultPrim
  - Three-level hierarchy (system → module → component)
  - BBox → xformOp:translate + extent_mm
  - InterfaceContract → rel interface:<dim>
  - DraftValue → typed custom properties with provenance
  - PackageMap clash map emission
  - Edge cases: empty tree, special characters, numeric-prefixed names
  - API endpoint integration (via TestClient)
"""

from __future__ import annotations

import re

import pytest

from app.models.schemas import (
    BBox,
    DraftValue,
    EngineeringSpecDraft,
    InterfaceContract,
    PackageMap,
    PackageNode,
    RequiredEnvelope,
    SpatialEstimate,
    SuggestedSubsystem,
)
from app.services.usda_serializer import (
    _build_clash_map,
    _build_drafts_by_code,
    _infer_shape,
    _sanitize_name,
    serialize_to_usda,
)


# ---------------------------------------------------------------------------
# _sanitize_name
# ---------------------------------------------------------------------------


class TestSanitizeName:
    def test_simple_alphanumeric(self):
        assert _sanitize_name("Motor") == "Motor"

    def test_spaces_replaced(self):
        assert _sanitize_name("Power Supply") == "Power_Supply"

    def test_hyphens_and_slashes(self):
        assert _sanitize_name("sub-system/v2") == "sub_system_v2"

    def test_leading_digit_gets_underscore(self):
        assert _sanitize_name("3DPrinter") == "_3DPrinter"

    def test_empty_string_returns_unnamed(self):
        assert _sanitize_name("") == "_unnamed"

    def test_all_special_chars(self):
        assert _sanitize_name("!@#$%") == "_unnamed"

    def test_brackets_and_dots(self):
        assert _sanitize_name("Motor [v1.2]") == "Motor_v1_2_"

    def test_unicode_stripped(self):
        # Chinese characters are not [a-zA-Z0-9_]
        result = _sanitize_name("馬達模組")
        assert result == "_unnamed"

    def test_mixed_unicode_and_ascii(self):
        result = _sanitize_name("Motor_馬達")
        assert result == "Motor_"


# ---------------------------------------------------------------------------
# Layer header
# ---------------------------------------------------------------------------


class TestLayerHeader:
    def test_header_contains_usda_magic(self):
        usda = serialize_to_usda([], project_id="test")
        assert usda.startswith("#usda 1.0")

    def test_header_meters_per_unit(self):
        usda = serialize_to_usda([], project_id="test")
        assert "metersPerUnit = 0.001" in usda

    def test_header_up_axis_z(self):
        usda = serialize_to_usda([], project_id="test")
        assert 'upAxis = "Z"' in usda

    def test_header_generator(self):
        usda = serialize_to_usda([], project_id="test")
        assert 'string generator = "RD_Design_Copilot"' in usda

    def test_header_project_id(self):
        usda = serialize_to_usda([], project_id="proj-42")
        assert '"proj-42"' in usda

    def test_header_export_timestamp(self):
        usda = serialize_to_usda([], project_id="test")
        assert "export_timestamp" in usda


# ---------------------------------------------------------------------------
# defaultPrim logic
# ---------------------------------------------------------------------------


class TestDefaultPrim:
    def test_single_root_uses_subsystem_name(self):
        root = SuggestedSubsystem(name="DriveUnit", level="system")
        usda = serialize_to_usda([root])
        assert 'defaultPrim = "DriveUnit"' in usda

    def test_multiple_roots_use_project_name(self):
        a = SuggestedSubsystem(name="SysA", level="system")
        b = SuggestedSubsystem(name="SysB", level="system")
        usda = serialize_to_usda([a, b], project_name="MyProject")
        assert 'defaultPrim = "MyProject"' in usda

    def test_multiple_roots_no_project_name_falls_back(self):
        a = SuggestedSubsystem(name="SysA", level="system")
        b = SuggestedSubsystem(name="SysB", level="system")
        usda = serialize_to_usda([a, b])
        assert 'defaultPrim = "Project"' in usda


# ---------------------------------------------------------------------------
# Empty tree
# ---------------------------------------------------------------------------


def test_empty_subsystems_produces_valid_header_only():
    usda = serialize_to_usda([], project_id="empty")
    assert usda.startswith("#usda 1.0")
    # Wrapper prim is emitted (len != 1), but no subsystem children
    assert 'def Xform "Project"' in usda
    assert usda.count("def Xform") == 1


# ---------------------------------------------------------------------------
# Three-level hierarchy
# ---------------------------------------------------------------------------


def _build_three_level_tree() -> SuggestedSubsystem:
    """Build System → Module → Component tree for testing."""
    component = SuggestedSubsystem(
        name="Stator",
        level="component",
    )
    module = SuggestedSubsystem(
        name="Motor",
        level="module",
        children=[component],
    )
    system = SuggestedSubsystem(
        name="DriveSystem",
        level="system",
        children=[module],
    )
    return system


class TestHierarchy:
    def test_system_has_assembly_kind(self):
        tree = _build_three_level_tree()
        usda = serialize_to_usda([tree])
        assert 'kind = "assembly"' in usda

    def test_module_has_group_kind(self):
        tree = _build_three_level_tree()
        usda = serialize_to_usda([tree])
        assert 'kind = "group"' in usda

    def test_component_has_component_kind(self):
        tree = _build_three_level_tree()
        usda = serialize_to_usda([tree])
        assert 'kind = "component"' in usda

    def test_nesting_depth(self):
        tree = _build_three_level_tree()
        usda = serialize_to_usda([tree])
        # Component "Stator" should be inside Motor, inside DriveSystem
        # Check for the nested def Xform sequence
        assert 'def Xform "DriveSystem"' in usda
        assert 'def Xform "Motor"' in usda
        assert 'def Xform "Stator"' in usda

    def test_braces_balanced(self):
        tree = _build_three_level_tree()
        usda = serialize_to_usda([tree])
        assert usda.count("{") == usda.count("}")


# ---------------------------------------------------------------------------
# customData: concept_origin, mapped_kpis, reason, related_contradictions
# ---------------------------------------------------------------------------


class TestCustomData:
    def test_concept_origin_code_emitted(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            concept_origin_code="S1.M1",
        )
        usda = serialize_to_usda([node])
        assert 'string concept_origin = "S1.M1"' in usda

    def test_mapped_kpis_emitted(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            mapped_kpis=["efficiency", "torque"],
        )
        usda = serialize_to_usda([node])
        assert '"efficiency"' in usda
        assert '"torque"' in usda
        assert "mapped_kpis" in usda

    def test_reason_emitted(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            reason="High torque requirement",
        )
        usda = serialize_to_usda([node])
        assert '"High torque requirement"' in usda

    def test_related_contradictions_emitted(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            related_contradictions=["TC-01", "TC-02"],
        )
        usda = serialize_to_usda([node])
        assert '"TC-01"' in usda
        assert '"TC-02"' in usda

    def test_display_name_always_emitted_in_customdata(self):
        """display_name is always emitted so customData is never absent."""
        node = SuggestedSubsystem(name="Motor", level="module")
        usda = serialize_to_usda([node])
        assert "customData" in usda
        assert 'string display_name = "Motor"' in usda
        # No other customData fields when optional fields are empty
        assert "concept_origin" not in usda
        assert "mapped_kpis" not in usda
        assert "reason" not in usda
        assert "related_contradictions" not in usda


# ---------------------------------------------------------------------------
# BBox / SpatialEstimate emission
# ---------------------------------------------------------------------------


def _module_with_spatial(
    name: str = "Motor",
    target: str = "Gearbox",
    **spatial_kwargs,
) -> SuggestedSubsystem:
    """Create a module with spatial data for testing."""
    bbox_fields = {"x_mm", "y_mm", "z_mm", "origin_mm", "anchor"}
    bbox_kwargs = {k: v for k, v in spatial_kwargs.items() if k in bbox_fields}
    rest = {k: v for k, v in spatial_kwargs.items() if k not in bbox_fields}
    return SuggestedSubsystem(
        name=name,
        level="module",
        interface_contracts={
            target: InterfaceContract(
                spatial=SpatialEstimate(bbox=BBox(**bbox_kwargs), **rest)
            )
        },
    )


class TestBBoxEmission:
    def test_translate_from_origin(self):
        node = _module_with_spatial(
            x_mm=180, y_mm=140, z_mm=120,
            origin_mm=(10.0, 20.0, 30.0),
        )
        usda = serialize_to_usda([node])
        assert "xformOp:translate = (10.0, 20.0, 30.0)" in usda

    def test_extent_mm(self):
        node = _module_with_spatial(x_mm=180, y_mm=140, z_mm=120)
        usda = serialize_to_usda([node])
        assert "extent_mm = (180.0, 140.0, 120.0)" in usda

    def test_anchor_string(self):
        node = _module_with_spatial(
            x_mm=100, y_mm=50, z_mm=50, anchor="downtube",
        )
        usda = serialize_to_usda([node])
        assert 'anchor = "downtube"' in usda

    def test_mass_g(self):
        node = _module_with_spatial(x_mm=180, y_mm=140, z_mm=120, mass_g=3900)
        usda = serialize_to_usda([node])
        assert "mass_g = 3900" in usda

    def test_mounting_pattern(self):
        node = _module_with_spatial(
            x_mm=100, y_mm=50, z_mm=50,
            mounting_pattern="M5x0.8",
        )
        usda = serialize_to_usda([node])
        assert 'mounting_pattern = "M5x0.8"' in usda

    def test_xform_op_order(self):
        node = _module_with_spatial(
            x_mm=100, y_mm=50, z_mm=50,
            origin_mm=(5.0, 0.0, 0.0),
        )
        usda = serialize_to_usda([node])
        assert 'xformOpOrder = ["xformOp:translate", "xformOp:scale"]' in usda

    def test_no_spatial_no_bbox_lines(self):
        node = SuggestedSubsystem(
            name="Motor", level="module",
            interface_contracts={"Gearbox": InterfaceContract()},
        )
        usda = serialize_to_usda([node])
        assert "xformOp:translate" not in usda
        assert "extent_mm" not in usda


# ---------------------------------------------------------------------------
# InterfaceContract → relationship arcs
# ---------------------------------------------------------------------------


class TestRelationships:
    def test_relationship_arc_emitted(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            interface_contracts={
                "Gearbox": InterfaceContract(
                    envelope="shared housing",
                    loadPath="torque transfer via spline",
                )
            },
        )
        usda = serialize_to_usda([node])
        assert "rel interface:envelope = </Motor/Gearbox>" in usda
        assert "rel interface:loadPath = </Motor/Gearbox>" in usda

    def test_empty_dimensions_skipped(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            interface_contracts={
                "Gearbox": InterfaceContract(
                    envelope="shared housing",
                    # other dimensions are empty/default
                )
            },
        )
        usda = serialize_to_usda([node])
        assert "rel interface:envelope" in usda
        assert "rel interface:thermalPath" not in usda

    def test_target_name_sanitized(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            interface_contracts={
                "3D-Printed Frame": InterfaceContract(envelope="bolted")
            },
        )
        usda = serialize_to_usda([node])
        assert "rel interface:envelope = </Motor/_3D_Printed_Frame>" in usda

    def test_no_contracts_no_relationship_section(self):
        node = SuggestedSubsystem(name="Motor", level="module")
        usda = serialize_to_usda([node])
        assert "Interface Relationships" not in usda


# ---------------------------------------------------------------------------
# DraftValue → Engineering Spec properties
# ---------------------------------------------------------------------------


def _make_draft(subsystem_code: str, specs: list[DraftValue]) -> EngineeringSpecDraft:
    """Build a minimal EngineeringSpecDraft."""
    return EngineeringSpecDraft(
        subsystem_code=subsystem_code,
        specs=specs,
    )


class TestEngSpecEmission:
    def test_float_value_uses_double_type(self):
        spec = DraftValue(
            field_name="rated_power",
            category="electrical",
            value=250.0,
            unit="W",
            source="datasheet",
            confidence="library",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "custom double electrical:rated_power:value = 250.0" in usda

    def test_int_value_uses_int_type(self):
        spec = DraftValue(
            field_name="pole_count",
            category="electrical",
            value=12,
            source="design",
            confidence="confirmed",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "custom int electrical:pole_count:value = 12" in usda

    def test_string_value_uses_string_type(self):
        spec = DraftValue(
            field_name="material",
            category="mechanical",
            value="Al-6061",
            source="estimate",
            confidence="estimate",
            needs_verification=True,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert 'custom string mechanical:material:value = "Al-6061"' in usda

    def test_unit_emitted_when_present(self):
        spec = DraftValue(
            field_name="voltage",
            category="electrical",
            value=48.0,
            unit="V",
            source="spec",
            confidence="confirmed",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert 'custom string electrical:voltage:unit = "V"' in usda

    def test_confidence_float_mapping(self):
        spec = DraftValue(
            field_name="power",
            category="electrical",
            value=500.0,
            source="estimate",
            confidence="speculative",
            needs_verification=True,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "custom float electrical:power:confidence = 0.4" in usda

    def test_needs_verification_bool(self):
        spec = DraftValue(
            field_name="power",
            category="electrical",
            value=500.0,
            source="estimate",
            confidence="estimate",
            needs_verification=True,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "custom bool electrical:power:needs_verification = true" in usda

    def test_rationale_emitted_when_present(self):
        spec = DraftValue(
            field_name="power",
            category="electrical",
            value=500.0,
            source="estimate",
            confidence="estimate",
            needs_verification=False,
            rationale="Based on motor efficiency curve",
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert '"Based on motor efficiency curve"' in usda

    def test_source_always_emitted(self):
        spec = DraftValue(
            field_name="power",
            category="electrical",
            value=500.0,
            source="vendor_datasheet_v2",
            confidence="library",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert 'custom string electrical:power:source = "vendor_datasheet_v2"' in usda

    def test_no_drafts_no_spec_section(self):
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        usda = serialize_to_usda([node])
        assert "Engineering Spec" not in usda

    def test_draft_matched_by_concept_origin_code(self):
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        spec = DraftValue(
            field_name="rpm",
            category="mechanical",
            value=3000,
            source="sim",
            confidence="estimate",
            needs_verification=False,
        )
        draft = _make_draft("S1.M1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "mechanical:rpm:value = 3000" in usda

    def test_draft_unmatched_code_not_emitted(self):
        node = SuggestedSubsystem(
            name="Motor", level="module",
            concept_origin_code="S1.M1",
        )
        spec = DraftValue(
            field_name="rpm",
            category="mechanical",
            value=3000,
            source="sim",
            confidence="estimate",
            needs_verification=False,
        )
        draft = _make_draft("WRONG_CODE", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "rpm" not in usda


# ---------------------------------------------------------------------------
# PackageMap clash map
# ---------------------------------------------------------------------------


class TestClashMap:
    def test_build_clash_map_from_package_map(self):
        pm = PackageMap(
            nodes=[
                PackageNode(name="Motor → Gearbox", clashes=["Battery → Frame"], spatial=SpatialEstimate(bbox=BBox(x_mm=1, y_mm=1, z_mm=1))),
                PackageNode(name="Battery → Frame", clashes=["Motor → Gearbox"], spatial=SpatialEstimate(bbox=BBox(x_mm=1, y_mm=1, z_mm=1))),
                PackageNode(name="Sensor → Board", clashes=[], spatial=SpatialEstimate(bbox=BBox(x_mm=1, y_mm=1, z_mm=1))),
            ],
            required=RequiredEnvelope(
                total_bbox_mm=(500, 150, 120),
                total_mass_g=7000,
            ),
        )
        clash_map = _build_clash_map(pm)
        assert clash_map["Motor → Gearbox"] == ["Battery → Frame"]
        assert clash_map["Battery → Frame"] == ["Motor → Gearbox"]
        assert "Sensor → Board" not in clash_map

    def test_build_clash_map_none(self):
        assert _build_clash_map(None) == {}

    def test_clash_emitted_in_usda(self):
        node = SuggestedSubsystem(
            name="Motor",
            level="module",
            interface_contracts={
                "Gearbox": InterfaceContract(
                    spatial=SpatialEstimate(
                        bbox=BBox(x_mm=180, y_mm=140, z_mm=120),
                    )
                )
            },
        )
        pm = PackageMap(
            nodes=[
                PackageNode(name="Motor", clashes=["Battery"], spatial=SpatialEstimate(bbox=BBox(x_mm=180, y_mm=140, z_mm=120))),
            ],
            required=RequiredEnvelope(
                total_bbox_mm=(180, 140, 120),
                total_mass_g=3000,
            ),
        )
        usda = serialize_to_usda([node], package_map=pm)
        assert 'aabb_clashes = ["Battery"]' in usda


# ---------------------------------------------------------------------------
# _build_drafts_by_code
# ---------------------------------------------------------------------------


class TestBuildDraftsByCode:
    def test_indexes_by_subsystem_code(self):
        d1 = _make_draft("S1.M1", [])
        d2 = _make_draft("S1.M2", [])
        idx = _build_drafts_by_code([d1, d2])
        assert "S1.M1" in idx
        assert "S1.M2" in idx
        assert idx["S1.M1"] is d1

    def test_none_returns_empty(self):
        assert _build_drafts_by_code(None) == {}

    def test_empty_list_returns_empty(self):
        assert _build_drafts_by_code([]) == {}


# ---------------------------------------------------------------------------
# Full integration: realistic tree
# ---------------------------------------------------------------------------


def test_realistic_tree_produces_valid_usda():
    """A realistic three-level tree with spatial data, contracts, and specs
    should produce a parseable USDA string."""
    stator = SuggestedSubsystem(name="Stator", level="component")
    rotor = SuggestedSubsystem(name="Rotor", level="component")
    motor = SuggestedSubsystem(
        name="Motor",
        level="module",
        concept_origin_code="S1.M1",
        children=[stator, rotor],
        interface_contracts={
            "Gearbox": InterfaceContract(
                envelope="shared housing",
                loadPath="torque spline",
                spatial=SpatialEstimate(
                    bbox=BBox(
                        x_mm=180, y_mm=140, z_mm=120,
                        origin_mm=(10.0, 0.0, 0.0),
                        anchor="BB",
                    ),
                    mass_g=3900,
                    mounting_pattern="M5x0.8",
                    confidence="library",
                ),
            )
        },
        mapped_kpis=["efficiency"],
        reason="Core drive unit",
    )
    battery = SuggestedSubsystem(
        name="Battery",
        level="module",
        concept_origin_code="S1.M2",
        interface_contracts={
            "Controller": InterfaceContract(
                signalPath="CAN bus",
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=380, y_mm=75, z_mm=65),
                    mass_g=3100,
                ),
            )
        },
    )
    drive = SuggestedSubsystem(
        name="DriveSystem",
        level="system",
        children=[motor, battery],
        related_contradictions=["TC-01"],
    )

    specs_motor = [
        DraftValue(
            field_name="rated_power",
            category="electrical",
            value=250.0,
            unit="W",
            source="datasheet",
            confidence="library",
            needs_verification=False,
        ),
        DraftValue(
            field_name="peak_torque",
            category="mechanical",
            value=120.0,
            unit="Nm",
            source="simulation",
            confidence="estimate",
            needs_verification=True,
            rationale="Estimated from motor curve at max current",
        ),
    ]
    specs_battery = [
        DraftValue(
            field_name="capacity",
            category="electrical",
            value=500,
            unit="Wh",
            source="vendor spec",
            confidence="confirmed",
            needs_verification=False,
        ),
    ]
    drafts = [
        _make_draft("S1.M1", specs_motor),
        _make_draft("S1.M2", specs_battery),
    ]

    pm = PackageMap(
        nodes=[
            PackageNode(name="Motor", clashes=["Battery"], spatial=SpatialEstimate(bbox=BBox(x_mm=180, y_mm=140, z_mm=120))),
            PackageNode(name="Battery", clashes=["Motor"], spatial=SpatialEstimate(bbox=BBox(x_mm=380, y_mm=140, z_mm=120))),
        ],
        required=RequiredEnvelope(
            total_bbox_mm=(560, 140, 120),
            total_mass_g=7000,
        ),
    )

    usda = serialize_to_usda(
        [drive],
        project_id="proj-e-bike-001",
        project_name="E-Bike Drive",
        drafts=drafts,
        package_map=pm,
    )

    # --- Structural assertions ---
    assert usda.startswith("#usda 1.0")
    assert 'defaultPrim = "DriveSystem"' in usda
    assert "metersPerUnit = 0.001" in usda

    # Hierarchy
    assert 'def Xform "DriveSystem"' in usda
    assert 'kind = "assembly"' in usda
    assert 'def Xform "S1_M1"' in usda
    assert 'kind = "group"' in usda
    assert 'def Xform "Stator"' in usda
    assert 'kind = "component"' in usda
    assert 'def Xform "Rotor"' in usda
    assert 'def Xform "S1_M2"' in usda

    # Spatial
    assert "xformOp:translate = (10.0, 0.0, 0.0)" in usda
    assert "extent_mm = (180.0, 140.0, 120.0)" in usda
    assert 'anchor = "BB"' in usda
    assert "mass_g = 3900" in usda
    assert 'mounting_pattern = "M5x0.8"' in usda

    # Relationships
    assert "rel interface:envelope = </DriveSystem/Gearbox>" in usda
    assert "rel interface:loadPath = </DriveSystem/Gearbox>" in usda
    assert "rel interface:signalPath = </DriveSystem/Controller>" in usda

    # Engineering specs (Motor)
    assert "custom double electrical:rated_power:value = 250.0" in usda
    assert 'custom string electrical:rated_power:unit = "W"' in usda
    assert "custom float electrical:rated_power:confidence = 0.92" in usda
    assert "custom double mechanical:peak_torque:value = 120.0" in usda
    assert "custom bool mechanical:peak_torque:needs_verification = true" in usda
    assert '"Estimated from motor curve at max current"' in usda

    # Engineering specs (Battery)
    assert "custom int electrical:capacity:value = 500" in usda
    assert "custom float electrical:capacity:confidence = 1.0" in usda

    # Clashes
    assert 'aabb_clashes = ["Battery"]' in usda

    # customData
    assert '"TC-01"' in usda
    assert 'string concept_origin = "S1.M1"' in usda
    assert '"efficiency"' in usda
    assert '"Core drive unit"' in usda

    # Balanced braces
    assert usda.count("{") == usda.count("}")

    # Trailing newline
    assert usda.endswith("\n")


# ---------------------------------------------------------------------------
# API endpoint (requires conftest client fixture)
# ---------------------------------------------------------------------------


class TestExportUsdaEndpoint:
    def test_returns_usda_content(self, client):
        payload = {
            "project_id": "p1",
            "project_name": "TestProject",
            "subsystems": [
                {
                    "name": "Motor",
                    "level": "module",
                }
            ],
        }
        resp = client.post("/api/v1/export/usda", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"].startswith("#usda 1.0")
        assert "TestProject" in data["filename"]
        assert data["filename"].endswith(".usda")

    def test_rejects_empty_subsystems(self, client):
        payload = {
            "project_id": "p1",
            "subsystems": [],
        }
        resp = client.post("/api/v1/export/usda", json=payload)
        assert resp.status_code == 422

    def test_nested_subsystems_via_api(self, client):
        payload = {
            "project_id": "p1",
            "project_name": "E-Bike",
            "subsystems": [
                {
                    "name": "DriveSystem",
                    "level": "system",
                    "children": [
                        {
                            "name": "Motor",
                            "level": "module",
                            "interface_contracts": {
                                "Gearbox": {
                                    "envelope": "shared housing",
                                    "spatial": {
                                        "bbox": {
                                            "x_mm": 180,
                                            "y_mm": 140,
                                            "z_mm": 120,
                                            "origin_mm": [10, 0, 0],
                                        },
                                        "mass_g": 3900,
                                    },
                                },
                            },
                        },
                    ],
                },
            ],
            "drafts": [
                {
                    "subsystem_code": "Motor",
                    "specs": [
                        {
                            "field_name": "rated_power",
                            "category": "electrical",
                            "value": 250.0,
                            "unit": "W",
                            "source": "datasheet",
                            "confidence": "library",
                            "needs_verification": False,
                        },
                    ],
                },
            ],
        }
        resp = client.post("/api/v1/export/usda", json=payload)
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert 'def Xform "DriveSystem"' in content
        assert 'def Xform "Motor"' in content
        assert "xformOp:translate = (10.0, 0.0, 0.0)" in content


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_bool_value_in_spec_uses_string_repr(self):
        """bool is a subclass of int in Python — serializer must treat it as
        a string/bool, NOT as ``custom int``."""
        spec = DraftValue(
            field_name="is_active",
            category="electrical",
            value=True,
            source="user",
            confidence="confirmed",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Relay", level="component",
            concept_origin_code="S1.C1",
        )
        draft = _make_draft("S1.C1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        # Should NOT use `custom int` for booleans
        assert "custom int electrical:is_active:value" not in usda
        assert 'custom string electrical:is_active:value = "true"' in usda

    def test_dict_value_serialized_as_json_string(self):
        spec = DraftValue(
            field_name="tolerance",
            category="mechanical",
            value={"min": 0.01, "max": 0.05},
            source="cad",
            confidence="confirmed",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Shaft", level="component",
            concept_origin_code="S1.C2",
        )
        draft = _make_draft("S1.C2", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        assert "custom string mechanical:tolerance:value" in usda
        # JSON content embedded in the string
        assert "min" in usda
        assert "max" in usda

    def test_quotes_in_string_value_escaped(self):
        spec = DraftValue(
            field_name="note",
            category="electrical",
            value='He said "hello"',
            source="user",
            confidence="confirmed",
            needs_verification=False,
        )
        node = SuggestedSubsystem(
            name="Widget", level="component",
            concept_origin_code="W1",
        )
        draft = _make_draft("W1", [spec])
        usda = serialize_to_usda([node], drafts=[draft])
        # Quotes must be escaped
        assert r'\"hello\"' in usda

    def test_multiple_roots_both_emitted(self):
        a = SuggestedSubsystem(name="SysA", level="system")
        b = SuggestedSubsystem(name="SysB", level="system")
        usda = serialize_to_usda([a, b], project_name="Multi")
        assert 'def Xform "SysA"' in usda
        assert 'def Xform "SysB"' in usda

    def test_deeply_nested_tree(self):
        """Four levels deep: system → module → component → component."""
        leaf = SuggestedSubsystem(name="Bearing", level="component")
        comp = SuggestedSubsystem(name="Shaft", level="component", children=[leaf])
        mod = SuggestedSubsystem(name="Gearbox", level="module", children=[comp])
        sys_ = SuggestedSubsystem(name="Drive", level="system", children=[mod])
        usda = serialize_to_usda([sys_])
        assert 'def Xform "Bearing"' in usda
        assert usda.count("{") == usda.count("}")

    def test_spatial_confidence_emitted(self):
        node = _module_with_spatial(
            x_mm=100, y_mm=50, z_mm=50,
            confidence="library",
        )
        usda = serialize_to_usda([node])
        assert 'spatial_confidence = "library"' in usda


# ---------------------------------------------------------------------------
# Chinese / CJK name scenarios  (Blender-import regression guard)
# ---------------------------------------------------------------------------

class TestChineseNameScenarios:
    """Guard against Blender-import failures when subsystem names are CJK-only."""

    def test_chinese_only_name_without_code_uses_unnamed(self):
        """A pure-Chinese name with no concept_origin_code → prim = '_unnamed'."""
        node = SuggestedSubsystem(name="馬達模組", level="module")
        usda = serialize_to_usda([node])
        assert 'def Xform "_unnamed"' in usda
        # Original Chinese name preserved in customData
        assert 'string display_name = "馬達模組"' in usda

    def test_chinese_name_with_concept_origin_code(self):
        """concept_origin_code takes priority so the prim is ASCII-safe."""
        node = SuggestedSubsystem(
            name="馬達模組", level="module", concept_origin_code="S1.M1",
        )
        usda = serialize_to_usda([node])
        assert 'def Xform "S1_M1"' in usda
        assert 'string display_name = "馬達模組"' in usda

    def test_multiple_chinese_siblings_get_unique_names(self):
        """Three CJK-only siblings without codes → _unnamed, _unnamed_1, _unnamed_2."""
        children = [
            SuggestedSubsystem(name="定子", level="component"),
            SuggestedSubsystem(name="轉子", level="component"),
            SuggestedSubsystem(name="軸承", level="component"),
        ]
        parent = SuggestedSubsystem(
            name="Motor", level="system", children=children,
        )
        usda = serialize_to_usda([parent])
        assert 'def Xform "_unnamed"' in usda
        assert 'def Xform "_unnamed_1"' in usda
        assert 'def Xform "_unnamed_2"' in usda
        # All display_names preserved
        assert 'string display_name = "定子"' in usda
        assert 'string display_name = "轉子"' in usda
        assert 'string display_name = "軸承"' in usda

    def test_mixed_cjk_ascii_name_keeps_ascii_part(self):
        """'馬達Motor' → only ASCII part 'Motor' is kept as prim name."""
        node = SuggestedSubsystem(name="馬達Motor", level="module")
        usda = serialize_to_usda([node])
        assert 'def Xform "Motor"' in usda
        assert 'string display_name = "馬達Motor"' in usda

    def test_chinese_system_with_coded_children(self):
        """Full tree: Chinese system name + children with concept_origin_code."""
        children = [
            SuggestedSubsystem(
                name="傳動齒輪", level="module", concept_origin_code="S2.G1",
            ),
            SuggestedSubsystem(
                name="控制電路", level="module", concept_origin_code="S2.C1",
            ),
        ]
        root = SuggestedSubsystem(
            name="驅動系統", level="system", children=children,
        )
        usda = serialize_to_usda([root])
        # Root has no code → falls back to _unnamed
        assert 'def Xform "_unnamed"' in usda
        assert 'string display_name = "驅動系統"' in usda
        # Children use their codes
        assert 'def Xform "S2_G1"' in usda
        assert 'string display_name = "傳動齒輪"' in usda
        assert 'def Xform "S2_C1"' in usda
        assert 'string display_name = "控制電路"' in usda
        # Braces still balanced
        assert usda.count("{") == usda.count("}")

    def test_duplicate_concept_origin_codes_get_suffix(self):
        """Two siblings sharing the same concept_origin_code get unique prim names."""
        children = [
            SuggestedSubsystem(
                name="元件A", level="component", concept_origin_code="X.1",
            ),
            SuggestedSubsystem(
                name="元件B", level="component", concept_origin_code="X.1",
            ),
        ]
        parent = SuggestedSubsystem(
            name="Parent", level="system", children=children,
        )
        usda = serialize_to_usda([parent])
        assert 'def Xform "X_1"' in usda
        assert 'def Xform "X_1_1"' in usda


# ---------------------------------------------------------------------------
# Proxy geometry — _infer_shape unit tests
# ---------------------------------------------------------------------------

class TestInferShape:
    """Direct tests for the _infer_shape helper."""

    def test_default_is_cube(self):
        assert _infer_shape("Motor") == "Cube"

    def test_generic_name_is_cube(self):
        assert _infer_shape("Gearbox Module") == "Cube"

    def test_shaft_keyword_returns_cylinder(self):
        assert _infer_shape("Main Shaft Assembly") == "Cylinder"

    def test_spindle_keyword_returns_cylinder(self):
        assert _infer_shape("spindle") == "Cylinder"

    def test_rotor_keyword_returns_cylinder(self):
        assert _infer_shape("Rotor Unit") == "Cylinder"

    def test_stator_keyword_returns_cylinder(self):
        assert _infer_shape("Inner Stator") == "Cylinder"

    def test_housing_keyword_returns_cylinder(self):
        assert _infer_shape("Housing Cover") == "Cylinder"

    def test_shell_keyword_returns_cylinder(self):
        assert _infer_shape("Outer Shell") == "Cylinder"

    def test_bb_keyword_returns_cylinder(self):
        assert _infer_shape("BB Cartridge") == "Cylinder"

    def test_chinese_shaft_returns_cylinder(self):
        assert _infer_shape("主軸模組") == "Cylinder"

    def test_chinese_rotor_returns_cylinder(self):
        assert _infer_shape("轉子") == "Cylinder"

    def test_chinese_stator_returns_cylinder(self):
        assert _infer_shape("定子組件") == "Cylinder"

    def test_chinese_housing_returns_cylinder(self):
        assert _infer_shape("殼體") == "Cylinder"

    def test_chinese_outer_shell_returns_cylinder(self):
        assert _infer_shape("外殼") == "Cylinder"

    def test_case_insensitive_match(self):
        assert _infer_shape("SHAFT") == "Cylinder"
        assert _infer_shape("sHaFt") == "Cylinder"


# ---------------------------------------------------------------------------
# Proxy geometry — integration tests
# ---------------------------------------------------------------------------

class TestProxyGeometry:
    """Tests for proxy geometry emission in serialize_to_usda."""

    def _spatial_node(
        self, name: str = "Motor", level: str = "module",
    ) -> SuggestedSubsystem:
        """Helper: create a node with spatial data for proxy geometry tests."""
        return SuggestedSubsystem(
            name=name,
            level=level,
            interface_contracts={
                "Target": InterfaceContract(
                    spatial=SpatialEstimate(
                        bbox=BBox(
                            x_mm=100.0, y_mm=80.0, z_mm=60.0,
                            origin_mm=(10.0, 20.0, 30.0),
                        ),
                    )
                )
            },
        )

    def test_cube_proxy_emitted_by_default(self):
        """Default settings emit a Cube proxy for non-cylinder names."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda([node])
        assert 'def Cube "proxy_Cube"' in usda
        assert "double size = 1.0" in usda
        assert "primvars:displayColor" in usda

    def test_cylinder_proxy_for_shaft_keyword(self):
        """Inferred mode emits Cylinder for shaft-like names."""
        node = self._spatial_node("Main Shaft")
        usda = serialize_to_usda([node])
        assert 'def Cylinder "proxy_Cylinder"' in usda
        assert "double radius" in usda
        assert "double height" in usda
        assert "primvars:displayColor" in usda

    def test_proxy_cube_mode_forces_cube_for_cylinder_name(self):
        """proxy_geometry_mode='cube' forces Cube even for shaft names."""
        node = self._spatial_node("Main Shaft")
        usda = serialize_to_usda([node], proxy_geometry_mode="cube")
        assert 'def Cube "proxy_Cube"' in usda
        assert 'def Cylinder' not in usda

    def test_include_proxy_geometry_false_suppresses(self):
        """include_proxy_geometry=False suppresses all proxy geometry."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda([node], include_proxy_geometry=False)
        assert "def Cube" not in usda
        assert "def Cylinder" not in usda
        assert "primvars:displayColor" not in usda

    def test_proxy_mode_none_suppresses(self):
        """proxy_geometry_mode='none' suppresses proxy even if flag is True."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda(
            [node], include_proxy_geometry=True, proxy_geometry_mode="none",
        )
        assert "def Cube" not in usda
        assert "def Cylinder" not in usda

    def test_no_spatial_no_proxy(self):
        """Nodes without spatial data never get proxy geometry."""
        node = SuggestedSubsystem(name="Motor", level="module")
        usda = serialize_to_usda([node])
        assert "def Cube" not in usda
        assert "def Cylinder" not in usda

    def test_proxy_cylinder_dimensions(self):
        """Cylinder proxy radius and height are derived from BBox."""
        node = self._spatial_node("Spindle")
        usda = serialize_to_usda([node])
        # radius = max(x_mm=100, y_mm=80) / 2 = 50.0
        assert "double radius = 50.0" in usda
        # height = z_mm = 60.0
        assert "double height = 60.0" in usda

    def test_proxy_cube_scale_from_bbox(self):
        """Cube proxy xformOp:scale matches BBox extents."""
        node = self._spatial_node("Gearbox")
        usda = serialize_to_usda([node])
        # The cube's own xformOp:scale inside the Cube prim
        # should contain bbox dimensions
        assert "def Cube" in usda
        assert "xformOp:scale = (100.0, 80.0, 60.0)" in usda

    def test_color_assignment_for_assembly(self):
        """Proxy gets colour from _ASSEMBLY_COLORS palette."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda([node])
        # First assembly should use first colour: (0.216, 0.494, 0.722)
        assert "primvars:displayColor = [(0.216, 0.494, 0.722)]" in usda

    def test_second_assembly_gets_different_color(self):
        """Two root assemblies get different colours from the palette."""
        n1 = self._spatial_node("Motor")
        n2 = self._spatial_node("Gearbox")
        usda = serialize_to_usda([n1, n2])
        # First: (0.216, 0.494, 0.722)
        assert "primvars:displayColor = [(0.216, 0.494, 0.722)]" in usda
        # Second: (0.894, 0.102, 0.110)
        assert "primvars:displayColor = [(0.894, 0.102, 0.11)]" in usda

    def test_braces_balanced_with_proxy(self):
        """Output with proxy geometry still has balanced braces."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda([node])
        assert usda.count("{") == usda.count("}")

    def test_semantic_data_preserved_with_proxy(self):
        """Proxy geometry doesn't replace semantic spatial properties."""
        node = self._spatial_node("Motor")
        usda = serialize_to_usda([node])
        # Semantic BBox data still present
        assert "extent_mm = (100.0, 80.0, 60.0)" in usda
        assert "xformOp:translate = (10.0, 20.0, 30.0)" in usda
        # Proxy also present
        assert "def Cube" in usda
