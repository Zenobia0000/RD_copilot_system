"""TRIZ tool registry factory — produces domain tools for ToolRegistry injection."""

from __future__ import annotations

from pathlib import Path

from app.harness.tools.base import Tool
from app.triz.kb.loader import KBLoader
from app.triz.state_manager import TrizStateManager
from app.triz.tools import (
    CCICalculateTool,
    MatrixLookupTool,
    ParamMapTool,
    SIMComputeTool,
    TrizStateAdvanceTool,
    TrizStateReadTool,
    TrizStateWriteTool,
)


def triz_tools(*, kb_root: Path, state_dir: Path) -> list[Tool]:
    """Create all TRIZ domain tools, ready for ToolRegistry.register().

    Args:
        kb_root: Path to triz_knowledge_base/ directory.
        state_dir: Path to .claude/context/triz/ directory.

    Returns:
        List of Tool instances (7 tools).
    """
    kb = KBLoader(kb_root)
    mgr = TrizStateManager(state_dir)

    return [
        MatrixLookupTool(kb),
        ParamMapTool(kb),
        CCICalculateTool(),
        SIMComputeTool(),
        TrizStateReadTool(mgr),
        TrizStateWriteTool(mgr),
        TrizStateAdvanceTool(mgr),
    ]
