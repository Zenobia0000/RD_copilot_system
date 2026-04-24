"""Tests for the TRIZ separation-principles structured parser.

Guards the Explore-stage TC→multi-PC decomposition contract: the 16 canonical
ids must round-trip cleanly from the markdown KB so that Pydantic validators
and frontend parity constants stay aligned.
"""

from __future__ import annotations

import pytest

from app.tools.separation_principles import (
    SEPARATION_PRINCIPLES,
    SeparationPrinciple,
    build_separation_principle_id_context,
    get_separation_principle,
    get_separation_principles_by_category,
    parse_separation_principles,
)


CANONICAL_IDS = [
    "time.pre_action",
    "time.post_action",
    "time.periodic_switching",
    "time.accelerated_pass",
    "space.local_quality",
    "space.partition_combine",
    "space.nesting",
    "space.geometry_transform",
    "condition.phase_change",
    "condition.threshold_trigger",
    "condition.responsive_material",
    "condition.external_field",
    "whole_part.composite",
    "whole_part.porous_hollow",
    "whole_part.gradient",
    "whole_part.fractal",
]

VALID_CATEGORIES = {"time", "space", "condition", "whole_part"}


def test_parse_returns_exactly_16_items() -> None:
    parsed = parse_separation_principles()
    assert len(parsed) == 16, f"expected 16 principles, got {len(parsed)}"
    assert len(SEPARATION_PRINCIPLES) == 16


def test_all_canonical_ids_present() -> None:
    parsed_ids = [sp.id for sp in SEPARATION_PRINCIPLES]
    missing = set(CANONICAL_IDS) - set(parsed_ids)
    extra = set(parsed_ids) - set(CANONICAL_IDS)
    assert not missing and not extra, (
        f"canonical id mismatch — missing={sorted(missing)} extra={sorted(extra)}"
    )
    # Order must match exactly too.
    assert parsed_ids == CANONICAL_IDS, (
        f"canonical id order mismatch:\n  expected={CANONICAL_IDS}\n  got={parsed_ids}"
    )


def test_no_empty_fields() -> None:
    for sp in SEPARATION_PRINCIPLES:
        assert sp.name_zh and sp.name_zh.strip(), f"{sp.id}: empty name_zh"
        assert sp.physical_principle and sp.physical_principle.strip(), (
            f"{sp.id}: empty physical_principle"
        )
        assert sp.cross_domain_examples and sp.cross_domain_examples.strip(), (
            f"{sp.id}: empty cross_domain_examples"
        )


def test_category_values_valid() -> None:
    for sp in SEPARATION_PRINCIPLES:
        assert sp.category in VALID_CATEGORIES, (
            f"{sp.id}: invalid category {sp.category!r}"
        )


def test_get_by_id_returns_match() -> None:
    sp = get_separation_principle("time.pre_action")
    assert sp is not None
    assert sp.category == "time"
    assert "預先" in sp.name_zh

    sp2 = get_separation_principle("whole_part.fractal")
    assert sp2 is not None
    assert sp2.category == "whole_part"
    assert "碎形" in sp2.name_zh or "自相似" in sp2.name_zh

    sp3 = get_separation_principle("condition.phase_change")
    assert sp3 is not None
    assert sp3.category == "condition"

    assert get_separation_principle("nonexistent.id") is None


def test_get_by_category_returns_4_each() -> None:
    for category in VALID_CATEGORIES:
        items = get_separation_principles_by_category(category)
        assert len(items) == 4, (
            f"category {category!r} expected 4 principles, got {len(items)}"
        )
        for sp in items:
            assert sp.category == category


def test_build_context_contains_all_ids() -> None:
    context = build_separation_principle_id_context()
    for canonical_id in CANONICAL_IDS:
        assert canonical_id in context, (
            f"prompt context missing canonical id {canonical_id!r}"
        )


def test_items_are_separation_principle_instances() -> None:
    for sp in SEPARATION_PRINCIPLES:
        assert isinstance(sp, SeparationPrinciple)
