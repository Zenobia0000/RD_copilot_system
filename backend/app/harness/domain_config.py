"""Domain configuration loader — reads .claude/domain.yaml to decouple harness from specific domains."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DomainPaths(BaseModel):
    """Paths section of domain.yaml (relative to project root)."""

    kb_root: str = "knowledge/triz"
    state_dir: str = ".claude/context/triz"
    engineering_root: str = "docs/engineering"


class DomainConfig(BaseModel):
    """Parsed domain.yaml — tells the harness which tools to load and where to find data."""

    domain_id: str = "triz-mechanical"
    display_name: str = "TRIZ + TR Engineering"
    command_prefixes: list[str] = Field(default_factory=lambda: ["triz-", "triz", "tr-", "tr"])
    paths: DomainPaths = Field(default_factory=DomainPaths)
    artifact_categories: list[str] = Field(default_factory=list)

    def is_domain_command(self, cmd_name: str) -> bool:
        """Check if a command name matches any configured prefix."""
        return any(cmd_name.startswith(p) for p in self.command_prefixes)

    def resolve_paths(self, project_root: Path) -> dict[str, Path]:
        """Resolve relative paths to absolute paths."""
        return {
            "kb_root": project_root / self.paths.kb_root,
            "state_dir": project_root / self.paths.state_dir,
            "engineering_root": project_root / self.paths.engineering_root,
        }


@lru_cache(maxsize=1)
def load_domain_config(project_root: Path) -> DomainConfig:
    """Load domain.yaml from .claude/ directory.

    Falls back to defaults if file doesn't exist (backward compatible).
    """
    domain_yaml = project_root / ".claude" / "domain.yaml"
    if not domain_yaml.is_file():
        return DomainConfig()

    raw: dict[str, Any] = yaml.safe_load(domain_yaml.read_text(encoding="utf-8")) or {}
    return DomainConfig(**raw)
