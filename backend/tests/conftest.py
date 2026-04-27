"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.auth import get_current_user

# A fake user payload returned by the overridden auth dependency in tests.
_FAKE_USER = {"sub": "test-user-id", "email": "test@example.com", "role": "authenticated"}


def _fake_current_user():
    """Bypass JWT validation in tests that don't care about auth."""
    return _FAKE_USER


@pytest.fixture()
def client():
    """Synchronous FastAPI test client with auth bypassed.

    Business-logic tests should use this fixture.  Auth-specific tests
    (test_auth.py) manage their own overrides and use a separate client.
    """
    app.dependency_overrides[get_current_user] = _fake_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def client_no_auth():
    """Test client WITHOUT the auth bypass — for testing auth itself."""
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def _reset_llm_client():
    """Reset the cached LLM client between tests so mocks take effect."""
    import app.agents.base as base_mod

    base_mod._anthropic_client = None
    base_mod._openai_compat_clients.clear()
    yield
    base_mod._anthropic_client = None
    base_mod._openai_compat_clients.clear()
