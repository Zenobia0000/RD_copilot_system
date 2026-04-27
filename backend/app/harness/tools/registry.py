"""ToolRegistry — collects Tool instances and exposes them for the agent loop."""

from __future__ import annotations

from typing import Any

from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.fs import GlobTool, ReadTool, WriteTool


class ToolRegistry:
    """Minimal registry: register by name, dispatch by name, expose schemas."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError(f"Tool {tool!r} has empty name")
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool {name!r} not registered")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def dispatch(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Run a tool by name. Catches handler exceptions and surfaces them."""
        try:
            tool = self.get(name)
        except KeyError as exc:
            return ToolResult(content=str(exc), is_error=True)

        try:
            return tool.run(**arguments)
        except TypeError as exc:
            return ToolResult(
                content=f"Error: bad arguments to {name}: {exc}",
                is_error=True,
            )
        except Exception as exc:  # noqa: BLE001 — surface to model, don't crash loop
            return ToolResult(
                content=f"Error in {name}: {type(exc).__name__}: {exc}",
                is_error=True,
            )

    def to_anthropic_schemas(self, only: list[str] | None = None) -> list[dict[str, Any]]:
        """Schemas in the shape Anthropic Messages API expects."""
        if only is None:
            tools = list(self._tools.values())
        else:
            missing = [n for n in only if n not in self._tools]
            if missing:
                raise KeyError(f"Tools not registered: {missing}")
            tools = [self._tools[n] for n in only]
        return [t.to_anthropic_schema() for t in tools]


def default_registry() -> ToolRegistry:
    """Registry pre-loaded with the fs tool subset (Read/Write/Glob)."""
    reg = ToolRegistry()
    reg.register(ReadTool())
    reg.register(WriteTool())
    reg.register(GlobTool())
    return reg
