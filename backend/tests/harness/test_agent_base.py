"""Tests for harness/agent_base.py — HarnessAgent + TRIZ Solver dual path."""

import json
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from app.harness.agent_base import HarnessAgent


# ---------------------------------------------------------------------------
# HarnessAgent unit tests
# ---------------------------------------------------------------------------


class _MockOutput(BaseModel):
    answer: str = ""
    score: int = 0


def test_harness_agent_repr():
    agent = HarnessAgent(
        name="test",
        system_prompt="You are a tester.",
        output_type=_MockOutput,
    )
    assert "test" in repr(agent)
    assert "_MockOutput" in repr(agent)


def test_harness_agent_name():
    agent = HarnessAgent(
        name="solver_1",
        system_prompt="System.",
        output_type=_MockOutput,
    )
    assert agent.name == "solver_1"


def test_harness_agent_run_sync_success():
    agent = HarnessAgent(
        name="test",
        system_prompt="System.",
        output_type=_MockOutput,
    )

    with patch("app.agents.base.call_llm_json") as mock_call:
        mock_call.return_value = json.dumps({"answer": "42", "score": 100})
        result = agent.run_sync("What is the answer?")

    assert isinstance(result, _MockOutput)
    assert result.answer == "42"
    assert result.score == 100


def test_harness_agent_run_sync_empty_response():
    agent = HarnessAgent(
        name="test",
        system_prompt="System.",
        output_type=_MockOutput,
    )

    with patch("app.agents.base.call_llm_json") as mock_call:
        mock_call.return_value = ""
        result = agent.run_sync("empty")

    # Empty response → empty dict → defaults
    assert result.answer == ""
    assert result.score == 0


def test_harness_agent_run_sync_invalid_json():
    agent = HarnessAgent(
        name="test",
        system_prompt="System.",
        output_type=_MockOutput,
    )

    with patch("app.agents.base.call_llm_json") as mock_call:
        mock_call.return_value = "not valid json {"
        result = agent.run_sync("bad json")

    # Invalid JSON → empty dict → defaults
    assert result.answer == ""
    assert result.score == 0


def test_harness_agent_run_sync_validation_error():
    """Output type with required field (no default) should raise on missing data."""

    class _StrictOutput(BaseModel):
        required_field: str  # no default — must be present

    agent = HarnessAgent(
        name="strict",
        system_prompt="System.",
        output_type=_StrictOutput,
    )

    with patch("app.agents.base.call_llm_json") as mock_call:
        mock_call.return_value = json.dumps({"wrong_field": "value"})
        with pytest.raises(Exception):
            agent.run_sync("missing required")


def test_harness_agent_model_override():
    agent = HarnessAgent(
        name="test",
        system_prompt="System.",
        output_type=_MockOutput,
        model_override="claude-haiku-4-5",
    )

    with patch("app.agents.base.call_llm_json") as mock_call:
        mock_call.return_value = json.dumps({"answer": "ok"})
        agent.run_sync("test")

    # Verify the model override was passed
    call_kwargs = mock_call.call_args
    assert call_kwargs[1]["model"] == "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# TRIZ Solver dual-path tests
# ---------------------------------------------------------------------------


def test_solve_tc_legacy_path():
    """USE_HARNESS_AGENTS=False should use legacy path (call_llm_json directly)."""
    from app.models.schemas import TrizLookupRequest

    req = TrizLookupRequest(
        project_id="test",
        contradiction_id="c-1",
        natural_description="Weight vs Strength",
        type="TC",
        improving_param=14,
        worsening_param=1,
    )

    with patch("app.core.config.settings") as mock_settings, \
         patch("app.agents.triz_solver.call_llm_json") as mock_call, \
         patch("app.agents.triz_solver.lookup_matrix") as mock_matrix, \
         patch("app.agents.triz_solver.build_triz_tc_context") as mock_ctx:

        mock_settings.use_harness_agents = False
        mock_settings.fast_model = "test-model"
        mock_matrix.return_value = [1, 35, 28]
        mock_ctx.return_value = "TRIZ context here"
        mock_call.return_value = json.dumps({
            "suggestions": [
                {
                    "principle_number": 35,
                    "principle_name": "Parameter changes",
                    "suggestion": "Change material flexibility",
                }
            ]
        })

        from app.agents.triz_solver import _solve_tc_legacy
        result = _solve_tc_legacy(req)

    assert result.candidate_principles == [1, 35, 28]
    assert len(result.suggestions) == 1
    assert result.suggestions[0].path == "TC"
    assert result.suggestions[0].principle_number == 35


def test_solve_tc_harness_path():
    """USE_HARNESS_AGENTS=True should use harness path (HarnessAgent)."""
    from app.models.schemas import TrizLookupRequest

    req = TrizLookupRequest(
        project_id="test",
        contradiction_id="c-1",
        natural_description="Weight vs Strength",
        type="TC",
        improving_param=14,
        worsening_param=1,
    )

    with patch("app.agents.triz_solver.settings") as mock_settings, \
         patch("app.agents.base.call_llm_json") as mock_call, \
         patch("app.agents.triz_solver.lookup_matrix") as mock_matrix, \
         patch("app.agents.triz_solver.build_triz_tc_context") as mock_ctx:

        mock_settings.use_harness_agents = True
        mock_settings.fast_model = "test-model"
        mock_matrix.return_value = [1, 35, 28]
        mock_ctx.return_value = "TRIZ context here"
        mock_call.return_value = json.dumps({
            "suggestions": [
                {
                    "principle_number": 35,
                    "principle_name": "Parameter changes",
                    "suggestion": "Change material flexibility",
                    "path": "TC",
                }
            ]
        })

        from app.agents.triz_solver import _solve_tc_harness
        result = _solve_tc_harness(req)

    assert result.candidate_principles == [1, 35, 28]
    assert len(result.suggestions) == 1
    assert result.suggestions[0].path == "TC"
    assert result.suggestions[0].principle_number == 35
    assert result.mapped_improving == 14
    assert result.mapped_worsening == 1


def test_solve_tc_routing():
    """_solve_tc should route based on use_harness_agents flag."""
    from app.agents.triz_solver import _solve_tc
    from app.models.schemas import TrizLookupRequest

    req = TrizLookupRequest(
        project_id="test",
        contradiction_id="c-1",
        natural_description="Test",
        type="TC",
        improving_param=6,
        worsening_param=14,
    )

    # Test legacy routing
    with patch("app.agents.triz_solver.settings") as mock_settings, \
         patch("app.agents.triz_solver._solve_tc_legacy") as mock_legacy:
        mock_settings.use_harness_agents = False
        _solve_tc(req)
        mock_legacy.assert_called_once_with(req)

    # Test harness routing
    with patch("app.agents.triz_solver.settings") as mock_settings, \
         patch("app.agents.triz_solver._solve_tc_harness") as mock_harness:
        mock_settings.use_harness_agents = True
        _solve_tc(req)
        mock_harness.assert_called_once_with(req)
