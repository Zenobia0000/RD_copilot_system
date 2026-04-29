"""Tests for /api/v1/triz/* — state JSON read endpoints."""

from __future__ import annotations

import json

import pytest

from app.api import state as state_module


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    """Build a tmp project tree with .claude/ + docs/engineering/ skeletons.

    Returns the project root path. Tests populate state files as needed.
    """
    (tmp_path / ".claude" / "context" / "triz").mkdir(parents=True)
    (tmp_path / "docs" / "engineering").mkdir(parents=True)
    monkeypatch.setattr(state_module, "_project_root", lambda: tmp_path)
    return tmp_path


def _minimal_triz_state(**overrides) -> dict:
    """A payload that satisfies TrizSession's required fields."""
    base = {
        "session_id": "test-session",
        "created_at": "2026-04-28T15:00:00+00:00",
        "current_step": "step5",
        "path": "tc-main",
        "problem_description": "test problem",
        "report_file": ".claude/context/triz/session-test.md",
    }
    base.update(overrides)
    return base


def _minimal_tr_state(**overrides) -> dict:
    base = {
        "project_id": "test-project",
        "created_at": "2026-04-28T16:00:00+00:00",
        "triz_session_ref": "test-session",
    }
    base.update(overrides)
    return base


def _write_triz_state(root, payload):
    (root / ".claude" / "context" / "triz" / ".triz-state.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_tr_state(root, payload):
    (root / ".claude" / "context" / "triz" / ".tr-state.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# ────────────────────────────────────────────────────────────────────────────
# /triz/state
# ────────────────────────────────────────────────────────────────────────────

def test_get_triz_state_returns_validated_session(client, fake_project):
    payload = _minimal_triz_state(
        step5={"completed": True, "total_files": 22, "kc_list_file": "kc_list.md"},
        preliminary_tcs=["TC-A: x vs y", "TC-B: a vs b"],
    )
    _write_triz_state(fake_project, payload)

    resp = client.get("/api/v1/triz/state")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == "test-session"
    assert body["step5"]["completed"] is True
    assert body["step5"]["total_files"] == 22
    # plain-string preliminary_tcs flow through (list[TCBrief | str])
    assert body["preliminary_tcs"] == ["TC-A: x vs y", "TC-B: a vs b"]


def test_get_triz_state_accepts_real_ebike_shape(client, fake_project):
    """Integration-style: feed in the actual v3 ebike payload to make sure
    permissive schema doesn't regress on the production structure."""
    payload = _minimal_triz_state(
        path="tc-main",
        current_step="step5",
        preliminary_tcs=[
            "TC-A: 散熱(P17) vs 體積(P8)",
            "TC-B: 功率密度(P21) vs 重量(P1)",
            "TC-C: 噪音(P31) vs 複雜度(P36)",
        ],
        step3={
            "completed": True,
            "solutions_count": 3,
            "sim": {"iteration": 1, "verdict": "CONVERGED", "synergies_count": 2},
        },
        step4={
            "completed": True,
            "verdict": "evolution",
            "complexity_scores": {"structural": 0.5, "energy": 0.25, "cognitive": 0.5,
                                  "evolution_aligned": 0.0, "cci": 0.3125},
            "cci_verdict": "Weak Evolution",
            "evidence_registry_stats": {"high": 6, "medium": 4, "low": 2, "total": 12},
        },
    )
    _write_triz_state(fake_project, payload)

    resp = client.get("/api/v1/triz/state")

    assert resp.status_code == 200
    body = resp.json()
    assert body["step3"]["solutions_count"] == 3
    assert body["step4"]["cci_verdict"] == "Weak Evolution"
    assert body["step4"]["complexity_scores"]["cci"] == 0.3125


def test_get_triz_state_404_when_missing(client, fake_project):
    resp = client.get("/api/v1/triz/state")
    assert resp.status_code == 404
    assert "triz-state" in resp.json()["error"]["message"]


def test_get_triz_state_500_on_corrupt(client, fake_project):
    (fake_project / ".claude" / "context" / "triz" / ".triz-state.json").write_text(
        "{not valid json", encoding="utf-8"
    )

    resp = client.get("/api/v1/triz/state")
    assert resp.status_code == 500
    assert "corrupt" in resp.json()["error"]["message"]


def test_get_triz_state_500_on_schema_mismatch(client, fake_project):
    """A payload missing required fields fails Pydantic validation."""
    _write_triz_state(fake_project, {"session_id": "incomplete"})

    resp = client.get("/api/v1/triz/state")
    assert resp.status_code == 500
    assert "schema mismatch" in resp.json()["error"]["message"] or "error" in resp.json()["error"]["message"]


def test_get_triz_state_requires_auth(client_no_auth, fake_project):
    _write_triz_state(fake_project, _minimal_triz_state())
    resp = client_no_auth.get("/api/v1/triz/state")
    assert resp.status_code == 401


# ────────────────────────────────────────────────────────────────────────────
# /triz/tr-state
# ────────────────────────────────────────────────────────────────────────────

def test_get_tr_state_returns_validated(client, fake_project):
    payload = _minimal_tr_state(
        current_tr="TR0",
        next_target="TR1",
        tr_gates={
            "TR0": {"name": "概念凍結", "status": "completed",
                    "completed_at": "2026-04-28T16:00:00+00:00"},
            "TR1": {"name": "可行性分析", "status": "pending",
                    "blocking_risks": ["R-001", "R-002"]},
        },
        subsystems={
            "halbach_motor": {"current_tr": "TR0", "next_target": "TR1", "wi": "WI-01"},
        },
        deliverable_counts={"wi": 7, "icd": 4, "mc": 6, "framework": 4, "kc_list": 1, "total": 22},
    )
    _write_tr_state(fake_project, payload)

    resp = client.get("/api/v1/triz/tr-state")

    assert resp.status_code == 200
    body = resp.json()
    assert body["current_tr"] == "TR0"
    assert body["subsystems"]["halbach_motor"]["wi"] == "WI-01"
    assert body["tr_gates"]["TR1"]["blocking_risks"] == ["R-001", "R-002"]
    assert body["deliverable_counts"]["total"] == 22


def test_get_tr_state_404_when_missing(client, fake_project):
    resp = client.get("/api/v1/triz/tr-state")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# /triz/manifest
# ────────────────────────────────────────────────────────────────────────────

def test_get_manifest_auto_initialises_when_missing(client, fake_project):
    """BundleManager.load_or_create() means missing MANIFEST.json is OK —
    the endpoint returns an empty manifest skeleton, not 404."""
    resp = client.get("/api/v1/triz/manifest")

    assert resp.status_code == 200
    body = resp.json()
    assert body["bundle_version"] == 0
    assert body["artifacts"] == {}


def test_get_manifest_returns_existing(client, fake_project):
    manifest_path = fake_project / "docs" / "engineering" / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps({
            "bundle_id": "test-bundle",
            "bundle_version": 5,
            "created_at": "2026-04-28T00:00:00+00:00",
            "updated_at": "2026-04-28T00:00:00+00:00",
            "source": {"triz_session": "s1"},
            "artifacts": {
                "work_instructions": [{
                    "path": "WI-01.md",
                    "category": "work_instructions",
                    "sha256": "a" * 64,
                    "produced_by": "triz-wi",
                    "registered_at": "2026-04-28T00:00:00+00:00",
                    "version": 1,
                }],
            },
            "statistics": {"work_instructions": 1, "total": 1},
        }),
        encoding="utf-8",
    )

    resp = client.get("/api/v1/triz/manifest")

    assert resp.status_code == 200
    body = resp.json()
    assert body["bundle_id"] == "test-bundle"
    assert body["bundle_version"] == 5
    assert len(body["artifacts"]["work_instructions"]) == 1
