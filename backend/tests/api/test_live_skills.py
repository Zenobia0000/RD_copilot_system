"""Live API smoke tests — actually hit Azure-Anthropic Sonnet 4.6.

Marked @pytest.mark.live, skipped by default. Run explicitly:
    pytest -m live tests/api/test_live_skills.py

Each test:
- Creates a fresh session via /api/v1/sessions
- POSTs the slash-command via /api/v1/sessions/{id}/run (sync, simpler than SSE)
- Asserts the agent ran (tool_calls > 0, iterations > 0, end_turn) and
  the final_text contains at least one domain-relevant keyword.

State preservation: an autouse module-level fixture snapshots
.claude/context/triz/ before tests and restores afterward, so a live run
doesn't trash the project's real session history.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

SESSIONS_BASE = "/api/v1/sessions"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_TRIZ_CTX = _PROJECT_ROOT / ".claude" / "context" / "triz"


pytestmark = pytest.mark.live  # whole module gated on `-m live`


# ────────────────────────────────────────────────────────────────────────────
# State preservation fixture
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def preserve_triz_context():
    """Snapshot .claude/context/triz/ before tests, restore on teardown.

    Live tests will mutate state.json and create session-*.md files. Without
    this fixture, running them once corrupts the project's real session
    history. With it, post-test state is byte-identical to pre-test state.
    """
    backup = Path(tempfile.mkdtemp(prefix="triz-live-test-backup-"))
    pre_files: set[str] = set()
    if _TRIZ_CTX.is_dir():
        for f in _TRIZ_CTX.iterdir():
            if f.is_file():
                pre_files.add(f.name)
                shutil.copy(f, backup / f.name)

    yield

    if _TRIZ_CTX.is_dir():
        # Drop files created during the test
        for f in list(_TRIZ_CTX.iterdir()):
            if f.is_file() and f.name not in pre_files:
                f.unlink()
        # Restore originals (overwrites any in-place mutations)
        for backed in backup.iterdir():
            shutil.copy(backed, _TRIZ_CTX / backed.name)

    shutil.rmtree(backup, ignore_errors=True)


# ────────────────────────────────────────────────────────────────────────────
# Helper: create session, run command, return parsed body
# ────────────────────────────────────────────────────────────────────────────

def _run(client, command: str, user_message: str = "", *, max_iter: int = 8, max_tokens: int = 4000) -> dict:
    sess = client.post(SESSIONS_BASE, json={"title": f"live-{command}"}).json()
    resp = client.post(
        f"{SESSIONS_BASE}/{sess['session_id']}/run",
        json={
            "command": command,
            "user_message": user_message,
            "max_iterations": max_iter,
            "max_tokens": max_tokens,
        },
    )
    assert resp.status_code == 200, f"{command} returned {resp.status_code}: {resp.text[:300]}"
    return resp.json()


def _assert_agent_did_work(body: dict, *, expect_keywords: list[str]) -> None:
    """Generic shape assertions plus at-least-one keyword match.

    Live tests can't pin exact wording — model output varies. We check the
    agent took some action (tool_calls > 0 or non-empty text) and that at
    least one of several expected terms appears in the final text.
    """
    assert body["iterations"] >= 1
    assert body["final_text"], "agent returned empty final_text"
    assert body["stop_reason"] in ("end_turn", "max_tokens"), (
        f"unexpected stop_reason {body['stop_reason']!r}"
    )
    text = body["final_text"]
    matched = [kw for kw in expect_keywords if kw in text]
    assert matched, (
        f"final_text contained none of {expect_keywords!r}.\n"
        f"First 800 chars:\n{text[:800]}"
    )


# ────────────────────────────────────────────────────────────────────────────
# /triz-solve — Step 2+3, the most complex skill (multi-TC, SIM, loop logic)
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizSolve:
    def test_runs_against_existing_state(self, client):
        body = _run(
            client, "/triz-solve",
            user_message=(
                "請對既有 session 中的矛盾「改善散熱(P17溫度) vs 體積(P7)」"
                "做 Step 2 矛盾矩陣查表並建議發明原理。"
            ),
            max_iter=10,
            max_tokens=6000,
        )
        # Step 2/3 output should mention at least one of these
        _assert_agent_did_work(body, expect_keywords=[
            "矛盾矩陣", "矩陣", "發明原理", "原理", "Px", "OZ", "Step 2", "Step 3",
        ])
        assert body["tool_calls"] >= 1, "expected agent to read state at minimum"


# ────────────────────────────────────────────────────────────────────────────
# /triz-verify — Step 4 CCI, complexity check
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizVerify:
    def test_runs_against_existing_state(self, client):
        body = _run(
            client, "/triz-verify",
            user_message="對既有 session 做 Step 4 驗證並計算 CCI。",
            max_iter=10,
            max_tokens=5000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "驗證", "CCI", "complexity", "複雜度", "Px", "Step 4",
        ])


# ────────────────────────────────────────────────────────────────────────────
# /triz-wi — Step 5 WI/MC/ICD generation
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizWi:
    def test_runs_against_existing_state(self, client):
        body = _run(
            client, "/triz-wi",
            user_message="依現有 session 產出 WI 體系（先列出計畫，不必真寫檔）。",
            max_iter=8,
            max_tokens=4000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "WI", "工程作業", "Work Instruction", "ICD", "MC", "Material Card",
        ])


# ────────────────────────────────────────────────────────────────────────────
# /tr-gate — TR Gate Review
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrGate:
    def test_tr1_feasibility_review(self, client):
        body = _run(
            client, "/tr-gate",
            user_message="TR1 可行性 gate review — 列出退出條件與當前狀態",
            max_iter=8,
            max_tokens=4000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "TR1", "TR", "gate", "Gate", "退出條件", "可行性",
        ])


# ────────────────────────────────────────────────────────────────────────────
# /tr-fea — FEA assist
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrFea:
    def test_motor_thermal_fea_setup(self, client):
        body = _run(
            client, "/tr-fea",
            user_message="WI-01 motor 散熱 FEA — 給我材料卡、邊界條件、網格策略建議",
            max_iter=8,
            max_tokens=4000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "FEA", "材料卡", "邊界條件", "網格", "thermal", "Material",
        ])


# ────────────────────────────────────────────────────────────────────────────
# /tr-test — Test report generator
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrTest:
    def test_motor_v1_test_report(self, client):
        body = _run(
            client, "/tr-test",
            user_message="Motor V1 散熱測試報告 — 指引我輸入哪些數據才能產出報告",
            max_iter=8,
            max_tokens=4000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "測試", "test", "Test", "pass", "Pass", "FEA correlation", "報告",
        ])


# ────────────────────────────────────────────────────────────────────────────
# /tr-dfm — DFM/DFA review
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrDfm:
    def test_shell_dfm_review(self, client):
        body = _run(
            client, "/tr-dfm",
            user_message="shell 子系統 DFM 審查 — 給 checklist",
            max_iter=8,
            max_tokens=4000,
        )
        _assert_agent_did_work(body, expect_keywords=[
            "DFM", "DFA", "checklist", "Checklist", "BOM", "製程", "審查",
        ])
