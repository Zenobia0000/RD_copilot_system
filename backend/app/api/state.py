"""TRIZ / TR state read endpoints — /api/v1/triz/*.

Exposes the three JSON sources the front-end needs to render the dashboard:
  - .claude/context/triz/.triz-state.json    (TRIZ session state, step 0-5)
  - .claude/context/triz/.tr-state.json      (TR engineering progress, TR0-10)
  - docs/engineering/MANIFEST.json           (artifact bundle index)

All three are returned as Pydantic-validated models so the OpenAPI schema is
machine-readable and the front-end can generate TypeScript types from
``/openapi.json``. The TRIZ models are permissive (``extra: "allow"``) so
fields the skills add later flow through unchanged.

Auth: re-uses ``get_current_user`` so the dev-bypass token works for local
development; in prod it requires a Supabase JWT.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.harness.cli import find_project_root
from app.middleware.auth import get_current_user
from app.triz.bundle import BundleError, BundleManager, BundleManifest
from app.triz.state import TRState, TrizSession
from app.triz.state_manager import StateError, TrizStateManager


# ────────────────────────────────────────────────────────────────────────────
# Path resolvers — process singletons
# ────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _project_root() -> Path:
    return find_project_root()


def _triz_context_dir() -> Path:
    return _project_root() / ".claude" / "context" / "triz"


def _engineering_root() -> Path:
    return _project_root() / "docs" / "engineering"


# ────────────────────────────────────────────────────────────────────────────
# Router
# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/triz",
    tags=["triz-state"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/state", response_model=TrizSession)
def get_triz_state() -> TrizSession:
    """Return the current .triz-state.json validated against TrizSession.

    404 if no session exists yet — the front-end should treat this as
    "no active TRIZ session" rather than an error.
    500 if the file is corrupt or fails schema validation (means a skill
    wrote something the schema doesn't accept; investigate which step).
    """
    mgr = TrizStateManager(_triz_context_dir())
    if not mgr.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="triz-state not found at .claude/context/triz/.triz-state.json",
        )
    try:
        return mgr.load()
    except StateError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"triz-state error: {exc}",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"corrupt triz-state: {exc}",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"triz-state schema mismatch: {exc.errors()[:3]}",
        )


@router.get("/tr-state", response_model=TRState)
def get_tr_state() -> TRState:
    """Return the current .tr-state.json validated against TRState.

    404 if TRIZ Step 5 hasn't fired yet (the TR state is bootstrapped by
    triz-wi at TR0 concept freeze).
    """
    mgr = TrizStateManager(_triz_context_dir())
    if not mgr.tr_state_exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tr-state not found at .claude/context/triz/.tr-state.json",
        )
    try:
        return mgr.load_tr_state()
    except StateError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"tr-state error: {exc}",
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"corrupt tr-state: {exc}",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"tr-state schema mismatch: {exc.errors()[:3]}",
        )


@router.get("/manifest", response_model=BundleManifest)
def get_manifest() -> BundleManifest:
    """Return the engineering bundle MANIFEST.json.

    Auto-initialises (empty manifest) if missing — front-end gets a
    consistent shape regardless of pipeline progress.
    """
    try:
        manager = BundleManager(
            engineering_root=_engineering_root(),
            state_dir=_triz_context_dir(),
        )
        return manager.load_or_create()
    except BundleError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"manifest error: {exc}",
        )
