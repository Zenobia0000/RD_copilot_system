"""Skill loader — parse .claude/skills/<name>/SKILL.md into a Skill record.

A skill bundles three things:
- frontmatter metadata (name, description, optional allowed-tools whitelist)
- a markdown body that becomes the agent's system prompt
- a source path for traceability / hot-reload

No global registry. Callers pass paths explicitly so tests can inject tmp dirs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


@dataclass(frozen=True)
class Skill:
    """Parsed SKILL.md content."""

    name: str
    description: str
    body: str
    source_path: Path
    allowed_tools: tuple[str, ...] | None = None
    """None means no restriction; tuple (possibly empty) means strict whitelist."""


class SkillParseError(ValueError):
    """Raised when a SKILL.md file cannot be parsed."""


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split frontmatter+body. Frontmatter is optional — Claude Code allows
    SKILL.md without it (e.g. tr-router), so we degrade gracefully to {}.

    A leading `---` line that does not close raises (treat as malformed).
    """
    if not text.lstrip().startswith("---"):
        return {}, text
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise SkillParseError("frontmatter opened with --- but never closed")
    raw_meta, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError as exc:
        raise SkillParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise SkillParseError(
            f"frontmatter must be a mapping, got {type(meta).__name__}"
        )
    return meta, body


def _coerce_allowed_tools(value: object) -> tuple[str, ...] | None:
    """Accept Claude Code's two forms or absence."""
    if value is None:
        return None
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        # comma-separated, e.g. "Read, Write, Bash(git status:*)"
        items = [s.strip() for s in value.split(",")]
    else:
        raise SkillParseError(
            f"allowed-tools must be list or string, got {type(value).__name__}"
        )
    cleaned = tuple(s for s in (str(x).strip() for x in items) if s)
    return cleaned


def parse_skill(text: str, source_path: Path, *, fallback_name: str) -> Skill:
    """Parse SKILL.md text. Use fallback_name (the directory name) if frontmatter omits it."""
    meta, body = _split_frontmatter(text)

    name = str(meta.get("name") or fallback_name).strip()
    if not name:
        raise SkillParseError("skill name is empty")

    description = str(meta.get("description", "")).strip()
    allowed_tools = _coerce_allowed_tools(meta.get("allowed-tools"))

    return Skill(
        name=name,
        description=description,
        body=body.strip(),
        source_path=source_path,
        allowed_tools=allowed_tools,
    )


def load_skill(skills_root: Path, name: str) -> Skill:
    """Load a single skill by directory name from skills_root.

    Layout expected: skills_root / <name> / SKILL.md
    """
    skill_dir = skills_root / name
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise FileNotFoundError(f"SKILL.md not found at {skill_file}")
    text = skill_file.read_text(encoding="utf-8")
    return parse_skill(text, skill_file, fallback_name=name)


def discover_skills(skills_root: Path) -> dict[str, Skill]:
    """Scan skills_root for all <dir>/SKILL.md files. Returns {name: Skill}.

    Skips directories without SKILL.md and directories whose SKILL.md fails
    to parse (errors are silently dropped — caller should validate up-front
    if strict behavior is needed).
    """
    if not skills_root.is_dir():
        return {}
    skills: dict[str, Skill] = {}
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        skill_file = child / "SKILL.md"
        if not skill_file.is_file():
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
            skill = parse_skill(text, skill_file, fallback_name=child.name)
        except (SkillParseError, OSError):
            continue
        skills[skill.name] = skill
    return skills
