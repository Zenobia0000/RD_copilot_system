"""Filesystem tools — Read, Write, Glob.

Interface mirrors Claude Code's tools so .claude/skills/* prompts work as-is.
"""

from __future__ import annotations

from pathlib import Path

from app.harness.tools.base import Tool, ToolResult

_DEFAULT_READ_LIMIT = 2000
_MAX_WRITE_BYTES = 5 * 1024 * 1024  # 5 MiB safety cap


def _require_absolute(file_path: str) -> ToolResult | None:
    if not Path(file_path).is_absolute():
        return ToolResult(
            content=f"Error: file_path must be absolute, got: {file_path!r}",
            is_error=True,
        )
    return None


class ReadTool(Tool):
    name = "Read"
    description = (
        "Read a file from disk. file_path must be absolute. Returns file "
        "contents in `cat -n` format (line number, tab, content). Default "
        f"reads up to {_DEFAULT_READ_LIMIT} lines from the start. Use offset "
        "and limit for paging through large files."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file.",
            },
            "offset": {
                "type": "integer",
                "description": "1-based line number to start reading from.",
            },
            "limit": {
                "type": "integer",
                "description": "Max number of lines to read.",
            },
        },
        "required": ["file_path"],
    }

    def run(
        self,
        *,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> ToolResult:
        if (err := _require_absolute(file_path)) is not None:
            return err

        path = Path(file_path)
        if not path.exists():
            return ToolResult(
                content=f"Error: file not found: {file_path}",
                is_error=True,
            )
        if not path.is_file():
            return ToolResult(
                content=f"Error: not a regular file: {file_path}",
                is_error=True,
            )

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                content=f"Error: cannot decode as utf-8 (binary?): {file_path}",
                is_error=True,
            )

        if not text:
            return ToolResult(content="<file is empty>")

        lines = text.splitlines()
        start = max(0, (offset - 1)) if offset else 0
        take = limit if limit and limit > 0 else _DEFAULT_READ_LIMIT
        end = min(len(lines), start + take)

        if start >= len(lines):
            return ToolResult(
                content=f"<offset {offset} past end of file ({len(lines)} lines)>",
            )

        body = "\n".join(
            f"{i + 1:>6}\t{line}" for i, line in enumerate(lines[start:end], start=start)
        )
        return ToolResult(content=body)


class WriteTool(Tool):
    name = "Write"
    description = (
        "Write content to a file on disk. Overwrites the file if it exists. "
        "Creates parent directories as needed. file_path must be absolute."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "Full content to write. Replaces existing content.",
            },
        },
        "required": ["file_path", "content"],
    }

    def run(self, *, file_path: str, content: str) -> ToolResult:
        if (err := _require_absolute(file_path)) is not None:
            return err

        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_WRITE_BYTES:
            return ToolResult(
                content=(
                    f"Error: content exceeds {_MAX_WRITE_BYTES} byte safety cap "
                    f"({len(encoded)} bytes)"
                ),
                is_error=True,
            )

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(
            content=f"Wrote {len(encoded)} bytes to {file_path}",
        )


class GlobTool(Tool):
    name = "Glob"
    description = (
        "Find files matching a glob pattern. Returns matching paths sorted by "
        "modification time, most recent first. `path` must be absolute if "
        "provided; defaults to the current working directory."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern, e.g. '**/*.py' or 'session-*.md'.",
            },
            "path": {
                "type": "string",
                "description": "Absolute directory to search in. Defaults to cwd.",
            },
        },
        "required": ["pattern"],
    }

    def run(self, *, pattern: str, path: str | None = None) -> ToolResult:
        base = Path(path) if path else Path.cwd()
        if path is not None and not base.is_absolute():
            return ToolResult(
                content=f"Error: path must be absolute, got: {path!r}",
                is_error=True,
            )
        if not base.exists():
            return ToolResult(
                content=f"Error: search root does not exist: {base}",
                is_error=True,
            )

        matches = [p for p in base.glob(pattern) if p.is_file()]
        if not matches:
            return ToolResult(content="<no matches>")

        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return ToolResult(content="\n".join(str(m) for m in matches))
