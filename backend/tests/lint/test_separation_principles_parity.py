"""Parity test: backend vs frontend separation principle lists.

Ensures backend/app/tools/separation_principles.py and
src/lib/triz/separationPrinciples.ts stay in sync (both id set AND order).

If either end changes an id without updating the other, this test fails.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.tools.separation_principles import SEPARATION_PRINCIPLES


def _frontend_ts_path() -> Path:
    """Resolve the frontend TS file relative to this test file.

    Using __file__ keeps the path robust regardless of pytest's cwd.
    backend/tests/test_*.py -> repo_root/src/lib/triz/separationPrinciples.ts
    """
    return (
        Path(__file__).resolve().parents[2]
        / "src"
        / "lib"
        / "triz"
        / "separationPrinciples.ts"
    )


def _extract_ts_ids(ts_source: str) -> list[str]:
    """Extract separation principle ids from the TS source file in order.

    Looks for `id: 'category.strategy'` / `id: "category.strategy"` patterns
    inside SeparationPrinciple object literals.
    """
    pattern = re.compile(r"id:\s*['\"]([a-z_]+\.[a-z_]+)['\"]")
    return pattern.findall(ts_source)


def test_frontend_ts_file_exists():
    path = _frontend_ts_path()
    assert path.exists(), f"Frontend TS file not found at {path}"


def test_frontend_ts_has_16_ids():
    path = _frontend_ts_path()
    ts_source = path.read_text(encoding="utf-8")
    ids = _extract_ts_ids(ts_source)
    assert len(ids) == 16, f"Expected 16 ids in TS file, found {len(ids)}: {ids}"


def test_backend_and_frontend_id_sets_match():
    """Both ends must contain the exact same id set (no missing / extra)."""
    backend_ids = {p.id for p in SEPARATION_PRINCIPLES}
    ts_source = _frontend_ts_path().read_text(encoding="utf-8")
    frontend_ids = set(_extract_ts_ids(ts_source))

    backend_only = backend_ids - frontend_ids
    frontend_only = frontend_ids - backend_ids
    assert not backend_only, (
        f"Backend-only ids (missing from frontend): {sorted(backend_only)}"
    )
    assert not frontend_only, (
        f"Frontend-only ids (missing from backend): {sorted(frontend_only)}"
    )


def test_backend_and_frontend_id_order_match():
    """Canonical order must match exactly (same first -> last)."""
    backend_order = [p.id for p in SEPARATION_PRINCIPLES]
    ts_source = _frontend_ts_path().read_text(encoding="utf-8")
    frontend_order = _extract_ts_ids(ts_source)
    assert backend_order == frontend_order, (
        f"Canonical order mismatch.\n"
        f"Backend: {backend_order}\n"
        f"Frontend: {frontend_order}"
    )
