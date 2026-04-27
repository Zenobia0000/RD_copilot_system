"""Web search service for evidence grounding.

Supports Tavily API when configured; otherwise falls back to no-op.
Results are formatted as evidence references for prompt injection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str = ""  # e.g. "ISO", "Google Patents", "SAE"
    relevance_score: float = 0.0


@dataclass
class SearchResponse:
    """Aggregated search results."""
    results: list[SearchResult] = field(default_factory=list)
    query: str = ""
    provider: str = "none"  # "tavily" | "none"


def _tavily_available() -> bool:
    """Check if Tavily is configured."""
    return bool(getattr(settings, "tavily_api_key", ""))


async def search_web(query: str, *, max_results: int = 5, topic: str = "general") -> SearchResponse:
    """Search the web for evidence.

    Args:
        query: Search query string.
        max_results: Max results to return.
        topic: Tavily topic hint ("general" or "news").

    Returns:
        SearchResponse with results, or empty if no search provider configured.
    """
    if not _tavily_available():
        logger.debug("No web search API configured — skipping web search for: %s", query)
        return SearchResponse(query=query, provider="none")

    try:
        from tavily import AsyncTavilyClient  # type: ignore[import-untyped]

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        raw = await client.search(
            query=query,
            max_results=max_results,
            topic=topic,
            include_answer=False,
        )

        results = []
        for item in raw.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source=_extract_domain(item.get("url", "")),
                relevance_score=item.get("score", 0.0),
            ))

        return SearchResponse(results=results, query=query, provider="tavily")

    except Exception:
        logger.exception("Web search failed for query: %s", query)
        return SearchResponse(query=query, provider="none")


def _extract_domain(url: str) -> str:
    """Extract domain from URL for source attribution."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return url


def format_search_context(response: SearchResponse) -> str:
    """Format search results as context block for prompt injection.

    Returns empty string if no results.
    """
    if not response.results:
        return ""

    lines = ["## 網路搜尋參考資料（以下為即時搜尋結果，請據此佐證你的建議）"]
    for i, r in enumerate(response.results, 1):
        ref_id = f"WEB-SEARCH-{i:03d}"
        lines.append(f"\n### [{ref_id}] {r.title}")
        lines.append(f"來源: {r.source} ({r.url})")
        lines.append(f"摘要: {r.snippet}")

    lines.append(
        "\n## 引用規則"
        "\n- 你的每條建議必須引用至少 1 條上述參考資料或明確標示為「工程推論」"
        "\n- 引用格式：[WEB-SEARCH-001] 或 [工程推論]"
        "\n- 若參考資料與建議內容無關，不要勉強引用"
    )
    return "\n".join(lines)
