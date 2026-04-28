"""TRIZ session state manager — atomic read/write with schema validation.

Handles .triz-state.json and .tr-state.json lifecycle.
All writes go through this module to ensure consistency.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .state import (
    STEP_ORDER,
    PathType,
    StepName,
    TRState,
    TrizSession,
    next_step,
    step_completed,
)

STATE_FILENAME = ".triz-state.json"
TR_STATE_FILENAME = ".tr-state.json"


class StateError(RuntimeError):
    """Raised on invalid state transitions or corrupted state."""


class TrizStateManager:
    """Manages TRIZ session state with schema validation and atomic writes."""

    def __init__(self, session_dir: Path) -> None:
        self._dir = session_dir
        self._state_path = session_dir / STATE_FILENAME
        self._tr_state_path = session_dir / TR_STATE_FILENAME

    @property
    def session_dir(self) -> Path:
        return self._dir

    @property
    def state_path(self) -> Path:
        return self._state_path

    # ── TRIZ State ───────────────────────────────────────────────────

    def exists(self) -> bool:
        return self._state_path.exists()

    def load(self) -> TrizSession:
        """Load and validate .triz-state.json."""
        if not self._state_path.exists():
            raise StateError(f"State file not found: {self._state_path}")
        raw = self._state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return TrizSession.model_validate(data)

    def save(self, session: TrizSession) -> None:
        """Atomic write of .triz-state.json (write to tmp, then rename)."""
        self._dir.mkdir(parents=True, exist_ok=True)
        data = session.model_dump(mode="json")
        self._atomic_write(self._state_path, data)

    def create_session(
        self,
        session_id: str,
        problem_description: str,
        *,
        specs: dict | None = None,
        path: PathType = PathType.tc_main,
    ) -> TrizSession:
        """Create a new TRIZ session with initial state."""
        now = datetime.now(timezone.utc)
        report_file = f".claude/context/triz/session-{session_id}.md"
        session = TrizSession(
            session_id=session_id,
            created_at=now,
            current_step=StepName.step0,
            path=path,
            problem_description=problem_description,
            report_file=report_file,
            specs=specs or {},
        )
        self.save(session)
        return session

    def advance_step(self, session: TrizSession, to_step: StepName) -> TrizSession:
        """Advance current_step with guard rails.

        Rules:
        - Current step must be completed
        - Can only advance to the immediate next step (no skipping)
        - Exception: step2→step3 is treated as one unit (triz-contradict handles both)
        """
        current = StepName(session.current_step)

        if not step_completed(session, current):
            raise StateError(
                f"Cannot advance: {current.value} is not completed"
            )

        expected_next = next_step(current)
        if expected_next is None:
            raise StateError("Already at final step (step5)")

        # step2 and step3 are handled together by triz-contradict
        if to_step == StepName.step3 and current == StepName.step2:
            pass  # allow step2→step3 even if step2 just completed
        elif to_step != expected_next:
            raise StateError(
                f"Cannot skip from {current.value} to {to_step.value}; "
                f"expected {expected_next.value}"
            )

        session.current_step = to_step.value
        self.save(session)
        return session

    # ── TR State ─────────────────────────────────────────────────────

    def tr_state_exists(self) -> bool:
        return self._tr_state_path.exists()

    def load_tr_state(self) -> TRState:
        """Load and validate .tr-state.json."""
        if not self._tr_state_path.exists():
            raise StateError(f"TR state file not found: {self._tr_state_path}")
        raw = self._tr_state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return TRState.model_validate(data)

    def save_tr_state(self, tr_state: TRState) -> None:
        """Atomic write of .tr-state.json."""
        self._dir.mkdir(parents=True, exist_ok=True)
        data = tr_state.model_dump(mode="json")
        self._atomic_write(self._tr_state_path, data)

    def compute_triz_state_hash(self) -> str:
        """SHA-256 hash of .triz-state.json content for staleness detection."""
        if not self._state_path.exists():
            return ""
        content = self._state_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    # ── Helpers ──────────────────────────────────────────────────────

    def _atomic_write(self, path: Path, data: dict) -> None:
        """Write JSON atomically: write to temp file, then rename."""
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        # Write to temp file in same directory (same filesystem for rename)
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, suffix=".tmp", prefix=path.stem
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.write("\n")
            Path(tmp_path).replace(path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
