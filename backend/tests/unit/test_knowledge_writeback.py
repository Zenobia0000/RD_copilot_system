"""Tests for knowledge writeback (auto-assetization) — WP-4.7.

TDD: these tests are written before the implementation.
All Supabase and LLM calls are mocked.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALL_ASSET_TYPES = [
    "design_pattern",
    "lesson_learned",
    "failure_mode",
    "contradiction_solution",
    "design_rule",
    "test_method",
]

PROJECT_ID = "proj-test-001"


def _mock_supabase_table_data():
    """Return mock data that each Supabase table query would return."""
    return {
        # alternatives table — selected alternative with mechanism
        "alternatives": [
            {
                "id": "alt-1",
                "project_id": PROJECT_ID,
                "name": "Belt Drive",
                "mechanism": "Timing belt with 3:1 ratio",
                "selected": True,
            }
        ],
        # triz_solutions table
        "triz_solutions": [
            {
                "id": "triz-1",
                "project_id": PROJECT_ID,
                "principle_name": "Segmentation",
                "suggestion": "Split motor into modular segments",
            }
        ],
        # risks table
        "risks": [
            {
                "id": "risk-1",
                "project_id": PROJECT_ID,
                "description": "Belt wear",
                "failure_mode": "Belt snap under load",
                "severity": 4,
                "mitigation": "Use reinforced kevlar belt",
            }
        ],
        # experiments table
        "experiments": [
            {
                "id": "exp-1",
                "project_id": PROJECT_ID,
                "name": "Belt tension test",
                "result": "Passed at 150N",
                "evidence_level": "E3",
            }
        ],
        # adverse_consequences (from assumptions or contradictions)
        "adverse_consequences": [
            {
                "id": "ac-1",
                "project_id": PROJECT_ID,
                "description": "Belt slippage at high torque",
                "worst_severity": "critical",
            }
        ],
        # contradictions table
        "contradictions": [
            {
                "id": "con-1",
                "project_id": PROJECT_ID,
                "description": "Increasing belt width improves grip but increases weight",
                "resolved": True,
                "triz_principles": "Segmentation, Prior Action",
            }
        ],
        # must_criteria table
        "must_criteria": [
            {
                "id": "must-1",
                "project_id": PROJECT_ID,
                "label": "Efficiency >= 95%",
                "threshold": "95%",
                "passed": True,
            }
        ],
        # knowledge_entries — existing entries (for idempotency test)
        "knowledge_entries": [],
    }


def _build_supabase_chain(rows):
    """Build a mock that supports .select(...).eq(...).execute() chain."""
    mock_resp = MagicMock()
    mock_resp.data = rows

    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.execute.return_value = mock_resp

    # Also support .insert(...).execute()
    chain.insert.return_value = chain

    return chain


def _make_supabase_mock(table_data: dict, *, existing_entries=None):
    """Create a Supabase client mock routing .table(name) to mock data."""
    if existing_entries is None:
        existing_entries = []

    insert_calls = []

    def table_router(name: str):
        chain = MagicMock()

        # select chain
        def select_fn(*args, **kwargs):
            eq_filters = {}

            eq_mock = MagicMock()

            def eq_fn(col, val):
                eq_filters[col] = val
                return eq_mock

            eq_mock.eq = eq_fn
            eq_mock.gte = lambda col, val: eq_mock

            def execute_fn():
                resp = MagicMock()
                if name == "knowledge_entries":
                    # Filter existing entries by asset_type if set
                    filtered = [
                        e for e in existing_entries
                        if all(e.get(k) == v for k, v in eq_filters.items())
                    ]
                    resp.data = filtered
                else:
                    resp.data = table_data.get(name, [])
                return resp

            eq_mock.execute = execute_fn
            return eq_mock

        chain.select = select_fn

        # insert chain
        def insert_fn(rows):
            insert_calls.append((name, rows))
            insert_mock = MagicMock()

            def exec_insert():
                resp = MagicMock()
                # Assign IDs to inserted rows
                inserted = []
                for r in (rows if isinstance(rows, list) else [rows]):
                    row = dict(r)
                    row["id"] = row.get("id", str(uuid.uuid4()))
                    inserted.append(row)
                resp.data = inserted
                return resp

            insert_mock.execute = exec_insert
            return insert_mock

        chain.insert = insert_fn
        return chain

    sb = MagicMock()
    sb.table = table_router
    return sb, insert_calls


def _llm_json_side_effect(system, user_message, **kwargs):
    """Return a fake LLM JSON response with title + content."""
    return json.dumps({
        "title": "Synthesized Knowledge Article",
        "content": "This is a synthesized knowledge article based on project data.",
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWritebackAllTypes:
    """Test writeback with all 6 asset types."""

    @patch("app.agents.knowledge_wb.call_llm_json", side_effect=_llm_json_side_effect)
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_writeback_all_types(self, mock_get_sb, mock_llm):
        from app.agents.knowledge_wb import writeback_knowledge

        table_data = _mock_supabase_table_data()
        sb, insert_calls = _make_supabase_mock(table_data)
        mock_get_sb.return_value = sb

        result = writeback_knowledge(PROJECT_ID, asset_types=None)

        # Should produce 6 assets (one per type)
        assert result.written_count == 6
        assert len(result.assets) == 6

        returned_types = {a.asset_type for a in result.assets}
        assert returned_types == set(ALL_ASSET_TYPES)

        # Each asset should have a title and id
        for asset in result.assets:
            assert asset.title
            assert asset.id

        # LLM should have been called 6 times (once per type)
        assert mock_llm.call_count == 6

        # Should have inserted 6 rows into knowledge_entries
        ke_inserts = [c for c in insert_calls if c[0] == "knowledge_entries"]
        assert len(ke_inserts) == 6


class TestWritebackFilteredTypes:
    """Test writeback with specific asset_types filter."""

    @patch("app.agents.knowledge_wb.call_llm_json", side_effect=_llm_json_side_effect)
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_writeback_two_types(self, mock_get_sb, mock_llm):
        from app.agents.knowledge_wb import writeback_knowledge

        table_data = _mock_supabase_table_data()
        sb, insert_calls = _make_supabase_mock(table_data)
        mock_get_sb.return_value = sb

        result = writeback_knowledge(
            PROJECT_ID, asset_types=["design_pattern", "failure_mode"]
        )

        assert result.written_count == 2
        assert len(result.assets) == 2

        returned_types = {a.asset_type for a in result.assets}
        assert returned_types == {"design_pattern", "failure_mode"}

        assert mock_llm.call_count == 2


class TestWritebackIdempotency:
    """Running writeback twice should not create duplicates."""

    @patch("app.agents.knowledge_wb.call_llm_json", side_effect=_llm_json_side_effect)
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_idempotent_no_duplicates(self, mock_get_sb, mock_llm):
        from app.agents.knowledge_wb import writeback_knowledge

        table_data = _mock_supabase_table_data()

        # Simulate that all 6 types already exist in knowledge_entries
        existing = [
            {
                "id": f"ke-{i}",
                "project_id": PROJECT_ID,
                "asset_type": t,
                "title": "Synthesized Knowledge Article",
                "content": "existing content",
            }
            for i, t in enumerate(ALL_ASSET_TYPES)
        ]

        sb, insert_calls = _make_supabase_mock(table_data, existing_entries=existing)
        mock_get_sb.return_value = sb

        result = writeback_knowledge(PROJECT_ID, asset_types=None)

        # Nothing new should be written
        assert result.written_count == 0
        assert len(result.assets) == 0

        # No inserts should have been made
        ke_inserts = [c for c in insert_calls if c[0] == "knowledge_entries"]
        assert len(ke_inserts) == 0


class TestWritebackEmptyProject:
    """Test writeback for a project with no data returns 0 assets."""

    @patch("app.agents.knowledge_wb.call_llm_json", side_effect=_llm_json_side_effect)
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_empty_project(self, mock_get_sb, mock_llm):
        from app.agents.knowledge_wb import writeback_knowledge

        # All tables return empty
        empty_data = {k: [] for k in _mock_supabase_table_data()}
        sb, insert_calls = _make_supabase_mock(empty_data)
        mock_get_sb.return_value = sb

        result = writeback_knowledge(PROJECT_ID, asset_types=None)

        # No source data means no articles to synthesize
        assert result.written_count == 0
        assert len(result.assets) == 0

        # LLM should NOT be called when there's no source data
        assert mock_llm.call_count == 0


class TestWritebackEndpoint:
    """Integration test via FastAPI TestClient."""

    @patch("app.agents.knowledge_wb.call_llm_json", side_effect=_llm_json_side_effect)
    @patch("app.agents.knowledge_wb.get_supabase")
    def test_endpoint_returns_200(self, mock_get_sb, mock_llm):
        from app.main import app
        from app.middleware.auth import get_current_user

        table_data = _mock_supabase_table_data()
        sb, _ = _make_supabase_mock(table_data)
        mock_get_sb.return_value = sb

        # Bypass auth for this integration test
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": "test-user", "email": "test@example.com", "role": "authenticated",
        }
        client = TestClient(app)
        resp = client.post(
            "/api/v1/knowledge/writeback",
            json={"project_id": PROJECT_ID},
        )
        app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 200
        body = resp.json()
        assert body["written_count"] == 6
        assert len(body["assets"]) == 6
