"""Tests for TRIZ domain tools — verify Tool ABC wrappers work correctly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.triz.tools import (
    CCICalculateTool,
    MatrixLookupTool,
    ParamMapTool,
    SIMComputeTool,
    TrizStateAdvanceTool,
    TrizStateReadTool,
    TrizStateWriteTool,
)
from app.triz.kb.loader import KBLoader
from app.triz.state_manager import TrizStateManager

KB_ROOT = Path(
    "/home/os-sunnie.gd.weng/python_workstation/sunny_01/"
    "RD_copilot_system/rd_assistant_design_system/triz_knowledge_base"
)


# ── Fixtures ────────────────────────────────────────────���───────────


@pytest.fixture
def kb():
    if not KB_ROOT.exists():
        pytest.skip("KB root not found")
    return KBLoader(KB_ROOT)


@pytest.fixture
def state_mgr(tmp_path):
    return TrizStateManager(tmp_path)


@pytest.fixture
def state_with_session(state_mgr):
    """State manager with a created session."""
    state_mgr.create_session("test-tools", "test problem", specs={"x": 1})
    return state_mgr


# ── MatrixLookup Tests ────────────────────────────────���─────────────


class TestMatrixLookupTool:
    def test_valid_lookup(self, kb):
        tool = MatrixLookupTool(kb)
        result = tool.run(improve_id=10, worsen_id=7)
        assert not result.is_error
        data = json.loads(result.content)
        assert data["principles"] == [15, 9, 12, 37]
        assert data["improve"]["id"] == 10
        assert data["worsen"]["id"] == 7

    def test_invalid_improve_id(self, kb):
        tool = MatrixLookupTool(kb)
        result = tool.run(improve_id=99, worsen_id=7)
        assert result.is_error
        assert "Invalid" in result.content

    def test_invalid_worsen_id(self, kb):
        tool = MatrixLookupTool(kb)
        result = tool.run(improve_id=10, worsen_id=0)
        assert result.is_error

    def test_same_parameter(self, kb):
        tool = MatrixLookupTool(kb)
        result = tool.run(improve_id=10, worsen_id=10)
        assert not result.is_error
        data = json.loads(result.content)
        assert data["principles"] == []

    def test_all_ebike_tcs(self, kb):
        """Verify all 5 ebike TC lookups through tool interface."""
        tool = MatrixLookupTool(kb)
        cases = [
            (10, 7, [15, 9, 12, 37]),
            (10, 1, [8, 1, 37, 18]),
            (31, 22, [19, 24, 3, 14]),
            (8, 17, [35, 39, 38]),
            (2, 14, [28, 2, 27]),
        ]
        for improve, worsen, expected in cases:
            result = tool.run(improve_id=improve, worsen_id=worsen)
            data = json.loads(result.content)
            assert data["principles"] == expected, f"TC({improve},{worsen}) mismatch"

    def test_schema(self, kb):
        tool = MatrixLookupTool(kb)
        schema = tool.to_anthropic_schema()
        assert schema["name"] == "MatrixLookup"
        assert "improve_id" in schema["input_schema"]["properties"]


# ── ParamMap Tests ──────────────────────────────────────────────────


class TestParamMapTool:
    def test_torque_mapping(self, kb):
        tool = ParamMapTool(kb)
        result = tool.run(description="馬達扭力密度")
        assert not result.is_error
        data = json.loads(result.content)
        assert len(data["candidates"]) == 5
        top_ids = [c["id"] for c in data["candidates"]]
        assert 10 in top_ids[:3]  # Force

    def test_empty_description(self, kb):
        tool = ParamMapTool(kb)
        result = tool.run(description="")
        assert result.is_error

    def test_custom_top_n(self, kb):
        tool = ParamMapTool(kb)
        result = tool.run(description="weight", top_n=3)
        data = json.loads(result.content)
        assert len(data["candidates"]) == 3

    def test_disambiguation_flag(self, kb):
        tool = ParamMapTool(kb)
        result = tool.run(description="something very generic")
        data = json.loads(result.content)
        assert data["needs_llm_disambiguation"] is True


# ── CCICalculate Tests ──────────────────────────────────────────────


class TestCCICalculateTool:
    def test_strong_evolution(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="reduced",
            energy="reduced",
            cognitive="simplified",
            trends_satisfied=3,
        )
        assert not result.is_error
        data = json.loads(result.content)
        assert data["cci"] == 0.0
        assert data["verdict"] == "Strong Evolution"

    def test_hard_patch(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="new_subsystem",
            energy="new_source",
            cognitive="new_model",
            trends_satisfied=0,
        )
        data = json.loads(result.content)
        assert data["cci"] == 1.0
        assert data["verdict"] == "Hard Patch"

    def test_ebike_scenario(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="added_no_interface",
            energy="reduced",
            cognitive="one_branch",
            trends_satisfied=2,
        )
        data = json.loads(result.content)
        expected = 0.30 * 0.50 + 0.25 * 0.00 + 0.20 * 0.50 + 0.25 * 0.33
        assert abs(data["cci"] - expected) < 0.001

    def test_invalid_structural(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="invalid",
            energy="reduced",
            cognitive="simplified",
            trends_satisfied=3,
        )
        assert result.is_error
        assert "invalid" in result.content.lower()

    def test_invalid_energy(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="reduced",
            energy="invalid",
            cognitive="simplified",
            trends_satisfied=3,
        )
        assert result.is_error

    def test_custom_total_trends(self):
        tool = CCICalculateTool()
        result = tool.run(
            structural="reduced",
            energy="reduced",
            cognitive="simplified",
            trends_satisfied=4,
            total_trends=4,
        )
        data = json.loads(result.content)
        assert data["scores"]["evolution_aligned"] == 0.0


# ── SIMCompute Tests ────────────────────────────────────────────────


class TestSIMComputeTool:
    def test_converged(self):
        tool = SIMComputeTool()
        result = tool.run(
            matrix={"SOL-TC1 × SOL-TC3": 0, "SOL-TC1 × SOL-TC4": 1, "SOL-TC3 × SOL-TC4": 0},
        )
        assert not result.is_error
        data = json.loads(result.content)
        assert data["verdict"] == "converged"
        assert data["summary"]["+1"] == 1
        assert data["summary"]["0"] == 2
        assert data["summary"]["-1"] == 0

    def test_has_conflicts(self):
        tool = SIMComputeTool()
        result = tool.run(
            matrix={"A × B": -1, "A × C": 0, "B × C": 1},
            iteration=1,
        )
        data = json.loads(result.content)
        assert data["verdict"] == "iterate"

    def test_ebike_sim(self):
        tool = SIMComputeTool()
        result = tool.run(matrix={
            "SOL-TC1 × SOL-TC3": 0,
            "SOL-TC1 × SOL-TC5": 0,
            "SOL-TC1 × SOL-TC4": 1,
            "SOL-TC3 × SOL-TC5": 1,
            "SOL-TC3 × SOL-TC4": 0,
            "SOL-TC5 × SOL-TC4": 0,
        })
        data = json.loads(result.content)
        assert data["summary"]["+1"] == 2
        assert data["summary"]["0"] == 4
        assert data["verdict"] == "converged"

    def test_invalid_score(self):
        tool = SIMComputeTool()
        result = tool.run(matrix={"A × B": 2})
        assert result.is_error
        assert "invalid score" in result.content.lower()

    def test_with_reasons(self):
        tool = SIMComputeTool()
        result = tool.run(
            matrix={"A × B": 1},
            synergy_reasons=["A helps B thermally"],
        )
        data = json.loads(result.content)
        assert len(data["synergies"]) == 1


# ── TrizStateRead Tests ────────────────────────────────────────────


class TestTrizStateReadTool:
    def test_no_session(self, state_mgr):
        tool = TrizStateReadTool(state_mgr)
        result = tool.run()
        assert result.is_error
        assert "not found" in result.content.lower()

    def test_full_read(self, state_with_session):
        tool = TrizStateReadTool(state_with_session)
        result = tool.run()
        assert not result.is_error
        data = json.loads(result.content)
        assert data["session_id"] == "test-tools"
        assert data["current_step"] == "step0"

    def test_read_step(self, state_with_session):
        tool = TrizStateReadTool(state_with_session)
        result = tool.run(step="step0")
        assert not result.is_error
        data = json.loads(result.content)
        assert data["step"] == "step0"
        assert data["data"]["completed"] is False

    def test_read_field(self, state_with_session):
        tool = TrizStateReadTool(state_with_session)
        result = tool.run(field="session_id")
        data = json.loads(result.content)
        assert data["value"] == "test-tools"

    def test_read_unknown_step(self, state_with_session):
        tool = TrizStateReadTool(state_with_session)
        result = tool.run(step="step99")
        assert result.is_error

    def test_read_unknown_field(self, state_with_session):
        tool = TrizStateReadTool(state_with_session)
        result = tool.run(field="nonexistent")
        assert result.is_error


# ── TrizStateWrite Tests ───────────────────────────────────────────


class TestTrizStateWriteTool:
    def test_no_session(self, state_mgr):
        tool = TrizStateWriteTool(state_mgr)
        result = tool.run(step="step0", data={"completed": True})
        assert result.is_error

    def test_write_step(self, state_with_session):
        tool = TrizStateWriteTool(state_with_session)
        result = tool.run(step="step0", data={"completed": True, "routing": "step1"})
        assert not result.is_error
        data = json.loads(result.content)
        assert data["ok"] is True
        assert len(data["hash"]) == 64  # SHA-256

        # Verify persistence
        read_tool = TrizStateReadTool(state_with_session)
        read_result = read_tool.run(step="step0")
        step_data = json.loads(read_result.content)["data"]
        assert step_data["completed"] is True
        assert step_data["routing"] == "step1"

    def test_write_unknown_field(self, state_with_session):
        tool = TrizStateWriteTool(state_with_session)
        result = tool.run(step="step0", data={"nonexistent_field": True})
        assert result.is_error

    def test_write_unknown_step(self, state_with_session):
        tool = TrizStateWriteTool(state_with_session)
        result = tool.run(step="step99", data={"completed": True})
        assert result.is_error


# ── TrizStateAdvance Tests ─────────────────────────────────────────


class TestTrizStateAdvanceTool:
    def test_no_session(self, state_mgr):
        tool = TrizStateAdvanceTool(state_mgr)
        result = tool.run(to_step="step1")
        assert result.is_error

    def test_advance_success(self, state_with_session):
        # First complete step0
        write_tool = TrizStateWriteTool(state_with_session)
        write_tool.run(step="step0", data={"completed": True})

        advance_tool = TrizStateAdvanceTool(state_with_session)
        result = advance_tool.run(to_step="step1")
        assert not result.is_error
        data = json.loads(result.content)
        assert data["ok"] is True
        assert data["current_step"] == "step1"

    def test_advance_not_completed(self, state_with_session):
        advance_tool = TrizStateAdvanceTool(state_with_session)
        result = advance_tool.run(to_step="step1")
        assert result.is_error
        assert "not completed" in result.content.lower()

    def test_advance_skip(self, state_with_session):
        write_tool = TrizStateWriteTool(state_with_session)
        write_tool.run(step="step0", data={"completed": True})

        advance_tool = TrizStateAdvanceTool(state_with_session)
        result = advance_tool.run(to_step="step3")
        assert result.is_error
        assert "skip" in result.content.lower()

    def test_invalid_step(self, state_with_session):
        advance_tool = TrizStateAdvanceTool(state_with_session)
        result = advance_tool.run(to_step="step99")
        assert result.is_error


# ── Registry Factory Tests ──────────────────────────────────────────


class TestTrizRegistry:
    def test_factory(self, tmp_path):
        if not KB_ROOT.exists():
            pytest.skip("KB root not found")
        from app.triz.registry import triz_tools
        tools = triz_tools(kb_root=KB_ROOT, state_dir=tmp_path)
        assert len(tools) == 7
        names = {t.name for t in tools}
        assert names == {
            "MatrixLookup", "ParamMap", "CCICalculate", "SIMCompute",
            "TrizStateRead", "TrizStateWrite", "TrizStateAdvance",
        }

    def test_all_have_schemas(self, tmp_path):
        if not KB_ROOT.exists():
            pytest.skip("KB root not found")
        from app.triz.registry import triz_tools
        tools = triz_tools(kb_root=KB_ROOT, state_dir=tmp_path)
        for tool in tools:
            schema = tool.to_anthropic_schema()
            assert schema["name"] == tool.name
            assert "input_schema" in schema
            assert schema["input_schema"]["type"] == "object"
