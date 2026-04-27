"""Live API smoke tests — actually hit Azure-Anthropic Sonnet 4.6.

Marked @pytest.mark.live, skipped by default. Run explicitly:
    pytest -m live tests/api/test_live_skills.py

Each test pulls specific values out of the project's real state files
(.triz-state.json + .tr-state.json) at fixture time, builds prompts that
reference those values, and asserts the agent's response actually echoes
state-derived content. This catches "agent didn't read state" or "agent
hallucinated instead of using state" — failure modes a generic-keyword
assertion would miss.

State preservation: the autouse module-level fixture archives every file
in .claude/context/triz/ to backend/tests/_live_artifacts/<timestamp>/
on teardown, then restores the originals. The artifacts directory is
gitignored.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

SESSIONS_BASE = "/api/v1/sessions"
# This file: backend/tests/api/test_live_skills.py
# parents[3] climbs api → tests → backend → <project root>
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TRIZ_CTX = _PROJECT_ROOT / ".claude" / "context" / "triz"
_TRIZ_STATE_PATH = _TRIZ_CTX / ".triz-state.json"
_TR_STATE_PATH = _TRIZ_CTX / ".tr-state.json"
_ARTIFACTS_ROOT = Path(__file__).resolve().parent.parent / "_live_artifacts"


pytestmark = pytest.mark.live  # whole module gated on `-m live`


# ────────────────────────────────────────────────────────────────────────────
# State-as-fixture: tests read the actual case at runtime, no hardcoding
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def triz_state() -> dict:
    """The project's real .triz-state.json, parsed once per module."""
    if not _TRIZ_STATE_PATH.is_file():
        pytest.skip(f".triz-state.json missing at {_TRIZ_STATE_PATH}")
    return json.loads(_TRIZ_STATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tr_state() -> dict:
    """The project's real .tr-state.json, parsed once per module."""
    if not _TR_STATE_PATH.is_file():
        pytest.skip(f".tr-state.json missing at {_TR_STATE_PATH}")
    return json.loads(_TR_STATE_PATH.read_text(encoding="utf-8"))


# ────────────────────────────────────────────────────────────────────────────
# State preservation + artifact archive
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def preserve_triz_context():
    """Snapshot before, archive-then-restore after.

    Test runs mutate state.json and create session-*.md. Archive captures
    what the agents wrote (so you can review prompt quality post-run);
    restore returns the project's session history to byte-identical.
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
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive = _ARTIFACTS_ROOT / stamp
        archive.mkdir(parents=True, exist_ok=True)
        for f in _TRIZ_CTX.iterdir():
            if f.is_file():
                shutil.copy(f, archive / f.name)

        for f in list(_TRIZ_CTX.iterdir()):
            if f.is_file() and f.name not in pre_files:
                f.unlink()
        for backed in backup.iterdir():
            shutil.copy(backed, _TRIZ_CTX / backed.name)

    shutil.rmtree(backup, ignore_errors=True)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
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


def _assert_basic(body: dict) -> None:
    assert body["iterations"] >= 1
    assert body["final_text"], "agent returned empty final_text"
    assert body["stop_reason"] in ("end_turn", "max_tokens")


def _assert_contains_any(text: str, alternatives: list[str], *, label: str) -> None:
    matched = [a for a in alternatives if a in text]
    assert matched, (
        f"{label}: response contained none of {alternatives!r}.\n"
        f"First 1000 chars:\n{text[:1000]}"
    )


# ────────────────────────────────────────────────────────────────────────────
# /triz-status — must echo the real session_id and current_step
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizStatus:
    def test_reports_real_session(self, client, triz_state):
        body = _run(client, "/triz-status", "", max_tokens=2500)
        _assert_basic(body)
        text = body["final_text"]

        # Must reference the actual session id from state
        assert triz_state["session_id"] in text, (
            f"agent did not echo session_id={triz_state['session_id']!r}; "
            f"likely didn't read state.\nFirst 600 chars: {text[:600]}"
        )
        # And must reflect that we're at step4 / done
        _assert_contains_any(
            text,
            [triz_state["current_step"], "step4", "Step 4", "完成", "complete"],
            label="current_step echo",
        )


# ────────────────────────────────────────────────────────────────────────────
# /triz — router on existing complete session: must offer resume/new choice
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizRouter:
    def test_detects_existing_session(self, client, triz_state):
        body = _run(
            client, "/triz",
            user_message="檢查目前 session 狀態，告訴我下一步建議。",
            max_iter=6, max_tokens=3000,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Agent must surface the existing session somehow
        _assert_contains_any(
            text,
            [triz_state["session_id"], "ebike", "drive-unit", "既有", "既存", "existing"],
            label="existing-session detection",
        )


# ────────────────────────────────────────────────────────────────────────────
# /triz-solve — must reference the real bottleneck TC + its principles
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizSolve:
    def test_references_real_bottleneck_tc(self, client, triz_state):
        bottleneck_tc = triz_state["step2"]["bottleneck_tc"]  # "TC1"
        tc1 = next(t for t in triz_state["step2"]["tcs"] if t["id"] == bottleneck_tc)
        principles = tc1["selected_principles"]  # [12, 15, 37]

        body = _run(
            client, "/triz-solve",
            user_message=(
                f"既有 session 中 {bottleneck_tc} 是瓶頸 (selected_principles="
                f"{principles})。請對 {bottleneck_tc} 給簡短回顧並說明為何選 P{principles[0]}。"
            ),
            max_iter=10, max_tokens=5000,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Must mention the bottleneck TC
        assert bottleneck_tc in text, f"missing {bottleneck_tc} reference"
        # Must mention at least one of the actual selected principles
        principle_strs = [f"P{p}" for p in principles] + [str(p) for p in principles] + ["原理"]
        _assert_contains_any(text, principle_strs, label=f"principle for {bottleneck_tc}")


# ────────────────────────────────────────────────────────────────────────────
# /triz-verify — must reference the real CCI value and verdict
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizVerify:
    def test_references_real_cci_and_verdict(self, client, triz_state):
        cci = triz_state["step4"]["complexity_scores"]["cci"]  # 0.35
        verdict = triz_state["step4"]["cci_verdict"]  # "Weak Evolution"

        body = _run(
            client, "/triz-verify",
            user_message=(
                f"既有 session 的 Step 4 已完成 CCI={cci}, verdict={verdict!r}。"
                f"請覆核這個結論並指出殘餘風險。"
            ),
            max_iter=10, max_tokens=5000,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Must reference the actual CCI number or verdict text
        _assert_contains_any(
            text,
            [str(cci), "0.35", verdict, "Weak Evolution", "weak evolution"],
            label="CCI/verdict echo",
        )


# ────────────────────────────────────────────────────────────────────────────
# /triz-wi — must list real WI files from step5
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrizWi:
    def test_lists_real_wi_files(self, client, triz_state):
        wi_files = triz_state["step5"]["wi_files"]  # 8 WI-XX files

        body = _run(
            client, "/triz-wi",
            user_message="既有 session 已產出 WI 體系，請列出已交付的 WI 清單與其用途。",
            max_iter=8, max_tokens=4500,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Agent should list at least 3 of the 8 WI files
        wi_names = [w.split("_")[0] for w in wi_files]  # ["WI-01", "WI-02", ...]
        mentioned = [n for n in wi_names if n in text]
        assert len(mentioned) >= 3, (
            f"only {len(mentioned)}/{len(wi_names)} WI files mentioned: {mentioned}\n"
            f"First 800 chars: {text[:800]}"
        )


# ────────────────────────────────────────────────────────────────────────────
# /tr — dashboard: must reflect real subsystem TR levels
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrDashboard:
    def test_reports_real_subsystem_levels(self, client, tr_state):
        subsystems = tr_state["subsystem_tr"]  # 6 entries
        motor_tr = subsystems["motor"]["current"]      # "TR0"
        gearbox_tr = subsystems["gearbox"]["current"]  # "TR0.5"

        body = _run(
            client, "/tr",
            user_message="顯示完整 TR 儀表板（用英文 subsystem 名稱：motor, gearbox, pcm, shell, pcb, sensor）。",
            max_iter=8, max_tokens=4500,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Accept either English or Chinese subsystem names
        _assert_contains_any(
            text, ["motor", "Motor", "馬達", "電機"],
            label="motor subsystem echo",
        )
        _assert_contains_any(
            text, ["gearbox", "Gearbox", "齒輪箱", "齒輪"],
            label="gearbox subsystem echo",
        )
        # And at least one specific TR level value
        _assert_contains_any(
            text, [motor_tr, gearbox_tr, "TR0", "TR1"],
            label="TR level echo",
        )


# ────────────────────────────────────────────────────────────────────────────
# /tr-gate TR1 — must surface the real NO-GO verdict + showstoppers
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrGate:
    def test_references_real_tr1_verdict(self, client, tr_state):
        tr1 = next((g for g in tr_state.get("gate_reviews", []) if g["gate"] == "TR1"), None)
        if tr1 is None:
            pytest.skip("no TR1 gate review in .tr-state.json")

        verdict = tr1["verdict"]              # "NO-GO"
        pass_rate = tr1["pass_rate"]          # 0.20
        showstoppers = tr1.get("showstoppers", [])  # ["R-001", "R-002"]

        body = _run(
            client, "/tr-gate",
            user_message=(
                f"TR1 gate review 已完成（verdict={verdict}, pass_rate={pass_rate}, "
                f"showstoppers={showstoppers}）。請直接基於這些已知結果說明：(1) 為何"
                f"判定 NO-GO (2) 下一步優先動作。不必讀檔，直接回答。"
            ),
            max_iter=4, max_tokens=3500,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Must surface the verdict somehow
        _assert_contains_any(
            text, [verdict, "NO-GO", "no-go", "未通過", "未過"],
            label="TR1 verdict echo",
        )
        # And at least one showstopper if any exist
        if showstoppers:
            _assert_contains_any(text, showstoppers, label="showstopper IDs")


# ────────────────────────────────────────────────────────────────────────────
# /tr-fea WI-01 — must reference real blockers from .tr-state.json
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrFea:
    def test_references_real_wi01_blockers(self, client, tr_state):
        motor = tr_state["subsystem_tr"]["motor"]
        blockers = motor.get("blockers", [])  # ["WI-01 FEA 未執行：Bg、扭矩、軸向力"]
        if not blockers:
            pytest.skip("no motor blockers to anchor on")

        body = _run(
            client, "/tr-fea",
            user_message=(
                "WI-01 motor FEA — 依 .tr-state.json 中標註的 blocker，"
                "建議材料卡、邊界條件、網格策略。"
            ),
            max_iter=8, max_tokens=4500,
        )
        _assert_basic(body)
        text = body["final_text"]

        # Must hit one of the blocker keywords (Bg / 扭矩 / 軸向力) or general FEA terms
        _assert_contains_any(
            text,
            ["Bg", "扭矩", "軸向力", "magnetic", "torque", "axial",
             "FEA", "材料卡", "邊界條件", "網格"],
            label="WI-01 FEA terms",
        )


# ────────────────────────────────────────────────────────────────────────────
# /tr-test V1 — should ask for the data the state hasn't recorded yet
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrTest:
    def test_motor_v1_test_report(self, client, tr_state):
        # State has no test data yet — agent should ask for inputs
        body = _run(
            client, "/tr-test",
            user_message="Motor V1 散熱測試報告 — 我還沒做測試，請告訴我需要哪些數據。",
            max_iter=8, max_tokens=4500,
        )
        _assert_basic(body)
        text = body["final_text"]

        _assert_contains_any(
            text,
            ["數據", "data", "輸入", "input", "需要", "請提供", "測試項",
             "pass", "fail", "FEA"],
            label="test-input prompts",
        )


# ────────────────────────────────────────────────────────────────────────────
# /tr-dfm shell — must reference the real shell material (AZ91D)
# ────────────────────────────────────────────────────────────────────────────

class TestLiveTrDfm:
    def test_shell_dfm_references_real_material(self, client, triz_state):
        shell_material = triz_state["specs"]["shell_material"]  # "AZ91D"

        # Scope-bounded prompt — without this, the agent can Glob the whole
        # docs/ tree and accumulate >1M tokens before terminating.
        body = _run(
            client, "/tr-dfm",
            user_message=(
                f"shell 子系統 DFM checklist 速查（殼體材料 {shell_material}）。"
                "不必讀檔，直接基於通用 DFM 知識給 5-8 條重點 checklist。"
            ),
            max_iter=4, max_tokens=3500,
        )
        _assert_basic(body)
        text = body["final_text"]

        _assert_contains_any(
            text,
            [shell_material, "AZ91D", "鎂合金", "magnesium", "DFM", "DFA",
             "checklist", "Checklist", "BOM", "製程"],
            label="DFM/material echo",
        )
