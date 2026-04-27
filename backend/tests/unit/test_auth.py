"""Tests for JWT authentication middleware (WP-1.4).

Validates that:
- Protected endpoints reject unauthenticated / invalid requests with 401
- Valid JWT tokens are accepted (mocked)
- Public endpoints (/api/v1/health, /docs) remain unprotected
"""

import time
from unittest.mock import patch

import jwt
import pytest

# A fixed secret used only in tests
TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests"

# A protected endpoint to probe (brief extraction requires POST)
PROTECTED_ENDPOINT = "/api/v1/definitions/extract"


def _make_token(payload: dict, secret: str = TEST_JWT_SECRET) -> str:
    """Helper: create a signed HS256 JWT."""
    return jwt.encode(payload, secret, algorithm="HS256")


def _valid_payload() -> dict:
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
    }


# ---- Test: unauthenticated request returns 401 ----

def test_unauthenticated_request_returns_401(client_no_auth):
    """A request without an Authorization header must be rejected."""
    resp = client_no_auth.post(PROTECTED_ENDPOINT, json={"raw_text": "test"})
    assert resp.status_code == 401
    body = resp.json()
    # Error handler wraps in {"error": {"code": ..., "message": ...}}
    assert "Missing authorization token" in body["error"]["message"]


# ---- Test: invalid token returns 401 ----

def test_invalid_token_returns_401(client_no_auth):
    """A request with a malformed / wrong-secret JWT must be rejected."""
    bad_token = _make_token(_valid_payload(), secret="wrong-secret")
    with patch("app.middleware.auth.settings") as mock_settings:
        mock_settings.jwt_secret = TEST_JWT_SECRET
        resp = client_no_auth.post(
            PROTECTED_ENDPOINT,
            json={"raw_text": "test"},
            headers={"Authorization": f"Bearer {bad_token}"},
        )
    assert resp.status_code == 401
    assert "Invalid token" in resp.json()["error"]["message"]


# ---- Test: expired token returns 401 ----

def test_expired_token_returns_401(client_no_auth):
    """A request with an expired JWT must be rejected."""
    payload = _valid_payload()
    payload["exp"] = int(time.time()) - 60  # expired 1 minute ago
    token = _make_token(payload)
    with patch("app.middleware.auth.settings") as mock_settings:
        mock_settings.jwt_secret = TEST_JWT_SECRET
        resp = client_no_auth.post(
            PROTECTED_ENDPOINT,
            json={"raw_text": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401
    assert "expired" in resp.json()["error"]["message"].lower()


# ---- Test: valid token passes auth ----

def test_valid_token_passes_auth(client_no_auth):
    """A request with a correctly signed, non-expired JWT should pass auth.

    We mock the jwt_secret setting and the downstream agent call so we only
    test the auth layer.
    """
    token = _make_token(_valid_payload())
    with patch("app.middleware.auth.settings") as mock_settings:
        mock_settings.jwt_secret = TEST_JWT_SECRET
        # Mock the downstream agent so we don't need LLM calls
        with patch("app.agents.analyst.extract_brief") as mock_extract:
            mock_extract.return_value = {
                "project_name": "test",
                "objectives": [],
                "constraints": [],
                "kpis": [],
                "design_review": None,
            }
            resp = client_no_auth.post(
                PROTECTED_ENDPOINT,
                json={"raw_text": "test brief"},
                headers={"Authorization": f"Bearer {token}"},
            )
    # Should NOT be 401/403 — auth passed
    assert resp.status_code != 401
    assert resp.status_code != 403


# ---- Test: /api/v1/health is unprotected ----

def test_health_endpoint_unprotected(client_no_auth):
    """The /api/v1/health endpoint must remain public (no auth)."""
    resp = client_no_auth.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---- Test: /docs is unprotected ----

def test_docs_endpoint_unprotected(client_no_auth):
    """The /docs endpoint (OpenAPI UI) must remain public."""
    resp = client_no_auth.get("/docs")
    assert resp.status_code == 200
