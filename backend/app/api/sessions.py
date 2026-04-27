"""Sessions API — placeholder shape, P3 wires it to the harness AgentLoop.

The endpoint surface is locked in here so the auth pattern, request/response
shape, and OpenAPI doc are all reviewable now. Every handler returns 501 until
P3 connects it to AgentLoop.run().

Designed surface:
- POST   /sessions               create a session, return its id
- POST   /sessions/{id}/run      run a slash-command in the session, return final text
- GET    /sessions/{id}/events   stream loop events as SSE (B milestone)
- GET    /sessions/{id}          fetch session state (current step, transcript path)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(get_current_user)],
)

_NOT_IMPLEMENTED_DETAIL = "Sessions API stub — wired in P3 (see ROADMAP)"


class CreateSessionRequest(BaseModel):
    """Future shape: client picks the workflow root, harness owns the rest."""

    title: str | None = Field(default=None, description="Optional human-readable label.")


class CreateSessionResponse(BaseModel):
    session_id: str


class RunCommandRequest(BaseModel):
    """Mirrors the CLI: a slash-command + free-form user message."""

    command: str = Field(description='Slash command, e.g. "/triz" or "/triz-scope"')
    user_message: str = Field(default="", description="User input forwarded to the agent.")
    max_iterations: int = Field(default=20, ge=1, le=100)
    max_tokens: int = Field(default=8000, ge=256, le=128000)


class RunCommandResponse(BaseModel):
    final_text: str
    iterations: int
    tool_calls: int
    stop_reason: str


@router.post("", response_model=CreateSessionResponse)
async def create_session(_req: CreateSessionRequest) -> CreateSessionResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=_NOT_IMPLEMENTED_DETAIL,
    )


@router.post("/{session_id}/run", response_model=RunCommandResponse)
async def run_command(session_id: str, _req: RunCommandRequest) -> RunCommandResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=_NOT_IMPLEMENTED_DETAIL,
    )


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=_NOT_IMPLEMENTED_DETAIL,
    )
