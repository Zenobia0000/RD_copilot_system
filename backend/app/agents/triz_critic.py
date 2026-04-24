"""L1 TRIZ critic — decides whether a TC contradiction needs PC drill-down.

Ref: docs/e2e/module/Forward_TRIZ_Solver_Architecture.md §6.2 (L2 trigger conditions)
Ref: rd_assistant_design_system/triz_knowledge_base/07_tc_pc_sf_differences.md §1.1
Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md tasks 2.1 / 2.1.5

This module currently exports ONLY the text-based heuristic helper
`contains_same_property_exclusion()`. The main `should_trigger_pc_decomposition()`
function will be added in a later wave (task 2.1) and will compose 5 rules:
    1. severity ∈ {fatal, major}
    2. len(candidate_principles) <= 2
    3. rd_manual=True
    4. LLM critic judges as "trade-off folding"
    5. contains_same_property_exclusion(natural_description)  ← this file
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from app.models.schemas import ContradictionFormalizeResponse

logger = logging.getLogger(__name__)


# Maximum characters allowed between the two anchors of a mutual-exclusion
# pattern (e.g. between 「既要」and「又要」). Kept tight to avoid spanning
# unrelated sentences while still tolerating adjectival phrases.
_GAP: Final[str] = r".{0,30}?"

# Regex patterns for same-property mutual-exclusion language detection.
# Ordered from most specific to most generic. A match at any level returns True.
#
# Design notes:
# - We deliberately do NOT match "增加 X 降低 Y" or "改善 X 惡化 Y" — those are
#   TC-shaped (one axis improves, another degrades) and should keep the flow
#   on the TC branch.
# - We DO match "既要...又要...", "必須...同時必須...", "需要...但又不能..." etc.,
#   which describe the SAME property being pulled in two incompatible directions.
_ZH_PATTERNS: Final[list[re.Pattern[str]]] = [
    # 既要 X 又要 Y  /  既 X 又 Y
    re.compile(r"既要" + _GAP + r"又要"),
    re.compile(r"既" + _GAP + r"又(?!要)"),  # "既保暖又透氣" — 又 not followed by 要
    # 必須 X 同時 (必須) Y  /  必須 X 又必須 Y
    re.compile(r"必須" + _GAP + r"同時" + _GAP + r"必須"),
    re.compile(r"必須" + _GAP + r"(?:又|也)必須"),
    re.compile(r"必須" + _GAP + r"同時" + _GAP + r"(?:又|也|還)"),
    # 一方面 X 另一方面 Y
    re.compile(r"一方面" + _GAP + r"另一方面"),
    # 需要 X 但又不能 Y  /  需要 X 卻又不能 Y
    re.compile(r"需要" + _GAP + r"但又不能"),
    re.compile(r"需要" + _GAP + r"卻又?不能"),
    re.compile(r"需要" + _GAP + r"但(?:又)?不能"),
    # 要 X 也要 Y  /  要 X 又要 Y
    re.compile(r"要" + _GAP + r"也要"),
    re.compile(r"要" + _GAP + r"又要"),
    # 應該 X 卻又要 Y  /  應該 X 又要 Y
    re.compile(r"應該" + _GAP + r"卻?又要"),
    # 同時滿足 X 和/與 Y
    re.compile(r"同時滿足"),
    re.compile(r"同一時間" + _GAP + r"同時滿足"),
    # 大 ... 又 ... 小 / 小 ... 又 ... 大  (explicit opposite pair with 又)
    re.compile(r"大" + _GAP + r"又" + _GAP + r"小"),
    re.compile(r"小" + _GAP + r"又" + _GAP + r"大"),
    re.compile(r"高" + _GAP + r"又" + _GAP + r"低"),
    re.compile(r"低" + _GAP + r"又" + _GAP + r"高"),
]

_EN_PATTERNS: Final[list[re.Pattern[str]]] = [
    # must be X and must be Y  /  must be X and must not be Y
    re.compile(r"must\s+be\b.{0,60}?\band\s+must(?:\s+not)?\s+be\b", re.IGNORECASE),
    # must X and must Y  (without "be")
    re.compile(r"must\b.{0,60}?\band\s+must\b", re.IGNORECASE),
    # needs to be X but cannot be Y  /  needs to be X yet cannot be Y
    re.compile(
        r"needs?\s+to\s+be\b.{0,60}?\b(?:but|yet)\s+(?:cannot|can't|must\s+not)\b",
        re.IGNORECASE,
    ),
    # both X and Y required / simultaneously
    re.compile(r"\bsimultaneously\s+(?:be\s+)?", re.IGNORECASE),
    re.compile(r"\bboth\b.{0,40}?\band\b.{0,40}?\b(?:required|needed|must)", re.IGNORECASE),
]


def contains_same_property_exclusion(text: str) -> bool:
    """Return True if the text describes a same-property mutual-exclusion (PC hint).

    This is rule #5 of the L1 critic (see module docstring).
    Used to detect PC-shaped contradictions from natural language before
    triggering TC→multi-PC decomposition.

    The detection is intentionally conservative: it looks for explicit
    natural-language markers that the same property is being pulled in two
    incompatible directions (e.g. "既要...又要...", "must be X and must be Y").
    It does NOT match classic TC-shaped language like "增加 X 降低 Y" or
    "improving X degrades Y", which describes two distinct parameters.

    Args:
        text: Natural-language contradiction description (Chinese or English).

    Returns:
        True if mutual-exclusion language is detected, False otherwise.
    """
    if not text or not text.strip():
        return False

    for pattern in _ZH_PATTERNS:
        if pattern.search(text):
            return True
    for pattern in _EN_PATTERNS:
        if pattern.search(text):
            return True
    return False


# ---------------------------------------------------------------------------
# Main L1 critic: decide whether TC needs PC drill-down (task 2.1)
# Ref: Forward_TRIZ_Solver_Architecture.md §6.2 (L2 trigger conditions)
# ---------------------------------------------------------------------------


def should_trigger_pc_decomposition(
    tc_response: "ContradictionFormalizeResponse",
    severity: str,
    natural_description: str,
    candidate_principles: list[int] | None = None,
    rd_manual: bool = False,
    enable_llm_critic: bool = True,
) -> tuple[bool, str]:
    """Decide whether a TC contradiction should trigger PC drill-down (L2).

    Implements 5 rules (rule layer first, LLM fallback last for cost):
      1. severity in {"fatal", "major"} → trigger
      2. len(candidate_principles) <= 2 → trigger (insufficient coverage)
      3. rd_manual is True → trigger (explicit RD request)
      4. contains_same_property_exclusion(natural_description) → trigger
         (Chinese/English mutual-exclusion language detected)
      5. LLM critic judges all suggestions as "trade-off folding" → trigger
         (only runs if rules 1-4 all miss and enable_llm_critic is True)

    Returns:
        (triggered: bool, reason: str)
    """
    # Rule 1: severity
    if severity in ("fatal", "major"):
        return True, f"severity={severity} ≥ major，預設深挖"

    # Rule 2: candidate_principles coverage
    candidates = candidate_principles or []
    if len(candidates) <= 2:
        return True, f"L1 principle hits={len(candidates)} ≤ 2，原理覆蓋不足"

    # Rule 3: RD manual request
    if rd_manual:
        return True, "RD 主動要求深挖"

    # Rule 4: same-property mutual-exclusion language (heuristic, free)
    if contains_same_property_exclusion(natural_description):
        return True, "偵測到同屬性互斥語言（例：既要...又要 / 必須...同時...）"

    # Rule 5: LLM critic (expensive, only if all rules above miss)
    if enable_llm_critic:
        try:
            return _llm_critic_judges_trade_off(tc_response, natural_description, candidates)
        except Exception as exc:  # noqa: BLE001
            logger.warning("L1 LLM critic failed, defaulting to no-trigger: %s", exc)
            return False, f"LLM critic failed: {exc}"

    return False, "L1 已足夠深（規則層全未觸發）"


def _llm_critic_judges_trade_off(
    tc_response: "ContradictionFormalizeResponse",
    natural_description: str,
    candidate_principles: list[int],
) -> tuple[bool, str]:
    """LLM fallback for rule 5. Uses L1_TRADE_OFF_CRITIC prompt."""
    from app.agents.base import call_llm_json
    from app.core.config import settings
    from app.prompts.analyst import ANALYST_SYSTEM, L1_TRADE_OFF_CRITIC
    from app.tools.triz_kb import get_param_name

    prompt = L1_TRADE_OFF_CRITIC.format(
        engineering_statement=tc_response.engineering_statement or natural_description,
        improving_param=tc_response.improving_param or 0,
        improving_name=get_param_name(tc_response.improving_param) if tc_response.improving_param else "",
        worsening_param=tc_response.worsening_param or 0,
        worsening_name=get_param_name(tc_response.worsening_param) if tc_response.worsening_param else "",
        candidate_principles=", ".join(str(p) for p in candidate_principles),
        suggestions_text="(none provided)",
    )

    if settings.use_harness_agents:
        from pydantic import BaseModel as _BM

        class _CriticOutput(_BM):
            all_trade_off: bool = False
            reason: str = ""

        from app.harness.agent_base import harness_call
        result = harness_call("triz_critic", ANALYST_SYSTEM, prompt, _CriticOutput)
        reason = str(result.reason)[:200]
        if result.all_trade_off:
            return True, f"critic: {reason}"
        return False, f"critic: L1 足夠深 ({reason})"

    raw = call_llm_json(ANALYST_SYSTEM, prompt)
    data = json.loads(raw) if raw and raw.strip() else {}
    all_trade_off = bool(data.get("all_trade_off"))
    reason = str(data.get("reason", ""))[:200]
    if all_trade_off:
        return True, f"critic: {reason}"
    return False, f"critic: L1 足夠深 ({reason})"
