"""MCP Server — exposes registered tools as MCP endpoints.

Supports stdio transport (default) for Claude Code integration.
Lists and dispatches tools from tool_registry.TOOL_REGISTRY.

Usage:
    # Start as stdio server (for Claude Code):
    python -m app.harness.mcp_server

    # Register with Claude Code:
    claude mcp add design-copilot stdio -- python -m app.harness.mcp_server
"""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP("Design Copilot")


def _register_tools_with_mcp() -> None:
    """Register all harness tools with the MCP server.

    Called at module load time to expose tools before the server starts.
    Must be called AFTER tool_registry tools are registered (import order matters).
    """
    from app.harness.tool_registry import TOOL_REGISTRY, dispatch_tool

    for tool_name, tool_def in TOOL_REGISTRY.items():
        # Create a closure to capture tool_name for each iteration
        def _make_handler(name: str, definition):
            async def handler(**kwargs) -> str:
                """MCP tool handler — dispatches to registered tool function."""
                try:
                    result = definition.fn(**kwargs)
                    # Serialize the result for MCP
                    if isinstance(result, (dict, list)):
                        return json.dumps(result, ensure_ascii=False)
                    return str(result)
                except Exception as exc:
                    logger.error("Tool '%s' failed: %s", name, exc)
                    raise

            # Set function metadata for FastMCP
            handler.__name__ = name
            handler.__doc__ = definition.description

            return handler

        handler = _make_handler(tool_name, tool_def)

        # Register with FastMCP using the tool's schema
        mcp.tool(
            name=tool_def.name,
            description=tool_def.description,
        )(handler)

    logger.info("Registered %d tools with MCP server", len(TOOL_REGISTRY))


def _ensure_triz_kb_tools_loaded() -> None:
    """Import the TRIZ KB tools module to trigger @register_tool decorators."""
    try:
        import app.tools.triz_kb_tools  # noqa: F401
    except ImportError:
        logger.warning(
            "triz_kb_tools not found — TRIZ KB tools will not be available via MCP"
        )


def run_stdio() -> None:
    """Start the MCP server with stdio transport."""
    _ensure_triz_kb_tools_loaded()
    _register_tools_with_mcp()
    logger.info("Starting MCP stdio server with %d tools", len(mcp._tool_manager._tools) if hasattr(mcp, '_tool_manager') else 0)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
