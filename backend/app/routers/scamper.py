"""SCAMPER router — DEPRECATED.

SCAMPER as an independent module has been removed. TRIZ 40 principles
already cover all SCAMPER actions.

Subsystem-related endpoints have moved to /subsystems/:
  - POST /scamper/subsystem-suggestions  -> POST /subsystems/suggest
  - POST /scamper/spatial-overlay        -> POST /subsystems/spatial-overlay

The stubs below return HTTP 308 Permanent Redirect so existing clients
get a clear signal to update. These redirects will be removed in the
next major version.

Removed endpoints (no redirect — functionality retired):
  - POST /scamper/perform                — use TRIZ 40 principles instead
  - POST /scamper/feedback-contradictions — stub, never fully implemented
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.post("/scamper/subsystem-suggestions", include_in_schema=False)
def scamper_subsystem_suggestions_redirect():
    """DEPRECATED: redirects to POST /subsystems/suggest."""
    return RedirectResponse(
        url="/api/v1/subsystems/suggest",
        status_code=308,
    )


@router.post("/scamper/spatial-overlay", include_in_schema=False)
def scamper_spatial_overlay_redirect():
    """DEPRECATED: redirects to POST /subsystems/spatial-overlay."""
    return RedirectResponse(
        url="/api/v1/subsystems/spatial-overlay",
        status_code=308,
    )
