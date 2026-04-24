"""Prompt Assembler — context engineering with cache separation + token budget.

Assembles prompts from:
- Structural templates (from prompts/*.py) — never truncated
- Knowledge skills (from skills/*/SKILL.md) — truncatable by budget
- Dynamic context (previous layer output, user input) — not cached

Separates static_system (cacheable, 5min TTL) from dynamic_context (non-cacheable)
to maximize Anthropic prompt cache hit rate.

Usage:
    from app.harness.prompt_assembler import assemble_prompt

    system, user = assemble_prompt(
        template=TRIZ_TC_SYSTEM,
        knowledge_blocks={"39_params": load_39_parameters()},
        dynamic_context={"tc_description": "Weight vs Strength"},
        token_budget=12000,
    )
"""

from __future__ import annotations

import logging
from typing import Any

from app.observability import emit_counter

logger = logging.getLogger(__name__)

# Rough token estimation: chars / 4
_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Rough token count: chars / 4 approximation."""
    return len(text) // _CHARS_PER_TOKEN


def assemble_prompt(
    template: str,
    *,
    knowledge_blocks: dict[str, str] | None = None,
    dynamic_context: dict[str, str] | None = None,
    token_budget: int = 12000,
) -> tuple[str, str]:
    """Assemble a prompt from structural template + knowledge + dynamic context.

    Returns:
        (system_prompt, user_message) tuple.
        - system_prompt: template + knowledge blocks (cacheable)
        - user_message: dynamic context (non-cacheable)

    The system_prompt is designed to be stable across calls so Anthropic's
    prompt cache (5min TTL) can be utilized. Dynamic context changes per call.

    Token budget controls knowledge block injection:
    1. Template tokens are always included (never truncated)
    2. Knowledge blocks are injected in order until budget is reached
    3. If a block would exceed budget, it's truncated with a note
    4. Dynamic context is always included (not subject to budget)
    """
    knowledge_blocks = knowledge_blocks or {}
    dynamic_context = dynamic_context or {}

    # Step 1: Template is always included
    template_tokens = _estimate_tokens(template)
    remaining_budget = token_budget - template_tokens

    if remaining_budget < 0:
        logger.warning(
            "Template alone (%d tokens) exceeds budget (%d tokens)",
            template_tokens,
            token_budget,
        )
        emit_counter("context.budget_exceeded")

    # Step 2: Inject knowledge blocks within budget
    knowledge_parts: list[str] = []
    for block_name, block_content in knowledge_blocks.items():
        block_tokens = _estimate_tokens(block_content)

        if remaining_budget <= 0:
            logger.debug(
                "Skipping knowledge block '%s' (%d tokens) — budget exhausted",
                block_name,
                block_tokens,
            )
            continue

        if block_tokens <= remaining_budget:
            knowledge_parts.append(
                f"<knowledge name=\"{block_name}\">\n{block_content}\n</knowledge>"
            )
            remaining_budget -= block_tokens
        else:
            # Truncate to fit
            max_chars = remaining_budget * _CHARS_PER_TOKEN
            truncated = block_content[:max_chars]
            knowledge_parts.append(
                f"<knowledge name=\"{block_name}\" truncated=\"true\">\n"
                f"{truncated}\n"
                f"[... truncated to fit token budget ...]\n"
                f"</knowledge>"
            )
            remaining_budget = 0
            logger.info(
                "Truncated knowledge block '%s' from %d to %d tokens",
                block_name,
                block_tokens,
                max_chars // _CHARS_PER_TOKEN,
            )

    # Step 3: Build system prompt (cacheable part)
    system_parts = [template]
    if knowledge_parts:
        system_parts.append("\n\n---\n\n" + "\n\n".join(knowledge_parts))
    system_prompt = "\n".join(system_parts)

    # Step 4: Build user message (dynamic, non-cacheable)
    user_parts: list[str] = []
    for ctx_name, ctx_content in dynamic_context.items():
        user_parts.append(
            f"<context name=\"{ctx_name}\">\n{ctx_content}\n</context>"
        )
    user_message = "\n\n".join(user_parts) if user_parts else ""

    logger.debug(
        "Assembled prompt: system=%d tokens, user=%d tokens, budget_remaining=%d",
        _estimate_tokens(system_prompt),
        _estimate_tokens(user_message),
        max(remaining_budget, 0),
    )

    return system_prompt, user_message


def build_cache_key(system_prompt: str) -> str:
    """Build a deterministic cache key for prompt cache identification.

    Two calls with the same system_prompt should hit the same cache entry.
    This is used for observability — Anthropic manages actual caching.
    """
    import hashlib

    return hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
