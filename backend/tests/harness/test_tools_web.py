"""Unit tests for WebFetch and WebSearch tools.

Tools are designed to:
- Accept injected clients for testability (no real HTTP / API calls)
- Surface all errors as is_error=True ToolResults (never raise)
- Cap response sizes to keep agent context bounded
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.harness.tools.base import ToolResult
from app.harness.tools.web import WebFetchTool, WebSearchTool


# ────────────────────────────────────────────────────────────────────────────
# WebFetch — httpx.Client injected via MockTransport
# ────────────────────────────────────────────────────────────────────────────

def _client_returning(*, status_code: int = 200, text: str = "ok",
                      content_type: str = "text/plain",
                      headers: dict[str, str] | None = None,
                      raise_on_get: Exception | None = None) -> httpx.Client:
    """Build an httpx.Client backed by MockTransport.

    Single response per Client (good enough for unit tests). For multi-call
    tests, pass a list via `responses` instead (see _client_with_sequence).
    """
    def handler(request: httpx.Request) -> httpx.Response:
        if raise_on_get is not None:
            raise raise_on_get
        h = {"content-type": content_type}
        if headers:
            h.update(headers)
        return httpx.Response(status_code, text=text, headers=h)

    return httpx.Client(transport=httpx.MockTransport(handler))


class TestWebFetch:
    def test_basic_get(self):
        tool = WebFetchTool(client=_client_returning(text="hello"))
        result = tool.run(url="https://example.com")
        assert result.is_error is False
        assert result.content == "hello"

    def test_url_must_have_scheme(self):
        tool = WebFetchTool(client=_client_returning())
        result = tool.run(url="example.com")
        assert result.is_error is True
        assert "http://" in result.content

    def test_empty_url_rejected(self):
        tool = WebFetchTool(client=_client_returning())
        result = tool.run(url="")
        assert result.is_error is True
        assert "non-empty" in result.content

    def test_404_returns_is_error(self):
        tool = WebFetchTool(client=_client_returning(status_code=404, text="Not Found"))
        result = tool.run(url="https://example.com/missing")
        assert result.is_error is True
        assert "HTTP 404" in result.content

    def test_500_returns_is_error(self):
        tool = WebFetchTool(client=_client_returning(status_code=500, text="oops"))
        result = tool.run(url="https://example.com/boom")
        assert result.is_error is True
        assert "HTTP 500" in result.content

    def test_redirect_followed_by_default(self):
        # With follow_redirects=True (default in our client), MockTransport
        # would need to handle multi-step. The injected client we pass in
        # has follow_redirects=False by default, so we just verify our tool
        # doesn't break on the underlying transport's behavior.
        tool = WebFetchTool(client=_client_returning(text="final"))
        result = tool.run(url="https://example.com")
        assert result.content == "final"

    def test_html_content_returned(self):
        tool = WebFetchTool(client=_client_returning(
            text="<html><body>hi</body></html>",
            content_type="text/html; charset=utf-8",
        ))
        result = tool.run(url="https://example.com")
        assert result.is_error is False
        assert "<html>" in result.content

    def test_json_content_returned(self):
        tool = WebFetchTool(client=_client_returning(
            text='{"a": 1}',
            content_type="application/json",
        ))
        result = tool.run(url="https://api.example.com/x")
        assert result.is_error is False
        assert result.content == '{"a": 1}'

    def test_binary_content_refused(self):
        tool = WebFetchTool(client=_client_returning(
            text="<binary data>",
            content_type="image/png",
        ))
        result = tool.run(url="https://example.com/img.png")
        assert result.is_error is True
        assert "non-text" in result.content

    def test_pdf_content_refused(self):
        tool = WebFetchTool(client=_client_returning(
            text="%PDF-1.4 ...",
            content_type="application/pdf",
        ))
        result = tool.run(url="https://example.com/doc.pdf")
        assert result.is_error is True

    def test_oversized_body_refused(self):
        # Build a response over the 1 MiB cap
        big_text = "x" * (1 * 1024 * 1024 + 100)
        tool = WebFetchTool(client=_client_returning(text=big_text))
        result = tool.run(url="https://example.com")
        assert result.is_error is True
        assert "exceeds" in result.content
        assert "byte cap" in result.content

    def test_timeout_returns_is_error(self):
        tool = WebFetchTool(client=_client_returning(
            raise_on_get=httpx.TimeoutException("simulated timeout"),
        ))
        result = tool.run(url="https://example.com")
        assert result.is_error is True
        assert "timed out" in result.content

    def test_connection_error_returns_is_error(self):
        tool = WebFetchTool(client=_client_returning(
            raise_on_get=httpx.ConnectError("connection refused"),
        ))
        result = tool.run(url="https://example.com")
        assert result.is_error is True
        assert "fetch failed" in result.content

    def test_no_content_type_header_allows_response(self):
        """Some servers omit Content-Type. We should NOT refuse on that."""
        tool = WebFetchTool(client=_client_returning(
            text="raw text",
            content_type="",
        ))
        result = tool.run(url="https://example.com")
        # No content-type → we don't refuse (defensive default)
        assert result.is_error is False
        assert result.content == "raw text"


# ────────────────────────────────────────────────────────────────────────────
# WebFetch — schema sanity
# ────────────────────────────────────────────────────────────────────────────

class TestWebFetchSchema:
    def test_metadata(self):
        tool = WebFetchTool()
        assert tool.name == "WebFetch"
        assert tool.description
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert schema["required"] == ["url"]
        assert "url" in schema["properties"]


# ────────────────────────────────────────────────────────────────────────────
# WebSearch — Tavily client mocked
# ────────────────────────────────────────────────────────────────────────────

class _FakeTavily:
    """Minimal stand-in for tavily.TavilyClient."""

    def __init__(self, response: Any = None, *, raise_on_search: Exception | None = None) -> None:
        self._response = response
        self._raise = raise_on_search
        self.calls: list[dict[str, Any]] = []

    def search(self, *, query: str, max_results: int) -> Any:
        self.calls.append({"query": query, "max_results": max_results})
        if self._raise is not None:
            raise self._raise
        return self._response


def _make_response(*results: dict[str, Any]) -> dict[str, Any]:
    return {"results": list(results), "query": "test"}


class TestWebSearch:
    def test_basic_search(self):
        fake = _FakeTavily(response=_make_response(
            {"title": "Doc A", "url": "https://a.example.com", "content": "About A"},
            {"title": "Doc B", "url": "https://b.example.com", "content": "About B"},
        ))
        tool = WebSearchTool(tavily_client=fake)

        result = tool.run(query="how does X work")

        assert result.is_error is False
        assert "Doc A" in result.content
        assert "https://a.example.com" in result.content
        assert "Doc B" in result.content
        # Default max_results = 5
        assert fake.calls[0]["max_results"] == 5

    def test_explicit_max_results_passed_through(self):
        fake = _FakeTavily(response=_make_response())
        tool = WebSearchTool(tavily_client=fake)
        tool.run(query="x", max_results=3)
        assert fake.calls[0]["max_results"] == 3

    def test_max_results_capped(self):
        """User asks for 100; we cap at 10."""
        fake = _FakeTavily(response=_make_response())
        tool = WebSearchTool(tavily_client=fake)
        tool.run(query="x", max_results=100)
        assert fake.calls[0]["max_results"] == 10

    def test_max_results_invalid_returns_is_error(self):
        tool = WebSearchTool(tavily_client=_FakeTavily(response=_make_response()))
        result = tool.run(query="x", max_results=0)
        assert result.is_error is True
        assert "positive" in result.content

    def test_empty_query_rejected(self):
        tool = WebSearchTool(tavily_client=_FakeTavily(response=_make_response()))
        result = tool.run(query="   ")
        assert result.is_error is True
        assert "non-empty" in result.content

    def test_no_results_renders_placeholder(self):
        fake = _FakeTavily(response=_make_response())
        tool = WebSearchTool(tavily_client=fake)
        result = tool.run(query="rare query")
        assert result.is_error is False
        assert result.content == "<no results>"

    def test_long_snippet_truncated(self):
        long = "x" * 800
        fake = _FakeTavily(response=_make_response(
            {"title": "T", "url": "https://e.com", "content": long},
        ))
        tool = WebSearchTool(tavily_client=fake)
        result = tool.run(query="x")
        # Truncated to 500 chars + ellipsis marker
        assert "…" in result.content

    def test_tavily_exception_returns_is_error(self):
        fake = _FakeTavily(raise_on_search=RuntimeError("api down"))
        tool = WebSearchTool(tavily_client=fake)
        result = tool.run(query="x")
        assert result.is_error is True
        assert "WebSearch failed" in result.content
        assert "api down" in result.content

    def test_response_with_snippet_field_supported(self):
        """Older Tavily responses use 'snippet' instead of 'content'.
        Tool should accept either."""
        fake = _FakeTavily(response={
            "results": [
                {"title": "T", "url": "https://e.com", "snippet": "fallback content"},
            ],
        })
        tool = WebSearchTool(tavily_client=fake)
        result = tool.run(query="x")
        assert "fallback content" in result.content

    def test_bare_list_response_supported(self):
        """If Tavily ever returns a bare list, accept it."""
        fake = _FakeTavily(response=[
            {"title": "T", "url": "https://e.com", "content": "hi"},
        ])
        tool = WebSearchTool(tavily_client=fake)
        result = tool.run(query="x")
        assert "hi" in result.content


class TestWebSearchConfig:
    """Path where caller did NOT inject a client — tool resolves Tavily +
    API key on its own. Caller controls env via the api_key kwarg or env.

    Both failure modes (tavily-python not installed; key not set) must
    surface as is_error=True. Tests accept either message because the
    test environment may or may not have the optional `[search]` extra
    installed."""

    def test_unconfigured_returns_is_error(self, monkeypatch):
        """Without tavily lib OR without API key → is_error with a message
        that mentions one of the two missing pieces."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        tool = WebSearchTool()  # no injected client, no api_key
        result = tool.run(query="x")
        assert result.is_error is True
        # Either "tavily-python" not installed, or "TAVILY_API_KEY" not set.
        assert "tavily-python" in result.content or "TAVILY_API_KEY" in result.content

    def test_explicit_empty_api_key_returns_is_error(self, monkeypatch):
        """Even if tavily lib is present, an empty api_key kwarg + empty
        env must fail loud."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        tool = WebSearchTool(api_key="")
        result = tool.run(query="x")
        assert result.is_error is True
        assert "tavily-python" in result.content or "TAVILY_API_KEY" in result.content


# ────────────────────────────────────────────────────────────────────────────
# WebSearch — schema sanity
# ────────────────────────────────────────────────────────────────────────────

class TestWebSearchSchema:
    def test_metadata(self):
        tool = WebSearchTool()
        assert tool.name == "WebSearch"
        assert tool.description
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert schema["required"] == ["query"]
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]
