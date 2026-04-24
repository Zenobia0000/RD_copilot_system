"""F2 subsystem_hint adapter tests (WBS §9.5).

Verifies that ``_enrich_contradiction_lines`` correctly injects
``[子系統提示: ...]`` and ``[物理變數: ...]`` tags into the formatted
prompt lines when contradiction dicts carry ``subsystem_hint`` and/or
``derived_parameter`` fields.

Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §9.5
"""

from __future__ import annotations

import pytest

from app.agents.triz_solver import _enrich_contradiction_lines


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _child_pc_with_hint() -> dict:
    """Child PC dict with subsystem_hint + derived_parameter."""
    return {
        "id": "C-EBIKE-012-PC1",
        "natural_description": "齒輪模數增加 → 傳動噪音增大",
        "subsystem_hint": "齒輪傳動",
        "derived_parameter": "齒輪模數",
    }


def _child_pc_without_hint() -> dict:
    """Child PC dict without enrichment fields."""
    return {
        "id": "C-EBIKE-012-PC2",
        "natural_description": "軸承壽命與重量矛盾",
    }


def _plain_string_contradiction() -> str:
    return "馬達功率密度提升導致溫升"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEnrichContradictionLines:
    """9.5.2 — Unit tests for the subsystem_hint adapter."""

    def test_contradiction_with_subsystem_hint_included_in_prompt(self):
        """Dict contradiction with subsystem_hint produces [子系統提示: ...] tag."""
        pc = _child_pc_with_hint()
        lines = _enrich_contradiction_lines([pc])
        assert len(lines) == 1
        assert "[子系統提示: 齒輪傳動]" in lines[0]
        assert "[物理變數: 齒輪模數]" in lines[0]
        # Also includes the natural description
        assert "齒輪模數增加 → 傳動噪音增大" in lines[0]

    def test_contradiction_without_hint_works_unchanged(self):
        """Plain string contradiction passes through without enrichment tags."""
        plain = _plain_string_contradiction()
        lines = _enrich_contradiction_lines([plain])
        assert len(lines) == 1
        assert lines[0] == f"- {plain}"
        assert "子系統提示" not in lines[0]
        assert "物理變數" not in lines[0]

    def test_mixed_parent_and_child_contradictions(self):
        """Mix of str, dict-with-hint, and dict-without-hint are handled correctly."""
        items: list = [
            _plain_string_contradiction(),          # str — no tags
            _child_pc_with_hint(),                   # dict — both tags
            _child_pc_without_hint(),                # dict — no tags
        ]
        lines = _enrich_contradiction_lines(items)
        assert len(lines) == 3

        # First line: plain string, no enrichment
        assert "[子系統提示:" not in lines[0]
        assert "[物理變數:" not in lines[0]

        # Second line: has both tags
        assert "[子系統提示: 齒輪傳動]" in lines[1]
        assert "[物理變數: 齒輪模數]" in lines[1]

        # Third line: dict but no hint fields
        assert "[子系統提示:" not in lines[2]
        assert "[物理變數:" not in lines[2]
        assert "軸承壽命與重量矛盾" in lines[2]

    def test_dict_with_only_subsystem_hint(self):
        """Dict with subsystem_hint but no derived_parameter shows only one tag."""
        pc = {"natural_description": "外殼剛性 vs 重量", "subsystem_hint": "外殼結構"}
        lines = _enrich_contradiction_lines([pc])
        assert "[子系統提示: 外殼結構]" in lines[0]
        assert "[物理變數:" not in lines[0]

    def test_dict_with_only_derived_parameter(self):
        """Dict with derived_parameter but no subsystem_hint shows only one tag."""
        pc = {"natural_description": "軸承配合間隙", "derived_parameter": "配合公差"}
        lines = _enrich_contradiction_lines([pc])
        assert "[子系統提示:" not in lines[0]
        assert "[物理變數: 配合公差]" in lines[0]

    def test_empty_list_returns_empty(self):
        """Empty input produces empty output."""
        assert _enrich_contradiction_lines([]) == []
