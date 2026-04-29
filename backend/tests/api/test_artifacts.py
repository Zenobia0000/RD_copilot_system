"""Tests for /api/v1/artifacts/* — file streaming + path traversal defence."""

from __future__ import annotations

import pytest

from app.api import artifacts as artifacts_module


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    """Build a tmp project tree with engineering artifacts under docs/."""
    eng = tmp_path / "docs" / "engineering"
    (eng / "work_instructions").mkdir(parents=True)
    (eng / "work_instructions" / "WI-01.md").write_text(
        "# WI-01\n\nHalbach motor work instruction.\n", encoding="utf-8"
    )
    (eng / "secret.bin").write_bytes(b"\xff\xfe\x00\x01binary\xc3\x28")
    # A sibling file outside engineering/ — must be unreachable
    (tmp_path / "docs" / "secrets.txt").write_text("nope", encoding="utf-8")
    monkeypatch.setattr(artifacts_module, "_project_root", lambda: tmp_path)
    return tmp_path


# ────────────────────────────────────────────────────────────────────────────
# Happy path
# ────────────────────────────────────────────────────────────────────────────

def test_get_artifact_returns_file(client, fake_project):
    resp = client.get("/api/v1/artifacts/work_instructions/WI-01.md")

    assert resp.status_code == 200
    assert "WI-01" in resp.text


def test_get_artifact_raw_returns_plain_text(client, fake_project):
    resp = client.get("/api/v1/artifacts/work_instructions/WI-01.md/raw")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "Halbach motor" in resp.text


def test_get_artifact_raw_rejects_non_utf8(client, fake_project):
    resp = client.get("/api/v1/artifacts/secret.bin/raw")
    assert resp.status_code == 415


# ────────────────────────────────────────────────────────────────────────────
# Path traversal defence
# ────────────────────────────────────────────────────────────────────────────

def test_traversal_dotdot_rejected(client, fake_project):
    resp = client.get("/api/v1/artifacts/..%2Fsecrets.txt")
    # FastAPI normalises %2F; either way we must not return the sibling file
    assert resp.status_code in (400, 403, 404)
    assert "nope" not in resp.text


def test_traversal_explicit_dotdot_rejected(client, fake_project):
    resp = client.get("/api/v1/artifacts/../secrets.txt")
    assert resp.status_code in (400, 403, 404)
    assert "nope" not in resp.text


def test_missing_artifact_returns_404(client, fake_project):
    resp = client.get("/api/v1/artifacts/work_instructions/WI-99.md")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────────────────────────────────

def test_artifacts_require_auth(client_no_auth, fake_project):
    resp = client_no_auth.get("/api/v1/artifacts/work_instructions/WI-01.md")
    assert resp.status_code == 401
