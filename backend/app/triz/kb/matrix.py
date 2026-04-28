"""Contradiction matrix lookup — pure deterministic functions.

No LLM calls. Just (improve_id, worsen_id) → principle_ids.
"""

from __future__ import annotations

from .loader import KBLoader


def lookup_principles(kb: KBLoader, improve_id: int, worsen_id: int) -> list[int]:
    """Look up candidate TRIZ inventive principles from the contradiction matrix.

    Args:
        kb: Loaded knowledge base.
        improve_id: Improving parameter ID (1-39).
        worsen_id: Worsening parameter ID (1-39).

    Returns:
        List of recommended principle IDs, or empty list if no match.

    Raises:
        ValueError: If parameter IDs are out of range.
    """
    _validate_param_id(kb, improve_id, "improve")
    _validate_param_id(kb, worsen_id, "worsen")

    if improve_id == worsen_id:
        return []  # Same parameter — no contradiction

    return kb.lookup_principles(improve_id, worsen_id)


def validate_parameter_id(kb: KBLoader, param_id: int) -> bool:
    """Check if a parameter ID exists in the 39 parameters."""
    return param_id in kb.parameters


def _validate_param_id(kb: KBLoader, param_id: int, label: str) -> None:
    if param_id not in kb.parameters:
        raise ValueError(
            f"Invalid {label} parameter ID: {param_id}. "
            f"Must be one of 1-39."
        )
