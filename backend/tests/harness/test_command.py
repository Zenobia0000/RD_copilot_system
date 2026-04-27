"""Unit tests for harness command resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness.command import (
    Command,
    CommandParseError,
    ResolvedCommand,
    discover_commands,
    load_command,
    parse_command,
    resolve_command,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_REAL_COMMANDS_DIR = _PROJECT_ROOT / ".claude" / "commands"


# ────────────────────────────────────────────────────────────────────────────
# parse_command
# ────────────────────────────────────────────────────────────────────────────

class TestParseCommand:
    def test_basic_with_skill_ref(self):
        text = (
            "---\n"
            "description: My command.\n"
            "---\n"
            "\n"
            "# Title\n"
            "載入 **my-skill** skill, do the thing.\n"
        )
        cmd = parse_command(text, Path("/x/cmd.md"), name="cmd")

        assert cmd.name == "cmd"
        assert cmd.description == "My command."
        assert cmd.referenced_skill == "my-skill"
        assert "do the thing" in cmd.body

    def test_no_skill_ref(self):
        text = "---\ndescription: d\n---\n\nfree text without skill ref\n"
        cmd = parse_command(text, Path("/x/cmd.md"), name="cmd")
        assert cmd.referenced_skill is None

    def test_skill_ref_first_match_wins(self):
        text = (
            "---\ndescription: d\n---\n\n"
            "載入 **first-skill** skill.\n"
            "Then maybe also 載入 **second-skill** skill.\n"
        )
        cmd = parse_command(text, Path("/x/cmd.md"), name="cmd")
        assert cmd.referenced_skill == "first-skill"

    def test_missing_frontmatter(self):
        with pytest.raises(CommandParseError, match="frontmatter"):
            parse_command("no frontmatter here\n", Path("/x"), name="cmd")

    def test_invalid_yaml(self):
        with pytest.raises(CommandParseError, match="invalid YAML"):
            parse_command("---\nbad: [unclosed\n---\nbody\n", Path("/x"), name="cmd")

    def test_frontmatter_not_a_mapping(self):
        with pytest.raises(CommandParseError, match="mapping"):
            parse_command("---\n- a\n- b\n---\nbody\n", Path("/x"), name="cmd")


# ────────────────────────────────────────────────────────────────────────────
# load_command + discover_commands
# ────────────────────────────────────────────────────────────────────────────

class TestLoadCommand:
    def test_loads_from_disk(self, tmp_path):
        (tmp_path / "foo.md").write_text(
            "---\ndescription: d\n---\n\n載入 **foo-skill** skill.\n",
            encoding="utf-8",
        )

        cmd = load_command(tmp_path, "foo")

        assert cmd.name == "foo"
        assert cmd.referenced_skill == "foo-skill"

    def test_missing_command_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_command(tmp_path, "nope")


class TestDiscoverCommands:
    def test_finds_all_md_files(self, tmp_path):
        for n in ("a", "b", "c"):
            (tmp_path / f"{n}.md").write_text(
                f"---\ndescription: d{n}\n---\n載入 **{n}-skill** skill.\n",
                encoding="utf-8",
            )

        result = discover_commands(tmp_path)

        assert set(result) == {"a", "b", "c"}
        assert result["b"].referenced_skill == "b-skill"

    def test_skips_unparseable(self, tmp_path):
        (tmp_path / "good.md").write_text("---\ndescription: ok\n---\n", encoding="utf-8")
        (tmp_path / "bad.md").write_text("no frontmatter", encoding="utf-8")

        result = discover_commands(tmp_path)
        assert set(result) == {"good"}

    def test_missing_root(self, tmp_path):
        assert discover_commands(tmp_path / "nope") == {}


# ────────────────────────────────────────────────────────────────────────────
# Real-world compatibility — every existing /triz* and /tr* command must
# parse cleanly and reference a discoverable skill name.
# ────────────────────────────────────────────────────────────────────────────

class TestRealCommands:
    def test_triz_command_routes_to_triz_router(self):
        cmd = load_command(_REAL_COMMANDS_DIR, "triz")
        assert cmd.referenced_skill == "triz-router"
        assert "TRIZ" in cmd.description

    def test_triz_scope_routes_to_triz_scoping(self):
        cmd = load_command(_REAL_COMMANDS_DIR, "triz-scope")
        assert cmd.referenced_skill == "triz-scoping"

    def test_tr_command_routes_to_tr_router(self):
        cmd = load_command(_REAL_COMMANDS_DIR, "tr")
        assert cmd.referenced_skill == "tr-router"

    def test_all_real_triz_and_tr_commands_have_skill_ref(self):
        all_cmds = discover_commands(_REAL_COMMANDS_DIR)
        triz_and_tr = {n: c for n, c in all_cmds.items() if n.startswith(("triz", "tr"))}
        # /triz-status reads state directly and has no skill body, so allow opt-out
        skipped = {"triz-status"}
        missing_ref = [
            n for n, c in triz_and_tr.items()
            if n not in skipped and c.referenced_skill is None
        ]
        assert not missing_ref, f"commands missing skill ref: {missing_ref}"


# ────────────────────────────────────────────────────────────────────────────
# Lint: every real command must meet baseline quality bars + resolve cleanly
# ────────────────────────────────────────────────────────────────────────────

_PROJECT_SKILLS_DIR = _PROJECT_ROOT / ".claude" / "skills"
_ALL_REAL_COMMAND_NAMES = sorted(
    p.stem for p in _REAL_COMMANDS_DIR.glob("*.md") if p.is_file()
)


@pytest.mark.parametrize("cmd_name", _ALL_REAL_COMMAND_NAMES)
class TestCommandLint:
    """Run once per command — no command is skipped."""

    def test_loads_without_error(self, cmd_name):
        load_command(_REAL_COMMANDS_DIR, cmd_name)

    def test_has_description(self, cmd_name):
        cmd = load_command(_REAL_COMMANDS_DIR, cmd_name)
        assert cmd.description, (
            f"/{cmd_name} has empty frontmatter `description` — required by "
            f"Claude Code spec for slash-command UX"
        )

    def test_body_is_substantial(self, cmd_name):
        cmd = load_command(_REAL_COMMANDS_DIR, cmd_name)
        assert len(cmd.body) >= 100, (
            f"/{cmd_name} body too short ({len(cmd.body)} chars) — "
            f"likely placeholder"
        )

    def test_resolve_succeeds(self, cmd_name):
        """Either it points at an existing skill, or it runs inline. Both
        are valid — but resolve_command must not raise."""
        from app.harness.command import resolve_command
        resolve_command(
            commands_root=_REAL_COMMANDS_DIR,
            skills_root=_PROJECT_SKILLS_DIR,
            name=cmd_name,
        )


# ────────────────────────────────────────────────────────────────────────────
# resolve_command — skill source vs inline source
# ────────────────────────────────────────────────────────────────────────────

class TestResolveCommand:
    def _setup(self, tmp_path: Path) -> tuple[Path, Path]:
        commands = tmp_path / "commands"
        skills = tmp_path / "skills"
        commands.mkdir()
        skills.mkdir()
        return commands, skills

    def test_resolves_skill_source(self, tmp_path):
        commands, skills = self._setup(tmp_path)
        (commands / "go.md").write_text(
            "---\ndescription: do go\n---\n載入 **the-skill** skill, do it.\n",
            encoding="utf-8",
        )
        skill_dir = skills / "the-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: the-skill\ndescription: skill desc\nallowed-tools: Read, Write\n---\n"
            "Skill body content.\n",
            encoding="utf-8",
        )

        r = resolve_command(commands_root=commands, skills_root=skills, name="go")

        assert isinstance(r, ResolvedCommand)
        assert r.source == "skill"
        assert r.name == "go"
        assert r.skill_name == "the-skill"
        assert r.body == "Skill body content."
        assert r.allowed_tools == ("Read", "Write")
        assert r.label == "Skill: the-skill"

    def test_resolves_inline_source(self, tmp_path):
        commands, skills = self._setup(tmp_path)
        (commands / "status.md").write_text(
            "---\ndescription: read state\n---\n"
            "# Status\n\nRead the .triz-state.json and report progress.\n",
            encoding="utf-8",
        )

        r = resolve_command(commands_root=commands, skills_root=skills, name="status")

        assert r.source == "inline"
        assert r.name == "status"
        assert r.skill_name is None
        assert r.allowed_tools is None
        assert "Read the .triz-state.json" in r.body
        assert r.label == "Command: status"

    def test_missing_command_raises(self, tmp_path):
        commands, skills = self._setup(tmp_path)
        with pytest.raises(FileNotFoundError):
            resolve_command(commands_root=commands, skills_root=skills, name="nope")

    def test_skill_ref_to_missing_skill_raises(self, tmp_path):
        commands, skills = self._setup(tmp_path)
        (commands / "broken.md").write_text(
            "---\ndescription: x\n---\n載入 **ghost-skill** skill.\n",
            encoding="utf-8",
        )

        with pytest.raises(FileNotFoundError, match="ghost-skill"):
            resolve_command(commands_root=commands, skills_root=skills, name="broken")

    def test_real_triz_status_resolves_inline(self):
        """The motivating use case: /triz-status has no skill body and must
        resolve to inline source so it can run without backend changes."""
        r = resolve_command(
            commands_root=_REAL_COMMANDS_DIR,
            skills_root=_PROJECT_ROOT / ".claude" / "skills",
            name="triz-status",
        )
        assert r.source == "inline"
        assert r.skill_name is None
        # Body should contain the inline instructions about reading state
        assert ".triz-state.json" in r.body

    def test_real_triz_resolves_to_skill(self):
        """Sanity: /triz still routes through the triz-router skill."""
        r = resolve_command(
            commands_root=_REAL_COMMANDS_DIR,
            skills_root=_PROJECT_ROOT / ".claude" / "skills",
            name="triz",
        )
        assert r.source == "skill"
        assert r.skill_name == "triz-router"
