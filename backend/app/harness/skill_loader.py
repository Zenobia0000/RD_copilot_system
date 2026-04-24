"""Skill Loader — filesystem-based skill discovery.

At startup, scans backend/app/skills/*/SKILL.md:
- Parses YAML frontmatter (name, description, type, when_to_use, cache_policy)
- Registers knowledge skills as prompt content sources
- Supports hot-reload: modify SKILL.md → next call picks up changes

Usage:
    from app.harness.skill_loader import load_all, get_skill, get_skill_content

    load_all()                          # Called at startup
    skill = get_skill("triz_39_parameters")
    content = get_skill_content("triz_39_parameters")  # Returns markdown body
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# Default skills directory: backend/app/skills/
_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


@dataclass
class SkillDefinition:
    """Parsed skill metadata + content."""
    name: str
    description: str = ""
    skill_type: Literal["knowledge", "handler", "hybrid"] = "knowledge"
    when_to_use: str = ""
    cache_policy: Literal["static", "dynamic"] = "static"
    content: str = ""
    source_path: str = ""
    tags: list[str] = field(default_factory=list)


# Global skill registry
SKILL_REGISTRY: dict[str, SkillDefinition] = {}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns (metadata_dict, body_content).
    Frontmatter is delimited by --- lines at the start of the file.
    """
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if not match:
        return {}, text

    frontmatter_text = match.group(1)
    body = match.group(2)

    # Simple YAML-like parsing (key: value per line)
    # Avoids PyYAML dependency for this simple use case
    metadata: dict = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # Handle lists (comma-separated)
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',') if v.strip()]
            # Handle quoted strings
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            metadata[key] = value

    return metadata, body


def _load_skill_file(skill_dir: Path) -> SkillDefinition | None:
    """Load a single skill from its directory.

    Expects: skill_dir/SKILL.md with YAML frontmatter.
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None

    try:
        raw = skill_file.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to read skill file %s: %s", skill_file, exc)
        return None

    metadata, body = _parse_frontmatter(raw)

    name = metadata.get("name", skill_dir.name)
    if not name:
        logger.warning("Skill at %s has no name — using directory name", skill_dir)
        name = skill_dir.name

    return SkillDefinition(
        name=name,
        description=str(metadata.get("description", "")),
        skill_type=metadata.get("type", "knowledge"),
        when_to_use=str(metadata.get("when_to_use", "")),
        cache_policy=metadata.get("cache_policy", "static"),
        content=body.strip(),
        source_path=str(skill_file),
        tags=metadata.get("tags", []) if isinstance(metadata.get("tags"), list) else [],
    )


def load_all(skills_dir: Path | None = None) -> int:
    """Scan skills directory and load all SKILL.md files.

    Args:
        skills_dir: Override the default skills directory.

    Returns:
        Number of skills loaded.
    """
    base = skills_dir or _SKILLS_DIR
    if not base.exists():
        logger.info("Skills directory %s does not exist — no skills loaded", base)
        return 0

    loaded = 0
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        skill = _load_skill_file(child)
        if skill is None:
            continue
        SKILL_REGISTRY[skill.name] = skill
        loaded += 1
        logger.debug(
            "Loaded skill '%s' (type=%s, cache=%s, %d chars)",
            skill.name, skill.skill_type, skill.cache_policy, len(skill.content),
        )

    logger.info("Skill loader: loaded %d skills from %s", loaded, base)
    return loaded


def get_skill(name: str) -> SkillDefinition | None:
    """Get a loaded skill by name."""
    return SKILL_REGISTRY.get(name)


def get_skill_content(name: str) -> str | None:
    """Get the content body of a loaded skill.

    Returns None if the skill is not found.
    """
    skill = SKILL_REGISTRY.get(name)
    return skill.content if skill else None


def list_skills() -> list[SkillDefinition]:
    """Return all loaded skills, sorted by name."""
    return sorted(SKILL_REGISTRY.values(), key=lambda s: s.name)


def get_knowledge_skills() -> dict[str, str]:
    """Return all knowledge-type skills as {name: content} dict.

    Useful for passing to prompt_assembler's knowledge_blocks parameter.
    """
    return {
        name: skill.content
        for name, skill in SKILL_REGISTRY.items()
        if skill.skill_type == "knowledge" and skill.content
    }
