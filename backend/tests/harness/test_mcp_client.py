"""Tests for harness/mcp_client.py — MCP config parsing."""

import json

import pytest

from app.harness.mcp_client import (
    _MCP_SERVERS,
    McpServerConfig,
    get_mcp_server,
    list_mcp_servers,
    load_mcp_config,
)


@pytest.fixture(autouse=True)
def _clean_servers():
    saved = dict(_MCP_SERVERS)
    _MCP_SERVERS.clear()
    yield
    _MCP_SERVERS.clear()
    _MCP_SERVERS.update(saved)


def test_load_nonexistent_config(tmp_path):
    result = load_mcp_config(tmp_path / "missing.json")
    assert result == {}


def test_load_valid_config(tmp_path):
    config = {
        "mcpServers": {
            "tavily": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "tavily-mcp"],
                "env": {"TAVILY_API_KEY": "test-key"},
            },
            "my_sse_server": {
                "transport": "sse",
                "url": "http://localhost:3000/sse",
            },
        }
    }
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config))

    servers = load_mcp_config(config_path)
    assert len(servers) == 2

    tavily = servers["tavily"]
    assert tavily.transport == "stdio"
    assert tavily.command == "npx"
    assert tavily.args == ["-y", "tavily-mcp"]
    assert tavily.env == {"TAVILY_API_KEY": "test-key"}

    sse = servers["my_sse_server"]
    assert sse.transport == "sse"
    assert sse.url == "http://localhost:3000/sse"


def test_load_invalid_json(tmp_path):
    config_path = tmp_path / ".mcp.json"
    config_path.write_text("not valid json {{{")

    result = load_mcp_config(config_path)
    assert result == {}


def test_list_mcp_servers(tmp_path):
    config = {
        "mcpServers": {
            "beta_server": {"command": "beta"},
            "alpha_server": {"command": "alpha"},
        }
    }
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config))

    load_mcp_config(config_path)
    servers = list_mcp_servers()
    assert [s.name for s in servers] == ["alpha_server", "beta_server"]


def test_get_mcp_server(tmp_path):
    config = {
        "mcpServers": {
            "test_server": {"command": "test", "transport": "stdio"},
        }
    }
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config))

    load_mcp_config(config_path)
    server = get_mcp_server("test_server")
    assert server is not None
    assert server.command == "test"

    assert get_mcp_server("nonexistent") is None


def test_empty_mcp_servers(tmp_path):
    config = {"mcpServers": {}}
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config))

    servers = load_mcp_config(config_path)
    assert servers == {}
