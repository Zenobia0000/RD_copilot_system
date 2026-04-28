"""ToolRegistry — collects Tool instances and exposes them for the agent loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from anthropic import Anthropic

from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.bash import BashTool
from app.harness.tools.fs import EditTool, GlobTool, GrepTool, ReadTool, WriteTool
from app.harness.tools.web import WebFetchTool, WebSearchTool


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
    """Registry pre-loaded with the standard tool surface:
    Read / Write / Glob (fs) + WebFetch / WebSearch (web).

    These are the tools available to subagents by default. Per-agent
    whitelisting (in `.claude/agents/*.md` frontmatter `tools:`) narrows the
    surface for any specific subagent.

    Note: this registry deliberately omits the Agent tool itself. Use
    `default_registry_with_agent()` for the main loop, and pass `default_registry`
    itself as the sub_registry_factory so subagents can't recurse.

    WebSearch is registered unconditionally — at run() time it returns
    is_error if tavily-python or TAVILY_API_KEY is missing, so the agent
    knows to skip web verification rather than crashing the loop.
    """
    reg = ToolRegistry()
    reg.register(ReadTool())
    reg.register(WriteTool())
    reg.register(EditTool())
    reg.register(GlobTool())
    reg.register(GrepTool())
    reg.register(BashTool())
    reg.register(WebFetchTool())
    reg.register(WebSearchTool())
    return reg


def default_registry_with_agent(
    *,
    client: Anthropic,
    default_model: str,
    agents_root: Path,
    sub_registry_factory: Callable[[], "ToolRegistry"] | None = None,
) -> ToolRegistry:
    """Main-loop registry: fs tools + the Agent tool for spawning subagents.

    Args:
        client: Anthropic client used by sub-loops.
        default_model: Model fallback when an agent definition omits `model`.
        agents_root: Directory containing `.claude/agents/<name>.md`.
        sub_registry_factory: Factory for sub-loop registries. Defaults to
            `default_registry` (fs tools, no Agent — nested spawn forbidden).
            Override only if subagents need a different tool surface.
    """
    # Late import to keep registry.py free of agent-specific deps at module
    # load time (and to avoid the import cycle agent.py ↔ tools/agent.py).
    from app.harness.tools.agent import AgentTool, AgentToolConfig

    factory = sub_registry_factory or default_registry

    reg = default_registry()
    reg.register(
        AgentTool(
            AgentToolConfig(
                client=client,
                default_model=default_model,
                agents_root=agents_root,
                sub_registry_factory=factory,
            )
        )
    )
    return reg


def default_registry_with_triz(
    *,
    client: Anthropic,
    default_model: str,
    agents_root: Path,
    kb_root: Path,
    state_dir: Path,
    artifact_categories: list[str] | None = None,
    sub_registry_factory: Callable[[], "ToolRegistry"] | None = None,
) -> ToolRegistry:
    """Main-loop registry with TRIZ domain tools: fs + web + bash + agent + TRIZ.

    Use this for TRIZ/TR commands. Non-TRIZ commands use
    ``default_registry_with_agent`` (no domain tools).

    Args:
        client: Anthropic client for sub-loops.
        default_model: Fallback model.
        agents_root: .claude/agents/ directory.
        kb_root: knowledge/triz/ directory.
        state_dir: .claude/context/triz/ directory.
        artifact_categories: Valid categories for ArtifactBundle.
            If None, uses built-in defaults.
        sub_registry_factory: Factory for sub-loop registries.
    """
    from app.triz.registry import triz_tools

    reg = default_registry_with_agent(
        client=client,
        default_model=default_model,
        agents_root=agents_root,
        sub_registry_factory=sub_registry_factory,
    )
    for tool in triz_tools(
        kb_root=kb_root,
        state_dir=state_dir,
        artifact_categories=artifact_categories,
    ):
        reg.register(tool)
    return reg
