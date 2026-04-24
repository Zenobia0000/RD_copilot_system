"""Tests for harness/tool_registry.py — tool registration, schema generation, dispatch."""

import pytest
from pydantic import BaseModel, Field

from app.harness.tool_registry import (
    TOOL_REGISTRY,
    ToolDefinition,
    dispatch_tool,
    get_mcp_specs,
    list_tools,
    register_tool,
)


# ---------------------------------------------------------------------------
# Fixtures: isolated registry state
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_registry():
    """Clear the registry before and after each test."""
    saved = dict(TOOL_REGISTRY)
    TOOL_REGISTRY.clear()
    yield
    TOOL_REGISTRY.clear()
    TOOL_REGISTRY.update(saved)


# ---------------------------------------------------------------------------
# Test: basic registration with Pydantic model
# ---------------------------------------------------------------------------


class AddInput(BaseModel):
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")


def test_register_with_pydantic_model():
    @register_tool("add", "Add two numbers", input_model=AddInput)
    def add(a: int, b: int) -> int:
        return a + b

    assert "add" in TOOL_REGISTRY
    tool = TOOL_REGISTRY["add"]
    assert tool.name == "add"
    assert tool.description == "Add two numbers"
    assert tool.fn is add

    # JSON Schema should come from Pydantic model
    schema = tool.input_schema
    assert schema["type"] == "object"
    assert "a" in schema["properties"]
    assert "b" in schema["properties"]
    assert schema["properties"]["a"]["type"] == "integer"


def test_register_without_model_infers_schema():
    @register_tool("greet", "Greet someone")
    def greet(name: str, loud: bool = False) -> str:
        return f"Hello {name}{'!' if loud else '.'}"

    schema = TOOL_REGISTRY["greet"].input_schema
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["loud"]["type"] == "boolean"
    assert schema["required"] == ["name"]


def test_register_with_tags():
    @register_tool("tagged", "A tagged tool", tags=["triz", "matrix"])
    def tagged() -> str:
        return "ok"

    assert TOOL_REGISTRY["tagged"].tags == ["triz", "matrix"]


# ---------------------------------------------------------------------------
# Test: dispatch
# ---------------------------------------------------------------------------


def test_dispatch_tool_calls_function():
    @register_tool("multiply", "Multiply two numbers")
    def multiply(x: int, y: int) -> int:
        return x * y

    result = dispatch_tool("multiply", {"x": 3, "y": 7})
    assert result == 21


def test_dispatch_unknown_tool_raises():
    with pytest.raises(ValueError, match="Unknown tool: nonexistent"):
        dispatch_tool("nonexistent", {})


# ---------------------------------------------------------------------------
# Test: listing and MCP spec generation
# ---------------------------------------------------------------------------


def test_list_tools_sorted():
    @register_tool("zebra", "Z tool")
    def z():
        return "z"

    @register_tool("alpha", "A tool")
    def a():
        return "a"

    tools = list_tools()
    assert [t.name for t in tools] == ["alpha", "zebra"]


def test_mcp_specs_format():
    @register_tool("test_tool", "A test tool", input_model=AddInput)
    def test_fn(a: int, b: int) -> int:
        return a + b

    specs = get_mcp_specs()
    assert len(specs) == 1
    spec = specs[0]
    assert spec["name"] == "test_tool"
    assert spec["description"] == "A test tool"
    assert "inputSchema" in spec
    assert spec["inputSchema"]["type"] == "object"


# ---------------------------------------------------------------------------
# Test: overwrite warning
# ---------------------------------------------------------------------------


def test_overwrite_logs_warning(caplog):
    @register_tool("dup", "First")
    def first():
        return 1

    with caplog.at_level("WARNING"):
        @register_tool("dup", "Second")
        def second():
            return 2

    assert "already registered" in caplog.text
    # Second registration should overwrite
    assert dispatch_tool("dup", {}) == 2


# ---------------------------------------------------------------------------
# Test: TRIZ KB tools registration (integration)
# ---------------------------------------------------------------------------


@pytest.fixture()
def _load_triz_tools():
    """Reload triz_kb_tools to re-execute @register_tool decorators."""
    import importlib

    import app.tools.triz_kb_tools as mod

    importlib.reload(mod)


def test_triz_kb_tools_register(_load_triz_tools):
    """Import triz_kb_tools and verify tools are registered."""
    assert "lookup_matrix" in TOOL_REGISTRY
    assert "build_triz_tc_context" in TOOL_REGISTRY
    assert "load_40_principles" in TOOL_REGISTRY
    assert "get_param_name" in TOOL_REGISTRY


def test_triz_kb_lookup_matrix_via_dispatch(_load_triz_tools):
    """Dispatch lookup_matrix through the registry."""
    result = dispatch_tool("lookup_matrix", {"improving": 6, "worsening": 14})
    assert isinstance(result, list)


def test_triz_kb_tool_mcp_spec_has_constraints(_load_triz_tools):
    """Verify that Pydantic field constraints appear in the MCP spec."""
    tool = TOOL_REGISTRY["lookup_matrix"]
    schema = tool.input_schema
    # Pydantic v2 uses 'minimum' for ge constraints
    improving_props = schema["properties"]["improving"]
    assert improving_props.get("minimum") == 1 or improving_props.get("exclusiveMinimum") == 0
