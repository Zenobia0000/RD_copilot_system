"""Harness — agent orchestration spine for Design Copilot.

Provides:
- HarnessAgent[Deps, Output]: typed agent with structured output (Phase 2b)
- harness_call(): one-shot convenience for LLM calls (Phase 2c)
- Tool Registry: @register_tool with MCP spec generation (Phase 1)
- Solver Registry: @register_solver for pluggable solvers (Phase 3)
- Skill Loader: filesystem-based skill discovery (Phase 4)
- MCP Server: exposes tools to Claude Code via FastMCP (Phase 1)
- MCP Client: consumes external MCP tools from .mcp.json (Phase 5)
- Orchestrator: L1→critic→L2→L3 pipeline coordinator (Phase 3)
- Model Adapter: wraps existing multi-provider LLM dispatch (Phase 2a)
- Prompt Assembler: context engineering with cache + budget (Phase 2a)

Ref: ADR-006, E5x--harness-refactor-plan.md
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

DepsT = TypeVar("DepsT")
OutputT = TypeVar("OutputT", bound=BaseModel)


@runtime_checkable
class HarnessAgentProtocol(Protocol[DepsT, OutputT]):
    """Marker Protocol for harness-managed agents."""

    @property
    def name(self) -> str: ...

    def run_sync(self, user_message: str, *, deps: DepsT | None = None) -> OutputT: ...


__all__ = [
    "HarnessAgentProtocol",
    "DepsT",
    "OutputT",
]
