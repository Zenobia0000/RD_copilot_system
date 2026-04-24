"""Tests for global error handling (WP-1.1)."""


def test_health_returns_200(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_unknown_route_returns_404_with_error_format(client):
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]


def test_request_id_header_present(client):
    resp = client.get("/api/v1/health")
    assert "X-Request-ID" in resp.headers
    # Should be a 32-char hex UUID
    rid = resp.headers["X-Request-ID"]
    assert len(rid) == 32
    int(rid, 16)  # must be valid hex
