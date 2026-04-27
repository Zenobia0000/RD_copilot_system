"""CustomAgent loader — parse .claude/agents/<name>.md into a CustomAgent record.

A custom agent is a subagent definition the main loop can spawn via the Agent
tool. The file format mirrors Claude Code's:

- Required frontmatter: name, description
- Optional frontmatter: model (override), tools (whitelist)
- Markdown body becomes the subagent's system prompt

Layout: agents_root / <name>.md (flat, like commands — not nested like skills).

The frontmatter parser duplicates skill.py / command.py logic by design; the
three callers have different policies (skill: optional fm, command: required
fm raising ParseError, agent: required fm with required name+description) and
extracting a shared parser would muddy each caller's contract. Refactor when
a fourth caller appears.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


@dataclass(frozen=True)
class CustomAgent:
    """Parsed agent definition file."""

    name: str
    description: str
    body: str
    source_path: Path
    model: str | None = None
    """Optional model override (e.g. 'opus', 'haiku', or full model id).
    None means inherit from main loop."""
    tools: tuple[str, ...] | None = None
    """Tool whitelist. None = inherit; tuple (possibly empty) = strict whitelist.
    Empty tuple means pure-chat agent with no tool surface."""


class AgentParseError(ValueError):
    """Raised when an agent file cannot be parsed."""


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split frontmatter+body. Frontmatter is required for agents — name and
    description are essential for the Agent tool to dispatch correctly."""
    if not text.lstrip().startswith("---"):
        raise AgentParseError("missing YAML frontmatter (required for agents)")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise AgentParseError("frontmatter opened with --- but never closed")
    raw_meta, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError as exc:
        raise AgentParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise AgentParseError(
            f"frontmatter must be a mapping, got {type(meta).__name__}"
        )
    return meta, body


def _coerce_tools(value: object) -> tuple[str, ...] | None:
    """Accept list, comma-separated string, or absence."""
    if value is None:
        return None
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [s.strip() for s in value.split(",")]
    else:
        raise AgentParseError(
            f"tools must be list or string, got {type(value).__name__}"
        )
    cleaned = tuple(s for s in (str(x).strip() for x in items) if s)
    return cleaned


def parse_agent(text: str, source_path: Path, *, fallback_name: str) -> CustomAgent:
    """Parse a .claude/agents/<name>.md file."""
    meta, body = _split_frontmatter(text)

    name = str(meta.get("name") or fallback_name).strip()
    if not name:
        raise AgentParseError("agent name is empty")

    description = str(meta.get("description", "")).strip()
    if not description:
        raise AgentParseError(
            f"agent {name!r} missing required 'description' frontmatter field"
        )

    model_raw = meta.get("model")
    model = str(model_raw).strip() if model_raw is not None else None
    if model == "":
        model = None

    tools = _coerce_tools(meta.get("tools"))

    return CustomAgent(
        name=name,
        description=description,
        body=body.strip(),
        source_path=source_path,
        model=model,
        tools=tools,
    )


def load_agent(agents_root: Path, name: str) -> CustomAgent:
    """Load a single agent by name (file stem) from agents_root.

    Layout expected: agents_root / <name>.md
    """
    agent_file = agents_root / f"{name}.md"
    if not agent_file.is_file():
        raise FileNotFoundError(f"agent file not found: {agent_file}")
    text = agent_file.read_text(encoding="utf-8")
    return parse_agent(text, agent_file, fallback_name=name)


def discover_agents(agents_root: Path) -> dict[str, CustomAgent]:
    """Scan agents_root for all *.md files. Returns {name: CustomAgent}.

    Skips files that fail to parse (callers needing strict validation should
    iterate themselves and surface errors)."""
    if not agents_root.is_dir():
        return {}
    agents: dict[str, CustomAgent] = {}
    for child in sorted(agents_root.glob("*.md")):
        try:
            text = child.read_text(encoding="utf-8")
            agent = parse_agent(text, child, fallback_name=child.stem)
        except (AgentParseError, OSError):
            continue
        agents[agent.name] = agent
    return agents
