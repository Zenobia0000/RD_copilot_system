"""Unit tests for harness custom agent loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness.agents import (
    AgentParseError,
    CustomAgent,
    discover_agents,
    load_agent,
    parse_agent,
)

# Path to the real .claude/agents/ root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_REAL_AGENTS_DIR = _PROJECT_ROOT / ".claude" / "agents"


# ────────────────────────────────────────────────────────────────────────────
# parse_agent
# ────────────────────────────────────────────────────────────────────────────

class TestParseAgent:
    def test_basic(self):
        text = (
            "---\n"
            "name: example\n"
            "description: A worker agent.\n"
            "---\n"
            "\n"
            "# Body\n"
            "Some system prompt.\n"
        )
        agent = parse_agent(text, Path("/fake/example.md"), fallback_name="example")

        assert agent.name == "example"
        assert agent.description == "A worker agent."
        assert agent.body == "# Body\nSome system prompt."
        assert agent.model is None
        assert agent.tools is None
        assert agent.source_path == Path("/fake/example.md")

    def test_with_model_and_tools_list(self):
        text = (
            "---\n"
            "name: triz-analyst\n"
            "description: Worker for Step 2 fan-out.\n"
            "model: opus\n"
            "tools:\n"
            "  - Read\n"
            "  - Grep\n"
            "  - WebSearch\n"
            "---\n"
            "body\n"
        )
        agent = parse_agent(text, Path("/x/a.md"), fallback_name="a")
        assert agent.name == "triz-analyst"
        assert agent.model == "opus"
        assert agent.tools == ("Read", "Grep", "WebSearch")

    def test_tools_as_comma_string(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "tools: Read, Write, Bash\n"
            "---\n"
            "body\n"
        )
        agent = parse_agent(text, Path("/x/a.md"), fallback_name="x")
        assert agent.tools == ("Read", "Write", "Bash")

    def test_empty_tools_list_is_strict_no_tools(self):
        """An explicit empty list means pure-chat agent — no tool surface.
        Must NOT collapse to None (which means inherit-all)."""
        text = (
            "---\n"
            "name: chat-only\n"
            "description: Pure chat, no tools.\n"
            "tools: []\n"
            "---\n"
            "body\n"
        )
        agent = parse_agent(text, Path("/x/a.md"), fallback_name="x")
        assert agent.tools == ()

    def test_fallback_name_when_frontmatter_omits_name(self):
        text = (
            "---\n"
            "description: only description\n"
            "---\n"
            "body\n"
        )
        agent = parse_agent(text, Path("/x/some_file.md"), fallback_name="some_file")
        assert agent.name == "some_file"

    def test_missing_frontmatter_raises(self):
        with pytest.raises(AgentParseError, match="missing YAML frontmatter"):
            parse_agent("just body, no fm\n", Path("/x/a.md"), fallback_name="x")

    def test_missing_description_raises(self):
        text = (
            "---\n"
            "name: nodesc\n"
            "---\n"
            "body\n"
        )
        with pytest.raises(AgentParseError, match="missing required 'description'"):
            parse_agent(text, Path("/x/a.md"), fallback_name="nodesc")

    def test_unclosed_frontmatter_raises(self):
        with pytest.raises(AgentParseError, match="never closed"):
            parse_agent("---\nname: x\n\nbody", Path("/x/a.md"), fallback_name="x")

    def test_frontmatter_not_mapping_raises(self):
        with pytest.raises(AgentParseError, match="must be a mapping"):
            parse_agent(
                "---\n- just\n- a\n- list\n---\nbody",
                Path("/x/a.md"),
                fallback_name="x",
            )

    def test_invalid_yaml_raises(self):
        with pytest.raises(AgentParseError, match="invalid YAML"):
            parse_agent(
                "---\nname: x\ndescription: 'unterminated\n---\nbody",
                Path("/x/a.md"),
                fallback_name="x",
            )

    def test_tools_wrong_type_raises(self):
        text = (
            "---\n"
            "name: x\n"
            "description: d\n"
            "tools: 42\n"
            "---\n"
            "body\n"
        )
        with pytest.raises(AgentParseError, match="tools must be"):
            parse_agent(text, Path("/x/a.md"), fallback_name="x")


# ────────────────────────────────────────────────────────────────────────────
# load_agent
# ────────────────────────────────────────────────────────────────────────────

class TestLoadAgent:
    def test_load_from_dir(self, tmp_path):
        (tmp_path / "worker.md").write_text(
            "---\n"
            "name: worker\n"
            "description: Test worker.\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )
        agent = load_agent(tmp_path, "worker")
        assert agent.name == "worker"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_agent(tmp_path, "nonexistent")


# ────────────────────────────────────────────────────────────────────────────
# discover_agents
# ────────────────────────────────────────────────────────────────────────────

class TestDiscoverAgents:
    def test_finds_multiple(self, tmp_path):
        (tmp_path / "a.md").write_text(
            "---\nname: a\ndescription: d\n---\nbody\n", encoding="utf-8"
        )
        (tmp_path / "b.md").write_text(
            "---\nname: b\ndescription: d\n---\nbody\n", encoding="utf-8"
        )
        agents = discover_agents(tmp_path)
        assert set(agents.keys()) == {"a", "b"}

    def test_skips_unparseable(self, tmp_path):
        # Valid one
        (tmp_path / "good.md").write_text(
            "---\nname: good\ndescription: d\n---\nbody\n", encoding="utf-8"
        )
        # Missing description (parse error → skipped)
        (tmp_path / "bad.md").write_text(
            "---\nname: bad\n---\nbody\n", encoding="utf-8"
        )
        agents = discover_agents(tmp_path)
        assert set(agents.keys()) == {"good"}

    def test_missing_dir_returns_empty(self, tmp_path):
        agents = discover_agents(tmp_path / "does-not-exist")
        assert agents == {}

    def test_skips_subdirs(self, tmp_path):
        # Subdirs (like .claude/skills/<name>/) are not the agent layout — flat *.md only
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "x.md").write_text(
            "---\nname: x\ndescription: d\n---\nbody\n", encoding="utf-8"
        )
        agents = discover_agents(tmp_path)
        assert agents == {}


# ────────────────────────────────────────────────────────────────────────────
# Real .claude/agents/ — sanity check the project's actual agents
# ────────────────────────────────────────────────────────────────────────────

class TestRealAgents:
    def test_triz_analyst_loads(self):
        agent = load_agent(_REAL_AGENTS_DIR, "triz-analyst")
        assert agent.name == "triz-analyst"
        assert agent.description  # non-empty
        assert agent.body  # non-empty
        # Per .claude/agents/triz-analyst.md frontmatter
        assert agent.model == "opus"
        assert agent.tools is not None
        assert "Read" in agent.tools

    def test_discover_finds_triz_analyst(self):
        agents = discover_agents(_REAL_AGENTS_DIR)
        assert "triz-analyst" in agents


# ────────────────────────────────────────────────────────────────────────────
# Lint: every real agent must meet baseline quality bars
# ────────────────────────────────────────────────────────────────────────────

_ALL_REAL_AGENT_FILES = sorted(
    p.stem for p in _REAL_AGENTS_DIR.glob("*.md") if p.is_file()
)


@pytest.mark.parametrize("agent_name", _ALL_REAL_AGENT_FILES)
class TestAgentLint:
    """Run once per real agent — no agent is skipped."""

    def test_loads_without_error(self, agent_name):
        load_agent(_REAL_AGENTS_DIR, agent_name)

    def test_has_description(self, agent_name):
        agent = load_agent(_REAL_AGENTS_DIR, agent_name)
        assert agent.description, (
            f"agent {agent_name!r} has empty description — required for "
            f"main loop to decide when to dispatch this subagent"
        )

    def test_body_is_substantial(self, agent_name):
        agent = load_agent(_REAL_AGENTS_DIR, agent_name)
        assert len(agent.body) >= 200, (
            f"agent {agent_name!r} body too short ({len(agent.body)} chars) — "
            f"subagent system prompt is likely placeholder"
        )

    def test_body_has_some_structure(self, agent_name):
        agent = load_agent(_REAL_AGENTS_DIR, agent_name)
        assert "\n#" in agent.body or agent.body.startswith("#"), (
            f"agent {agent_name!r} body has no markdown headings — "
            f"wall of text would confuse the subagent"
        )

    def test_name_matches_file_stem(self, agent_name):
        agent = load_agent(_REAL_AGENTS_DIR, agent_name)
        # Name in frontmatter must match file stem so dispatch can find it
        assert agent.name == agent_name, (
            f"agent file {agent_name}.md declares name={agent.name!r} — "
            f"file stem and frontmatter name must match for routing"
        )
