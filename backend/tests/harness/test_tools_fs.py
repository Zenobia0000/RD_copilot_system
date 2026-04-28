"""Unit tests for harness fs tools (Read / Write / Glob) + ToolRegistry."""

from __future__ import annotations

import time

import pytest

from app.harness.tools import (
    GlobTool,
    GrepTool,
    ReadTool,
    ToolRegistry,
    WriteTool,
    default_registry,
)
from app.harness.tools.base import Tool, ToolResult


# ────────────────────────────────────────────────────────────────────────────
# ReadTool
# ────────────────────────────────────────────────────────────────────────────

class TestReadTool:
    def test_reads_file_with_line_numbers(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

        result = ReadTool().run(file_path=str(f))

        assert not result.is_error
        # cat -n style: right-aligned line number, tab, content
        assert result.content == "     1\talpha\n     2\tbeta\n     3\tgamma"

    def test_offset_and_limit(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("\n".join(f"line{i}" for i in range(1, 11)), encoding="utf-8")

        result = ReadTool().run(file_path=str(f), offset=4, limit=2)

        assert not result.is_error
        assert "line4" in result.content
        assert "line5" in result.content
        assert "line3" not in result.content
        assert "line6" not in result.content
        # Line numbers reflect original positions
        assert "     4\tline4" in result.content
        assert "     5\tline5" in result.content

    def test_offset_past_end(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("only one line", encoding="utf-8")

        result = ReadTool().run(file_path=str(f), offset=99)

        assert not result.is_error
        assert "past end" in result.content

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")

        result = ReadTool().run(file_path=str(f))

        assert not result.is_error
        assert "empty" in result.content

    def test_relative_path_rejected(self):
        result = ReadTool().run(file_path="relative/path.txt")

        assert result.is_error
        assert "absolute" in result.content

    def test_missing_file(self, tmp_path):
        result = ReadTool().run(file_path=str(tmp_path / "nope.txt"))

        assert result.is_error
        assert "not found" in result.content

    def test_directory_rejected(self, tmp_path):
        result = ReadTool().run(file_path=str(tmp_path))

        assert result.is_error
        assert "not a regular file" in result.content

    def test_binary_file_rejected(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x80\xff\x01\x02")

        result = ReadTool().run(file_path=str(f))

        assert result.is_error
        assert "decode" in result.content


# ────────────────────────────────────────────────────────────────────────────
# WriteTool
# ────────────────────────────────────────────────────────────────────────────

class TestWriteTool:
    def test_writes_new_file(self, tmp_path):
        target = tmp_path / "out.txt"

        result = WriteTool().run(file_path=str(target), content="hello world")

        assert not result.is_error
        assert target.read_text(encoding="utf-8") == "hello world"
        assert "11 bytes" in result.content

    def test_creates_parent_dirs(self, tmp_path):
        target = tmp_path / "deeply" / "nested" / "out.txt"

        result = WriteTool().run(file_path=str(target), content="x")

        assert not result.is_error
        assert target.exists()

    def test_overwrites_existing(self, tmp_path):
        target = tmp_path / "out.txt"
        target.write_text("old", encoding="utf-8")

        result = WriteTool().run(file_path=str(target), content="new")

        assert not result.is_error
        assert target.read_text(encoding="utf-8") == "new"

    def test_relative_path_rejected(self):
        result = WriteTool().run(file_path="rel.txt", content="x")

        assert result.is_error
        assert "absolute" in result.content

    def test_oversize_rejected(self, tmp_path):
        target = tmp_path / "huge.txt"
        # 6 MiB > 5 MiB cap
        result = WriteTool().run(file_path=str(target), content="x" * (6 * 1024 * 1024))

        assert result.is_error
        assert "safety cap" in result.content
        assert not target.exists()


# ────────────────────────────────────────────────────────────────────────────
# GlobTool
# ────────────────────────────────────────────────────────────────────────────

class TestGlobTool:
    def test_matches_pattern(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        (tmp_path / "c.txt").write_text("")

        result = GlobTool().run(pattern="*.py", path=str(tmp_path))

        assert not result.is_error
        lines = result.content.splitlines()
        assert len(lines) == 2
        assert all(line.endswith(".py") for line in lines)

    def test_recursive_pattern(self, tmp_path):
        (tmp_path / "x.py").write_text("")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "y.py").write_text("")

        result = GlobTool().run(pattern="**/*.py", path=str(tmp_path))

        assert not result.is_error
        assert "x.py" in result.content
        assert "y.py" in result.content

    def test_sorts_by_mtime_desc(self, tmp_path):
        old = tmp_path / "old.py"
        old.write_text("")
        time.sleep(0.02)
        new = tmp_path / "new.py"
        new.write_text("")

        result = GlobTool().run(pattern="*.py", path=str(tmp_path))

        assert not result.is_error
        lines = result.content.splitlines()
        assert lines[0].endswith("new.py")
        assert lines[1].endswith("old.py")

    def test_no_matches(self, tmp_path):
        result = GlobTool().run(pattern="*.nonexistent", path=str(tmp_path))

        assert not result.is_error
        assert "no matches" in result.content

    def test_relative_path_rejected(self):
        result = GlobTool().run(pattern="*.py", path="relative/dir")

        assert result.is_error
        assert "absolute" in result.content

    def test_missing_root(self, tmp_path):
        result = GlobTool().run(pattern="*.py", path=str(tmp_path / "nope"))

        assert result.is_error
        assert "does not exist" in result.content

    def test_only_files_not_dirs(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        (tmp_path / "subdir").mkdir()

        result = GlobTool().run(pattern="*", path=str(tmp_path))

        assert not result.is_error
        # Only the file, not the dir
        lines = result.content.splitlines()
        assert len(lines) == 1
        assert lines[0].endswith("file.txt")


# ────────────────────────────────────────────────────────────────────────────
# ToolRegistry
# ────────────────────────────────────────────────────────────────────────────

class _DummyTool(Tool):
    name = "Dummy"
    description = "echoes its input back"
    input_schema = {
        "type": "object",
        "properties": {"msg": {"type": "string"}},
        "required": ["msg"],
    }

    def run(self, *, msg: str):
        return ToolResult(content=f"echo:{msg}")


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = _DummyTool()
        reg.register(tool)

        assert reg.get("Dummy") is tool
        assert reg.names() == ["Dummy"]

    def test_duplicate_register_rejected(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_DummyTool())

    def test_get_unknown_raises(self):
        reg = ToolRegistry()
        with pytest.raises(KeyError):
            reg.get("Nope")

    def test_dispatch_runs_tool(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())

        result = reg.dispatch("Dummy", {"msg": "hi"})

        assert not result.is_error
        assert result.content == "echo:hi"

    def test_dispatch_unknown_tool_returns_error(self):
        reg = ToolRegistry()
        result = reg.dispatch("Nope", {})

        assert result.is_error
        assert "not registered" in result.content

    def test_dispatch_bad_arguments_returns_error(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())

        # missing required 'msg'
        result = reg.dispatch("Dummy", {})

        assert result.is_error
        assert "bad arguments" in result.content

    def test_dispatch_handler_exception_returns_error(self):
        class _ExplodingTool(Tool):
            name = "Boom"
            description = ""
            input_schema = {"type": "object", "properties": {}}

            def run(self, **_):
                raise RuntimeError("kaboom")

        reg = ToolRegistry()
        reg.register(_ExplodingTool())

        result = reg.dispatch("Boom", {})

        assert result.is_error
        assert "RuntimeError" in result.content
        assert "kaboom" in result.content

    def test_anthropic_schema_shape(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())

        schemas = reg.to_anthropic_schemas()

        assert len(schemas) == 1
        s = schemas[0]
        assert s["name"] == "Dummy"
        assert s["description"] == "echoes its input back"
        assert s["input_schema"]["properties"]["msg"]["type"] == "string"

    def test_anthropic_schema_filter(self):
        reg = default_registry()

        only_read = reg.to_anthropic_schemas(only=["Read"])

        assert len(only_read) == 1
        assert only_read[0]["name"] == "Read"

    def test_anthropic_schema_filter_unknown_raises(self):
        reg = default_registry()
        with pytest.raises(KeyError, match="not registered"):
            reg.to_anthropic_schemas(only=["Read", "GhostTool"])

    def test_default_registry_has_standard_tools(self):
        """Default registry: fs (Read/Write/Edit/Glob/Grep) + Bash + web."""
        reg = default_registry()
        assert set(reg.names()) == {
            "Read", "Write", "Edit", "Glob", "Grep", "Bash",
            "WebFetch", "WebSearch",
        }


# ────────────────────────────────────────────────────────────────────────────
# GrepTool
# ────────────────────────────────────────────────────────────────────────────

class TestGrepTool:
    def _seed(self, root):
        (root / "a.md").write_text(
            "alpha line\nbeta CONTRADICTION here\ngamma\n", encoding="utf-8"
        )
        (root / "b.md").write_text(
            "no hits in this file\n", encoding="utf-8"
        )
        sub = root / "sub"
        sub.mkdir()
        (sub / "c.py").write_text(
            "def contradiction():\n    return 1\n", encoding="utf-8"
        )
        (sub / "d.txt").write_text(
            "two\nCONTRADICTION lines\nCONTRADICTION here\n", encoding="utf-8"
        )

    def test_content_mode_default(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(pattern="CONTRADICTION", path=str(tmp_path))
        assert not result.is_error
        # a.md: 1 hit on line 2; d.txt: 2 hits
        lines = result.content.splitlines()
        assert any("a.md:2:" in line for line in lines)
        assert any("d.txt:2:" in line for line in lines)
        assert any("d.txt:3:" in line for line in lines)

    def test_files_with_matches_mode(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="CONTRADICTION", path=str(tmp_path),
            output_mode="files_with_matches",
        )
        assert not result.is_error
        files = set(result.content.splitlines())
        # 2 unique files match (case-sensitive default — c.py 'contradiction' lowercase doesn't)
        assert any("a.md" in f for f in files)
        assert any("d.txt" in f for f in files)

    def test_count_mode(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="CONTRADICTION", path=str(tmp_path),
            output_mode="count",
        )
        assert not result.is_error
        # Format: path:N
        assert "a.md:1" in result.content
        assert "d.txt:2" in result.content

    def test_case_insensitive(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="contradiction", path=str(tmp_path),
            case_insensitive=True,
            output_mode="files_with_matches",
        )
        assert not result.is_error
        files = result.content.splitlines()
        # Now c.py also matches (def contradiction)
        assert any("a.md" in f for f in files)
        assert any("c.py" in f for f in files)
        assert any("d.txt" in f for f in files)

    def test_glob_filter(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="contradiction", path=str(tmp_path),
            glob="**/*.py", case_insensitive=True,
            output_mode="files_with_matches",
        )
        assert not result.is_error
        files = result.content.splitlines()
        # Only the python file
        assert all(".py" in f for f in files if not f.startswith("<"))
        assert any("c.py" in f for f in files)

    def test_no_matches_returns_placeholder(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="ZZZNOTHING", path=str(tmp_path),
        )
        assert not result.is_error
        assert result.content == "<no matches>"

    def test_invalid_regex_returns_is_error(self, tmp_path):
        result = GrepTool().run(pattern="[invalid", path=str(tmp_path))
        assert result.is_error
        assert "invalid regex" in result.content

    def test_relative_path_rejected(self, tmp_path):
        result = GrepTool().run(pattern="x", path="relative/dir")
        assert result.is_error
        assert "absolute" in result.content

    def test_missing_path_rejected(self, tmp_path):
        result = GrepTool().run(
            pattern="x", path=str(tmp_path / "nonexistent"),
        )
        assert result.is_error
        assert "does not exist" in result.content

    def test_invalid_output_mode_rejected(self, tmp_path):
        self._seed(tmp_path)
        result = GrepTool().run(
            pattern="x", path=str(tmp_path), output_mode="bogus",
        )
        assert result.is_error
        assert "output_mode" in result.content

    def test_empty_pattern_rejected(self, tmp_path):
        result = GrepTool().run(pattern="", path=str(tmp_path))
        assert result.is_error
        assert "non-empty" in result.content

    def test_head_limit_caps_content_lines(self, tmp_path):
        # Create 50 hits across one file
        f = tmp_path / "big.md"
        f.write_text("\n".join(f"hit {i}" for i in range(50)), encoding="utf-8")
        result = GrepTool().run(
            pattern="hit", path=str(tmp_path), head_limit=10,
        )
        assert not result.is_error
        lines = result.content.splitlines()
        # 10 hits + 1 truncation marker
        assert len(lines) == 11
        assert "<truncated at 10 matches>" in lines[-1]

    def test_search_single_file(self, tmp_path):
        f = tmp_path / "single.txt"
        f.write_text("alpha\nbeta\nalpha again\n", encoding="utf-8")
        result = GrepTool().run(pattern="alpha", path=str(f))
        assert not result.is_error
        lines = result.content.splitlines()
        assert len(lines) == 2
        assert all("alpha" in line for line in lines)

    def test_skips_binary_files(self, tmp_path):
        # Write a binary file with the search pattern in raw bytes
        binary_file = tmp_path / "bin.dat"
        binary_file.write_bytes(b"\x00\x01\x02alpha\x03\x04\xff\xfe")
        text_file = tmp_path / "txt.md"
        text_file.write_text("alpha line\n", encoding="utf-8")

        result = GrepTool().run(pattern="alpha", path=str(tmp_path))
        assert not result.is_error
        # Only the text file should appear; binary silently skipped
        assert "txt.md" in result.content
        assert "bin.dat" not in result.content

    def test_too_many_files_refused(self, tmp_path):
        # Touch 1001 files
        for i in range(1001):
            (tmp_path / f"f{i}.md").write_text("x\n", encoding="utf-8")
        result = GrepTool().run(pattern="x", path=str(tmp_path))
        assert result.is_error
        assert "too many files" in result.content


class TestGrepSchema:
    def test_metadata(self):
        tool = GrepTool()
        assert tool.name == "Grep"
        assert tool.description
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert schema["required"] == ["pattern"]
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert "glob" in schema["properties"]
        assert "output_mode" in schema["properties"]
        assert schema["properties"]["output_mode"]["enum"] == [
            "content", "files_with_matches", "count",
        ]
