"""Tests for /api/v1/deliverables/* — KC and Risk JSON arrays."""

from __future__ import annotations

import textwrap

import pytest

from app.api import deliverables as deliverables_module


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    (tmp_path / "docs" / "engineering").mkdir(parents=True)
    monkeypatch.setattr(deliverables_module, "_project_root", lambda: tmp_path)
    return tmp_path


def _write(path, body):
    path.write_text(textwrap.dedent(body), encoding="utf-8")


# ────────────────────────────────────────────────────────────────────────────
# /deliverables/kcs
# ────────────────────────────────────────────────────────────────────────────

def test_kcs_returns_parsed_rows(client, fake_project):
    _write(fake_project / "docs" / "engineering" / "kc_list.md", """\
        # KC List

        | KC ID | 特徵 | 子系統 | 規格值 | 公差 | 來源 WI/ICD | 量測方法 | 等級 |
        |:------|:-----|:-------|:-------|:-----|:------------|:---------|:-----|
        | KC-001 | Air gap 同心度 | 馬達 | 1.0 mm | ≤ 0.02 mm | ICD-01, WI-04 | CMM | **Critical** |
        | KC-002 | Halbach 段磁化角度 | 馬達 | per Halbach | ±0.5° | WI-01, MC-01 | 磁通量測 | **Critical** |
        | KC-018 | 螺絲扭矩 | 結構 | 4 Nm | ±10% | ICD-04 | torque wrench | Minor |
    """)

    resp = client.get("/api/v1/deliverables/kcs")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    assert body[0]["id"] == "KC-001"
    assert body[0]["feature"] == "Air gap 同心度"
    assert body[0]["level"] == "Critical"  # bold stripped
    assert body[2]["level"] == "Minor"


def test_kcs_skips_non_kc_rows(client, fake_project):
    """Statistics tables (no KC ID) at the file's tail must not become entries."""
    _write(fake_project / "docs" / "engineering" / "kc_list.md", """\
        | KC ID | 特徵 | 子系統 | 規格值 | 公差 | 來源 WI/ICD | 量測方法 | 等級 |
        |:------|:-----|:-------|:-------|:-----|:------------|:---------|:-----|
        | KC-001 | foo | x | y | z | a | b | Critical |

        ## Stats

        | 等級 | 數量 |
        |:-----|:-----|
        | Critical | 17 |
    """)

    resp = client.get("/api/v1/deliverables/kcs")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == "KC-001"


def test_kcs_404_when_missing(client, fake_project):
    resp = client.get("/api/v1/deliverables/kcs")
    assert resp.status_code == 404


def test_kcs_500_when_no_table_found(client, fake_project):
    """File exists but contains no KC table → 500 (something is wrong)."""
    _write(fake_project / "docs" / "engineering" / "kc_list.md", """\
        # Empty file

        Just prose, no tables.
    """)
    resp = client.get("/api/v1/deliverables/kcs")
    assert resp.status_code == 500


# ────────────────────────────────────────────────────────────────────────────
# /deliverables/risks
# ────────────────────────────────────────────────────────────────────────────

def test_risks_returns_parsed_rows(client, fake_project):
    _write(fake_project / "docs" / "engineering" / "risk_register.md", """\
        # Risks

        | Risk ID | 風險描述 | 來源 | 影響域 | 可能性 | 衝擊度 | 緩解措施 | 負責 WI |
        |:--------|:---------|:-----|:-------|:-------|:-------|:---------|:--------|
        | **R-001** | Halbach 增益估計 | obs C-B002 | 馬達 | M | H | FEA 驗證 | WI-01 |
        | **R-002** | HPR50 噪音基準 | obs C-C002 | 噪音 | H | M | 實機測試 | WI-02 |
    """)

    resp = client.get("/api/v1/deliverables/risks")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["id"] == "R-001"  # ** stripped
    assert body[0]["probability"] == "M"
    assert body[0]["impact"] == "H"
    assert body[0]["owner_wi"] == "WI-01"


def test_risks_404_when_missing(client, fake_project):
    resp = client.get("/api/v1/deliverables/risks")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────────────────────────────────

def test_kcs_requires_auth(client_no_auth, fake_project):
    resp = client_no_auth.get("/api/v1/deliverables/kcs")
    assert resp.status_code == 401


def test_risks_requires_auth(client_no_auth, fake_project):
    resp = client_no_auth.get("/api/v1/deliverables/risks")
    assert resp.status_code == 401
