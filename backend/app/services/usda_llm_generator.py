"""LLM-based USDA generator — per-node USD ASCII generation.

Uses ``call_llm_structured`` to generate USDA text for a single
hierarchy node, then post-processes / validates the output.
"""

from __future__ import annotations

import re

from app.agents.base import call_llm_structured
from app.prompts.usda_style import USDA_SYSTEM_PROMPT, build_usda_user_message

# Re-use the lightweight schemas import only at call-time to avoid circular deps.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import NodeUsdaLlmRequest


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_node_usda(req: "NodeUsdaLlmRequest") -> str:
    """Generate USDA via LLM and post-process.

    Parameters
    ----------
    req:
        Validated request containing node context assembled by the frontend.

    Returns
    -------
    str
        Post-processed, syntactically checked USDA text.

    Raises
    ------
    ValueError
        If bracket balance validation fails after LLM generation.
    """
    #print("req: ", req)
    user_message = build_usda_user_message(
        node_name=req.node_name,
        node_level=req.node_level,
        node_description=req.node_description,
        specs_summary=req.specs_summary,
        interface_contracts=req.interface_contracts,
        children_names=req.children_names,
    )

    # 1. Call LLM
    print("USDA_SYSTEM_PROMPT: ", USDA_SYSTEM_PROMPT)
    print("="*20)
    print("="*20)
    print("user_message: ", user_message)
    print("="*20)
    print("="*20)
    # print(a)
    raw = call_llm_structured(USDA_SYSTEM_PROMPT, user_message)
    print("1 raw: ", raw)
    print("="*20)
    print("="*20)
    # 2. Strip markdown code fences (if LLM added ```usda … ```)
    raw = strip_code_fences(raw)
    print("2 raw: ", raw)
    print("="*20)
    print("="*20)
    # 3. Ensure #usda 1.0 header
    if not raw.strip().startswith("#usda 1.0"):
        raw = "#usda 1.0\n" + raw
    print("3 raw: ", raw)
    print("="*20)
    print("="*20)
    # 4. Basic syntax validation — bracket balance
    validate_bracket_balance(raw)
    print("4 raw: ", raw)
    print("="*20)
    print("="*20)

    return raw


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(
    r"^```[\w]*\s*\n(.*?)```\s*$",
    re.DOTALL | re.MULTILINE,
)


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences wrapping USDA content.

    Handles patterns like:
    - \\`\\`\\`usda\\n…\\`\\`\\`
    - \\`\\`\\`\\n…\\`\\`\\`
    """
    m = _CODE_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def validate_bracket_balance(usda_text: str) -> None:
    """Raise ``ValueError`` if braces / parens are not balanced.

    Respects double-quoted strings (ignoring brackets inside them).
    """
    stack: list[str] = []
    pairs = {"{": "}", "(": ")"}
    in_string = False
    prev = ""
    for ch in usda_text:
        if ch == '"' and prev != "\\":
            in_string = not in_string
        if not in_string:
            if ch in pairs:
                stack.append(pairs[ch])
            elif ch in pairs.values():
                if not stack or stack[-1] != ch:
                    raise ValueError(f"Unbalanced bracket: unexpected '{ch}'")
                stack.pop()
        prev = ch
    if stack:
        raise ValueError(f"Unclosed brackets: {stack}")
