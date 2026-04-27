"""Sessions API — wires HTTP requests into the harness AgentLoop.

State model (PoC): in-memory `_SESSIONS` dict, scoped by user `sub`. Cross-user
access returns 404 (not 403) so existence isn't leaked. A future iteration
moves this to Supabase if we need cross-process / multi-instance sessions.

Project root + Anthropic client are resolved once per process via lru_cache.
The harness client is exposed as a FastAPI dependency so tests can override it
with a fake without re-stubbing `lru_cache`.

The run endpoint is sync (`def`, not `async def`) — FastAPI executes sync
handlers in its threadpool, which is the right home for AgentLoop's blocking
HTTP calls. An `async def` handler that called AgentLoop directly would block
the event loop.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.harness.agent import AgentLoop, AgentLoopError
from app.harness.cli import build_system_prompt, find_project_root
from app.harness.command import CommandParseError, load_command
from app.harness.config import HarnessClient, HarnessConfigError, build_client, load_env
from app.harness.skill import SkillParseError, load_skill
from app.harness.tools.registry import default_registry
from app.middleware.auth import get_current_user


# ────────────────────────────────────────────────────────────────────────────
# Process-singleton helpers
# ────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _project_root() -> Path:
    """Resolved once per process from the uvicorn cwd."""
    return find_project_root()


@lru_cache(maxsize=1)
def _harness_client_singleton() -> HarnessClient:
    """Build the HarnessClient once. .env is loaded from the project root."""
    load_env(_project_root() / ".env")
    return build_client()


def get_harness_client() -> HarnessClient:
    """FastAPI dependency. Override in tests via `app.dependency_overrides`."""
    return _harness_client_singleton()


# ────────────────────────────────────────────────────────────────────────────
# In-memory session store
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class SessionRecord:
    session_id: str
    user_id: str
    title: str | None
    created_at: str
    runs: list[dict[str, Any]] = field(default_factory=list)


_SESSIONS: dict[str, SessionRecord] = {}
_SESSIONS_LOCK = threading.Lock()


def _new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:16]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_session_for_user(session_id: str, user_id: str) -> SessionRecord:
    """Fetch a session, enforcing ownership. Foreign sessions look like 404."""
    with _SESSIONS_LOCK:
        record = _SESSIONS.get(session_id)
    if record is None or record.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        )
    return record


def _reset_sessions_for_tests() -> None:
    """Test helper. Not part of the public API."""
    with _SESSIONS_LOCK:
        _SESSIONS.clear()


# ────────────────────────────────────────────────────────────────────────────
# Request / response models
# ────────────────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, description="Optional human-readable label.")


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str


class RunCommandRequest(BaseModel):
    command: str = Field(description='Slash command, e.g. "/triz" or "/triz-scope"')
    user_message: str = Field(default="", description="User input forwarded to the agent.")
    max_iterations: int = Field(default=20, ge=1, le=100)
    max_tokens: int = Field(default=8000, ge=256, le=128000)


class RunRecord(BaseModel):
    command: str
    ran_at: str
    iterations: int
    tool_calls: int
    stop_reason: str


class RunCommandResponse(BaseModel):
    final_text: str
    iterations: int
    tool_calls: int
    stop_reason: str


class GetSessionResponse(BaseModel):
    session_id: str
    title: str | None
    created_at: str
    runs: list[RunRecord]


# ────────────────────────────────────────────────────────────────────────────
# Router
# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CreateSessionResponse)
def create_session(
    req: CreateSessionRequest,
    user: dict = Depends(get_current_user),
) -> CreateSessionResponse:
    record = SessionRecord(
        session_id=_new_session_id(),
        user_id=user["sub"],
        title=req.title,
        created_at=_now_iso(),
    )
    with _SESSIONS_LOCK:
        _SESSIONS[record.session_id] = record
    return CreateSessionResponse(session_id=record.session_id, created_at=record.created_at)


@router.get("/{session_id}", response_model=GetSessionResponse)
def get_session(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> GetSessionResponse:
    record = _get_session_for_user(session_id, user["sub"])
    return GetSessionResponse(
        session_id=record.session_id,
        title=record.title,
        created_at=record.created_at,
        runs=[RunRecord(**r) for r in record.runs],
    )


@router.post("/{session_id}/run", response_model=RunCommandResponse)
def run_command(
    session_id: str,
    req: RunCommandRequest,
    user: dict = Depends(get_current_user),
    harness: HarnessClient = Depends(get_harness_client),
) -> RunCommandResponse:
    record = _get_session_for_user(session_id, user["sub"])

    # Resolve command → skill (mirrors the CLI; both speak the same convention)
    try:
        project_root = _project_root()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    cmd_name = req.command.lstrip("/")
    try:
        command = load_command(project_root / ".claude" / "commands", cmd_name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"command /{cmd_name} not found",
        )
    except CommandParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"malformed command /{cmd_name}: {exc}",
        )

    if command.referenced_skill is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"command /{cmd_name} has no `載入 **<skill>** skill` reference",
        )

    try:
        skill = load_skill(project_root / ".claude" / "skills", command.referenced_skill)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"skill {command.referenced_skill!r} (referenced by /{cmd_name}) not found"
            ),
        )
    except SkillParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"malformed skill {command.referenced_skill!r}: {exc}",
        )

    # Compose + run
    system_prompt = build_system_prompt(
        project_root=project_root,
        skill_name=skill.name,
        skill_body=skill.body,
    )
    user_message = req.user_message or (
        f"請依 {skill.name} skill 的步驟引導我，先告訴我下一步要做什麼。"
    )

    loop = AgentLoop(
        client=harness.client,
        model=harness.default_model,
        system_prompt=system_prompt,
        tool_registry=default_registry(),
        allowed_tools=list(skill.allowed_tools) if skill.allowed_tools is not None else None,
        max_iterations=req.max_iterations,
        max_tokens=req.max_tokens,
    )

    try:
        result = loop.run(user_message)
    except AgentLoopError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"agent loop failed: {exc}",
        )

    # Append to session history (best-effort; failure shouldn't 500 the response)
    with _SESSIONS_LOCK:
        record.runs.append(
            {
                "command": req.command,
                "ran_at": _now_iso(),
                "iterations": result.iterations,
                "tool_calls": result.tool_calls,
                "stop_reason": result.stop_reason,
            }
        )

    return RunCommandResponse(
        final_text=result.final_text,
        iterations=result.iterations,
        tool_calls=result.tool_calls,
        stop_reason=result.stop_reason,
    )
