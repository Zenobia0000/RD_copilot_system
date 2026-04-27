"""Tool primitives — the surface an agent uses to act on the world.

Each tool exposes:
- a JSON-schema input contract (the model sees this)
- a synchronous handler that returns a ToolResult (the model reads this back)

Standard surface: fs (Read/Write/Glob) + web (WebFetch/WebSearch).
The Agent tool (subagent dispatcher) is opt-in via
`registry.default_registry_with_agent()`.
"""

from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.fs import GlobTool, ReadTool, WriteTool
from app.harness.tools.registry import ToolRegistry, default_registry
from app.harness.tools.web import WebFetchTool, WebSearchTool

__all__ = [
    "Tool",
    "ToolResult",
    "ReadTool",
    "WriteTool",
    "GlobTool",
    "WebFetchTool",
    "WebSearchTool",
    "ToolRegistry",
    "default_registry",
]
