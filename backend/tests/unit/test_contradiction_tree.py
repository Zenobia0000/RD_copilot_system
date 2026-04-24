"""Tests for contradiction_tree utilities (§9.3 leaves-only filter)."""
import copy

import pytest

from app.tools.contradiction_tree import (
    get_children_of,
    get_contradiction_leaves,
    get_root_tcs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _c(id_: str, parent: str | None = None, **extra) -> dict:
    """Shortcut to build a minimal contradiction dict."""
    return {"id": id_, "parent_contradiction_id": parent, **extra}


# ---------------------------------------------------------------------------
# get_contradiction_leaves
# ---------------------------------------------------------------------------

def test_all_orphans_returns_all():
    """3 contradictions with no parent -> all returned."""
    data = [_c("c1"), _c("c2"), _c("c3")]
    assert get_contradiction_leaves(data) == data


def test_children_only():
    """1 parent + 2 children -> only 2 children returned."""
    data = [_c("tc1"), _c("pc1", "tc1"), _c("pc2", "tc1")]
    result = get_contradiction_leaves(data)
    assert len(result) == 2
    assert all(r["parent_contradiction_id"] == "tc1" for r in result)


def test_mixed_orphans_and_parents():
    """1 orphan TC + 1 parent TC with 2 children -> orphan + 2 children = 3."""
    data = [_c("tc_orphan"), _c("tc_parent"), _c("pc1", "tc_parent"), _c("pc2", "tc_parent")]
    result = get_contradiction_leaves(data)
    ids = [r["id"] for r in result]
    assert ids == ["tc_orphan", "pc1", "pc2"]


def test_empty_list():
    assert get_contradiction_leaves([]) == []


def test_preserves_input_order():
    """Output order must match input order for kept items."""
    data = [_c("pc2", "tc1"), _c("tc1"), _c("pc1", "tc1")]
    result = get_contradiction_leaves(data)
    result_ids = [r["id"] for r in result]
    assert result_ids == ["pc2", "pc1"]


# ---------------------------------------------------------------------------
# get_root_tcs
# ---------------------------------------------------------------------------

def test_get_root_tcs():
    """2 roots + 2 children -> only 2 roots returned."""
    data = [_c("tc1"), _c("tc2"), _c("pc1", "tc1"), _c("pc2", "tc2")]
    result = get_root_tcs(data)
    assert [r["id"] for r in result] == ["tc1", "tc2"]


# ---------------------------------------------------------------------------
# get_children_of
# ---------------------------------------------------------------------------

def test_get_children_of():
    """Returns children of specified parent_id only."""
    data = [_c("tc1"), _c("pc1", "tc1"), _c("pc2", "tc1"), _c("pc3", "tc2")]
    result = get_children_of(data, "tc1")
    assert [r["id"] for r in result] == ["pc1", "pc2"]


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------

def test_no_mutation():
    """Original list must not be mutated by get_contradiction_leaves."""
    data = [_c("tc1"), _c("pc1", "tc1")]
    original = copy.deepcopy(data)
    get_contradiction_leaves(data)
    assert data == original
