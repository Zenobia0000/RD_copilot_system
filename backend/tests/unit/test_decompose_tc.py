"""Unit + router tests for decompose_tc_to_pcs (L2 WBS tasks 3.5 + 3.6).

Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from app.models.schemas import (
    ContradictionDecomposeRequest,
    ContradictionDecomposeResponse,
    DecomposedPC,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req(**overrides) -> ContradictionDecomposeRequest:
    """Build a sample decompose request with sane defaults."""
    base = dict(
        project_id="proj-test",
        parent_contradiction_id="c-001",
        engineering_statement="扭矩必須大但重量必須小",
        improving_param=10,
        worsening_param=1,
        severity="major",  # rule 1 of critic → always triggers
        mission="設計輕量化 e-Bike 驅動單元",
        constraints=["重量 < 2500 g"],
        kpis=["扭矩 >= 125 Nm"],
        socraticAnswers=["承受彎曲應力約 125 Nm", "外徑限制 111 mm"],
        candidate_principles=[1, 15, 35, 28],
        rd_manual=False,
    )
    base.update(overrides)
    return ContradictionDecomposeRequest(**base)


_VALID_PC_1 = {
    "derived_parameter": "齒輪模數",
    "subsystem_hint": "齒輪傳動",
    "physical_contradiction": "齒輪模數必須大（承受彎曲應力）且必須小（在外徑內達成減速比）",
    "pc_attribute_a": "大模數",
    "pc_attribute_not_a": "小模數",
    "separation_principle_id": "space.partition_combine",
    "separation_category": "space",
    "separation_rationale": "行星齒輪結構讓多個小模數齒輪分擔負載",
    "confidence": 0.85,
}

_VALID_PC_2 = {
    "derived_parameter": "殼體密度",
    "subsystem_hint": "外殼結構",
    "physical_contradiction": "殼體必須高密度且必須低密度",
    "pc_attribute_a": "高密度",
    "pc_attribute_not_a": "低密度",
    "separation_principle_id": "whole_part.composite",
    "separation_category": "whole_part",
    "separation_rationale": "高應力區用鋼材、低應力區用碳纖維",
    "confidence": 0.80,
}

_VALID_PC_3 = {
    "derived_parameter": "接觸面積",
    "subsystem_hint": "軸承配合",
    "physical_contradiction": "接觸面積必須大且必須小",
    "pc_attribute_a": "大接觸面積",
    "pc_attribute_not_a": "小接觸面積",
    "separation_principle_id": "time.pre_action",
    "separation_category": "time",
    "separation_rationale": "預應力階段接觸，工作階段脫離",
    "confidence": 0.72,
}


# ---------------------------------------------------------------------------
# Agent-level tests (3.5)
# ---------------------------------------------------------------------------

@patch("app.agents.analyst.should_trigger_pc_decomposition")
@patch("app.agents.analyst.call_llm_json")
def test_critic_not_triggered_returns_empty(mock_llm, mock_critic):
    """Rule 1 of WBS §3.3: if critic says no, skip LLM entirely."""
    from app.agents.analyst import decompose_tc_to_pcs

    mock_critic.return_value = (False, "L1 已足夠深")
    req = _make_req(severity="minor", candidate_principles=[1, 2, 3, 4, 5])
    resp = decompose_tc_to_pcs(req)

    assert isinstance(resp, ContradictionDecomposeResponse)
    assert resp.triggered is False
    assert resp.decomposed_pcs == []
    assert "L1 已足夠深" in resp.trigger_reason
    mock_llm.assert_not_called()


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="- insight 1\n- insight 2")
@patch("app.agents.analyst.call_llm_json")
def test_happy_path_three_distinct_pcs(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    mock_llm.return_value = json.dumps({
        "decomposed_pcs": [_VALID_PC_1, _VALID_PC_2, _VALID_PC_3],
        "reasoning": "Three-level decomposition across gear/housing/bearing.",
    })

    resp = decompose_tc_to_pcs(_make_req())
    assert resp.triggered is True
    assert len(resp.decomposed_pcs) == 3
    ids = {pc.separation_principle_id for pc in resp.decomposed_pcs}
    assert ids == {
        "space.partition_combine",
        "whole_part.composite",
        "time.pre_action",
    }
    assert "Three-level" in resp.reasoning


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_duplicate_derived_parameter_deduplicates(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    dup = dict(_VALID_PC_2)
    dup["derived_parameter"] = _VALID_PC_1["derived_parameter"]  # duplicate
    mock_llm.return_value = json.dumps({
        "decomposed_pcs": [_VALID_PC_1, dup, _VALID_PC_3],
        "reasoning": "test",
    })

    resp = decompose_tc_to_pcs(_make_req())
    assert resp.triggered is True
    # _VALID_PC_1 kept, dup dropped, _VALID_PC_3 kept → 2
    assert len(resp.decomposed_pcs) == 2
    params = [pc.derived_parameter for pc in resp.decomposed_pcs]
    assert params == ["齒輪模數", "接觸面積"]


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_invalid_separation_principle_id_rejected(mock_llm, mock_insights, mock_critic, caplog):
    from app.agents.analyst import decompose_tc_to_pcs

    bad = dict(_VALID_PC_2)
    bad["separation_principle_id"] = "fake.invalid"
    mock_llm.return_value = json.dumps({
        "decomposed_pcs": [_VALID_PC_1, bad],
        "reasoning": "test",
    })

    with caplog.at_level("WARNING"):
        resp = decompose_tc_to_pcs(_make_req())

    assert resp.triggered is True
    assert len(resp.decomposed_pcs) == 1
    assert resp.decomposed_pcs[0].derived_parameter == "齒輪模數"
    assert any("Rejecting invalid PC" in rec.message for rec in caplog.records)


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_llm_returns_empty_list(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    mock_llm.return_value = json.dumps({
        "decomposed_pcs": [],
        "reasoning": "no decomposition possible",
    })
    resp = decompose_tc_to_pcs(_make_req())
    assert resp.triggered is True
    assert resp.decomposed_pcs == []
    assert resp.reasoning == "no decomposition possible"


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json", side_effect=RuntimeError("LLM error"))
def test_llm_exception_returns_error_not_crash(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    resp = decompose_tc_to_pcs(_make_req())
    assert resp.triggered is True
    assert resp.decomposed_pcs == []
    assert "Decomposition failed" in resp.reasoning
    assert "LLM error" in resp.reasoning


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json", return_value="not valid json {{")
def test_llm_returns_malformed_json(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    resp = decompose_tc_to_pcs(_make_req())
    assert resp.triggered is True
    assert resp.decomposed_pcs == []
    assert "Decomposition failed" in resp.reasoning


@patch("app.agents.analyst.should_trigger_pc_decomposition", return_value=(True, "severity=major"))
@patch("app.agents.analyst._extract_socratic_insights")
@patch("app.agents.analyst.call_llm_json")
def test_socratic_insights_are_injected(mock_llm, mock_insights, mock_critic):
    from app.agents.analyst import decompose_tc_to_pcs

    mock_insights.return_value = "- clarified insight"
    mock_llm.return_value = json.dumps({"decomposed_pcs": [], "reasoning": "ok"})

    req = _make_req(socraticAnswers=["answer A", "answer B"])
    decompose_tc_to_pcs(req)

    mock_insights.assert_called_once()
    args, _ = mock_insights.call_args
    assert args[0] == ["answer A", "answer B"]


# ---------------------------------------------------------------------------
# Router-level tests (3.6)
# ---------------------------------------------------------------------------

def _sample_request_payload() -> dict:
    return {
        "project_id": "proj-test",
        "parent_contradiction_id": "c-001",
        "engineering_statement": "扭矩必須大但重量必須小",
        "improving_param": 10,
        "worsening_param": 1,
        "severity": "major",
        "mission": "m",
        "constraints": [],
        "kpis": [],
        "socraticAnswers": [],
        "candidate_principles": [1, 2, 3],
        "rd_manual": False,
    }


@patch("app.routers.contradictions.decompose_tc_to_pcs")
def test_router_happy_path(mock_agent, client):
    mock_agent.return_value = ContradictionDecomposeResponse(
        triggered=True,
        trigger_reason="severity=major",
        decomposed_pcs=[DecomposedPC(**_VALID_PC_1)],
        reasoning="ok",
    )
    resp = client.post(
        "/api/v1/contradictions/c-001/decompose",
        json=_sample_request_payload(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["triggered"] is True
    assert len(body["decomposed_pcs"]) == 1
    assert body["decomposed_pcs"][0]["derived_parameter"] == "齒輪模數"
    mock_agent.assert_called_once()


@patch("app.routers.contradictions.decompose_tc_to_pcs", side_effect=RuntimeError("boom"))
def test_router_502_on_agent_exception(mock_agent, client):
    resp = client.post(
        "/api/v1/contradictions/c-001/decompose",
        json=_sample_request_payload(),
    )
    assert resp.status_code == 502
    # Global error_handler middleware reshapes HTTPException.detail into
    # body["error"]["message"] (see app/middleware/error_handler.py).
    body = resp.json()
    assert "PC 分解失敗" in body["error"]["message"]
