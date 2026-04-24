"""TRIZ Knowledge Base — tool registrations for MCP exposure.

Registers triz_kb.py functions as harness tools so they can be
called via MCP by Claude Code or other MCP clients.

This module is imported by mcp_server.py at startup.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.harness.tool_registry import register_tool
from app.tools.triz_kb import (
    build_sufield_context,
    build_triz_pc_context,
    build_triz_tc_context,
    get_matrix_context,
    get_param_name,
    load_39_parameters,
    load_40_principles,
    load_76_standard_solutions,
    load_separation_principles,
    lookup_matrix,
)


# ---------------------------------------------------------------------------
# Pydantic input models for schema generation
# ---------------------------------------------------------------------------


class MatrixLookupInput(BaseModel):
    improving: int = Field(..., ge=1, le=39, description="Improving parameter number (1-39)")
    worsening: int = Field(..., ge=1, le=39, description="Worsening parameter number (1-39)")


class ParamNameInput(BaseModel):
    num: int = Field(..., ge=1, le=39, description="TRIZ parameter number (1-39)")


class SuFieldContextInput(BaseModel):
    system_state: str | None = Field(
        None,
        description="Su-Field system state: incomplete|harmful|insufficient|effective|measurement|simplify",
    )


# ---------------------------------------------------------------------------
# Tool registrations
# ---------------------------------------------------------------------------


@register_tool(
    "lookup_matrix",
    "Look up the TRIZ contradiction matrix for improving/worsening parameter pair. "
    "Returns a list of candidate inventive principle numbers.",
    input_model=MatrixLookupInput,
    tags=["triz", "matrix"],
)
def _lookup_matrix(improving: int, worsening: int) -> list[int]:
    return lookup_matrix(improving, worsening)


@register_tool(
    "get_matrix_context",
    "Get human-readable context string for a TRIZ matrix lookup result.",
    input_model=MatrixLookupInput,
    tags=["triz", "matrix"],
)
def _get_matrix_context(improving: int, worsening: int) -> str:
    return get_matrix_context(improving, worsening)


@register_tool(
    "build_triz_tc_context",
    "Build full prompt context for Technical Contradiction resolution. "
    "Includes 39 parameters + relevant matrix row + filtered 40 principles.",
    input_model=MatrixLookupInput,
    tags=["triz", "tc"],
)
def _build_triz_tc_context(improving: int, worsening: int) -> str:
    return build_triz_tc_context(improving, worsening)


@register_tool(
    "build_triz_pc_context",
    "Build prompt context for Physical Contradiction resolution (separation principles).",
    tags=["triz", "pc"],
)
def _build_triz_pc_context() -> str:
    return build_triz_pc_context()


@register_tool(
    "build_sufield_context",
    "Build prompt context for Su-Field analysis (76 standard solutions). "
    "Optionally filter by system state for token efficiency.",
    input_model=SuFieldContextInput,
    tags=["triz", "sufield"],
)
def _build_sufield_context(system_state: str | None = None) -> str:
    return build_sufield_context(system_state)


@register_tool(
    "get_param_name",
    "Return the Chinese parameter name for a TRIZ 39 parameter number.",
    input_model=ParamNameInput,
    tags=["triz", "parameters"],
)
def _get_param_name(num: int) -> str:
    return get_param_name(num)


@register_tool(
    "load_39_parameters",
    "Load full text of TRIZ 39 engineering parameters (~1,500 tokens).",
    tags=["triz", "knowledge"],
)
def _load_39_parameters() -> str:
    return load_39_parameters()


@register_tool(
    "load_40_principles",
    "Load full text of TRIZ 40 inventive principles (~4,000 tokens).",
    tags=["triz", "knowledge"],
)
def _load_40_principles() -> str:
    return load_40_principles()


@register_tool(
    "load_separation_principles",
    "Load full text of TRIZ separation principles (~1,000 tokens).",
    tags=["triz", "knowledge"],
)
def _load_separation_principles() -> str:
    return load_separation_principles()


@register_tool(
    "load_76_standard_solutions",
    "Load full text of TRIZ 76 standard solutions.",
    tags=["triz", "knowledge"],
)
def _load_76_standard_solutions() -> str:
    return load_76_standard_solutions()
