"""Unit tests for _persist_consolidation_result (2026-05 fail-loud hardening).

Background：原版 `_persist_consolidation_result` 用 `except Exception` 把任何
DB 錯誤都當成「migration 未套用」處理 → silent pop Phase 3 欄位 → 結果 DB 半殘、
前端重整後出現 VerdictCard 殘留、Top2 替換徽章誤標等問題。

新版改成顯式回傳 `PersistenceOutcome`，並只在錯誤訊息明確帶有 column-missing
signature (42703 / PGRST204 / 'column does not exist' 等) 時才退回 legacy schema。

這個檔案驗證三種情境：
  1. 完整 payload upsert 成功 → status="ok"
  2. 第一次 upsert 拋 UndefinedColumn → 退回 legacy schema 成功 → status="partial"
  3. 第一次 upsert 拋非 schema 錯誤（network） → 直接 status="failed"
     **不能** silent pop Phase 3 欄位
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.agents.triz_solver import (
    _looks_like_missing_column_error,
    _persist_consolidation_result,
)
from app.models.schemas import (
    ConsolidationResult,
    DirectionGroup,
    EngineeringVerdictCard,
    PersistenceOutcome,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_consolidation_result() -> ConsolidationResult:
    """Build a minimal but realistic ConsolidationResult including Phase 3 fields."""
    return ConsolidationResult(
        status="compatible",
        adopted_directions={
            "TC-1": DirectionGroup(
                direction_id="DIR-1",
                direction_name="折疊/可變形",
                direction_summary="把外殼設計成可折疊以兼顧體積與剛性。",
                solutions=[],
                tc_count=2,
                pc_count=1,
                sf_count=0,
            )
        },
        conflict_report=None,
        integration_advice="採納 DIR-1。",
        was_user_picked={"TC-1": "DIR-1"},
        candidate_pools={},
        exhausted_contradictions=[],
        total_rounds=0,
    )


def _make_verdict_card() -> EngineeringVerdictCard:
    return EngineeringVerdictCard(
        project_id="proj-abc",
        consolidation_id="TCR-proj-abc",
        final_verdict="adopt_with_conditions",
        final_rationale="採用，但需驗證熱循環。",
        confidence=0.7,
    )


# ---------------------------------------------------------------------------
# _looks_like_missing_column_error — single-purpose discrimination test
# ---------------------------------------------------------------------------


class TestLooksLikeMissingColumnError:
    """確保判別函式不會把 generic exception 誤判成 schema 錯。"""

    @pytest.mark.parametrize(
        "msg",
        [
            'column "verdict_card" does not exist (SQLSTATE 42703)',
            "PGRST204: column 'candidate_pools' not in schema cache",
            "ERROR 42703: column total_rounds does not exist",
            "Could not find the 'verdict_card' column of 'triz_consolidation_results' in the schema cache",
        ],
    )
    def test_recognizes_schema_errors(self, msg: str) -> None:
        assert _looks_like_missing_column_error(Exception(msg))

    @pytest.mark.parametrize(
        "msg",
        [
            "Connection refused",
            "Network timeout",
            "JSON encoding failed: not a valid object",
            "RLS policy denies INSERT",
            "duplicate key violates unique constraint",
        ],
    )
    def test_does_not_misclassify_non_schema_errors(self, msg: str) -> None:
        # 這正是 2026-05 bug 的關鍵 — 非 schema 錯誤絕不能被當成 schema 錯處理
        assert not _looks_like_missing_column_error(Exception(msg))


# ---------------------------------------------------------------------------
# _persist_consolidation_result — three scenarios
# ---------------------------------------------------------------------------


class TestPersistConsolidationResult:
    """確保 persist 函式以 PersistenceOutcome 顯式回報，從不靜默吞錯。"""

    def test_full_upsert_success_returns_ok(self) -> None:
        """情境 1：完整 payload upsert 成功 → status='ok'，所有 Phase 3 欄位都被寫入。"""
        # Arrange — supabase client mock：upsert 成功
        mock_table = MagicMock()
        mock_upsert = MagicMock()
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = MagicMock(data=[{"id": "TCR-proj-abc"}])
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch("app.core.supabase.get_supabase", return_value=mock_sb):
            outcome = _persist_consolidation_result(
                project_id="proj-abc-12345678",
                result=_make_consolidation_result(),
                intra_compatibility=[],
                verdict_card=_make_verdict_card(),
            )

        # Assert
        assert isinstance(outcome, PersistenceOutcome)
        assert outcome.status == "ok"
        assert outcome.reason is None
        # 確認所有 Phase 3 欄位都進了 payload
        actual_payload = mock_table.upsert.call_args[0][0]
        assert "verdict_card" in actual_payload
        assert "was_user_picked" in actual_payload
        assert actual_payload["was_user_picked"] == {"TC-1": "DIR-1"}
        assert "candidate_pools" in actual_payload
        assert "exhausted_contradictions" in actual_payload
        assert "total_rounds" in actual_payload
        assert "intra_compatibility" in actual_payload
        # outcome.columns_written 應記錄這些欄位
        for col in [
            "verdict_card",
            "was_user_picked",
            "candidate_pools",
            "intra_compatibility",
            "total_rounds",
        ]:
            assert col in outcome.columns_written

    def test_missing_column_falls_back_to_legacy_returns_partial(self) -> None:
        """情境 2：第一次拋 column missing → legacy fallback 成功 → status='partial'。"""
        # Arrange — 第一次 upsert 拋「column does not exist」，第二次 (legacy) 成功
        first_call = MagicMock(
            side_effect=Exception(
                "ERROR: column \"verdict_card\" does not exist (SQLSTATE 42703)"
            )
        )
        second_call = MagicMock(return_value=MagicMock(data=[{"id": "TCR-proj-abc"}]))

        mock_upsert_obj = MagicMock()
        mock_upsert_obj.execute.side_effect = [
            first_call.side_effect,  # 第一次 raise
            second_call.return_value,  # 第二次 return
        ]
        mock_table = MagicMock()
        mock_table.upsert.return_value = mock_upsert_obj
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch("app.core.supabase.get_supabase", return_value=mock_sb):
            outcome = _persist_consolidation_result(
                project_id="proj-abc-12345678",
                result=_make_consolidation_result(),
                intra_compatibility=[],
                verdict_card=_make_verdict_card(),
            )

        # Assert — partial + reason 提示要跑 migration
        assert outcome.status == "partial"
        assert outcome.reason is not None
        assert "migration" in outcome.reason.lower() or "phase 3" in outcome.reason.lower()
        # 確認 upsert 被呼叫了 2 次（full + legacy）
        assert mock_table.upsert.call_count == 2
        # 第二次的 payload 應該不包含 Phase 3 欄位
        legacy_payload = mock_table.upsert.call_args_list[1][0][0]
        assert "verdict_card" not in legacy_payload
        assert "was_user_picked" not in legacy_payload
        assert "candidate_pools" not in legacy_payload
        # 但仍包含 legacy 欄位
        assert "status" in legacy_payload
        assert "adopted_directions" in legacy_payload

    def test_non_schema_error_returns_failed_without_popping_phase3(self) -> None:
        """情境 3 — 2026-05 bug 的核心防禦：

        非 schema 錯誤（network / RLS / JSON）絕對**不能**被當成 schema 錯而
        silent pop Phase 3 欄位再重試 — 那樣會把 DB 寫成半殘 row。新版應該
        直接回 status='failed' 讓 FE 提示重試。
        """
        # Arrange — upsert 拋網路錯
        mock_upsert_obj = MagicMock()
        mock_upsert_obj.execute.side_effect = Exception("Connection refused: backend timeout")
        mock_table = MagicMock()
        mock_table.upsert.return_value = mock_upsert_obj
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_table

        with patch("app.core.supabase.get_supabase", return_value=mock_sb):
            outcome = _persist_consolidation_result(
                project_id="proj-abc-12345678",
                result=_make_consolidation_result(),
                intra_compatibility=[],
                verdict_card=_make_verdict_card(),
            )

        # Assert
        assert outcome.status == "failed"
        assert outcome.reason is not None
        assert "connection refused" in outcome.reason.lower()
        assert outcome.columns_written == []
        # 關鍵：upsert 只被呼叫 1 次（沒退到 legacy fallback）
        # 這證明非 schema 錯誤不會 silent pop Phase 3 columns
        assert mock_table.upsert.call_count == 1
        # 第一次 payload 包含 Phase 3 欄位（原本就是要寫進去的）
        first_payload = mock_table.upsert.call_args_list[0][0][0]
        assert "verdict_card" in first_payload
        assert "was_user_picked" in first_payload

    def test_supabase_client_init_failure_returns_failed(self) -> None:
        """情境 4 — get_supabase() 本身失敗 (例如 env 未設定) → status='failed'。"""
        with patch(
            "app.core.supabase.get_supabase",
            side_effect=RuntimeError("SUPABASE_URL not configured"),
        ):
            outcome = _persist_consolidation_result(
                project_id="proj-abc-12345678",
                result=_make_consolidation_result(),
                intra_compatibility=[],
                verdict_card=_make_verdict_card(),
            )

        assert outcome.status == "failed"
        assert outcome.reason is not None
        assert "supabase" in outcome.reason.lower()
