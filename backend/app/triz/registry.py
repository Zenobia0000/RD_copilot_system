"""TRIZ tool registry factory — produces domain tools for ToolRegistry injection."""

from __future__ import annotations

from pathlib import Path

from app.harness.tools.base import Tool
from app.triz.bundle import BundleManager
from app.triz.kb.loader import KBLoader
from app.triz.state_manager import TrizStateManager
from app.triz.tools import (
    ArtifactBundleTool,
    CCICalculateTool,
    MatrixLookupTool,
    ParamMapTool,
    SIMComputeTool,
    TrizStateAdvanceTool,
    TrizStateReadTool,
    TrizStateWriteTool,
)


def triz_tools(
    *,
    kb_root: Path,
    state_dir: Path,
    engineering_root: Path | None = None,
    artifact_categories: list[str] | None = None,
) -> list[Tool]:
    """Create all TRIZ domain tools, ready for ToolRegistry.register().

    Args:
        kb_root: Path to knowledge/triz/ directory.
        state_dir: Path to .claude/context/triz/ directory.
        engineering_root: Path to docs/engineering/ directory. If None,
            defaults to kb_root's grandparent / "docs" / "engineering"
            (i.e. project_root / "docs" / "engineering").
        artifact_categories: Valid artifact categories for ArtifactBundle.
            If None, uses the built-in defaults from bundle.py.

    Returns:
        List of Tool instances (8 tools).
    """
    kb = KBLoader(kb_root)
    mgr = TrizStateManager(state_dir)

    if engineering_root is None:
        # kb_root is typically project_root/knowledge/triz
        # Walk up to project_root
        engineering_root = kb_root.parent.parent / "docs" / "engineering"

    categories = frozenset(artifact_categories) if artifact_categories else None
    bundle_mgr = BundleManager(engineering_root, state_dir=state_dir, valid_categories=categories)

    return [
        MatrixLookupTool(kb),
        ParamMapTool(kb),
        CCICalculateTool(),
        SIMComputeTool(),
        TrizStateReadTool(mgr),
        TrizStateWriteTool(mgr),
        TrizStateAdvanceTool(mgr),
        ArtifactBundleTool(bundle_mgr),
    ]
