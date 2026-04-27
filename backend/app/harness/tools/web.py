"""Web tools — WebFetch, WebSearch.

Interface mirrors Claude Code's tools so .claude/agents/* prompts using
WebFetch / WebSearch work as-is when those agents are dispatched.

Design contracts:
- All errors surface as `is_error=True` ToolResults — never raise into the
  agent loop.
- WebFetch is synchronous (httpx.Client) — same threading model as fs tools.
- WebSearch requires `tavily-python` (pyproject `[search]` extra) and a
  `TAVILY_API_KEY` env var. Both missing → graceful is_error result that
  tells the agent the tool is unconfigured (not a Python crash).
- Response size capped to keep agent context manageable.
"""

from __future__ import annotations

import os
from typing import Any, ClassVar

import httpx

from app.harness.tools.base import Tool, ToolResult

# Caps balance "useful for the agent" against "don't flood context".
_FETCH_TIMEOUT_SECONDS = 30.0
_FETCH_MAX_BYTES = 1 * 1024 * 1024  # 1 MiB — text only; binary refused
_SEARCH_DEFAULT_MAX_RESULTS = 5
_SEARCH_MAX_RESULTS_CAP = 10


class WebFetchTool(Tool):
    """Fetch a URL and return its text content."""

    name: ClassVar[str] = "WebFetch"
    description: ClassVar[str] = (
        "Fetch a URL via HTTP GET and return the response body as text. "
        "Useful for reading documentation, specs, or other web pages "
        "referenced during analysis. Returns is_error for non-2xx responses, "
        "non-text content types, or bodies exceeding "
        f"{_FETCH_MAX_BYTES} bytes. Timeout is {_FETCH_TIMEOUT_SECONDS}s."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Full URL including scheme (http:// or https://).",
            },
        },
        "required": ["url"],
    }

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        # DI for tests; default constructs per-call client (no shared state).
        self._injected_client = client

    def run(self, *, url: str) -> ToolResult:
        if not isinstance(url, str) or not url.strip():
            return ToolResult(
                content="Error: url must be a non-empty string",
                is_error=True,
            )
        if not (url.startswith("http://") or url.startswith("https://")):
            return ToolResult(
                content=f"Error: url must start with http:// or https://, got: {url!r}",
                is_error=True,
            )

        try:
            if self._injected_client is not None:
                response = self._injected_client.get(url)
            else:
                with httpx.Client(
                    timeout=_FETCH_TIMEOUT_SECONDS,
                    follow_redirects=True,
                ) as c:
                    response = c.get(url)
        except httpx.TimeoutException:
            return ToolResult(
                content=f"Error: fetch timed out after {_FETCH_TIMEOUT_SECONDS}s: {url}",
                is_error=True,
            )
        except httpx.HTTPError as exc:
            return ToolResult(
                content=f"Error: fetch failed: {type(exc).__name__}: {exc}",
                is_error=True,
            )

        if response.status_code < 200 or response.status_code >= 300:
            return ToolResult(
                content=f"Error: HTTP {response.status_code} from {url}",
                is_error=True,
            )

        content_type = (response.headers.get("content-type") or "").lower()
        if content_type and not _is_textual(content_type):
            return ToolResult(
                content=(
                    f"Error: refusing to return non-text content "
                    f"(content-type={content_type!r}) from {url}"
                ),
                is_error=True,
            )

        body_bytes = response.content
        if len(body_bytes) > _FETCH_MAX_BYTES:
            return ToolResult(
                content=(
                    f"Error: response body exceeds {_FETCH_MAX_BYTES} byte cap "
                    f"({len(body_bytes)} bytes) from {url}"
                ),
                is_error=True,
            )

        try:
            text = response.text
        except UnicodeDecodeError:
            return ToolResult(
                content=f"Error: cannot decode response as text: {url}",
                is_error=True,
            )

        return ToolResult(content=text)


def _is_textual(content_type: str) -> bool:
    """Decide whether to return a body to the agent. Allow text/* and the
    common JSON / XML / yaml structured types; refuse images / video /
    binaries that would just burn context."""
    if content_type.startswith("text/"):
        return True
    structured = (
        "application/json",
        "application/ld+json",
        "application/xml",
        "application/xhtml+xml",
        "application/yaml",
        "application/x-yaml",
        "application/javascript",
        "application/ecmascript",
    )
    return any(content_type.startswith(prefix) for prefix in structured)


class WebSearchTool(Tool):
    """Search the web via Tavily and return ranked results.

    Requires `tavily-python` (pyproject `[search]` extra) and TAVILY_API_KEY
    env var. Without either, run() returns is_error so the agent knows to
    skip web verification rather than crashing.
    """

    name: ClassVar[str] = "WebSearch"
    description: ClassVar[str] = (
        "Search the web for a query and return ranked results "
        "(title + url + snippet). Useful for verifying claims, finding "
        "documentation, or gathering evidence. Requires TAVILY_API_KEY."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query in natural language.",
            },
            "max_results": {
                "type": "integer",
                "description": (
                    f"Max number of results to return "
                    f"(default {_SEARCH_DEFAULT_MAX_RESULTS}, "
                    f"cap {_SEARCH_MAX_RESULTS_CAP})."
                ),
            },
        },
        "required": ["query"],
    }

    def __init__(self, *, tavily_client: Any = None, api_key: str | None = None) -> None:
        """DI for tests. In production neither is provided — TAVILY_API_KEY is
        read from env at run() time and a fresh TavilyClient built per call.

        `tavily_client`: pre-built client (overrides api_key + env).
        `api_key`: override env. Useful when key comes from .env via config.
        """
        self._injected_client = tavily_client
        self._injected_api_key = api_key

    def run(self, *, query: str, max_results: int | None = None) -> ToolResult:
        if not isinstance(query, str) or not query.strip():
            return ToolResult(
                content="Error: query must be a non-empty string",
                is_error=True,
            )

        n = max_results if max_results is not None else _SEARCH_DEFAULT_MAX_RESULTS
        if not isinstance(n, int) or n <= 0:
            return ToolResult(
                content=f"Error: max_results must be a positive integer, got: {max_results!r}",
                is_error=True,
            )
        n = min(n, _SEARCH_MAX_RESULTS_CAP)

        # Resolve client.
        if self._injected_client is not None:
            client = self._injected_client
        else:
            try:
                from tavily import TavilyClient  # type: ignore[import-not-found]
            except ImportError:
                return ToolResult(
                    content=(
                        "Error: WebSearch requires `tavily-python`. Install with "
                        "`pip install tavily-python` or via the pyproject "
                        "`[search]` extra."
                    ),
                    is_error=True,
                )
            api_key = self._injected_api_key or os.environ.get("TAVILY_API_KEY", "").strip()
            if not api_key:
                return ToolResult(
                    content=(
                        "Error: TAVILY_API_KEY is not set. WebSearch unavailable. "
                        "Set it in .env or skip web verification for this query."
                    ),
                    is_error=True,
                )
            try:
                client = TavilyClient(api_key=api_key)
            except Exception as exc:  # noqa: BLE001
                return ToolResult(
                    content=f"Error: failed to construct TavilyClient: {type(exc).__name__}: {exc}",
                    is_error=True,
                )

        try:
            response = client.search(query=query, max_results=n)
        except Exception as exc:  # noqa: BLE001 — surface any tavily error
            return ToolResult(
                content=f"Error: WebSearch failed: {type(exc).__name__}: {exc}",
                is_error=True,
            )

        results = _normalize_search_results(response)
        if not results:
            return ToolResult(content="<no results>")

        return ToolResult(content="\n\n".join(_format_result(r) for r in results))


def _normalize_search_results(response: Any) -> list[dict[str, Any]]:
    """Tavily's API returns {"results": [...], ...}. Defensive against shape
    drift — also accept a bare list."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        results = response.get("results")
        if isinstance(results, list):
            return results
    return []


def _format_result(result: dict[str, Any]) -> str:
    """One result rendered as title + url + snippet (newline-separated)."""
    title = str(result.get("title", "<no title>")).strip()
    url = str(result.get("url", "")).strip()
    content = str(result.get("content", "") or result.get("snippet", "")).strip()
    parts = [f"# {title}"]
    if url:
        parts.append(url)
    if content:
        # Keep snippet bounded — tavily can return multi-paragraph chunks
        if len(content) > 500:
            content = content[:500] + "…"
        parts.append(content)
    return "\n".join(parts)
