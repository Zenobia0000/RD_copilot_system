"""Tests for TRIZ state models and state manager."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.triz.state import (
    CCIScores,
    CCIVerdict,
    FAEntry,
    FAType,
    PathType,
    SFEntry,
    SFStatus,
    Step0State,
    Step1State,
    StepName,
    TrizSession,
    next_step,
    step_completed,
)
from app.triz.state_manager import StateError, TrizStateManager


# ── TrizSession model tests ─────────────────────────────────────────

class TestTrizSession:
    def test_minimal_session(self):
        session = TrizSession(
            session_id="test-session",
            created_at=datetime.now(timezone.utc),
            current_step=StepName.step0,
            path=PathType.tc_main,
            problem_description="test problem",
            report_file="test.md",
        )
        assert session.session_id == "test-session"
        assert session.current_step == "step0"
        assert session.step0.completed is False

    def test_roundtrip_json(self):
        session = TrizSession(
            session_id="roundtrip",
            created_at=datetime(2026, 4, 28, tzinfo=timezone.utc),
            current_step=StepName.step1,
            path=PathType.multi_tc,
            problem_description="ebike drive unit",
            report_file="report.md",
            specs={"max_od_mm": 111},
        )
        session.step0 = Step0State(completed=True, routing="step1")

        data = session.model_dump(mode="json")
        restored = TrizSession.model_validate(data)
        assert restored.session_id == "roundtrip"
        assert restored.step0.completed is True
        assert restored.specs["max_od_mm"] == 111

    def test_fa_entry_types(self):
        entry = FAEntry(
            source="Motor", function="generates torque", target="Gearbox",
            type=FAType.useful,
        )
        assert entry.type == "useful"

    def test_sf_entry(self):
        entry = SFEntry(
            id="SF1", s1="Motor coil", f="thermal", s2="Shell",
            status=SFStatus.harmful, tc="TC4",
        )
        assert entry.status == "harmful"

    def test_cci_scores_validation(self):
        scores = CCIScores(
            structural=0.50, energy=0.00, cognitive=0.50,
            evolution_aligned=0.33, cci=0.33,
        )
        assert scores.cci == 0.33

        with pytest.raises(Exception):
            CCIScores(structural=1.5, energy=0, cognitive=0, evolution_aligned=0, cci=0)


# ── Step navigation tests ───────────────────────────────────────────

class TestStepNavigation:
    def test_next_step(self):
        assert next_step(StepName.step0) == StepName.step1
        assert next_step(StepName.step4) == StepName.step5
        assert next_step(StepName.step5) is None

    def test_step_completed(self):
        session = TrizSession(
            session_id="test", created_at=datetime.now(timezone.utc),
            current_step=StepName.step0, path=PathType.tc_main,
            problem_description="test", report_file="t.md",
        )
        assert step_completed(session, StepName.step0) is False
        session.step0.completed = True
        assert step_completed(session, StepName.step0) is True


# ── State Manager tests ─────────────────────────────────────────────

class TestStateManager:
    @pytest.fixture
    def tmp_dir(self, tmp_path):
        return tmp_path / "triz_session"

    @pytest.fixture
    def mgr(self, tmp_dir):
        return TrizStateManager(tmp_dir)

    def test_create_and_load(self, mgr):
        session = mgr.create_session("test-001", "test problem", specs={"x": 1})
        assert session.session_id == "test-001"
        assert mgr.exists()

        loaded = mgr.load()
        assert loaded.session_id == "test-001"
        assert loaded.specs["x"] == 1

    def test_save_atomic(self, mgr, tmp_dir):
        session = mgr.create_session("atomic-test", "test")
        session.step0.completed = True
        mgr.save(session)

        loaded = mgr.load()
        assert loaded.step0.completed is True

    def test_advance_step_success(self, mgr):
        session = mgr.create_session("advance-test", "test")
        session.step0.completed = True
        mgr.save(session)

        session = mgr.advance_step(session, StepName.step1)
        assert session.current_step == "step1"

    def test_advance_step_not_completed(self, mgr):
        session = mgr.create_session("fail-test", "test")
        with pytest.raises(StateError, match="not completed"):
            mgr.advance_step(session, StepName.step1)

    def test_advance_step_skip_not_allowed(self, mgr):
        session = mgr.create_session("skip-test", "test")
        session.step0.completed = True
        mgr.save(session)
        with pytest.raises(StateError, match="Cannot skip"):
            mgr.advance_step(session, StepName.step3)

    def test_load_nonexistent(self, mgr):
        with pytest.raises(StateError, match="not found"):
            mgr.load()

    def test_compute_hash(self, mgr):
        session = mgr.create_session("hash-test", "test")
        hash1 = mgr.compute_triz_state_hash()
        assert len(hash1) == 64  # SHA-256 hex

        session.step0.completed = True
        mgr.save(session)
        hash2 = mgr.compute_triz_state_hash()
        assert hash1 != hash2

    def test_load_existing_ebike_state(self):
        """Test that we can load the actual ebike session state file."""
        state_path = (
            Path(__file__).resolve().parents[3]
            / ".claude" / "context" / "triz"
        )
        if not (state_path / ".triz-state.json").exists():
            pytest.skip("No ebike session state file")

        mgr = TrizStateManager(state_path)
        session = mgr.load()
        assert session.session_id  # non-empty
        assert session.problem_description  # non-empty
