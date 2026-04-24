"""Tests for `contains_same_property_exclusion` (L1 critic rule #5).

Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md task 2.1.5

Guards the text heuristic that decides whether a natural-language contradiction
description uses same-property mutual-exclusion language (a PC-shaped hint) vs.
a classic TC-shaped trade-off between two distinct parameters.
"""

from __future__ import annotations

import pytest

from app.agents.triz_critic import contains_same_property_exclusion


# ---------------------------------------------------------------------------
# Positive cases — should return True
# ---------------------------------------------------------------------------


def test_gear_module_must_be_large_and_small_returns_true() -> None:
    text = "齒輪模數必須大（為了強度）又必須小（為了空間）"
    assert contains_same_property_exclusion(text) is True


def test_both_high_depth_and_low_compute_returns_true() -> None:
    text = "既要高計算深度又要低計算量"
    assert contains_same_property_exclusion(text) is True


def test_shell_rigid_but_not_heavy_returns_true() -> None:
    text = "殼體需要剛硬但又不能太重"
    assert contains_same_property_exclusion(text) is True


def test_simultaneously_satisfy_sealing_and_heat_returns_true() -> None:
    text = "同一時間同時滿足密封和散熱"
    assert contains_same_property_exclusion(text) is True


def test_english_must_be_high_precision_and_low_cost_returns_true() -> None:
    text = "must be high precision and must be low cost"
    assert contains_same_property_exclusion(text) is True


def test_classic_warm_and_breathable_returns_true() -> None:
    text = "既保暖又透氣"
    assert contains_same_property_exclusion(text) is True


def test_on_one_hand_heat_on_the_other_moldable_returns_true() -> None:
    # invented: one-hand / other-hand construction
    text = "一方面要耐高溫另一方面要可塑形"
    assert contains_same_property_exclusion(text) is True


def test_english_must_be_rigid_and_must_be_flexible_returns_true() -> None:
    # invented: explicit English both-and
    text = "The material must be rigid and must be flexible."
    assert contains_same_property_exclusion(text) is True


# ---------------------------------------------------------------------------
# Negative cases — should return False
# ---------------------------------------------------------------------------


def test_torque_vs_weight_tradeoff_returns_false() -> None:
    text = "輸出扭矩 125 Nm 和系統重量 2500 g 的權衡"
    assert contains_same_property_exclusion(text) is False


def test_stiffness_reduces_damping_returns_false() -> None:
    text = "增加剛度會降低阻尼"
    assert contains_same_property_exclusion(text) is False


def test_insufficient_cooling_returns_false() -> None:
    text = "散熱不足"
    assert contains_same_property_exclusion(text) is False


def test_empty_string_returns_false() -> None:
    assert contains_same_property_exclusion("") is False


def test_short_battery_life_returns_false() -> None:
    text = "電池續航短"
    assert contains_same_property_exclusion(text) is False


def test_improve_x_degrades_y_english_returns_false() -> None:
    # invented: English TC-shape, two distinct parameters
    text = "Improving the output torque degrades the overall efficiency."
    assert contains_same_property_exclusion(text) is False


def test_raise_temperature_lowers_viscosity_returns_false() -> None:
    # invented: 改善 X 惡化 Y pattern
    text = "改善密封會惡化散熱"
    assert contains_same_property_exclusion(text) is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_whitespace_only_returns_false() -> None:
    assert contains_same_property_exclusion("   \n\t  ") is False


def test_none_like_empty_returns_false() -> None:
    # Python typing says str, but defensively the helper treats falsy as False.
    assert contains_same_property_exclusion("") is False


def test_long_text_with_pattern_in_middle_returns_true() -> None:
    prefix = "根據 RD 提供的需求背景，" * 5
    suffix = "，請工程團隊評估可行性。" * 5
    text = prefix + "齒輪既要大又要小" + suffix
    assert contains_same_property_exclusion(text) is True


def test_mixed_english_chinese_pattern_returns_true() -> None:
    text = "The housing 既要 lightweight 又要 rigid for vibration damping"
    assert contains_same_property_exclusion(text) is True


def test_pattern_too_far_apart_returns_false() -> None:
    # 既 and 又 separated by more than 30 characters — should NOT match the
    # generic 既...又... pattern because we use a bounded lazy quantifier.
    text = "既" + ("然這個設計的邏輯複雜度非常高而且牽涉到眾多外部模組和供應商協作" * 2) + "又"
    assert contains_same_property_exclusion(text) is False
