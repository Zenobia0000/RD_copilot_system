"""Tests for /api/v1/sessions — auth boundary, validation, handler logic.

Handler logic uses two test-side overrides:
- get_harness_client → fake Anthropic client (no real API hit)
- module._project_root → tmp_path with synthetic .claude/ tree
"""

from __future__ import annotations

import time
from unittest.mock import patch

import jwt
import pytest

from app.api import sessions as sessions_module
from app.api.sessions import _reset_sessions_for_tests, get_harness_client
from app.harness.config import HarnessClient
from app.main import app
from app.middleware.auth import get_current_user
from tests.harness.test_agent import (
    FakeAnthropicClient,
    FakeResponse,
    FakeTextBlock,
    FakeToolUseBlock,
)

TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests-32-bytes-min"
SESSIONS_BASE = "/api/v1/sessions"


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_sessions():
    """Reset the in-memory session store between every test."""
    _reset_sessions_for_tests()
    yield
    _reset_sessions_for_tests()


@pytest.fixture
def fake_harness():
    """Override get_harness_client with a configurable fake. Returns the
    FakeMessages object so tests can append responses before triggering the run.
    """
    fake = FakeAnthropicClient.with_responses()  # empty; tests append

    def _override() -> HarnessClient:
        return HarnessClient(client=fake, default_model="claude-test", provider="anthropic")

    app.dependency_overrides[get_harness_client] = _override
    yield fake.messages
    app.dependency_overrides.pop(get_harness_client, None)


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    """Set up a tmp .claude/ tree with one command + one skill and point
    sessions._project_root at it."""
    cmds = tmp_path / ".claude" / "commands"
    skills = tmp_path / ".claude" / "skills" / "echo-skill"
    cmds.mkdir(parents=True)
    skills.mkdir(parents=True)
    (cmds / "echo.md").write_text(
        "---\ndescription: echo command\n---\n載入 **echo-skill** skill, echo back.\n",
        encoding="utf-8",
    )
    (skills / "SKILL.md").write_text(
        "---\nname: echo-skill\ndescription: echoes input\n---\n"
        "You are an echo bot. Repeat the user message back.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sessions_module, "_project_root", lambda: tmp_path)
    return tmp_path


def _override_user(user: dict):
    """Helper: swap the get_current_user dependency for one test."""
    app.dependency_overrides[get_current_user] = lambda: user


def _restore_default_user():
    """Restore conftest.py's _fake_current_user."""
    from tests.conftest import _fake_current_user
    app.dependency_overrides[get_current_user] = _fake_current_user


# ────────────────────────────────────────────────────────────────────────────
# Auth boundary — every endpoint behind get_current_user
# ────────────────────────────────────────────────────────────────────────────

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


class TestSessionsAuth:
    def test_create_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.post(SESSIONS_BASE, json={"title": "x"})
        assert resp.status_code == 401
        assert "Missing authorization token" in resp.json()["error"]["message"]

    def test_run_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.post(f"{SESSIONS_BASE}/abc/run", json={"command": "/triz"})
        assert resp.status_code == 401

    def test_get_without_token_returns_401(self, client_no_auth):
        resp = client_no_auth.get(f"{SESSIONS_BASE}/abc")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client_no_auth):
        bad = _make_token(_valid_payload(), secret="wrong-secret")
        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.jwt_secret = TEST_JWT_SECRET
            mock_settings.debug = False
            resp = client_no_auth.post(
                SESSIONS_BASE, json={"title": "x"},
                headers={"Authorization": f"Bearer {bad}"},
            )
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client_no_auth):
        payload = _valid_payload()
        payload["exp"] = int(time.time()) - 60
        token = _make_token(payload)
        with patch("app.middleware.auth.settings") as mock_settings:
            mock_settings.jwt_secret = TEST_JWT_SECRET
            mock_settings.debug = False
            resp = client_no_auth.post(
                SESSIONS_BASE, json={"title": "x"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401


# ────────────────────────────────────────────────────────────────────────────
# Pydantic validation
# ────────────────────────────────────────────────────────────────────────────

class TestRunValidation:
    def test_missing_command_returns_422(self, client):
        resp = client.post(f"{SESSIONS_BASE}/x/run", json={})
        assert resp.status_code == 422

    def test_invalid_max_iterations_returns_422(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/x/run",
            json={"command": "/triz", "max_iterations": 0},
        )
        assert resp.status_code == 422

    def test_invalid_max_tokens_returns_422(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/x/run",
            json={"command": "/triz", "max_tokens": 5_000_000},
        )
        assert resp.status_code == 422


# ────────────────────────────────────────────────────────────────────────────
# Create / Get session
# ────────────────────────────────────────────────────────────────────────────

class TestCreateSession:
    def test_returns_session_id(self, client):
        resp = client.post(SESSIONS_BASE, json={"title": "my session"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"].startswith("sess_")
        assert "created_at" in body

    def test_no_title_is_allowed(self, client):
        resp = client.post(SESSIONS_BASE, json={})
        assert resp.status_code == 200


class TestGetSession:
    def test_returns_full_record(self, client):
        sess = client.post(SESSIONS_BASE, json={"title": "abc"}).json()
        resp = client.get(f"{SESSIONS_BASE}/{sess['session_id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == sess["session_id"]
        assert body["title"] == "abc"
        assert body["runs"] == []

    def test_unknown_session_returns_404(self, client):
        resp = client.get(f"{SESSIONS_BASE}/sess_doesnotexist")
        assert resp.status_code == 404


class TestSessionIsolation:
    def test_other_users_session_returns_404(self, client):
        # User A (the default fake user) creates a session
        sess = client.post(SESSIONS_BASE, json={"title": "private"}).json()

        # Switch to user B and try to read it
        _override_user({"sub": "user-b", "email": "b@x", "role": "authenticated"})
        try:
            resp = client.get(f"{SESSIONS_BASE}/{sess['session_id']}")
            assert resp.status_code == 404
        finally:
            _restore_default_user()


# ────────────────────────────────────────────────────────────────────────────
# Run command
# ────────────────────────────────────────────────────────────────────────────

class TestRunCommandErrors:
    def test_unknown_session_returns_404(self, client):
        resp = client.post(
            f"{SESSIONS_BASE}/sess_nope/run",
            json={"command": "/triz"},
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["error"]["message"]

    def test_unknown_command_returns_404(self, client, fake_project, fake_harness):
        sess = client.post(SESSIONS_BASE, json={}).json()
        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/ghost"},
        )
        assert resp.status_code == 404
        assert "/ghost" in resp.json()["error"]["message"]

    def test_command_without_skill_ref_runs_inline(self, client, fake_project, fake_harness):
        """Resolver enhancement: a command without a `載入 **skill**` ref now
        runs in inline mode (command body becomes the system prompt) instead
        of returning 400."""
        inline_cmd = fake_project / ".claude" / "commands" / "status.md"
        inline_cmd.write_text(
            "---\ndescription: inline status\n---\n"
            "Read .triz-state.json and print a one-line summary.\n",
            encoding="utf-8",
        )
        fake_harness.responses.append(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        sess = client.post(SESSIONS_BASE, json={}).json()

        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/status"},
        )

        assert resp.status_code == 200
        # System prompt sent to the model should carry the inline command body
        sys_prompt = fake_harness.calls[0]["system"]
        assert "Command: status" in sys_prompt
        assert "Read .triz-state.json" in sys_prompt

    def test_unknown_skill_returns_404(self, client, fake_project, fake_harness):
        # Command points at a non-existent skill
        bad = fake_project / ".claude" / "commands" / "ghost.md"
        bad.write_text(
            "---\ndescription: g\n---\n載入 **does-not-exist** skill.\n",
            encoding="utf-8",
        )
        sess = client.post(SESSIONS_BASE, json={}).json()
        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/ghost"},
        )
        assert resp.status_code == 404
        assert "does-not-exist" in resp.json()["error"]["message"]

    def test_other_users_session_returns_404(self, client, fake_project, fake_harness):
        sess = client.post(SESSIONS_BASE, json={}).json()
        _override_user({"sub": "user-b", "email": "b@x", "role": "authenticated"})
        try:
            resp = client.post(
                f"{SESSIONS_BASE}/{sess['session_id']}/run",
                json={"command": "/echo"},
            )
            assert resp.status_code == 404
        finally:
            _restore_default_user()


class TestRunCommandHappyPath:
    def test_runs_agent_loop_and_returns_text(self, client, fake_project, fake_harness):
        # Single end_turn response — no tool use needed
        fake_harness.responses.append(
            FakeResponse(
                content=[FakeTextBlock(text="echoed: hello")],
                stop_reason="end_turn",
            )
        )
        sess = client.post(SESSIONS_BASE, json={"title": "echo test"}).json()

        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/echo", "user_message": "hello"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["final_text"] == "echoed: hello"
        assert body["iterations"] == 1
        assert body["tool_calls"] == 0
        assert body["stop_reason"] == "end_turn"

    def test_records_run_in_session_history(self, client, fake_project, fake_harness):
        fake_harness.responses.append(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        sess = client.post(SESSIONS_BASE, json={}).json()
        client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/echo"},
        )

        # GET should now show one run record
        resp = client.get(f"{SESSIONS_BASE}/{sess['session_id']}")
        body = resp.json()
        assert len(body["runs"]) == 1
        run = body["runs"][0]
        assert run["command"] == "/echo"
        assert run["iterations"] == 1
        assert run["stop_reason"] == "end_turn"

    def test_tool_use_loop_works(self, client, fake_project, fake_harness):
        # Simulate: model calls Read, gets result, then end_turn
        fake_harness.responses.append(
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        id="tu_1",
                        name="Glob",
                        input={"pattern": "*.md", "path": str(fake_project)},
                    ),
                ],
                stop_reason="tool_use",
            )
        )
        fake_harness.responses.append(
            FakeResponse(
                content=[FakeTextBlock(text="found 0 files")],
                stop_reason="end_turn",
            )
        )

        sess = client.post(SESSIONS_BASE, json={}).json()
        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/echo", "user_message": "list md files"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["iterations"] == 2
        assert body["tool_calls"] == 1
        assert body["stop_reason"] == "end_turn"

    def test_default_user_message_when_omitted(self, client, fake_project, fake_harness):
        fake_harness.responses.append(
            FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn")
        )
        sess = client.post(SESSIONS_BASE, json={}).json()

        resp = client.post(
            f"{SESSIONS_BASE}/{sess['session_id']}/run",
            json={"command": "/echo"},  # no user_message
        )

        assert resp.status_code == 200
        # First user message should be the default prompt mentioning the
        # command name (not empty), since `user_message` was omitted.
        first_call = fake_harness.calls[0]
        first_user_msg = first_call["messages"][0]
        assert first_user_msg["role"] == "user"
        assert "echo" in first_user_msg["content"]
        assert len(first_user_msg["content"]) > 5
