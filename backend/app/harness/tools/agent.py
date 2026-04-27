"""Agent tool — main loop calls this to spawn a custom subagent.

Wraps a `.claude/agents/<name>.md` definition into a Tool. When the model
decides to dispatch the Agent tool, this handler:

1. Loads the agent definition from disk (name, description, model, tools, body)
2. Builds a fresh sub-AgentLoop with:
   - Its own (independent) ToolRegistry — created via the injected factory
   - The agent's body as system prompt
   - The agent's tools whitelist (or inherit-all if absent)
   - The agent's model override (or default if absent)
3. Runs the sub-loop with the user's prompt
4. Returns the sub-loop's final_text as the tool_result content

Design contracts:
- The injected registry factory MUST NOT include the Agent tool itself —
  Claude Code does not support nested subagent spawning (DK-03 §3.6). If the
  factory includes Agent, sub-loops could recurse indefinitely.
- The handler is synchronous — true wall-clock parallelism across multiple
  Agent calls in one turn is a future upgrade (registry-level
  ThreadPoolExecutor or async dispatch). For now, multiple Agent dispatches
  in one tool_use turn run sequentially but each is fully isolated (separate
  context window, separate registry).
- Sub-loop failures (invalid agent name, sub-loop error) surface as
  is_error=True ToolResult, not Python exceptions — the loop must keep the
  main agent informed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, ClassVar

from anthropic import Anthropic

from app.harness.agents import AgentParseError, load_agent
from app.harness.tools.base import Tool, ToolResult
from app.harness.tools.registry import ToolRegistry


@dataclass(frozen=True)
class AgentToolConfig:
    """Host-injected configuration for the Agent tool.

    Fields:
        client: Anthropic SDK client to use for sub-loops. Same client is
            fine — sub-calls are independent at the API level.
        default_model: Model to use when the agent definition omits `model`.
        agents_root: Directory containing `.claude/agents/<name>.md`.
        sub_registry_factory: Callable returning a fresh ToolRegistry for
            each sub-loop. MUST NOT include the Agent tool (would enable
            nested spawn). Typical: a function that builds default fs tools.
        max_iterations: Max iterations for sub-loops. Defaults to 20 (same
            as main loop default).
        max_tokens: Max tokens per sub-loop response. Defaults to 16000.
    """

    client: Anthropic
    default_model: str
    agents_root: Path
    sub_registry_factory: Callable[[], ToolRegistry]
    max_iterations: int = 20
    max_tokens: int = 16000


class AgentTool(Tool):
    """The Agent tool — spawns a custom subagent.

    To register, instantiate with an AgentToolConfig and add to the main
    ToolRegistry. The model will see this tool and learn to dispatch when
    its description matches a problem shape requiring a specialised worker.
    """

    name: ClassVar[str] = "Agent"
    description: ClassVar[str] = (
        "Spawn a specialised subagent defined in .claude/agents/. Use this "
        "when a task is independent enough to be handled in isolation (e.g. "
        "one-of-many parallel workers in a fan-out). The subagent runs in "
        "its own context window with its own tool whitelist, and returns a "
        "summary of its work. You cannot communicate with the subagent "
        "after dispatch — it returns only when complete."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "description": (
                    "Name of the subagent (file stem under .claude/agents/, "
                    "e.g. 'triz-analyst'). Must match an existing definition."
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "The user message / instruction to give the subagent. "
                    "Should be self-contained — the subagent has no access "
                    "to the main conversation history."
                ),
            },
        },
        "required": ["agent", "prompt"],
    }

    def __init__(self, config: AgentToolConfig) -> None:
        self._config = config

    def run(self, *, agent: str, prompt: str) -> ToolResult:
        # Load agent definition.
        try:
            agent_def = load_agent(self._config.agents_root, agent)
        except FileNotFoundError as exc:
            return ToolResult(
                content=f"Agent {agent!r} not found: {exc}",
                is_error=True,
            )
        except AgentParseError as exc:
            return ToolResult(
                content=f"Agent {agent!r} definition is malformed: {exc}",
                is_error=True,
            )

        # Build sub-loop. Late import to avoid circular dependency:
        # agent.py → tools/registry.py → ... → tools/agent.py would otherwise
        # close the loop at import time.
        from app.harness.agent import AgentLoop, AgentLoopError

        sub_registry = self._config.sub_registry_factory()
        if "Agent" in sub_registry.names():
            return ToolResult(
                content=(
                    "Sub-registry must not include the Agent tool — nested "
                    "subagent spawning is not supported. Fix the registry "
                    "factory."
                ),
                is_error=True,
            )

        # `tools` whitelist: None = inherit-all (allowed_tools=None);
        # tuple (possibly empty) = strict whitelist (allowed_tools=list(...)).
        # Empty whitelist means pure-chat subagent — no tool surface.
        if agent_def.tools is None:
            allowed_tools: list[str] | None = None
        else:
            allowed_tools = list(agent_def.tools)

        # Resolve model: explicit per-agent override wins.
        model = agent_def.model or self._config.default_model

        sub_loop = AgentLoop(
            client=self._config.client,
            model=model,
            system_prompt=agent_def.body,
            tool_registry=sub_registry,
            allowed_tools=allowed_tools,
            max_iterations=self._config.max_iterations,
            max_tokens=self._config.max_tokens,
        )

        try:
            result = sub_loop.run(prompt)
        except AgentLoopError as exc:
            return ToolResult(
                content=f"Subagent {agent!r} failed: {exc}",
                is_error=True,
            )
        except KeyError as exc:
            # ToolRegistry.to_anthropic_schemas raises KeyError when the
            # agent's `tools:` whitelist references a tool not in the
            # sub-registry. Surface visibly — agent definition needs fixing
            # OR sub_registry_factory needs to add the tool.
            return ToolResult(
                content=(
                    f"Subagent {agent!r} declares tool(s) not in sub-registry: "
                    f"{exc}. Either add the tool to default_registry or "
                    f"remove it from .claude/agents/{agent}.md frontmatter."
                ),
                is_error=True,
            )

        # The contract is "subagent returns a summary" — sub-loop's final_text
        # IS that summary (the subagent was instructed to produce a concise
        # report). We don't wrap or annotate further.
        return ToolResult(content=result.final_text, is_error=False)
