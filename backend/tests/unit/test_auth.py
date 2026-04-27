"""Tests for JWT authentication middleware.

Currently only the unprotected-endpoint tests survive — the protected-path
tests probed /api/v1/definitions/extract, which was deleted in the v1 cleanup.
P2 will add a real protected endpoint (POST /api/v1/sessions); the
unauthenticated/invalid/expired/valid token tests should be rewritten then.
"""


def test_health_endpoint_unprotected(client_no_auth):
    """/api/v1/health must remain public (no auth)."""
    resp = client_no_auth.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_docs_endpoint_unprotected(client_no_auth):
    """/docs (OpenAPI UI) must remain public."""
    resp = client_no_auth.get("/docs")
    assert resp.status_code == 200
