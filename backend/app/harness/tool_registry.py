"""Tool Registry — @register_tool decorator with MCP spec generation.

Pattern adapted from Hermes Agent tool auto-registration:
- Decorator-based registration (aligned with evaluator_registry.py)
- JSON Schema auto-generation from Pydantic v2 models
- MCP Tool spec production for mcp_server.py

Usage:
    from app.harness.tool_registry import register_tool

    class MatrixLookupInput(BaseModel):
        improving: int
        worsening: int

    @register_tool("lookup_matrix", "Look up TRIZ contradiction matrix", input_model=MatrixLookupInput)
    def lookup_matrix(improving: int, worsening: int) -> list[int]:
        ...
"""

from __future__ import annotations

import inspect
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolDefinition:
    """Registered tool metadata + callable."""

    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema from Pydantic model
    fn: Callable
    tags: list[str] = field(default_factory=list)

    def to_mcp_spec(self) -> dict[str, Any]:
        """Produce an MCP-compatible tool specification."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    description: str,
    *,
    input_model: type[BaseModel] | None = None,
    tags: list[str] | None = None,
) -> Callable:
    """Decorator to register a function as a harness tool.

    If input_model is provided, its JSON Schema is used for the MCP spec.
    Otherwise, the schema is inferred from the function signature.

    Args:
        name: Unique tool name (used in MCP and agent tool calls).
        description: Human-readable description.
        input_model: Optional Pydantic model for input validation + schema.
        tags: Optional tags for categorization (e.g., ["triz", "knowledge"]).
    """

    def decorator(fn: Callable) -> Callable:
        if name in TOOL_REGISTRY:
            logger.warning("Tool '%s' already registered — overwriting", name)

        if input_model is not None:
            schema = input_model.model_json_schema()
        else:
            schema = _infer_schema_from_signature(fn)

        tool_def = ToolDefinition(
            name=name,
            description=description,
            input_schema=schema,
            fn=fn,
            tags=list(tags or []),
        )
        TOOL_REGISTRY[name] = tool_def
        logger.debug("Registered tool: %s", name)
        return fn

    return decorator


def dispatch_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Call a registered tool by name with the given arguments.

    Raises ValueError if the tool is not registered.
    """
    tool_def = TOOL_REGISTRY.get(name)
    if tool_def is None:
        raise ValueError(
            f"Unknown tool: {name}. "
            f"Registered: {set(TOOL_REGISTRY.keys())}"
        )
    return tool_def.fn(**arguments)


def list_tools() -> list[ToolDefinition]:
    """Return all registered tools (sorted by name)."""
    return sorted(TOOL_REGISTRY.values(), key=lambda t: t.name)


def get_mcp_specs() -> list[dict[str, Any]]:
    """Return MCP-compatible tool specs for all registered tools."""
    return [t.to_mcp_spec() for t in list_tools()]


# ---------------------------------------------------------------------------
# Schema inference from function signature (fallback)
# ---------------------------------------------------------------------------

_PY_TYPE_TO_JSON: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _infer_schema_from_signature(fn: Callable) -> dict[str, Any]:
    """Infer a JSON Schema from a function's type annotations.

    This is a simple fallback for tools that don't declare a Pydantic model.
    """
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        annotation = param.annotation
        json_type = _PY_TYPE_TO_JSON.get(annotation, "string")
        properties[param_name] = {"type": json_type}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema
