"""CLI entry: `python -m app.harness <command> [args...]`.

Wires M1-M3 together: locate the project, resolve the slash-command, load
its skill, build the agent loop, run it, print the result.

Skills express paths relative to the project root (e.g. ".claude/context/
triz/.triz-state.json"), but the fs tools require absolute paths. We bridge
that by injecting an Environment header into the system prompt that tells
the agent the working directory — the agent constructs absolute paths from
the relative ones it finds in skill instructions.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from app.harness.agent import AgentLoop, AgentLoopError
from app.harness.command import CommandParseError, load_command
from app.harness.config import HarnessConfigError, build_client, load_env
from app.harness.skill import SkillParseError, load_skill
from app.harness.tools.registry import default_registry


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from `start` (or cwd) looking for a .claude/ directory.

    Project root convention = nearest ancestor (or cwd itself) containing
    .claude/. Raises FileNotFoundError if none found.
    """
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".claude").is_dir():
            return candidate
    raise FileNotFoundError(
        f"no .claude/ directory found in {cur} or any ancestor"
    )


def build_system_prompt(*, project_root: Path, skill_name: str, skill_body: str) -> str:
    """Wrap a skill body with the environment header the agent needs.

    The agent must know its absolute working directory so it can convert
    skill-relative paths (e.g. .claude/context/triz/...) to absolute ones
    that Read/Write will accept.
    """
    return (
        "# Environment\n\n"
        f"- Working directory: {project_root}\n"
        f"- Today's date: {date.today().isoformat()}\n"
        "- All filesystem tools require ABSOLUTE paths. When skill instructions\n"
        "  reference paths like `.claude/context/triz/...`, prefix them with\n"
        "  the working directory above.\n"
        "\n"
        "---\n"
        "\n"
        f"# Skill: {skill_name}\n\n"
        f"{skill_body}\n"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.harness",
        description="Run a Claude Code style slash command via the v2 harness.",
    )
    parser.add_argument(
        "command",
        help="Slash command to run, e.g. /triz or /triz-scope",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to forward to the command as the user message",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Max agent loop iterations (default: 20)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8000,
        help="Max tokens per model response (default: 8000)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = _build_parser()
    ns = parser.parse_args(argv)

    if ns.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    cmd_name = ns.command.lstrip("/")
    user_args = " ".join(ns.args).strip()

    # 1. Project discovery
    try:
        project_root = find_project_root()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    commands_dir = project_root / ".claude" / "commands"
    skills_dir = project_root / ".claude" / "skills"

    # 2. Resolve command → skill
    try:
        command = load_command(commands_dir, cmd_name)
    except FileNotFoundError:
        print(f"error: command /{cmd_name} not found in {commands_dir}", file=sys.stderr)
        return 2
    except CommandParseError as exc:
        print(f"error: malformed command /{cmd_name}: {exc}", file=sys.stderr)
        return 2

    if command.referenced_skill is None:
        print(
            f"error: command /{cmd_name} body has no `載入 **<skill>** skill` "
            f"reference; cannot resolve which skill to load",
            file=sys.stderr,
        )
        return 2

    try:
        skill = load_skill(skills_dir, command.referenced_skill)
    except FileNotFoundError:
        print(
            f"error: skill {command.referenced_skill!r} (referenced by /{cmd_name}) "
            f"not found in {skills_dir}",
            file=sys.stderr,
        )
        return 2
    except SkillParseError as exc:
        print(
            f"error: malformed skill {command.referenced_skill!r}: {exc}",
            file=sys.stderr,
        )
        return 2

    # 3. Client (load .env from project root for path stability)
    load_env(project_root / ".env")
    try:
        hc = build_client()
    except HarnessConfigError as exc:
        print(f"error: harness config: {exc}", file=sys.stderr)
        return 2

    # 4. Compose system prompt + user message
    system_prompt = build_system_prompt(
        project_root=project_root,
        skill_name=skill.name,
        skill_body=skill.body,
    )
    user_message = user_args or (
        f"請依 {skill.name} skill 的步驟引導我，先告訴我下一步要做什麼。"
    )

    # 5. Build and run the loop
    loop = AgentLoop(
        client=hc.client,
        model=hc.default_model,
        system_prompt=system_prompt,
        tool_registry=default_registry(),
        allowed_tools=list(skill.allowed_tools) if skill.allowed_tools is not None else None,
        max_iterations=ns.max_iterations,
        max_tokens=ns.max_tokens,
    )

    print(
        f"==> /{cmd_name} → skill={skill.name} | provider={hc.provider} | "
        f"model={hc.default_model}",
        file=sys.stderr,
    )

    try:
        result = loop.run(user_message)
    except AgentLoopError as exc:
        print(f"error: agent loop: {exc}", file=sys.stderr)
        return 1

    # 6. Print result to stdout; metadata to stderr
    print(result.final_text)
    print(
        f"\n--- iterations={result.iterations} tool_calls={result.tool_calls} "
        f"stop={result.stop_reason}",
        file=sys.stderr,
    )

    if result.stop_reason == "max_tokens":
        print(
            "warning: response truncated at max_tokens; consider --max-tokens higher",
            file=sys.stderr,
        )
        return 1
    return 0
