"""Command resolver — parse .claude/commands/<name>.md into a Command record.

A slash-command file has YAML frontmatter (description) and a markdown body.
By project convention the body's first paragraph references the skill it
triggers, in the form `載入 **<skill-name>** skill, ...`. The resolver
extracts that reference so the harness can pre-load the skill before the
agent loop starts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from app.harness.skill import Skill, load_skill

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)
_SKILL_REF_RE = re.compile(r"載入\s*\*\*([\w\-./]+)\*\*\s*skill", re.IGNORECASE)


@dataclass(frozen=True)
class Command:
    """Parsed command file."""

    name: str
    description: str
    body: str
    referenced_skill: str | None
    source_path: Path


class CommandParseError(ValueError):
    """Raised when a command file cannot be parsed."""


def _split_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise CommandParseError("missing or malformed YAML frontmatter")
    raw_meta, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError as exc:
        raise CommandParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise CommandParseError(
            f"frontmatter must be a mapping, got {type(meta).__name__}"
        )
    return meta, body


def _extract_skill_ref(body: str) -> str | None:
    match = _SKILL_REF_RE.search(body)
    return match.group(1) if match else None


def parse_command(text: str, source_path: Path, *, name: str) -> Command:
    """Parse a command file's text. The name comes from the file stem."""
    meta, body = _split_frontmatter(text)
    description = str(meta.get("description", "")).strip()
    return Command(
        name=name,
        description=description,
        body=body.strip(),
        referenced_skill=_extract_skill_ref(body),
        source_path=source_path,
    )


def load_command(commands_root: Path, name: str) -> Command:
    """Load a single command by name (file stem) from commands_root.

    Layout expected: commands_root / <name>.md
    """
    cmd_file = commands_root / f"{name}.md"
    if not cmd_file.is_file():
        raise FileNotFoundError(f"command file not found: {cmd_file}")
    text = cmd_file.read_text(encoding="utf-8")
    return parse_command(text, cmd_file, name=name)


def discover_commands(commands_root: Path) -> dict[str, Command]:
    """Scan commands_root for all *.md files. Returns {name: Command}."""
    if not commands_root.is_dir():
        return {}
    commands: dict[str, Command] = {}
    for child in sorted(commands_root.glob("*.md")):
        try:
            text = child.read_text(encoding="utf-8")
            cmd = parse_command(text, child, name=child.stem)
        except (CommandParseError, OSError):
            continue
        commands[cmd.name] = cmd
    return commands


# ────────────────────────────────────────────────────────────────────────────
# Resolution: command → instructions for the agent
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ResolvedCommand:
    """A command turned into agent-ready instructions.

    Two sources are valid:

    - `skill`: the command body references `載入 **<skill>** skill`. We load
      that skill's body and use it as the prompt; the command body itself is
      discarded. allowed_tools comes from the skill's frontmatter.
    - `inline`: the command body has no skill ref. The command body itself
      becomes the prompt. allowed_tools is None (no whitelist) — inline
      commands haven't been given a way to declare one yet.
    """

    name: str
    """Command name (file stem)."""

    description: str
    """Description from the command's frontmatter."""

    body: str
    """Instructions to give to the agent. Either the skill body or the
    command body, depending on `source`."""

    source: Literal["skill", "inline"]
    """Where `body` came from."""

    skill_name: str | None
    """Resolved skill name when source == 'skill', else None."""

    allowed_tools: tuple[str, ...] | None
    """Tool whitelist from the skill's frontmatter, or None for unrestricted.
    Always None when source == 'inline'."""

    @property
    def label(self) -> str:
        """Human-readable source label for the system prompt header.

        e.g. `"Skill: triz-router"` or `"Command: triz-status"`.
        """
        if self.source == "skill":
            return f"Skill: {self.skill_name}"
        return f"Command: {self.name}"


def resolve_command(
    *,
    commands_root: Path,
    skills_root: Path,
    name: str,
) -> ResolvedCommand:
    """Load a command and resolve it to agent-ready instructions.

    Raises:
        FileNotFoundError if the command file or referenced skill is missing.
        CommandParseError / SkillParseError on malformed frontmatter.
    """
    cmd = load_command(commands_root, name)

    if cmd.referenced_skill is not None:
        skill: Skill = load_skill(skills_root, cmd.referenced_skill)
        return ResolvedCommand(
            name=cmd.name,
            description=cmd.description,
            body=skill.body,
            source="skill",
            skill_name=skill.name,
            allowed_tools=skill.allowed_tools,
        )

    return ResolvedCommand(
        name=cmd.name,
        description=cmd.description,
        body=cmd.body,
        source="inline",
        skill_name=None,
        allowed_tools=None,
    )
