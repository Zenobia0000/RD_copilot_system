"""Filesystem tools — Read, Write, Glob, Grep.

Interface mirrors Claude Code's tools so .claude/skills/* prompts work as-is.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, ClassVar

from app.harness.tools.base import Tool, ToolResult

_DEFAULT_READ_LIMIT = 2000
_MAX_WRITE_BYTES = 5 * 1024 * 1024  # 5 MiB safety cap
_GREP_DEFAULT_HEAD_LIMIT = 100
_GREP_MAX_FILES_SCANNED = 1000  # safety cap — refuse to walk huge trees
_GREP_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB per file — skip larger


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


class EditTool(Tool):
    """Exact string replacement in files — mirrors Claude Code's Edit tool."""

    name = "Edit"
    description = (
        "Perform an exact string replacement in a file. file_path must be "
        "absolute. old_string must appear exactly once in the file (unless "
        "replace_all is true). The edit fails if old_string is not found or "
        "is ambiguous (appears more than once without replace_all)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit.",
            },
            "old_string": {
                "type": "string",
                "description": "Exact text to find and replace.",
            },
            "new_string": {
                "type": "string",
                "description": "Replacement text.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences. Default false.",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def run(
        self,
        *,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ToolResult:
        if (err := _require_absolute(file_path)) is not None:
            return err

        path = Path(file_path)
        if not path.is_file():
            return ToolResult(
                content=f"Error: file not found: {file_path}",
                is_error=True,
            )

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                content=f"Error: cannot decode as utf-8: {file_path}",
                is_error=True,
            )

        if old_string == new_string:
            return ToolResult(
                content="Error: old_string and new_string are identical.",
                is_error=True,
            )

        count = text.count(old_string)
        if count == 0:
            return ToolResult(
                content="Error: old_string not found in file.",
                is_error=True,
            )
        if count > 1 and not replace_all:
            return ToolResult(
                content=(
                    f"Error: old_string appears {count} times. "
                    "Set replace_all=true or provide more context to make it unique."
                ),
                is_error=True,
            )

        if replace_all:
            new_text = text.replace(old_string, new_string)
        else:
            new_text = text.replace(old_string, new_string, 1)

        path.write_text(new_text, encoding="utf-8")
        replacements = count if replace_all else 1
        return ToolResult(
            content=f"Replaced {replacements} occurrence(s) in {file_path}",
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


class GrepTool(Tool):
    """Search file contents by regex. Subset of Claude Code's Grep covering
    the cases triz-analyst actually needs: pattern + path + glob filter +
    output mode + case-insensitive option.

    Output modes:
      - 'content' (default): `path:line_no:matched_line` per hit, head-limited
      - 'files_with_matches': just paths that have ≥1 match (faster, dedup)
      - 'count': `path:N` per file
    """

    name: ClassVar[str] = "Grep"
    description: ClassVar[str] = (
        "Search file contents by regular expression. Returns matching lines "
        "or matching files. `path` must be absolute if provided. Use `glob` "
        "to limit which files are scanned (e.g. '**/*.py'). Default output "
        f"is 'content' mode, capped at {_GREP_DEFAULT_HEAD_LIMIT} hits."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Python regex to search for (re module syntax).",
            },
            "path": {
                "type": "string",
                "description": "Absolute directory or file path. Defaults to cwd.",
            },
            "glob": {
                "type": "string",
                "description": (
                    "Glob filter for files to scan (e.g. '**/*.md'). "
                    "Defaults to '**/*' (all files)."
                ),
            },
            "output_mode": {
                "type": "string",
                "enum": ["content", "files_with_matches", "count"],
                "description": "Output shape. Default 'content'.",
            },
            "case_insensitive": {
                "type": "boolean",
                "description": "Match without regard to case. Default false.",
            },
            "head_limit": {
                "type": "integer",
                "description": (
                    f"Cap output rows. Default {_GREP_DEFAULT_HEAD_LIMIT}. "
                    "Applies to lines (content) or files (other modes)."
                ),
            },
        },
        "required": ["pattern"],
    }

    def run(
        self,
        *,
        pattern: str,
        path: str | None = None,
        glob: str = "**/*",
        output_mode: str = "content",
        case_insensitive: bool = False,
        head_limit: int | None = None,
    ) -> ToolResult:
        if not isinstance(pattern, str) or not pattern:
            return ToolResult(
                content="Error: pattern must be a non-empty string",
                is_error=True,
            )
        if output_mode not in ("content", "files_with_matches", "count"):
            return ToolResult(
                content=f"Error: invalid output_mode {output_mode!r}",
                is_error=True,
            )

        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as exc:
            return ToolResult(
                content=f"Error: invalid regex {pattern!r}: {exc}",
                is_error=True,
            )

        # Resolve search root.
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

        # Enumerate target files.
        if base.is_file():
            files = [base]
        else:
            files = [p for p in base.glob(glob) if p.is_file()]
            if len(files) > _GREP_MAX_FILES_SCANNED:
                return ToolResult(
                    content=(
                        f"Error: too many files to scan ({len(files)} > "
                        f"{_GREP_MAX_FILES_SCANNED}). Narrow `glob` or `path`."
                    ),
                    is_error=True,
                )

        cap = head_limit if (head_limit and head_limit > 0) else _GREP_DEFAULT_HEAD_LIMIT

        if output_mode == "files_with_matches":
            return _grep_files_only(files, regex, cap)
        if output_mode == "count":
            return _grep_count(files, regex, cap)
        return _grep_content(files, regex, cap)


def _safe_read_lines(file: Path) -> list[str] | None:
    """Read a file as utf-8 lines. Returns None on binary / oversized /
    decode failure — caller should skip silently."""
    try:
        if file.stat().st_size > _GREP_MAX_FILE_BYTES:
            return None
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return text.splitlines()


def _grep_content(files: list[Path], regex: re.Pattern[str], cap: int) -> ToolResult:
    out: list[str] = []
    for file in files:
        lines = _safe_read_lines(file)
        if lines is None:
            continue
        for i, line in enumerate(lines, start=1):
            if regex.search(line):
                out.append(f"{file}:{i}:{line}")
                if len(out) >= cap:
                    out.append(f"<truncated at {cap} matches>")
                    return ToolResult(content="\n".join(out))
    if not out:
        return ToolResult(content="<no matches>")
    return ToolResult(content="\n".join(out))


def _grep_files_only(files: list[Path], regex: re.Pattern[str], cap: int) -> ToolResult:
    out: list[str] = []
    for file in files:
        lines = _safe_read_lines(file)
        if lines is None:
            continue
        if any(regex.search(line) for line in lines):
            out.append(str(file))
            if len(out) >= cap:
                out.append(f"<truncated at {cap} files>")
                return ToolResult(content="\n".join(out))
    if not out:
        return ToolResult(content="<no matches>")
    return ToolResult(content="\n".join(out))


def _grep_count(files: list[Path], regex: re.Pattern[str], cap: int) -> ToolResult:
    out: list[str] = []
    for file in files:
        lines = _safe_read_lines(file)
        if lines is None:
            continue
        n = sum(1 for line in lines if regex.search(line))
        if n > 0:
            out.append(f"{file}:{n}")
            if len(out) >= cap:
                out.append(f"<truncated at {cap} files>")
                return ToolResult(content="\n".join(out))
    if not out:
        return ToolResult(content="<no matches>")
    return ToolResult(content="\n".join(out))
