"""Tests for LLM service retry logic, token management, and JSON cleaning.

WP-1.3 — TDD tests written before implementation.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import anthropic
import pytest
from pydantic import BaseModel

from app.agents.base import (
    call_llm_json,
    call_llm_json_parsed,
    retry_on_transient,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(text: str):
    """Build a minimal mock that looks like an Anthropic Messages response."""
    block = SimpleNamespace(text=text)
    return SimpleNamespace(content=[block])


class _SampleModel(BaseModel):
    name: str
    score: float


# ---------------------------------------------------------------------------
# 1. call_llm_json returns parsed content
# ---------------------------------------------------------------------------


class TestCallLlmJsonBasic:
    @patch("app.agents.base._get_anthropic")
    def test_returns_parsed_content(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response('{"ok": true}')

        result = call_llm_json("system prompt", "user prompt")
        assert result == '{"ok": true}'
        mock_client.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# 2. Retry on RateLimitError (up to 3 retries with exponential backoff)
# ---------------------------------------------------------------------------


class TestRetryOnRateLimitError:
    @patch("app.agents.base.time.sleep")
    @patch("app.agents.base._get_anthropic")
    def test_retries_on_rate_limit(self, mock_get_anthropic, mock_sleep):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client

        # Fail twice with RateLimitError, then succeed
        rate_err = anthropic.RateLimitError.__new__(anthropic.RateLimitError)
        rate_err.status_code = 429
        rate_err.message = "rate limit"
        rate_err.response = MagicMock()
        rate_err.body = None

        mock_client.messages.create.side_effect = [
            rate_err,
            rate_err,
            _make_response('{"retried": true}'),
        ]

        result = call_llm_json("sys", "usr")
        assert result == '{"retried": true}'
        assert mock_client.messages.create.call_count == 3
        # Verify exponential backoff: 1s then 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)


# ---------------------------------------------------------------------------
# 3. Retry on APIConnectionError
# ---------------------------------------------------------------------------


class TestRetryOnAPIConnectionError:
    @patch("app.agents.base.time.sleep")
    @patch("app.agents.base._get_anthropic")
    def test_retries_on_connection_error(self, mock_get_anthropic, mock_sleep):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client

        conn_err = anthropic.APIConnectionError.__new__(anthropic.APIConnectionError)
        conn_err.message = "connection failed"
        # APIConnectionError needs request attribute
        conn_err.request = MagicMock()

        mock_client.messages.create.side_effect = [
            conn_err,
            _make_response('{"connected": true}'),
        ]

        result = call_llm_json("sys", "usr")
        assert result == '{"connected": true}'
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# 4. No retry on BadRequestError (client error)
# ---------------------------------------------------------------------------


class TestNoRetryOnBadRequest:
    @patch("app.agents.base.time.sleep")
    @patch("app.agents.base._get_anthropic")
    def test_no_retry_on_bad_request(self, mock_get_anthropic, mock_sleep):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client

        bad_req = anthropic.BadRequestError.__new__(anthropic.BadRequestError)
        bad_req.status_code = 400
        bad_req.message = "bad request"
        bad_req.response = MagicMock()
        bad_req.body = None

        mock_client.messages.create.side_effect = bad_req

        with pytest.raises(anthropic.BadRequestError):
            call_llm_json("sys", "usr")

        assert mock_client.messages.create.call_count == 1
        mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Strips markdown code fences from JSON response
# ---------------------------------------------------------------------------


class TestJsonCodeFenceStripping:
    @patch("app.agents.base._get_anthropic")
    def test_strips_json_code_fences(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '```json\n{"clean": true}\n```'
        )

        result = call_llm_json("sys", "usr")
        assert result == '{"clean": true}'

    @patch("app.agents.base._get_anthropic")
    def test_strips_plain_code_fences(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '```\n{"clean": true}\n```'
        )

        result = call_llm_json("sys", "usr")
        assert result == '{"clean": true}'

    @patch("app.agents.base._get_anthropic")
    def test_no_fences_unchanged(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response('{"raw": true}')

        result = call_llm_json("sys", "usr")
        assert result == '{"raw": true}'


# ---------------------------------------------------------------------------
# 6. call_llm_json_parsed returns Pydantic model
# ---------------------------------------------------------------------------


class TestCallLlmJsonParsed:
    @patch("app.agents.base._get_anthropic")
    def test_returns_pydantic_model(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '{"name": "test", "score": 0.95}'
        )

        result = call_llm_json_parsed("sys", "usr", response_model=_SampleModel)
        assert isinstance(result, _SampleModel)
        assert result.name == "test"
        assert result.score == 0.95

    @patch("app.agents.base._get_anthropic")
    def test_parsed_strips_fences(self, mock_get_anthropic):
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_response(
            '```json\n{"name": "fenced", "score": 1.0}\n```'
        )

        result = call_llm_json_parsed("sys", "usr", response_model=_SampleModel)
        assert result.name == "fenced"


# ---------------------------------------------------------------------------
# 7. retry_on_transient decorator retries 5xx APIStatusError
# ---------------------------------------------------------------------------


class TestRetryOn5xxApiStatusError:
    @patch("app.agents.base.time.sleep")
    def test_retries_on_500(self, mock_sleep):
        call_count = 0

        @retry_on_transient
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                err = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
                err.status_code = 500
                err.message = "internal server error"
                err.response = MagicMock()
                err.body = None
                raise err
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3

    @patch("app.agents.base.time.sleep")
    def test_exhausts_retries(self, mock_sleep):
        """After max retries the error is re-raised."""

        @retry_on_transient
        def always_fails():
            err = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
            err.status_code = 502
            err.message = "bad gateway"
            err.response = MagicMock()
            err.body = None
            raise err

        with pytest.raises(anthropic.APIStatusError):
            always_fails()


# ---------------------------------------------------------------------------
# 8. Token usage warning
# ---------------------------------------------------------------------------


class TestTokenWarning:
    @patch("app.agents.base._get_anthropic")
    def test_warns_on_high_token_usage(self, mock_get_anthropic, caplog):
        """When input is large relative to max_tokens, a warning is logged."""
        mock_client = MagicMock()
        mock_get_anthropic.return_value = mock_client
        # Create a large prompt: 4000 chars => ~1000 tokens, with max_tokens=1024
        # 80% of 1024 = ~819 tokens; 1000 > 819 so should warn
        large_text = "x" * 4000
        mock_client.messages.create.return_value = _make_response('{"ok": true}')

        import logging

        with caplog.at_level(logging.WARNING, logger="app.agents.base"):
            call_llm_json("sys", large_text, max_tokens=1024)

        assert any("token" in r.message.lower() for r in caplog.records)
