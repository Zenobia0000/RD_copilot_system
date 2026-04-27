"""Tests for /api/v1/sessions — auth pattern + 501 stub confirmation.

Until P3 wires AgentLoop in, these endpoints return 501. The tests here lock
the auth boundary (every endpoint sits behind get_current_user) and the
request shape (Pydantic validation kicks in before 501).
"""

import time
from unittest.mock import patch

import jwt

TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests-32-bytes-min"
SESSIONS_BASE = "/api/v1/sessions"


def _make_token(payload: dict, secret: str = TEST_JWT_SECRET) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


def _valid_payload() -> dict:
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "aud": "authenticated",
    }


# ────────────────────────────────────────────────────────────────────────────
# Auth boundary — every sessions endpoint must reject unauth/invalid tokens
# ────────────────────────────────────────────────────────────────────────────

class TestSessionsAuth:
    def test_create_session_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.post(SESSIONS_BASE, json={"title": "x"})
        assert resp.status_code == 401
        assert "Missing authorization token" in resp.json()["error"]["message"]

    def test_run_command_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.post(
            f"{SESSIONS_BASE}/abc/run",
            json={"command": "/triz"},
        )
        assert resp.status_code == 401

    def test_get_session_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.get(f"{SESSIONS_BASE}/abc")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client_no_auth):
        bad = _make_token(_valid_payload(), secret="wrong-secret")
        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.jwt_secret = TEST_JWT_SECRET
            mock_settings.debug = False
            resp = client_no_auth.post(
                SESSIONS_BASE,
                json={"title": "x"},
                headers={"Authorization": f"Bearer {bad}"},
            )
        assert resp.status_code == 401
        assert "Invalid token" in resp.json()["error"]["message"]

    def test_expired_token_returns_401(self, client_no_auth):
        payload = _valid_payload()
        payload["exp"] = int(time.time()) - 60
        token = _make_token(payload)
        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.jwt_secret = TEST_JWT_SECRET
            mock_settings.debug = False
            resp = client_no_auth.post(
                SESSIONS_BASE,
                json={"title": "x"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401
        assert "expired" in resp.json()["error"]["message"].lower()


# ────────────────────────────────────────────────────────────────────────────
# Stub confirmation — auth passes → reach handler → 501 (until P3)
# ────────────────────────────────────────────────────────────────────────────

class TestSessionsStub:
    def test_create_session_with_valid_token_returns_501(self, client):
        resp = client.post(SESSIONS_BASE, json={"title": "test"})
        assert resp.status_code == 501
        assert "P3" in resp.json()["error"]["message"]

    def test_run_command_with_valid_token_returns_501(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/sess_abc/run",
            json={"command": "/triz", "user_message": "hi"},
        )
        assert resp.status_code == 501

    def test_get_session_with_valid_token_returns_501(self, client):
        resp = client.get(f"{SESSIONS_BASE}/sess_abc")
        assert resp.status_code == 501


# ────────────────────────────────────────────────────────────────────────────
# Request validation — Pydantic kicks in before the handler
# ────────────────────────────────────────────────────────────────────────────

class TestSessionsValidation:
    def test_run_command_missing_command_returns_422(self, client):
        resp = client.post(f"{SESSIONS_BASE}/x/run", json={})
        assert resp.status_code == 422

    def test_run_command_invalid_max_iterations_returns_422(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/x/run",
            json={"command": "/triz", "max_iterations": 0},
        )
        assert resp.status_code == 422

    def test_run_command_invalid_max_tokens_returns_422(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/x/run",
            json={"command": "/triz", "max_tokens": 5_000_000},
        )
        assert resp.status_code == 422
