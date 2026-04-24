"""MCP Client — consumes external MCP tools from .mcp.json configuration.

Reads .mcp.json from the project root and registers external MCP server
tools into the tool_registry as mcp__<server>__<tool>.

Supports:
- stdio transport (subprocess-based MCP servers)
- SSE transport (HTTP SSE-based MCP servers)

Usage:
    from app.harness.mcp_client import load_mcp_config, list_mcp_servers

    config = load_mcp_config()  # Reads .mcp.json
    servers = list_mcp_servers()

Note: Actual MCP client connections require the `mcp` SDK and are
established lazily when a tool is first called. This module handles
configuration parsing and tool registration scaffolding.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Project root .mcp.json (same level as .env)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MCP_CONFIG_PATH = _PROJECT_ROOT / ".mcp.json"


@dataclass
class McpServerConfig:
    """Parsed configuration for a single MCP server."""
    name: str
    transport: Literal["stdio", "sse"] = "stdio"
    command: str = ""
    args: list[str] = field(default_factory=list)
    url: str = ""  # For SSE transport
    env: dict[str, str] = field(default_factory=dict)


_MCP_SERVERS: dict[str, McpServerConfig] = {}


def load_mcp_config(config_path: Path | None = None) -> dict[str, McpServerConfig]:
    """Load and parse .mcp.json configuration.

    Returns:
        Dict of server_name -> McpServerConfig.
    """
    path = config_path or _MCP_CONFIG_PATH
    if not path.exists():
        logger.debug("No .mcp.json found at %s — no external MCP servers", path)
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to parse .mcp.json: %s", exc)
        return {}

    servers: dict[str, McpServerConfig] = {}
    mcp_servers = raw.get("mcpServers", {})

    for name, spec in mcp_servers.items():
        if not isinstance(spec, dict):
            logger.warning("Skipping invalid MCP server spec for '%s'", name)
            continue

        transport = spec.get("transport", "stdio")
        config = McpServerConfig(
            name=name,
            transport=transport,
            command=spec.get("command", ""),
            args=spec.get("args", []),
            url=spec.get("url", ""),
            env=spec.get("env", {}),
        )
        servers[name] = config
        logger.info(
            "MCP server configured: '%s' (transport=%s, command=%s)",
            name, transport, config.command or config.url,
        )

    _MCP_SERVERS.clear()
    _MCP_SERVERS.update(servers)
    return servers


def list_mcp_servers() -> list[McpServerConfig]:
    """Return all configured MCP servers."""
    return sorted(_MCP_SERVERS.values(), key=lambda s: s.name)


def get_mcp_server(name: str) -> McpServerConfig | None:
    """Get a specific MCP server configuration by name."""
    return _MCP_SERVERS.get(name)
