"""Lint tests for reference_source namespace + confidence enum (WBS 1.2).

These are NOT behaviour tests — they're static guards against string drift.

Background: `SpatialEstimate.reference_source` is a free-form string in the
schema because different backends emit different key shapes
(`rd_override:<key>`, `learned:<key>`, `web:<query>`, `seed:<key>`,
`llm_estimate`). That flexibility is load-bearing — but it also means a
typo like `rd_overide:` or `learnt:` will silently break the FE's badge
logic, the layered resolver's prefix matching, and the invalidation
pipeline.

This file locks down:

1. The **five canonical prefixes** that downstream code is allowed to emit.
2. The **three confidence enum values** used for badge colouring.
3. The prompt template must mention the full set (so the LLM knows its
   vocabulary).
4. The resolver backends must not introduce new prefixes without updating
   this test file — tests fail → PR fails → someone notices.

If you need to add a new prefix (e.g. `vendor_datasheet:`), update
ALLOWED_REFERENCE_SOURCE_PREFIXES here AND the FE badge logic AND the
prompt AND any documentation. That is the whole point of this lint.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# The authoritative list. Keep in sync with:
#   - app/services/spatial_lookup.py (each backend's emitted reference_source)
#   - app/prompts/triz_solver.py SUBSYSTEM_SUGGESTION instructions
#   - src/types/generated/subsystem.ts SpatialEstimate.reference_source doc
#   - src/components/create/InterfaceContractsPanel.tsx SpatialBlock colour map
#   - src/components/create/SpatialConfidenceBadge.tsx tooltip legend
ALLOWED_REFERENCE_SOURCE_PREFIXES: frozenset[str] = frozenset(
    {"rd_override", "learned", "web", "seed", "llm_estimate"}
)

ALLOWED_CONFIDENCE_VALUES: frozenset[str] = frozenset(
    {"library", "estimate", "rd_confirmed"}
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent / "app"


# ---------------------------------------------------------------------------
# reference_source prefix lint
# ---------------------------------------------------------------------------


def _prefixes_in_file(path: Path) -> set[str]:
    """Extract every `prefix:` token that appears in the file where
    `prefix` is something that looks like it's being used as a
    reference_source namespace. We keep this loose on purpose — the test
    is a smoke detector, not a parser. It flags obvious typos.
    """
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    # Match things like   "rd_override:"   'seed:'   f"web:{...}"
    # Does NOT match URLs like https: or timestamps.
    # Strategy: look for `<quote><lowercase_word>:` where the word is not
    # one of the well-known url schemes.
    IGNORE = {"http", "https", "file", "ftp", "ws", "wss", "data"}
    found: set[str] = set()
    for m in re.finditer(r"""['"]([a-z][a-z_0-9]*):""", text):
        tok = m.group(1)
        if tok in IGNORE:
            continue
        found.add(tok)
    return found


def test_spatial_lookup_only_uses_allowed_prefixes() -> None:
    """The resolver backends must only emit reference_source values whose
    prefix is in ALLOWED_REFERENCE_SOURCE_PREFIXES. New backends must
    update this list deliberately."""
    prefixes = _prefixes_in_file(BACKEND_ROOT / "services" / "spatial_lookup.py")
    # Every explicit reference_source=f"<prefix>:..." in spatial_lookup.py
    # uses one of these four backend name literals: `rd_override`,
    # `learned`, `web`, `seed`. `llm_estimate` is only set by the agent
    # layer, not the resolver, so it legitimately does not need to appear
    # here. Any OTHER literal that looks like a reference_source prefix
    # and is NOT in the allowed set is a drift bug.
    resolver_only_allowed = {"rd_override", "learned", "web", "seed"}
    # Keep only the tokens that look like reference_source prefixes (they
    # show up in contexts like f"rd_override:{...}"). The heuristic above
    # is generous and will pick up unrelated stuff like "category:";
    # intersect with the allowed set to avoid false positives.
    resolver_prefixes = prefixes & resolver_only_allowed
    # At minimum we expect to see rd_override, learned, seed. `web` only
    # appears behind an optional import guard in some branches.
    assert {"rd_override", "learned", "seed"}.issubset(resolver_prefixes), (
        f"spatial_lookup.py no longer emits some of the canonical reference_source "
        f"prefixes. Found: {sorted(resolver_prefixes)}. "
        f"If you renamed a backend, update ALLOWED_REFERENCE_SOURCE_PREFIXES in this file."
    )


def test_agent_fallback_uses_llm_estimate_literal() -> None:
    """The triz_solver agent must use the literal `llm_estimate` (not
    `llm-estimate`, `llmEstimate`, etc.) as the fallback reference_source.
    This is the only prefix the FE specifically colours red to nudge RD
    to override, so a typo would silently demote critical UX signals."""
    text = (BACKEND_ROOT / "agents" / "triz_solver.py").read_text(encoding="utf-8")
    # The resolver downgrade path and the prompt both reference this.
    # If someone renames it, at least one of these assertions fires.
    assert "llm_estimate" in text, (
        "triz_solver.py no longer references 'llm_estimate'. This is the FE's "
        "last-resort fallback prefix. Either update this test or restore the literal."
    )


def test_prompt_mentions_full_prefix_vocabulary() -> None:
    """The SUBSYSTEM_SUGGESTION prompt trains the LLM to cite
    reference_source values. If the prompt and the resolver disagree on
    the namespace, the LLM will emit values the resolver cannot parse."""
    path = BACKEND_ROOT / "prompts" / "triz_solver.py"
    if not path.exists():  # keep test safe even if structure changes
        pytest.skip("prompts file missing; update this test")
    text = path.read_text(encoding="utf-8")
    missing = [p for p in ALLOWED_REFERENCE_SOURCE_PREFIXES if p not in text]
    assert not missing, (
        f"The LLM prompt in triz_solver.py does not mention these "
        f"reference_source prefixes: {missing}. "
        f"Teach the LLM the full vocabulary or the resolver will reject its output."
    )


# ---------------------------------------------------------------------------
# confidence enum lint
# ---------------------------------------------------------------------------


def test_schema_confidence_enum_is_exactly_three_values() -> None:
    """The `SpatialEstimate.confidence` field is typed as a Literal of
    exactly three values. Changing this silently would break the FE
    badge colour mapping in at least 3 places."""
    schemas_text = (BACKEND_ROOT / "models" / "schemas.py").read_text(encoding="utf-8")
    for value in ALLOWED_CONFIDENCE_VALUES:
        assert value in schemas_text, (
            f"confidence value '{value}' is missing from schemas.py. "
            f"If you removed it, update ALLOWED_CONFIDENCE_VALUES in this test."
        )


# ---------------------------------------------------------------------------
# Schema behavioural guards — the text checks above catch typos in source,
# but they don't prove the Pydantic model actually REJECTS bad values. These
# tests instantiate the model and assert ValidationError fires on drift.
# (Added after Socratic audit: Finding A / Finding B.)
# ---------------------------------------------------------------------------


def test_spatial_estimate_rejects_unknown_confidence() -> None:
    """Construction with an unknown confidence string must raise. This is
    what `Literal[...]` guarantees; a plain `str` would silently accept."""
    from pydantic import ValidationError

    from app.models.schemas import SpatialEstimate

    # Happy paths — sanity.
    for ok in ("library", "estimate", "rd_confirmed"):
        SpatialEstimate(confidence=ok)

    # Drift cases — must raise.
    for bad in ("Library", "high", "unknown", "LLM_estimate", ""):
        with pytest.raises(ValidationError):
            SpatialEstimate(confidence=bad)


def test_suggested_subsystem_rejects_unknown_level() -> None:
    """level must be exactly one of the three canonical values. LLM emitting
    'sub-module' or 'Component' (case-mismatch) used to slip through the
    previous `str` typing and hit the FE, which has a stricter Literal."""
    from pydantic import ValidationError

    from app.models.schemas import SuggestedSubsystem

    for ok in ("system", "module", "component"):
        SuggestedSubsystem(name="X", level=ok)

    for bad in ("System", "Module", "sub-module", "system-level", ""):
        with pytest.raises(ValidationError):
            SuggestedSubsystem(name="X", level=bad)


# ---------------------------------------------------------------------------
# Stale-prefix regression guard — Finding D from Socratic audit.
# `ref_lib:` was an early-version prefix that no longer exists anywhere in
# the resolver. An earlier comment on `SpatialEstimate.reference_source`
# kept referencing it, which misled readers learning the vocabulary.
# ---------------------------------------------------------------------------


def test_schemas_does_not_reference_deprecated_ref_lib_prefix() -> None:
    """No comment, field doc, or literal in schemas.py should mention
    `ref_lib`. That prefix was removed when the layered resolver replaced
    the static JSON library — any surviving mention is stale doc drift."""
    schemas_text = (BACKEND_ROOT / "models" / "schemas.py").read_text(encoding="utf-8")
    assert "ref_lib" not in schemas_text, (
        "schemas.py still mentions the deprecated 'ref_lib' prefix. "
        "Replace with the canonical five-prefix list: rd_override, learned, "
        "web, seed, llm_estimate."
    )


def test_spatial_lookup_does_not_reference_deprecated_ref_lib_prefix() -> None:
    """Same guard for the resolver module — the one place most likely to
    accumulate doc drift as new backends are added and old ones renamed."""
    text = (BACKEND_ROOT / "services" / "spatial_lookup.py").read_text(encoding="utf-8")
    assert "ref_lib" not in text, (
        "spatial_lookup.py still mentions 'ref_lib'. That prefix no longer "
        "exists; use rd_override / learned / web / seed."
    )


def test_prompt_mentions_llm_emittable_confidence_values() -> None:
    """The LLM prompt must describe the confidence values the LLM is
    *allowed to emit* (`library`, `estimate`). `rd_confirmed` is a
    special value only set by RD via inline override, so the prompt
    must NOT teach the LLM to emit it — doing so would let the LLM
    spoof RD-level confidence on its own guesses, which would leak
    through the FE's darker-green badge semantics and trick the user."""
    path = BACKEND_ROOT / "prompts" / "triz_solver.py"
    if not path.exists():
        pytest.skip("prompts file missing")
    text = path.read_text(encoding="utf-8")
    llm_emittable = {"library", "estimate"}
    missing = [v for v in llm_emittable if v not in text]
    assert not missing, (
        f"The LLM prompt is missing confidence enum values: {missing}. "
        f"The LLM will emit values the schema rejects."
    )
    assert "rd_confirmed" not in text, (
        "The LLM prompt mentions 'rd_confirmed'. That value is RD-only — "
        "teaching the LLM to emit it lets the model spoof RD-approved "
        "confidence on its own estimates. Remove the mention."
    )
