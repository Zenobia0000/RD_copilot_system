"""Tests for request_id middleware (WP-1.1)."""

import uuid


def test_request_id_is_valid_uuid_hex(client):
    """Each request should get a unique UUID request ID."""
    resp1 = client.get("/api/v1/health")
    resp2 = client.get("/api/v1/health")

    rid1 = resp1.headers["X-Request-ID"]
    rid2 = resp2.headers["X-Request-ID"]

    # Both should be valid hex UUIDs
    assert len(rid1) == 32
    assert len(rid2) == 32

    # They should be different
    assert rid1 != rid2


def test_request_id_context_variable():
    """get_request_id() returns None outside a request."""
    from app.middleware.request_id import get_request_id
    assert get_request_id() is None
