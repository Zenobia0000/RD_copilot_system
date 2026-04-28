"""Parameter mapping scorer — deterministic ranking of 39-parameter candidates.

Given a natural language description of an improving/worsening attribute,
score each of the 39 parameters for relevance. LLM is only needed when
top candidates are too close to disambiguate automatically.

Scoring algorithm from triz-contradict SKILL.md Step M1-M5.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..kb.loader import KBLoader, Parameter


@dataclass
class ScoredCandidate:
    """A parameter candidate with its relevance score."""
    param: Parameter
    score: float
    breakdown: dict[str, float]


# ── Category keywords ────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[int]] = {
    "geometric": [1, 2, 3, 4, 5, 6, 7, 8, 12],
    "physical": [9, 10, 11, 13, 14],
    "energy": [15, 16, 17, 18, 19, 20, 21, 22],
    "information": [23, 24, 25, 26, 27, 28, 29, 30],
    "system": [31, 32, 33, 34, 35, 36, 37, 38, 39],
}

# Common keyword → parameter ID associations
KEYWORD_MAP: dict[str, list[int]] = {
    # Force / torque
    "torque": [10], "扭矩": [10], "扭力": [10], "force": [10], "力": [10],
    # Weight
    "weight": [1, 2], "重量": [1, 2], "質量": [1, 2], "輕量": [1, 2],
    # Volume
    "volume": [7, 8], "體積": [7, 8], "size": [7, 8], "尺寸": [7, 8],
    # Temperature / thermal
    "temperature": [17], "溫度": [17], "散熱": [17], "thermal": [17], "溫升": [17],
    # Noise / harmful effects
    "noise": [31], "噪聲": [31], "噪音": [31], "振動": [31],
    "harmful": [31], "有害": [31], "副作用": [31],
    # Strength
    "strength": [14], "強度": [14], "剛性": [14],
    # Energy
    "efficiency": [22], "效率": [22], "能量損失": [22], "energy loss": [22],
    "power": [21], "功率": [21],
    # Speed
    "speed": [9], "速度": [9], "轉速": [9],
    # Stress
    "stress": [11], "應力": [11], "壓力": [11],
    # Reliability
    "reliability": [27], "可靠性": [27], "壽命": [15, 16],
    # Complexity
    "complexity": [36], "複雜度": [36], "零件數": [36],
    # Area
    "area": [5, 6], "面積": [5, 6],
    # Moving vs stationary disambiguation
    "motor": [1, 7, 10], "馬達": [1, 7, 10], "rotor": [1, 7],
    "shell": [2, 8], "外殼": [2, 8], "殼體": [2, 8], "housing": [2, 8],
    "gear": [10, 14], "齒輪": [10, 14],
}

# ── Scoring Weights ──────────────────────────────────────────────────

W_KEYWORD = 0.35
W_CATEGORY = 0.20
W_DEFINITION = 0.25
W_ENGINEERING = 0.20


def rank_candidates(
    nl_description: str,
    kb: KBLoader,
    *,
    top_n: int = 5,
) -> list[ScoredCandidate]:
    """Rank all 39 parameters by relevance to a natural language description.

    Args:
        nl_description: e.g. "馬達扭力密度" or "gear noise level"
        kb: Loaded knowledge base.
        top_n: Number of top candidates to return.

    Returns:
        Sorted list of top N candidates, highest score first.
    """
    desc_lower = nl_description.lower()
    candidates: list[ScoredCandidate] = []

    for pid, param in kb.parameters.items():
        breakdown: dict[str, float] = {}

        # Keyword match
        keyword_score = _keyword_score(desc_lower, pid)
        breakdown["keyword"] = keyword_score

        # Category alignment (does the description suggest this category?)
        cat_score = _category_score(desc_lower, pid)
        breakdown["category"] = cat_score

        # Definition overlap (word overlap between description and param definition)
        def_score = _definition_overlap(desc_lower, param)
        breakdown["definition"] = def_score

        # Engineering mapping overlap
        eng_score = _engineering_overlap(desc_lower, param)
        breakdown["engineering"] = eng_score

        total = (
            W_KEYWORD * keyword_score
            + W_CATEGORY * cat_score
            + W_DEFINITION * def_score
            + W_ENGINEERING * eng_score
        )
        candidates.append(ScoredCandidate(
            param=param, score=round(total, 4), breakdown=breakdown,
        ))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_n]


def needs_llm_disambiguation(candidates: list[ScoredCandidate], gap_threshold: float = 0.15) -> bool:
    """Check if top candidates are too close and need LLM disambiguation.

    Rules from SKILL.md:
    - If gap between #1 and #2 >= threshold → auto-select #1
    - If gap < threshold → need LLM
    - If all scores < 0.40 → need LLM (poor match)
    """
    if not candidates:
        return True
    if len(candidates) < 2:
        return candidates[0].score < 0.40
    if candidates[0].score < 0.40:
        return True
    gap = candidates[0].score - candidates[1].score
    return gap < gap_threshold


# ── Scoring helpers ──────────────────────────────────────────────────

def _keyword_score(desc: str, param_id: int) -> float:
    """Score based on keyword→parameter associations."""
    hits = 0
    total_keywords = 0
    for keyword, param_ids in KEYWORD_MAP.items():
        if keyword in desc:
            total_keywords += 1
            if param_id in param_ids:
                hits += 1
    if total_keywords == 0:
        return 0.0
    return min(hits / max(total_keywords, 1), 1.0)


def _category_score(desc: str, param_id: int) -> float:
    """Score based on whether the description suggests this param's category."""
    category_hints: dict[str, str] = {
        "geometric": "長度|寬度|面積|體積|尺寸|size|length|width|area|volume|diameter|直徑",
        "physical": "力|扭矩|速度|應力|強度|force|torque|speed|stress|strength|stiffness",
        "energy": "溫度|能量|功率|效率|thermal|energy|power|efficiency|temperature|heat",
        "information": "精度|可靠|資訊|量測|accuracy|reliability|information|measurement",
        "system": "噪音|複雜|可製造|有害|noise|complexity|manufacture|harmful|操作",
    }
    for cat, pattern in category_hints.items():
        if re.search(pattern, desc, re.IGNORECASE):
            if param_id in CATEGORY_KEYWORDS.get(cat, []):
                return 1.0
    return 0.0


def _definition_overlap(desc: str, param: Parameter) -> float:
    """Word overlap between description and parameter definition/name."""
    desc_words = set(re.findall(r"\w+", desc.lower()))
    param_words = set(re.findall(r"\w+", (
        f"{param.name_zh} {param.name_en} {param.description}"
    ).lower()))
    if not desc_words or not param_words:
        return 0.0
    overlap = desc_words & param_words
    return min(len(overlap) / max(len(desc_words), 1), 1.0)


def _engineering_overlap(desc: str, param: Parameter) -> float:
    """Word overlap between description and engineering mapping field."""
    desc_words = set(re.findall(r"\w+", desc.lower()))
    eng_words = set(re.findall(r"\w+", param.engineering_mapping.lower()))
    if not desc_words or not eng_words:
        return 0.0
    overlap = desc_words & eng_words
    return min(len(overlap) / max(len(desc_words), 1), 1.0)
