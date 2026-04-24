"""Tests for SCAMPER feedback contradictions endpoint (WP-3.5).

TDD tests for:
- Deduplication via SequenceMatcher (>80% similarity = duplicate)
- Severity classification passthrough (fatal/major/minor)
- Supabase integration (mocked)
- Response format matches ScamperFeedbackResponse
"""

from unittest.mock import MagicMock, patch
import uuid

import pytest

from app.agents.scamper_feedback import process_scamper_feedback
from app.models.schemas import ScamperFeedbackResponse


def _mock_supabase(existing_rows: list[dict] | None = None):
    """Build a mock Supabase client with chainable query builder."""
    if existing_rows is None:
        existing_rows = []

    client = MagicMock()

    # SELECT chain: client.table("contradictions").select("*").eq("project_id", ...).execute()
    select_result = MagicMock()
    select_result.data = existing_rows

    select_chain = MagicMock()
    select_chain.eq.return_value = MagicMock(execute=MagicMock(return_value=select_result))

    # INSERT chain: client.table("contradictions").insert([...]).execute()
    def make_insert_result(rows):
        result = MagicMock()
        # Simulate Supabase returning rows with generated IDs
        result.data = [
            {**row, "id": row.get("id", str(uuid.uuid4()))} for row in rows
        ]
        return result

    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(
        side_effect=lambda: make_insert_result(insert_chain._last_rows)
    )

    def capture_insert(rows):
        insert_chain._last_rows = rows
        return insert_chain

    table_mock = MagicMock()
    table_mock.select.return_value = select_chain
    table_mock.insert.side_effect = capture_insert

    client.table.return_value = table_mock
    return client


# ---------------------------------------------------------------------------
# Test: deduplication — same description should not create duplicate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplication_skips_near_identical():
    """Contradiction with >80% similarity to existing one is skipped."""
    existing = [
        {"id": "c-001", "natural_description": "Motor torque conflicts with battery weight"},
    ]
    client = _mock_supabase(existing)

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Motor torque conflicts with battery weight", "severity": "major"},
            ],
        )

    assert result.created_count == 0
    assert result.deduplicated_count == 1
    assert result.contradiction_ids == []


@pytest.mark.asyncio
async def test_deduplication_allows_different_contradictions():
    """Sufficiently different contradictions are not deduplicated."""
    existing = [
        {"id": "c-001", "natural_description": "Motor torque conflicts with battery weight"},
    ]
    client = _mock_supabase(existing)

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Frame stiffness reduces rider comfort", "severity": "minor"},
            ],
        )

    assert result.created_count == 1
    assert result.deduplicated_count == 0


# ---------------------------------------------------------------------------
# Test: severity classification passthrough
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("severity", ["fatal", "major", "minor"])
async def test_severity_classification(severity):
    """Each severity value is passed through to the inserted row."""
    client = _mock_supabase(existing_rows=[])

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Some unique contradiction text", "severity": severity},
            ],
        )

    assert result.created_count == 1

    # Verify the inserted row has the correct severity
    insert_call = client.table.return_value.insert
    insert_call.assert_called_once()
    inserted_rows = insert_call.call_args[0][0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0]["severity"] == severity


# ---------------------------------------------------------------------------
# Test: contradictions are created in Supabase (mock)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_creates_contradictions_in_supabase():
    """Non-duplicate contradictions are inserted into the contradictions table."""
    client = _mock_supabase(existing_rows=[])

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Heat dissipation vs. compact size", "severity": "major"},
                {"description": "Cost reduction vs. material strength", "severity": "minor"},
            ],
        )

    assert result.created_count == 2
    assert result.deduplicated_count == 0
    assert len(result.contradiction_ids) == 2

    # Verify Supabase table("contradictions") was called
    client.table.assert_any_call("contradictions")

    # Verify inserted rows have correct fields
    insert_call = client.table.return_value.insert
    inserted_rows = insert_call.call_args[0][0]
    assert len(inserted_rows) == 2
    for row in inserted_rows:
        assert row["project_id"] == "proj-1"
        assert row["type"] == "TC"
        assert row["resolved"] is False
        assert "natural_description" in row


# ---------------------------------------------------------------------------
# Test: response format matches ScamperFeedbackResponse
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_response_format():
    """Return value is a valid ScamperFeedbackResponse."""
    client = _mock_supabase(existing_rows=[])

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Vibration damping vs. weight", "severity": "fatal"},
            ],
        )

    assert isinstance(result, ScamperFeedbackResponse)
    assert isinstance(result.created_count, int)
    assert isinstance(result.deduplicated_count, int)
    assert isinstance(result.contradiction_ids, list)


# ---------------------------------------------------------------------------
# Test: empty input
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_contradictions_list():
    """Empty new_contradictions list returns zero counts."""
    client = _mock_supabase(existing_rows=[])

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[],
        )

    assert result.created_count == 0
    assert result.deduplicated_count == 0
    assert result.contradiction_ids == []


# ---------------------------------------------------------------------------
# Test: deduplication within the same batch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplication_within_batch():
    """Two near-identical contradictions in the same batch — only the first is kept."""
    client = _mock_supabase(existing_rows=[])

    with patch("app.agents.scamper_feedback.get_supabase", return_value=client):
        result = await process_scamper_feedback(
            project_id="proj-1",
            new_contradictions=[
                {"description": "Motor torque conflicts with battery weight", "severity": "major"},
                {"description": "Motor torque conflicts with battery weight", "severity": "minor"},
            ],
        )

    assert result.created_count == 1
    assert result.deduplicated_count == 1
