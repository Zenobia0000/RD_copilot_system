"""Unit tests for harness CLI — error paths and helpers.

The happy path (running an actual command end-to-end) requires a live API key
and is verified manually via the smoke runs documented in the M4 commit. These
tests cover everything that's testable without spending API tokens.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness.cli import build_system_prompt, find_project_root, main


# ────────────────────────────────────────────────────────────────────────────
# find_project_root
# ────────────────────────────────────────────────────────────────────────────

class TestFindProjectRoot:
    def test_finds_root_when_dot_claude_in_start(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        assert find_project_root(start=tmp_path) == tmp_path.resolve()

    def test_walks_up_to_find_root(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        assert find_project_root(start=deep) == tmp_path.resolve()

    def test_raises_when_no_dot_claude_anywhere(self, tmp_path):
        with pytest.raises(FileNotFoundError, match=".claude"):
            find_project_root(start=tmp_path)


# ────────────────────────────────────────────────────────────────────────────
# build_system_prompt
# ────────────────────────────────────────────────────────────────────────────

class TestBuildSystemPrompt:
    def test_includes_working_dir_and_body(self):
        prompt = build_system_prompt(
            project_root=Path("/project"),
            instructions_label="Skill: my-skill",
            instructions_body="# Do this\nbody content.",
        )
        assert "Working directory: /project" in prompt
        assert "# Skill: my-skill" in prompt
        assert "body content." in prompt

    def test_supports_inline_command_label(self):
        """Label is freeform — inline commands use 'Command: <name>' instead."""
        prompt = build_system_prompt(
            project_root=Path("/x"),
            instructions_label="Command: triz-status",
            instructions_body="Read state file.",
        )
        assert "# Command: triz-status" in prompt
        assert "Skill:" not in prompt  # no leftover skill header

    def test_warns_about_absolute_paths(self):
        prompt = build_system_prompt(
            project_root=Path("/x"),
            instructions_label="Skill: s",
            instructions_body="b",
        )
        assert "ABSOLUTE paths" in prompt

    def test_includes_today_date(self):
        prompt = build_system_prompt(
            project_root=Path("/x"),
            instructions_label="Skill: s",
            instructions_body="b",
        )
        # Date format YYYY-MM-DD
        import re
        assert re.search(r"Today's date: \d{4}-\d{2}-\d{2}", prompt)


# ────────────────────────────────────────────────────────────────────────────
# main() — error paths (no API hit)
# ────────────────────────────────────────────────────────────────────────────

class TestMainErrorPaths:
    def _make_project(self, tmp_path: Path) -> Path:
        """Create a minimal project layout under tmp_path."""
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".claude" / "skills").mkdir(parents=True)
        return tmp_path

    def test_no_project_returns_2(self, tmp_path, monkeypatch, capsys):
        # cwd has no .claude/
        monkeypatch.chdir(tmp_path)
        rc = main(["/triz"])
        assert rc == 2
        assert ".claude" in capsys.readouterr().err

    def test_unknown_command_returns_2(self, tmp_path, monkeypatch, capsys):
        self._make_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        rc = main(["/nonexistent"])
        assert rc == 2
        assert "not found" in capsys.readouterr().err

    def test_command_without_skill_ref_resolves_inline(self, tmp_path, monkeypatch, capsys):
        """Inline commands (no `載入 **skill**` ref) used to error out at
        resolution. After the resolver enhancement they resolve successfully
        — the failure point moves down to build_client (no API key here)."""
        self._make_project(tmp_path)
        (tmp_path / ".claude" / "commands" / "bare.md").write_text(
            "---\ndescription: bare\n---\nrun this inline\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        for key in (
            "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_BASE_URL", "LLM_PROVIDER",
        ):
            monkeypatch.delenv(key, raising=False)

        rc = main(["/bare"])

        # Resolver no longer rejects — failure is now at config (no API key)
        assert rc == 2
        err = capsys.readouterr().err
        assert "harness config" in err
        assert "skill" not in err.lower()  # not a skill error anymore

    def test_skill_not_found_returns_2(self, tmp_path, monkeypatch, capsys):
        self._make_project(tmp_path)
        # Command points at a skill that doesn't exist on disk
        (tmp_path / ".claude" / "commands" / "test.md").write_text(
            "---\ndescription: t\n---\n載入 **ghost** skill, do something.\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        rc = main(["/test"])
        assert rc == 2
        assert "ghost" in capsys.readouterr().err

    def test_missing_api_key_returns_2(self, tmp_path, monkeypatch, capsys):
        self._make_project(tmp_path)
        (tmp_path / ".claude" / "commands" / "test.md").write_text(
            "---\ndescription: t\n---\n載入 **realskill** skill.\n",
            encoding="utf-8",
        )
        skill_dir = tmp_path / ".claude" / "skills" / "realskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: realskill\ndescription: r\n---\nbody\n", encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        # Strip every key build_client might consult so neither path succeeds
        for key in (
            "ANTHROPIC_API_KEY", "ANTHROPIC_DEFAULT_MODEL",
            "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEFAULT_MODEL",
            "AZURE_OPENAI_BASE_URL", "LLM_PROVIDER",
        ):
            monkeypatch.delenv(key, raising=False)

        rc = main(["/test"])
        assert rc == 2
        err = capsys.readouterr().err
        assert "harness config" in err
