"""Evidence retrieval orchestrator — combines web search + document context.

Provides grounding context for Brief-stage AI suggestions to reduce hallucination.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.web_search import search_web, format_search_context, SearchResult


@dataclass
class EvidenceReference:
    """A single evidence reference returned alongside AI suggestions."""
    ref_id: str          # e.g. "WEB-SEARCH-001", "DOC-001", "ENG-REASONING"
    ref_type: str        # "web_search" | "uploaded_doc" | "engineering_reasoning"
    title: str
    source: str          # domain, filename, or "工程推論"
    url: str = ""
    snippet: str = ""


@dataclass
class EvidenceContext:
    """Aggregated evidence context for prompt injection."""
    prompt_context: str                             # formatted text block for LLM prompt
    references: list[EvidenceReference] = field(default_factory=list)  # structured refs for API response


async def retrieve_constraint_evidence(
    mission: str,
    existing_constraints: list[str],
) -> EvidenceContext:
    """Retrieve evidence for constraint suggestions.

    Searches for: safety standards, regulations, physical limits relevant to the mission.
    """
    queries = [
        f"{mission} 安全標準 法規 ISO EN 認證",
        f"{mission} safety standards regulations certification",
    ]
    return await _multi_query_retrieve(queries, max_per_query=3)


async def retrieve_kpi_evidence(
    mission: str,
    constraints: list[str],
) -> EvidenceContext:
    """Retrieve evidence for KPI suggestions.

    Searches for: industry benchmarks, test standards, performance metrics.
    """
    constraint_text = " ".join(constraints[:3]) if constraints else ""
    queries = [
        f"{mission} KPI benchmark 測試標準 performance metrics",
        f"{mission} test standard specification {constraint_text}",
    ]
    return await _multi_query_retrieve(queries, max_per_query=3)


async def retrieve_5w1h_evidence(
    mission: str,
) -> EvidenceContext:
    """Retrieve evidence for 5W1H task definition.

    Searches for: design methodology, project planning best practices.
    """
    queries = [
        f"{mission} 設計開發流程 milestone 專案規劃",
    ]
    return await _multi_query_retrieve(queries, max_per_query=3)


async def retrieve_mission_rewrite_evidence(
    mission: str,
) -> EvidenceContext:
    """Retrieve evidence for mission rewrite.

    Searches for: engineering specification writing standards.
    """
    queries = [
        f"{mission} specification requirements engineering",
    ]
    return await _multi_query_retrieve(queries, max_per_query=3)


def format_document_context(doc_texts: list[dict[str, str]]) -> tuple[str, list[EvidenceReference]]:
    """Format uploaded document texts as prompt context.

    Args:
        doc_texts: List of {"filename": str, "content": str} dicts.

    Returns:
        Tuple of (prompt_context_string, list_of_evidence_references).
    """
    if not doc_texts:
        return "", []

    lines = ["## 使用者上傳文件內容（以下為專案相關文件，請據此佐證你的建議）"]
    refs = []

    for i, doc in enumerate(doc_texts, 1):
        ref_id = f"DOC-{i:03d}"
        filename = doc.get("filename", f"document-{i}")
        content = doc.get("content", "")
        # Truncate very long documents
        if len(content) > 3000:
            content = content[:3000] + "\n... (已截斷)"

        lines.append(f"\n### [{ref_id}] {filename}")
        lines.append(content)

        refs.append(EvidenceReference(
            ref_id=ref_id,
            ref_type="uploaded_doc",
            title=filename,
            source=filename,
            snippet=content[:200],
        ))

    return "\n".join(lines), refs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _multi_query_retrieve(
    queries: list[str],
    *,
    max_per_query: int = 3,
) -> EvidenceContext:
    """Run multiple search queries and merge results."""
    all_results: list[SearchResult] = []
    seen_urls: set[str] = set()

    for query in queries:
        response = await search_web(query, max_results=max_per_query)
        for r in response.results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)

    # Build prompt context
    from app.services.web_search import SearchResponse
    merged = SearchResponse(results=all_results, query=" | ".join(queries), provider="tavily" if all_results else "none")
    prompt_context = format_search_context(merged)

    # Build structured references
    refs = []
    for i, r in enumerate(all_results, 1):
        refs.append(EvidenceReference(
            ref_id=f"WEB-SEARCH-{i:03d}",
            ref_type="web_search",
            title=r.title,
            source=r.source,
            url=r.url,
            snippet=r.snippet[:200],
        ))

    return EvidenceContext(prompt_context=prompt_context, references=refs)
