"""Tests for KB loader and contradiction matrix lookup."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.triz.kb.loader import KBLoader
from app.triz.kb.matrix import lookup_principles, validate_parameter_id

KB_ROOT = Path(
    "/home/os-sunnie.gd.weng/python_workstation/sunny_01/"
    "RD_copilot_system/rd_assistant_design_system/triz_knowledge_base"
)


@pytest.fixture
def kb():
    if not KB_ROOT.exists():
        pytest.skip("KB root not found")
    return KBLoader(KB_ROOT)


class TestKBLoader:
    def test_load_parameters(self, kb):
        assert len(kb.parameters) == 39
        p10 = kb.get_parameter(10)
        assert p10 is not None
        assert "Force" in p10.name_en or "力" in p10.name_zh

    def test_load_principles(self, kb):
        assert len(kb.principles) >= 38  # at least most of 40
        p1 = kb.get_principle(1)
        assert p1 is not None
        assert "Segmentation" in p1.name_en or "分割" in p1.name_zh

    def test_load_matrix(self, kb):
        # Matrix should have hundreds of entries
        assert len(kb.matrix) > 200

    def test_load_separation(self, kb):
        seps = kb.separation_principles
        assert len(seps) == 4
        names = [s.name_en for s in seps]
        assert "Separation in Time" in names
        assert "Separation in Space" in names


class TestMatrixLookup:
    def test_tc1_lookup(self, kb):
        """TC1: Force (#10) → Volume of moving object (#7)."""
        result = lookup_principles(kb, 10, 7)
        assert result == [15, 9, 12, 37]

    def test_tc2_lookup(self, kb):
        """TC2: Force (#10) → Weight of moving object (#1)."""
        result = lookup_principles(kb, 10, 1)
        assert result == [8, 1, 37, 18]

    def test_tc3_lookup(self, kb):
        """TC3: Harmful side effects (#31) → Energy loss (#22)."""
        result = lookup_principles(kb, 31, 22)
        assert result == [19, 24, 3, 14]

    def test_tc4_lookup(self, kb):
        """TC4: Volume of stationary object (#8) → Temperature (#17)."""
        result = lookup_principles(kb, 8, 17)
        assert result == [35, 39, 38]

    def test_tc5_lookup(self, kb):
        """TC5: Weight of stationary object (#2) → Strength (#14)."""
        result = lookup_principles(kb, 2, 14)
        assert result == [28, 2, 27]

    def test_same_parameter(self, kb):
        """Same param → empty (no self-contradiction)."""
        assert lookup_principles(kb, 10, 10) == []

    def test_invalid_param(self, kb):
        with pytest.raises(ValueError, match="Invalid"):
            lookup_principles(kb, 99, 1)

    def test_validate_parameter_id(self, kb):
        assert validate_parameter_id(kb, 1) is True
        assert validate_parameter_id(kb, 39) is True
        assert validate_parameter_id(kb, 0) is False
        assert validate_parameter_id(kb, 40) is False

    def test_get_matrix_row(self, kb):
        row = kb.get_matrix_row(10)
        assert 7 in row
        assert row[7] == [15, 9, 12, 37]

    def test_inject_principles_for_prompt(self, kb):
        text = kb.inject_principles_for_prompt([1, 15])
        assert "#1" in text
        assert "#15" in text
        assert "Segmentation" in text or "分割" in text
