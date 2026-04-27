"""Tool primitives — the surface an agent uses to act on the world.

Each tool exposes:
- a JSON-schema input contract (the model sees this)
- a synchronous handler that returns a ToolResult (the model reads this back)

Subset implemented for the /triz PoC: Read, Write, Glob.
"""

from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.fs import GlobTool, ReadTool, WriteTool
from app.harness.tools.registry import ToolRegistry, default_registry

__all__ = [
    "Tool",
    "ToolResult",
    "ReadTool",
    "WriteTool",
    "GlobTool",
    "ToolRegistry",
    "default_registry",
]
