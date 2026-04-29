"""Structured engineering deliverables — /api/v1/deliverables/*.

These endpoints turn the markdown tables in ``docs/engineering/`` into
JSON arrays so the front-end can sort, filter, and bind them to UI widgets
without re-parsing markdown client-side.

Source-of-truth invariant:
The markdown file is canonical. If a table column is renamed in the
markdown, update the ``HEADERS`` constant AND the field mapping below in
the same commit. This module never writes back — read-only by design.

Endpoints:
  GET /deliverables/kcs    → KCEntry[]   (from kc_list.md)
  GET /deliverables/risks  → RiskEntry[] (from risk_register.md)

Both 404 if the source markdown is absent (the front-end should treat that
as "TRIZ Step 5 hasn't run yet").
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.harness.cli import find_project_root
from app.middleware.auth import get_current_user
from app.triz.deliverable_schemas import KCEntry, RiskEntry
from app.triz.markdown_parser import find_table_by_header


# ────────────────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _project_root() -> Path:
    return find_project_root()


def _engineering_root() -> Path:
    return _project_root() / "docs" / "engineering"


def _read_markdown(path: Path, *, kind: str) -> str:
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{kind} not found at {path.relative_to(_project_root())}",
        )
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot read {kind}: {exc}",
        )


# ────────────────────────────────────────────────────────────────────────────
# Header-to-field mappings.
# Markdown header text on the LEFT, Pydantic field name on the RIGHT.
# Update both sides if either changes.
# ────────────────────────────────────────────────────────────────────────────

KC_HEADERS = {
    "KC ID": "id",
    "特徵": "feature",
    "子系統": "subsystem",
    "規格值": "spec",
    "公差": "tolerance",
    "來源 WI/ICD": "source",
    "量測方法": "method",
    "等級": "level",
}

RISK_HEADERS = {
    "Risk ID": "id",
    "風險描述": "description",
    "來源": "source",
    "影響域": "domain",
    "可能性": "probability",
    "衝擊度": "impact",
    "緩解措施": "mitigation",
    "負責 WI": "owner_wi",
}


def _rows_to_models(
    rows: list[dict[str, str]],
    header_map: dict[str, str],
    model_cls,
) -> list:
    """Map column headers → field names, then validate each row."""
    out = []
    for row in rows:
        kwargs = {}
        for md_header, field in header_map.items():
            kwargs[field] = row.get(md_header, "")
        # ``id`` is required — skip rows where it's blank (header-only or
        # statistics summary rows that don't have an ID column populated).
        if not kwargs.get("id"):
            continue
        out.append(model_cls(**kwargs))
    return out


# ────────────────────────────────────────────────────────────────────────────
# Router
# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/deliverables",
    tags=["deliverables"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/kcs", response_model=list[KCEntry])
def list_kcs() -> list[KCEntry]:
    """Return every Key Characteristic from kc_list.md as a JSON array.

    Front-end use cases: SPC plan, Control Plan, PPAP dimension report,
    Critical/Major/Minor filtering for QA dashboards.
    """
    md = _read_markdown(_engineering_root() / "kc_list.md", kind="kc_list")
    table = find_table_by_header(md, ["KC ID"])
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="kc_list.md exists but no KC table was found",
        )
    return _rows_to_models(table, KC_HEADERS, KCEntry)


@router.get("/risks", response_model=list[RiskEntry])
def list_risks() -> list[RiskEntry]:
    """Return every risk row from risk_register.md as a JSON array.

    Front-end use cases: risk dashboard, TR Gate blocking-risk drill-down,
    H/H severity filter.
    """
    md = _read_markdown(_engineering_root() / "risk_register.md", kind="risk_register")
    table = find_table_by_header(md, ["Risk ID"])
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="risk_register.md exists but no Risk table was found",
        )
    return _rows_to_models(table, RISK_HEADERS, RiskEntry)
