"""Tests for harness/skill_loader.py — skill discovery + loading."""

import textwrap
from pathlib import Path

import pytest

from app.harness.skill_loader import (
    SKILL_REGISTRY,
    SkillDefinition,
    _parse_frontmatter,
    get_knowledge_skills,
    get_skill,
    get_skill_content,
    list_skills,
    load_all,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Save and restore SKILL_REGISTRY around each test."""
    saved = dict(SKILL_REGISTRY)
    SKILL_REGISTRY.clear()
    yield
    SKILL_REGISTRY.clear()
    SKILL_REGISTRY.update(saved)


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def test_parse_frontmatter_basic():
    text = textwrap.dedent("""\
        ---
        name: my_skill
        description: A test skill
        type: knowledge
        ---

        Body content here.
    """)
    meta, body = _parse_frontmatter(text)
    assert meta["name"] == "my_skill"
    assert meta["description"] == "A test skill"
    assert meta["type"] == "knowledge"
    assert "Body content here." in body


def test_parse_frontmatter_with_list():
    text = textwrap.dedent("""\
        ---
        name: tagged
        tags: [triz, params]
        ---

        Content.
    """)
    meta, body = _parse_frontmatter(text)
    assert meta["tags"] == ["triz", "params"]


def test_parse_frontmatter_no_frontmatter():
    text = "Just plain markdown content."
    meta, body = _parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_parse_frontmatter_quoted_values():
    text = textwrap.dedent("""\
        ---
        name: "quoted_name"
        description: 'single quoted'
        ---

        Body.
    """)
    meta, body = _parse_frontmatter(text)
    assert meta["name"] == "quoted_name"
    assert meta["description"] == "single quoted"


# ---------------------------------------------------------------------------
# load_all from filesystem
# ---------------------------------------------------------------------------


def test_load_all_from_real_skills_dir():
    """Load skills from the actual backend/app/skills/ directory."""
    skills_dir = Path(__file__).resolve().parents[2] / "app" / "skills"
    count = load_all(skills_dir)
    assert count >= 3  # triz_39_parameters, triz_separation_principles, triz_76_standards

    # Verify specific skills loaded
    assert get_skill("triz_39_parameters") is not None
    assert get_skill("triz_separation_principles") is not None
    assert get_skill("triz_76_standards") is not None


def test_load_all_skill_properties():
    """Verify skill metadata is parsed correctly."""
    skills_dir = Path(__file__).resolve().parents[2] / "app" / "skills"
    load_all(skills_dir)

    skill = get_skill("triz_39_parameters")
    assert skill is not None
    assert skill.skill_type == "knowledge"
    assert skill.cache_policy == "static"
    assert "parameter" in skill.description.lower() or "39" in skill.description
    assert skill.content  # Non-empty body


def test_load_all_nonexistent_dir():
    """Loading from a nonexistent directory returns 0."""
    count = load_all(Path("/tmp/nonexistent_skills_dir"))
    assert count == 0


def test_load_all_with_temp_skill(tmp_path):
    """Load a custom skill from a temporary directory."""
    skill_dir = tmp_path / "my_test_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: my_test_skill
        description: Test skill for unit testing
        type: knowledge
        cache_policy: dynamic
        ---

        This is test content for the skill.
        It has multiple lines.
    """))

    count = load_all(tmp_path)
    assert count == 1

    skill = get_skill("my_test_skill")
    assert skill is not None
    assert skill.description == "Test skill for unit testing"
    assert skill.skill_type == "knowledge"
    assert skill.cache_policy == "dynamic"
    assert "test content" in skill.content


# ---------------------------------------------------------------------------
# Registry accessors
# ---------------------------------------------------------------------------


def test_get_skill_content():
    skills_dir = Path(__file__).resolve().parents[2] / "app" / "skills"
    load_all(skills_dir)

    content = get_skill_content("triz_39_parameters")
    assert content is not None
    assert len(content) > 0


def test_get_skill_content_missing():
    assert get_skill_content("nonexistent") is None


def test_list_skills_sorted():
    skills_dir = Path(__file__).resolve().parents[2] / "app" / "skills"
    load_all(skills_dir)

    skills = list_skills()
    names = [s.name for s in skills]
    assert names == sorted(names)
    assert len(names) >= 3


def test_get_knowledge_skills():
    skills_dir = Path(__file__).resolve().parents[2] / "app" / "skills"
    load_all(skills_dir)

    knowledge = get_knowledge_skills()
    assert isinstance(knowledge, dict)
    assert "triz_39_parameters" in knowledge
    assert len(knowledge["triz_39_parameters"]) > 0


def test_skill_dir_without_skill_md(tmp_path):
    """Directories without SKILL.md are silently skipped."""
    (tmp_path / "empty_dir").mkdir()
    (tmp_path / "also_empty").mkdir()

    count = load_all(tmp_path)
    assert count == 0
