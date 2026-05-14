"""Unit tests for the LLM-based USDA generator helpers.

These tests cover prompt assembly, code-fence stripping, and bracket
validation — all pure functions that do NOT require an LLM call.
"""

from __future__ import annotations

import pytest

from app.prompts.usda_style import build_usda_user_message
from app.services.usda_llm_generator import strip_code_fences, validate_bracket_balance


# ---------------------------------------------------------------------------
# build_usda_user_message
# ---------------------------------------------------------------------------


class TestBuildUsdaUserMessage:
    """Verify the user-message builder includes all relevant context."""

    def test_basic_fields(self):
        msg = build_usda_user_message(
            node_name="Motor",
            node_level="component",
            node_description="BLDC motor for drive",
            specs_summary=[
                {"field_name": "mass", "value": 450, "unit": "g", "category": "spatial"},
            ],
            interface_contracts={},
            children_names=[],
        )
        assert "Motor" in msg
        assert "component" in msg
        assert "mass" in msg
        assert "450" in msg
        assert "BLDC motor" in msg

    def test_children_included(self):
        msg = build_usda_user_message(
            node_name="Drive_System",
            node_level="system",
            node_description="Main drive",
            specs_summary=[],
            interface_contracts={},
            children_names=["Motor", "Gearbox", "Shaft"],
        )
        assert "Motor" in msg
        assert "Gearbox" in msg
        assert "Shaft" in msg
        assert "Child Subsystems" in msg

    def test_interface_contracts_included(self):
        msg = build_usda_user_message(
            node_name="PCB",
            node_level="component",
            node_description="Control board",
            specs_summary=[],
            interface_contracts={"Motor": {"type": "electrical", "voltage": "24V"}},
            children_names=[],
        )
        assert "Interface with Motor" in msg
        assert "Interface Contracts" in msg

    def test_spec_without_unit(self):
        msg = build_usda_user_message(
            node_name="Shell",
            node_level="component",
            node_description="Outer shell",
            specs_summary=[
                {"field_name": "material", "value": "ABS", "unit": None, "category": "material"},
            ],
            interface_contracts={},
            children_names=[],
        )
        assert "material: ABS" in msg
        # No trailing space before bracket when unit is None
        assert "ABS [material]" in msg

    def test_empty_context(self):
        """Even with no specs/children/contracts, message is valid."""
        msg = build_usda_user_message(
            node_name="X",
            node_level="module",
            node_description="desc",
            specs_summary=[],
            interface_contracts={},
            children_names=[],
        )
        assert "Generate" in msg
        assert "module" in msg


# ---------------------------------------------------------------------------
# strip_code_fences
# ---------------------------------------------------------------------------


class TestStripCodeFences:
    def test_removes_usda_fence(self):
        raw = "```usda\n#usda 1.0\n()\n```"
        result = strip_code_fences(raw)
        assert result.startswith("#usda 1.0")
        assert "```" not in result

    def test_removes_plain_fence(self):
        raw = "```\n#usda 1.0\n()\n```"
        result = strip_code_fences(raw)
        assert result.startswith("#usda 1.0")

    def test_no_fence_passthrough(self):
        raw = "#usda 1.0\n(\n    upAxis = \"Z\"\n)\n"
        result = strip_code_fences(raw)
        assert result.startswith("#usda 1.0")

    def test_strips_whitespace(self):
        raw = "  \n #usda 1.0\n  "
        result = strip_code_fences(raw)
        assert result.startswith("#usda 1.0")


# ---------------------------------------------------------------------------
# validate_bracket_balance
# ---------------------------------------------------------------------------


class TestValidateBracketBalance:
    def test_valid_usda(self):
        usda = '#usda 1.0\n(\n    upAxis = "Z"\n)\ndef Xform "X" {\n    custom int a = 1\n}\n'
        # Should not raise
        validate_bracket_balance(usda)

    def test_unclosed_brace(self):
        usda = 'def Xform "X" { custom int a = 1'
        with pytest.raises(ValueError, match="Unclosed"):
            validate_bracket_balance(usda)

    def test_unexpected_close(self):
        usda = 'def Xform "X" }'
        with pytest.raises(ValueError, match="Unbalanced"):
            validate_bracket_balance(usda)

    def test_brackets_in_string_ignored(self):
        usda = 'custom string x = "has { and } inside"\n'
        validate_bracket_balance(usda)

    def test_nested_balanced(self):
        usda = (
            '#usda 1.0\n'
            '(\n    metersPerUnit = 0.001\n)\n'
            'def Xform "A" {\n'
            '    def Xform "B" {\n'
            '        custom int x = 1\n'
            '    }\n'
            '}\n'
        )
        validate_bracket_balance(usda)

    def test_mismatched_types(self):
        usda = 'def Xform "X" (kind = "assembly"}'
        with pytest.raises(ValueError):
            validate_bracket_balance(usda)
