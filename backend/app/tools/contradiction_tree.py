"""Contradiction tree utilities — parent/child (TC->PC) relationships.

Uses the `parent_contradiction_id` FK from migration 009 to provide
leaves-only filtering for downstream consumers (CLD).

Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md §9.3.1
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_contradiction_leaves(
    contradictions: list[dict],
) -> list[dict]:
    """Return leaf-node contradictions for downstream consumption (CLD).

    A "leaf" is:
    - A child PC (has parent_contradiction_id set) — always included
    - A root TC/PC/SF (parent_contradiction_id is None) that has NO children in the input list

    This ensures that when a TC has been decomposed into multiple PCs,
    only the PCs appear in CLD input — not both parent AND children.

    Args:
        contradictions: List of contradiction dicts. Each dict must have at minimum:
            - 'id': str
            - 'parent_contradiction_id': str | None

    Returns:
        Filtered list (subset of input, preserving order).
    """
    # Collect set of all ids that ARE parents (have at least one child in the list)
    parent_ids: set[str] = set()
    for c in contradictions:
        pid = c.get("parent_contradiction_id")
        if pid:
            parent_ids.add(pid)

    # Keep: children (always) + orphans (no children found)
    leaves = [
        c for c in contradictions
        if c.get("parent_contradiction_id") is not None  # child -> always keep
        or c["id"] not in parent_ids                      # orphan -> keep
    ]

    if len(leaves) != len(contradictions):
        logger.debug(
            "contradiction_tree: filtered %d -> %d leaves (removed %d parents with children)",
            len(contradictions), len(leaves), len(contradictions) - len(leaves),
        )
    return leaves


def get_root_tcs(contradictions: list[dict]) -> list[dict]:
    """Return only root-level contradictions (parent_contradiction_id is None)."""
    return [c for c in contradictions if c.get("parent_contradiction_id") is None]


def get_children_of(contradictions: list[dict], parent_id: str) -> list[dict]:
    """Return children of a specific parent contradiction."""
    return [c for c in contradictions if c.get("parent_contradiction_id") == parent_id]
