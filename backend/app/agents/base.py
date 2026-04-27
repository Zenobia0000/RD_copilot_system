"""Base agent utilities — shared LLM client and structured output helpers.

Supports multiple LLM providers (Anthropic / OpenAI / Azure OpenAI / Gemini /
Qwen) via config.llm_provider. LangGraph orchestration will be added in v0.2.

This module provides two distinct call paths:
1. Structured LLM calls (call_llm_structured, call_llm_json, call_llm_json_parsed)
   — deterministic, JSON-safe, never touch web search.
2. Web search calls (web_search_with_llm)
   — free-form text + citations, provider-agnostic web search.

The two paths share client singletons and retry logic but are otherwise
completely independent to prevent web search from polluting JSON output.
"""

from __future__ import annotations

import functools
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.core.config import LLMProvider, settings
from app.observability import emit_counter, phase_timer

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Retry decorator (provider-agnostic)
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BASE_BACKOFF = 1  # seconds


def _is_transient(exc: Exception) -> bool:
    """Return True if the exception is transient and should be retried."""
    # Anthropic SDK
    try:
        from anthropic import APIConnectionError as AConn, RateLimitError as ARL, APIStatusError as ASt
        if isinstance(exc, (ARL, AConn)):
            return True
        if isinstance(exc, ASt) and exc.status_code >= 500:
            return True
    except ImportError:
        pass

    # OpenAI SDK
    try:
        from openai import APIConnectionError as OConn, RateLimitError as ORL, APIStatusError as OSt
        if isinstance(exc, (ORL, OConn)):
            return True
        if isinstance(exc, OSt) and exc.status_code >= 500:
            return True
    except ImportError:
        pass

    return False


def _is_non_retryable(exc: Exception) -> bool:
    """Return True if the exception should NOT be retried."""
    try:
        from anthropic import BadRequestError as ABR, AuthenticationError as AAE
        if isinstance(exc, (ABR, AAE)):
            return True
    except ImportError:
        pass
    try:
        from openai import BadRequestError as OBR, AuthenticationError as OAE
        if isinstance(exc, (OBR, OAE)):
            return True
    except ImportError:
        pass
    return False


def retry_on_transient(fn):
    """Decorator that retries on transient LLM API errors.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s).
    Works with both Anthropic and OpenAI SDKs.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                if _is_non_retryable(exc):
                    raise
                if _is_transient(exc):
                    last_exc = exc
                else:
                    raise

            if attempt == _MAX_RETRIES:
                raise last_exc  # type: ignore[misc]

            delay = _BASE_BACKOFF * (2 ** attempt)
            logger.warning(
                "LLM call failed (attempt %d/%d), retrying in %ds: %s",
                attempt + 1,
                _MAX_RETRIES + 1,
                delay,
                last_exc,
            )
            time.sleep(delay)

        raise last_exc  # type: ignore[misc]

    return wrapper


# ---------------------------------------------------------------------------
# JSON response cleaning
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) from LLM output."""
    m = _CODE_FENCE_RE.match(text.strip())
    return m.group(1).strip() if m else text.strip()


# ---------------------------------------------------------------------------
# Token estimation + warning
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """Rough token count: chars / 4 approximation."""
    return len(text) // 4


# ---------------------------------------------------------------------------
# max_tokens resolution — no hardcoded limits
# ---------------------------------------------------------------------------
# Anthropic API requires max_tokens → use env-configurable setting.
# OpenAI-compatible APIs → omit max_tokens entirely, let model decide.


def _resolve_anthropic_max_tokens(explicit: int | None) -> int:
    """Anthropic requires max_tokens. Use explicit override or config setting."""
    if explicit is not None:
        return explicit
    return settings.anthropic_max_output_tokens


def _warn_if_high_token_usage(system: str, user_message: str, max_tokens: int) -> None:
    """Log a warning if the estimated input tokens exceed 80% of max_tokens."""
    estimated = _estimate_tokens(system + user_message)
    threshold = int(max_tokens * 0.8)
    if estimated > threshold:
        logger.warning(
            "Estimated input token count (%d) exceeds 80%% of max_tokens (%d). "
            "Consider increasing max_tokens or shortening the prompt.",
            estimated,
            max_tokens,
        )


# ---------------------------------------------------------------------------
# LLM clients — provider-agnostic singleton
# ---------------------------------------------------------------------------

_anthropic_client = None
# OpenAI-compatible clients keyed by provider name
_openai_compat_clients: dict[str, object] = {}


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic

        kwargs: dict = {}

        # Azure proxy 指向 Anthropic 的場景
        if settings.llm_provider == LLMProvider.AZURE_OPENAI:
            base_url = (settings.azure_openai_base_url or "").lower()
            if "anthropic" in base_url:
                kwargs["api_key"] = settings.azure_openai_api_key
                kwargs["base_url"] = settings.azure_openai_base_url

        if "api_key" not in kwargs:
            kwargs["api_key"] = settings.anthropic_api_key

        _anthropic_client = Anthropic(**kwargs)
    return _anthropic_client


def _get_openai_compat(provider: LLMProvider):
    """Get or create an OpenAI-compatible client for the given provider.

    Works for: openai, azure_openai, gemini, qwen — all use the OpenAI SDK
    with different base_url / api_key combinations.
    """
    key = provider.value
    if key not in _openai_compat_clients:
        from openai import OpenAI
        cfg = {
            LLMProvider.OPENAI: {
                "api_key": settings.openai_api_key,
            },
            LLMProvider.AZURE_OPENAI: {
                "api_key": settings.azure_openai_api_key,
                "base_url": settings.azure_openai_base_url or None,
            },
            LLMProvider.GEMINI: {
                "api_key": settings.gemini_api_key,
                "base_url": settings.gemini_base_url,
            },
            LLMProvider.QWEN: {
                "api_key": settings.qwen_api_key,
                "base_url": settings.qwen_base_url,
            },
        }
        params = {k: v for k, v in cfg[provider].items() if v}
        _openai_compat_clients[key] = OpenAI(**params)
    return _openai_compat_clients[key]


# ---------------------------------------------------------------------------
# Provider routing helper — determines Anthropic vs OpenAI-compat
# ---------------------------------------------------------------------------

def _use_anthropic_path() -> bool:
    """Check if the current provider config should route to Anthropic SDK.

    Returns True for:
    - LLM_PROVIDER=anthropic
    - LLM_PROVIDER=azure_openai with base_url containing 'anthropic'
    """
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        return True
    if settings.llm_provider == LLMProvider.AZURE_OPENAI:
        base_url = (settings.azure_openai_base_url or "").lower()
        if "anthropic" in base_url:
            return True
    return False


# ---------------------------------------------------------------------------
# Structured LLM calls (no web search — deterministic, JSON-safe)
# ---------------------------------------------------------------------------

def _call_anthropic(
    system: str,
    user_message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
) -> str:
    client = _get_anthropic()
    resolved = _resolve_anthropic_max_tokens(max_tokens)
    # Use streaming to avoid SDK 10-minute non-streaming timeout limit
    with client.messages.stream(
        model=model or settings.default_model,
        max_tokens=resolved,
        temperature=temperature,
        system=system,
        cache_control={"type": "ephemeral"},
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        return stream.get_final_text()


def _call_openai_compat(
    system: str,
    user_message: str,
    *,
    provider: LLMProvider,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
) -> str:
    """Call any OpenAI-compatible provider (OpenAI / Azure / Gemini / Qwen).
    max_tokens is omitted by default — the model uses its full output capacity."""
    client = _get_openai_compat(provider)
    resolved_model = model or settings.default_model
    if not resolved_model:
        raise ValueError(
            f"No model configured for provider '{settings.llm_provider.value}'. "
            f"Set the corresponding *_DEFAULT_MODEL in .env."
        )
    kwargs: dict = {
        "model": resolved_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def _call_provider(
    system: str,
    user_message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
) -> str:
    """Route to the active LLM provider."""
    if _use_anthropic_path():
        return _call_anthropic(
            system, user_message,
            model=model, max_tokens=max_tokens, temperature=temperature,
        )
    return _call_openai_compat(
        system, user_message,
        provider=settings.llm_provider,
        model=model, max_tokens=max_tokens, temperature=temperature,
    )


# Keep backward-compatible accessor
def get_llm():
    """Return the Anthropic client (for legacy callers)."""
    return _get_anthropic()


# ---------------------------------------------------------------------------
# Structured LLM call functions (public API — never use web search)
# ---------------------------------------------------------------------------


@retry_on_transient
def call_llm_structured(
    system: str,
    user_message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
) -> str:
    """Call LLM and return the text response. max_tokens=None lets each provider use its full capacity."""
    if max_tokens is not None:
        _warn_if_high_token_usage(system, user_message, max_tokens)
    return _call_provider(system, user_message, model=model, max_tokens=max_tokens, temperature=temperature)


@retry_on_transient
def call_llm_json(
    system: str,
    user_message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.2,
) -> str:
    """Call LLM requesting JSON output. max_tokens=None lets each provider use its full capacity."""
    if max_tokens is not None:
        _warn_if_high_token_usage(system, user_message, max_tokens)
    json_system = system + "\n\n回覆格式：純 JSON，不要 markdown code block。"
    with phase_timer("llm.call", model=(model or settings.default_model or "")):
        raw = _call_provider(json_system, user_message, model=model, max_tokens=max_tokens, temperature=temperature)
    cleaned = _strip_code_fences(raw)
    if not cleaned or not cleaned.strip():
        emit_counter("llm.empty_response")
    else:
        # Observability-only parse probe: emit a counter when the payload is
        # unparseable JSON. We deliberately do NOT raise here — downstream
        # callers handle parse errors themselves (some tolerate empty dicts).
        try:
            json.loads(cleaned)
        except json.JSONDecodeError:
            emit_counter("llm.json_parse_fail")
    return cleaned


def call_llm_json_parsed(
    system: str,
    user_message: str,
    *,
    response_model: type[T],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.2,
) -> T:
    """Call LLM for JSON, then parse into a Pydantic model."""
    raw_json = call_llm_json(
        system,
        user_message,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    data = json.loads(raw_json)
    if isinstance(response_model, type) and issubclass(response_model, BaseModel):
        return response_model.model_validate(data)  # type: ignore[return-value]
    raise TypeError(f"response_model must be a Pydantic BaseModel subclass, got {response_model}")


# ===========================================================================
# Web Search — provider-agnostic web search with LLM synthesis
# ===========================================================================
#
# Design: web search is intentionally separated from the structured LLM calls
# above. The two paths share client singletons and retry logic, but:
#
# - Structured calls (call_llm_json, etc.) → deterministic, JSON-safe, no search
# - Web search (web_search_with_llm) → free-form text + citations
#
# This prevents web search results from polluting JSON output. When you need
# both search AND structured analysis, call them in sequence:
#
#   search = web_search_with_llm("market trends for X")
#   analysis = call_llm_json(SYSTEM, f"Given: {search.text}\n\nAnalyze...")
# ===========================================================================


# ---------------------------------------------------------------------------
# WebSearchResult — structured output for all web search calls
# ---------------------------------------------------------------------------

@dataclass
class WebSearchResult:
    """Result from a web-search-augmented LLM call.

    Attributes:
        text: LLM-synthesized answer (natural language, NOT JSON).
        citations: De-duplicated list of source URLs with metadata.
            Each citation dict has keys: url, title, cited_text.
        search_queries_used: Number of web search queries the LLM made
            (for cost/usage tracking).
    """
    text: str
    citations: list[dict] = field(default_factory=list)
    search_queries_used: int = 0

    @property
    def text_with_citations(self) -> str:
        """Text with appended citation footnotes — ready for display."""
        if not self.citations:
            return self.text
        parts = [self.text, "\n\n---\n**Sources:**"]
        for i, cite in enumerate(self.citations, 1):
            title = cite.get("title") or cite.get("url", "")
            parts.append(f"{i}. [{title}]({cite['url']})")
        return "\n".join(parts)

    @property
    def citation_urls(self) -> list[str]:
        """Convenience: just the URLs for downstream processing."""
        return [c["url"] for c in self.citations if c.get("url")]


# ---------------------------------------------------------------------------
# Anthropic web search helpers
# ---------------------------------------------------------------------------

def _extract_anthropic_text_blocks(content_blocks: list) -> str:
    """Extract only TextBlock content from Anthropic response.

    Skips ServerToolUseBlock, WebSearchToolResultBlock, etc. so the
    returned string is clean LLM-generated text without tool artifacts.
    """
    parts = []
    for block in content_blocks:
        if getattr(block, "type", "") == "text" and hasattr(block, "text"):
            parts.append(block.text)
    return "".join(parts)


def _extract_anthropic_citations(content_blocks: list) -> list[dict]:
    """Extract citations from Anthropic response content blocks.

    Two sources of citation data:
    1. TextBlock.citations — inline citations the model placed within text
    2. WebSearchToolResultBlock.content — raw search result URLs/titles
    """
    citations = []
    seen_urls: set[str] = set()

    for block in content_blocks:
        # Source 1: TextBlock inline citations
        if hasattr(block, "citations") and block.citations:
            for cite in block.citations:
                url = getattr(cite, "url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append({
                        "url": url,
                        "title": getattr(cite, "title", ""),
                        "cited_text": getattr(cite, "cited_text", ""),
                    })

        # Source 2: WebSearchToolResultBlock search results
        block_type = getattr(block, "type", "")
        if block_type == "web_search_tool_result" and hasattr(block, "content"):
            for result_block in (block.content or []):
                url = getattr(result_block, "url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append({
                        "url": url,
                        "title": getattr(result_block, "title", ""),
                        "cited_text": "",
                    })

    return citations


def _get_anthropic_search_count(response) -> int:
    """Extract the number of web search queries used from Anthropic usage metadata."""
    if hasattr(response, "usage") and hasattr(response.usage, "server_tool_use"):
        stu = response.usage.server_tool_use
        return getattr(stu, "web_search_requests", 0)
    return 0


# ---------------------------------------------------------------------------
# OpenAI web search helpers
# ---------------------------------------------------------------------------

def _extract_openai_citations(response) -> list[dict]:
    """Extract URL citations from OpenAI Responses API output.

    The Responses API returns annotations with type="url_citation"
    on output message content blocks.
    """
    citations = []
    seen_urls: set[str] = set()
    for item in response.output:
        if not hasattr(item, "content"):
            continue
        for content_block in item.content:
            if not hasattr(content_block, "annotations"):
                continue
            for ann in content_block.annotations:
                if getattr(ann, "type", None) == "url_citation":
                    url = getattr(ann, "url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        citations.append({
                            "url": url,
                            "title": getattr(ann, "title", ""),
                            "cited_text": "",
                        })
    return citations


# ---------------------------------------------------------------------------
# Provider-specific web search implementations
# ---------------------------------------------------------------------------

def _web_search_anthropic(
    query: str,
    *,
    system: str,
    model: str | None,
    max_tokens: int | None,
    temperature: float,
    max_uses: int,
) -> WebSearchResult:
    """Web search via Anthropic's built-in web_search tool.

    Uses messages.create (non-streaming) because streaming does not
    support server-side tool use.
    """
    client = _get_anthropic()
    resolved_model = model or settings.default_model
    resolved_tokens = _resolve_anthropic_max_tokens(max_tokens)

    logger.info(
        "Anthropic web search: model=%s, max_uses=%d",
        resolved_model, max_uses,
    )

    response = client.messages.create(
        model=resolved_model,
        max_tokens=resolved_tokens,
        temperature=temperature,
        system=system,
        cache_control={"type": "ephemeral"},
        messages=[{"role": "user", "content": query}],
        tools=[{
            "type": "web_search_20260209",
            "name": "web_search",
            "max_uses": max_uses,
        }],
    )

    text = _extract_anthropic_text_blocks(response.content)
    citations = _extract_anthropic_citations(response.content)
    search_count = _get_anthropic_search_count(response)

    logger.info(
        "Anthropic web search complete: %d citations, %d searches used",
        len(citations), search_count,
    )

    return WebSearchResult(
        text=text,
        citations=citations,
        search_queries_used=search_count,
    )


def _web_search_openai(
    query: str,
    *,
    system: str,
    model: str | None,
    provider: LLMProvider,
) -> WebSearchResult:
    """Web search via OpenAI Responses API (works for OpenAI and Azure OpenAI).

    Uses the responses.create endpoint with tools=[{"type": "web_search"}].
    """
    client = _get_openai_compat(provider)
    resolved_model = model or settings.default_model

    logger.info(
        "OpenAI web search: provider=%s, model=%s",
        provider.value, resolved_model,
    )

    response = client.responses.create(
        model=resolved_model,
        tools=[{"type": "web_search"}],
        instructions=system,
        input=query,
    )

    text = response.output_text or ""
    citations = _extract_openai_citations(response)

    logger.info(
        "OpenAI web search complete: %d citations", len(citations),
    )

    return WebSearchResult(
        text=text,
        citations=citations,
        search_queries_used=1,  # Responses API doesn't expose exact count
    )


def _web_search_gemini(
    query: str,
    *,
    system: str,
    model: str | None,
    max_tokens: int | None,
    temperature: float,
) -> WebSearchResult:
    """Web search via Gemini's google_search grounding tool.

    Uses the OpenAI-compatible chat completions endpoint with
    a google_search function tool.
    """
    client = _get_openai_compat(LLMProvider.GEMINI)
    resolved_model = model or settings.default_model

    logger.info("Gemini web search (grounding): model=%s", resolved_model)

    kwargs: dict = {
        "model": resolved_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        "tools": [{"type": "function", "function": {"name": "google_search"}}],
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""

    # Gemini doesn't return standardized citations in the OpenAI-compat format
    return WebSearchResult(text=text, citations=[], search_queries_used=1)


def _web_search_qwen(
    query: str,
    *,
    system: str,
    model: str | None,
    max_tokens: int | None,
    temperature: float,
) -> WebSearchResult:
    """Web search via Qwen's DashScope enable_search parameter.

    Uses extra_body={"enable_search": True} on the OpenAI-compatible endpoint.
    """
    client = _get_openai_compat(LLMProvider.QWEN)
    resolved_model = model or settings.default_model

    logger.info("Qwen web search: model=%s", resolved_model)

    kwargs: dict = {
        "model": resolved_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        "extra_body": {"enable_search": True},
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""

    # Qwen search results don't have standardized citation format
    return WebSearchResult(text=text, citations=[], search_queries_used=1)


# ---------------------------------------------------------------------------
# Web search public API
# ---------------------------------------------------------------------------

_DEFAULT_SEARCH_SYSTEM = (
    "You are a helpful research assistant. Provide accurate, "
    "well-sourced answers based on web search results."
)


@retry_on_transient
def web_search_with_llm(
    query: str,
    *,
    system: str = _DEFAULT_SEARCH_SYSTEM,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
    max_search_uses: int = 3,
) -> WebSearchResult:
    """Perform a web search and return an LLM-synthesized answer with citations.

    This is completely independent from the structured LLM calls above.
    It automatically routes to the correct provider's web search API.

    Args:
        query: The user's question (sent as user message to the LLM).
        system: System prompt guiding the LLM's synthesis of search results.
        model: Override the default model. None = use settings.default_model.
        max_tokens: Override max output tokens. None = provider default.
        temperature: Sampling temperature. Default 0.3 for factual answers.
        max_search_uses: Max number of web searches the LLM can perform
            (Anthropic only; other providers ignore this).

    Returns:
        WebSearchResult with .text, .citations, and .search_queries_used.

    Raises:
        RuntimeError: If web search is disabled (WEB_SEARCH_ENABLED=false).
        ValueError: If the current provider doesn't support web search.

    Example:
        # Simple search
        result = web_search_with_llm("What did Trump say today?")
        print(result.text)
        for cite in result.citations:
            print(f"  - {cite['title']}: {cite['url']}")

        # Search + structured analysis (two-step pattern)
        search = web_search_with_llm("2024 EV battery cost trends")
        analysis = call_llm_json(SYSTEM, f"Given: {search.text}\\nAnalyze...")
    """
    if not settings.web_search_enabled:
        raise RuntimeError(
            "Web search is disabled. Set WEB_SEARCH_ENABLED=true in .env to enable."
        )

    provider = settings.llm_provider

    if _use_anthropic_path():
        return _web_search_anthropic(
            query,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            max_uses=max_search_uses,
        )

    if provider in (LLMProvider.OPENAI, LLMProvider.AZURE_OPENAI):
        return _web_search_openai(
            query,
            system=system,
            model=model,
            provider=provider,
        )

    if provider == LLMProvider.GEMINI:
        return _web_search_gemini(
            query,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if provider == LLMProvider.QWEN:
        return _web_search_qwen(
            query,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    raise ValueError(
        f"Web search not supported for provider: {provider.value}. "
        f"Supported: anthropic, openai, azure_openai, gemini, qwen."
    )