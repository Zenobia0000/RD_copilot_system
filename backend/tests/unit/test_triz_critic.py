"""Unit tests for should_trigger_pc_decomposition (task 2.1).

Each of the 5 rules is tested in isolation plus combined fallthrough cases.
"""
from unittest.mock import patch

import pytest

from app.agents.triz_critic import should_trigger_pc_decomposition
from app.models.schemas import ContradictionFormalizeResponse


def _make_tc(
    *,
    engineering_statement: str = "improving weight worsens strength",
    improving: int | None = 1,
    worsening: int | None = 14,
) -> ContradictionFormalizeResponse:
    return ContradictionFormalizeResponse(
        engineering_statement=engineering_statement,
        improving_param=improving,
        worsening_param=worsening,
        type="TC",
        confidence=0.8,
    )


# ---------------------------------------------------------------------------
# Rule 1: severity
# ---------------------------------------------------------------------------


def test_rule_1_severity_major_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="major",
        natural_description="normal description",
        candidate_principles=[1, 2, 3, 4, 5],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "severity" in reason


def test_rule_1_severity_fatal_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="fatal",
        natural_description="normal description",
        candidate_principles=[1, 2, 3, 4, 5],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "severity" in reason
    assert "fatal" in reason


# ---------------------------------------------------------------------------
# Rule 2: candidate_principles coverage
# ---------------------------------------------------------------------------


def test_rule_2_few_candidates_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="normal description",
        candidate_principles=[1],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "hits" in reason


def test_rule_2_zero_candidates_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="normal description",
        candidate_principles=[],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "hits" in reason


def test_rule_2_none_candidates_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="normal description",
        candidate_principles=None,
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "hits" in reason


# ---------------------------------------------------------------------------
# Rule 3: RD manual
# ---------------------------------------------------------------------------


def test_rule_3_rd_manual_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="normal description",
        candidate_principles=[1, 2, 3, 4, 5],
        rd_manual=True,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "RD" in reason


# ---------------------------------------------------------------------------
# Rule 4: same-property exclusion language
# ---------------------------------------------------------------------------


def test_rule_4_same_property_language_triggers():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="齒輪既要大又要小",
        candidate_principles=[1, 2, 3, 4, 5],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is True
    assert "互斥" in reason


# ---------------------------------------------------------------------------
# Rule 5: LLM critic fallback
# ---------------------------------------------------------------------------


def test_rule_5_llm_critic_triggers_when_trade_off():
    tc = _make_tc()
    with patch(
        "app.agents.triz_critic._llm_critic_judges_trade_off",
        return_value=(True, "critic: all trade-off"),
    ) as mock_critic:
        triggered, reason = should_trigger_pc_decomposition(
            tc_response=tc,
            severity="minor",
            natural_description="normal description without exclusion",
            candidate_principles=[1, 2, 3, 4, 5],
            rd_manual=False,
            enable_llm_critic=True,
        )
    assert triggered is True
    assert "critic" in reason
    assert mock_critic.called


def test_rule_5_llm_critic_does_not_trigger_when_breakthrough():
    tc = _make_tc()
    with patch(
        "app.agents.triz_critic._llm_critic_judges_trade_off",
        return_value=(False, "critic: L1 足夠深 (has breakthrough)"),
    ):
        triggered, reason = should_trigger_pc_decomposition(
            tc_response=tc,
            severity="minor",
            natural_description="normal description without exclusion",
            candidate_principles=[1, 2, 3, 4, 5],
            rd_manual=False,
            enable_llm_critic=True,
        )
    assert triggered is False
    assert "critic" in reason


def test_llm_critic_exception_returns_false():
    tc = _make_tc()
    with patch(
        "app.agents.triz_critic._llm_critic_judges_trade_off",
        side_effect=RuntimeError("LLM timeout"),
    ):
        triggered, reason = should_trigger_pc_decomposition(
            tc_response=tc,
            severity="minor",
            natural_description="normal description without exclusion",
            candidate_principles=[1, 2, 3, 4, 5],
            rd_manual=False,
            enable_llm_critic=True,
        )
    assert triggered is False
    assert "failed" in reason


# ---------------------------------------------------------------------------
# Fallthrough (no rule triggers, LLM disabled)
# ---------------------------------------------------------------------------


def test_no_trigger_when_all_rules_miss_and_llm_disabled():
    tc = _make_tc()
    triggered, reason = should_trigger_pc_decomposition(
        tc_response=tc,
        severity="minor",
        natural_description="normal description without exclusion",
        candidate_principles=[1, 2, 3, 4, 5],
        rd_manual=False,
        enable_llm_critic=False,
    )
    assert triggered is False
    assert "足夠深" in reason or "規則" in reason
