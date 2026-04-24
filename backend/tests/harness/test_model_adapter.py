"""Tests for harness/model_adapter.py — message extraction + token emission."""

from unittest.mock import patch

import pytest

from app.harness.model_adapter import (
    HarnessModel,
    _extract_system_prompt,
    _extract_user_message,
    emit_token_usage,
)
from pydantic_ai.messages import ModelRequest, SystemPromptPart, UserPromptPart
from pydantic_ai.usage import RequestUsage


# ---------------------------------------------------------------------------
# Message extraction
# ---------------------------------------------------------------------------


def test_extract_system_prompt():
    messages = [
        ModelRequest(parts=[
            SystemPromptPart(content="You are a TRIZ expert."),
            UserPromptPart(content="Solve this contradiction."),
        ]),
    ]
    assert _extract_system_prompt(messages) == "You are a TRIZ expert."


def test_extract_system_prompt_multiple():
    messages = [
        ModelRequest(parts=[
            SystemPromptPart(content="Part 1."),
            SystemPromptPart(content="Part 2."),
            UserPromptPart(content="Hello."),
        ]),
    ]
    assert _extract_system_prompt(messages) == "Part 1.\n\nPart 2."


def test_extract_user_message():
    messages = [
        ModelRequest(parts=[
            SystemPromptPart(content="System."),
            UserPromptPart(content="What is TRIZ?"),
        ]),
    ]
    assert _extract_user_message(messages) == "What is TRIZ?"


def test_extract_user_message_empty():
    messages = [
        ModelRequest(parts=[
            SystemPromptPart(content="System only."),
        ]),
    ]
    assert _extract_user_message(messages) == ""


# ---------------------------------------------------------------------------
# Token usage emission
# ---------------------------------------------------------------------------


def test_emit_token_usage_logs(caplog):
    usage = RequestUsage(input_tokens=100, output_tokens=50)
    with caplog.at_level("INFO"):
        emit_token_usage("test_agent", usage, latency_ms=250.0)
    assert "test_agent" in caplog.text
    assert "input=100" in caplog.text
    assert "output=50" in caplog.text


def test_emit_token_usage_skips_empty():
    usage = RequestUsage()  # all zeros
    # Should not raise or log
    emit_token_usage("test_agent", usage)


# ---------------------------------------------------------------------------
# HarnessModel properties
# ---------------------------------------------------------------------------


def test_harness_model_name_default():
    model = HarnessModel(agent_name="test")
    # Uses settings.default_model or "default"
    assert isinstance(model.model_name, str)


def test_harness_model_name_override():
    model = HarnessModel(agent_name="test", model_override="claude-sonnet-4-5-20250514")
    assert model.model_name == "claude-sonnet-4-5-20250514"


def test_harness_model_system():
    model = HarnessModel(agent_name="test")
    assert model.system == "harness"


# ---------------------------------------------------------------------------
# HarnessModel.request (requires mocking _call_provider)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_harness_model_request():
    model = HarnessModel(agent_name="test_solver")

    messages = [
        ModelRequest(parts=[
            SystemPromptPart(content="You are a solver."),
            UserPromptPart(content="Solve X."),
        ]),
    ]

    with patch("app.agents.base._call_provider") as mock_call:
        mock_call.return_value = '{"solution": "use principle 35"}'

        from pydantic_ai.models import ModelRequestParameters
        response = await model.request(
            messages,
            model_settings=None,
            model_request_parameters=ModelRequestParameters(),
        )

    assert response.parts[0].content == '{"solution": "use principle 35"}'
    mock_call.assert_called_once()
    # Verify the system + user were extracted correctly
    call_args = mock_call.call_args
    assert call_args[0][0] == "You are a solver."
    assert call_args[0][1] == "Solve X."
