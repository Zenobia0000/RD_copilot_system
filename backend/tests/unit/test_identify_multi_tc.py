"""Unit + router tests for identify_multiple_tcs (3-stage TC pipeline).

Covers:
- 3-stage pipeline happy path (Stage 1 → 2 → 3)
- ADR-007 coercion (non-TC → type=null, invalid params → type=null)
- Dedup by (improving_param, worsening_param) pair
- Truncation to MAX_IDENTIFIED_TCS (5)
- Single-object normalization (Stage 2 LLM returns dict instead of list)
- LLM returns items wrapped in {"items": [...]}
- LLM exception → propagates from Stage 2
- Malformed JSON → propagates from Stage 2
- Stage 1 failure → graceful degradation (empty ProblemFrame)
- Stage 3 failure → fallback to top-5 candidates by confidence
- New fields (linked_kpis, why_selected, priority) pass through
- Backward compat when new fields missing
- Router 200 happy path
- Router 502 on agent exception
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from app.models.schemas import (
    MultiTcIdentifyRequest,
    MultiTcIdentifyResponse,
    IdentifiedTC,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req(**overrides) -> MultiTcIdentifyRequest:
    """Build a sample multi-TC identify request with sane defaults."""
    base = dict(
        project_id="proj-test",
        mission="設計輕量化 e-Bike 驅動單元",
        constraints=["重量 < 2500 g", "外徑 ≤ 111 mm"],
        kpis=["扭矩 >= 125 Nm", "效率 > 92%"],
        socraticAnswers=["承受彎曲應力約 125 Nm", "工作溫度 -10°C ~ 60°C"],
        existing_descriptions=["扭矩提升時重量必然增加"],
    )
    base.update(overrides)
    return MultiTcIdentifyRequest(**base)


_VALID_TC_1 = {
    "engineering_statement": "提升扭矩(#10)會惡化重量(#1)",
    "type": "TC",
    "confidence": 0.90,
    "rationale": "提升扭矩需要更大的磁鐵與齒輪，導致重量增加。",
    "improving_param": 10,
    "worsening_param": 1,
}

_VALID_TC_2 = {
    "engineering_statement": "提升效率(#22)會惡化製造複雜度(#36)",
    "type": "TC",
    "confidence": 0.85,
    "rationale": "高效率需要精密齒輪加工與嚴格公差。",
    "improving_param": 22,
    "worsening_param": 36,
}

_VALID_TC_3 = {
    "engineering_statement": "減少外部尺寸(#13)會惡化強度(#14)",
    "type": "TC",
    "confidence": 0.78,
    "rationale": "縮小外殼使壁厚降低，結構強度不足。",
    "improving_param": 13,
    "worsening_param": 14,
}


def _stage1_response(**overrides) -> str:
    """Build a Stage 1 (ProblemFrame) JSON response string."""
    data = {
        "system_boundary": "e-Bike drive unit",
        "kpi_priorities": [
            {"kpi": "torque >= 125 Nm", "severity": "hard", "failure_mode": "cannot climb"},
        ],
        "inferred_engineering_actions": [
            {
                "action": "increase magnet volume",
                "driven_by": "torque KPI",
                "likely_side_effects": ["weight increase"],
            },
        ],
        "critical_constraints": ["weight < 2500g"],
        "design_tensions": ["torque density vs weight"],
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


def _stage2_response(items: list[dict] | None = None) -> str:
    """Build a Stage 2 (candidates) JSON response string."""
    if items is None:
        items = [_VALID_TC_1, _VALID_TC_2, _VALID_TC_3]
    return json.dumps(items, ensure_ascii=False)


def _stage3_response(items: list[dict] | None = None) -> str:
    """Build a Stage 3 (selected / ranked) JSON response string."""
    if items is None:
        items = [
            {**_VALID_TC_1, "linked_kpis": ["torque >= 125 Nm"], "why_selected": "core tension", "priority": 1},
            {**_VALID_TC_2, "linked_kpis": ["efficiency > 92%"], "why_selected": "secondary", "priority": 2},
            {**_VALID_TC_3, "linked_kpis": [], "why_selected": "tertiary", "priority": 3},
        ]
    return json.dumps(items, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent-level tests — 3-stage pipeline
# ---------------------------------------------------------------------------

@patch("app.agents.analyst._extract_socratic_insights", return_value="- insight 1\n- insight 2")
@patch("app.agents.analyst.call_llm_json")
def test_happy_path_multiple_tcs(mock_llm, mock_insights):
    """3-stage pipeline: all stages succeed, 3 valid TCs returned."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response(),
        _stage3_response(),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert isinstance(resp, MultiTcIdentifyResponse)
    assert len(resp.items) == 3
    assert resp.items[0].engineering_statement == _VALID_TC_1["engineering_statement"]
    assert resp.items[0].type == "TC"
    assert resp.items[0].improving_param == 10
    assert resp.items[0].worsening_param == 1
    assert resp.items[1].improving_param == 22
    assert resp.items[2].improving_param == 13
    # Verify 3-stage enrichment fields
    assert resp.items[0].priority == 1
    assert resp.items[0].linked_kpis == ["torque >= 125 Nm"]
    assert resp.items[0].why_selected == "core tension"
    assert mock_llm.call_count == 3


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_adr007_coercion_non_tc_type(mock_llm, mock_insights):
    """ADR-007: non-TC type (e.g. 'PC') is coerced to type=null."""
    from app.agents.analyst import identify_multiple_tcs

    pc_item = {
        "engineering_statement": "齒輪模數必須大且必須小",
        "type": "PC",
        "confidence": 0.80,
        "improving_param": 10,
        "worsening_param": 1,
    }
    # Stage 3 returns the PC item as-is; ADR-007 coercion happens in _apply_adr007_and_dedup
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1, pc_item]),
        _stage3_response([
            {**_VALID_TC_1, "priority": 1, "why_selected": "main", "linked_kpis": []},
            {**pc_item, "priority": 2, "why_selected": "secondary", "linked_kpis": []},
        ]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 2

    # First should remain TC
    assert resp.items[0].type == "TC"
    assert resp.items[0].improving_param == 10

    # Second should be coerced to None (ADR-007)
    assert resp.items[1].type is None
    assert resp.items[1].improving_param is None
    assert resp.items[1].worsening_param is None
    assert "ADR-007" in (resp.items[1].rationale or "")


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_adr007_coercion_invalid_params(mock_llm, mock_insights):
    """ADR-007: type=TC but params out of range (1-39) → coerce to null."""
    from app.agents.analyst import identify_multiple_tcs

    bad_params = {
        "engineering_statement": "提升效率會惡化壽命",
        "type": "TC",
        "confidence": 0.75,
        "improving_param": 99,  # invalid: > 39
        "worsening_param": 0,   # invalid: < 1
    }
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([bad_params]),
        _stage3_response([{**bad_params, "priority": 1, "why_selected": "test", "linked_kpis": []}]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].type is None
    assert resp.items[0].improving_param is None
    assert resp.items[0].worsening_param is None
    assert "valid TRIZ 39" in (resp.items[0].rationale or "")


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_adr007_coercion_params_none(mock_llm, mock_insights):
    """ADR-007: type=TC but improving_param is None → coerce to null."""
    from app.agents.analyst import identify_multiple_tcs

    null_params = {
        "engineering_statement": "提升效率會惡化壽命",
        "type": "TC",
        "confidence": 0.75,
        "improving_param": None,
        "worsening_param": 5,
    }
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([null_params]),
        _stage3_response([{**null_params, "priority": 1, "why_selected": "test", "linked_kpis": []}]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].type is None


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_dedup_same_param_pair(mock_llm, mock_insights):
    """Dedup: same (improving, worsening) pair → keep first only."""
    from app.agents.analyst import identify_multiple_tcs

    dup = dict(_VALID_TC_1)
    dup["engineering_statement"] = "重複的矛盾描述"
    dup["confidence"] = 0.70
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1, dup, _VALID_TC_2]),
        _stage3_response([
            {**_VALID_TC_1, "priority": 1, "why_selected": "first", "linked_kpis": []},
            {**dup, "priority": 2, "why_selected": "dup", "linked_kpis": []},
            {**_VALID_TC_2, "priority": 3, "why_selected": "second", "linked_kpis": []},
        ]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 2
    # First TC-1 kept, duplicate dropped, TC-2 kept
    assert resp.items[0].engineering_statement == _VALID_TC_1["engineering_statement"]
    assert resp.items[1].engineering_statement == _VALID_TC_2["engineering_statement"]


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_dedup_null_pair_not_deduped(mock_llm, mock_insights):
    """Dedup: (None, None) pairs should NOT be deduped against each other."""
    from app.agents.analyst import identify_multiple_tcs

    null_tc_1 = {
        "engineering_statement": "描述 A",
        "type": None,
        "improving_param": None,
        "worsening_param": None,
    }
    null_tc_2 = {
        "engineering_statement": "描述 B",
        "type": None,
        "improving_param": None,
        "worsening_param": None,
    }
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([null_tc_1, null_tc_2]),
        _stage3_response([
            {**null_tc_1, "priority": 1, "why_selected": "a", "linked_kpis": []},
            {**null_tc_2, "priority": 2, "why_selected": "b", "linked_kpis": []},
        ]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 2  # both kept


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_truncation_to_max_identified_tcs(mock_llm, mock_insights):
    """More than MAX_IDENTIFIED_TCS (5) items → truncated to 5."""
    from app.agents.analyst import identify_multiple_tcs

    items = []
    for i in range(8):
        items.append({
            "engineering_statement": f"TC-{i}",
            "type": "TC",
            "confidence": 0.80,
            "improving_param": i + 1,
            "worsening_param": i + 10 if i + 10 <= 39 else 39,
            "priority": i + 1,
            "why_selected": f"reason {i}",
            "linked_kpis": [],
        })
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response(items),
        _stage3_response(items),  # Stage 3 returns all 8
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) <= 5


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_single_object_normalization(mock_llm, mock_insights):
    """Stage 2 LLM returns a single dict (not wrapped in list) → normalized."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        _stage1_response(),
        json.dumps(_VALID_TC_1),  # Stage 2: single dict, not a list
        _stage3_response([{**_VALID_TC_1, "priority": 1, "why_selected": "only", "linked_kpis": []}]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].improving_param == 10
    assert resp.items[0].type == "TC"


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_items_wrapper_normalization(mock_llm, mock_insights):
    """Stage 2 LLM returns {"items": [...]} — should unwrap correctly."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        _stage1_response(),
        json.dumps({"items": [_VALID_TC_1, _VALID_TC_2]}),  # Stage 2: items wrapper
        _stage3_response([
            {**_VALID_TC_1, "priority": 1, "why_selected": "a", "linked_kpis": []},
            {**_VALID_TC_2, "priority": 2, "why_selected": "b", "linked_kpis": []},
        ]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 2


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_empty_list_returns_empty(mock_llm, mock_insights):
    """Stage 2 returns empty list → empty response (Stage 3 skipped)."""
    from app.agents.analyst import identify_multiple_tcs

    # Stage 3 is never called because candidates list is empty
    mock_llm.side_effect = [
        _stage1_response(),
        json.dumps([]),  # Stage 2: empty candidates
    ]

    resp = identify_multiple_tcs(_make_req())
    assert resp.items == []
    assert mock_llm.call_count == 2  # Stage 3 skipped


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json", side_effect=RuntimeError("LLM service unavailable"))
def test_llm_exception_returns_empty(mock_llm, mock_insights):
    """LLM throws exception → Stage 1 recovers gracefully, Stage 2 propagates."""
    from app.agents.analyst import identify_multiple_tcs

    with pytest.raises(RuntimeError, match="LLM service unavailable"):
        identify_multiple_tcs(_make_req())


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json", return_value="not valid json {{")
def test_llm_malformed_json(mock_llm, mock_insights):
    """LLM returns invalid JSON → Stage 1 recovers, Stage 2 raises."""
    from app.agents.analyst import identify_multiple_tcs

    with pytest.raises(json.JSONDecodeError):
        identify_multiple_tcs(_make_req())


@patch("app.agents.analyst._extract_socratic_insights")
@patch("app.agents.analyst.call_llm_json")
def test_socratic_insights_injected(mock_llm, mock_insights):
    """Verify socratic insights are extracted and injected into prompt."""
    from app.agents.analyst import identify_multiple_tcs

    mock_insights.return_value = "- clarified insight"
    # Stage 2 returns empty → Stage 3 skipped
    mock_llm.side_effect = [
        _stage1_response(),
        json.dumps([]),
    ]

    req = _make_req(socraticAnswers=["answer A", "answer B"])
    identify_multiple_tcs(req)

    mock_insights.assert_called_once()
    args, _ = mock_insights.call_args
    assert args[0] == ["answer A", "answer B"]


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_non_dict_items_skipped(mock_llm, mock_insights):
    """Items that are not dicts (e.g. strings, ints) should be skipped."""
    from app.agents.analyst import identify_multiple_tcs

    # Stage 3 returns a mix of dicts and non-dicts;
    # _stage3_rank_and_select filters non-dicts before _apply_adr007_and_dedup
    stage3_mixed = [
        {**_VALID_TC_1, "priority": 1, "why_selected": "a", "linked_kpis": []},
        "garbage string",
        42,
        {**_VALID_TC_2, "priority": 2, "why_selected": "b", "linked_kpis": []},
    ]
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1, _VALID_TC_2]),
        json.dumps(stage3_mixed),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 2


# ---------------------------------------------------------------------------
# New 3-stage pipeline specific tests
# ---------------------------------------------------------------------------

@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_stage1_failure_graceful_degradation(mock_llm, mock_insights):
    """Stage 1 failure → Stage 2 still proceeds with empty ProblemFrame."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        "INVALID JSON FOR STAGE 1",  # Stage 1 fails gracefully
        _stage2_response([_VALID_TC_1]),
        _stage3_response([
            {**_VALID_TC_1, "priority": 1, "why_selected": "main", "linked_kpis": ["torque"]},
        ]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].type == "TC"
    assert mock_llm.call_count == 3  # all 3 stages called


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_stage3_failure_fallback_to_candidates(mock_llm, mock_insights):
    """Stage 3 failure → fallback to top-5 candidates by confidence."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1, _VALID_TC_2, _VALID_TC_3]),
        "INVALID JSON FOR STAGE 3",  # Stage 3 fails → fallback
    ]

    resp = identify_multiple_tcs(_make_req())
    # Should fall back to candidates sorted by confidence desc
    assert len(resp.items) == 3
    assert resp.items[0].confidence == 0.90   # TC_1
    assert resp.items[1].confidence == 0.85   # TC_2
    assert resp.items[2].confidence == 0.78   # TC_3
    # Fallback items should NOT have enrichment fields
    assert resp.items[0].why_selected is None
    assert resp.items[0].priority is None


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_new_fields_pass_through(mock_llm, mock_insights):
    """linked_kpis, why_selected, priority are correctly passed through."""
    from app.agents.analyst import identify_multiple_tcs

    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1]),
        _stage3_response([{
            **_VALID_TC_1,
            "linked_kpis": ["torque >= 125 Nm", "efficiency > 92%"],
            "why_selected": "核心任務張力，直接影響產品可行性",
            "priority": 1,
        }]),
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].linked_kpis == ["torque >= 125 Nm", "efficiency > 92%"]
    assert resp.items[0].why_selected == "核心任務張力，直接影響產品可行性"
    assert resp.items[0].priority == 1


@patch("app.agents.analyst._extract_socratic_insights", return_value="insights")
@patch("app.agents.analyst.call_llm_json")
def test_backward_compat_no_new_fields(mock_llm, mock_insights):
    """Stage 3 doesn't return new fields → IdentifiedTC uses defaults."""
    from app.agents.analyst import identify_multiple_tcs

    # Stage 3 returns items WITHOUT linked_kpis, why_selected, priority
    mock_llm.side_effect = [
        _stage1_response(),
        _stage2_response([_VALID_TC_1]),
        _stage3_response([_VALID_TC_1]),  # no enrichment fields
    ]

    resp = identify_multiple_tcs(_make_req())
    assert len(resp.items) == 1
    assert resp.items[0].linked_kpis == []
    assert resp.items[0].why_selected is None
    assert resp.items[0].priority is None


# ---------------------------------------------------------------------------
# Router-level tests (unchanged — mock at identify_multiple_tcs level)
# ---------------------------------------------------------------------------

def _sample_request_payload() -> dict:
    return {
        "project_id": "proj-test",
        "mission": "設計輕量化 e-Bike 驅動單元",
        "constraints": ["重量 < 2500 g"],
        "kpis": ["扭矩 >= 125 Nm"],
        "socraticAnswers": ["承受彎曲應力約 125 Nm"],
        "existing_descriptions": ["扭矩提升時重量必然增加"],
    }


@patch("app.routers.contradictions.identify_multiple_tcs")
def test_router_happy_path(mock_agent, client):
    mock_agent.return_value = MultiTcIdentifyResponse(
        items=[
            IdentifiedTC(**_VALID_TC_1),
            IdentifiedTC(**_VALID_TC_2),
        ]
    )
    resp = client.post(
        "/api/v1/contradictions/identify-multi",
        json=_sample_request_payload(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["type"] == "TC"
    assert body["items"][0]["improving_param"] == 10
    assert body["items"][1]["improving_param"] == 22
    mock_agent.assert_called_once()


@patch("app.routers.contradictions.identify_multiple_tcs", side_effect=RuntimeError("boom"))
def test_router_502_on_agent_exception(mock_agent, client):
    resp = client.post(
        "/api/v1/contradictions/identify-multi",
        json=_sample_request_payload(),
    )
    assert resp.status_code == 502
    body = resp.json()
    assert "Multi-TC 識別失敗" in body["error"]["message"]
