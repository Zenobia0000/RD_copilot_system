"""Unit tests for harness skill loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness.skill import (
    Skill,
    SkillParseError,
    discover_skills,
    load_skill,
    parse_skill,
)

# Path to the real .claude/skills/ root (project root / .claude / skills)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_REAL_SKILLS_DIR = _PROJECT_ROOT / ".claude" / "skills"


# ────────────────────────────────────────────────────────────────────────────
# parse_skill
# ────────────────────────────────────────────────────────────────────────────

class TestParseSkill:
    def test_basic(self):
        text = (
            "---\n"
            "name: example\n"
            "description: An example skill.\n"
            "---\n"
            "\n"
            "# Body\n"
            "Some content.\n"
        )
        skill = parse_skill(text, Path("/fake/SKILL.md"), fallback_name="example")

        assert skill.name == "example"
        assert skill.description == "An example skill."
        assert skill.body == "# Body\nSome content."
        assert skill.allowed_tools is None
        assert skill.source_path == Path("/fake/SKILL.md")

    def test_fallback_name_when_frontmatter_omits_name(self):
        text = (
            "---\n"
            "description: only description\n"
            "---\n"
            "\n"
            "body\n"
        )
        skill = parse_skill(text, Path("/x/SKILL.md"), fallback_name="dir_name")
        assert skill.name == "dir_name"

    def test_allowed_tools_as_list(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "allowed-tools:\n"
            "  - Read\n"
            "  - Write\n"
            "---\n"
            "body\n"
        )
        skill = parse_skill(text, Path("/x/SKILL.md"), fallback_name="x")
        assert skill.allowed_tools == ("Read", "Write")

    def test_allowed_tools_as_comma_string(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "allowed-tools: Read, Write, Bash(git status:*)\n"
            "---\n"
            "body\n"
        )
        skill = parse_skill(text, Path("/x/SKILL.md"), fallback_name="x")
        assert skill.allowed_tools == ("Read", "Write", "Bash(git status:*)")

    def test_allowed_tools_empty_list(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "allowed-tools: []\n"
            "---\n"
            "body\n"
        )
        skill = parse_skill(text, Path("/x/SKILL.md"), fallback_name="x")
        assert skill.allowed_tools == ()  # empty whitelist != None

    def test_allowed_tools_invalid_type(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "allowed-tools: 42\n"
            "---\n"
            "body\n"
        )
        with pytest.raises(SkillParseError, match="allowed-tools"):
            parse_skill(text, Path("/x/SKILL.md"), fallback_name="x")

    def test_missing_frontmatter_is_lenient(self):
        """Claude Code allows SKILL.md without frontmatter (e.g. tr-router).
        Parser must degrade to fallback_name + empty description + full body."""
        skill = parse_skill(
            "# just markdown\nno frontmatter\n",
            Path("/x/SKILL.md"),
            fallback_name="dirname",
        )
        assert skill.name == "dirname"
        assert skill.description == ""
        assert "just markdown" in skill.body
        assert skill.allowed_tools is None

    def test_unclosed_frontmatter_raises(self):
        """A `---` opener with no closer is malformed, not 'no frontmatter'."""
        text = "---\nname: x\ndescription: never closed\nbody continues...\n"
        with pytest.raises(SkillParseError, match="never closed"):
            parse_skill(text, Path("/x"), fallback_name="x")

    def test_invalid_yaml_in_frontmatter(self):
        text = "---\nname: [unclosed\n---\nbody\n"
        with pytest.raises(SkillParseError, match="invalid YAML"):
            parse_skill(text, Path("/x"), fallback_name="x")

    def test_frontmatter_not_a_mapping(self):
        text = "---\n- list\n- items\n---\nbody\n"
        with pytest.raises(SkillParseError, match="mapping"):
            parse_skill(text, Path("/x"), fallback_name="x")


# ────────────────────────────────────────────────────────────────────────────
# load_skill
# ────────────────────────────────────────────────────────────────────────────

class TestLoadSkill:
    def test_loads_from_disk(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: d\n---\nbody\n",
            encoding="utf-8",
        )

        skill = load_skill(tmp_path, "my-skill")

        assert skill.name == "my-skill"
        assert skill.body == "body"

    def test_missing_skill_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_skill(tmp_path, "nope")


# ────────────────────────────────────────────────────────────────────────────
# discover_skills
# ────────────────────────────────────────────────────────────────────────────

class TestDiscoverSkills:
    def test_finds_all_with_skill_md(self, tmp_path):
        for n in ("a", "b", "c"):
            d = tmp_path / n
            d.mkdir()
            (d / "SKILL.md").write_text(
                f"---\nname: {n}\ndescription: d\n---\nbody-{n}\n",
                encoding="utf-8",
            )

        result = discover_skills(tmp_path)

        assert set(result) == {"a", "b", "c"}
        assert result["a"].body == "body-a"

    def test_skips_dirs_without_skill_md(self, tmp_path):
        (tmp_path / "real").mkdir()
        (tmp_path / "real" / "SKILL.md").write_text(
            "---\nname: real\ndescription: d\n---\n", encoding="utf-8"
        )
        (tmp_path / "empty").mkdir()  # no SKILL.md
        (tmp_path / "loose-file.md").write_text("---\nname: x\n---\n")  # not in dir

        result = discover_skills(tmp_path)
        assert set(result) == {"real"}

    def test_skips_unparseable_skills(self, tmp_path):
        (tmp_path / "good").mkdir()
        (tmp_path / "good" / "SKILL.md").write_text(
            "---\nname: good\ndescription: d\n---\n", encoding="utf-8"
        )
        (tmp_path / "broken").mkdir()
        # Open --- without close = malformed (vs no --- at all which is now legal)
        (tmp_path / "broken" / "SKILL.md").write_text(
            "---\nname: x\nbut no closer\nbody...\n",
            encoding="utf-8",
        )

        result = discover_skills(tmp_path)
        assert set(result) == {"good"}

    def test_missing_root(self, tmp_path):
        assert discover_skills(tmp_path / "nope") == {}


# ────────────────────────────────────────────────────────────────────────────
# Real-world compatibility: .claude/skills/triz-router (the M2 PoC target)
# ────────────────────────────────────────────────────────────────────────────

class TestRealClaudeSkills:
    def test_triz_router_loads(self):
        skill = load_skill(_REAL_SKILLS_DIR, "triz-router")

        assert skill.name == "triz-router"
        assert "TRIZ" in skill.description
        # Body should contain the routing decision tree marker
        assert "路由決策樹" in skill.body
        assert skill.allowed_tools is None  # not set in real file yet

    def test_discover_finds_all_real_skills(self):
        skills = discover_skills(_REAL_SKILLS_DIR)
        # At minimum, the M2 PoC target must be discoverable
        assert "triz-router" in skills
        # And all the other TRIZ/TR skills the project relies on
        for expected in ("triz-scoping", "triz-model", "triz-contradict",
                         "triz-verify", "triz-wi", "tr-router"):
            assert expected in skills, f"missing skill: {expected}"


# ────────────────────────────────────────────────────────────────────────────
# Lint: every real skill must meet baseline quality bars
# ────────────────────────────────────────────────────────────────────────────

# Skills authored by the project — anything present in .claude/skills/
# (sub-dirs only). pytest discovers these at collect time so missing skills
# fail fast.
_ALL_REAL_SKILL_DIRS = sorted(
    p.name for p in _REAL_SKILLS_DIR.iterdir()
    if p.is_dir() and (p / "SKILL.md").is_file()
)


@pytest.mark.parametrize("skill_dir", _ALL_REAL_SKILL_DIRS)
class TestSkillLint:
    """Run once per skill — no skill is skipped."""

    def test_loads_without_error(self, skill_dir):
        """Parser must accept the SKILL.md (frontmatter optional, body any)."""
        load_skill(_REAL_SKILLS_DIR, skill_dir)

    def test_body_is_substantial(self, skill_dir):
        """A 200-char floor catches accidentally-empty SKILL.md files. Real
        skills run from 2KB to 25KB; nothing legitimate sits below 200."""
        skill = load_skill(_REAL_SKILLS_DIR, skill_dir)
        assert len(skill.body) >= 200, (
            f"{skill_dir} body too short ({len(skill.body)} chars) — "
            f"likely placeholder or accidentally truncated"
        )

    def test_body_has_some_structure(self, skill_dir):
        """Every skill body should expose at least one markdown heading.
        Headings indicate sections (Phase, Step, Overview, etc.) — without
        them the prompt is just a wall of text."""
        skill = load_skill(_REAL_SKILLS_DIR, skill_dir)
        assert "\n#" in skill.body or skill.body.startswith("#"), (
            f"{skill_dir} body has no markdown headings — wall of text"
        )

    def test_name_matches_directory_when_set(self, skill_dir):
        """If frontmatter declares `name`, it must match the directory name —
        otherwise the discoverable identity (dir name) and the declared
        identity diverge and downstream resolution breaks."""
        skill = load_skill(_REAL_SKILLS_DIR, skill_dir)
        assert skill.name == skill_dir, (
            f"{skill_dir}/SKILL.md declares name={skill.name!r} but lives "
            f"in dir {skill_dir!r} — these must match"
        )
