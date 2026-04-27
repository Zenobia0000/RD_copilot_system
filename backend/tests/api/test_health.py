"""Tests for /api/v1/health — public liveness."""


def test_health_returns_ok(client_no_auth):
    resp = client_no_auth.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_does_not_require_auth(client_no_auth):
    """Even without a Bearer token, /health must succeed — it's the
    liveness probe, not behind the auth wall."""
    resp = client_no_auth.get("/api/v1/health")
    assert resp.status_code != 401
    assert resp.status_code != 403
