"""Tests for harness/prompt_assembler.py — context engineering."""

import pytest

from app.harness.prompt_assembler import (
    _estimate_tokens,
    assemble_prompt,
    build_cache_key,
)


def test_estimate_tokens():
    assert _estimate_tokens("hello world") == 2  # 11 chars / 4 ≈ 2
    assert _estimate_tokens("") == 0


def test_assemble_basic():
    system, user = assemble_prompt(
        "You are a solver.",
        dynamic_context={"problem": "Weight vs Strength"},
    )
    assert "You are a solver." in system
    assert "Weight vs Strength" in user
    assert '<context name="problem">' in user


def test_assemble_with_knowledge():
    system, user = assemble_prompt(
        "System template.",
        knowledge_blocks={"params": "39 parameters here..."},
        dynamic_context={"input": "test"},
    )
    assert '<knowledge name="params">' in system
    assert "39 parameters here..." in system
    assert "test" in user


def test_assemble_knowledge_within_budget():
    template = "X" * 40  # 10 tokens
    knowledge = "Y" * 400  # 100 tokens

    system, user = assemble_prompt(
        template,
        knowledge_blocks={"big": knowledge},
        token_budget=200,  # plenty of room
    )
    assert 'truncated="true"' not in system
    assert knowledge in system


def test_assemble_knowledge_truncated():
    template = "X" * 40  # 10 tokens
    knowledge = "Y" * 4000  # 1000 tokens

    system, user = assemble_prompt(
        template,
        knowledge_blocks={"big": knowledge},
        token_budget=50,  # only 40 tokens left after template
    )
    assert 'truncated="true"' in system
    assert "[... truncated to fit token budget ...]" in system
    # Should not contain the full knowledge
    assert knowledge not in system


def test_assemble_multiple_knowledge_blocks():
    system, user = assemble_prompt(
        "Template.",
        knowledge_blocks={
            "block_a": "Content A",
            "block_b": "Content B",
        },
        token_budget=10000,
    )
    assert '<knowledge name="block_a">' in system
    assert '<knowledge name="block_b">' in system


def test_assemble_empty_dynamic_context():
    system, user = assemble_prompt("Template.")
    assert "Template." in system
    assert user == ""


def test_assemble_multiple_dynamic_contexts():
    system, user = assemble_prompt(
        "Template.",
        dynamic_context={
            "prev_output": "L1 result here",
            "user_input": "Solve this TC",
        },
    )
    assert '<context name="prev_output">' in user
    assert '<context name="user_input">' in user


def test_cache_key_deterministic():
    key1 = build_cache_key("same prompt")
    key2 = build_cache_key("same prompt")
    assert key1 == key2


def test_cache_key_differs():
    key1 = build_cache_key("prompt A")
    key2 = build_cache_key("prompt B")
    assert key1 != key2
