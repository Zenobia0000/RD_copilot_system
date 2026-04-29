"""Artifact download endpoints — /api/v1/artifacts/*.

Streams files from ``docs/engineering/`` so the front-end can either render
markdown content (WI/ICD/MC bodies) or offer a download for binary artifacts
(CSV, PDF, ZIP).

Path traversal defence:
  - The relative path is joined onto ``docs/engineering/`` and resolved.
  - The resolved path must still live under the engineering root, otherwise
    a 403 is returned.
  - Reject ``..`` segments before resolution as a fast-fail.

Why two endpoints (raw vs file):
  - ``/raw`` returns ``text/plain`` with the file body inline. Useful for
    front-end markdown previews where you'd ``fetch().then(t => render(t))``.
  - ``/`` returns ``FileResponse`` with the proper media type — browsers
    will download non-text files (CSV, ZIP) and render text/markdown inline.

Listing endpoint omitted on purpose: front-ends should derive the list from
``GET /api/v1/triz/manifest`` (the MANIFEST.json is the SSOT for what
artifacts exist). A directory walk here would be a parallel source of
truth and drift over time.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse

from app.harness.cli import find_project_root
from app.middleware.auth import get_current_user


@lru_cache(maxsize=1)
def _project_root() -> Path:
    return find_project_root()


def _engineering_root() -> Path:
    return _project_root() / "docs" / "engineering"


def _resolve_artifact(rel_path: str) -> Path:
    """Resolve a relative artifact path safely.

    Returns the absolute path. Raises 400/403/404 on traversal attempts,
    out-of-root paths, or missing files.
    """
    if not rel_path or rel_path.startswith("/") or ".." in rel_path.split("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid path",
        )

    root = _engineering_root().resolve()
    target = (root / rel_path).resolve()

    # Must stay under engineering root after resolution
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="path escapes engineering root",
        )

    if not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"artifact not found: {rel_path}",
        )

    return target


router = APIRouter(
    prefix="/artifacts",
    tags=["artifacts"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{rel_path:path}/raw", response_class=PlainTextResponse)
def get_artifact_raw(rel_path: str) -> PlainTextResponse:
    """Return the artifact body as ``text/plain; charset=utf-8``.

    Suitable for markdown previews. Binary files (CSV with non-UTF-8 bytes,
    ZIP, PDF) will fail to decode here — use the non-/raw endpoint for
    those.
    """
    target = _resolve_artifact(rel_path)
    try:
        body = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="artifact is not UTF-8 text; use /artifacts/{path} (without /raw) to download as binary",
        )
    return PlainTextResponse(body, media_type="text/plain; charset=utf-8")


@router.get("/{rel_path:path}")
def get_artifact(rel_path: str) -> FileResponse:
    """Return the artifact as a file response with auto-detected media type.

    Browsers will inline-render markdown/text and offer download for ZIP/PDF.
    """
    target = _resolve_artifact(rel_path)
    return FileResponse(target, filename=target.name)
