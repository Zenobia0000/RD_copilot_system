"""Bash tool — execute shell commands with safety constraints.

Mirrors Claude Code's Bash tool for skills that need shell access
(e.g. git operations, python scripts).
"""

from __future__ import annotations

import subprocess
from typing import Any, ClassVar

from app.harness.tools.base import Tool, ToolResult

_DEFAULT_TIMEOUT = 120  # seconds
_MAX_TIMEOUT = 600      # 10 minutes
_MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MiB output cap


class BashTool(Tool):
    """Execute a shell command and return its output."""

    name: ClassVar[str] = "Bash"
    description: ClassVar[str] = (
        "Execute a bash command and return stdout + stderr. "
        "Commands run in the project working directory. "
        "Use for system operations that dedicated tools cannot handle "
        "(e.g. git, python, pip). Default timeout is 120 seconds."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": f"Timeout in seconds. Default {_DEFAULT_TIMEOUT}, max {_MAX_TIMEOUT}.",
            },
        },
        "required": ["command"],
    }

    def __init__(self, *, cwd: str | None = None) -> None:
        """
        Args:
            cwd: Working directory for commands. Defaults to current directory.
        """
        self._cwd = cwd

    def run(self, *, command: str, timeout: int | None = None) -> ToolResult:
        if not command.strip():
            return ToolResult(
                content="Error: command must be non-empty.",
                is_error=True,
            )

        effective_timeout = min(timeout or _DEFAULT_TIMEOUT, _MAX_TIMEOUT)

        try:
            proc = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=self._cwd,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                content=f"Error: command timed out after {effective_timeout}s.",
                is_error=True,
            )
        except OSError as exc:
            return ToolResult(
                content=f"Error: failed to execute command: {exc}",
                is_error=True,
            )

        output = proc.stdout
        if proc.stderr:
            output += ("\n" if output else "") + proc.stderr

        # Truncate oversized output
        if len(output.encode("utf-8", errors="replace")) > _MAX_OUTPUT_BYTES:
            output = output[:_MAX_OUTPUT_BYTES] + "\n<truncated>"

        if proc.returncode != 0:
            content = output or f"Command failed with exit code {proc.returncode}"
            return ToolResult(content=content, is_error=True)

        return ToolResult(content=output or "<no output>")
